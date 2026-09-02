#!/usr/bin/env python3
"""Generate a synthetic JD evaluation log matching the real schema.

The real log holds 1,066 rows of genuine job evaluations — named employers,
private assessments of each, and compensation judgments. None of that belongs
in a public repository, but the *shape* of the data does: without it, the
score-component parsing in the Dataflow Gen2 M code and the rubric's
capped-score handling are impossible to follow.

So this produces fabricated rows with the same 24-column schema, the same
value distributions, and — critically — the same `Notes` grammar, because the
Notes field is what the parsing logic keys on:

    "Score 62 = Lane 12 + Scope 8 + Comp 12 + Location 10 + Skills 14 +
     Applicants 6. Capped from 78 ..."

Everything here is invented. Any resemblance to a real posting is coincidence.

Usage:
    python3 generate-sample-log.py --rows 60 --out sample.csv
    python3 generate-sample-log.py --rows 1000 --seed 7    # bigger, still deterministic
"""
from __future__ import annotations

import argparse
import csv
import random
import sys
from datetime import date, timedelta

COLUMNS = [
    "Job_ID", "Date_Evaluated", "Company", "Role_Title", "Location", "Work_Type",
    "Employment_Type", "Comp_Posted", "Applicant_Volume", "Source", "URL",
    "Verdict", "Score", "Role_Type", "Comp_Flag", "Biggest_Gap",
    "Biggest_Strength", "Recommended_Action", "Carls_Action", "Carls_Action_Date",
    "Outcome", "Reason", "Notes", "Score_Raw",
]

# Invented employers, deliberately generic so none collides with a real firm.
COMPANIES = [
    "Northwind Analytics", "Vantage Grid", "Cobalt Reach", "Meridian Data Co",
    "Bright Fen Systems", "Halcyon Retail Group", "Ironwood Health", "Tessellate AI",
    "Quarry Lane Logistics", "Blue Ridge Insurance", "Parallax Manufacturing",
    "Cedar & Vale", "Openfield Energy", "Summit Row Financial", "Larkspur Media",
    "Foundry Nine", "Willow Bank Credit Union", "Anvil Freight", "Perihelion Labs",
    "Greystone Public Sector",
]
STAFFING = ["Apex Talent Partners", "Bridgeway Staffing", "Northgate Recruiting"]

ROLES = [
    "Business Intelligence Analyst", "Senior BI Developer", "Data Architect",
    "Analytics Engineer", "Power BI Developer", "Manager, Data & Analytics",
    "Senior Data Analyst", "BI Engineering Lead", "Director of Analytics",
    "Reporting & Insights Manager", "Fabric Data Engineer",
]
CITIES = [
    "Nashville, TN", "Remote (US)", "Atlanta, GA", "Charlotte, NC", "Austin, TX",
    "Columbus, OH", "Franklin, TN", "United States", "Brentwood, TN", "Chicago, IL",
]
WORK_TYPES = [
    "Remote", "Hybrid (2 days onsite)", "Onsite",
    "Remote-first (confirmed on both the posting and the company career site)",
]
EMPLOYMENT = ["Full-time", "Full-time (W2)", "Contract (12 months)", "Contract-to-hire"]
SOURCES = ["LinkedIn job alert", "LinkedIn saved search", "Recruiter message"]

# Rubric components, mirroring the real Pts_* set.
COMPONENTS = ["Lane", "Scope", "Comp", "Location", "Skills", "Perks", "Applicants"]

GAPS = [
    "Fixed-term contract rather than a permanent role",
    "Comp tops out below the floor for the posted band",
    "Job is delivery/consulting shaped rather than product-side ownership",
    "Title reads senior but the body describes an IC reporting role",
    "Stack is Snowflake-core with Power BI as a secondary surface",
    "Heavy people-management with little hands-on modelling",
]
STRENGTHS = [
    "Explicit semantic-model ownership named in the responsibilities",
    "Direct match to the Fabric / Power BI stack already in use",
    "Governed reporting layer that program teams consume directly",
    "Remote-first and the posted state list includes the target state",
    "Clear analytics-engineering lane rather than generic BI support",
]
REASONS_PASS = [
    "consulting delivery role", "director+ scope", "low comp",
    "data engineering, not BI", "contract; sub-target comp",
    "no longer accepting applications", "analyst-level scope",
]
ACTIONS = ["Applied", "Pass", "Referral Requested", "Withdrew", "None", ""]
OUTCOMES = ["", "", "", "", "Interview", "Rejected", "No Response",
            "Interview; Rejected", "Interview; Offer"]


def build_notes(rng, score_raw, capped, comps):
    """Notes text carrying the formula clause the Dataflow M code parses.

    Two shapes matter to downstream parsing:
      * a plain "Score N = Lane a + Scope b + ..." clause, and
      * a "capped from N" variant, where the arithmetic deliberately does not
        reconcile against the visible components. 26% of the real rows look
        like this, which is why deductions are only computed for the rest.
    """
    parts = " + ".join(f"{name} {pts}" for name, pts in comps)
    shown = min(score_raw, 70) if capped else score_raw
    clause = f"Score {shown} = {parts}."
    if capped:
        clause += f" Capped from {score_raw} (rubric ceiling for this lane applied)."
    gate = rng.choice([
        " G1 fires: fixed-term language in the body -> Review-class, deduction applied.",
        " G2b fires: top of posted range sits in the VETO_LINE-FLOOR band.",
        " G3b fires: client-delivery shape rather than product ownership.",
        "",
    ])
    return clause + gate


def make_row(rng, i, today):
    capped = rng.random() < 0.26           # matches the measured capped share
    evaluated = rng.random() < 0.94        # ~6% arrive unevaluated

    comps = []
    for name in COMPONENTS:
        if name == "Perks" and rng.random() < 0.57:
            continue                        # Perks is genuinely absent ~57% of the time
        comps.append((name, rng.randint(0, 20)))
    score_raw = sum(p for _, p in comps)
    score = min(score_raw, 70) if capped else score_raw

    is_staffing = rng.random() < 0.18
    company = rng.choice(STAFFING if is_staffing else COMPANIES)
    verdict = rng.choices(
        ["Skip", "Pass", "Pursue", "Review", "Not evaluated"],
        weights=[58, 19, 15, 5, 3],
    )[0]
    if not evaluated:
        verdict = "Not evaluated"

    d_eval = today - timedelta(days=rng.randint(0, 45))
    action = rng.choice(ACTIONS) if verdict in ("Pursue", "Review") else rng.choice(
        ["Pass", "", "", "None"])
    d_action = ""
    if action and action != "None" and rng.random() < 0.8:
        # occasionally negative: applied before the posting was ever scored
        offset = rng.randint(-6, 21)
        d_action = (d_eval + timedelta(days=offset)).isoformat()

    lo = rng.randrange(95, 190) * 1000
    hi = lo + rng.randrange(15, 60) * 1000
    comp_posted = "" if rng.random() < 0.42 else f"${lo:,}.00 - ${hi:,}.00"

    return {
        "Job_ID": 4_400_000_000 + i * rng.randint(101, 997),
        "Date_Evaluated": d_eval.isoformat(),
        "Company": company,
        "Role_Title": rng.choice(ROLES),
        "Location": rng.choice(CITIES),
        "Work_Type": rng.choice(WORK_TYPES),
        "Employment_Type": rng.choice(EMPLOYMENT),
        "Comp_Posted": comp_posted,
        "Applicant_Volume": rng.choice(
            ["", f"{rng.randint(3, 99)} applicants", "Over 100 applicants",
             f"{rng.randint(10, 80)} clicked apply"]),
        "Source": rng.choice(SOURCES),
        "URL": f"https://example.invalid/jobs/{rng.randrange(10**9, 10**10)}",
        "Verdict": verdict,
        "Score": score if evaluated else "",
        "Role_Type": rng.choice(["BI / Analytics", "Data Engineering",
                                 "Analytics Leadership", "Consulting Delivery"]),
        "Comp_Flag": rng.choice(
            ["None (>=TARGET)", "Sub-target (FLOOR-TARGET)",
             "Below floor (VETO_LINE-FLOOR)", "Below veto line (<VETO_LINE)", ""]),
        "Biggest_Gap": rng.choice(GAPS) if evaluated else "",
        "Biggest_Strength": rng.choice(STRENGTHS) if evaluated else "",
        "Recommended_Action": rng.choice(
            ["Pursue - strong lane match", "Pass - fails the comp gate",
             "Review (judgment call) - compensable gate fired, no veto",
             "Skip - delivery-shaped role"]) if evaluated else "",
        "Carls_Action": action,
        "Carls_Action_Date": d_action,
        "Outcome": rng.choice(OUTCOMES) if action == "Applied" else "",
        "Reason": rng.choice(REASONS_PASS) if verdict in ("Skip", "Pass") else "",
        "Notes": build_notes(rng, score_raw, capped, comps) if evaluated
                 else "Not evaluated - posting body could not be retrieved.",
        "Score_Raw": score_raw if evaluated else "",
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rows", type=int, default=60)
    ap.add_argument("--seed", type=int, default=1729,
                    help="fixed by default so the committed sample is reproducible")
    ap.add_argument("--out", default="-", help="output path, or - for stdout")
    args = ap.parse_args()

    rng = random.Random(args.seed)
    today = date(2026, 9, 2)   # pinned so regenerating gives identical output
    rows = [make_row(rng, i, today) for i in range(1, args.rows + 1)]

    fh = sys.stdout if args.out == "-" else open(args.out, "w", newline="", encoding="utf-8")
    try:
        w = csv.DictWriter(fh, fieldnames=COLUMNS, quoting=csv.QUOTE_MINIMAL)
        w.writeheader()
        w.writerows(rows)
    finally:
        if fh is not sys.stdout:
            fh.close()
            print(f"wrote {len(rows)} rows -> {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
