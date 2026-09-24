# Screenshots

Two sets, all PNG:

- **Final (7):** full-resolution captures of the finished workspace, taken on the capacity's last day.
- **Session (106):** captured during the build, named by guide day (`d04`…`d25`) or exam item (`ex4`, `ex5`, `ex9`). Most are 400–700 px wide: evidence, not heroes. Days 4–7 are Part 1, on the P1 NYC Taxi workspace; everything from Day 8 on is the Olist workspace.

**Redactions.** Shots marked *(redacted)* had a test user's UPN, the tenant domain, or a workspace, lakehouse, endpoint or connection identifier covered with a solid box. Nothing else was altered.

| Day | File | Shows | Backs |
|---|---|---|---|
| Final | [`p2-lineage.png`](p2-lineage.png) | Item lineage of Olist Model: OlistEH → KQL database → OlistLH → Olist Model → Olist Report | The Eventhouse edge is the `silver.kql_orders` shortcut (Day 23) |
| Final | [`p2-model-diagram.png`](p2-model-diagram.png) | Olist Model diagram: header → lines, bridge, three date relationships (one active), calc group, field parameters, hidden `rls_user_state` | The model |
| Final | [`p2-report-calc-group.png`](p2-report-calc-group.png) | Three self-labeling matrices: one calculation group, three measures, per-item formats | Days 16–17 |
| Final | [`p2-report-field-parameters.png`](p2-report-field-parameters.png) | Freight by Customer State, driven by two field-parameter slicers | Day 17 |
| Final | [`p2-report-windowing.png`](p2-report-windowing.png) | Rank, gap, cumulative %, % of top; window measures beside their calendar twins | Day 18 |
| Final | [`p2-deploy-compare.png`](p2-deploy-compare.png) | Olist Deployment Pipeline, Dev → Test, every item "Same as source" | Lifecycle |
| Final | [`p2-workspace-lineage-partial.png`](p2-workspace-lineage-partial.png) | Whole-workspace lineage (cut off at the bottom) | Evidence only |
| D4 | [`d04-deploy-change-review-members-missing.png`](d04-deploy-change-review-members-missing.png) | Change Review: salary_readers role deploys empty — ADD MEMBER lines only in Dev *(redacted)* | Who doesn't deploy |
| D4 | [`d04-deploy-compare-warehouse-different.png`](d04-deploy-compare-warehouse-different.png) | Deployment pipeline compare: every item Same as source except NYCTaxiWH — Different | Who doesn't deploy: users and role members |
| D4 | [`d04-deployment-rules-grayed.png`](d04-deployment-rules-grayed.png) | Both deployment-rule types grayed out for a Direct Lake on OneLake model | Direct Lake doesn't rebind; parameterize the path |
| D5 | [`d05-impact-dataflow.png`](d05-impact-dataflow.png) | Impact analysis — GetData_DataFlow: 27 items incl. hidden staging lakehouse/warehouse | Impact analysis per item type |
| D5 | [`d05-impact-lakehouse.png`](d05-impact-lakehouse.png) | Impact analysis — NYCTaxiLH: 23 items, 2 workspaces | Impact analysis per item type |
| D5 | [`d05-impact-model.png`](d05-impact-model.png) | Impact analysis — NYC Taxi Model: 1 report | Impact analysis per item type |
| D5 | [`d05-impact-warehouse.png`](d05-impact-warehouse.png) | Impact analysis — NYCTaxiWH: 25 items, 3 workspaces (the shortcuts) | Impact analysis per item type |
| D5 | [`d05-queryinsights-model-sql.png`](d05-queryinsights-model-sql.png) | queryinsights.exec_requests_history — the exact SQL the model sent | Read the SQL the engine actually ran |
| D5 | [`d05-rename-error-says-capacity.png`](d05-rename-error-says-capacity.png) | Column renamed: tip visuals fail with 'capacity or license issue' — the error lies | The error lies; the cause is behind See details |
| D5 | [`d05-stale-column-name-in-model.png`](d05-stale-column-name-in-model.png) | Every visual fails on 'tipAmount_x' after the rename was reversed | A DirectQuery model caches a stale schema refresh won't clear |
| D5 | [`d05-warehouse-catalog-clean.png`](d05-warehouse-catalog-clean.png) | sys.columns and INFORMATION_SCHEMA both say tipAmount | Model-side, not source-side |
| D6 | [`d06-direct-lake-no-download.png`](d06-direct-lake-no-download.png) | 'Can't download … the dataset is in Direct Lake mode' | Direct Lake blocks .pbix download |
| D6 | [`d06-file-formats-sizes.png`](d06-file-formats-sizes.png) | .pbix 1,938 KB · .pbit 17 KB · .pbip 1 KB · .pbids 1 KB | PBIX holds data only for Import tables |
| D6 | [`d06-lineage-shared-model.png`](d06-lineage-shared-model.png) | Item lineage: two reports on one model; cross-workspace shortcut edge | Shared semantic model |
| D6 | [`d06-xmla-edit-uncommitted.png`](d06-xmla-edit-uncommitted.png) | After a Tabular Editor save, Source control shows NYC Taxi Model Uncommitted | XMLA and Git edit the same definition; uncommitted ≠ not applied |
| D7 | [`d07-alm-toolkit-update-trap.png`](d07-alm-toolkit-update-trap.png) | ALM Toolkit pre-selects Update on LakehousePath — would repoint Test at Dev | ALM Toolkit knows nothing about deployment rules |
| D7 | [`d07-best-practice-analyzer.png`](d07-best-practice-analyzer.png) | BPA: 181 objects breaking 16 rules — four matter | BPA is the only tool with a ruleset; the value is the triage |
| D7 | [`d07-dates-2008-to-2081.png`](d07-dates-2008-to-2081.png) | Unfiltered, the date axis runs 2008 → 2081 — out-of-range trip dates | Data quality: dim_date bloat |
| D7 | [`d07-dax-studio-cold-1203ms.png`](d07-dax-studio-cold-1203ms.png) | Cold: 1,203 ms — SE 88% | SE-heavy → fix the model, not the DAX |
| D7 | [`d07-dax-studio-warm-127ms.png`](d07-dax-studio-warm-127ms.png) | Warm: 127 ms, all from SE cache | Measure cold (Clear on Run) |
| D7 | [`d07-dmv-calc-dependency.png`](d07-dmv-calc-dependency.png) | DISCOVER_CALC_DEPENDENCY: what depends on what inside a model | DMVs |
| D7 | [`d07-memory-analyzer-zeros.png`](d07-memory-analyzer-zeros.png) | Fabric Memory analyzer agrees: every Direct Lake table 0 bytes | Two tools agree — it's the engine, not the tool |
| D7 | [`d07-performance-analyzer.png`](d07-performance-analyzer.png) | Performance analyzer: 250–380 ms first, ~1,000–1,450 ms after a slicer change | Rendering → Performance analyzer |
| D7 | [`d07-vertipaq-dim-date-74pct.png`](d07-vertipaq-dim-date-74pct.png) | Warehouse model: dim_date[Date] 1.70 MB = 74% of the model, cardinality 26,474 | Cut cardinality to cut size |
| D7 | [`d07-vertipaq-not-resident.png`](d07-vertipaq-not-resident.png) | VertiPaq Analyzer on Direct Lake on OneLake: every column 0, 'not resident' | Storage tools read 0 for Direct Lake on OneLake |
| D7 | [`d07-vertipaq-summary-2mib.png`](d07-vertipaq-summary-2mib.png) | Warehouse model total: 2.17 MiB | Baseline size |
| D8 | [`d08-raw-ground-truth-counts.png`](d08-raw-ground-truth-counts.png) | Python CSV record counts — the ground truth every load is checked against | Row counts, not 'Succeeded' |
| D9 | [`d09-dataflow-profiling.png`](d09-dataflow-profiling.png) | Dataflow Gen2 column quality / distribution / profile — top 1,000 rows by default | Profile before transforming |
| D9 | [`d09-folding-constant.png`](d09-folding-constant.png) | A whole-column expression folded — collapsed to the constant 'bebes' | Folding rule, corrected |
| D9 | [`d09-staging-on-vs-off.png`](d09-staging-on-vs-off.png) | Monitor: staging on 1m 7s vs off 15s, same dataflow | Staging is a cost unless something downstream uses it |
| D11 | [`d11-expression-not-ancestor.png`](d11-expression-not-ancestor.png) | Expression builder: 'not an ancestor' — connect the arrow first | Pipeline gotcha |
| D11 | [`d11-fault-tolerance-off-fails.png`](d11-fault-tolerance-off-fails.png) | Fault tolerance off: TypeConversionFailure on 'abc' — 0 rows loaded | One bad row stops everything |
| D11 | [`d11-fault-tolerance-on-skipped-1.png`](d11-fault-tolerance-on-skipped-1.png) | Fault tolerance on: rowsRead 112,651 · rowsCopied 112,650 · rowsSkipped 1 | Skip keeps it running; logging makes it auditable |
| D11 | [`d11-p2-incremental-false-branch.png`](d11-p2-incremental-false-branch.png) | P2 Incremental: Lookup → notebook → If; ForEach Copy ×9; False branch taken | Pipeline control flow |
| D12 | [`d12-scd2-movers-same-key.png`](d12-scd2-movers-same-key.png) | Existing movers: 1900-01-01 row closed, 2018 row current, same customer_key | SCD2 proof (names synthetic) |
| D12 | [`d12-scd2-people-96195-bug.png`](d12-scd2-people-96195-bug.png) | First run: people 96,195 — 99 too many (the lazy-evaluation bug) | Materialize before you change the table you read |
| D13 | [`d13-monitor-hc-names-430.png`](d13-monitor-hc-names-430.png) | Monitor: failed runs use plain names, the success runs HC_ (shared session) | HTTP 430 = one Spark session |
| D13 | [`d13-p2-rebuild-four-green.png`](d13-p2-rebuild-four-green.png) | P2 Rebuild: Bronze → Silver → SCD2 → Gold, ~7½ min | One-button rebuild; key sums identical |
| D14 | [`d14-count-after-vacuum-3713.png`](d14-count-after-vacuum-3713.png) | After VACUUM RETAIN 0 HOURS, COUNT(*) at version 0 still answers 3,713 | COUNT(*) is metadata-only |
| D14 | [`d14-hidden-livysession.png`](d14-hidden-livysession.png) | A closed Spark SQL query tab still holds a LivySession | Hidden sessions hold the capacity |
| D14 | [`d14-maintenance-false-branch.png`](d14-maintenance-false-branch.png) | Run 2: compact → skipped | Conditional OPTIMIZE |
| D14 | [`d14-maintenance-true-branch.png`](d14-maintenance-true-branch.png) | P2 Maintenance run 1: too many files → Optimize Table ran | Conditional OPTIMIZE |
| D14 | [`d14-sum-after-vacuum-404.png`](d14-sum-after-vacuum-404.png) | SUM(price) at version 0 fails — 404 on a data file *(redacted)* | A version you can list is not a version you can read |
| D15 | [`d15-bridge-blank-row.png`](d15-bridge-blank-row.png) | Bridge model: Order Count flat, Unknown row, and the virtual blank row | Bridge = two one-to-many relationships |
| D15 | [`d15-direct-lake-all-scan-157ms.png`](d15-direct-lake-all-scan-157ms.png) | DAX Studio: every SE line a Scan, no SQL — Direct Lake proven | Prove it's Direct Lake |
| D15 | [`d15-edit-tables-fails-with-parameter.png`](d15-edit-tables-fails-with-parameter.png) | Edit tables: 'ConceptualSchemaSettings should not be provided for non-Direct Lake queries' | Add tables first, parameterize last |
| D15 | [`d15-info-expressions-lakehousepath.png`](d15-info-expressions-lakehousepath.png) | INFO.EXPRESSIONS(): Source reads AzureStorage.DataLake(LakehousePath, …) *(redacted)* | Check the Source line, not just the rule |
| D15 | [`d15-many-to-many-no-blank-row.png`](d15-many-to-many-no-blank-row.png) | Forced *:* : Order Count splits, blank row gone — a limited relationship | Observed the limited-relationship difference |
| D15 | [`d15-orders-containing-crossfilter.png`](d15-orders-containing-crossfilter.png) | Avg Days to Deliver flat at 12.50; CROSSFILTER version varies by category | Filters don't flow uphill |
| D15 | [`d15-related-fails-limited.png`](d15-related-fails-limited.png) | RELATED across the *:* relationship fails | Limited relationship |
| D15 | [`d15-test-fails-is-the-pass.png`](d15-test-fails-is-the-pass.png) | Test stage: every visual errors — Test reads its own empty lakehouse | A pipeline moves code, never data |
| D16 | [`d16-calc-group-unconstrained-join.png`](d16-calc-group-unconstrained-join.png) | Calculation-group column with no measure: InvalidUnconstrainedJoin | Calc groups need explicit measures |
| D16 | [`d16-yoy-formatted-as-currency.png`](d16-yoy-formatted-as-currency.png) | YoY % renders as $122.65 / $0.20 — inherits the measure's format | Bridge into dynamic format strings |
| D17 | [`d17-dynamic-format-strings.png`](d17-dynamic-format-strings.png) | Revenue 49.8K/6.2M/13.6M; YoY % item renders 0.0% while Current keeps each measure's format | Two levels of dynamic format string |
| D17 | [`d17-field-parameter-blank.png`](d17-field-parameter-blank.png) | Field-parameter visual blank — wells reversed, no Show selected field | Diagnose the wells before the engine |
| D17 | [`d17-field-parameter-working.png`](d17-field-parameter-working.png) | Freight by Customer State — one visual, two slicers | Field parameters do work on Direct Lake on OneLake |
| D17 | [`d17-self-labeling-matrices.png`](d17-self-labeling-matrices.png) | SELECTEDMEASURENAME() label item — each matrix names its measure | Calculation item as a label |
| D17 | [`d17-show-selected-field.png`](d17-show-selected-field.png) | The one setting: Field well → Show selected field | Field parameters |
| D18 | [`d18-bad-filter-measure.png`](d18-bad-filter-measure.png) | Bad Filter (measure): 3 SE queries, every column of 112,650 rows | 8× slower, 450× more data |
| D18 | [`d18-bad-filter-optimized-away.png`](d18-bad-filter-optimized-away.png) | Bad and Good send the identical storage-engine query | The optimizer rewrote Bad into Good |
| D18 | [`d18-fast-iterate.png`](d18-fast-iterate.png) | Fast Iterate: one scan, CallbackDataID, 1 row back | Context transition |
| D18 | [`d18-good-filter-column.png`](d18-good-filter-column.png) | Good Filter (column): 1 SE query, 1,099 rows | Filter columns, not tables |
| D18 | [`d18-has-one-value-trap.png`](d18-has-one-value-trap.png) | Six one-category states: Has One Value FALSE, Has One Category TRUE | Filter through the fact |
| D18 | [`d18-info-campinas.png`](d18-info-campinas.png) | Campinas: Is Filtered FALSE, Is Cross TRUE, Selected State SP | ISFILTERED vs ISCROSSFILTERED |
| D18 | [`d18-info-other-table.png`](d18-info-other-table.png) | Customer-state filter: Lines Crossed TRUE, seller_state not crossed | Filters never climb back up |
| D18 | [`d18-pareto-gap-cumulative.png`](d18-pareto-gap-cumulative.png) | Revenue Rank · Gap to State Above · Cumulative Revenue % · % of Top State | Window functions where there's no calendar |
| D18 | [`d18-slow-iterate.png`](d18-slow-iterate.png) | Slow Iterate: every column shipped twice, FE 266–312 ms | 9× slower |
| D18 | [`d18-window-vs-calendar-twins.png`](d18-window-vs-calendar-twins.png) | Window measures beside their calendar twins — rows match, totals diverge | OFFSET vs PREVIOUSMONTH |
| D19 | [`d19-display-units-0-0mm.png`](d19-display-units-0-0mm.png) | 0.0MM — card display units on top of a self-scaling format string | Display units: None |
| D19 | [`d19-field-param-ols-owner.png`](d19-field-param-ols-owner.png) | As Carl: Customer Name draws a bar per customer | OLS through a field parameter |
| D19 | [`d19-field-param-ols-quiet.png`](d19-field-param-ols-quiet.png) | As test.north: the secured field silently drops out | OLS fails quietly through a field parameter |
| D19 | [`d19-ols-visual-errors.png`](d19-ols-visual-errors.png) | OLS: the visual errors like a deleted field *(redacted)* | OLS fails loudly |
| D19 | [`d19-rls-no-role.png`](d19-rls-no-role.png) | No role: 13.6M · 99K · 96K · $16.0M | Dynamic RLS |
| D19 | [`d19-rls-test-analyst-rj.png`](d19-rls-test-analyst-rj.png) | test.analyst (RJ): 1.8M · 13K · 12K · $2.1M | Dynamic RLS |
| D19 | [`d19-rls-test-north-sp.png`](d19-rls-test-north-sp.png) | test.north (SP): 5.2M · 42K · 40K · $6.0M | Dynamic RLS |
| D19 | [`d19-static-seller-role-leak.png`](d19-static-seller-role-leak.png) | Static seller role: only Revenue changes — orders, customers, payments leak | Put RLS at the top of what you protect |
| D19 | [`d19-test-as-role-sso.png`](d19-test-as-role-sso.png) | 'Test as role does not work with Single Sign-On (SSO)' | SSO vs fixed identity trade-off |
| D19 | [`d19-test-north-lakehouse-gold-only.png`](d19-test-north-lakehouse-gold-only.png) | test.north in the lakehouse: gold only, Files unable to load *(redacted)* | OneLake role scope |
| D19 | [`d19-test-north-sees-all-customers.png`](d19-test-north-sees-all-customers.png) | test.north reads every customer row in the lakehouse *(redacted)* | Model RLS protects the report; OneLake security protects the data |
| D20 | [`d20-incremental-refresh-policy.png`](d20-incremental-refresh-policy.png) | Incremental refresh: archive 11 years, refresh 12 months *(redacted)* | Rolling window counts back from today |
| D20 | [`d20-partitions-refreshed-time.png`](d20-partitions-refreshed-time.png) | Second refresh touched only the 12 monthly partitions | Incremental proven |
| D20 | [`d20-partitions-rows.png`](d20-partitions-rows.png) | 25 partitions; only 2016/2017/2018 hold rows | Coarse years, fine months |
| D20 | [`d20-sso-default-connection.png`](d20-sso-default-connection.png) | Import model on 'Default: Single Sign-On' — can't refresh *(redacted)* | Import refresh needs a stored credential |
| D21 | [`d21-bad-columns.png`](d21-bad-columns.png) | Bad model columns: text keys, review comments, timestamps with seconds | Where the +17% went |
| D21 | [`d21-bad-model-86mib.png`](d21-bad-model-86mib.png) | Olist Model Bad: 85.56 MiB · 2 tables · 42 columns | Good vs bad model |
| D21 | [`d21-import-columns.png`](d21-import-columns.png) | Import model columns: customer_unique_id and names lead | Text columns cost the most |
| D21 | [`d21-import-model-73mib.png`](d21-import-model-73mib.png) | Olist Model Import: 73.15 MiB · 13 tables · 83 columns | Good vs bad model |
| D22 | [`d22-kql-queries.png`](d22-kql-queries.png) | The KQL drill in a queryset | KQL |
| D22 | [`d22-kql-timechart-black-friday.png`](d22-kql-timechart-black-friday.png) | Weekly orders timechart — the Black Friday 2017 spike | render timechart |
| D23 | [`d23-eventstream-3-events.png`](d23-eventstream-3-events.png) | Workspace-item events arriving — 3 messages *(redacted)* | Scope locked at creation |
| D23 | [`d23-mirroring-statistics-63pct.png`](d23-mirroring-statistics-63pct.png) | mirroring-statistics: 63.6% complete, MaxLatency 01:22 — latency is per table *(redacted)* | OneLake availability batches up to 3 hours |
| D23 | [`d23-real-time-hub.png`](d23-real-time-hub.png) | Real-Time hub: data in motion | Real-Time hub vs OneLake catalog |
| D23 | [`d23-shortcut-passthrough-delegated.png`](d23-shortcut-passthrough-delegated.png) | Shortcut connection method: Passthrough vs Delegated identity | Delegated turns per-user security into one identity |
| D24 | [`d24-dl-sql-new-column-grayed.png`](d24-dl-sql-new-column-grayed.png) | Direct Lake on SQL: New column grayed; the view carries a warning | OneLake vs SQL flavor |
| D24 | [`d24-tmdl-sql-database.png`](d24-tmdl-sql-database.png) | TMDL view: expression DatabaseQuery = Sql.Database(…, <endpoint GUID>) *(redacted)* | How to tell the flavors apart |
| D24 | [`d24-user-context-calc-column.png`](d24-user-context-calc-column.png) | Direct Lake on OneLake: Is Big user-context calculated column | Calculated columns, preview |
| D25 | [`d25-direct-lake-only-error.png`](d25-direct-lake-only-error.png) | DirectLakeOnly: the fallback becomes an error | The production setting |
| D25 | [`d25-scan-17ms.png`](d25-scan-17ms.png) | fact_orders: Scan, 17 ms | Direct Lake |
| D25 | [`d25-view-fallback-10057ms.png`](d25-view-fallback-10057ms.png) | v_delivered_orders: SQL, 10,057 ms — 9,329 ms opening the connection | Silent fallback |
| exam-4 | [`ex4-custom-pool-start-banner.png`](ex4-custom-pool-start-banner.png) | Custom Small pool: 'Session will start soon — 30 sec–5 min' *(redacted)* | Custom pools aren't pre-warmed |
| exam-4 | [`ex4-http-430.png`](ex4-http-430.png) | TooManyRequestsForCapacity — HTTP 430 | One session at a time |
| exam-4 | [`ex4-spark-jobs-8-of-8.png`](ex4-spark-jobs-8-of-8.png) | Spark Jobs: 8/8 cores used by one session | FTL4 = 8 Spark cores; one Medium node fills it |
| exam-5 | [`ex5-govern-tab.png`](ex5-govern-tab.png) | OneLake catalog Govern tab: 198 items, recommended actions | Purview hub → Govern tab |
| exam-5 | [`ex5-protect-77pct-unlabeled.png`](ex5-protect-77pct-unlabeled.png) | Protect report: 46 labeled, 152 (77%) unlabeled *(redacted)* | Label coverage |
| exam-5 | [`ex5-security-roles-defaultreader.png`](ex5-security-roles-defaultreader.png) | Every OneLake security role — DefaultReader on every lakehouse | Roles add up |
| exam-9 | [`ex9-m-delivery-bands.png`](ex9-m-delivery-bands.png) | M drill: 8 orders 'delivered' with no delivery date | A real data-quality find |
