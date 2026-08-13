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

### P2 — Finance / Supply Chain *(in progress)*

Medallion architecture on messier real-world data: incremental loads, SCD Type 2, row- and object-level security, calculation groups, and a deliberate before/after optimization exercise. Picks up directly from P1's conventions.

### P3 — Original build *(planned)*

Architecture ownership and lifecycle: original source data, a written architecture decision record, git integration, Dev→Test→Prod deployment pipelines, XMLA-managed semantic model, and a real-time component.

---

## Reference material

Built during P1, kept because it stayed useful independent of the project that produced it:

- **[Delta compaction & optimization matrix](P1-nyc-taxi/reference/delta-compaction-matrix-v2.html)** — every technique with syntax, read/write impact, and whether its cost is deferred or paid per-write
- **[Fabric glossary](P1-nyc-taxi/reference/fabric-glossary.html)** — terminology, with mappings to SQL Server and Power BI equivalents where they exist
- **[DP-600 project checklist](P1-nyc-taxi/reference/dp600-project-checklist.html)** — the three-project structure this work was built against

---

## Documentation

- [`P1-nyc-taxi/README.md`](P1-nyc-taxi/README.md) — the full P1 write-up: findings, benchmarks, gotchas

---

## Environment note

This work was done on a Fabric trial capacity. Trial capacities expire after 60 days with **no read-only fallback** — non-Power BI items go inactive immediately and are permanently deleted after a 7-day grace window unless reassigned to paid capacity. This repository is the durable record: code, queries, findings, and screenshots preserved independently of the environment that produced them.
