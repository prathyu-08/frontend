import streamlit as st
import requests
import os
from dotenv import load_dotenv
from datetime import datetime
from textwrap import dedent

# ---------------- CONFIG ----------------
load_dotenv()
API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")
S3_BUCKET = os.getenv("S3_BUCKET_NAME", "candidate-profile-assets")

st.set_page_config(
    page_title="Public Profile",
    layout="wide",
)

# ---------------- STYLES ----------------
st.markdown("""
<style>
.block-container {
    max-width: 1100px;
    padding-top: 2rem;
}

/* Cards */
.card {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 14px;
    padding: 22px 26px;
    margin-bottom: 22px;
}

/* Header */
.header {
    display: flex;
    gap: 24px;
    align-items: center;
}
.name {
    font-size: 26px;
    font-weight: 700;
}
.headline {
    font-size: 16px;
    font-weight: 500;
}
.muted {
    color: #6b7280;
    font-size: 14px;
}

/* Section titles */
.section-title {
    font-size: 18px;
    font-weight: 600;
    margin-bottom: 12px;
}

/* Skills */
.skill-chip {
    display: inline-block;
    background: #f1f5f9;
    border: 1px solid #e5e7eb;
    padding: 6px 14px;
    border-radius: 999px;
    margin: 4px 8px 4px 0;
    font-size: 14px;
}

/* Experience / Education */
.exp-role {
    font-weight: 600;
    font-size: 16px;
}
.exp-company {
    font-size: 14px;
    color: #374151;
}
.exp-dates {
    font-size: 13px;
    color: #6b7280;
    margin-bottom: 6px;
}

hr {
    border: none;
    border-top: 1px solid #e5e7eb;
    margin: 16px 0;
}
</style>
""", unsafe_allow_html=True)

# ---------------- FETCH PROFILE ----------------
username = st.query_params.get("username")
if not username:
    st.error("Invalid profile link")
    st.stop()

res = requests.get(f"{API_BASE}/candidate/public/{username}")
if res.status_code != 200:
    st.error("Profile not found or not public")
    st.stop()

profile = res.json()

# ---------------- HELPERS ----------------
def profile_image(key):
    if not key:
        return "https://via.placeholder.com/140"
    if key.startswith("http"):
        return key
    return f"https://{S3_BUCKET}.s3.amazonaws.com/{key}"

def fmt(date):
    if not date:
        return ""
    return datetime.fromisoformat(date).strftime("%b %Y")

# ---------------- HEADER ----------------
st.markdown(dedent(f"""
<div class="card header">
    <img src="{profile_image(profile.get('profile_picture'))}" width="140" style="border-radius:12px;" />
    <div>
        <div class="name">{profile.get("full_name","")}</div>
        <div class="headline">{profile.get("headline","")}</div>
        <div class="muted">{profile.get("experience_years",0)} years experience</div>
        <div class="muted">📍 {profile.get("location","")}</div>
        <div class="muted">📧 {profile.get("email","")}</div>
        <div class="muted">📞 {profile.get("phone_number","")}</div>
    </div>
</div>
"""), unsafe_allow_html=True)

# ---------------- ABOUT ----------------
st.markdown(dedent(f"""
<div class="card">
  <div class="section-title">📝 About</div>
  {profile.get("summary","—")}
</div>
"""), unsafe_allow_html=True)

# ---------------- SKILLS ----------------
skills = profile.get("skills", [])
skills_html = "".join(
    f"<span class='skill-chip'>{s.get('name')}</span>" for s in skills
)

st.markdown(dedent(f"""
<div class="card">
  <div class="section-title">🛠 Skills</div>
  {skills_html if skills_html else "<span class='muted'>No skills added</span>"}
</div>
"""), unsafe_allow_html=True)

# ---------------- EXPERIENCE ----------------
exp_html = ""
for e in profile.get("experience", []):
    end = "Present" if e.get("is_current") else fmt(e.get("end_date"))
    exp_html += dedent(f"""
    <div class="exp-role">{e.get("role")}</div>
    <div class="exp-company">{e.get("company_name")}</div>
    <div class="exp-dates">{fmt(e.get("start_date"))} – {end}</div>
    <div>{e.get("description","")}</div>
    <hr>
    """)

st.markdown(dedent(f"""
<div class="card">
  <div class="section-title">💼 Experience</div>
  {exp_html if exp_html else "<span class='muted'>No experience added</span>"}
</div>
"""), unsafe_allow_html=True)

# ---------------- EDUCATION ----------------
edu_html = ""
for e in profile.get("education", []):
    edu_html += dedent(f"""
    <div class="exp-role">{e.get("degree")}</div>
    <div class="exp-company">{e.get("institution")}</div>
    <div class="exp-dates">{e.get("start_year")} – {e.get("end_year")}</div>
    <hr>
    """)

st.markdown(dedent(f"""
<div class="card">
  <div class="section-title">🎓 Education</div>
  {edu_html if edu_html else "<span class='muted'>No education added</span>"}
</div>
"""), unsafe_allow_html=True)

# ---------------- PROJECTS ----------------
proj_html = ""
for p in profile.get("projects", []):
    link = (
        f"<a href='{p.get('project_url')}' target='_blank'>🔗 View Project</a>"
        if p.get("project_url") else ""
    )
    proj_html += dedent(f"""
    <div class="exp-role">{p.get("title")}</div>
    <div>{p.get("description","")}</div>
    {link}
    <hr>
    """)

st.markdown(dedent(f"""
<div class="card">
  <div class="section-title">🚀 Projects</div>
  {proj_html if proj_html else "<span class='muted'>No projects added</span>"}
</div>
"""), unsafe_allow_html=True)

st.caption("🔓 This is a public profile")
