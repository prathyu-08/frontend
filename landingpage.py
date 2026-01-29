import streamlit as st

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(
    page_title="NMK Recruitment Portal",
    layout="wide",
)

# --------------------------------------------------
# TOP NAVBAR
# --------------------------------------------------
nav1, nav2, nav3 = st.columns([2.4, 6, 2])

with nav1:
    st.image("assets/nmk_logo.png", width=180)

with nav2:
    st.markdown(
        """
        <div style="margin-top:30px;">
            <h1 style="color:#0A66C2;margin-bottom:0;font-weight:800;">
                NMK Recruitment Portal
            </h1>
            <p style="color:#666;font-size:16px;margin-top:4px;">
                Modern Recruitment Management Platform
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with nav3:
    st.write("")
    st.write("")
    n1, n2 = st.columns(2)
    with n1:
        if st.button("Login", key="nav_login", use_container_width=True):
            st.switch_page("pages/login.py")
    with n2:
        if st.button("Get Started", key="nav_get_started", use_container_width=True):
            st.switch_page("pages/1_signup.py")

st.markdown("<hr style='margin:25px 0 45px 0;'>", unsafe_allow_html=True)

# --------------------------------------------------
# HERO SECTION (SaaS STYLE)
# --------------------------------------------------
left, right = st.columns([1.2, 1])

with left:
    st.markdown(
        """
        <h1 style="font-size:46px;font-weight:800;line-height:1.2;">
            Hire smarter.<br>
            Grow faster.
        </h1>

        <p style="font-size:18px;color:#555;line-height:1.7;max-width:650px;">
            NMK Recruitment Portal helps organizations find the right talent
            efficiently and enables candidates to discover meaningful career
            opportunities with ease.
        </p>
        """,
        unsafe_allow_html=True,
    )

    h1, h2 = st.columns(2)
    with h1:
        if st.button("🔍 Explore Jobs", key="hero_explore_jobs", use_container_width=True):
            st.switch_page("pages/4_job_listings.py")
    with h2:
        if st.button("🏢 Recruiter Login", key="hero_recruiter_login", use_container_width=True):
            st.switch_page("pages/login.py")

with right:
    st.markdown(
        """
        <div style="
            background:linear-gradient(135deg,#f4f7fb,#e8eef7);
            border-radius:20px;
            padding:45px;
        ">
            <h4 style="color:#0A66C2;margin-bottom:15px;">
                Why NMK?
            </h4>
            <ul style="font-size:16px;color:#555;line-height:1.9;">
                <li>Secure AWS Cognito authentication</li>
                <li>Recruiter & candidate role separation</li>
                <li>End-to-end job lifecycle</li>
                <li>Clean and intuitive dashboards</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<hr style='margin:70px 0;'>", unsafe_allow_html=True)

# --------------------------------------------------
# VALUE STRIP
# --------------------------------------------------
v1, v2, v3, v4 = st.columns(4)

with v1:
    st.markdown("### 🔐 Secure")
    st.write("AWS Cognito based authentication")

with v2:
    st.markdown("### ⚡ Fast")
    st.write("FastAPI powered backend")

with v3:
    st.markdown("### 📊 Scalable")
    st.write("Cloud-ready architecture")

with v4:
    st.markdown("### 🎯 Reliable")
    st.write("Role-based access control")

st.markdown("<hr style='margin:70px 0;'>", unsafe_allow_html=True)

# --------------------------------------------------
# FEATURES
# --------------------------------------------------
st.markdown(
    "<h2 style='text-align:center;font-weight:700;'>Built for Candidates & Recruiters</h2>",
    unsafe_allow_html=True,
)
st.write("")

f1, f2, f3 = st.columns(3)

with f1:
    st.markdown("### 👤 Candidates")
    st.write(
        """
        - Discover relevant jobs  
        - Apply seamlessly  
        - Track application status  
        - Maintain professional profile  
        """
    )

with f2:
    st.markdown("### 🧑‍💼 Recruiters")
    st.write(
        """
        - Post and manage jobs  
        - Archive & unarchive postings  
        - View candidates per job  
        - Simplify hiring decisions  
        """
    )

with f3:
    st.markdown("### 🧠 Platform")
    st.write(
        """
        - PostgreSQL database  
        - Secure APIs  
        - Modular backend  
        - Production-ready design  
        """
    )

st.markdown("<hr style='margin:70px 0;'>", unsafe_allow_html=True)

# --------------------------------------------------
# HOW IT WORKS
# --------------------------------------------------
st.markdown(
    "<h2 style='text-align:center;font-weight:700;'>How it works</h2>",
    unsafe_allow_html=True,
)
st.write("")

w1, w2, w3 = st.columns(3)

with w1:
    st.markdown("**1️⃣ Sign Up**")
    st.write("Register as a candidate or recruiter")

with w2:
    st.markdown("**2️⃣ Apply or Post Jobs**")
    st.write("Candidates apply, recruiters manage postings")

with w3:
    st.markdown("**3️⃣ Track & Hire**")
    st.write("Review applications and complete hiring")

# --------------------------------------------------
# FINAL CTA
# --------------------------------------------------
st.markdown(
    """
    <div style="
        background:#0A66C2;
        padding:40px;
        border-radius:18px;
        text-align:center;
        color:white;
        margin-top:60px;
    ">
        <h2 style="margin-bottom:10px;">Start hiring smarter today</h2>
        <p style="font-size:17px;">
            Experience a modern recruitment workflow with NMK Recruitment Portal.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.write("")
c1, c2, _ = st.columns([1, 1, 3])

with c1:
    if st.button("Get Started", key="footer_get_started", use_container_width=True):
        st.switch_page("pages/1_signup.py")

with c2:
    if st.button("Login", key="footer_login", use_container_width=True):
        st.switch_page("pages/login.py")

# --------------------------------------------------
# FOOTER
# --------------------------------------------------
st.markdown("<hr style='margin-top:60px;'>", unsafe_allow_html=True)

st.markdown(
    """
    <div style="text-align:center;color:#777;font-size:14px;">
        © 2026 NMK Recruitment Portal · Designed with inspiration from modern SaaS platforms
    </div>
    """,
    unsafe_allow_html=True,
)
