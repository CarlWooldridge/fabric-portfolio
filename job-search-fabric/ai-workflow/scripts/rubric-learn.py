#!/usr/bin/env python3
"""
rubric-learn.py — measure the rubric against Carl's actions and PROPOSE adjustments.

This script never changes the rubric. It writes `rubric/weights.proposed.json` and an
entry in `rubric/learning_log.md`; promoting a proposal to `rubric/weights.json` is a
separate, deliberate act (`--promote`, which only copies an already-reviewed proposal).
It never writes to JD_Evaluation_Log.csv, to the OneDrive mirror, or to Fabric.

    python3 scripts/rubric-learn.py              # measure + propose
    python3 scripts/rubric-learn.py --no-pull    # reuse scratch/fabric_actions.csv
    python3 scripts/rubric-learn.py --promote    # accept the standing proposal

WHAT IT MEASURES
  1. Override rate per rule — of the rows a rule killed, how many did Carl apply to
     anyway. This is the test that decides a rule's class:
         <= veto_max      -> veto      (nothing outweighs it)
         >= review_min    -> review    (routinely outweighed; compensable)
     A rule whose measured class differs from its declared class is proposed for
     reclassification, with the evidence attached.
     An application dated BEFORE the row was evaluated is not an override and is not
     counted — see `applied_before_evaluation` and the 2026-08-28 incident below.
  2. Component means, applied vs. passed, within the Pursue population — which
     components actually separate the two, and which point the wrong way.
  3. Review precision — of the rows Review would surface, how many became applications.
  4. A backtest of every proposed change over the training window, reporting both what
     it fixes and what it breaks. A proposal that trades recall for precision has to
     say so in numbers.

WHAT IT REFUSES TO DO
  - Move a rule on fewer than `min_n_to_move_a_rule` observations.
  - Move a component weight by more than `max_component_move_per_run`.
  - Use the `Outcome` field while it has no variance (see weights.json).
  - Touch anything outside rubric/.
"""
import argparse, csv, datetime, json, os, re, shutil, statistics as st, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RUBRIC = os.path.join(ROOT, "rubric")
WEIGHTS  = os.path.join(RUBRIC, "weights.json")
PROPOSED = os.path.join(RUBRIC, "weights.proposed.json")
LOG      = os.path.join(RUBRIC, "learning_log.md")
PULL     = os.path.join(ROOT, "scratch", "fabric_actions.csv")

VETO_MAX, REVIEW_MIN = 0.10, 0.25   # class boundaries on measured override rate
MIN_COMPONENT_DELTA = 0.50          # ignore component gaps smaller than this — noise, not signal
TODAY = datetime.date.today().isoformat()

# Pts_Perks stays in this list only because the Fabric model still carries the column
# for rows scored before 2026-08-10, when perks was removed and its 5 points moved to
# Skills. New rows leave it null. Do not treat it as a live component.
PTS = ["Pts_Lane", "Pts_Scope", "Pts_Comp", "Pts_Location",
       "Pts_Skills", "Pts_Perks", "Pts_Applicants", "Pts_Deductions"]


# Dates on which a rule change silently re-pointed values already written under an older
# meaning. Established by the 2026-08-31 sweep; see the incident log in
# instructions/REVAMP_PLAN.md. A measurement that pools rows across one of these is comparing
# two different scales, and nothing in the data says so — the strings and numbers look identical
# either side.
SCALE_BOUNDARIES = [
    {"date": "2026-08-10", "fields": ["Pts_Skills", "Pts_Perks", "Verdict"],
     "what": "perks removed and its 5 points moved to Skills (max 15 -> 20); the 50-69 Pursue "
             "band was deleted, so a pre-boundary `Pursue` includes scores that are now `Skip`"},
    {"date": "2026-08-26", "fields": ["Pts_Comp", "Comp_Flag"],
     "what": "comp floor raised VETO_LINE -> FLOOR, shifting every comp band and both Comp_Flag band "
             "names. (`Verdict` moved that day too — G1 demoted to Review, G3 split — but that "
             "one needs no boundary guard: `current_verdict_class()` re-derives the verdict from "
             "current rules on every read, per Carl's 2026-08-31 decision, so the stale label is "
             "never consulted. 13 rows are affected and are reported each run.)"},
]


def boundary_warnings(rows, fields):
    """Which scale boundaries does this population straddle, for the fields being compared?"""
    dates = sorted({(r.get("Date_Evaluated") or "")[:10] for r in rows} - {""})
    if not dates:
        return []
    out = []
    for b in SCALE_BOUNDARIES:
        touched = [f for f in b["fields"] if f in fields]
        if touched and dates[0] < b["date"] <= dates[-1]:
            n_before = sum(1 for r in rows if (r.get("Date_Evaluated") or "")[:10] < b["date"])
            out.append({"date": b["date"], "fields": touched, "what": b["what"],
                        "n_before": n_before, "n_after": len(rows) - n_before})
    return out


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def load_weights():
    with open(WEIGHTS) as f:
        return json.load(f)


def pull():
    print("  pulling current actions from Fabric...", file=sys.stderr)
    r = subprocess.run([sys.executable, os.path.join(HERE, "fabric-pull-actions.py")],
                       capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"Fabric pull failed:\n{r.stderr}")


def training_set(w):
    """Two populations, because the two measurements ask different questions.

    `rates` — every row a gate could have fired on, blank action INCLUDED. For a veto,
    "Carl never acted" is the expected outcome of the rule working, not a missing label:
    the question is only "of the rows this killed, how many did he apply to anyway?"
    Filtering to acted-on rows would leave a denominator of nothing but overrides and
    report every rule at ~100%.

    `components` — applied vs. passed within Pursue, blank action EXCLUDED. Here a blank
    genuinely is an absent label: the row was never judged either way.

    Both drop posting-status rows, whose Reason records that a listing closed rather than
    anything about Carl's preferences.
    """
    with open(PULL, newline="") as f:
        rows = list(csv.DictReader(f))
    start = w["training"]["window_start"]
    junk = re.compile(w["training"]["exclude_reason_match"], re.I)

    rates_pop, comp_pop = [], []
    dropped = {"posting_status": 0, "pre_window_pursue": 0, "blank_action": 0}
    for r in rows:
        if r.get("Verdict") == "Pass" and junk.search(r.get("Reason") or ""):
            dropped["posting_status"] += 1
            continue
        rates_pop.append(r)

        d = (r.get("Date_Evaluated") or "")[:10]
        if r.get("Verdict") == "Pursue" and d and d < start:
            dropped["pre_window_pursue"] += 1;  continue
        if not (r.get("Carls_Action") or "").strip():
            dropped["blank_action"] += 1;       continue
        comp_pop.append(r)
    return rows, rates_pop, comp_pop, dropped


def rule_fires(w, rule, r):
    """Does one declared rule fire on one row, under the rule's current definition?

    Split out 2026-08-31 so `current_verdict_class()` and `override_rates()` share one matcher
    rather than keeping two copies that can drift — the same reason `triage-match.py` imports
    `jd-dedupe.py`'s `norm()` instead of reimplementing it.

    Qualifiers are declared in weights.json, not hardcoded here (`outranked_by_employer_list`
    was previously an `if name == "contract"` special case, which meant G3b silently lacked the
    same protection).
    """
    if not re.search(rule["match_reason"], r.get("Reason") or "", re.I):
        return False
    if rule.get("excludes_reason_match") and re.search(rule["excludes_reason_match"],
                                                       r.get("Reason") or "", re.I):
        return False              # a veto-class reason on the same row outranks this one
    if rule.get("requires_field_match") and not field_matches(rule["requires_field_match"], r):
        return False              # the Reason says one thing and the field says another
    firms = re.compile("|".join(re.escape(f) for f in w["consulting_firms"]), re.I) \
            if w.get("consulting_firms") else None
    company = r.get("Company") or ""
    if rule.get("requires_employer_list") and not (firms and firms.search(company)):
        return False
    if rule.get("outranked_by_employer_list") and firms and firms.search(company):
        return False              # G3a outranks; not this rule's row to answer for
    return True


def current_verdict_class(w, r):
    """What class of gate does this row's `Reason` fire TODAY? "veto", "review", or None.

    Carl, 2026-08-31: **measure under current rules, not the rules in force at evaluation.**
    So the stored `Verdict` string is not read here — it is re-derived from the row's `Reason`
    against the classes currently declared in `weights.json`. A row evaluated 2026-08-14 whose
    `Reason` is `contract` counted as a veto then and counts as `review` now, because that is
    what the rule says now.

    **The stored column is never rewritten.** `Verdict` is a judgment field that
    `04-log-and-write-discipline.md` forbids overwriting, and a re-derivation is a reading, not a
    correction — the row was right when it was written. Re-derive at measurement time, every time.

    Veto outranks review, matching the documented precedence: Pass-type gates > Review >
    Skip-type gates.
    """
    classes = {rule["class"] for name, rule in w["rules"].items() if rule_fires(w, rule, r)}
    return "veto" if "veto" in classes else ("review" if "review" in classes else None)


def stale_verdicts(w, rows):
    """Rows whose stored `Verdict` disagrees with what the current rules would produce.

    Only the case that actually exists is reported: stored `Pass` (a veto verdict) on a row where
    no veto-class rule fires today but a review-class one does. G1's demotion and the G3 split on
    2026-08-26 did that to 22 rows. Reported, never written back.
    """
    out = []
    for r in rows:
        if (r.get("Verdict") or "").strip() != "Pass":
            continue
        if current_verdict_class(w, r) == "review":
            out.append({"Job_ID": r.get("Job_ID"), "date": (r.get("Date_Evaluated") or "")[:10],
                        "company": (r.get("Company") or "")[:28], "reason": (r.get("Reason") or "")[:40]})
    return out


def field_matches(fq, r):
    """Does a row's field satisfy a rule's `requires_field_match` qualifier?

    Supports an era split, because `Comp_Flag`'s vocabulary changed meaning under the rows
    (2026-08-26, when the comp floor was raised from VETO_LINE to FLOOR) without the strings changing
    or anything on the row recording which scheme it was written under. Both `Below floor` and
    `Sub-target` shifted by exactly one band, so a single pattern over the whole log is wrong for
    one era or the other.

    **The vocabulary and its era table are defined in
    `instructions/04-log-and-write-discipline.md` under `Comp_Flag`** — the single authoritative
    copy, collapsed there 2026-08-31. Not restated here: this docstring went stale once already
    by being one of four copies. The patterns themselves live in `rubric/weights.json` and are
    derived from that list, never the other way round.

    Declare `pattern_before` / `pattern_after` / `boundary_date` to read each row under the rules
    in force when it was evaluated; `pattern` alone still means "same everywhere". A row with no
    `Date_Evaluated` is read under the older scheme — it cannot be newer than the boundary if it
    predates the practice of dating rows at all.
    """
    v = r.get(fq["field"]) or ""
    if "boundary_date" in fq:
        d = (r.get("Date_Evaluated") or "")[:10]
        pat = fq["pattern_after"] if (d and d >= fq["boundary_date"]) else fq["pattern_before"]
    else:
        pat = fq["pattern"]
    return re.search(pat, v, re.I) is not None


def applied_before_evaluation(r):
    """True if Carl applied to this posting before the row was ever scored.

    Such a row is not an override. The gate had no opportunity to stop him — the evaluation
    that fired it did not exist yet. The 2026-08-12 backfill retro-logged months of Carl's
    application history and scored every row under the current rubric, so this is not an
    edge case: it is 142 of the 413 actioned rows in the pull.

    Ported 2026-08-31 from `recall-audit.py`, which carries the same rule and the incident
    that produced it. The signatures differ because the data does — there both dates come from
    a log row joined to a pull row, here the pull row carries both. **The comparison must stay
    identical**; a divergence would have the two scripts reporting different rates for the same
    rule. Both are covered by their own `--self-test`.

    A same-day pair counts as an override. Carl, 2026-08-31, on the two rows this decides
    (InterEx 4445507224 and Riana 4452713933): he does not remember either, and would count
    them as overrides. Backfilled rows sit months apart, so this boundary is not where the
    contamination lives — but it is the whole distance between G1 and veto class, so it is a
    real choice, not a formality.
    """
    ev = (r.get("Date_Evaluated") or "")[:10]
    ad = (r.get("Carls_Action_Date") or "")[:10]
    if not ev or not ad:
        return False
    return ad < ev


def override_rates(w, rows):
    """For each declared rule: how often did Carl apply despite it firing?

    "Despite" is the whole measurement, so the numerator counts only applications the rule
    could actually have prevented — an `Applied` dated before `Date_Evaluated` is dropped
    (`applied_before_evaluation`). `raw_override_rate` is reported alongside so the gap
    between the two stays visible rather than being quietly corrected away.

    2026-08-28: this function had no ordering check, and G1 `contract` was demoted from
    veto to review on 2026-08-26 on the strength of a 47% rate that is 9% once corrected.
    Any measurement of "Carl did X despite rule Y" must check that the evaluation came first.
    """
    out = {}
    for name, rule in w["rules"].items():
        fired = [r for r in rows if rule_fires(w, rule, r)]
        acted    = [r for r in fired if (r.get("Carls_Action") or "").strip()]
        applied  = [r for r in fired if r.get("Carls_Action") == "Applied"]
        pre      = [r for r in applied if applied_before_evaluation(r)]
        override = [r for r in applied if not applied_before_evaluation(r)]
        rate     = len(override) / len(fired) if fired else None
        raw_rate = len(applied)  / len(fired) if fired else None
        measured = None
        if rate is not None:
            measured = "veto" if rate <= VETO_MAX else ("review" if rate >= REVIEW_MIN else "borderline")
        out[name] = {"gate": rule["gate"], "declared": rule["class"], "measured_class": measured,
                     "n_fired": len(fired), "n_applied": len(applied), "n_acted": len(acted),
                     "n_override": len(override), "n_pre_dated": len(pre),
                     "override_rate": rate, "raw_override_rate": raw_rate,
                     "override_ids": [r.get("Job_ID") for r in override],
                     "pre_dated_ids": [r.get("Job_ID") for r in pre]}
    return out


def component_separation(rows):
    """Within Pursue rows, which components separate applied from passed?

    Same ordering guard as `override_rates`, for the same reason and applied to BOTH groups
    (2026-08-31). This measurement asks which component scores drove Carl's choice — so a row
    he decided on before it was ever scored carries no information about that, whichever way
    he decided. It is dropped, not moved to the other group: a pre-dated `Applied` is not
    evidence he passed, it is evidence the score played no part.

    The window exclusion in `training_set` hides most of this but not all of it: the
    2026-08-12 backfill rows are evaluated *after* `window_start` (2026-08-10) and carry
    action dates from months earlier, so they survive that filter and land here.

    `n_pre_dated_*` is reported rather than silently netted out — the size of what the guard
    removes is the check on whether it is doing anything.
    """
    pursue = [r for r in rows if r.get("Verdict") == "Pursue"]
    tp_all = [r for r in pursue if r.get("Carls_Action") == "Applied"]
    fp_all = [r for r in pursue if r.get("Carls_Action") == "Pass"]
    tp = [r for r in tp_all if not applied_before_evaluation(r)]
    fp = [r for r in fp_all if not applied_before_evaluation(r)]
    out = {}
    for p in PTS:
        a = [num(r.get(p)) for r in tp if num(r.get(p)) is not None]
        b = [num(r.get(p)) for r in fp if num(r.get(p)) is not None]
        if a and b:
            out[p] = {"applied_mean": round(st.mean(a), 2), "passed_mean": round(st.mean(b), 2),
                      "delta": round(st.mean(a) - st.mean(b), 2), "n_applied": len(a), "n_passed": len(b)}
    return {"n_pursue_applied": len(tp), "n_pursue_passed": len(fp),
            "n_pre_dated_applied": len(tp_all) - len(tp),
            "n_pre_dated_passed": len(fp_all) - len(fp),
            "boundaries": boundary_warnings(tp + fp, PTS),
            "components": out}


def watchlist(w, rates):
    """Rules the proposal machinery cannot speak for, so they do not go silent.

    Added 2026-08-31. `propose()` only ever emits a rule whose measured class differs from its
    declared class AND clears the n floor. Everything else produces nothing at all — no
    proposal, no note, no mention. Three ways a rule can disappear:

      borderline   measured between veto_max and review_min. Neither class is supported, so
                   no proposal is possible — but the rule is also, by that same measurement,
                   not sitting comfortably in its declared class. G1 `contract` landed here on
                   2026-08-31 at 11% and would otherwise never have come up again.
      unmeasured   the rule fired zero times. Usually the pattern is wrong rather than the rule
                   being unused — G2b and G3b both read n=0 until 2026-08-31, when the cause
                   turned out to be `match_reason` strings written from memory.
      thin         measured class disagrees with declared but n is under the floor. `propose()`
                   already reports these as blocked; they are repeated here so one list answers
                   "what is the learner unsure about?"

    This is a report, never a change. Nothing here touches weights.json.
    """
    min_n = w["training"]["min_n_to_move_a_rule"]
    out = []
    for name, m in rates.items():
        if m["n_fired"] == 0:
            out.append({"rule": name, "gate": m["gate"], "why": "unmeasured",
                        "note": f"declared {m['declared']}, fired 0 times — check `match_reason` "
                                f"against the Reason strings actually in the log before assuming "
                                f"the rule is simply unused"})
        elif m["measured_class"] == "borderline":
            out.append({"rule": name, "gate": m["gate"], "why": "borderline",
                        "note": f"declared {m['declared']}, measured {m['override_rate']:.0%} on "
                                f"n={m['n_fired']} — between the {VETO_MAX:.0%} veto ceiling and "
                                f"the {REVIEW_MIN:.0%} review floor, so no class is supported by "
                                f"the number. Needs a human, not a proposal."})
        elif (m["measured_class"] and m["measured_class"] != m["declared"]
              and m["n_fired"] < min_n):
            note = (f"declared {m['declared']}, measures {m['measured_class']} at "
                    f"{m['override_rate']:.0%} but only n={m['n_fired']} (floor {min_n})")
            if m["n_acted"] == 0:
                note += ("; and Carl has acted on NONE of them, so the rate means he has never "
                         "looked, not that he agreed")
            elif m["n_acted"] < 3:
                note += f"; only {m['n_acted']} of them has he acted on at all"
            out.append({"rule": name, "gate": m["gate"], "why": "thin", "note": note})
    return out


def propose(w, rates, sep):
    """Build the proposal. Every change carries its evidence and clears the n floor.

    A rule that measures `borderline`, or fires zero times, produces nothing here by design —
    see `watchlist()`, which exists so that "nothing to propose" stops reading as "nothing to
    look at".
    """
    min_n = w["training"]["min_n_to_move_a_rule"]
    changes, blocked = [], []

    for name, m in rates.items():
        if m["measured_class"] in (None, "borderline") or m["measured_class"] == m["declared"]:
            continue
        ev = (f"fired {m['n_fired']}, applied anyway {m['n_override']} "
              f"({m['override_rate']:.0%})")
        if m["n_pre_dated"]:
            # Say what was dropped and what the uncorrected number would have read, so a
            # proposal can never again rest on a rate nobody could see was contaminated.
            ev += (f"; {m['n_pre_dated']} further application(s) pre-date the evaluation "
                   f"and are not overrides (uncorrected: {m['raw_override_rate']:.0%})")
        item = {"kind": "rule_class", "rule": name, "gate": m["gate"],
                "from": m["declared"], "to": m["measured_class"],
                "evidence": ev, "n": m["n_fired"]}
        (changes if m["n_fired"] >= min_n else blocked).append(item)

    # A component is only "inverted" if it points the wrong way by a margin worth acting
    # on. Without this floor, a -0.03 delta on 40 rows reads as a finding; it is noise.
    for p, c in sep["components"].items():
        if c["delta"] > -MIN_COMPONENT_DELTA:
            continue
        # The binding n is the SMALLER group, not the sum. 31 applied against 3 passed
        # is a 3-row finding wearing a 34-row coat.
        n = min(c["n_applied"], c["n_passed"])
        item = {"kind": "component_inverted", "component": p,
                "evidence": f"applied mean {c['applied_mean']} < passed mean {c['passed_mean']} "
                            f"(delta {c['delta']}; n={c['n_applied']} applied vs "
                            f"{c['n_passed']} passed)",
                "n": n,
                "suggestion": "review the component's direction before reweighting"}
        (changes if n >= min_n else blocked).append(item)

    return changes, blocked


def backtest(w, rows, rates, changes):
    """What each proposed reclassification would have done over the training window."""
    results = []
    for ch in changes:
        if ch["kind"] != "rule_class":
            continue
        m = rates[ch["rule"]]
        # Counts here are overrides, not raw applies: a pre-dated application would not
        # have been "freed" by a reclassification — it happened before the gate existed.
        if ch["to"] == "review":
            results.append({"rule": ch["rule"],
                            "frees": m["n_fired"], "of_which_applied": m["n_override"],
                            "reads": f"{m['n_override']} rows Carl wanted stop being auto-killed; "
                                     f"{m['n_fired'] - m['n_override']} more rows land in the Review list"})
        else:
            results.append({"rule": ch["rule"],
                            "kills": m["n_fired"], "of_which_applied": m["n_override"],
                            "reads": f"{m['n_fired']} rows become auto-Pass; "
                                     f"{m['n_override']} of them are rows Carl actually applied to "
                                     f"after seeing the evaluation"})
    return results


def write_proposal(w, rates, sep, changes, blocked, bt, watch, stale, dropped, n_rows, n_train):
    prop = json.loads(json.dumps(w))
    prop["version"] = f"{TODAY}.proposed"
    prop["supersedes"] = w["version"]
    for ch in changes:
        if ch["kind"] == "rule_class":
            prop["rules"][ch["rule"]]["class"] = ch["to"]
    prop["provenance"] = {"generated": TODAY, "training_rows": n_train, "rows_in_log": n_rows,
                          "measured_override_rates": {k: v["override_rate"] for k, v in rates.items()},
                          "uncorrected_override_rates": {k: v["raw_override_rate"] for k, v in rates.items()},
                          "n_applications_pre_dating_evaluation": {k: v["n_pre_dated"] for k, v in rates.items()},
                          "override_rate_note": ("measured_override_rates exclude applications dated before "
                                                 "Date_Evaluated (not overrides — the gate had not fired yet). "
                                                 "uncorrected_* is what this script reported before 2026-08-31."),
                          "watchlist": [{k: x[k] for k in ("rule", "gate", "why")} for x in watch],
                          "verdict_basis": "current_rules",
                          "n_stored_verdicts_superseded": len(stale),
                          "excluded": dropped}
    with open(PROPOSED, "w") as f:
        json.dump(prop, f, indent=2)

    entry = [f"\n## {TODAY} — proposal (not applied)\n",
             f"Training set: {n_train} rows of {n_rows}. "
             f"Excluded: {dropped['pre_window_pursue']} pre-window Pursue, "
             f"{dropped['posting_status']} posting-status Pass, "
             f"{dropped['blank_action']} blank-action.\n",
             "\n### Measured override rates\n",
             "Applications dated before the row was evaluated are excluded — the gate had not "
             "fired yet, so they are not overrides. `uncorrected` is what this table reported "
             "before 2026-08-31; a wide gap means the backfill is doing the talking.\n",
             "`acted` is how many of the fired rows Carl has decided on at all. A 0% override "
             "rate over rows he never touched is an absence of evidence, not agreement.\n",
             "| rule | gate | declared | measured | fired | acted | override | pre-dated | rate | uncorrected |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for k, m in sorted(rates.items(), key=lambda kv: -(kv[1]["override_rate"] or 0)):
        rate = "—" if m["override_rate"] is None else f"{m['override_rate']:.0%}"
        raw  = "—" if m["raw_override_rate"] is None else f"{m['raw_override_rate']:.0%}"
        entry.append(f"| {k} | {m['gate']} | {m['declared']} | {m['measured_class'] or '—'} "
                     f"| {m['n_fired']} | {m['n_acted']} | {m['n_override']} | {m['n_pre_dated']} "
                     f"| {rate} | {raw} |")

    pre_note = ""
    if sep["n_pre_dated_applied"] or sep["n_pre_dated_passed"]:
        pre_note = (f"; {sep['n_pre_dated_applied']} applied and {sep['n_pre_dated_passed']} passed "
                    f"dropped as decided before the row was evaluated")
    entry.append(f"\n### Component separation (Pursue: {sep['n_pursue_applied']} applied "
                 f"vs {sep['n_pursue_passed']} passed{pre_note})\n")
    for b in sep["boundaries"]:
        entry.append(f"> ⚠️ **This comparison spans the {b['date']} scale change** "
                     f"({b['n_before']} rows before, {b['n_after']} on or after) — {b['what']}. "
                     f"Affected columns: {', '.join(b['fields'])}. Those means pool two scales.\n")
    entry.append("| component | applied mean | passed mean | delta |")
    entry.append("|---|---|---|---|")
    for p, c in sorted(sep["components"].items(), key=lambda kv: -kv[1]["delta"]):
        entry.append(f"| {p} | {c['applied_mean']} | {c['passed_mean']} | {c['delta']:+} |")

    entry.append("\n### Proposed changes\n")
    entry += [f"- **{c.get('rule') or c.get('component')}** ({c['kind']})"
              + (f": {c['from']} -> {c['to']}" if c.get('to') else "")
              + f" — {c['evidence']}" for c in changes] or \
             ["- none; every rule sits in its declared class and no component is meaningfully inverted."]
    if bt:
        entry.append("\n### Backtest\n")
        entry += [f"- **{b['rule']}**: {b['reads']}" for b in bt]
    if blocked:
        entry.append(f"\n### Blocked — below the n floor "
                     f"({w['training']['min_n_to_move_a_rule']} observations)\n")
        entry += [f"- {b.get('rule') or b.get('component')}: {b['evidence']} (n={b['n']})" for b in blocked]
    if stale:
        entry.append(f"\n### Stored `Verdict` vs current rules — {len(stale)} row(s)\n")
        entry.append("Measured under **current rules** (Carl, 2026-08-31). These rows are stored "
                     "as `Pass` because a veto fired when they were evaluated; under today's "
                     "classes no veto fires and a compensable gate does, so they count as "
                     "`Review` in every measurement here. **The stored column is not rewritten** "
                     "— each row was correct when written.\n")
        entry.append("| Job_ID | evaluated | company | reason |")
        entry.append("|---|---|---|---|")
        entry += [f"| {x['Job_ID']} | {x['date']} | {x['company']} | {x['reason']} |" for x in stale]
    if watch:
        entry.append("\n### Watchlist — measured, but the machinery cannot propose for it\n")
        entry += [f"- **{x['rule']}** ({x['gate']}, {x['why']}) — {x['note']}" for x in watch]
    entry.append("\n**Status:** proposed. Review `rubric/weights.proposed.json`, then "
                 "`python3 scripts/rubric-learn.py --promote` to accept.\n")

    header = ("# Rubric learning log\n\nEvery adjustment to `weights.json`, with the evidence "
              "behind it. Newest last. A proposal is only a proposal until it is promoted.\n")
    prior = open(LOG).read() if os.path.exists(LOG) else header
    with open(LOG, "w") as f:
        f.write(prior + "\n".join(entry) + "\n")
    return prop


def self_test():
    """Assertions for the ordering guard. Written before trusting the re-measurement.

    The 2026-08-28 incident was invisible to code review — the missing check reads as a
    perfectly ordinary comprehension. These cases fail loudly if it is ever removed.
    """
    fails = []
    def ck(label, got, want):
        if got != want:
            fails.append(f"{label}: got {got!r}, want {want!r}")

    A = applied_before_evaluation
    ck("applied two months before evaluation -> not an override",
       A({"Date_Evaluated": "2026-08-12", "Carls_Action_Date": "2026-06-14"}), True)
    ck("applied the day before evaluation -> not an override",
       A({"Date_Evaluated": "2026-08-12", "Carls_Action_Date": "2026-08-11"}), True)
    ck("applied same day as evaluation -> IS an override",
       A({"Date_Evaluated": "2026-08-12", "Carls_Action_Date": "2026-08-12"}), False)
    ck("applied after evaluation -> IS an override",
       A({"Date_Evaluated": "2026-08-12", "Carls_Action_Date": "2026-08-26"}), False)
    ck("timestamped action date is truncated to the day",
       A({"Date_Evaluated": "2026-08-12", "Carls_Action_Date": "2026-08-11 16:30:00"}), True)
    ck("missing action date -> cannot conclude, counts as an override",
       A({"Date_Evaluated": "2026-08-12", "Carls_Action_Date": ""}), False)
    ck("missing evaluation date -> cannot conclude, counts as an override",
       A({"Date_Evaluated": "", "Carls_Action_Date": "2026-06-14"}), False)

    # The incident itself, in miniature: a gate that fired 20 times with 9 applications,
    # 8 of them made before the row existed. Uncorrected this reads 45% (review class);
    # corrected it reads 5% (veto class). The proposal must not fire.
    w = {"consulting_firms": ["Company-09"],
         "rules": {"contract": {"gate": "G1", "class": "veto", "match_reason": r"\bcontract\b"}},
         "training": {"min_n_to_move_a_rule": 15}}
    rows = []
    for i in range(8):
        rows.append({"Job_ID": f"pre{i}", "Company": "Acme", "Reason": "contract role",
                     "Carls_Action": "Applied", "Date_Evaluated": "2026-08-12",
                     "Carls_Action_Date": "2026-06-01"})
    rows.append({"Job_ID": "real", "Company": "Acme", "Reason": "contract role",
                 "Carls_Action": "Applied", "Date_Evaluated": "2026-08-12",
                 "Carls_Action_Date": "2026-08-20"})
    for i in range(11):
        rows.append({"Job_ID": f"kill{i}", "Company": "Acme", "Reason": "contract role",
                     "Carls_Action": "", "Date_Evaluated": "2026-08-12", "Carls_Action_Date": ""})
    m = override_rates(w, rows)["contract"]
    ck("n_fired", m["n_fired"], 20)
    ck("n_applied (raw)", m["n_applied"], 9)
    ck("n_pre_dated", m["n_pre_dated"], 8)
    ck("n_override", m["n_override"], 1)
    ck("corrected rate", round(m["override_rate"], 4), 0.05)
    ck("uncorrected rate", round(m["raw_override_rate"], 4), 0.45)
    ck("corrected class is veto", m["measured_class"], "veto")
    ck("the contaminated reading would have been review",
       "review" if m["raw_override_rate"] >= REVIEW_MIN else "veto", "review")
    changes, blocked = propose(w, m and {"contract": m}, {"components": {}})
    ck("no reclassification proposed on the corrected rate", changes, [])
    ck("nothing blocked either", blocked, [])

    # component_separation drops rows decided before the score existed, from BOTH groups.
    # Rigged so the contamination is visible: the pre-dated applies carry Pts_Comp 0, which
    # would drag the applied mean below the passed mean and read as an inverted component.
    def row(action, pts, ev, ad):
        return {"Verdict": "Pursue", "Carls_Action": action, "Pts_Comp": pts,
                "Date_Evaluated": ev, "Carls_Action_Date": ad}
    rows3 = ([row("Applied", 20, "2026-08-12", "2026-08-20") for _ in range(3)]
             + [row("Applied", 0, "2026-08-12", "2026-06-01") for _ in range(4)]
             + [row("Pass", 10, "2026-08-12", "2026-08-20") for _ in range(2)]
             + [row("Pass", 30, "2026-08-12", "2026-05-01")])
    sep = component_separation(rows3)
    ck("pre-dated applies dropped", sep["n_pre_dated_applied"], 4)
    ck("pre-dated passes dropped too", sep["n_pre_dated_passed"], 1)
    ck("applied group is the 3 real ones", sep["n_pursue_applied"], 3)
    ck("passed group is the 2 real ones", sep["n_pursue_passed"], 2)
    ck("applied mean uncontaminated", sep["components"]["Pts_Comp"]["applied_mean"], 20.0)
    ck("passed mean uncontaminated", sep["components"]["Pts_Comp"]["passed_mean"], 10.0)
    ck("component points the right way once corrected",
       sep["components"]["Pts_Comp"]["delta"] > 0, True)
    # Same rows without the guard would have read: applied 8.57 vs passed 16.67, delta -8.10 —
    # an "inverted component" that is nothing but the backfill.

    # Current-rules derivation (Carl, 2026-08-31). The stored Verdict is not consulted.
    wc = {"consulting_firms": ["Company-09"], "training": {"min_n_to_move_a_rule": 15},
          "rules": {"contract":  {"gate": "G1",  "class": "review", "match_reason": r"\bcontract\b",
                                  "outranked_by_employer_list": "consulting_firms"},
                    "low_comp":  {"gate": "G2",  "class": "veto",   "match_reason": r"\blow comp\b"},
                    "consulting_named": {"gate": "G3a", "class": "veto", "match_reason": r"\bconsulting\b",
                                         "requires_employer_list": "consulting_firms"}}}
    def vrow(reason, verdict="Pass", company="Acme"):
        return {"Job_ID": "v", "Company": company, "Reason": reason, "Verdict": verdict,
                "Date_Evaluated": "2026-08-14", "Carls_Action": "", "Carls_Action_Date": ""}
    ck("a contract row is review-class today, whatever it was stored as",
       current_verdict_class(wc, vrow("contract")), "review")
    ck("a low-comp row is still veto", current_verdict_class(wc, vrow("low comp")), "veto")
    ck("veto outranks review on a row carrying both",
       current_verdict_class(wc, vrow("contract; low comp")), "veto")
    ck("a row no rule fires on has no class",
       current_verdict_class(wc, vrow("out of lane")), None)
    ck("the stored Verdict is not consulted — same row, different label, same answer",
       current_verdict_class(wc, vrow("contract", verdict="Skip")), "review")
    ck("a stored Pass that is now review-class is reported as superseded",
       [x["Job_ID"] for x in stale_verdicts(wc, [vrow("contract")])], ["v"])
    ck("a stored Pass that is still veto-class is not",
       stale_verdicts(wc, [vrow("low comp")]), [])
    ck("a non-Pass row is never reported, even if review-class",
       stale_verdicts(wc, [vrow("contract", verdict="Skip")]), [])
    ck("G3a still outranks G1 in the derivation too",
       current_verdict_class(wc, vrow("contract; consulting", company="Company-09")), "veto")

    # Scale boundaries: a population straddling one must say so (2026-08-31 sweep).
    def brow(date):
        return {"Verdict": "Pursue", "Carls_Action": "Applied", "Pts_Comp": 20,
                "Date_Evaluated": date, "Carls_Action_Date": "2026-08-30"}
    ck("a population entirely after both boundaries is clean",
       boundary_warnings([brow("2026-08-27"), brow("2026-08-28")], PTS), [])
    ck("a population entirely before a boundary is clean",
       boundary_warnings([brow("2026-08-11"), brow("2026-08-20")], ["Pts_Comp"]), [])
    ck("straddling 2026-08-26 with Pts_Comp is flagged",
       [b["date"] for b in boundary_warnings([brow("2026-08-20"), brow("2026-08-27")], ["Pts_Comp"])],
       ["2026-08-26"])
    ck("straddling it while comparing an unaffected column is not",
       boundary_warnings([brow("2026-08-20"), brow("2026-08-27")], ["Pts_Location"]), [])
    ck("straddling both boundaries reports both",
       [b["date"] for b in boundary_warnings([brow("2026-08-01"), brow("2026-08-27")], PTS)],
       ["2026-08-10", "2026-08-26"])
    ck("a row ON the boundary counts as after",
       boundary_warnings([brow("2026-08-26"), brow("2026-08-27")], ["Pts_Comp"]), [])

    # A pre-dated row is DROPPED, never counted for the other side.
    only_pre = component_separation([row("Applied", 5, "2026-08-12", "2026-06-01")])
    ck("a lone pre-dated applied leaves both groups empty", 
       (only_pre["n_pursue_applied"], only_pre["n_pursue_passed"]), (0, 0))
    ck("and produces no component rows", only_pre["components"], {})

    # G3a still outranks G1 — but only because the rule now DECLARES it. The hardcoded
    # `if name == "contract"` was removed 2026-08-31; this assertion is what caught the
    # regression when it was, so keep both halves.
    rows2 = [{"Job_ID": "x", "Company": "Company-09", "Reason": "contract role",
              "Carls_Action": "Applied", "Date_Evaluated": "2026-08-12",
              "Carls_Action_Date": "2026-08-20"}]
    w2 = json.loads(json.dumps(w))
    w2["rules"]["contract"]["outranked_by_employer_list"] = "consulting_firms"
    ck("consulting-firm row excluded when the rule declares it",
       override_rates(w2, rows2)["contract"]["n_fired"], 0)
    ck("and NOT excluded when it does not — the qualifier must be declared, not assumed",
       override_rates(w, rows2)["contract"]["n_fired"], 1)

    # --- the new qualifiers, on the real shapes that motivated them (2026-08-31) ----------
    wq = {"consulting_firms": ["Company-09"], "training": {"min_n_to_move_a_rule": 15},
          "rules": {"comp_floor": {"gate": "G2b", "class": "review",
                                   "match_reason": r"sub-?target comp|comp at floor|\bcomp gap\b",
                                   "excludes_reason_match": r"\blow comp\b|comp below floor|comp too low",
                                   "requires_field_match": {"field": "Comp_Flag",
                                                            "pattern": r"sub-?target|below floor|at floor"}}}}
    def crow(reason, flag):
        return {"Job_ID": reason[:8], "Company": "Acme", "Reason": reason, "Comp_Flag": flag,
                "Carls_Action": "", "Date_Evaluated": "2026-08-12", "Carls_Action_Date": ""}
    qrows = [
        crow("SAP stack, sub-target comp", "Sub-target"),                 # in band
        crow("comp at floor, dbt gap", "Sub-target"),                     # in band
        crow("Comp gap; Snowflake", "Sub-target - tops out at $136,442"), # in band
        crow("Python/R required, sub-target comp", "None"),               # Reason vs field disagree
        crow("data engineering, comp below floor", "BELOW FLOOR"),        # G2's row, not G2b's
        crow("sub-target comp; but also low comp", "Sub-target"),         # veto reason outranks
    ]
    q = override_rates(wq, qrows)["comp_floor"]
    ck("G2b fires on the three real band rows only", q["n_fired"], 3)
    # each qualifier must be load-bearing on its own — assert by removal, not by inspection
    # The era split: the same Comp_Flag string means a different band either side of 2026-08-26.
    we = {"consulting_firms": [], "training": {"min_n_to_move_a_rule": 15},
          "rules": {"comp_floor": {"gate": "G2b", "class": "review",
                                   "match_reason": r"comp",
                                   "requires_field_match": {"field": "Comp_Flag",
                                                            "boundary_date": "2026-08-26",
                                                            "pattern_before": r"sub-?target",
                                                            "pattern_after": r"below floor"}}}}
    def erow(date, flag):
        return {"Job_ID": date + flag[:4], "Company": "Acme", "Reason": "comp", "Comp_Flag": flag,
                "Carls_Action": "", "Date_Evaluated": date, "Carls_Action_Date": ""}
    ck("pre-boundary row: 'Sub-target' IS the VETO_LINE-150K band",
       override_rates(we, [erow("2026-08-12", "Sub-target")])["comp_floor"]["n_fired"], 1)
    ck("pre-boundary row: 'Below floor' is NOT (it meant under VETO_LINE then)",
       override_rates(we, [erow("2026-08-12", "Below floor")])["comp_floor"]["n_fired"], 0)
    ck("post-boundary row: 'Below floor' IS the band",
       override_rates(we, [erow("2026-08-27", "Below floor")])["comp_floor"]["n_fired"], 1)
    ck("post-boundary row: 'Sub-target' is NOT (it means FLOOR-175K now)",
       override_rates(we, [erow("2026-08-27", "Sub-target")])["comp_floor"]["n_fired"], 0)
    ck("the boundary date itself reads under the NEW scheme",
       override_rates(we, [erow("2026-08-26", "Below floor")])["comp_floor"]["n_fired"], 1)
    ck("an undated row reads under the OLD scheme",
       override_rates(we, [erow("", "Sub-target")])["comp_floor"]["n_fired"], 1)

    no_field = json.loads(json.dumps(wq)); del no_field["rules"]["comp_floor"]["requires_field_match"]
    ck("without requires_field_match the Comp_Flag=None row creeps in",
       override_rates(no_field, qrows)["comp_floor"]["n_fired"], 4)
    no_excl = json.loads(json.dumps(wq)); del no_excl["rules"]["comp_floor"]["excludes_reason_match"]
    ck("without excludes_reason_match the low-comp row creeps in",
       override_rates(no_excl, qrows)["comp_floor"]["n_fired"], 4)

    # G3b must catch the log's real wordings and must NOT swallow a lane call.
    wd = {"consulting_firms": ["Company-09"], "training": {"min_n_to_move_a_rule": 15},
          "rules": {"delivery_role": {"gate": "G3b", "class": "review",
                                      "match_reason": r"consulting[\s-]*(firm[\s-]*)?delivery",
                                      "outranked_by_employer_list": "consulting_firms"}}}
    drows = [crow("consulting-firm delivery pattern", ""),
             crow("consulting delivery, people-mgmt scope", ""),
             crow("consulting delivery pattern", ""),
             crow("consulting delivery, dbt/Snowflake stack", ""),
             crow("consulting delivery role", ""),          # the rubric's canonical token
             crow("IT delivery management, not BI", "")]    # a lane call, NOT this gate
    ck("G3b matches every real wording and stops at the lane call",
       override_rates(wd, drows)["delivery_role"]["n_fired"], 5)

    # --- watchlist: the three ways a rule goes silent ------------------------------------
    ww = {"consulting_firms": [], "training": {"min_n_to_move_a_rule": 15},
          "rules": {"bord": {"gate": "Gb", "class": "review", "match_reason": "bord"},
                    "quiet": {"gate": "Gq", "class": "review", "match_reason": "nothing-matches-this"},
                    "thin": {"gate": "Gt", "class": "veto", "match_reason": "thin"}}}
    wrows = ([crow("bord", "")] * 8 + [dict(crow("bord", ""), Carls_Action="Applied",
                                            Carls_Action_Date="2026-08-20")]
             + [crow("thin", "")] * 8 + [dict(crow("thin", ""), Carls_Action="Applied",
                                              Carls_Action_Date="2026-08-20")] * 4)
    wr = override_rates(ww, wrows)
    ck("borderline rule measures borderline", wr["bord"]["measured_class"], "borderline")
    ck("borderline produces no proposal", propose(ww, wr, {"components": {}})[0], [])
    wl = {x["rule"]: x["why"] for x in watchlist(ww, wr)}
    ck("borderline is on the watchlist", wl.get("bord"), "borderline")
    ck("a rule that never fires is on the watchlist", wl.get("quiet"), "unmeasured")
    ck("a class disagreement under the n floor is on the watchlist", wl.get("thin"), "thin")
    ck("nothing else is", len(wl), 3)
    ck("a thin rule nobody has acted on says so",
       "never looked" in [x for x in watchlist(ww, wr) if x["rule"] == "thin"][0]["note"], False)
    # G2b's real shape: declared review, 8 rows fired, Carl has acted on none of them.
    ww2 = {"consulting_firms": [], "training": {"min_n_to_move_a_rule": 15},
           "rules": {"unlooked": {"gate": "Gu", "class": "review", "match_reason": "unlooked"}}}
    wr2 = override_rates(ww2, [crow("unlooked", "")] * 8)
    ck("declared review, measures veto", wr2["unlooked"]["measured_class"], "veto")
    ck("a rule fired 8 times with zero actions is flagged as unlooked-at",
       "never looked" in watchlist(ww2, wr2)[0]["note"], True)
    ck("n_acted counts decided rows, not applications", wr["thin"]["n_acted"], 4)

    for f in fails:
        print(f"  FAIL  {f}", file=sys.stderr)
    print(f"\n  self-test: {'FAILED' if fails else 'passed'} "
          f"({len(fails)} failure(s))\n", file=sys.stderr)
    return 1 if fails else 0


def promote():
    if not os.path.exists(PROPOSED):
        sys.exit("No standing proposal to promote.")
    stamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    shutil.copy2(WEIGHTS, os.path.join(RUBRIC, f"weights_{stamp}.json"))
    prop = json.load(open(PROPOSED))
    prop["version"] = f"{TODAY}.1"
    prop["effective_from"] = TODAY
    with open(WEIGHTS, "w") as f:
        json.dump(prop, f, indent=2)
    os.remove(PROPOSED)
    with open(LOG, "a") as f:
        f.write(f"\n> Promoted {TODAY}: proposal accepted, previous weights kept as "
                f"`rubric/weights_{stamp}.json`.\n")
    print(f"  Promoted. Previous weights saved as rubric/weights_{stamp}.json", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-pull", action="store_true", help="reuse the existing Fabric pull")
    ap.add_argument("--promote", action="store_true", help="accept the standing proposal")
    ap.add_argument("--self-test", action="store_true",
                    help="run the ordering-guard assertions and exit")
    args = ap.parse_args()

    if args.self_test:
        return sys.exit(self_test())
    if args.promote:
        return promote()

    w = load_weights()
    if not args.no_pull or not os.path.exists(PULL):
        pull()

    all_rows, rates_pop, comp_pop, dropped = training_set(w)
    rates = override_rates(w, rates_pop)
    sep = component_separation(comp_pop)
    changes, blocked = propose(w, rates, sep)
    watch = watchlist(w, rates)
    stale = stale_verdicts(w, rates_pop)
    bt = backtest(w, comp_pop, rates, changes)
    write_proposal(w, rates, sep, changes, blocked, bt, watch, stale, dropped,
                   len(all_rows), len(comp_pop))

    e = sys.stderr
    print(f"\n  override-rate population : {len(rates_pop)} rows "
          f"(all rows minus {dropped['posting_status']} posting-status)", file=e)
    print(f"  component population     : {len(comp_pop)} rows "
          f"(also minus {dropped['pre_window_pursue']} pre-window Pursue, "
          f"{dropped['blank_action']} blank-action)\n", file=e)
    print(f"  {'rule':<20}{'gate':<6}{'declared':<10}{'measured':<12}{'fired':>6}{'acted':>6}"
          f"{'ovrd':>6}{'pre':>5}{'rate':>7}{'uncorr':>8}", file=e)
    for k, m in sorted(rates.items(), key=lambda kv: -(kv[1]["override_rate"] or 0)):
        rate = "—" if m["override_rate"] is None else f"{m['override_rate']:.0%}"
        raw  = "—" if m["raw_override_rate"] is None else f"{m['raw_override_rate']:.0%}"
        flag = "" if m["measured_class"] in (m["declared"], None, "borderline") else "  <- RECLASSIFY"
        print(f"  {k:<20}{m['gate']:<6}{m['declared']:<10}{str(m['measured_class']):<12}"
              f"{m['n_fired']:>6}{m['n_acted']:>6}{m['n_override']:>6}{m['n_pre_dated']:>5}"
              f"{rate:>7}{raw:>8}{flag}", file=e)
    pre_total = sum(m["n_pre_dated"] for m in rates.values())
    if pre_total:
        print(f"\n  {pre_total} application(s) across all rules pre-date their evaluation and are "
              f"NOT counted as overrides.\n  (2026-08-28 incident: uncorrected, these read as the "
              f"filter being too tight.)", file=e)

    for b in sep["boundaries"]:
        print(f"\n  !! the component comparison SPANS the {b['date']} scale change "
              f"({b['n_before']} rows before, {b['n_after']} on or after).\n"
              f"     {b['what']}.\n"
              f"     Affected here: {', '.join(b['fields'])}. Those means pool two scales.", file=e)
    if sep["n_pre_dated_applied"] or sep["n_pre_dated_passed"]:
        print(f"  component separation drops {sep['n_pre_dated_applied']} applied / "
              f"{sep['n_pre_dated_passed']} passed decided before evaluation "
              f"({sep['n_pursue_applied']} vs {sep['n_pursue_passed']} remain).", file=e)

    print(f"\n  proposed changes: {len(changes)}   blocked below n floor: {len(blocked)}", file=e)
    for c in changes:
        print(f"    - {c.get('rule') or c.get('component')}: {c['evidence']}", file=e)
    for b in blocked:
        print(f"    (blocked) {b.get('rule') or b.get('component')}: n={b['n']}", file=e)
    if stale:
        print(f"\n  {len(stale)} row(s) stored as `Pass` count as `Review` under current rules "
              f"(Carl, 2026-08-31 — measure under current rules).\n"
              f"    Stored column not rewritten; re-derived at measurement time.", file=e)
    if watch:
        print(f"\n  watchlist: {len(watch)} rule(s) the proposal machinery cannot speak for", file=e)
        for x in watch:
            print(f"    [{x['why']:<10}] {x['rule']} ({x['gate']}) — {x['note']}", file=e)
    print(f"\n  -> rubric/weights.proposed.json\n  -> rubric/learning_log.md\n"
          f"  Nothing was applied. Review, then --promote.\n", file=e)


if __name__ == "__main__":
    main()
