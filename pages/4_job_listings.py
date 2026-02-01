import streamlit as st
import requests
from auth import require_login, require_role, auth_headers
from layout import render_sidebar

API_BASE = "http://localhost:8000"
def safe_error_message(res):
    try:
        data = res.json()
        if isinstance(data, dict):
            return data.get("detail", str(data))
        return str(data)
    except Exception:
        return res.text or f"HTTP {res.status_code}"


st.set_page_config(page_title="Job Listings", layout="wide")
require_login()
render_sidebar()



st.title("💼 Job Opportunities")
st.caption("Search and apply for jobs")

# ---------------- FILTERS ----------------
col1, col2, col3 = st.columns(3)

with col1:
    keyword = st.text_input("🔍 Job Title")

with col2:
    location = st.text_input("📍 Location")

with col3:
    min_experience = st.number_input(
        "💼 Min Experience", 0.0, 50.0, 0.0, 0.5
    )

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

# ---------------- JOB LIST ----------------
for job in jobs:
    with st.container():
        st.markdown(
            f"""
            <div style="border:1px solid #ddd;padding:16px;border-radius:10px;">
                <h4>{job['title']}</h4>
                <p><b>{job['company_name']}</b></p>
                <p>📍 {job.get('location')}</p>
                <p>💼 {job.get('min_experience')} – {job.get('max_experience')} yrs</p>
                <p>💰 ₹{job.get('salary_min')} – ₹{job.get('salary_max')} LPA</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("📩 Apply", key=f"apply_{job['job_id']}"):
            res = requests.post(
                f"{API_BASE}/applications/apply",
                headers=auth_headers(),
                params={"job_id": job["job_id"]},
            )

            if res.status_code == 200:
                st.success("Applied successfully ✅")
            else:
                st.error(res.json().get("detail", res.text))

        st.divider()
