// update-linkedin-message-log.js — generates/updates LinkedIn_Message_Log.csv from
// scripts/linkedin-thread-ledger.json. Added 2026-08-24 at Carl's request, modeled on
// JD_Evaluation_Log.csv's operational discipline: backup before write, a real CSV
// writer (never manual string concatenation — Message and Reply fields routinely
// contain embedded newlines and need correct RFC 4180 quoting), and a mirrored write
// to its own dedicated OneDrive subfolder, every run.
//
// Hardened 2026-08-28 (Phase G). Seven defects were found by measuring this script
// against the live data rather than reading its comments; each fix is marked [Gn]
// below and the evidence is in ../instructions/REVAMP_PLAN.md's incident log.
//
//   [G1] No post-write validation at all. It wrote both copies and never re-read
//        them. jd-append.py and jd-update.py both validate; this one did not — the
//        same class of blind spot that hid the Fabric misparse for a week in August.
//        Now: writes atomically via a temp file, re-reads both copies from disk,
//        asserts header / field count / row count / no-raw-newline / primary==mirror,
//        and restores from this run's backup if anything fails.
//   [G2] Evening runs stamped tomorrow's date. resolveDate() built a LOCAL Date and
//        then read it back with toISOString(), so in America/Chicago every run after
//        19:00 shifted the calendar day forward: at 20:30 local, "TODAY 8:30 PM"
//        resolved to 2026-08-29. Same root cause as the "27 rows dated a day early"
//        incident on 2026-08-27. All date formatting is now local-calendar
//        (localDate/localStamp) and toISOString is never used for a date.
//   [G3] Transcript freshness was a coincidence. The source list was six hardcoded
//        filenames with first-one-wins, but fetch-linkedin-messages.js takes --out and
//        can write anywhere, so a new capture file was structurally invisible. Sources
//        are now discovered and ranked by each file's own `scrapedAt`, newest wins.
//   [G4] A missing transcript silently downgraded Replied -> Received. deriveStatus()
//        was called with `t && t.transcript`, so when a thread was not in this run's
//        capture the undefined transcript fell through lastSpeakerIsCarl() to false
//        and the row read Received. With a 25-thread fetch cap this fires the first
//        time a batch does not cover every Focused thread, and Received is the
//        actionable state — it manufactures work on threads Carl has already answered.
//        Status is now carried forward when there is no evidence to recompute it from,
//        and every carry-forward is reported.
//   [G5] Reading the existing CSV trusted its header. A header change or a truncated
//        column silently blanked fields via `r[idx[c]] || ''`. Now halts.
//   [G7] Every run re-dated every row to the run date. Relative day markers
//        ("TODAY", "MONDAY") were resolved against `now` instead of against the
//        transcript's own scrapedAt, so a 2026-08-25 capture read on 2026-08-28
//        moved seven rows forward by up to seven days. Invisible until now because
//        both prior runs happened on the scrape date. See resolveDate().
//   [G6] The flattener trimmed after collapsing, so a leading or trailing line break
//        left a stray ¶ at the edge of the field. Found by --self-test on its first
//        run — see flattenNewlines().
//
// Columns: Thread_ID, Thread_URL, Date, Sender, Message, Reply, Status
//   - Thread_ID/Thread_URL are the stable key for update-in-place matching (not asked
//     for explicitly, but required for the "update existing row" behavior Carl asked
//     for — same role Job_ID plays in the JD log).
//   - Date / Sender / Message reflect the sender's most recent message in the thread —
//     never Carl's own messages.
//   - Reply is the exact text from the thread's current draft file, if one exists;
//     blank otherwise. Flattened to one physical line, see NEWLINE_MARKER.
//   - Status is Received / Replied / Archived — see deriveStatus(),
//     kept in sync on every run — this is what turns a row from "active" into
//     "history" without ever deleting it, per Carl's explicit design.
//
// Row lifecycle (Carl's explicit rules, 2026-08-24):
//   - Rows are permanent — once a thread is logged, it stays, even after it leaves
//     Focused. Status is what changes, not row presence.
//   - Every currently-Focused thread gets a row, whether or not it has a drafted
//     reply (Reply is blank when there's none).
//   - Existing rows are updated in place on each run, keyed by Thread_ID — never
//     duplicated across runs.
//   - Initial population is Focused-only, going forward — no backdating of
//     already-Other/Archived threads from before this feature existed.
//
// Usage:
//   node update-linkedin-message-log.js              # write both copies, then validate
//   node update-linkedin-message-log.js --dry-run    # report the diff, write nothing
//   node update-linkedin-message-log.js --self-test  # unit checks, touches no file
//   node update-linkedin-message-log.js --transcripts <file>   # extra capture file(s)

const fs = require('fs');
const path = require('path');

const SCRIPTS_DIR = __dirname;
const JOBSEARCH_DIR = path.join(SCRIPTS_DIR, '..');
const CSV_NAME = 'LinkedIn_Message_Log.csv';
const PRIMARY_PATH = path.join(JOBSEARCH_DIR, CSV_NAME);
const ONEDRIVE_ROOT = process.env.LI_LOG_ONEDRIVE_ROOT || path.join(
  require('os').homedir(),
  'Library', 'CloudStorage', 'OneDrive-DefaultDirectory'
);
// The mirror lives one folder down, in its own dedicated subfolder. A Fabric table
// shortcut maps one folder to exactly one Delta table and requires every file in that
// folder to share an identical schema, so this file cannot sit alongside
// JD_Evaluation_Log.csv in the OneDrive root. See "Downstream consumer contract —
// Company-423 Fabric" in ../instructions/04-log-and-write-discipline.md.
const ONEDRIVE_DIR = path.join(ONEDRIVE_ROOT, 'LinkedIn_Message_Log');
const ONEDRIVE_PATH = path.join(ONEDRIVE_DIR, CSV_NAME);
const BACKUP_DIR = path.join(JOBSEARCH_DIR, 'backups');
const LEDGER_PATH = path.join(SCRIPTS_DIR, 'linkedin-thread-ledger.json');

const COLUMNS = ['Thread_ID', 'Thread_URL', 'Date', 'Sender', 'Message', 'Reply', 'Status'];
const STATUSES = new Set(['Received', 'Replied', 'Archived']);

// Line-break marker. Message/Reply are free text and routinely arrive with hard line
// breaks, but the Fabric shortcut's CSV reader is not multiline-aware — an embedded
// newline shatters one logical record into many garbage rows. Collapse every run of
// line breaks into a single visible marker so each record stays on one physical line.
// Restore real breaks downstream with SUBSTITUTE([Reply], " ¶ ", UNICHAR(10)).
const NEWLINE_MARKER = ' ¶ ';

// ---------------------------------------------------------------------------
// [G2] Local-calendar date helpers. Never toISOString() for a date: it converts a
// local Date to UTC, which in America/Chicago rolls the day forward on any run after
// 19:00 and silently writes tomorrow's date into the log.
// ---------------------------------------------------------------------------
const p2 = (n) => String(n).padStart(2, '0');

function localDate(d) {
  return `${d.getFullYear()}-${p2(d.getMonth() + 1)}-${p2(d.getDate())}`;
}

function localStamp(d) {
  return `${d.getFullYear()}${p2(d.getMonth() + 1)}${p2(d.getDate())}_` +
         `${p2(d.getHours())}${p2(d.getMinutes())}${p2(d.getSeconds())}`;
}

// [G6] Trim BEFORE collapsing, not after. The old order replaced a leading or
// trailing run of line breaks with the marker first, and the trailing .trim() then
// could not remove it — "\n a \n" came out as "¶ a ¶", putting a stray pilcrow at the
// edge of the field in Power BI. Found by this script's own --self-test, 2026-08-28.
function flattenNewlines(value) {
  const s = (value === null || value === undefined) ? '' : String(value);
  return s.trim().replace(/[ \t]*(?:\r\n|\r|\n)+[ \t]*/g, NEWLINE_MARKER);
}

// RFC 4180 CSV field quoting — always quote (simplest correct approach given how many
// fields here routinely contain commas and quotes).
function csvField(value) {
  const s = flattenNewlines(value);
  return '"' + s.replace(/"/g, '""') + '"';
}

function toCsvRow(fields) {
  return COLUMNS.map((c) => csvField(fields[c])).join(',') + '\r\n';
}

function parseCsv(text) {
  // Minimal RFC 4180 parser sufficient for files this script itself writes
  // (always-quoted fields, CRLF row endings). Not a general-purpose CSV parser.
  const rows = [];
  let row = [];
  let field = '';
  let inQuotes = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (inQuotes) {
      if (c === '"') {
        if (text[i + 1] === '"') { field += '"'; i++; }
        else { inQuotes = false; }
      } else {
        field += c;
      }
    } else if (c === '"') {
      inQuotes = true;
    } else if (c === ',') {
      row.push(field); field = '';
    } else if (c === '\r' && text[i + 1] === '\n') {
      row.push(field); field = '';
      rows.push(row); row = [];
      i++;
    } else if (c === '\n') {
      row.push(field); field = '';
      rows.push(row); row = [];
    } else {
      field += c;
    }
  }
  if (field.length > 0 || row.length > 0) { row.push(field); rows.push(row); }
  return rows.filter((r) => r.length > 1 || r[0] !== '');
}

function halt(msg) {
  console.error(`HALT: ${msg}`);
  process.exit(1);
}

// [G5] The header is asserted, not trusted. The old version indexed columns by
// header.indexOf() and fell back to '' for a -1, so a renamed or dropped column
// silently blanked that field on every tracked row instead of stopping.
function loadExistingRows(csvPath) {
  if (!fs.existsSync(csvPath)) return new Map();
  const text = fs.readFileSync(csvPath, 'utf8');
  const rows = parseCsv(text);
  if (rows.length === 0) return new Map();
  const header = rows[0];
  if (header.length !== COLUMNS.length || COLUMNS.some((c, i) => header[i] !== c)) {
    halt(`${csvPath} header is ${JSON.stringify(header)}, expected ${JSON.stringify(COLUMNS)}. ` +
         `Refusing to read it — a mismatched header would blank every field it cannot find. ` +
         `Restore from backups/.`);
  }
  const byId = new Map();
  for (let i = 1; i < rows.length; i++) {
    const r = rows[i];
    if (r.length !== COLUMNS.length) {
      halt(`${csvPath} line ${i + 1} has ${r.length} fields, expected ${COLUMNS.length}. ` +
           `Restore from backups/.`);
    }
    const obj = {};
    COLUMNS.forEach((c, j) => { obj[c] = r[j]; });
    if (!obj.Thread_ID) halt(`${csvPath} line ${i + 1} has an empty Thread_ID.`);
    if (byId.has(obj.Thread_ID)) halt(`${csvPath} has a duplicate Thread_ID: ${obj.Thread_ID}.`);
    byId.set(obj.Thread_ID, obj);
  }
  return byId;
}

function backupIfExists(csvPath, label, now) {
  if (!fs.existsSync(csvPath)) return null;
  if (!fs.existsSync(BACKUP_DIR)) fs.mkdirSync(BACKUP_DIR, { recursive: true });
  // [G2] Local stamp, matching JD_Evaluation_Log's backups. The UTC stamp this used
  // to write put an evening run's backup under the next calendar day's name.
  const backupPath = path.join(BACKUP_DIR, `LinkedIn_Message_Log_${label}_${localStamp(now)}.csv`);
  fs.copyFileSync(csvPath, backupPath);
  return backupPath;
}

// Extracts the sender's most recent message (not Carl's) from a saved transcript,
// same "X sent the following message(s) at TIME" block parsing used elsewhere in
// this codebase (see classify-old-threads.js).
const DAY_LINE_RE = /^(TODAY|YESTERDAY|[A-Z]{3,9}\s+\d{1,2}(?:,\s*\d{4})?|MONDAY|TUESDAY|WEDNESDAY|THURSDAY|FRIDAY|SATURDAY|SUNDAY)$/;
const WEEKDAYS = ['SUNDAY', 'MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY'];
const MONTH_ABBR = { JAN: 0, FEB: 1, MAR: 2, APR: 3, MAY: 4, JUN: 5, JUL: 6, AUG: 7, SEP: 8, OCT: 9, NOV: 10, DEC: 11 };

// Resolves a day-divider marker ("TODAY", "TUESDAY", "AUG 21") plus a clock time into
// an actual calendar date — Carl wants a real, sortable date in the CSV, not a
// relative word that stops meaning anything the day after it's written.
//
// [G7] `asOf` is the moment the TRANSCRIPT WAS SCRAPED, never the moment this script
// runs. This was the worst defect in the script and it was invisible for three days:
// relative markers were resolved against `now`, so every run re-dated every
// relative-marker row forward to the run date. "TODAY" in a capture scraped
// 2026-08-25 means 2026-08-25 forever; resolving it on 2026-08-28 silently rewrote
// Anthony Soriano 08-25 -> 08-28, Natalie Sherrill 08-19 -> 08-26, and five more.
// It hid because both prior runs happened on the same day as the scrape. Caught
// 2026-08-28 by diffing a real run against a pre-run snapshot — the output was
// supposed to be a no-op and was not. Same family as the 2026-08-27 "27 rows dated a
// day early" incident: a date derived from when the code ran rather than from when
// the thing happened.
function resolveDate(dayMarker, timeText, asOf) {
  let d = null;
  if (!dayMarker || dayMarker === 'TODAY') {
    d = new Date(asOf);
  } else if (dayMarker === 'YESTERDAY') {
    d = new Date(asOf); d.setDate(d.getDate() - 1);
  } else if (WEEKDAYS.includes(dayMarker)) {
    const targetDow = WEEKDAYS.indexOf(dayMarker);
    d = new Date(asOf);
    let diff = (d.getDay() - targetDow + 7) % 7;
    if (diff === 0) diff = 7; // a bare weekday name always means a past occurrence, not today
    d.setDate(d.getDate() - diff);
  } else {
    const m = dayMarker.match(/^([A-Z]{3,9})\s+(\d{1,2})(?:,\s*(\d{4}))?$/);
    if (m && MONTH_ABBR[m[1].slice(0, 3)] !== undefined) {
      const month = MONTH_ABBR[m[1].slice(0, 3)];
      const day = parseInt(m[2], 10);
      let year = m[3] ? parseInt(m[3], 10) : asOf.getFullYear();
      d = new Date(year, month, day);
      if (!m[3] && d > asOf) d.setFullYear(year - 1); // undated "AUG 21" past the scrape date means last year
    }
  }
  if (!d) return timeText || '';
  const iso = localDate(d); // [G2] local calendar day, not the UTC one
  return timeText ? `${iso} ${timeText}` : iso;
}

// Who spoke last in the thread? Drives the Received/Replied distinction. Note this is
// about messages actually IN the thread — a drafted-but-unsent reply does not make the
// thread "Replied"; Carl has to have actually sent something.
function lastSpeakerIsCarl(transcript) {
  if (!transcript) return null; // [G4] "no evidence", distinct from "not Carl"
  const blockRe = /([^\n]+?) sent the following messages? at ([^\n]+)\n/g;
  let m;
  let lastSender = null;
  while ((m = blockRe.exec(transcript)) !== null) lastSender = m[1].trim();
  if (lastSender === null) return null;
  return lastSender.startsWith('Carl Wooldridge');
}

// Status vocabulary (revised 2026-08-25). Archived is a disposition and outranks the
// conversational state — a thread moved to Other or Archived reads Archived no matter
// who spoke last. Otherwise it reflects which way the ball is facing.
//
// [G4] priorStatus is the fallback when there is no transcript to recompute from.
// The protocol says Status is re-derived every run, but re-deriving it from absent
// evidence is not re-deriving, it is defaulting — and the old default was Received,
// the actionable state. Returns {status, source} so the caller can report every row
// whose Status was carried rather than computed.
function deriveStatus(disposition, transcript, priorStatus) {
  if (disposition === 'other' || disposition === 'archived') {
    return { status: 'Archived', source: 'disposition' };
  }
  const carlSpokeLast = lastSpeakerIsCarl(transcript);
  if (carlSpokeLast === null) {
    if (priorStatus && STATUSES.has(priorStatus) && priorStatus !== 'Archived') {
      return { status: priorStatus, source: 'carried' };
    }
    // A brand-new Focused row with no transcript: the thread is in the inbox and
    // nothing says Carl has answered it, so Received is the honest reading — but it
    // is a guess, and the run summary says so.
    return { status: 'Received', source: 'assumed' };
  }
  return { status: carlSpokeLast ? 'Replied' : 'Received', source: 'transcript' };
}

function extractLastTheirMessage(transcript, participantName, asOf) {
  // Day-divider lines (e.g. "TODAY", "AUG 21", "FRIDAY") appear on their own line
  // before a run of messages and aren't repeated on every message — track the most
  // recent one seen as we scan down, so a time like "11:26 AM" can be paired with
  // the actual day it belongs to, not just left as a bare time-of-day.
  const blockRe = /([^\n]+?) sent the following messages? at ([^\n]+)\n([\s\S]*?)(?=\n[^\n]+? sent the following messages? at |\n?$)/g;

  let m;
  let lastTheirBlock = null;
  let lastTheirDate = null;
  let lastKnownDayMarker = ''; // carries forward across messages within the same day
  while ((m = blockRe.exec(transcript)) !== null) {
    const sender = m[1].trim();

    // Update the running day-marker from every line between the previous match and
    // this one (not just a short lookback window) — a message later in the same day
    // has no marker of its own and must inherit the last one seen, however far back.
    const segment = transcript.slice(0, m.index);
    const segLines = segment.split('\n');
    for (let i = segLines.length - 1; i >= 0; i--) {
      const l = segLines[i].trim();
      if (DAY_LINE_RE.test(l)) { lastKnownDayMarker = l; break; }
    }

    if (sender.startsWith('Carl Wooldridge')) continue;
    lastTheirBlock = m[3].trim();
    lastTheirDate = resolveDate(lastKnownDayMarker, m[2].trim(), asOf);
  }
  if (!lastTheirBlock) {
    // Fallback: whole transcript is one message with no clear "sent the following" markers.
    return { message: transcript.trim().slice(0, 2000), dateText: null };
  }
  // Strip boilerplate header lines that precede the actual body — there can be more
  // than one in sequence ("View X's profile" followed by a repeated "Name  Time"
  // line), so loop rather than removing just the first line.
  const lines = lastTheirBlock.split('\n');
  const firstName = participantName.split(' ')[0];
  while (lines.length > 1) {
    const l = lines[0].trim();
    const isViewProfileLine = /^View .+.s profile$/i.test(l);
    const isNameTimeLine = l.startsWith(firstName) && /\d{1,2}:\d{2}\s*(AM|PM)?\s*$/i.test(l);
    if (isViewProfileLine || isNameTimeLine) lines.shift();
    else break;
  }
  // Strip LinkedIn's own trailing quick-reply suggestion chips ("Reply to
  // conversation with "X"" followed by the chip's own label text) — these are UI
  // suggestions for what Carl could send, not anything either party actually sent,
  // and they trail the real message text with no header of their own to split on.
  const quickReplyIdx = lines.findIndex(l => /^Reply to conversation with/i.test(l.trim()));
  const trimmedLines = quickReplyIdx === -1 ? lines : lines.slice(0, quickReplyIdx);
  return { message: trimmedLines.join('\n').trim().slice(0, 3000), dateText: lastTheirDate };
}

// ---------------------------------------------------------------------------
// [G3] Transcript source discovery. The old version listed six filenames and took
// the FIRST match for a thread. fetch-linkedin-messages.js accepts --out and can
// write anywhere, so any capture not on that list was invisible; and "first" only
// happened to mean "newest" because of the order someone typed the list in. Every
// capture file carries its own `scrapedAt`, so rank by that and let the newest win.
// ---------------------------------------------------------------------------
const TRANSCRIPT_GLOB_DIRS = [
  SCRIPTS_DIR,
  path.join(JOBSEARCH_DIR, 'scratch', 'linkedin-discovery'),
  path.join(JOBSEARCH_DIR, 'scratch'),
];

function discoverTranscriptSources(extraPaths) {
  const candidates = new Set(extraPaths.map((p) => path.resolve(p)));
  for (const dir of TRANSCRIPT_GLOB_DIRS) {
    if (!fs.existsSync(dir)) continue;
    for (const name of fs.readdirSync(dir)) {
      if (name.endsWith('.json')) candidates.add(path.join(dir, name));
    }
  }
  const sources = [];
  for (const p of candidates) {
    let d;
    try { d = JSON.parse(fs.readFileSync(p, 'utf8')); } catch (e) { continue; }
    if (!d || !Array.isArray(d.threads)) continue;
    if (!d.threads.some((t) => t && t.thread_id && typeof t.transcript === 'string')) continue;
    // A capture with no scrapedAt cannot be ranked against one that has it. Fall back
    // to the file's mtime and say so, rather than silently treating it as oldest.
    const stamped = typeof d.scrapedAt === 'string' && !Number.isNaN(Date.parse(d.scrapedAt));
    const when = stamped ? Date.parse(d.scrapedAt) : fs.statSync(p).mtimeMs;
    sources.push({ path: p, when, stamped, threads: d.threads });
  }
  sources.sort((a, b) => b.when - a.when); // newest first
  return sources;
}

function buildTranscriptIndex(sources) {
  const byThreadId = {};
  for (const src of sources) {
    for (const t of src.threads) {
      if (!t || !t.thread_id) continue;
      if (t.thread_id in byThreadId) continue; // sources are newest-first, so first wins == newest wins
      byThreadId[t.thread_id] = { thread: t, source: src };
    }
  }
  return byThreadId;
}

// ---------------------------------------------------------------------------
// [G1] Post-write validation. Everything below this line is what the script used to
// be missing entirely. It re-reads what was actually written, from disk, and treats
// any disagreement as a failure to be rolled back rather than a warning to print.
// ---------------------------------------------------------------------------
function validateWritten(csvPath, expectedRows) {
  const text = fs.readFileSync(csvPath, 'utf8');
  const rows = parseCsv(text);
  if (rows.length === 0) return `${csvPath} re-read as empty.`;

  const header = rows[0];
  if (header.length !== COLUMNS.length || COLUMNS.some((c, i) => header[i] !== c)) {
    return `${csvPath} header re-read as ${JSON.stringify(header)}, expected ${JSON.stringify(COLUMNS)}.`;
  }
  const body = rows.slice(1);
  if (body.length !== expectedRows.length) {
    return `${csvPath} row count re-read as ${body.length}, expected ${expectedRows.length}.`;
  }
  const seen = new Set();
  for (let i = 0; i < body.length; i++) {
    const r = body[i];
    const line = i + 2;
    if (r.length !== COLUMNS.length) {
      return `${csvPath} line ${line} re-read with ${r.length} fields, expected ${COLUMNS.length}.`;
    }
    for (let j = 0; j < r.length; j++) {
      if (/[\r\n]/.test(r[j])) {
        // The whole point of the pilcrow flattener — a raw newline here means the
        // Fabric reader will shatter this record into garbage rows.
        return `${csvPath} line ${line}, column ${COLUMNS[j]}: raw line break survived the flattener.`;
      }
    }
    const expect = expectedRows[i];
    for (const c of COLUMNS) {
      const want = flattenNewlines(expect[c]);
      if (r[COLUMNS.indexOf(c)] !== want) {
        return `${csvPath} line ${line}, column ${c}: wrote ${JSON.stringify(want)}, ` +
               `re-read ${JSON.stringify(r[COLUMNS.indexOf(c)])}.`;
      }
    }
    const id = r[0];
    if (!id) return `${csvPath} line ${line} has an empty Thread_ID.`;
    if (seen.has(id)) return `${csvPath} line ${line} duplicates Thread_ID ${id}.`;
    seen.add(id);
    if (!STATUSES.has(r[COLUMNS.indexOf('Status')])) {
      return `${csvPath} line ${line} Status is ${JSON.stringify(r[COLUMNS.indexOf('Status')])}, ` +
             `not one of ${[...STATUSES].join('/')}.`;
    }
  }
  return null;
}

function writeAtomic(csvPath, text) {
  const tmp = csvPath + '.updating';
  fs.writeFileSync(tmp, text, 'utf8');
  fs.renameSync(tmp, csvPath);
}

function restore(backupPath, csvPath) {
  if (backupPath && fs.existsSync(backupPath)) {
    fs.copyFileSync(backupPath, csvPath);
    return true;
  }
  return false;
}

// ---------------------------------------------------------------------------
// Self-test. Same convention as triage-match.py / stale-sweep.py --self-test: it
// touches no file and every case below is one that actually went wrong.
// ---------------------------------------------------------------------------
function selfTest() {
  let failures = 0;
  const check = (name, got, want) => {
    const ok = JSON.stringify(got) === JSON.stringify(want);
    if (!ok) { failures++; console.log(`  FAIL ${name}\n       got  ${JSON.stringify(got)}\n       want ${JSON.stringify(want)}`); }
    else console.log(`  ok   ${name}`);
  };

  console.log('[G2] date resolution is local-calendar, not UTC');
  // The regression: 20:30 local used to resolve TODAY to the next calendar day.
  const evening = new Date(2026, 7, 28, 20, 30, 0);      // Fri 2026-08-28 20:30 local
  const lateNight = new Date(2026, 7, 28, 23, 45, 0);
  const morning = new Date(2026, 7, 28, 9, 0, 0);
  check('TODAY at 20:30 local', resolveDate('TODAY', '8:30 PM', evening), '2026-08-28 8:30 PM');
  check('TODAY at 23:45 local', resolveDate('TODAY', '11:45 PM', lateNight), '2026-08-28 11:45 PM');
  check('TODAY at 09:00 local', resolveDate('TODAY', '9:00 AM', morning), '2026-08-28 9:00 AM');
  check('YESTERDAY at 20:30 local', resolveDate('YESTERDAY', '4:00 PM', evening), '2026-08-27 4:00 PM');
  check('MONDAY at 21:00 local (Fri)', resolveDate('MONDAY', '2:00 PM', new Date(2026, 7, 28, 21, 0, 0)), '2026-08-24 2:00 PM');
  check('AUG 21 at 21:00 local', resolveDate('AUG 21', '10:00 AM', new Date(2026, 7, 28, 21, 0, 0)), '2026-08-21 10:00 AM');
  check('local stamp is local', localStamp(evening), '20260828_203000');

  console.log('[G7] relative markers anchor to the scrape, not to the run');
  // The live regression: a capture scraped Tue 2026-08-25 11:29, read on Fri 2026-08-28.
  const scraped = new Date(2026, 7, 25, 18, 9, 50);   // linkedin-threads.json's real scrapedAt, local
  const readOn  = new Date(2026, 7, 28, 13, 34, 0);   // the 2026-08-28 run that exposed it
  check('TODAY anchored to scrape', resolveDate('TODAY', '11:29 AM', scraped), '2026-08-25 11:29 AM');
  check('TODAY is NOT anchored to run date', resolveDate('TODAY', '11:29 AM', scraped) !== resolveDate('TODAY', '11:29 AM', readOn), true);
  check('YESTERDAY anchored to scrape', resolveDate('YESTERDAY', '5:34 PM', scraped), '2026-08-24 5:34 PM');
  // Natalie Sherrill: "TUESDAY" in a Tue 08-25 capture means the PREVIOUS Tuesday, 08-18.
  check('weekday anchored to scrape', resolveDate('TUESDAY', '5:34 PM', scraped), '2026-08-18 5:34 PM');
  check('absolute marker is anchor-independent', resolveDate('AUG 19', '5:34 PM', scraped), resolveDate('AUG 19', '5:34 PM', readOn));
  // Re-resolving the same capture on a later day must be a no-op — this is the
  // property whose absence re-dated seven rows.
  check('re-run on a later day is a no-op', resolveDate('MONDAY', '9:48 AM', scraped), resolveDate('MONDAY', '9:48 AM', scraped));

  console.log('[G4] status is carried, never defaulted, when there is no transcript');
  const T_CARL = 'Carl Wooldridge sent the following message at 2:21 PM\nhi\n';
  const T_THEM = 'Jase Renneke sent the following message at 3:25 PM\nhello\n';
  check('transcript, Carl last', deriveStatus('focused', T_CARL, 'Received'), { status: 'Replied', source: 'transcript' });
  check('transcript, them last', deriveStatus('focused', T_THEM, 'Replied'), { status: 'Received', source: 'transcript' });
  check('no transcript, prior Replied', deriveStatus('focused', undefined, 'Replied'), { status: 'Replied', source: 'carried' });
  check('no transcript, prior Received', deriveStatus('focused', undefined, 'Received'), { status: 'Received', source: 'carried' });
  check('no transcript, brand new row', deriveStatus('focused', undefined, ''), { status: 'Received', source: 'assumed' });
  check('disposition outranks transcript', deriveStatus('other', T_CARL, 'Replied'), { status: 'Archived', source: 'disposition' });
  check('archived outranks transcript', deriveStatus('archived', T_THEM, 'Received'), { status: 'Archived', source: 'disposition' });
  // A stale Archived must not resurrect a Focused thread as Archived.
  check('re-focused thread does not carry Archived', deriveStatus('focused', undefined, 'Archived'), { status: 'Received', source: 'assumed' });

  console.log('flattener keeps every record on one physical line');
  check('LF run collapses', flattenNewlines('a\n\nb'), 'a ¶ b');
  check('CRLF collapses', flattenNewlines('a\r\nb'), 'a ¶ b');
  check('surrounding space absorbed', flattenNewlines('a  \n\t b'), 'a ¶ b');
  check('leading/trailing breaks trimmed, no stray marker [G6]', flattenNewlines('\n a \n'), 'a');
  check('leading break, interior break kept [G6]', flattenNewlines('\na\nb\n'), 'a ¶ b');
  check('no break, untouched', flattenNewlines('a, "b"'), 'a, "b"');

  console.log('[G1] validation catches what it exists to catch');
  const good = [{ Thread_ID: 'x', Thread_URL: 'u', Date: '2026-08-28', Sender: 's', Message: 'm\nn', Reply: '', Status: 'Received' }];
  const tmpDir = fs.mkdtempSync(path.join(require('os').tmpdir(), 'limsglog-'));
  const tmpCsv = path.join(tmpDir, 'x.csv');
  writeAtomic(tmpCsv, COLUMNS.join(',') + '\r\n' + toCsvRow(good[0]));
  check('clean file validates', validateWritten(tmpCsv, good), null);
  check('row-count mismatch caught', typeof validateWritten(tmpCsv, [...good, good[0]]), 'string');
  writeAtomic(tmpCsv, 'Thread_ID,Nope\r\n"x","y"\r\n');
  check('bad header caught', typeof validateWritten(tmpCsv, good), 'string');
  // A raw newline inside a quoted field: RFC-legal, but fatal to the Fabric reader.
  writeAtomic(tmpCsv, COLUMNS.join(',') + '\r\n' + '"x","u","2026-08-28","s","m\nn","","Received"\r\n');
  check('raw newline in field caught', typeof validateWritten(tmpCsv, good), 'string');
  writeAtomic(tmpCsv, COLUMNS.join(',') + '\r\n' + toCsvRow({ ...good[0], Status: 'Focused' }));
  check('bad Status caught', typeof validateWritten(tmpCsv, [{ ...good[0], Status: 'Focused' }]), 'string');
  fs.rmSync(tmpDir, { recursive: true, force: true });

  console.log(failures === 0 ? '\nself-test: all checks passed.' : `\nself-test: ${failures} FAILURE(S).`);
  process.exit(failures === 0 ? 0 : 1);
}

// ---------------------------------------------------------------------------

function main() {
  const argv = process.argv.slice(2);
  if (argv.includes('--self-test')) return selfTest();
  const dryRun = argv.includes('--dry-run');
  const verbose = argv.includes('--verbose');
  const extraTranscripts = [];
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--transcripts' && argv[i + 1]) extraTranscripts.push(argv[++i]);
  }

  const now = new Date();
  if (!fs.existsSync(LEDGER_PATH)) halt(`ledger not found at ${LEDGER_PATH}.`);
  const ledger = JSON.parse(fs.readFileSync(LEDGER_PATH, 'utf8'));

  const sources = discoverTranscriptSources(extraTranscripts);
  if (sources.length === 0) halt('no transcript capture files found. Run fetch-linkedin-messages.js first.');
  const byThreadId = buildTranscriptIndex(sources);

  console.log('Transcript sources (newest first, newest wins per thread):');
  for (const s of sources) {
    const age = ((now - s.when) / 86400000).toFixed(1);
    console.log(`  ${localDate(new Date(s.when))} (${age}d old${s.stamped ? '' : ', mtime — no scrapedAt'})  ` +
                `${s.threads.length} thread(s)  ${path.relative(JOBSEARCH_DIR, s.path)}`);
  }

  const existingPrimary = loadExistingRows(PRIMARY_PATH);
  const existingOneDrive = loadExistingRows(ONEDRIVE_PATH);
  // Merge: primary is source of truth if both exist and differ; this is a simple
  // single-writer file (no Carl-owned columns), so no reconciliation logic is needed
  // beyond "primary wins" — unlike JD_Evaluation_Log.csv.
  const merged = new Map(existingOneDrive);
  for (const [id, row] of existingPrimary) merged.set(id, row);
  const startingIds = new Set(merged.keys());

  // Eligibility, per Carl's explicit rule (2026-08-24): a thread only ever enters this
  // CSV by being seen in Focused. Once added, its row is permanent (Status updates,
  // row never disappears) — but a thread that was Other/Archived BEFORE this feature
  // existed, and was never Focused since, must never get a row. That ledger holds 90+
  // such historical entries from the pre-CSV backlog sweep; iterating the whole ledger
  // unconditionally backdated all of them into this file on the very first run — caught
  // and fixed before Carl saw it. The eligible set is exactly: currently-Focused ledger
  // entries, union already-tracked rows from a prior run of this script.
  let updated = 0, added = 0;
  const statusChanges = [];
  const dateChanges = [];
  const carried = [];
  const assumed = [];
  const noTranscript = [];

  for (const entry of ledger) {
    const isCurrentlyFocused = entry.disposition === 'focused';
    const alreadyTracked = merged.has(entry.thread_id);
    if (!isCurrentlyFocused && !alreadyTracked) continue;

    // Start from the existing row (if any) so a run with no fresh transcript/draft
    // data available never blanks out Message/Reply that a prior run already
    // captured — only overwrite a field when fresh data is actually found this run.
    const priorRow = merged.get(entry.thread_id) || {};

    const hit = byThreadId[entry.thread_id];
    const t = hit && hit.thread;
    let message = priorRow.Message || '';
    let dateText = priorRow.Date || entry.last_message_at || '';
    if (t && t.transcript) {
      // [G7] Anchor relative day markers to when this capture was scraped, not to now.
      const asOf = new Date(hit.source.when);
      const extracted = extractLastTheirMessage(t.transcript, entry.participant, asOf);
      if (extracted.message) message = extracted.message;
      if (extracted.dateText) dateText = extracted.dateText;
    } else {
      noTranscript.push(entry.participant);
    }

    let reply = priorRow.Reply || '';
    if (entry.draft_file) {
      const draftPath = path.join(JOBSEARCH_DIR, entry.draft_file);
      if (fs.existsSync(draftPath)) {
        const draftText = fs.readFileSync(draftPath, 'utf8');
        const m = draftText.match(/## Draft reply\s*\n\n([\s\S]*?)\s*$/);
        if (m) reply = m[1].trim();
      }
    }

    const { status, source } = deriveStatus(entry.disposition, t && t.transcript, priorRow.Status);
    if (source === 'carried') carried.push(`${entry.participant} (${status})`);
    if (source === 'assumed') assumed.push(`${entry.participant} (${status})`);
    if (priorRow.Status && priorRow.Status !== status) {
      statusChanges.push(`${entry.participant}: ${priorRow.Status} -> ${status} (${source})`);
    }
    // [G7] A Date that moves on an already-tracked row is the signature of the bug
    // that re-dated seven rows on 2026-08-28. It is legitimate only when the thread
    // genuinely has a newer message from them, so it is always reported, never silent.
    if (priorRow.Date && priorRow.Date !== dateText) {
      dateChanges.push(`${entry.participant}: ${priorRow.Date} -> ${dateText}`);
    }

    const row = {
      Thread_ID: entry.thread_id,
      Thread_URL: entry.thread_url,
      Date: dateText,
      Sender: entry.participant,
      Message: message,
      Reply: reply,
      Status: status,
    };

    if (merged.has(entry.thread_id)) updated++; else added++;
    merged.set(entry.thread_id, row);
  }

  // A row must never disappear — rows are permanent by Carl's rule, so a shrinking
  // file is a bug, not an update.
  for (const id of startingIds) {
    if (!merged.has(id)) halt(`Thread_ID ${id} was in the file and is not in the output. Rows are permanent.`);
  }

  const outRows = [...merged.values()];
  let out = COLUMNS.join(',') + '\r\n';
  for (const row of outRows) out += toCsvRow(row);

  // ---- report ----
  console.log(`\nRows: ${added} added, ${updated} updated, ${outRows.length} total.`);
  if (statusChanges.length) {
    console.log(`  Status changes (${statusChanges.length}):`);
    for (const c of statusChanges) console.log(`    ${c}`);
  } else {
    console.log('  Status changes: none');
  }
  if (dateChanges.length) {
    console.log(`  Date changes (${dateChanges.length}) — each should correspond to a genuinely newer message:`);
    for (const c of dateChanges) console.log(`    ${c}`);
  } else {
    console.log('  Date changes: none');
  }
  // [G4] These two lists are the whole reason the carry-forward exists. Silence here
  // used to mean "everything recomputed"; it actually meant "some rows silently reset".
  console.log(`  Status carried forward, no transcript this run (${carried.length}):` +
              (carried.length ? '\n    ' + carried.join('\n    ') : ' none'));
  console.log(`  Status assumed Received, new row with no transcript (${assumed.length}):` +
              (assumed.length ? '\n    ' + assumed.join('\n    ') : ' none'));
  if (verbose && noTranscript.length) {
    console.log(`  No transcript found for: ${noTranscript.join(', ')}`);
  }

  if (dryRun) {
    console.log('\nDry run — nothing written. Re-run without --dry-run to write.');
    return;
  }

  const primaryBackup = backupIfExists(PRIMARY_PATH, 'primary', now);
  const oneDriveBackup = backupIfExists(ONEDRIVE_PATH, 'OneDrive', now);

  writeAtomic(PRIMARY_PATH, out);
  let mirrored = false;
  if (!fs.existsSync(ONEDRIVE_ROOT)) {
    console.log(`\nWARNING: OneDrive folder not found at ${ONEDRIVE_ROOT} — primary written, mirror skipped.`);
  } else {
    fs.mkdirSync(ONEDRIVE_DIR, { recursive: true });
    writeAtomic(ONEDRIVE_PATH, out);
    mirrored = true;
  }

  // [G1] Post-write validation. Re-read from disk — not from `out` — so a truncated
  // write, an encoding surprise or a sync client rewriting the file is caught here
  // rather than a week later in Fabric.
  const problems = [];
  const p1 = validateWritten(PRIMARY_PATH, outRows);
  if (p1) problems.push(p1);
  if (mirrored) {
    const p2v = validateWritten(ONEDRIVE_PATH, outRows);
    if (p2v) problems.push(p2v);
    const a = fs.readFileSync(PRIMARY_PATH);
    const b = fs.readFileSync(ONEDRIVE_PATH);
    if (!a.equals(b)) problems.push('primary and OneDrive copies differ byte-for-byte after write.');
  }

  if (problems.length) {
    console.error('\nVALIDATION FAILED:');
    for (const p of problems) console.error(`  ${p}`);
    const r1 = restore(primaryBackup, PRIMARY_PATH);
    const r2 = mirrored ? restore(oneDriveBackup, ONEDRIVE_PATH) : false;
    console.error(`  Restored from this run's backup: primary=${r1}, OneDrive=${r2}.`);
    if (!r1 || (mirrored && !r2)) {
      console.error(`  A copy could NOT be restored — recover by hand from ${BACKUP_DIR}.`);
    }
    process.exit(1);
  }

  console.log(`\nValidated: header, ${outRows.length} rows x ${COLUMNS.length} fields, ` +
              `no raw line breaks, Status in {${[...STATUSES].join('/')}}` +
              (mirrored ? ', both copies byte-identical.' : ', primary only (mirror skipped).'));
  console.log(`Primary:  ${PRIMARY_PATH}`);
  console.log(`OneDrive: ${mirrored ? ONEDRIVE_PATH : '(skipped)'}`);
}

main();
