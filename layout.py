import streamlit as st
import os
from auth import get_current_user, logout


def render_sidebar():
    user = get_current_user()
    if not user:
        return

    # Respect sidebar visibility toggle
    if not st.session_state.get("show_sidebar", True):
        return

    role = user.get("role")
    logo_path = os.path.join("assets", "nmk_logo.png")

    if os.path.exists(logo_path):
            st.image(logo_path, width=180)

    with st.sidebar:
        # --------------------------------------------------
        # LOGO
        # --------------------------------------------------
        st.image(logo_path, use_container_width=True)
        st.markdown("---")

        # --------------------------------------------------
        # USER DASHBOARD
        # --------------------------------------------------
        if role == "user":
            st.markdown("## 👤 User Dashboard")

            if st.button("👤 Profile", use_container_width=True):
                st.switch_page("pages/3_candidate_profile.py")
                
            if st.button("👤 Profile analytics", use_container_width=True):
                st.switch_page("pages/7_profile_analytics.py")


            if st.button("💼 Jobs search", use_container_width=True):
                st.switch_page("pages/4_job_listings.py")

            if st.button("📄 Resumes", use_container_width=True):
                st.switch_page("pages/5_resume_upload.py")

            if st.button("📌 My Applications", use_container_width=True):
                st.switch_page("pages/6_my_applications.py")

            if st.button("🔔 Notifications", use_container_width=True):
                st.switch_page("pages/notifications.py")

        # --------------------------------------------------
        # RECRUITER DASHBOARD
        # --------------------------------------------------
        elif role == "recruiter":
            st.markdown("## 🧑‍💼 Recruiter Dashboard")
            if st.button("job posting", use_container_width=True):
                st.switch_page("pages/recruiter_dashboard.py")
            if st.button("application form", use_container_width=True):
                st.switch_page("pages/recruiter_application_form.py")
            if st.button("Recruiter Analytics", use_container_width=True):
                st.switch_page("pages/recruiter_analytics.py")
            
            


            
        # --------------------------------------------------
        # LOGOUT
        # --------------------------------------------------
        st.divider()

        if st.button("🚪 Logout", use_container_width=True):
            logout()