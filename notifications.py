import streamlit as st
import requests
from auth import require_login, auth_headers
from layout import render_sidebar

API_BASE = "http://localhost:8000"
require_login()
render_sidebar()
st.title("🔔 Notifications")

res = requests.get(
    f"{API_BASE}/notifications",
    headers=auth_headers()
)

if res.status_code != 200:
    st.error("Failed to load notifications")
    st.stop()

notifications = res.json()

if not notifications:
    st.info("No notifications yet")
else:
    for n in notifications:
        st.markdown(f"### {n['title']}")
        st.write(n["message"])
        st.caption(n["created_at"])
        st.divider()