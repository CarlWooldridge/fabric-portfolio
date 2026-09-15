# Application triage, Phase E, Phase F

*Part of the JobSearch workflow. Start at [`COWORK_INSTRUCTIONS.md`](../COWORK_INSTRUCTIONS.md) — it holds the naming convention, the run-type map, and the rules that apply everywhere.*

**When to load this file:** Load for application/rejection/interview triage, the stale-Pursue closure sweep, or the monthly recall audit. NOT needed for a job-alert evaluation run.

---

### Application / rejection / interview triage (runs after the job-alert phases)

(Added 2026-08-08.) After the job-alert evaluation phases finish, reconcile record of applications
Carl has *already submitted* — confirmations, rejections, and interview invitations — against the
log, from two sources: Inbox mail (below), and the LinkedIn Job Tracker (see "Second source" below,
added the same day). Both feed the identical downstream pipeline: match → blank-gate → prompt →
write → validate.

**This phase is deliberately NOT unattended.** Unlike the job-alert phases, every proposed change
is presented to Carl as a multiple-choice prompt (accept / accept-with-modification / skip) before
anything is written. Carl asked for this explicitly: these writes touch `Carls_Action`, `Outcome`,
and `Reason` — the columns that represent his own decisions and the employer's, not Claude's
analysis — so a wrong automated write corrupts the record of what actually happened.

**Mechanics — scripted as of 2026-08-27.** `scripts/triage-match.py` now does the mechanical
half: it joins `triage-candidates.json` to log rows, classifies each sender from the envelope,
parses each email's date, and renders the model's classifications into a validated
`jd-update.py` edit list. It never decides what an email *means* — that stays with the model,
for the reasons under "Do NOT classify with a keyword/phrase list" below. Run it as:

```
osascript scripts/mail-triage-scan.applescript 3
node scripts/fetch-applied-tracker.js                                 # second source, page 1
python3 scripts/triage-match.py --out scratch/triage-matches.json     # match BOTH sources
#   ... read each body, write scratch/decisions.json ...
python3 scripts/triage-match.py --decisions scratch/decisions.json    # render + validate
python3 scripts/jd-update.py --input scratch/triage-edits.json --dry-run
python3 scripts/jd-update.py --input scratch/triage-edits.json        # after Carl approves
python3 scripts/mail-move.py --op archive                             # mandatory, every run
python3 scripts/triage-match.py --commit-ledger                       # resolved IDs only
```

**Both sources run in one Phase D invocation, and `triage-match.py` reports them together.
This is enforced, not advised.** (Tightened 2026-08-28 at Carl's request, because the revamp's
first pass dropped the tracker entirely and nothing noticed.) Both match mode and render mode
**halt** when `applied-tracker.json` is missing, older than today, or records a halted fetch.
`--skip-tracker` overrides and prints a warning naming exactly what goes unseen; it should be
used only when LinkedIn itself is unavailable.

**A halted fetch is not an empty tracker.** `HALT_EXPIRED` means the session aged out and the
page was never read; reading that as "no new applications" is a silent false negative of exactly
the kind this source exists to prevent. The script treats a halt as unread and stops.
A decision carries `message_id` (email-sourced) or `tracker_job_id` (tracker-sourced), never
both. When the two sources name the same posting, the renderer merges them and **halts if they
set a field differently** — a confirmation email and a tracker entry for one application have to
agree about when it happened.

On the first live run (2026-08-27, 45 Inbox messages) this routed 26 of 45 to Phase B/Phase G
from the envelope alone, leaving 19 bodies for the model to read. The matching itself — 45
emails against 921 log rows — is a set operation over a 1.2 MB CSV and no longer enters context
at all, the same saving `jd-dedupe.py` made in Phase B.

**Cross-reference Fabric's write-back before writing anything.** (Added 2026-08-27 at Carl's
direction.) Carl triages in the Power BI report, and those decisions live in `JobSearch_DB`, not
in this CSV. `triage-match.py` loads `scratch/fabric_actions.csv` (from
`fabric-pull-actions.py`) and **suppresses any write to a field the database already holds on a
`WriteBack_Applied = True` row** — reporting it as honored rather than writing it. The CSV stays
blank there on purpose: pre-filling a field Carl has overridden makes his override
indistinguishable from a front-end pre-fill. The pulled value decides *whether to write* and is
never itself written, so this does not weaken the one-way rule in
`04-log-and-write-discipline.md` — it enforces it earlier. Render mode **halts** when the pull is
missing or older than today; run `python3 scripts/fabric-pull-actions.py` first, every run.

The check is per-field: if Carl wrote back `Carls_Action` but left `Outcome` blank in the
database, a rejection notice may still pre-fill `Outcome`. And the database wins on
disagreement — on 2026-08-27 Fabric held `2026-08-26` for Company-519 where the tracker computed
`2026-08-25`; the divergence is reported, not reconciled.

**The script refuses, rather than warns, on the four rules this phase has broken before:**
a `Carls_Action_Date` with no `date_source` (or one that disagrees with the email it claims to
come from), a write with no `Job_ID` or an unknown one, ledgering an email classified `blocked`,
and archiving a named individual's mail. Each refusal names the incident behind it. Do not work
around one — a halt here means the classification is wrong, not the rule.

**Three findings from that first run, all of which had been invisible:**

- **The documented LinkedIn-notification sender was incomplete.** LinkedIn mail splits into
  **two families that never overlap**, and this file named only one of the four senders:

  | Family | Senders | Goes to |
  |---|---|---|
  | Message notifications | `hit-reply@linkedin.com`, `inmail-hit-reply@linkedin.com` | **Phase G** — trashed, never matched to a log row |
  | Posting digests | `jobalerts-noreply@linkedin.com`, `jobs-noreply@linkedin.com` | **Phase A/C** — already pulled, then trashed |

  This file previously named only `inmail-hit-reply@`; live mail uses the bare `hit-reply@`
  (all four instances on 2026-08-25 were "Message replied: …" recruiter threads), and
  `jobs-noreply@` appeared 2026-08-26 carrying recommendation digests. `inmail-hit-reply@` has
  never actually been observed in Carl's mail — it is covered, not relied on. A message
  notification is **never** a job alert and a digest is **never** a message, whatever the
  subject line says. `triage-match.py --self-test` asserts all four routings; run it after
  touching either pattern. Treat the sender list as observed, not fixed — if a digest or
  notification turns up needing a body read, the sender is new and belongs in that test.
- **A short-form company name in the mail defeats full-name matching.** Company-76
  rejected Carl from `careers@onebarnes.com`, naming only "the Barnes Job Portal". The row was
  in the log, applied 2026-07-15, and matched nothing — it would have been surfaced as an
  ask-Carl case, or appended as a duplicate row. The script now matches on a multi-token
  company's leading token *only when the role title also matches*, since the short name alone
  is nearly free evidence.
- **A forwarded job-alert digest matches beautifully and means nothing.** A friend forwards
  LinkedIn digests to Carl; each names four to six companies that all match log rows perfectly.
  The script detects the quoted LinkedIn envelope in the body and refuses to write from such an
  email without an explicit override. Route the postings to Phase B and ledger the forward —
  unlike LinkedIn's own digests, nothing else will ever consume it.

**Two scope calls made on that run, both narrowing what this phase touches:**

- **Non-job mail is ledgered but never archived.** Phase D scans the whole Inbox, so it sees
  newsletters, shipping notices and family mail. "Resolved" for those means "not ours" — it does
  not license moving them out of Carl's Inbox. Ledger them so they are never re-read; leave them
  where they are.
- **LinkedIn's own digests are not ledgered here.** Phase A already pulled them and Phase C
  trashes them; Phase D neither resolves nor records them. A digest a friend *forwarded* is the
  opposite case — nothing else consumes it, so it must be ledgered once its postings are routed.

**Mechanics**

1. `scripts/mail-triage-scan.applescript` scans the Inbox over the same rolling date window as
   `mail-pull.applescript` (2 days by default; pass a day count as the first argument to widen it,
   and run both phases with the same N — see "Rolling date window" in `scripts/mail-README.md`,
   especially the note that a skipped run permanently hides mail that ages out of the window),
   skips Message-IDs already in `triaged-message-ids.json`, and writes
   every remaining message (sender / subject / date / Message-ID / body) to
   `triage-candidates.json`. It is read-only with respect to Mail — it never moves or deletes.
2. Claude **reads each body and classifies by judgment** — see the warning below. **A LinkedIn
   message-notification email (sender `inmail-hit-reply@linkedin.com`, as distinct from a job-alert
   digest) is a separate classification outcome: trash it immediately, per Phase G.6 in `instructions/06-linkedin-messages.md`.** Do not
   classify it as a recruiter email under the exception below and do not match it to a log row —
   this is Carl's explicit call: these emails are disposable notifications, not a reliable record,
   and their disposition never depends on the status of the corresponding LinkedIn thread (revised
   2026-08-24 from an earlier defer-until-resolved design that turned out to be unnecessary).
3. Match to a log row on normalized Company + Role_Title (these emails carry no LinkedIn Job_ID).
4. Apply the blank-gate, prompt Carl per email, then write approved changes to both CSV copies.
5. Archive and ledger every **resolved** email; hold back every **unresolved** one — see the two
   rules immediately below. Do not conflate them.

**"Archive the emails acted on" means every resolved email, not just the ones that wrote a
change.** (Clarified 2026-08-10, after Carl found four resolved emails — including the Mental
Health Cooperative example two paragraphs down — still sitting in the Inbox weeks after they were
correctly classified.) A no-op is still a resolution: Claude read the body, matched it to a row,
and the blank-gate correctly declined to overwrite existing data. That email's job in this
workflow is done. Archive it in the same batch as the ones that did write a change, using
`scripts/mail-move.py --op archive` on **every** Message-ID classified this run, whether or not it
produced a CSV write. The earlier, narrower reading — "only archive the ones I actually wrote
something for" — is exactly what left the four stuck: three (Company-416, Company-573,
Company-218) had already resolved cleanly (two no-ops, one already-`Applied`) but
were never archived because the archiving step was skipped or, in the very first Phase D runs on
2026-08-08, because `mail-archive.applescript` did not yet exist — it was written the next day,
2026-08-09. **Run `python3 scripts/mail-move.py --op archive` as the mandatory last step of every
Phase D invocation, with no exceptions** — an empty `confirmed-archive-ids.txt` write (because nothing
resolved this run) is fine; skipping the call itself is not.

**Exception — do not archive individual recruiter or single-person emails, unless they're LinkedIn
message notifications (those go to Phase G instead).** (Added 2026-08-11; narrowed 2026-08-24 when
Phase G — LinkedIn message triage — was added.) "Resolved" for archiving purposes means resolved
*for the CSV/log* — it does not mean Carl has nothing left to do. A message from a named individual
(a recruiter, a hiring manager, an interviewer) — as opposed to an automated ATS/company-system
notification (Workday, Greenhouse, LinkedIn job-alert digests, "no-reply" confirmation senders) —
routinely still needs a live human reply, a scheduled call, or an interview to actually happen,
even after this workflow has finished classifying it and (if applicable) writing to the log.
Archiving it out of the Inbox at that point just buries something Carl still owes a response to.

This exception now splits by channel:
- **A LinkedIn message-notification email** — never reaches this archiving step at all. Per the
  classification rule above, it's trashed immediately at step 2, unconditionally — the reply lives
  in LinkedIn's own messaging platform, not in this email, and its disposition doesn't wait on
  anything.
- **A direct recruiter/hiring-manager/interviewer email, not via LinkedIn's messaging platform** —
  this exception is unchanged from 2026-08-11: classify normally, write any CSV change per the
  blank-gate, and ledger the Message-ID as usual so it doesn't get re-surfaced and re-asked-about
  next run — but leave the message itself sitting in the Inbox; do not add it to
  `confirmed-archive-ids.txt`. This applies whether or not the email produced a CSV write (an Company-698
  or Beacon Hill recruiter pitching a new, unlogged opportunity is exactly this case, not an edge
  case).

Automated system emails (a Workday rejection notice, a LinkedIn tracker confirmation) are not
covered by this exception and archive normally once resolved.

**An email that cannot be confidently matched or resolved is not "scanned," it's "blocked" — do
not add it to `triaged-message-ids.json` until it resolves.** The fourth stuck email (Company-412,
"Lead Data Architect," req JR0142165) exposed a worse version of the same gap: it had no matching
log row at all (applied outside this workflow, no LinkedIn Job_ID available from the Workday
confirmation), so it should have been surfaced as an ask-Carl case per "Job_ID on triage-sourced
rows" below — instead its Message-ID went straight into the ledger with nothing else done. Because
the ledger suppresses anything already listed, that made the email permanently invisible to every
future Phase D scan — worse than sitting unarchived, since unarchived-but-ledgered at least stays
processed. **The fix: only append a Message-ID to `triaged-message-ids.json` once it is fully
resolved** — written, correctly no-op'd, or answered by Carl. An email still waiting on a
Carl-supplied Job_ID/URL, an ambiguous company/title match, or any other open question stays
**out of the ledger** and **in the Inbox**, so it resurfaces on the next run instead of vanishing.
Batch these asks at the end of the run same as Step 1's Job_ID rule — don't block the rest of the
run on one unresolved email — but do not ledger or archive it until Carl answers.

**Recovery for this specific incident:** the three resolved-but-stuck emails were archived and the
Company-412 email was un-ledgered and asked about (see run history 2026-08-10). Going forward, treat
"an email's Message-ID is in `triaged-message-ids.json` but the message still shows in the Inbox"
as a bug signature, not a benign state — if noticed, it means the archive step didn't run for that
message. There's no automated audit for this yet; if it recurs, that's the signal a periodic
ledger-vs-Inbox reconciliation pass is worth building rather than continuing to catch it by eye.

**The blank-gate — the core safety rule.** The applied-workflow writes `Carls_Action` only when
it is blank; the rejection-workflow writes `Outcome` only when it is blank. Never overwrite an
existing value. This is not merely tidiness: on the first live run, 9 of 13 job-related emails
correctly no-op'd because of it, including a Company-416 rejection whose row already
read `Outcome = "Interview; Rejected"` — a blind write of `Rejected` would have destroyed the
record that Carl interviewed.

**Do NOT classify with a keyword/phrase list.** Read the body and decide. A phrase-matching
classifier was built from ~18 months of Carl's archived mail and then tested against the live
Inbox on 2026-08-08: it missed **3 of 5 real rejections** and produced a false positive on a
pest-control email. The misses were all near-miss wording — "decision to close this requisition"
vs. "decided to…", a curly apostrophe in "aren't able to move forward", "another candidate"
(singular) vs. "other candidates". Reading the bodies directly classified 13/13 and 7/7 correctly
in two separate samples. Phrase lists are a useful sorting prior; they are not the decision.

**Why subject lines can't be trusted either.** From the same training set: "Update on/to your
application" was 12/12 rejection, "…your candidacy" 4/4 rejection, "Application Status" 6/6
rejection, and "Thank you for applying…" 6/6 confirmation — but the large "…your interest in…"
family split **50/50**, and "Thank you from `<Company>`" is a rejection template while "Thank you
for applying to `<Company>`" is a confirmation, from the same company on consecutive days.

**`Reason` on a rejection.** Use the employer's stated reason when it is specific and not
boilerplate (e.g. Company-302's "only pursuing candidates that live or are licensed in the specific
states we operate in" → `state licensing requirement`). When the stated reason is boilerplate
("many applications", "more qualified candidates"), synthesize a 1–5 word reason from the row's
existing `Biggest_Gap` / `Comp_Flag` — that analysis already encodes the résumé-vs-JD comparison
done at evaluation time. Carl's parseable résumé, if a fresh comparison is ever needed, is at
`../../Carl_Wooldridge_Resume_Parseable_2026.txt`. Always surface the proposed `Reason` in the
triage prompt for confirmation rather than writing it silently.

**Ambiguous matches — ask, don't guess.** 24 companies occupy more than one row in the log
(Company-196 13, HCA 6, Company-30 5, Ladders 5). Employer mail also frequently names a different title
than the logged one — a Horizon3 rejection on 2026-08-08 cited "Director, Product Analytics"
against a logged row titled "Director of Analytics & Business Intelligence". Where company matches
but title doesn't disambiguate, surface it as a choice rather than picking a row.

**`Job_ID` on triage-sourced rows — resolved 2026-08-08.** Step 1 ("`Job_ID` is required on every
row… never append with `Job_ID` left blank") appeared to conflict with the rule under "Matching
rejections back to logged rows" ("if a rejection is clearly not in the log at all, append it as a
new row…"), which doesn't mention `Job_ID`. This surfaced live with a Company-681
rejection for a role Carl applied to outside this workflow.

**Step 1 wins: ask Carl for the URL/Job_ID, don't append a blank one.** When a triage-sourced row
has no `Job_ID`, surface it and ask — Carl supplied the LinkedIn URL on request and it was
backfilled. Do not invent, guess, or leave the field blank, and do not silently drop the rejection
instead. Batching the ask to the end of a run is fine; writing the row before the ID is in hand is
not.

**Scripted 2026-08-27.** `fetch-applied-tracker.js` was already written and is unchanged;
what the revamp added is the matching half, now a section of `triage-match.py`'s report. Exact
`Job_ID` lookup, the same blank-gate view as the email path, and three states per entry:
`writable` (row exists, `Carls_Action` blank), `already_applied` (no-op), `no_log_row`
(ask Carl). Tracker-sourced decisions use `tracker_job_id` instead of `message_id`, are limited
to `applied` / `noop` / `blocked` — the tracker cannot express a rejection — and must record a
`tracker_date` equal to the date being written.

**Approximate dates are Carl's to confirm, and the script enforces it.** LinkedIn exposes only
relative stamps, so anything reported in whole days (`Applied 2d ago`) is ±1 day. Such a date may
only be written with `date_source: carl_confirmed`; `date_source: job_tracker` is accepted only
for the minute/hour-precision stamps of a same-day application. This is the documented rule made
mechanical rather than remembered.

**The first scripted run (2026-08-27) proved the source's value three times in ten entries** —
after the email path had already run to completion over the same window:

- **`4457961944` Company-562, "Director, Analytics"** — the email path had blocked a bare
  `savista@myworkday.com` "Thank you so much for applying!" that named no role and matched no
  row. The tracker supplied the role, the `Job_ID` and the URL outright. This is the "ask Carl
  for the URL/Job_ID" case answering itself.
- **`4431006891` Company-519, "Data Platform & Analytics Manager"** — applied to, `Carls_Action`
  blank, and **no confirmation email anywhere in the window**. Invisible to the email path by
  construction. This is the second time this source has caught that (first: 2026-08-08).
- **`4454103847` Arkhya Tech, "MS Fabric Architect"** — the email path saw only a recruiter
  pitching the role and correctly wrote nothing, because a pitch is not evidence of applying.
  The tracker showed Carl had in fact applied. **A recruiter email and an application are
  different facts about the same posting; only the tracker carries the second one.**

**Do not treat the email path as complete on its own.** Nine of the ten tracker entries were
already correct in the log, which is what a working pipeline looks like — the value is entirely
in the tenth.

**Second source: LinkedIn Job Tracker.** (Added 2026-08-08.) In the same Phase D run, also check
`https://www.linkedin.com/jobs-tracker/?stage=applied` via `scripts/fetch-applied-tracker.js` —
this is a **step within Phase D**, not a separate phase, since it feeds the identical "applied to"
pipeline (match → blank-gate → prompt → write). Spin up a short-lived headless Chromium using the
same saved auth as `fetch-jds.js` (`~/.li-auth/storageState.json`); don't try to retain a browser
from Phase B — it may never have launched (no new postings that run), and this is one page load.

- **First page only, always.** The tracker holds hundreds of entries; page 1 is the most recent
  ~10, which is all a daily run needs. Do not add pagination without Carl's explicit say-so.
  **This is still the standing behavior and was re-confirmed 2026-08-28.**
  `fetch-applied-tracker-paginated.js` exists but is a **one-time backfill tool**, authorized
  2026-08-12 for a historical sweep — it is not the per-run path and must not be substituted for
  one without Carl saying so again.

  **Page 1 is roughly a five-to-six-day window at Carl's current rate** — measured 2026-08-27
  (10 entries spanning 08-22..08-27) and 2026-08-28 (08-23..08-28). Daily runs lose nothing; a
  longer gap silently drops applications off the bottom. `triage-match.py` now records the date
  of each successful tracker read in `scripts/phase-d-state.json` and **warns when page 1's
  oldest entry is newer than the previous read**, which is the signature of exactly that loss.
  Recovering from it is what the paginated variant is for.
- **Matching is exact, not fuzzy — this is the point of this source.** Every tracker entry carries
  a real `/jobs/view/<id>` link, so match on `Job_ID` directly. Confirmed 2026-08-08: 10/10 tracker
  entries matched a log row by Job_ID with zero ambiguity, versus the normalized-company-name
  guessing the email path needs. The script deliberately does **not** try to split each card's text
  into title vs. company — the anchor wraps the whole card with no reliable boundary between them
  (sometimes space-separated, sometimes run together, e.g. "...Product AnalyticsJobgether"), so for
  a matched row use the log's own `Company`/`Role_Title` and ignore the scraped `headline`; only
  fall back to `headline` to show an *unmatched* entry to Carl in readable form.
- **Catches applications with no confirmation email at all.** Confirmed 2026-08-08: an application
  submitted 55 minutes earlier appeared in the tracker with no corresponding email anywhere in the
  Inbox. Don't assume Inbox-mail triage alone is complete — this source finds real gaps in it.
- **Applied date is a computed approximation.** LinkedIn only exposes relative stamps ("52m ago",
  "1d ago"); the script resolves them to a calendar date at scrape time. Anything reported in whole
  days (not minutes/hours) is `applied_date_is_approximate = true` and is ±1 day — surface the
  computed date in the prompt for Carl to confirm rather than writing it silently, same as any
  other Phase D write.
- **Same halt handling as `fetch-jds.js`.** `HALT_EXPIRED` (re-run `save-auth.js`) vs.
  `HALT_CHALLENGE` (stop, report to Carl, do not re-auth and retry) mean the same things here.

**Third source: the applied badge on the JD itself.** (Added 2026-08-31 at Carl's request.)
Phase B's applied-badge check writes observations to `scratch/applied-badge.json` while it has
each JD body in hand — see "Applied-badge check" in `instructions/01-intake-and-fetch.md`. Those
entries feed this same pipeline (match → blank-gate → prompt → write) as a third source, with
`date_source: jd_applied_badge`.

Everything the tracker source does applies here unchanged: **matching is exact** (the badge is
observed on a known `/jobs/view/<id>`, so it joins on `Job_ID`), the **date is approximate**
whenever LinkedIn reported it in whole days, and a decision carries exactly one of
`message_id` / `tracker_job_id` / `badge_job_id`. When two sources name the same posting the
renderer merges them and **halts if they set a field differently** — same rule, now across three.

**This source is a backstop and is ranked last.** Two limits, both structural:

- **It only sees postings Phase B fetched**, which is the post-dedupe *new* set. An
  already-logged posting dedupes out and its body is never retrieved — on 2026-08-31, 60 of 166
  extracted postings were dupes or reposts and none were fetched. Applied-to roles are
  disproportionately in that pile, so the badge misses exactly the population it looks best at.
- **It is not a sweep and has no window guarantee.** It reports whatever happened to come
  through, so it can never be reasoned about as coverage the way tracker page 1's five-to-six-day
  window can.

**Therefore it does not reduce the tracker's job.** The tracker stays a required, every-run
source and `--skip-tracker` keeps its existing warning. A run with badge entries and no tracker
read is still a halt. Where badge and tracker disagree on date, **the tracker wins** — it reads
LinkedIn's own application record, while the badge is rendered page text.

**Implemented in `triage-match.py` on 2026-09-01.** Match mode reads `scratch/applied-badge.json`
(override with `--badges`) and reports every entry with its log row, its blank gate, and its
tracker overlap; render mode accepts `badge_job_id` decisions with `date_source:
jd_applied_badge` or `carl_confirmed`. A missing badge file is a note, never a halt — the tracker
is the required source, this one is not. Four refusals are specific to it: a classification other
than applied/noop/blocked (the badge says one thing only), an approximate date not confirmed by
Carl (in practice all of them — LinkedIn never timestamps the badge exactly), a decision carrying
more than one of `message_id` / `tracker_job_id` / `badge_job_id`, and a badge date the tracker
contradicts, which halts and asks for the decision to be re-issued from the tracker rather than
silently re-dating it here.

**The first live read confirms the "backstop, not coverage" framing.** On 2026-09-01 the scan
found 6 badges and the Job Tracker had already caught all 6 — **0 badge-only**. On the same
data the two sources disagreed on the date for 2 of the 6 (Company-535 4458425988, AllClear
4459364332), by one day each, which is exactly the whole-day approximation the confirm rule
exists for. The gap this source was added to close has not yet materialized; it is here for the
run where the tracker's page-1 window misses something.

### Phase E — stale-Pursue closure sweep

(Added 2026-08-09, after Carl caught a `Pursue`-verdict, blank-`Carls_Action` row (Company-169,
Job_ID 4449138308) that had gone to "No longer accepting applications" after it was logged, with
nothing in the workflow ever re-checking it.) The closed-posting check in Step 3 only fires **at
JD-fetch time** — the moment a posting is first evaluated. Nothing previously re-checked a posting
after that, so a `Pursue` row can sit indefinitely showing a live opportunity that actually closed
days or weeks ago, until Carl happens to click through and notice.

**What this phase does.** For every row where `Verdict` is `"Pursue"` **or** `"Review"` **and**
`Carls_Action` is blank — i.e. a posting Carl hasn't acted on yet and might still apply to —
re-fetch the LinkedIn
page via the same Tier 1 signed-in headless Chromium runner (`fetch-jds.js`) used elsewhere in
this workflow, and run the closed-posting check against the fresh page. This is a **fact
re-check, not a re-evaluation**: `Score`, `Verdict`, `Role_Type`, `Comp_Flag`, `Biggest_Gap`,
`Biggest_Strength`, and `Recommended_Action` are never touched by this phase, even if the
re-fetched JD text looks different from what was originally read. Only closure status is checked.

**If "No longer accepting applications" is now present**, apply the exact same write as the Step
3 closed-posting check — `Carls_Action = "None"`, `Carls_Action_Date` = today's date (the date of
the sweep), `Reason = "No longer accepting applications"` — to both CSV copies, following the same
validation and backup discipline as any other write. This is the same sanctioned exception as Step
3: closure is an observed fact, not a judgment call, so it does **not** need Carl's per-row
confirmation the way Phase D's `Carls_Action`/`Outcome` writes do. Still report every row changed
in the run summary, listed by name — this changes records even though it doesn't need a prompt.

**If the posting is still open**, do nothing to that row — no write, no Notes churn, don't
re-stamp `Date_Evaluated` or anything else just because it was re-checked.

**Same pacing and volume caps as Step 3** — 3–8s randomized delay between postings, ~25 postings
per run, split into multiple sequential sweeps for a larger backlog rather than raising the cap
(the first sweep, 2026-08-09, covered 34 blank-`Carls_Action` `Pursue` rows in two batches of 25
and 9). Same halt handling too: `HALT_EXPIRED` → tell Carl to re-run `save-auth.js`;
`HALT_CHALLENGE` → stop and report, don't re-auth and retry.

**When to run it.** Treat this as a standard step in "run job alert evaluation process" —
run it once per full pipeline invocation, after Phase D, since the set of eligible rows only
grows via Phase B's new `Pursue` rows and only shrinks via Carl acting on them (which Phase D just
reconciled). It's also fine to run standalone, on request, without the rest of the pipeline (no
new mail needed) — it only touches already-logged rows.

### Phase F — monthly Skip audit (recall check)

(Added 2026-08-10, alongside the criteria tightening of the same date.)

Every criteria change made on 2026-08-10 was derived from false positives — roles marked Pursue
that Carl passed on. **False negatives were never measured**, because roles the process skipped
were never re-read. That asymmetry is the main risk in the revision: the filter can be tightened
until it starts eating good roles, and nothing in the workflow would ever reveal it.

Phase F is the counterweight. Run it **monthly**, or on request.

1. Pull every row from the last 30 days where `Verdict = "Skip"` and the score fell in the
   **60–69** band — the band most likely to contain a wrongly-rejected role.
2. Also pull every row skipped by a gate added on 2026-08-10: **G6** (industry), **G10** (stack
   absence), **G11** (domain-as-deliverable), **G12** (travel), and every row where the Director+
   seniority screen fired. (There is no G9 — see section 4.0.)
3. Also pull every row that took the **−10 people-management deduction** and landed in the 60–69
   band. This is the population a G9 gate would have killed outright, and it is the specific place
   to watch: if Carl repeatedly says he'd have looked at these, the deduction is too heavy and the
   2026-08-10 call needs revisiting with evidence. If he never does, the deduction is doing its
   job and a gate was correctly rejected.
4. Also pull every row listed under **Bridge candidates** that Carl did not act on, so the bridge
   lane's real value is measured rather than assumed.
5. Present them to Carl as a compact list — company, title, score, gate or score band, and one
   line on what killed it. Not full write-ups.
6. Ask one question: **were any of these worth a look?**
7. Record the answer. If Carl flags roles in the same gate repeatedly, that gate is over-firing
   and the rule needs loosening — bring the pattern back with the evidence rather than adjusting
   it silently.

**Report the ratio in the run summary each month**: how many audited, how many Carl would have
wanted. That number is the recall estimate, and it is the only check on whether this revision
went too far. A month with zero flags means the gates are calibrated. A month with three or more
means something is too tight.

**Do not skip this phase because nothing looks wrong.** The whole point is that over-tightening is
invisible from the inside — a filter that's cutting good roles produces exactly the same run
summary as one that's working.

#### Mechanics — scripted as of 2026-08-28

`scripts/recall-audit.py`. Two modes, on the `triage-match.py` pattern: the script selects and
measures, and never decides what a posting *means*. It writes nothing to
`JD_Evaluation_Log.csv` — its only writable file is `rubric/learning_log.md`, in `--record`.

```
python3 scripts/fabric-pull-actions.py            # once, at the start of the run
python3 scripts/recall-audit.py                   # select, measure, present
#   -> scratch/recall_audit_YYYYMMDD.md      the list Carl reads
#   -> scratch/recall_answers_YYYYMMDD.json  the file his answers go into
python3 scripts/recall-audit.py --record scratch/recall_answers_YYYYMMDD.json
python3 scripts/recall-audit.py --self-test
```

**It halts on a stale or missing Fabric pull.** Phase F writes nothing, so this is not the
write-safety guard D and E carry — it is a correctness guard on the selection. Every criterion
here turns on whether Carl has acted on a row, and the pull is the only place his write-backs
live. A stale pull puts rows he has already answered back in front of him *and* counts them in
the recall ratio as unanswered. Age is measured in minutes (`--max-pull-age-minutes`, default
120), because the pull is once per run, not once per day. `--skip-pull-check` overrides and
names the cost out loud.

**Selection comes from `Reason`, never from a gate label in `Notes`.** (Measured 2026-08-28.)
Gate labels appear in the narrative fields of 209 rows, but of the 34 rows whose text names
G10, only 9 were killed by it — the rest record a gate that was *checked and did not fire*,
including `Pursue` rows. `Reason` carries the rubric's own prescribed wording
(`"wrong stack (X)"`, `"X domain gate"`, `"director+ scope"`, `"industry exclusion (X)"`) and
is the authoritative kill field. Label-vs-`Reason` disagreements are reported as a
discrepancy count, so wording drift stays visible, but they never select a row.

**Bridge candidates are Lane 12 and 65–69** (`02-evaluate-and-report.md`), not every row whose
`Role_Type` string contains the word "bridge". Read the wrong way it selects 251 rows instead
of 25, and the audit drowns.

**The people-management deduction is detected as `Pts_Scope = 0`** — `weights.json` records it
as "with scope=0", and `Pts_Deductions` is an aggregate that cannot isolate one deduction from
another. The text evidence is reported alongside; it is not what selects.

#### An application made before the row was evaluated is not an override

(Added 2026-08-28, from the first real Phase F run, and it inverted the run's headline finding.)

The first pass measured the Director+ screen at a **30% override rate** on n=46 — review-class
by `rubric-learn.py`'s own boundaries, comfortably over the n floor, and apparently the
strongest evidence yet that a gate was too tight. It was an artifact. **13 of those 14
"overrides" were applications Carl made before the row existed** — dated 2026-05-14 to
2026-07-29 against evaluations dated 2026-08-12. The 2026-08-12 backfill retro-logged months
of his application history and scored every row under the current rubric. The gate could not
have stopped an application made two months before it fired.

Corrected, the Director+ screen measures **2%**. Every Phase F gate lands in veto class:

| gate | fired | true overrides | raw rate | true rate |
|---|---|---|---|---|
| G11 domain gate | 23 | 2 | 22% | 9% |
| people-management scope | 15 | 1 | 27% | 7% |
| Director+ screen | 46 | 1 | 30% | 2% |
| G10 wrong stack | 10 | 0 | 20% | 0% |
| G12 travel | 5 | 0 | 0% | 0% |
| G6 industry exclusion | 1 | 0 | 0% | 0% |

**This is not a small correction and it is not confined to Phase F.** 142 of the 400 actioned
rows in the log carry a `Carls_Action_Date` earlier than their `Date_Evaluated`. Any
measurement that counts `Carls_Action = "Applied"` without checking the order of the two dates
is measuring the backfill. `rubric-learn.py` does exactly that — see the note under Phase F in
`REVAMP_PLAN.md`.

**A same-day pair counts as an override.** The order within a day is unrecoverable, and ties go
against the gate: the failure this phase exists to catch is a gate quietly eating good roles,
so the ambiguous case should read as "too tight", not as "working".

**Report both numbers.** The script prints `raw rate` beside `true rate` rather than silently
correcting, because the gap between them is itself the finding.

---
