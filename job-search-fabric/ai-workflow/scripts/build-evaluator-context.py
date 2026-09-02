#!/usr/bin/env python3
"""Rebuild rubric/evaluator-context.md from the authoritative instruction files.

The jd-evaluator agent needs Row format (04) and the comp lookup / closed-posting
rules (01), but not the Fabric contract, the OneDrive mirror rules, the backup
discipline, or the fetch pipeline. Carrying those cost ~45KB in the agent's context
on every turn of every batch. This extracts the needed sections verbatim.

Sections are located by heading, not line number, so ordinary edits to the source
files do not silently shift the extract. `--check` verifies every heading still
resolves and that the controlled vocabularies made it in.
"""
import argparse, io, sys

SECTIONS = [
    # (path, start heading, end heading or None for "next heading of same-or-higher level")
    ("instructions/04-log-and-write-discipline.md",
     "## Row format", "### Backup before each write-batch", "Row format"),
    ("instructions/01-intake-and-fetch.md",
     "#### Applied-badge check", "#### Compensation retrieval", "Applied-badge check"),
    ("instructions/01-intake-and-fetch.md",
     "#### Compensation retrieval", "#### If Tier 1 fails", "Compensation retrieval"),
    ("instructions/01-intake-and-fetch.md",
     "#### Closed-posting check", None, "Closed postings"),
]
OUT = "rubric/evaluator-context.md"
# Must survive the extract or the agent silently invents vocabulary.
SENTINELS = ["Lane-advancing", "Bridge", "Out of lane", "Below floor", "Comp_Flag", "Score_Raw",
             "Applied-badge", "No longer accepting applications"]


def extract(path, start, end):
    """Slice from the line starting with `start` up to the line starting with `end`.

    Heading-anchored rather than line-numbered: these files get edited, and a fixed
    line range silently grabs the wrong text instead of failing loudly.
    """
    lines = open(path, encoding="utf-8").read().splitlines(keepends=True)
    try:
        a = next(i for i, l in enumerate(lines) if l.startswith(start))
    except StopIteration:
        raise LookupError(f"{path}: no heading starting {start!r}")
    if end is None:
        level = len(start) - len(start.lstrip("#"))
        b = len(lines)
        for i in range(a + 1, len(lines)):
            l = lines[i]
            if l.startswith("#") and (len(l) - len(l.lstrip("#"))) <= level:
                b = i
                break
    else:
        try:
            b = next(i for i, l in enumerate(lines) if l.startswith(end) and i > a)
        except StopIteration:
            raise LookupError(f"{path}: no end heading starting {end!r} after {start!r}")
    return "".join(lines[a:b])


HEADER = """# Evaluator context — row format, comp lookup, closed postings

**GENERATED FILE — do not edit by hand.**
Rebuild with `python3 scripts/build-evaluator-context.py`.

This is a verbatim extract of the sections of `instructions/04-log-and-write-discipline.md`
and `instructions/01-intake-and-fetch.md` that the jd-evaluator agent actually needs. It exists
so the evaluator does not carry the Fabric contract, the OneDrive mirror rules, the backup
discipline, or the fetch pipeline in its context on every turn — those are orchestrator
concerns and cost ~45KB per turn to no purpose.

The source files remain authoritative. If this file ever disagrees with them, they win —
say so in your report rather than picking one.

---

"""


def build():
    out = io.StringIO()
    out.write(HEADER)
    for path, start, end, label in SECTIONS:
        out.write(f"## From `{path}` — {label}\n\n")
        out.write(extract(path, start, end))
        out.write("\n---\n\n")
    return out.getvalue()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="verify boundaries and vocabularies without writing")
    args = ap.parse_args()

    problems = []
    try:
        text = build()
    except LookupError as e:
        print(f"FAIL: {e}", file=sys.stderr)
        return 1
    for s in SENTINELS:
        if s not in text:
            problems.append(f"controlled vocabulary {s!r} missing from the extract")

    if problems:
        for p in problems:
            print(f"FAIL: {p}", file=sys.stderr)
        return 1

    if args.check:
        print(f"OK: boundaries and vocabularies intact ({len(text)} bytes)")
        return 0

    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(text)
    print(f"wrote {OUT} ({len(text)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
