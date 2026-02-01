import streamlit as st
import os
from auth import get_current_user, logout

def render_top_nav():
    user = get_current_user()
    if not user:
        return

    role = user.get("role")
    logo_path = os.path.join("assets", "nmk_logo.png")

    # -------------------------------
    # CSS for responsive navbar
    # -------------------------------
    st.markdown("""
        <style>
        /* Remove default padding */
        .block-container {
            padding-top: 0.5rem;
        }

        /* Top nav wrapper */
        .top-nav {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 10px 24px;
            background: white;
            border-bottom: 1px solid #e0e0e0;
            flex-wrap: wrap;
        }

        /* Nav items */
        .nav-items {
            display: flex;
            gap: 16px;
            flex-wrap: wrap;
        }

        /* Mobile responsiveness */
        @media (max-width: 768px) {
            .nav-items {
                width: 100%;
                justify-content: space-around;
                margin-top: 8px;
            }
        }
        </style>
    """, unsafe_allow_html=True)

    # -------------------------------
    # Layout
    # -------------------------------
    col_logo, col_nav, col_logout = st.columns([2,5,1])

    with col_logo:
        st.image(logo_path, width=150)

    with col_nav:
        nav_cols = st.columns(4)

        if role == "user":
            with nav_cols[0]:
                if st.button("Profile", width="stretch"):
                    st.switch_page("pages/3_candidate_profile.py")

            with nav_cols[1]:
                if st.button("Jobs", width="stretch"):
                    st.switch_page("pages/4_job_listings.py")

            with nav_cols[2]:
                if st.button("Resumes", width="stretch"):
                    st.switch_page("pages/5_resume_upload.py")

            with nav_cols[3]:
                if st.button("Applications", width="stretch"):
                    st.switch_page("pages/6_my_applications.py")

    with col_logout:
        if st.button("Logout", width="stretch"):
            logout()

    st.divider()
