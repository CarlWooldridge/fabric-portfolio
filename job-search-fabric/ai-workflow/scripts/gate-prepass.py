#!/usr/bin/env python3
"""
gate-prepass.py — run the mechanical half of the §4.0 hard gates without a model.

instructions/02-evaluate-and-report.md §4.0 defines gates G1-G12. Seven of them are
decidable from fields the intake/fetch stage has already extracted — no JD body, no
judgment, no tokens:

    G2 / G2b  comp thresholds, on the top of the posted BASE range
    G3a       employer on the named consulting-firm list (rubric/weights.json)
    G4        Ladders / staffing board
    G5        named employer exclusions
    G6        industry exclusions
    G7        location gate

G1, G3b, G8, G10, G11 and G12 need the body read and stay with the evaluator. So do the
clauses of the seven above that are body-dependent — see PARTIAL GATES below.

**This script does not set a Verdict, and must not be made to.** It reports which gates it
believes fired. Precedence, the score, and the verdict remain the evaluator's. Wiring the
output into a run is a separate decision, to be taken once the diff below stays clean.

USAGE

    python3 scripts/gate-prepass.py --json scratch/extracted.json
    python3 scripts/gate-prepass.py --json scratch/rescore-results-all.json --quiet

Input is a JSON list of objects using JD_Evaluation_Log.csv field names. Only these are
read: Job_ID, Company, Role_Title, Location, Work_Type, Employment_Type, Comp_Posted,
Source, URL. Judgment fields are ignored even when present.

Output is JSON on stdout, a per-row table on stderr. Each gate gets one of three states:

    fired    the gate fires on the extracted fields
    clear    the gate does not fire
    review   undecidable from the fields — the evaluator has to look

`review` is a first-class answer, not a failure. A pre-pass that guesses is worse than one
that abstains, because a wrong `clear` is invisible.

PARTIAL GATES — what this script deliberately does not decide

    G2/G2b   fires on the POSTED base range only. The gate also reads a *researched*
             figure when comp is unlisted; researching one is not mechanical. Unlisted
             comp returns `review`, never `clear`.
    G4       decides the Ladders clause. The second clause — anonymous end client PLUS
             (contract or sub-target comp) — needs the body to establish anonymity, so a
             recognized staffing intermediary returns `review` with the reason attached.
    G6       never fires on its own. Industry is a fact about the employer, not a string
             in the posting: "Company-84" is not a firearms employer and
             a keyword rule that fires on it is worse than no rule. A keyword hit returns
             `review`; only the evaluator (or Carl) turns that into a gate.
    G7       decides on the location/work-type FIELDS. §4.0's expanded detection is
             explicitly about bodies that contradict a Remote tag — state-restricted
             remote, commuting-distance language, relocation assistance. A `clear` here
             means "the fields do not fire it", never "the body was checked".
"""
import argparse, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
WEIGHTS = os.path.join(ROOT, "rubric", "weights.json")

FIRED, CLEAR, REVIEW = "fired", "clear", "review"
GATES = ["G2", "G2b", "G3a", "G4", "G5", "G6", "G7"]

# --- G5: named employer exclusions -------------------------------------------------
# instructions/03-scoring-rubric.md "Employer exclusions". UMG is location-qualified:
# the exclusion is the Nashville division, so a non-Nashville UMG posting is `review`,
# not `fired` — the rubric says to evaluate those normally and say why it didn't apply.
EMPLOYER_EXCLUSIONS = [
    (r"\bamazon\b",  "Company-30"),
    (r"\boracle\b",  "Company-463"),
    (r"\basurion\b", "Company-59"),
]
UMG = re.compile(r"\buniversal music\b|\bumg\b", re.I)

# --- G6: industry watchlist ---------------------------------------------------------
# A hit is a prompt to look, never a gate. See PARTIAL GATES above.
INDUSTRY_WATCH = [
    (r"\bcannabis\b|\bdispensar|\bcbd\b",                       "cannabis"),
    (r"\bcasino\b|\bgambl|\bsportsbook\b|\bigaming\b|\bbetting\b", "gambling"),
    (r"\badult entertainment\b",                                 "adult"),
    (r"\bfirearm|\bammunition\b|\brifle\b|\bgun[s]?\b",          "firearms"),
    (r"\bmulti[- ]?level marketing\b|\bmlm\b|\bdirect sales\b",  "MLM"),
    (r"\bministr|\bchristian\b|\bfaith\b|\bgospel\b|\bworship\b|\bdiocese\b|\bcatholic\b",
                                                                 "religious content"),
]

# --- G4: staffing intermediaries ----------------------------------------------------
# Not a veto list. These employers post on behalf of someone else often enough that the
# anonymous-end-client clause is worth checking; the body decides whether it fires.
STAFFING_HINT = re.compile(
    r"\bladders\b|\brobert half\b|\blhh\b|\bjobgether\b|\bremotehunter\b|\binsight global\b|"
    r"\bmichael page\b|\bkforce\b|\baerotek\b|\bteksystems\b|\brandstad\b|\badecco\b|"
    r"\bmodis\b|\bcybercoders\b|\bmatrix usa\b|\bsynergy search\b|\bmadison-?davis\b|"
    r"\bhays\b|\bexecu\w*search\b|\brecruit|\bstaffing\b|\btalent (?:group|solutions)\b|"
    r"\bsearch (?:group|partners)\b|\bintuition it\b|\blncsearch\b", re.I)
LADDERS = re.compile(r"\bladders\b", re.I)

# --- G7: Nashville Metro ------------------------------------------------------------
# The rubric names Smyrna, Franklin, Murfreesboro, Brentwood, LaVergne, Spring Hill and
# Nashville itself in the Location scoring tiers; the rest are Davidson-County and MSA
# municipalities that plainly sit inside the same commute. A Tennessee location NOT on
# this list returns `review` rather than firing — a wrong Skip on a commutable TN role
# is the expensive error here, and there are few enough of them to look at by hand.
NASHVILLE_METRO = [
    "nashville", "smyrna", "franklin", "murfreesboro", "brentwood", "la vergne",
    "lavergne", "spring hill", "hermitage", "antioch", "madison", "donelson",
    "bellevue", "green hills", "berry hill", "goodlettsville", "hendersonville",
    "gallatin", "mount juliet", "mt juliet", "lebanon", "columbia", "dickson",
    "springfield", "white house", "nolensville", "thompson's station", "thompsons station",
    "fairview", "ashland city", "portland", "cool springs", "cane ridge",
]
TN = re.compile(r"\btn\b|\btennessee\b", re.I)
REMOTE = re.compile(r"\bremote\b|\bwork from home\b|\bwfh\b|\bdistributed\b", re.I)
NOT_REMOTE = re.compile(r"\bon[- ]?site\b|\bhybrid\b|\bin[- ]?office\b", re.I)

NUM   = r"([\d,]+(?:\.\d+)?)\s*([kK])?"
# A range's second endpoint routinely drops the dollar sign — "$100,300-160,500 USD" is a
# real posting from 2026-08-31, and reading only the first figure turned a $160K role into
# a G2 veto. Match the range as a unit first, then any remaining standalone $ figures.
RANGE = re.compile(r"\$\s*" + NUM + r"\s*(?:-|–|—|to)\s*\$?\s*" + NUM, re.I)
MONEY = re.compile(r"\$\s*" + NUM)
HOURLY = re.compile(r"/\s*hr\b|\bper hour\b|\bhourly\b|\ban hour\b", re.I)


def load_consulting_firms():
    with open(WEIGHTS) as f:
        return json.load(f)["consulting_firms"]


def _num(amt, k):
    try:
        v = float(amt.replace(",", ""))
    except ValueError:
        return None
    if k:
        v *= 1000
    # Under $1,000 and not K-suffixed is a percentage, a headcount or a stray year, not a
    # salary. Dropping it is safer than letting "+ 10% bonus" become a $10 base.
    return int(v) if v >= 1000 else None


def money_values(text):
    """Every salary figure in `text`, as annual-looking integers."""
    out, spans = [], []
    for m in RANGE.finditer(text):
        lo = _num(m.group(1), m.group(2))
        hi = _num(m.group(3), m.group(4) or m.group(2))   # "$180K-200K": carry the K over
        out += [v for v in (lo, hi) if v is not None]
        spans.append(m.span())
    for m in MONEY.finditer(text):
        if any(a <= m.start() < b for a, b in spans):
            continue
        v = _num(m.group(1), m.group(2))
        if v is not None:
            out.append(v)
    return out


def base_top(comp):
    """Top of the posted BASE range, or (None, why).

    §4.0, clarified 2026-08-31: the comp gates read base, never total. Bonus, variable and
    equity earn Compensation points but never lift a posting over a gate — so everything
    after a '+' is dropped, and so is every parenthetical, which is where postings park
    'may grow to $255,694 with tenure/AIP bonus' and 'other market tiers also listed'.
    """
    comp = (comp or "").strip()
    if not comp:
        return None, "comp unlisted — needs research, not a field read"
    if HOURLY.search(comp):
        return None, "hourly rate — annualizing it is an estimate, not a field read"
    head = re.sub(r"\([^)]*\)", " ", comp)       # drop parentheticals
    head = re.split(r"\+", head)[0]              # drop bonus/equity riders
    vals = money_values(head)
    if not vals:
        return None, f"no parseable dollar figure in {comp!r}"
    return max(vals), None


def gate_comp(row):
    """G2 (veto, < VETO_LINE) and G2b (review, VETO_LINE-FLOOR)."""
    top, why = base_top(row.get("Comp_Posted"))
    if top is None:
        return (REVIEW, why), (REVIEW, why)
    veto, floor = W["comp"]["veto_below_usd"], W["comp"]["floor_usd"]
    if top < veto:
        return (FIRED, f"base tops out at ${top:,} (< ${veto:,})"), (CLEAR, None)
    if top < floor:
        return (CLEAR, None), (FIRED, f"base tops out at ${top:,} (${veto:,}-${floor:,} band)")
    return (CLEAR, None), (CLEAR, None)


def gate_consulting(row):
    """G3a — employer on the named consulting-firm list. Word-boundary, never substring:
    a substring match puts 'Company-701' inside 'Seiko' and 'Company-696' inside a random acronym."""
    company = row.get("Company") or ""
    for firm in FIRMS:
        if re.search(r"\b" + re.escape(firm.lower()) + r"\b", company.lower()):
            return FIRED, f"named consulting firm ({firm})"
    return CLEAR, None


def gate_staffing(row):
    """G4 — Ladders clause decided; anonymous-end-client clause deferred."""
    blob = " ".join(str(row.get(f) or "") for f in ("Company", "Source", "URL", "Role_Title"))
    if LADDERS.search(blob):
        return FIRED, "Ladders posting"
    if STAFFING_HINT.search(blob):
        return REVIEW, ("staffing intermediary — clause 2 (anonymous end client + contract "
                        "or sub-target comp) needs the body")
    return CLEAR, None


def gate_employer(row):
    """G5 — named employer exclusions."""
    company = (row.get("Company") or "").lower()
    for pat, name in EMPLOYER_EXCLUSIONS:
        if re.search(pat, company):
            return FIRED, f"employer exclusion ({name})"
    if UMG.search(company):
        loc = row.get("Location") or ""
        if "nashville" in loc.lower():
            return FIRED, "employer exclusion (Christian music) — UMG Nashville"
        return REVIEW, "UMG posting outside Nashville — check the division before scoring"
    return CLEAR, None


def gate_industry(row):
    """G6 — watchlist only. Never fires on its own; see PARTIAL GATES."""
    blob = " ".join(str(row.get(f) or "") for f in ("Company", "Role_Title"))
    for pat, name in INDUSTRY_WATCH:
        if re.search(pat, blob, re.I):
            return REVIEW, f"industry keyword ({name}) in employer/title — confirm what they do"
    return CLEAR, None


def gate_location(row):
    """G7 — location gate, on the fields."""
    wt  = row.get("Work_Type") or ""
    loc = row.get("Location") or ""
    blob = f"{wt} {loc}"

    # "Remote (quarterly on-site trips to Denver HQ)" is Remote; "Remote (tag says On-site;
    # body contradicts)" is the evaluator's own note and also resolves Remote. Take the
    # leading token of Work_Type as the tag, and let Location's own remote language count.
    tag = wt.strip().split("(")[0].strip().lower()
    is_remote = tag.startswith("remote") or (not tag and bool(REMOTE.search(loc)))
    if not is_remote and REMOTE.search(blob) and not NOT_REMOTE.search(blob):
        is_remote = True
    if is_remote:
        return CLEAR, "tagged remote — body may still contradict (§4.0 expanded detection)"

    if not loc.strip():
        return REVIEW, "no location on the row"
    low = loc.lower()
    if any(city in low for city in NASHVILLE_METRO):
        return CLEAR, None
    if TN.search(loc):
        return REVIEW, f"Tennessee location not on the metro list ({loc}) — confirm the commute"
    return FIRED, f"location gate ({loc})"


def evaluate(row):
    g2, g2b = gate_comp(row)
    res = {
        "G2":  g2,
        "G2b": g2b,
        "G3a": gate_consulting(row),
        "G4":  gate_staffing(row),
        "G5":  gate_employer(row),
        "G6":  gate_industry(row),
        "G7":  gate_location(row),
    }
    out = {"Job_ID": str(row.get("Job_ID") or "").strip(),
           "Company": row.get("Company"), "Role_Title": row.get("Role_Title"),
           "gates": {g: {"state": s, "why": w} for g, (s, w) in res.items()},
           "fired":  [g for g in GATES if res[g][0] == FIRED],
           "review": [g for g in GATES if res[g][0] == REVIEW]}
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", required=True, metavar="FILE",
                    help="JSON list of postings using JD_Evaluation_Log.csv field names")
    ap.add_argument("--quiet", action="store_true", help="suppress the per-row table")
    args = ap.parse_args()

    with open(args.json) as f:
        rows = json.load(f)
    if not isinstance(rows, list):
        sys.exit("--json must contain a JSON list.")

    global W, FIRMS
    W = json.load(open(WEIGHTS))
    FIRMS = W["consulting_firms"]

    out = [evaluate(r) for r in rows]
    e = sys.stderr
    if not args.quiet:
        for r in out:
            if not (r["fired"] or r["review"]):
                continue
            print(f"  {r['Job_ID']}  {(r['Company'] or '?')[:32]:<32}", file=e)
            for g in GATES:
                st, why = r["gates"][g]["state"], r["gates"][g]["why"]
                if st == FIRED:
                    print(f"      FIRED  {g:<4} {why}", file=e)
                elif st == REVIEW:
                    print(f"      review {g:<4} {why}", file=e)
    counts = {g: {s: sum(1 for r in out if r["gates"][g]["state"] == s)
                  for s in (FIRED, REVIEW, CLEAR)} for g in GATES}
    print(f"\n  {len(out)} postings\n", file=e)
    print(f"  {'gate':<5} {'fired':>6} {'review':>7} {'clear':>6}", file=e)
    for g in GATES:
        c = counts[g]
        print(f"  {g:<5} {c[FIRED]:>6} {c[REVIEW]:>7} {c[CLEAR]:>6}", file=e)
    print("\n  No Verdict is set by this script — by design.\n", file=e)

    json.dump({"rows": out, "counts": counts}, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
