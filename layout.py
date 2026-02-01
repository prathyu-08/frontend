import streamlit as st
import os
from auth import get_current_user, logout


def render_sidebar(page: str = "default"):
    """
    page: unique page name (e.g. 'candidate', 'recruiter_dashboard')
    used to namespace Streamlit keys safely
    """

    user = get_current_user()

    # 🔒 Do not render sidebar if user not logged in
    if not user:
        return

    role = user.get("role")
    key_prefix = f"sb_{page}_"

    with st.sidebar:
        # ======================
        # LOGO
        # ======================
        BASE_DIR = os.path.dirname(__file__)
        logo_path = os.path.join(BASE_DIR, "assets", "nmk_logo.png")

        if os.path.exists(logo_path):
            st.image(logo_path, width=160)

        st.markdown("---")

        # ======================
        # CANDIDATE SIDEBAR
        # ======================
        if role == "user":
            st.markdown("### 👤 Candidate Panel")

            if st.button("👤 Profile", use_container_width=True, key=key_prefix + "profile"):
                st.switch_page("pages/3_candidate_profile.py")

            if st.button("💼 Job Listings", use_container_width=True, key=key_prefix + "jobs"):
                st.switch_page("pages/4_job_listings.py")

            if st.button("📄 Resumes", use_container_width=True, key=key_prefix + "resumes"):
                st.switch_page("pages/5_resume_upload.py")

            if st.button("📌 My Applications", use_container_width=True, key=key_prefix + "applications"):
                st.switch_page("pages/6_my_applications.py")

            if st.button("🔔 Notifications", use_container_width=True, key=key_prefix + "notifications"):
                st.switch_page("pages/notifications.py")


        # ======================
        # RECRUITER SIDEBAR
        # ======================
        elif role == "recruiter":
            st.markdown("### 🧑‍💼 Recruiter Panel")

            if st.button("📊 Dashboard", use_container_width=True, key=key_prefix + "dashboard"):
                st.switch_page("pages/recruiter_dashboard.py")

            if st.button("➕ Post Job", use_container_width=True, key=key_prefix + "post_job"):
                st.switch_page("pages/recruiter_dashboard.py")

            if st.button("📈 Analytics", use_container_width=True, key=key_prefix + "analytics"):
                st.switch_page("pages/recruiter_analytics.py")

        st.markdown("---")

        # ======================
        # LOGOUT
        # ======================
        if st.button("🚪 Logout", use_container_width=True, key=key_prefix + "logout"):
            logout()
