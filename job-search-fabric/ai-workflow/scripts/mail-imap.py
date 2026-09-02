#!/usr/bin/env python3
"""
mail-imap.py — move mail by Message-ID over IMAP, server-side. The fast path.

Covers every mailbox move in the pipeline. All three did the same expensive thing:

    --op trash     Phase C   INBOX -> Deleted Messages   was mail-trash.applescript
    --op archive   Phase D   INBOX -> Archive            was mail-archive.applescript
    --op restore   recovery  Deleted Messages -> INBOX   was mail-restore-from-trash.applescript

WHY. The cost was always the lookup, never the move. Every one of those AppleScripts resolves
a target with `messages of <mailbox> whose message id is <id>`, and Mail does not push that
filter down to its own index — it materializes the mailbox across the Apple Event bridge and
filters there. Measured 2026-09-01 on a 58,953-message Inbox, 60 messages:

    mail-trash.applescript   `whose message id is` x ~150 full passes      91 min
    mail-trash.py            one bulk Apple Event, match in Python         ~50 s
    mail-imap.py (this)      server-side SEARCH HEADER, indexed by iCloud  ~seconds

IMAP does not go through Mail at all: iCloud resolves `HEADER Message-ID` against its own
server-side index and answers with a UID. Archive was never as painful as Phase C only because
Phase D archives five or six messages, not sixty — it is the same cost per message.

WHAT IT DOES TO YOUR MAIL. Exactly what these phases have always done: it MOVES a message
between mailboxes. Never an expunge, never a permanent delete — a trashed message sits in
Deleted Messages, recoverable, as before. Mail.app syncs the change down on its own; this is
the same protocol Mail itself speaks, not a way around it.

THIS SCRIPT IS NOT THE GATE. It moves what it is told to move. Which messages may be archived
— never a named individual's mail, never a LinkedIn notification, never non-job mail — is
decided upstream by triage-match.py, which writes confirmed-archive-ids.txt. Same for
confirmed-trash-ids.txt, which may only ever contain postings confirmed logged.

CREDENTIALS — read, never held, never entered by Claude.
This script reads an app-specific password from the macOS Keychain at runtime. Claude does not
create it, does not type it, and never sees its value. Carl does both steps himself, once:

    1. Generate an app-specific password at appleid.apple.com -> Sign-In and Security.
       (Requires two-factor auth on the Apple ID. A normal Apple ID password will NOT work
       for IMAP and should never be used here.)

    2. Store it in the Keychain — Carl runs this and types the password at the prompt:

         security add-generic-password -U -s jobsearch-icloud-imap \\
             -a <your-icloud-username> -w

       -w with no value makes `security` prompt for it, so the password never appears in a
       command line, in shell history, or in this session.

Apple wants the NAME of the iCloud address as the username, not the full address —
`emilyparker`, not `emilyparker@icloud.com`. Both are accepted here; --check reports which one
authenticated.

    python3 scripts/mail-imap.py --check                       # connect, no changes
    python3 scripts/mail-imap.py --op archive --dry-run         # resolve, verify, move nothing
    python3 scripts/mail-imap.py --op trash
    python3 scripts/mail-imap.py --op restore --ids some-ids.txt

Each op has its own default ID file and its own log, matching the AppleScript it replaces, so
mail-trash-log.txt and mail-archive-log.txt stay continuous across the change. IMAP-path lines
carry an `[imap]` marker so a slow run and a fast one are distinguishable after the fact.

SAFETY. Every candidate is fetched and its Message-ID header compared to the target before the
move. A mismatch is logged MISMATCH and skipped. A search returning more than one UID for one
Message-ID is logged AMBIGUOUS and skipped — duplicates are Carl's to look at, not this
script's to guess at.
"""
import argparse, datetime, email, imaplib, os, ssl, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))

HOST = "imap.mail.me.com"
PORT = 993
KEYCHAIN_SERVICE = "jobsearch-icloud-imap"

# Destinations are discovered from the server's special-use flags, never hardcoded — an
# account whose Archive is named something else still works. The fallbacks are iCloud's
# usual names, used only when the server advertises no flag.
OPS = {
    "trash":   {"src": "INBOX",   "dst": "\\Trash",   "dst_fallback": "Deleted Messages",
                "ids": "confirmed-trash-ids.txt",   "log": "mail-trash-log.txt",
                "verb": "TRASHED",  "all_copies": True},
    "archive": {"src": "INBOX",   "dst": "\\Archive", "dst_fallback": "Archive",
                "ids": "confirmed-archive-ids.txt", "log": "mail-archive-log.txt",
                "verb": "ARCHIVED", "all_copies": True},
    "restore": {"src": "\\Trash", "dst": "INBOX",     "dst_fallback": "INBOX",
                "ids": None,                        "log": "mail-archive-log.txt",
                "verb": "RESTORED", "all_copies": False},
}

imaplib._MAXLINE = 10_000_000     # iCloud sends long LIST/SEARCH responses on a big mailbox


def stamp():
    return datetime.datetime.now().strftime("%A, %B %-d, %Y at %-I:%M:%S %p")


UNAVAILABLE = 3      # this backend cannot run at all — a dispatcher should fall back


def unavailable(msg):
    """Exit 3: the IMAP backend is unusable (no credential, bad login, no network).

    Distinct from exit 1 so mail-move.py can fall back to the Apple Events path instead of
    halting an unattended A->C run. A revoked app-specific password must not stop Phase C.
    """
    print(msg, file=sys.stderr)
    sys.exit(UNAVAILABLE)


def keychain(service, account):
    """Read the app-specific password from the Keychain. Never printed, never logged."""
    cmd = ["security", "find-generic-password", "-w", "-s", service]
    if account:
        cmd += ["-a", account]
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode:
        unavailable(
            f"\n  No Keychain item for service {service!r}"
            + (f", account {account!r}" if account else "") + ".\n"
            f"  Carl creates it himself — Claude never handles the password:\n\n"
            f"      security add-generic-password -U -s {service} -a <icloud-username> -w\n\n"
            f"  -w with no value prompts for the password, so it never lands in a command\n"
            f"  line or in shell history. Generate the app-specific password first at\n"
            f"  appleid.apple.com -> Sign-In and Security.\n")
    return p.stdout.rstrip("\n")


def keychain_account(service):
    """The account (iCloud username) stored alongside the password, so it isn't hardcoded."""
    p = subprocess.run(["security", "find-generic-password", "-s", service],
                       capture_output=True, text=True)
    for line in p.stdout.splitlines():
        line = line.strip()
        if line.startswith('"acct"'):
            return line.split('="')[-1].rstrip('"')
    return None


def login_forms(user):
    """The forms iCloud might accept, in the order Apple documents.

    Apple asks for the NAME of the iCloud Mail address — `<user>`, not
    `<user>@<mail-domain>`. The three domains (@icloud/@me/@mac) are one mailbox sharing
    one local part, so trying each costs nothing and covers accounts whose Mail service sits
    on a different domain from the Apple ID (this one: Apple ID @mac.com, Mail @me.com).

    ALIASES ARE NOT LOGIN NAMES. An Apple ID can carry several alias addresses that receive
    mail perfectly well and cannot authenticate. If login fails for every form below, check
    that the username is the PRIMARY address's local part and not an alias.
    """
    local = user.split("@")[0]
    forms = [local, f"{local}@me.com", f"{local}@icloud.com", f"{local}@mac.com"]
    if "@" in user and user not in forms:
        forms.insert(1, user)
    seen, out = set(), []
    for f in forms:
        if f not in seen:
            seen.add(f); out.append(f)
    return out


def connect(user, password):
    ctx = ssl.create_default_context()
    M = imaplib.IMAP4_SSL(HOST, PORT, ssl_context=ctx)
    tried, last = [], ""
    for u in login_forms(user):
        tried.append(u)
        try:
            M.login(u, password)
            return M, u
        except imaplib.IMAP4.error as err:
            last = str(err)
            continue
    M.logout()
    unavailable(f"\n  IMAP login rejected for every form of {user!r}:\n"
             f"      {', '.join(tried)}\n"
             f"  server said: {last}\n\n"
             f"  Two things this usually means:\n"
             f"    * the Keychain item holds the Apple ID password, not an APP-SPECIFIC one\n"
             f"    * the username is an ALIAS. Aliases receive mail but cannot sign in —\n"
             f"      use the local part of the PRIMARY iCloud Mail address.\n")


def find_mailbox(M, flag, fallback):
    """Resolve a mailbox by its IMAP special-use flag, falling back to a literal name.

    Discovering it beats hardcoding: the old restore AppleScript carries a comment about
    `trash mailbox of account` erroring on this very account, and works around it by trying
    "Deleted Messages" / "Deleted Items" / "Trash" by name. The server tells us directly.
    """
    if not flag.startswith("\\"):
        return flag                       # already a literal name, e.g. "INBOX"
    typ, boxes = M.list()
    if typ == "OK":
        for raw in boxes or []:
            line = raw.decode(errors="replace")
            if flag in line:
                return line.rsplit(' "/" ', 1)[-1].strip().strip('"')
    return fallback


def search_id(M, mid):
    """UIDs whose Message-ID header matches. Server-side and indexed.

    THE BRACKETS ARE NOT OPTIONAL. The raw header reads `Message-ID: <id@host>`, and Mail's
    AppleScript hands back the id WITHOUT the angle brackets, so the ID files in this folder
    are all bracketless. iCloud does not substring-match the header value — it wants the
    literal form:

        UID SEARCH HEADER Message-ID "id@host"     -> OK, no results   (silently wrong)
        UID SEARCH HEADER Message-ID "<id@host>"   -> OK, UID 148080

    Caught 2026-09-01 by dry-running five messages known to be in the Inbox and getting zero
    hits. That is the failure this script most needs to not have: a bare `SEARCH` miss looks
    exactly like "already handled", so Phase C would have reported nothing to do and moved on.
    Bracketless is still tried second, for a server that behaves the other way round.
    """
    bare = mid.strip()
    if bare.startswith("<") and bare.endswith(">"):
        bare = bare[1:-1]
    for form in (f"<{bare}>", bare):
        safe = form.replace('\\', '\\\\').replace('"', '\\"')
        typ, data = M.uid("SEARCH", "HEADER", "Message-ID", f'"{safe}"')
        if typ == "OK" and data and data[0]:
            return data[0].split()
    return []


def header_id(M, uid):
    """The message's own Message-ID, for the pre-move check."""
    typ, data = M.uid("FETCH", uid, "(BODY.PEEK[HEADER.FIELDS (MESSAGE-ID)])")
    if typ != "OK" or not data or not isinstance(data[0], tuple):
        return None
    msg = email.message_from_bytes(data[0][1])
    raw = (msg.get("Message-ID") or "").strip()
    return raw[1:-1] if raw.startswith("<") and raw.endswith(">") else raw


def log(path, entries):
    """Append to the same log the AppleScript for this op wrote, same vocabulary.

    The `[imap]` marker is the one addition: it keeps a 91-minute run and a 3-second run
    distinguishable after the fact, which matters when reading back why a phase was slow.
    """
    with open(path, "a") as f:
        for kind, mid in entries:
            f.write(f"{stamp()}  {kind}  {mid}   [imap]\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--op", choices=list(OPS), default="trash",
                    help="trash (Phase C), archive (Phase D), or restore (recovery). "
                         "Each has its own default ID file and log.")
    ap.add_argument("--ids", help="file of Message-IDs, one per line "
                                  "(default: the op's own file; required for restore)")
    ap.add_argument("--user", help="iCloud username (default: the Keychain item's account)")
    ap.add_argument("--service", default=KEYCHAIN_SERVICE, help="Keychain service name")
    ap.add_argument("--check", action="store_true",
                    help="connect, report mailbox state, change nothing")
    ap.add_argument("--dry-run", action="store_true",
                    help="resolve Message-IDs to UIDs and verify; move nothing")
    ap.add_argument("--max", type=int, default=200, help="refuse to move more than this")
    ap.add_argument("--all-copies", action=argparse.BooleanOptionalAction, default=None,
                    help="move EVERY copy when one Message-ID matches more than one message. "
                         "ON by default for trash and archive (Carl, 2026-09-01: the ID list "
                         "means the posting is confirmed logged, and every copy of that exact "
                         "email is equally confirmed; leaving one behind strands it, since "
                         "Phase A will never re-pull an ID it has already recorded). OFF for "
                         "restore, where duplicates are worth seeing before they go back. Each "
                         "copy is header-verified before it moves either way; "
                         "--no-all-copies reports AMBIGUOUS and skips.")
    args = ap.parse_args()

    e = sys.stderr
    op = OPS[args.op]
    all_copies = op["all_copies"] if args.all_copies is None else args.all_copies
    log_path = os.path.join(HERE, op["log"])
    ids_name = args.ids or op["ids"]
    if not ids_name:
        sys.exit(f"  --op {args.op} has no default ID file; pass --ids explicitly.")

    user = args.user or keychain_account(args.service)
    if not user:
        unavailable(
            f"\n  No Keychain item for service {args.service!r} — this is the one-time setup,\n"
            f"  and both steps are Carl's. Claude never sees the password.\n\n"
            f"  1. Generate an app-specific password:\n"
            f"       appleid.apple.com -> Sign-In and Security -> App-Specific Passwords\n"
            f"       (needs two-factor auth; the normal Apple ID password will not work)\n\n"
            f"  2. Store it — this prompts, so the password never touches a command line:\n\n"
            f"       security add-generic-password -U -s {args.service} -a <icloud-username> -w\n\n"
            f"     The username is the NAME of the iCloud address, not the full address.\n\n"
            f"  Then: python3 scripts/mail-imap.py --check\n")
    password = keychain(args.service, user)

    t0 = time.time()
    M, who = connect(user, password)
    del password
    print(f"\n  logged in as {who!r} in {time.time()-t0:.2f}s", file=e)
    src = find_mailbox(M, op["src"], op["src"])
    dst = find_mailbox(M, op["dst"], op["dst_fallback"])
    typ, data = M.select(f'"{src}"', readonly=(args.check or args.dry_run))
    if typ != "OK":
        M.logout(); sys.exit(f"  cannot select source mailbox {src!r}")
    count = int(data[0])
    print(f"  {args.op}: {src!r} ({count} message(s))  ->  {dst!r}", file=e)

    if args.check:
        t = time.time()
        M.uid("SEARCH", None, "HEADER", "Message-ID", '"probe-not-a-real-id"')
        print(f"  server-side SEARCH round trip: {time.time()-t:.3f}s", file=e)
        print(f"\n  Connection OK. Nothing was changed.\n", file=e)
        M.logout()
        return 0

    path = ids_name if os.path.isabs(ids_name) else os.path.join(HERE, ids_name)
    if not os.path.exists(path):
        M.logout(); sys.exit(f"  ID file not found: {path}")
    targets = []
    for line in open(path, encoding="utf-8"):
        t = line.strip()
        if t and t not in targets:
            targets.append(t)
    if len(targets) > args.max:
        M.logout(); sys.exit(f"  {len(targets)} IDs exceeds --max {args.max}.")
    print(f"  {len(targets)} target Message-ID(s) from {os.path.basename(path)}", file=e)

    # Message-ID is supposed to be unique and in this mailbox it is not: two 2015/2020
    # messages were each stored twice, same id, same date, same subject. Duplicates are
    # skipped unless --all-copies, because "move more than you found" is Carl's call.
    resolved, missing, ambiguous, mismatch = {}, [], [], []
    ts = time.time()
    for mid in targets:
        uids = search_id(M, mid)
        if not uids:
            missing.append(mid);  continue
        if len(uids) > 1 and not all_copies:
            ambiguous.append((mid, len(uids)));  continue
        good = []
        for u in uids:
            got = header_id(M, u)
            if got == mid:
                good.append(u)
            else:
                mismatch.append((mid, got))
        if good:
            resolved[mid] = good
    print(f"  resolved {len(resolved)} of {len(targets)} in {time.time()-ts:.2f}s "
          f"({(time.time()-ts)/max(1,len(targets)):.3f}s per lookup, server-side)", file=e)

    if args.dry_run:
        for mid, uids in resolved.items():
            for u in uids:
                print(f"     would move  uid {u.decode():>8}  verified  {mid}", file=e)
        for mid in missing:
            print(f"     NOT IN {src.upper():<14} {mid}", file=e)
        for mid, n in ambiguous:
            print(f"     AMBIGUOUS ({n} copies)  {mid}   — skipped; --all-copies moves them all",
                  file=e)
        for mid, got in mismatch:
            print(f"     MISMATCH  header says {got!r}  for  {mid}", file=e)
        print(f"\n  DRY RUN — nothing moved out of {src!r}. "
              f"{time.time()-t0:.2f}s total.\n", file=e)
        M.logout()
        return 1 if (ambiguous or mismatch) else 0

    moved, failed = [], []
    for mid, uids in resolved.items():
        ok_all = True
        for uid in uids:
            typ, _ = M.uid("MOVE", uid, f'"{dst}"')
            if typ != "OK":                   # servers without MOVE: COPY + \Deleted + EXPUNGE
                t1, _ = M.uid("COPY", uid, f'"{dst}"')
                if t1 == "OK":
                    M.uid("STORE", uid, "+FLAGS", "(\\Deleted)")
                    M.expunge()
                    typ = "OK"
            ok_all = ok_all and typ == "OK"
        (moved if ok_all else failed).append(mid)

    entries = ([(op["verb"], m) for m in moved] + [("FAILED", m) for m in failed]
               + [("NOT_FOUND", m) for m in missing]
               + [("AMBIGUOUS", m) for m, _ in ambiguous]
               + [("MISMATCH", m) for m, _ in mismatch])
    log(log_path, entries)
    print(f"\n  {op['verb']:<9} {len(moved)}", file=e)
    for label, items in (("FAILED", failed), ("NOT_FOUND", missing)):
        if items:
            print(f"  {label:<9} {len(items)}", file=e)
            for m in items:
                print(f"      {m}", file=e)
    if ambiguous:
        print(f"  AMBIGUOUS {len(ambiguous)}   duplicate copies, skipped — "
              f"re-run with --all-copies to move them", file=e)
        for m, n in ambiguous:
            print(f"      {m}  ({n} copies)", file=e)
    if mismatch:
        print(f"  MISMATCH  {len(mismatch)}", file=e)
        for m, got in mismatch:
            print(f"      {m}  (header said {got!r})", file=e)
    print(f"\n  {time.time()-t0:.2f}s total.\n", file=e)
    M.logout()
    return 0


if __name__ == "__main__":
    sys.exit(main())
