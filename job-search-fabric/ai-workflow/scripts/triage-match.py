#!/usr/bin/env python3
"""
triage-match.py — join triage-candidates.json to JD_Evaluation_Log.csv rows, and
render the model's classifications into a jd-update.py edit list.

Implements the mechanical half of Phase D (instructions/05-triage-and-audits.md,
"Application / rejection / interview triage"). The judgment half stays with the
model: this script never decides whether an email is a rejection, a confirmation
or an interview invitation. It finds the candidate rows, reports what is already
in them, and refuses writes that break a documented rule.

Same reasoning as jd-dedupe.py: matching 17 emails against 921 log rows is a set
operation over a 1.2 MB CSV. It does not need a language model and should not
consume one.

TWO MODES
---------

1. MATCH (default) — read scripts/triage-candidates.json, emit a match report.

       python3 scripts/triage-match.py
       python3 scripts/triage-match.py --out scratch/triage-matches.json

   The report also carries the two Job_ID-keyed sources: the LinkedIn Job Tracker
   (required) and the applied badges Phase B saw on the JD pages (optional backstop).

   For every email it reports a sender class, a parsed ISO date, the log rows it
   could plausibly be about, and the current contents of the four write-back
   fields on each of those rows (so the blank-gate outcome is visible before any
   prompt is written). Read the report, read each body, classify.

2. RENDER (--decisions FILE) — turn classifications into a validated edit list.

       python3 scripts/triage-match.py --decisions scratch/decisions.json \
                                       --out-edits scratch/triage-edits.json

   Emits edits.json for `jd-update.py --input`, the archive-ID list for
   mail-archive.applescript, the ledger additions, and the blocked list. It
   halts rather than emit anything if a decision breaks a rule below.

WHAT THE RENDER MODE REFUSES TO DO
----------------------------------
  * Write Carls_Action_Date without a `date_source`, or with a source that does
    not agree with the date. Six rows were dated with the run date on 2026-08-24
    when the real application date was in the confirmation email.
  * Accept a decision carrying more than one of message_id / tracker_job_id /
    badge_job_id. Each source validates differently; a decision answering to two
    of them answers to neither.
  * Write a badge-sourced date that the Job Tracker contradicts. The tracker reads
    LinkedIn's own application record; the badge is rendered page text, so the
    tracker wins and the decision has to be re-sourced.
  * Ledger an unresolved email. "Blocked" and "scanned" are different states; a
    ledgered-but-unresolved email is permanently invisible to future scans.
  * Archive a named individual's email (recruiter / hiring manager), a LinkedIn
    message notification, or mail that isn't job-related at all. The first still
    owes Carl a reply; the second is trashed by Phase G; the third is not this
    workflow's mail to move — it is ledgered so it is never re-read, and left in
    the Inbox.
  * Write from a forwarded LinkedIn job-alert digest without an explicit override.
  * Touch a judgment field. That is jd-update.py's rule; this just fails earlier.

A decision may pass `archive: false` to hold back a message the envelope called
automated but the body shows is a live human thread. It may never pass
`archive: true` to push one the other way.

SENDER CLASSES (mechanical, from the envelope only — never from the body)
    linkedin_message   (inmail-)hit-reply@linkedin.com — Phase G, trash, no match
    job_alert          jobalerts-noreply@linkedin.com — Phase B's input, not D's
    individual         a named human; classify and ledger, but never archive
    automated          ATS / no-reply system mail; archives normally once resolved
"""
import argparse, csv, datetime, importlib.util, json, os, re, sys, unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LOG        = os.path.join(ROOT, "JD_Evaluation_Log.csv")
CANDIDATES = os.path.join(HERE, "triage-candidates.json")
LEDGER     = os.path.join(HERE, "triaged-message-ids.json")
TRACKER    = os.path.join(HERE, "applied-tracker.json")
BADGES     = os.path.join(ROOT, "scratch", "applied-badge.json")
WRITEBACK  = os.path.join(ROOT, "scratch", "fabric_actions.csv")
STATE      = os.path.join(HERE, "phase-d-state.json")

# Reuse jd-dedupe.py's normalizer and title comparison rather than writing a second
# matcher. Both jobs are the same job — match a company/title pair with no Job_ID to
# a logged row — and two copies would drift. (The hyphen in the filename is why this
# is an importlib load and not an import statement.)
_spec = importlib.util.spec_from_file_location("jd_dedupe", os.path.join(HERE, "jd-dedupe.py"))
_dd = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_dd)
norm, title_match, TITLE_SIMILARITY = _dd.norm, _dd.title_match, _dd.TITLE_SIMILARITY

TODAY = datetime.date.today().isoformat()          # never from a prompt — 2026-08-27 incident

CARL_FIELDS = ["Carls_Action", "Carls_Action_Date", "Outcome", "Reason"]
# Shown on every candidate: the rejection workflow synthesizes `Reason` from these
# when the employer's stated reason is boilerplate.
CONTEXT_FIELDS = ["Verdict", "Score", "Comp_Flag", "Biggest_Gap", "Date_Evaluated"]

# The documented sender is inmail-hit-reply@linkedin.com. Live mail on 2026-08-25 used
# the bare hit-reply@linkedin.com for the same notification type, so match both.
LINKEDIN_MSG = re.compile(r"^(?:[\w-]+-)?hit-reply@linkedin\.com$", re.I)
JOB_ALERT    = re.compile(r"^job(?:s|alerts)-noreply@linkedin\.com$", re.I)

# Mail from these domains carries the ATS's name, not the employer's — never take a
# company match from the sender domain here.
ATS_DOMAINS = {
    "greenhouse-mail", "greenhouse-jobs", "greenhouse", "myworkday", "workday",
    "workdaysuite", "icims", "lever", "ashbyhq", "smartrecruiters", "taleo",
    "jobvite", "successfactors", "brassring", "breezy", "workable", "paylocity",
    "adp", "ukg", "dayforce", "linkedin", "amazonses", "bbnotify", "oraclecloud",
    "notifications", "notification", "sendgrid", "mailgun", "hire", "myworkdayjobs",
}

NOREPLY_LOCAL = re.compile(
    r"^(no[-_.]?reply|donot[-_.]?reply|noreply|notifications?|alerts?|mailer|bounce|"
    r"login|team|info|support|careers?|jobs|recruiting|recruitment|hr|talent\w*|"
    r"help|news|updates?|hello|contact|admin|postmaster)([-_.+].*)?$", re.I)

# Normalized company names too short or too generic to match on text alone.
COMPANY_STOP = {"ladders", "beacon", "insight", "apex", "collabera", "signature",
                "motion", "spectrum", "pinnacle", "premier", "summit", "vision"}

MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july", "august",
     "september", "october", "november", "december"], 1)}

JOBVIEW = re.compile(r"(?:jobs/view/|currentJobId=|jobId=)(\d{6,})", re.I)

# A forwarded LinkedIn job-alert digest carries its own envelope in the body. Detecting
# that is the same kind of mechanical envelope read as classify_sender() — it is NOT the
# body-meaning classification the instructions reserve for the model. Two of the 17 mails
# on 2026-08-25 were these, forwarded by a friend, and each named 4-6 unrelated companies
# that matched log rows perfectly. Annotate so the model routes them to Phase B.
FWD_ALERT = re.compile(r"forwarded message.{0,400}?jobalerts-noreply@linkedin\.com",
                       re.I | re.S)

# A tracker entry can only ever mean "Carl applied" — there is no rejection, interview or
# newsletter on the Job Tracker. Anything else is a mis-classification. The applied badge
# on the JD says exactly the same one thing, so it takes the same set.
TRACKER_CLASSIFICATIONS = {"applied", "noop", "blocked"}
BADGE_CLASSIFICATIONS   = TRACKER_CLASSIFICATIONS

CLASSIFICATIONS = {
    "applied", "rejected", "interview",       # write to the log
    "noop",                                   # matched, blank-gate declined — resolved
    "not_job_related",                        # resolved, archives normally
    "recruiter_pitch",                        # resolved for the log, stays in Inbox
    "linkedin_message",                       # Phase G — trashed, never archived
    "job_alert",                              # Phase B's input — not resolved here
    "blocked",                                # unresolved: ask Carl, do not ledger
}
WRITING = {"applied", "rejected", "interview"}
DATE_SOURCES = {"email_date_received", "job_tracker", "jd_applied_badge", "carl_confirmed"}
# jd_applied_badge added 2026-08-31: the Phase B applied-badge check
# (scratch/applied-badge.json). Match and render paths wired 2026-09-01 — see the
# "Third source" section of instructions/05-triage-and-audits.md.

# The three sources a decision may come from, and the key each one is addressed by. A
# decision carries EXACTLY ONE of these; carrying two is a halt, because the validation
# rules differ per source and a decision that answers to two of them answers to neither.
DECISION_KEYS = ("message_id", "tracker_job_id", "badge_job_id")


# ---------------------------------------------------------------- helpers

def load_writeback(path):
    """Carl's own triage decisions, read DOWN the pipe from Fabric — never written back up.

    Carl triages in the Power BI report and writes back to JobSearch_DB. That database, not
    this CSV, holds the current Carls_Action / Carls_Action_Date / Outcome / Reason for any
    row he has touched. When it already carries a value, Phase D must HONOR it and leave
    the CSV alone: writing the same fact into the CSV makes his override indistinguishable
    from a front-end pre-fill, which is what it is meant to override.

    Returns {Job_ID: {"applied": bool, "fields": {field: value}}}. The values are used ONLY
    to decide whether to suppress a write. They are never copied into an edit — that is the
    2026-08-26 incident, and it cost Carl hours.
    """
    if not os.path.exists(path):
        return None
    out = {}
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            jid = (r.get("Job_ID") or "").strip()
            if not jid:
                continue
            out[jid] = {
                "applied": str(r.get("WriteBack_Applied", "")).strip().lower() == "true",
                "fields": {k: (r.get(k) or "").strip() for k in CARL_FIELDS},
            }
    return out


def squash(s):
    """Collapse every unicode space (nbsp, narrow nbsp, en-space) to a plain one."""
    s = "".join(" " if unicodedata.category(c) == "Zs" else c for c in (s or ""))
    return re.sub(r"\s+", " ", s).strip()


def parse_date(raw):
    """'Tuesday, August 25, 2026 at 5:01:35 PM' -> '2026-08-25'. None if unparseable."""
    m = re.search(r"([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})", squash(raw))
    if not m or m.group(1).lower() not in MONTHS:
        return None
    try:
        return datetime.date(int(m.group(3)), MONTHS[m.group(1).lower()],
                             int(m.group(2))).isoformat()
    except ValueError:
        return None


def split_sender(sender):
    """-> (display name, email address, domain-label list)."""
    s = squash(sender)
    m = re.search(r"<([^>]+)>", s)
    addr = (m.group(1) if m else s).strip().strip('"')
    display = (s[:m.start()] if m else "").strip().strip('"').strip()
    domain = addr.split("@")[-1].lower() if "@" in addr else ""
    return display, addr.lower(), domain.split(".")


def classify_sender(display, addr, labels):
    if LINKEDIN_MSG.match(addr):
        return "linkedin_message"
    if JOB_ALERT.match(addr):
        return "job_alert"
    local = addr.split("@")[0]
    if NOREPLY_LOCAL.match(local):
        return "automated"
    # A named human: two or more capitalized name tokens in the display name.
    if len(re.findall(r"\b[A-Z][a-z]{1,}\b", display)) >= 2:
        return "individual"
    return "automated"


def contains_tokens(hay_tokens, needle_tokens):
    """Is needle a contiguous run inside hay? Token-wise, so 'idr' never hits 'idris'."""
    n = len(needle_tokens)
    if not n or n > len(hay_tokens):
        return False
    return any(hay_tokens[i:i + n] == needle_tokens
               for i in range(len(hay_tokens) - n + 1))


def best_window(hay_tokens, needle_tokens):
    """Best title similarity over same-length windows of the haystack."""
    n = len(needle_tokens)
    if not n or not hay_tokens:
        return 0.0
    needle = " ".join(needle_tokens)
    best = 0.0
    for width in {max(1, n - 1), n, n + 1}:
        if width > len(hay_tokens):
            continue
        for i in range(len(hay_tokens) - width + 1):
            best = max(best, title_match(needle, " ".join(hay_tokens[i:i + width])))
            if best == 1.0:
                return 1.0
    return best


def load_log():
    with open(LOG, newline="") as f:
        rdr = csv.DictReader(f)
        rows = list(rdr)
        header = rdr.fieldnames
    bad = [n for n, r in enumerate(rows, 2) if len(r) != len(header) or None in r.values()]
    if bad:
        sys.exit(f"Log has {len(bad)} malformed row(s), first at line {bad[0]}.")
    return rows, header


def strength_of(why, sim, where):
    """How much evidence stands behind a candidate.

    'weak' exists because a company name in a body is nearly free: a recruiter naming
    Carl's former employer (Company-59, 2026-08-25) and a forwarded alert digest listing
    six companies both produce perfect company matches with no title support. Those are
    honest matches to report and terrible matches to act on.
    """
    if why == "job_id_in_body":
        return "job_id"
    if sim >= TITLE_SIMILARITY and why in ("company:subject", "company:sender_domain"):
        return "strong"
    if why == "company:partial":
        return "moderate"
    if sim >= TITLE_SIMILARITY:
        return "moderate"
    return "weak"


WB = {"map": None}          # populated once per run by match()/render()


def wb_view(jid):
    """What Fabric already holds for this row, if anything."""
    if WB["map"] is None:
        return None
    w = WB["map"].get(jid)
    if not w or not w["applied"]:
        return {"carls_writeback": False}
    held = {f: v for f, v in w["fields"].items() if v}
    return {"carls_writeback": True, "fields_held": held,
            "note": "Carl triaged this in the report. HONOR these; do not write them to the CSV."}


def row_view(line, row, why, sim, where):
    v = {"line": line, "Job_ID": (row.get("Job_ID") or "").strip(),
         "Company": row.get("Company"), "Role_Title": row.get("Role_Title"),
         "matched_by": why, "title_similarity": round(sim, 3), "title_seen_in": where,
         "strength": strength_of(why, sim, where)}
    v["current"] = {f: (row.get(f) or "").strip() for f in CARL_FIELDS}
    v["blank_gate"] = {f: ("blank" if not v["current"][f] else "populated")
                       for f in CARL_FIELDS}
    v["context"] = {f: (row.get(f) or "").strip() for f in CONTEXT_FIELDS}
    v["writeback"] = wb_view(v["Job_ID"])
    return v


# ---------------------------------------------------------------- match mode

def rel(path):
    """Path relative to the folder, or absolute when it lives outside it."""
    r = os.path.relpath(path, ROOT)
    return path if r.startswith("..") else r


def attach_row_state(rec, jid, by_id):
    """Join an applied-source entry (tracker or badge) to its log row, in place.

    Both sources ask the log the same four questions — is there a row, what do Carl's
    columns already hold, is the blank gate open, and does Fabric hold a write-back for
    it — so they share one answer. Two copies of this would drift, and the drift would be
    invisible until a badge wrote over a write-back the tracker path would have honored.
    """
    hit = by_id.get(jid)
    if hit:
        line, row = hit
        rec["matched"] = True
        rec["line"] = line
        rec["Company"] = row.get("Company")
        rec["Role_Title"] = row.get("Role_Title")
        rec["current"] = {f: (row.get(f) or "").strip() for f in CARL_FIELDS}
        rec["blank_gate"] = {f: ("blank" if not rec["current"][f] else "populated")
                             for f in CARL_FIELDS}
        rec["context"] = {f: (row.get(f) or "").strip() for f in CONTEXT_FIELDS}
        rec["writeback"] = wb_view(jid)
        wbf = (rec["writeback"] or {}).get("fields_held") or {}
        rec["state"] = ("carl_writeback"
                        if wbf.get("Carls_Action") else
                        "already_applied"
                        if rec["current"]["Carls_Action"] == "Applied" else
                        "action_populated"
                        if rec["current"]["Carls_Action"] else "writable")
    else:
        # Applied outside this workflow, or the posting was never evaluated. Step 1
        # wins: ask Carl for the URL/Job_ID, never append a row with a blank one.
        rec["matched"] = False
        rec["state"] = "no_log_row"
    return rec


def match_tracker(args, by_id):
    """Reconcile LinkedIn's Job Tracker against the log. Exact Job_ID, no guessing.

    The second source for Phase D's applied-to pipeline, and the better-identified one:
    every tracker entry carries a real /jobs/view/<id> link, so this is a dictionary
    lookup where the email path has to normalize a company name and hope. It also finds
    applications that produced no confirmation email at all (verified 2026-08-08).
    """
    skipped = require_tracker(args)
    if skipped:
        return skipped
    data = json.load(open(args.tracker))

    entries = []
    for e in data.get("entries", []):
        jid = str(e.get("job_id") or "").strip()
        rec = {"Job_ID": jid, "url": e.get("url"), "headline": e.get("headline"),
               "location": e.get("location"),
               "applied_date": e.get("applied_date"),
               "applied_relative": e.get("applied_relative"),
               "applied_date_is_approximate": e.get("applied_date_is_approximate")}
        attach_row_state(rec, jid, by_id)
        entries.append(rec)

    counts = {}
    for r in entries:
        counts[r["state"]] = counts.get(r["state"], 0) + 1
    coverage = check_tracker_gap(data.get("entries", []))
    record_tracker_read()
    return {"available": True, "scrapedAt": data.get("scrapedAt"),
            "first_page_only": data.get("firstPageOnly"),
            "coverage": coverage,
            "entries": entries, "counts": {"entries": len(entries), "by_state": counts}}


def match_badge(args, by_id, tracker):
    """Reconcile the applied badges Phase B saw on the JD pages themselves.

    The THIRD source, and deliberately the weakest — instructions/05-triage-and-audits.md,
    "Third source". It only ever sees postings Phase B actually fetched, i.e. the post-dedupe
    new set, which is exactly the population an applied-to role tends not to be in. It is a
    backstop, not coverage, and it never reduces the tracker's job: a missing badge file is a
    note, a missing tracker is still a halt.

    Every entry is reported with its tracker overlap, because the tracker wins on date and the
    model needs to see the disagreement before it writes anything.
    """
    where = rel(args.badges)
    if not os.path.exists(args.badges):
        return {"available": False,
                "note": (f"{where} not found. Optional — it exists only when Phase B fetched "
                         f"bodies this run (`python3 scripts/applied-badge-scan.py`).")}
    data = json.load(open(args.badges))
    if not isinstance(data, list):
        return {"available": False, "note": f"{where} is not a JSON list of badge records."}

    t_by_id = {}
    if tracker.get("available"):
        t_by_id = {e["Job_ID"]: e for e in tracker.get("entries", []) if e.get("Job_ID")}

    entries = []
    for b in data:
        jid = str(b.get("job_id") or "").strip()
        rec = {"Job_ID": jid, "url": b.get("url"), "badge_text": b.get("badge_text"),
               "applied_date": b.get("applied_date"),
               "applied_date_is_approximate": b.get("applied_date_is_approximate"),
               "observed_at": b.get("observed_at")}
        attach_row_state(rec, jid, by_id)
        t = t_by_id.get(jid)
        if t is None:
            rec["tracker"] = None
        else:
            rec["tracker"] = {"applied_date": t.get("applied_date"),
                              "agrees": t.get("applied_date") == rec["applied_date"]}
            if not rec["tracker"]["agrees"]:
                rec["note"] = (f"tracker says {t.get('applied_date')}, badge says "
                               f"{rec['applied_date']} — the tracker wins; write this row "
                               f"from the tracker source, not the badge.")
        entries.append(rec)

    counts = {}
    for r in entries:
        counts[r["state"]] = counts.get(r["state"], 0) + 1
    covered = sum(1 for r in entries if r["tracker"] is not None)
    return {"available": True, "source": where, "entries": entries,
            "counts": {"entries": len(entries), "by_state": counts,
                       "also_in_tracker": covered,
                       "badge_only": len(entries) - covered}}


def require_tracker(args):
    """The Job Tracker is a required step, not an optional one.

    It was dropped from the revamp's first pass precisely because nothing enforced it, and
    the live run then showed it catching three applications the mail path cannot see —
    including one with no confirmation email in existence. A run without it is half a run,
    so a missing, stale or halted fetch stops the process rather than printing a note.

    A halted fetch counts as NOT read. HALT_EXPIRED means the LinkedIn session aged out and
    the tracker was never loaded; treating that as "no new applications" would be a silent
    false negative of exactly the kind this step exists to prevent.
    """
    rel = os.path.relpath(args.tracker, ROOT)
    problem = None
    if args.skip_tracker:
        print(f"  WARNING: --skip-tracker. The Job Tracker was NOT reconciled this run; any "
              f"application without a confirmation email is invisible.", file=sys.stderr)
        return {"available": False, "skipped": True,
                "note": "explicitly skipped with --skip-tracker"}
    if not os.path.exists(args.tracker):
        problem = (f"{rel} not found. Run `node scripts/fetch-applied-tracker.js` — the Job "
                   f"Tracker is a required Phase D source, not an optional one.")
    else:
        data = json.load(open(args.tracker))
        age = (datetime.date.today()
               - datetime.date.fromtimestamp(os.path.getmtime(args.tracker))).days
        if data.get("halted"):
            h = data["halted"]
            problem = (f"{rel} records a halted fetch ({h.get('kind')}). A halt is not an "
                       f"empty tracker — nothing was read. "
                       + ("Re-run `node scripts/save-auth.js`, then re-fetch."
                          if h.get("kind") == "HALT_EXPIRED" else
                          "Do NOT re-auth and retry; report to Carl."))
        elif age > 0:
            problem = (f"{rel} is {age} day(s) old. Re-run "
                       f"`node scripts/fetch-applied-tracker.js` — a stale tracker misses "
                       f"every application made since it was scraped.")
    if problem:
        sys.exit(f"\n  HALT: {problem}\n  (--skip-tracker overrides, deliberately.)\n")
    return None


def check_tracker_gap(entries):
    """Warn when skipped runs may have pushed applications off page 1.

    fetch-applied-tracker.js reads page 1 only (~10 entries) by design. That is ample for a
    daily run and silently lossy for a gap: if the OLDEST entry on page 1 is newer than the
    last run, everything between the two is gone from this source. Nothing else in the
    workflow would ever notice.
    """
    dates = sorted(d for d in (e.get("applied_date") for e in entries) if d)
    if not dates:
        return None
    span = {"oldest": dates[0], "newest": dates[-1], "entries": len(entries)}
    prev = None
    if os.path.exists(STATE):
        try:
            prev = json.load(open(STATE)).get("last_tracker_read")
        except Exception:
            prev = None
    span["last_tracker_read"] = prev
    if prev and dates[0] > prev:
        span["gap_warning"] = (
            f"Page 1 reaches back only to {dates[0]}, but the last tracker read was {prev}. "
            f"Applications between those dates have scrolled off page 1 and this source "
            f"cannot see them. Use fetch-applied-tracker-paginated.js (Carl's say-so "
            f"required) to recover them.")
    return span


def record_tracker_read():
    prev = {}
    if os.path.exists(STATE):
        try:
            prev = json.load(open(STATE))
        except Exception:
            prev = {}
    prev["last_tracker_read"] = TODAY
    with open(STATE, "w") as f:
        json.dump(prev, f, indent=1)


def pull_age_minutes(path):
    """Age of the Fabric pull in whole minutes, from its mtime."""
    delta = datetime.datetime.now() - datetime.datetime.fromtimestamp(os.path.getmtime(path))
    return int(delta.total_seconds() // 60)


def require_writeback(args, writing):
    """Load Fabric's write-back state. Refuse to render writes without a current one.

    The pull is ONE PER RUN, not one per day (Carl, 2026-08-28). It carries his write-backs,
    and he can write one back at any hour: a pull taken at 08:00 knows nothing about a
    write-back he made at noon, so a 16:00 run against it would overwrite that decision in
    the CSV with a blank. The original guard compared calendar dates and passed all day,
    catching only the stale-overnight case.

    So the check is an age in MINUTES, wide enough that one pull at the start of a run covers
    every step of that run (do not re-pull between steps), and narrow enough that yesterday's
    pull — or this morning's, used in the afternoon — stops the run.
    """
    WB["map"] = load_writeback(args.writeback)
    rel = os.path.relpath(args.writeback, ROOT)
    if WB["map"] is None:
        msg = (f"{rel} not found. Run `python3 scripts/fabric-pull-actions.py` first — "
               f"Phase D must know which rows Carl has already triaged in the report.")
    else:
        age = pull_age_minutes(args.writeback)
        if age > args.max_pull_age_minutes:
            msg = (f"{rel} is {age} minute(s) old (limit {args.max_pull_age_minutes}). "
                   f"Re-run `python3 scripts/fabric-pull-actions.py` — the pull is once per "
                   f"run, not once per day. A pull this old can miss a write-back Carl made "
                   f"since, and Phase D would overwrite his decision with a blank.")
        else:
            print(f"  write-back    {len(WB['map'])} row(s) from {rel} "
                  f"({age} min old)", file=sys.stderr)
            return
    if writing and not args.skip_writeback_check:
        sys.exit(f"\n  HALT: {msg}\n  (--skip-writeback-check overrides, deliberately.)\n")
    print(f"  WARNING: {msg}", file=sys.stderr)


def match(args):
    require_writeback(args, writing=False)
    with open(args.candidates) as f:
        emails = json.load(f)
    rows, _ = load_log()
    ledger = set(json.load(open(LEDGER))) if os.path.exists(LEDGER) else set()

    by_id, by_company = {}, {}
    for n, r in enumerate(rows, 2):
        jid = (r.get("Job_ID") or "").strip()
        if jid:
            by_id[jid] = (n, r)
        c = norm(r.get("Company"))
        if c:
            by_company.setdefault(c, []).append((n, r))
    companies = sorted(by_company, key=len, reverse=True)

    out = []
    for e in emails:
        mid = e.get("message_id", "")
        display, addr, labels = split_sender(e.get("sender", ""))
        cls = classify_sender(display, addr, labels)
        subject, body = squash(e.get("subject")), squash(e.get("body"))

        rec = {"message_id": mid, "sender": e.get("sender"), "sender_display": display,
               "sender_address": addr, "sender_class": cls, "subject": e.get("subject"),
               "date_received": e.get("date_received"),
               "date_received_iso": parse_date(e.get("date_received")),
               "already_ledgered": mid in ledger,
               "archive_exempt": cls in ("individual", "linkedin_message")}

        # Phase G and Phase B mail is not Phase D's to match. Report and move on.
        if cls in ("linkedin_message", "job_alert"):
            rec["match_state"] = "not_phase_d"
            rec["candidates"] = []
            rec["note"] = ("LinkedIn message notification — trash per Phase G.6, never match"
                           if cls == "linkedin_message"
                           else "Job-alert digest — Phase B's input, not a triage candidate")
            out.append(rec)
            continue

        if FWD_ALERT.search(body):
            rec["content_signal"] = "forwarded_linkedin_job_alert"
            rec["note"] = ("Body is a forwarded LinkedIn job-alert digest. Its company/title "
                           "matches below are the digest's other listings, not something Carl "
                           "applied to. Route the postings to Phase B; this is not a Phase D "
                           "write.")

        subj_t, body_t = norm(subject).split(), norm(body).split()
        hay_t = subj_t + body_t
        dom_t = [norm(l) for l in labels if norm(l) and norm(l) not in ATS_DOMAINS]

        cands, seen = [], set()

        # 1. A Job_ID in the body beats every heuristic below it.
        for jid in dict.fromkeys(JOBVIEW.findall(e.get("body") or "")):
            if jid in by_id:
                line, row = by_id[jid]
                cands.append(row_view(line, row, "job_id_in_body", 1.0, "body"))
                seen.add(line)

        # 2. Otherwise: normalized company present in the mail, then title similarity.
        for c in companies:
            if len(c) < 3 or c in COMPANY_STOP:
                continue
            ct = c.split()
            where_c = ("sender_domain" if any(contains_tokens(d.split(), ct) or d == c
                                              for d in dom_t)
                       else "subject" if contains_tokens(subj_t, ct)
                       else "body" if contains_tokens(body_t, ct)
                       else None)
            partial = False
            if not where_c and len(ct) > 1 and len(ct[0]) >= 5:
                head = [ct[0]]
                if (any(head[0] in d for d in dom_t) or contains_tokens(subj_t, head)
                        or contains_tokens(body_t, head)):
                    where_c, partial = "partial", True
            if not where_c:
                continue
            for line, row in by_company[c]:
                if line in seen:
                    continue
                t = norm(row.get("Role_Title")).split()
                s_sub, s_body = best_window(subj_t, t), best_window(body_t, t)
                sim, where_t = ((s_sub, "subject") if s_sub >= s_body else (s_body, "body"))
                # A short-form company name on its own proves nothing; require the title.
                if partial and sim < TITLE_SIMILARITY:
                    continue
                cands.append(row_view(line, row, f"company:{where_c}", sim, where_t))
                seen.add(line)

        ids = [c for c in cands if c["strength"] == "job_id"]
        exact = [c for c in cands if c["title_similarity"] >= 1.0
                 and c["title_seen_in"] == "subject"]
        titled = [c for c in cands if c["title_similarity"] >= TITLE_SIMILARITY]
        if ids:
            rec["match_state"] = "job_id"
        elif len(exact) == 1:
            # Nightingale posted "Solutions Architect I/II" and "III/IV" and mailed a
            # confirmation for each; both titles are 0.9+ similar to each other, so a
            # plain similarity test calls both mails ambiguous. An exact subject hit
            # with exactly one claimant is not a guess.
            rec["match_state"] = "unique_exact"
        elif len(titled) == 1:
            rec["match_state"] = "unique"
        elif len(titled) > 1:
            rec["match_state"] = "ambiguous"
        elif cands:
            rec["match_state"] = "company_only"
        else:
            rec["match_state"] = "none"

        RANK = {"job_id": 0, "strong": 1, "moderate": 2, "weak": 3}
        cands.sort(key=lambda c: (RANK[c["strength"]], -c["title_similarity"]))
        # Cap weak candidates per company: four Company-59 rows all matched on the same
        # incidental body mention and said the same thing four times.
        kept, per_company = [], {}
        for c in cands:
            if c["strength"] == "weak":
                k = norm(c["Company"])
                per_company[k] = per_company.get(k, 0) + 1
                if per_company[k] > 2:
                    continue
            kept.append(c)
        rec["candidates"] = kept[:args.max_candidates]
        rec["candidates_truncated"] = len(kept) > args.max_candidates
        rec["weak_candidates_suppressed"] = len(cands) - len(kept)
        b = e.get("body") or ""
        rec["body"] = b[:args.max_body]
        rec["body_truncated"] = len(b) > args.max_body
        out.append(rec)

    counts = {}
    for r in out:
        counts[f"{r['sender_class']}/{r['match_state']}"] = \
            counts.get(f"{r['sender_class']}/{r['match_state']}", 0) + 1
    tracker = match_tracker(args, by_id)
    badges  = match_badge(args, by_id, tracker)
    report = {"generated": TODAY, "source": os.path.basename(args.candidates),
              "emails": out, "tracker": tracker, "badges": badges,
              "counts": {"emails": len(out), "by_class_and_state": counts,
                         "needs_classification": sum(
                             1 for r in out if r["sender_class"] not in
                             ("linkedin_message", "job_alert")),
                         "already_ledgered": sum(1 for r in out if r["already_ledgered"]),
                         "undated": sum(1 for r in out if not r["date_received_iso"])}}

    e_ = sys.stderr
    print(f"\n  {len(out)} email(s) from {os.path.basename(args.candidates)}\n", file=e_)
    for r in out:
        flag = "L" if r["already_ledgered"] else " "
        print(f"  {flag} [{r['sender_class']:<16} {r['match_state']:<12}] "
              f"{(r['date_received_iso'] or '????-??-??')}  {(r['subject'] or '')[:58]}",
              file=e_)
        if r.get("content_signal"):
            print(f"        !! {r['content_signal']}", file=e_)
        for c in r["candidates"]:
            if c["strength"] == "weak":
                print(f"        ~  {c['Job_ID']:>12} sim {c['title_similarity']:.2f} weak "
                      f"{c['Company'][:22]:24s} {c['Role_Title'][:34]}", file=e_)
                continue
            gate = ",".join(f"{f.split('_')[-1]}={c['current'][f] or '-'}"
                            for f in CARL_FIELDS)
            print(f"        -> {c['Job_ID']:>12} sim {c['title_similarity']:.2f} "
                  f"{c['strength']:<8} {c['matched_by']:<18} {c['Company'][:22]:24s} "
                  f"{c['Role_Title'][:34]:36s} [{gate}]", file=e_)
        if r.get("weak_candidates_suppressed"):
            print(f"        ~  (+{r['weak_candidates_suppressed']} more weak, suppressed)",
                  file=e_)
    if any(not r["date_received_iso"] for r in out):
        print("\n  WARNING: some emails have an unparseable date — an 'Applied' write "
              "cannot be dated from them.", file=e_)
    print(f"\n  needs classification: {report['counts']['needs_classification']}", file=e_)

    if not tracker.get("available"):
        print(f"\n  JOB TRACKER: {tracker.get('note')}\n", file=e_)
    else:
        cov = tracker.get("coverage") or {}
        if cov.get("oldest"):
            print(f"\n  tracker page 1 covers {cov['oldest']} .. {cov['newest']} "
                  f"({cov['entries']} entries)", file=e_)
        if cov.get("gap_warning"):
            print(f"\n  *** TRACKER GAP: {cov['gap_warning']}", file=e_)
        print(f"\n  JOB TRACKER ({tracker['counts']['entries']} entries, page 1, "
              f"scraped {(tracker.get('scrapedAt') or '')[:10]})", file=e_)
        for t in tracker["entries"]:
            approx = "~" if t.get("applied_date_is_approximate") else " "
            if t["matched"]:
                gate = ",".join(f"{f.split('_')[-1]}={t['current'][f] or '-'}"
                                for f in CARL_FIELDS)
                print(f"     {approx}{t['applied_date'] or '????-??-??'} {t['Job_ID']:>12} "
                      f"{t['state']:<16} {(t['Company'] or '')[:22]:24s} "
                      f"{(t['Role_Title'] or '')[:32]:34s} [{gate}]", file=e_)
            else:
                print(f"     {approx}{t['applied_date'] or '????-??-??'} {t['Job_ID']:>12} "
                      f"NO LOG ROW       {(t['headline'] or '')[:58]}", file=e_)
                print(f"                               {t['url']}", file=e_)
        print(f"\n     ~ = date is a whole-day approximation, +/-1 day. It may only be "
              f"written\n       after Carl confirms it (date_source: carl_confirmed).\n",
              file=e_)

    if not badges.get("available"):
        print(f"  APPLIED BADGES: {badges.get('note')}\n", file=e_)
    else:
        bc = badges["counts"]
        print(f"  APPLIED BADGES ({bc['entries']} entr(y/ies) from {badges['source']}; "
              f"{bc['also_in_tracker']} also on the tracker, {bc['badge_only']} badge-only)",
              file=e_)
        for b in badges["entries"]:
            approx = "~" if b.get("applied_date_is_approximate") else " "
            if b["matched"]:
                gate = ",".join(f"{f.split('_')[-1]}={b['current'][f] or '-'}"
                                for f in CARL_FIELDS)
                print(f"     {approx}{b['applied_date'] or '????-??-??'} {b['Job_ID']:>12} "
                      f"{b['state']:<16} {(b['Company'] or '')[:22]:24s} "
                      f"{(b['Role_Title'] or '')[:32]:34s} [{gate}]", file=e_)
            else:
                print(f"     {approx}{b['applied_date'] or '????-??-??'} {b['Job_ID']:>12} "
                      f"NO LOG ROW       {b['url']}", file=e_)
            if b["tracker"] is None:
                print(f"                               badge-only — the tracker did not "
                      f"see this one", file=e_)
            elif not b["tracker"]["agrees"]:
                print(f"        *** {b['note']}", file=e_)
        print(f"\n     Backstop source, ranked last. It sees only what Phase B fetched, so "
              f"it is\n     never coverage — the Job Tracker stays required.\n", file=e_)

    dump(report, args.out)


# ---------------------------------------------------------------- render mode

def render(args):
    decisions = json.load(open(args.decisions))
    if not isinstance(decisions, list) or not decisions:
        sys.exit("--decisions must be a non-empty JSON list.")
    require_tracker(args)
    require_writeback(args, writing=True)
    with open(args.candidates) as f:
        emails = {e["message_id"]: e for e in json.load(f)}
    tracker_entries = {}
    if os.path.exists(args.tracker):
        td = json.load(open(args.tracker))
        tracker_entries = {str(e.get("job_id")): e for e in td.get("entries", [])}
    badge_entries = {}
    if os.path.exists(args.badges):
        bd = json.load(open(args.badges))
        if isinstance(bd, list):
            badge_entries = {str(b.get("job_id")): b for b in bd}
    rows, header = load_log()
    by_id = {(r.get("Job_ID") or "").strip(): r for r in rows if (r.get("Job_ID") or "").strip()}

    edits, archive, ledger_add, blocked, halts = [], [], [], [], []
    to_phase_b, phase_ac = [], []

    for d in decisions:
        mid = d.get("message_id")
        cls = d.get("classification")
        tjid = str(d.get("tracker_job_id") or "").strip()
        bjid = str(d.get("badge_job_id") or "").strip()

        # One source per decision. With three of them the pairwise check the tracker branch
        # used stops scaling, so name every key present and refuse if it is not exactly one.
        present = [k for k in DECISION_KEYS if str(d.get(k) or "").strip()]
        if len(present) > 1:
            halts.append(f"{'/'.join(present)}: a decision carries exactly one of "
                         f"{list(DECISION_KEYS)}, not {present}.")
            continue

        # --- badge-sourced decisions --------------------------------------------------
        if bjid:
            where = f"badge/{bjid}"
            entry = badge_entries.get(bjid)
            if entry is None:
                halts.append(f"{where}: not in {rel(args.badges)}. Re-run "
                             f"`python3 scripts/applied-badge-scan.py` or drop the decision.")
                continue
            if cls not in BADGE_CLASSIFICATIONS:
                halts.append(f"{where}: classification {cls!r} is impossible for an applied "
                             f"badge — the badge only records that Carl applied. Use one of "
                             f"{sorted(BADGE_CLASSIFICATIONS)}.")
                continue
            if cls == "blocked":
                blocked.append({"badge_job_id": bjid, "url": entry.get("url"),
                                "headline": entry.get("badge_text"),
                                "ask": d.get("ask") or "(no question recorded)"})
                continue
            if cls == "noop":
                continue
            setmap = d.get("set") or {}
            if bjid not in by_id:
                halts.append(f"{where}: no log row. Ask Carl for the URL/Job_ID and append "
                             f"it properly — never write a badge sighting into a row that "
                             f"does not exist.")
                continue
            if not setmap:
                halts.append(f"{where}: classification 'applied' with an empty 'set'.")
                continue
            adate = str(setmap.get("Carls_Action_Date") or "").strip()
            if not adate:
                halts.append(f"{where}: sets Carls_Action without Carls_Action_Date.")
                continue
            src = d.get("date_source")
            if src not in ("jd_applied_badge", "carl_confirmed"):
                halts.append(f"{where}: badge writes need date_source 'jd_applied_badge' or "
                             f"'carl_confirmed', not {src!r}.")
                continue
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", adate) or adate > TODAY:
                halts.append(f"{where}: Carls_Action_Date {adate!r} is not a past ISO date.")
                continue
            if str(d.get("badge_date") or "").strip() != adate:
                halts.append(f"{where}: badge_date {d.get('badge_date')!r} must be recorded "
                             f"and must equal Carls_Action_Date {adate!r}.")
                continue
            # Same rule as the tracker: LinkedIn's relative stamp in whole days is +/-1 day,
            # and an approximation is Carl's to confirm. In practice this catches nearly every
            # badge — the page never gives a badge an exact timestamp.
            if entry.get("applied_date_is_approximate") and src != "carl_confirmed":
                halts.append(f"{where}: {entry.get('badge_text')!r} resolves to an approximate "
                             f"date (+/-1 day). Surface it and use date_source: "
                             f"carl_confirmed once Carl confirms.")
                continue
            if adate != entry.get("applied_date") and src != "carl_confirmed":
                halts.append(f"{where}: {adate!r} disagrees with the badge's computed "
                             f"{entry.get('applied_date')!r}.")
                continue
            # Ranked last on purpose. If the tracker saw this posting too and dates it
            # differently, the tracker wins (05, "Third source") — and the decision has to
            # be re-sourced rather than silently re-dated here.
            t = tracker_entries.get(bjid)
            if t and t.get("applied_date") and t["applied_date"] != adate:
                halts.append(f"{where}: the Job Tracker dates this posting "
                             f"{t['applied_date']!r} and this badge decision writes {adate!r}. "
                             f"The tracker wins — re-issue the decision with "
                             f"tracker_job_id/date_source: job_tracker.")
                continue
            edits.append({"Job_ID": bjid, "set": setmap,
                          "why": d.get("why") or f"Phase D badge applied, {bjid}"})
            continue

        # --- tracker-sourced decisions ------------------------------------------------
        if tjid:
            where = f"tracker/{tjid}"
            entry = tracker_entries.get(tjid)
            if entry is None:
                halts.append(f"{where}: not in {os.path.basename(args.tracker)}.")
                continue
            if cls not in TRACKER_CLASSIFICATIONS:
                halts.append(f"{where}: classification {cls!r} is impossible for a tracker "
                             f"entry — the Job Tracker only records that Carl applied. "
                             f"Use one of {sorted(TRACKER_CLASSIFICATIONS)}.")
                continue
            if cls == "blocked":
                blocked.append({"tracker_job_id": tjid, "url": entry.get("url"),
                                "headline": entry.get("headline"),
                                "ask": d.get("ask") or "(no question recorded)"})
                continue
            if cls == "noop":
                continue
            setmap = d.get("set") or {}
            if tjid not in by_id:
                halts.append(f"{where}: no log row. Ask Carl for the URL/Job_ID and append "
                             f"it properly — never write a tracker entry into a row that "
                             f"does not exist.")
                continue
            if not setmap:
                halts.append(f"{where}: classification 'applied' with an empty 'set'.")
                continue
            adate = str(setmap.get("Carls_Action_Date") or "").strip()
            if not adate:
                halts.append(f"{where}: sets Carls_Action without Carls_Action_Date.")
                continue
            src = d.get("date_source")
            if src not in ("job_tracker", "carl_confirmed"):
                halts.append(f"{where}: tracker writes need date_source 'job_tracker' or "
                             f"'carl_confirmed', not {src!r}.")
                continue
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", adate) or adate > TODAY:
                halts.append(f"{where}: Carls_Action_Date {adate!r} is not a past ISO date.")
                continue
            if str(d.get("tracker_date") or "").strip() != adate:
                halts.append(f"{where}: tracker_date {d.get('tracker_date')!r} must be "
                             f"recorded and must equal Carls_Action_Date {adate!r}.")
                continue
            # LinkedIn only exposes relative stamps; anything reported in whole days is
            # +/-1 day. An approximation is Carl's to confirm, never ours to write.
            if entry.get("applied_date_is_approximate") and src != "carl_confirmed":
                halts.append(f"{where}: {entry.get('applied_relative')!r} resolves to an "
                             f"approximate date (+/-1 day). Surface it and use "
                             f"date_source: carl_confirmed once Carl confirms.")
                continue
            if adate != entry.get("applied_date") and src != "carl_confirmed":
                halts.append(f"{where}: {adate!r} disagrees with the tracker's computed "
                             f"{entry.get('applied_date')!r}.")
                continue
            edits.append({"Job_ID": tjid, "set": setmap,
                          "why": d.get("why") or f"Phase D tracker applied, {tjid}"})
            continue

        # --- email-sourced decisions --------------------------------------------------
        where = f"{mid or '<no message_id>'}"
        if mid not in emails:
            halts.append(f"{where}: not in {os.path.basename(args.candidates)}.")
            continue
        if cls not in CLASSIFICATIONS:
            halts.append(f"{where}: classification {cls!r} not one of "
                         f"{sorted(CLASSIFICATIONS)}.")
            continue

        email = emails[mid]
        display, addr, _ = split_sender(email.get("sender", ""))
        sender_class = classify_sender(display, addr, _)
        email_date = parse_date(email.get("date_received"))

        if cls == "blocked":
            blocked.append({"message_id": mid, "subject": email.get("subject"),
                            "sender": email.get("sender"),
                            "ask": d.get("ask") or "(no question recorded)"})
            continue

        setmap = d.get("set") or {}
        if cls in WRITING and FWD_ALERT.search(squash(email.get("body"))) \
                and not d.get("override_signal"):
            halts.append(f"{where}: writes to the log, but the body is a forwarded LinkedIn "
                         f"job-alert digest — its company/title matches are the digest's other "
                         f"listings. If Carl really applied via this mail, set "
                         f"override_signal: true and say why.")
            continue
        if cls in WRITING:
            jid = str(d.get("Job_ID") or "").strip()
            if not jid:
                halts.append(f"{where}: classification {cls!r} writes to the log but "
                             f"carries no Job_ID. Ask Carl — never append a blank one.")
                continue
            if jid not in by_id:
                halts.append(f"{where}: Job_ID {jid} is not in the log. jd-update.py "
                             f"never creates rows; this is an ask-Carl case.")
                continue
            if not setmap:
                halts.append(f"{where}: classification {cls!r} with an empty 'set'.")
                continue

            # The 2026-08-24 incident: six rows stamped with the run date.
            adate = str(setmap.get("Carls_Action_Date") or "").strip()
            if adate:
                src = d.get("date_source")
                if src not in DATE_SOURCES:
                    halts.append(f"{where}: Carls_Action_Date {adate!r} has no valid "
                                 f"date_source (need one of {sorted(DATE_SOURCES)}).")
                    continue
                if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", adate):
                    halts.append(f"{where}: Carls_Action_Date {adate!r} is not ISO.")
                    continue
                if adate > TODAY:
                    halts.append(f"{where}: Carls_Action_Date {adate!r} is in the future.")
                    continue
                if src == "email_date_received" and adate != email_date:
                    halts.append(f"{where}: date_source=email_date_received but "
                                 f"{adate!r} != the email's date {email_date!r}.")
                    continue
                if src == "job_tracker" and not d.get("tracker_date"):
                    halts.append(f"{where}: date_source=job_tracker needs the scraped "
                                 f"tracker_date recorded alongside it.")
                    continue
            elif setmap.get("Carls_Action"):
                halts.append(f"{where}: sets Carls_Action without Carls_Action_Date.")
                continue

            edits.append({"Job_ID": jid, "set": setmap,
                          "why": d.get("why") or f"Phase D {cls}, {mid}"})

        # A job-alert digest is somebody else's input, but which body's depends on how it
        # arrived. LinkedIn's own digest was already pulled by Phase A and gets trashed by
        # Phase C, so Phase D neither resolves nor ledgers it — it simply leaves the Inbox.
        # A digest a friend forwarded was never pulled by anything: its postings have to be
        # routed to Phase B, and it must be ledgered afterwards or it resurfaces every run.
        forwarded = bool(FWD_ALERT.search(squash(email.get("body"))))
        resolved = cls != "job_alert"
        if cls == "job_alert":
            if sender_class == "job_alert" and not forwarded:
                phase_ac.append({"message_id": mid, "subject": email.get("subject")})
            else:
                to_phase_b.append({"message_id": mid, "subject": email.get("subject"),
                                   "sender": email.get("sender"),
                                   "note": "forwarded digest — extract its postings for "
                                           "Phase B, then ledger this ID"})
                resolved = True
        if resolved:
            ledger_add.append(mid)
        # Archiving: automated system mail only. A named individual still owes a reply;
        # a LinkedIn notification was trashed at classification time.
        if (resolved and sender_class == "automated"
                and cls not in ("linkedin_message", "not_job_related")):
            archive.append(mid)
        if d.get("archive") is False and mid in archive:
            archive.remove(mid)
        if d.get("archive") is True and sender_class != "automated":
            halts.append(f"{where}: asked to archive a {sender_class} email. "
                         f"Recruiter/individual mail stays in the Inbox.")

    # Honor Carl's write-back. A field the database already holds is his decision, and the
    # CSV is deliberately left blank so that his override stays distinguishable from a
    # front-end pre-fill. Suppress the write; never copy the database value into the edit.
    honored = []
    for ed in edits:
        w = (WB["map"] or {}).get(ed["Job_ID"])
        if not w or not w["applied"]:
            continue
        for f in list(ed["set"]):
            held = w["fields"].get(f, "")
            if not held:
                continue
            honored.append({"Job_ID": ed["Job_ID"], "field": f,
                             "would_have_written": ed["set"][f], "fabric_holds": held,
                             "agrees": held == ed["set"][f]})
            del ed["set"][f]
    edits = [e for e in edits if e["set"]]

    merged = {}
    for ed in edits:
        prior = merged.get(ed["Job_ID"])
        if prior is None:
            merged[ed["Job_ID"]] = ed
            continue
        for f, v in ed["set"].items():
            if f in prior["set"] and prior["set"][f] != v:
                halts.append(f"{ed['Job_ID']}: two decisions set {f} differently "
                             f"({prior['set'][f]!r} vs {v!r}). A confirmation email, a "
                             f"tracker entry and an applied badge for the same posting must "
                             f"agree. On a date disagreement the tracker wins — re-issue the "
                             f"losing decision as noop rather than editing this merge.")
            else:
                prior["set"][f] = v
        prior["why"] = f"{prior['why']} | {ed['why']}"
    edits = list(merged.values())

    if halts:
        print("\n  HALT — nothing written:\n", file=sys.stderr)
        for h in halts:
            print(f"    {h}", file=sys.stderr)
        sys.exit(f"\n  {len(halts)} decision(s) rejected. Fix them and re-run.\n")

    e_ = sys.stderr
    if honored:
        print(f"\n  HONORING FABRIC WRITE-BACK — {len(honored)} field(s) NOT written to "
              f"the CSV:", file=e_)
        for h in honored:
            flag = "" if h["agrees"] else "   <- DIFFERS, Fabric wins"
            print(f"      {h['Job_ID']:>12} {h['field']:<18} fabric={h['fabric_holds']!r} "
                  f"(would have written {h['would_have_written']!r}){flag}", file=e_)
        print(f"      These are Carl's own decisions from the report. The CSV stays blank "
              f"on purpose.", file=e_)

    print(f"\n  {len(decisions)} decision(s) -> {len(edits)} edit(s), "
          f"{len(archive)} to archive, {len(ledger_add)} to ledger, "
          f"{len(blocked)} blocked, {len(to_phase_b)} to Phase B\n", file=e_)
    for ed in edits:
        r = by_id[ed["Job_ID"]]
        print(f"    {ed['Job_ID']:>12} {r['Company'][:24]:26s} {r['Role_Title'][:32]:34s}",
              file=e_)
        for f, v in ed["set"].items():
            cur = (r.get(f) or "").strip()
            mark = ("already correct" if cur == v
                    else "BLANK-GATE holds, jd-update will skip" if cur
                    else "will set")
            print(f"                 {f:<18} {cur!r} -> {v!r}   {mark}", file=e_)
    for b in blocked:
        label = (b.get("subject") or b.get("headline") or b.get("tracker_job_id")
                 or b.get("badge_job_id") or "(unlabelled)")
        print(f"    BLOCKED  {label[:60]}\n             ask: {b['ask']}", file=e_)
    for r in to_phase_b:
        print(f"    -> PHASE B  {(r['subject'] or '')[:60]}", file=e_)
    if phase_ac:
        print(f"    {len(phase_ac)} LinkedIn digest(s) left to Phase A/C — not ledgered here.",
              file=e_)
    print("", file=e_)

    dump(edits, args.out_edits)
    dump({"honoured_writeback": honored,
          "archive_message_ids": archive, "ledger_additions": ledger_add,
          "blocked": blocked, "route_to_phase_b": to_phase_b,
          "phase_a_c_handles": phase_ac}, args.out_disposition)
    if args.out_archive_ids and archive:
        with open(args.out_archive_ids, "w") as f:
            f.write("\n".join(archive) + "\n")
        print(f"  archive IDs -> {args.out_archive_ids}\n", file=e_)


# Two disjoint families of LinkedIn mail, confirmed against live mail 2026-08-27. Getting
# these backwards routes a recruiter's message into the log as employer mail, or drops a
# postings digest into the model's reading pile. The list is observed, not guessed: only
# hit-reply@ and the two -noreply@ forms have ever actually appeared. inmail-hit-reply@ is
# documented but unobserved, so it is covered without being relied on.
SENDER_ROUTING_CASES = [
    # LinkedIn message notifications -> Phase G, trashed, never matched to a log row.
    ("hit-reply@linkedin.com", "linkedin_message"),
    ("inmail-hit-reply@linkedin.com", "linkedin_message"),
    # Posting digests -> Phase A pulled them, Phase C trashes them.
    ("jobalerts-noreply@linkedin.com", "job_alert"),
    ("jobs-noreply@linkedin.com", "job_alert"),
    # Everything else is ordinary mail and must not be swept into either family.
    ("no-reply@notifications.ukg.net", "automated"),
    ("talentacquisition@nightingale.edu", "automated"),
    ("jase.renneke@experis.com", "individual"),
]


def self_test():
    """Assert the sender routing. Run after touching LINKEDIN_MSG or JOB_ALERT."""
    fails = []
    for addr, expected in SENDER_ROUTING_CASES:
        display = "Jase Renneke" if expected == "individual" else ""
        got = classify_sender(display, addr, addr.split("@")[-1].split("."))
        if got != expected:
            fails.append(f"    {addr} -> {got}, expected {expected}")
    for raw, expected in [("Tuesday, August 25, 2026 at 5:01:35\u202fPM", "2026-08-25"),
                          ("Wednesday, August 26, 2026 at 12:28:14 PM", "2026-08-26"),
                          ("not a date", None)]:
        got = parse_date(raw)
        if got != expected:
            fails.append(f"    parse_date({raw!r}) -> {got!r}, expected {expected!r}")
    if fails:
        print("  SELF-TEST FAILED:", file=sys.stderr)
        print("\n".join(fails), file=sys.stderr)
        sys.exit(1)
    print(f"  self-test OK ({len(SENDER_ROUTING_CASES)} sender cases, 3 date cases)\n",
          file=sys.stderr)


def commit_ledger(args):
    """Append resolved Message-IDs to triaged-message-ids.json. Resolved only."""
    disp = json.load(open(args.out_disposition))
    add = disp["ledger_additions"]
    cur = json.load(open(LEDGER)) if os.path.exists(LEDGER) else []
    new = [m for m in add if m not in set(cur)]
    if not new:
        print("  ledger already current — nothing to add.\n", file=sys.stderr)
        return
    stamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    bak = os.path.join(ROOT, "backups", f"triaged-message-ids_{stamp}.json")
    with open(bak, "w") as f:
        json.dump(cur, f, indent=1)
    with open(LEDGER, "w") as f:
        json.dump(cur + new, f, indent=1)
    print(f"  ledger {len(cur)} -> {len(cur) + len(new)} (+{len(new)}), "
          f"backup backups/{os.path.basename(bak)}\n", file=sys.stderr)


def dump(obj, path):
    if path:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w") as f:
            json.dump(obj, f, indent=2)
        print(f"  wrote {path}", file=sys.stderr)
    else:
        json.dump(obj, sys.stdout, indent=2)
        print()


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--candidates", default=CANDIDATES)
    ap.add_argument("--writeback", default=WRITEBACK,
                    help="fabric_actions.csv from fabric-pull-actions.py")
    ap.add_argument("--skip-writeback-check", action="store_true",
                    help="render writes without a current Fabric pull (you must say why)")
    ap.add_argument("--max-pull-age-minutes", type=int, default=120,
                    help="how old scratch/fabric_actions.csv may be (default 120). The pull "
                         "is once per run, not once per day.")
    ap.add_argument("--tracker", default=TRACKER,
                    help="applied-tracker.json from fetch-applied-tracker.js")
    ap.add_argument("--skip-tracker", action="store_true",
                    help="run without reconciling the Job Tracker (you must say why)")
    ap.add_argument("--badges", default=BADGES,
                    help="applied-badge.json from applied-badge-scan.py. Optional: it exists "
                         "only when Phase B fetched bodies this run. A missing file is a "
                         "note, never a halt — this source is a backstop, not coverage.")
    ap.add_argument("--decisions", metavar="FILE", help="render mode: model classifications")
    ap.add_argument("--self-test", action="store_true",
                    help="assert sender routing and date parsing, then exit")
    ap.add_argument("--commit-ledger", action="store_true",
                    help="append the resolved IDs from --out-disposition to the ledger")
    ap.add_argument("--out", metavar="FILE", help="match report (default: stdout)")
    ap.add_argument("--out-edits", default=os.path.join(ROOT, "scratch", "triage-edits.json"))
    ap.add_argument("--out-disposition",
                    default=os.path.join(ROOT, "scratch", "triage-disposition.json"))
    ap.add_argument("--out-archive-ids",
                    default=os.path.join(HERE, "confirmed-archive-ids.txt"))
    ap.add_argument("--max-body", type=int, default=2500)
    ap.add_argument("--max-candidates", type=int, default=8)
    args = ap.parse_args()

    if args.self_test:
        self_test()
    elif args.commit_ledger:
        commit_ledger(args)
    elif args.decisions:
        render(args)
    else:
        match(args)


if __name__ == "__main__":
    main()
