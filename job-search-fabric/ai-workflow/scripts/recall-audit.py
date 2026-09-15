#!/usr/bin/env python3
"""
recall-audit.py — Phase F, the monthly Skip audit (recall check).

Surfaces rows the filter rejected so over-tightening becomes visible. It does NOT
re-verdict anything, and it NEVER writes to JD_Evaluation_Log.csv or its mirror.
The only file it can modify is `rubric/learning_log.md`, and only in --record mode.

    python3 scripts/fabric-pull-actions.py          # once, at the start of the run
    python3 scripts/recall-audit.py                 # select + present
    python3 scripts/recall-audit.py --record scratch/recall_answers_YYYYMMDD.json
    python3 scripts/recall-audit.py --self-test

WHY THIS IS A SEPARATE SCRIPT FROM rubric-learn.py
  The revamp plan asked whether Phase F belongs as a mode of `rubric-learn.py`. It does not,
  for three measured reasons:
    1. rubric-learn.py reads ONLY the Fabric pull. The pull carries no `Biggest_Gap`, `Notes`,
       `Location` or `URL` — the four fields that make an audit line readable. Phase F has to
       join the pull to JD_Evaluation_Log.csv. (Verified 2026-08-28: pull has 24 columns, log
       has 24, and the overlap excludes exactly those four.)
    2. rubric-learn.py never asks a question. Phase F is a two-step with Carl in the middle:
       present, then record his answer. Folding an interactive step into the learner would
       cost it the property that makes it safe to run unattended.
    3. rubric-learn.py measures the rules declared in `weights.json` — G1, G2, G2b, G3a, G3b,
       G4. Phase F's gates (G6, G10, G11, G12, the Director+ screen, the people-management
       deduction) are not in that dict and have never been measured by anything. That is the
       gap Phase F fills, not a mode of an existing measurement.
  What it DOES share: the same pull, the same class boundaries, and the same learning log.

WHAT IT SELECTS  (instructions/05-triage-and-audits.md, "Phase F")
  1. Last N days (default 30), Verdict = Skip, Score in the 60-69 band.
  2. Rows killed by a gate added 2026-08-10 — G6, G10, G11, G12 — or by the Director+ screen.
  3. Rows that took the -10 people-management deduction and landed 60-69.
  4. Bridge candidates Carl did not act on: Lane fit = 12 and score 65-69
     (instructions/02-evaluate-and-report.md, "Bridge candidates"), NOT every row whose
     Role_Type string happens to contain the word "bridge" — that reads 251 rows instead of 25.

THE ASK IS TWO BUCKETS, AND THEY DO NOT POOL
  A window's unanswered rows are too many to read one by one (121 on 2026-08-28). Two smaller
  asks answer different questions, and mixing them produces a number that means nothing:

    --ask ID,ID,...     a THEME shortlist: rows selected by a rule Carl has already stated.
                        A high hit rate here is expected — the rows were chosen for it. This
                        measures what the stated rule is worth, NOT recall.
    --control-sample N  N rows drawn at RANDOM from everything else, seeded on the window so
                        the draw is reproducible. This is the only unbiased recall estimate,
                        and the only thing that can find a theme Carl has not named yet.

  It also checks the shortlist itself: if a control row turns out to be one Carl wanted and it
  looks like the rows the theme filter discarded, the filter was applied wrongly.

WHAT IT REFUSES TO DO
  - Run against a stale or missing Fabric pull. "Unactioned" is the whole selection criterion,
    and a pull from this morning can miss an action Carl took at noon.
  - Select a gate from a gate LABEL in Notes/Biggest_Gap. Measured 2026-08-28: of 34 rows whose
    text names G10, 9 were actually killed by it — the rest record a gate that was CHECKED and
    did NOT fire, including Pursue rows. `Reason` is the authoritative kill field; labels are
    narrative. Labels are reported as a discrepancy, never used to select.
  - Count an application Carl made BEFORE the row was evaluated as an override of the gate
    that killed it. Measured 2026-08-28: 142 of 400 actioned rows carry a Carls_Action_Date
    earlier than their Date_Evaluated — the 2026-08-12 backfill retro-logged months of his
    application history and scored it under the current rubric. Counting those, the Director+
    screen reads a 30% override rate; counting only applications that could actually have been
    stopped by it, 2%. See `applied_before_evaluation` below.
  - Record an answer for a Job_ID not in the audit population, or an answer outside the
    allowed set, or into a learning log that does not exist.
  - Pool the theme shortlist and the control sample into one ratio. They are reported, and
    recorded, separately.
  - Write anything at all to JD_Evaluation_Log.csv.
"""
import argparse, csv, datetime, json, os, random, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LOG_CSV  = os.path.join(ROOT, "JD_Evaluation_Log.csv")
PULL     = os.path.join(ROOT, "scratch", "fabric_actions.csv")
LEARNING = os.path.join(ROOT, "rubric", "learning_log.md")
WEIGHTS  = os.path.join(ROOT, "rubric", "weights.json")
SCRATCH  = os.path.join(ROOT, "scratch")

# Get the date from the clock, never from a prompt. (Incident 2026-08-27: 27 rows dated a day
# early because the session had crossed midnight and the evaluator was handed the date in text.
# Date_Evaluated drives this script's own 30-day window, so the error would be silent here too.)
TODAY = datetime.date.today()

# Same boundaries rubric-learn.py uses, so a rate measured here means the same thing there.
VETO_MAX, REVIEW_MIN = 0.10, 0.25

# The kill reasons this phase audits, matched against `Reason` — the string the rubric tells
# the evaluator to write. Each pattern is the rubric's own prescribed wording.
GATES = {
    "G6":  ("industry exclusion",  r"industry exclusion"),
    "G10": ("wrong stack",         r"wrong stack"),
    "G11": ("domain gate",         r"domain gate"),
    "G12": ("travel",              r"\btravel\b"),
    "DIR": ("director+ screen",    r"director\s*\+\s*scope|director-plus scope"),
    "PMS": ("people-mgmt scope",   r"people-management scope"),
}
# Reasons that record a posting's status rather than anything about Carl's preferences.
# Same exclusion rubric-learn.py applies, and for the same reason.
POSTING_STATUS = re.compile(
    r"no longer accepting|boilerplate rejection|anonymous end client|duplicate job posting", re.I)

ANSWERS = {"wanted", "not_wanted", "already_applied", "closed", "unsure"}
# Answers that count toward the numerator of the recall ratio.
WANTED = {"wanted", "already_applied"}


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def score(r):
    v = num(r.get("Score"))
    return int(v) if v is not None else None


def rel(p):
    return os.path.relpath(p, ROOT)


# ---------------------------------------------------------------- inputs and guards

def pull_age_minutes(path):
    delta = datetime.datetime.now() - datetime.datetime.fromtimestamp(os.path.getmtime(path))
    return int(delta.total_seconds() // 60)


def require_pull(args):
    """Refuse to select against a stale pull.

    Phase F writes nothing to the CSV, so this is not the write-safety guard Phase D and E
    carry. It is a correctness guard on the selection itself: every criterion here turns on
    whether Carl has acted on a row, and the pull is the only place his write-backs live.
    A stale pull puts rows he has already answered back in front of him, and — worse —
    reports them in the recall ratio as unanswered. The pull is once per RUN, not once per
    day (Carl, 2026-08-28), so the check is in minutes.
    """
    if not os.path.exists(args.pull):
        msg = (f"{rel(args.pull)} not found. Run `python3 scripts/fabric-pull-actions.py` "
               f"first — Phase F cannot tell an unactioned row from one Carl has already "
               f"answered without it.")
    else:
        age = pull_age_minutes(args.pull)
        if age > args.max_pull_age_minutes:
            msg = (f"{rel(args.pull)} is {age} minute(s) old (limit "
                   f"{args.max_pull_age_minutes}). Re-run "
                   f"`python3 scripts/fabric-pull-actions.py` — the pull is once per run, "
                   f"not once per day.")
        else:
            print(f"  pull          {age} min old  ({rel(args.pull)})", file=sys.stderr)
            return
    if not args.skip_pull_check:
        sys.exit(f"\n  HALT: {msg}\n"
                 f"  (--skip-pull-check overrides. What goes unseen if you use it: any action\n"
                 f"   Carl took since that pull. Those rows will be presented to him again as\n"
                 f"   unactioned, and counted in the recall ratio as though he never answered.)\n")
    print(f"  WARNING (--skip-pull-check): {msg}\n"
          f"  Rows Carl actioned since that pull will be re-presented and mis-counted.",
          file=sys.stderr)


def load_sources(args):
    with open(LOG_CSV, newline="") as f:
        log = {r["Job_ID"]: r for r in csv.DictReader(f) if r.get("Job_ID")}
    pull = {}
    if os.path.exists(args.pull):
        with open(args.pull, newline="") as f:
            pull = {r["Job_ID"]: r for r in csv.DictReader(f) if r.get("Job_ID")}
    missing = [j for j in log if j not in pull]
    if missing:
        print(f"  NOTE          {len(missing)} log row(s) absent from the pull; they are "
              f"treated as unactioned.", file=sys.stderr)
    return log, pull


# ---------------------------------------------------------------- selection

def classify(jid, L, P, cutoff):
    """Return the list of criteria this row is selected under. Empty means not selected.

    Pure function of the two rows and the window, so --self-test can drive it directly.
    """
    hits = []
    d = (L.get("Date_Evaluated") or "")[:10]
    if not d or d < cutoff:
        return hits
    s = score(L)
    v = (L.get("Verdict") or "").strip()
    reason = L.get("Reason") or ""

    # 1. the 60-69 Skip band
    if v == "Skip" and s is not None and 60 <= s <= 69:
        hits.append("band_60_69")

    # 2. the gates added 2026-08-10, plus the Director+ screen.
    #    Selected from `Reason` only — see the module docstring on why labels do not select.
    if v == "Skip" and not POSTING_STATUS.search(reason):
        for key, (_, pat) in GATES.items():
            if re.search(pat, reason, re.I):
                hits.append("gate_" + key)

    # 3. the -10 people-management deduction landing 60-69.
    #    The structured signature is Pts_Scope == 0 (weights.json: people_management_core
    #    "with scope=0"). Pts_Deductions is an aggregate and cannot isolate this one, so the
    #    scope floor is the detector and the text evidence is reported alongside, not relied on.
    if num(P.get("Pts_Scope")) == 0 and s is not None and 60 <= s <= 69:
        hits.append("pm_deduction")

    # 4. Bridge candidates Carl did not act on: Lane 12 and 65-69.
    if num(P.get("Pts_Lane")) == 12 and s is not None and 65 <= s <= 69 \
            and not (P.get("Carls_Action") or "").strip():
        hits.append("bridge_unacted")

    return hits


def select(log, pull, window_days):
    cutoff = (TODAY - datetime.timedelta(days=window_days)).isoformat()
    rows = []
    for jid, L in log.items():
        P = pull.get(jid, {})
        hits = classify(jid, L, P, cutoff)
        if not hits:
            continue
        rows.append({
            "Job_ID": jid,
            "Company": L.get("Company") or "",
            "Role_Title": L.get("Role_Title") or "",
            "Score": score(L),
            "Verdict": L.get("Verdict") or "",
            "Reason": (L.get("Reason") or "").strip(),
            "Role_Type": L.get("Role_Type") or "",
            "Date_Evaluated": (L.get("Date_Evaluated") or "")[:10],
            "URL": L.get("URL") or "",
            "Biggest_Gap": (L.get("Biggest_Gap") or "").strip(),
            "criteria": hits,
            # Carl's own state comes from the pull, which is authoritative for the four
            # write-back fields. Never read it back into the CSV (the one-way rule).
            "Carls_Action": (P.get("Carls_Action") or "").strip(),
            "Carls_Action_Date": (P.get("Carls_Action_Date") or "")[:10],
            "WriteBack_Applied": (P.get("WriteBack_Applied") or "").strip(),
            "pre_dated": applied_before_evaluation(L, P),
        })
    rows.sort(key=lambda r: (-(r["Score"] or 0), r["Company"].lower()))
    return rows, cutoff


# ---------------------------------------------------------------- measurement

def applied_before_evaluation(L, P):
    """True if Carl applied to this posting before the row was ever scored.

    Such a row is not an override. The gate had no opportunity to stop him — the evaluation
    that fired it did not exist yet. The 2026-08-12 backfill retro-logged months of Carl's
    application history and scored every row under the current rubric, so this is not an edge
    case: it is 142 of the 400 actioned rows in the log.

    A same-day pair counts as an override. That errs toward reporting the filter as too tight,
    which is the safe direction for a recall audit — the failure this phase exists to catch is a
    gate quietly eating good roles, so ties go against the gate. Confirmed by Carl 2026-08-31 on
    the two rows it decides in `rubric-learn.py` (InterEx 4445507224, Riana 4452713933): he does
    not remember either and counts them as overrides.

    `rubric-learn.py` carries the same rule, with a one-argument signature because its pull row
    holds both dates. **The comparison must stay identical**; a divergence would have the two
    scripts reporting different rates for the same rule.
    """
    ev = (L.get("Date_Evaluated") or "")[:10]
    ad = (P.get("Carls_Action_Date") or "")[:10]
    if not ev or not ad:
        return False
    return ad < ev


def override_rates(log, pull):
    """For each Phase F gate: of the rows it killed, how many did Carl apply to anyway?

    Denominator is every row the gate fired on, blank action INCLUDED — for a screen meant to
    reject, "Carl never acted" is the rule working, not a missing label. Same population
    rubric-learn.py uses, and posting-status rows are dropped for the same reason.

    Numerator counts only applications the gate could actually have prevented. `raw_rate` is
    kept alongside so the gap between the two is visible rather than quietly corrected — on
    2026-08-28 that gap was the entire finding.
    """
    out = {}
    for key, (label, pat) in GATES.items():
        fired = []
        for jid, L in log.items():
            r = L.get("Reason") or ""
            if POSTING_STATUS.search(r):
                continue
            if re.search(pat, r, re.I):
                fired.append(jid)
        applied = [j for j in fired if (pull.get(j, {}).get("Carls_Action") or "") == "Applied"]
        pre = [j for j in applied if applied_before_evaluation(log[j], pull.get(j, {}))]
        override = [j for j in applied if j not in set(pre)]
        passed  = [j for j in fired if (pull.get(j, {}).get("Carls_Action") or "") == "Pass"]
        rate     = len(override) / len(fired) if fired else None
        raw_rate = len(applied) / len(fired) if fired else None
        measured = None
        if rate is not None:
            measured = "veto" if rate <= VETO_MAX else ("review" if rate >= REVIEW_MIN else "borderline")
        out[key] = {"label": label, "n_fired": len(fired), "n_applied": len(applied),
                    "n_override": len(override), "n_pre_dated": len(pre),
                    "n_passed": len(passed), "rate": rate, "raw_rate": raw_rate,
                    "measured_class": measured, "override_ids": override, "pre_dated_ids": pre}
    return out


def label_discrepancies(log):
    """Rows whose narrative text names a gate that `Reason` does not record as the killer.

    Reported, never selected on. Most are a gate that was checked and correctly did not fire;
    a cluster on one gate would mean the Reason wording has drifted from the rubric.
    """
    pairs = {"G6": r"\bG6\b", "G10": r"\bG10\b", "G11": r"\bG11\b", "G12": r"\bG12\b"}
    out = {}
    for g, lab in pairs.items():
        _, rpat = GATES[g]
        label_only = 0
        for L in log.values():
            blob = " ".join((L.get(k) or "") for k in ("Biggest_Gap", "Recommended_Action", "Notes"))
            if re.search(lab, blob) and not re.search(rpat, L.get("Reason") or "", re.I):
                label_only += 1
        out[g] = label_only
    return out


def review_verdict_check(log):
    """Has the fourth verdict ever had an opportunity to fire?

    The revamp plan (2026-08-28) flagged that `Verdict = "Review"` has never appeared since it
    was added on 2026-08-26, and asked Phase F to look once. Two different findings hide here:
    a Review-shaped row that scored something else is a broken rule; zero Review-shaped rows at
    all is just no opportunity yet. Report which.
    """
    added = "2026-08-26"
    try:
        w = json.load(open(WEIGHTS))
        firms = re.compile("|".join(re.escape(f) for f in w["consulting_firms"]), re.I)
    except Exception:
        firms = re.compile(r"(?!)")
    compensable = {"G1 contract": r"\bcontract\b",
                   "G2b comp floor": r"below comp floor",
                   "G3b delivery": r"consulting delivery role"}
    veto = {"G2 low comp": r"\blow comp\b", "G4 Ladders": r"Ladders"}
    n_review = sum(1 for L in log.values() if (L.get("Verdict") or "").strip() == "Review")
    shaped = []
    for jid, L in log.items():
        if (L.get("Date_Evaluated") or "")[:10] < added:
            continue
        reason = L.get("Reason") or ""
        c = [k for k, p in compensable.items() if re.search(p, reason, re.I)]
        v = [k for k, p in veto.items() if re.search(p, reason, re.I)]
        if re.search(r"\bconsulting\b", reason, re.I) and firms.search(L.get("Company") or ""):
            v.append("G3a named firm")
        if c and not v:
            shaped.append({"Job_ID": jid, "Company": L.get("Company"), "Verdict": L.get("Verdict"),
                           "Score": score(L), "gate": c[0], "Reason": reason})
    n_since = sum(1 for L in log.values() if (L.get("Date_Evaluated") or "")[:10] >= added)
    return {"n_review_verdicts": n_review, "rows_since_added": n_since,
            "review_shaped": shaped, "added": added}


# ---------------------------------------------------------------- presentation

def one_line(r):
    why = r["Reason"] or (r["Biggest_Gap"][:70] + "..." if r["Biggest_Gap"] else "(no reason recorded)")
    return (f"| {r['Job_ID']} | {r['Company'][:34]} | {r['Role_Title'][:52]} | "
            f"{r['Score'] if r['Score'] is not None else '—'} | {why[:64]} |")


CRIT_TITLES = {
    "band_60_69":    "Score band 60-69 (Skip) — the band most likely to hold a wrongly-rejected role",
    "gate_DIR":      "Director+ seniority screen",
    "gate_G11":      "G11 — domain gate (stated years-of-industry / clearance requirement)",
    "gate_G10":      "G10 — stack absence (zero Tier-1/Tier-2, a Tier-3 platform is the primary tooling)",
    "gate_G12":      "G12 — recurring international travel",
    "gate_G6":       "G6 — industry exclusion",
    "gate_PMS":      "People-management scope",
    "pm_deduction":  "-10 people-management deduction, landing 60-69",
    "bridge_unacted":"Bridge candidates (Lane 12, 65-69) Carl did not act on",
}
CRIT_ORDER = ["band_60_69", "bridge_unacted", "gate_DIR", "gate_PMS", "pm_deduction",
              "gate_G11", "gate_G10", "gate_G12", "gate_G6"]


def render(rows, rates, disc, review, cutoff, window_days, args):
    unacted  = [r for r in rows if not r["Carls_Action"]]
    override = [r for r in rows if r["Carls_Action"] == "Applied" and not r["pre_dated"]]
    pre      = [r for r in rows if r["Carls_Action"] == "Applied" and r["pre_dated"]]
    passed   = [r for r in rows if r["Carls_Action"] == "Pass"]
    other    = [r for r in rows if r["Carls_Action"] not in ("", "Applied", "Pass")]

    L = []
    L.append(f"# Phase F — recall audit, {TODAY.isoformat()}")
    L.append("")
    L.append(f"Window: {window_days} days ({cutoff} to {TODAY.isoformat()}). "
             f"{len(rows)} row(s) selected.")
    L.append("")
    L.append("## Carl has already answered these with his feet")
    L.append("")
    L.append(f"Of the {len(rows)} audited rows: **{len(override)} the filter marked Skip and "
             f"Carl applied to afterwards** — a real override, no question needed. "
             f"{len(pre)} more carry an application he made *before* the row was ever "
             f"evaluated. {len(passed)} he explicitly passed on, {len(other)} carry another "
             f"action, and {len(unacted)} are unanswered.")
    L.append("")
    if override:
        L.append("### Overrides — the gate fired, Carl applied anyway")
        L.append("")
        L.append("| Job_ID | Company | Title | Score | what killed it |")
        L.append("|---|---|---|---|---|")
        L += [one_line(r) for r in override]
        L.append("")
    if pre:
        L.append(f"### Applied before evaluation — not overrides ({len(pre)})")
        L.append("")
        L.append("The 2026-08-12 backfill retro-logged Carl's application history and scored "
                 "every row under the current rubric. These are applications he made weeks or "
                 "months before the gate that now shows against them existed. **The gate never "
                 "had a chance to stop him, so it did not fail.** They are excluded from the "
                 "override rate and from the recall ratio.")
        L.append("")
        L.append("| Job_ID | Company | evaluated | applied | Score | what now shows against it |")
        L.append("|---|---|---|---|---|---|")
        for r in sorted(pre, key=lambda r: r["Carls_Action_Date"]):
            L.append(f"| {r['Job_ID']} | {r['Company'][:30]} | {r['Date_Evaluated']} | "
                     f"{r['Carls_Action_Date']} | {r['Score']} | {r['Reason'][:44]} |")
        L.append("")

    L.append("## Override rate per gate")
    L.append("")
    L.append("Of the rows each gate killed, how many did Carl apply to **afterwards**. "
             f"Boundaries are rubric-learn.py's own: <= {VETO_MAX:.0%} veto, "
             f">= {REVIEW_MIN:.0%} review. None of these gates is in `weights.json`'s `rules` "
             "dict, so none has ever been measured before.")
    L.append("")
    L.append("| gate | fired | override | applied first | passed | raw rate | true rate | class |")
    L.append("|---|---|---|---|---|---|---|---|")
    for k in sorted(rates, key=lambda k: -(rates[k]["rate"] or 0)):
        m = rates[k]
        r  = "—" if m["rate"] is None else f"{m['rate']:.0%}"
        rr = "—" if m["raw_rate"] is None else f"{m['raw_rate']:.0%}"
        L.append(f"| {k} {m['label']} | {m['n_fired']} | {m['n_override']} | "
                 f"{m['n_pre_dated']} | {m['n_passed']} | {rr} | {r} | "
                 f"{m['measured_class'] or '—'} |")
    L.append("")
    L.append("**`raw rate` is the number this audit would have reported without the ordering "
             "check, and it is wrong.** `applied first` counts applications Carl made before "
             "the row existed. Where the two columns diverge, the raw figure is measuring the "
             "2026-08-12 backfill, not the filter.")
    L.append("")

    L.append("## Unanswered — the audit list")
    L.append("")
    L.append("One line each. The question is the same for all of them: **were any of these "
             "worth a look?**")
    L.append("")
    seen = set()
    for crit in CRIT_ORDER:
        group = [r for r in unacted if crit in r["criteria"] and r["Job_ID"] not in seen]
        if not group:
            continue
        for r in group:
            seen.add(r["Job_ID"])
        L.append(f"### {CRIT_TITLES[crit]}  ({len(group)})")
        L.append("")
        L.append("| Job_ID | Company | Title | Score | what killed it |")
        L.append("|---|---|---|---|---|")
        L += [one_line(r) for r in group]
        L.append("")
    L.append("*Each row appears once, under the first criterion that selected it; a row may "
             "have matched several.*")
    L.append("")

    L.append("## Gate-label discrepancies (reported, not selected on)")
    L.append("")
    L.append("| gate | rows whose text names it but whose `Reason` does not |")
    L.append("|---|---|")
    for g, n in disc.items():
        L.append(f"| {g} | {n} |")
    L.append("")
    L.append("Most of these record a gate that was checked and correctly did not fire. "
             "A cluster on one gate would mean the `Reason` wording has drifted from the rubric.")
    L.append("")

    L.append("## `Review` — the fourth verdict")
    L.append("")
    rv = review
    L.append(f"`Verdict = \"Review\"` has appeared **{rv['n_review_verdicts']}** time(s) in the "
             f"log since it was added {rv['added']}. {rv['rows_since_added']} row(s) have been "
             f"evaluated since.")
    if rv["review_shaped"]:
        L.append("")
        L.append("Rows where a compensable gate fired and no veto-class gate did — these should "
                 "have been `Review`:")
        L.append("")
        L.append("| Job_ID | Company | got | score | gate |")
        L.append("|---|---|---|---|---|")
        for s in rv["review_shaped"]:
            L.append(f"| {s['Job_ID']} | {s['Company']} | {s['Verdict']} | {s['Score']} | {s['gate']} |")
        L.append("")
        L.append("**That is a broken rule, not an absent opportunity.**")
    else:
        L.append("")
        L.append("**Zero rows since then were Review-shaped** — no compensable gate fired "
                 "without a veto-class gate also firing. The verdict is untested, not dead: "
                 "it has had no opportunity, so nothing is proven either way. Look again next "
                 "month.")
    L.append("")
    return "\n".join(L), unacted, override


def render_ask(theme, control, pool_n, control_n):
    """The short list Carl actually answers, with the two buckets kept visibly apart."""
    L = ["", "---", "", "# The ask", "",
         f"**{len(theme) + len(control)} rows**, not the whole unanswered list. Two buckets, "
         f"answered the same way but counted separately.", ""]
    if theme:
        L += [f"## Theme shortlist ({len(theme)}) — rows matching a rule Carl already stated", "",
              "A high hit rate here is expected: these were picked because they match. It "
              "measures what the rule is worth, not recall.", "",
              "| Job_ID | Company | Title | Score | what killed it |", "|---|---|---|---|---|"]
        L += [one_line(r) for r in sorted(theme, key=lambda r: -(r["Score"] or 0))]
        L.append("")
    if control:
        L += [f"## Random control ({len(control)} drawn from {pool_n}) — the actual recall estimate",
              "", "Drawn at random, seeded on the window so the draw is reproducible. This is "
              "the only bucket that generalizes, and the only one that can surface a theme "
              "nobody has named.", "",
              "| Job_ID | Company | Title | Score | what killed it |", "|---|---|---|---|---|"]
        L += [one_line(r) for r in sorted(control, key=lambda r: -(r["Score"] or 0))]
        L.append("")
    return "\n".join(L)


def build_ask(rows, ask_ids, control_n, seed_key):
    """Split the unanswered rows into the theme shortlist and a seeded random control.

    The seed is the window, not the clock, so re-running the same window redraws the same
    control sample. A control sample that changes on every run is not a control.
    """
    unanswered = [r for r in rows if not r["Carls_Action"]]
    known = {r["Job_ID"] for r in unanswered}
    missing = [i for i in ask_ids if i not in known]
    if missing:
        sys.exit(f"\n  HALT: --ask names {len(missing)} row(s) that are not unanswered in this "
                 f"window: {', '.join(missing[:5])}\n  A shortlist may only name rows the audit "
                 f"actually selected and Carl has not already answered.\n")
    theme = [r for r in unanswered if r["Job_ID"] in set(ask_ids)]
    pool  = [r for r in unanswered if r["Job_ID"] not in set(ask_ids)]
    rng = random.Random(f"recall-audit:{seed_key}")
    control = rng.sample(pool, min(control_n, len(pool)))
    for r in theme:
        r["bucket"] = "theme"
    for r in control:
        r["bucket"] = "control"
    return theme, control, len(pool)


def answer_template(rows, unacted, override, cutoff, window_days, path):
    tpl = {
        "generated": TODAY.isoformat(),
        "window_days": window_days,
        "cutoff": cutoff,
        "n_selected": len(rows),
        "n_excluded_applied_before_evaluation": sum(1 for r in rows if r["pre_dated"]),
        "_answers": sorted(ANSWERS),
        "_note": ("Fill in `answer` for each row. `already_applied` is pre-filled for rows the "
                  "pull shows Carl applied to — do not change those. Anything left as null is "
                  "counted as unanswered, not as 'not wanted'."),
        "rows": [],
    }
    for r in rows:
        # An application Carl made before the row was evaluated is not a question and not a
        # recall hit — the gate never had a chance to stop him. It leaves the file entirely
        # rather than sitting in it pre-answered, where it would inflate the ratio.
        if r["pre_dated"]:
            continue
        pre = "already_applied" if r["Carls_Action"] == "Applied" else None
        tpl["rows"].append({
            "Job_ID": r["Job_ID"], "Company": r["Company"], "Role_Title": r["Role_Title"],
            "Score": r["Score"],
            # 6 of 549 Skip rows carry no Reason (measured 2026-08-28). The rubric requires
            # one on a gate kill, so fall back to Biggest_Gap rather than record an em-dash.
            "Reason": r["Reason"] or (r["Biggest_Gap"][:80] if r["Biggest_Gap"] else ""),
            "criteria": r["criteria"],
            "bucket": r.get("bucket", "all"),
            "answer": pre, "note": "",
        })
    with open(path, "w") as f:
        json.dump(tpl, f, indent=2)


# ---------------------------------------------------------------- record

def record(args):
    """Append Carl's answers and the recall ratio to rubric/learning_log.md.

    Refuses anything it cannot verify. The learning log is the only durable record of the
    ratio, and a wrong number there outlives the run that produced it.
    """
    if not os.path.exists(args.record):
        sys.exit(f"\n  HALT: {rel(args.record)} not found.\n")
    learning = args.learning_log
    if not os.path.exists(learning):
        sys.exit(f"\n  HALT: {rel(learning)} not found. Phase F records into the existing "
                 f"learning log; it does not create one.\n")
    data = json.load(open(args.record))
    rows = data.get("rows") or []
    if not rows:
        sys.exit("\n  HALT: no rows in the answer file.\n")

    log, pull = load_sources(args)
    bad = [r["Job_ID"] for r in rows if r["Job_ID"] not in log]
    if bad:
        sys.exit(f"\n  HALT: {len(bad)} Job_ID(s) in the answer file are not in the log: "
                 f"{', '.join(bad[:5])}\n  An audit answer must name a row that exists.\n")
    wrong = [(r["Job_ID"], r.get("answer")) for r in rows
             if r.get("answer") is not None and r.get("answer") not in ANSWERS]
    if wrong:
        sys.exit(f"\n  HALT: unrecognized answer(s): "
                 f"{', '.join(f'{j}={a}' for j, a in wrong[:5])}\n"
                 f"  Allowed: {', '.join(sorted(ANSWERS))}\n")

    answered = [r for r in rows if r.get("answer") is not None]
    unanswered = len(rows) - len(answered)
    # The denominator is what Carl was actually asked about. A closed posting is not a
    # question he can answer, so it leaves the ratio entirely rather than counting as a no.
    scored = [r for r in answered if r["answer"] != "closed"]
    wanted = [r for r in scored if r["answer"] in WANTED]
    closed = [r for r in answered if r["answer"] == "closed"]
    ratio = f"{len(wanted)} of {len(scored)}" if scored else "0 of 0"

    def sub(bucket):
        sc = [r for r in scored if r.get("bucket") == bucket]
        wt = [r for r in sc if r["answer"] in WANTED]
        return len(wt), len(sc)
    t_w, t_n = sub("theme")
    c_w, c_n = sub("control")

    e = [f"\n## {TODAY.isoformat()} — Phase F recall audit\n",
         f"Window: {data.get('window_days', '?')} days "
         f"({data.get('cutoff', '?')} to {TODAY.isoformat()}). "
         f"{data.get('n_selected', len(rows))} row(s) selected, {len(answered)} answered, "
         f"{unanswered} left unanswered, {len(closed)} closed and out of the ratio.\n",
         f"**Recall estimate: {ratio} audited rows were wanted.**\n"]
    if t_n or c_n:
        e.append(f"\nSplit by bucket — **these do not pool**:\n")
        if t_n:
            e.append(f"- **Theme shortlist: {t_w} of {t_n}.** Rows chosen because they match a "
                     f"rule Carl had already stated, so a high rate is expected. This measures "
                     f"what that rule is worth, not recall.")
        if c_n:
            e.append(f"- **Random control: {c_w} of {c_n}.** Drawn at random from everything "
                     f"else. **This is the recall estimate** — the only figure here that "
                     f"generalizes to the rows nobody read.")
        if c_n and c_w == 0:
            e.append(f"\nZero flags in the control: no unnamed theme is visible in this window "
                     f"at n={c_n}. That is weak evidence, not proof — {c_n} rows cannot rule out "
                     f"a pattern that affects a handful.")
        e.append("")
    # The protocol's "three or more means something is too tight" line is a statement about
    # RECALL, so it is measured on the control sample alone. Firing it on the theme shortlist
    # would let a rule Carl already stated prove itself — the rows were picked for it.
    judged_w, judged_n, basis = (c_w, c_n, "control sample") if c_n else \
                                (len(wanted), len(scored), "audited rows")
    if judged_w >= 3:
        e.append(f"That is at or above the protocol's own \"three or more means something is "
                 f"too tight\" line, measured on the {basis}.\n")
    elif judged_w == 0 and judged_n:
        e.append(f"Zero flags in the {basis} — the gates are calibrated for this window.\n")
    if c_n and len(wanted) >= 3 > c_w:
        e.append(f"**The pooled count ({len(wanted)}) is not the recall figure and must not be "
                 f"read as one.** It is carried by the theme shortlist, whose rows were "
                 f"selected because Carl had already said he wanted that shape.\n")

    if wanted:
        e += ["\n### Rows Carl wanted\n",
              "| posting | score | what killed it | answer | note |",
              "|---|---|---|---|---|"]
        for r in sorted(wanted, key=lambda r: -(r["Score"] or 0)):
            e.append(f"| {r['Company']} — {r['Role_Title']} | {r['Score']} | "
                     f"{r['Reason'] or '—'} | {r['answer']} | {r.get('note') or ''} |")

    declined = [r for r in scored if r["answer"] not in WANTED and (r.get("note") or "").strip()]
    if declined:
        e += ["\n### Rows Carl declined, with his reasoning\n",
              "Kept because a *why-not* often carries more signal than a yes — a borderline he "
              "would look at under a different rule, or a fact the JD never showed.\n",
              "| posting | score | what killed it | note |", "|---|---|---|---|"]
        for r in sorted(declined, key=lambda r: -(r["Score"] or 0)):
            e.append(f"| {r['Company']} — {r['Role_Title']} | {r['Score']} | "
                     f"{r['Reason'] or '—'} | {r['note']} |")

    # Which gate the wanted rows were killed by. A repeat offender is the finding; one row is not.
    by_gate = {}
    for r in wanted:
        for c in r.get("criteria") or []:
            by_gate[c] = by_gate.get(c, 0) + 1
    if by_gate:
        e.append("\n### Which criterion surfaced them\n")
        for c, n in sorted(by_gate.items(), key=lambda kv: -kv[1]):
            e.append(f"- **{CRIT_TITLES.get(c, c)}** — {n}")
        repeat = [c for c, n in by_gate.items()
                  if n >= 3 and (c.startswith("gate_") or c == "pm_deduction")]
        if repeat:
            e.append(f"\n**Over-firing, on this window's evidence:** "
                     f"{', '.join(CRIT_TITLES.get(c, c) for c in repeat)}. "
                     f"Bring the pattern back with the evidence; do not loosen it silently.")
        band = by_gate.get("band_60_69", 0)
        if band >= 3:
            e.append(f"\n**{band} of the wanted rows were surfaced by the 60-69 score band, not "
                     f"by a gate.** That is not a gate over-firing — it is the score threshold "
                     f"placing roles Carl wants just under 70. The question it raises is about "
                     f"component weights, which is `rubric-learn.py`'s measurement, not this "
                     f"one. Look at what those rows have in common before moving anything.")

    e.append(f"\n**Status:** recorded. Nothing in the rubric changed. "
             f"Full list: `{rel(args.out_md) if args.out_md else 'scratch/'}`.\n")

    with open(learning, "a") as f:
        f.write("\n".join(e) + "\n")
    print(f"\n  Recorded to {rel(learning)}", file=sys.stderr)
    print(f"  Recall estimate: {ratio} wanted"
          f"{f' ({len(closed)} closed, excluded)' if closed else ''}\n", file=sys.stderr)


# ---------------------------------------------------------------- self-test

def self_test():
    cutoff = (TODAY - datetime.timedelta(days=30)).isoformat()
    inside = TODAY.isoformat()
    outside = (TODAY - datetime.timedelta(days=45)).isoformat()
    ok = True

    def check(name, got, want):
        nonlocal ok
        if got != want:
            ok = False
            print(f"  FAIL {name}: got {got}, want {want}")
        else:
            print(f"  ok   {name}")

    def C(L, P):
        return sorted(classify(L.get("Job_ID", "x"), L, P, cutoff))

    base = {"Job_ID": "1", "Date_Evaluated": inside, "Verdict": "Skip", "Score": "65", "Reason": ""}

    check("60-69 Skip selects",
          C({**base}, {}), ["band_60_69"])
    check("59 Skip does not",
          C({**base, "Score": "59"}, {}), [])
    check("70 Skip does not",
          C({**base, "Score": "70"}, {}), [])
    check("outside the window does not",
          C({**base, "Date_Evaluated": outside}, {}), [])
    check("Pursue in the band does not",
          C({**base, "Verdict": "Pursue"}, {}), [])
    check("director+ scope selects even at score 20",
          C({**base, "Score": "20", "Reason": "director+ scope"}, {}), ["gate_DIR"])
    check("domain gate selects",
          C({**base, "Score": "35", "Reason": "government clearance domain gate"}, {}), ["gate_G11"])
    check("wrong stack selects",
          C({**base, "Score": "40", "Reason": "wrong stack (Cognos/SAS)"}, {}), ["gate_G10"])
    check("industry exclusion selects",
          C({**base, "Score": "30", "Reason": "industry exclusion (cannabis)"}, {}), ["gate_G6"])
    check("posting-status reason never selects a gate",
          C({**base, "Score": "35", "Reason": "no longer accepting applications"}, {}), [])
    check("a gate LABEL in Notes does not select",
          C({**base, "Score": "75", "Verdict": "Pursue",
             "Notes": "G10 checked and did not fire; G11 n/a"}, {}), [])
    check("Pts_Scope 0 in band selects the deduction",
          C({**base}, {"Pts_Scope": "0"}), ["band_60_69", "pm_deduction"])
    check("Pts_Scope 0 outside the band does not",
          C({**base, "Score": "35"}, {"Pts_Scope": "0"}), [])
    check("Lane 12 at 65-69, unactioned, is a bridge",
          C({**base}, {"Pts_Lane": "12"}), ["band_60_69", "bridge_unacted"])
    check("Lane 12 at 64 is not a bridge",
          C({**base, "Score": "64"}, {"Pts_Lane": "12"}), ["band_60_69"])
    check("Lane 12 Carl already actioned is not a bridge",
          C({**base}, {"Pts_Lane": "12", "Carls_Action": "Pass"}), ["band_60_69"])
    check("blank score selects nothing",
          C({**base, "Score": ""}, {}), [])

    # override-rate arithmetic
    log = {"a": {"Verdict": "Skip", "Reason": "director+ scope"},
           "b": {"Verdict": "Skip", "Reason": "director+ scope"},
           "c": {"Verdict": "Skip", "Reason": "director+ scope"},
           "d": {"Verdict": "Skip", "Reason": "director+ scope"},
           "e": {"Verdict": "Pass", "Reason": "no longer accepting applications"}}
    pull = {"a": {"Carls_Action": "Applied"}, "b": {"Carls_Action": ""},
            "c": {"Carls_Action": "Pass"}, "d": {"Carls_Action": ""}}
    r = override_rates(log, pull)["DIR"]
    check("override rate counts blanks in the denominator", (r["n_fired"], r["n_applied"]), (4, 1))
    check("override rate classes at 25%", r["measured_class"], "review")

    # the ordering rule — the 2026-08-28 finding
    check("applied a month before evaluation is not an override",
          applied_before_evaluation({"Date_Evaluated": "2026-08-12"},
                                    {"Carls_Action_Date": "2026-07-15"}), True)
    check("applied after evaluation is an override",
          applied_before_evaluation({"Date_Evaluated": "2026-08-12"},
                                    {"Carls_Action_Date": "2026-08-22"}), False)
    check("same day is an override (ties go against the gate)",
          applied_before_evaluation({"Date_Evaluated": "2026-08-12"},
                                    {"Carls_Action_Date": "2026-08-12"}), False)
    check("a missing action date is not a pre-date",
          applied_before_evaluation({"Date_Evaluated": "2026-08-12"},
                                    {"Carls_Action_Date": ""}), False)
    check("a missing eval date is not a pre-date",
          applied_before_evaluation({"Date_Evaluated": ""},
                                    {"Carls_Action_Date": "2026-08-12"}), False)

    log2 = {f"r{i}": {"Verdict": "Skip", "Reason": "director+ scope",
                      "Date_Evaluated": "2026-08-12"} for i in range(4)}
    pull2 = {"r0": {"Carls_Action": "Applied", "Carls_Action_Date": "2026-07-01"},   # backfill
             "r1": {"Carls_Action": "Applied", "Carls_Action_Date": "2026-07-02"},   # backfill
             "r2": {"Carls_Action": "Applied", "Carls_Action_Date": "2026-08-20"},   # override
             "r3": {"Carls_Action": ""}}
    m = override_rates(log2, pull2)["DIR"]
    check("backfilled applications leave the numerator",
          (m["n_applied"], m["n_override"], m["n_pre_dated"]), (3, 1, 2))
    check("raw rate and true rate diverge", (m["raw_rate"], m["rate"]), (0.75, 0.25))

    print("\n  self-test PASSED" if ok else "\n  self-test FAILED")
    return 0 if ok else 1


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description="Phase F — monthly Skip audit (recall check).")
    ap.add_argument("--window-days", type=int, default=30)
    ap.add_argument("--pull", default=PULL)
    ap.add_argument("--max-pull-age-minutes", type=int, default=120)
    ap.add_argument("--skip-pull-check", action="store_true",
                    help="run against a stale/missing pull; prints exactly what goes unseen")
    ap.add_argument("--record", metavar="ANSWERS.json",
                    help="record Carl's answers into rubric/learning_log.md")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--ask", default="",
                    help="comma-separated Job_IDs for the theme shortlist")
    ap.add_argument("--control-sample", type=int, default=0,
                    help="draw N random rows from everything else as the unbiased control")
    ap.add_argument("--out-md")
    ap.add_argument("--learning-log", default=LEARNING,
                    help="where --record appends (override only to rehearse a record run)")
    args = ap.parse_args()

    if args.self_test:
        return self_test()

    stamp = TODAY.strftime("%Y%m%d")
    args.out_md = args.out_md or os.path.join(SCRATCH, f"recall_audit_{stamp}.md")
    out_json = os.path.join(SCRATCH, f"recall_answers_{stamp}.json")

    require_pull(args)

    if args.record:
        return record(args)

    log, pull = load_sources(args)
    rows, cutoff = select(log, pull, args.window_days)
    rates = override_rates(log, pull)
    disc = label_discrepancies(log)
    review = review_verdict_check(log)
    md, unacted, override = render(rows, rates, disc, review, cutoff, args.window_days, args)

    os.makedirs(SCRATCH, exist_ok=True)
    with open(args.out_md, "w") as f:
        f.write(md + "\n")
    ask_ids = [i.strip() for i in args.ask.split(",") if i.strip()]
    if ask_ids or args.control_sample:
        theme, control, pool_n = build_ask(rows, ask_ids, args.control_sample,
                                           f"{cutoff}:{TODAY.isoformat()}")
        answer_template(theme + control, unacted, override, cutoff, args.window_days, out_json)
        with open(args.out_md, "a") as f:
            f.write(render_ask(theme, control, pool_n, args.control_sample) + "\n")
        print(f"\n  ask           theme shortlist {len(theme)} + random control "
              f"{len(control)} (drawn from {pool_n}) = {len(theme) + len(control)} to answer",
              file=sys.stderr)
    else:
        answer_template(rows, unacted, override, cutoff, args.window_days, out_json)

    e = sys.stderr
    print(f"\n  window        {args.window_days} days ({cutoff} -> {TODAY.isoformat()})", file=e)
    print(f"  selected      {len(rows)} row(s)", file=e)
    pre_n = sum(1 for r in rows if r["pre_dated"])
    print(f"    overrides (gate fired, Carl applied after)  : {len(override)}", file=e)
    print(f"    applied BEFORE evaluation (not overrides)   : {pre_n}", file=e)
    print(f"    unanswered, needing Carl's eye              : {len(unacted)}", file=e)
    print(f"\n  {'gate':<24}{'fired':>6}{'override':>9}{'raw':>7}{'true':>7}  measured", file=e)
    for k in sorted(rates, key=lambda k: -(rates[k]["rate"] or 0)):
        m = rates[k]
        r  = "—" if m["rate"] is None else f"{m['rate']:.0%}"
        rr = "—" if m["raw_rate"] is None else f"{m['raw_rate']:.0%}"
        flag = "  <- REVIEW-CLASS" if m["measured_class"] == "review" else ""
        print(f"  {k + ' ' + m['label']:<24}{m['n_fired']:>6}{m['n_override']:>9}"
              f"{rr:>7}{r:>7}  {m['measured_class'] or '—'}{flag}", file=e)
    print(f"\n  -> {rel(args.out_md)}\n  -> {rel(out_json)}", file=e)
    print(f"  Nothing was written to JD_Evaluation_Log.csv. Answer the JSON, then "
          f"--record it.\n", file=e)
    return 0


if __name__ == "__main__":
    sys.exit(main())
