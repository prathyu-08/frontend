import streamlit as st
import requests
from datetime import datetime
from auth import require_login, auth_headers, logout

# ==================================================
# CONFIG
# ==================================================
API_BASE = "http://localhost:8000"

APPLICATION_STATUSES = [
    "applied",
    "shortlisted",
    "interview",
    "offered",
    "rejected",
]

STATUS_ICONS = {
    "applied": "🟡",
    "shortlisted": "🟢",
    "interview": "🔵",
    "offered": "🟣",
    "rejected": "🔴",
}

st.set_page_config(page_title="Recruiter Dashboard", layout="wide")
require_login()

# ==================================================
# SIDEBAR
# ==================================================
with st.sidebar:
    st.markdown("### 🧑‍💼 Recruiter Panel")
    if st.button("🚪 Logout"):
        logout()

st.title("🧑‍💼 Recruiter Dashboard")
st.caption("Recruitment management + platform analytics")
st.divider()

# ==================================================
# 📊 PLATFORM ANALYTICS
# ==================================================
st.header("📊 Platform Analytics")


def fetch_admin_data(endpoint):
    res = requests.get(f"{API_BASE}{endpoint}", headers=auth_headers())
    if res.status_code != 200:
        return None
    return res.json()


apps_per_job = fetch_admin_data("/admin/applications-per-job")
status_summary = fetch_admin_data("/admin/application-status-summary")
recent_resumes = fetch_admin_data("/admin/recent-resumes")
upcoming_interviews = fetch_admin_data("/admin/upcoming-interviews")
job_performance = fetch_admin_data("/admin/job-performance")

col1, col2, col3 = st.columns(3)
col1.metric("Total Jobs", len(apps_per_job) if apps_per_job else 0)
col2.metric(
    "Total Applications",
    sum(j["applications"] for j in apps_per_job) if apps_per_job else 0,
)
col3.metric(
    "Active Status Types",
    len(status_summary) if status_summary else 0,
)

# ---------------- STATUS SUMMARY ----------------
st.subheader("📌 Applications by Status")
if status_summary:
    status_chart_data = [
        {"status": k, "count": v}
        for k, v in status_summary.items()
    ]
    st.bar_chart(status_chart_data)
else:
    st.info("No status data available")

# ---------------- APPLICATIONS PER JOB ----------------
st.subheader("💼 Applications per Job")
if apps_per_job:
    st.table(apps_per_job)
else:
    st.info("No job application data")

# ---------------- JOB PERFORMANCE ----------------
st.subheader("📈 Job Performance")
if job_performance:
    st.table(job_performance)
else:
    st.info("No job performance data")

# ---------------- UPCOMING INTERVIEWS ----------------
st.subheader("📅 Upcoming Interviews")
if upcoming_interviews:
    st.table(upcoming_interviews)
else:
    st.info("No upcoming interviews")

# ---------------- RECENT RESUMES ----------------
st.subheader("📄 Recently Uploaded Resumes")
if recent_resumes:
    st.table(recent_resumes)
else:
    st.info("No recent resumes")

st.divider()

# ==================================================
# ➕ POST JOB
# ==================================================
st.header("➕ Post a New Job")

with st.form("post_job_form", clear_on_submit=True):
    col1, col2 = st.columns(2)

    with col1:
        title = st.text_input("Job Title *")
        location = st.text_input("Location")
        employment_type = st.selectbox(
            "Employment Type",
            ["Full-time", "Part-time", "Contract", "Internship"],
        )

    with col2:
        min_exp = st.number_input("Min Experience (Years)", 0.0, 30.0, 0.0, 0.5)
        max_exp = st.number_input("Max Experience (Years)", 0.0, 30.0, 5.0, 0.5)

    s1, s2 = st.columns(2)
    with s1:
        salary_min = st.number_input("Salary Min (₹ LPA)", 0.0, step=0.5)
    with s2:
        salary_max = st.number_input("Salary Max (₹ LPA)", 0.0, step=0.5)

    description = st.text_area("Job Description *", height=150)
    publish = st.form_submit_button("🚀 Publish Job")

    if publish:
        if not title or not description:
            st.error("Job title and description are required")
        else:
            payload = {
                "title": title,
                "description": description,
                "location": location,
                "min_experience": min_exp,
                "max_experience": max_exp,
                "salary_min": salary_min,
                "salary_max": salary_max,
                "employment_type": employment_type,
            }

            res = requests.post(
                f"{API_BASE}/jobs/",
                headers=auth_headers(),
                json=payload,
            )

            if res.status_code == 201:
                st.success("✅ Job posted successfully")
                st.rerun()
            else:
                st.error(res.text)

st.divider()

# ==================================================
# 📌 MY JOBS
# ==================================================
st.header("📌 My Job Postings")

jobs_res = requests.get(f"{API_BASE}/jobs/my", headers=auth_headers())
if jobs_res.status_code != 200:
    st.error("Failed to load jobs")
    st.stop()

jobs = jobs_res.json()
job_map = {job["title"]: job["job_id"] for job in jobs}

if not job_map:
    st.info("No jobs posted yet.")
    st.stop()

selected_job = st.selectbox("Select Job", list(job_map.keys()))
job_id = job_map[selected_job]

# ==================================================
# 👥 CANDIDATES
# ==================================================
st.header("👥 Candidates")

apps_res = requests.get(
    f"{API_BASE}/applications/job/{job_id}",
    headers=auth_headers(),
)

if apps_res.status_code != 200:
    st.error("Failed to load candidates")
    st.stop()

applications = apps_res.json()
if not applications:
    st.info("No candidates have applied yet.")
    st.stop()

for app in applications:
    with st.container():
        col1, col2, col3 = st.columns([4, 3, 4])

        with col1:
            status = app.get("status", "applied")
            icon = STATUS_ICONS.get(status, "⚪")
            st.markdown(f"**{icon} {app.get('candidate_name', 'Unknown')}**")
            st.caption(f"📌 Status: {status.title()}")
            st.write(f"📧 {app.get('candidate_email', '-')}")
            st.write(f"📞 {app.get('candidate_phone', '-')}")

        with col2:
            st.write("🕒 Applied on")
            st.write(app.get("applied_at", "-"))

        with col3:
            status_index = (
                APPLICATION_STATUSES.index(status)
                if status in APPLICATION_STATUSES else 0
            )

            new_status = st.selectbox(
                "Update Status",
                APPLICATION_STATUSES,
                index=status_index,
                key=f"status_{app['application_id']}",
            )

            if st.button("💾 Save", key=f"save_{app['application_id']}"):
                res = requests.put(
                    f"{API_BASE}/applications/{app['application_id']}/status",
                    headers=auth_headers(),
                    params={"status": new_status},
                )

                if res.status_code == 200:
                    st.success("Status updated")
                    st.rerun()
                else:
                    st.error(res.text)

            if st.button("👁️ View Profile", key=f"view_{app['application_id']}"):
                res = requests.get(
                    f"{API_BASE}/applications/{app['application_id']}/candidate",
                    headers=auth_headers(),
                )

                if res.status_code == 200:
                    cand = res.json()
                    with st.expander(f"Profile: {cand.get('full_name','Candidate')}", expanded=True):
                        st.write(f"✉️ {cand.get('email', '-')}")
                        st.write(f"📍 {cand.get('current_location', '-')}")
                        exp = cand.get('total_experience')
                        st.write(f"💼 {exp} years" if exp else "💼 Fresher")
                        summary = cand.get('profile_summary')
                        if summary:
                            st.markdown(summary)
                        else:
                            st.info("No profile summary")

                        st.subheader("Education")
                        educations = cand.get('educations', []) or []
                        if educations:
                            for e in educations:
                                st.markdown(f"**{e.get('degree','')}**, {e.get('institution','')} — {e.get('start_year','')}–{e.get('end_year','')}")
                        else:
                            st.write("No education records")

                        st.subheader("Experience")
                        experiences = cand.get('experiences', []) or []
                        if experiences:
                            for ex in experiences:
                                st.markdown(f"**{ex.get('role','')}** at {ex.get('company_name','')} — {ex.get('start_date','')} to {ex.get('end_date','')}")
                        else:
                            st.write("No experience records")

                        st.subheader("Skills")
                        skills = cand.get('skills', []) or []
                        if skills:
                            for s in skills:
                                st.write(f"- {s.get('skill_name','Unknown')} ({s.get('proficiency','')}, {s.get('years_of_experience','0')} yrs)")
                        else:
                            st.write("No skills listed")

                else:
                    st.error(res.text)

        # ==================================================
        # 📅 SCHEDULE INTERVIEW
        # ==================================================
        st.markdown("#### 📅 Schedule Interview")

        interview_date = st.date_input(
            "Interview Date",
            key=f"date_{app['application_id']}"
        )

        interview_time = st.time_input(
            "Interview Time",
            key=f"time_{app['application_id']}"
        )

        meeting_link = st.text_input(
            "Meeting Link",
            placeholder="https://meet.google.com/...",
            key=f"meet_{app['application_id']}"
        )

        if st.button("📌 Schedule Interview", key=f"schedule_{app['application_id']}"):
            scheduled_at = datetime.combine(interview_date, interview_time)

            res = requests.post(
                f"{API_BASE}/interviews/schedule",
                headers=auth_headers(),
                json={
                    "application_id": app["application_id"],  # UUID (correct)
                    "scheduled_at": scheduled_at.isoformat(),
                    "meeting_link": meeting_link,
                },
            )

            if res.status_code == 200:
                st.success("Interview scheduled successfully")
                st.rerun()
            else:
                st.error(res.text)

        st.divider()
