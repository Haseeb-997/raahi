"""
result_card.py — Streamlit UI component for a single recommendation card.

Public API
----------
show_result_card(rank, result, field_data)
    Renders one complete recommendation card with admission status, budget,
    why/risk bullets, salary outlook, and a Reality Check expander.

get_field_key(program_name)
    Maps a CSV program_name to its fields.json dict key.
"""

from __future__ import annotations
import streamlit as st

# ── Program name → fields.json key ───────────────────────────────────────────
PROGRAM_TO_FIELD_KEY: dict[str, str] = {
    "BS CS":                   "Computer Science",
    "BS SE":                   "Software Engineering",
    "BS AI":                   "Artificial Intelligence",
    "BS Data Science":         "Data Science",
    "BS EE":                   "Electrical Engineering",
    "BS ME":                   "Mechanical Engineering",
    "BS Civil":                "Civil Engineering",
    "BBA":                     "BBA",
    "BS Accounting & Finance": "Accounting & Finance",
    "BS Psychology":           "Psychology",
    "BS Pharmacy":             "Pharmacy",
    "MBBS":                    "MBBS",
}


def get_field_key(program_name: str) -> str:
    """Return the fields.json key for a given program_name from the CSV."""
    return PROGRAM_TO_FIELD_KEY.get(program_name, program_name)


# ── CSS (injected once per Streamlit session) ─────────────────────────────────
_CARD_CSS = """
<style>
/* ── Card wrapper ── */
.rec-card {
    background: rgba(255,255,255,0.038);
    border: 1px solid rgba(255,255,255,0.09);
    border-radius: 20px;
    padding: 1.7rem 1.9rem 1.4rem 1.9rem;
    margin-bottom: 0.5rem;
    transition: border-color 0.25s ease, box-shadow 0.25s ease;
}
.rec-card:hover {
    border-color: rgba(108,99,255,0.38);
    box-shadow: 0 4px 32px rgba(108,99,255,0.1);
}
/* ── Header ── */
.rc-option-label {
    font-size: 0.66rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.14em;
    color: #6c63ff;
    margin-bottom: 0.18rem;
}
.rc-program-title {
    font-size: 1.22rem;
    font-weight: 800;
    color: #e2e8f0;
    margin-bottom: 0.12rem;
    line-height: 1.3;
}
.rc-uni-line {
    font-size: 0.87rem;
    color: #718096;
    margin-bottom: 1.1rem;
}
.rc-uni-line b { color: #a0aec0; }

/* ── Micro section labels ── */
.rc-sec {
    font-size: 0.63rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #4a5568;
    margin-bottom: 0.28rem;
}

/* ── Inline badges ── */
.badge {
    display: inline-block;
    font-size: 0.73rem;
    font-weight: 700;
    padding: 0.18rem 0.6rem;
    border-radius: 20px;
    margin-bottom: 0.35rem;
    letter-spacing: 0.02em;
}
.b-green  { background:rgba(72,207,173,0.16); color:#48cfad; border:1px solid rgba(72,207,173,0.32); }
.b-lime   { background:rgba(154,230,180,0.14); color:#9ae6b4; border:1px solid rgba(154,230,180,0.28); }
.b-yellow { background:rgba(247,183,51,0.16);  color:#f7b733; border:1px solid rgba(247,183,51,0.32); }
.b-red    { background:rgba(255,107,107,0.16); color:#fc8181; border:1px solid rgba(255,107,107,0.32); }
.b-purple { background:rgba(108,99,255,0.16);  color:#a78bfa; border:1px solid rgba(108,99,255,0.32); }
.b-gray   { background:rgba(160,174,192,0.12); color:#a0aec0; border:1px solid rgba(160,174,192,0.22); }

/* ── Detail text ── */
.rc-detail {
    font-size: 0.84rem;
    color: #a0aec0;
    margin: 0.06rem 0;
    line-height: 1.5;
}
.rc-detail b { color: #cbd5e0; }

/* ── Why / Risk bullets ── */
.rc-why-block  { margin: 0.5rem 0 0.2rem 0; }
.rc-risk-block { margin: 0.6rem 0 0.2rem 0; }
.rc-why-item {
    display: flex; gap: 0.45rem; align-items: flex-start;
    font-size: 0.86rem; color: #c6f6d5; padding: 0.18rem 0;
}
.rc-risk-item {
    display: flex; gap: 0.45rem; align-items: flex-start;
    font-size: 0.86rem; color: #fbd38d; padding: 0.18rem 0;
}
.rc-why-dot  { color: #48cfad; margin-top: 1px; flex-shrink: 0; }
.rc-risk-dot { color: #f7b733; margin-top: 1px; flex-shrink: 0; }

/* ── Risk section label ── */
.rc-risk-label {
    font-size: 0.63rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #92400e;
    margin-bottom: 0.28rem;
    margin-top: 0.7rem;
}

/* ── Salary strip ── */
.salary-strip {
    display: flex;
    flex-wrap: wrap;
    gap: 1rem;
    justify-content: space-between;
    align-items: center;
    background: rgba(108,99,255,0.07);
    border: 1px solid rgba(108,99,255,0.17);
    border-radius: 12px;
    padding: 0.85rem 1.1rem;
    margin-top: 1rem;
}
.ss-item    { display: flex; flex-direction: column; gap: 0.15rem; }
.ss-label   { font-size: 0.62rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; color: #4a5568; }
.ss-val     { font-size: 0.92rem; font-weight: 700; color: #e2e8f0; }
.ss-sub     { font-size: 0.8rem; color: #a0aec0; }

/* ── Expander tweaks ── */
.streamlit-expanderHeader {
    font-size: 0.88rem !important;
    color: #a0aec0 !important;
    background: rgba(255,255,255,0.03) !important;
    border-radius: 8px !important;
}
</style>
"""

# ── Internal helpers ──────────────────────────────────────────────────────────

def _inject_css() -> None:
    if not st.session_state.get("_rc_css_done", False):
        st.markdown(_CARD_CSS, unsafe_allow_html=True)
        st.session_state["_rc_css_done"] = True


def _badge(text: str, cls: str) -> str:
    return f'<span class="badge {cls}">{text}</span>'


def _admission_badge(label: str) -> str:
    configs = {
        "Strong Match": ("Strong Match &#10003;", "b-green"),
        "Likely":       ("Likely &#9679;",        "b-yellow"),
        "Reach":        ("Reach &#9888;",          "b-red"),
    }
    text, cls = configs.get(label, (label, "b-gray"))
    return _badge(text, cls)


def _budget_badge(label: str) -> str:
    configs = {
        "Comfortable":   ("Comfortable &#10003;",   "b-green"),
        "Within Budget": ("Within Budget &#10003;", "b-lime"),
        "Slight Risk":   ("Slight Risk &#9888;",    "b-yellow"),
    }
    text, cls = configs.get(label, (label, "b-gray"))
    return _badge(text, cls)


def _demand_badge(demand: str) -> str:
    configs = {
        "Very High": ("Very High", "b-purple"),
        "High":      ("High",      "b-green"),
        "Medium":    ("Medium",    "b-yellow"),
        "Low":       ("Low",       "b-red"),
    }
    text, cls = configs.get(demand, (demand, "b-gray"))
    return _badge(text, cls)


def _saturation_color(saturation: str) -> str:
    return {
        "Low":       "#48cfad",
        "Medium":    "#f7b733",
        "High":      "#fc8181",
        "Very High": "#fc8181",
    }.get(saturation, "#a0aec0")


def _rank_medal(rank: int) -> str:
    return {1: "&#127945;", 2: "&#127946;", 3: "&#127947;"}.get(rank, f"#{rank}")


# ══════════════════════════════════════════════════════════════════════════════
# Main card renderer
# ══════════════════════════════════════════════════════════════════════════════

def show_result_card(rank: int, result: dict, field_data: dict) -> None:
    """
    Render one recommendation card.

    Parameters
    ----------
    rank       : 1, 2, or 3.
    result     : Dict from matcher.get_recommendations().
    field_data : Entry from fields.json for this program's field.
                 Pass {} if the field has no data (card degrades gracefully).
    """
    _inject_css()

    medal     = _rank_medal(rank)
    sector    = result.get("sector", "")
    tier      = result.get("ranking_tier", "?")
    sector_icon = "&#127963;" if sector == "Public" else "&#127970;"

    # ── FSc for comparison (read from session state — available app-wide) ─────
    fsc = st.session_state.get("student_profile", {}).get("fsc_percentage", None)
    cutoff = result.get("merit_cutoff_percentage", None)

    # Build FSc vs cutoff line
    if fsc is not None and cutoff is not None:
        gap = round(fsc - cutoff, 1)
        gap_str = f"+{gap}%" if gap >= 0 else f"{gap}%"
        gap_color = "#48cfad" if gap >= 0 else "#fc8181"
        fsc_line = (
            f'Your FSc: <b>{fsc}%</b> &nbsp;|&nbsp; '
            f'Cutoff: <b>{cutoff}%</b> &nbsp;|&nbsp; '
            f'<span style="color:{gap_color};font-weight:700;">{gap_str}</span>'
        )
    elif cutoff is not None:
        fsc_line = f'Merit cutoff: <b>{cutoff}%</b>'
    else:
        fsc_line = "Cutoff data unavailable"

    with st.container():
        st.markdown('<div class="rec-card">', unsafe_allow_html=True)

        # ── HEADER ────────────────────────────────────────────────────────────
        st.markdown(f"""
        <div class="rc-option-label">Option #{rank} &nbsp; {medal}</div>
        <div class="rc-program-title">{result.get('program_name', 'N/A')}</div>
        <div class="rc-uni-line">
            <b>{result.get('university_name', '')}</b>
            &nbsp;&bull;&nbsp; {result.get('city', '')}
            &nbsp;&bull;&nbsp; {sector_icon} {sector} (Tier {tier})
        </div>
        """, unsafe_allow_html=True)

        # ── ADMISSION + BUDGET ────────────────────────────────────────────────
        col_adm, col_bud = st.columns(2)

        with col_adm:
            adm_label = result.get("admission_label", "")
            st.markdown(f"""
            <div class="rc-sec">Admission Status</div>
            {_admission_badge(adm_label)}
            <div class="rc-detail" style="margin-top:0.35rem;">{fsc_line}</div>
            """, unsafe_allow_html=True)

        with col_bud:
            fee       = result.get("annual_fee_pkr", 0)
            bud_label = result.get("budget_label", "")
            hostel    = result.get("hostel_available", "N/A")
            st.markdown(f"""
            <div class="rc-sec">Fees &amp; Budget</div>
            {_budget_badge(bud_label)}
            <div class="rc-detail" style="margin-top:0.35rem;">
                <b>PKR {fee:,}</b> / year
            </div>
            <div class="rc-detail">Hostel on campus: <b>{hostel}</b></div>
            """, unsafe_allow_html=True)

        st.write("")

        # ── WHY THIS ──────────────────────────────────────────────────────────
        why_list = result.get("why_list", [])
        if why_list:
            why_items = "".join(
                f'<div class="rc-why-item">'
                f'<span class="rc-why-dot">&#10003;</span>'
                f'<span>{w}</span></div>'
                for w in why_list
            )
            st.markdown(f"""
            <div class="rc-sec">Why we recommend this</div>
            <div class="rc-why-block">{why_items}</div>
            """, unsafe_allow_html=True)

        # ── RISKS ─────────────────────────────────────────────────────────────
        risk_list = result.get("risk_list", [])
        if risk_list:
            risk_items = "".join(
                f'<div class="rc-risk-item">'
                f'<span class="rc-risk-dot">&#9888;</span>'
                f'<span>{r}</span></div>'
                for r in risk_list
            )
            st.markdown(f"""
            <div class="rc-risk-label">Things to consider</div>
            <div class="rc-risk-block">{risk_items}</div>
            """, unsafe_allow_html=True)

        # ── SALARY OUTLOOK STRIP ──────────────────────────────────────────────
        sal_min    = field_data.get("salary_min_pkr", 0)
        sal_max    = field_data.get("salary_max_pkr", 0)
        demand     = field_data.get("demand", "N/A")
        saturation = field_data.get("saturation", "N/A")
        remote     = field_data.get("remote_work_possible", False)
        growth     = field_data.get("growth_outlook", "N/A")

        sat_color    = _saturation_color(saturation)
        remote_label = "&#10003; Remote possible" if remote else "&#9679; On-site"

        st.markdown(f"""
        <div class="salary-strip">
            <div class="ss-item">
                <span class="ss-label">Avg Monthly Salary</span>
                <span class="ss-val">PKR {sal_min:,} &ndash; {sal_max:,}</span>
                <span class="ss-sub">after graduation</span>
            </div>
            <div class="ss-item">
                <span class="ss-label">Market Demand</span>
                {_demand_badge(demand)}
            </div>
            <div class="ss-item">
                <span class="ss-label">Field Saturation</span>
                <span class="ss-val" style="font-size:0.85rem;color:{sat_color};">{saturation}</span>
            </div>
            <div class="ss-item">
                <span class="ss-label">Growth Outlook</span>
                <span class="ss-val" style="font-size:0.85rem;">{growth}</span>
            </div>
            <div class="ss-item">
                <span class="ss-label">Work Mode</span>
                <span class="ss-sub">{remote_label}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── REALITY CHECK (collapsible) ────────────────────────────────────────
        jobs         = field_data.get("jobs_after_3_years", [])
        reality_note = field_data.get("reality_note", "")
        sat_note     = field_data.get("saturation_note", "")
        trend        = field_data.get("market_trend", "")
        employers    = field_data.get("top_employers_pakistan", [])

        with st.expander("What graduates actually do \U0001f447"):
            if jobs:
                col_j1, col_j2 = st.columns(2)
                mid = len(jobs) // 2 + len(jobs) % 2
                with col_j1:
                    st.markdown("**Common roles after 3 years**")
                    for j in jobs[:mid]:
                        st.markdown(f"- {j}")
                with col_j2:
                    if employers:
                        st.markdown("**Top employers in Pakistan**")
                        for e in employers[:4]:
                            st.markdown(f"- {e}")

            if reality_note:
                st.info(f"**Reality Check:** {reality_note}")

            if sat_note:
                st.warning(f"**Saturation:** {sat_note}")

            cols_meta = st.columns(2)
            with cols_meta[0]:
                st.markdown(f"**Growth Outlook:** {growth}")
            with cols_meta[1]:
                st.markdown(f"**Market Trend:** {trend}")

        st.markdown('</div>', unsafe_allow_html=True)

    st.divider()
