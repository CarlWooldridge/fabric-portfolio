# Revamp plan — finishing what Phase B started

*Written 2026-08-27, at the end of the session that revamped Phase B. This exists so a fresh
session can pick up one phase and start work without re-deriving any of it.*

**Read this file plus the one phase you are working on. Nothing else.**

---

## Status

| Phase | What it is | State |
|---|---|---|
| A | Mail pull (`mail-pull.applescript`) | Working, scripted, unchanged |
| **B** | **Job-alert evaluation** | **DONE 2026-08-27 — fully scripted, run for real.** ⚠️ Three rule changes of 2026-08-31 have not yet been through a live run — see State of play |
| C | Trash source emails | Working, scripted, unchanged |
| **D** | **Application / rejection / interview triage** | **DONE 2026-08-27 — scripted, run for real** |
| **E** | **Stale-Pursue closure sweep** | **DONE 2026-08-28 — scripted; ran clean with 0 rows eligible.** ⚠️ The live fetch path has still never executed |
| **F** | Monthly Skip audit (recall check) | **DONE 2026-08-28 — scripted, run for real, answered, recorded.** 13 unasked Review-gate rows are held for the next run |
| **G** | LinkedIn message triage and replies | **DONE 2026-08-28 — writer hardened, live run completed end to end** |

### 2026-08-31 — rubric and vocabulary session (no phase changed)

| Area | Change | State |
|---|---|---|
| `rubric-learn.py` | `override_rates()` ordering guard; `component_separation()` the same; `rule_fires()` extracted; `current_verdict_class()`; `watchlist()`; `SCALE_BOUNDARIES`; `--self-test` (24 assertions, fault-injected 5 ways) | **Done, measured, nothing promoted** |
| G1 `contract` | 47% -> **11%** corrected. Stays `review` on the 2026-08-26 recall sweep, not on the rate | **Carl's decision, recorded** |
| G2b / G3b | Patterns were written from memory and measured n=0. Rebuilt from the log; G2 was short 4 rows | **Done — G2b n=7, G3b n=5, both 0% on almost no evidence** |
| Lane-12 cap | Now **conditional on the handoff test** (option C). Backtested over all 22 rows sitting at 69 | **Done — not yet seen by a live run** |
| `Comp_Flag` | Era drift found (the floor moved 2026-08-26 and both band names shifted one place). Banded tokens forward; four copies collapsed to one in `04` | **Done — no rows rewritten** |
| `Verdict` | Measured under **current rules**, re-derived, never rewritten. Vocabulary completed — `Unretrieved` and `Not evaluated` were missing from it | **Carl's decision, implemented** |
| `Role_Type` | Declared controlled; 16 of 32 off-spec rows normalised, qualifiers moved to `Notes` | **Done — 16 one-offs left by choice** |
| `Outcome` | Spec widened to permit `Interview; Rejected`, which the process already depended on | **Done** |
| `jd-evaluator` agent | Told about the conditional cap and the `Role_Type` vocabulary | **Done — it had neither** |
| `Work_Type`, `Applicant_Volume` | Checked: 203 and 57 spellings, **zero ambiguous**, nothing reads them | **No action, by decision** |
| `COWORK_INSTRUCTIONS.md` | Routing table re-measured — every line count had drifted, `REVAMP_PLAN` listed at 190 vs 833 | **Done** |

Phase B's scripts: `extract-postings.py`, `jd-dedupe.py`, `jd-append.py`, `jd-update.py`,
`fabric-pull-actions.py`, `rubric-learn.py`. Phase D added `triage-match.py`, E added
`stale-sweep.py`, F added `recall-audit.py`. G hardened `update-linkedin-message-log.js` rather
than adding a script. Read them before writing new ones — most of what Phase G needs already
exists.

---

## The method that worked

Do not start by writing code. Phase B's wins came from measuring first.

1. **Measure what the model is doing that a script should.** For Phase B this found two things
   nobody had noticed: dedupe was being done by reading a 1.2 MB CSV into context on every run,
   and the CSV writer was being *re-authored from scratch* each run (39 KB, 21 KB, 11 KB scripts
   found in `scratch/`). Together, ~40–50% of the run's tokens. Look for the same shape.
2. **Build the script and test it against real data**, never synthetic. Every real bug found this
   session — the HTML `href` stripping, the containment matcher, `Score_Raw` inversion, the
   backfill — surfaced only against real files.
3. **Fix the instructions**, with the date and the evidence that motivated the change. A rule
   with its incident attached survives; a bare rule gets re-litigated.
4. **Run it for real.** Dry-run first, show the rows, then write.

**Do this on Sonnet or Opus, not Haiku.** Haiku is fine *running* a hardened process — that is
what the pinning is for. Hardening one is judgement work over unfamiliar code, and Haiku tested
badly at it: it halted on a misdiagnosed environment error, and it inverted `Score_Raw` against
`Score` on capped rows.

**One phase per session.** Not because any phase is huge, but because the work needs room to
measure, run, and catch its own errors. Roughly half this session's mistakes came from moving
fast in a long context.

---

## Rules that apply to every phase

**The one-way rule.** Data flows `CSV → OneDrive → OneLake → JobSearch_DB → Carl's write-back is
the override`. `fabric-pull-actions.py` reads *down* that pipe for the learner only. **Nothing it
returns may ever be written into `JD_Evaluation_Log.csv`.** A database value the CSV lacks is the
design working, not drift. Flag it; never backfill it. Full statement in
`04-log-and-write-discipline.md`.

**Writing the four write-back fields at the front end is wanted**, not merely tolerated —
pre-filling as much as possible before data crosses into the database is the goal. The documented
triage processes populate them, and the closed-posting check writes `Carls_Action = "None"`. The
prohibition is narrow: *not from a pull*.

**But a field Carl has already written back is finished, and the CSV stays blank on it.**
(Added 2026-08-27 at Carl's direction, after Phase D's tracker step proposed writing two rows he
had already triaged in the Power BI report.) Before any phase writes `Carls_Action`,
`Carls_Action_Date`, `Outcome` or `Reason`, it must **cross-reference `fabric-pull-actions.py`'s
output and honour what the database holds**:

- `WriteBack_Applied = True` and the field is non-empty → **that is Carl's decision. Suppress the
  write. Leave the CSV blank.** Pre-filling it makes his override indistinguishable from a
  front-end pre-fill, which is the entire thing it exists to override.
- **Honouring is not backfilling.** The pulled value decides *whether to write*; it is never
  itself written. Nothing from a pull enters the CSV — that rule is unchanged.
- The database wins even when it disagrees. On the first run, Fabric held
  `Carls_Action_Date = 2026-08-26` for Company-519 (4431006891) where LinkedIn's tracker computed
  `2026-08-25`. Carl's date is the right one; the divergence gets reported, not resolved.
- **A blank field on a write-back row is still writable.** The check is per-field, not per-row:
  if Carl wrote back `Carls_Action` but `Outcome` is empty in the database, a rejection notice
  may still pre-fill `Outcome`.
- **No current pull, no writes.** `triage-match.py --decisions` halts when
  `scratch/fabric_actions.csv` is missing or not from today, because a stale pull can miss a
  write-back Carl made since and the phase would silently overwrite it.
  `--skip-writeback-check` exists and should essentially never be used.

This applies to **every remaining phase**, not just D. Phase E writes `Carls_Action = "None"` on
closed postings — if Carl has already actioned that row in the report, Phase E must leave it
alone too.

**Every CSV write:** reconcile → one backup per run → real CSV writer → independent dual write →
post-write validation. `jd-append.py` and `jd-update.py` already encode this. Use them rather
than writing new writers.

**Schema changes:** `ALTER TABLE ... ADD`, never `DROP`/`CREATE`. See the incident log below.

**Model pinning:** `.claude/agents/jd-evaluator.md` pins evaluation to Sonnet regardless of
session model. The orchestrator is whatever the session is set to.

---

## Phase D — application / rejection / interview triage — DONE 2026-08-27

**Built:** `scripts/triage-match.py`, two modes. Match mode joins `triage-candidates.json` to
log rows and classifies each sender from the envelope; render mode turns the model's
classifications into a validated `jd-update.py` edit list. The full command sequence is in
`05-triage-and-audits.md` under "Mechanics — scripted as of 2026-08-27".

**The split that made it work:** the script never decides what an email *means*. It finds
candidate rows, reports what is already in the four write-back fields, and refuses writes that
break a documented rule. Classification stayed with the model, per the phrase-list evidence in
`05-triage-and-audits.md`. Everything mechanical — matching 45 emails against 921 rows, parsing
dates, deciding which mail is even Phase D's — left the context entirely.

**Measured on the live run (2026-08-27, 45 Inbox messages):** 26 of 45 routed to Phase B/G from
the envelope alone; 19 bodies read. 7 rows written, 12 fields, every one filling a blank. One
email blocked and deliberately left un-ledgered.

**The refusals are the load-bearing part.** `triage-match.py --decisions` halts on: a
`Carls_Action_Date` with no `date_source` or one that disagrees with the email it claims to come
from; a write with a missing or unknown `Job_ID`; ledgering a `blocked` email; archiving a named
individual's mail; and writing from a forwarded job-alert digest. All ten guards were tested
against deliberately malformed decisions before the first real run.

**Three real bugs that only real data would have shown:**
- The documented LinkedIn-notification sender (`inmail-hit-reply@`) missed the live one
  (`hit-reply@`), and missed `jobs-noreply@` recommendation digests entirely.
- Company-76 rejected Carl from `careers@onebarnes.com` naming only "Barnes". The row
  existed, applied 2026-07-15, and matched nothing. Short-form company names now match, but only
  when the title matches too.
- A friend forwards LinkedIn digests; each names 4-6 companies that match log rows perfectly and
  mean nothing. Detected from the quoted envelope, and writes from them are refused.

**Second source — LinkedIn Job Tracker — is part of Phase D, and now mechanically required.**
Match mode and render mode both halt without a same-day, non-halted `applied-tracker.json`
(`--skip-tracker` overrides, loudly). It stays **page 1 only** — re-confirmed 2026-08-28;
`fetch-applied-tracker-paginated.js` is a one-time backfill tool, not the per-run path. Page 1
spans about five to six days at Carl's current rate, so `scripts/phase-d-state.json` records each
successful read and the script warns when a gap means applications scrolled off unseen. It was in the legacy
process, `fetch-applied-tracker.js` already existed, and the revamp's first pass left it out.
Now folded into `triage-match.py`'s report: exact `Job_ID` match, its own decision key
(`tracker_job_id`), and a restriction to `applied`/`noop`/`blocked` since the tracker cannot
express a rejection. It earned its place immediately — of ten entries, one named the role for an
email that had been blocked as unidentifiable, one was an application with **no confirmation
email in existence**, and one was a posting whose only email was a recruiter's pitch (a pitch is
not evidence of applying; the tracker is). LinkedIn's whole-day stamps are ±1 day and may only be
written with `date_source: carl_confirmed`.

**Guard tightened 2026-08-28 (after D was marked done).** `require_writeback`'s staleness
check was date-based and passed a whole calendar day. Carl's rule is **one pull per run of the
process, not one per day** — he can write back at any hour, so an afternoon run against a
morning pull could overwrite a decision he made at noon. Now measured in minutes
(`--max-pull-age-minutes`, default 120). Tested against fresh / 3-hours-old / missing / override
cases; `--self-test` still passes.

**Closed 2026-08-28 — Company-562, `4457961944`, "Director, Analytics".** Went through the Phase B
path as Carl chose; the row now exists (score 64, Lane 25, killed by the Director+ screen) and
carries `Carls_Action = Applied`. Phase F picked it up as one of the seven true overrides.

## Phase E — stale-Pursue closure sweep

**What it does.** For every row where `Verdict` is `Pursue` **or** `Review` and `Carls_Action` is
blank, re-fetch the posting and run the closed-posting check. It is a **fact re-check, not a
re-evaluation** — `Score`, `Verdict`, `Role_Type` and the judgment fields are never revised.

**The work:** a selector script that queries the log for those rows, batches them to
`fetch-jds.js` (cap 25/run), detects "no longer accepting applications" in the fetched
`bodyText`, and emits a `jd-update.py` edit list writing `Carls_Action = "None"`,
`Carls_Action_Date` = today, `Reason = "No longer accepting applications"`.

**Reusable:** the closed-posting detection already exists as a one-off in this session's Phase F
sweep — check the git-less `scratch/` history or just rewrite it, it is one regex against
`bodyText`. `fetch-jds.js` handles the fetching unchanged.

**Trap:** a fetch that fails with `SKELETON_AFTER_MAX_ATTEMPTS` returns an **empty** `bodyText`.
Absence of "no longer accepting applications" in an empty string is not evidence the posting is
open. Report those as `UNVERIFIED`, never as open. This exact mistake was made on 2026-08-26.

**Two things Phase D established that E inherits directly:**

- **The write-back rule applies here.** E writes `Carls_Action = "None"`, which is one of the four
  fields Carl overrides in the report. Cross-reference `fabric-pull-actions.py` and skip any row
  the database already holds — see "a field Carl has already written back is finished" in the
  rules section above. Do not let a closure sweep overwrite a decision he made.
- **`triage-match.py` is the reference implementation for the guards.** Its render mode refuses
  bad writes rather than warning about them, and every refusal names the incident behind it. The
  `SKELETON_AFTER_MAX_ATTEMPTS` trap below is the same shape and should be a halt in the selector,
  not a line in the run summary. Copy the pattern, not the code — E's inputs are different.

**Run the upstream fetches first — E inherits Phase D's preconditions, and they are a real
failure surface.** (Added 2026-08-28.)

- Two separate auths, either of which can fail on its own: `python3
  scripts/fabric-pull-actions.py` needs `az login`, and `fetch-jds.js` needs a live LinkedIn
  session at `~/.li-auth/storageState.json` (`node scripts/save-auth.js` when it has aged out).
  E does **not** need the applied tracker — that is Phase D's second source, and E's LinkedIn
  dependency is posting fetches, not the tracker.
- **The pull is once per run of the process — not once per day.** (Carl, 2026-08-28.) It
  carries Carl's write-backs, and he can write one back at any hour; a pull from this morning
  can already be wrong by this afternoon. So: pull at the start of the run, then reuse that one
  file for the rest of the run. Do not re-pull between steps within a run.
- **`triage-match.py`'s guard was tightened to match, 2026-08-28.** It compared mtime *date*
  against today, so a 16:00 run against an 08:00 pull passed while missing a noon write-back —
  it caught the stale-overnight case only. Now `require_writeback` measures age in **minutes**
  against `--max-pull-age-minutes` (default 120): wide enough that one pull at the start of a
  run covers every step of that run, narrow enough that this morning's pull will not serve an
  afternoon run. **Copy that guard into E's selector** — it lives in `triage-match.py`, not in
  the pull script, so E gets no copy of it for free.
- Phase D's overrides (`--skip-writeback-check`, `--skip-tracker`) print exactly what goes
  unseen when used. E needs the same shape for its own pull check: an override that names the
  cost out loud, not a silent flag.

**Built 2026-08-28: `scripts/stale-sweep.py`,** two modes on the `triage-match.py` pattern.
`select` (default) queries the log, honours Fabric's write-backs and emits an ID list;
`--classify DIR` reads what `fetch-jds.js` returned and emits a `jd-update.py` edit list. The
script never decides what a posting *means* — only whether the closed phrase is present.

**The first real run found nothing to do, and that is the result.** 10 rows matched
Pursue/Review + blank `Carls_Action`; **all 10 were suppressed** because Fabric already holds
Carl's decision (8 `Pass`, 2 `Applied`, `WriteBack_Applied = True`). Zero fetched. Under the old
CSV-only reading those same 10 rows would have been re-fetched and written — the write-back
cross-reference is not theoretical here, it was the entire outcome of the run.

**Verified against real data, not synthetic:**
- The real `SKELETON_AFTER_MAX_ATTEMPTS` file from 2026-08-26
  (`scratch/fetched_sweep_20260826/4453245128.json`) → `UNVERIFIED`, halt, exit 1. Never "open".
- The real 2026-08-16 sweep directory → 3 open, 1 closed-but-already-actioned, 0 writes.
- A confirmed-closed writable row → one correct edit, and `jd-update.py --dry-run` accepted it
  and set exactly the three intended fields on both copies.
- Suppression re-checked in classify mode, not trusted from select: the same closed posting
  emits an edit against an unsuppressed pull and is left alone against the real one.
- Stale pull → halt, exit 1. `--self-test` covers closure phrasings and the suppression truth
  table.

**Still unrun: the fetch path.** `select` had nothing to hand `fetch-jds.js`, so no live fetch
happened this session. The classify side was exercised against previously fetched real pages.
First sweep with actual eligible rows should be watched rather than trusted.

**Acceptance test:** a sweep that reports open/closed/unverified counts separately, and writes
only for confirmed-closed rows.

---

## Phase F — monthly Skip audit (recall check)

**What it does.** Surfaces rows the filter rejected, so over-tightening becomes visible. Present
a compact list, ask Carl one question — *were any of these worth a look?* — and record the answer
and the ratio. It does not re-verdict anything.

**The work is mostly analysis, and `rubric-learn.py` already does the adjacent half.** Consider
whether this belongs as a mode of that script rather than a new one — both read the same pull,
apply the same exclusions, and report against the same rubric.

**Selection criteria** are specified in `05-triage-and-audits.md`: last 30 days, `Verdict = Skip`
in the 60–69 band; plus rows killed by G6/G10/G11/G12 or the Director+ screen; plus rows taking
the people-management deduction that landed 60–69; plus unactioned Bridge candidates.

**Record the answer in `rubric/learning_log.md`**, not just in chat. The 2026-08-26 sweep entry
is the format to follow. The ratio — audited vs. wanted — is the recall estimate, and it is the
only check on whether the filter has gone too far.

**Live finding to carry in:** the 2026-08-26 sweep scored **2 of 3**, above the protocol's own
"three or more means something is too tight" line.

**Built 2026-08-28: `scripts/recall-audit.py`.** Not a mode of `rubric-learn.py`, and the reason
is measured rather than stylistic: the pull carries no `Biggest_Gap`, `Notes`, `Location` or
`URL`, so Phase F must join the pull to the CSV; `rubric-learn.py` never asks a question, and
folding an interactive step into it would cost it the property that makes it safe to run
unattended; and `rubric-learn.py` measures only the rules in `weights.json` — G1, G2, G2b, G3a,
G3b, G4 — while every Phase F gate (G6, G10, G11, G12, Director+, the people-management
deduction) is absent from that dict and had **never been measured by anything**. It shares the
pull, the class boundaries and the learning log. Full mechanics in `05-triage-and-audits.md`.

**The first real run's headline finding was a measurement bug, and it inverted the answer.**
The audit's first pass put the Director+ screen at a **30% override rate on n=46** — review-class,
over the n floor, apparently the strongest evidence yet that a 2026-08-10 gate was too tight.
Checking it before reporting it showed **13 of those 14 applications were made before the row was
ever evaluated**, dated 2026-05-14 to 2026-07-29 against evaluations dated 2026-08-12. The
2026-08-12 backfill retro-logged Carl's application history and scored it under the current
rubric; the gate could not have stopped an application made two months before it fired.
Corrected, Director+ measures 2% and **every Phase F gate lands in veto class**. The gates added
2026-08-10 are not over-firing.

**FIXED 2026-08-31 — see "The ordering fix, measured" below.** The paragraph that follows is
what the bug looked like before it was corrected; the corrected numbers are at the end of this
section.

**This bug is in `rubric-learn.py` too, and it is load-bearing there.** 142 of the log's 400
actioned rows carry a `Carls_Action_Date` earlier than their `Date_Evaluated`.
`rubric-learn.py`'s `override_rates()` counts `Carls_Action == "Applied"` with no ordering
check, so its numbers carry the same contamination:

| rule | fired | applied | of which pre-date the evaluation | raw rate | true rate |
|---|---|---|---|---|---|
| `contract` (G1) | 22 | 10 | **8** | 45% | **9%** |
| `low_comp` (G2) | 41 | 1 | 0 | 2% | 2% |
| `ladders` (G4) | 27 | 0 | 0 | 0% | 0% |

**G1 `contract` was demoted from veto to review on 2026-08-26 on the strength of a 47% override
rate. Corrected for ordering that rate is 9% — veto class.** The demotion may well still be
right on other grounds, but the number that justified it does not say what it was read as
saying. Not changed this session: it is `rubric-learn.py`'s measurement and the rubric's call,
and one phase per session. **Fix `override_rates()` before the next promote, and re-read the
2026-08-26 entry in `rubric/learning_log.md` in that light.**

**Also confirmed this run, per the note below:** `Verdict = "Review"` has still never appeared,
and **zero rows evaluated since 2026-08-26 were Review-shaped** — no compensable gate fired
without a veto-class gate also firing. Untested, not dead code. The check now runs every Phase F.

**Answered 2026-08-28. Theme shortlist 5 of 7; random control 0 of 15.**

121 unanswered rows is not a list anyone reads one by one, so the ask was split into two
buckets that are reported and recorded separately and **never pooled**: a *theme shortlist*
of rows matching a rule Carl had already stated, and a seeded *random control* drawn from
everything else. Only the control is a recall estimate — the shortlist's rows were selected
because he had said he wanted that shape, so a high rate there proves nothing. `--ask` and
`--control-sample N` in `recall-audit.py`; the control seed is the window, so a re-run of the
same window redraws the same sample.

**The control came back 0 of 15. No unnamed theme is visible, and the gates are calibrated.**
Weak evidence, not proof — 15 rows cannot rule out a pattern affecting a handful — but it is
the first honest recall number the process has ever produced.

**The one real finding is a lane contradiction, not a gate.** All five wanted rows are data
architecture, data platform or semantic-layer work. `03-scoring-rubric.md` has carried a
**handoff test** since 2026-08-27 — *"my jobs should ultimately always be a handoff to a
stakeholder; I shouldn't be the primary user of what I build"* — written almost entirely from
its negative side. Its positive side was never spelled out, and Lane scoring contradicts it:
G8 sends data-platform work to Lane 0, these postings land at Lane 12, and **Lane 12 caps the
total at 69 — one point under Pursue.** Five of the seven true overrides score exactly 69 and
every one is Lane 12. Carl, 2026-08-28: *"core BI is one of my lanes, but data architecture
and Finance Systems are also my lanes."*

**Title family is not the signal; the consumer is.** "FP&A **Business Systems** Analyst" and
"Finance **Transformation** Data Analyst" pass the test and were still declined for other
reasons; "Senior Financial Analyst" and "Strategic Finance Manager" fail it. The audit's open
conflict — a handoff-shaped role inside a function-modifier-capped lane (Company-558) — Carl
answered **want**, which settles the precedence: the handoff test runs first, and the
function-modifier cap fires only on roles that fail it. Recorded in `03-scoring-rubric.md`.

**The Lane re-weight — DECIDED 2026-08-31, and it was never a re-weight.** It could not go
through `rubric-learn.py`'s propose/promote path at all: `weights.json` holds only `lane.max`, and
that path proposes rule classes and inverted components, neither of which this is. Carl chose
option C — the Lane-12 cap is conditional on the handoff test. See "Suggested order" item 2.

**Two smaller findings from the same answers:**
- **Company-412 (4436361951) is `Review`-shaped and the rubric cannot express it.** Carl declined
  it but said it "might be in the Review category — comp is good, on-site in La Vergne is good,
  some good skill alignment, but ultimately out of lane." `Review` currently fires only on the
  compensable gates G1/G2b/G3b; a good-on-everything-but-lane row has no way to reach it. That
  is the first evidence the trigger is too narrow — n=1, so watch for a second.
- **Comp that only exists off-LinkedIn killed a row the JD made look fine.** Company-326
  (4453716999) posted no range; Carl found $120–130K on the corporate site, below the VETO_LINE
  veto floor. The evaluator cannot see that, and `Comp_Posted` was blank.

### The ordering fix, measured — 2026-08-31

**`override_rates()` now excludes applications dated before `Date_Evaluated`.**
`applied_before_evaluation()` was ported verbatim from `recall-audit.py` (keep the two
identical), and `--self-test` was added: 15 assertions, including the 2026-08-26 incident in
miniature — a gate that reads 45% raw and 5% corrected must not produce a reclassification.
Fault-injected by reverting the guard to `return False`: 8 assertions fail and the test
reproduces the exact bad proposal, `contract: veto -> review, "fired 20, applied anyway 9 (45%)"`.

**The population did not change; only the numerator did.** The re-measured uncorrected rate is
`0.47368421052631576` — byte-identical to the standing 2026-08-27 proposal's provenance. That is
the proof that this is the ordering fix and nothing else.

| rule | gate | declared | measured | fired | override | pre-dated | rate | uncorrected |
|---|---|---|---|---|---|---|---|---|
| contract | G1 | review | **borderline** | 19 | 2 | 7 | **11%** | 47% |
| low_comp | G2 | veto | veto | 41 | 1 | 0 | 2% | 2% |
| consulting_named | G3a | veto | veto | 57 | 0 | 1 | 0% | 2% |
| ladders | G4 | veto | veto | 27 | 0 | 0 | 0% | 0% |
| comp_floor | G2b | review | — | 0 | 0 | 0 | — | — |
| delivery_role | G3b | review | — | 0 | 0 | 0 | — | — |

**All 7 pre-dated `contract` rows are 2026-08-12 backfill rows acted on in June and July** —
Company-495, Company-542, Company-197, Silicontek, InterEx, Company-619, Focused HR. Not a boundary
case; the whole 47% was the backfill talking.

**G1 lands at borderline (11%), not veto, and `propose()` skips borderline — so the machinery
will never revisit the 2026-08-26 demotion on its own.** Reverting `contract` to veto is Carl's
call, not the script's, and the number no longer argues for `review` either: 11% sits between
`veto_max` 10% and `review_min` 25%.

**Read the 11% with its tie-break attached.** Both true overrides are **same-day** pairs —
InterEx `4445507224` (eval and action both 2026-08-12) and Riana `4452713933` (both 2026-08-14).
`applied_before_evaluation` counts a same-day pair as an override by design, which errs toward
reporting the filter as too tight. Treat same-day as pre-dated instead and `contract` measures
**0% on n=19** — squarely veto. So the entire distance between G1 and veto class is two same-day
rows. Worth one look at whether those two evaluations actually preceded the applications.

**Not done here, deliberately:** nothing was promoted. `rubric/weights.proposed.json` is now the
2026-08-31 measurement (contract still declared `review`, zero proposed changes), and the
contaminated 2026-08-27 proposal is kept as evidence at
`backups/weights.proposed.json.pre_ordering_fix_20260831_093046`.

**`component_separation()` was fixed the same day, and it was the worse of the two.** 21 of 33
`Applied` rows in the Pursue population were decided before the row was scored — **64% of the
applied group** — against 0 of 11 `Pass` rows. One-sided by construction: a backfilled row is by
definition one Carl acted on. Corrected, the applied group is 12, not 33.

- **`Pts_Comp` separation nearly tripled**, +0.65 -> **+1.92**. Comp discriminates far harder than
  the contaminated table showed. `Pts_Location` flips sign, +0.10 -> -0.18.
- **Nothing is actionable.** The binding n is `min(12, 11) = 11`, under the floor of 15, so every
  component finding is now blocked. The honest sample is a third of what it looked like.
- **`Pts_Lane` is 25.0 on both sides — this measurement cannot see the Lane question at all.**
  Every Pursue row scores full Lane, and the five 69s that motivate the re-weight are `Skip` rows
  that never enter the population. See the carry-forward list; this changes what item 2 is.

Rows are **dropped, not moved to the other group** — a pre-dated `Applied` is not evidence he
passed, it is evidence the score played no part. Fault-injected both ways.

**Decisions Carl made on the results, 2026-08-31:**

- **G1 `contract` stays `review`, on other grounds.** 11% is borderline and `propose()` skips
  borderline, so the script will never revisit it unprompted. The 45% that justified the
  2026-08-26 demotion is gone; what holds it up is the recall sweep from that same day — rows the
  gate had auto-killed, Carl wanted 2 of 3 (SHI International 85 at $160-215K, and Company-96 62
  which he had already applied to). Recorded in `03-scoring-rubric.md`, which also carried the
  contaminated 45% in its veto-admission table and has been corrected.
- **Same-day pairs count as overrides.** He does not remember InterEx `4445507224` or Riana
  `4452713933` and counts both as overrides. This is the entire distance between G1's 11% and 0%.

---

## Phase G — LinkedIn message triage and replies

**Largest, most isolated, lowest risk to `JD_Evaluation_Log.csv`. Do it last.**

566 lines of protocol in `06-linkedin-messages.md`, its own CSV (`LinkedIn_Message_Log.csv`,
7 columns), and four Chromium scripts: `fetch-linkedin-messages.js`, `linkedin-msg-dispose.js`,
`sweep-delete-sponsored.js`, plus `update-linkedin-message-log.js` as its writer.

**This is a review-and-harden job, not a rewrite.** The scripts work. The gap is discipline.

**The concrete finding to start from:** `update-linkedin-message-log.js` has backup handling and
dual-write to OneDrive, but **no post-write validation at all** — no field-count assertion, no
re-read from disk. `jd-append.py` and `jd-update.py` both validate; this one does not. That is
the first thing to fix, and it is the same class of bug that made the Fabric misparse invisible
for a week in August.

**Domain-specific rules that already exist and must be preserved:**
- Never delete a thread (`sweep-delete-sponsored.js` carries an absolute no-delete rule).
- Replies are **drafted, never sent** — written to `LinkedIn_Drafts/` for Carl to copy.
- No embedded line breaks in the CSV: the Fabric reader is not multiline-aware, and this file's
  writer flattens them to ` ¶ `. That is load-bearing.
- The LinkedIn log lives in its **own OneDrive subfolder** with its own Fabric shortcut. One
  folder maps to exactly one Delta table — never put a second CSV beside it.

**Trap:** this CSV feeds a *different* Fabric table from the JD log. Anything learned about the
JD log's write-back merge does not automatically apply here — check before assuming.

**Done 2026-08-28 — the writer. `update-linkedin-message-log.js`, seven defects, each marked
`[Gn]` in its header with the evidence.** The concrete finding above was right and was the smallest
of the seven. Measuring the script against the live data rather than reading its comments found the
rest. In severity order:

- **`[G7]` every run re-dated every row to the run date.** LinkedIn renders message times as
  relative day markers (`TODAY`, `WEDNESDAY`); `resolveDate()` resolved them against `now` instead
  of against the transcript's own `scrapedAt`. A 2026-08-25 capture read on 2026-08-28 moved seven
  of seventeen rows forward by up to seven days — Anthony Soriano 08-25→08-28, Natalie Sherrill
  08-19→08-26. **It was invisible because both prior runs happened on the same day as the scrape**,
  and the wrong dates are plausible-looking, so nothing downstream would have flagged them.
- **`[G1]` no post-write validation, the finding this phase started from.** Now: atomic write via
  temp file, re-read both copies from disk, assert header / field count / row count / no raw line
  break / unique Thread_IDs / legal Status / byte-identical copies. **Restores from this run's
  backup and exits 1 on failure** — fault-injection tested against a truncated file and a raw
  newline in a field.
- **`[G4]` a thread missing from the run's capture silently reset `Replied` → `Received`.** With a
  25-thread fetch cap and 14 Focused threads this fires the first time a batch does not cover
  everything, and `Received` is the actionable state, so it manufactures work on threads Carl has
  already answered. Status is still recomputed every run, but with no transcript the prior value is
  carried and the carry is reported.
- **`[G3]` transcript freshness was a coincidence.** Six hardcoded filenames, first match wins;
  `fetch-linkedin-messages.js` takes `--out`, so any other path was structurally invisible. Sources
  are now discovered and ranked by `scrapedAt`. Discovery immediately turned up three real capture
  files the list had never read.
- **`[G5]`** reading the existing CSV trusted its header and blanked any column it could not find;
  **`[G2]`** `toISOString()` on a local Date shifted every evening run's dates and backup filenames
  forward a day (same family as the 2026-08-27 incident); **`[G6]`** the flattener trimmed after
  collapsing, leaving a stray `¶` at the edge of a field — found by `--self-test` on its first run.

**Verified against real data, not synthetic.** The acceptance test was that a run today against a
three-day-old capture is a **byte-for-byte no-op on both copies** — it is, and that same property
is what proves the stored file was never corrupted by `[G7]` before now. `--self-test` covers 27
cases; `--dry-run` reports rows added/updated, every Status change, every Date change, and every
carried Status.

**The live steady-state run happened the same day and the whole pipeline held.** 17 Focused
threads fetched; 2 new (Nick Casalenda, Kishore Mishra); 4 drafts written; 1 move applied (Kyle
Chandler → Other); 1 LinkedIn notification email trashed; log written to 19 rows and validated on
both copies. The classification side (G.1–G.5), the drafting rules, `linkedin-msg-dispose.js` and
the G.6 mail cleanup were reviewed and needed no changes — the no-delete rule is enforced in three
independent layers in the dispose script.

**The run re-confirmed `[G7]` on live data, which is the strongest evidence in this file.** The
fresh 2026-08-28 capture became the winning source for all 17 threads, so under the old code every
row would have re-dated to 08-28. It reported **exactly one** `Date` change — Kyle Chandler
`2026-08-25 11:45 AM → 2026-08-26 9:16 AM` — corresponding to a real new message he sent. Sixteen
dates held still. That is the guard doing the job it was built for, on data it had never seen.

**Three judgment calls Carl made that the rubric would have decided differently** — worth carrying,
because two of them went against the mechanical reading:

- **Kyle Chandler → Cold.** *Director of Data Architecture*, Nashville-local, direct-hire,
  remote-first, JD attached, **VETO_LINE–135K**. In lane and at the right level; comp is at the VETO_LINE
  veto line and well under the FLOOR scoring floor, and the end client was unnamed — two confirmed
  strikes, so Cold was also the mechanical answer. Carl declined naming comp as the reason and
  leaving the door open at a higher band. **This is the first Phase G row where comp alone killed
  an otherwise ideal in-lane, in-market, right-level role**, and it is the same comp-vs-lane
  tension Phase F surfaced in the five 69s. Worth watching as evidence for the Lane re-weight.
- **Nick Casalenda → Hot, over a Warm recommendation.** *Data Architect (Azure DW)*, remote,
  6-month contract-to-hire, end client **named** (Accanto) — so the anonymous-client half of the
  staffing strike does not fire, leaving one strike. Near-exact stack match (SQL Server warehouse
  architecture, T-SQL refactoring, dimensional modeling, SSRS/Power BI, SSIS/ADF) across
  Clinical/RCM/CRM/**Finance incl. GL and revenue recognition**. Comp was entirely unstated, which
  is normally what keeps a lead Warm; Carl called it Hot on scope detail alone. The draft still
  carries one rate question, since G.4's "nothing material left to ask" is not literally true
  without a rate on a contract role.
- **Donavon S. reversed from Cold to a call.** He was declined and moved to Other on 2026-08-25;
  he reappeared in Focused on 08-28 with **no new message**. The dispose log confirmed the move had
  applied, so this was not a silent LinkedIn revert — Carl had moved it back himself and wanted a
  call. The prior decline draft was superseded into `LinkedIn_Drafts/archive/` and replaced.
  **A thread reappearing in Focused is not automatically a failed move — check the dispose log
  before re-applying anything, and ask.**

**Also observed, no action taken:** Jonah Wimmer, Sam Ingwell and Nicole Swift all sat at **exactly
14 days** on 2026-08-28 (last message 08-14, Carl spoke last, awaiting them). G.5 keeps a thread at
"14 days or less", so they stayed — and all three go to **Archived** on the next run, since Carl has
sent in each. The boundary is inclusive; do not round it.

---

## Incident log — do not relearn these

**2026-08-26 — write-back data destroyed by a schema change.** `Score_Raw` was added by dropping
and recreating the SQL table. That emptied the dataflow's write-back self-join, every row resolved
to `WriteBack_Applied = false`, and 11 rows of Carl's triage decisions were overwritten with the
CSV's blanks. Nothing errored. **Use `ALTER TABLE ... ADD`.** And never carry a CSV-vs-database
divergence across a schema change without snapshotting the database side first, into
`backups/fabric/`.

**2026-08-26 — pulled values written back into the CSV.** During the investigation above, 11 rows
were copied from a Fabric pull into `JD_Evaluation_Log.csv`. The values were correct, so nothing
looked wrong — what it destroyed was Carl's ability to tell whether his database restore had
worked, and it cost him hours. The pull script's own `--diff` output had recommended it. **Flag,
never backfill.**

**2026-08-27 — 27 rows dated a day early.** The evaluator was handed `"today is 2026-08-26"` in
its prompt; the session had crossed midnight. `Date_Evaluated` drives the learner's training
window and Phase F's 30-day sweep, so the error is silent. **Get the date from `date +%F`, never
from a prompt.**

**2026-08-26 — a rule with no definition decided differently on similar postings.** G10's
"primary tooling" was never defined, so one run fired the gate on `"Looker (or similar BI tools)"`
and another did not fire it on a tool buried in a list. **If a rule needs judgement, write down
what the judgement is.**

---

**2026-08-27 — a documented sender list was wrong and nothing noticed.** Phase D's instructions
named `inmail-hit-reply@linkedin.com` as the LinkedIn-notification sender; live mail used
`hit-reply@linkedin.com`. Every such email had been falling through to be read and classified as
if it were employer mail. **A sender, domain or format list written from memory is a hypothesis —
check it against a live scan before relying on it.**

**2026-08-27 — "resolved" was quietly conflated with "ours to move".** Phase D scans the whole
Inbox, so the first archive list it produced included a school newsletter, a podcast mailing and
two Sam's Club receipts. Resolving non-job mail means "not ours", which is a reason to stop
touching it, not a licence to move it out of Carl's Inbox. **Scope a phase's write permissions to
the mail it is actually for.**

**2026-08-27 — a front-end write duplicated a write-back Carl had already made.** Phase D's
email path wrote `Carls_Action`/`Carls_Action_Date` to Company-331 (4454535147) from a
confirmation email. The values were right, and Fabric already held them with
`WriteBack_Applied = True`. Nothing was corrupt — what was lost was the ability to tell Carl's
override apart from a front-end pre-fill on that row, which is the whole point of the write-back
column. Reverted to blank on both copies the same day; Fabric kept the values. **A correct value
written in the wrong place is still a defect.** The pull is now consulted before any write, and
render mode halts without a current one. The other six rows written that session were audited
against the pull and were all legitimate — the field was blank in Fabric on a non-write-back row
in every case.

**2026-08-28 — `jd-dedupe.py` catches reposts, and the process was not asking it to.** The
recall audit surfaced two duplicate postings Carl spotted immediately: Company-483
"Data Architect" logged twice (4367009665 on 08-11, 4457166880 on 08-25) and Selective
Insurance "Data & Analytics Architect" logged three times (4249256573 applied 07-27 and
rejected, then 4249254755 on 08-13 and 4436141178 on 08-15). Tested against the live script:
both pairs normalise to an identical company — the suffix stripper handles "Corporation" — and
score **title similarity 1.0**, well over the 0.82 floor. `probable_reposts` would have flagged
every one. The gap is the invocation: `jd-dedupe.py <ids>` does **exact Job_ID matching only**,
and a LinkedIn repost always carries a *new* Job_ID, so that path structurally cannot see one.
Repost detection needs `--json` with the extracted postings. The same role also scored
differently across sightings (Phibro 64 then 69; Selective 67 then 65), so a missed repost
costs a duplicate row *and* an inconsistent score. **Run `jd-dedupe.py --json`, and treat a
`probable_reposts` hit as something to resolve, not a line in the summary.**

**2026-08-28 — an override rate measured the backfill, not the filter.** Phase F's first run
reported the Director+ screen at a 30% override rate (n=46), review-class and over the n floor.
13 of the 14 "overrides" were applications Carl made *before* the row was evaluated — the
2026-08-12 backfill retro-logged months of his application history and scored it under the
current rubric. The true rate is 2%. 142 of the log's 400 actioned rows have an action date
earlier than their evaluation date, and `rubric-learn.py` has the same unguarded comparison —
its `contract` rule reads 45% raw and 9% corrected. **Any measurement of "Carl did X despite
rule Y" must check that the evaluation came first.** A rule cannot be overridden by a decision
made before it fired. **Closed 2026-08-31:** `rubric-learn.py` now carries the same guard and a
`--self-test` that reproduces the bad proposal when the guard is removed. Measured live, G1
`contract` is 11% (2 of 19), not 47%. Two things this leaves behind — `propose()` ignores
`borderline`, so a rule that lands there is invisible to the machinery and needs a human; and
`component_separation()` still has no ordering check.

**2026-08-28 — a date derived from when the code ran, not from when the thing happened.** For the
third time in this project. `update-linkedin-message-log.js` resolved LinkedIn's relative day
markers (`TODAY`, `WEDNESDAY`) against the run date instead of against the transcript's `scrapedAt`,
so every run silently re-dated every relative-marker row forward. Seven of seventeen rows moved by
up to seven days on the first run that was not same-day as its capture. It survived two live runs
undetected because both happened on the scrape date, and the wrong dates look entirely plausible.
Caught only by diffing a real run against a pre-run snapshot — the run was supposed to be a no-op
and was not; the file was restored from that snapshot the same minute. **Two rules from this.**
First, the one already in this log — *get the date from the thing, never from the run* — now
covers scraped relative markers, not just prompt-supplied dates. Second, and more generally:
**when hardening a script, make its first real run a provable no-op and diff it.** A refactor that
is supposed to change nothing is the only cheap opportunity to see what the old code was
silently doing. Nothing else in this session would have found this.

**2026-08-28 — `--out` is relative to the shell's cwd, not to the script.**
`fetch-linkedin-messages.js --out linkedin-threads-2026-08-28.json` run from the JobSearch root
wrote the capture to the **root**, not to `scripts/`. The log writer's source discovery scans
`scripts/` and `scratch/`, so the fresh capture was invisible to it and the next step failed on a
missing file. Harmless because it failed loudly; it would not have been harmless if discovery had
silently fallen back to the three-day-old capture. **Pass `--out` a path under `scripts/`, or move
the file before running the writer.**

**2026-08-31 — normalise against the thing the label describes, not against its spelling.** The
`Role_Type` cleanup looked like string tidying: strip a parenthetical from two regular variants,
16 rows. Checked against `Pts_Lane` instead of against itself, **9 of the 16 did not fit the naive
strip** — 6 had no Lane score at all, and 3 scored Lane 25 while being labelled `Bridge`. A
string-level normalisation would have run clean, reported 16 rows fixed, and quietly mislabelled
three. The qualifier turned out to be encoding a second concept the field does not mean — career
significance rather than lane fit — which is why it could not be dropped without checking.

**2026-08-31 — every controlled vocabulary in the log had drifted, in a different way each time.**
Checked after `Comp_Flag`: `Verdict` was defined in **two separate bullets of the same file** and
both lists were incomplete — `Unretrieved - needs manual pull` (3 rows) lived only in `01`, and
`Not evaluated` (10 rows) was documented **nowhere**. `Role_Type` was documented as three values
but never declared controlled, and the log holds **18**, with 32 rows carrying variants and four
of those mapping to no Lane score; `recall-audit.py` already carries a warning that matching
`Role_Type` on the word "bridge" reads **251 rows instead of 25** — a 10x miscount someone had to
work around. `Outcome` was specified as two mutually exclusive values while
`05-triage-and-audits.md` depended on the compound `Interview; Rejected`, the very value whose
near-overwrite justifies the blank-gate rule. **The drift never came from a copy being wrong — it
came from a vocabulary with no single owner.** A controlled vocabulary needs one home, inbound
links, and the word "controlled" written on it.

**2026-08-31 — one definition in four files is how drift survives.** `Comp_Flag`'s controlled
vocabulary was stated in `01`, `03`, `04` and a `rubric-learn.py` docstring. When the comp floor
moved on 2026-08-26, no single copy was wrong enough on its own to notice, and each read as if it
were the definition — the drift lasted five days and was caught by a gate pattern needing to read
the field, not by anyone reading the docs. Collapsed to one copy in
`04-log-and-write-discipline.md` (the field spec, and the only file that already held the
`Unlisted - …` half); the others now point at it, and `weights.json`'s patterns are declared
derived **from** it. **A controlled vocabulary needs one home and inbound links — restating it "for
convenience" is what makes a change invisible.**

**2026-08-31 — the sweep: this defect had already happened three times.** Asked of every label
field after the `Comp_Flag` finding: is its meaning defined relative to a rule that has since
changed, with nothing on the row saying which version applies? Four real instances. `Verdict =
Pursue` (2026-08-10, the deleted 50-69 band, 124 rows) — **already guarded**, by
`training_set()`'s `pre_window_pursue` exclusion, which is this exact defect handled correctly and
never generalised. `Comp_Flag` (2026-08-26, 124 rows) — fixed the same day. `Pts_Comp` and
`Pts_Skills`/`Pts_Perks` — two scales each, not currently biting because the compared population
happens to sit inside one era, which is luck: `window_start` coincides with the 2026-08-10
boundary and nothing protected the 2026-08-26 one. And `Role_Type = Bridge`, ambiguous for four
hours by the conditional-cap change made earlier the same day. **One still open: 22 pre-2026-08-26
`Pass` rows carry a `contract` or `consulting delivery` reason, both of which produce `Review`
now.** Guard added — `SCALE_BOUNDARIES` in `rubric-learn.py` declares each boundary date and the
fields it re-pointed, and any measurement straddling one says so. **The lesson is not "check
Comp_Flag": it is that a rule change re-points every value already named after the old rule, and
the project had fixed one instance of that without ever writing down that it was a class.**

**2026-08-31 — a threshold moved and silently re-pointed 124 existing rows.** The comp floor was
raised from VETO_LINE to FLOOR on 2026-08-26. The change was recorded carefully as a scoring change,
and nothing noticed that two `Comp_Flag` band *names* — `Below floor` and `Sub-target` — were
defined relative to that threshold and so changed meaning for every row already written under
them. No value changed, no error appeared, and the strings look identical either side of the
boundary. It surfaced only because a gate pattern written five days later needed to read the field
and got one row wrong. **When a threshold moves, ask what already-written values were named after
the old threshold.** A label that encodes a rule is a dependency on that rule.

**2026-08-28 — a self-test found a defect on its first execution.** The `--self-test` written for
the hardened LinkedIn writer failed one case immediately: the newline flattener trimmed *after*
collapsing, so a leading or trailing line break became a stray `¶` at the edge of the field. Minor
in effect, but it had been shipping since 2026-08-25 and no amount of reading the function would
have shown it. **Write the assertions before believing the code.**

**2026-08-28 — `Verdict = "Review"` has never once appeared in the log.** It was added to the
rubric 2026-08-26 as the fourth verdict; 28 rows have been evaluated since and the counts are
Skip 549 / Pursue 180 / Pass 179 / Not evaluated 10 / Unretrieved 3 — no `Review`, ever. Phase E
selects on it, so the selector is written for a value that has yet to exist. Not proven broken:
the two consulting rows since then were named firms, which G3a sends to `Pass` ahead of G3b's
`Review`, and no contract/staffing posting has come through. **Worth one look during Phase F** —
if a `Review`-shaped posting has gone by and scored `Skip` or `Pass` instead, the fourth verdict
is dead code and the recall audit is the place that would show it.

## Suggested order

**D → E → F → G — all four are done, including Phase G's live triage run (2026-08-28).** The line
that used to sit here said G's live run was outstanding; it was stale from the moment G finished
the same day, and it survived three sessions unnoticed. Corrected 2026-08-31.

**Carry into the next session, in this order:**

1. ~~**Fix `rubric-learn.py`'s `override_rates()`**~~ — **DONE 2026-08-31.** Guard ported,
   `--self-test` added and fault-injected, re-measured against a same-day Fabric pull. Results
   and the two loose ends in "The ordering fix, measured" under Phase F. **This no longer blocks
   the item below.**
2. ~~**Propose the Lane re-weight**~~ — **DECIDED 2026-08-31: option C.** A Lane-12 role is
   capped at 69 only if it **fails the handoff test**; pass it and the cap lifts and the score
   stands. Written into `03-scoring-rubric.md` ("The Lane-12 cap is conditional on the handoff
   test") and `02-evaluate-and-report.md` (a handoff-passing Lane-12 row is no longer a bridge
   candidate). **It was never a re-weight and could not go through propose/promote** —
   `weights.json` holds only `lane.max = 25`; the tiers and the cap are prose, and
   `rubric-learn.py` proposes only rule classes and inverted components.

   **Backtested over all 22 rows sitting at exactly 69:** six applications clear the cap
   (Company-576 from 84, Company-324 Lead Data Architect and Company-316 from 75, Arista from 72, plus
   Vantage and Company-702); the four Company-64 "Business Analytics Manager" rows, Company-591, Company-478 and
   Yusen fail the test and stay at 69. **Company-176 and Phibro — both roles Carl wanted — do not move:
   they score 69 on their own totals and were never capped.** That is option C's honest limit;
   more of that shape reopens the question as option A (Lane 25 for handoff-shaped roles).

   **`Is_Capped_Score` is unreliable** — it disagrees with `Notes` on 4 of the 22 (Company-693,
   Company-303, Vantage, Company-702). `Score_Raw` would settle it and is blank on 894 of 922 rows. Read
   `Notes`; the rubric requires the cap to be stated there.

2b. ~~**Decide G1 `contract`.**~~ **DONE 2026-08-31 — stays `review`**, on the 2026-08-26 recall
   sweep rather than on the override rate. See above.
2c. **`propose()` is blind to borderline rules, and G1 now sits there.** A rule that lands between
   `veto_max` 10% and `review_min` 25% produces no proposal and no flag — it simply never comes up
   again. That is fine for a rule someone has just decided on and bad for one nobody has looked at
   in months. Consider making borderline something the report nags about.
2d. ~~**G2b `comp_floor` has never been measured**~~ **DONE 2026-08-31.** Both patterns were
   written from memory: G2b's `below comp floor` is a word order that appears nowhere in 922 rows,
   and G3b's `consulting delivery role` is a token the log has never used. Corrected from the
   actual `Reason` strings and cross-checked against `Comp_Flag`; G2 was short by 4 rows for the
   same reason (41 -> 45). **G2b now fires 8 and G3b 5, both at 0% override — and Carl has acted
   on exactly one of the 13.** The rate means he has never looked, not that he agreed.
2g. ~~**`Verdict = "Pass"` on 22 pre-2026-08-26 rows**~~ **DONE 2026-08-31 — Carl: measure under
   current rules.** Implemented as `current_verdict_class()`, a re-derivation from `Reason` against
   the classes now in `weights.json`; the stored column is never rewritten and is not consulted.
   **The real count is 13, not 22** — the sweep's figure came from a bare regex that ignored
   precedence: 4 rows still carry a G2 low-comp veto, 4 a G3a named-firm veto, 2 are posting-status
   rows outside the population. All 13 are `contract`; G3b contributes none. `rule_fires()` was
   split out so the derivation and `override_rates()` share one matcher rather than two that drift.
   Standing rule now recorded against `Verdict` in `04-log-and-write-discipline.md`.
2e. **Put those 13 rows to Carl on the NEXT PHASE F RUN — held, not asked, at his direction
   2026-08-31.** They are Phase F's job and have never been asked. G1, G2b and
   G3b *are* the `Review` verdict. G1 measures borderline; G2b and G3b measure veto-class on no
   evidence. Nothing currently measures as compensable, which is consistent with `Verdict =
   "Review"` never once appearing in the log.
2f. ~~**`Comp_Flag`'s vocabulary contradicts its own spec.**~~ **DONE 2026-08-31 — and the
   diagnosis was wrong.** Nothing contradicted anything: the comp floor moved VETO_LINE -> FLOOR on
   2026-08-26 and **both `Below floor` and `Sub-target` shifted one band**, with no era marker on
   any row. The 47 `Below floor` rows were correct when written. It had already produced a wrong
   number in code written the same morning — G2b counted Company-140 `4400129341` (top exactly
   VETO_LINE) in the wrong band; 8 -> 7. Fixed forward with a banded token (`Below floor
   (VETO_LINE-150K)`), an era table in `01-intake-and-fetch.md`, and `field_matches()` in
   `rubric-learn.py` reading each row under its own era. **No rows rewritten** — each is correct
   under its era, and `Comp_Flag` is a judgment field the intake rules forbid overwriting.
2h. **`Role_Type` normalised 2026-08-31 at Carl's direction — 16 of 16 written, 32 -> 16 off-spec
   rows.** The 6 `Out of lane (retrospective)` rows all have a blank `Pts_Lane` (retrospective
   backfills, never component-scored) and went to `Out of lane`; 7 of the 10
   `Bridge (paycheck + currency…)` rows scored Lane 12 and went to `Bridge`. Qualifiers moved to
   `Notes`, not dropped. The 3 Lane-25 rows —
   Company-655 `4445863502`, Ancora `4447164680`, Company-148 `4447535851` — went to
   `Lane-advancing` at Carl's direction in a second run: the mapping wins, and *"paycheck +
   currency, not a lane move"* is preserved in `Notes`. **All 16 normalised; off-spec rows 32 ->
   16**, the remainder being the one-offs Carl chose to leave. Both qualifier strings are now 0 in
   `Role_Type` and 16 in `Notes`; both copies byte-identical (sha `d43b5ff7c935577b`).
   **Open, but only if it comes up:** `Role_Type` has no way to say *"in lane, but not a career
   move"* — a $75K in-lane contract and a real lane move now read identically. If a sweep ever
   needs to separate them, that is a **separate field**, not a qualifier smuggled back into this
   one.
3. **`propose()` no longer goes silent — `watchlist()` added 2026-08-31.** A rule that measures
   `borderline`, fires zero times, or disagrees with its declared class under the n floor used to
   produce no output at all. All three now print in the run summary, the learning log and the
   proposal provenance, with an `acted` count beside each rate so "0% because he agreed" and "0%
   because nobody looked" stop reading the same.
4. **Phase G is done.** Next Phase G run: three threads age past 14 days and go to Archived
   (Jonah Wimmer, Sam Ingwell, Nicole Swift), and four drafts are sitting `pending_send` from
   2026-08-28 — they go stale on 2026-09-11 if Carl has not sent them.

After each phase: update the Status table at the top of this file, and add anything learned to
the incident log.

---

## State of play — 2026-08-31, for a fresh session

**All seven phases are built, hardened and have been run for real.** The process is ready to run
end to end. What follows is everything a new session needs to know before it does.

**Run it on Haiku if you want to — with one caveat.** Running a hardened process is what the
model pinning is for: `.claude/agents/jd-evaluator.md` pins scoring to Sonnet regardless of the
orchestrator's model, and every mechanical step is a script with its own `--self-test` and its own
refusals. **The caveat is that three rules changed on 2026-08-31 and none has been exercised by a
live evaluation run yet** — see "Not yet exercised" below. Watch the first run rather than
trusting it. **Do not harden anything on Haiku** — that rule is unchanged and the evidence for it
is in "The method that worked".

**Not yet exercised by a live run** (all three are 2026-08-31 changes):
1. **The conditional Lane-12 cap.** The first Lane-12 posting through Phase B is the test. It must
   state the cap decision in `Notes` *both ways* — lifted or applied. The evaluator agent has been
   told; nothing has checked that it does it.
2. **The banded `Comp_Flag` token** (`Below floor (VETO_LINE-150K)`). No live row carries one yet.
3. **The three-value `Role_Type`.** Newly declared controlled; the 16 legacy one-offs stay.

**Also still unrun, and older:** Phase E's fetch path. `select` has never had an eligible row to
hand `fetch-jds.js`, so the live fetch half has never executed. Watch it the first time it does.

**Two auths expire and fail independently.** `az login` for `fabric-pull-actions.py`, and the
LinkedIn session at `~/.li-auth/storageState.json` for every Chromium script
(`node scripts/save-auth.js` to refresh). Neither failure is subtle, but they are separate.

**Every self-test passes as of 2026-08-31:** `recall-audit.py`, `rubric-learn.py`,
`stale-sweep.py`, `triage-match.py`, and `update-linkedin-message-log.js`. Run them first if
anything looks wrong — they are faster than reasoning about the code.

### How fast the instruction set grows, and how to tell normal cost from bloat

Measured 2026-08-31 from the dated copies in `backups/` (there is no git here, so those backups
are the only history — do not clear them out).

| date | whole instruction set |
|---|---|
| 2026-08-10 | 1,159 lines |
| 2026-08-25 | 2,197 |
| 2026-08-26 | 2,542 — split into `instructions/` here |
| 2026-08-31 | 3,397 |

That is **~86 lines/day** over the first stretch and **~171/day** over the second. It is
accelerating, and at a glance that reads as a problem.

**It is not, and the reason matters: every one of those days was a rule-changing session.** The
growth is this file's own method charging its price — *"a rule with its incident attached
survives; a bare rule gets re-litigated"* — so each session appends the rule **and** the evidence
that produced it. 2026-08-31 alone added 94 lines to `04` (three controlled vocabularies and an
era warning), 50 to `03` (the conditional cap, the corrected override table) and 5 to `01`.

**A session that only *runs* the process adds roughly zero lines.** A Phase B run appends rows to
`JD_Evaluation_Log.csv`, not lines to `instructions/`. So:

> **Line count is the wrong variable to watch. The question is whether the instruction set grows
> during a stretch of pure running.** If it does, that is real bloat and worth a pass. If it only
> grows on sessions that change rules, it is the method working and the lines are load-bearing.

**Do not "slim" the instruction set on line count alone.** Assessed 2026-08-31 and declined:
the 2026-08-26 split still saves the common Phase B run **1,148 lines (34%)** by skipping `05`,
`06` and `99`, which is exactly what it was built to do. And the obvious slimming move — lifting
the reasoning out of the rule files into `rubric/learning_log.md` — would recreate the precise
failure that cost four separate measurements this session: **a definition in one file and its
meaning in another, free to drift apart.** Only 6% of `03`'s lines carry a date at all; it is 886
lines because the rubric is genuinely large, not because it is padded.

**What to watch instead — duplication, not size.** Every drift found on 2026-08-31 came from one
definition living in more than one place. That check is cheap:

```
grep -c "Below veto line\|Lane-advancing\|Interview; Rejected" instructions/*.md
```

More than one file per vocabulary means it can drift again.
