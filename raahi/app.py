"""
app.py — Raahi: Find Your Realistic University Path
Main Streamlit entry point. Three-page flow:
  Page 1 → Student Profile Form
  Page 2 → Personality Quiz
  Page 3 → Ranked University Recommendations
"""

import json
import os
import time
import streamlit as st

from logic.matcher import get_recommendations
from components.result_card import show_result_card, get_field_key

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Raahi – Find Your University Path",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ══════════════════════════════════════════════════════════════════════════════
# GLOBAL CSS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}
.stApp {
    background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%);
    min-height: 100vh;
}
#MainMenu, footer, header { visibility: hidden; }

/* ── Hero (pages 1 & 2) ─────────────────────────────────────────────────── */
.hero-title {
    font-size: 3rem;
    font-weight: 900;
    background: linear-gradient(135deg, #6c63ff, #48cfad, #f7971e);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    text-align: center;
    margin-bottom: 0.2rem;
    letter-spacing: -1.5px;
}
.hero-subtitle {
    font-size: 1.05rem;
    color: #718096;
    text-align: center;
    margin-bottom: 0.5rem;
    font-weight: 400;
}
.hero-divider {
    width: 60px;
    height: 3px;
    background: linear-gradient(90deg, #6c63ff, #48cfad);
    border-radius: 2px;
    margin: 0 auto 2.5rem auto;
}

/* ── Results page header (page 3) ───────────────────────────────────────── */
.results-hero {
    text-align: center;
    margin-bottom: 0.4rem;
}
.results-hero-title {
    font-size: 2.2rem;
    font-weight: 900;
    background: linear-gradient(135deg, #48cfad, #6c63ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -1px;
}
.results-hero-sub {
    font-size: 0.95rem;
    color: #718096;
    margin-top: 0.25rem;
}
.results-divider {
    width: 50px;
    height: 3px;
    background: linear-gradient(90deg, #48cfad, #6c63ff);
    border-radius: 2px;
    margin: 0.6rem auto 1.6rem auto;
}

/* ── Summary bar ─────────────────────────────────────────────────────────── */
.summary-bar {
    background: rgba(72, 207, 173, 0.06);
    border: 1px solid rgba(72, 207, 173, 0.2);
    border-radius: 14px;
    padding: 0.9rem 1.4rem;
    margin-bottom: 1.8rem;
    display: flex;
    flex-wrap: wrap;
    gap: 1.4rem;
    align-items: center;
}
.sb-item {
    font-size: 0.83rem;
    color: #a0aec0;
}
.sb-item strong { color: #e2e8f0; }
.sb-sep {
    color: rgba(255,255,255,0.12);
    font-size: 1rem;
}

/* ── Glassmorphism form card ─────────────────────────────────────────────── */
.form-card {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 20px;
    padding: 2rem 2.2rem;
    backdrop-filter: blur(12px);
    margin-bottom: 1.5rem;
}
.section-label {
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.13em;
    color: #6c63ff;
    margin-bottom: 1rem;
}

/* ── Profile mini bar (page 2 top strip) ─────────────────────────────────── */
.profile-mini {
    background: rgba(108, 99, 255, 0.07);
    border: 1px solid rgba(108, 99, 255, 0.2);
    border-radius: 14px;
    padding: 0.8rem 1.3rem;
    margin-bottom: 1.4rem;
    display: flex;
    flex-wrap: wrap;
    gap: 1.2rem;
    align-items: center;
}
.profile-mini-item { font-size: 0.82rem; color: #a0aec0; }
.profile-mini-item strong { color: #e2e8f0; }

/* ── Buttons ─────────────────────────────────────────────────────────────── */
.stButton > button {
    background: linear-gradient(135deg, #6c63ff 0%, #48cfad 100%);
    color: white;
    font-weight: 700;
    font-size: 1rem;
    border: none;
    border-radius: 12px;
    padding: 0.8rem 2rem;
    letter-spacing: 0.03em;
    transition: all 0.25s ease;
    cursor: pointer;
}
.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 28px rgba(108, 99, 255, 0.4);
}
.stButton > button:active { transform: translateY(0px); }

/* ── Quiz ────────────────────────────────────────────────────────────────── */
.quiz-counter {
    font-size: 0.7rem;
    font-weight: 700;
    color: #6c63ff;
    text-transform: uppercase;
    letter-spacing: 0.13em;
    margin-bottom: 0.35rem;
}
.quiz-question {
    font-size: 1.18rem;
    font-weight: 700;
    color: #e2e8f0;
    line-height: 1.55;
    margin: 0.9rem 0 1.3rem 0;
}
div[data-testid="stRadio"] label {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 10px;
    padding: 0.6rem 1rem;
    margin-bottom: 0.42rem;
    display: block;
    transition: border-color 0.2s, background 0.2s;
    cursor: pointer;
    color: #cbd5e0 !important;
    font-size: 0.93rem;
}
div[data-testid="stRadio"] label:hover {
    border-color: rgba(108, 99, 255, 0.5);
    background: rgba(108, 99, 255, 0.07);
}

/* ── Section separator ───────────────────────────────────────────────────── */
.section-sep {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(108,99,255,0.3), transparent);
    margin: 1.8rem 0;
}

/* ── No-results warning ──────────────────────────────────────────────────── */
.no-results {
    background: rgba(247, 151, 30, 0.07);
    border: 1px solid rgba(247, 151, 30, 0.22);
    border-radius: 14px;
    padding: 1.4rem 1.6rem;
    color: #f7b733;
    font-size: 0.93rem;
    text-align: center;
}

/* ── Footer ──────────────────────────────────────────────────────────────── */
.raahi-footer {
    text-align: center;
    padding: 2rem 0 1rem 0;
    font-size: 0.75rem;
    color: #2d3748;
    letter-spacing: 0.04em;
}
.raahi-footer span { color: #4a5568; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════════════════════════════════════════
CITIES = [
    "Islamabad", "Rawalpindi", "Lahore", "Karachi",
    "Peshawar", "Quetta", "Multan", "Faisalabad", "Other",
]
STUDY_CITIES = ["Any"] + [c for c in CITIES if c != "Other"]

FIELD_LABELS = {
    "CS":    "Computer Science",
    "SE":    "Software Engineering",
    "AI":    "Artificial Intelligence",
    "Data":  "Data Science",
    "Elec":  "Electrical Engineering",
    "Mech":  "Mechanical Engineering",
    "Civil": "Civil Engineering",
    "BBA":   "BBA",
    "Fin":   "Accounting & Finance",
    "Med":   "MBBS",
    "Pharma":"Pharmacy",
    "Psych": "Psychology",
}

OPTION_KEYS = ["A", "B", "C", "D"]

QUESTIONS = [
    {
        "q": "You have a free weekend. Which sounds most exciting?",
        "options": [
            ("Build a mobile app",          {"CS": 3, "SE": 3, "AI": 2}),
            ("Design a bridge",             {"Civil": 3, "Mech": 3, "Elec": 2}),
            ("Run a business experiment",   {"BBA": 3, "Fin": 2}),
            ("Analyze a disease outbreak",  {"Med": 3, "Pharma": 2, "Data": 2}),
        ],
    },
    {
        "q": "A company gives you a problem. What do you do first?",
        "options": [
            ("Write code",                     {"CS": 3, "SE": 3, "AI": 2}),
            ("Draw a system or process map",   {"Mech": 3, "Civil": 2, "Elec": 2}),
            ("Research data and patterns",     {"Data": 3, "AI": 2, "CS": 1}),
            ("Organize people and resources",  {"BBA": 3, "Fin": 2}),
        ],
    },
    {
        "q": "Which result makes you proudest?",
        "options": [
            ("Your app has 10,000 users",        {"CS": 3, "SE": 3}),
            ("A building standing in 50 years",  {"Civil": 3, "Mech": 2}),
            ("Your startup turns profitable",    {"BBA": 3, "Fin": 2}),
            ("You discover a life-saving drug",  {"Med": 3, "Pharma": 3}),
        ],
    },
    {
        "q": "What kind of problem do you enjoy?",
        "options": [
            ("Logical / algorithmic puzzles",      {"CS": 3, "AI": 3, "Data": 2}),
            ("Physical / mechanical challenges",   {"Mech": 3, "Elec": 2, "Civil": 2}),
            ("Human behavior and markets",         {"BBA": 2, "Psych": 3, "Fin": 2}),
            ("Biological or chemical problems",    {"Med": 3, "Pharma": 3}),
        ],
    },
    {
        "q": "Pick your ideal work environment:",
        "options": [
            ("Tech startup",                 {"CS": 3, "SE": 3, "AI": 2}),
            ("Construction site or factory", {"Civil": 3, "Mech": 3}),
            ("Corporate office or bank",     {"BBA": 2, "Fin": 3}),
            ("Hospital or research lab",     {"Med": 3, "Pharma": 2, "Psych": 2}),
        ],
    },
    {
        "q": "Which FSc subject did you genuinely enjoy?",
        "options": [
            ("Computer / IT",         {"CS": 3, "SE": 2, "AI": 2}),
            ("Physics & Math",        {"Elec": 3, "Mech": 2, "Civil": 2}),
            ("Economics or Commerce", {"BBA": 3, "Fin": 3}),
            ("Biology & Chemistry",   {"Med": 3, "Pharma": 3}),
        ],
    },
]

TOTAL_Q = len(QUESTIONS)

# ── Data paths ─────────────────────────────────────────────────────────────────
_BASE_DIR   = os.path.dirname(__file__)
FIELDS_PATH = os.path.join(_BASE_DIR, "data", "fields.json")


# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE INITIALISATION
# ══════════════════════════════════════════════════════════════════════════════
_defaults: dict = {
    "profile_submitted": False,
    "student_profile":   {},
    "quiz_q_idx":        0,
    "quiz_answers":      {},   # {question_index (int): option_index (int)}
    "quiz_completed":    False,
    "field_scores":      {},
    "recs":              None,  # cached matcher output for this session
}
for _k, _v in _defaults.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def calculate_quiz_scores() -> dict:
    """Tally raw personality field scores from the quiz answers."""
    scores = {k: 0 for k in FIELD_LABELS}
    for q_idx, opt_idx in st.session_state.quiz_answers.items():
        _, field_map = QUESTIONS[q_idx]["options"][opt_idx]
        for field, pts in field_map.items():
            scores[field] += pts
    return scores


def top_interest_label() -> str:
    """Return the full label of the student's highest-scoring personality field."""
    scores = st.session_state.field_scores
    if not scores or all(v == 0 for v in scores.values()):
        return "Not determined"
    best_key = max(scores, key=lambda k: scores[k])
    return FIELD_LABELS.get(best_key, best_key)


@st.cache_data(show_spinner=False)
def load_fields() -> dict:
    """Load fields.json once and cache for the Streamlit session."""
    with open(FIELDS_PATH, encoding="utf-8") as f:
        return json.load(f)


def _clear_session() -> None:
    """Reset all Raahi session state keys and restart the app."""
    keys = list(_defaults.keys()) + ["_rc_css_done"]
    for k in keys:
        st.session_state.pop(k, None)
    st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# SHARED COMPONENTS
# ══════════════════════════════════════════════════════════════════════════════
def _render_footer() -> None:
    st.markdown(
        '<div class="raahi-footer">'
        'Raahi MVP &nbsp;&bull;&nbsp; '
        '<span>Data based on 2024 admissions</span>'
        '</div>',
        unsafe_allow_html=True,
    )


def _render_hero() -> None:
    st.markdown('<div class="hero-title">Raahi &#129959;</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="hero-subtitle">Find your realistic university path</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="hero-divider"></div>', unsafe_allow_html=True)


def _render_profile_mini() -> None:
    """Compact read-only profile strip shown at top of quiz and results pages."""
    p = st.session_state.student_profile
    city_preview = ", ".join(p["preferred_cities"][:2])
    if len(p["preferred_cities"]) > 2:
        city_preview += f" +{len(p['preferred_cities']) - 2}"

    st.markdown(f"""
    <div class="profile-mini">
        <span class="profile-mini-item">&#128202; <strong>{p['fsc_percentage']}%</strong> FSc</span>
        <span class="profile-mini-item">&#128205; <strong>{p['home_city']}</strong></span>
        <span class="profile-mini-item">&#128176; <strong>PKR {p['annual_budget_pkr']:,}</strong>/yr</span>
        <span class="profile-mini-item">&#127961; <strong>{city_preview}</strong></span>
        <span class="profile-mini-item">&#128100; <strong>{p['gender']}</strong></span>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — STUDENT PROFILE FORM
# ══════════════════════════════════════════════════════════════════════════════
def render_profile_page() -> None:
    _render_hero()

    st.markdown('<div class="form-card">', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-label">&#128203; Your Academic Profile</div>',
        unsafe_allow_html=True,
    )

    with st.form(key="student_profile_form"):

        col1, col2 = st.columns(2)
        with col1:
            fsc_percentage = st.number_input(
                "FSc / Matric Percentage (%)",
                min_value=40.0, max_value=100.0,
                value=75.0, step=0.5, format="%.1f",
                help="Your FSc or equivalent intermediate percentage.",
            )
        with col2:
            home_city = st.selectbox(
                "Your Home City", options=CITIES, index=0,
                help="The city you currently live in.",
            )

        st.write("")

        annual_budget = st.slider(
            "Annual Budget (PKR)",
            min_value=50_000, max_value=800_000,
            value=200_000, step=25_000, format="PKR %d",
            help="Total tuition fee you can comfortably afford per year.",
        )
        if annual_budget <= 100_000:
            budget_tier = "&#128994; Public university range"
        elif annual_budget <= 250_000:
            budget_tier = "&#128993; Mid-tier private range"
        elif annual_budget <= 500_000:
            budget_tier = "&#128992; Premium private range"
        else:
            budget_tier = "&#128308; Top-tier (LUMS / AKU) range"
        st.caption(f"PKR {annual_budget:,} / year — {budget_tier}")

        st.write("")

        col3, col4 = st.columns([3, 2])
        with col3:
            preferred_cities = st.multiselect(
                "Preferred Study Cities",
                options=STUDY_CITIES, default=["Any"],
                help="Select 'Any' if you're open to studying anywhere in Pakistan.",
            )
        with col4:
            gender = st.radio(
                "Gender",
                options=["Male", "Female", "Prefer not to say"],
                index=0,
                help="Used for hostel availability and campus filtering.",
            )

        st.write("")
        form_submitted = st.form_submit_button(
            "Find My Path  &#8594;", use_container_width=True
        )

    st.markdown('</div>', unsafe_allow_html=True)

    if form_submitted:
        errors = []
        if not preferred_cities:
            errors.append("Please select at least one preferred study city.")
        if errors:
            for err in errors:
                st.error(err)
            return

        resolved_cities = (
            STUDY_CITIES[1:] if "Any" in preferred_cities else preferred_cities
        )
        with st.spinner("Saving your profile..."):
            time.sleep(0.4)

        st.session_state.student_profile = {
            "fsc_percentage":    fsc_percentage,
            "home_city":         home_city,
            "annual_budget_pkr": annual_budget,
            "preferred_cities":  resolved_cities,
            "gender":            gender,
        }
        st.session_state.profile_submitted = True
        st.rerun()

    _render_footer()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — PERSONALITY QUIZ
# ══════════════════════════════════════════════════════════════════════════════
def render_quiz_page() -> None:
    _render_hero()
    _render_profile_mini()

    st.markdown('<div class="section-sep"></div>', unsafe_allow_html=True)
    st.markdown('<div class="form-card">', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-label">&#129504; Personality Quiz</div>',
        unsafe_allow_html=True,
    )

    q_idx     = st.session_state.quiz_q_idx
    current_q = QUESTIONS[q_idx]
    is_last   = (q_idx == TOTAL_Q - 1)

    # Progress
    st.markdown(
        f'<div class="quiz-counter">Question {q_idx + 1} of {TOTAL_Q}</div>',
        unsafe_allow_html=True,
    )
    st.progress(q_idx / TOTAL_Q)

    # Question
    st.markdown(
        f'<div class="quiz-question">{current_q["q"]}</div>',
        unsafe_allow_html=True,
    )

    # Options
    option_labels = [
        f"{OPTION_KEYS[i]})  {text}"
        for i, (text, _) in enumerate(current_q["options"])
    ]
    saved_idx = st.session_state.quiz_answers.get(q_idx, None)

    chosen_label = st.radio(
        label="Select one:",
        options=option_labels,
        index=saved_idx,
        key=f"quiz_radio_{q_idx}",
        label_visibility="collapsed",
    )

    st.write("")

    btn_label = "See My Results  &#8594;" if is_last else "Next  &#8594;"
    if st.button(btn_label, use_container_width=True, key=f"quiz_btn_{q_idx}"):
        if chosen_label is None:
            st.error("Please pick one option before continuing.")
        else:
            chosen_idx = option_labels.index(chosen_label)
            st.session_state.quiz_answers[q_idx] = chosen_idx

            if is_last:
                with st.spinner("Calculating your personality scores..."):
                    time.sleep(0.8)
                st.session_state.field_scores = calculate_quiz_scores()
                st.session_state.quiz_completed = True
            else:
                st.session_state.quiz_q_idx += 1

            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
    _render_footer()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — RESULTS
# ══════════════════════════════════════════════════════════════════════════════
def render_results_page() -> None:
    p = st.session_state.student_profile

    # ── Results header ────────────────────────────────────────────────────────
    st.markdown("""
    <div class="results-hero">
        <div class="results-hero-title">Your Raahi Results &#129959;</div>
        <div class="results-hero-sub">Here is your personalised university path</div>
    </div>
    <div class="results-divider"></div>
    """, unsafe_allow_html=True)

    # ── Summary bar ────────────────────────────────────────────────────────────
    top_interest = top_interest_label()
    city_str     = ", ".join(p["preferred_cities"][:3])
    if len(p["preferred_cities"]) > 3:
        city_str += f" +{len(p['preferred_cities']) - 3}"

    st.markdown(f"""
    <div class="summary-bar">
        <span class="sb-item">&#128202; FSc: <strong>{p['fsc_percentage']}%</strong></span>
        <span class="sb-sep">|</span>
        <span class="sb-item">&#128176; Budget: <strong>PKR {p['annual_budget_pkr']:,}/yr</strong></span>
        <span class="sb-sep">|</span>
        <span class="sb-item">&#127919; Top Interest: <strong>{top_interest}</strong></span>
        <span class="sb-sep">|</span>
        <span class="sb-item">&#127961; Cities: <strong>{city_str}</strong></span>
    </div>
    """, unsafe_allow_html=True)

    # ── Run matcher (compute once, cache in session state) ────────────────────
    if st.session_state.recs is None:
        with st.spinner("Raahi is finding your path..."):
            time.sleep(1.0)   # brief pause so spinner is visible
            st.session_state.recs = get_recommendations(
                fsc_percentage=p["fsc_percentage"],
                annual_budget=p["annual_budget_pkr"],
                preferred_cities=p["preferred_cities"],
                gender=p["gender"],
                personality_scores=st.session_state.field_scores,
            )

    recs       = st.session_state.recs
    all_fields = load_fields()

    # ── Render cards ──────────────────────────────────────────────────────────
    if not recs:
        st.markdown("""
        <div class="no-results">
            &#128533; No matching universities found for your profile.<br>
            Try increasing your budget or expanding your preferred cities, then start over.
        </div>
        """, unsafe_allow_html=True)
    else:
        for r in recs:
            field_key  = get_field_key(r["program_name"])
            field_data = all_fields.get(field_key, {})
            show_result_card(rank=r["rank"], result=r, field_data=field_data)

    # ── Start Over ────────────────────────────────────────────────────────────
    st.write("")
    col_btn, _, _ = st.columns([1.4, 1, 1])
    with col_btn:
        if st.button("&#8635;  Start Over", use_container_width=True):
            _clear_session()

    _render_footer()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE ROUTER
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.quiz_completed:
    render_results_page()
elif st.session_state.profile_submitted:
    render_quiz_page()
else:
    render_profile_page()
