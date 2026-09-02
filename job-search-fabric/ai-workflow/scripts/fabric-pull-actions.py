#!/usr/bin/env python3
"""
fabric-pull-actions.py — pull the authoritative Carl-action fields down from Fabric.

Carl triages in the Power BI report and writes back to the Fabric SQL database
`JobSearch_DB` (workspace "Job Search"). That database — not the local
JD_Evaluation_Log.csv — holds the current Carls_Action / Carls_Action_Date /
Outcome / Reason. This script reads them back with zero stored credentials: it
mints a short-lived token from the machine's existing `az login` and runs a DAX
query against the "Job Search" semantic model, which is Direct Lake over the SQL
database's OneLake mirror (so it reflects write-backs within ~a minute).

Usage:
    python3 scripts/fabric-pull-actions.py            # export -> scratch/fabric_actions.csv
    python3 scripts/fabric-pull-actions.py --diff     # export, then diff vs local CSV

Requires: `az login` as <user>@<tenant>.onmicrosoft.com (already done;
re-run `az login` if the token call fails with a login prompt).

THE ONE-WAY RULE — the single most important thing about this script
--------------------------------------------------------------------
Data flows in ONE direction: CSV (front end) -> OneLake -> database -> and from
there Carl's report write-back is the override. It never travels back up.

This script reads DOWN that pipe for the LEARNER ONLY. Its output measures Carl's
decisions against the rubric. **Nothing it returns may ever be written into
JD_Evaluation_Log.csv.**

A row where the database has a Carls_Action / Carls_Action_Date / Outcome / Reason
that the CSV lacks is NOT drift and NOT a defect to reconcile. It is the system
working: Carl triaged in the report, and that value is meant to live only in the
database. Copying it back into the CSV makes his write-back indistinguishable from
a front-end pre-fill, and it stops being an override of anything.

FLAG IT, NEVER BACKFILL IT. (Learned the hard way 2026-08-26: 11 rows were copied
back from a pull, which masked whether a database restore had worked and cost Carl
hours of misdirected troubleshooting.)

Writing those four fields at the FRONT end is fine and wanted — the documented
job-alert, email and LinkedIn triage processes pre-fill them, and the closed-posting
check writes Carls_Action = "None". The prohibition is specific: not from a pull.

NOTE: the output file is written under scratch/ inside the JobSearch folder.
Never write it to the OneDrive root — a Fabric shortcut points there and any
stray .csv gets absorbed into the JD Delta table (see
instructions/04-log-and-write-discipline.md, "Folder hygiene").
"""
import argparse, csv, json, os, subprocess, sys, urllib.error, urllib.request

WORKSPACE_ID = "<workspace-id>"   # "Job Search"
DATASET_ID   = "<semantic-model-id>"   # "Job Search Model"
API = (f"https://api.powerbi.com/v1.0/myorg/groups/{WORKSPACE_ID}"
       f"/datasets/{DATASET_ID}/executeQueries")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT  = os.path.join(ROOT, "scratch", "fabric_actions.csv")
LOCAL_LOG = os.path.join(ROOT, "JD_Evaluation_Log.csv")

# Columns pulled from Fact_JobPostings. The four Carl-owned fields are the point
# of the exercise; the Pts_* components come along so the rubric can be scored
# against outcomes without re-deriving them.
COLS = ["Job_ID", "Company", "Role_Title", "Date_Evaluated", "Score", "Score_Raw", "Verdict",
        "Role_Type", "Comp_Flag", "Recommended_Action",
        "Carls_Action", "Carls_Action_Date", "Outcome", "Reason",
        "Pts_Lane", "Pts_Scope", "Pts_Comp", "Pts_Location", "Pts_Skills",
        "Pts_Perks", "Pts_Applicants", "Pts_Deductions",
        "Is_Capped_Score", "WriteBack_Applied"]
# Score_Raw joined the model 2026-08-26 and is blank on every pre-migration row; it
# populates going forward. Once populated, Score_Raw > Score identifies a capped row
# and by how much, which is what a Review rule keyed on "high raw score killed by a
# gate" needs. Is_Capped_Score becomes redundant at that point.

CARL_FIELDS = ["Carls_Action", "Carls_Action_Date", "Outcome", "Reason"]


def get_token():
    try:
        p = subprocess.run(
            ["az", "account", "get-access-token",
             "--resource", "https://analysis.windows.net/powerbi/api",
             "--query", "accessToken", "-o", "tsv"],
            capture_output=True, text=True, check=True)
    except FileNotFoundError:
        sys.exit("az CLI not found. Install it, or run the Notebook export fallback.")
    except subprocess.CalledProcessError as e:
        sys.exit(f"az token call failed — run `az login` and retry.\n{e.stderr.strip()}")
    tok = p.stdout.strip()
    if len(tok) < 100:
        sys.exit("az returned no usable token — run `az login` and retry.")
    return tok


def dax(query, tok):
    body = json.dumps({"queries": [{"query": query}],
                       "serializerSettings": {"includeNulls": True}}).encode()
    req = urllib.request.Request(API, data=body, headers={
        "Authorization": f"Bearer {tok}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return json.load(r)["results"][0]["tables"][0]["rows"]
    except urllib.error.HTTPError as e:
        sys.exit(f"Execute Queries API returned {e.code}:\n{e.read().decode()[:1000]}")


def norm(value, field):
    v = "" if value is None else str(value).strip()
    if field in ("Carls_Action_Date", "Date_Evaluated") and v:
        v = v.split("T")[0]          # DAX returns ISO datetimes
    return v


def export(tok):
    sel = ", ".join(f'"{c}", Fact_JobPostings[{c}]' for c in COLS)
    rows = dax(f"EVALUATE SELECTCOLUMNS(Fact_JobPostings, {sel})", tok)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", newline="") as f:
        w = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        w.writerow(COLS)
        for r in rows:
            w.writerow([norm(r.get(f"[{c}]"), c) for c in COLS])
    # same post-write validation discipline as every other CSV in this workflow
    check = list(csv.reader(open(OUT)))
    bad = [i for i, row in enumerate(check) if len(row) != len(COLS)]
    if bad:
        sys.exit(f"Validation failed: rows {bad[:5]} have the wrong field count.")
    print(f"Pulled {len(rows)} rows from Fabric -> {os.path.relpath(OUT, ROOT)}")
    return rows


def diff():
    fab = {r["Job_ID"]: r for r in csv.DictReader(open(OUT))}
    loc = {r["Job_ID"]: r for r in csv.DictReader(open(LOCAL_LOG))}
    only_fab, only_loc = set(fab) - set(loc), set(loc) - set(fab)
    print(f"\nFabric {len(fab)} rows | local {len(loc)} rows | "
          f"only-in-Fabric {len(only_fab)} | only-in-local {len(only_loc)}")
    if only_fab:
        print("  only in Fabric:", ", ".join(sorted(only_fab)[:10]))
    if only_loc:
        print("  only in local :", ", ".join(sorted(only_loc)[:10]))

    ahead, conflict = [], []
    for jid in sorted(set(fab) & set(loc)):
        for f in CARL_FIELDS:
            l, v = norm(loc[jid][f], f), norm(fab[jid][f], f)
            if l == v:
                continue
            (ahead if l == "" else conflict).append((jid, f, l, v))

    print(f"\n{len(ahead)} field(s) Fabric has and the CSV is blank on. "
          f"THIS IS NORMAL — DO NOT BACKFILL:")
    for jid, f, _, v in ahead:
        print(f"  {jid}  {fab[jid]['Company'][:24]:<24} {f:<18} fabric={v[:52]!r}")
    if ahead:
        print("  ^ These are Carl's report write-backs. They are SUPPOSED to exist only in the\n"
              "    database. Copying them into the CSV collapses the override model — see the\n"
              "    one-way rule at the top of this file. Report them; never write them back.")

    print(f"\n{len(conflict)} field(s) where the CSV and Fabric BOTH have values and disagree "
          f"— report to Carl, change nothing:")
    for jid, f, l, v in conflict:
        print(f"  {jid}  {fab[jid]['Company'][:24]:<24} {f:<18} "
              f"csv={l[:36]!r} fabric={v[:36]!r}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--diff", action="store_true",
                    help="after exporting, compare against the local JD_Evaluation_Log.csv")
    args = ap.parse_args()
    export(get_token())
    if args.diff:
        diff()
