import streamlit as st
from google import genai
from dotenv import load_dotenv
import os
import json
import tempfile

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="AI Resume Critic",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# CUSTOM CSS
# =========================================================
st.markdown("""
<style>

.main-title {
    font-size: 42px;
    font-weight: 800;
    margin-bottom: 0;
}

.subtitle {
    font-size: 18px;
    opacity: 0.75;
    margin-bottom: 20px;
}

.section-title {
    font-size: 24px;
    font-weight: 700;
}

.score-box {
    padding: 20px;
    border-radius: 15px;
    border: 1px solid rgba(128,128,128,0.25);
    text-align: center;
    margin-bottom: 15px;
}

.score-number {
    font-size: 38px;
    font-weight: 800;
}

.keyword {
    display: inline-block;
    padding: 7px 12px;
    margin: 4px;
    border-radius: 20px;
    border: 1px solid rgba(128,128,128,0.3);
    font-size: 14px;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# LOAD API KEY
# =========================================================
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("Gemini API key not found. Please check your .env file.")
    st.stop()

client = genai.Client(api_key=api_key)

# =========================================================
# SESSION STATE
# =========================================================
if "analysis" not in st.session_state:
    st.session_state.analysis = None

# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:

    st.header("🤖 AI Resume Critic")

    st.write(
        "Analyze your resume against a target job "
        "using an AI-powered recruiter."
    )

    st.divider()

    st.subheader("🔎 What gets analyzed?")

    st.write("✓ Job Match Score")
    st.write("✓ Resume Strengths")
    st.write("✓ Missing Keywords")
    st.write("✓ Weak Areas")
    st.write("✓ Skill Gaps")
    st.write("✓ ATS Optimization")
    st.write("✓ Improved Bullet Points")
    st.write("✓ Recruiter Verdict")

    st.divider()

    st.caption("Built with Streamlit + Gemini AI")

# =========================================================
# HEADER
# =========================================================
st.markdown(
    '<p class="main-title">🤖 AI Resume Critic</p>',
    unsafe_allow_html=True
)

st.markdown(
    '<p class="subtitle">'
    'Your AI-powered recruiter for smarter, job-ready resumes.'
    '</p>',
    unsafe_allow_html=True
)

st.divider()

# =========================================================
# INPUT SECTION
# =========================================================
st.markdown(
    '<p class="section-title">📥 Resume & Job Information</p>',
    unsafe_allow_html=True
)

col1, col2 = st.columns(2)

with col1:

    st.subheader("📄 Your Resume")

    resume_file = st.file_uploader(
        "Upload your resume",
        type=["pdf"],
        help="Upload your resume as a PDF file."
    )

    if resume_file:
        st.success(f"✓ {resume_file.name} uploaded")

with col2:

    st.subheader("🎯 Target Job")

    job_description = st.text_area(
        "Paste the Job Description",
        height=220,
        placeholder=(
            "Paste the complete job description here...\n\n"
            "Include responsibilities, required skills, "
            "qualifications and preferred skills."
        )
    )

st.divider()

# =========================================================
# ANALYZE FORM
# =========================================================
with st.form("resume_analysis_form"):

    analyze = st.form_submit_button(
        "🔍 Analyze My Resume",
        use_container_width=True
    )

# =========================================================
# AI ANALYSIS
# =========================================================
if analyze:

    if resume_file is None:

        st.warning(
            "⚠️ Please upload your resume PDF before analyzing."
        )

    elif not job_description.strip():

        st.warning(
            "⚠️ Please paste the target job description."
        )

    else:

        with st.spinner(
            "🤖 AI Recruiter is reviewing your resume..."
        ):

            temp_path = None

            try:

                # -----------------------------------------
                # Temporary PDF
                # -----------------------------------------

                with tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=".pdf"
                ) as temp_file:

                    temp_file.write(
                        resume_file.getvalue()
                    )

                    temp_path = temp_file.name

                # -----------------------------------------
                # Upload Resume to Gemini
                # -----------------------------------------

                uploaded_resume = client.files.upload(
                    file=temp_path
                )

                # -----------------------------------------
                # Recruiter Prompt
                # -----------------------------------------

                prompt = f"""
You are an expert technical recruiter and ATS resume reviewer.

Your job is to critically evaluate the uploaded resume against
the target job description.

Be specific, practical, honest and recruiter-focused.

TARGET JOB DESCRIPTION:
{job_description}

Return ONLY valid JSON using exactly this structure:

{{
    "match_score": 0,

    "strengths": [
        "strength 1",
        "strength 2",
        "strength 3"
    ],

    "missing_keywords": [
        "keyword 1",
        "keyword 2",
        "keyword 3"
    ],

    "weak_areas": [
        "weak area 1",
        "weak area 2",
        "weak area 3"
    ],

    "skill_gaps": [
        "skill gap 1",
        "skill gap 2",
        "skill gap 3"
    ],

    "improved_bullets": [
        "improved bullet 1",
        "improved bullet 2",
        "improved bullet 3"
    ],

    "ats_tips": [
        "ATS tip 1",
        "ATS tip 2",
        "ATS tip 3"
    ],

    "recruiter_verdict":
        "A concise recruiter verdict"
}}

Rules:

- match_score must be an integer from 0 to 100.
- Do not invent experience, education or skills.
- Missing keywords must come from the job description.
- Improved bullets must remain truthful to the resume.
- Do not recommend fake achievements.
- Keep the recruiter verdict concise.
"""

                # -----------------------------------------
                # Gemini
                # -----------------------------------------

                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[
                        uploaded_resume,
                        prompt
                    ]
                )

                result_text = response.text.strip()

                # -----------------------------------------
                # Clean JSON response
                # -----------------------------------------

                result_text = (
                    result_text
                    .replace("```json", "")
                    .replace("```", "")
                    .strip()
                )

                analysis = json.loads(result_text)

                st.session_state.analysis = analysis

            except json.JSONDecodeError:

                st.error(
                    "⚠️ AI returned an unexpected format. "
                    "Please try analyzing again."
                )

            except Exception as e:

                st.error(
                    f"⚠️ Something went wrong: {e}"
                )

            finally:

                if temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)

# =========================================================
# RESULTS
# =========================================================
if st.session_state.analysis:

    data = st.session_state.analysis

    st.divider()

    st.markdown(
        '<p class="section-title">📊 Resume Analysis Dashboard</p>',
        unsafe_allow_html=True
    )

    score = int(data.get("match_score", 0))

    strengths = data.get("strengths", [])
    keywords = data.get("missing_keywords", [])
    weak_areas = data.get("weak_areas", [])
    skill_gaps = data.get("skill_gaps", [])

    # =====================================================
    # KPI CARDS
    # =====================================================

    c1, c2, c3, c4 = st.columns(4)

    with c1:

        st.metric(
            "🎯 Job Match",
            f"{score}%"
        )

    with c2:

        st.metric(
            "💪 Strengths",
            len(strengths)
        )

    with c3:

        st.metric(
            "🔑 Missing Keywords",
            len(keywords)
        )

    with c4:

        st.metric(
            "⚠️ Weak Areas",
            len(weak_areas)
        )

    st.progress(
        max(0, min(score, 100)) / 100
    )

    # =====================================================
    # OVERVIEW
    # =====================================================

    st.subheader("📌 Quick Overview")

    if score >= 80:
        st.success(
            "🟢 Strong match — your resume aligns well "
            "with this job."
        )

    elif score >= 60:
        st.warning(
            "🟡 Moderate match — some improvements "
            "could strengthen your application."
        )

    else:
        st.error(
            "🔴 Low match — significant optimization "
            "may be needed."
        )

    # =====================================================
    # TWO COLUMN ANALYSIS
    # =====================================================

    left, right = st.columns(2)

    with left:

        st.subheader("💪 Resume Strengths")

        if strengths:

            for item in strengths:
                st.success(f"✓ {item}")

        else:

            st.info("No major strengths identified.")

    with right:

        st.subheader("🔑 Missing Keywords")

        if keywords:

            for keyword in keywords:

                st.markdown(
                    f'<span class="keyword">{keyword}</span>',
                    unsafe_allow_html=True
                )

        else:

            st.success(
                "No major missing keywords detected."
            )

    # =====================================================
    # WEAK AREAS
    # =====================================================

    with st.expander(
        "⚠️ Weak Areas & Resume Issues",
        expanded=True
    ):

        if weak_areas:

            for item in weak_areas:
                st.warning(f"• {item}")

        else:

            st.success(
                "No major weaknesses identified."
            )

    # =====================================================
    # SKILL GAPS
    # =====================================================

    with st.expander(
        "🎯 Skill Gaps"
    ):

        if skill_gaps:

            for item in skill_gaps:
                st.write(f"• {item}")

        else:

            st.success(
                "No significant skill gaps detected."
            )

    # =====================================================
    # IMPROVED BULLETS
    # =====================================================

    with st.expander(
        "✍️ AI-Improved Resume Bullet Points"
    ):

        for index, item in enumerate(
            data.get("improved_bullets", []),
            start=1
        ):

            st.markdown(
                f"**{index}.** {item}"
            )

    # =====================================================
    # ATS TIPS
    # =====================================================

    with st.expander(
        "🤖 ATS Optimization Tips"
    ):

        for item in data.get("ats_tips", []):

            st.write(f"✓ {item}")

    # =====================================================
    # RECRUITER VERDICT
    # =====================================================

    st.subheader("👔 Recruiter Verdict")

    st.info(
        data.get(
            "recruiter_verdict",
            "No verdict available."
        )
    )
        # =====================================================
    # DOWNLOAD ANALYSIS
    # =====================================================

    st.subheader("📥 Download Your Analysis")

    download_text = f"""
AI RESUME CRITIC
================

JOB MATCH SCORE: {score}%

RESUME STRENGTHS
---------------
{chr(10).join("- " + item for item in strengths)}

MISSING KEYWORDS
----------------
{chr(10).join("- " + item for item in keywords)}

WEAK AREAS
----------
{chr(10).join("- " + item for item in weak_areas)}

SKILL GAPS
----------
{chr(10).join("- " + item for item in skill_gaps)}

IMPROVED RESUME BULLETS
-----------------------
{chr(10).join("- " + item for item in data.get("improved_bullets", []))}

ATS OPTIMIZATION TIPS
---------------------
{chr(10).join("- " + item for item in data.get("ats_tips", []))}

RECRUITER VERDICT
-----------------
{data.get("recruiter_verdict", "")}

Generated by AI Resume Critic
"""

    st.download_button(
        label="📄 Download Analysis",
        data=download_text,
        file_name="resume_analysis.txt",
        mime="text/plain",
        use_container_width=True
    )

    # =====================================================
    # FOOTER
    # =====================================================

    st.divider()

    st.caption(
        "AI Resume Critic • Streamlit + Gemini AI"
    )