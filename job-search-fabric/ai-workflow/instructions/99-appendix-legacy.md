# Appendix — retired retrieval methods

*Part of the JobSearch workflow. Start at [`COWORK_INSTRUCTIONS.md`](../COWORK_INSTRUCTIONS.md) — it holds the naming convention, the run-type map, and the rules that apply everywhere.*

**When to load this file:** Historical record. Retired 2026-08-05, kept so the reasoning stays findable. Never load for a run.

---

## Appendix: Legacy retrieval methods (retired 2026-08-05)

Superseded by the signed-in headless Chromium runner in Step 3. Kept verbatim in case any of
them needs reinstating. **Do not use these unless Carl explicitly says to.**

**Why they were retired.** The Claude-in-Chrome extension required Carl's actual Chrome app to be
running, signed in, and focused — so a run made his computer unusable, with no signal for when it
finished, and the extension dropped connection mid-run more than once. Those were the disqualifying
problems, not retrieval quality.

**Honest caveat on the failure data.** Legacy Tier 1 looked worse than it was. On 2026-08-05 it
initially failed on 6 of 6 postings, which drove this redesign — but after the extension
reconnected, the same method rendered 9 of 13 postings cleanly, several on the first attempt,
including ones tagged "Promoted by hirer." Some of the early failure was Claude giving up after 2
attempts when this protocol has always specified 5. If the new runner disappoints, the honest
comparison is against ~70% Tier 1 success, not the ~0% the morning suggested.

### Legacy Tier 1 — Claude in Chrome page render

Used `navigate` → `wait` (3s) → `scroll` down a few ticks → `wait` (6–8s) → `get_page_text` via the
Claude in Chrome extension against Carl's logged-in browser session. On skeleton/placeholder
content, re-`navigate` and repeat as five independent attempts, varying the wait (6s, 8s, 10s,
12s, 15s) in case of slow-load rather than true no-render. LinkedIn visually collapses "About the
job" behind a "…more" toggle, but `get_page_text` read the underlying content regardless. Only
after five consecutive skeleton/empty returns did a posting count as a genuine failure.

### Legacy Tier 2 — Company career site

Fallback after five failed Legacy Tier 1 attempts. Postings tagged "Promoted by hirer" and/or
"Responses managed off LinkedIn" route their apply button off-platform, so the posting also exists
on the employer's own careers page. Searched company name plus role title, or followed the apply
link's destination domain. Carried no account risk and frequently carried *better* data than
LinkedIn — notably real comp figures LinkedIn left blank (this is how the Company-703 $130–160K and
Company-153 $126,762–145,000 ranges were obtained on 2026-08-05).

Note: this remains sanctioned in the separate "Alternate source: original company career-site
posting" section for backfills when Carl pastes an employer URL himself. That is a different
workflow and is **not** retired.

### Legacy Tier 3 — LinkedIn internal API

Last resort, with caps. LinkedIn's web app fetches JD content from
`/voyager/api/jobs/jobPostings/<job_id>`, called from the logged-in session with a `csrf-token`
header (the `JSESSIONID` cookie value, quotes stripped) and
`accept: application/vnd.linkedin.normalized+json+2.1`. Description sits at `description.text` on
the `data` object or somewhere in `included`.

Caps were: small batches only, human-paced delays (1–2s minimum), never the routine path. `/voyager/`
is a private internal endpoint; automated access violates LinkedIn's User Agreement and exposure
lands on Carl's account. On a checkpoint, 401/403, or unexpected shape, the rule was to stop using
it for that run and tell Carl.

**This tier carried the highest risk of the three and was used more than it should have been** —
13 rows in the log were built on it versus 4 on Tier 2. If retrieval ever gets reinstated, prefer
Legacy Tier 2 over Legacy Tier 3.
