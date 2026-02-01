import streamlit as st
import requests

from auth import require_role, auth_headers
from layout import render_sidebar

# =================================================
# CONFIG
# ==================================================
API_BASE = "http://localhost:8000"



st.session_state.setdefault("applied_jobs", set())
# ==================================================
# PAGE SETUP
# ==================================================
st.set_page_config(page_title="Job Listings", layout="wide")
require_role("user")
render_sidebar()

st.title("💼 Job Opportunities")
st.caption("Search and apply for jobs")



# ---------------- SUCCESS MESSAGE ----------------
if st.session_state.get("application_success"):
    st.success("🎉 Application submitted successfully!")
    st.session_state.application_success = False
# ==================================================
# SESSION STATE
# ==================================================
st.session_state.setdefault("apply_job_id", None)

# ==================================================
# FILTERS
# ==================================================
col1, col2, col3 = st.columns(3)

with col1:
    keyword = st.text_input("🔍 Job Title")

with col2:
    location = st.text_input("📍 Location")

with col3:
    min_experience = st.number_input(
        "💼 Min Experience", 0.0, 50.0, 0.0, 0.5
    )

# ==================================================
# FETCH JOBS
# ==================================================
def fetch_jobs():
    params = {}
    if keyword:
        params["keyword"] = keyword
    if location:
        params["location"] = location
    if min_experience > 0:
        params["min_experience"] = min_experience

    res = requests.get(
        f"{API_BASE}/jobs/search",
        headers=auth_headers(),
        params=params,
    )

    if res.status_code != 200:
        st.error("Failed to load jobs")
        return []

    return res.json()

jobs = fetch_jobs()
st.divider()

if not jobs:
    st.info("No jobs found")
    st.stop()

# ==================================================
# JOB LISTINGS
# ==================================================
for job in jobs:
    job_id = job["job_id"]

    with st.container():
        # ---------------- JOB CARD ----------------
        st.markdown(
            f"""
            <div style="border:1px solid #ddd;padding:16px;border-radius:10px;">
                <h4>{job['title']}</h4>
                <p><b>{job['company_name']}</b></p>
                <p>📍 {job.get('location', 'N/A')}</p>
                <p>💼 {job.get('min_experience')} – {job.get('max_experience')} yrs</p>
                <p>💰 ₹{job.get('salary_min')} – ₹{job.get('salary_max')} LPA</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ---------------- JOB DESCRIPTION (TEXT) ----------------
        if job.get("description"):
            description_text = job["description"].strip()
            if description_text:
                with st.expander("📄 Job Description (Text)"):
                    st.write(description_text)

        # ---------------- JOB DESCRIPTION (PDF) ----------------
        if job.get("description_file_key"):
            jd_res = requests.get(
                f"{API_BASE}/job-descriptions/file/{job['description_file_key']}",
                headers=auth_headers(),
            )

            if jd_res.status_code == 200:
                st.link_button(
                    "📄 View Job Description (PDF)",
                    jd_res.json()["url"],
                )

        if job_id in st.session_state.applied_jobs:
            st.button("✅ Applied", disabled=True, key=f"applied_{job_id}")
        else:
            if st.button("📩 Apply", key=f"apply_{job_id}"):
                st.session_state.apply_job_id = job_id
                st.switch_page("pages/job_application_form.py")

        st.divider()
