#!/usr/bin/env python3
"""
phase-state.py — record and report when each pipeline phase last completed.

Why this exists. On 2026-09-01 Carl found 60 job-alert emails still in his Inbox from the
2026-08-31 run. Phases A, B, D and E had all run; **Phase C had never run at all**, and
nothing in the workflow could tell. Phase C leaves no artifact of its own — it writes to
Mail's Trash, not to this folder — so a skipped C is invisible until the Inbox is noticed
by eye, days later.

A→C is meant to run unattended in one invocation, where C cannot be skipped. It got skipped
because the 2026-08-31 run broke on token cost and was recovered piecemeal over two days,
and a piecemeal recovery has no such guarantee. Recoveries will happen again.

THE CHECK THAT MATTERS. Not "how old is each phase" — a quiet week makes every phase old and
that is fine. It is: **is any phase older than the most recent Phase A?** Phase A is what
starts a run. A phase stamped earlier than the last A means a run began and that phase never
finished it. That is the exact shape of the 2026-08-31 miss, and `--report` names it.

    python3 scripts/phase-state.py --report
    python3 scripts/phase-state.py --mark C --note "60 emails trashed, 0 reverted"

Phase F is the one exception: it is monthly by design, not per-run, so it is measured against
its own 30-day cadence and never against Phase A.

This file records completions. It does not enforce them and it does not run anything — a
marker that silently blocked a phase would be a worse failure than the one it prevents.
"""
import argparse, datetime, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(HERE, "phase-state.json")

# Execution order, which is NOT alphabetical: F was named before G existed and always runs
# last. See the naming convention in COWORK_INSTRUCTIONS.md.
PHASES = {
    "A": "pull mail (mail-pull.applescript)",
    "B": "dedupe, fetch JDs, evaluate, write both CSVs, archive the .emls",
    "C": "trash the confirmed-logged source emails (mail-trash.applescript)",
    "D": "application / rejection / interview triage",
    "E": "stale-Pursue closure sweep",
    "G": "LinkedIn message triage and reply drafting",
    "F": "monthly Skip audit (recall check)",
}
PER_RUN = [p for p in PHASES if p != "F"]     # measured against the last Phase A
MONTHLY_DAYS = 30                             # Phase F's own cadence


def load():
    if not os.path.exists(STATE):
        return {}
    try:
        return json.load(open(STATE))
    except (ValueError, OSError):
        return {}


def save(state):
    with open(STATE, "w") as f:
        json.dump(state, f, indent=1, sort_keys=True)


def days_since(iso):
    try:
        return (datetime.date.today() - datetime.date.fromisoformat(iso[:10])).days
    except (ValueError, TypeError):
        return None


def mark(args):
    state = load()
    when = args.date or datetime.date.today().isoformat()
    state[args.phase] = {"last_completed": when,
                         "note": args.note or "",
                         "stamped_at": datetime.datetime.now().replace(
                             microsecond=0).isoformat()}
    save(state)
    print(f"  Phase {args.phase} marked complete {when}"
          + (f" — {args.note}" if args.note else ""), file=sys.stderr)


def report(args):
    state = load()
    e = sys.stderr
    a = (state.get("A") or {}).get("last_completed")
    print(f"\n  phase  last run     age   note", file=e)
    problems = []
    for p, desc in PHASES.items():
        rec = state.get(p) or {}
        last = rec.get("last_completed")
        age = days_since(last) if last else None
        agestr = f"{age}d" if age is not None else "  -"
        print(f"  {p:<6} {last or 'never':<12} {agestr:>4}   {rec.get('note','')[:44]}", file=e)
        if p == "F":
            if last is None or (age is not None and age > MONTHLY_DAYS):
                problems.append(f"Phase F is {'never run' if not last else f'{age}d old'} — "
                                f"monthly audit is due.")
            continue
        if last is None:
            problems.append(f"Phase {p} has never been marked — {desc}.")
        elif a and last < a:
            problems.append(
                f"Phase {p} last completed {last}, but a run started (Phase A) on {a}. "
                f"That run never finished {p} — {desc}.")
    print("", file=e)
    if problems:
        print("  ⚠️  INCOMPLETE:", file=e)
        for x in problems:
            print(f"     {x}", file=e)
        print("", file=e)
        return 1
    print("  All phases current against the last Phase A.\n", file=e)
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mark", dest="phase", choices=list(PHASES),
                    help="record a phase as completed")
    ap.add_argument("--note", help="one line of context for the run summary")
    ap.add_argument("--date", help="ISO date of completion (default today) — for backfill")
    ap.add_argument("--report", action="store_true", help="show every phase and flag gaps")
    args = ap.parse_args()
    if args.phase:
        mark(args)
        return 0
    if args.report:
        return report(args)
    return report(args)


if __name__ == "__main__":
    sys.exit(main())
