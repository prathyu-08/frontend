import streamlit as st
import requests
from auth import require_login, auth_headers, logout
from layout import render_sidebar
import pandas as pd
import plotly.express as px

# ==============================
# PAGE CONFIG
# ==============================
st.set_page_config(page_title="Recruiter Analytics", layout="wide")

st.markdown("""
<style>
[data-testid="stSidebar"] button {
    background-color: #FFA94D;
    color: white;
    border-radius: 8px;
    padding: 0.6rem;
    font-weight: 600;
    border: none;
}
[data-testid="stSidebar"] button:hover {
    background-color: #FF922B;
    color: white;
}
</style>
""", unsafe_allow_html=True)

st.title("📊 Recruiter Analytics")
st.caption("Platform analytics & monitoring")

require_login()
render_sidebar()

API_BASE = "http://localhost:8000"

# ==============================
# SAFE API CALL FUNCTION
# ==============================
def get_data(endpoint):
    try:
        res = requests.get(
            f"{API_BASE}{endpoint}",
            headers=auth_headers(),
        )
        if res.status_code == 200:
            return res.json()
        return None
    except Exception:
        return None


apps_per_job = get_data("/admin/recruiter/applications-per-job")
status_summary = get_data("/admin/application-status-summary")
upcoming_interviews = get_data("/admin/upcoming-interviews")
job_performance = get_data("/admin/job-performance")
candidates_needing_action = get_data("/admin/candidates-needing-action")

# ==============================
# TOP METRICS
# ==============================
col1, col2, col3 = st.columns(3)

total_jobs = len(apps_per_job) if apps_per_job else 0
total_apps = sum(j["applications"] for j in apps_per_job) if apps_per_job else 0
active_status = len(status_summary) if status_summary else 0

col1.metric("Total Jobs", total_jobs)
col2.metric("Total Applications", total_apps)
col3.metric("Active Status Types", active_status)

st.divider()

# ==============================
# HIRING PIPELINE ANALYTICS
# ==============================
st.subheader("🚀 Hiring Pipeline Overview")

if status_summary:

    PIPELINE_ORDER = ["applied", "shortlisted", "interview", "offered", "rejected"]

    normalized_summary = {
        str(k).lower(): v for k, v in status_summary.items()
    }

    applied = normalized_summary.get("applied", 0)
    shortlisted = normalized_summary.get("shortlisted", 0)
    interview = normalized_summary.get("interview", 0)
    offered = normalized_summary.get("offered", 0)
    rejected = normalized_summary.get("rejected", 0)

    pipeline_counts = [
        applied, shortlisted, interview, offered, rejected
    ]

    df = pd.DataFrame({
        "Status": PIPELINE_ORDER,
        "Count": pipeline_counts
    })

    # 🎨 Colors
    color_map = {
        "applied": "#F4C430",
        "shortlisted": "#95A5A6",
        "interview": "#3498DB",
        "offered": "#2ECC71",
        "rejected": "#E74C3C",
    }

    # 🔥 Clean Bar Chart (Counts Only)
    fig = px.bar(
        df,
        x="Status",
        y="Count",
        color="Status",
        color_discrete_map=color_map,
        text="Count"
    )

    fig.update_traces(
        textposition="inside"
    )

    fig.update_layout(
        showlegend=False,
        xaxis_title="Hiring Stage",
        yaxis_title="Number of Candidates"
    )

    st.plotly_chart(fig, use_container_width=True)

    # ==============================
    # KEY INSIGHTS (Counts Only)
    # ==============================
    st.markdown("### 📈 Key Hiring Insights")

    col1, col2, col3 = st.columns(3)

    col1.metric("📄 Total Shortlisted", shortlisted)
    col2.metric("🎯 Total Interviews", interview)
    col3.metric("🏆 Total Offers", offered)

else:
    st.info("No pipeline data available")

# ==============================
# APPLICATIONS PER JOB
# ==============================
st.subheader("💼 Applications per Job")

if apps_per_job:
    for job in apps_per_job:
        col1, col2 = st.columns([6, 2])

        with col1:
            if st.button(f"🔗 {job['job_title']}", key=f"job_link_{job['job_id']}"):
                st.session_state.selected_job_id = job["job_id"]
                st.session_state.open_job_from_analytics = True
                st.switch_page("pages/recruiter_dashboard.py")

        with col2:
            st.write(f"📄 Applications: {job['applications']}")
else:
    st.info("No job data available")

# ==============================
# UPCOMING INTERVIEWS
# ==============================
st.subheader("📅 Upcoming Interviews")

if upcoming_interviews:
    st.table(upcoming_interviews)
else:
    st.info("No upcoming interviews")

# ==============================
# CANDIDATES NEEDING ACTION
# ==============================
st.subheader("⏳ Hiring Actions Pending")
st.caption("Candidates pending or delayed in the hiring pipeline")

if candidates_needing_action:
    st.table(candidates_needing_action)
else:
    st.success("🎉 No candidates pending action")