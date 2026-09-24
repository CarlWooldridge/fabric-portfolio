# Microsoft Fabric — Hands-On Project Portfolio

Structured, hands-on work with Microsoft Fabric, built alongside DP-600 (Fabric Analytics Engineer) certification study.

The emphasis throughout is on **measuring rather than assuming** — benchmarking claims against real data, verifying that settings did what they said they did, and documenting where platform boundaries actually sit rather than where documentation implies they should be. Several findings below correct assumptions made earlier in the same project, on the record, because the correction was the more useful outcome.

---

## Projects

### [P1 — NYC Taxi](P1-nyc-taxi/) *(complete)*

76.5M rows through every core Fabric mechanism, compared empirically. Built over 12 working days (Jul 28 – Aug 13).

**Selected findings:**
- Three ingestion methods (Copy activity, Dataflow Gen2, PySpark notebook) produced file counts of 2, 25, and 80 for identical data — a 15–20x duration spread and a 30% size difference driven by compression efficiency, not row count
- Compaction improved an unfiltered aggregate by 41% and hit a hard ceiling; a filtered query improved 91% — because file-skipping optimizations need something to skip
- A materialized view took the same aggregate from 3,764 ms to 69 ms — precomputation, not optimization, and worth naming as the distinction it is
- A `ZORDER BY` clause that silently did nothing, caught by checking `clusteringColumns` rather than trusting the command
- Five T-SQL surface-area gaps in Fabric Warehouse (no manual indexing, no `nvarchar`, no cross-database `INFORMATION_SCHEMA` in a distributed write plan), followed by the correction that Warehouse *does* have write-time optimization via `CLUSTER BY` and automatic compaction — it just isn't exposed as a post-hoc command the way Lakehouse's `OPTIMIZE` is
- A DAX `AVERAGEX` iterator over the full fact table that exceeded the trial capacity's memory limit outright, resolved by moving the calculation upstream instead of tuning the query

### [P2 — Olist: the DP-600 build](P2-olist/) *(complete)*

My DP-600 preparation, built rather than read: 25 day-sessions mapped to the exam's skills outline, run Sep 16–24 on a new Olist e-commerce workspace plus the P1 and Job Search workspaces. Every step closed on a measured number, not "it succeeded."

![Eight numbers from the build](P2-olist/graphics/headline-numbers.svg)

**Selected findings:**
- Security is enforced where the query runs, and as whom: the same Viewer saw every row with real values through Import and Direct Lake on OneLake, and only their own rows, masked, through DirectQuery and Direct Lake on the SQL endpoint. A delegated-identity shortcut leaked the whole RLS-protected table
- A SQL view silently cost ~600×: 17 ms as a Direct Lake scan vs 10,057 ms through DirectQuery fallback, with no error until `DirectLakeOnly` turned it into one
- An SCD2 run produced 96,195 people, 99 too many, while every row count matched: a lazy DataFrame re-read the table the `MERGE` had just changed
- After `VACUUM`, `COUNT(*)` at an old version still answered from the Delta log while `SUM(price)` got a 404 — a version you can list is not a version you can read
- A deliberately bad model came out 17% larger (85.56 vs 73.15 MiB) at the same query speed, and the promised "bad `FILTER`" gap didn't exist until the rule was corrected: a measure inside `FILTER` is ~8× slower and moves ~450× more data

### P3 — Original build *(planned)*

Architecture ownership on data I assemble myself, with a written architecture decision record. The lifecycle mechanics once planned here (Git integration, deployment pipelines, XMLA, real-time) were built in P2; P3 applies them end to end.

---

## Applied project

Outside the P1→P3 progression: a system built because I needed it, not because a checklist called for it.

### [Job Search — an AI evaluation pipeline on Fabric](job-search-fabric/) *(complete)*

An AI-assisted job-posting evaluation workflow I run daily, productionized on Fabric with write-back — so the report is something I act *in*, not just look at. 1,066 evaluated postings, 676 employers, a Direct Lake semantic model over a Fabric SQL Database, and a Python User Data Function wired to the report through Translytical Task Flows.

**Selected findings:**
- A `DROP` and recreate destroyed every report write-back, because the dataflow read its own output table to preserve them — the table was its own only backup. The refresh didn't just fail to restore the data, it overwrote the evidence any had existed. Recovered via point-in-time restore, then redesigned around an append-only log so the fact table is genuinely disposable
- A DAX measure returning wrong answers for 8 of 9 rows while the measure, the relationship, the data and every field binding each verified correct — `ALLEXCEPT` operates on a table's *expanded* table, so it silently cleared the filter every visual actually supplies
- Six Fabric boundaries hit the hard way, including a folder shortcut that merges a second CSV into the wrong schema rather than creating a table, a CSV reader that isn't multiline-aware, and a SQL view that falls an entire Direct Lake model back to DirectQuery
- A scoring rubric calibrated by measured override rate rather than preference — two rules I believed in turned out to be coin flips at 45% and 48%, and a threshold change moved precision from 43% to 75% with the recall cost visible in the other column
- Parsing an LLM's prose into a star schema: 93.9% of rows carry a machine-readable score formula inside a sentence, and the 26% whose arithmetic doesn't reconcile get a deliberate two-tier treatment rather than a forced number

---

## Reference material

Built during P1, kept because it stayed useful independent of the project that produced it:

- **[Delta compaction & optimization matrix](https://carlwooldridge.github.io/fabric-portfolio/P1-nyc-taxi/reference/delta-compaction-matrix-v2.html)** ([source](P1-nyc-taxi/reference/delta-compaction-matrix-v2.html)) — every technique with syntax, read/write impact, and whether its cost is deferred or paid per-write
- **[Fabric glossary](https://carlwooldridge.github.io/fabric-portfolio/P1-nyc-taxi/reference/fabric-glossary.html)** ([source](P1-nyc-taxi/reference/fabric-glossary.html)) — terminology, with mappings to SQL Server and Power BI equivalents where they exist
- **[DP-600 project checklist](https://carlwooldridge.github.io/fabric-portfolio/P1-nyc-taxi/reference/dp600-project-checklist.html)** ([source](P1-nyc-taxi/reference/dp600-project-checklist.html)) — every build item mapped to the exam's own skills outline (revised 21 Jul 2026), tagged by domain and by whether it needs Fabric capacity

From P2:

- **[Security in Fabric: ten layers](https://carlwooldridge.github.io/fabric-portfolio/P2-olist/reference/security-ten-layers.html)** ([source](P2-olist/reference/security-ten-layers.html)) — ten security layers, each built and tested as a real user: what each decides, which engines enforce it, what travels through Git and deployment, and the path around every one

From the Job Search project:

- **[Write-back data loss — post-mortem](https://carlwooldridge.github.io/fabric-portfolio/job-search-fabric/reference/writeback-incident-postmortem.html)** ([source](job-search-fabric/reference/writeback-incident-postmortem.html)) — how a routine `DROP` erased its own evidence, why recovery was luck rather than design, and the redesign that removes the failure mode instead of guarding against it
- **[The Verdict Loop](https://carlwooldridge.github.io/fabric-portfolio/job-search-fabric/reference/the-verdict-loop.html)** ([source](job-search-fabric/reference/the-verdict-loop.html)) — design spec for a scoring rubric that corrects itself from recorded decisions, with the measured override rates that justify each rule
- **[Report wireframe](https://carlwooldridge.github.io/fabric-portfolio/job-search-fabric/reference/report-wireframe.html)** ([source](job-search-fabric/reference/report-wireframe.html)) — built before the report, and it caught real layout problems before they were built for real

---

## Documentation

- [`P1-nyc-taxi/README.md`](P1-nyc-taxi/README.md) — the full P1 write-up: findings, benchmarks, gotchas
- [`P2-olist/README.md`](P2-olist/README.md) — the DP-600 build: security and lifecycle, the medallion build, the semantic model, Direct Lake internals, and the corrections along the way
- [`job-search-fabric/README.md`](job-search-fabric/README.md) — the Job Search write-up: write-back architecture, the data-loss incident, platform boundaries, and the AI evaluation pipeline behind it

---

## Environment note

This work was done on a Fabric trial capacity. Trial capacities expire after 60 days with **no read-only fallback** — non-Power BI items go inactive immediately and are permanently deleted after a 7-day grace window unless reassigned to paid capacity. This repository is the durable record: code, queries, findings, and screenshots preserved independently of the environment that produced them.
