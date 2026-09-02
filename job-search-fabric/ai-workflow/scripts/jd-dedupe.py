#!/usr/bin/env python3
"""
jd-dedupe.py — partition extracted postings against JD_Evaluation_Log.csv.

Implements Step 2 ("Dedupe — do this before any browsing") of
instructions/01-intake-and-fetch.md
as a deterministic script. This is a set operation on Job_ID plus a normalized
Company+Role_Title comparison; it does not need a language model and should not
consume one. Previously this was done by reading a 1.2 MB / 894-row CSV into
context on every run.

INPUT — either form:

  1. Plain job IDs (exact-match dedupe only):
       python3 scripts/jd-dedupe.py 4454535147 4444368338
       cat ids.txt | python3 scripts/jd-dedupe.py

  2. JSON records (full dedupe + backfill plan) — the useful form, since it
     enables repost detection and tells you which blanks a dupe can fill:
       python3 scripts/jd-dedupe.py --json extracted.json

     extracted.json is a list of objects using JD_Evaluation_Log.csv field names:
       [{"Job_ID": "4454535147", "Company": "Company-331",
         "Role_Title": "Data Engineering Lead", "Location": "Remote",
         "Comp_Posted": "FLOOR-$180,000", "Applicant_Volume": "22"}, ...]

OUTPUT — JSON on stdout, human-readable summary on stderr:

  {"new": [...],                 # never seen; fetch and evaluate these
   "exact_dupes": [...],         # Job_ID already logged; carries a backfill plan
   "probable_reposts": [...],    # normalized Company+Role_Title match, different/absent ID
   "within_batch_dupes": [...],  # same posting appearing twice in this batch
   "body_dupes": [...],          # identical JD text under a different ID/company (needs --bodies)
   "counts": {...}}

  3. Body-level dedupe (--bodies) — the backstop for what the metadata misses:
       python3 scripts/jd-dedupe.py --json extracted.json --bodies scratch/fetched

     WHERE THIS SITS IN THE PIPELINE. Steps 1 and 2 above run BEFORE any browsing, as
     Step 2 of instructions/01-intake-and-fetch.md requires. A body comparison cannot:
     there is no body until the posting has been fetched. So --bodies is a SECOND pass,
     run after fetch-jds.js and before evaluation, over the postings the first pass
     called "new". It does not save a fetch — it saves an evaluation, a log row, and
     the manual cleanup of a duplicate row. Run it as:

       jd-dedupe --json extracted.json        -> new IDs      (pre-fetch, as today)
       fetch-jds.js <those IDs>               -> scratch/fetched/
       jd-dedupe --json extracted.json --bodies scratch/fetched --update-index
                                              -> new IDs minus body dupes (pre-evaluate)

     Coverage against ALREADY-LOGGED postings is only as good as the cached bodies on
     hand, since scratch/fetched holds one run. --update-index accumulates fingerprints
     into scripts/jd-body-fingerprints.json so that coverage grows run over run; without
     it the pass still catches every within-batch pair, which is where both misses of
     2026-08-31 lived.

Feed the new IDs straight to the fetcher:
    python3 scripts/jd-dedupe.py --json extracted.json \
      | python3 -c 'import json,sys; print(" ".join(r["Job_ID"] for r in json.load(sys.stdin)["new"]))'

This script is READ-ONLY. It never writes to either CSV — the backfill plan it
produces is a proposal for jd-append.py / a backfill pass to act on.
"""
import argparse, csv, difflib, glob, hashlib, itertools, json, os, re, sys

# A repost rarely reuses the title verbatim — "…Data Analytics" vs
# "…Data Analytics and Reporting" is the same job. Same normalized company plus a
# title this similar is a *hypothesis* to report, never a silent discard.
TITLE_SIMILARITY = 0.82

# Two JD bodies this alike are the same posting. Measured over the 93 fetched bodies of
# the 2026-08-31 run (4278 pairs): the four true duplicate pairs scored 1.000, and the
# highest-scoring genuine non-duplicate scored 0.285 (two different Company-477 analytics
# roles sharing an employer boilerplate block). Nothing lands between. 0.90 sits in the
# middle of that gap with room on both sides.
BODY_SIMILARITY = 0.90
SHINGLE = 8   # words per shingle; long enough that shared boilerplate phrasing doesn't match

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LOG  = os.path.join(ROOT, "JD_Evaluation_Log.csv")
FPRINTS = os.path.join(HERE, "jd-body-fingerprints.json")

# Fields a dupe sighting may fill in when the logged row left them blank.
# Per instructions/01-intake-and-fetch.md Step 2: extracted data only, never judgments.
BACKFILLABLE = ["Job_ID", "URL", "Location", "Work_Type", "Employment_Type",
                "Comp_Posted", "Applicant_Volume"]

# Never touched on a dupe — these are judgments, not extracted data.
NEVER_TOUCH = {"Carls_Action", "Carls_Action_Date", "Verdict", "Role_Type",
               "Comp_Flag", "Biggest_Gap", "Biggest_Strength", "Recommended_Action",
               "Score", "Outcome", "Reason"}

# A placeholder is neither "blank" nor "a value" — flag it, don't fill or overwrite.
PLACEHOLDER = re.compile(r"^\s*\[.*\]\s*$")

SUFFIXES = re.compile(
    r"\b(inc|llc|l\.l\.c|ltd|limited|corp|corporation|co|company|plc|gmbh|"
    r"holdings|group|the)\b", re.I)


def norm(s):
    """Lowercase, strip punctuation and corporate suffixes, collapse whitespace."""
    s = (s or "").lower()
    s = re.sub(r"[^\w\s]", " ", s)
    s = SUFFIXES.sub(" ", s)
    return re.sub(r"\s+", " ", s).strip()


# A fetched body is mostly LinkedIn, not employer. The header above "About the job" carries
# the poster's own city and a posting age that ticks over daily ("3 days ago · 7 people
# clicked apply"), and the footer below the benefits/alert strip is site chrome — nav links,
# the copyright line, and a 35-language picker — byte-identical on all 93 bodies. Comparing
# whole bodies makes every unrelated pair look 40% alike and hides the pairs that matter, so
# cut to the employer's text before comparing.
BODY_START = "About the job"
BODY_ENDS  = ["Benefits found in job post", "Set alert for similar jobs", "Looking for talent?"]


def body_core(text):
    """The employer's own JD text, normalized. Empty if the markers aren't there."""
    if not text:
        return ""
    i = text.find(BODY_START)
    if i >= 0:
        text = text[i + len(BODY_START):]
    end = len(text)
    for m in BODY_ENDS:
        j = text.find(m)
        if j >= 0:
            end = min(end, j)
    text = text[:end].lower()
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def fingerprint(core):
    return hashlib.sha1(core.encode("utf-8")).hexdigest() if core else ""


def shingles(core):
    w = core.split()
    if len(w) < SHINGLE:
        return frozenset()
    return frozenset(hash(tuple(w[i:i + SHINGLE])) for i in range(len(w) - SHINGLE + 1))


def body_similarity(a, b):
    """Jaccard over word shingles. Cheap enough for all-pairs on a run-sized batch."""
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def load_bodies(dirs):
    """Job_ID -> normalized core, from fetch-jds.js result files."""
    out = {}
    for d in dirs:
        for f in sorted(glob.glob(os.path.join(d, "*.json"))):
            if os.path.basename(f).startswith("_"):
                continue          # _run-summary.json and friends
            try:
                rec = json.load(open(f))
            except (ValueError, OSError):
                continue
            jid = str(rec.get("jobId") or "").strip()
            core = body_core(rec.get("bodyText"))
            if jid and core:
                out[jid] = core
    return out


def load_index():
    """Accumulated fingerprint -> first-seen sighting, across past runs."""
    if not os.path.exists(FPRINTS):
        return {}
    try:
        return json.load(open(FPRINTS))
    except (ValueError, OSError):
        return {}


def load_log():
    if not os.path.exists(LOG):
        sys.exit(f"Log not found: {LOG}")
    with open(LOG, newline="") as f:
        rdr = csv.DictReader(f)
        rows = list(rdr)
        header = rdr.fieldnames
    bad = [n for n, r in enumerate(rows, 2) if len(r) != len(header) or None in r.values()]
    if bad:
        sys.exit(f"Log has {len(bad)} malformed row(s), first at line {bad[0]}. "
                 f"Fix the file before deduping.")
    return rows, header


def title_match(a, b):
    """Similarity of two normalized titles.

    Measured on real pairs from the log:

        "…Data Analytics" vs "…Data Analytics and Reporting"   0.86  same job
        "Director of Analytics" vs "…Analytics Engineering"    0.78  different jobs

    so plain sequence matching at TITLE_SIMILARITY (0.82) separates them. There is
    deliberately NO containment shortcut: scoring "a is a substring of b" as a perfect
    match made the second pair above look identical, and would have suppressed a real
    posting as a repost. (Caught 2026-08-26 on that Company-293 pair.) A repost is reported
    and overrule-able, never silently dropped, so a false positive here costs one line
    in the run summary while a false negative costs a duplicate row in the log.
    """
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    return difflib.SequenceMatcher(None, a, b).ratio()


def find_repost(company_index, company, title):
    """Best same-company title match at or above the similarity floor."""
    best, score = None, 0.0
    for line, row, logged_title in company_index.get(company, ()):
        s = title_match(title, logged_title)
        if s > score:
            best, score = (line, row), s
    return (best, score) if best and score >= TITLE_SIMILARITY else (None, score)


def backfill_plan(logged, incoming):
    """Which blanks in the logged row this sighting could fill, plus conflicts."""
    fills, conflicts, placeholders = {}, [], []
    for fld in BACKFILLABLE:
        new = (incoming.get(fld) or "").strip()
        if not new:
            continue
        cur = (logged.get(fld) or "").strip()
        if PLACEHOLDER.match(cur):
            placeholders.append({"field": fld, "logged": cur, "sighted": new})
        elif not cur:
            fills[fld] = new
        elif cur != new:
            # Populated and contradicted: never overwrite. Note it, surface it.
            conflicts.append({"field": fld, "logged": cur, "sighted": new})
    return fills, conflicts, placeholders


def body_pass(new_posts, bodies, index):
    """Second-pass dedupe on JD text, over the postings the metadata matchers called new.

    Two things can match: another posting in this same batch, or a fingerprint carried
    forward in the index from a run that already logged it. Batch matches resolve against
    the FIRST posting in list order, so the survivor is stable and the rest report against
    it.

    Returns (still_new, body_dupes, sightings) where sightings is the fingerprint ->
    sighting map this run would add to the index.
    """
    still_new, dupes, kept = [], [], []          # kept = survivors, for batch comparison
    for post in new_posts:
        jid = str(post.get("Job_ID") or "").strip()
        core = bodies.get(jid)
        if not core:
            still_new.append(post)               # no body cached: nothing to compare, stays new
            continue
        fp, sh = fingerprint(core), shingles(core)

        # Same batch first — the survivor is a posting this run will evaluate anyway.
        hit = None
        for other, ofp, osh in kept:
            sim = 1.0 if fp == ofp else body_similarity(sh, osh)
            if sim >= BODY_SIMILARITY:
                hit = {"scope": "within_batch", "matches_Job_ID": other["Job_ID"],
                       "matches_Company": other.get("Company") or None,
                       "similarity": round(sim, 4),
                       "match": "exact" if fp == ofp else "near"}
                break

        # Then the accumulated index — a body already logged under some other ID.
        if not hit and fp in index:
            prior = index[fp]
            pid = str(prior.get("Job_ID") or "").strip()
            if pid and pid != jid:
                hit = {"scope": "logged", "matches_Job_ID": pid,
                       "matches_Company": prior.get("Company"),
                       "line": prior.get("line"), "similarity": 1.0, "match": "exact"}

        if hit:
            hit.update({"Job_ID": jid, "fingerprint": fp,
                        "Company": post.get("Company") or None,
                        "Role_Title": post.get("Role_Title") or None})
            dupes.append(hit)
            continue

        kept.append((post, fp, sh))
        still_new.append(post)

    sightings = {fp: {"Job_ID": str(p.get("Job_ID") or "").strip(),
                      "Company": p.get("Company") or None,
                      "Role_Title": p.get("Role_Title") or None}
                 for p, fp, _ in kept}
    return still_new, dupes, sightings


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ids", nargs="*", help="job IDs (exact-match dedupe only)")
    ap.add_argument("--json", metavar="FILE",
                    help="JSON list of extracted postings (enables repost detection + backfill plan)")
    ap.add_argument("--bodies", metavar="DIR", action="append", default=[],
                    help="directory of fetch-jds.js results (<Job_ID>.json). Repeatable. "
                         "Enables body-level dedupe — POST-FETCH only; see the header.")
    ap.add_argument("--update-index", action="store_true",
                    help=f"write this run's body fingerprints into {os.path.basename(FPRINTS)} "
                         "so later runs can match against them")
    args = ap.parse_args()

    if args.json:
        with open(args.json) as f:
            incoming = json.load(f)
        if not isinstance(incoming, list):
            sys.exit("--json must contain a JSON list of posting objects.")
    else:
        raw = args.ids or [l.strip() for l in sys.stdin.read().split()]
        incoming = [{"Job_ID": re.sub(r"\D", "", i)} for i in raw if re.search(r"\d", i)]
    if not incoming:
        sys.exit("No postings given.")

    rows, _ = load_log()
    by_id = {(r.get("Job_ID") or "").strip(): (n, r) for n, r in enumerate(rows, 2)
             if (r.get("Job_ID") or "").strip()}
    company_index = {}
    for n, r in enumerate(rows, 2):
        c, t = norm(r.get("Company")), norm(r.get("Role_Title"))
        if c and t:
            company_index.setdefault(c, []).append((n, r, t))

    out = {"new": [], "exact_dupes": [], "probable_reposts": [], "within_batch_dupes": []}
    seen_ids, seen_ct = set(), set()

    for post in incoming:
        jid = str(post.get("Job_ID") or "").strip()
        company, title = norm(post.get("Company")), norm(post.get("Role_Title"))

        # Dedupe within the batch first — the same job spans multiple alert emails.
        if jid and jid in seen_ids:
            out["within_batch_dupes"].append(post)
            continue
        if company and title and any(
                c == company and title_match(title, t) >= TITLE_SIMILARITY
                for c, t in seen_ct):
            out["within_batch_dupes"].append(post)
            continue
        if jid:
            seen_ids.add(jid)
        if company and title:
            seen_ct.add((company, title))

        if jid and jid in by_id:
            line, logged = by_id[jid]
            fills, conflicts, placeholders = backfill_plan(logged, post)
            out["exact_dupes"].append({
                "Job_ID": jid, "line": line,
                "Company": logged.get("Company"), "Role_Title": logged.get("Role_Title"),
                "backfill": fills, "conflicts": conflicts, "placeholders": placeholders})
            continue

        hit, sim = find_repost(company_index, company, title) if company and title else (None, 0.0)
        if hit:
            line, logged = hit
            fills, conflicts, placeholders = backfill_plan(logged, post)
            out["probable_reposts"].append({
                "sighted_Job_ID": jid or None, "logged_Job_ID": logged.get("Job_ID"),
                "line": line, "similarity": round(sim, 3),
                "Company": logged.get("Company"),
                "logged_Role_Title": logged.get("Role_Title"),
                "sighted_Role_Title": post.get("Role_Title"),
                "backfill": fills, "conflicts": conflicts, "placeholders": placeholders})
        else:
            out["new"].append(post)

    # --- body-level dedupe (second pass, post-fetch) -----------------------------
    # The matchers above key on Job_ID and on normalized Company+Role_Title. Both misses
    # of 2026-08-31 slipped through a gap in that key, not a bug in it:
    #   * Two Company-456 "Enterprise Data Strategy Manager" sightings came out of the
    #     text/html part of a forwarded alert with Company and Role_Title both EMPTY, so
    #     there was no company+title key to match on at all.
    #   * Company-24 and Company-646 posted the same JD verbatim under
    #     two different poster names; find_repost only searches within one company, so a
    #     title match at 1.00 was never even considered.
    # The body is the thing neither could see.
    bodies = load_bodies(args.bodies) if args.bodies else {}
    index  = load_index()
    out["body_dupes"] = []
    if bodies:
        out["new"], out["body_dupes"], sightings = body_pass(out["new"], bodies, index)
        if args.update_index:
            index.update(sightings)
            with open(FPRINTS, "w") as f:
                json.dump(index, f, indent=1, sort_keys=True)

    out["counts"] = {
        "postings_found": len(incoming),
        "new": len(out["new"]),
        "exact_dupes": len(out["exact_dupes"]),
        "probable_reposts": len(out["probable_reposts"]),
        "within_batch_dupes": len(out["within_batch_dupes"]),
        "body_dupes": len(out["body_dupes"]),
        "bodies_compared": sum(1 for p in incoming
                               if str(p.get("Job_ID") or "").strip() in bodies),
        "rows_with_backfill": sum(1 for k in ("exact_dupes", "probable_reposts")
                                  for d in out[k] if d["backfill"]),
        "conflicts_flagged": sum(len(d["conflicts"]) for k in ("exact_dupes", "probable_reposts")
                                 for d in out[k]),
        "placeholders_flagged": sum(len(d["placeholders"]) for k in ("exact_dupes", "probable_reposts")
                                    for d in out[k]),
    }

    c = out["counts"]
    e = sys.stderr
    print(f"\n  postings found      {c['postings_found']:>4}", file=e)
    print(f"  new (fetch these)   {c['new']:>4}", file=e)
    print(f"  exact dupes         {c['exact_dupes']:>4}", file=e)
    print(f"  probable reposts    {c['probable_reposts']:>4}   <- overrule-able, see summary", file=e)
    print(f"  dupes within batch  {c['within_batch_dupes']:>4}", file=e)
    if bodies:
        print(f"  body dupes          {c['body_dupes']:>4}   <- same JD text, different ID", file=e)
        print(f"  bodies compared     {c['bodies_compared']:>4} / {c['postings_found']}", file=e)
    else:
        print(f"  body dupes           n/a   <- pass --bodies DIR after fetch to enable", file=e)
    print(f"  rows w/ backfill    {c['rows_with_backfill']:>4}", file=e)
    print(f"  conflicts flagged   {c['conflicts_flagged']:>4}", file=e)
    print(f"  placeholders        {c['placeholders_flagged']:>4}", file=e)

    for d in out["body_dupes"]:
        where = "in this batch" if d["scope"] == "within_batch" else "already logged"
        print(f"    BODY DUPE {d['Job_ID']} ({d.get('Company') or '?'}) == "
              f"{d['matches_Job_ID']} ({d.get('matches_Company') or '?'}) {where} — "
              f"{d['match']} match, sim {d['similarity']}", file=e)
    for d in out["probable_reposts"]:
        print(f"    repost? sighted {d['sighted_Job_ID']} vs logged {d['logged_Job_ID']} "
              f"(sim {d['similarity']}) — {d['Company']}", file=e)
        print(f"            logged  {d['logged_Role_Title']!r}", file=e)
        print(f"            sighted {d['sighted_Role_Title']!r}", file=e)
    for k in ("exact_dupes", "probable_reposts"):
        for d in out[k]:
            for cf in d["conflicts"]:
                print(f"    CONFLICT {d.get('Job_ID') or d.get('logged_Job_ID')} "
                      f"{cf['field']}: logged={cf['logged']!r} sighted={cf['sighted']!r}", file=e)
            for ph in d["placeholders"]:
                print(f"    PLACEHOLDER {d.get('Job_ID') or d.get('logged_Job_ID')} "
                      f"{ph['field']}={ph['logged']!r} — leave alone, ask Carl", file=e)
    print("", file=e)

    json.dump(out, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
