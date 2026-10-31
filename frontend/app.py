"""
SchemePathAI — Streamlit Frontend
Autonomous student government scheme navigator powered by Gen AI.
"""

import streamlit as st
import requests
import pandas as pd
import json
from typing import Optional

# ─── Page Config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="SchemePathAI 🎓",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Constants ─────────────────────────────────────────────────────────────────

BACKEND_URL = "http://localhost:8000"

INDIAN_STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
    "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya",
    "Mizoram", "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim",
    "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand",
    "West Bengal",
    # Union Territories
    "Andaman and Nicobar Islands", "Chandigarh",
    "Dadra and Nagar Haveli and Daman and Diu", "Delhi",
    "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry",
]

CATEGORY_COLORS = {
    "scholarship": "#4CAF50",
    "education_loan": "#2196F3",
    "hostel": "#9C27B0",
    "fee_reimbursement": "#FF9800",
    "digital_access": "#00BCD4",
    "skill_development": "#8BC34A",
    "research_fellowship": "#673AB7",
    "study_abroad": "#F44336",
    "girl_child": "#E91E63",
    "differently_abled": "#FF5722",
    "sports": "#CDDC39",
    "health_insurance": "#009688",
    "book_grant": "#795548",
    "internship": "#607D8B",
}

CATEGORY_LABELS = {
    "scholarship": "🎓 Scholarship",
    "education_loan": "🏦 Education Loan",
    "hostel": "🏠 Hostel",
    "fee_reimbursement": "💸 Fee Reimbursement",
    "digital_access": "💻 Digital Access",
    "skill_development": "🛠️ Skill Development",
    "research_fellowship": "🔬 Research Fellowship",
    "study_abroad": "✈️ Study Abroad",
    "girl_child": "👧 Girl Child",
    "differently_abled": "♿ Differently Abled",
    "sports": "🏅 Sports",
    "health_insurance": "🏥 Health Insurance",
    "book_grant": "📚 Book Grant",
    "internship": "💼 Internship",
}

# ─── Custom CSS ────────────────────────────────────────────────────────────────

st.markdown("""
<style>
    /* ── Main theme ── */
    :root {
        --primary: #1565C0;
        --secondary: #FF6F00;
        --bg-card: #F8F9FA;
        --border: #E0E0E0;
        --success: #2E7D32;
        --text-muted: #757575;
    }

    /* ── Hide Streamlit default branding ── */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0D47A1 0%, #1565C0 60%, #1976D2 100%);
        color: white;
    }
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stRadio label {
        color: white !important;
    }
    [data-testid="stSidebar"] .stRadio > div {
        background: rgba(255,255,255,0.1);
        border-radius: 8px;
        padding: 4px 8px;
    }

    /* ── Hero ── */
    .hero-container {
        background: linear-gradient(135deg, #1565C0 0%, #0D47A1 50%, #FF6F00 100%);
        border-radius: 16px;
        padding: 60px 40px;
        text-align: center;
        color: white;
        margin-bottom: 32px;
    }
    .hero-container h1 {
        font-size: 3rem;
        font-weight: 800;
        margin-bottom: 12px;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    .hero-container p {
        font-size: 1.25rem;
        opacity: 0.9;
        max-width: 600px;
        margin: 0 auto;
    }

    /* ── Stat cards ── */
    .stat-card {
        background: white;
        border-radius: 12px;
        padding: 28px 20px;
        text-align: center;
        box-shadow: 0 2px 12px rgba(0,0,0,0.08);
        border-top: 4px solid #FF6F00;
        transition: transform 0.2s;
    }
    .stat-card:hover { transform: translateY(-4px); }
    .stat-number { font-size: 2.5rem; font-weight: 800; color: #1565C0; }
    .stat-label { font-size: 1rem; color: #757575; margin-top: 6px; }

    /* ── Scheme card ── */
    .scheme-card {
        background: white;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.07);
        border-left: 5px solid #1565C0;
        transition: box-shadow 0.2s;
    }
    .scheme-card:hover { box-shadow: 0 6px 24px rgba(0,0,0,0.13); }

    /* ── Badge ── */
    .badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 600;
        color: white;
        margin-bottom: 10px;
    }

    /* ── Benefit chip ── */
    .benefit-chip {
        background: #E8F5E9;
        color: #2E7D32;
        border-radius: 8px;
        padding: 6px 14px;
        font-weight: 700;
        font-size: 1.05rem;
        display: inline-block;
    }

    /* ── Match reason ── */
    .match-reason {
        color: #2E7D32;
        font-size: 0.88rem;
        margin: 2px 0;
    }

    /* ── Step indicator ── */
    .step-indicator {
        display: flex;
        gap: 8px;
        margin-bottom: 24px;
    }
    .step-dot {
        width: 32px; height: 32px;
        border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-weight: 700; font-size: 0.9rem;
        background: #E0E0E0; color: #757575;
    }
    .step-dot.active { background: #1565C0; color: white; }
    .step-dot.done   { background: #4CAF50; color: white; }

    /* ── Section header ── */
    .section-header {
        font-size: 1.6rem;
        font-weight: 700;
        color: #1565C0;
        border-bottom: 3px solid #FF6F00;
        padding-bottom: 8px;
        margin-bottom: 24px;
    }

    /* ── Info box ── */
    .info-box {
        background: #E3F2FD;
        border-radius: 10px;
        padding: 16px 20px;
        border-left: 4px solid #1565C0;
        margin: 12px 0;
    }

    /* ── Tech tag ── */
    .tech-tag {
        display: inline-block;
        background: #E8EAF6;
        color: #3949AB;
        border-radius: 6px;
        padding: 4px 12px;
        margin: 4px;
        font-size: 0.85rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# ─── Session State Init ────────────────────────────────────────────────────────

if "page" not in st.session_state:
    st.session_state.page = "Home"
if "form_step" not in st.session_state:
    st.session_state.form_step = 1
if "form_data" not in st.session_state:
    st.session_state.form_data = {}
if "results" not in st.session_state:
    st.session_state.results = None
if "session_id" not in st.session_state:
    st.session_state.session_id = None

# ─── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding: 16px 0 8px 0;'>
        <div style='font-size:3rem;'>🎓</div>
        <div style='font-size:1.5rem; font-weight:800; color:white; letter-spacing:1px;'>SchemePathAI</div>
        <div style='font-size:0.82rem; color:rgba(255,255,255,0.7); margin-top:4px;'>
            AI-powered government scheme navigator for every Indian student
        </div>
    </div>
    <hr style='border-color:rgba(255,255,255,0.2); margin:12px 0;'/>
    """, unsafe_allow_html=True)

    nav = st.radio(
        "Navigate",
        ["🏠 Home", "🔍 Discover Schemes", "📋 My Applications", "ℹ️ About"],
        index=["🏠 Home", "🔍 Discover Schemes", "📋 My Applications", "ℹ️ About"].index(
            {
                "Home": "🏠 Home",
                "Discover": "🔍 Discover Schemes",
                "Applications": "📋 My Applications",
                "About": "ℹ️ About",
            }.get(st.session_state.page, "🏠 Home")
        ),
        label_visibility="collapsed",
    )

    # Map nav label → internal page key
    NAV_MAP = {
        "🏠 Home": "Home",
        "🔍 Discover Schemes": "Discover",
        "📋 My Applications": "Applications",
        "ℹ️ About": "About",
    }
    st.session_state.page = NAV_MAP[nav]

    st.markdown("<hr style='border-color:rgba(255,255,255,0.2); margin:16px 0;'/>", unsafe_allow_html=True)
    st.markdown("""
    <div style='font-size:0.78rem; color:rgba(255,255,255,0.6); text-align:center;'>
        Data sourced from<br/>
        <b style='color:white;'>myscheme.gov.in · NSP · Vidya Lakshmi</b><br/>
        <br/>🇮🇳 Made for Bharat
    </div>
    """, unsafe_allow_html=True)

# ─── Helpers ──────────────────────────────────────────────────────────────────

def backend_post(endpoint: str, payload: dict) -> Optional[dict]:
    """POST to backend; returns parsed JSON or None on error."""
    try:
        resp = requests.post(
            f"{BACKEND_URL}{endpoint}",
            json=payload,
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        st.error(
            "⚠️ **Backend is not running.**\n\n"
            "Start it with:\n```bash\ncd backend\nuvicorn main:app --reload --port 8000\n```"
        )
        return None
    except requests.exceptions.Timeout:
        st.error("⏱️ Request timed out. The AI agent is still working — please try again in a moment.")
        return None
    except requests.exceptions.HTTPError as e:
        st.error(f"❌ Backend error: {e.response.status_code} — {e.response.text[:300]}")
        return None
    except Exception as e:
        st.error(f"❌ Unexpected error: {e}")
        return None


def score_color(score: float) -> str:
    if score >= 0.75:
        return "#4CAF50"
    elif score >= 0.5:
        return "#FF9800"
    return "#F44336"


def results_to_df(schemes: list) -> pd.DataFrame:
    rows = []
    for s in schemes:
        rows.append({
            "Scheme Name": s.get("name", ""),
            "Category": s.get("category", ""),
            "Eligibility Score (%)": round(s.get("eligibility_score", 0) * 100, 1),
            "Benefit": s.get("benefit_amount", "—"),
            "Portal": s.get("application_portal", ""),
            "URL": s.get("portal_url", ""),
            "Deadline": s.get("deadline", "—"),
        })
    return pd.DataFrame(rows)


# ─── Page: HOME ───────────────────────────────────────────────────────────────

def page_home():
    st.markdown("""
    <div class='hero-container'>
        <h1>Find Every Scheme You Deserve 🎓</h1>
        <p>
            SchemePathAI uses Gemini AI to match your profile against 500+ government
            scholarship and welfare schemes — then helps you apply, automatically.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class='stat-card'>
            <div class='stat-number'>500+</div>
            <div class='stat-label'>Government Schemes</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class='stat-card'>
            <div class='stat-number'>14</div>
            <div class='stat-label'>Scheme Categories</div>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class='stat-card'>
            <div class='stat-number'>100%</div>
            <div class='stat-label'>Government Sources</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)

    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        if st.button("🔍 Get Started — Find My Schemes", use_container_width=True, type="primary"):
            st.session_state.page = "Discover"
            st.session_state.form_step = 1
            st.rerun()

    st.markdown("<br/>", unsafe_allow_html=True)

    st.markdown("<div class='section-header'>How It Works</div>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    steps = [
        ("📝", "Fill Your Profile", "Tell us your academic background, income, state, and category."),
        ("🤖", "AI Matching", "Gemini AI scans 500+ schemes and computes your eligibility score."),
        ("📋", "Get Results", "See ranked schemes with benefit amounts and required documents."),
        ("🚀", "Auto-Apply", "Our Playwright agent navigates government portals and fills forms for you."),
    ]
    for col, (icon, title, desc) in zip([c1, c2, c3, c4], steps):
        with col:
            st.markdown(f"""
            <div style='text-align:center; padding:20px 10px;'>
                <div style='font-size:2.5rem;'>{icon}</div>
                <div style='font-weight:700; font-size:1rem; margin:8px 0 4px;'>{title}</div>
                <div style='font-size:0.85rem; color:#757575;'>{desc}</div>
            </div>""", unsafe_allow_html=True)


# ─── Page: DISCOVER ───────────────────────────────────────────────────────────

def render_step_indicator(current: int):
    steps = ["Basic Info", "Academic Info", "Additional Info"]
    html = "<div class='step-indicator'>"
    for i, label in enumerate(steps, 1):
        cls = "done" if i < current else ("active" if i == current else "")
        icon = "✓" if i < current else str(i)
        html += f"""
        <div style='display:flex; align-items:center; gap:6px;'>
            <div class='step-dot {cls}'>{icon}</div>
            <span style='font-size:0.85rem; color:{"#1565C0" if i==current else "#757575"};
                         font-weight:{"700" if i==current else "400"};'>{label}</span>
        </div>
        """
        if i < 3:
            html += "<div style='flex:1; height:2px; background:#E0E0E0; margin:0 4px;'></div>"
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def page_discover():
    st.markdown("<div class='section-header'>🔍 Discover Government Schemes</div>", unsafe_allow_html=True)

    if st.session_state.results is None:
        _show_discovery_form()
    else:
        _show_results()


def _show_discovery_form():
    render_step_indicator(st.session_state.form_step)

    fd = st.session_state.form_data  # shorthand

    # ── Step 1: Basic Info ────────────────────────────────────────────────────
    if st.session_state.form_step == 1:
        st.markdown("#### 👤 Basic Information")
        with st.container():
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Full Name *", value=fd.get("name", ""), placeholder="e.g. Priya Sharma")
                age = st.number_input("Age *", min_value=14, max_value=35, value=fd.get("age", 18))
                gender = st.selectbox(
                    "Gender *",
                    ["Male", "Female", "Other"],
                    index=["Male", "Female", "Other"].index(fd.get("gender", "Female")),
                )
            with col2:
                state = st.selectbox(
                    "State / UT *",
                    INDIAN_STATES,
                    index=INDIAN_STATES.index(fd.get("state", "Maharashtra")) if fd.get("state") in INDIAN_STATES else 13,
                )
                district = st.text_input("District (optional)", value=fd.get("district", ""), placeholder="e.g. Pune")

        if st.button("Next: Academic Info →", type="primary"):
            if not name.strip():
                st.error("Please enter your name.")
            else:
                fd.update({"name": name, "age": age, "gender": gender, "state": state, "district": district})
                st.session_state.form_step = 2
                st.rerun()

    # ── Step 2: Academic Info ─────────────────────────────────────────────────
    elif st.session_state.form_step == 2:
        st.markdown("#### 📚 Academic Information")
        col1, col2 = st.columns(2)
        with col1:
            category_opts = ["General", "SC", "ST", "OBC", "EWS", "Minority"]
            category = st.selectbox(
                "Caste Category *",
                category_opts,
                index=category_opts.index(fd.get("category", "General")),
            )
            income = st.number_input(
                "Annual Family Income (₹) *",
                min_value=0,
                max_value=2_000_000,
                value=fd.get("annual_family_income", 200_000),
                step=10_000,
            )
            income_slider = st.slider(
                "Or use slider (₹)",
                0, 1_500_000, income, step=5_000,
                help="Drag to set annual family income",
            )
            income = max(income, income_slider)

            edu_opts = ["Class 8", "Class 10", "Class 12", "Diploma", "Undergraduate", "Postgraduate", "PhD", "Vocational"]
            education_level = st.selectbox(
                "Current Education Level *",
                edu_opts,
                index=edu_opts.index(fd.get("education_level_label", "Undergraduate")),
            )

        with col2:
            course = st.text_input("Course / Class Name *", value=fd.get("course", ""), placeholder="e.g. B.Tech Computer Science")
            stream_opts = ["Science", "Arts", "Commerce", "Engineering", "Medical", "Law", "Vocational", "Other"]
            stream = st.selectbox(
                "Stream *",
                stream_opts,
                index=stream_opts.index(fd.get("stream", "Engineering")),
            )
            inst_opts = ["Government", "Private", "Aided"]
            institution_type = st.selectbox(
                "Institution Type *",
                inst_opts,
                index=inst_opts.index(fd.get("institution_type_label", "Government")),
            )
            percentage = st.slider(
                "Percentage / CGPA % *",
                0.0, 100.0, float(fd.get("percentage_marks", 75.0)), step=0.5,
            )

        bcol1, bcol2 = st.columns(2)
        with bcol1:
            if st.button("← Back"):
                st.session_state.form_step = 1
                st.rerun()
        with bcol2:
            if st.button("Next: Additional Info →", type="primary"):
                if not course.strip():
                    st.error("Please enter your course name.")
                else:
                    # Map labels to enum values
                    edu_map = {
                        "Class 8": "class_8", "Class 10": "class_10", "Class 12": "class_12",
                        "Diploma": "diploma", "Undergraduate": "undergraduate",
                        "Postgraduate": "postgraduate", "PhD": "phd", "Vocational": "vocational",
                    }
                    inst_map = {"Government": "government", "Private": "private", "Aided": "aided"}
                    fd.update({
                        "category": category.lower() if category != "General" else "general",
                        "annual_family_income": income,
                        "education_level": edu_map[education_level],
                        "education_level_label": education_level,
                        "course": course,
                        "stream": stream,
                        "institution_type": inst_map[institution_type],
                        "institution_type_label": institution_type,
                        "percentage_marks": percentage,
                    })
                    st.session_state.form_step = 3
                    st.rerun()

    # ── Step 3: Additional Info ───────────────────────────────────────────────
    elif st.session_state.form_step == 3:
        st.markdown("#### 🔖 Additional Information")
        col1, col2 = st.columns(2)
        with col1:
            has_disability = st.checkbox("Do you have a disability?", value=fd.get("has_disability", False))
            disability_type = ""
            if has_disability:
                disability_type = st.text_input(
                    "Disability Type",
                    value=fd.get("disability_type", ""),
                    placeholder="e.g. Visual Impairment, Hearing Loss",
                )
            interests = st.multiselect(
                "Interests (select all that apply)",
                ["Sports", "Research", "Arts", "Coding", "Agriculture", "None"],
                default=fd.get("interests", []),
            )

        with col2:
            aadhar = st.checkbox("Aadhaar Card Available?", value=fd.get("aadhar_available", True))
            bank = st.checkbox("Bank Account Available?", value=fd.get("bank_account_available", True))
            income_cert = st.checkbox("Income Certificate Available?", value=fd.get("income_certificate_available", True))

            st.markdown("<br/>", unsafe_allow_html=True)
            st.markdown("""
            <div class='info-box'>
            ℹ️ These documents are needed for most government schemes.
            Even if you don't have them now, we'll show you which ones to arrange.
            </div>
            """, unsafe_allow_html=True)

        bcol1, bcol2 = st.columns(2)
        with bcol1:
            if st.button("← Back"):
                st.session_state.form_step = 2
                st.rerun()
        with bcol2:
            if st.button("🔍 Find My Schemes", type="primary"):
                interests_clean = [i.lower() for i in interests if i != "None"]
                fd.update({
                    "has_disability": has_disability,
                    "disability_type": disability_type if has_disability else None,
                    "interests": interests_clean,
                    "aadhar_available": aadhar,
                    "bank_account_available": bank,
                    "income_certificate_available": income_cert,
                })
                _submit_and_fetch()


def _submit_and_fetch():
    fd = st.session_state.form_data

    profile = {
        "name": fd["name"],
        "age": fd["age"],
        "gender": fd["gender"].lower(),
        "state": fd["state"],
        "district": fd.get("district") or None,
        "category": fd["category"],
        "annual_family_income": fd["annual_family_income"],
        "education_level": fd["education_level"],
        "course": fd["course"],
        "stream": fd.get("stream"),
        "institution_type": fd["institution_type"],
        "percentage_marks": fd["percentage_marks"],
        "has_disability": fd.get("has_disability", False),
        "disability_type": fd.get("disability_type"),
        "interests": fd.get("interests", []),
        "aadhar_available": fd.get("aadhar_available", True),
        "bank_account_available": fd.get("bank_account_available", True),
        "income_certificate_available": fd.get("income_certificate_available", True),
    }

    payload = {"profile": profile, "auto_apply": False}

    with st.spinner("🤖 Searching across 500+ government schemes… this may take 20–30 seconds."):
        data = backend_post("/api/discover", payload)

    if data:
        st.session_state.results = data
        st.session_state.session_id = data.get("session_id")
        st.rerun()


def _show_results():
    data = st.session_state.results
    schemes: list = data.get("eligible_schemes", [])

    # ── Summary bar ──────────────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("✅ Schemes Found", data.get("total_found", len(schemes)))
    col2.metric("📂 Categories", len(data.get("categories_covered", [])))
    col3.metric("💰 Est. Total Benefit", data.get("estimated_total_benefit", "—"))
    col4.metric("⏱️ Processed In", f"{data.get('processing_time_seconds', 0):.1f}s")

    # ── Top recommendations ───────────────────────────────────────────────────
    top = data.get("top_recommendations", [])
    if top:
        st.markdown(f"""
        <div class='info-box'>
        ⭐ <b>Top Pick{'' if len(top)==1 else 's'}:</b> {' · '.join(top[:3])}
        </div>""", unsafe_allow_html=True)

    # ── Next steps ────────────────────────────────────────────────────────────
    next_steps = data.get("next_steps", [])
    if next_steps:
        with st.expander("📌 Recommended Next Steps"):
            for step in next_steps:
                st.markdown(f"- {step}")

    st.markdown("---")

    if not schemes:
        st.warning(
            "😔 No matching schemes found for your profile. Try adjusting your income range "
            "or education level. You can also contact your state scholarship board directly."
        )
        if st.button("🔄 Search Again"):
            st.session_state.results = None
            st.session_state.form_step = 1
            st.rerun()
        return

    # Sort by eligibility score descending
    schemes_sorted = sorted(schemes, key=lambda x: x.get("eligibility_score", 0), reverse=True)

    # ── Sidebar filters ───────────────────────────────────────────────────────
    all_cats = list({s.get("category", "") for s in schemes_sorted})
    all_cats.sort()

    with st.sidebar:
        st.markdown("---")
        st.markdown("**🔧 Filter Results**")
        selected_cats = []
        for cat in all_cats:
            label = CATEGORY_LABELS.get(cat, cat.replace("_", " ").title())
            if st.checkbox(label, value=True, key=f"filter_{cat}"):
                selected_cats.append(cat)

    filtered = [s for s in schemes_sorted if s.get("category", "") in selected_cats]

    # ── Download button ───────────────────────────────────────────────────────
    df = results_to_df(filtered)
    csv = df.to_csv(index=False).encode("utf-8")
    colA, colB = st.columns([4, 1])
    with colA:
        st.markdown(f"**Showing {len(filtered)} of {len(schemes)} schemes**")
    with colB:
        st.download_button(
            label="⬇️ Download CSV",
            data=csv,
            file_name="schemepath_results.csv",
            mime="text/csv",
        )

    st.markdown("<br/>", unsafe_allow_html=True)

    # ── Scheme cards ─────────────────────────────────────────────────────────
    for scheme in filtered:
        _render_scheme_card(scheme)

    st.markdown("---")
    if st.button("🔄 Start New Search"):
        st.session_state.results = None
        st.session_state.form_data = {}
        st.session_state.form_step = 1
        st.rerun()


def _render_scheme_card(scheme: dict):
    score = scheme.get("eligibility_score", 0.0)
    score_pct = int(score * 100)
    cat = scheme.get("category", "scholarship")
    badge_color = CATEGORY_COLORS.get(cat, "#1565C0")
    cat_label = CATEGORY_LABELS.get(cat, cat.replace("_", " ").title())
    sc = score_color(score)

    with st.container():
        st.markdown(f"""
        <div class='scheme-card' style='border-left-color:{badge_color};'>
            <div style='display:flex; justify-content:space-between; align-items:flex-start;'>
                <div>
                    <div style='font-size:1.2rem; font-weight:800; color:#1565C0;'>
                        {scheme.get('name', 'Unknown Scheme')}
                    </div>
                    <span class='badge' style='background:{badge_color};'>{cat_label}</span>
                    {"<span style='margin-left:8px;'><span class='benefit-chip'>💰 " + scheme.get('benefit_amount','') + "</span></span>" if scheme.get('benefit_amount') else ""}
                </div>
                <div style='text-align:right; min-width:120px;'>
                    <div style='font-size:0.8rem; color:#757575;'>Eligibility</div>
                    <div style='font-size:1.6rem; font-weight:800; color:{sc};'>{score_pct}%</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Eligibility progress bar
        st.progress(score)

        st.markdown(f"<p style='color:#424242; font-size:0.9rem;'>{scheme.get('description','')[:300]}…</p>", unsafe_allow_html=True)

        # Match reasons
        reasons = scheme.get("match_reasons", [])
        if reasons:
            reasons_html = "".join([f"<div class='match-reason'>✅ {r}</div>" for r in reasons[:4]])
            st.markdown(reasons_html, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    # Documents expander
    docs = scheme.get("documents_required", [])
    if docs:
        with st.expander("📋 Required Documents"):
            for doc in docs:
                st.markdown(f"- 📄 {doc}")

    # Action buttons
    portal_url = scheme.get("portal_url", "")
    col1, col2 = st.columns(2)
    with col1:
        if portal_url:
            st.link_button("🌐 Apply Now", portal_url, use_container_width=True)
        else:
            st.button("🌐 Apply Now", disabled=True, use_container_width=True, key=f"apply_{scheme.get('scheme_id','')}")
    with col2:
        if st.button(
            "🤖 Auto-Navigate",
            key=f"auto_{scheme.get('scheme_id', '')}",
            use_container_width=True,
        ):
            _auto_apply(scheme)

    st.markdown("<hr style='border-color:#F0F0F0; margin:8px 0;'/>", unsafe_allow_html=True)


def _auto_apply(scheme: dict):
    if not st.session_state.session_id:
        st.error("No active session. Please search for schemes first.")
        return

    payload = {
        "session_id": st.session_state.session_id,
        "scheme_id": scheme.get("scheme_id"),
        "profile": st.session_state.form_data,
    }
    with st.spinner(f"🤖 Auto-navigating to {scheme.get('name', 'scheme')} portal…"):
        result = backend_post("/api/apply", payload)

    if result:
        if result.get("success"):
            st.success(
                f"✅ {result.get('message', 'Navigation complete!')}\n\n"
                f"Tracking ID: `{result.get('tracking_id', 'N/A')}`"
            )
        else:
            st.warning(f"⚠️ {result.get('message', 'Could not complete auto-navigation.')}")
            if result.get("error_details"):
                with st.expander("Error Details"):
                    st.code(result["error_details"])


# ─── Page: APPLICATIONS ───────────────────────────────────────────────────────

def page_applications():
    st.markdown("<div class='section-header'>📋 My Applications</div>", unsafe_allow_html=True)
    st.markdown("""
    <div class='info-box'>
    🚧 Application tracking is coming soon. After using <b>Auto-Navigate</b> on any scheme,
    your application status will appear here.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 🔔 What You Can Do Now")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **Manually track your applications:**
        1. Visit [myscheme.gov.in](https://www.myscheme.gov.in)
        2. Log in with your Aadhaar / DigiLocker
        3. Check "My Applications" dashboard
        """)
    with col2:
        st.markdown("""
        **National Scholarship Portal:**
        1. Visit [scholarships.gov.in](https://scholarships.gov.in)
        2. Log in with your NSP registration
        3. Track under "Application Status"
        """)

    if st.button("🔍 Discover New Schemes"):
        st.session_state.page = "Discover"
        st.rerun()


# ─── Page: ABOUT ──────────────────────────────────────────────────────────────

def page_about():
    st.markdown("<div class='section-header'>ℹ️ About SchemePathAI</div>", unsafe_allow_html=True)

    st.markdown("""
    **SchemePathAI** is an autonomous AI-powered student welfare scheme navigator built for the Indian
    education ecosystem. Millions of students miss out on government scholarships and benefits simply
    because they don't know about them or find the application process too complex. We solve both problems.
    """)

    st.markdown("### 🎯 Mission")
    st.markdown("""
    > Ensure every eligible Indian student — regardless of location, language, or digital literacy — 
    > discovers and applies for every government scheme they deserve.
    """)

    st.markdown("### 🛠️ Tech Stack")
    tech = {
        "🤖 AI / LLM": ["Google Gemini 1.5 Pro", "LangGraph (Agent Orchestration)", "ChromaDB (RAG / Vector Search)"],
        "⚙️ Backend": ["FastAPI (Python)", "LangChain", "Pydantic v2"],
        "🖥️ Frontend": ["Streamlit", "Custom CSS"],
        "🌐 Automation": ["Playwright (Browser Agent)", "browser-use"],
        "📦 Data": ["myscheme.gov.in", "NSP API", "Vidya Lakshmi Portal"],
    }
    for category, items in tech.items():
        st.markdown(f"**{category}**")
        tags_html = "".join([f"<span class='tech-tag'>{item}</span>" for item in items])
        st.markdown(tags_html, unsafe_allow_html=True)
        st.markdown("")

    st.markdown("### 📊 Data Sources")
    sources = [
        ("myscheme.gov.in", "Central government scheme aggregator", "https://www.myscheme.gov.in"),
        ("scholarships.gov.in", "National Scholarship Portal (NSP)", "https://scholarships.gov.in"),
        ("vidyalakshmi.co.in", "Vidya Lakshmi Education Loan Portal", "https://www.vidyalakshmi.co.in"),
        ("ugc.ac.in", "UGC Fellowships & Scholarships", "https://www.ugc.ac.in"),
        ("aicte-india.org", "AICTE Scholarships", "https://www.aicte-india.org"),
        ("State Portals", "28 state + 8 UT scholarship portals", "#"),
    ]
    df_src = pd.DataFrame(sources, columns=["Source", "Description", "URL"])
    st.dataframe(df_src, use_container_width=True, hide_index=True)

    st.markdown("### 🏆 Scheme Categories Covered")
    cats = list(CATEGORY_LABELS.values())
    cols = st.columns(4)
    for i, cat in enumerate(cats):
        with cols[i % 4]:
            st.markdown(f"- {cat}")

    st.markdown("---")
    st.markdown(
        "<div style='text-align:center; color:#757575; font-size:0.85rem;'>"
        "Built with ❤️ for Bharat · SchemePathAI Hackathon Project · MIT License"
        "</div>",
        unsafe_allow_html=True,
    )


# ─── Router ───────────────────────────────────────────────────────────────────

page = st.session_state.page

if page == "Home":
    page_home()
elif page == "Discover":
    page_discover()
elif page == "Applications":
    page_applications()
elif page == "About":
    page_about()
