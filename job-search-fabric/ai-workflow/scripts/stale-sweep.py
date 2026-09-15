#!/usr/bin/env python3
"""
stale-sweep.py — Phase E, the stale-Pursue closure sweep.

For every row where Verdict is "Pursue" or "Review" and Carls_Action is blank, re-fetch the
posting and ask one question: is it still accepting applications? This is a FACT RE-CHECK, NOT
A RE-EVALUATION. Score, Verdict, Role_Type, Comp_Flag, Biggest_Gap, Biggest_Strength and
Recommended_Action are never touched, even if the re-fetched text reads differently now.

Two modes, deliberately split the way triage-match.py splits its two:

  select   (default)  — query the log, honor Fabric's write-backs, emit an ID list to fetch
  classify --fetched  — read what fetch-jds.js returned, emit a jd-update.py edit list

USAGE
    python3 scripts/fabric-pull-actions.py                 # once, at the start of the run
    python3 scripts/stale-sweep.py                         # -> scratch/stale-sweep-ids.txt
    node    scripts/fetch-jds.js --ids-file ../scratch/stale-sweep-ids.txt \
                                 --out ../scratch/fetched_phaseE_<date>
    python3 scripts/stale-sweep.py --classify scratch/fetched_phaseE_<date>
    python3 scripts/jd-update.py --input scratch/stale-sweep-edits.json --dry-run
    python3 scripts/jd-update.py --input scratch/stale-sweep-edits.json

WHAT IT REFUSES TO DO (each refusal has an incident behind it)

  * Read "still open" out of an empty page. A fetch that fails with
    SKELETON_AFTER_MAX_ATTEMPTS returns an EMPTY bodyText. The absence of "no longer accepting
    applications" in an empty string is not evidence of anything. Those rows are UNVERIFIED and
    classify mode HALTS on them rather than noting them in a summary. (The exact mistake made
    2026-08-26.) --allow-unverified proceeds, writing only the confirmed-closed rows and naming
    what went unchecked.

  * Write over a decision Carl already made. Carls_Action is one of the four fields he
    overrides in the Power BI report. Any row where Fabric holds a non-empty Carls_Action with
    WriteBack_Applied = True is suppressed — his write-back is finished, and the CSV stays blank
    on it. The pulled value decides WHETHER to write; it is never itself written. Nothing from a
    pull enters the CSV. (2026-08-26 and 2026-08-27 incidents.)

  * Run on a stale pull. The pull is ONCE PER RUN, not once per day (Carl, 2026-08-28): he can
    write back at any hour, so a pull from this morning can already be wrong this afternoon.
    Age is checked in minutes. Suppression is re-checked in classify mode, not trusted from
    select mode, because a fetch batch takes time and he may have acted during it.
"""
import argparse, csv, datetime, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

LOG       = os.path.join(ROOT, "JD_Evaluation_Log.csv")
WRITEBACK = os.path.join(ROOT, "scratch", "fabric_actions.csv")
OUT_IDS   = os.path.join(ROOT, "scratch", "stale-sweep-ids.txt")
OUT_EDITS = os.path.join(ROOT, "scratch", "stale-sweep-edits.json")

TODAY = datetime.date.today().isoformat()   # never from a prompt — 2026-08-27 incident
ELIGIBLE_VERDICTS = ("Pursue", "Review")
MAX_PER_RUN = 25                            # same cap as Step 3; split larger backlogs
CLOSED_RE = re.compile(r"no longer accepting applications", re.I)


# ---------------------------------------------------------------- inputs

def load_log():
    with open(LOG, newline="") as f:
        r = csv.DictReader(f)
        return list(r), r.fieldnames


def pull_age_minutes(path):
    delta = datetime.datetime.now() - datetime.datetime.fromtimestamp(os.path.getmtime(path))
    return int(delta.total_seconds() // 60)


def require_writeback(args):
    """Load Fabric's write-back state, or refuse to run.

    Phase E writes Carls_Action. It may not do that without knowing which rows Carl has
    already decided in the report. Copied from triage-match.py's render-mode guard on
    purpose — refuse the bad write rather than warn about it.
    """
    rel = os.path.relpath(args.writeback, ROOT)
    if not os.path.exists(args.writeback):
        problem = (f"{rel} not found. Run `python3 scripts/fabric-pull-actions.py` first — "
                   f"Phase E must know which rows Carl has already triaged in the report.")
    else:
        age = pull_age_minutes(args.writeback)
        if age > args.max_pull_age_minutes:
            problem = (f"{rel} is {age} minute(s) old (limit {args.max_pull_age_minutes}). "
                       f"Re-run `python3 scripts/fabric-pull-actions.py` — the pull is once "
                       f"per run, not once per day. A pull this old can miss a write-back "
                       f"Carl made since, and this sweep would overwrite his decision.")
        else:
            with open(args.writeback, newline="") as f:
                wb = {r["Job_ID"]: r for r in csv.DictReader(f)}
            print(f"  write-back    {len(wb)} row(s) from {rel} ({age} min old)",
                  file=sys.stderr)
            return wb
    if not args.skip_writeback_check:
        sys.exit(f"\n  HALT: {problem}\n  (--skip-writeback-check overrides, deliberately.)\n")
    print(f"  WARNING: --skip-writeback-check. {problem}\n"
          f"  Rows Carl has already actioned in the report are INVISIBLE to this run and may "
          f"be overwritten.", file=sys.stderr)
    return {}


def suppressed_by_writeback(wb, job_id):
    """True when Carl's report write-back owns Carls_Action on this row.

    Per-field, not per-row: this phase only writes Carls_Action / Carls_Action_Date / Reason,
    and only Carls_Action decides eligibility here — a row he has actioned is not a stale
    Pursue any more, whatever the other three fields hold.
    """
    f = wb.get(job_id)
    if not f:
        return False
    applied = str(f.get("WriteBack_Applied", "")).strip().lower() in ("true", "1")
    return applied and bool(f.get("Carls_Action", "").strip())


# ---------------------------------------------------------------- select

def select(args):
    wb = require_writeback(args)
    rows, _ = load_log()

    eligible, suppressed = [], []
    for r in rows:
        if r.get("Verdict", "").strip() not in ELIGIBLE_VERDICTS:
            continue
        if r.get("Carls_Action", "").strip():
            continue
        if suppressed_by_writeback(wb, r.get("Job_ID", "")):
            suppressed.append(r)
        else:
            eligible.append(r)

    # Oldest first: a Pursue that has sat longest is likeliest to have closed.
    eligible.sort(key=lambda r: r.get("Date_Evaluated", ""))
    batch, remainder = eligible[:args.cap], eligible[len(eligible[:args.cap]):]

    print(f"\n  Phase E — stale-Pursue closure sweep, {TODAY}")
    print(f"  {'-'*66}")
    print(f"  eligible rows (Pursue/Review, blank Carls_Action)   {len(eligible) + len(suppressed):>4}")
    print(f"    suppressed — Carl already actioned in the report  {len(suppressed):>4}")
    print(f"    to re-check this run                              {len(batch):>4}")
    if remainder:
        print(f"    deferred to the next sweep (cap {args.cap})            {len(remainder):>4}")

    if suppressed:
        print(f"\n  Suppressed (his write-back is finished; CSV stays blank):")
        for r in suppressed:
            f = wb[r["Job_ID"]]
            print(f"    {r['Job_ID']}  {r.get('Company','')[:28]:30} "
                  f"Fabric: {f.get('Carls_Action','')} {f.get('Carls_Action_Date','')}")

    if batch:
        print(f"\n  To fetch:")
        for r in batch:
            print(f"    {r['Job_ID']}  {r.get('Date_Evaluated',''):12} "
                  f"{r.get('Company','')[:28]:30} {r.get('Role_Title','')[:40]}")
        with open(args.out_ids, "w") as f:
            f.write("\n".join(r["Job_ID"] for r in batch) + "\n")
        rel = os.path.relpath(args.out_ids, ROOT)
        print(f"\n  -> {rel} ({len(batch)} id(s))")
        print(f"  Next: node scripts/fetch-jds.js --ids-file ../{rel} "
              f"--out ../scratch/fetched_phaseE_{TODAY.replace('-','')}")
    else:
        print(f"\n  Nothing to fetch. No stale Pursue/Review rows are awaiting a decision.")
        if os.path.exists(args.out_ids):
            os.remove(args.out_ids)   # never leave a previous run's list to be re-fetched
    print()


# ---------------------------------------------------------------- classify

def classify(args):
    wb = require_writeback(args)
    rows, _ = load_log()
    by_id = {r.get("Job_ID", ""): r for r in rows}

    d = args.classify if os.path.isabs(args.classify) else os.path.join(ROOT, args.classify)
    if not os.path.isdir(d):
        sys.exit(f"\n  HALT: {args.classify} is not a directory.\n")
    files = sorted(f for f in os.listdir(d)
                   if f.endswith(".json") and not f.startswith("_"))
    if not files:
        sys.exit(f"\n  HALT: no fetched postings in {args.classify}.\n")

    closed, still_open, unverified, halts = [], [], [], []
    for name in files:
        p = os.path.join(d, name)
        try:
            j = json.load(open(p))
        except Exception as e:
            unverified.append((name.replace(".json", ""), f"unreadable JSON ({e})"))
            continue
        jid = str(j.get("jobId") or name.replace(".json", ""))
        body = j.get("bodyText") or ""

        # The 2026-08-26 trap. An empty page is not an open posting.
        if not j.get("ok", False):
            unverified.append((jid, f"fetch failed: {j.get('reason', 'unknown')}"))
            continue
        if not body.strip():
            unverified.append((jid, "ok=true but bodyText is empty"))
            continue

        row = by_id.get(jid)
        if row is None:
            halts.append(f"{jid}: fetched, but no such Job_ID in the log. jd-update.py "
                         f"will not create a row.")
            continue
        if CLOSED_RE.search(body):
            # Re-check suppression: the fetch batch takes time, and Carl may have acted
            # during it. select mode's answer is not trusted here.
            if suppressed_by_writeback(wb, jid):
                f = wb[jid]
                still_open.append((jid, row, f"CLOSED, but suppressed — Fabric holds "
                                             f"{f.get('Carls_Action','')} "
                                             f"{f.get('Carls_Action_Date','')}"))
                continue
            if row.get("Carls_Action", "").strip():
                still_open.append((jid, row, "CLOSED, but Carls_Action is already set in "
                                             "the CSV; jd-update.py fills blanks only"))
                continue
            closed.append((jid, row))
        else:
            still_open.append((jid, row, "open"))

    print(f"\n  Phase E — closure classification, {TODAY}")
    print(f"  {'-'*66}")
    print(f"  fetched            {len(files):>4}")
    print(f"    closed  -> write {len(closed):>4}")
    print(f"    open    -> leave {len([x for x in still_open if x[2] == 'open']):>4}")
    print(f"    skipped -> leave {len([x for x in still_open if x[2] != 'open']):>4}")
    print(f"    UNVERIFIED       {len(unverified):>4}")

    if halts:
        print(f"\n  {len(halts)} rejected:")
        for h in halts:
            print(f"    - {h}")
        sys.exit(f"\n  Fix them and re-run.\n")

    if unverified:
        print(f"\n  UNVERIFIED — nothing was read from these pages:")
        for jid, why in unverified:
            print(f"    {jid}  {why}")
        if not args.allow_unverified:
            sys.exit(
                f"\n  HALT: {len(unverified)} posting(s) could not be read. An empty page is "
                f"not an open posting\n  and it is not a closed one either — it is no "
                f"evidence at all (2026-08-26).\n  Re-fetch them, or re-run with "
                f"--allow-unverified to write the {len(closed)} confirmed-closed row(s)\n"
                f"  and leave these for the next sweep.\n")
        print(f"\n  WARNING: --allow-unverified. The {len(unverified)} posting(s) above were "
              f"NOT checked;\n  their closure status is unknown and they stay eligible for "
              f"the next sweep.", file=sys.stderr)

    for jid, row, why in still_open:
        if why != "open":
            print(f"\n  left alone: {jid} {row.get('Company','')[:28]} — {why}")

    if not closed:
        print(f"\n  No confirmed-closed rows. Nothing to write.\n")
        if os.path.exists(args.out_edits):
            os.remove(args.out_edits)
        return

    edits = []
    print(f"\n  Confirmed closed — writing Carls_Action = \"None\":")
    for jid, row in closed:
        print(f"    {jid}  {row.get('Company','')[:28]:30} {row.get('Role_Title','')[:38]}")
        edits.append({
            "Job_ID": jid,
            "set": {"Carls_Action": "None",
                    "Carls_Action_Date": TODAY,
                    "Reason": "No longer accepting applications"},
            "why": f"Phase E closure sweep {TODAY}: posting re-fetched and no longer "
                   f"accepting applications",
        })
    with open(args.out_edits, "w") as f:
        json.dump(edits, f, indent=2)
    rel = os.path.relpath(args.out_edits, ROOT)
    print(f"\n  -> {rel} ({len(edits)} edit(s))")
    print(f"  Next: python3 scripts/jd-update.py --input {rel} --dry-run\n")


# ---------------------------------------------------------------- self-test

def self_test():
    import tempfile
    ok = []

    # closure detection against the real phrasings seen in fetched pages
    for s, want in [
        ("No longer accepting applications", True),
        ("No longer accepting applications\n\nUse AI to assess how you fit", True),
        ("no longer accepting applications", True),
        ("Be among the first 25 applicants", False),
        ("", False),
    ]:
        got = bool(CLOSED_RE.search(s))
        assert got == want, f"closure detection: {s!r} -> {got}, want {want}"
        ok.append(1)

    # suppression is per-field and needs BOTH the flag and a value
    for f, want in [
        ({"WriteBack_Applied": "True",  "Carls_Action": "Pass"}, True),
        ({"WriteBack_Applied": "True",  "Carls_Action": ""},     False),
        ({"WriteBack_Applied": "False", "Carls_Action": "Pass"}, False),
        ({"WriteBack_Applied": "",      "Carls_Action": ""},     False),
    ]:
        got = suppressed_by_writeback({"X": f}, "X")
        assert got == want, f"suppression: {f} -> {got}, want {want}"
        ok.append(1)
    assert suppressed_by_writeback({}, "missing") is False

    print(f"  self-test OK ({len(ok)} cases)")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--writeback", default=WRITEBACK,
                    help="fabric_actions.csv from fabric-pull-actions.py")
    ap.add_argument("--skip-writeback-check", action="store_true",
                    help="run without a current Fabric pull (you must say why)")
    ap.add_argument("--max-pull-age-minutes", type=int, default=120,
                    help="how old the pull may be (default 120). Once per run, not per day.")
    ap.add_argument("--cap", type=int, default=MAX_PER_RUN,
                    help=f"postings to re-check per run (default {MAX_PER_RUN})")
    ap.add_argument("--classify", metavar="DIR",
                    help="classify mode: directory fetch-jds.js wrote to")
    ap.add_argument("--allow-unverified", action="store_true",
                    help="write confirmed-closed rows even though some fetches failed")
    ap.add_argument("--out-ids", default=OUT_IDS)
    ap.add_argument("--out-edits", default=OUT_EDITS)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        self_test()
    elif args.classify:
        classify(args)
    else:
        select(args)


if __name__ == "__main__":
    main()
