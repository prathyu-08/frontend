import streamlit as st
import requests
from auth import require_login, auth_headers, logout

API_BASE = "http://localhost:8000"

st.set_page_config(page_title="Admin Dashboard", layout="wide")
require_login()

# ==================================================
# SIDEBAR
# ==================================================
with st.sidebar:
    st.markdown("### 🛡 Admin Panel")
    if st.button("🚪 Logout"):
        logout()

st.title("📊 Admin Dashboard")
st.caption("Platform analytics & monitoring")
st.divider()


# ==================================================
# FETCH DATA
# ==================================================
def get_data(endpoint):
    res = requests.get(
        f"{API_BASE}{endpoint}",
        headers=auth_headers(),
    )
    if res.status_code != 200:
        st.error(res.text)
        return None
    return res.json()


apps_per_job = get_data("/admin/applications-per-job")
status_summary = get_data("/admin/application-status-summary")
upcoming_interviews = get_data("/admin/upcoming-interviews")
recent_resumes = get_data("/admin/recent-resumes")
job_performance = get_data("/admin/job-performance")


# ==================================================
# METRICS
# ==================================================
col1, col2, col3 = st.columns(3)

col1.metric(
    "Total Jobs",
    len(apps_per_job) if apps_per_job else 0
)
col2.metric(
    "Total Applications",
    sum(j["applications"] for j in apps_per_job) if apps_per_job else 0
)
col3.metric(
    "Active Status Types",
    len(status_summary) if status_summary else 0
)

st.divider()


# ==================================================
# APPLICATION STATUS SUMMARY
# ==================================================
st.subheader("📌 Applications by Status")
if status_summary:
    st.bar_chart(status_summary)
else:
    st.info("No data available")


# ==================================================
# APPLICATIONS PER JOB
# ==================================================
st.subheader("💼 Applications per Job")
if apps_per_job:
    st.table(apps_per_job)
else:
    st.info("No job data available")


# ==================================================
# JOB PERFORMANCE
# ==================================================
st.subheader("📈 Job Performance")
if job_performance:
    st.table(job_performance)
else:
    st.info("No performance data")


# ==================================================
# UPCOMING INTERVIEWS
# ==================================================
st.subheader("📅 Upcoming Interviews")
if upcoming_interviews:
    st.table(upcoming_interviews)
else:
    st.info("No upcoming interviews")


# ==================================================
# RECENT RESUMES
# ==================================================
st.subheader("📄 Recently Uploaded Resumes")
if recent_resumes:
    st.table(recent_resumes)
else:
    st.info("No recent resumes")
