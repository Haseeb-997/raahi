"""
matcher.py — Diversity-aware recommendation selector for Raahi.

Public API
----------
get_recommendations(fsc_percentage, annual_budget, preferred_cities,
                    gender, personality_scores)
    → list[dict]   Exactly 3 ranked recommendations with why/risk labels.

Pipeline
--------
  score_universities()  →  _select_top_3()  →  _annotate()  →  caller
"""

from __future__ import annotations

from collections import defaultdict

from logic.scorer import score_universities

# ── Program → broad family mapping ────────────────────────────────────────────
# Used to enforce "variety" — e.g., don't return 3 tech programs if the
# student also has strong Engineering scores.
PROGRAM_FAMILY: dict[str, str] = {
    "BS CS":                   "tech",
    "BS SE":                   "tech",
    "BS AI":                   "tech",
    "BS Data Science":         "tech",
    "BS EE":                   "engineering",
    "BS ME":                   "engineering",
    "BS Civil":                "engineering",
    "BBA":                     "business",
    "BS Accounting & Finance": "business",
    "MBBS":                    "medical",
    "BS Pharmacy":             "medical",
    "BS Psychology":           "social",
}


# ══════════════════════════════════════════════════════════════════════════════
# Selection logic
# ══════════════════════════════════════════════════════════════════════════════

def _select_top_3(ranked: list[dict]) -> list[dict]:
    """
    Pick the 3 best recommendations from a pre-scored, pre-sorted list,
    enforcing all diversity and quality constraints.

    Rules applied in order
    ----------------------
    1. University cap     — at most 2 results from the same university.
    2. Family diversity   — at most 2 results from the same program family
                            (tech / engineering / business / medical / social).
    3. Strong Match lock  — if ANY Strong Match exists in ranked, at least
                            one of the 3 must be a Strong Match.
    4. Budget safety      — at least one result must be fully within budget
                            (budget_label ≠ "Slight Risk").

    If the strict pass yields < 3 results, the family constraint is relaxed
    for the remaining slots. Guarantees 3 and 4 trigger a swap of the
    lowest-scoring slot when they cannot be satisfied during greedy selection.
    """
    if not ranked:
        return []
    if len(ranked) <= 3:
        return ranked[:]

    selected: list[dict] = []
    uni_counts:    defaultdict[str, int] = defaultdict(int)
    family_counts: defaultdict[str, int] = defaultdict(int)

    def _family(r: dict) -> str:
        return PROGRAM_FAMILY.get(r["program_name"], "other")

    def _pick(r: dict) -> None:
        selected.append(r)
        uni_counts[r["university_short"]] += 1
        family_counts[_family(r)] += 1

    # ── Pass 1: Greedy with full constraints (university + family diversity) ──
    for r in ranked:
        if len(selected) == 3:
            break
        if uni_counts[r["university_short"]] >= 2:
            continue    # university cap
        if family_counts[_family(r)] >= 2:
            continue    # family diversity cap
        _pick(r)

    # ── Pass 2: Relax family cap if still fewer than 3 ───────────────────────
    if len(selected) < 3:
        for r in ranked:
            if len(selected) == 3:
                break
            if r in selected:
                continue
            if uni_counts[r["university_short"]] < 2:
                _pick(r)

    # ── Guarantee 3: At least 1 Strong Match ─────────────────────────────────
    # Only enforced when at least one Strong Match exists in the full ranked list.
    pool_has_strong    = any(r["admission_label"] == "Strong Match" for r in ranked)
    picks_have_strong  = any(r["admission_label"] == "Strong Match" for r in selected)

    if pool_has_strong and not picks_have_strong:
        # Find the highest-scoring Strong Match that:
        #   (a) is not already selected
        #   (b) wouldn't create a third entry from the same university
        for strong_r in ranked:
            if strong_r["admission_label"] != "Strong Match":
                continue
            if strong_r in selected:
                continue
            # Temporarily reduce count for the item we'll swap out
            swap_out = selected[-1]   # weakest slot (list is score-sorted)
            if uni_counts[strong_r["university_short"]] < 2:
                selected[-1] = strong_r
                break
            # If the Strong Match is from the same uni as swap_out,
            # the count would still be ≤ 2 after swapping — allow it.
            if strong_r["university_short"] == swap_out["university_short"]:
                selected[-1] = strong_r
                break

    # ── Guarantee 4: At least 1 result fully within budget ───────────────────
    picks_have_budget = any(not r.get("budget_over", False) for r in selected)

    if not picks_have_budget:
        for safe_r in ranked:
            if safe_r.get("budget_over", False):
                continue
            if safe_r in selected:
                continue
            if uni_counts[safe_r["university_short"]] < 2:
                selected[-1] = safe_r
                break

    return selected[:3]


# ══════════════════════════════════════════════════════════════════════════════
# Annotation: why_list and risk_list
# ══════════════════════════════════════════════════════════════════════════════

def _build_why_risk(r: dict) -> tuple[list[str], list[str]]:
    """
    Generate human-readable explanation and risk strings for one result.

    why_list : 2–4 positive reasons this university/program was recommended.
    risk_list : 0–2 cautions the student should be aware of.
    """
    why:  list[str] = []
    risk: list[str] = []

    # ── Admission ─────────────────────────────────────────────────────────────
    label = r["admission_label"]
    cutoff_gap = round(r["total_score"] - r["admission_score"])  # not used directly, left for future

    if label == "Strong Match":
        why.append("Admission very likely - you're well above the merit cutoff")
    elif label == "Likely":
        why.append("Merit cutoff is within reach based on your FSc")
    elif label == "Reach":
        why.append("Borderline merit — worth applying but prepare a backup")
        risk.append("Competitive merit cutoff — borderline admission chance")

    # ── Budget ────────────────────────────────────────────────────────────────
    bud_label = r["budget_label"]
    fee_fmt   = f"PKR {r['annual_fee_pkr']:,}/yr"

    if bud_label == "Comfortable":
        why.append(f"Well within your budget ({fee_fmt})")
    elif bud_label == "Within Budget":
        why.append(f"Fits your annual budget ({fee_fmt})")
    elif bud_label == "Slight Risk":
        risk.append(f"Slightly above your stated budget ({fee_fmt})")

    # ── Personality fit ───────────────────────────────────────────────────────
    pers = r["personality_score"]   # scaled 0–30
    if pers >= 27:
        why.append("Excellent match with your quiz interests")
    elif pers >= 18:
        why.append("Good alignment with your personality profile")
    elif pers >= 9:
        why.append("Moderate interest alignment")
    # Below 9 — no positive why; let score speak for itself

    # ── City ──────────────────────────────────────────────────────────────────
    if r["city_score"] > 0:
        why.append(f"Located in your preferred city ({r['city']})")
    else:
        risk.append(f"Campus is in {r['city']} — outside your preferred cities")

    # ── Ranking tier ──────────────────────────────────────────────────────────
    tier = r["ranking_tier"]
    if tier == "A":
        why.append("Tier A university — strong graduate employability")
    elif tier == "B":
        why.append("Tier B university — solid regional reputation")

    # ── Sector ───────────────────────────────────────────────────────────────
    if r["sector"] == "Public":
        why.append("Public university — lower fee, government-backed degree")
    elif r["sector"] == "Private" and tier == "A":
        why.append("Top private university — premium network & placements")

    # ── Hostel note ───────────────────────────────────────────────────────────
    if str(r.get("hostel_available", "")).lower() == "no":
        risk.append("No on-campus hostel — off-campus accommodation needed")

    # Cap lists: 4 why-reasons, 2 risk-flags
    return why[:4], risk[:2]


# ══════════════════════════════════════════════════════════════════════════════
# Public entry point
# ══════════════════════════════════════════════════════════════════════════════

def get_recommendations(
    fsc_percentage:    float,
    annual_budget:     int,
    preferred_cities:  list[str],
    gender:            str,
    personality_scores: dict[str, int],
) -> list[dict]:
    """
    Full recommendation pipeline: score → select → annotate.

    Parameters
    ----------
    fsc_percentage     : Student's intermediate percentage (40–100).
    annual_budget      : Max annual fee the student can afford (PKR).
    preferred_cities   : E.g. ['Lahore', 'Islamabad'] or ['Any'].
    gender             : 'Male' | 'Female' | 'Prefer not to say'.
    personality_scores : {'CS': 9, 'SE': 6, ...} from the quiz.

    Returns
    -------
    List of exactly 3 dicts (or fewer if the data has < 3 eligible rows).
    Each dict contains all fields from scorer.py PLUS:
      rank       : 1, 2, or 3
      why_list   : list[str]   2–4 positive reasons
      risk_list  : list[str]   0–2 caution notes
    """
    # Step 1 — Score all (university × program) rows; get top-30 candidates
    # (We pass top_n=30 so the matcher has enough diversity to work with)
    ranked = score_universities(
        fsc_percentage=fsc_percentage,
        annual_budget=annual_budget,
        preferred_cities=preferred_cities,
        gender=gender,
        personality_scores=personality_scores,
        top_n=30,
    )

    if not ranked:
        return []   # No eligible results after hard eliminators

    # Step 2 — Apply diversity and quality rules to pick exactly 3
    top3 = _select_top_3(ranked)

    # Step 3 — Annotate each result with rank, why_list, risk_list
    annotated: list[dict] = []
    for rank_idx, r in enumerate(top3, start=1):
        why, risk = _build_why_risk(r)
        annotated.append({
            **r,
            "rank":      rank_idx,
            "why_list":  why,
            "risk_list": risk,
        })

    return annotated
