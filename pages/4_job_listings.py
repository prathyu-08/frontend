import streamlit as st
import requests
from auth import require_login, auth_headers, logout

API_BASE = "http://localhost:8000"

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(page_title="Job Listings", layout="wide")
require_login()

# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------
with st.sidebar:
    st.markdown("### 👤 Account")
    if st.button("🚪 Logout"):
        logout()

# --------------------------------------------------
# PAGE HEADER
# --------------------------------------------------
st.title("💼 Job Opportunities")
st.caption("Search and apply for jobs")

# --------------------------------------------------
# FILTERS
# --------------------------------------------------
col1, col2, col3 = st.columns(3)

with col1:
    keyword = st.text_input("🔍 Job Title")

with col2:
    location = st.text_input("📍 Location")

with col3:
    min_experience = st.number_input(
        "💼 Min Experience", 0.0, 50.0, 0.0, 0.5
    )

# --------------------------------------------------
# FETCH JOBS
# --------------------------------------------------
def fetch_jobs():
    params = {}
    if keyword:
        params["keyword"] = keyword
    if location:
        params["location"] = location
    if min_experience > 0:
        params["min_experience"] = min_experience

    res = requests.get(
        f"{API_BASE}/candidate/jobs",
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

# --------------------------------------------------
# FETCH PRIMARY RESUME
# --------------------------------------------------
resumes_res = requests.get(
    f"{API_BASE}/resume/my-resumes",
    headers=auth_headers(),
)

primary_resume_id = None

if resumes_res.status_code == 200:
    resumes = resumes_res.json().get("resumes", [])
    for r in resumes:
        if r.get("is_primary"):
            primary_resume_id = r.get("resume_id")
            break

# --------------------------------------------------
# JOB LIST + APPLY FORM
# --------------------------------------------------
# --------------------------------------------------
# JOB LIST + APPLY FORM
# --------------------------------------------------
for job in jobs:
    with st.container():

        # ---------- JOB CARD ----------
        st.markdown(
            f"""
            <div style="
                border:1px solid #e5e7eb;
                padding:18px;
                border-radius:14px;
                background:#ffffff;
                margin-bottom:10px;
            ">
                <h4>{job['title']}</h4>
                <p><b>{job['company_name']}</b></p>
                <p>📍 {job['location']}</p>
                <p>💼 {job['min_experience']} – {job['max_experience']} yrs</p>
                <p>💰 ₹{job['salary_min']} – ₹{job['salary_max']} LPA</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ==================================================
        # JOB DESCRIPTION
        # ==================================================
        with st.expander("📄 View Job Description"):

            description = job.get("description")

            # 📝 TEXT JD
            if description and description.strip():
                st.markdown(description)

            # 📎 FILE JD
            elif job.get("description_file_key"):
                jd_res = requests.get(
                    f"{API_BASE}/job-descriptions/file/{job['description_file_key']}",
                    headers=auth_headers(),
                )

                if jd_res.status_code == 200:
                    jd_url = jd_res.json().get("url")
                    st.markdown(
                        f"🔗 [Click here to view Job Description (PDF)]({jd_url})",
                        unsafe_allow_html=True,
                    )
                else:
                    st.warning("Job description file not available")

            else:
                st.info("No job description provided")

        # ==================================================
        # APPLY BUTTON
        # ==================================================
        if st.button("✅ Apply", key=f"apply_{job['job_id']}"):
            st.session_state["apply_job_id"] = job["job_id"]

        # ==================================================
        # APPLICATION FORM
        # ==================================================
        if st.session_state.get("apply_job_id") == job["job_id"]:
            with st.form(f"apply_form_{job['job_id']}"):

                cover_note = st.text_area(
                    "Why should we hire you? *"
                )
                relevant_experience = st.text_input(
                    "Relevant Experience *"
                )
                availability = st.text_input(
                    "Availability / Notice Period *"
                )

                submit = st.form_submit_button("📤 Submit Application")

                if submit:
                    if not cover_note.strip():
                        st.error("Cover note is required")
                    elif not relevant_experience.strip():
                        st.error("Relevant experience is required")
                    elif not availability.strip():
                        st.error("Availability is required")
                    else:
                        payload = {
                            "job_id": job["job_id"],
                            "cover_note": cover_note,
                            "relevant_experience": relevant_experience,
                            "availability": availability,
                        }

                        res = requests.post(
                            f"{API_BASE}/applications/apply",
                            json=payload,
                            headers=auth_headers(),
                        )

                        if res.status_code == 200:
                            st.success("✅ Application submitted successfully")
                            del st.session_state["apply_job_id"]
                            st.rerun()
                        else:
                            st.error(res.text)

        st.divider()


        # ==================================================
# JOB DESCRIPTION (TEXT OR FILE)
# ==================================================
with st.expander("📄 View Job Description"):

    # ✅ PRIORITY 1: PDF JD
    if job.get("description_file_key"):
        jd_res = requests.get(
            f"{API_BASE}/job-descriptions/file/{job['description_file_key']}",
            headers=auth_headers(),
        )

        if jd_res.status_code == 200:
            jd_url = jd_res.json().get("url")

            st.markdown(
                f"🔗 **[Click here to view Job Description (PDF)]({jd_url})**",
                unsafe_allow_html=True,
            )
        else:
            st.warning("Job description file not available")

    # 📝 PRIORITY 2: TEXT JD
    elif job.get("description"):
        st.markdown(job["description"])

    else:
        st.info("No job description provided")



        # -------- APPLY BUTTON --------
        if st.button("✅ Apply", key=f"apply_{job['job_id']}"):
            st.session_state["apply_job_id"] = job["job_id"]

        # -------- APPLICATION FORM --------
        if st.session_state.get("apply_job_id") == job["job_id"]:
            with st.form(f"apply_form_{job['job_id']}"):
                cover_note = st.text_area("Why should we hire you? *")
                relevant_experience = st.text_input("Relevant Experience *")
                availability = st.text_input("Availability / Notice Period *")

                submit = st.form_submit_button("Submit Application")

                if submit:
                    if not cover_note or not relevant_experience or not availability:
                        st.error("All fields are mandatory")
                    else:
                        payload = {
                            "job_id": job["job_id"],
                            "cover_note": cover_note,
                            "relevant_experience": relevant_experience,
                            "availability": availability,
                        }

                        res = requests.post(
                            f"{API_BASE}/applications/apply",
                            json=payload,
                            headers=auth_headers(),
                        )

                        if res.status_code == 200:
                            st.success("✅ Application submitted")
                            del st.session_state["apply_job_id"]
                        else:
                            st.error(res.text)

        st.divider()
