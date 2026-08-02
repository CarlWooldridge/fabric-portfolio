# Delta Compaction & Optimization Matrix

Reference for `OPTIMIZE`, Z-Order, V-Order, liquid clustering, and related maintenance techniques used throughout P1. A styled, interactive HTML version is also available: [`delta-compaction-matrix-v2.html`](delta-compaction-matrix-v2.html) (download and open locally — GitHub doesn't render HTML files inline).

**Reading the matrix:** 🔵 deferred techniques cost nothing until you invoke them — the "put data anywhere, clean up later" model. 🟠 per-write techniques cost something on *every* write, continuously, in exchange for never letting the problem accumulate. ⬛ one-off is a deliberate, infrequent operation. ⚪ tuning settings don't optimize anything themselves — they change how another technique behaves.

---

## 🔵 Plain OPTIMIZE — Deferred

| | |
|---|---|
| **Command** | `OPTIMIZE dbo.table` |
| **What it optimizes** | File count/size — bins small files together |
| **Initiated by** | Manual, or auto compaction |
| **Read impact** | ▲ Faster — fewer files to open |
| **Write impact** | — None on regular writes |
| **Rewrites files?** | Yes — always |

Default target ~1GB, tuned for large tables. **Adaptive target file size** scales this down for smaller tables. Idempotent.

## 🔵 Z-Order — Deferred

| | |
|---|---|
| **Command** | `OPTIMIZE dbo.table ZORDER BY (col1, col2)` |
| **What it optimizes** | Row placement — co-locates similar values across filter columns |
| **Initiated by** | Manual, part of OPTIMIZE |
| **Read impact** | ▲ Faster multi-column filtered queries (file skipping) |
| **Write impact** | — None on regular writes |
| **Rewrites files?** | Yes |

Named for the **Z-order space-filling curve** — a genuine geometry reference. Best when queries filter 2+ columns together. **Does nothing on a table that compacts to a single file** — verify with `clusteringColumns` in `DESCRIBE DETAIL`, not by trusting the command ran.

## 🟠 V-Order — Per-write

| | |
|---|---|
| **Command** | `OPTIMIZE dbo.table VORDER` (or table property / session default) |
| **What it optimizes** | Internal file encoding — sorting, row-group layout, dictionary encoding |
| **Initiated by** | Automatic on every write once enabled, or forced via OPTIMIZE |
| **Read impact** | ▲ Faster reads, esp. Direct Lake/Power BI (~10–50% for Spark) |
| **Write impact** | ▼ ~15% slower on **every** write while enabled |
| **Rewrites files?** | Yes, at write time |

**Required for Direct Lake** to perform well. Disabled by default in new workspaces (write-heavy default). "V" likely nods to VertiPaq/Verti-Scan — unconfirmed.

## 🔵 Liquid Clustering — Deferred

| | |
|---|---|
| **Command** | Table property `clusterBy` + `OPTIMIZE` |
| **What it optimizes** | Row placement, like Z-Order but reconfigurable later |
| **Initiated by** | Manual OPTIMIZE required to actually cluster |
| **Read impact** | ▲ Faster filtered reads via file skipping |
| **Write impact** | — None on regular writes |
| **Rewrites files?** | Yes, on OPTIMIZE only |

**Regular writes do NOT cluster data** — easy to forget and end up stale. More flexible than Z-Order — can change keys without redefining partitions, because the clustering key is stored as persistent table metadata (`delta.clusteringColumns`) rather than being a stateless, one-off command. Plain `OPTIMIZE` only clusters files not yet marked with the current key; it will not recluster files stamped with an old key.

## ⬛ OPTIMIZE FULL — One-off

| | |
|---|---|
| **Command** | `OPTIMIZE dbo.table FULL` |
| **What it optimizes** | Full reclustering of every file, including previously-clustered ones |
| **Initiated by** | Manual, deliberate |
| **Read impact** | ▲ Restores full clustering benefit after a strategy change |
| **Write impact** | ▼ High — can rewrite most/all of a large table |
| **Rewrites files?** | Yes, all files |

Requires **Fabric Spark runtime 2.0 (Delta 4.2)**. Use only after changing clustering keys/provider — not routine maintenance.

## ⚪ Fast Optimize — Tuning

| | |
|---|---|
| **Command** | `SET spark.microsoft.delta.optimize.fast.enabled = TRUE` |
| **What it optimizes** | Smarter bin selection — skips compaction unlikely to help |
| **Initiated by** | Session-level, applies during any OPTIMIZE |
| **Read impact** | ▲ Same benefit as plain OPTIMIZE |
| **Write impact** | ▲ Lower — fewer unnecessary rewrites |
| **Rewrites files?** | Only bins likely to benefit |

Not compatible with Z-Order or liquid clustering. Tunable via `minNumFiles`, `parquetCoefficient`.

## 🟠 Auto Compaction — Per-write

| | |
|---|---|
| **Command** | `SET spark.databricks.delta.autoCompact.enabled = TRUE` (session) or `TBLPROPERTIES('delta.autoOptimize.autoCompact'='true')` (table) |
| **What it optimizes** | File count/size, same target as plain OPTIMIZE |
| **Initiated by** | Automatic, triggered right after each write |
| **Read impact** | ▲ Same as plain OPTIMIZE, continuously maintained |
| **Write impact** | ▼ Small added cost on writes that trigger it |
| **Rewrites files?** | Yes, when triggered |

The production answer to **"won't a re-run undo this?"** — stops a table from re-fragmenting on every reload, at the cost of paying compaction on every write rather than deferring it.

## ⚪ onCheckpointOnly mode — Tuning

| | |
|---|---|
| **Command** | `SET spark.microsoft.delta.autoCompact.onCheckpointOnly.enabled = TRUE` |
| **What it optimizes** | Reduces overhead of auto compaction's own fragmentation checks |
| **Initiated by** | Session-level, modifies auto compaction behavior |
| **Read impact** | — No direct read impact |
| **Write impact** | ▲ Lowers per-commit overhead |
| **Rewrites files?** | N/A — tuning only |

Requires **runtime 2.0 (Delta 4.1)**. Defers evaluation to checkpoint commits (~every 10) instead of every write.

## ⚪ File-level compaction targets — Tuning

| | |
|---|---|
| **Command** | `SET spark.microsoft.delta.optimize.fileLevelTarget.enabled = TRUE` |
| **What it optimizes** | Prevents re-compacting files that already met a prior target size |
| **Initiated by** | Session-level, modifies OPTIMIZE |
| **Read impact** | — No direct read impact |
| **Write impact** | ▲ Reduces write amplification |
| **Rewrites files?** | Fewer files touched |

Not on by default — **Microsoft recommends enabling it.**

## 🔵 VACUUM — Deferred

| | |
|---|---|
| **Command** | `VACUUM dbo.table [RETAIN n HOURS]` |
| **What it optimizes** | Physically deletes old file versions no longer part of current table state |
| **Initiated by** | Manual, separate from OPTIMIZE |
| **Read impact** | — No benefit to current queries |
| **Write impact** | — Storage cleanup, not query optimization |
| **Rewrites files?** | Deletes, doesn't rewrite |

Default retention 7 days, governed by the `delta.deletedFileRetentionDuration` table property. This is the direct answer to "won't old versions from repeated overwrites just sit there" — they do, until VACUUM runs.

---

## Warehouse — a different model entirely

Everything above is Lakehouse/Spark syntax. **Fabric Warehouse has no `OPTIMIZE`, `VORDER`, or `ZORDER` command at all** — because it isn't meant to need one:

- **Compaction is automatic and query-triggered** — it can fire on a plain `SELECT`, with no user action.
- **V-Order is applied automatically**, not opt-in the way it is on Lakehouse.
- **`CLUSTER BY`** in `CREATE TABLE` / CTAS is the write-time Z-Order equivalent — declared once at ingestion, not re-run as maintenance. Requires ≥1M rows per ingestion statement to engage.

**The distinction that actually matters:** Lakehouse exposes optimization as maintenance you run *after* the fact. Warehouse exposes it as declarative intent specified *at write time*. Neither is "better" — they're different philosophies matched to different engines, and confusing one for a lesser version of the other is a mistake worth avoiding.
