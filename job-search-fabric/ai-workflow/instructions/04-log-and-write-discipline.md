# The log, the write rules, and the Fabric contract

*Part of the JobSearch workflow. Start at [`COWORK_INSTRUCTIONS.md`](../COWORK_INSTRUCTIONS.md) — it holds the naming convention, the run-type map, and the rules that apply everywhere.*

**When to load this file:** Load for any run that WRITES to `JD_Evaluation_Log.csv`. Most of it is enforced by `scripts/jd-append.py` and `scripts/jd-update.py`.

---

## Row format

Append to `JD_Evaluation_Log.csv` using these columns exactly:

`Job_ID, Date_Evaluated, Company, Role_Title, Location, Work_Type, Employment_Type,
Comp_Posted, Applicant_Volume, Source, URL, Verdict, Score, Role_Type, Comp_Flag, Biggest_Gap,
Biggest_Strength, Recommended_Action, Carls_Action, Carls_Action_Date, Outcome, Reason,
Notes, Score_Raw`

**24 columns as of 2026-08-26** (was 23; `Score_Raw` was appended last — see below).

The header in the file is `Reason` — not `Likely_Reason`. Use the file's spelling.

- `Verdict` — **controlled vocabulary; this list is the single authoritative copy.** Set from the
  `Score` thresholds in `instructions/03-scoring-rubric.md` unless a gate fires. A veto-class gate
  sets `Pass` regardless of score (see "Hard override triggers"); a compensable gate sets `Review`
  (see "`Review` — the fourth verdict").

  | value | when |
  |---|---|
  | `Pursue` | score ≥ 70, no gate fired |
  | `Skip` | score < 70, no gate fired |
  | `Pass` | a veto-class gate fired |
  | `Review` | a compensable gate fired and no veto did |
  | `Unretrieved - needs manual pull` | the JD could not be fetched after five attempts, so the row was never scored (`01-intake-and-fetch.md`, "If Tier 1 fails"). Judgment fields stay blank. |
  | `Not evaluated` | a row that entered the log without going through the rubric — historical backfills only. **Do not write this on a live run.** |

  There is no "Pursue via referral only" value — see "Verdict thresholds" in
  `instructions/03-scoring-rubric.md` for where the referral recommendation belongs.
  (`Unretrieved` and `Not evaluated` added to this list 2026-08-31: both were in live use — 3 and
  10 rows — with `Unretrieved` defined only in `01` and `Not evaluated` documented nowhere at all.)

  **The stored value records what the rules said when the row was evaluated, and is never
  rewritten when a rule later changes.** (Standing rule, Carl 2026-08-31.) **Measurement uses
  current rules**: any analysis asking "is this a veto row or a Review row" must re-derive the
  answer from the row's `Reason` against the classes currently in `rubric/weights.json`, not read
  this column. `current_verdict_class()` in `rubric-learn.py` is that derivation — use it rather
  than writing a second one. 13 rows stored as `Pass` are `Review` under today's classes (G1's
  demotion and the G3 split, 2026-08-26); each was correct when written, and re-deriving is a
  reading, not a correction.
  - **`Pass` is never used to record that a posting closed.** A closed posting is recorded by the
    Step 3 closed-posting check (`Carls_Action = None`), not by the verdict — availability is not
    a preference. (Added 2026-08-26: ~22 historical rows carry `Reason` values like "No longer
    accepting applications" in the `Pass` class. Leave them alone — `Verdict` is a never-touch
    field — but don't add more, and exclude them from any rubric-learning training set.)
- `Score` — integer 0–100 from the Scoring rubric, **after** any cap or floor is applied. Show
  your component math in `Notes` (e.g. `Score 80 = Lane 25 + Scope 15 + Comp 20 + Location 12 +
  Skills 13 + Applicants 3 - true-gap 5 - domain 3`) so the number is auditable, not a guess.
- `Score_Raw` — integer 0–100: the same rubric total **before** the Lane-fit hard cap, the
  Location hard gate cap, and the Employer/Industry exclusion caps are applied. (Added 2026-08-26,
  column 24.) When nothing capped the row, `Score_Raw` equals `Score` — write it anyway, every
  time. When something capped it, `Score_Raw > Score`, and the gap is how much the cap removed.
  - **Populate it on every new evaluation.** It is not optional and not conditional on a cap
    having fired.
  - **It is blank on all 894 rows evaluated before 2026-08-26**, and that is deliberate. The
    uncapped score is not recoverable for those rows — of the 236 that scored exactly 35, only
    2 carry component math in `Notes`. Blank means "not recorded at the time"; do not backfill
    it by re-deriving a score from a title.
  - **Why it exists.** The caps flatten every out-of-lane posting to ~35, so 236 rows share one
    score and cannot be ranked against each other — and 30 of Carl's applications are inside that
    pile. `Score_Raw` makes the capped population rankable, and lets a `Review` rule key on "high
    raw score killed by a gate," which is the real pattern. It also makes a separate
    `Is_Capped` flag unnecessary: `Score_Raw > Score` says it.
- `Role_Type` — **controlled vocabulary; exactly three values, no qualifiers, no free text.**
  They mark the Lane score and **nothing else**:

  | value | Lane |
  |---|---|
  | `Lane-advancing` | 25 |
  | `Bridge` | 12 |
  | `Out of lane` | 0 |

  **Tightened 2026-08-31, and this one has already cost a real measurement.** The field was
  documented as three values but never declared controlled, and **18 distinct values are in the
  log** — 32 rows carrying variants like `Bridge (paycheck + currency, not a lane move)`,
  `Out of lane (retrospective)`, `Lane-advancing on scope, blocked on stack + location`,
  `Lane-adjacent`, `Partial fit, lost on domain` and `Not aligned`. Four of those map to no Lane
  score at all. `recall-audit.py` carries a standing warning about it: selecting Bridge candidates
  by *"whose `Role_Type` contains the word bridge"* reads **251 rows instead of 25**.

  **Put the qualifier in `Notes`, never in the value.** The reasoning is welcome — the field is
  not where it goes. Anything a variant was trying to say (`blocked on location`, `retrospective`,
  `paycheck + currency`) belongs in `Notes` beside the component math.

  **The 32 legacy rows are not rewritten** — same standing rule as `Verdict` and `Comp_Flag`
  above: each was written in good faith and a rewrite would erase what the evaluator concluded.
  Read them for what they are; write only the three values from here on.

  ⚠️ **`Bridge` no longer tells you whether the cap applied.** Since the Lane-12 cap became
  conditional on the handoff test (2026-08-31), `Bridge` covers both a role capped at 69 and one
  whose cap was lifted. **Read `Notes` for the cap decision**, which `03-scoring-rubric.md`
  requires to be stated there either way.
- `Comp_Flag` — **controlled vocabulary; this list is the single authoritative copy.** (Collapsed
  here 2026-08-31 — it had been restated in three files, which is how the 2026-08-26 drift went
  unnoticed. `01-intake-and-fetch.md` says *when* to recompute it and `03-scoring-rubric.md` says
  what each band *scores*; neither restates the tokens. **If this vocabulary changes, it changes
  here, and nowhere else.**) Use exactly one token; do not invent variants. (Tightened 2026-08-27
  — a run wrote `Unlisted - not researched` on a row whose own `Notes` said steps 1–2 had been run
  and found nothing. The label contradicted the reasoning beside it.)

  | token — write it exactly | means |
  |---|---|
  | `None (>=TARGET)` | top of range ≥ TARGET (clears target) |
  | `Sub-target (FLOOR-175K)` | top of range FLOOR–TARGET |
  | `Below floor (VETO_LINE-150K)` | top of range VETO_LINE–FLOOR — the `Review` band |
  | `Below veto line (<VETO_LINE)` | top of range < VETO_LINE |
  | `Unlisted - researched $X-$Y` | no posted figure, but a credible figure was found |
  | `Unlisted - none in pill or body` | steps 1–2 of the comp lookup ran and found nothing. **The only correct "unlisted" label on a normal evaluation run.** |
  | `Unlisted - step 3 not run` | steps 1–2 found nothing **and** the external Apply-link lookup was deliberately skipped (it is discretionary; see the comp retrieval protocol). Never use this to mean "I didn't look." |

  Free text may follow the token and is often useful — `Below veto line (<VETO_LINE) - tops out at
  $121,400`. The token comes first and is never abbreviated.

  **Never write `not researched` on its own.** It does not distinguish *looked and found nothing*
  from *did not look*, which are different facts with different follow-ups.

  > ### ⚠️ This vocabulary changed meaning on 2026-08-26. Read older rows under their own era.
  >
  > The comp floor was raised from VETO_LINE to FLOOR that day. The band *names* did not change, so
  > **both `Below floor` and `Sub-target` shifted by exactly one band**, and nothing on a row
  > records which scheme it was written under:
  >
  > | string | evaluated before 2026-08-26 | evaluated on/after 2026-08-26 |
  > |---|---|---|
  > | `Below floor` | **under VETO_LINE** | **VETO_LINE–FLOOR** |
  > | `Sub-target` | **VETO_LINE–FLOOR** | **FLOOR–TARGET** |
  >
  > 47 rows carry `Below floor` and 77 carry `Sub-target`; all but five are pre-boundary. Only 3
  > rows have ever used `Below veto line`, all post-boundary.
  >
  > **Any code or analysis reading `Comp_Flag` across the whole log must branch on
  > `Date_Evaluated`**, or it is wrong for one era. `rubric-learn.py` does — see `field_matches()`
  > and G2b's `requires_field_match` in `rubric/weights.json`, where a single non-era-aware
  > pattern counted one row (Company-140 `4400129341`, a VETO_LINE top) in the wrong band until
  > 2026-08-31.
  >
  > **The old rows are not rewritten.** Each was correct under the rules in force when it was
  > written, and overwriting a judgment field to make history look tidy is what the "flag, never
  > backfill" rule below exists to prevent — it would destroy the ability to tell what the
  > evaluator actually concluded. Same reasoning as the `Verdict` rule above: re-derive at
  > read time, never correct the stored value.
  >
  > **The banded token is the fix and it is forward-only.** Once every live row carries its band
  > in the string, the era rule stops mattering.
- `Carls_Action` / `Carls_Action_Date` — **leave blank during your own evaluation runs**, with one
  exception: the closed-posting check in Step 3 (`No longer accepting applications` detected at
  JD-fetch time) writes `Carls_Action = None` and `Carls_Action_Date` = today automatically —
  that's an observed fact, not a judgment call. Otherwise, Carl fills these in himself and his
  entry overrides your verdict. If he wrote `Applied` on a row you'd marked Skip, that is not an
  error to correct. This is about your own unprompted writes — if Carl directly asks in chat to
  set or update these fields (e.g. "mark X as applied, dated today"), do it; that's him filling
  them in himself via you.
  - **`Carls_Action_Date` on an `Applied` write is the actual application date, not the date of
    the processing run.** (Added 2026-08-24, after a run defaulted six triage-sourced
    `Carls_Action_Date` values to the run date instead of sourcing them, and had to be corrected
    after the fact.) Derive it from the source: a confirmation/ATS email's `date_received`
    (Inbox triage), or the LinkedIn Job Tracker's resolved `applied_date` (which is itself only
    ±1 day when `applied_date_is_approximate` — see "Second source: LinkedIn Job Tracker" below).
    Only fall back to the run date when Carl explicitly says "dated today" or there is genuinely
    no dated source available (e.g. Carl reports he applied outside this workflow, with no
    confirmation email or tracker entry) — and in that no-source case, ask Carl for the actual
    date rather than silently defaulting to the run date.
  - `Carls_Action` values are the action only — `Applied` / `Pass` / blank. **Never write
    `Applied - rejected`**; the application and its outcome are now separate columns. **Never
    append a qualifier in parentheses either** — e.g. `Applied (same postion)`, used on 2 rows to
    flag a duplicate-underlying-req situation (cleaned up 2026-08-08, both corrected to plain
    `Applied`). That context belongs in `Notes` (as it already was, redundantly, on both rows), not
    folded into the controlled-vocabulary field.
- `Outcome` — **what the employer did**, after Carl acted. Controlled values: `Rejected` /
  `Interview`, **or both joined with `; ` in the order they happened** — `Interview; Rejected`.
  Blank means no employer response recorded yet, which includes both "applied, no response" and
  every row where Carl passed or never applied. Leave blank on your own evaluation runs — same
  rule as `Carls_Action`; Carl fills it in, or asks you to.
  - **The compound is not a stylistic variant; it carries information neither half does.**
    (Documented 2026-08-31 — `05-triage-and-audits.md` already depended on it while this list
    still read as two mutually exclusive values.) `Interview; Rejected` records that Carl
    interviewed *and* was then rejected. On the first live rejection run, the blank-gate stopped a
    blind write of `Rejected` over a Company-416 row that already read
    `Interview; Rejected` — which would have destroyed the record that he interviewed. **A later
    stage never overwrites an earlier one; it appends.**
- `Reason` — **why the row ended the way it did.** This column pairs with whichever of
  `Carls_Action` / `Outcome` is populated, and carries one of the kinds of entry below.
  - **Carl's decision rationale**, when `Carls_Action` is `Pass` or `None` and `Outcome` is
    blank. Short and in his words — e.g. `Comp gap; Snowflake`, `experience gap`,
    `No longer accepting applications`. This is the common case and it is *not* a rejection.
  - **Rejection retrospective**, when `Outcome` = `Rejected`. A short read on why the rejection
    probably happened (domain gate, stack gap, lane mismatch, level). When Carl reports a
    rejection, offer this based on the row's logged `Biggest_Gap` and `Comp_Flag` rather than
    guessing fresh.
  - **Closed posting**, when the Step 3 closed-posting check detects "No longer accepting
    applications" at JD-fetch time — write `Reason = "No longer accepting applications"`
    automatically alongside `Carls_Action`/`Carls_Action_Date`. See Step 3.
  - **Skip headline**, whenever `Verdict = "Skip"` (score-driven, not a hard-override `"Pass"`).
    Write a 1–5 word summary of the single biggest thing pulling the score down or killing the
    role outright — synthesized from `Score`, `Role_Type`, `Comp_Flag`, `Biggest_Gap`,
    `Recommended_Action`, and `Notes` together, not copied verbatim from any one field. Favor the
    dominant disqualifier: lane/function mismatch (`"data engineering, not BI"`,
    `"CPG domain gate"`), a hard comp gate (`"comp below floor"`), a location gate
    (`"location gate (NYC)"`), scope mismatch (`"people-management scope"`,
    `"layered org leadership"`), or a domain gate (`"healthcare domain gate"`). If two factors
    are both genuinely decisive, a short combined phrase is fine (`"CPG domain, comp at floor"`),
    but don't try to list everything — pick what actually sank it. This entry is written by Claude
    on its own evaluation runs (see rule below) since it's a compact synthesis of the evaluation,
    not Carl's personal decision language.

    **Never write an IC-scope headline as a negative** — no `"IC scope, not leadership"`,
    `"IC role"`, `"below level"`, or equivalents. IC scope is what Carl wants; if a role is a
    Skip, the real reason is something else (lane, comp, location, domain, or genuine
    people-management scope). Find that reason instead. See Scope fit in the Scoring rubric.

  Rules that hold across all kinds:
  - **Leave `Reason` blank on your own evaluation runs**, except for: the closed-posting case
    above, the hard-override triggers (contract / low comp / consulting firm / Ladders posting —
    see "Hard override triggers" in `instructions/03-scoring-rubric.md`), and the Skip-headline case above. All three write
    automatically; everything else is Carl's to fill in, or he'll ask you to — same rule as
    `Carls_Action` and `Outcome`. Beyond the Skip headline, the reason *you* recommended a skip
    still belongs primarily in `Biggest_Gap` and `Recommended_Action` — the headline is a
    pointer to that reasoning, not a replacement for it.
  - A populated `Reason` with a blank `Outcome` is correct and expected. Do not "fix" it by
    inferring `Rejected`, and do not treat it as a data-quality problem in a run summary.
  - Don't restate the same text in both `Reason` and `Biggest_Gap`. `Biggest_Gap` is your
    full analysis of the posting; `Reason` is either the record of what was decided and by whom,
    or — for the Skip-headline case — a compact pointer into that analysis.

**Matching rejections back to logged rows.** When Carl supplies a rejection list (email, export,
or a crossref file) rather than naming a specific row, match on Job_ID first, then normalized
Company + Role_Title. Require a confident match — if the same company appears on multiple rows
and the title doesn't disambiguate, ask rather than guessing. If a rejection is clearly not in
the log at all, append it as a new row with `Carls_Action` = `Applied`, `Outcome` = `Rejected`,
and a dated `Notes` line naming the source it came from.

### Backup before each write-batch

(Added 2026-08-08.) Before the *first* write of a processing run touches `JD_Evaluation_Log.csv`
— append, dedupe backfill, or a Carl-requested `Carls_Action`/`Outcome`/`Reason` edit — copy the
file's current, pre-write state to `JobSearch/backups/` (create the folder if it doesn't exist
yet). Name the copy `JD_Evaluation_Log_<YYYY-MM-DD_HHMMSS>.csv` so backups sort chronologically
and never collide. Do the same for the OneDrive mirror, named
`JD_Evaluation_Log_OneDrive_<YYYY-MM-DD_HHMMSS>.csv`, using the same timestamp — each file gets
its own backup of its own pre-write state, same independent-copies discipline as the writes
themselves (see "OneDrive mirror" below).

**One backup per run, taken once before that run's first write — not one per row.** A run that
appends 38 rows and backfills 3 more takes exactly one backup of each file, not 41. The backup
exists so a corruption discovered later (a bad write, a bug like the ones found 2026-08-08, a
Fabric-side misparse someone tries to "fix" by editing the source file) has a known-good rollback
point; it is not a version-control system and backups are never taken mid-run.

**Backups accumulate — never auto-delete or overwrite them.** Pruning old backups is Carl's call,
not something to do silently as cleanup.

### Writing rows — always use a CSV writer, never manual string edits

Several fields (`Comp_Posted`, `Notes`, sometimes `Biggest_Gap`) routinely contain commas,
which breaks the file if rows are appended as raw text via a text-editing tool. Write and
backfill rows with a small Python script using the `csv` module
(`csv.writer(f, quoting=csv.QUOTE_MINIMAL)` for appends, or read-modify-write the full file
with `csv.reader`/`csv.writer` for backfills), never with manual comma-joined strings.

After every write, validate before moving on: re-read the file with `csv.reader` and assert
every row has the same number of fields as the header. Fix any mismatch immediately — don't
carry a broken file into the next step.

### Downstream consumer contract — Company-423 Fabric

(Added 2026-08-08, after a real ingestion bug. Expanded 2026-08-25 to cover the second table.)
Both CSVs in this workflow are read by Company-423 Fabric OneLake shortcuts that auto-transform them
into Delta tables for Power BI (lakehouse `JobSearch_LH`, region East US). Fabric is a second
audience for these files beyond Carl reading them directly, and it has its own parsing
configuration that has to agree with how the files are written.

#### One folder per table — the layout is load-bearing

**A Fabric table shortcut maps one *folder* to exactly one Delta table.** It does not create a
table per file. It merges every file it finds in the target folder into a single table, and
requires that they **all share an identical schema**. The shortcut picker only lets you check
folders — files aren't selectable — so there is no way to point a shortcut at one specific `.csv`.

The layout that follows from that, in the OneDrive root
`<onedrive-root>/`:

```
Documents/  (OneDrive root)
  JD_Evaluation_Log.csv               → shortcut #1 → JD table        (23 columns)
  LinkedIn_Message_Log/
    LinkedIn_Message_Log.csv          → shortcut #2 → LinkedIn table   (7 columns)
```

Two folders, two shortcuts, two tables. **Adding a second differently-shaped CSV to a folder does
not produce a second table** — it corrupts the table that folder already feeds. Confirmed
2026-08-25: with the 7-column LinkedIn log sitting beside the 23-column JD log in the OneDrive
root, the shortcut kept producing only the JD table and mapped the LinkedIn rows onto the JD
schema as junk (`Thread_ID` landing in `Job_ID`, columns 8–23 null). Creating an additional
shortcut on the same folder changed nothing, because the folder — not the file — is the unit.

**Any new CSV that needs its own table gets its own subfolder and its own shortcut. Never drop a
second CSV into a folder a shortcut already points at.**

#### Who wins on the four Carl-owned fields — `WriteBack_Applied` is the lock

(Added 2026-08-26, after reading the `JD_Transform` mashup directly rather than guessing.)
`Carls_Action`, `Carls_Action_Date`, `Outcome` and `Reason` exist twice: as CSV columns, and as
columns the Power BI write-back function updates straight into the SQL table. The dataflow
resolves the conflict per row, on a flag:

- **`WriteBack_Applied = true`** — a genuine report write-back happened. **The SQL value is locked
  and wins**, and a CSV edit to that row's four fields will never take effect.
- **`WriteBack_Applied` false or null** — **the CSV wins**, regardless of what SQL currently holds.

So editing these fields in the CSV is the right move for any row Carl has *not* triaged in the
report, and a no-op for any row he has. When both need to change on a write-back-locked row, the
change has to be made in the report; nothing local can override it.

#### The chain is not automatic — `JD_Transform` is manual-invoke

(Added 2026-08-26.) The OneLake shortcut polls every 2 minutes, but **the dataflow does not run on
a schedule** — every recorded run carries `invokeType = Manual`. Until someone runs `JD_Transform`,
a CSV change reaches OneLake and stops there: `JobSearch_DB`, the semantic model and the report all
still show the old values.

**Local writes therefore need two things before they appear in Power BI: OneDrive finishing its
upload, then a dataflow run — in that order.** Measured 2026-08-26: a write at 17:58 UTC was
*missed* by the 18:03 run (sync had not completed) and picked up by the 18:08 run. When verifying
a write round-tripped, confirm the dataflow ran *after* the sync settled, not merely after the
write — a run that started too early looks like a successful refresh and silently carries stale data.

#### A schema change can DESTROY write-back data — read this before altering a column

(Added 2026-08-26, after it happened. 11 of Carl's triage decisions were lost and had to be
restored by hand from a copy he still had open.)

The dataflow preserves report write-backs by self-joining the destination SQL table to itself and
reading `WriteBack_Applied` per row: true means "a real write-back set this, keep it"; false or
null means "the CSV wins, regardless of what SQL currently holds."

**That protection lives in the table's own rows, so anything that empties the table destroys it.**

**Add a column with `ALTER TABLE ... ADD`. Never `DROP` and `CREATE`.** A drop-and-recreate looks
equivalent — same columns, same data reloaded from the CSV on the next refresh — but it discards
every existing row first. The self-join then returns nothing, every row resolves to
`WriteBack_Applied = false`, the CSV wins everywhere, and **every write-back value that exists
only in SQL is overwritten with the CSV's blank.** Nothing errors. The dataflow reports success.
The loss is visible only by comparing counts to a pull taken beforehand.

Measured on the `Score_Raw` migration (2026-08-26), where the column was added by dropping and
recreating the table: `WriteBack_Applied` went from 12 rows true to **0 rows true**, and 11 rows
lost `Carls_Action` / `Carls_Action_Date` / `Reason`. They were recoverable only because a copy
of the values still existed outside the database.

**Before any schema change to `JD_Evaluation_Log.csv`:**

1. **Pull first and back up what only exists in SQL.** Run `scripts/fabric-pull-actions.py` and
   copy its output into `backups/fabric/` — it is the only copy of any write-back value the CSV
   does not have. `backups/` otherwise holds CSV snapshots, and the CSV is exactly the thing that
   does not contain this data.
2. **Do NOT backfill those values into the CSV.** (Corrected 2026-08-27.) An earlier version of
   this section said to reconcile Fabric-ahead fields into the CSV before migrating. That advice
   was wrong and it caused real damage — see the one-way rule below. A snapshot in
   `backups/fabric/` gives you the recovery copy without collapsing the override model.
3. **Check the flag after the dataflow runs.** Query `WriteBack_Applied`; if it went to all-false,
   the lock was reset and any value living only in SQL is already gone — restore it from the
   snapshot taken in step 1, in the database, not in the CSV.

### The one-way rule — never write a pulled value back into the CSV

Data flows in one direction:

```
CSV (front end) → OneDrive → OneLake → JobSearch_DB → Carl's report write-back is the override
```

**`scripts/fabric-pull-actions.py` reads down that pipe for the rubric learner only. Nothing it
returns may ever be written into `JD_Evaluation_Log.csv`.**

A row where the database holds a `Carls_Action` / `Carls_Action_Date` / `Outcome` / `Reason` that
the CSV lacks is **not drift and not a defect**. It is the design working: Carl triaged in the
report, and that value is meant to live only in the database. Copy it back and his write-back
becomes indistinguishable from a front-end pre-fill — it stops being an override of anything, and
it masks whether the database holds what he thinks it holds.

**Flag it. Never backfill it.** Reporting the divergence in a run summary is correct and useful.
Acting on it is not, and it is never a judgment call to make unilaterally.

**Writing those four fields at the front end is fine and wanted.** The whole point is to pre-fill
as much as possible before the data crosses into the database: the job-alert evaluation, the
email and LinkedIn triage marking a role `Applied`, and the Step 3 closed-posting check writing
`Carls_Action = "None"` all populate them legitimately. The prohibition is narrow and specific —
**not from a pull.**

(Added 2026-08-27 after 11 rows were copied back from a pull during a data-loss investigation.
The values happened to be correct, so nothing looked wrong; what it destroyed was Carl's ability
to tell whether his database restore had worked, and it cost him hours.)

#### Schema changes — both copies and the downstream chain move together

(Added 2026-08-26, after the `Score_Raw` migration.) The JD log went 23 → 24 columns on that date
via `scripts/migrate-add-score-raw.py`. Adding or removing a column is not an ordinary write and
does not follow the ordinary rules:

- **Both CSVs migrate in the same operation, or neither does.** A 23-column file sitting beside a
  24-column one in a shortcut's folder is the exact schema-mismatch failure documented above.
- **Append new columns at the end.** Inserting mid-table shifts every column after it while the
  shortcut re-infers, for no benefit — Power BI does not care about physical column order.
- **The chain past the shortcut is manual.** The pipeline is
  `OneDrive CSV → OneLake shortcut → JobSearch_LH → dataflow JD_Transform → JobSearch_DB →
  semantic model`. The shortcut re-infers on its next 2-minute poll, but **the dataflow's column
  mapping, the SQL table, and the semantic model do not update themselves.** A new column is
  invisible in Power BI until `JD_Transform` is edited to carry it and the model is refreshed.
  Budget for that as part of any schema change; don't assume the 2-minute poll finished the job.

#### Folder hygiene — the OneDrive root is a shared space

The OneDrive root is Carl's general Documents folder (Attachments, Meetings, Recordings, Copilot
Chat Files, tutorial folders, stray `.xlsx`), **and shortcut #1 points at it.** Any file landing
there with a CSV-family extension — `.csv`, `.txt`, `.tsv`, `.psv`, or their `.gz`/`.bz2`
variants — gets absorbed into the JD table on the next poll. Timestamped backups are safe only
because the convention puts the stamp *after* the extension
(`JD_Evaluation_Log.csv.bak_20260815_211341` reads as extension `bak_…`, not `csv`) — **do not
change that convention to `..._20260815.csv`, which would silently double the JD table.**

This is a standing risk, not a solved problem. The durable fix is to give the JD log its own
subfolder too (`Documents/JD_Evaluation_Log/`), which costs one shortcut re-creation and
re-setting Escape/Quote per below. Until that happens, treat the OneDrive root as a folder with a
live consumer attached.

#### Self-healing on removal

Fabric polls each shortcut target **every two minutes** and syncs in both directions: new or
modified files append or overwrite rows, and **deleted or moved-away files have their rows removed
from the Delta table automatically.** So the repair for a polluted table is to fix the *folder*
and wait a cycle — not to try to delete rows in Fabric. Direct `DELETE` and `MERGE INTO` against a
transformation target table aren't supported; these tables are read-optimized copies.

If rows persist after several poll cycles, delete the shortcut and recreate it. Deleting a
shortcut removes only the shortcut object — **the underlying CSV files are never touched.**

Verify at the table level (SQL analytics endpoint), not in the report — Power BI caches, and a
stale visual looks identical to a broken table:

```sql
SELECT COUNT(*) AS total,
       SUM(CASE WHEN Verdict IS NULL THEN 1 ELSE 0 END) AS junk_rows
FROM JD_Evaluation_Log;
```

`junk_rows` must be 0. Every legitimate JD row has a `Verdict`; rows carried in from a foreign
schema have nulls across columns 8–23.

#### Parsing configuration — must match how the files are written

Each shortcut carries its own settings, and a newly created shortcut does **not** inherit them
from an existing one. Set them explicitly every time.

**The files use RFC 4180 doubled-quote escaping** (a literal `"` inside a field is written as
`""`) — this is Python's `csv` module default (`doublequote=True`) and is what every write in
this workflow produces. **The Fabric shortcut's Escape character and Quote character must both
be set to Double Quote (`"`), not Backslash.** Confirmed 2026-08-08: with Escape set to
Backslash, 40 of 285 rows (14%) misparsed — Spark's parser stopped treating `""` as an escaped
literal quote and closed the field at the first `"`, shifting every column after it. The CSV file
itself was never malformed; this was purely a read-side config mismatch, and no data was lost or
needed repair once the setting was corrected.

**The Fabric CSV reader is not multiline-aware.** A hard line break inside a quoted field ends
the record as far as the reader is concerned, shattering one logical row into many malformed ones.
`JD_Evaluation_Log.csv` has never contained an embedded newline; `LinkedIn_Message_Log.csv` did,
and its writer now flattens them to a ` ¶ ` marker — see "No embedded line breaks" under G.7. Any
future free-text column feeding Fabric needs the same treatment.

If Fabric ingestion ever looks corrupted again (values bleeding into the wrong column, a field
count that doesn't match the header when queried, or a row count well above what the file holds),
**check the read side before suspecting the write path** — in order: is a foreign file sitting in
the shortcut's folder, are the Escape/Quote characters right, does the field contain a newline.
Validate the raw file first (see "Writing rows" above) — if `csv.reader` parses every row cleanly
with the header's field count, the file is fine and the bug is on the Fabric side, not here.

### OneDrive mirror — write to both copies, every time

(Added 2026-08-08.) A second copy of the log lives at
`<onedrive-root>/JD_Evaluation_Log.csv`. Confirmed
2026-08-08: same filename, same 23-column header, same row count and content as the primary file
at that time.

**Every write operation to `JD_Evaluation_Log.csv` — append, dedupe backfill, `Carls_Action` /
`Outcome` / `Reason` update, anything — must also be applied to the OneDrive copy, as the
identical operation, independently.** This is not a full-file copy or overwrite of one file onto
the other. Each file gets its own read-modify-write pass with the `csv` module (append via
`csv.writer(f, quoting=csv.QUOTE_MINIMAL)`, in-place edits via full read-modify-write with
`csv.reader`/`csv.writer`), and each write gets its own post-write validation (re-read with
`csv.reader`, assert every row's length equals the header's length) — same discipline as the
primary file, done twice, not copy-pasted from one success to assume the other worked.

**If the two files ever go out of sync** — one write succeeds and the other fails, or a
validation pass on one file turns up a mismatch the other doesn't have — **stop and flag it to
Carl explicitly**, naming which file is ahead and what the discrepancy is. Do not auto-repair by
copying either file over the other; that's a judgment call that belongs to Carl, not something to
resolve silently. Do not continue with further writes to either file once a desync is detected
until Carl says how to proceed.

If the OneDrive folder is ever inaccessible (not mounted, path changed, sync error) at the start
of a run, say so up front and ask Carl before proceeding — don't skip the mirror write silently
and don't fall back to writing only the primary file without saying so.

### Pre-run reconciliation: propagate Carl's manual edits to the primary file

(Added 2026-08-09, at Carl's request.) Carl edits the **primary** `JD_Evaluation_Log.csv` in the
JobSearch folder directly and by hand from time to time — outside any Claude-run workflow, with no
corresponding OneDrive write. The most common edit is setting `Carls_Action` to `Pass` on a row,
along with `Carls_Action_Date` and `Reason` (occasionally `Outcome` too). Because these are
one-sided edits to the primary file only, the OneDrive mirror silently falls behind on exactly
these fields until something reconciles it — and nothing did, until now.

**Before the first write of any run** (Phase B's first CSV touch, Phase E's first closure write,
or any ad hoc Carl-requested edit) — and before that first-write backup described above — diff the
primary file against the OneDrive mirror row-by-row on `Job_ID`:

- **Expected case: primary has a value in `Carls_Action`, `Carls_Action_Date`, `Outcome`, or
  `Reason` that the OneDrive row lacks or has differently.** This is Carl's manual-edit pattern.
  Propagate the primary file's values for those four fields to the matching OneDrive row — a
  targeted field-level update, not a full-row or full-file overwrite. This is the one sanctioned
  exception to "do not auto-repair by copying either file over the other" above: for these four
  Carl-owned fields specifically, primary is the known-ahead source because Carl only ever edits
  primary by hand.
- **Anything else found in the diff is still a stop-and-flag case, not an auto-repair one.** A
  difference in any other column (`Score`, `Verdict`, `Notes`, etc.), a row present in one file but
  not the other, or the OneDrive file being ahead of primary on one of the four Carl-owned fields
  (the reverse of the expected direction) — none of that matches the known manual-edit pattern.
  Report it to Carl exactly as the existing OneDrive-desync rule says and pause further writes
  until he says how to proceed. Do not guess at reconciling it as if it were the expected case.
- **Run this reconciliation pass even on invocations that end up finding nothing else to do** — a
  Phase E sweep with zero closures, or a Phase A pull with zero new mail, should still reconcile
  manual edits before reporting "nothing to do," since Carl's edits accumulate between runs
  regardless of whether new postings showed up.
- Validate both files after reconciling (same `csv.reader` field-count check as any other write),
  and report the count of rows reconciled in the run summary — this changes the OneDrive file even
  when nothing else in the run does.

---
