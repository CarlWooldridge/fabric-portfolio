# Intake and JD retrieval

*Part of the JobSearch workflow. Start at [`COWORK_INSTRUCTIONS.md`](../COWORK_INSTRUCTIONS.md) — it holds the naming convention, the run-type map, and the rules that apply everywhere.*

**When to load this file:** Load for any run that pulls new postings — job-alert emails, pasted URLs, or a manual ID list.

---

### 1. Extract
Read every new email in the folder. **A single alert-digest email routinely contains multiple
postings, not just the one named in the subject line** — confirmed 2026-08-08, when 12
"single-subject" digest emails carried 67 total posting mentions among them. Extract every
posting in the body, not only the one that generated the subject/notification. Pull for each
posting: company, role title, location, work-type tag (Remote/Hybrid/On-site), employment-type
tag, posted comp range if shown, applicant count if shown, and the LinkedIn URL. Extract the
numeric LinkedIn job ID from the URL (the digits after `/jobs/view/`) — that is the reliable
dedupe key.

**`Job_ID` is required on every row.** Never append or backfill a row with `Job_ID` left
blank, and never fabricate, guess, or synthesize a placeholder value on your own initiative.
If a posting's URL/Job_ID can't be obtained during processing — the source doesn't carry a
link, the JD fetch fails before the ID is captured, or a match can't be confirmed — stop and
ask Carl for the URL or Job_ID for that specific posting before logging the row, rather than
leaving it blank or inventing one. It's fine to batch these asks at the end of a run instead
of interrupting mid-run, as long as the row isn't written until the ID is in hand.

**Forwarded emails count the same as direct alerts.** Some alert emails arrive as a "Fwd:"
from a different LinkedIn account (e.g. a friend or family member's alert forwarded to Carl),
addressed to someone else's name and using a `/comm/jobs/view/` link path instead of
`/jobs/view/`. Treat these identically to Carl's own alerts — extract, dedupe, fetch, evaluate,
archive. Don't ask about this each time; it's settled.

Not every email in this folder is guaranteed to be Carl's own LinkedIn alert — some may be
forwarded from other sources or people. That's fine and expected; process every email placed
in this folder exactly the same way regardless of who it was originally addressed to. No
special handling or flagging based on addressee.

### 2. Dedupe — do this before any browsing
Check each posting against `JD_Evaluation_Log.csv`:
- **Exact match** on `Job_ID` → already seen. Skip.
- **No Job_ID, or no match** → compare normalized `Company` + `Role_Title` (lowercase,
  strip punctuation and suffixes like "Inc"/"LLC"). A close match is a probable repost.
  Skip it, but list it in the run summary as "probable repost" so Carl can overrule.
- Also dedupe **within** the batch — the same job appears across multiple alert emails
  constantly. Evaluate it once.

**A second dedupe pass runs AFTER the fetch, on the JD bodies.** (Added 2026-09-01.) The three
checks above key on `Job_ID` and on normalized `Company` + `Role_Title`, and two duplicates got
past them on 2026-08-31 — both through a gap in that key, not a bug in it. Two Company-456
sightings came out of a forwarded alert's `text/html` part with `Company` and `Role_Title`
**empty**, so there was no company+title key to compare; and Company-24 and
Company-646 posted the same JD **verbatim under two different poster names**, which the
same-company repost search never even considers. The body is the thing neither check can see —
and it does not exist until the posting has been fetched, so this pass cannot move earlier:

    python3 scripts/jd-dedupe.py --json extracted.json                     # pre-fetch, as above
    node scripts/fetch-jds.js <the new IDs>                                # Step 3
    python3 scripts/jd-dedupe.py --json extracted.json --bodies scratch/fetched --update-index

It does not save a fetch. It saves an evaluation, a log row, and the manual cleanup of a
duplicate row — the 2026-08-31 run wrote three Company-456 rows and two AllClear/Towsleys rows that
this pass would have collapsed to one each. `--update-index` accumulates body fingerprints in
`scripts/jd-body-fingerprints.json` so a duplicate that arrives in a *later* run is caught too;
without it the pass still catches every within-batch pair, which is where both 2026-08-31 misses
lived.

**Backfill on every dupe hit.** A duplicate is not just something to discard — it is a second
chance at data the first sighting was missing. When a posting matches an existing row, compare
field by field and fill in anything the logged row left blank: `Job_ID`, `URL`, `Location`,
`Work_Type`, `Employment_Type`, `Comp_Posted`, `Applicant_Volume`. Write those into the existing
row rather than appending a new one.

Backfill rules:
- **Only fill blanks.** Never overwrite a field that already has a value. **A placeholder string
  is not "blank" and is not "a value" either** — e.g. `Role_Title` = `[see rejection batch]` left
  over from a bulk historical import (encountered 2026-08-08). Don't silently overwrite it and
  don't treat it as real data to preserve. Fill the surrounding genuinely-blank fields as normal,
  leave the placeholder field alone, and flag it in the run summary for Carl to confirm or correct
  directly — don't guess at unilaterally "fixing" it.
- **Never touch** `Carls_Action`, `Carls_Action_Date`, `Verdict`, `Role_Type`, `Comp_Flag`,
  `Biggest_Gap`, `Biggest_Strength`, or `Recommended_Action` on a dupe. Those are judgments,
  not extracted data.
- **If the new sighting contradicts a populated field** (e.g. logged as On-site, now tagged
  Remote), leave the existing value alone, append a dated note to `Notes` describing the
  conflict, and surface it in the run summary. A changed work-type or comp range may mean the
  posting was genuinely revised and is worth re-evaluating — flag it, don't decide it.
- Append `Backfilled YYYY-MM-DD: <fields>` to `Notes` so the edit is traceable.
- It's fine to open the LinkedIn page briefly for a backfill-only hit if the alert email
  doesn't carry a field you need (e.g. comp or applicant count) — you're not re-evaluating
  the posting, just completing the extracted data.

Report the counts at the end: postings found, exact dupes, probable reposts, rows backfilled,
conflicts flagged, newly evaluated.

### 3. Fetch the JD
For each genuinely new posting, fetch the LinkedIn page with the **signed-in headless Chromium
runner** (Tier 1, below) and extract the full job description body. Do not evaluate from the
alert-email summary alone — the email gives title and tags only, and the tags routinely
contradict the JD body. Never invent JD content.

This is now the **sole** retrieval method. The previous Claude-in-Chrome extension approach, the
company-career-site fallback, and the `/voyager/` internal API are retired — see
"Appendix: Legacy retrieval methods" at the end of this file if they ever need reinstating.

#### Tier 1 — Signed-in headless Chromium (Playwright)

**Implemented in `scripts/save-auth.js` and `scripts/fetch-jds.js` in this folder — use those
files, don't re-derive this from scratch.** `scripts/README.md` has setup and usage. The code
below documents the protocol those scripts implement; if they ever drift out of sync, the scripts
are the source of truth for mechanics and this file is the source of truth for policy (caps, halt
handling, when to stop).

**This must run with real local execution** — a full terminal, package installs, and a
long-running Node process. That is outside what a Cowork chat session can do on its own (its
shell tool is a cloud sandbox with no LinkedIn access — see the IP note below). Use **Claude
Code** running directly on Carl's Mac to drive this end-to-end: fetching, dedupe, scoring, and the
CSV write in one pass. A Cowork session can still prepare emails/CSV work and hand off, but the
fetch step itself needs Claude Code or Carl's own hands on the terminal.

Runs as a local background process on Carl's Mac. No visible window, no focus stealing, no
dependency on the Chrome app being open. Chrome may be running or closed — it does not matter,
because auth comes from a saved `storageState` file rather than a live Chrome profile directory.

**Must run on Carl's own machine.** Datacenter/cloud IPs get nothing from LinkedIn — verified
2026-08-05, when both `/jobs/view/<id>` and `/jobs-guest/jobs/api/jobPosting/<id>` returned empty
from a cloud sandbox. Residential IP is required.

**One-time setup**

```bash
npm install playwright
npx playwright install chromium
```

Capture auth once, headed, with a real manual login:

```js
// save-auth.js — run once, and again whenever the session expires
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  await page.goto('https://www.linkedin.com/login');
  console.log('Log in manually, complete any 2FA, then press Enter here.');
  await new Promise(r => process.stdin.once('data', r));
  await page.context().storageState({ path: process.env.LI_STATE });
  await browser.close();
})();
```

Point `LI_STATE` at a path **outside** any synced/backed-up folder — it is a credential
equivalent to a logged-in session. Do not put it in this JobSearch folder.

**Per-run fetch**

```js
const { chromium } = require('playwright');

const JITTER = () => 3000 + Math.random() * 5000;   // 3-8s, randomized
const MAX_ATTEMPTS = 5;
const MAX_POSTINGS_PER_RUN = 25;

async function fetchJD(context, jobId) {
  for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt++) {
    const page = await context.newPage();
    try {
      await page.goto(`https://www.linkedin.com/jobs/view/${jobId}/`,
                      { waitUntil: 'domcontentloaded' });

      // Halt conditions - do NOT retry through these.
      // Distinguish benign expiry from a flagged session: they look similar but
      // mean very different things and have different remedies.
      const url = page.url();
      if (/\/login|\/uas\/login|authwall/.test(url)) throw new Error('HALT_EXPIRED');
      if (/checkpoint|challenge/.test(url)) throw new Error('HALT_CHALLENGE');
      if (await page.locator('text=/unusual activity|verify you.re human/i')
                    .count()) throw new Error('HALT_CHALLENGE');

      // Wait for substantive body text, not a fixed timeout. This is the actual
      // fix for the skeleton problem - the old approach guessed at wait duration.
      await page.waitForFunction(() => {
        const el = document.querySelector('main');
        return el && el.innerText.length > 1500;
      }, { timeout: 15000 });

      const text = await page.locator('main').innerText();
      if (text.length < 1500) throw new Error('SKELETON');
      await page.close();
      return text;
    } catch (e) {
      await page.close();
      if (String(e.message).startsWith('HALT_')) throw e;   // bubble up, stop the run
      if (attempt === MAX_ATTEMPTS) return null;
      await new Promise(r => setTimeout(r, JITTER() * attempt));  // backoff
    }
  }
}
```

Notes on the above:

- **Wait on a content condition, not a clock.** The old method's failure mode was guessing a
  fixed wait and reading a loading skeleton. `waitForFunction` on body-text length removes that
  guess entirely. The "…more" toggle only collapses the text visually — `innerText` reads the
  full body regardless, so no click is needed.
- **Five attempts, as the protocol has always said.** Fresh `goto` each time, exponential-ish
  backoff. Postings tagged "Promoted by hirer" or "Responses managed off LinkedIn" get the full
  five — those tags are a hint the render may be slow, not proof it will fail. (On 2026-08-05,
  9 of 13 such postings rendered fine on attempt 1–2 once the connection was stable.)
- **Selectors drift.** LinkedIn changes class names without notice. The length heuristic above is
  deliberately selector-light. If it starts misfiring, capture the current description container
  on one posting and tighten it rather than adding more waiting.
- **Clearing the length floor doesn't guarantee a substantive JD.** Confirmed 2026-08-08: two
  postings cleared the 1500-char `SKELETON` threshold but had no Responsibilities/Qualifications
  section at all — genuinely thin, templated listings, not a render failure. The length check only
  catches the empty/loading case; it can't tell a real-but-thin JD from a normal one. When the
  fetched body reads unusually generic or short relative to a typical posting, evaluate on what's
  actually there, score conservatively, and flag the low confidence explicitly in `Notes` and the
  run summary rather than silently treating a passed length check as "fully evaluated."
- **The whole-page length floor can also be fooled the other direction — a total false pass on a
  posting with zero real content.** Confirmed 2026-08-08 on Job_ID 4438043264 (Company-129): the
  fetched body was 1513 chars, clearing the threshold, but every byte of it was LinkedIn's
  footer/language-selector chrome — the "About the job" heading itself never appeared, because
  that section hadn't rendered yet on that attempt. This is different from the thin-but-real case
  above: there was no JD to evaluate at all, and simply waiting/retrying (which `fetch-jds.js`'s
  existing 5-attempt loop already does) fixed it on the next attempt. **`fetch-jds.js` now gates
  on the "About the job" section's own length, not just the whole-page total**, so this triggers a
  genuine retry instead of a false pass — if a fetch ever again returns a body that reads as
  real-length but empty of actual job content, that's this failure mode recurring; check whether
  the About-section extraction in `fetch-jds.js` needs its marker strings adjusted (LinkedIn may
  have changed the surrounding boilerplate text) before assuming it's a new problem.

**Pacing and volume caps — not optional**

- Randomized 3–8s between postings. Never a fixed interval; uniform timing is the most obvious
  automation signal there is.
- Cap at ~25 postings per run. A normal alert batch is 14–20, so this is not a real constraint —
  but a backlog or multi-week catch-up batch can exceed it (38 new postings on 2026-08-08, the
  first Mail.app-sourced run). When that happens, split into multiple sequential fetch runs, each
  respecting the cap and the pacing/jitter rules independently — do not raise the cap and do not
  skip the excess. "One run per alert batch" below is about not re-processing the same batch
  repeatedly, not a prohibition on this kind of split.
- One run per alert batch. Do not loop the whole log.

**Session lifetime and re-auth.** The `storageState` file persists across runs — normal sessions
go weeks to months without a re-login, and no 2FA prompt appears on subsequent runs because the
session is already established. To extend it further, re-save the state at the end of every
successful run so token rotation is captured rather than going stale:

```js
await context.storageState({ path: process.env.LI_STATE });   // on success only
```

Re-auth must always use the headed `save-auth.js` flow. Never attempt a login headlessly.

**Hard stop conditions — two kinds, don't conflate them.** Both stop the run immediately: no
retry, no fallback, no continuing to the next posting. But report them differently, because the
remedy differs.

- **`HALT_EXPIRED`** (redirect to `/login`, `/uas/login`, or authwall) — benign. The session
  simply aged out. Tell Carl to re-run `save-auth.js`, then resume. Note in the summary how long
  it had been since the last re-auth.
- **`HALT_CHALLENGE`** (redirect to `/checkpoint` or `/challenge`, CAPTCHA, "unusual activity"
  interstitial, or a 999 status) — **not** benign. The session has been flagged. Report to Carl
  with the job ID that triggered it and stop. Do not re-auth and retry as if it were an expiry;
  that reads as evasion and escalates the problem. Carl decides what happens next.

**Watch the re-auth interval as a health metric.** A jump from months to days between
`HALT_EXPIRED` events means the pattern is drawing attention even without a formal challenge.
Surface that trend to Carl rather than quietly re-authing each time.

**Risk note, for the record.** Automated access violates LinkedIn's User Agreement regardless of
volume or how human-paced it is. Because this method is authenticated, enforcement attaches to
**Carl's account** — his primary job-search channel — not merely to an IP. Enforcement escalates
roughly rate-limit → checkpoint → temporary restriction → ban, and volume is the dominant
trigger, which is what the caps above are for. Carl adopted this method on 2026-08-05 with these
tradeoffs stated explicitly. Do not add fingerprint-spoofing or stealth-plugin layers to this
runner; if it stops working, tell Carl rather than escalating the evasion.

**What to extract per posting** (feeds the Row format in Step 4):

- Role title, company, location, work-type tag, employment-type tag
- Comp range if posted
- Applicant count ("N people clicked apply" / "Over 100 applicants")
- Visible connections / school-alumni signals — the main thing the signed-in session buys, and a
  direct input to the referral rule and the Applicant-competition rubric item
- "No longer accepting applications" (see closed-posting check below)
- Full "About the job" body

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

#### If Tier 1 fails
There is no fallback tier. After five failed attempts, log the row with
`Verdict = "Unretrieved - needs manual pull"` (one of the controlled `Verdict` values listed in
`04-log-and-write-discipline.md`, which is authoritative for that vocabulary), leave the judgment
fields blank, and say so plainly in the run summary. See the "no Skip without a JD" rule in Step 4.

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

### Alternate source: original company career-site posting
Carl sometimes pastes the original (non-LinkedIn) posting URL for a role already logged —
usually because LinkedIn didn't show comp and the company's own careers page does. Treat this
as a backfill, following the same backfill rules as Step 2 (fill blanks only, dated `Backfilled`
note in `Notes`), with one exception: if the original posting shows a real comp figure and the
logged row's `Comp_Flag` is currently `Unlisted - researched $X-$Y`, overwrite both
`Comp_Posted` and `Comp_Flag` with the actual figures — posted data supersedes a research
estimate, that's not the same as overwriting a judgment call.

Also use the original posting to re-check any location/work-type contradiction that was flagged
from LinkedIn alone. A company's standard HQ/mailing address sitting in a posting's location
field is not the same as an actual on-site work requirement — if the original source's JD text
confirms remote/hybrid language consistent with what LinkedIn showed, that resolves the
contradiction rather than deepening it. Note the resolution in `Notes`.

### Alternate input: Mail.app pull-and-auto-trash (Claude Code only)

(Added 2026-08-08; tested and confirmed working end-to-end the same day — this is the standard
path now, not a plan awaiting a first run.) Instead of Carl manually dragging alert emails into
this folder, a Playwright-adjacent local workflow pulls them directly from Mail.app and, after a
run fully succeeds, moves the source emails to Mail's Trash (soft delete, recoverable). Full spec
and the AppleScript itself live in `scripts/mail-README.md`, `scripts/mail-pull.applescript`, and
`scripts/mail-trash.applescript` — read those before using this path.

**A prompt like "run job alert evaluation process" means the whole pipeline**, in one invocation:

1. **Phase A** — pull mail (`python3 scripts/mail-pull-imap.py`; the older
   `mail-pull.applescript` is kept as a fallback)
2. **Phase B** — dedupe, fetch JDs, evaluate, write both CSV copies, validate, archive the `.eml`s
3. **Phase C** — trash the confirmed-logged source emails
   (`python3 scripts/mail-move.py --op trash`, which picks the fastest working backend)
4. **Phase D** — application/rejection/interview triage (`mail-triage-scan.applescript`), per
   "Application / rejection / interview triage" in `instructions/05-triage-and-audits.md`
5. **Phase E** — stale-Pursue closure sweep (re-check `Verdict = Pursue` or `Review` / blank-`Carls_Action`
   rows for "No longer accepting applications"), per "Phase E — stale-Pursue closure sweep" in `instructions/05-triage-and-audits.md`
6. **Phase G** — LinkedIn message triage & reply drafting, per "Phase G — LinkedIn message triage
   and reply drafting" in `instructions/06-linkedin-messages.md`. Runs after E; see that section for its own attended/unattended split.
7. **Phase F** — monthly Skip audit, per "Phase F — monthly Skip audit" in `instructions/05-triage-and-audits.md`. **Not part of every
   run** — it fires once a month or on request, and it is interactive like Phase D because it ends
   in a question to Carl. If it's been more than 30 days since the last one, run it at the end of
   the pipeline, **after Phase G**; otherwise say when it's next due and move on. (Phase F keeps
   its letter for history — it was named before G existed — but always runs last regardless.)

**Mark every phase as it completes, and check the marks before you start.**
(Added 2026-09-01.) Run `python3 scripts/phase-state.py --report` at the top of a run and
`--mark <PHASE> --note "…"` as each one finishes. The report's real check is not age — a quiet
week makes everything look old and that is fine — it is **whether any phase is older than the
most recent Phase A**, which means a run started and that phase never finished it.

This exists because of a specific miss. The 2026-08-31 run broke on token cost and was recovered
piecemeal over two days; Phases A, B, D and E all completed and **Phase C never ran at all**.
Nothing could tell, because Phase C's only output is in Mail's Trash, not in this folder. Carl
found it by noticing 60 alert emails still sitting in his Inbox on 2026-09-01. A→C in a single
unattended invocation cannot skip C; a recovery can, and recoveries will happen again.

**Phases A→C run unattended**, with no pause for approval between them. **Phase D is interactive
by design** and prompts Carl per email before writing — that is a deliberate exception, not a
checkpoint to skip, because its writes land in `Carls_Action` / `Outcome` / `Reason`. Do not treat
"unattended" as license to auto-apply Phase D's changes, and do not skip Phase D just because it
requires prompting. See "Phase A through Phase C runs unattended" in `scripts/mail-README.md` for
the reasoning behind A→C. **Phase E runs unattended too** — like the Step 3 closed-posting check
it draws from, closure status is an observed fact, not a judgment call, so it doesn't need Carl's
per-row confirmation the way Phase D's writes do. **Phase G is a split** — mechanical dispositions
(age-out, obvious junk, absolute-gate kills) run unattended; every lead classification and every
drafted reply prompts Carl. See "Phase G" in `instructions/06-linkedin-messages.md` for the exact boundary.

Same constraint as the LinkedIn fetcher in Step 3: this **requires Claude Code running locally
on Carl's Mac**. It no longer requires Mail.app itself: Phases A, C and D's archive all run over
IMAP against iCloud as of 2026-09-01, so they need the Keychain credential described in
`scripts/mail-README.md` rather than a macOS Automation grant. The AppleScript fallbacks still
need the grant. A Cowork chat session cannot run either path and should not attempt to.

**Two reasons the IMAP path is the default, and speed is the smaller one.** The AppleScript
path **locks Mail.app's UI for the whole run** — Carl cannot use his own mail client while
Phase A or C is working, which on 2026-09-01 meant 91 minutes of frozen Mail. And the
Automation grant it depends on stopped working mid-session that same day (`-1743`, with
claude.app still showing as enabled), which left Phase A unable to run at all. IMAP touches
neither Mail.app nor TCC.

Key points, detailed fully in `scripts/mail-README.md`:
- **Scoped to the Inbox only** — never Archive, Sent, Trash, or any other mailbox.
- Matches (a) sender `jobalerts-noreply@linkedin.com`, (b) sender
  `<forwarding-sender>` with subject starting `"Fwd"` and body containing
  `jobalerts-noreply@linkedin.com`, or (c) sender `jobs-noreply@linkedin.com` — see "Jobs You
  Might Be Interested In emails" below.
- Pull (export to `.eml` + manifest) and trash (move to Mail's Trash) are separate scripts run at
  separate times, correlated by the email's Message-ID header — never by position or subject.
- An email is only trashed after its posting is confirmed logged to `JD_Evaluation_Log.csv`
  **and** its OneDrive mirror, both validated, and the `.eml` archived to `/processed`. A failed
  or partial run leaves the source email untouched in the Inbox.

Once pulled via `mail-pull.applescript`, the exported `.eml` files feed into the normal Step 1–7
workflow exactly like manually-dropped emails.

#### "Jobs You Might Be Interested In" emails — third input source

(Added 2026-08-10, at Carl's request, after one surfaced in his Inbox and had been treated as
noise by Phase D's triage scan.) LinkedIn sends two distinct email types from two distinct
addresses, easy to conflate because both land in the same Inbox with similar-looking job cards:

- **Job alerts** — sender `jobalerts-noreply@linkedin.com`, subject `"Your job alert for <search
  term> in <location>"`. Driven by Carl's own saved searches. This is the primary source
  documented throughout this file.
- **"Jobs You Might Be Interested In"** — sender `jobs-noreply@linkedin.com`, subject varies per
  email (e.g. `"<Company> is hiring for a <function> role"`), footer reads `"You are receiving
  Jobs You Might Be Interested In emails."` Algorithmic recommendations based on activity, not a
  saved search. `mail-pull.applescript` now matches this sender too (see above).

**Treat postings from this source identically to job-alert postings** — same extraction, same
dedupe, same fetch/evaluate/log pipeline, same archiving. The only structural difference is
layout: postings are grouped into category sections (e.g. "Analytics jobs", "Azure jobs", "Cloud
jobs") reflecting why LinkedIn recommended them, but that grouping has no bearing on evaluation —
extract every posting across every section, same as pulling every posting out of a job-alert
digest regardless of which one generated the subject line.

Before this change, `mail-triage-scan.applescript`'s date-window scan could pick up a "Jobs You
Might Be Interested In" email as an untriaged Inbox message, but Phase D has no classification
path for "job recommendation, not an application status update" — it would read as noise and get
logged to `triaged-message-ids.json` with no further action, silently dropping any postings it
contained. `mail-pull.applescript` matching this sender is what actually surfaces these postings
for evaluation now; without that, they were invisible to the pipeline entirely.

### Alternate input: pasted URLs
When Carl pastes one or more `linkedin.com/jobs/view/...` URLs into chat instead of (or in
addition to) an alert email, run the identical pipeline with two adjustments to Step 1:

- **Extraction is trivial.** The Job_ID comes straight from the URL — no email parsing needed.
  Company, role title, location, work-type, comp, and applicant count come from the LinkedIn
  page itself once fetched (Step 3), not from an email summary, since none exists.
- **Dedupe (Step 2) still runs first, before opening the page** — check the Job_ID and the
  normalized Company+Role against `JD_Evaluation_Log.csv` exactly as with email-sourced
  postings. Still show Carl the dupe/backfill/new determination and get confirmation before
  browsing, same as the email workflow, unless Carl explicitly says to skip the confirmation
  step for a quick single-URL check.
- Steps 3–5 (fetch JD, evaluate, summarize) are unchanged. There's no email to move to
  `/processed` for this path — skip that part.
- If Carl pastes a bare job ID or a shortened/redirect link instead of the full
  `/jobs/view/<id>/` URL, resolve it the same way: extract or confirm the numeric ID, then
  proceed.
