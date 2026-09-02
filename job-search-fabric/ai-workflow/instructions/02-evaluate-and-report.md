# Evaluation, run summary, archive

*Part of the JobSearch workflow. Start at [`COWORK_INSTRUCTIONS.md`](../COWORK_INSTRUCTIONS.md) — it holds the naming convention, the run-type map, and the rules that apply everywhere.*

**When to load this file:** Load for any run that evaluates postings. Holds the hard gates (section 4.0); the scoring itself is in 03.

---

### 4. Evaluate
Apply the protocol below. Then append one row per posting to `JD_Evaluation_Log.csv`,
leaving `Carls_Action` and `Carls_Action_Date` blank.

#### 4.0 Hard gates — run these FIRST, before any scoring

These are mechanical pass/fail checks against the JD body. They are not scored components and
they are not judgment calls. Run every one of them before computing a single point. If any gate
fires, the verdict is fixed, `Reason` is set to the gate's headline, and the score is still
computed and logged for pattern-tracking — but the score no longer determines the verdict.

Run in this order. First gate to fire wins for `Verdict`; list *all* that fired in `Notes`.

| Gate | Condition | Verdict | Reason headline |
|---|---|---|---|
| G1 Contract | Contract, C2C, or fixed-term, per the body | Review | `contract` |
| G2 Comp veto | Posted/researched top of **base** range < VETO_LINE | Pass | `low comp` |
| G2b Comp floor | Posted/researched top of **base** range VETO_LINE–FLOOR | Review | `below comp floor` |
| G3a Consulting firm | Employer is on the named consulting-firm list | Pass | `consulting` |
| G3b Delivery role | Client-delivery/engagement *role shape*, any employer | Review | `consulting delivery role` |
| G4 Staffing board | Ladders, or anonymous end client + (contract or sub-target comp) | Pass | `Ladders post` / `anonymous end client` |
| G5 Employer exclusion | Company-30, Company-463, Company-59, UMG Nashville | Skip | `employer exclusion (X)` |
| G6 Industry exclusion | Cannabis, gambling/casino/sportsbook, adult, firearms, MLM, religious content, faith-based where mission alignment is a stated qualification | Skip | `industry exclusion (X)` |
| G7 Location | Not remote, and on-site/hybrid outside Nashville Metro — see the expanded detection rules in the Location hard gate section | Skip | `location gate (City, ST)` |
| G8 Lane | Lane fit scores 0 | Skip | per Skip-headline rule |
| G10 Stack absence | Zero Tier-1 and zero Tier-2 terms, AND a Tier-3 competitor platform named as **the** platform in use — see the definition below | Skip | `wrong stack (X)` |
| G11 Domain years | Explicit N-years-**in-industry** requirement ("7+ years in healthcare") — see Domain gate | Skip | `X domain gate` |
| G12 Recurring international travel | Body requires international travel on a recurring cadence | Skip | `travel requirement` |

**The comp gates read base, never total.** (Clarified 2026-08-31 at Carl's request, after an
Company-699 posting quoting `$120–140K base + 10% bonus` was scored without a stated rule.) G2 and G2b
test the top of the **posted base range**. Bonus, variable, equity and profit-sharing earn points
in the Compensation component — where the TARGET is explicitly total comp — but they never
lift a posting over a gate. A role whose base tops out at $140K is a `Review` even if a bonus
would nominally clear FLOOR, because the bonus is not the offer. Record the bonus in `Notes`
either way.

**Seven of these gates are decidable without a model, and a script now reports them.**
(Added 2026-09-01.) `scripts/gate-prepass.py` computes G2, G2b, G3a, G4, G5, G6 and G7 from
fields the intake/fetch stage has already extracted. G1, G3b, G8, G10, G11 and G12 need the body
read and stay with the evaluator, and so do the body-dependent clauses of the seven — the script
answers `review` rather than guessing, for unlisted comp, for G4's anonymous-end-client clause,
and for an industry keyword it cannot confirm.

**It does not set a `Verdict`, and is not yet wired into a run.** It reports which gates it
believes fired, for comparison against the evaluator. Diffed against the 93 rows of 2026-08-31
(`scripts/gate-prepass-selftest.py`) it reproduces every one with zero divergences and four
declared abstentions. Wiring it into the run — letting the evaluator take its answers rather than
re-deriving them — is a separate decision for Carl once the diff has stayed clean over more than
one run.

**G9 does not exist.** (2026-08-10.) A people-management gate was proposed and deliberately
rejected — explicit people-management requirement language sets **Scope 0** and applies a
**−10 deduction** instead, with no verdict override. See Scope fit. The G9 identifier is left
vacant on purpose so the G10–G12 numbering stays stable and so this decision doesn't get quietly
re-litigated. If a future run finds itself skipping a role *because* it has direct reports,
that's the rejected gate creeping back in — don't.

**Order of precedence when gates conflict:** (Revised 2026-08-26 — the old rule assumed G1–G4
were all Pass-type, which the G1/G3 demotions changed.) Rank by *class*, not by gate number:

1. **Pass-type (veto)** — G2, G3a, G4. Any one of these wins outright.
2. **Skip-type** — G5–G12.
3. **Review-type (compensable)** — G1, G2b, G3b.

A veto beats everything. A Skip-type gate beats a Review-type gate, because a posting that is
out of lane or fails the location gate is not a judgment call Carl needs to make — it is a Skip
that also happens to be a contract. `Review` is reserved for rows whose *only* disqualifier is
compensable. Within a class, the lower gate number wins the `Reason` headline; list all that
fired in `Notes` as always.

**One gate has an escape hatch:**
- **G10 (stack absence)** does not fire when the JD names no tooling at all. Absent tooling is
  unknown, not wrong; score Skills at the unknown tier and flag it.

**What "primary tooling" means for G10.** (Defined 2026-08-26 — it was previously undefined and
two runs decided it differently on similar postings.) The competitor platform has to be named as
**the platform the job actually uses**, in the requirements or the responsibilities. It is *not*
primary tooling when:

- **The posting hedges it with "or similar", "or equivalent", "such as", "e.g.", "like".**
  `"Looker (or similar BI tools)"` is a request for BI-tool fluency, and Carl's Power BI answers
  it. Read the hedge literally — the employer told you the specific tool is not the requirement.
- **It appears inside a grab-bag list** of five or more mixed tools (`"SQL, Qlik, Excel,
  QuickBase, Salesforce, etc."`). That is a survey of the environment, not a stack commitment.
- **It appears only in a "nice to have" / "bonus" / "preferred" block.**

When the gate does not fire on a hedged mention, still note the named platform in `Notes` — it is
real information about the environment even when it is not disqualifying.

**Both halves of G11 are not the same rule.** The gate fires *only* on an explicit
years-in-industry figure. Domain-artifacts-as-the-deliverable, with no years figure, is a **−15
deduction and no gate** — see the Domain gate section in `instructions/03-scoring-rubric.md`,
which is authoritative. (Corrected 2026-08-26: this table previously joined them with "or", which
would auto-Skip a BI-core role at a domain employer that the rubric only means to penalise.)

**A gate firing is not a reason to skip the rest of the evaluation.** Score every component and
show the math in `Notes` exactly as always. The gates decide the verdict; the score still records
what the role looked like, which is what makes the monthly Skip audit (Phase F) possible.

**Whenever the resulting `Verdict` is `"Skip"`** (score-driven, not a hard-override `"Pass"`),
also fill in `Reason` with a 1–5 word headline naming the single biggest thing that killed the
role — see the Skip-headline rule under `Reason` in Row format (`instructions/04-log-and-write-discipline.md`) for the synthesis method and
examples. This is the one case besides closed-postings and hard overrides where `Reason` is
populated on Claude's own evaluation run.

**Never mark a posting `Skip` without having read the full job description.** This holds even
when the verdict looks obvious from the title, the company, or a similar posting already logged.
A `Skip` is a real judgment and it needs the JD behind it — no exceptions for:

- **Title-based dismissals.** "Data Engineer," "Analytics Engineer," and "Data Scientist" are
  named lane exclusions, but the title alone is not the record. Retrieve the JD, run every check,
  and let the body confirm it. JDs regularly carry disqualifiers the title never showed — one
  "Data Engineer" posting turned out to be a 12-month contract, tagged "Full-time" on LinkedIn,
  which is a second independent disqualifier that would have been missed on a title-only skip.
- **Carry-over from a near-identical posting.** Two listings sharing a title and comp range are a
  *hypothesis* that they're the same underlying role, not a finding. Fetch both and verify. If
  one genuinely can't be retrieved, say the verdict is inferred from the twin and name the twin's
  Job_ID — don't present an inference as a confirmed evaluation.
- **Obvious-looking lane or comp failures.** Run the full protocol anyway. Carl wants the whole
  reasoning visible, and a posting that fails one check often fails others worth recording.

If the JD cannot be retrieved after the five Tier 1 attempts in Step 3, the verdict is
`Unretrieved - needs manual pull` — **not** `Skip`. Leave `Role_Type`, `Biggest_Gap`,
`Biggest_Strength`, and the other judgment fields blank rather than filling them from the title.
"Probably a skip" and "confirmed skip" are different states and the log must distinguish them.

**Report retrieval honestly in the run summary.** State how many postings were evaluated from a
full JD and how many were not, and list every posting in the second group by name. Do not let a
count of flagged-as-unretrieved rows stand in for the count of postings actually lacking a JD —
those are different numbers whenever a verdict was reached without the body.

### 5. Summarize
End with a short chat summary, in this order:

1. **The counts** from step 2.
2. **Pursue rows** first, each with its one-line action. Where applicant volume is 100+, the
   referral routing goes here in `Recommended_Action`, not in the verdict.
3. **Bridge candidates** — see below.
4. **Skips**, in a compact list. Not full write-ups.

#### Bridge candidates

(Added 2026-08-10.) List every row where **Lane fit scored 12** and the final score landed in the
**65–69** band. These are roles that are BI-adjacent rather than BI-core — FP&A, financial
reporting, analytics with BI as one responsibility among several — and that scored well on
everything else.

**A Lane-12 row that passed the handoff test is not a bridge candidate.** (Updated 2026-08-31,
when the Lane-12 cap became conditional — see "The Lane-12 cap is conditional on the handoff
test" in `03-scoring-rubric.md`.) Its cap is lifted, so it scores its own total: if that clears
70 it is a **Pursue** and belongs in the Pursue list; if it lands 65–69 on the merits it is a
bridge candidate like any other. This heading is for roles the cap is still holding down — the
ones where Carl builds and then uses the output himself.

**They are Skips and they stay Skips.** `Verdict` is `Skip`, the row is written as a Skip, and
they do **not** join the Pursue list or the Pursue count. This heading is a visibility mechanism,
not a verdict tier — the whole point is that Carl makes the bridge call himself rather than having
the rubric make it for him.

Give one line each, and only these facts:

- Company and title
- Score, and the one thing that held it to Lane 12 — e.g. `Lane 12: FP&A with Power BI layered in`
- **Comp** — posted range, or researched, or "unlisted"
- **Stack** — the Tier-1/Tier-2 terms the JD actually named, or "none named"

No write-ups, no recommendation, no verdict language. Comp and stack are there because they are
the two things that decide whether a bridge role is worth a paycheck-and-currency move, and Carl
shouldn't have to reopen the JD to see them.

If there are none in a given run, say `Bridge candidates: none` rather than omitting the heading —
a run with no bridges and a run where the section was forgotten should not look the same.

### 6. Archive
Move every alert-email file handled in this run into `/processed` (create the folder if it
doesn't exist yet). Do this for **every** email touched, not just the ones that yielded new
rows — an email that was 100% dupes still needs to move, or it will be re-read and re-summarized
next run. This step is mandatory and is not complete until the move has actually happened;
don't just note it as a to-do.

### 7. Clean up the run
The headless runner opens no tabs in Carl's browser, so there is nothing to close there. Instead:

- **Close the Playwright browser and context**, including on the error path. An abandoned
  headless Chromium process keeps running invisibly — wrap the run in `try/finally` with
  `await browser.close()` so a mid-run failure doesn't leave one behind.
- **Clear the scratch JSON** from the fetch stage once rows are written and validated, or leave
  it deliberately and say so — it's useful for re-scoring without re-fetching, but stale files
  will confuse the next run if they linger unannounced.
- **Never delete or modify the `storageState` auth file** as part of cleanup.
- Report in the Step 5 summary: postings fetched, attempts used, any that hit the five-attempt
  limit, and whether any hard stop condition fired.

If Carl asks to have a Pursue posting open to apply to right away, just give him the URL — he
opens it himself in his own browser. That is also where any connections/referral lookup happens.
