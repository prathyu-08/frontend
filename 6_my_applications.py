import streamlit as st
import requests
from auth import require_login, auth_headers, logout

API_BASE = "http://localhost:8000"

st.set_page_config(page_title="My Applications", layout="wide")
require_login()

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.markdown("### 👤 Candidate Panel")
    if st.button("🚪 Logout"):
        logout()

st.title("📌 My Applications")
st.caption("Track the status of jobs you have applied for")

# ---------------- FETCH APPLICATIONS ----------------
apps_res = requests.get(
    f"{API_BASE}/applications/my",
    headers=auth_headers(),
)

if apps_res.status_code != 200:
    st.error("❌ Failed to load applications")
    st.write(apps_res.text)
    st.stop()

applications = apps_res.json()


if not applications:
    st.info("You haven’t applied for any jobs yet.")
    st.stop()

# ---------------- DISPLAY APPLICATIONS ----------------
STATUS_COLORS = {
    "applied": "#e5e7eb",
    "shortlisted": "#fef3c7",
    "interview": "#dbeafe",
    "offered": "#dcfce7",
    "rejected": "#fee2e2",
}

for app in applications:
    raw_status = str(app.get("status", "applied")).lower()
    raw_status = raw_status.replace("applicationstatus.", "").strip()

    status_label = raw_status.replace("_", " ").title()
    bg_color = STATUS_COLORS.get(raw_status, "#e5e7eb")

    st.markdown(
        f"""
        <div style="
            padding:14px;
            border-radius:14px;
            border:1px solid #e5e7eb;
            background:{bg_color};
            margin-bottom:12px;
        ">
            <h4>📌 {app.get("job_title", "Job")}</h4>
            <p>🏢 {app.get("company_name", "-")}</p>
            <p>🕒 Applied on: {app.get("applied_at", "-")}</p>
            <strong>📍 Status: {status_label}</strong>
        </div>
        """,
        unsafe_allow_html=True
    )
