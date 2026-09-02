# Phase G — LinkedIn message triage and replies

*Part of the JobSearch workflow. Start at [`COWORK_INSTRUCTIONS.md`](../COWORK_INSTRUCTIONS.md) — it holds the naming convention, the run-type map, and the rules that apply everywhere.*

**When to load this file:** Load ONLY for LinkedIn inbox work. Nothing in a JD evaluation run touches this.

---

### Phase G — LinkedIn message triage and reply drafting

(Added 2026-08-24.) Phases A–F process **postings**. This phase processes **people**. Recruiter
outreach arrives in LinkedIn's own messaging platform — not primarily as email — and nothing in
this workflow previously read it, classified it, or answered it. The one prior acknowledgement
(the recruiter exception above) just left it sitting in the Inbox indefinitely.

**Phase G's goal is not the same as Phase B's.** Phase B answers "is this posting worth applying
to?" and writes a scored row. Phase G answers "can I turn this person into an interview?" and
writes a **question**. A LinkedIn thread is a live channel — unlike a posted JD, a thin pitch can
be made informative by asking the recruiter directly. So Phase G's output is a drafted reply that
tries to move a cold/warm lead toward hot, never a CSV row and never a sent message.

**This phase never writes to `JD_Evaluation_Log.csv`, under any circumstance.** Message-derived
leads are guesses next to a fetched JD, and letting them into the log would pollute the very
scoring data Phase F's recall audit depends on. When a lead goes fully hot — a real JD or
equivalent detail is already in hand from the thread — Phase G flags it in the run summary and
stops. Carl asks for the full JD evaluation himself, by name, when he's ready; only then does the
normal Phase B/4.0 rubric touch it.

**Secondary goal:** get LinkedIn's Focused inbox down to only two things — threads Carl owes a
reply to, and hot leads. Everything else moves to Other, Spam, or Archived, per the residency rule
below. **Nothing is ever deleted.**

**Two hard rules, at the same weight as the HALT conditions in Step 3:**
- **Never send a message on any channel, under any circumstance.** Every draft is a file Carl
  reads and sends himself — never LinkedIn's compose box, never an email client, never a connection
  request.
- **Never delete a thread from a person.** No script in the standing Phase G pipeline
  (`fetch-linkedin-messages.js`, `linkedin-msg-dispose.js`) may contain a code path that clicks
  Delete. **The one sanctioned exception** (added 2026-08-24, at Carl's explicit direction after
  reviewing his own Archived mailbox): LinkedIn's own Sponsored / "LinkedIn Offer" promotional
  messages, deleted via the separate one-off `scripts/sweep-delete-sponsored.js` utility — see
  "Sponsored/LinkedIn Offer cleanup" below. This exception is scoped narrowly to LinkedIn's own ad
  content; it does not loosen the rule for any real person's thread, however cold or junk.

#### G.1 — Absolute disqualifiers (still fatal)

Carl's non-negotiables kill outright here exactly as they do in the Step 4.0 hard gates:
- **Location** — see the location refinement immediately below; this fires only for an
  *unambiguous* full relocation or unqualified full-time onsite requirement outside Nashville
  Metro, not for anything short of that.
- **Employer exclusion** — Company-30, Company-463, Company-59, UMG Nashville.
- **Industry exclusion** — cannabis, gambling, adult, firearms, MLM, faith-based-as-qualification.
- **Recurring international travel.**

Any hit → **Cold**, move to Other, decline drafted per "Reply drafting" below (2026-08-25: a
short polite decline is now drafted whenever the ball is in Carl's court, including here).
**Unattended** — the classification itself is a mechanical fact, same footing as the closed-posting
check in Step 3; only the reply-drafting step (if a reply is actually owed) follows the usual rule.

**Location refinement (added 2026-08-24, after the first live batch).** The literal Step 4.0
Location hard gate reads any on-site/hybrid posting outside Nashville Metro as a kill. On a
LinkedIn thread — where Carl can actually ask — that's too blunt, and it fired wrong twice in the
first real batch:
- **Ambiguous location (a city named, no "remote" or "onsite" stated) is not an onsite
  assumption.** A bare "Location: Los Angeles, CA" does not mean onsite — it means unknown. Treat
  it exactly like any other unknown: if the role is otherwise in-lane, it's Warm, and the draft
  asks whether it's remote or has any remote flexibility.
- **Explicit partial/hybrid onsite** (e.g., "2 Days Onsite") for an otherwise strong, in-lane role
  does **not** auto-kill either. Warm instead — draft a reply expressing genuine interest and
  asking specifically about remote flexibility or a reduced onsite cadence, being upfront that
  Carl is Nashville-based and not relocating.
- **G.1 still fires** for an unambiguous full relocation requirement, or an explicit unqualified
  "100% onsite" / "on-site, no remote" posting outside Nashville Metro with no ambiguity and no
  partial-remote language — that remains a mechanical, unattended Cold.
- The line between "ambiguous/partial → ask" and "unambiguous full onsite → kill" is still being
  calibrated. If a borderline case comes up, propose the disposition and say why rather than
  applying either rule silently.

#### G.2 — Lane check

Not genuine BI / Analytics / Data Architecture function work → **Cold**, Other, decline drafted
per "Reply drafting" below. **Prompts Carl** — lane fit on a thin pitch is a judgment call, not a
mechanical fact.

#### G.3 — Weighted negatives (heavy, but not fatal alone)

**This deliberately differs from Step 4.0 and the hard-override triggers in the Scoring rubric.**
On a posted JD, contract/C2C, consulting-delivery, staffing-board sourcing, and sub-floor comp are
each an automatic `Verdict = "Pass"` with no exceptions. On a live LinkedIn thread they are not
automatic kills — Carl can ask a person for the missing detail in a way he can't ask a job
posting, and a real conversation is worth more latitude. Each of the following is a serious strike;
**none is fatal alone**:

- Contract, C2C, or fixed-term
- Consulting-delivery firm (the major-firm list and delivery-language pattern from the Hard
  override triggers section)
- Staffing board or anonymous end client
- Comp below the veto line — **VETO_LINE salary, or roughly $60/hr for a contract rate** (state the
  conversion so a contract lead and a permanent lead are judged against the same line). A lead
  between VETO_LINE and FLOOR is below the scoring floor but not disqualified — treat it as a weighted
  negative under G.3, not an absolute one.
- Predominantly people-management, not IC (per Carl's context in `instructions/03-scoring-rubric.md`: a mostly-IC role with some
  direct reports is still a good lead — only *predominantly* managing people is the negative)
- Stack absence — a Tier-3 competitor platform named as the primary tooling, with none of Carl's
  stack present

**Rule: two or more *confirmed* strikes → Cold, Other, decline drafted per "Reply drafting"
below.** One confirmed strike, with
everything else in-lane or unknown → **Warm** — draft a reply that asks about the strike. **An
unknown is never a strike.** That distinction is the entire mechanism by which a warm lead becomes
hot: a thin pitch has lots of unknowns, and Phase G's job is to ask about them, not penalize their
absence.

**Prompts Carl** on every Cold produced at this step.

#### G.4 — Temperature

- **Hot** — in lane, no fatal gate, and a real JD or equivalent detail (comp, scope, employment
  type) is already in the thread. Nothing material left to ask. → Stays in Focused. Ledgered as
  hot. Listed in the run summary as ready for JD evaluation on request. **Never auto-logged to the
  CSV** — see the goal statement above.
- **Warm** — plausibly in lane, not disqualified, but material unknowns remain. → Stays in Focused.
  Draft a reply asking the unknowns (see "Reply drafting" below). **Exception — the Analyst/Engineer
  bar** (added 2026-08-24): Carl's current target is Lead/Architect/Manager/Director level, not
  Analyst or Engineer, at this stage of the search. For a role titled at the Analyst or Engineer
  level, an otherwise-Warm classification still needs *something intriguing* before drafting a
  reply — a near-perfect tech-stack match is the confirmed bar (Sophie Fox's "Business Intelligence
  Analyst" pitch cleared it on SQL/T-SQL/SSRS/SSIS/Power BI alignment alone). A generic or unverified
  Analyst/Engineer pitch with nothing distinguishing it does not clear the bar — hold it and ask
  Carl rather than drafting by default. This bar does not apply to Lead/Architect/Manager/Director
  titles, which are Warm on the normal terms above.
- **Cold** — killed at G.1, G.2, or G.3. → Other, decline drafted per "Reply drafting" below.
- **Junk** — not job-search related at all (a SaaS pitch, coaching services, event marketing, an
  MLM approach). → **Other, no reply drafted.** This is not a real person awaiting a job-related
  answer, so the 2026-08-25 "always draft when the ball is in Carl's court" rule doesn't reach it —
  it's noise, not a conversation. LinkedIn's Spam folder is never used by this phase — see "Why
  Spam is never used" below. This is not a pending calibration; it's the permanent rule.

**Prompts Carl** on every Warm and every Hot classification.

**Why Spam is never used.** (Confirmed live 2026-08-24 — see the discovery step below and
`scripts/linkedin-msg-dispose.js`'s header comment.) LinkedIn's per-thread action menu offers
`Move to Other`, `Label as Jobs`, `Mark as unread`, `Star`, `Mute`, `Archive`, `Report / Block`,
`Delete conversation`, and `Manage settings` — there is no plain "move to Spam." The Spam folder
(one of the four real filter categories alongside Focused/Other/Archived) is only reachable via
`Report / Block`, an outward-facing action against the sender's LinkedIn account, not an internal
move. Junk goes to Other instead, permanently — this is a design decision, not an open item
awaiting verification.

#### G.5 — Focused residency rule (overrides G.1–G.4's default placement)

A thread stays in **Focused** only if one of these is true:
- The last message in the thread is **14 days old or less** — regardless of temperature or draft
  status (see the correction immediately below).
- It is a **hot** lead with activity in the last 14 days.

Everything else leaves Focused, and the **14-day age is the single, uniform gate** — not two
separate thresholds. **A drafted-but-unsent reply does NOT exempt a thread from this clock.**
(Corrected 2026-08-24, after Carl found six Warm threads with pending drafts sitting untouched in
Focused for 3+ weeks — the original wording, "Carl owes a reply... including a draft pending his
send," was read as an indefinite exemption. It isn't one. If Carl hasn't actually sent a reply
within 14 days of the last message, the lead is stale by definition, exactly like an unanswered
cold pitch — the existence of a draft file doesn't change that.) Disposition once the 14 days pass:
- **Carl sent at least one message in the thread, ever** → Archived. **Unattended.**
- **Carl never sent a message in the thread** (including "only an unsent draft exists") → Other.
  **Unattended.** Move the corresponding draft file to `LinkedIn_Drafts/archive/` in the same step —
  it's now stale and shouldn't be presented as ready-to-send.
- **1st-degree connection** follows the identical rule — degree alone never keeps a thread in
  Focused past 14 days of silence, and never pulls one out of Focused early either. **Never archive
  an active lead on connection degree alone** — a recruiter Carl has connected with is a 1st-degree
  connection, and that is exactly the thread this rule must not catch while it's still within the
  14-day window.

This single 14-day check replaces the earlier two-tier design (a 90-day catch-all plus a separate
14-day-if-Carl-already-replied rule) — 14 days is strictly tighter, so the 90-day threshold never
fired on its own once this was in place. Keep the logic simple: one age check, one branch on
whether Carl ever sent anything in the thread.

**"Quiet" means the recruiter hasn't responded — check whose turn it is, not just who spoke
last.** (Added 2026-08-24, after the first live batch got two threads wrong this way.) A reply
being the most recent message in the thread does not by itself mean the recruiter went silent —
check *who the last message was actually addressed to*. Anthony Copes's thread showed no message
in 14 days, but the last message was *his* question to Carl ("are you free this afternoon?"),
never answered — the silence was Carl's, not the recruiter's, so this is a live reply-owed thread,
not a quiet one. Read the actual content and direction of the last message before applying the
14-day quiet rule; don't infer it from elapsed time alone.

**Prompt for a status check on any thread with real momentum before finalizing its disposition.**
(Added 2026-08-24.) A thread showing escalating back-and-forth — comp/scope negotiated, a call or
interview scheduled, multiple exchanges — often continues off-platform (phone, email) once contact
is established, and the LinkedIn thread stops reflecting reality. Stephen Dance's thread showed a
scheduled technical-assessment interview as its last LinkedIn message and read as an open Hot
lead — the real state, only known to Carl, was that the conversation moved to phone, he interviewed
twice, and withdrew over fit. Before finalizing a disposition on any such thread, ask Carl what
actually happened rather than inferring status purely from the visible LinkedIn content.

**Read the full thread before classifying, not just the most recent message or a preview
snippet.** (Added 2026-08-24, the same root cause behind both misses above — Jack C.'s thread was
initially read as an open Warm lead when Carl had already written an explicit decline further up
the same thread: "makes this one not a fit... good luck filling this one.") This mirrors Phase D's
"read the body, don't trust the subject line" rule — a thread's classification comes from reading
everything in it, not from whichever message happens to be easiest to see.

#### Reply drafting

**Always draft a reply whenever the ball is in Carl's court** — i.e. whenever `Status` would read
`Received` (see G.7). (Added 2026-08-25, at Carl's explicit direction, superseding the two
no-draft rules below.) This holds regardless of temperature: a Warm lead gets the
clarifying-questions draft as before, but a Cold lead now gets a short, polite decline rather than
silence, and a Hot lead gets a short acknowledgment/next-step note rather than nothing. The point
is that every thread awaiting Carl's reply should have *something* ready for him to send — even
if it's just "Thanks, appreciate you thinking of me" — rather than leaving him to compose a
courtesy reply from scratch. This does not change anything else about temperature: Cold still
means Other with no further engagement sought, Hot still means flagged for a full JD evaluation on
request — only the "draft nothing" behavior is gone.

- **Warm lead** → a clarifying-questions-first draft targeting the confirmed strike and the
  material unknowns from G.3/G.4 — e.g. rate, duration, and conversion path for a contract strike;
  real scope (technical vs. people-lead) for a management-heavy pitch; comp range when unstated.
  State Carl's stack briefly, no overclaiming.
- **Never phrase a contract/C2C question as "only open to direct-hire."** (Corrected 2026-08-24.)
  Carl is open to contract/C2C — the bar is just raised: comp, title, stack, or perks need to be
  genuinely exceptional to be worth it. Phrase the question as an open one ("direct W2 or a
  contract placement?"), not as a stated restriction, and don't imply contract is a non-starter.
- **Sign off every draft "–Carl"** (en dash before the name, added 2026-08-24), not a bare "Carl."
- **Cold lead** → **draft a short, polite decline** (e.g. "Thanks for reaching out, but this isn't
  a fit for what I'm targeting right now — appreciate you thinking of me.") rather than moving to
  Other silently. Still move the thread to Other per G.1–G.4 as usual; the draft is just handed to
  Carl in case he wants to close the loop with the person, not a precondition for the move.
- **Hot lead** → **draft a short acknowledgment/next-step note** (e.g. "This looks like a strong
  fit — let me get you a fuller read on it and follow up.") rather than nothing. Still flagged for
  Carl to request the full JD evaluation separately; the draft just covers the immediate reply so
  the thread doesn't sit unacknowledged while that happens.
- **No phone number, no résumé attachment, ever** — Carl adds his own contact details himself if he
  chooses to move forward.
- **Draft storage.** LinkedIn has no drafts API to write to; a reply here is text handed to Carl to
  paste into the message box himself. One Markdown file per thread in `LinkedIn_Drafts/` (create
  the folder if it doesn't exist yet), named `YYYY-MM-DD_Firstname-Lastname_Company.md`:

  ```markdown
  ---
  thread_id: <linkedin thread urn>
  thread_url: https://www.linkedin.com/messaging/thread/<urn>/
  participant: <name>
  company: <company>
  temp: warm
  strikes: [<list>]
  unknowns: [<list>]
  drafted: <date>
  status: pending_send
  ---

  ## Draft reply

  <text Carl pastes into LinkedIn himself>
  ```

  A thread whose draft is `pending_send` is not re-drafted on a later run — it's re-checked only
  for staleness (per G.5). Once a thread goes cold or the draft is sent, move its file to
  `LinkedIn_Drafts/archive/` so the top level stays scannable.
- **Every draft prompts Carl before the file is written** — same footing as Phase D's per-email
  prompt, because this is text written in Carl's voice about his own job search.

#### Mechanics — read/write split, same shape as Phase A/C

Two new scripts, deliberately split into a read step and a write step — the same reasoning as the
`mail-pull.applescript` / `mail-trash.applescript` split above: a thread is only moved after its
disposition is confirmed, correlated by **thread ID, never by list position**, and a failed or
partial run leaves every thread untouched.

- **`scripts/fetch-linkedin-messages.js`** (read-only) — modeled on `fetch-applied-tracker.js`, the
  closest existing precedent for scraping an authenticated LinkedIn SPA. Reuses its
  `chromium.launch({headless:true})` + `newContext({storageState: STATE_PATH})` pattern (same
  `~/.li-auth/storageState.json`, same `LI_STATE_PATH` override), its `HaltError`/`checkForHalt()`
  pair and HTTP-999/challenge-text checks, its content-signal `waitForFunction` instead of a fixed
  timeout, and its selector-light ancestor walk — including the documented trap not to use
  `a.closest('li')`, since the anchors on these LinkedIn SPA pages aren't wrapped in per-card list
  items and it returns a shared ancestor instead (hit 2026-08-08 on the tracker page). Loads
  `/messaging/?filter=focused`, scrolls to load the backlog, and writes `scripts/linkedin-threads.json`
  (thread id, URL, participant, connection degree, last-message timestamp and direction, body text).
- **`scripts/linkedin-msg-dispose.js`** (write) — reads a validated `{thread_id, disposition}` list
  and performs the moves. Same halt handling as above; 3–8s randomized jitter between operations,
  matching `jitterMs()` in `fetch-jds.js`; hard cap of **25 threads per batch**, matching
  `MAX_POSTINGS_PER_RUN`; **no Delete code path, anywhere in the script.** Appends outcomes to
  `scripts/linkedin-dispose-log.txt` in the same `<date>  <STATUS>  <id>` format as
  `mail-trash-log.txt`.
- **`scripts/linkedin-thread-ledger.json`** — one record per thread, keyed by `thread_id`, tracking
  `thread_url`, `participant`, `participant_degree`, `company`, `first_seen`, `last_message_at`,
  `last_message_from`, `temp`, `strikes`, `unknowns`, `disposition`, `disposition_applied_at`,
  `draft_file`, `draft_created_at`, `awaiting`, `notes`. This intentionally differs from the flat
  Message-ID arrays in `pulled-message-ids.json` and `triaged-message-ids.json` — those answer one
  idempotent question ("have I seen this?"), while a thread's temperature, draft status, and
  staleness all change over time and need a mutable record.

#### G.6 — Mail-side cleanup (trash on sight, no deferral)

The Apple Mail side of this phase is pure de-duplication — the real triage happens in LinkedIn
itself, per the classification and residency rules above, not in Mail.app. A LinkedIn message
often also arrives as an email notification of the same message.

**Trash these emails as soon as they're found, unconditionally — never wait on the corresponding
LinkedIn thread's disposition.** (Simplified 2026-08-24, at Carl's explicit correction, from an
earlier "defer until the thread is resolved" design.) Carl's reasoning: these emails are periodic
notifications, not a reliable record — they aren't even a trustworthy signal that a message has
actually landed in LinkedIn's messaging platform, which is the sole canonical source of truth for
what Carl has and hasn't received. A thread sitting Held/pending in LinkedIn, or not yet looked at
at all, is not a reason to keep its email copy around — there is nothing in Mail.app worth
preserving here, regardless of triage state on the LinkedIn side.

- **Confirmed sender: `inmail-hit-reply@linkedin.com`** (confirmed live 2026-08-24 — none had shown
  up in the historical `/processed` sample used to originally write this phase, but a live 30-day
  Inbox scan turned up several). The display name is the recruiter's own name, not "LinkedIn,"
  which is why classification still needs the sender *address*, not the display name — e.g. `Cj
  Liles <inmail-hit-reply@linkedin.com>`. This is a real, checkable signal now, not a guess — but
  keep reading the body too (same as the rest of Phase D) in case LinkedIn ever adds a second
  notification sender address; don't assume this one address is exhaustive forever.
- **Same rolling window as the rest of the pipeline — never an unbounded Inbox search.** (Corrected
  2026-08-24, at Carl's explicit direction, right after a one-time historical cleanup swept back to
  2017.) G.6 finds its candidates from `mail-triage-scan.applescript`'s normal output
  (`triage-candidates.json`), scanned over the same N-day window as `mail-pull.applescript` — see
  "Rolling date window" in `scripts/mail-README.md`. Trashing on sight (above) means "don't wait on
  LinkedIn thread status," not "search all of Mail.app history every run." A years-deep sender-based
  sweep is a **deliberate, one-off, Carl-requested recovery action** — one actually happened on
  2026-08-24 (found and cleared ~40 stuck emails going back to 2017, root cause in the next bullet)
  — never something this phase does automatically as part of "run job alert evaluation process."
- Phase D's scan can trash these directly the moment it identifies them — there is no need to check
  LinkedIn thread status first, and no need for a deferral ledger. (`scripts/linkedin-msg-email-ids.json`
  existed for the old defer-until-resolved design and is no longer used; it's cleared out rather than
  deleted, in case a future variant of this rule needs it again.)
- **A ledger can silently poison this check within the normal window too — worth knowing, not
  worth re-running unbounded by default.** (Found and fixed 2026-08-24.)
  `mail-triage-scan.applescript` skips any Message-ID already in `triaged-message-ids.json`. A batch
  of `inmail-hit-reply@linkedin.com` emails had been ledgered under the *pre-Phase-G* recruiter
  exception (classify, ledger, but deliberately leave in the Inbox) — correct under the old rule,
  but invisible to every future scan under the new one, since "already triaged" now silently means
  "already handled" when it doesn't. If Carl reports a LinkedIn notification email still sitting in
  the Inbox despite this phase running, and it falls inside the normal N-day window, don't trust the
  ledger for it — check that one sender/Message-ID directly rather than the scan. **Do not respond
  to that report by re-running an unbounded, all-history sender search** — that's the one-off
  recovery action above, and it requires Carl asking for it specifically, the same way the
  Sponsored/Offer cleanup below does.
- Trash via `scripts/mail-trash.applescript`, passing the optional ID-file argument
  `confirmed-trash-linkedin-msgs.txt` — **a separate file from Phase C's `confirmed-trash-ids.txt`**,
  since Phase C consumes that file earlier in the same pipeline invocation and sharing it would
  collide.
- Append the trashed Message-IDs to `triaged-message-ids.json` once the trash step succeeds — same
  shared ledger Phases A–D already use.
- **This is trash, not archive**, unlike the rest of Phase D's default for resolved human mail. A
  LinkedIn notification email is a disposable copy of something whose durable record lives in
  LinkedIn itself, not in Mail.app — Carl's explicit call, not an inconsistency with the rest of
  Phase D.

#### Sponsored/LinkedIn Offer cleanup (one-off utility, not part of the standing pipeline)

(Added 2026-08-24.) Carl reviewed his own Archived mailbox and found it full of LinkedIn's own
promotional content — Sponsored ads and "LinkedIn Offer" messages, going back years, mixed in
alongside real archived recruiter threads (Jack C., Kaitlyn Moreschi, Stephen Dance). He asked for
these deleted, which is a deliberate, narrow exception to the no-delete rule above, not a general
loosening of it.

**Run `scripts/sweep-delete-sponsored.js` on request — it is not part of "run job alert evaluation
process" and does not run automatically.** `--dry-run` (the default) only identifies and reports;
`--execute` is required to actually delete anything.

**How it tells a Sponsored/Offer thread apart from a real one:** the badge text "Sponsored" or
"LinkedIn Offer" literally appears in the row — LinkedIn renders it after the sender's display
name, so the match is **not** anchored to the start of the row (an anchored-only version missed
38 of 47 real matches on the first attempt). This is a reliable, LinkedIn-rendered signal, not a
guess from sender name or content — a real person's name ("Jim Fitzgerald," "Fran Gomory") can be
the *sender* of a Sponsored ad and still gets caught correctly, while a real recruiter thread never
carries the badge at all.

**A near-miss during development is why this script's design is defensive, not simple.** An early
ad-hoc version's row-matching loop found no match after a filter switch (a stale-render timing
issue) and then fell through to clicking an unrelated element — which happened to open a real,
active recruiter thread (Anthony Soriano's, with a pending draft) instead of a Sponsored one. It
only reached the confirmation dialog and was never confirmed, so nothing was actually lost, but it
is the reason the shipped script:
- Re-locates every target by **content match at click-time**, never a cached index.
- **Skips and logs** anything it can't uniquely re-locate — it never falls through to clicking
  whatever happens to be there.
- Re-checks the **opened thread's own body** for the same snippet as a second, independent
  confirmation immediately before deleting.

**Expect to run it several times per sitting.** The thread list is virtualized and reflows after
each deletion, revealing more matches that weren't visible on the previous pass — one real cleanup
took 4 passes (39, then 23, then 11, then 0 newly found) to fully converge. Re-run it until it
reports 0 identified.

**"Skipped" entries are the safe outcome, not a bug to chase.** An item skipped as
"not uniquely found" was correctly left untouched — it will very likely be found and deleted
cleanly on the next pass once the list has settled.

#### Initial backlog sweep (one time)

Phase G has never run, so the first invocation hits the entire Focused backlog. Message moves are
**state changes** against a live account — a heavier footprint than the page reads the 25-per-run
cap elsewhere in this file was written for, so extra caution up front is warranted.

1. **Discovery step — completed 2026-08-24, not a per-run requirement.** The per-thread overflow
   menu was opened live and read verbatim (see "Why Spam is never used" above and
   `scratch/linkedin-discovery/` for the raw dumps and screenshots); the read script
   (`fetch-linkedin-messages.js`) and the write script (`linkedin-msg-dispose.js`) were both run
   live and verified end to end — including one real `Move to Other` on a genuine lane-mismatch
   thread, independently re-checked afterward to confirm it left Focused and landed in Other. The
   confirmed selectors are documented in both scripts' header comments. If LinkedIn's messaging UI
   changes later and a script starts failing to find its controls, redo this discovery step before
   trusting it again — don't assume the old selectors still hold.
2. **Batch 1 is still a dry run — 25 threads, classify and propose only.** Move nothing, write no
   drafts. Present the proposed dispositions as a compact list and let Carl correct any
   miscalibrated *judgment call* (lane fit, strike weighting, temperature) before it costs more
   than 25 threads — this is about the classification rules, not the mechanics, which are already
   confirmed.
3. Fold Carl's corrections into this phase's criteria before batch 2.
4. **Batches 2..N** — 25 threads each, 3–8s jitter, report after each batch, and Carl can stop
   between any two batches.

Steady-state runs after the initial sweep are much smaller: every Focused thread not yet in the
ledger, any ledgered thread with a newer message since last seen, and a staleness re-check across
ledgered Focused threads (pure date math against `last_message_at`, no page loads needed for that
part).

#### G.7 — LinkedIn_Message_Log.csv (runs last, after every LinkedIn-side disposition is final)

(Added 2026-08-24, at Carl's request — modeled on `JD_Evaluation_Log.csv`'s operational discipline:
a real CSV writer, a backup before every write, and a mirrored write to the same OneDrive folder,
every run.) A parallel, lighter-weight log of LinkedIn message threads, meant to be viewed in Power
BI or Excel the same way the JD log is.

**Columns:** `Thread_ID`, `Thread_URL`, `Date`, `Sender`, `Message`, `Reply`, `Status`.
- `Date` / `Sender` / `Message` reflect the sender's most recent message in the thread — never
  Carl's own messages. `Date` is a resolved calendar date (`YYYY-MM-DD HH:MM AM/PM`), not a
  relative word like "TODAY" or "TUESDAY" — those stop meaning anything the day after they're
  written, so they're resolved against the actual run date before writing.
- `Reply` is the exact text of the thread's current draft, flattened to a single line (see "No
  embedded line breaks" below) — blank when no draft exists (a Held thread, or one where Carl or
  the recruiter already has the ball, like Nicole Swift or Jonah Wimmer).
- `Status` is one of exactly three values — **`Received`**, **`Replied`**, **`Archived`** — and is
  **re-derived from scratch on every run**, never carried forward from the previous run. See
  "Status — recheck every run" below.

**Status — recheck every run:**

(Revised 2026-08-25, replacing the old `Focused`/`Other`/`Archived` vocabulary, which just echoed
the ledger disposition and said nothing about whose turn it was.) The three values:

| Value | Means |
| --- | --- |
| `Received` | The most recent message in the thread is **theirs** — a first outreach, a follow-up nudge, or a reply to something Carl sent. The ball is in Carl's court. |
| `Replied` | The most recent message in the thread is **Carl's**. The ball is in theirs. |
| `Archived` | The thread has been moved to **Archived or Other** by the disposition rules elsewhere in Phase G. |

**Precedence:** `Archived` outranks the other two. A thread that has been dispositioned to Other or
Archived reads `Archived` regardless of who spoke last — the disposition is a decision, the other
two values are just a description of whose turn it is.

**A drafted reply is not a sent reply.** `Replied` requires that Carl actually sent a message into
the thread. A thread with a `pending_send` draft sitting in `LinkedIn_Drafts/` is still `Received`
— the draft hasn't reached the recruiter, so the ball is still on Carl's side of the net. Getting
this wrong would hide exactly the threads that need action.

**Rechecking `Status` is part of every run, not a write-once field.** Threads move: a recruiter
answers a message Carl sent (`Replied` → `Received`), Carl sends the draft that was pending
(`Received` → `Replied`), a thread gets dispositioned away (either → `Archived`). On every Phase G
invocation, **re-evaluate `Status` for every row already in the file**, not just for rows being
added or refreshed with new transcript data. This is the one field that is always recomputed —
unlike `Message` and `Reply`, which are only overwritten when the run actually found something
newer. A stale `Status` is worse than a missing one: it silently misreports whose turn it is,
which is the entire reason the column exists.

Mechanically this is `deriveStatus(disposition, transcript)` in
`scripts/update-linkedin-message-log.js`, which reads the last `… sent the following message(s) at
…` block in the transcript and checks whether that sender is Carl.

**No embedded line breaks — `Message` and `Reply` must each stay on one physical line:**

(Added 2026-08-25, after the Fabric shortcut for this file was set up.) Both fields are free text
and routinely arrive with hard line breaks in them. **Every run of line breaks is collapsed to a
single ` ¶ ` marker (space, U+00B6 pilcrow, space) before writing** — surrounding spaces and tabs
absorbed, leading/trailing whitespace trimmed. The writer does this in `csvField`, so it applies
to both copies of the file and to every column, and there is no way to write a raw newline into
this CSV without editing the script.

This is not cosmetic. The Fabric shortcut's CSV reader is **not multiline-aware**: an embedded
newline inside a quoted field ends the record as far as the reader is concerned, so one logical
row shatters into many malformed rows. Measured on 2026-08-25 before the fix: 15 real records
occupied 376 physical lines. RFC 4180 quoting is correct and Python's `csv` module parsed the file
perfectly — the file was never malformed, the reader simply doesn't honor that part of the spec.
Same class of read-side mismatch as the 2026-08-08 Escape-character bug on the JD log; see
"Downstream consumer contract — Company-423 Fabric" in `instructions/04-log-and-write-discipline.md`.

To render real line breaks in a Power BI visual — and to copy a reply out of the report ready to
paste into LinkedIn's message box — substitute the marker back at the **report layer** rather than
putting newlines in the file. Measure on the `LinkedIn_Message_Log` table:

```dax
Reply Formatted =
SUBSTITUTE ( SELECTEDVALUE ( 'LinkedIn_Message_Log'[Reply] ), " ¶ ", UNICHAR ( 10 ) )
```

Put `Reply Formatted` in the visual instead of the raw `Reply` column, enable word wrap on it, and
copy from that cell (right-click → **Copy → Copy value**).

**Known fidelity limit:** the flattener collapses *any* run of line breaks to one marker, so a
paragraph break (`\n\n`) and a single break (`\n`) both become ` ¶ ` and are indistinguishable in
the CSV. The measure therefore restores single line breaks where the original draft had
blank-line-separated paragraphs — readable, but tighter than what was written. The pristine text
with real paragraph breaks always remains in the thread's `LinkedIn_Drafts/*.md` file under
`## Draft reply`; copy from there if exact formatting matters.

**Row lifecycle — this is the part most likely to be gotten wrong, so read it carefully:**
- A thread only ever *enters* this file by being seen in Focused. A thread that was already
  Other/Archived before this feature existed, and has never been Focused since, **never gets a
  row** — Carl was explicit: no backdating history from before this file existed.
- Once a row exists, it is **permanent** — a thread leaving Focused does not remove its row, only
  updates its `Status`. The eligible set on every run is: currently-Focused ledger entries, union
  whatever rows the file already has from a prior run.
- Existing rows are **updated in place, keyed by `Thread_ID`** — never duplicated across runs. A
  run that finds no fresher transcript or draft data for an already-tracked thread must not blank
  out `Message`/`Reply` that a previous run already captured; only overwrite a field when this
  run actually found something newer.
- **The very first run of this feature iterated the entire ledger and backdated all 90+
  already-resolved historical entries into the file before Carl ever saw it — caught and reverted
  immediately.** The bug was using "exists in the ledger" as the eligibility test instead of
  "is currently Focused, or was already tracked." If this script is ever rewritten, preserve that
  distinction exactly.

**Dates in this file are anchored to the scrape, not to the run.** (Added 2026-08-28, after the
defect below.) `Date` describes when *they* sent their last message. A LinkedIn transcript renders
that as a relative day marker — `TODAY`, `YESTERDAY`, `WEDNESDAY` — and those words mean whatever
they meant **at the moment the transcript was captured**. Resolving them against the current run
date is wrong on every run after the capture day, and wrong silently, because the result is still a
plausible-looking date. `resolveDate()` therefore takes the capture's own `scrapedAt` as its anchor.
The property to hold onto: **re-running this script against an unchanged capture must be a
byte-for-byte no-op**, however many days later. If a `Date` moves, a genuinely newer message
arrived — the run summary lists every date change for exactly this reason.

**Mechanics:** `scripts/update-linkedin-message-log.js`, run at the end of every Phase G invocation
(after all dispositions for the run are final). **Always `--dry-run` first** — it reports rows
added/updated, every `Status` change, every `Date` change, and every row whose `Status` had to be
carried rather than recomputed, and writes nothing. `--self-test` runs the unit checks against no
files. `--transcripts <file>` adds a capture the auto-discovery missed. Writes `LinkedIn_Message_Log.csv` in the JobSearch
folder and mirrors it to
`<onedrive-root>/LinkedIn_Message_Log/LinkedIn_Message_Log.csv`
— note the **dedicated `LinkedIn_Message_Log/` subfolder**, one level below the OneDrive root
where `JD_Evaluation_Log.csv` still lives. (Changed 2026-08-25. A Fabric table shortcut maps one
folder to exactly one Delta table and requires every file in that folder to share an identical
schema, so this 7-column file cannot sit beside the 23-column JD log — pointed at the shared root,
the shortcut only ever produced the JD table and silently dropped these rows. One folder per
table, one shortcut per folder. **The JD log's location is unchanged; do not move it.**) The
script creates the subfolder if it is missing, but still treats the OneDrive root itself being
absent as the unmounted-sync case. Backs
up both existing copies first (to `backups/`, timestamped in **local** time, same convention as the
JD log's backups). Unlike `JD_Evaluation_Log.csv`, this file has no Carl-owned columns Claude must
never overwrite, so it doesn't need the JD log's pre-run reconciliation step — primary simply wins
if the two copies ever disagree.

**Post-write validation (added 2026-08-28 — it did not exist before).** The writer had backups and
a dual write but never re-read what it wrote, which is the one discipline `jd-append.py` and
`jd-update.py` both have and this file's writer did not. It now writes each copy atomically through
a temp file, re-reads **from disk**, and asserts: the header matches the seven columns exactly;
every row has seven fields; the row count matches what was built; **no raw line break survived the
flattener** (the Fabric-shattering failure the pilcrow exists to prevent, now caught at write time
instead of a week later in Power BI); every `Thread_ID` is present and unique; every `Status` is one
of the three legal values; and the two copies are byte-identical. **On any failure it restores both
copies from the backup it took this run and exits 1.** Fault-injection tested 2026-08-28 against a
truncated file and a raw newline in a field — both caught, both copies rolled back.

**Seven defects were fixed on 2026-08-28 and each is marked `[Gn]` in the script's header comment**
with the evidence that found it. Beyond the two above, the ones worth knowing when reading the
code: reading the existing CSV used to trust its header and silently blank any column it could not
find (now halts); the transcript source list was six hardcoded filenames taking the *first* match,
so a capture written to any other path — `fetch-linkedin-messages.js` accepts `--out` — was
structurally invisible, and "first" only meant "newest" by luck of the order someone typed them
(sources are now discovered and ranked by `scrapedAt`); and a thread missing from this run's
capture had its `Status` silently reset from `Replied` to `Received`, which with a 25-thread fetch
cap manufactures work on threads Carl has already answered. **`Status` is still recomputed every
run — but recomputing it from absent evidence is defaulting, not recomputing.** With no transcript
the prior value is carried forward, and every carry-forward is named in the run summary.

#### Run summary

Print every heading even when empty, same convention as Bridge candidates in Step 5 — a run with
no hot leads and a run where the section was forgotten must not look identical:

```
Phase G — LinkedIn message triage
  Focused threads scanned: 34   new: 6   re-checked: 28

  HOT (1) — ready for JD evaluation on request:
    Sam Ingwell / Summit Human Capital — Fabric Lead
    JD in-thread, $70–80/hr, remote. Strike: contract.
    → say "evaluate the Summit lead" to log it to the CSV

  WARM — drafts written for Carl to send (2):
    Dana Reyes / Northwind — LinkedIn_Drafts/2026-08-21_Dana-Reyes_Northwind.md
    ...

  Awaiting Carl's send (3, unchanged from last run): ...
  Moved: Other 4 · Archived 11 · Spam 0 (control unverified)
  Mail: 7 LinkedIn notification emails trashed
```
