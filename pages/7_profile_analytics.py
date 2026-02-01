import streamlit as st
import requests
import matplotlib.pyplot as plt
from auth import require_login, auth_headers
import os
from dotenv import load_dotenv
from layout import render_sidebar
# -------------------------------------------------
# CONFIG
# -------------------------------------------------
load_dotenv()
API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")

st.set_page_config(
    page_title="My Analytics",
    layout="wide",
    page_icon="📊"
)

# -------------------------------------------------
# AUTH
# -------------------------------------------------
require_login()
render_sidebar()
role = st.session_state.get("role")
if role != "user":
    st.error("❌ Analytics is only available for candidates.")
    st.stop()

# -------------------------------------------------
# HEADER
# -------------------------------------------------
st.title("📊 My Application Analytics")
st.caption("Track your job applications and progress")

# -------------------------------------------------
# FETCH ANALYTICS
# -------------------------------------------------
@st.cache_data(ttl=120)
def fetch_analytics():
    res = requests.get(
        f"{API_BASE}/candidate/profile-analytics",
        headers=auth_headers(),
        timeout=10
    )
    if res.status_code != 200:
        return None
    return res.json()

data = fetch_analytics()

if not data:
    st.error("Failed to load analytics data")
    st.stop()

# -------------------------------------------------
# TOP METRICS
# -------------------------------------------------
col1, col2, col3, col4 = st.columns(4)

col1.metric("👁️ Profile Views", data.get("profile_views", 0))
col2.metric("📨 Applications", data.get("total_applications", 0))
col3.metric("⭐ Profile Score", f"{data.get('profile_score', 0)}%")
col4.metric("💾 Saved Jobs", data.get("saved_jobs", 0))

st.divider()

# -------------------------------------------------
# APPLICATION STATUS PIE CHART
# -------------------------------------------------
st.subheader("🧩 Application Status Breakdown")

status_map = {
    "applied": "Applied",
    "viewed": "Viewed",
    "shortlisted": "Shortlisted",
    "interview": "Interview",
    "offered": "Offered",
    "rejected": "Rejected",
}

labels = []
sizes = []

for key, label in status_map.items():
    count = data.get("application_breakdown", {}).get(key, 0)
    if count > 0:
        labels.append(label)
        sizes.append(count)

if not sizes:
    st.info("No application activity yet.")
else:
    fig, ax = plt.subplots()
    ax.pie(
        sizes,
        labels=labels,
        autopct="%1.1f%%",
        startangle=90,
        wedgeprops={"edgecolor": "white"},
    )
    ax.axis("equal")
    st.pyplot(fig)

st.divider()

# -------------------------------------------------
# APPLICATION STATUS TABLE
# -------------------------------------------------
st.subheader("📋 Detailed Status Count")

table_data = []
for key, label in status_map.items():
    table_data.append({
        "Status": label,
        "Count": data.get("application_breakdown", {}).get(key, 0)
    })

st.table(table_data)

st.divider()