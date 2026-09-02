# Carl's context and the scoring rubric

*Part of the JobSearch workflow. Start at [`COWORK_INSTRUCTIONS.md`](../COWORK_INSTRUCTIONS.md) — it holds the naming convention, the run-type map, and the rules that apply everywhere.*

**When to load this file:** Load whenever a posting is scored. Point VALUES live in `rubric/weights.json`; this file holds what they mean.

---

## Carl's context

20+ years in BI and data architecture. Currently unemployed and searching full-time.
Last role: Data Engineer at Marquis Data (Nov 2025–Jul 2026, position eliminated). Before
that, 17+ years at Company-59 (Feb 2008–Jun 2025), 12 of them in the Finance org, progressing
Sr. BI Developer → BI Manager → Technical Solutions Architect → Sr. BI Manager. MBA from
UT Knoxville (Haslam). Based in Smyrna, TN.

**Carl is not relocating.** This is absolute and not a preference to be weighed against a strong
role. Any position requiring a move, or requiring on-site presence at an office outside Nashville
Metro, is out — see the Location hard gate for the detection rules, including postings tagged
Remote whose bodies say otherwise.

Stack: Power BI, DAX, Power Query, SQL, semantic modeling, legacy BI architecture, Azure SQL,
Azure DevOps. Company-59 analytics stack was AWS S3/parquet → Databricks → Presto/Trino → Power BI
(Finance consumed it; he did not engineer it). Currently working toward DP-600 and building a
Company-423 Fabric portfolio project.

**True gaps** (do not soften these): hands-on Python, dbt, Snowflake.
**Adjacent, not gaps**: Databricks/Presto exposure covers "Fabric/Synapse or similar" language;
insurance claims, enrollment, and carrier-feed work reads as healthcare-adjacent even though
the resume doesn't label it that way.

**Scope preference (updated 2026-07-30, reaffirmed 2026-08-05): Carl wants IC roles.** This is
settled and not up for re-litigation. BI Architect / individual-contributor / thought-leader roles
score HIGHER than people-management roles. A senior IC/Architect role with real technical
authority is Carl's **best outcome**, not a consolation prize or a step down — see Scope fit in
the Scoring rubric below for how to score it and what language never to use.

Stated in his own words: *"I want IC roles, not full people-leader roles. I don't mind some
people-leadership if most of the job is IC. Also, I'm not opposed to leadership in general —
i.e. thought-leadership, technology-leadership — I just don't want my role to be predominantly
managing people."*

Three things that follow from that, so there's no ambiguity:
1. **IC is the goal, not the fallback.** Never describe an IC role as "below level," a "scope
   mismatch," or lacking leadership. It isn't a shortfall.
2. **Leadership ≠ people-management.** Technical leadership, architectural authority, thought
   leadership, mentoring, and being the senior technical voice are all things he *wants*. Only
   predominantly-managing-people is the negative.
3. **A mostly-IC role with some direct reports is still a good role.** The downgrade applies when
   people-management is the bulk of the job, not when it's a slice of it.

This preference does not override the lane check (still needs to be real
BI/Analytics/Data-Architecture function work) or the compensation floor.

**Note (updated 2026-08-04):** this reversed guidance that was previously written into Carl's
top-level project custom instructions. Those have since been reconciled — Protocol item 6 now
scores IC/Architect roles as a strong scope fit, and rule 1's target framing leads with
BI Architect / Principal / Lead IC. Claude can't edit those instructions directly, so if a future
chat shows the standing instructions still describing scope mismatches as non-flexing or leading
with a people-management target list, that copy is stale — flag it to Carl rather than following it
over this file.

---

## Scoring rubric (0–100)

Score every posting on this points-based rubric. Still run every check and show the full
reasoning against the **job description body**, never the title or alert-email summary alone —
see the "no Skip without a JD" rule in Step 4. The total score is what drives the verdict now;
nothing auto-zeroes the whole score except the compensation floor treatment below, and even that
only zeroes its own component.

**1. Lane fit — 25 pts.** The test is not "does this role touch data." It is: **is the core
function building and owning BI — semantic models, enterprise reporting, dimensional
architecture — for a business function?**

- **In-lane: 25.** BI / Analytics / Data Architecture where the deliverable is reporting,
  semantic models, or the dimensional layer beneath them.
- **Adjacent/bridge: 12.** BI-adjacent but not the primary function. Includes FP&A or financial
  reporting roles with BI tooling layered in, and roles where BI is one responsibility among
  several. **A Lane-12 role caps the total score at 69 — unless the role passes the handoff
  test.** (Conditional cap adopted 2026-08-31, Carl's decision; see "The Lane-12 cap is
  conditional" below.) A capped Lane-12 role scoring **65–69** is still surfaced to Carl under
  the "Bridge candidates" heading in the run summary — see Step 5. It is not a Pursue verdict and
  does not join the Pursue list; it is a Skip that Carl gets to see, because he is currently
  unemployed and the bridge lane should not close silently.
- **Out of lane: 0** → gate G8, Verdict = Skip. Data engineering, analytics engineering, product
  analytics, data science, credit risk, CPG-core, insurance BPO, SAP S/4HANA integration, supply
  chain/ops research, Snowflake/dbt-first engineering.

**Three function families that were scoring 25 and should not:**

- **Data governance / enablement, data platform, data infrastructure, enterprise architecture.**
  The deliverable is policy, pipelines, or reference architecture — not reports and models.
  Score **12** if BI consumption is a named responsibility; **0** if it isn't.
- **Function-modifier analytics.** If the title carries **GTM, Revenue Operations / RevOps,
  Commercial, Market Access, Client Analytics, Sales Intelligence, Growth**, the role is
  analytics *for that function's operators*, not enterprise BI. Score **12 maximum**, regardless
  of how the body reads. These are structurally different jobs: the work is funnel and pipeline
  instrumentation, and the hiring bar is domain fluency in that function.
  - *"and Insights" and "Strategy" alone do not trigger this* — they're too weak, and would catch
    in-lane roles.
- **Database administration.** "Lead and manage the Database Administration function" is not BI.
  Score **0**.

**The handoff test — who consumes what this role builds?** (Added 2026-08-27, in Carl's words.)
A posting can name every right verb — *"build and maintain dashboards and reports"*, *"build
models and forecasts"* — and still be the wrong job. The question is **who the output is for**:

> *"There's a difference between merely using BI tools and processes and
> building/maintaining/designing the BI tools and processes. I want the latter. My jobs should
> ultimately always be a handoff to a stakeholder — I shouldn't be the primary user of what I
> build."*

- **The role builds for others to consume → in lane.** The dashboard, model or semantic layer is
  delivered to a business function that uses it. That is the job.
- **The role builds what it then uses itself → not in lane, whatever the verbs say.** An analyst,
  FP&A or RevOps person who builds their own dashboards is building tooling *incidentally*,
  usually because nobody else will. The point of that job is the analysis, and the BI work is
  overhead on the way to it.

**Apply this before scoring Lane, and say which side it landed on in `Notes`.** Look for who the
deliverable is named for — *"self-service analytics for operations leaders"*, *"reporting the
field team relies on"*, *"partner with stakeholders to deliver"* — versus a body that describes
the person building and then acting on their own numbers with no named downstream consumer.

Worked example — **Company-253, Revenue Analytics Manager** (2026-08-27, scored 67, kept as a
Skip on Carl's read): the body says *"Build and maintain dashboards and reports"* and *"build
models and forecasts"*, but the role's purpose is using them to drive revenue decisions. No
downstream consumer is named. Carl's read: *"I have a feeling this person is only building them
because there's no one else to."* Verbs alone would have scored this higher; the handoff test is
what settles it.

**Show the reasoning.** In `Notes`, name the function you concluded the role actually is, in your
own words, before naming the score — e.g. `Lane 12: this is RevOps pipeline analytics with Power
BI as the display layer, not enterprise BI`. A bare number here is what let 18 of these through.

**The handoff test currently contradicts Lane scoring, and Lane scoring is losing.**
(Found 2026-08-28 by the first Phase F recall audit.)

The test above is written almost entirely from its negative side — the analyst who builds their
own dashboard. Its positive side was never spelled out, and Lane scoring was left contradicting
it. **Data architecture, data platform, MDM/governance and finance-*systems* roles pass the
handoff test cleanly**: Carl builds the platform, the semantic layer and the pipeline, and hands
them to analysts and finance to run the business on. Yet G8 sends "data engineering / analytics
engineering" to Lane 0, and these postings are landing at Lane 12 — which caps the total at
**69, one point under the Pursue threshold**.

The audit measured the consequence. Of the seven postings the filter marked Skip and Carl
applied to afterwards, **five score exactly 69 and every one of them is Lane 12** — Company-176,
Company-324, Company-576, Company-702, Vantage Elevator. He is applying to roles the lane rule is pinning at
the ceiling it imposes. Carl, 2026-08-28: *"core BI is one of my lanes, but data architecture
and Finance Systems are also my lanes."*

**Title family is not the signal; the consumer is.** "Sr FP&A **Business Systems** Analyst"
(builds SAP Analytics Cloud for finance to use) and "Lead Finance **Transformation** Data
Analyst" (builds the reporting playbook) pass the test. "Senior Financial Analyst" and
"Strategic Finance Manager" — same domain, same BI tools named — fail it, because the analysis
is the job and the dashboard is their own instrument. The existing Company-253 example is the
same shape and remains correctly out.

**Resolved 2026-08-28 — the handoff test outranks the function-modifier cap.** Company-558's
"Senior Marketing Analytics Manager — BI & Data Architecture" builds Gold-layer semantic models
for marketing analysts to consume: handoff-shaped, but sitting inside a capped function.
Presented as an open conflict in the recall audit, Carl answered **want**. So the cap is about
*who consumes the output*, not about the word in the title — a marketing-analytics title that
builds the layer marketing analysts run on is in lane, while a marketing-analytics role that
owns and performs on the marketing numbers is not. Carl's own framing: *"analytics jobs cross
that line, because their goal is to own, maintain, and perform on specific metrics, while my
lane is creating the tools and process to deliver the metrics for the analytics team."*

The four RevOps/marketing rows he declined the same day — Company-303, Company-693, Company-253,
Company-323 — are all the second shape, so the cap keeps its teeth. **Apply the handoff test
first, and let the function-modifier cap fire only on roles that fail it.** One instance
decided this; a second that contradicts it should reopen the question rather than be argued
away.

### The Lane-12 cap is conditional on the handoff test

**Adopted 2026-08-31 (Carl's decision — option C of three put to him).**

> **A Lane-12 role is capped at 69 only if it fails the handoff test. If it passes, there is no
> cap and the score stands on its own total.**

Lane still scores 12 for an adjacent role. What changes is only the ceiling: a role that builds
something a named downstream consumer runs on is allowed to reach `Pursue` on the strength of the
rest of its score, while a role that owns and performs on its own numbers stays pinned at 69.

**This adds no new judgment step.** The handoff test is already required *before* scoring Lane
and already has to be recorded in `Notes`. This rule reads the answer that is already there.

**Write the cap decision in `Notes`, both ways.** A capped row already says
`69 (capped from 75 - Lane 12)`. An uncapped one must say why the cap did not fire — e.g.
`75 (Lane 12, cap lifted - passes the handoff test: builds the semantic layer FP&A runs on)`.
Without that sentence a reader cannot tell a lifted cap from a cap nobody applied, which is the
exact ambiguity that made the four rows below inconsistent.

**Why not simply raise Lane to 25, or drop the cap outright.** Measured across the whole log:
239 rows score Lane 12, and **22 sit at exactly 69**. Those 22 hold both shapes at once — six
roles Carl applied to (Company-576 and Vantage "Enterprise Data Architect", Company-324 "Lead Data
Architect", Company-316 "Sr Finance Analytics Manager", Arista "Business Applications Analyst -
FP&A", Company-702 "Principal, Data/Analytics") sit beside four Company-64 "Business Analytics Manager"
postings, Company-591 "Decision Scientist", Yusen "Senior Financial Analyst" and Company-478 "Revenue
and Customer Operations Manager". Dropping the cap promotes all of them. The handoff test is the
only line already drawn that separates the two.

**Backtest over those 22 rows** — the six applications above pass the test and clear the cap
(Company-576 was capped from 84, Company-324 and Company-316 from 75, Arista from 72); the four Company-64
rows, Company-591, Company-478 and Yusen fail it and stay at 69. **Two rows Carl wanted do not move:
Company-176 (`FP&A Systems and AI Enablement Manager`) and Phibro (`Data Architect`) score 69 on their
own totals and were never capped** — their `Notes` record no cap. For those the Lane *score*, not
the cap, is what holds them under 70. **If a second sweep finds more of that shape, the question
reopens as option A — reclassifying handoff-shaped roles to Lane 25 — and this rule is not the
answer to it.**

**`Is_Capped_Score` in the Fabric model is not trustworthy for this.** It disagrees with `Notes`
on 4 of the 22: Company-693, Company-303, Vantage and Company-702 all record a cap in `Notes` and carry
`Is_Capped_Score = False`. `Score_Raw` would settle it and is blank on 894 of 922 rows — it only
populates going forward from 2026-08-26. **Read `Notes` when it matters, not the flag.**

**2. Scope fit — 15 pts.** Score the *actual* day-to-day scope, independent of title.
- IC / Architect / thought-leader role with real technical authority, no direct reports: **15**
- Player-coach with a small team (roughly 1–3 direct reports): **10**
- Full people-manager — hiring, succession planning, workforce planning for a team of
  analysts/engineers: **5**
- Large-scale org leadership — layered management, multiple direct-report managers below them: **0**

A title mismatch (Manager/Lead/Architect wrapping IC-execution work, or vice versa) is no longer
itself a penalty — score the real scope described in the body, not the label on it.

**Detection rule — IC must be established positively, never inferred from silence.**

The old failure mode: scoring 15 because the phrase "direct reports" was absent. Leadership-voiced
JDs routinely describe a full people-management job without ever using that phrase. Company-279,
titled *"Head of Group Data Enablement,"* scored 15 on exactly that reasoning.

**Required beats Preferred.** (Added 2026-08-27.) A years-figure sitting under **Preferred**,
**Nice to have** or **Bonus** is *not* an explicit requirement and does not trigger the harsh
Scope-0 / −10 tier. Count it as an ordinary hit instead. Only a figure in **Required**,
**Qualifications**, **Basic Qualifications** or equivalent — or stated in the responsibilities as
something the person will do — is explicit. Say which section you found it in, in `Notes`.
(Surfaced on a Company-196 posting where `"6+ years of experience leading teams"` sat under
Preferred and was scored at the required tier.)

**Scan the body for people-management requirement language.** Each of these counts as one hit:

**The language must be about PEOPLE, not about scope.** (Tightened 2026-08-26.) A hit costs 25
points — Scope drops to 0 *and* a −10 deduction applies — so it has to be earned by the posting
actually saying the job manages people. Leading a *function*, an *area*, a *capability*, a
*practice*, a *portfolio* or a *strategy* is scope language, and on its own it is **not** a hit:

- `"15+ years leading enterprise analytics functions"` → **not a hit** (leads an area)
- `"significant leadership experience across enterprise data"` → **not a hit** (unspecified)
- `"lead the evolution of our data architecture"` → **not a hit** (leads work)
- `"5+ years of direct people-leadership experience"` → **hit**
- `"manage, coach and develop a team of analysts"` → **hit**
- `"3 direct reports"` → **hit**

When it is genuinely ambiguous, **do not take the hit** — score it, and say in `Notes` which
phrase you considered and why you did not count it. This asymmetry is deliberate: 47% of the
roles Carl has applied to carry a manager/director/VP title, and `Pts_Scope` measures *inverted*
against his behaviour (roles he passed on score higher on Scope than roles he applied to). A
false hit is therefore the more costly error, and it is invisible unless the reasoning is written
down. Three postings were skipped on this reading on 2026-08-26 before the rule was tightened.

The qualifying phrases:

- `N+ years of (people )management` / `N+ years managing` / `N+ years leading a team`
- `direct reports`
- `performance management` / `performance reviews` / `performance oversight`
- `succession planning` / `workforce planning` / `staffing plans`
- `managing managers` / `leaders of leaders`
- `people leadership` / `people leader`
- `hire, develop, and retain` / `build and grow the team` / `recruiting and onboarding`
- `career development` / `coaching and development` of a named team
- `lead a team of` [analysts / engineers / developers]

Then:

- **Any explicit *requirement* of prior people-management experience** — a stated years figure, or
  a screening question asking whether Carl has led a team — scores **Scope 0** and applies a
  **−10 deduction**. Name it in `Biggest_Gap`. **This is not a gate and never overrides the
  verdict.** (2026-08-10 — a hard gate was proposed here and rejected; see "G9 does not exist"
  in section 4.0.)

  The combined 25-point swing off the IC tier is the whole mechanism, and it is deliberately
  severe: a BI-core Company-423-stack role at target comp can still clear 70 with a management
  requirement attached, and a merely-adjacent one cannot. People management is the most common
  single thing Carl passes on — 20 of 59 — but he has also applied to people-management roles
  since reaffirming the IC preference (Company-556 2026-08-05, Company-120 2026-08-06). Both facts are
  true, and a deduction expresses both. A gate would express only the first.
- **Two or more hits without an explicit years requirement: Scope 5**, and say so in
  `Biggest_Gap`.
- **One hit: Scope 10** (player-coach), which remains a solid score.
- **Zero hits: Scope 15 is available** — but only if the body *positively* describes hands-on
  building, architecture ownership, or technical authority as the day-to-day. If the body
  describes neither management nor hands-on work, score **10** and flag the ambiguity. Silence is
  not evidence of IC.

**Title override.** If the title begins with **Head of, Director, Senior Director, VP, AVP, SVP,
or Chief**, Scope may not be scored above **5** unless the body explicitly states the role is an
individual contributor or has no direct reports. See the Seniority screen below.

**None of this changes what Carl wants.** IC remains the top of the scale and the best outcome.
The rules above make the evaluator *prove* a role is IC before scoring it as one — they do not
lower IC's value. Every prohibition on IC-as-negative language elsewhere in this file still
stands in full.

**The one thing to get right here: Carl wants IC roles. "IC" is the top of this scale, not the
bottom.** The test is *what he spends his days doing*, not whether the word "leadership" appears:

- **"IC scope" is never a reason to skip, downgrade, or hedge on a role.** An individual-contributor
  or Architect role with real technical authority is Carl's *best available outcome*. If a JD says
  "this is an individual contributor role," that is a point in its favor. Never write `Reason`,
  `Biggest_Gap`, or `Recommended_Action` text that treats IC scope as a shortfall — phrasings like
  "IC scope, not leadership," "below level," or "not a leadership seat" are wrong under the current
  criteria and must not be used.
- **Carl is not anti-leadership — he is anti-people-management.** Thought leadership, technical
  leadership, setting architectural direction, owning standards, being the senior technical voice,
  mentoring, influencing without authority — all of that is *desirable* and belongs in
  `Biggest_Strength`, not `Biggest_Gap`. Only *predominantly managing people* is the downgrade.
- **Some people-leadership is fine when the role is mostly IC.** A few direct reports, mentoring
  juniors, or leading a small team while still building hands-on is a good role — that's the
  player-coach tier at 10 pts, a solid score, not a red flag. The penalty only bites when
  managing people *is* the job: hiring pipelines, succession planning, workforce planning,
  performance management as the primary day-to-day, and especially layered management.
- When the JD is ambiguous, ask "would he be building and deciding, or would he be running a
  team and attending staffing meetings?" Score the answer to that question.

A "Manager"/"Lead"/"Director" title sitting on top of hands-on IC execution work is a **favorable
finding** — flag it as such. The reverse — an "Architect" or "Principal" title that turns out to be
running a team — is the actual downgrade.

**3. Compensation — 20 pts.** (Revised 2026-08-26 at Carl's request — floor raised from VETO_LINE.)
Hard floor is **FLOOR base**; real target is **TARGET total comp** (bonus/variable counts). See
"Compensation retrieval — three-step lookup" under Step 3 of `instructions/01-intake-and-fetch.md` for how to find the figure in the
first place before scoring it here.
- Meets or exceeds the TARGET, posted or credibly researched: **20**
- Clears the FLOOR, tops out FLOOR–TARGET: **12**
- **VETO_LINE–FLOOR — below the floor but above the veto line: 4.** This band no longer zeroes the
  component, because it is now a `Review` band, not a rejection band — see "Comp floor" below and
  the Verdict thresholds section. Flag it with the matching `Comp_Flag` token from
  `04-log-and-write-discipline.md`, which is the authoritative vocabulary and carries the
  2026-08-26 era warning.
- Below **VETO_LINE**: **0** for this component, and the posting is vetoed outright — see the Hard
  override triggers section.

**Bonus scores; it does not open gates.** (Clarified 2026-08-31.) The TARGET is total comp
and bonus/variable counts toward it, exactly as stated above. The **FLOOR and the VETO_LINE
veto are base figures** and nothing blended lifts a posting past them. Where a posting quotes
base plus an unquantified or discretionary bonus, band it on base for G2/G2b, score the
component on the credible total, and say both numbers in `Notes`.
- Unlisted and not researched: **10** (neutral default — go research it before finalizing if
  time allows).

**Why the floor and the veto line are different numbers.** The VETO_LINE veto is measured: across 894
logged rows it fired 26 times and Carl applied anyway once — a 4% override rate, which is what
earns a rule veto status. A veto at FLOOR would have blocked 11 of the 49 applications carrying
posted comp (22%), including a score-92 Senior BI Analyst at $140K and two score-83 Company-703 roles at
$130K. So FLOOR is the standard the *score* is measured against, and VETO_LINE is the line below which
a posting is not worth surfacing at all. Do not collapse them back into one number.

**4. Location — 15 pts.**
- Hybrid or on-site in Smyrna, Franklin, Murfreesboro, or Brentwood: **15**
- Fully remote (U.S.): **12**
- Hybrid in downtown Nashville: **6**
- On-site in downtown Nashville: **3**
- Hybrid or on-site elsewhere in Nashville Metro (Nashville outside downtown, LaVergne, Spring
  Hill): **10**
- Outside Nashville Metro and not remote: **0** — see the Location hard gate below; this tier
  also forces the verdict to Skip regardless of the rest of the score.

If the posting's tag and the JD body disagree on location or work-type, flag the contradiction,
go with the body, and score the body's version.

**5. Skills match — 20 pts. This is a POSITIVE test.** Score what the JD *names*, not what it
omits. The absence of Carl's true gaps is worth nothing on its own — a JD built entirely on a
stack he has never touched must not score full marks.

Read the JD body and count **distinct** terms in each tier below. Count term families once
(e.g. "Power BI" and "PowerBI" are one; "semantic model" and "semantic layer" are one).

**Tier 1 — Carl's core stack.** Power BI · DAX · Power Query / M · SSAS / Analysis Services ·
Tabular model · semantic model / semantic layer · SSRS / paginated reports · SSIS ·
T-SQL · SQL Server · dimensional modeling · star schema · Kimball · data mart ·
Power BI Premium / capacity · row-level security (RLS)

*Note:* generic "data warehouse," "ETL," or "SQL" alone do **not** count as Tier 1 — they appear
in every data-engineering JD. They count only alongside at least one genuinely BI-specific term.

**Tier 2 — Adjacent and credible.** Company-423 Fabric · OneLake · Lakehouse · Direct Lake ·
Azure Synapse · Azure SQL · Azure Data Lake · Azure Data Factory · Databricks · Delta Lake ·
Presto / Trino · Azure DevOps · Dynamics 365 / Dynamics AX / D365 · Power Automate · Power Apps ·
Power Platform · Company-423 Purview · PowerPivot

**Tier 3 — Competitor BI platforms.** Neutral in isolation; decisive when they are the *only*
stack named. Tableau · Looker / LookML · Qlik · MicroStrategy · OBIEE / Company-463 Analytics ·
Cognos · BusinessObjects · SAS · Domo · Sigma · Hex · Sisense · ThoughtSpot · Mode · Metabase

**True gaps.** Do not soften these. Python as a primary hands-on requirement · PySpark / Spark
development · Scala · Java · dbt · Snowflake · Airflow / Dagster / Prefect · Kafka / streaming ·
Terraform / IaC · Informatica · Company-463 PL/SQL · SAP BW / HANA development · GCP / BigQuery ·
Redshift · ML / MLOps / feature stores · R

Scoring:
- **3+ Tier-1 terms: 20.** This is a real Company-423-stack BI role.
- **1–2 Tier-1 terms, or 0 Tier-1 with 2+ Tier-2: 13.**
- **0 Tier-1, exactly 1 Tier-2: 7.**
- **No tooling named anywhere in the body: 7** (unknown, not wrong — flag it in `Biggest_Gap` as
  "stack unnamed; confirm on screen").
- **0 Tier-1 and 0 Tier-2: 0** — and check gate G10 below.

**Gate G10 — stack absence.** If the body names **zero** Tier-1 and **zero** Tier-2 terms *and*
names one or more Tier-3 platforms as the primary tooling, the verdict is **Skip**, `Reason =
"wrong stack (X)"` naming the platform. This is the Company-221 case: a role can be genuinely
BI-functional, well-paid, remote, and still be built on a stack Carl would be learning from
scratch while competing against people who already have it. It does not fire when no tooling is
named at all.

**True-gap deduction (applies on top of the score above):**
- **Two or more true-gap tools required as core hands-on skills: −10**
- **Exactly one true-gap tool required as a core hands-on skill: −5**
- Listed as "preferred," "nice to have," or "or similar": **0** — treat "or similar" platform
  language literally, as always. Databricks/Presto exposure covers "Fabric/Synapse or similar."

Unemployment lowers the bar on *tooling stretch* — a −5 single-gap role is still worth pursuing.
It does not lower the bar on gate G10, which is about the stack being wrong, not stretched.

**6. Perks/equity — removed 2026-08-10.** Formerly 5 pts; the 5 points moved to Skills match,
which discriminates and this did not. Still *record* meaningful equity, bonus, or profit-sharing
in `Notes` where named — it matters for negotiation and for the sub-target comp judgment — it
just no longer scores.

The rubric now sums to:
**Lane 25 + Scope 15 + Comp 20 + Location 15 + Skills 20 + Applicants 5 = 100.**

**7. Applicant competition — 5 pts.**
- Under 30 applicants (or "actively reviewing"/low-volume signal): **5**
- 30–99 applicants: **3**
- 100+ applicants: **0** — still means referral over cold apply regardless of score; note the
  Haslam/UT Knoxville routing angle and flag if an alumni connection is visible. Anonymous
  postings kill the referral lever — say so.

### Deductions (subtract from the sum above; floor the total at 0)

These used to be hard disqualifiers. They're now lighter penalties — real drags on the score,
not automatic skips. Score the role on its actual merits first, then apply what's relevant:

- **Third-party recruiter / staffing-board posting** (Ladders, staffing agencies, "for our
  client" anonymous-employer postings): **−10**. These also usually kill the referral lever and
  limit company research — say so in `Biggest_Gap`.

  **The intermediary alone is not disqualifying.** Carl has applied through Central Point
  Partners, Company-275, Company-468, Hire Elevation, and Company-354. What actually kills
  these is **an unnamed end client combined with either contract terms or sub-target comp** —
  that combination is gate G4, `Reason = "anonymous end client"`. A named end client with a
  direct-hire W2 role at target comp is fine; score it normally with the −10 and move on.

  **Employer verifiability.** If the hiring company can't be confirmed to exist — no website, no
  LinkedIn company page, a name that reads as generated — flag it in `Notes` and set
  `Recommended_Action` to verify before applying. Don't gate on suspicion alone, but don't let it
  pass unremarked either.

- **Travel requirement**: **−10** for stated domestic travel above roughly 10%, or any recurring
  international travel cadence. Recurring international travel is also gate G12 (Verdict = Skip)
  — a role requiring trips to another continent several times a year isn't a job Carl wants
  regardless of how it scores. Occasional travel to a home office, or "up to 10%," is **0**.
- **Domain gate — the unit is the *deliverable*, not the employer's industry.** (Rewritten
  2026-08-10.) Carl has applied to healthcare and insurance employers repeatedly and passed on
  others in the same industries. The distinction that actually predicts his behavior:

  - **The employer operates in a gated industry, but the role is BI-core: 0 deduction.** A Power
    BI Administrator at a healthcare company is a Power BI job. Do not deduct. Note the industry
    in `Notes` and move on.
  - **Domain knowledge is a soft preference — "healthcare experience a plus": −3.**
  - **Domain expertise is the job's subject matter: −15.** The deliverables are domain artifacts
    — medical coding and reimbursement, claims adjudication, market access, clinical quality
    measures, regulatory or statutory reporting, actuarial work. Carl would be hired for domain
    fluency he doesn't have, with BI as the tool.
  - **An explicit years-of-industry-experience requirement — "7+ years in healthcare," "5+ years
    in insurance," federal/government clearance or citizenship requirements: gate G11,
    Verdict = Skip**, `Reason = "X domain gate"`. This is a stated requirement he fails on its
    face, not a stretch.

  **Adjacency still holds and is not overridden here.** Insurance claims, enrollment, and
  carrier-feed work reads as healthcare-adjacent even though the resume doesn't label it. Where a
  JD names that kind of work rather than clinical or coding expertise, score it as adjacent and
  say so.

  A useful test when it's ambiguous: *would a BI architect from a different industry be
  competitive for this role?* If yes, no deduction. If the JD is really asking for a domain
  specialist who can also report, deduct or gate.
- **IT consulting / managed-services delivery pattern** (Company-500/Company-215/Company-694/Company-691-type shops:
  presales, plural "client engagements," scoping, practice leadership meaning project mentoring
  rather than direct reports): **−10** for a heavy blend, **−5** for a light one.
- **Contract / C2C, not direct W2/FTE**: **−10**, unless the posting clearly implies
  contract-to-hire, in which case **−5**. Tag-vs-body contradictions on employment type: flag,
  and follow the body.

### Seniority screen — Director and above

(Added 2026-08-10 at Carl's request.)

If the role title contains **Director, Sr./Senior Director, Head of, VP, Vice President, AVP,
SVP, or Chief**, apply this screen. It is deliberately a high bar rather than a hard gate: these
roles are a needle in a haystack for Carl, not an impossibility, and the right one could come
around.

Carl's reasoning, recorded so it isn't re-litigated: Director-and-above roles are usually people
leadership, and the ones that aren't still carry a breadth of organizational responsibility and
involvement that he doesn't want. His judgment is that the money doesn't compensate for the stress
and the total consumption of his time. This is a preference about how he wants to work, not an
assessment of whether he could do the job — never write it up as a qualification gap.

**Mechanics:**

1. Scope may not score above **5** (per the title override above) unless the body explicitly
   states individual contributor or no direct reports.
2. **The verdict may only be `Pursue` if all three hold:**
   - Final score ≥ **80**, **and**
   - **Zero** people-management requirement hits fired (per the detection rule above), **and**
   - The role is BI-core on the Company-423 stack — Skills scored 20.
3. Otherwise: **Verdict = Skip**, `Reason = "director+ scope"`.

**No separate seniority deduction.** (2026-08-10.) A −8 seniority-breadth deduction was proposed
here and removed. The Scope cap at 5 already costs 10 points against the IC tier, and stacking a
further −8 on top double-counted the same concern — with it, a Director+ role not explicitly
labelled IC topped out at **79** when fully remote, one point under this screen's own ≥80
requirement. That made the screen an unconditional gate for remote roles while describing itself
as a high bar, and it would have blocked eight roles Carl applied to, four of them scoring 82–85.
Without the deduction the remote ceiling is **87** and the three conditions above do the work they
were written to do.

**What this screen actually rejects, stated plainly:** a Director+ role with any
people-management requirement in the body fails condition 2 outright. A Director+ role on a
non-Company-423 stack fails condition 3. What survives is a Director/Head-of/VP title sitting on
top of hands-on Company-423-stack BI work with no team attached — which is exactly the "needle in a
haystack" Carl described, and it is now genuinely reachable rather than arithmetically excluded.

**Company size is a strong secondary signal — record it, don't gate on it.** A Director of BI at
a 150-person company is frequently a hands-on architect with a title; at a 15,000-person company
it is committee membership and headcount. Note the org size and which pattern the body suggests in
`Notes` whenever this screen fires, even on a Skip. If a Director+ role clears all three
conditions above, say plainly in `Recommended_Action` why this one is the exception — Carl should
be able to see the argument without re-reading the JD.

### Lane-fit hard cap

If Lane fit scores **0** (genuinely out-of-lane function — data engineering, product analytics,
data science, credit risk, CPG-core, insurance BPO, SAP integration, supply chain/ops research,
Snowflake/dbt-first engineering), **cap the total score at 35** regardless of how the other
components sum, and the verdict is **Skip** regardless of the numeric total. Targeting scatter
across the wrong function — not skills or resume weakness — caused most of Carl's early
rejections; a strong comp/location/skills read on the wrong function is still the wrong function,
and the points system must not paper over that. Show the uncapped component sum in `Notes` for
transparency, then apply the cap: e.g. `Score 35 (capped from 58 - Lane 0) = ...`.

### Location hard gate

(Added 2026-08-06, after Carl flagged two Pursue-verdict rows — Company-187 and Company-211 —
that were hybrid, required on-site presence, and sat outside Nashville Metro with no remote
option. Under the plain weighted rubric a strong lane/comp/skills read could still clear the
Pursue threshold despite scoring 0 on Location, which isn't the intended behavior: a role that
would require relocation or an unsustainable commute isn't actionable for Carl right now no
matter how good the rest of the profile is.)

If Location scores **0** (the posting is not remote and the on-site/hybrid location falls outside
Nashville Metro), **cap the total score at 35** regardless of how the other components sum, and
the verdict is **Skip** regardless of the numeric total — same mechanism as the Lane-fit hard cap
above, and the two can co-occur without double-capping (an out-of-lane role that's also
non-remote and out-of-area is still just capped once, at 35). Show the uncapped component sum in
`Notes` for transparency, then apply the cap: e.g. `Score 35 (capped from 62 - Location 0 hard
gate) = ...`. Populate `Reason` with the Skip headline per the rule below, e.g.
`"location gate (Louisville, CO)"` or `"location gate (Atlanta, GA)"`.

**Expanded detection (added 2026-08-10). Carl is not relocating. Treat this as absolute.**

The gate has fired correctly when location was stated plainly. It has been evaded when the
posting *presents* as remote and the body says otherwise. Check every one of these before
scoring Location above 0:

- **State-restricted remote.** "Remote — must reside in one of the following states," or a named
  list of approved states. **Tennessee must appear on that list.** If it doesn't, the gate fires.
  If the list is vague ("most US states"), flag it in `Notes` and ask Carl rather than assuming.
- **Commuting-distance language.** "Within commuting distance of," "able to come to the [X]
  office as needed," "occasional on-site," "remote but local to [city]." If the named city is
  outside Nashville Metro, the gate fires — regardless of the Remote tag.
- **Stated on-site cadence.** Any "N days per week/month on-site," "hybrid schedule," or
  "flexible hybrid" attached to an office outside Nashville Metro. The gate fires.
- **Relocation assistance offered.** This is near-conclusive evidence the role is on-site, even
  when the posting is tagged Remote. Treat the role as on-site at the named office and score
  Location accordingly.
- **Headquarters-only postings.** A single office named with no remote language anywhere in the
  body is on-site at that office, not remote-by-omission.
- **Multi-location postings.** If several offices are listed and none is in Nashville Metro, the
  gate fires. If one is, score it as that location.

**Where the tag and the body disagree, the body wins** — this is already the rule everywhere else
in this file and it applies here without exception. When the gate fires on a Remote-tagged
posting, say so explicitly in `Notes`: `Tagged Remote; body requires 3 days on-site in Columbus,
OH — location gate fired on body language.` That sentence is how this stops recurring.

This gate is subordinate to the Hard override triggers below — if a posting also hits a Pass
trigger (low comp under VETO_LINE, named consulting firm, Ladders), Pass wins. A Review-type gate (contract, comp VETO_LINE–FLOOR, delivery role) does NOT outrank a Skip-type exclusion — see the precedence rule in §4.0.

**Not retroactive.** This gate applies to evaluations run from 2026-08-06 onward. Rows logged
before that date under the plain weighted rubric (including the Company-187 and Emory rows that
prompted this change) are left as-is at Carl's request — don't "fix" them unless he asks.

### Verdict thresholds

Score is primary; `Verdict` is its label for quick scanning.
- **Score ≥ 70 → Pursue**
- **Score < 70 → Skip**

(Revised 2026-08-10. The former `50–69 → Pursue` band is deleted. It was assigning the same
verdict as the band above it, which made the threshold decorative — and it accounted for 37 of
the 59 Pursue verdicts Carl later passed on. Scores in the 50–69 range are now Skips, and are
re-read monthly under Phase F so the recall cost of this change stays visible rather than
invisible. Lane-12 roles landing in the 65–69 band are additionally surfaced under the "Bridge
candidates" heading in Step 5 — still Skips, but visible.)

### `Review` — the fourth verdict

(Added 2026-08-26.) `Verdict = "Review"` means *a negative fired, but it is one Carl's own history
says he routinely outweighs — so this is his call, not the rubric's.*

**It fires when a compensable gate fired and no veto-class gate did.** The compensable gates are
currently **G1** (`contract`), **G2b** (comp VETO_LINE–FLOOR), and **G3b** (client-delivery role
shape). A veto-class gate — **G2** `low comp` under VETO_LINE, **G3a** named consulting firm, **G4**
Ladders — still produces `Pass` and outranks `Review`.

A `Review` row is a **Skip that Carl has not been asked about yet**, not a soft Pursue. It does
not go in the Pursue list in Step 5's summary; it gets its own short "Review — your call" heading
naming the gate that fired and the one thing that would make it worth it.

**Precedence:** Pass-type gates > Skip-type gates > `Review` > score threshold.
(Corrected 2026-08-31. This line read `Pass-type > Review > Skip-type` — the pre-2026-08-26
order, missed when the G1/G3 demotions were made. It contradicted §4.0 of
`02-evaluate-and-report.md`, `weights.json`'s `verdict.precedence`, and the Verdict thresholds
section of this same file. `Review` is reserved for rows whose *only* disqualifier is
compensable, so a Skip-type gate beats it.)

**Why this exists, and why it is not a score band.** Within the current-era Skip population the
apply rate is flat at 18–22% from score 10 through 79 — carving out a band surfaces rows at
roughly the 20% base rate and is not worth the reading. Keying on the compensable gates instead
surfaces 64 rows and catches 34 of Carl's applications: **53% precision, 2.6× base rate.** A rule
enters the compensable set only when its measured override rate says it belongs there; see the
override-rate table in the Hard override triggers section.

**`Verdict` is never "Pursue via referral only."** (Cleaned up 2026-08-08: 26 existing rows had
this exact string; all corrected to `Pursue`.) `Verdict` only ever answers "is this worth
pursuing" — it doesn't encode *how*. When the verdict is `Pursue` **and** applicant volume is
100+, say so in `Recommended_Action` instead (e.g. "Pursue via referral — 100+ applicants, work the
Haslam/UT Knoxville network before cold applying"). This isn't a loss of information: as of
2026-08-08, 22 of the 26 affected rows already carried the referral recommendation in
`Recommended_Action` independent of the verdict label — that's the field that was always doing the
real work.

**Be honest, not encouraging.** If it's a poor fit, the score should say so plainly — don't grade
on a curve to avoid a low number. Label bridge/paycheck moves as such so they never blur into
lane-advancing ones, regardless of score.

### Hard override triggers (Verdict = "Pass")

Still run the full rubric — lane, scope, comp, location, skills, perks, applicants, and all
deductions — and show the component math in `Notes` exactly as always. But if a posting hits any
of the criteria below, `Verdict` is overridden to `"Pass"` and `Reason` is set to the fixed value
shown, regardless of what the numeric score or threshold would otherwise produce. A hard override
always wins — it supersedes the Verdict thresholds above, the Lane-fit hard cap, the
Location hard gate (see above), and the Employer exclusions gate (see below) when any of these
would otherwise apply.

- **Contract role → `Review`, not `Pass`.** (Demoted 2026-08-26.) Any contract, C2C, or fixed-term
  posting (not stated as a direct permanent W2/FTE hire) → `Verdict = "Review"`,
  `Reason = "contract"`, plus the −10 deduction in the component math. **This is no longer a
  veto.** Measured: it fired 22 times and Carl applied anyway 10 times — a 45% override rate,
  including a Company-542 "Power BI/Fabric Developer" and a Company-495 "Power BI Developer",
  both scoring 77. A contract term is a real negative he routinely outweighs when the stack is
  right, which is the definition of compensable.
- **Comp below VETO_LINE.** If the posted (or credibly researched) upper end of the salary range is
  below VETO_LINE → `Verdict = "Pass"`, `Reason = "low comp"`. (Measured override rate 4% — this
  is the line the veto is *earned* at. The scoring floor is higher, at FLOOR; a posting topping
  out between VETO_LINE and FLOOR is **not** vetoed, it is `Review` — see below.)
- **Consulting — split into two rules 2026-08-26.** The old single rule fired 80 times and Carl
  applied anyway 25 times (31%). Splitting it by detection method shows why: the **named-firm**
  half fired 28 times with **zero** overrides, while the **JD-language** half fired 52 times with
  25 overrides — a coin flip. One rule was doing two jobs and only one of them well.

  - **G3a — Named consulting firm → `Verdict = "Pass"`, `Reason = "consulting"`.** A veto, earned
    at a 0% override rate. The list is not limited to the Big-N; it is any firm whose business
    *is* selling consulting/advisory delivery:
    **Company-704 · Company-196 · Company-700 · Company-715 · Company-716 · Company-713 · Company-717 (incl. Company-717 Platinion) · Company-09 ·
    Company-575 · Company-178 · Company-696 · RSM · Grant Thornton · Protiviti · Huron · Guidehouse · Alvarez &
    Marsal · AlixPartners · ZS Associates · Company-135 · Company-697 · Company-04 · Company-02 · Company-701 · Company-678 ·
    Company-459 · Company-116 · Company-653 · Company-256**
    — and any firm that plainly belongs beside them. **Add to this list rather than relying on
    G3b to catch a consultancy by its language.** (Expanded 2026-08-26: a sweep of unacted rows
    found Company-575, Company-717, Company-04, Company-135, Company-697, Company-701, Company-178, Company-678, Company-459 and Trinity all being
    caught only by the language heuristic — correctly, but by the weaker rule.)

  - **G3b — Client-delivery role shape → `Verdict = "Review"`, `Reason = "consulting delivery
    role"`.** Compensable, not a veto. Fires on the *role*, at any employer: titles and bodies
    built around **engagement management, billable client delivery, practice/business development,
    or program delivery leadership** — "Engagement Manager," "Managing Consultant," "Senior
    Delivery Consultant," "Data Program Delivery Lead," "Principal, Analytics" at an advisory shop.

    **The signal is role shape, not employer.** Carl applies to hands-on Company-423-stack roles at
    IT-services and Company-423-partner shops constantly — Company-285, Company-714, Company-66, Company-500,
    NRI, Company-47, Company-350, Company-188 — when the title is a *stack* role: Power BI Developer, BI
    Engineer, Data Architect, Solutions Architect, Advanced Analytics Developer. **Company-178 sits on
    both sides**: he applied to its Advanced Analytics Developer/Lead posting (score 78) and left
    its Performance Improvement Operations Consultant posting (33) alone. Do not deduct or gate a
    posting merely because the employer sells services — read what the person would actually do.

    Generic consulting *vocabulary* alone — "client," "stakeholder," "engagement" used loosely —
    is not this gate. Neither is a services employer hiring for an internal or product BI role.
- **Ladders posting.** If the posting company is Ladders (or any listing sourced through Ladders,
  regardless of the underlying client) → `Verdict = "Pass"`, `Reason = "Ladders post"`.

If more than one trigger applies to the same posting, set `Reason` to all applicable short
reasons joined with `; ` in the order listed above (e.g. `"contract; low comp"`), and call out
each trigger explicitly in `Notes`.

**A veto fixes the `Verdict`, not the `Score`.** (Clarified 2026-08-27.) "A hard override always
wins — it supersedes the Verdict thresholds, the Lane-fit hard cap, the Location hard gate and the
Employer exclusions gate" means it wins **the verdict**. It does not switch off the score caps.
Score the row exactly as you would have without the veto: apply every cap that fires, put the
capped number in `Score`, the uncapped total in `Score_Raw`, and let the veto set `Verdict`. The
score still has to be usable by Phase F and the learner, and a veto row scored on different rules
from every other row is not comparable to them. (Surfaced on two consulting-veto rows scored
uncapped on the opposite reading.)

**Which rules belong here, and the test for admission.** (Added 2026-08-26.) This section is for
vetoes only, and a rule earns veto status **empirically**: its measured override rate — the share
of rows where it fired and Carl applied anyway — must be at or near zero. Carl's decision function
is compensatory; a negative he routinely outweighs is a deduction or a `Review` trigger, never a
veto. Measured across all 894 logged rows:

**These rates were wrong when written, and one of them decided a rule's class.** (Corrected
2026-08-31.) The measurement counted every row where the gate fired and `Carls_Action = Applied`,
without checking that the application came *after* the evaluation. The 2026-08-12 backfill
retro-logged months of Carl's application history and scored it under the current rubric, so a
gate got charged with "overrides" that happened weeks before it existed. Corrected figures are
from `rubric-learn.py` on 2026-08-31, which now excludes them; the 2026-08-26 column is kept so
the size of the error stays visible.

| Rule | Fired | Overrides | Override rate | 2026-08-26 read | Class |
|---|---|---|---|---|---|
| Ladders post (G4) | 27 | 0 | 0% | 0% | veto |
| Consulting — named firm (G3a) | 57 | 0 | 0% | 0% | veto |
| Comp below VETO_LINE (G2) | 41 | 1 | 2% | 4% | veto |
| Contract (G1) | 19 | 2 | **11%** | **45%** | **Review** — see below |
| Comp VETO_LINE–150K (G2b) | 8 | 0 | 0% | 22% | Review — but see below |
| Client-delivery shape (G3b) | 5 | 0 | 0% | (not measured) | Review — but see below |
| Consulting — language (old G3) | — | — | n/a, rewritten | 48% | rewritten as G3b |

**G1 `contract` stays `Review`, and not because of this number.** (Carl, 2026-08-31.) 45% was
the stated basis for demoting it from veto on 2026-08-26 and that basis is gone — 11% is
borderline, between the 10% veto ceiling and the 25% review floor, and `rubric-learn.py` will
never propose anything for a borderline rule. What holds the demotion up is the independent
evidence from the same day: the 2026-08-26 recall sweep re-surfaced rows the gate had been
auto-killing and Carl wanted **2 of 3** — SHI International (85, $160–215K) a real miss, and
Company-96 (62) one he had already applied to. Those are postings the veto made invisible. The
rate was never the argument; the recall sweep was.

**Two of G1's 19 rows are the whole margin, and Carl chose how they count.** InterEx
`4445507224` and Riana `4452713933` are the only overrides, and both were applied to on the
same day the row was evaluated. Carl, 2026-08-31: he does not remember either, and counts them
as overrides. Counted the other way G1 measures 0% on n=19 — veto class. The 11% is a decision,
not just an observation.

**G2b and G3b were measured for the first time on 2026-08-31, and their numbers mean almost
nothing yet.** Both had read n=0 because their `match_reason` patterns were written from memory:
G2b's was `below comp floor`, a word order that appears nowhere in 922 rows, and G3b's was its
own canonical token `consulting delivery role`, which the log has never used. Corrected, G2b
fires 8 times and G3b 5 — **and Carl has acted on exactly one of those 13 rows.** A 0% override
rate over rows nobody has looked at is an absence of evidence, not agreement. Both sit under the
n floor and neither can move. The 22% previously shown for G2b was a 2026-08-26 hand count that
the script has never reproduced; do not quote it.

**Company-114 `Reason` tokens, and why they matter beyond tidiness.** A gate's `Reason` string is
the only trace it fired — the learner measures the rule by matching that text, so an
undocumented or drifting phrase makes the rule invisible rather than merely untidy. The
authoritative tokens:

| gate | write this | also accepted (already in the log) |
|---|---|---|
| G1 | `contract` | — |
| G2 | `low comp` | `comp below floor`, `comp too low` |
| G2b | `sub-target comp` | `comp at floor`, `comp gap` |
| G3a | `consulting` | — |
| G3b | `consulting delivery role` | `consulting delivery pattern`, `consulting-firm delivery pattern` |
| G4 | `Ladders post` | — |

**`comp below floor` means below the VETO_LINE, not the VETO_LINE–150K band** — confirmed
against `Comp_Flag` on every row that uses it. The phrase reads like G2b and is always G2. Prefer
`low comp` for the veto and `sub-target comp` for the band.

**Resolved 2026-08-31 — `Comp_Flag` was never inconsistent with itself; it changed meaning.**
The 47 rows reading `Below floor` for sub-VETO_LINE postings were written when the floor *was* VETO_LINE,
before the 2026-08-26 revision raised it to FLOOR. Both `Below floor` and `Sub-target` shifted one
band that day, and nothing on a row says which scheme applies. Fixed forward with a banded token, an era
table, and `field_matches()` in `rubric-learn.py` reading each row under its own era. The
vocabulary and the era table live in `04-log-and-write-discipline.md` — collapsed there
2026-08-31 as the single authoritative copy, since being restated in three files is how this
drift went unnoticed in the first place. **No rows were rewritten** — each was correct under the
rules in force when it was written.

**Before adding a rule here, measure it.** Before removing one, measure it. Do not promote a rule
to veto status because it feels decisive — three of the six above failed that test. **And check
that the evaluation came before the action** — a rule cannot be overridden by a decision made
before it fired.

This section previously also vetoed contract roles and consulting-by-language, reversing an even
earlier behavior where they were point deductions (contract −10, consulting-pattern −10,
third-party/staffing-board −10). Those two have now been returned to the compensable side as
`Review` triggers, with their deductions still applied to the component math in `Notes`. The
remaining vetoes above still determine `Verdict` outright when they fire.

This is also a change to who can populate `Reason` on Claude's own runs. Normally `Reason` is
left blank on Claude's own evaluation runs and filled in by Carl (see Row format in `instructions/04-log-and-write-discipline.md`); a
hard-override trigger is the second sanctioned exception to that rule, alongside the
closed-posting check in Step 3.

### The G3a firm list is deliberately short

(Added 2026-08-31 at Carl's request, after a Company-409 posting raised the question.)

**Do not add a firm to the G3a veto list just because it describes itself as a consulting or
technology-services company.** The list names the specific large firms Carl will not work for; it
is not a register of every consulting shop that appears in an alert. Growing it one mid-size
vendor at a time turns a deliberate exclusion into an ever-widening filter nobody reviewed.

Consulting character is already priced, twice over, and that is the intended mechanism:

- the **IT consulting / managed-services delivery pattern** deduction, −10 for a heavy blend and
  −5 for a light one, under Deductions; and
- **G3b**, which fires on client-delivery *role shape* at any employer and yields `Review`.

Together those cost a consulting-flavoured posting real points and put it in front of Carl as a
judgment call. That is the outcome he wants — a role that loses points for being consulting, not
one vetoed for it. Adding a firm to G3a is a decision Carl makes explicitly, never one an
evaluation run makes on resemblance.

### Employer exclusions (Verdict = "Skip")

(Added 2026-08-06 at Carl's request.)

Still run the full rubric and show the component math in `Notes` exactly as always. But if the
employer is one of the companies below, `Verdict` is overridden to `"Skip"` regardless of what
the numeric score or threshold would otherwise produce — same mechanism as the Lane-fit hard cap
and Location hard gate (cap the total score at 35, verdict = Skip), not the Pass-type hard
overrides above. This gate is subordinate to the Hard override triggers section — if a posting
from an excluded employer also hits a veto-class trigger (low comp under VETO_LINE, named consulting firm, Ladders),
Pass wins.

- **Company-30** → `Reason = "employer exclusion (Company-30)"`.
- **Company-463** → `Reason = "employer exclusion (Company-463)"`.
- **Company-59** → `Reason = "employer exclusion (Company-59)"`. (Added 2026-08-10.) Carl's former
  employer of 17 years. He does not want to be re-hired there. This is settled — don't surface
  Company-59 roles as opportunities or ask about them case by case.
- **Company-664 — Nashville postings** → `Reason = "employer exclusion (Christian
  music)"`. (Added 2026-08-10.) UMG's Nashville operation is Capitol Christian Music Group. Carl
  does not want to work in Christian music. **This has to live here, at the employer level,
  because it is not detectable from the JD** — all three logged UMG postings were checked and
  none contains the words "Christian," "gospel," "faith," or "worship." Nothing in the body
  reveals it. If a UMG posting is clearly *not* Nashville/Christian-division, evaluate it
  normally and say why the exclusion didn't apply.

**The music industry itself is not excluded.** Carl has no music-industry experience and said so,
but he is not opposed to the sector. Do not add music or entertainment to the industry exclusions
below. The experience half of his objection is already covered by the domain-as-deliverable rule:
the UMG postings centre on *"artist growth"* and *"recording artists and songwriters,"* which is
domain-as-deliverable at **−15**, not an industry ban. A music-industry employer hiring for
Company-423-stack enterprise BI is in lane and should be scored as such.

### Industry exclusions (Verdict = "Skip")

(Added 2026-08-10.) Same mechanism as Employer exclusions — cap the score at 35, Verdict = Skip,
subordinate to the veto-class hard override triggers (G2, G3a, G4), and superior to the Review-class gates (G1, G2b, G3b). These are gate G6.

- **Cannabis** → `Reason = "industry exclusion (cannabis)"`.
- **Gambling, casino, sportsbook, iGaming** → `Reason = "industry exclusion (gambling)"`.
- **Adult entertainment** → `Reason = "industry exclusion (adult)"`.
- **Firearms and ammunition** → `Reason = "industry exclusion (firearms)"`.
- **MLM / direct sales** → `Reason = "industry exclusion (MLM)"`.
- **Faith-based or mission-aligned employers where alignment with the mission is a stated
  qualification** → `Reason = "industry exclusion (mission alignment)"`. This is narrow: it fires
  when the JD asks for personal alignment with a religious or ideological mission, not merely
  because an employer is a nonprofit or has a values statement.
- **Employers whose primary output is religious content** — Christian music labels and publishers,
  faith-based broadcasting, devotional media → `Reason = "industry exclusion (religious content)"`.
  This fires on what the company *makes*, independent of whether the JD asks for personal
  alignment. Judge it from company research, not the JD body.

**Known blind spot — read this before assuming the gate covers it.** Neither faith bullet above
catches the Company-664 case, and it is worth knowing why. The UMG postings name no
religious content and ask for no mission alignment; the Christian-music connection is a fact about
UMG's Nashville division that appears nowhere in the text. Any employer whose religious-content
business is invisible from the posting has to be handled as a named employer exclusion above
instead. **When an otherwise-in-lane role is at a company whose divisions you don't know, spend
one search on what that specific division does before scoring it.** That search is the only thing
standing between this gate and a repeat.

Judge on the industry of the **actual hiring employer** as described in the JD body, not a
staffing intermediary and not a mention of the sector as a customer or vendor.

This applies to the employer named in the JD body (the actual hiring company), not a staffing
intermediary that happens to be posting on their behalf in the other direction — e.g. a posting
that names Company-30 or Company-463 as the real employer is excluded even if surfaced through a
third-party board; a posting merely mentioning either company as a client or vendor is not.

**Not retroactive.** Applies to evaluations run from 2026-08-06 onward. Rows already logged for
Company-30 or Company-463 before that date are left as-is unless Carl asks otherwise.

---
