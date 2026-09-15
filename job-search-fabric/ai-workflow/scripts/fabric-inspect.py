#!/usr/bin/env python3
"""
fabric-inspect.py — read-only introspection of the "Job Search" Fabric workspace.

Purpose: let an agent answer "has this been built yet?" by looking at Fabric
directly, instead of asking Carl. Every subcommand is a read. Nothing here
mutates a Fabric item, and `sql` refuses anything that is not a SELECT unless
you pass --allow-write (see instructions/04-log-and-write-discipline.md).

Auth is the same zero-stored-credential pattern as fabric-pull-actions.py: a
short-lived token minted from the machine's existing `az login`. Three different
audiences are needed depending on the surface (Fabric control plane, OneLake
storage, Azure SQL) — get_token() handles that.

Usage:
    scripts/fabric-inspect.py items                     # inventory + last-modified
    scripts/fabric-inspect.py item  <name|id>           # one item, with definition parts
    scripts/fabric-inspect.py source <name|id> [part]   # dump the item's real source
    scripts/fabric-inspect.py jobs  <name|id> [-n 10]   # refresh / run history
    scripts/fabric-inspect.py onelake [subpath]         # OneLake listing with timestamps
    scripts/fabric-inspect.py objects [--db NAME]       # sys.objects + create/modify dates
    scripts/fabric-inspect.py columns <table>           # column list for one table
    scripts/fabric-inspect.py sql "<SELECT ...>"        # arbitrary read-only SQL
    scripts/fabric-inspect.py model                     # semantic model tables/columns/measures
    scripts/fabric-inspect.py check                     # run the standing build checklist

SQL subcommands (objects/columns/sql) need `mssql-python`, which lives in the
project venv:  .venv/bin/python scripts/fabric-inspect.py sql "..."
Everything else is stdlib-only and runs under plain python3.
"""
import argparse, base64, json, os, re, struct, subprocess, sys, time
import urllib.error, urllib.parse, urllib.request

WORKSPACE_ID   = "<workspace-id>"   # "Job Search"
WORKSPACE_NAME = "Job Search"
DATASET_ID     = "<semantic-model-id>"   # "Job Search Model"

SQL_SERVER = ("<server>"
              ".database.fabric.microsoft.com,1433")
SQL_DBS = {   # friendly name -> Initial Catalog (name-GUID, as Fabric requires)
    "JobSearch_DB":        "JobSearch_DB-<sql-database-id>",
    "JobSearch_DB_backup": "JobSearch_DB_backup-<sql-database-backup-id>",
}

FABRIC   = "https://api.fabric.microsoft.com"
POWERBI  = "https://api.powerbi.com/v1.0/myorg"
ONELAKE  = "https://onelake.dfs.fabric.microsoft.com"

RES_FABRIC  = "https://api.fabric.microsoft.com"
RES_POWERBI = "https://analysis.windows.net/powerbi/api"
RES_STORAGE = "https://storage.azure.com"
RES_SQL     = "https://database.windows.net/"

_tokens = {}


def get_token(resource):
    if resource in _tokens:
        return _tokens[resource]
    try:
        p = subprocess.run(["az", "account", "get-access-token", "--resource", resource,
                            "--query", "accessToken", "-o", "tsv"],
                           capture_output=True, text=True, check=True)
    except FileNotFoundError:
        sys.exit("az CLI not found — install it, or run the checks in the Fabric portal.")
    except subprocess.CalledProcessError as e:
        sys.exit(f"az token call failed — run `az login` and retry.\n{e.stderr.strip()}")
    tok = p.stdout.strip()
    if len(tok) < 100:
        sys.exit("az returned no usable token — run `az login` and retry.")
    _tokens[resource] = tok
    return tok


def api(url, resource, method="GET", body=None, raw=False, soft=False):
    """soft=True returns None on an HTTP error instead of exiting — for endpoints
    that legitimately 404 depending on item type."""
    req = urllib.request.Request(url, method=method, data=body, headers={
        "Authorization": f"Bearer {get_token(resource)}",
        "Content-Type": "application/json"})
    try:
        resp = urllib.request.urlopen(req, timeout=180)
    except urllib.error.HTTPError as e:
        if soft:
            return None
        sys.exit(f"{method} {url}\n  -> HTTP {e.code}: {e.read().decode()[:800]}")
    return resp if raw else json.load(resp)


def lro(url, resource, method="POST", body=b""):
    """POST an endpoint that may answer 200 (inline) or 202 (long-running)."""
    resp = api(url, resource, method, body, raw=True)
    if resp.status == 200:
        return json.load(resp)
    loc = resp.headers.get("Location")
    wait = int(resp.headers.get("Retry-After", "2") or 2)
    for _ in range(40):
        time.sleep(wait)
        state = api(loc, resource)
        if state.get("status") == "Succeeded":
            return api(loc.rstrip("/") + "/result", resource)
        if state.get("status") == "Failed":
            sys.exit(f"Operation failed: {json.dumps(state)[:600]}")
    sys.exit("Long-running operation did not finish in time.")


# ---------------------------------------------------------------- inventory

def list_items():
    return api(f"{FABRIC}/v1/workspaces/{WORKSPACE_ID}/items", RES_FABRIC)["value"]


def resolve(ref):
    """Accept a GUID or a displayName (case-insensitive) and return the item dict."""
    items = list_items()
    for i in items:
        if i["id"] == ref:
            return i
    hits = [i for i in items if i["displayName"].lower() == ref.lower()]
    if not hits:
        hits = [i for i in items if ref.lower() in i["displayName"].lower()]
    if not hits:
        sys.exit(f"No item matching {ref!r}. Run `items` to see the inventory.")
    if len(hits) > 1:
        sys.exit("Ambiguous: " + ", ".join(f"{h['displayName']} ({h['type']})" for h in hits))
    return hits[0]


def onelake_ls(directory="", recursive=False):
    q = urllib.parse.urlencode({"recursive": str(recursive).lower(),
                                "resource": "filesystem", "directory": directory})
    url = f"{ONELAKE}/{urllib.parse.quote(WORKSPACE_NAME)}?{q}"
    return api(url, RES_STORAGE).get("paths", [])


# OneLake names an item's folder "<displayName>.<Kind>"; Kind is not always the
# item type from the Fabric API, so map the ones that differ.
ONELAKE_SUFFIX = {"Dataflow": "DataflowFabric", "Notebook": "SynapseNotebook",
                  "SQLDatabase": "SQLDbNative", "UserDataFunction": "FunctionSet",
                  "Lakehouse": "Lakehouse", "Warehouse": "Warehouse"}


def cmd_items(args):
    items = list_items()
    stamps = {}
    for p in onelake_ls():
        name = p["name"].rsplit("/", 1)[-1]
        stamps[name.rsplit(".", 1)[0].lower()] = p.get("lastModified", "")
    print(f"{'TYPE':<18} {'NAME':<44} {'ONELAKE MODIFIED':<32} ID")
    for i in sorted(items, key=lambda x: (x["type"], x["displayName"])):
        ts = stamps.get(i["displayName"].lower(), "")
        print(f"{i['type']:<18} {i['displayName']:<44} {ts:<32} {i['id']}")
    print(f"\n{len(items)} items in workspace {WORKSPACE_NAME!r}.")
    print("Note: ONELAKE MODIFIED is the item folder's timestamp — it moves when the "
          "item's stored\ndefinition or data changes. Reports/semantic models have no "
          "OneLake folder, so they show blank;\nuse `jobs` for those.")


def cmd_item(args):
    it = resolve(args.ref)
    print(json.dumps(it, indent=2))
    parts = get_definition(it)
    if parts:
        print("\nDefinition parts:")
        for path, raw in parts:
            print(f"  {path:<40} {len(raw):>8} bytes")
        print(f"\nDump one with:  scripts/fabric-inspect.py source '{it['displayName']}' <part>")


def get_definition(it):
    """Return [(path, decoded_bytes), ...] or [] for item types with no definition."""
    url = f"{FABRIC}/v1/workspaces/{WORKSPACE_ID}/items/{it['id']}/getDefinition"
    try:
        d = lro(url, RES_FABRIC)
    except SystemExit:
        return []
    return [(p["path"], base64.b64decode(p["payload"]))
            for p in d.get("definition", {}).get("parts", [])]


def cmd_source(args):
    it = resolve(args.ref)
    parts = get_definition(it)
    if not parts:
        sys.exit(f"{it['displayName']} ({it['type']}) exposes no definition.")
    wanted = [(p, r) for p, r in parts
              if args.part is None or args.part.lower() in p.lower()]
    if not wanted:
        sys.exit("No part matching %r. Have: %s" % (args.part, ", ".join(p for p, _ in parts)))
    for path, raw in wanted:
        print(f"===== {it['displayName']} :: {path} =====")
        print(raw.decode("utf-8", "replace"))


def cmd_jobs(args):
    it = resolve(args.ref)
    # Fabric job instances cover dataflows, notebooks and pipelines. Semantic
    # models 404 here; their refreshes live on the Power BI surface instead.
    # Neither endpoint honors $top reliably, so slice client-side.
    res = api(f"{FABRIC}/v1/workspaces/{WORKSPACE_ID}/items/{it['id']}/jobs/instances",
              RES_FABRIC, soft=True)
    rows = (res or {}).get("value", [])
    if rows:
        for r in rows[:args.n]:
            print(f"{r.get('startTimeUtc','')[:19]}  {r.get('status',''):<12} "
                  f"{r.get('jobType',''):<10} {r.get('invokeType','')}"
                  + (f"  FAIL: {json.dumps(r['failureReason'])[:120]}"
                     if r.get("failureReason") else ""))
        return
    res = api(f"{POWERBI}/groups/{WORKSPACE_ID}/datasets/{it['id']}/refreshes",
              RES_POWERBI, soft=True)
    rows = (res or {}).get("value", [])
    if not rows:
        print(f"No job or refresh history for {it['displayName']} ({it['type']}).")
        return
    for r in rows[:args.n]:
        print(f"{r.get('startTime','')[:19]}  {r.get('status',''):<12} "
              f"{r.get('refreshType','')}"
              + (f"  {r['serviceExceptionJson'][:120]}"
                 if r.get("serviceExceptionJson") else ""))


def cmd_onelake(args):
    for p in onelake_ls(args.path or "", args.recursive):
        kind = "D" if p.get("isDirectory") == "true" else "F"
        size = "" if kind == "D" else f"{int(p.get('contentLength', 0)):>12,}"
        print(f"{p.get('lastModified','')[:25]:<26} {kind} {size:>13} {p['name']}")


# ---------------------------------------------------------------- SQL

def sql_connect(db="JobSearch_DB"):
    try:
        from mssql_python import connect
    except ImportError:
        sys.exit("mssql-python is not importable. Use the project venv:\n"
                 "  .venv/bin/python scripts/fabric-inspect.py <cmd>\n"
                 "or create it:  python3 -m venv .venv && .venv/bin/pip install mssql-python")
    if db not in SQL_DBS:
        sys.exit(f"Unknown database {db!r}. Known: {', '.join(SQL_DBS)}")
    b = get_token(RES_SQL).encode("utf-16-le")
    tok = struct.pack("<I", len(b)) + b
    cs = (f"Server={SQL_SERVER};Database={SQL_DBS[db]};"
          f"Encrypt=yes;TrustServerCertificate=no;")
    return connect(cs, attrs_before={1256: tok})   # 1256 = SQL_COPT_SS_ACCESS_TOKEN


def run_sql(query, db="JobSearch_DB"):
    cur = sql_connect(db).cursor()
    cur.execute(query)
    cols = [d[0] for d in cur.description] if cur.description else []
    return cols, (cur.fetchall() if cols else [])


def show(cols, rows, limit=200):
    if not cols:
        print("(no result set)")
        return
    w = [max(len(c), *(len(str(r[i])) for r in rows[:limit])) if rows else len(c)
         for i, c in enumerate(cols)]
    w = [min(x, 60) for x in w]
    print("  ".join(c[:w[i]].ljust(w[i]) for i, c in enumerate(cols)))
    print("  ".join("-" * x for x in w))
    for r in rows[:limit]:
        print("  ".join(str(v)[:w[i]].ljust(w[i]) for i, v in enumerate(r)))
    if len(rows) > limit:
        print(f"... {len(rows) - limit} more rows")
    print(f"({len(rows)} rows)")


WRITE_RE = re.compile(r"\b(insert|update|delete|drop|create|alter|truncate|merge|exec)\b", re.I)


def cmd_sql(args):
    if not args.allow_write and WRITE_RE.search(args.query):
        sys.exit("Refusing: this looks like a write. This tool is for introspection.\n"
                 "Pass --allow-write only if you genuinely intend to change Fabric data,\n"
                 "and re-read instructions/04-log-and-write-discipline.md first.")
    show(*run_sql(args.query, args.db))


def cmd_objects(args):
    cols, rows = run_sql("""
        SELECT o.type_desc, s.name AS [schema], o.name, o.create_date, o.modify_date
        FROM   sys.objects o JOIN sys.schemas s ON s.schema_id = o.schema_id
        WHERE  o.is_ms_shipped = 0 AND o.parent_object_id = 0
        ORDER BY o.type_desc, o.name""", args.db)
    show(cols, rows)


def cmd_columns(args):
    cols, rows = run_sql(f"""
        SELECT c.name, t.name AS type, c.max_length, c.is_nullable
        FROM   sys.columns c
        JOIN   sys.types t ON t.user_type_id = c.user_type_id
        WHERE  c.object_id = OBJECT_ID('{args.table}')
        ORDER BY c.column_id""", args.db)
    if not rows:
        print(f"No object named {args.table!r} in {args.db} (or it has no columns).")
    else:
        show(cols, rows)


# ---------------------------------------------------------------- semantic model

def dax(query):
    url = f"{POWERBI}/groups/{WORKSPACE_ID}/datasets/{DATASET_ID}/executeQueries"
    body = json.dumps({"queries": [{"query": query}],
                       "serializerSettings": {"includeNulls": True}}).encode()
    return api(url, RES_POWERBI, "POST", body)["results"][0]["tables"][0]["rows"]


def cmd_model(args):
    # INFO.VIEW.* are the DAX INFO functions the Execute Queries API accepts;
    # the bare INFO.TABLES() form returns a 400 here.
    print("== Tables ==")
    for r in dax('EVALUATE SELECTCOLUMNS(INFO.VIEW.TABLES(), "Name", [Name])'):
        print("  ", r["[Name]"])
    print("== Columns ==")
    for r in dax('EVALUATE SELECTCOLUMNS(INFO.VIEW.COLUMNS(), '
                 '"T", [Table], "C", [Name], "Type", [DataType])'):
        if not str(r["[C]"]).startswith("RowNumber-"):
            print(f"   {r['[T]']}.{r['[C]']}  ({r['[Type]']})")
    print("== Measures ==")
    for r in dax('EVALUATE SELECTCOLUMNS(INFO.VIEW.MEASURES(), "T", [Table], "M", [Name])'):
        print(f"   {r['[T]']}.{r['[M]']}")


# ---------------------------------------------------------------- checklist

# The standing "is it built yet?" questions, from
# scratch/HANDOFF_fabric-writeback-incident_2026-08-26.md ("Open items").
# Each entry: (label, kind, target, needle)
#   sqlobject : target = object name,  needle = expected type_desc (or None)
#   sqlcolumn : target = "table.column"
#   source    : target = item displayName, needle = regex that must appear in its source
#   nosource  : same, but the regex must NOT appear
CHECKS = [
    ("WriteBack_Log table exists",        "sqlobject", "WriteBack_Log",        "USER_TABLE"),
    ("vw_WriteBack_Latest view exists",   "sqlobject", "vw_WriteBack_Latest",  "VIEW"),
    ("WriteBack_Log has Written_By",      "sqlcolumn", "dbo.WriteBack_Log.Written_By", None),
    ("UDF takes an actionDate parameter", "source",    "JD_ActionWriteback",   r"actionDate"),
    ("UDF no longer hardcodes GETDATE()", "nosource",  "JD_ActionWriteback",   r"GETDATE\(\)"),
    ("UDF writes to WriteBack_Log",       "source",    "JD_ActionWriteback",   r"INSERT\s+INTO\s+dbo\.WriteBack_Log"),
    ("Dataflow reads vw_WriteBack_Latest","source",    "JD_Transform",         r"vw_WriteBack_Latest"),
    ("NormalizeFlag keys off the log",    "source",    "JD_Transform",         r"WB_Job_ID"),
    ("JobSearch_DB_backup cleaned up",    "noitem",    "JobSearch_DB_backup",  None),
]


def cmd_check(args):
    items = {i["displayName"].lower(): i for i in list_items()}
    src_cache = {}

    def source_of(name):
        if name.lower() not in src_cache:
            it = items.get(name.lower())
            if not it:
                src_cache[name.lower()] = None
            else:
                src_cache[name.lower()] = "\n".join(
                    r.decode("utf-8", "replace") for _, r in get_definition(it))
        return src_cache[name.lower()]

    objs = {}
    try:
        _, rows = run_sql("""SELECT o.name, o.type_desc, o.create_date, o.modify_date
                             FROM sys.objects o WHERE o.is_ms_shipped = 0""")
        objs = {r[0].lower(): r for r in rows}
        sql_ok = True
    except SystemExit as e:
        print(f"[warn] SQL checks skipped: {e}\n")
        sql_ok = False

    width = max(len(c[0]) for c in CHECKS)
    for label, kind, target, needle in CHECKS:
        detail = ""
        if kind in ("sqlobject", "sqlcolumn") and not sql_ok:
            state = "?"
        elif kind == "sqlobject":
            row = objs.get(target.lower())
            state = "YES" if row and (needle is None or row[1] == needle) else "no"
            if row:
                detail = f"{row[1]}, created {row[2]:%Y-%m-%d %H:%M}, modified {row[3]:%Y-%m-%d %H:%M}"
        elif kind == "sqlcolumn":
            tbl, col = target.rsplit(".", 1)
            _, r = run_sql(f"SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('{tbl}') "
                           f"AND name = '{col}'")
            state = "YES" if r else "no"
        elif kind in ("source", "nosource"):
            s = source_of(target)
            if s is None:
                state, detail = "no", "item not found"
            else:
                found = re.search(needle, s) is not None
                state = "YES" if found == (kind == "source") else "no"
        elif kind == "noitem":
            state = "no" if target.lower() in items else "YES"
            if target.lower() in items:
                detail = "still present"
        print(f"  [{state:^3}] {label:<{width}}   {detail}")
    print("\nYES = built and verified on Fabric right now. Re-run after any change; "
          "this reads live state,\nnot notes. Definition reads can lag a portal save by "
          "a few seconds.")


# ---------------------------------------------------------------- cli

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("items").set_defaults(fn=cmd_items)

    p = sub.add_parser("item");   p.add_argument("ref"); p.set_defaults(fn=cmd_item)
    p = sub.add_parser("source"); p.add_argument("ref"); p.add_argument("part", nargs="?")
    p.set_defaults(fn=cmd_source)
    p = sub.add_parser("jobs");   p.add_argument("ref"); p.add_argument("-n", type=int, default=10)
    p.set_defaults(fn=cmd_jobs)
    p = sub.add_parser("onelake"); p.add_argument("path", nargs="?")
    p.add_argument("-r", "--recursive", action="store_true"); p.set_defaults(fn=cmd_onelake)

    p = sub.add_parser("objects"); p.add_argument("--db", default="JobSearch_DB")
    p.set_defaults(fn=cmd_objects)
    p = sub.add_parser("columns"); p.add_argument("table")
    p.add_argument("--db", default="JobSearch_DB"); p.set_defaults(fn=cmd_columns)
    p = sub.add_parser("sql"); p.add_argument("query"); p.add_argument("--db", default="JobSearch_DB")
    p.add_argument("--allow-write", action="store_true"); p.set_defaults(fn=cmd_sql)

    sub.add_parser("model").set_defaults(fn=cmd_model)
    sub.add_parser("check").set_defaults(fn=cmd_check)

    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
