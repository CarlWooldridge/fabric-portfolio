# Cowork Folder Instructions — Carl's Job Alert Triage

## What this folder is

This folder receives LinkedIn job-alert emails. Your job is to extract every posting from
them, discard the ones already seen, pull the real job descriptions for the rest, evaluate
them against Carl's criteria, and append the results to `JD_Evaluation_Log.csv`.

Files in this folder:
- `JD_Evaluation_Log.csv` — the running log. Source of truth. Append new rows, and backfill
  blank fields on existing rows per step 2. Never reorder or delete rows, never overwrite a
  field that already has a value, and never touch the `Carls_Action` or `Carls_Action_Date`
  columns, which Carl maintains by hand.
- Job-alert emails (`.eml`, `.msg`, `.html`, or `.pdf`) — the input.
- `/processed` — move emails here once their postings are logged.
- `LinkedIn_Drafts/` — one Markdown file per LinkedIn message thread awaiting a reply, written by
  Phase G. Never sent automatically; Carl copies the text himself. See Phase G below.
- `LinkedIn_Message_Log.csv` — Power BI/Excel-facing log of LinkedIn threads seen in Focused, one
  row per thread, updated in place every Phase G run. See Phase G.7 below for the row-lifecycle
  rules — a thread never gets a row from before it was first seen in Focused.

Carl may also paste one or more LinkedIn job URLs directly into chat instead of (or alongside)
dropping an alert email. Treat that exactly like the file-based workflow — see
"Alternate input: pasted URLs" below.

## Workflow

### Naming convention — read this first

**Phases are letters. Steps within a phase are numbers.** Do not mix the two schemes, and do not
renumber existing ones.

- **Phases (A, B, C, D…)** are the top-level stages of a full run, most of which are driven by a
  script in `scripts/`. The current set is **A** (pull mail) → **B** (process postings) →
  **C** (trash source emails) → **D** (application/rejection/interview triage) → **E** (stale-Pursue
  closure sweep) → **G** (LinkedIn message triage & reply drafting) → **F** (monthly Skip audit).
  Note the letter **F comes before G alphabetically but runs last** — F is monthly/on-request and
  always ends in a question to Carl, so it stays at the end of the pipeline regardless of when it
  was added. Letter order is assignment order, not execution order. A prompt like "run job alert
  evaluation process" means all of them, in this run order — see "Alternate input: Mail.app
  pull-and-auto-trash" below for the authoritative list and which phases are unattended.
- **Steps (1, 2, 3…)** are the ordered stages *inside* a phase. The numbered Steps 1–7 immediately
  below (Extract → Dedupe → Fetch the JD → Evaluate → Summarize → Archive → Clean up) are the
  contents of **Phase B**; that's why this section reads as "Steps" while the run reads as
  "Phases."

If you add a new top-level stage, give it the next **letter**. If you add a stage inside an
existing phase, give it the next **number** within that phase. This convention was settled
2026-08-08 after the phases had drifted into a confusing "A → 2 → B → C" mix.

---

## Before a run: check for a session handoff

**If `scratch/NEXT_SESSION_PROMPT.md` exists, read it before starting.** It is the previous
session's note to this one — what it changed, what has not been exercised yet, and what to watch
on this run. It is *not* a standing rule and it never overrides the instruction files; where it
disagrees with them, they win.

It carries its own date at the top. **Act on it, then move it aside**
(`scratch/NEXT_SESSION_PROMPT.md.done_<date>`) so the next session does not follow stale watch
items. If it is more than about a week old and nothing has consumed it, treat it as history and
say so rather than acting on it.

This pointer exists so that "run job alert evaluation process" is a sufficient prompt. Carl
should not have to remember which scratch file a previous session left behind.

## The instruction set — load what the run needs

This file is the index and the always-applicable rules. **The rest of the workflow lives in
`instructions/`, split by run type on 2026-08-26.** The file was 2,542 lines (~41,000 tokens) as a
single document, and every run loaded all of it — including 559 lines of LinkedIn inbox protocol
that a job-alert evaluation never touches.

**Read this file first, then load only the parts the run actually needs.**

*Line counts below were re-measured 2026-09-01. Every one had drifted — `REVAMP_PLAN.md` was
listed at 190 and is 833. **If you edit a file here, re-measure this table** (`wc -l
instructions/*.md`); a routing table that lies about size is how a run picks the wrong load.*

| Part | Lines | Load it when |
|---|---|---|
| [`01-intake-and-fetch.md`](instructions/01-intake-and-fetch.md) | 549 | Pulling new postings — alert emails, pasted URLs, or a manual ID list. Steps 1–3. |
| [`02-evaluate-and-report.md`](instructions/02-evaluate-and-report.md) | 204 | Evaluating postings. Holds the hard gates (§4.0). Steps 4–7. |
| [`03-scoring-rubric.md`](instructions/03-scoring-rubric.md) | 917 | Scoring a posting. Carl's context, the components, the gates' definitions, the verdict classes. |
| [`04-log-and-write-discipline.md`](instructions/04-log-and-write-discipline.md) | 545 | Writing to `JD_Evaluation_Log.csv`. Row format, the controlled vocabularies, backups, dual write, the Fabric contract. |
| [`05-triage-and-audits.md`](instructions/05-triage-and-audits.md) | 528 | Phase D triage, Phase E closure sweep, Phase F recall audit. |
| [`06-linkedin-messages.md`](instructions/06-linkedin-messages.md) | 602 | Phase G only — LinkedIn inbox. Never needed for JD evaluation. |
| [`99-appendix-legacy.md`](instructions/99-appendix-legacy.md) | 63 | Never, for a run. Retired methods, kept for the reasoning. |
| [`REVAMP_PLAN.md`](instructions/REVAMP_PLAN.md) | 894 | **Modernising a phase, or starting a fresh session.** All seven phases are done as of 2026-08-31 — read its "State of play" section first. Scope, traps, incident log. |

> ⚠️ **The split's saving has largely eroded, and it is worth knowing before a run.** Phase B's
> load was 1,771 lines at the 2026-08-26 split; it is **2,215 now (+25%)**, against the 2,542-line
> monolith the split replaced — so the common run now loads **86%** of what it used to. Almost all
> the growth is incident narrative accumulating inside the rule files. Nothing is wrong with any
> of it, but `03` (917) and `04` (545) are the two to look at first if a run starts feeling heavy:
> the reasoning behind a rule can live in `rubric/learning_log.md` with the rule itself pointing
> at it.

### Which parts each run needs

- **Phase B — job-alert evaluation** (the common run): this file + **01 + 02 + 03 + 04**.
  Skips 05, 06 and the appendix — 2,215 lines, against 3,408 for the whole instruction set.
- **Phase D — application/rejection triage**: this file + **05 + 04**.
- **Phase E — stale-Pursue closure sweep**: this file + **05 + 01** (it re-fetches) + **04**.
- **Phase F — monthly recall audit**: this file + **05 + 03**. Ends in a question to Carl.
- **Phase G — LinkedIn messages**: this file + **06**.
- **Rubric learning**: `rubric/weights.json`, `rubric/learning_log.md`, and **03** for what the
  numbers mean. See `scripts/rubric-learn.py` — it proposes, it never applies.
- **Revamping a phase** (not running one): `REVAMP_PLAN.md` plus the one part file for that
  phase. It carries the method, the reusable scripts, and the incidents not to repeat.

**Splitting the file did not change any rule.** Every line moved verbatim; only the headers and
the cross-reference wording are new. If a rule here contradicts one of the parts, the part is
authoritative and this index is stale — say so rather than picking one.

### Where the numbers live

Point values, thresholds, gate classes and the consulting-firm list are **data**, in
[`rubric/weights.json`](rubric/weights.json) — not prose. `03-scoring-rubric.md` defines what each
component *means*; the weights file holds what it's *worth*. Never hardcode a value from the
weights file into the prose, and never edit the weights file by hand when
`scripts/rubric-learn.py --promote` will do it with an audit trail.

### Which model runs which part

(Added 2026-08-26 after a two-tier test run.) The two roles are pinned differently, and only
one of them can be pinned from inside this folder:

- **The evaluator IS pinned.** `.claude/agents/jd-evaluator.md` carries `model: sonnet` in its
  frontmatter, so evaluation runs on Sonnet no matter what model the session is set to. Delegate
  scoring to it by name — one agent per BATCH of postings, never one per posting (each agent
  starts cold and re-reads the ~670-line rubric, so fanning out per posting costs more than doing
  them in one context).
- **The orchestrator is whatever the session model is.** There is no way for the workflow to pin
  it; that is the session's own setting, chosen in the app's model picker before the run starts.

  **Carl's standing decision, 2026-09-01: Sonnet for the orchestrator, at medium reasoning
  effort. Haiku is not used for any part of this pipeline.** That settles a question this file
  had left open — it previously described Haiku as "a cost choice, not a correctness one" on the
  grounds that every mechanical step is a script. The reasoning was sound and the conclusion is
  overruled: the orchestrator still decides what to run, what to re-run, and what to tell Carl
  went wrong, and the 2026-08-26 Haiku test run got two of those wrong (it inverted `Score_Raw`
  against `Score` on capped rows and stopped a run on an environment error that did not exist).
  Do not reopen this per-run to save tokens.

  **Nothing in this folder can enforce that**, which is the point of writing it down: if a run
  starts on the wrong model, only Carl can see it, in the picker. `REVAMP_PLAN.md` still carries
  the older "run it on Haiku if you want to" line for *hardening* work — that section is about
  a different activity and is superseded by this decision for pipeline runs.

**Do not move scoring to the orchestrator to save a hop.** Measured 2026-08-26: an orchestrator
doing its own evaluating inverted `Score_Raw` against `Score` on capped rows and stopped a run on
an environment error that did not exist. The split exists because the judgment half is where
model quality actually shows.

### The one-way rule — data never travels back up the pipe

```
CSV (front end) → OneDrive → OneLake → JobSearch_DB → Carl's report write-back = the override
```

`scripts/fabric-pull-actions.py` reads **down** that pipe, for the rubric learner only.
**Nothing it returns may ever be written into `JD_Evaluation_Log.csv`.**

When the database holds a `Carls_Action` / `Carls_Action_Date` / `Outcome` / `Reason` that the CSV
does not, that is the design working — Carl triaged in the report and the value belongs only in
the database. **Flag it in the run summary; never backfill it.** Copying it up makes his
write-back indistinguishable from a front-end pre-fill and destroys the override.

Writing those four fields at the **front end** is wanted, not merely allowed — pre-filling as much
as possible before the data crosses into the database is the goal. The documented job-alert,
email and LinkedIn triage processes populate them, and the Step 3 closed-posting check writes
`Carls_Action = "None"`. The prohibition is narrow: **not from a pull.**

### The scripts do the mechanical work

Every deterministic operation is a script. Do not re-derive these by hand in a run:

| Script | Does |
|---|---|
| `scripts/fetch-jds.js` | Retrieves JD bodies (Tier 1 headless Chromium). Pacing caps are deliberate — do not tune for speed. |
| `scripts/jd-dedupe.py` | Partitions extracted postings into new / dupe / repost, with a backfill plan. Read-only. `--bodies DIR` adds a body-level pass — run it a second time after the fetch, per Step 2. |
| `scripts/jd-append.py` | Appends rows to both CSV copies. Backup, dual write, validation. |
| `scripts/jd-update.py` | In-place field edits. Blank-only by default; refuses judgment fields. |
| `scripts/fabric-pull-actions.py` | Pulls Carl's current actions down from Fabric. One-way, read-only. |
| `scripts/fabric-inspect.py` | Reads Fabric workspace state directly — items, created/modified dates, deployed dataflow and UDF source, `sys.objects`, refresh history, arbitrary SELECT. Read-only. **Run this instead of asking Carl whether something has been built.** See `scratch/HANDOFF_fabric-introspection_2026-08-27.md`. |
| `scripts/extract-postings.py` | Parses postings out of alert `.eml` files. Decodes MIME properly — never grep the raw file. |
| `scripts/rubric-learn.py` | Measures the rubric against Carl's actions and proposes changes. Never applies them. |
| `scripts/phase-state.py` | Records when each phase last completed and flags any phase older than the last Phase A. Run `--report` at the start and end of every run. |
| `scripts/mail-pull-imap.py` | **Phase A.** Exports matching Inbox mail to `.eml` + manifest over IMAP. Never opens Mail.app, so Mail stays usable during a run. |
| `scripts/mail-move.py` | **Phase C and Phase D's archive run through this.** Picks the fastest working backend and falls back rather than halting. |
| `scripts/mail-imap.py` | Fastest backend: server-side IMAP `SEARCH HEADER`. Trash / archive / restore. No Apple Events, so no Automation grant needed. |
| `scripts/mail-trash.py` | Apple Events backend, trash only. One bulk event (~50s vs the legacy 91min). |
| `scripts/gate-prepass.py` | Reports the seven mechanical §4.0 gates (G2/G2b/G3a/G4/G5/G6/G7) from extracted fields. Sets no `Verdict`; not yet wired into a run. |
| `scripts/gate-prepass-selftest.py` | Diffs the pre-pass against the 93 evaluated rows of 2026-08-31. Run after touching either. |
| `scripts/applied-badge-scan.py` | Finds LinkedIn applied badges in fetched JD bodies -> `scratch/applied-badge.json`. Phase D's third source. |
| `scripts/triage-match.py` | Phase D's matcher and renderer. Three sources: email, Job Tracker, applied badge. Halts rather than write a rule-breaking edit. |
