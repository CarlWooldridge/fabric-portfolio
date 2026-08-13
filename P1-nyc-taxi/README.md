# Project 1 — NYC Taxi on Microsoft Fabric

**Goal:** Touch every core Fabric mechanism once, on clean data, and compare them empirically rather than accepting documentation claims at face value.

**Dataset:** NYC TLC Green Taxi trip records — 76,513,115 rows, ~2 GB Parquet, sourced from Azure Open Datasets.

**Environment:** Fabric trial capacity (F-SKU trial, East US), schema-enabled Lakehouse (`NYCTaxiLH`), Warehouse (`NYC_Taxi_WH`).

---

## Summary of what was actually built

- Same dataset ingested three independent ways (Data pipeline Copy activity, Dataflow Gen2, PySpark notebook) and compared on duration, file layout, and query performance
- Six variants of the fact table created to isolate the effect of individual optimization techniques
- A star schema (1 fact, 6 dimensions) built in a `gold` schema, feeding a Direct Lake semantic model and Power BI report
- A Materialized Lake View for precomputed aggregates
- A Warehouse populated via cross-database CTAS, with a duplicate report bound to it for engine comparison
- Pipeline orchestration with parameterized notebook activities

---

## Finding 1 — The three ingestion methods produce wildly different physical layouts

Same 76.5M rows. Same logical data. Row counts and date ranges verified identical via T-SQL across all three.

| Method | Duration | Files | Size | Avg file size |
|---|---|---|---|---|
| Data pipeline (Copy activity) | 1m30s – 2m33s | 80 | 2.39 GB | 30.5 MB |
| Notebook (PySpark) | 43s – 8m* | 25 | 1.68 GB | 68.7 MB |
| Dataflow Gen2 | 35m55s – 37m25s | 2 | 1.52 GB | 777 MB |

\* Notebook durations are unreliable when run interactively — the Spark session stays alive until manually stopped, so "duration" measures clicking habits, not execution. Pipeline-orchestrated notebook runs give honest numbers because Fabric manages the session lifecycle.

**Why Dataflow Gen2 was 15–20x slower.** Not a configuration mistake — it's structural. Dataflow Gen2 writes through an internal staging Lakehouse in Delta Parquet format even when the destination is your own Lakehouse, and it has no parallel file ingestion — Power Query processes files in series. Published benchmarks put Fast Copy at ~40% slower than the Copy activity even when using the same backend; the gap here suggests Fast Copy wasn't engaged at all.

**The right conclusion isn't "Dataflow Gen2 is bad."** It trades throughput for a low-code transformation model and automatic Delta staging. For a bulk full-copy with no transformations, Copy activity or a notebook is the correct tool. Dataflow Gen2 earns its overhead when you actually need Power Query's transformation surface — or when the person maintaining the logic isn't a Spark developer.

### Fragmentation costs compression, not just I/O

The size differences above are the same rows compressed differently. Parquet compression (dictionary encoding, RLE) operates *within* row groups — more files means smaller row groups, smaller dictionaries, fewer long identical runs, and every row group starting compression fresh.

This was confirmed directly: running `OPTIMIZE` on the Copy activity table took it from **2.39 GB / 80 files → 1.67 GB / 3 files**. A 30% size reduction with zero data change.

---

## Finding 2 — Optimization only helps queries that have something to skip

Two benchmark queries, run repeatedly, averaged via `queryinsights.exec_requests_history`:

- **Query 1** — full-table aggregate, no `WHERE` clause
- **Query 2** — filtered by date range, grouped by day

| Table | Query 1 (ms) | Query 2 (ms) |
|---|---|---|
| copy_activity (raw, 80 files) | 3,764 | 2,418 |
| copy_activity + OPTIMIZE | 2,218 | 701 |
| copy_activity + OPTIMIZE + VORDER | 2,493 | 246 |
| copy_activity + OPTIMIZE + ZORDER + VORDER | 2,482 | 222 |
| dataflow (2 files) | 2,841 | 1,977 |
| notebook (25 files) | 3,116 | 1,597 |
| **taxi_summary_mlv** (materialized) | **69** | — |

**Query 1 improved 41% and then stopped.** Compaction helped — fewer files means less per-file open overhead. V-Order and Z-Order added nothing (arguably slightly negative, within noise). This is structural: an unfiltered aggregate over every row has *nothing to skip*, and file-skipping is the entire mechanism behind V-Order and Z-Order.

**Query 2 improved 91%.** 2,418 → 701 (compaction) → 246 (V-Order) → 222 (Z-Order). The `WHERE` clause gives skipping something to do.

**A precise note on the V-Order gain in Query 2:** with only 2–3 files, the improvement can't be file-level skipping — there aren't enough files. That gain is row-group pruning *within* files, enabled by V-Order's sorting making Parquet's internal min/max statistics far more selective.

### The materialized view result is a different category of answer

3,764 ms → 69 ms, a 98% reduction. But this isn't a faster scan — it's no scan. The 76M-row aggregation still happens, it just moved to refresh time and off the interactive query path.

**The honest framing: precomputation, not optimization.** Once a table is compacted, an unfiltered aggregate has no data-skipping headroom left. The next lever isn't storage tuning, it's not scanning.

### A Z-Order request that silently did nothing

`OPTIMIZE gold.fact_trips ZORDER BY (PickupDate) VORDER` was run against the gold fact table. `DESCRIBE DETAIL` afterward showed:

```
numFiles=1, clusteringColumns=[], properties={'delta.parquet.vorder.enabled': 'true'}
```

V-Order applied and is verifiable in table properties. **Z-Order did not** — `clusteringColumns` is empty. The compacted table collapsed to a single 1.8 GB file, leaving no distribution for Z-Order to act on.

Z-Order's benefit is contingent on file count. Including it in the command doesn't guarantee it did anything, and `clusteringColumns` is how you check rather than assume.

---

## Finding 3 — Lakehouse vs. Warehouse

### The engine boundary is real, and I hit it five separate ways

Attempting to populate the Warehouse from the Lakehouse surfaced a series of T-SQL surface-area gaps, each traceable to Warehouse's Parquet-based distributed architecture rather than being arbitrary:

| Attempted | Result |
|---|---|
| `CREATE CLUSTERED COLUMNSTORE INDEX` | Unsupported — indexing isn't a user-facing concept; every table is columnstore by default |
| `ON [PRIMARY]` filegroup syntax | Unsupported — no filegroups other than PRIMARY |
| `sysname` column in a created table | `Msg 24574` — not a storable type |
| `nvarchar` column | `Msg 24574` — Warehouse has no `nvarchar`; `varchar` is already UTF-8 |
| `SELECT INTO` / `INSERT INTO...SELECT` from cross-database `INFORMATION_SCHEMA` | `Msg 15816` — cross-database metadata can't participate in a distributed write plan |
| `%%tsql` notebook magic | Not available in this environment |
| Path-based Spark `OPTIMIZE` against Warehouse table | `DELTA_MISSING_DELTA_TABLE` — the path Warehouse's Properties pane surfaces isn't an externally-addressable Delta root |

The loop-based automation was abandoned in favor of explicit CTAS statements. **Knowing where the automation boundary sits was more useful than the loop would have been.**

### Warehouse optimization: automatic, but not absent

My first conclusion — that Warehouse offers no optimization control at all — was wrong, and worth correcting because the accurate version is more interesting.

- **Automatic data compaction is real and query-triggered.** It merges small Parquet files in the background, and can fire on a plain `SELECT`. Documentation is candid that performance may degrade until it completes.
- **`CLUSTER BY` exists** in `CREATE TABLE` and CTAS — a write-time Z-Order equivalent using the same space-filling-curve approach, with clustering metadata embedded in the manifest. Requires ≥1M rows per ingestion statement to engage.
- **V-Order is applied automatically** in Warehouse, unlike Lakehouse where it's opt-in.

**The corrected distinction:** Lakehouse exposes optimization as *maintenance you run after the fact*; Warehouse exposes it as *declarative intent specified at write time*. That's a sharper contrast than "one has controls and one doesn't."

The Warehouse `fact_trips` populated via CTAS landed at 42 files averaging ~48 MB — below the documented 100 MB minimum. Whether automatic compaction had simply not yet run, or whether a one-shot 76M-row cross-database CTAS is an atypical write pattern for it, was not resolved.

### Direct Lake performance depends on file layout, not item type

Both Lakehouse and Warehouse store Delta Parquet in OneLake. Building a semantic model via the OneLake catalog against the *Warehouse* offered Direct Lake as the storage mode — Direct Lake is not Lakehouse-exclusive.

That means **Direct-Lake-on-Lakehouse vs. Direct-Lake-on-Warehouse should perform identically**, since both bypass the SQL engine and read the same file format. Any difference reduces to physical layout, which is a function of the write path.

The comparison that *does* show a difference is Direct Lake vs. genuine DirectQuery. A duplicate report bound to a composite model (DirectQuery fact + Import dims) against Warehouse was noticeably less responsive during interactive use than the Direct Lake model. Two compounding causes: DirectQuery requires a live T-SQL round trip on every visual interaction, and the Warehouse's fact table was unoptimized relative to the hand-tuned Lakehouse source.

### Why no indexes, yet full transactions

These seem contradictory but aren't — they're different concerns.

**Indexes are read-optimization.** Warehouse has none because Parquet's columnar layout and embedded min/max statistics already serve that role. The Parquet files *are* the index.

**Transactions are write-atomicity.** Delta is natively atomic at the single-commit level — files are immutable, and a commit either appends a log entry or doesn't. `BEGIN TRAN`/`COMMIT`/`ROLLBACK` adds a coordination layer *above* that: holding several already-atomic proposals pending, then making them all visible together.

Delta's immutable-file design makes multi-statement transactions *easier* to build than in a traditional mutable-page database — there's no in-place page to corrupt mid-write.

---

## Finding 4 — Gotchas worth carrying forward

**"Succeeded" does not mean "correct."** The first Copy job reported success with **0 rows read, 0 rows written** — a file-level passthrough that copied folder structure into `Tables/` rather than parsing rows. It produced a folder Fabric couldn't recognize as Delta. Row counts, not status flags, are how you verify a load.

**Spark's default case-insensitive column resolution.** After joining `dim_date` to a holidays table, `.drop("date")` removed **both** `Date` and `date` — Spark's default (`spark.sql.caseSensitive = false`) matched both. The notebook ran clean; Direct Lake discovered the missing primary key column much later. Rename before joining rather than relying on case to disambiguate.

**Direct Lake enforces exact type matching on relationship keys.** `fact_trips[vendorID]` (Int64) against `dim_vendor[VendorID]` (String) was rejected outright — Import mode would have coerced. There's no modeling-side fix; it has to be corrected at the source table.

**CSV reads default to all-string.** `spark.read.format("csv").option("header","true")` without `inferSchema` types *every* column as `StringType`. That's the upstream cause of the type mismatch above.

**Relationship grain matters as much as relationship existence.** The `dim_date` relationship was initially built on a full `Datetime` column rather than a date-only key. The star schema had the right shape but the join key defeated its cardinality benefit — date-range slicers were visibly slow until the relationship was rebuilt on a true `Date` column.

**Iterators over large fact tables blow memory budgets.** `AVERAGEX` computing `DATEDIFF` per row across 76.5M rows required 5,289 MB against a 3,072 MB limit. It has to materialize a 76M-row virtual table before averaging. The fix is the same materialize-upstream principle as the MLV: store the derived value as a column, and `AVERAGE` becomes a native single-pass aggregation.

**Metadata sync lag is a recurring pattern, not a series of unrelated bugs.** Spark writes take time to propagate to the SQL analytics endpoint, the Direct Lake wizard's table picker, and semantic model schemas. Symptoms looked like missing tables, missing columns, and schema errors. First hypothesis for any "the thing I just created isn't there" should be sync lag, verified with `DESCRIBE` in the notebook.

**Capacity throttling is measurable and worth diagnosing.** After a heavy day, the Capacity Metrics app showed `Health: Throttling`, 2,100 seconds cumulative throttling, and P95 interactive delay of 63.81 seconds, with usage variance at 390 — spiky, burst-heavy load. Slow model editing wasn't a modeling problem.

**Fabric UI traps.** The Copy data assistant creates a *Copy job* item rather than a Copy activity. Task flows look like orchestration but are a static diagram with no execution engine. Lakehouse schemas can't be retrofitted onto an existing Lakehouse. Notebook parameter cells must be explicitly toggled or pipeline parameters silently don't arrive — a deliberately absurd sentinel default (`"THIS_DEFAULT_WAS_NOT_OVERRIDDEN"`) is the fastest way to prove whether injection is working.

---

## Naming convention adopted

| Layer | Convention | Rationale |
|---|---|---|
| `Files/` | Source system naming | Raw, unmanaged, no modeling claim yet |
| Bronze | Source system naming | Faithful mirror of source, just in Delta |
| Silver | Entity naming (`customers`, `orders`) | Cleaned and conformed, not yet dimensionally shaped |
| Gold | `dim_` / `fact_` prefixes | Grain fixed, keys assigned, playing a dimensional role |
| Semantic model | Same as gold, unchanged | No renaming layer between storage and model |

Dimensional naming starts at the layer where dimensional modeling actually happens.

---

## What was deliberately not done

- **Full factorial isolation of V-Order vs. Z-Order.** Tested combined, since Microsoft's Direct Lake guidance recommends applying both together. A five-table factorial breakdown was out of scope for a project whose mandate was "speed over polish."
- **Optimizing the small dimension tables.** `dim_date` at a few thousand rows compacted from 8 files to 1; the others were already single-file. Z-Order and V-Order were skipped deliberately — nothing to skip, real write cost, no measurable benefit.
- **A precomputed `TripDuration` column.** Considered and deferred as schema scope creep; the DAX iterator cost was validated via the memory error instead.

---

## Reference artifacts

- [`reference/delta-compaction-matrix-v2.html`](reference/delta-compaction-matrix-v2.html) — every compaction and optimization technique, with syntax, read/write impact, and whether cost is deferred or per-write
- [`reference/fabric-glossary.html`](reference/fabric-glossary.html) — Fabric terminology, with mappings to SQL Server / Power BI equivalents where they exist
- [`reference/dp600-project-checklist.html`](reference/dp600-project-checklist.html) — the three-project checklist this work was built against
