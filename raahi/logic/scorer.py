"""
scorer.py — Recommendation scoring engine for Raahi.

Public API
----------
score_universities(fsc_percentage, annual_budget, preferred_cities,
                   gender, personality_scores, top_n=10)
    → list[dict]   Ranked (university × program) results, best first.

Scoring breakdown (max 100 pts):
  Admission    0 – 30 pts   merit cutoff match
  Budget       0 – 25 pts   fee vs annual budget
  Personality  0 – 30 pts   quiz field scores
  City         0 – 15 pts   location preference
"""

from __future__ import annotations

import os
import pandas as pd

# ── Program → personality key mapping ─────────────────────────────────────────
# Maps every program_name in universities.csv to its quiz field key.
# Add new programs here as the dataset grows.
PROGRAM_TO_FIELD: dict[str, str] = {
    "BS CS":                   "CS",
    "BS SE":                   "SE",
    "BS AI":                   "AI",
    "BS Data Science":         "Data",
    "BS EE":                   "Elec",
    "BS ME":                   "Mech",
    "BS Civil":                "Civil",
    "BBA":                     "BBA",
    "BS Accounting & Finance": "Fin",
    "BS Psychology":           "Psych",
    "BS Pharmacy":             "Pharma",
    "MBBS":                    "Med",
}

# ── Score tier constants ───────────────────────────────────────────────────────
# Each tuple is (human-readable label, points).
# Using named constants makes _admission_score / _budget_score readable.

# Admission tiers
_ADM_STRONG = ("Strong Match", 30)   # fsc >= cutoff + 5
_ADM_LIKELY = ("Likely",       20)   # fsc >= cutoff
_ADM_REACH  = ("Reach",        10)   # fsc >= cutoff - 3
_ADM_OUT    = ("No Match",      0)   # fsc < cutoff - 3  → eliminated

# Budget tiers
_BUD_EASY   = ("Comfortable",   25)  # fee <= budget * 0.80
_BUD_FIT    = ("Within Budget", 20)  # fee <= budget
_BUD_RISK   = ("Slight Risk",   10)  # fee <= budget * 1.15  → flagged
_BUD_OUT    = ("Over Budget",    0)  # fee > budget * 1.15   → eliminated

# ── Path to data file ─────────────────────────────────────────────────────────
_DATA_DIR        = os.path.join(os.path.dirname(__file__), "..", "data")
UNIVERSITIES_CSV = os.path.normpath(os.path.join(_DATA_DIR, "universities.csv"))


# ══════════════════════════════════════════════════════════════════════════════
# Data loading
# ══════════════════════════════════════════════════════════════════════════════

def _load_universities() -> pd.DataFrame:
    """
    Read universities.csv, clean types, and drop rows with missing
    critical fields (fee, cutoff, program, city).

    Returns a clean DataFrame ready for scoring.
    """
    if not os.path.exists(UNIVERSITIES_CSV):
        raise FileNotFoundError(
            f"Universities data not found at: {UNIVERSITIES_CSV}\n"
            "Make sure raahi/data/universities.csv exists."
        )

    df = pd.read_csv(UNIVERSITIES_CSV)

    # Strip leading/trailing whitespace from all string columns
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].str.strip()

    # Coerce numeric columns; bad values become NaN (handled below)
    df["annual_fee_pkr"]          = pd.to_numeric(df["annual_fee_pkr"],          errors="coerce")
    df["merit_cutoff_percentage"] = pd.to_numeric(df["merit_cutoff_percentage"], errors="coerce")

    # Drop rows where any critical field is missing or unparseable
    critical = ["annual_fee_pkr", "merit_cutoff_percentage", "program_name", "city"]
    before = len(df)
    df.dropna(subset=critical, inplace=True)
    dropped = before - len(df)
    if dropped:
        print(f"[scorer] Warning: dropped {dropped} row(s) with missing critical fields.")

    df.reset_index(drop=True, inplace=True)
    return df


# ══════════════════════════════════════════════════════════════════════════════
# Component scorers
# ══════════════════════════════════════════════════════════════════════════════

def _admission_score(fsc: float, cutoff: float) -> tuple[str, int]:
    """
    Compare the student's FSc percentage to the program merit cutoff.

    Tiers
    -----
    Strong Match  30 pts   fsc >= cutoff + 5   (well above — very safe)
    Likely        20 pts   fsc >= cutoff        (meets cutoff)
    Reach         10 pts   fsc >= cutoff - 3    (borderline — worth trying)
    No Match       0 pts   fsc < cutoff - 3     → row is eliminated
    """
    if fsc >= cutoff + 5:
        return _ADM_STRONG
    if fsc >= cutoff:
        return _ADM_LIKELY
    if fsc >= cutoff - 3:
        return _ADM_REACH
    return _ADM_OUT


def _budget_score(fee: float, budget: float) -> tuple[str, int]:
    """
    Compare the program's annual fee to the student's budget.

    Tiers
    -----
    Comfortable   25 pts   fee <= budget * 0.80   (leaves breathing room)
    Within Budget 20 pts   fee <= budget           (just affordable)
    Slight Risk   10 pts   fee <= budget * 1.15    (flagged — marginal)
    Over Budget    0 pts   fee > budget * 1.15     → row is eliminated
    """
    if fee <= budget * 0.80:
        return _BUD_EASY
    if fee <= budget:
        return _BUD_FIT
    if fee <= budget * 1.15:
        return _BUD_RISK
    return _BUD_OUT


def _personality_score(
    program_name: str,
    personality_scores: dict[str, int],
    max_raw: float,
) -> tuple[int, int]:
    """
    Map the program to its quiz field key and normalise against the
    student's personal maximum raw score.

    Normalisation: best_field_score → 30 pts, everything else scales
    proportionally. This ensures the student's top-matching field
    always earns the full 30 pts regardless of quiz scoring density.

    Returns
    -------
    (raw_score, scaled_score_out_of_30)
    """
    field_key = PROGRAM_TO_FIELD.get(program_name)

    # Program not in mapping (e.g., future programs) → neutral score
    if not field_key:
        return 0, 0

    raw = personality_scores.get(field_key, 0)

    # Avoid division by zero if all personality scores are 0
    if max_raw == 0:
        return raw, 0

    scaled = round((raw / max_raw) * 30)
    return raw, scaled


def _city_score(uni_city: str, preferred_cities: list[str]) -> int:
    """
    Score location preference.

    15 pts  university city is in preferred_cities, OR student chose 'Any'
     0 pts  city not in preference list
    """
    if "Any" in preferred_cities or uni_city in preferred_cities:
        return 15
    return 0


# ══════════════════════════════════════════════════════════════════════════════
# Main scoring function
# ══════════════════════════════════════════════════════════════════════════════

def score_universities(
    fsc_percentage: float,
    annual_budget: int,
    preferred_cities: list[str],
    gender: str,
    personality_scores: dict[str, int],
    top_n: int = 10,
) -> list[dict]:
    """
    Score every (university × program) row in universities.csv and
    return the top_n matches ranked by total score (descending).

    Hard eliminators
    ----------------
    - admission_score == 0   → student cannot meet the merit cutoff
    - budget_score    == 0   → fee exceeds budget by more than 15 %

    Tie-breaking
    ------------
    Equal total scores are broken by annual_fee_pkr ascending (cheaper first).

    Parameters
    ----------
    fsc_percentage     : Intermediate percentage (40.0 – 100.0).
    annual_budget      : Max annual fee in PKR the student can afford.
    preferred_cities   : E.g. ['Lahore', 'Islamabad'], or ['Any'].
    gender             : 'Male' | 'Female' | 'Prefer not to say'.
                         (Reserved for future hostel/campus filtering.)
    personality_scores : {'CS': 9, 'SE': 6, 'AI': 4, ...} from the quiz.
    top_n              : Number of results to return (default: 10).

    Returns
    -------
    List of result dicts, each containing:
      identity   : university_name, university_short, city, program_name,
                   degree_type, annual_fee_pkr, sector, ranking_tier,
                   hostel_available, gender_policy
      components : admission_label, admission_score,
                   budget_label, budget_score, budget_over (bool),
                   personality_raw, personality_score, city_score
      total      : total_score
    """
    df = _load_universities()

    # The highest raw quiz score a student got in any field.
    # All personality scores are normalised against this value so the
    # student's top field always earns the full 30 pts.
    max_raw_personality = max(personality_scores.values(), default=1) or 1

    results: list[dict] = []

    for _, row in df.iterrows():
        fee     = float(row["annual_fee_pkr"])
        cutoff  = float(row["merit_cutoff_percentage"])
        city    = str(row["city"])
        program = str(row["program_name"])

        # ── 1. Admission score (0–30 pts) ─────────────────────────────────────
        adm_label, adm_pts = _admission_score(fsc_percentage, cutoff)
        if adm_pts == 0:
            continue   # Student cannot qualify → skip this row

        # ── 2. Budget score (0–25 pts) ────────────────────────────────────────
        bud_label, bud_pts = _budget_score(fee, annual_budget)
        if bud_pts == 0:
            continue   # Fee is unaffordable → skip this row

        # ── 3. Personality score (0–30 pts) ───────────────────────────────────
        pers_raw, pers_pts = _personality_score(
            program, personality_scores, max_raw_personality
        )

        # ── 4. City score (0–15 pts) ──────────────────────────────────────────
        city_pts = _city_score(city, preferred_cities)

        # ── Total score ───────────────────────────────────────────────────────
        total = adm_pts + bud_pts + pers_pts + city_pts

        results.append({
            # ── Identity ──────────────────────────────────────────────────────
            "university_name":        str(row["university_name"]),
            "university_short":       str(row["university_short"]),
            "city":                   city,
            "program_name":           program,
            "degree_type":            str(row.get("degree_type", "BS")),
            "annual_fee_pkr":         int(fee),
            "merit_cutoff_percentage": float(cutoff),   # exposed for result card
            "sector":                 str(row.get("sector", "Unknown")),
            "ranking_tier":           str(row.get("ranking_tier", "C")),
            "hostel_available":       str(row.get("hostel_available", "N/A")),
            "gender_policy":          str(row.get("gender_policy", "Co-ed")),
            # ── Component scores ──────────────────────────────────────────────
            "admission_label":   adm_label,
            "admission_score":   adm_pts,
            "budget_label":      bud_label,
            "budget_score":      bud_pts,
            "budget_over":       (bud_label == "Slight Risk"),   # flag for UI warning
            "personality_raw":   pers_raw,
            "personality_score": pers_pts,
            "city_score":        city_pts,
            # ── Total ─────────────────────────────────────────────────────────
            "total_score":       total,
        })

    # Primary sort: total score descending.
    # Secondary (tie-break): fee ascending — cheaper option wins ties.
    results.sort(key=lambda r: (-r["total_score"], r["annual_fee_pkr"]))

    return results[:top_n]
