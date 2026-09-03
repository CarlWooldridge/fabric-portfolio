> **This is the original build spec, and it has been superseded in places.**
>
> It was written before the project was built, and the build corrected it. Kept as-is
> because the corrections are the interesting part — but do not read it as documentation
> of the shipped system. Specifically:
>
> * The refresh mechanism here is a scheduled Dataflow refresh. A Power Automate trigger
>   (SharePoint *modified* → refresh dataflow) was built later and works; the guide predates it.
> * The write-back design here keeps write-back values in `Fact_JobPostings`. That design
>   caused a data-loss incident and was replaced by the append-only `Fact_WriteBack` table.
>   See [the post-mortem](writeback-incident-postmortem.html).
> * The User Data Function signature uses `snake_case` parameters. Fabric requires camelCase.
> * `Fact_ScoreComponents` was later given an explicit `CREATE TABLE` with a composite key
>   and renamed `Bridge_ScoreComponents`.
>
> The shipped state is in [`../dataflow/`](../dataflow/), [`../sql/`](../sql/) and
> [`../semantic-model/`](../semantic-model/).

---

# Building the JD Evaluation Log Power BI Report — Step by Step

## Architecture note (read first)

Direct Lake semantic models do **not** support Power Query transformations or
calculated columns. This means the M code for splitting `Comp_Posted`,
splitting `Location`, and parsing the score components out of `Notes` cannot
live inside Power BI Desktop's Power Query editor if the model stays in
Direct Lake mode. Instead, that logic runs **upstream** in a Fabric Dataflow
Gen2, which writes clean, already-transformed Delta tables into the
Lakehouse. Power BI then reads those tables directly — no further
transformation step, which is exactly what Direct Lake requires.

This adds a second freshness variable: the existing ~15 minute OneLake
shortcut cache (raw CSV → shortcut) plus whatever refresh cadence you set on
the Dataflow (shortcut output → clean Fact tables). Total time-to-report is
the sum of both, not just the first one.

**Update — write-back requirement.** To support write-back (recording
`Carls_Action`, `Carls_Action_Date`, `Outcome`, `Reason` directly from the
report via Translytical Task Flows), `Fact_JobPostings` moves from the
Lakehouse to a **Fabric SQL Database** instead — it's the only Fabric item
type a User Data Function can reliably target for row-level UPDATE
statements. `Fact_ScoreComponents` moves there too, for consistency — one
source item is simpler than a composite model spanning two.

Fabric SQL Database automatically mirrors its tables into OneLake in near
real-time, so the semantic model still reads via **Direct Lake**, same as
before — the Power Query/calculated-column restriction still applies, so the
Dataflow Gen2 transform layer from Phase 1 stays exactly as designed, just
pointed at a new destination.

---

## Phase 1 — Build the transformation layer (Dataflow Gen2)

1. In the `JobSearch_LH` workspace, select **New item → Dataflow Gen2**. Name
   it `JD_Transform`.
2. **Get data → OneLake catalog**, select `JobSearch_LH`, and choose the
   `JobPostings` table (the existing shortcut to the CSV) as the source.
3. Get the combined M code into the query — here's exactly where it goes:
   a. Fabric auto-generates a query named `JobPostings`, matching the
      source table, with one step already in it, typically named `Source`.
      **Don't delete or rewrite that step** — it holds the actual
      connection info to your Lakehouse shortcut, which you can't easily
      recreate by hand.
   b. With that query selected, go to **Home ribbon → Advanced Editor**.
      You'll see something like:
      ```m
      let
          Source = ... (your actual connector call, already filled in) ...
      in
          Source
      ```
   c. Replace the code between `let` and `in Source` — keep the `Source =`
      line exactly as generated, delete everything after it (including the
      trailing `in Source`), and paste in the block below instead. This
      chains every transformation off of `Source` and ends on the final
      step, `AddDeductions`.
   d. Click **Done**. **Rename the query** from `JobPostings` to
      `Fact_JobPostings` — right-click the query name in the Queries pane
      → Rename. This is a query rename inside the Dataflow only; it
      doesn't touch the actual `JobPostings` table name in the Lakehouse.
   e. **Before wiring the write-back-preserving logic below, first create a
      second, small query** that reads back the current state of the
      destination table:
      - **Get data → SQL Database** → connect to `JobSearch_DB` → select
        the `Fact_JobPostings` table.
      - In the query, keep only `Job_ID`, `Carls_Action`,
        `Carls_Action_Date`, `Outcome`, `Reason` — remove every other
        column (Home ribbon → Choose Columns).
      - Fabric will auto-name this query after the table it's reading
        (`Fact_JobPostings`, matching the SQL Database table it's pulling
        from — a different `Fact_JobPostings` than the Dataflow query from
        step 3d, just the same name because it's reading that same
        destination table). **Rename this query** to `Existing_WriteBack`
        so the two don't get confused with each other in the Queries pane.
        **Don't give it a data destination** — it's a helper query the
        main query reads from, not something that gets written anywhere
        itself.

      On the very first run, `Fact_JobPostings` is still the empty table
      you created with `CREATE TABLE`, so `Existing_WriteBack` returns zero
      rows — which is exactly right: nothing has a write-back yet, so
      everything falls back to the CSV, giving you the "populated from CSV
      initially" behavior.
   f. Now go back into `Fact_JobPostings`'s Advanced Editor and append the
      merge logic below, right after the `AddDeductions` step (replace the
      `in AddDeductions` line — the new final step is
      `SetWholeNumberTypes`):

      ```m
          // --- Preserve write-back values across refreshes ---
          // Carls_Action / Carls_Action_Date / Outcome / Reason exist both as
          // native CSV columns (your existing manual-override fields) and as
          // columns the write-back function updates directly in the SQL table.
          // On every refresh: if the SQL table already has a value, it was set
          // by an earlier CSV load or a report write-back — keep it. Only fall
          // back to the CSV's value when the SQL table has nothing yet. This is
          // what makes a report write-back survive the next Dataflow refresh.
          Merged = Table.NestedJoin(AddDeductions, {"Job_ID"}, Existing_WriteBack, {"Job_ID"}, "WB", JoinKind.LeftOuter),
          Expanded = Table.ExpandTableColumn(Merged, "WB",
              {"Carls_Action", "Carls_Action_Date", "Outcome", "Reason"},
              {"WB_Carls_Action", "WB_Carls_Action_Date", "WB_Outcome", "WB_Reason"}),

          ResolveText = (csvVal as nullable text, wbVal as nullable text) as nullable text =>
              if wbVal <> null and Text.Trim(wbVal) <> "" then wbVal else csvVal,
          ResolveDate = (csvVal as nullable date, wbVal as nullable date) as nullable date =>
              if wbVal <> null then wbVal else csvVal,

          FinalAction  = Table.AddColumn(Expanded,     "Final_Carls_Action",      each ResolveText([Carls_Action], [WB_Carls_Action]), type nullable text),
          FinalDate    = Table.AddColumn(FinalAction,  "Final_Carls_Action_Date", each ResolveDate([Carls_Action_Date], [WB_Carls_Action_Date]), type nullable date),
          FinalOutcome = Table.AddColumn(FinalDate,    "Final_Outcome",           each ResolveText([Outcome], [WB_Outcome]), type nullable text),
          FinalReason  = Table.AddColumn(FinalOutcome, "Final_Reason",            each ResolveText([Reason], [WB_Reason]), type nullable text),

          RemoveOldWB = Table.RemoveColumns(FinalReason,
              {"Carls_Action", "Carls_Action_Date", "Outcome", "Reason",
               "WB_Carls_Action", "WB_Carls_Action_Date", "WB_Outcome", "WB_Reason"}),
          RenameFinal = Table.RenameColumns(RemoveOldWB, {
              {"Final_Carls_Action", "Carls_Action"},
              {"Final_Carls_Action_Date", "Carls_Action_Date"},
              {"Final_Outcome", "Outcome"},
              {"Final_Reason", "Reason"}
          }),

          // The CREATE TABLE statement declares these as SQL INT ("Whole number"
          // in the destination UI), but ExtractComponentFn and the applicant-volume
          // parsing above both produce Power Query's generic "Decimal Number" type.
          // Without this explicit cast, the destination mapping screen won't
          // auto-match them by name — it'll show "(none)" even though the column
          // names line up exactly, since it won't assume a decimal→integer
          // narrowing is safe on its own.
          SetWholeNumberTypes = Table.TransformColumnTypes(RenameFinal, {
              {"Pts_Lane", Int64.Type}, {"Pts_Scope", Int64.Type}, {"Pts_Comp", Int64.Type},
              {"Pts_Location", Int64.Type}, {"Pts_Skills", Int64.Type}, {"Pts_Perks", Int64.Type},
              {"Pts_Applicants", Int64.Type}, {"Pts_Deductions", Int64.Type},
              {"Applicant_Volume_Num", Int64.Type}
          })
      in
          SetWholeNumberTypes
      ```

      **Known limitation, worth knowing rather than discovering later:**
      this logic means once a write-back happens for a job, editing that
      job's `Carls_Action` in the CSV again afterward has no effect on
      refresh — the SQL value always wins once populated. If you ever want
      a manual CSV correction to be able to override a stale report
      write-back, that needs a recency comparison using
      `Carls_Action_Date` on both sides instead of a simple
      populated-or-not check — a reasonable enhancement, but not something
      to build until you actually hit that situation.

   ```m
   let
       Source = ... (leave your generated Source step here, unchanged) ...,

       // --- Applicant volume: "26 applicants" / "Over 100 applicants" -> numeric
       CleanApplicants = Table.AddColumn(Source, "Applicant_Volume_Num", each
           let
               raw = [Applicant_Volume],
               isOver100 = raw <> null and Text.Contains(raw, "Over 100"),
               leadingDigits = if raw = null then null else Text.BeforeDelimiter(Text.Trim(raw) & " ", " "),
               parsed = try Number.FromText(leadingDigits) otherwise null
           in
               if raw = null then null
               else if isOver100 then 100
               else parsed
       , type nullable number),

       // --- Comp_Posted split: "$127,700.00 - $185,150.00" -> Comp_Min / Comp_Max / Comp_Mid
       SplitComp = Table.SplitColumn(CleanApplicants, "Comp_Posted",
           Splitter.SplitTextByDelimiter(" - ", QuoteStyle.None),
           {"Comp_Min_Text", "Comp_Max_Text"}),

       CleanNumberFn = (txt as nullable text) as nullable number =>
           let
               cleaned = if txt = null or Text.Trim(txt) = "" then null
                         else Text.Remove(Text.Trim(txt), {"$", ","}),
               result = try Number.FromText(cleaned) otherwise null
           in result,

       AddCompMin = Table.AddColumn(SplitComp, "Comp_Min", each CleanNumberFn([Comp_Min_Text]), type nullable number),
       AddCompMax = Table.AddColumn(AddCompMin, "Comp_Max", each
           let m = CleanNumberFn([Comp_Max_Text]) in if m = null then [Comp_Min] else m
       , type nullable number),
       AddCompMid = Table.AddColumn(AddCompMax, "Comp_Mid", each
           if [Comp_Min] = null then null else ([Comp_Min] + [Comp_Max]) / 2
       , type nullable number),
       RemoveCompHelpers = Table.RemoveColumns(AddCompMid, {"Comp_Min_Text", "Comp_Max_Text"}),

       // --- Location split: "Nashville, TN" / "United States" / "Nashville, TN (multi-city)"
       StripParen = Table.AddColumn(RemoveCompHelpers, "Location_Clean", each
           Text.Trim(Text.BeforeDelimiter([Location], "(")), type text),
       AddCity = Table.AddColumn(StripParen, "Location_City", each
           if Text.Contains([Location_Clean], ",") then Text.Trim(Text.BeforeDelimiter([Location_Clean], ","))
           else null
       , type nullable text),
       AddState = Table.AddColumn(AddCity, "Location_State", each
           if Text.Contains([Location_Clean], ",") then Text.Trim(Text.AfterDelimiter([Location_Clean], ","))
           else Text.Trim([Location_Clean])
       , type nullable text),
       RemoveLocationHelper = Table.RemoveColumns(AddState, {"Location_Clean"}),

       // --- Notes parsing: pull the "Score X = Lane ... + Scope ... " formula clause out,
       // then extract each named component's point value from within it.
       // Prefixed Pts_ rather than Comp_ deliberately, so these rubric-point columns
       // aren't confused with the dollar-value Comp_Min/Comp_Max/Comp_Mid above.
       ExtractFormulaFn = (notes as nullable text) as nullable text =>
           let
               idx = if notes = null then null else Text.PositionOf(notes, "= Lane"),
               after = if idx = null or idx = -1 then null else Text.Range(notes, idx + 2),
               endPos = if after = null then null else Text.PositionOf(after, ". "),
               formula = if after = null then null
                         else if endPos = null or endPos = -1 then after
                         else Text.Range(after, 0, endPos)
           in formula,

       ExtractComponentFn = (formula as nullable text, label as text) as nullable number =>
           let
               searchFor = label & " ",
               hasLabel = formula <> null and Text.Contains(formula, searchFor),
               afterLabel = if hasLabel then Text.AfterDelimiter(formula, searchFor) else null,
               digitsOnly = if afterLabel <> null then Text.BeforeDelimiter(afterLabel & " ", " ") else null,
               numeric = try Number.FromText(digitsOnly) otherwise null
           in if hasLabel then numeric else null,

       AddFormula      = Table.AddColumn(RemoveLocationHelper, "ScoreFormula", each ExtractFormulaFn([Notes]), type nullable text),
       AddLane         = Table.AddColumn(AddFormula,  "Pts_Lane",       each ExtractComponentFn([ScoreFormula], "Lane"),       type nullable number),
       AddScope        = Table.AddColumn(AddLane,     "Pts_Scope",      each ExtractComponentFn([ScoreFormula], "Scope"),      type nullable number),
       AddCompPts      = Table.AddColumn(AddScope,    "Pts_Comp",       each ExtractComponentFn([ScoreFormula], "Comp"),       type nullable number),
       AddLocPts       = Table.AddColumn(AddCompPts,  "Pts_Location",   each ExtractComponentFn([ScoreFormula], "Location"),   type nullable number),
       AddSkills       = Table.AddColumn(AddLocPts,   "Pts_Skills",     each ExtractComponentFn([ScoreFormula], "Skills"),     type nullable number),
       AddPerks        = Table.AddColumn(AddSkills,   "Pts_Perks",      each ExtractComponentFn([ScoreFormula], "Perks"),      type nullable number),
       AddApplicantPts = Table.AddColumn(AddPerks,    "Pts_Applicants", each ExtractComponentFn([ScoreFormula], "Applicants"), type nullable number),

       AddIsCapped = Table.AddColumn(AddApplicantPts, "Is_Capped_Score", each
           [Notes] <> null and Text.Contains([Notes], "capped from")
       , type logical),

       // Deductions computed only for non-capped rows — see the earlier validation
       // against your real data: 26% of rows have "capped from" text whose arithmetic
       // doesn't reconcile against the visible components, so forcing a deduction
       // value there would be misleading rather than informative.
       AddDeductions = Table.AddColumn(AddIsCapped, "Pts_Deductions", each
           let
               namedSum = List.Sum({[Pts_Lane],[Pts_Scope],[Pts_Comp],[Pts_Location],[Pts_Skills],[Pts_Perks],[Pts_Applicants]})
           in
               if [Is_Capped_Score] or namedSum = null or [Score] = null then null
               else [Score] - namedSum
       , type nullable number)
   in
       AddDeductions
   ```
4. Before setting the destination, first create the target: **New item →
   SQL Database**, name it `JobSearch_DB`. Open it, and under its query
   editor run:
   ```sql
   CREATE TABLE Fact_JobPostings (
       Job_ID BIGINT PRIMARY KEY,
       Date_Evaluated DATE,
       Company NVARCHAR(200),
       Role_Title NVARCHAR(300),
       Location NVARCHAR(200),
       Location_City NVARCHAR(100),
       Location_State NVARCHAR(100),
       Work_Type NVARCHAR(300),
       Employment_Type NVARCHAR(200),
       Comp_Min FLOAT, Comp_Max FLOAT, Comp_Mid FLOAT,
       Applicant_Volume NVARCHAR(100),
       Applicant_Volume_Num INT,
       Source NVARCHAR(100), URL NVARCHAR(1000),
       Verdict NVARCHAR(50), Score INT, Role_Type NVARCHAR(150),
       Comp_Flag NVARCHAR(300), Biggest_Gap NVARCHAR(MAX),
       Biggest_Strength NVARCHAR(MAX), Recommended_Action NVARCHAR(MAX),
       Carls_Action NVARCHAR(50), Carls_Action_Date DATE,
       Outcome NVARCHAR(100), Reason NVARCHAR(500), Notes NVARCHAR(MAX),
       ScoreFormula NVARCHAR(MAX),
       Pts_Lane INT, Pts_Scope INT, Pts_Comp INT, Pts_Location INT,
       Pts_Skills INT, Pts_Perks INT, Pts_Applicants INT, Pts_Deductions INT,
       Is_Capped_Score BIT
   );
   ```

   These sizes are checked against actual max lengths in your real CSV
   (not guessed) — `Work_Type` in particular needs real headroom, since
   values like "Remote-first (confirmed on both LinkedIn and company
   career-site postings)" run to 150 characters. If you're building this
   guide against a CSV that's grown substantially since, it's worth
   re-checking max lengths per column rather than trusting these numbers
   blindly — same mistake, same fix, just repeated later.
   The `PRIMARY KEY` on `Job_ID` isn't strictly required by the UDF's SQL
   (a plain `UPDATE ... WHERE Job_ID = ?` works without one), but it's what
   makes this table a proper writable target rather than an append-only
   log, and it's the step Lakehouse tables can't satisfy at all — worth
   keeping as correct relational design regardless.

   Back in the Dataflow, with `Fact_JobPostings` selected, open **Data
   destination** → choose **SQL Database** → `JobSearch_DB` → **Use
   existing table** → select `Fact_JobPostings` (not "Create new table" —
   this must be the table you already built with the SQL above) → map
   **all** columns, including `Carls_Action`, `Carls_Action_Date`,
   `Outcome`, and `Reason` → **Update method: Replace**. Unlike the earlier
   version of this step, you no longer need to exclude those four columns
   — the merge logic added in step 3f already resolves the correct value
   for each of them before the query ever reaches this destination, so a
   full Replace is safe.
5. **Right-click `Fact_JobPostings` → Reference** to create a second query
   from the same cleaned output (don't reference the raw shortcut again —
   reference the already-cleaned query so you're not re-parsing).
6. On the referenced query, select all **eight** `Pts_*` score-component
   columns (`Pts_Lane`, `Pts_Scope`, `Pts_Comp`, `Pts_Location`,
   `Pts_Skills`, `Pts_Perks`, `Pts_Applicants`, `Pts_Deductions`) — hold
   Ctrl to multi-select — then **Transform ribbon → Unpivot Columns →
   Unpivot Only Selected Columns**. Rename the resulting columns
   `Attribute` → `Component`, `Value` → `Points`. Remove all other columns
   except `Job_ID`, `Component`, `Points`.

   Then add one more step: filter out rows where `Points` is null (Home
   ribbon → Remove Rows → Remove Empty, or a filter on the `Points`
   column). This matters specifically for `Pts_Deductions` — recall it's
   deliberately left null on capped-score rows, since the arithmetic
   doesn't reconcile there. Without this filter, the unpivot produces a
   `Pts_Deductions` row with a blank `Points` value for every capped row,
   which is meaningless noise in the destination table rather than a real
   data point.
7. **Rename this query** from `Fact_JobPostings (2)` (or similar — whatever
   Fabric auto-labels the reference) to `Fact_ScoreComponents`. Set its
   data destination the same way: **SQL Database** `JobSearch_DB`, new
   table `Fact_ScoreComponents`, Replace. (This table doesn't need a
   primary key — the write-back function never touches it.)
8. **Enable staging** on the two queries that get referenced by another
   query — right-click `Fact_JobPostings` → **Enable staging**, and
   right-click `Existing_WriteBack` → **Enable staging**. Leave
   `Fact_ScoreComponents` unstaged, since nothing reads from it.

   This isn't about performance at your data volume (a few hundred rows
   either way is negligible) — it's about correctness. `Fact_JobPostings`
   reads `Existing_WriteBack` in its merge step, and `Fact_ScoreComponents`
   reads `Fact_JobPostings` in its unpivot step. Staging is what lets each
   referencing query work off a consistent, already-computed snapshot from
   *this* run, rather than either recomputing the whole upstream chain
   (redoing the Notes-parsing work twice) or reading stale data left over
   from the previous run. Expect a hidden internal item like
   `DataflowStagingLakehouse` to appear in the workspace once you do this —
   that's normal Fabric-managed plumbing, not something to clean up.
9. **Save & Run** the Dataflow (the button set is "Save," "Save & Close,"
   "Save & Run," and "Close" — there's no separate "Publish" button since
   every new Dataflow Gen2 now ships CI/CD-enabled). Save & Run is the one
   you want here specifically: it both saves your query edits and
   immediately executes them, which is what actually populates
   `Fact_JobPostings` and `Fact_ScoreComponents` in `JobSearch_DB` for the
   first time — Phase 2 needs real data sitting in those tables to connect
   to.
10. Set the Dataflow's refresh schedule: open `JD_Transform`'s settings →
    **Refresh → Scheduled refresh** → enable it, and set an interval of
    every 15–30 minutes.

    **Why not Data Activator, after all the earlier discussion of it:**
    Activator cannot directly monitor a Lakehouse table at all, batch or
    shortcut-sourced — it only accepts event-based sources (Eventstreams,
    Real-Time Hub sources, Power BI visuals, KQL Querysets). The only
    documented way to get Activator involved with a batch-loaded Lakehouse
    table is to stand up a KQL Queryset that compares each load against the
    previous one and feed *that* into Activator — provisioning a whole
    Eventhouse/KQL Database just to detect "did this table change." That's
    a disproportionate amount of infrastructure for a job log that updates
    a handful of times a day, so a plain schedule is the right call here,
    not a fallback settled for after the event-driven path didn't pan out.

    Combined with the ~15-minute OneLake shortcut caching delay from
    earlier, expect total freshness (CSV edit → visible in the report)
    somewhere in the 15–45 minute range depending on refresh timing — worth
    setting expectations at that level rather than assuming anything closer
    to real-time.

---

## Phase 2 — Build the semantic model

1. **Don't start with "New item → Semantic model" and a generic "Get
   data"** — that routes through the same external-connector gallery used
   for MySQL, on-prem SQL Server, etc., and a Fabric SQL Database in your
   own tenant won't show up there at all. Instead, click **Create** in the
   left nav → select **OneLake catalog**.
2. Find `JobSearch_DB` in the list (it appears there as a Fabric item with
   Delta tables, thanks to its automatic OneLake mirroring) → **Connect**.
   Name the semantic model `JobSearch Model`, pick the `JobSearch_LH`
   workspace, and select `Fact_JobPostings` and `Fact_ScoreComponents` from
   the table list → **OK**. This opens web modeling directly in the
   browser with both tables already wired in as Direct Lake — no
   connection string or credentials involved.
3. Open the model in **web modeling** (or Power BI Desktop, live-connected —
   see Phase 3) and create the relationship: `Fact_JobPostings[Job_ID]`
   (one) → `Fact_ScoreComponents[Job_ID]` (many).
4. Add a date dimension as a **DAX calculated table** (this is allowed even
   in Direct Lake, as long as it doesn't reference a Direct Lake column
   directly):

   ```dax
   Dim_Date =
   ADDCOLUMNS(
       CALENDAR(DATE(2026,1,1), DATE(2027,12,31)),
       "Year", YEAR([Date]),
       "MonthName", FORMAT([Date], "MMM"),
       "MonthNum", MONTH([Date]),
       "WeekStart", [Date] - WEEKDAY([Date], 2) + 1
   )
   ```

   Use a self-contained static range like this rather than deriving it from
   `MIN`/`MAX` of the fact table's dates — pulling values from a Direct Lake
   table into a calculated table's definition risks tripping the "no
   calculated table referencing Direct Lake columns" restriction.

5. Mark `Dim_Date[Date]` as a **Date Table** (Table tools ribbon → Mark as
   date table).
6. Create relationships: `Dim_Date[Date]` → `Fact_JobPostings[Date_Evaluated]`
   (active), and `Dim_Date[Date]` → `Fact_JobPostings[Carls_Action_Date]`
   (this second one will default to inactive since a date can only have one
   active relationship — leave it inactive, and use `USERELATIONSHIP` in any
   measure that needs to filter by action date instead of evaluation date).
7. Add these DAX measures via **New measure** in web modeling or Desktop:

   ```dax
   Total Evaluated = COUNTROWS(Fact_JobPostings)

   Pursue Count = CALCULATE([Total Evaluated], Fact_JobPostings[Verdict] = "Pursue")

   Pursue Rate = DIVIDE([Pursue Count], [Total Evaluated])

   Avg Score = AVERAGE(Fact_JobPostings[Score])

   Avg Comp Mid = AVERAGE(Fact_JobPostings[Comp_Mid])

   Active Applications =
   CALCULATE(
       [Total Evaluated],
       Fact_JobPostings[Carls_Action] <> BLANK(),
       Fact_JobPostings[Outcome] = BLANK()
   )

   Postings This Week =
   VAR ThisWeekStart = TODAY() - WEEKDAY(TODAY(), 2) + 1
   RETURN
   CALCULATE(
       [Total Evaluated],
       Fact_JobPostings[Date_Evaluated] >= ThisWeekStart,
       Fact_JobPostings[Date_Evaluated] <= TODAY()
   )

   Days to Action =
   AVERAGEX(
       FILTER(Fact_JobPostings, NOT ISBLANK(Fact_JobPostings[Carls_Action_Date])),
       DATEDIFF(Fact_JobPostings[Date_Evaluated], Fact_JobPostings[Carls_Action_Date], DAY)
   )

   Avg Component Points = AVERAGE(Fact_ScoreComponents[Points])
   ```

   `Postings This Week` uses a Monday-start calendar week (`WEEKDAY(TODAY(), 2)`
   returns 1 for Monday), matching the same convention as `Dim_Date[WeekStart]`
   from step 4 — so the Command Center's weekly trend chart and this KPI card
   agree on where a week begins and ends, rather than using two different
   definitions of "week" on the same page.

---

## Phase 3 — Build the report in Power BI Desktop

1. Open Power BI Desktop → **Get Data → Power BI semantic models** → select
   `JobSearch Model` → **Connect** (this is a live connection; the report
   file itself stores no data, matching Direct Lake behavior).
2. At the bottom, right-click the default page tab → rename it
   `Command Center`. Add five more pages (right-click → New page) and name
   them: `All Jobs`, `Action Queue`, `Score Breakdown`,
   `Pipeline & Outcomes`, `Job Detail`.
3. **Command Center:**
   - Insert 5 **Card** visuals bound to `[Total Evaluated]`, `[Pursue Rate]`,
     `[Avg Score]`, `[Active Applications]`, and `[Postings This Week]`.
   - Insert a **Stacked Area Chart**: Axis = `Dim_Date[WeekStart]`, Legend =
     `Fact_JobPostings[Verdict]`, Values = `[Total Evaluated]`.
   - Insert a **Donut Chart**: Legend = `Verdict`, Values = `[Total
     Evaluated]`.
   - Insert a **Clustered Bar Chart**: Axis = `Reason`, Values = `[Total
     Evaluated]`; apply a **Top N filter** (top 10) on the visual.
4. **All Jobs:**
   - Insert **Slicers** for `Verdict`, `Role_Type`, `Work_Type`,
     `Location_State`, `Score` (as a range slicer), and `Date_Evaluated`.
   - Insert a **Table** visual with `Company`, `Role_Title`, `Location`,
     `Verdict`, `Score`, `Comp_Min`/`Comp_Max`, `Date_Evaluated`.
5. **Action Queue:**
   - Table 1: filter pane → `Verdict = Pursue` AND `Carls_Action is blank`.
     Columns: `Company`, `Role_Title`, `Score`, `Comp_Mid`,
     `Date_Evaluated`, `Biggest_Strength`.
   - Table 2: filter pane → `Verdict = Skip` AND relative date filter
     (`Date_Evaluated` is in the last 14 days). Columns: `Company`,
     `Role_Title`, `Score`, `Reason`, `Biggest_Gap`.
   - On Table 2, select the `Score` column → **Format → Conditional
     formatting → Background color → Rules**: highlight where value is
     between 50 and 69.
6. **Score Breakdown:**
   - Insert a **Waterfall Chart**: Category = `Fact_ScoreComponents[Component]`,
     Y-axis = average of `Fact_ScoreComponents[Points]`.
   - Insert a **Scatter Chart**: X = `Applicant_Volume_Num` (parsed to
     numeric already, back in Phase 1's Dataflow), Y = `Score`, Legend =
     `Verdict`.
   - Insert small-multiple bar charts of component values split by
     `Verdict`, using the **Small multiples** well in the visual formatting
     pane.
   - Add a **Text box**: "Deductions shown only for non-capped rows —
     capped-score rows display named components without a forced
     reconciliation."
7. **Pipeline & Outcomes:**
   - Insert a **Funnel Chart**: stages = a calculated column or measure
     representing Evaluated → Pursue → Applied → Interview/Offer counts.
   - Insert a **Table** of active applications.
   - Insert a **Histogram** (Clustered column with binned `[Days to
     Action]`).
8. **Job Detail:**
   - Insert **Card** visuals for `Company`, `Role_Title`, `Verdict`, `Score`,
     `Location`, `Applicant_Volume`.
   - Copy the waterfall visual from Score Breakdown (Ctrl+C / Ctrl+V) — it
     will now show only the selected job once drillthrough filtering is
     applied.
   - Add a **Card** or **Text box** bound to `Notes`.
   - Right-click the `Job Detail` tab → **Hide page**.

---

## Phase 4 — Drillthrough

1. On the `Job Detail` page, drag `Job_ID` into the **Drill through** field
   well in the Visualizations pane. This automatically adds a Back button
   to the page.
2. No source-side configuration is needed — once `Job Detail` has `Job_ID`
   in its drillthrough well, right-clicking any data point tied to a
   `Job_ID` on `All Jobs`, `Action Queue`, or `Score Breakdown` will show
   **Drillthrough → Job Detail** in the context menu automatically.

---

## Phase 5 — Page Navigator

1. On `Command Center`: **Insert ribbon → Buttons → Navigator → Page
   navigator**. It auto-populates with all currently visible pages.
2. Position it at the top of the page and format it (Format pane → adjust
   fill, current-page style, font) to match your intended look.
3. Copy this visual (Ctrl+C) and paste it (Ctrl+V) onto `All Jobs`,
   `Action Queue`, `Score Breakdown`, and `Pipeline & Outcomes`. Do **not**
   paste it onto `Job Detail` — it's hidden, and Page Navigator excludes
   hidden pages from its list by default anyway.
4. Remember: this is a copy-paste, not a shared component. If you add,
   remove, or reorder pages later, re-sync the navigator on every page.

---

## Phase 6 — Publish

1. **File → Publish → Publish to Power BI** → select the `JobSearch_LH`
   workspace.
2. Confirm the report now appears in that workspace alongside the
   `JobSearch Model` semantic model and the `JobSearch_DB` SQL database.

---

## Phase 7 — Build the User Data Function

1. In Power BI Desktop, enable the preview features this needs: **File →
   Options and settings → Options → Preview features** → check
   **Translytical task flows** and **New slicer visuals (text, list,
   button)**. Restart Desktop.
2. In the `JobSearch_LH` workspace, select **New item → User data
   function**. Name it `JD_ActionWriteback`.
3. In the function editor, add a connection: **Manage connections → Add
   data source** → select `JobSearch_DB`. This creates an alias (e.g.
   `jobsearch_db`) you'll reference in code.
4. Write the function. This is real Python — a genuine skill data point,
   not low-code:

   ```python
   import fabric.functions as fn

   udf = fn.UserDataFunctions()

   @udf.connection(argName="db", alias="jobsearch_db")
   @udf.function()
   def update_job_action(
       db: fn.FabricSqlConnection,
       job_id: int,
       carls_action: str,
       outcome: str,
       reason: str
   ) -> str:
       # Input validation — required practice per Company-423's TTF guidance,
       # and it's what makes failures show up as a clean message on the
       # report instead of a silent no-op or a raw stack trace.
       valid_actions = {"Applied", "Referral Requested", "Withdrawn", "None"}
       if carls_action not in valid_actions:
           raise fn.UserThrownError(f"'{carls_action}' isn't a recognized action.")

       try:
           conn = db.connect()
           cursor = conn.cursor()
           cursor.execute(
               """
               UPDATE Fact_JobPostings
               SET Carls_Action = ?, Carls_Action_Date = CAST(GETDATE() AS DATE),
                   Outcome = ?, Reason = ?
               WHERE Job_ID = ?
               """,
               (carls_action, outcome, reason, job_id)
           )
           conn.commit()
       except Exception as e:
           raise fn.UserThrownError(f"Write failed: {str(e)}")

       return f"Saved: {carls_action} recorded for Job_ID {job_id}."
   ```

   Note the parameterized query (`?` placeholders, not string-formatted SQL)
   — this is the SQL-injection safeguard Company-423's own TTF guidance calls
   out explicitly, and it matters here since a text-input field (`Reason`)
   is user-typed.

   Also note: `Carls_Action_Date` is set automatically to today's date
   server-side (`GETDATE()`) rather than taken as a user input. Date
   slicers aren't currently one of the supported TTF input types (only
   button, list, and text slicers are) — this sidesteps that gap rather
   than fighting it, and "today" is the correct value in practice anyway,
   since you're always logging the action as it happens.

5. **Publish** the function.

---

## Phase 8 — Wire the write-back controls into the Action Queue page

1. Back in Power BI Desktop, on the **Action Queue** page, add three input
   controls near the "Jobs to Pursue" table:
   - A **List Slicer**, bound to a small local table of the four
     `Carls_Action` options (Applied, Referral Requested, Withdrawn, None)
     — easiest built via **Enter data** (Home ribbon) rather than pulling
     from the fact table.
   - A second **List Slicer** for `Outcome` options (Interview, Rejected,
     No Response, Offer), built the same way.
   - A **Text Slicer** for `Reason` — add it with no fields in its Data
     well, since it's an input, not a filter.
2. For each of the three slicers: **Format pane → Edit interactions**, and
   set them to **None** against every other visual on the page. Without
   this, selecting "Applied" would filter your Jobs-to-Pursue table down to
   only previously-Applied rows instead of just capturing your input —
   the same fix the earlier community write-ups flag as the most common
   first mistake with these.
3. Add a **Button** visual, label it "Save Action". In the Format pane:
   **Action → Type: Data function button** → select `JD_ActionWriteback`.
4. Map the function's parameters to report elements:
   - `job_id` → a measure: `SelectedJobID = SELECTEDVALUE(Fact_JobPostings[Job_ID])`.
     This resolves correctly once exactly one row is selected in the "Jobs
     to Pursue" table — clicking a row is what sets the selection context.
   - `carls_action` → the first List Slicer.
   - `outcome` → the second List Slicer.
   - `reason` → the Text Slicer.
5. Test: click a row in "Jobs to Pursue", pick values in the two list
   slicers, type a reason, click **Save Action**. Power BI shows the
   function's returned string (your `"Saved: ..."` message, or the
   validation error if something's wrong) inline near the button, and
   report visuals refresh automatically to reflect the write — no manual
   refresh call needed, unlike the Power Apps path.

No separate licensing step here — the SQL Server premium-connector question
from the Power Apps discussion doesn't apply at all, since there's no
Power Apps or Power Platform connector involved. Everything runs on your
existing Fabric trial.
