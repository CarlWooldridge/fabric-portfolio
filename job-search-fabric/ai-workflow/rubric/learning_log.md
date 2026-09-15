# Rubric learning log

Every adjustment to `weights.json`, with the evidence behind it. Newest last. A proposal is only a proposal until it is promoted.

## 2026-08-26 — proposal (not applied)

Training set: 247 rows of 894. Excluded: 124 pre-window Pursue, 26 posting-status Pass, 497 blank-action.


### Measured override rates

| rule | gate | declared | measured | fired | applied anyway | rate |
|---|---|---|---|---|---|---|
| contract | G1 | review | review | 19 | 9 | 47% |
| low_comp | G2 | veto | veto | 38 | 1 | 3% |
| consulting_named | G3a | veto | veto | 55 | 1 | 2% |
| ladders | G4 | veto | veto | 27 | 0 | 0% |
| comp_floor | G2b | review | — | 0 | 0 | — |
| delivery_role | G3b | review | — | 0 | 0 | — |

### Component separation (Pursue: 31 applied vs 3 passed)

| component | applied mean | passed mean | delta |
|---|---|---|---|
| Pts_Comp | 15.6 | 14.0 | +1.6 |
| Pts_Skills | 16.77 | 15.33 | +1.43 |
| Pts_Applicants | 0.6 | 0.0 | +0.6 |
| Pts_Deductions | -1.19 | -1.67 | +0.47 |
| Pts_Lane | 25.0 | 25.0 | +0.0 |
| Pts_Location | 12.3 | 12.33 | -0.03 |
| Pts_Scope | 13.83 | 15.0 | -1.17 |

### Proposed changes

- none; every rule sits in its declared class and no component is meaningfully inverted.

### Blocked — below the n floor (15 observations)

- Pts_Scope: applied mean 13.83 < passed mean 15.0 (delta -1.17; n=30 applied vs 3 passed) (n=3)

**Status:** proposed. Review `rubric/weights.proposed.json`, then `python3 scripts/rubric-learn.py --promote` to accept.


## 2026-08-26 — proposal (not applied)

Training set: 247 rows of 894. Excluded: 124 pre-window Pursue, 26 posting-status Pass, 497 blank-action.


### Measured override rates

| rule | gate | declared | measured | fired | applied anyway | rate |
|---|---|---|---|---|---|---|
| contract | G1 | review | review | 19 | 9 | 47% |
| low_comp | G2 | veto | veto | 38 | 1 | 3% |
| consulting_named | G3a | veto | veto | 55 | 1 | 2% |
| ladders | G4 | veto | veto | 27 | 0 | 0% |
| comp_floor | G2b | review | — | 0 | 0 | — |
| delivery_role | G3b | review | — | 0 | 0 | — |

### Component separation (Pursue: 31 applied vs 3 passed)

| component | applied mean | passed mean | delta |
|---|---|---|---|
| Pts_Comp | 15.6 | 14.0 | +1.6 |
| Pts_Skills | 16.77 | 15.33 | +1.43 |
| Pts_Applicants | 0.6 | 0.0 | +0.6 |
| Pts_Deductions | -1.19 | -1.67 | +0.47 |
| Pts_Lane | 25.0 | 25.0 | +0.0 |
| Pts_Location | 12.3 | 12.33 | -0.03 |
| Pts_Scope | 13.83 | 15.0 | -1.17 |

### Proposed changes

- none; every rule sits in its declared class and no component is meaningfully inverted.

### Blocked — below the n floor (15 observations)

- Pts_Scope: applied mean 13.83 < passed mean 15.0 (delta -1.17; n=30 applied vs 3 passed) (n=3)

**Status:** proposed. Review `rubric/weights.proposed.json`, then `python3 scripts/rubric-learn.py --promote` to accept.


## 2026-08-26 — Phase F recall sweep (post G1/G3 demotion)

Triggered by the same-day rule changes rather than the monthly cadence: the G1 `contract`
and G3 consulting demotions freed rows that had been auto-killed, and those postings are
live and closing.

**Population.** 894 rows -> 489 unacted -> 67 where a changed rule touches the row -> 31
where no surviving gate still kills it -> **13** after the expanded G3a firm list correctly
re-vetoed 18 (Company-575 x3, Company-717 x2, Company-02 x3, Company-04, Company-135, Company-697, Company-701, Company-178, Company-678,
Company-459, Company-116, Trinity, Gainwell). Top 6 re-fetched for open/closed.

**Carl's answers — 1 of 3 wanted, 1 already applied, 1 correctly rejected:**

| posting | score | status | Carl's answer |
|---|---|---|---|
| SHI International — Solutions Architect, Data Visualization | 85 | open, $160–215K | **will apply** — a real miss |
| Company-96 — Lead Engineer, Power BI | 62 | open | **already applied 2026-08-25** — a real miss, found late |
| Company-419 — Senior BI Engineer | 62 | open | Pass — IBM Cognos is a must-have |
| Company-354 — Solutions Architect, Data Visualization | 78 | closed | n/a (same role as the SHI posting) |
| Company-10 — MS Fabric Data Platform Architect | 70 | closed | n/a |

**Recall estimate: 2 of 3 live postings surfaced were wanted.** Under the old rubric both
would have stayed auto-killed and invisible. That is the demotion doing its job, and it is
also above the "three or more means something is too tight" line the Phase F protocol sets —
the pre-2026-08-26 gate configuration was too tight, which is now measured rather than argued.

### New observation — not acted on (n=1)

Metasys was killed by G1 `contract`, but Carl's actual reason was **"IBM Cognos Analytics
(must-have)"**. G10 correctly did not fire: it requires *zero* Tier-1 terms, and this JD names
Power BI and SSRS alongside Cognos.

The gap is real but unmodelled: **a named must-have competitor platform Carl does not have is
a disqualifier even when Tier-1 tools are also present.** The current rule is all-or-nothing on
Tier-1 presence and cannot express it.

Not changing anything on one observation. Watch for a second and third instance; if
"must-have <Tier-3 platform>" keeps appearing in Carl's Pass reasons, propose a deduction
(or a G10b Review trigger) with the evidence then.

## 2026-08-26 — proposal (not applied)

Training set: 251 rows of 894. Excluded: 124 pre-window Pursue, 26 posting-status Pass, 493 blank-action.


### Measured override rates

| rule | gate | declared | measured | fired | applied anyway | rate |
|---|---|---|---|---|---|---|
| contract | G1 | review | review | 19 | 9 | 47% |
| low_comp | G2 | veto | veto | 38 | 1 | 3% |
| consulting_named | G3a | veto | veto | 55 | 1 | 2% |
| ladders | G4 | veto | veto | 27 | 0 | 0% |
| comp_floor | G2b | review | — | 0 | 0 | — |
| delivery_role | G3b | review | — | 0 | 0 | — |

### Component separation (Pursue: 31 applied vs 3 passed)

| component | applied mean | passed mean | delta |
|---|---|---|---|
| Pts_Comp | 15.6 | 14.0 | +1.6 |
| Pts_Skills | 16.77 | 15.33 | +1.43 |
| Pts_Applicants | 0.6 | 0.0 | +0.6 |
| Pts_Deductions | -1.19 | -1.67 | +0.47 |
| Pts_Lane | 25.0 | 25.0 | +0.0 |
| Pts_Location | 12.3 | 12.33 | -0.03 |
| Pts_Scope | 13.83 | 15.0 | -1.17 |

### Proposed changes

- none; every rule sits in its declared class and no component is meaningfully inverted.

### Blocked — below the n floor (15 observations)

- Pts_Scope: applied mean 13.83 < passed mean 15.0 (delta -1.17; n=30 applied vs 3 passed) (n=3)

**Status:** proposed. Review `rubric/weights.proposed.json`, then `python3 scripts/rubric-learn.py --promote` to accept.


## 2026-08-26 — proposal (not applied)

Training set: 251 rows of 894. Excluded: 124 pre-window Pursue, 26 posting-status Pass, 493 blank-action.


### Measured override rates

| rule | gate | declared | measured | fired | applied anyway | rate |
|---|---|---|---|---|---|---|
| contract | G1 | review | review | 19 | 9 | 47% |
| low_comp | G2 | veto | veto | 38 | 1 | 3% |
| consulting_named | G3a | veto | veto | 55 | 1 | 2% |
| ladders | G4 | veto | veto | 27 | 0 | 0% |
| comp_floor | G2b | review | — | 0 | 0 | — |
| delivery_role | G3b | review | — | 0 | 0 | — |

### Component separation (Pursue: 31 applied vs 3 passed)

| component | applied mean | passed mean | delta |
|---|---|---|---|
| Pts_Comp | 15.6 | 14.0 | +1.6 |
| Pts_Skills | 16.77 | 15.33 | +1.43 |
| Pts_Applicants | 0.6 | 0.0 | +0.6 |
| Pts_Deductions | -1.19 | -1.67 | +0.47 |
| Pts_Lane | 25.0 | 25.0 | +0.0 |
| Pts_Location | 12.3 | 12.33 | -0.03 |
| Pts_Scope | 13.83 | 15.0 | -1.17 |

### Proposed changes

- none; every rule sits in its declared class and no component is meaningfully inverted.

### Blocked — below the n floor (15 observations)

- Pts_Scope: applied mean 13.83 < passed mean 15.0 (delta -1.17; n=30 applied vs 3 passed) (n=3)

**Status:** proposed. Review `rubric/weights.proposed.json`, then `python3 scripts/rubric-learn.py --promote` to accept.


## 2026-08-27 — proposal (not applied)

Training set: 263 rows of 921. Excluded: 124 pre-window Pursue, 28 posting-status Pass, 506 blank-action.


### Measured override rates

| rule | gate | declared | measured | fired | applied anyway | rate |
|---|---|---|---|---|---|---|
| contract | G1 | review | review | 19 | 9 | 47% |
| low_comp | G2 | veto | veto | 41 | 1 | 2% |
| consulting_named | G3a | veto | veto | 57 | 1 | 2% |
| ladders | G4 | veto | veto | 27 | 0 | 0% |
| comp_floor | G2b | review | — | 0 | 0 | — |
| delivery_role | G3b | review | — | 0 | 0 | — |

### Component separation (Pursue: 33 applied vs 11 passed)

| component | applied mean | passed mean | delta |
|---|---|---|---|
| Pts_Comp | 15.56 | 14.91 | +0.65 |
| Pts_Scope | 13.91 | 13.64 | +0.27 |
| Pts_Location | 12.28 | 12.18 | +0.1 |
| Pts_Lane | 25.0 | 25.0 | +0.0 |
| Pts_Skills | 16.75 | 16.89 | -0.14 |
| Pts_Applicants | 0.66 | 1.0 | -0.34 |
| Pts_Deductions | -1.58 | 3.27 | -4.85 |

### Proposed changes

- none; every rule sits in its declared class and no component is meaningfully inverted.

### Blocked — below the n floor (15 observations)

- Pts_Deductions: applied mean -1.58 < passed mean 3.27 (delta -4.85; n=33 applied vs 11 passed) (n=11)

**Status:** proposed. Review `rubric/weights.proposed.json`, then `python3 scripts/rubric-learn.py --promote` to accept.



## 2026-08-28 — Phase F recall audit

Window: 30 days (2026-07-29 to 2026-08-28). 22 row(s) selected, 22 answered, 0 left unanswered, 0 closed and out of the ratio.

**Recall estimate: 5 of 22 audited rows were wanted.**


Split by bucket — **these do not pool**:

- **Theme shortlist: 5 of 7.** Rows chosen because they match a rule Carl had already stated, so a high rate is expected. This measures what that rule is worth, not recall.
- **Random control: 0 of 15.** Drawn at random from everything else. **This is the recall estimate** — the only figure here that generalizes to the rows nobody read.

Zero flags in the control: no unnamed theme is visible in this window at n=15. That is weak evidence, not proof — 15 rows cannot rule out a pattern that affects a handful.

Zero flags in the control sample — the gates are calibrated for this window.

**The pooled count (5) is not the recall figure and must not be read as one.** It is carried by the theme shortlist, whose rows were selected because Carl had already said he wanted that shape.


### Rows Carl wanted

| posting | score | what killed it | answer | note |
|---|---|---|---|---|
| Company-166 — Data Architect | 69 | Lane 12: data architecture/platform bridge, not enterprise BI | wanted |  |
| Company-483 — Data Architect | 69 | data platform lane, unlisted comp | wanted |  |
| Company-567 — Data & Analytics Architect | 67 | data governance/architecture, not BI-core | wanted | applied ~2026-07-14 to an earlier posting of this same role; this is a repost |
| Company-484 — Data Architect | 64 | data platform/Fabric migration, not BI | wanted | duplicate posting of 4457166880 |
| Company-558 — Senior Marketing Analytics Manager - BI & Data Architecture | 62 | marketing/GTM analytics, not enterprise BI | wanted | resolves the handoff-vs-function-modifier conflict in favor of the handoff test |

### Rows Carl declined, with his reasoning

Kept because a *why-not* often carries more signal than a yes — a borderline he would look at under a different rule, or a fact the JD never showed.

| posting | score | what killed it | note |
|---|---|---|---|
| Company-412 — Sr FP&A Business Systems Analyst - SAP Analytics | 69 | FP&A/SAP Analytics, not BI core | out of lane / analyst role — but Review-shaped: comp good, La Vergne on-site good, some skill alignment |
| Company-326 — Lead Finance Transformation Data Analyst | 67 | FP&A reporting, not BI core | analyst role; comp on corporate site $120-130K, below the veto floor — not visible in the JD |

### Which criterion surfaced them

- **Score band 60-69 (Skip) — the band most likely to hold a wrongly-rejected role** — 5
- **Bridge candidates (Lane 12, 65-69) Carl did not act on** — 2

**5 of the wanted rows were surfaced by the 60-69 score band, not by a gate.** That is not a gate over-firing — it is the score threshold placing roles Carl wants just under 70. The question it raises is about component weights, which is `rubric-learn.py`'s measurement, not this one. Look at what those rows have in common before moving anything.

**Status:** recorded. Nothing in the rubric changed. Full list: `scratch/recall_audit_20260828.md`.


## 2026-08-31 — proposal (not applied)

Training set: 265 rows of 922. Excluded: 124 pre-window Pursue, 28 posting-status Pass, 505 blank-action.


### Measured override rates

Applications dated before the row was evaluated are excluded — the gate had not fired yet, so they are not overrides. `uncorrected` is what this table reported before 2026-08-31; a wide gap means the backfill is doing the talking.

| rule | gate | declared | measured | fired | override | pre-dated | rate | uncorrected |
|---|---|---|---|---|---|---|---|---|
| contract | G1 | review | borderline | 19 | 2 | 7 | 11% | 47% |
| low_comp | G2 | veto | veto | 41 | 1 | 0 | 2% | 2% |
| consulting_named | G3a | veto | veto | 57 | 0 | 1 | 0% | 2% |
| ladders | G4 | veto | veto | 27 | 0 | 0 | 0% | 0% |
| comp_floor | G2b | review | — | 0 | 0 | 0 | — | — |
| delivery_role | G3b | review | — | 0 | 0 | 0 | — | — |

### Component separation (Pursue: 33 applied vs 11 passed)

| component | applied mean | passed mean | delta |
|---|---|---|---|
| Pts_Comp | 15.56 | 14.91 | +0.65 |
| Pts_Scope | 13.91 | 13.64 | +0.27 |
| Pts_Location | 12.28 | 12.18 | +0.1 |
| Pts_Lane | 25.0 | 25.0 | +0.0 |
| Pts_Skills | 16.75 | 16.89 | -0.14 |
| Pts_Applicants | 0.66 | 1.0 | -0.34 |
| Pts_Deductions | -1.58 | 3.27 | -4.85 |

### Proposed changes

- none; every rule sits in its declared class and no component is meaningfully inverted.

### Blocked — below the n floor (15 observations)

- Pts_Deductions: applied mean -1.58 < passed mean 3.27 (delta -4.85; n=33 applied vs 11 passed) (n=11)

**Status:** proposed. Review `rubric/weights.proposed.json`, then `python3 scripts/rubric-learn.py --promote` to accept.


## 2026-08-31 — proposal (not applied)

Training set: 265 rows of 922. Excluded: 124 pre-window Pursue, 28 posting-status Pass, 505 blank-action.


### Measured override rates

Applications dated before the row was evaluated are excluded — the gate had not fired yet, so they are not overrides. `uncorrected` is what this table reported before 2026-08-31; a wide gap means the backfill is doing the talking.

| rule | gate | declared | measured | fired | override | pre-dated | rate | uncorrected |
|---|---|---|---|---|---|---|---|---|
| contract | G1 | review | borderline | 19 | 2 | 7 | 11% | 47% |
| low_comp | G2 | veto | veto | 41 | 1 | 0 | 2% | 2% |
| consulting_named | G3a | veto | veto | 57 | 0 | 1 | 0% | 2% |
| ladders | G4 | veto | veto | 27 | 0 | 0 | 0% | 0% |
| comp_floor | G2b | review | — | 0 | 0 | 0 | — | — |
| delivery_role | G3b | review | — | 0 | 0 | 0 | — | — |

### Component separation (Pursue: 12 applied vs 11 passed; 21 applied and 0 passed dropped as decided before the row was evaluated)

| component | applied mean | passed mean | delta |
|---|---|---|---|
| Pts_Comp | 16.83 | 14.91 | +1.92 |
| Pts_Scope | 14.17 | 13.64 | +0.53 |
| Pts_Lane | 25.0 | 25.0 | +0.0 |
| Pts_Location | 12.0 | 12.18 | -0.18 |
| Pts_Applicants | 0.75 | 1.0 | -0.25 |
| Pts_Skills | 16.5 | 16.89 | -0.39 |
| Pts_Deductions | -2.08 | 3.27 | -5.36 |

### Proposed changes

- none; every rule sits in its declared class and no component is meaningfully inverted.

### Blocked — below the n floor (15 observations)

- Pts_Deductions: applied mean -2.08 < passed mean 3.27 (delta -5.36; n=12 applied vs 11 passed) (n=11)

**Status:** proposed. Review `rubric/weights.proposed.json`, then `python3 scripts/rubric-learn.py --promote` to accept.


## 2026-08-31 — the ordering guard, and G1 kept as `review` on other grounds

**What changed in the code.** `rubric-learn.py` now excludes applications dated before
`Date_Evaluated` from both of its measurements. `applied_before_evaluation()` was ported
verbatim from `recall-audit.py` — keep the two identical. `--self-test` added: 24 assertions,
fault-injected twice (guard disabled, and pre-dated rows moved to the other group instead of
dropped); both injections fail the suite.

**`override_rates()` — the population did not change, only the numerator.** The re-measured
uncorrected rate for `contract` is `0.47368421052631576`, byte-identical to the 2026-08-27
proposal's provenance. That is the proof this is the ordering fix and nothing else. All 7 of the
dropped `contract` rows are 2026-08-12 backfill rows acted on in June and July.

**`component_separation()` had the same hole, and it was worse.** 21 of 33 `Applied` rows in the
Pursue population were decided before the row was scored — **64% of the applied group** — against
0 of 11 `Pass` rows. The contamination was entirely one-sided, because a backfilled row is by
definition one Carl acted on. Corrected, the applied group is 12, not 33:

| component | applied mean | passed mean | delta | delta as contaminated |
|---|---|---|---|---|
| Pts_Comp | 16.83 | 14.91 | **+1.92** | +0.65 |
| Pts_Scope | 14.17 | 13.64 | +0.53 | +0.27 |
| Pts_Lane | 25.0 | 25.0 | 0.0 | 0.0 |
| Pts_Location | 12.0 | 12.18 | -0.18 | +0.10 |
| Pts_Applicants | 0.75 | 1.0 | -0.25 | -0.34 |
| Pts_Skills | 16.5 | 16.89 | -0.39 | -0.14 |
| Pts_Deductions | -2.08 | 3.27 | -5.36 | -4.85 |

**Comp separates applied from passed roughly three times as strongly as it appeared to**
(+0.65 -> +1.92), and `Pts_Location` flips sign. Neither is actionable yet: the binding n is
min(12, 11) = 11, under the floor of 15, so every component finding is now blocked. **The honest
sample is a third of what it looked like.**

**`Pts_Lane` is 25.0 on both sides — this measurement cannot see the Lane question at all.**
Every Pursue row scores full Lane; the five 69s that motivate the Lane re-weight are `Skip` rows
and never enter this population. The re-weight cannot go through `component_separation()`, and
that is a change in what the next step has to look like, not a delay.

**Decision — G1 `contract` stays `review`.** (Carl, 2026-08-31.) Its measured rate is 11%: 2
overrides of 19, borderline, and `propose()` skips borderline so the script will never revisit it
unprompted. The 45% that justified the 2026-08-26 demotion does not survive the fix. The demotion
stands on the independent evidence from that same day instead — the recall sweep re-surfaced rows
the gate had auto-killed and Carl wanted 2 of 3 (SHI International 85 at $160-215K; Company-96 62,
already applied). Recorded in `instructions/03-scoring-rubric.md`.

**Decision — same-day pairs count as overrides.** (Carl, 2026-08-31.) The only two `contract`
overrides, InterEx `4445507224` and Riana `4452713933`, both have the evaluation and the action on
the same date. He does not remember either and counts them as overrides. Counted the other way G1
measures 0% on n=19 and is veto class, so this tie-break is the entire distance between the two
classes.

**Status:** measured, recorded, nothing promoted. `rubric/weights.proposed.json` is the
2026-08-31 measurement with zero proposed changes; the contaminated 2026-08-27 proposal is kept at
`backups/weights.proposed.json.pre_ordering_fix_20260831_093046`.

## 2026-08-31 — proposal (not applied)

Training set: 265 rows of 922. Excluded: 124 pre-window Pursue, 28 posting-status Pass, 505 blank-action.


### Measured override rates

Applications dated before the row was evaluated are excluded — the gate had not fired yet, so they are not overrides. `uncorrected` is what this table reported before 2026-08-31; a wide gap means the backfill is doing the talking.

| rule | gate | declared | measured | fired | override | pre-dated | rate | uncorrected |
|---|---|---|---|---|---|---|---|---|
| contract | G1 | review | borderline | 19 | 2 | 7 | 11% | 47% |
| low_comp | G2 | veto | veto | 45 | 1 | 0 | 2% | 2% |
| consulting_named | G3a | veto | veto | 57 | 0 | 1 | 0% | 2% |
| ladders | G4 | veto | veto | 27 | 0 | 0 | 0% | 0% |
| comp_floor | G2b | review | veto | 8 | 0 | 0 | 0% | 0% |
| delivery_role | G3b | review | veto | 5 | 0 | 0 | 0% | 0% |

### Component separation (Pursue: 12 applied vs 11 passed; 21 applied and 0 passed dropped as decided before the row was evaluated)

| component | applied mean | passed mean | delta |
|---|---|---|---|
| Pts_Comp | 16.83 | 14.91 | +1.92 |
| Pts_Scope | 14.17 | 13.64 | +0.53 |
| Pts_Lane | 25.0 | 25.0 | +0.0 |
| Pts_Location | 12.0 | 12.18 | -0.18 |
| Pts_Applicants | 0.75 | 1.0 | -0.25 |
| Pts_Skills | 16.5 | 16.89 | -0.39 |
| Pts_Deductions | -2.08 | 3.27 | -5.36 |

### Proposed changes

- none; every rule sits in its declared class and no component is meaningfully inverted.

### Blocked — below the n floor (15 observations)

- comp_floor: fired 8, applied anyway 0 (0%) (n=8)
- delivery_role: fired 5, applied anyway 0 (0%) (n=5)
- Pts_Deductions: applied mean -2.08 < passed mean 3.27 (delta -5.36; n=12 applied vs 11 passed) (n=11)

### Watchlist — measured, but the machinery cannot propose for it

- **contract** (G1, borderline) — declared review, measured 11% on n=19 — between the 10% veto ceiling and the 25% review floor, so no class is supported by the number. Needs a human, not a proposal.
- **comp_floor** (G2b, thin) — declared review, measures veto at 0% but only n=8 (floor 15)
- **delivery_role** (G3b, thin) — declared review, measures veto at 0% but only n=5 (floor 15)

**Status:** proposed. Review `rubric/weights.proposed.json`, then `python3 scripts/rubric-learn.py --promote` to accept.


## 2026-08-31 — proposal (not applied)

Training set: 265 rows of 922. Excluded: 124 pre-window Pursue, 28 posting-status Pass, 505 blank-action.


### Measured override rates

Applications dated before the row was evaluated are excluded — the gate had not fired yet, so they are not overrides. `uncorrected` is what this table reported before 2026-08-31; a wide gap means the backfill is doing the talking.

`acted` is how many of the fired rows Carl has decided on at all. A 0% override rate over rows he never touched is an absence of evidence, not agreement.

| rule | gate | declared | measured | fired | acted | override | pre-dated | rate | uncorrected |
|---|---|---|---|---|---|---|---|---|---|
| contract | G1 | review | borderline | 19 | 13 | 2 | 7 | 11% | 47% |
| low_comp | G2 | veto | veto | 45 | 9 | 1 | 0 | 2% | 2% |
| consulting_named | G3a | veto | veto | 57 | 4 | 0 | 1 | 0% | 2% |
| ladders | G4 | veto | veto | 27 | 1 | 0 | 0 | 0% | 0% |
| comp_floor | G2b | review | veto | 8 | 1 | 0 | 0 | 0% | 0% |
| delivery_role | G3b | review | veto | 5 | 0 | 0 | 0 | 0% | 0% |

### Component separation (Pursue: 12 applied vs 11 passed; 21 applied and 0 passed dropped as decided before the row was evaluated)

| component | applied mean | passed mean | delta |
|---|---|---|---|
| Pts_Comp | 16.83 | 14.91 | +1.92 |
| Pts_Scope | 14.17 | 13.64 | +0.53 |
| Pts_Lane | 25.0 | 25.0 | +0.0 |
| Pts_Location | 12.0 | 12.18 | -0.18 |
| Pts_Applicants | 0.75 | 1.0 | -0.25 |
| Pts_Skills | 16.5 | 16.89 | -0.39 |
| Pts_Deductions | -2.08 | 3.27 | -5.36 |

### Proposed changes

- none; every rule sits in its declared class and no component is meaningfully inverted.

### Blocked — below the n floor (15 observations)

- comp_floor: fired 8, applied anyway 0 (0%) (n=8)
- delivery_role: fired 5, applied anyway 0 (0%) (n=5)
- Pts_Deductions: applied mean -2.08 < passed mean 3.27 (delta -5.36; n=12 applied vs 11 passed) (n=11)

### Watchlist — measured, but the machinery cannot propose for it

- **contract** (G1, borderline) — declared review, measured 11% on n=19 — between the 10% veto ceiling and the 25% review floor, so no class is supported by the number. Needs a human, not a proposal.
- **comp_floor** (G2b, thin) — declared review, measures veto at 0% but only n=8 (floor 15); only 1 of them has he acted on at all
- **delivery_role** (G3b, thin) — declared review, measures veto at 0% but only n=5 (floor 15); and Carl has acted on NONE of them, so the rate means he has never looked, not that he agreed

**Status:** proposed. Review `rubric/weights.proposed.json`, then `python3 scripts/rubric-learn.py --promote` to accept.


## 2026-08-31 — proposal (not applied)

Training set: 265 rows of 922. Excluded: 124 pre-window Pursue, 28 posting-status Pass, 505 blank-action.


### Measured override rates

Applications dated before the row was evaluated are excluded — the gate had not fired yet, so they are not overrides. `uncorrected` is what this table reported before 2026-08-31; a wide gap means the backfill is doing the talking.

`acted` is how many of the fired rows Carl has decided on at all. A 0% override rate over rows he never touched is an absence of evidence, not agreement.

| rule | gate | declared | measured | fired | acted | override | pre-dated | rate | uncorrected |
|---|---|---|---|---|---|---|---|---|---|
| contract | G1 | review | borderline | 19 | 13 | 2 | 7 | 11% | 47% |
| low_comp | G2 | veto | veto | 45 | 9 | 1 | 0 | 2% | 2% |
| consulting_named | G3a | veto | veto | 57 | 4 | 0 | 1 | 0% | 2% |
| ladders | G4 | veto | veto | 27 | 1 | 0 | 0 | 0% | 0% |
| comp_floor | G2b | review | veto | 8 | 1 | 0 | 0 | 0% | 0% |
| delivery_role | G3b | review | veto | 5 | 0 | 0 | 0 | 0% | 0% |

### Component separation (Pursue: 12 applied vs 11 passed; 21 applied and 0 passed dropped as decided before the row was evaluated)

| component | applied mean | passed mean | delta |
|---|---|---|---|
| Pts_Comp | 16.83 | 14.91 | +1.92 |
| Pts_Scope | 14.17 | 13.64 | +0.53 |
| Pts_Lane | 25.0 | 25.0 | +0.0 |
| Pts_Location | 12.0 | 12.18 | -0.18 |
| Pts_Applicants | 0.75 | 1.0 | -0.25 |
| Pts_Skills | 16.5 | 16.89 | -0.39 |
| Pts_Deductions | -2.08 | 3.27 | -5.36 |

### Proposed changes

- none; every rule sits in its declared class and no component is meaningfully inverted.

### Blocked — below the n floor (15 observations)

- comp_floor: fired 8, applied anyway 0 (0%) (n=8)
- delivery_role: fired 5, applied anyway 0 (0%) (n=5)
- Pts_Deductions: applied mean -2.08 < passed mean 3.27 (delta -5.36; n=12 applied vs 11 passed) (n=11)

### Watchlist — measured, but the machinery cannot propose for it

- **contract** (G1, borderline) — declared review, measured 11% on n=19 — between the 10% veto ceiling and the 25% review floor, so no class is supported by the number. Needs a human, not a proposal.
- **comp_floor** (G2b, thin) — declared review, measures veto at 0% but only n=8 (floor 15); only 1 of them has he acted on at all
- **delivery_role** (G3b, thin) — declared review, measures veto at 0% but only n=5 (floor 15); and Carl has acted on NONE of them, so the rate means he has never looked, not that he agreed

**Status:** proposed. Review `rubric/weights.proposed.json`, then `python3 scripts/rubric-learn.py --promote` to accept.


## 2026-08-31 — G2b and G3b measured for the first time; watchlist added

**Why they read n=0.** Neither pattern was wrong by a little. G2b's `match_reason` was
`below comp floor`, a word order that appears **nowhere** in 922 rows — the log writes
`comp below floor`, `comp at floor`, `sub-target comp`, `Comp gap`. G3b's was the rubric's
canonical token `consulting delivery role`, which the log has never once used; it writes
`consulting delivery pattern`, `consulting-firm delivery pattern`, `consulting delivery, <detail>`.
Both were written from memory rather than from the data — the same failure as the 2026-08-27
sender-list incident, in a different file.

**G2 was also short by 4 rows.** `comp below floor` and `comp too low` are used for postings
under the VETO_LINE — cross-checked against `Comp_Flag` on every row — and contain no
literal "low comp", so the veto's denominator missed them. 41 -> 45 fired; the rate is unchanged
at 2%.

**Patterns are now derived from the log and cross-checked, not guessed:**

| gate | pattern | qualifiers |
|---|---|---|
| G2 | `\blow comp\b\|comp below floor\|comp too low` | — |
| G2b | `sub-?target comp\|comp at floor\|\bcomp gap\b` | excludes G2's reasons; `Comp_Flag` must agree |
| G3b | `consulting[\s-]*(firm[\s-]*)?delivery` | G3a outranks |

Two qualifiers are new and both are load-bearing, asserted by removal in `--self-test`:
`requires_field_match` drops two rows reading `sub-target comp` whose `Comp_Flag` is `None`
(the Reason and the field contradict each other), and `excludes_reason_match` sends a row
carrying both a G2 and a G2b phrase to G2, matching the documented precedence. The
`if name == "contract"` hardcode became a declared `outranked_by_employer_list` — G3b never had
that protection and now does. The self-test caught the regression when the hardcode came out.

**The result, and the reason not to act on it yet:**

| gate | fired | acted on | overrides | rate | class |
|---|---|---|---|---|---|
| G2b `comp_floor` | 8 | **1** | 0 | 0% | measures veto, declared review |
| G3b `delivery_role` | 5 | **0** | 0 | 0% | measures veto, declared review |

**Both compensable gates measure at veto-class rates — and both are meaningless numbers.**
12 of the 13 rows have a blank `Carls_Action`. A 0% override rate over rows Carl has never
looked at is an absence of evidence, not agreement. Both are under the n floor and neither
produces a proposal.

**This matters more than it looks, because those two gates plus G1 are the entire `Review`
verdict.** `Review` fires when a compensable gate fired and no veto fired. G1 measures
borderline, G2b and G3b measure veto-class on no evidence. Nothing currently measures as
compensable, which is consistent with `Verdict = "Review"` never once having appeared in the
log. **The 13 rows above are the population Phase F should be asking Carl about** — they are
exactly the rows the Review verdict was invented to surface, and none has been put to him.

**`watchlist()` added, because "no proposed changes" was hiding all of this.** `propose()` only
ever emits a rule whose measured class differs from its declared class *and* clears the n floor;
everything else produced no output at all. Three ways a rule went silent — `borderline` (no class
is supported by the number), `unmeasured` (fired zero times, which usually means the pattern is
wrong, not that the rule is unused), and `thin` (disagrees with its declared class under the n
floor). All three now print in the run summary, the learning log and the proposal provenance. The
`acted` column was added alongside for the same reason.

**Nothing promoted.** `weights.json` changed only in `match_reason` and the new qualifiers —
measurement plumbing, no score or verdict is affected. Previous file kept at
`backups/weights.json.pre_gatefix_*`.

## 2026-08-31 — Lane-12 cap made conditional on the handoff test (option C)

**Carl's decision**, from three options put to him. Not a re-weight: `weights.json` holds only
`lane.max = 25`, and the 25/12/0 tiers and the 69 cap live entirely in `03-scoring-rubric.md`
prose. `rubric-learn.py` proposes a rule's veto/review class and inverted components and nothing
else, so this could not go through propose/promote — it is a rubric edit with a backtest.
`component_separation()` cannot see the question either: every Pursue row is Lane 25, so the
column reads 25.0 vs 25.0, and every capped row is a Skip outside that population.

**The rule.** A Lane-12 role is capped at 69 **only if it fails the handoff test**. Pass it and
there is no cap; the score stands on its own total. Lane still scores 12 either way. No new
judgment step — the handoff test already runs before Lane is scored and already has to be
recorded in `Notes`.

**Backtest, all 22 rows currently sitting at exactly 69:**

| outcome | rows |
|---|---|
| cap lifts, becomes Pursue | Company-576 (capped from 84), Company-324 Lead Data Architect (75), Company-316 (75), Arista (72), Vantage, Company-702 — **all six are applications** |
| cap holds, stays 69/Skip | Company-64 Business Analytics Manager ×4 (75), Company-591 Decision Scientist (72), Company-478 (75), Yusen Senior Financial Analyst, Company-693, Company-303 |
| **unaffected — never capped** | **Company-176 (FP&A Systems & AI Enablement, applied) and Phibro (Data Architect, wanted)**, plus Careismatic and Company-165 |

**The two that do not move are the honest limit of this option.** Company-176 and Phibro score 69 on
their own totals — their `Notes` record no cap — so it is the Lane *score* holding them under 70,
not the ceiling. Option A (reclassifying handoff-shaped roles to Lane 25) is the answer to that
shape, and this rule is not. **If a second sweep turns up more of it, reopen the question.**

**Data-quality finding: `Is_Capped_Score` disagrees with `Notes` on 4 of the 22.** Company-693,
Company-303, Vantage and Company-702 all state a cap in `Notes` and carry `Is_Capped_Score = False`.
`Score_Raw` would settle it and is blank on 894 of 922 rows (it only populates from 2026-08-26).
The backtest above was built from `Notes`, which the rubric requires the cap to be written into.
**Read `Notes`, not the flag.**

**Also 2026-08-31:** the 13 rows newly surfaced by the corrected G2b/G3b patterns are **held for
the next Phase F run** at Carl's direction, not asked now.

## 2026-08-31 — proposal (not applied)

Training set: 265 rows of 922. Excluded: 124 pre-window Pursue, 28 posting-status Pass, 505 blank-action.


### Measured override rates

Applications dated before the row was evaluated are excluded — the gate had not fired yet, so they are not overrides. `uncorrected` is what this table reported before 2026-08-31; a wide gap means the backfill is doing the talking.

`acted` is how many of the fired rows Carl has decided on at all. A 0% override rate over rows he never touched is an absence of evidence, not agreement.

| rule | gate | declared | measured | fired | acted | override | pre-dated | rate | uncorrected |
|---|---|---|---|---|---|---|---|---|---|
| contract | G1 | review | borderline | 19 | 13 | 2 | 7 | 11% | 47% |
| low_comp | G2 | veto | veto | 45 | 9 | 1 | 0 | 2% | 2% |
| consulting_named | G3a | veto | veto | 57 | 4 | 0 | 1 | 0% | 2% |
| ladders | G4 | veto | veto | 27 | 1 | 0 | 0 | 0% | 0% |
| comp_floor | G2b | review | veto | 7 | 1 | 0 | 0 | 0% | 0% |
| delivery_role | G3b | review | veto | 5 | 0 | 0 | 0 | 0% | 0% |

### Component separation (Pursue: 12 applied vs 11 passed; 21 applied and 0 passed dropped as decided before the row was evaluated)

| component | applied mean | passed mean | delta |
|---|---|---|---|
| Pts_Comp | 16.83 | 14.91 | +1.92 |
| Pts_Scope | 14.17 | 13.64 | +0.53 |
| Pts_Lane | 25.0 | 25.0 | +0.0 |
| Pts_Location | 12.0 | 12.18 | -0.18 |
| Pts_Applicants | 0.75 | 1.0 | -0.25 |
| Pts_Skills | 16.5 | 16.89 | -0.39 |
| Pts_Deductions | -2.08 | 3.27 | -5.36 |

### Proposed changes

- none; every rule sits in its declared class and no component is meaningfully inverted.

### Blocked — below the n floor (15 observations)

- comp_floor: fired 7, applied anyway 0 (0%) (n=7)
- delivery_role: fired 5, applied anyway 0 (0%) (n=5)
- Pts_Deductions: applied mean -2.08 < passed mean 3.27 (delta -5.36; n=12 applied vs 11 passed) (n=11)

### Watchlist — measured, but the machinery cannot propose for it

- **contract** (G1, borderline) — declared review, measured 11% on n=19 — between the 10% veto ceiling and the 25% review floor, so no class is supported by the number. Needs a human, not a proposal.
- **comp_floor** (G2b, thin) — declared review, measures veto at 0% but only n=7 (floor 15); only 1 of them has he acted on at all
- **delivery_role** (G3b, thin) — declared review, measures veto at 0% but only n=5 (floor 15); and Carl has acted on NONE of them, so the rate means he has never looked, not that he agreed

**Status:** proposed. Review `rubric/weights.proposed.json`, then `python3 scripts/rubric-learn.py --promote` to accept.


## 2026-08-31 — `Comp_Flag` did not disagree with its spec; it changed meaning under the rows

**The finding was misdiagnosed when it was raised earlier the same day.** It looked like the log
contradicting `01-intake-and-fetch.md` — 47 rows flagged `Below floor` for postings under VETO_LINE,
which that file defines as `Below veto line`. Checked against `Date_Evaluated`, every one of those
rows was evaluated **before 2026-08-26**, the day the comp floor was raised from VETO_LINE to FLOOR.
They were correct when written.

**Both band names shifted by exactly one band, and nothing on a row records which scheme it
was written under:**

| string | before 2026-08-26 | on/after 2026-08-26 |
|---|---|---|
| `Below floor` | under VETO_LINE | VETO_LINE–FLOOR |
| `Sub-target` | VETO_LINE–FLOOR | FLOOR–TARGET |

47 rows carry `Below floor`, 77 carry `Sub-target`; all but five are pre-boundary. Only 3 rows
have ever used `Below veto line`, all post-boundary.

**This had already produced a wrong number, in code written earlier today.** G2b's new
`requires_field_match` used one pattern over the whole log and counted Company-140 `4400129341` —
`Below floor`, evaluated 2026-08-03, top of range **exactly VETO_LINE** — as a VETO_LINE–FLOOR row.
Under its own era that string means *under* the floor, and the row belongs to G2. G2b: 8 -> 7.

**Fixed three ways, none of them a data migration:**

1. **Forward:** `Comp_Flag`'s canonical token now carries its own band — `Below floor
   (VETO_LINE-150K)`, `Sub-target (FLOOR-175K)`, `Below veto line (<VETO_LINE)`, `None (>=TARGET)`. Once
   every live row carries the band in the string, the era stops mattering.
2. **Documented:** the era table above is in `01-intake-and-fetch.md` as a warning beside the
   `Comp_Flag` rule, cross-referenced from the comp component in `03-scoring-rubric.md`.
3. **In code:** `field_matches()` in `rubric-learn.py` takes `boundary_date` /
   `pattern_before` / `pattern_after`, so a rule reads each row under the rules in force when it
   was evaluated. G2b declares it. Six self-test cases including both boundary directions, the
   boundary date itself, and an undated row; fault-injected by collapsing the split, which fails
   three assertions.

**No rows were rewritten, deliberately.** Each is correct under its own era, `Comp_Flag` is a
judgment field that `01-intake-and-fetch.md` forbids overwriting, and rewriting it to make history
look tidy is exactly what the 2026-08-26 "flag, never backfill" incident is about — it would
destroy the ability to see what the evaluator actually concluded.

**The general lesson, which is new to this log:** a rule change that alters what an existing
column's values *mean*, without changing the values or adding an era marker, is silent and
retroactive. The 2026-08-26 floor revision was recorded carefully as a scoring change and nothing
noticed it had also re-pointed 124 existing rows. **When a threshold moves, ask what already-
written values were named after the old threshold.**

## 2026-08-31 — proposal (not applied)

Training set: 265 rows of 922. Excluded: 124 pre-window Pursue, 28 posting-status Pass, 505 blank-action.


### Measured override rates

Applications dated before the row was evaluated are excluded — the gate had not fired yet, so they are not overrides. `uncorrected` is what this table reported before 2026-08-31; a wide gap means the backfill is doing the talking.

`acted` is how many of the fired rows Carl has decided on at all. A 0% override rate over rows he never touched is an absence of evidence, not agreement.

| rule | gate | declared | measured | fired | acted | override | pre-dated | rate | uncorrected |
|---|---|---|---|---|---|---|---|---|---|
| contract | G1 | review | borderline | 19 | 13 | 2 | 7 | 11% | 47% |
| low_comp | G2 | veto | veto | 45 | 9 | 1 | 0 | 2% | 2% |
| consulting_named | G3a | veto | veto | 57 | 4 | 0 | 1 | 0% | 2% |
| ladders | G4 | veto | veto | 27 | 1 | 0 | 0 | 0% | 0% |
| comp_floor | G2b | review | veto | 7 | 1 | 0 | 0 | 0% | 0% |
| delivery_role | G3b | review | veto | 5 | 0 | 0 | 0 | 0% | 0% |

### Component separation (Pursue: 12 applied vs 11 passed; 21 applied and 0 passed dropped as decided before the row was evaluated)

| component | applied mean | passed mean | delta |
|---|---|---|---|
| Pts_Comp | 16.83 | 14.91 | +1.92 |
| Pts_Scope | 14.17 | 13.64 | +0.53 |
| Pts_Lane | 25.0 | 25.0 | +0.0 |
| Pts_Location | 12.0 | 12.18 | -0.18 |
| Pts_Applicants | 0.75 | 1.0 | -0.25 |
| Pts_Skills | 16.5 | 16.89 | -0.39 |
| Pts_Deductions | -2.08 | 3.27 | -5.36 |

### Proposed changes

- none; every rule sits in its declared class and no component is meaningfully inverted.

### Blocked — below the n floor (15 observations)

- comp_floor: fired 7, applied anyway 0 (0%) (n=7)
- delivery_role: fired 5, applied anyway 0 (0%) (n=5)
- Pts_Deductions: applied mean -2.08 < passed mean 3.27 (delta -5.36; n=12 applied vs 11 passed) (n=11)

### Watchlist — measured, but the machinery cannot propose for it

- **contract** (G1, borderline) — declared review, measured 11% on n=19 — between the 10% veto ceiling and the 25% review floor, so no class is supported by the number. Needs a human, not a proposal.
- **comp_floor** (G2b, thin) — declared review, measures veto at 0% but only n=7 (floor 15); only 1 of them has he acted on at all
- **delivery_role** (G3b, thin) — declared review, measures veto at 0% but only n=5 (floor 15); and Carl has acted on NONE of them, so the rate means he has never looked, not that he agreed

**Status:** proposed. Review `rubric/weights.proposed.json`, then `python3 scripts/rubric-learn.py --promote` to accept.


## 2026-08-31 — sweep: which other labels were named after a threshold that moved?

Prompted by the `Comp_Flag` finding above. The question asked of every label field and every
scored component: **is its meaning defined relative to a rule that has since changed, with no
marker on the row saying which version applies?** Six candidates found, four real.

| field | what moved | when | rows affected | status |
|---|---|---|---|---|
| `Comp_Flag` | floor VETO_LINE → FLOOR; both band names shifted one band | 08-26 | 124 | fixed earlier today |
| `Verdict` = `Pursue` | the 50–69 Pursue band was deleted | 08-10 | 124 | **already guarded** |
| `Verdict` = `Pass` | G1 demoted to Review, G3 split into G3a/G3b | 08-26 | **22** | **open** |
| `Pts_Comp` | every comp band shifted with the floor | 08-26 | 775 pre / 23 post | guarded now |
| `Pts_Skills` / `Pts_Perks` | perks removed, its 5 pts moved to Skills (max 15 → 20) | 08-10 | 276 pre / 516 post | guarded now |
| `Role_Type` = `Bridge` | the Lane-12 cap became conditional | **08-31** | all Lane-12 | fixed today |
| `Applicant_Volume`, `Work_Type`, `Employment_Type`, `Outcome` | — | — | — | clean |

**The project had already hit this once and fixed it without naming it.**
`training_set()` drops `Verdict == "Pursue"` rows evaluated before `window_start`, recorded in
`weights.json` as *"pre-window Pursue (deleted 50-69 band)"* — 124 rows. That is exactly this
defect, correctly handled, in 2026-08-10's instance. The fix was never generalized, so 2026-08-26
walked straight into it again with `Comp_Flag`, and today's cap change made a third instance
before the sweep caught it.

**`Verdict = "Pass"` is the one still open.** 22 rows evaluated before 2026-08-26 carry `Pass` for
a `contract` or `consulting delivery` reason — both of which produce `Review` now, not `Pass`.
Any count of "how often does a veto fire" that pools the log is counting 22 rows under a rule
that no longer exists. Not fixed here: it needs a decision about whether `Review`'s population is
measured from the current rules or from the rules in force at evaluation, and that is Carl's call.

**`Pts_Comp` is the live risk, not a historical one.** Pre-2026-08-26, `Pts_Comp = 20` means
≥FLOOR (368 rows); after, it means ≥TARGET (8 rows). The new VETO_LINE–150K band scores 4 and appears on
exactly one row. `component_separation()` compares `Pts_Comp` means directly and reported it as
the **strongest** discriminator today (+1.92). **Checked: today's 23 compared rows all fall
between 2026-08-10 and 2026-08-25 — one era, no contamination.** That is luck rather than design:
`window_start` happens to sit on the 08-10 boundary, and nothing protected the 08-26 one. As
post-08-26 rows get actioned, that comparison starts pooling two comp scales.

**Guard added: `SCALE_BOUNDARIES` and `boundary_warnings()` in `rubric-learn.py`.** The two known
dates and the fields each one re-pointed are declared in one table. Any measurement whose
population straddles a boundary for a field it is comparing prints a warning in the run summary
and a blockquote in this log, naming the date, the split, and what changed. Seven self-test cases
— clean before, clean after, straddling with an affected column, straddling with an unaffected
one, both boundaries at once, and a row exactly on a boundary counting as after. Fault-injected by
making the check unconditional-false; two assertions fail. **The live run prints nothing, which is
the correct answer today and is now verified by the code rather than by hand.**

**`Role_Type = "Bridge"` was ambiguous for about four hours, by my own change.** Making the
Lane-12 cap conditional meant `Bridge` covers both a capped role and one whose cap was lifted,
with nothing distinguishing them. Fixed in `04-log-and-write-discipline.md`: `Role_Type` marks the
Lane score and nothing else, and the cap decision is read from `Notes`, which the rubric already
requires to state it either way. **A rule change that alters what an existing label implies is the
same defect whether it happened in August or this afternoon.**

## 2026-08-31 — proposal (not applied)

Training set: 265 rows of 922. Excluded: 124 pre-window Pursue, 28 posting-status Pass, 505 blank-action.


### Measured override rates

Applications dated before the row was evaluated are excluded — the gate had not fired yet, so they are not overrides. `uncorrected` is what this table reported before 2026-08-31; a wide gap means the backfill is doing the talking.

`acted` is how many of the fired rows Carl has decided on at all. A 0% override rate over rows he never touched is an absence of evidence, not agreement.

| rule | gate | declared | measured | fired | acted | override | pre-dated | rate | uncorrected |
|---|---|---|---|---|---|---|---|---|---|
| contract | G1 | review | borderline | 19 | 13 | 2 | 7 | 11% | 47% |
| low_comp | G2 | veto | veto | 45 | 9 | 1 | 0 | 2% | 2% |
| consulting_named | G3a | veto | veto | 57 | 4 | 0 | 1 | 0% | 2% |
| ladders | G4 | veto | veto | 27 | 1 | 0 | 0 | 0% | 0% |
| comp_floor | G2b | review | veto | 7 | 1 | 0 | 0 | 0% | 0% |
| delivery_role | G3b | review | veto | 5 | 0 | 0 | 0 | 0% | 0% |

### Component separation (Pursue: 12 applied vs 11 passed; 21 applied and 0 passed dropped as decided before the row was evaluated)

| component | applied mean | passed mean | delta |
|---|---|---|---|
| Pts_Comp | 16.83 | 14.91 | +1.92 |
| Pts_Scope | 14.17 | 13.64 | +0.53 |
| Pts_Lane | 25.0 | 25.0 | +0.0 |
| Pts_Location | 12.0 | 12.18 | -0.18 |
| Pts_Applicants | 0.75 | 1.0 | -0.25 |
| Pts_Skills | 16.5 | 16.89 | -0.39 |
| Pts_Deductions | -2.08 | 3.27 | -5.36 |

### Proposed changes

- none; every rule sits in its declared class and no component is meaningfully inverted.

### Blocked — below the n floor (15 observations)

- comp_floor: fired 7, applied anyway 0 (0%) (n=7)
- delivery_role: fired 5, applied anyway 0 (0%) (n=5)
- Pts_Deductions: applied mean -2.08 < passed mean 3.27 (delta -5.36; n=12 applied vs 11 passed) (n=11)

### Stored `Verdict` vs current rules — 13 row(s)

Measured under **current rules** (Carl, 2026-08-31). These rows are stored as `Pass` because a veto fired when they were evaluated; under today's classes no veto fires and a compensable gate does, so they count as `Review` in every measurement here. **The stored column is not rewritten** — each row was correct when written.

| Job_ID | evaluated | company | reason |
|---|---|---|---|
| 202607271423 | 2026-07-28 | Company-205 (staffing agency | contract |
| 4446945006 | 2026-08-10 | Company-10 (end-client u | contract |
| 202608111806 | 2026-08-12 | Company-496 | contract |
| 4445507224 | 2026-08-12 | Company-344 (anonymous end | contract |
| 4434684371 | 2026-08-12 | Company-542 (anonymous end c | contract |
| 4428532689 | 2026-08-12 | Company-197 (anonymous/unclear en | contract |
| 4435231918 | 2026-08-12 | Company-570 | contract |
| 4415288536 | 2026-08-12 | Company-344 (anonymous end | contract |
| 4416680741 | 2026-08-12 | Company-619 (anonymous end | contract |
| 4188980088 | 2026-08-12 | Company-240 (direct | contract |
| 4452713933 | 2026-08-14 | Company-537 | contract |
| 4453245128 | 2026-08-15 | Company-660 | contract |
| 4456212997 | 2026-08-24 | Company-419 | contract; IBM Cognos listed as must-have |

### Watchlist — measured, but the machinery cannot propose for it

- **contract** (G1, borderline) — declared review, measured 11% on n=19 — between the 10% veto ceiling and the 25% review floor, so no class is supported by the number. Needs a human, not a proposal.
- **comp_floor** (G2b, thin) — declared review, measures veto at 0% but only n=7 (floor 15); only 1 of them has he acted on at all
- **delivery_role** (G3b, thin) — declared review, measures veto at 0% but only n=5 (floor 15); and Carl has acted on NONE of them, so the rate means he has never looked, not that he agreed

**Status:** proposed. Review `rubric/weights.proposed.json`, then `python3 scripts/rubric-learn.py --promote` to accept.


## 2026-08-31 — measurement basis settled: current rules

**Carl's decision.** When a rule change means a stored `Verdict` no longer matches what the rules
would produce today, **measurement uses the current rules**. The stored column keeps saying what
was true when the row was evaluated and is never rewritten.

**Implemented as a re-derivation, not a correction.** `current_verdict_class()` answers "does this
row fire a veto-class or review-class gate?" from the row's `Reason` against the classes currently
in `weights.json`. The stored `Verdict` string is not consulted — a self-test asserts that the same
row returns the same answer whether it is stored as `Pass` or `Skip`. `stale_verdicts()` reports
the rows where the two disagree, every run.

**Why not rewrite the column.** `Verdict` is a judgment field `04-log-and-write-discipline.md`
forbids overwriting; each of those rows was correct under the rules in force when it was written;
and rewriting would destroy the ability to see that the rule changed at all — the same reasoning as
"flag, never backfill" and as the `Comp_Flag` decision earlier today. Re-derive at measurement time,
every time.

**The count is 13, not the 22 reported in the sweep.** The sweep's 22 came from a bare regex over
`Reason` that ignored gate precedence. Applying the rules properly:

| dropped | why |
|---|---|
| Company-473, Company-581, Company-183, Kforce | `contract; low comp` — **G2 still vetoes** |
| Company-523, Company-02 ×2, Grey Parrot | named consulting firm — **G3a still vetoes** |
| Grey Parrot, Company-438 | posting-status rows, excluded from the population |

**All 13 are `contract` rows** (G1). G3b contributes none — its 5 rows are all stored `Skip`, never
`Pass`. Two of the 13 are the same InterEx and Riana rows that are G1's only two true overrides.

**A refactor came out of it:** `rule_fires()` was split out of `override_rates()` so the derivation
and the rate measurement share one matcher instead of keeping two that can drift — the same reason
`triage-match.py` imports `jd-dedupe.py`'s `norm()`. Nine self-test cases on the derivation,
including veto-outranks-review and G3a-outranks-G1; fault-injected by making it read the stored
`Verdict`, which fails four assertions.

**The 2026-08-26 `Verdict` scale boundary is now closed by construction** and was removed from
`SCALE_BOUNDARIES`' field list — a boundary guard is for values that cannot be re-derived
(`Pts_Comp`, `Pts_Skills`, and the 2026-08-10 `Pursue` band, which needs the original score band).
A verdict can be re-derived, so it is, on every read.

## 2026-08-31 — proposal (not applied)

Training set: 265 rows of 922. Excluded: 124 pre-window Pursue, 28 posting-status Pass, 505 blank-action.


### Measured override rates

Applications dated before the row was evaluated are excluded — the gate had not fired yet, so they are not overrides. `uncorrected` is what this table reported before 2026-08-31; a wide gap means the backfill is doing the talking.

`acted` is how many of the fired rows Carl has decided on at all. A 0% override rate over rows he never touched is an absence of evidence, not agreement.

| rule | gate | declared | measured | fired | acted | override | pre-dated | rate | uncorrected |
|---|---|---|---|---|---|---|---|---|---|
| contract | G1 | review | borderline | 19 | 13 | 2 | 7 | 11% | 47% |
| low_comp | G2 | veto | veto | 45 | 9 | 1 | 0 | 2% | 2% |
| consulting_named | G3a | veto | veto | 57 | 4 | 0 | 1 | 0% | 2% |
| ladders | G4 | veto | veto | 27 | 1 | 0 | 0 | 0% | 0% |
| comp_floor | G2b | review | veto | 7 | 1 | 0 | 0 | 0% | 0% |
| delivery_role | G3b | review | veto | 5 | 0 | 0 | 0 | 0% | 0% |

### Component separation (Pursue: 12 applied vs 11 passed; 21 applied and 0 passed dropped as decided before the row was evaluated)

| component | applied mean | passed mean | delta |
|---|---|---|---|
| Pts_Comp | 16.83 | 14.91 | +1.92 |
| Pts_Scope | 14.17 | 13.64 | +0.53 |
| Pts_Lane | 25.0 | 25.0 | +0.0 |
| Pts_Location | 12.0 | 12.18 | -0.18 |
| Pts_Applicants | 0.75 | 1.0 | -0.25 |
| Pts_Skills | 16.5 | 16.89 | -0.39 |
| Pts_Deductions | -2.08 | 3.27 | -5.36 |

### Proposed changes

- none; every rule sits in its declared class and no component is meaningfully inverted.

### Blocked — below the n floor (15 observations)

- comp_floor: fired 7, applied anyway 0 (0%) (n=7)
- delivery_role: fired 5, applied anyway 0 (0%) (n=5)
- Pts_Deductions: applied mean -2.08 < passed mean 3.27 (delta -5.36; n=12 applied vs 11 passed) (n=11)

### Stored `Verdict` vs current rules — 13 row(s)

Measured under **current rules** (Carl, 2026-08-31). These rows are stored as `Pass` because a veto fired when they were evaluated; under today's classes no veto fires and a compensable gate does, so they count as `Review` in every measurement here. **The stored column is not rewritten** — each row was correct when written.

| Job_ID | evaluated | company | reason |
|---|---|---|---|
| 202607271423 | 2026-07-28 | Company-205 (staffing agency | contract |
| 4446945006 | 2026-08-10 | Company-10 (end-client u | contract |
| 202608111806 | 2026-08-12 | Company-496 | contract |
| 4445507224 | 2026-08-12 | Company-344 (anonymous end | contract |
| 4434684371 | 2026-08-12 | Company-542 (anonymous end c | contract |
| 4428532689 | 2026-08-12 | Company-197 (anonymous/unclear en | contract |
| 4435231918 | 2026-08-12 | Company-570 | contract |
| 4415288536 | 2026-08-12 | Company-344 (anonymous end | contract |
| 4416680741 | 2026-08-12 | Company-619 (anonymous end | contract |
| 4188980088 | 2026-08-12 | Company-240 (direct | contract |
| 4452713933 | 2026-08-14 | Company-537 | contract |
| 4453245128 | 2026-08-15 | Company-660 | contract |
| 4456212997 | 2026-08-24 | Company-419 | contract; IBM Cognos listed as must-have |

### Watchlist — measured, but the machinery cannot propose for it

- **contract** (G1, borderline) — declared review, measured 11% on n=19 — between the 10% veto ceiling and the 25% review floor, so no class is supported by the number. Needs a human, not a proposal.
- **comp_floor** (G2b, thin) — declared review, measures veto at 0% but only n=7 (floor 15); only 1 of them has he acted on at all
- **delivery_role** (G3b, thin) — declared review, measures veto at 0% but only n=5 (floor 15); and Carl has acted on NONE of them, so the rate means he has never looked, not that he agreed

**Status:** proposed. Review `rubric/weights.proposed.json`, then `python3 scripts/rubric-learn.py --promote` to accept.


## 2026-08-31 — `Comp_Flag`'s vocabulary collapsed to one authoritative copy

It had been stated in four places: the recompute rule in `01-intake-and-fetch.md`, the comp
component in `03-scoring-rubric.md`, the field spec in `04-log-and-write-discipline.md`, and a
docstring in `rubric-learn.py`. **That is how the 2026-08-26 drift went unnoticed for five days** —
no single copy was wrong enough on its own to notice, and each read as if it were the definition.

**`04-log-and-write-discipline.md` is now the only copy**, chosen because it is the field spec and
already held the `Unlisted - …` half of the vocabulary that nothing else did. It carries all seven
tokens in one table, the free-text rule, the `not researched` prohibition, and the 2026-08-26 era
warning. The other three now point at it:

- `01` keeps *when* to recompute and the sanctioned-overwrite exception; the token list is gone.
- `03` keeps what each band *scores* — it never needed the tokens.
- `rubric-learn.py`'s `field_matches()` docstring keeps the mechanics of the era split and names
  `04` as the source; the era table it used to restate is gone.
- `weights.json`'s G2b `requires_field_match` keeps its patterns, since those are operational, with
  a note that they are derived **from** `04` and never the other way round.

**A structural defect fell out of the merge:** the vocabulary list in `04` had been split in two by
a paragraph inserted between list items earlier the same day, orphaning the three `Unlisted - …`
tokens from the four band tokens. Rewritten as a single table.

**The rule going in:** if this vocabulary changes, it changes in `04` and nowhere else. Stated in
the block itself, so the next person to add a token is told where the definition lives before they
add a fifth copy of it.

## 2026-08-31 — `Verdict`, `Role_Type` and `Outcome` checked for the same drift. All three had it.

Asked after `Comp_Flag` was collapsed: is any other controlled vocabulary stated in more than one
place, or stated in one place and contradicted by the data? All three fields came back positive,
in three different ways.

**`Verdict` — defined twice in the same file, and incomplete in both.** The field had two separate
bullets in `04-log-and-write-discipline.md`: the original vocabulary spec and the standing
measurement rule added earlier the same day. Merged. The list also omitted two values in live use:
`Unretrieved - needs manual pull` (3 rows, defined only in `01-intake-and-fetch.md`) and
`Not evaluated` (10 rows, **documented nowhere in the instructions at all** — it appears only as an
observation in a count in `REVAMP_PLAN.md`). Both are now in the table, with `Not evaluated` marked
historical-backfill-only. `01` now cross-references rather than defining.

**`Role_Type` — 3 documented values, 18 in the log, and it has already cost a measurement.** The
field was listed as `Lane-advancing` / `Bridge` / `Out of lane` but never declared *controlled*, so
32 rows carry variants: `Bridge (paycheck + currency, not a lane move)` (10),
`Out of lane (retrospective)` (6), `In-lane, single identifiable gap`, `Lane-adjacent`,
`Lane-advancing on scope, blocked on stack + location`, `Partial fit, lost on domain`,
`Not aligned`, and eight more. Four map to no Lane score at all.

**The cost is already on the record.** `recall-audit.py` carries a standing warning that selecting
Bridge candidates by *"whose `Role_Type` contains the word bridge"* reads **251 rows instead of
25** — a 10x miscount someone had to notice and work around. That is what an unenforced controlled
vocabulary costs, and it is the strongest argument in this log for declaring one. Now declared,
with the rule that qualifiers go in `Notes` and never in the value.

**`Outcome` — the docs forbade a value the process depends on.** `04` read *"Controlled values:
`Rejected` / `Interview`"*, as two mutually exclusive states. `05-triage-and-audits.md` already
relied on the compound `Interview; Rejected` — and cited it in the incident that justifies the
blank-gate, where a blind write of `Rejected` over a Company-416 row would have
destroyed the record that Carl interviewed. One row carries it today. The compound is now
documented as carrying information neither half does, with the rule that a later stage appends
rather than overwrites.

**No rows were rewritten in any of the three**, consistent with the standing rule set earlier
today for `Verdict` and `Comp_Flag`: each value was written in good faith under what was
documented at the time, and a rewrite erases what the evaluator concluded. Read legacy rows for
what they are; write only the controlled values from here on.

**The pattern across all four fields this session:** the drift never came from a copy being wrong.
It came from a vocabulary having no single owner — `Comp_Flag` restated in four places, `Verdict`
split across two bullets and two files, `Role_Type` documented but not enforced, `Outcome` narrower
in the spec than in the process. **A controlled vocabulary needs one home, inbound links, and the
word "controlled" actually written on it.**

## 2026-08-31 — `Role_Type` normalized: 13 of 16 written, 3 held

Carl's direction: normalize the two regular variants, leave the one-offs. Done for 13; **the
naive strip would have been wrong on 9 of the 16, and on 3 it still needs his call.**

**`Out of lane (retrospective)` — 6 rows, all normalized to `Out of lane`.** Every one has a
**blank `Pts_Lane`**: these are the 14-rejection diagnostic backfill rows, retrospectively judged
rather than component-scored, so there was no Lane value to check the label against. The base
value is unchanged and the qualifier is real information — it flags that the row never went
through the rubric — so it moved to `Notes` rather than being dropped. Five already implied it via
*"Part of the 14-rejection diagnostic batch"*; Company-695 (`4443081798`) did not, and now does.

**`Bridge (paycheck + currency, not a lane move)` — 10 rows, and the qualifier was load-bearing on
three of them.** Checked against `Pts_Lane` rather than trusted:

| Pts_Lane | rows | normalized to |
|---|---|---|
| 12 | 7 | `Bridge` — written |
| **25** | **3** | **`Lane-advancing` per the mapping — held, not written** |

Company-655 `4445863502`, Company-38 `4447164680` and Company-148 `4447535851` all
score **Lane 25** in their own component math — *"in-lane, Fabric/SQL/KQL-centered"*. Stripping the
qualifier to `Bridge` would have contradicted the row's own arithmetic. But writing
`Lane-advancing` asserts in plain English the opposite of what the evaluator wrote, on rows they
explicitly called *"not a lane move"*.

**What the qualifier was actually encoding is not a lane fact.** All three are sub-VETO_LINE
contract or third-party-recruiter roles — two are anonymous-end-client staffing. The stack is in
lane; what makes them "not a lane move" is comp and employment type, which the rubric already
handles through G1 and the comp component, and which shows in their scores (50, 70, 57 with
−10/−10 deductions). **`Role_Type` was being used for two concepts at once — lane fit, and career
significance — and only the first is what the field means.** That is the same root cause as every
other vocabulary finding this session.

**Method note.** The check that caught this was comparing the label against `Pts_Lane` instead of
against itself. A string-level normalization would have looked completely clean and quietly
mislabelled three rows. **Normalize against the thing the label is supposed to describe, not
against the label's own spelling.**

**Written with the full discipline:** reconcile, one backup per file per run
(`JD_Evaluation_Log_2026-08-31_104936.csv` and its OneDrive pair), `jd-update.py` with
`--force-judgment` (a judgment-field write, which the script refuses by default and which is
exactly the Carl-directed correction that flag exists for), independent dual write, both copies
revalidated from disk. 26 fields set on each copy, 0 skipped. Off-spec `Role_Type` rows: 32 → 19.

> **Completed 2026-08-31: the 3 held rows were set to `Lane-advancing` at Carl's direction.**
> Company-655 `4445863502`, Ancora `4447164680`, Company-148 `4447535851` — the mapping
> wins, and the "paycheck + currency, not a lane move" judgment is preserved in `Notes` on each.
> Both copies byte-identical afterwards (sha `d43b5ff7c935577b`). All 16 rows normalized; both
> qualifier strings are now **0 in `Role_Type` and 16 in `Notes`**. Off-spec `Role_Type` rows:
> **32 -> 16**, and the 16 remaining are the one-offs Carl chose to leave.
>
> **`Role_Type` still carries no way to say "in lane, but not a career move."** That judgment now
> lives only in prose. If it turns out to matter — a sweep wanting to separate a $75K in-lane
> contract from a real lane move — the answer is a separate field, not a qualifier smuggled back
> into this one. Nothing needs doing unless it comes up.
