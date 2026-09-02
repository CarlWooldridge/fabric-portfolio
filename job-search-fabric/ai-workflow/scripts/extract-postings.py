#!/usr/bin/env python3
"""
extract-postings.py — pull job postings out of LinkedIn alert .eml files.

Implements Step 1 ("Extract") of instructions/01-intake-and-fetch.md as a script.
This was the last step in Phase B still done by a model, and it was the one least
suited to it: it is MIME parsing, and getting it wrong silently drops postings
before evaluation ever sees them.

WHY THIS EXISTS — measured 2026-08-26 on the same 13 alert emails:

    reading text/plain only ......... 48 job IDs   (what two model-driven runs got)
    reading text/html ............... 54 job IDs   (correct)
    grepping the raw undecoded file .. 61 job IDs   (7 are garbage)

Two of the thirteen emails were forwards whose `text/plain` part is empty — every
posting in them lives only in the HTML. Reading the plain part alone silently lost
6 real postings. And grepping the raw file is worse than useless: quoted-printable
soft line breaks (`=\\n`) split IDs mid-string, so `4457618847` becomes `44576188`
plus `47`, and the short fragment matches as a bogus 8-digit ID.

THE RULE, therefore: walk the MIME tree, decode every text part properly, take the
union of text/html and text/plain, and never regex the undecoded bytes.

USAGE
    python3 scripts/extract-postings.py                  # every .eml in the folder root
    python3 scripts/extract-postings.py a.eml b.eml      # specific files
    python3 scripts/extract-postings.py --out scratch/extracted.json

Output is a JSON list shaped for `jd-dedupe.py --json`:
    [{"Job_ID": "...", "Company": "...", "Role_Title": "...", "Location": "...",
      "Comp_Posted": "...", "Applicant_Volume": "...", "Source": "LinkedIn job alert",
      "URL": "...", "_source_file": "..."}]

Fields other than Job_ID are best-effort: alert emails carry the title/company/location
block reliably, comp and applicant counts only sometimes. Anything not found is left
blank for the JD fetch to fill in — never guessed.
"""
import argparse, email, glob, html as htmllib, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

JOB_ID = re.compile(r"jobs/view/(\d{8,})")
# LinkedIn job IDs are 10 digits today. Anything shorter is a truncation artifact.
MIN_ID_LEN = 10

MONEY = re.compile(r"\$[\d,]+(?:\.\d{2})?(?:\s*[-–—]\s*\$?[\d,]+(?:\.\d{2})?)?"
                   r"(?:\s*(?:/|per\s+)(?:yr|year|hr|hour))?", re.I)
APPLICANTS = re.compile(r"([\d,]+)\+?\s*(?:applicants?|people clicked apply)", re.I)
TAG = re.compile(r"<[^>]+>")


def part_text(part):
    """Decoded text for one MIME part, HTML reduced to line-structured text.

    In HTML the job URL exists ONLY inside an <a href="..."> attribute, so tags must
    be rewritten to keep the href as visible text before the rest are stripped —
    stripping first deletes the thing we are looking for. (That bug is why the first
    version of this script found 0 postings in exactly the forwarded emails it was
    written to rescue.)
    """
    try:
        raw = part.get_payload(decode=True)
    except Exception:
        return ""
    if raw is None:
        return ""
    charset = part.get_content_charset() or "utf-8"
    try:
        text = raw.decode(charset, "replace")
    except LookupError:
        text = raw.decode("utf-8", "replace")

    if part.get_content_type() == "text/html":
        text = re.sub(r"(?is)<(script|style).*?</\1>", " ", text)
        # Surface every href as its own text line BEFORE any tag is removed.
        text = re.sub(r'(?is)<a\b[^>]*?href\s*=\s*["\']([^"\']+)["\'][^>]*>',
                      lambda m: "\n" + htmllib.unescape(m.group(1)) + "\n", text)
        text = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</tr>|</td>|</a>", "\n", text)
        text = TAG.sub("\n", text)
        text = htmllib.unescape(text)
    return re.sub(r"[ \t\xa0]+", " ", text)


def blocks(text):
    """Yield (job_id, preceding_lines, following_lines) for each posting link."""
    lines = [l.strip() for l in text.split("\n")]
    for i, line in enumerate(lines):
        m = JOB_ID.search(line)
        if not m:
            continue
        jid = m.group(1)
        if len(jid) < MIN_ID_LEN:
            continue                       # truncation artifact, not a job
        before = [l for l in lines[max(0, i - 12):i] if l]
        after = [l for l in lines[i + 1:i + 8] if l]
        yield jid, before, after


# Lines that sit inside the title/company/location block but are not part of it.
# LinkedIn interleaves badges ("This company is actively hiring", "4 school alumni
# work here") between the location and the link, which shifts a naive last-3-lines
# window and silently swaps Company with Location. Filter them before windowing.
NOISE = re.compile(
    r"^("
    r"view job|see all jobs|view all|apply|unsubscribe|linkedin|this email|"
    r"you are receiving|new jobs? match|a new job matches|your job alert|"
    r"actively recruiting|actively hiring|this company is|"
    r"be an early applicant|easy apply|promoted|viewed|reposted|"
    r"\d+ (school )?alumni|\d+ connections?|\d+ applicants?|"
    r"\d+ (new )?jobs?|https?://|·|—|-{2,}"
    r")\b", re.I)

# A location line is not a company name. Used to sanity-check the parsed block.
LOCATION_LIKE = re.compile(
    r"(,\s*[A-Z]{2}$)|^(united states|remote|usa|u\.s\.)$|"
    r"(metropolitan area$)|(\b(area|region)$)", re.I)


def fields_from(before, after):
    """The alert renders title / company / location on the lines above the link."""
    clean = [l for l in before if l and not NOISE.match(l) and not JOB_ID.search(l)]
    tail = clean[-3:] if len(clean) >= 3 else clean
    title = company = location = ""
    if len(tail) == 3:
        title, company, location = tail
    elif len(tail) == 2:
        title, company = tail
    elif len(tail) == 1:
        title = tail[0]

    # Sanity check: the block is title / company / location in that order. If what
    # landed in Company reads like a place and Location does not, the window was off
    # by one — drop both rather than record a location as the employer, which would
    # poison repost detection in jd-dedupe.py. Blank is recoverable; wrong is not.
    if company and LOCATION_LIKE.search(company) and not (location and LOCATION_LIKE.search(location)):
        if not location:
            location, company = company, ""
        else:
            company = ""

    ctx = " ".join(before[-6:] + after)
    money = MONEY.search(ctx)
    apps = APPLICANTS.search(ctx)
    return {"Role_Title": title, "Company": company, "Location": location,
            "Comp_Posted": money.group(0) if money else "",
            "Applicant_Volume": apps.group(1) if apps else ""}


def extract(path):
    """Job_ID and URL are guaranteed; the descriptive fields are best-effort.

    Two passes with different jobs, because they have different reliability:
      1. text/plain — the alert renders title / company / location as clean lines
         directly above the link, so fields parsed here are trustworthy.
      2. text/html  — the authoritative set of IDs (a superset; on forwarded alerts
         the plain part is empty entirely). Fields here are far less reliable, so an
         ID seen only in HTML is recorded with whatever the block yields and blank
         otherwise. Blank is honest: the JD fetch fills these in authoritatively, and
         a guessed company name would corrupt repost detection in jd-dedupe.py.
    """
    with open(path, errors="replace") as f:
        msg = email.message_from_file(f)
    found = {}
    for want in ("text/plain", "text/html"):
        for part in msg.walk():
            if part.get_content_type() != want:
                continue
            for jid, before, after in blocks(part_text(part)):
                fields = fields_from(before, after)
                if jid in found:
                    # Never let a weaker HTML parse overwrite good plain-text fields.
                    for k, v in fields.items():
                        if v and not found[jid].get(k):
                            found[jid][k] = v
                    continue
                rec = {"Job_ID": jid, "Source": "LinkedIn job alert",
                       "URL": f"https://www.linkedin.com/jobs/view/{jid}/",
                       "_source_file": os.path.basename(path),
                       "_seen_in": want}
                rec.update(fields)
                found[jid] = rec
    return found


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="*", help="*.eml (default: every .eml in the folder root)")
    ap.add_argument("--out", metavar="FILE", help="write JSON here (default: stdout)")
    args = ap.parse_args()

    files = args.files or sorted(glob.glob(os.path.join(ROOT, "*.eml")))
    if not files:
        sys.exit("No .eml files found.")

    merged, per_file = {}, []
    for p in files:
        got = extract(p)
        per_file.append((os.path.basename(p), len(got)))
        for jid, rec in got.items():
            if jid not in merged or not merged[jid].get("Role_Title"):
                merged[jid] = rec

    rows = sorted(merged.values(), key=lambda r: r["Job_ID"])
    e = sys.stderr
    print(f"\n  {len(files)} file(s) parsed\n", file=e)
    for name, n in per_file:
        print(f"    {n:>3}  {name[:66]}", file=e)
    complete = sum(1 for r in rows if r["Role_Title"] and r["Company"])
    print(f"\n  {len(rows)} unique postings"
          f"  |  {complete} with title+company  |  {len(rows)-complete} needing the JD fetch", file=e)

    out = json.dumps(rows, indent=2)
    if args.out:
        with open(args.out, "w") as f:
            f.write(out + "\n")
        print(f"  -> {args.out}\n", file=e)
    else:
        print(out)


if __name__ == "__main__":
    main()
