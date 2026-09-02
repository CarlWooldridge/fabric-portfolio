# Evaluator context — row format, comp lookup, closed postings

**GENERATED FILE — do not edit by hand.**
Rebuild with `python3 scripts/build-evaluator-context.py`.

This is a verbatim extract of the sections of `instructions/04-log-and-write-discipline.md`
and `instructions/01-intake-and-fetch.md` that the jd-evaluator agent actually needs. It exists
so the evaluator does not carry the Fabric contract, the OneDrive mirror rules, the backup
discipline, or the fetch pipeline in its context on every turn — those are orchestrator
concerns and cost ~45KB per turn to no purpose.

The source files remain authoritative. If this file ever disagrees with them, they win —
say so in your report rather than picking one.

---

## From `instructions/04-log-and-write-discipline.md` — Row format

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


---

## From `instructions/01-intake-and-fetch.md` — Applied-badge check

#### Applied-badge check — run this on every JD fetch, right after the closed-posting check

(Added 2026-08-31 at Carl's request.) While the body is in hand, check whether LinkedIn shows an
application badge on the posting — `Applied`, `Applied on company site`, `Application submitted`,
usually with a relative stamp ("Applied 2 days ago"). This is the **third source** for Phase D's
applied-to pipeline, alongside confirmation email and the LinkedIn Job Tracker.

**Record it. Do not write it.** Append an entry to `scratch/applied-badge.json`:

```json
{"job_id": "4458425988", "badge_text": "Applied on company site 2 days ago",
 "applied_date": "2026-08-29", "applied_date_is_approximate": true,
 "observed_at": "2026-08-31T14:02:11Z"}
```

and say so in that row's `Notes`. **Leave `Carls_Action` and `Carls_Action_Date` blank** — the
badge is an observation, and every applied-to write goes through Phase D's prompt so Carl
confirms it. This is *not* like the closed-posting check: a closed posting is a fact about the
posting, while an application is a fact about Carl, and those columns are his.

**Why it is worth capturing anyway.** Email and tracker are both time-boxed — a confirmation
mail only exists if the employer sent one, and tracker page 1 covers roughly five to six days.
The badge is not time-boxed: it is visible whenever the posting is fetched, however old the
application. It is the only source that recovers an application that generated no email and has
scrolled off the tracker.

**Its blind spot, and why the tracker stays primary.** The badge is only ever seen on postings
Phase B actually fetches, and Phase B fetches only the post-dedupe *new* set. A posting Carl
applied to is usually already in the log, so it dedupes out and its body is never retrieved —
on the 2026-08-31 run, 60 of 166 extracted postings were dupes or reposts and none were fetched.
So the badge is an opportunistic backstop, never a sweep. **It does not reduce the tracker's
job** and is not a reason to relax the tracker's every-run requirement.


---

## From `instructions/01-intake-and-fetch.md` — Compensation retrieval

#### Compensation retrieval — three-step lookup (added 2026-08-19)

Check in this order and stop at the first clear figure found. This applies whenever `Comp_Posted`
is being determined — a fresh Step 4 evaluation, a dupe backfill, or a Carl-requested comp
backfill pass over already-logged rows.

**Steps 1 and 2 are mandatory on every evaluation. Step 3 is the only discretionary one.**
(Clarified 2026-08-26.) Steps 1 and 2 read the `bodyText` that has *already been fetched* — they
cost nothing beyond reading text you are holding, so there is no such thing as skipping them for
time. Only step 3 (opening an external Apply link in a browser) is slow enough to reserve for
`Pursue`/high-priority rows.

**"Not researched" is only ever a statement about step 3.** Comp 10 — the neutral unlisted
default — is correct *only* after steps 1 and 2 have genuinely found nothing. Writing
`Comp 10 (unlisted; not researched due to time)` after skipping steps 1–2 is a scoring error, not
a shortcut: it silently biases every unlisted-comp posting downward by up to 10 points and can
flip a Pursue to a Skip on its own. If steps 1–2 found nothing, say so explicitly in `Notes`
(`"no comp figure in the LinkedIn pill or the About-the-job body"`) so the record distinguishes
*looked and found nothing* from *did not look*.

1. **LinkedIn's own comp field** — the pill/chip shown near the Remote/Hybrid/On-site and
   Full-time/Contract tags at the top of the posting. Present in the fetched `bodyText` before
   "About the job" starts.
2. **The "About the job" body itself.** Read for an explicit compensation statement ("The typical
   pay range for this position is $X-$Y", "Salary Range: $X-$Y", "Base Salary Range: $X-$Y
   annually"). Apply judgment, not a bare scan for `$`:
   - **Reject:** job/req IDs, years-of-experience figures, employee/follower counts, revenue or
     funding figures ("$300 million in programs", "$1B in funding"), benefit caps unrelated to
     base pay ("$720/year" wellness reimbursement, "$5,000 orthodontia benefit", "up to FLOOR
     of Net Purchases" credit-card terms) — and, critically, dollar figures belonging to a
     **different posting entirely**. LinkedIn's rendered page routinely appends "More
     jobs"/"Set alert for similar jobs" sidebar cards after the real posting's content, each
     carrying their own company and comp; a `$` figure found there is not this posting's comp.
     Confirmed 2026-08-19 during a comp-backfill pass: several postings' only `$` hits were
     sidebar cards for unrelated companies.
   - **Accept, with judgment:** figures phrased without "$" or with a "K" suffix where context
     makes it unambiguous (e.g., immediately following "Compensation:" or "Salary Range:").
3. **External company-site Apply link** — only when LinkedIn shows a genuine off-platform Apply
   button (postings tagged "Promoted by hirer" / "Responses managed off LinkedIn" route here),
   **never** "Easy Apply". Open the destination with the Browser tool and apply the same judgment
   as step 2. This step is comparatively slow — one manual browser round-trip per posting — so
   reserve it for `Pursue`/high-priority rows or an explicit Carl-requested comp backfill, rather
   than running it by default on every fresh Step 4 evaluation.

**Multi-location/multi-tier postings.** When a posting lists different ranges per market (e.g.,
"Mountain View $X-$Y / San Diego $A-$B" or "SF Bay Area & NYC $X-$Y / All Other US Locations
$A-$B"), prefer the broadest/most nationally-representative tier, not a premium-market figure —
Carl is Nashville-based, not a resident of the named target markets. Note the other tiers in
`Notes` if genuinely ambiguous rather than silently picking one.

**`Comp_Flag` is mechanically recomputed once a figure is found**, using the floor/target logic
from the Scoring rubric (`instructions/03-scoring-rubric.md`). This is not a new judgment call,
just applying that logic to a now-known number.

**Write exactly one of the tokens defined in `04-log-and-write-discipline.md`** under `Comp_Flag`
— that list is the single authoritative copy and is not restated here. ⚠️ It also carries the
2026-08-26 era warning: the same band names meant one band lower before that date, so **read it
before interpreting the flag on any older row**. The one place this can overwrite an
already-populated `Comp_Flag` outside a
fresh evaluation is the sanctioned exception documented under "Alternate source: original company
career-site posting" further down (a posted figure superseding a prior
`Unlisted - researched $X-$Y` estimate).

Write one JSON object per posting to a scratch folder, then run dedupe/evaluate/log against
those files. Keep fetching and scoring as separate stages so a scoring change never re-fetches.


---

## From `instructions/01-intake-and-fetch.md` — Closed postings

#### Closed-posting check — run this on every JD fetch
As soon as the page renders (Tier 1) or the source page loads (Tier 2), check whether
"No longer accepting applications" appears near the top of the page, before doing anything
else with the posting. This applies to **every** JD fetch — batch email processing, pasted-URL
one-offs, and backfills alike. If the text is present:
- `Carls_Action` = `None`
- `Carls_Action_Date` = today's date (the date of the run)
- `Reason` = `No longer accepting applications`

This is the one sanctioned exception to "leave `Carls_Action`/`Carls_Action_Date`/`Reason` blank
on your own evaluation runs" (see Step 4 and Row format in `instructions/04-log-and-write-discipline.md`) — closure status is an observed
fact, not a judgment call, so it's fine to write it automatically. Still run the full evaluation
and log a `Score`/`Verdict` as normal; a closed posting is still worth recording for pattern
purposes, it's just no longer actionable. Note the closure in the run summary alongside the
normal counts.


---

