import streamlit as st
import requests
from auth import require_login, auth_headers
import os
from dotenv import load_dotenv
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import json
import traceback
from layout import render_sidebar

# -------------------------------------------------
# ENV + CONFIG
# -------------------------------------------------
load_dotenv()

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")
S3_BUCKET = os.getenv("S3_BUCKET_NAME", "candidate-profile-assets")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

st.set_page_config(page_title="Candidate Profile", layout="wide", page_icon="👤")
require_login()
render_sidebar()
role = st.session_state.get("role")

if role != "user":
    st.error("❌ Candidate profile is only for candidates.")
    st.stop()

# -------------------------------------------------
# SESSION STATES
# -------------------------------------------------
def init_session_states():
    default_states = {
        "edit_basic_info": False,
        "edit_skills": False,
        "edit_education": False,
        "edit_experience": False,
        "edit_projects": False,
        "edit_certifications": False,
        "edit_resume_headline": False,
        "candidate_skills": [],
        "education_list": [],
        "experience_list": [],
        "project_list": [],
        "certification_list": [],
        "show_profile_visibility": False,
        "profile_data": None,
        "profile_loaded": False
    }
    
    
    for key, value in default_states.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_states()


if "profile_pic_uploader_key" not in st.session_state:
    st.session_state.profile_pic_uploader_key = 0


def format_date(value):
    if not value:
        return ""
    try:
        dt = datetime.fromisoformat(value)
        return dt.strftime("%d %b %Y")
    except Exception:
        return str(value)


def completion_percentage(completion):
    if isinstance(completion, dict):
        pct = completion.get("percentage", 0)
    else:
        pct = completion
    try:
        return int(pct)
    except Exception:
        return 0


def parse_date(value, default_date):
    if not value:
        return default_date
    try:
        return datetime.fromisoformat(value).date()
    except Exception:
        return default_date





# -------------------------------------------------
# FETCH PROFILE DATA - WITH ERROR HANDLING
# -------------------------------------------------
def fetch_profile_data(user_id: str, token: str):
    headers = {"Authorization": f"Bearer {token}"}

    def safe_get(session, url, default=None):
        try:
            res = session.get(url, headers=headers, timeout=10)
        except Exception:
            return default
        if res.status_code != 200:
            return default
        return res.json()

    endpoints = {
        "profile": (f"{API_BASE}/candidate/profile", {}),
        "completion": (f"{API_BASE}/candidate/profile-completion", {}),
        "educations": (f"{API_BASE}/candidate/education", []),
        "experiences": (f"{API_BASE}/candidate/experience", []),
        "skills": (f"{API_BASE}/candidate/skills", []),
        "projects": (f"{API_BASE}/candidate/projects", []),
    }

    results = {}
    with requests.Session() as session:
        with ThreadPoolExecutor(max_workers=6) as executor:
            future_map = {
                executor.submit(safe_get, session, url, default): name
                for name, (url, default) in endpoints.items()
            }
            for future in future_map:
                name = future_map[future]
                results[name] = future.result()

    return (
        results.get("profile", {}),
        results.get("completion", {}),
        results.get("educations", []),
        results.get("experiences", []),
        results.get("skills", []),
        results.get("projects", []),
    )




# 2️⃣ LOAD PROFILE DATA ONCE
if not st.session_state.profile_loaded:
    with st.spinner("Loading profile data..."):
        token = st.session_state.get("id_token")
        user_id = st.session_state.get("user_id")

        if "user_id" not in st.session_state:
            st.error("Invalid session. Please login again.")
            st.session_state.clear()
            st.stop()

        if not token or not user_id:
            st.error("Session expired. Please login again.")
            st.stop()

        profile, completion, educations, experiences, skills, projects = fetch_profile_data(
            user_id=user_id,
            token=token
        )

        st.session_state.profile_data = {
            "profile": profile,
            "completion": completion,
            "educations": educations,
            "experiences": experiences,
            "skills": skills,
            "projects": projects,
        }

        st.session_state.profile_loaded = True

# Get data from session state
if st.session_state.profile_data:
    profile = st.session_state.profile_data["profile"]
    completion = st.session_state.profile_data["completion"]
    educations = st.session_state.profile_data["educations"]
    experiences = st.session_state.profile_data["experiences"]
    skills = st.session_state.profile_data["skills"]
    projects = st.session_state.profile_data["projects"]
else:
    # Fallback to empty data
    profile, completion, educations, experiences, skills, projects = {}, {}, [], [], [], []

# -------------------------------------------------
# CUSTOM CSS
# -------------------------------------------------
st.markdown("""
<style>
    .profile-card {
        background: #ffffff;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }

    .section-header {
        font-size: 20px;
        font-weight: 600;
        color: #1a1a1a;
        margin-bottom: 16px;
        border-bottom: 2px solid #e5e7eb;
        padding-bottom: 8px;
    }

    .skill-badge {
        padding: 6px 12px;
        border-radius: 16px;
        font-size: 13px;
        background: #f1f3f5;
        color: #333;
        border: 1px solid #ddd;
    }

    /* ===============================
       Professional Button Style
       =============================== */
    .stButton > button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 10px 18px !important;

        background-color: #ffffff !important;
        color: #111827 !important;
        border: 1px solid #d1d5db !important;

        box-shadow: none !important;
        transition: all 0.18s ease-in-out !important;
    }

    .stButton > button:hover {
        background-color: #f9fafb !important;
        border-color: #9ca3af !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.06) !important;
        transform: translateY(-1px);
    }

    .stButton > button:focus,
    .stButton > button:active {
        outline: none !important;
        box-shadow: none !important;
    }

    /* Hide streamlit file uploader 200MB text */
    [data-testid="stFileUploader"] small {
        display: none !important;
    }

</style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# HEADER WITH PROFILE PICTURE
# -------------------------------------------------
st.markdown("# 👤 My Profile")

col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    if isinstance(profile, dict) and profile.get("profile_picture"):
        profile_pic = profile.get("profile_picture", "")
        if profile_pic:
            image_url = (
                profile_pic
                if profile_pic.startswith("http")
                else f"https://{S3_BUCKET}.s3.amazonaws.com/{profile_pic}"
            )
            st.image(image_url, width=150)
    else:
        st.image("https://via.placeholder.com/150", width=150)
    
    # Upload profile picture
    uploaded_file = st.file_uploader(
        "Profile picture",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=False,
        label_visibility="collapsed",
        key=f"profile_pic_uploader_{st.session_state.profile_pic_uploader_key}",
    )


    st.caption("📸 JPG / PNG only · Max size 2 MB")


    if uploaded_file:
        # 🔒 FRONTEND SIZE VALIDATION (2MB)
        if uploaded_file.size > 2 * 1024 * 1024:
            st.error("❌ Image size must be less than 2MB")
            st.stop()

        files = {
            "file": (
                uploaded_file.name,
                uploaded_file,
                uploaded_file.type
            )
        }

        with st.spinner("Uploading profile photo..."):
            try:
                res = requests.post(
                    f"{API_BASE}/candidate/profile-picture",
                    files=files,
                    headers=auth_headers(),
                    timeout=30
                )

                if res.status_code == 200:
                    st.success("✅ Photo updated successfully")

                    # ✅ reset uploader so file is cleared
                    st.session_state.profile_pic_uploader_key += 1

                    # reload profile ONCE
                    st.session_state.profile_loaded = False
                    st.rerun()
                else:
                    st.error(res.json().get("detail", "Upload failed"))

            except Exception as e:
                st.error(f"Upload error: {e}")


with col2:
    full_name = profile.get('full_name', 'Your Name') if isinstance(profile, dict) else 'Your Name'
    st.markdown(f"### {full_name}")
    
    
    # Resume Headline (editable)
    if not st.session_state.edit_resume_headline:
        headline = profile.get('resume_headline', 'Add a resume headline to grab attention') if isinstance(profile, dict) else 'Add a resume headline'
        st.markdown(f"**{headline}**")
        if st.button("✏️ Edit Headline", key="edit_headline_btn"):
            st.session_state.edit_resume_headline = True
            st.rerun()
    else:
        new_headline = st.text_input(
            "Resume Headline", 
            value=profile.get('resume_headline', '') if isinstance(profile, dict) else '',
            max_chars=200,
            key="headline_input"
        )
        col_save, col_cancel = st.columns(2)
        if col_save.button("Save", key="save_headline", use_container_width=True):
            try:
                res = requests.put(
                    f"{API_BASE}/candidate/profile",
                    json={"resume_headline": new_headline},
                    headers=auth_headers(),
                    timeout=10
                )
                if res.status_code == 200:
                    st.session_state.edit_resume_headline = False
                    st.session_state.profile_loaded = False
                    st.rerun()
                else:
                    st.error("Failed to update headline")
            except Exception as e:
                st.error(f"Error updating headline: {str(e)}")
        
        if col_cancel.button("Cancel", key="cancel_headline", use_container_width=True):
            st.session_state.edit_resume_headline = False
            st.rerun()
    
    if st.button("✏️ Edit Profile", key="edit_profile_btn"):
        st.session_state.edit_basic_info = True
        st.rerun()

    
    # Display contact information
    if isinstance(profile, dict):
        current_location = profile.get('current_location', 'Not specified')
        if current_location:
            st.write(f"📍 {current_location}")
        
        exp = profile.get("total_experience")
        if exp:
            st.write(f"💼 {exp} years experience")
        else:
            st.write("💼 Fresher")
        
        email = profile.get('email')
        if email:
            st.write(f"✉️ {email}")
        
        phone = profile.get('phone_number', 'Add phone number')
        st.write(f"📱 {phone}")

with col3:
    # Profile completion score
    completion_pct = completion_percentage(completion)
    if completion_pct < 0:
        completion_pct = 0
    if completion_pct > 100:
        completion_pct = 100
    st.metric("Profile Strength", f"{completion_pct}%")
    st.progress(float(completion_pct) / 100 if completion_pct else 0)
    
    if completion_pct < 100 and isinstance(completion, dict):
        st.markdown("#### 📋 Complete Your Profile")
        for m in completion.get("missing_sections", []):
            st.write(f"• {m}")
    


st.divider()
# -------------------------------------------------
# EDIT BASIC PROFILE INFO (ONLY 4 FIELDS)
# -------------------------------------------------
if st.session_state.edit_basic_info:
    st.markdown("### ✏️ Edit Profile")

    current_location = st.text_input(
        "Current Location",
        value=profile.get("current_location", ""),
        key="edit_current_location"
    )

    total_experience = st.number_input(
        "Total Experience (Years)",
        0.0, 50.0,
        value=float(profile.get("total_experience") or 0.0),
        step=0.5,
        key="edit_total_experience"
    )

    phone_number = st.text_input(
        "Phone Number",
        value=profile.get("phone_number", ""),
        key="edit_phone_number"
    )
    MAX_SUMMARY_CHARS = 500

    profile_summary = st.text_area(
        "Profile Summary",
        value=profile.get("profile_summary") or "",  # ✅ FIX
        height=150,
        max_chars=MAX_SUMMARY_CHARS,
        help=f"Maximum {MAX_SUMMARY_CHARS} characters",
        key="profile_summary_input"
    )

    # ✅ SAFE LENGTH CHECK
    summary_len = len(profile_summary) if profile_summary else 0
    st.caption(f"{summary_len}/{MAX_SUMMARY_CHARS} characters")

    col1, col2 = st.columns(2)

    if col1.button("💾 Save", use_container_width=True):
        payload = {
            "current_location": current_location,
            "total_experience": total_experience,
            "phone_number": phone_number,
            "profile_summary": profile_summary,
        }

        res = requests.put(
            f"{API_BASE}/candidate/profile",
            json=payload,
            headers=auth_headers(),
            timeout=10
        )

        if res.status_code == 200:
            st.success("Profile updated successfully ✅")
            st.session_state.edit_basic_info = False
            st.session_state.profile_loaded = False
            st.rerun()
        else:
            st.error(res.text)

    if col2.button("❌ Cancel", use_container_width=True):
        st.session_state.edit_basic_info = False
        st.rerun()

# -------------------------------------------------
# QUICK ACTIONS
# -------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    if st.button("👁️ Preview Profile", use_container_width=True, key="preview_profile"):
        if profile.get("public_username"):
            public_ui_url = (
                f"http://localhost:8501/public_profile"
                f"?username={profile['public_username']}"
            )

            st.markdown(
                f"""
                <a href="{public_ui_url}" target="_blank">
                    🔗 <b>Open Public Profile</b>
                </a>
                """,
                unsafe_allow_html=True
            )
        else:
            st.warning("Public profile will be available after saving profile")
with col2:
    if st.button("📊 View Analytics", use_container_width=True, key="view_analytics"):
        st.switch_page("pages/7_profile_analytics.py")


st.divider()

# -------------------------------------------------
# PROFILE SUMMARY
# -------------------------------------------------
st.markdown('<div class="section-header">📝 Profile Summary</div>', unsafe_allow_html=True)

if isinstance(profile, dict):
    summary = profile.get("profile_summary")
    if summary:
        st.markdown(f"""
        <div style="background:#f8f9fa;padding:16px;border-radius:8px;line-height:1.6">
            {summary}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("💡 Add a compelling profile summary to attract recruiters. Highlight your key skills, experience, and career goals.")
else:
    st.info("💡 Profile data not available")

st.divider()

# -------------------------------------------------
# KEY SKILLS
# -------------------------------------------------
st.markdown('<div class="section-header">🛠️ Key Skills</div>', unsafe_allow_html=True)

if not st.session_state.edit_skills:
    if skills and isinstance(skills, list):
        skill_html = "<div style='display:flex; flex-wrap:wrap; gap:8px; margin-top:10px;'>"

        for s in skills:
            if not isinstance(s, dict):
                continue

            # handle both API formats
            if "skill" in s and isinstance(s["skill"], dict):
                name = s["skill"].get("name")
            else:
                name = s.get("name")

            if not name:
                continue

            skill_html += f"<div class='skill-badge'>{name}</div>"

        skill_html += "</div>"
        st.markdown(skill_html, unsafe_allow_html=True)
    else:
        st.info("Add skills to your profile")

    
    if st.button("✏️ Edit Skills", key="edit_skills_btn_main"):
        # Initialize skills list
        if skills and isinstance(skills, list):
            skill_list = []
            for s in skills:
                if isinstance(s, dict):
                    skill_data = {
                        "name": s.get('skill', {}).get('name', '') if 'skill' in s else s.get('name', ''),
                        "proficiency": s.get('proficiency', 'Beginner'),
                        "years_of_experience": s.get('years_of_experience', 0),
                    }
                    if skill_data["name"]:  # Only add if name exists
                        skill_list.append(skill_data)
            st.session_state.candidate_skills = skill_list
        else:
            st.session_state.candidate_skills = []
        
        st.session_state.edit_skills = True
        st.rerun()
else:
    # EDIT SKILLS MODE
    st.markdown("### ✏️ Edit Skills")
    
    # Display existing skills for editing
    for i, s in enumerate(st.session_state.candidate_skills):
        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
        
        with col1:
            st.session_state.candidate_skills[i]["name"] = st.text_input(
                "Skill", 
                value=s.get("name", ""),
                key=f"skill_name_{i}",
                max_chars=50,
                placeholder="e.g., Python, React, AWS"
            )
        with col2:
            st.session_state.candidate_skills[i]["proficiency"] = st.selectbox(
                "Proficiency",
                ["Beginner", "Intermediate", "Advanced", "Expert"],
                index=["Beginner", "Intermediate", "Advanced", "Expert"].index(
                    s.get("proficiency", "Beginner")
                ),
                key=f"skill_prof_{i}"
            )
        with col3:
            st.session_state.candidate_skills[i]["years_of_experience"] = st.number_input(
                "Years", 
                0.0, 50.0, 
                value=float(s.get("years_of_experience", 0.0)), 
                step=0.5,
                key=f"skill_years_{i}"
            )
        with col4:
            if st.button("❌", key=f"remove_skill_{i}"):
                st.session_state.candidate_skills.pop(i)
                st.rerun()
    
    st.divider()
    
    # Add new skill
    st.markdown("### ➕ Add New Skill")
    col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
    with col1:
        new_skill_name = st.text_input("Skill name", key="new_skill_name", placeholder="Enter skill name")
    with col2:
        new_prof = st.selectbox("Proficiency", 
                               ["Beginner", "Intermediate", "Advanced", "Expert"],
                               key="new_skill_prof")
    with col3:
        new_years = st.number_input("Years", 0.0, 50.0, 1.0, 0.5, key="new_skill_years")
    with col4:
        MAX_SKILLS = 15

        if st.button("Add", key="add_new_skill"):
            if len(st.session_state.candidate_skills) >= MAX_SKILLS:
                st.error("❌ You can add only 15 skills")
            elif new_skill_name and new_skill_name.strip():
                st.session_state.candidate_skills.append({
                    "name": new_skill_name.strip().lower(),
                    "proficiency": new_prof,
                    "years_of_experience": new_years,
                })
                st.rerun()
            else:
                st.warning("Please enter a skill name")
    
    # Save/Cancel buttons
    col1, col2 = st.columns(2)
    with col1:
        st.info("ℹ️ Removing a skill requires clicking **Save Skills** to apply changes")
        if st.button("💾 Save Skills", key="save_skills", use_container_width=True):
            # Prepare data for API
            valid_skills = []
            for skill in st.session_state.candidate_skills:
                if skill["name"] and skill["name"].strip():
                    valid_skills.append({
                        "name": skill["name"].strip(),
                        "proficiency": skill["proficiency"],
                        "years_of_experience": skill["years_of_experience"]
                    })
            
            res = requests.put(
                f"{API_BASE}/candidate/skills",
                json=valid_skills,  # empty list allowed
                headers=auth_headers(),
                timeout=10
            )

            if res.status_code == 200:
                st.success("Skills updated successfully ✅")
                st.session_state.edit_skills = False
                st.session_state.profile_loaded = False
                st.session_state.profile_data = None
                st.rerun()
            else:
                st.error(f"Failed to update skills: {res.text}")
    with col2:
        if st.button("❌ Cancel", key="cancel_skills", use_container_width=True):
            st.session_state.edit_skills = False
            st.rerun()

st.divider()

# -------------------------------------------------
# EMPLOYMENT / EXPERIENCE
# -------------------------------------------------
st.markdown('<div class="section-header">💼 Employment</div>', unsafe_allow_html=True)

if not st.session_state.edit_experience:
    if experiences and isinstance(experiences, list):
        for exp in experiences:
            if isinstance(exp, dict):
                is_current = bool(exp.get("is_current"))
                start_date = format_date(exp.get("start_date"))
                end_date = "Present" if is_current else format_date(exp.get("end_date"))
                if not start_date:
                    start_date = "-"
                if not end_date:
                    end_date = "-"

                st.markdown(f"""
                <div style='background:#f8f9fa;padding:16px;border-radius:8px;margin-bottom:12px;'>
                    <h4 style='margin:0'>{exp.get("role", "")}</h4>
                    <b>{exp.get("company_name", "")}</b><br>
                    <small>{start_date} to {end_date}</small>
                    <p>{exp.get("description") or ""}</p>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("Add your work experience")

    experience_button_label = "Add Experience" if not experiences else "Edit Experience"
    if st.button(experience_button_label):
        exp_list = []

        if experiences:
            for e in experiences:
                exp_list.append({
                    "id": e.get("id"),
                    "company_name": e.get("company_name", ""),
                    "role": e.get("role", ""),
                    "start_date": e.get("start_date"),
                    "end_date": e.get("end_date"),
                    "is_current": e.get("is_current", False),
                    "description": e.get("description", ""),
                })

        if not exp_list:
            exp_list.append({
                "id": None,
                "company_name": "",
                "role": "",
                "start_date": None,
                "end_date": None,
                "is_current": False,
                "description": "",
            })

        st.session_state.experience_list = exp_list
        st.session_state.edit_experience = True
        st.rerun()

else:
    st.markdown("### ✏️ Edit Experience")

    delete_exp_index = None

    with st.form("experience_form"):
        for i, exp in enumerate(st.session_state.experience_list):
            with st.expander(
                f"Experience {i + 1}: {exp.get('role', 'New Position')}",
                expanded=(i == 0)
            ):
                st.session_state.experience_list[i]["role"] = st.text_input(
                    "Job Title",
                    exp.get("role", ""),
                    max_chars=100,
                    help="Maximum 100 characters",
                    key=f"exp_role_{i}"
                )

                st.session_state.experience_list[i]["company_name"] = st.text_input(
                    "Company Name",
                    exp.get("company_name", ""),
                    max_chars=100,
                    help="Maximum 100 characters",
                    key=f"exp_company_{i}"
                )

                col1, col2 = st.columns(2)

                with col1:
                    sd = exp.get("start_date")
                    st.session_state.experience_list[i]["start_date"] = str(
                        st.date_input(
                            "Start Date",
                            parse_date(sd, datetime.today().date()),
                            key=f"exp_start_{i}"
                        )
                    )

                with col2:
                    is_current = st.checkbox(
                        "Currently Working",
                        exp.get("is_current", False),
                        key=f"exp_current_{i}"
                    )
                    st.session_state.experience_list[i]["is_current"] = is_current

                    if not is_current:
                        ed = exp.get("end_date")
                        st.session_state.experience_list[i]["end_date"] = str(
                            st.date_input(
                                "End Date",
                                parse_date(ed, datetime.today().date()),
                                key=f"exp_end_{i}"
                            )
                        )
                    else:
                        st.session_state.experience_list[i]["end_date"] = None
                        st.caption("End date is ignored when currently working is checked.")

                desc = st.text_area(
                    "Description",
                    exp.get("description") or "",
                    max_chars=600,
                    height=120,
                    key=f"exp_desc_{i}"
                )

                st.session_state.experience_list[i]["description"] = desc

                # 🗑️ DELETE EXPERIENCE (FORM SAFE)
                if exp.get("id"):
                    if st.form_submit_button("🗑️ Delete This Experience", key=f"del_exp_{i}"):
                        delete_exp_index = i

        save_clicked = st.form_submit_button("💾 Save Experience")

        # ---------------- DELETE HANDLER ----------------
        if delete_exp_index is not None:
            exp = st.session_state.experience_list[delete_exp_index]

            res = requests.delete(
                f"{API_BASE}/candidate/experience/{exp['id']}",
                headers=auth_headers()
            )

            if res.status_code == 204:
                st.success("Experience deleted successfully ✅")
                st.session_state.profile_loaded = False
                st.session_state.edit_experience = False
                st.rerun()
            else:
                st.error(res.text)

        # ---------------- SAVE HANDLER ----------------
        if save_clicked:
            for exp in st.session_state.experience_list:
                if not exp.get("company_name") or not exp.get("role"):
                    continue

                payload = {
                    "company_name": exp["company_name"],
                    "role": exp["role"],
                    "start_date": exp["start_date"],
                    "end_date": exp["end_date"],
                    "is_current": exp["is_current"],
                    "description": exp["description"],
                }

                if exp.get("id"):
                    requests.put(
                        f"{API_BASE}/candidate/experience/{exp['id']}",
                        json=payload,
                        headers=auth_headers(),
                    )
                else:
                    requests.post(
                        f"{API_BASE}/candidate/experience",
                        json=payload,
                        headers=auth_headers(),
                    )

            st.success("Experience saved successfully ✅")
            st.session_state.profile_loaded = False
            st.session_state.edit_experience = False
            st.rerun()

    MAX_EXPERIENCES = 5

    if st.button("➕ Add Another Experience"):
        if len(st.session_state.experience_list) >= MAX_EXPERIENCES:
            st.error("❌ Maximum 5 experiences allowed")
        else:
            st.session_state.experience_list.append({
                "id": None,
                "company_name": "",
                "role": "",
                "start_date": None,
                "end_date": None,
                "is_current": False,
                "description": "",
            })
            st.rerun()


st.divider()



# -------------------------------------------------
# EDUCATION
# -------------------------------------------------
st.markdown('<div class="section-header">🎓 Education</div>', unsafe_allow_html=True)

if not st.session_state.edit_education:
    if educations and isinstance(educations, list):
        for e in educations:
            if isinstance(e, dict):
                start_year = e.get('start_year', '')
                end_year = e.get('end_year', '')
                grade = e.get('grade', '')
                
                st.markdown(f"""
                <div style='background:#f8f9fa;padding:12px;border-radius:8px;margin-bottom:10px;'>
                    <h4 style='margin:0;'>{e.get('degree', 'Degree')}</h4>
                    <p style='margin:4px 0;color:#666;'>{e.get('institution', 'Institution')}</p>
                    <p style='margin:4px 0;color:#888;font-size:14px;'>
                        {start_year} - {end_year} 
                        {(' | Grade: ' + grade) if grade else ''}
                    </p>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("💡 Add your educational qualifications")
    
    if st.button("✏️ Edit Education", key="edit_education_btn"):
        st.session_state.education_list = educations.copy() if educations else []
        st.session_state.edit_education = True
        st.rerun()
else:
    # EDIT EDUCATION MODE
    st.markdown("### ✏️ Edit Education")
    
    for i, e in enumerate(st.session_state.education_list):
        with st.expander(f"Education {i + 1}: {e.get('institution', 'New Institution')}", expanded=(i == 0)):
            col1, col2 = st.columns(2)
            with col1:
                e["institution"] = st.text_input(
                    "Institution", 
                    value=e.get("institution", ""), 
                    max_chars=100,
                    key=f"ei{i}"
                )
                e["degree"] = st.text_input(
                    "Degree", 
                    value=e.get("degree", ""), 
                    max_chars=100,
                    key=f"ed{i}"
                )
            with col2:
                e["field_of_study"] = st.text_input(
                    "Field of Study", 
                    value=e.get("field_of_study", ""),
                    max_chars=100, 
                    key=f"efs{i}"
                )
                e["grade"] = st.text_input(
                    "Grade/CGPA", 
                    value=e.get("grade", ""),
                    max_chars=10, 
                    key=f"eg{i}"
                )
            
            col3, col4 = st.columns(2)
            with col3:
                start_year = e.get("start_year", datetime.now().year - 4)
                if not isinstance(start_year, int):
                    try:
                        start_year = int(start_year)
                    except:
                        start_year = datetime.now().year - 4
                e["start_year"] = st.number_input(
                    "Start Year", 
                    1950, 2100, 
                    value=start_year, 
                    key=f"es{i}"
                )
            with col4:
                end_year = e.get("end_year", datetime.now().year)
                if not isinstance(end_year, int):
                    try:
                        end_year = int(end_year)
                    except:
                        end_year = datetime.now().year
                e["end_year"] = st.number_input(
                    "End Year", 
                    1950, 2100, 
                    value=end_year, 
                    key=f"ee{i}"
                )
            
                if e.get("id"):
                    col_del, col_spacer = st.columns([1, 4])
                    with col_del:
                        if st.button("🗑️ Delete", key=f"del_edu_{i}"):
                            res = requests.delete(
                                f"{API_BASE}/candidate/education/{e['id']}",
                                headers=auth_headers()
                            )

                            if res.status_code == 204:
                                st.success("Education deleted successfully ✅")
                                st.session_state.profile_loaded = False
                                st.session_state.edit_education = False
                                st.rerun()
                            else:
                                st.error(res.text)
    
    MAX_EDUCATION = 5

    if st.button("➕ Add Education", key="add_education"):
        if len(st.session_state.education_list) >= MAX_EDUCATION:
            st.error("❌ You can add only 5 education records")
        else:
            st.session_state.education_list.append({
                "institution": "",
                "degree": "",
                "field_of_study": "",
                "start_year": datetime.now().year - 4,
                "end_year": datetime.now().year,
                "grade": ""
            })
            st.rerun()
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Save Education", key="save_education", use_container_width=True):
            try:
                saved_count = 0
                for edu in st.session_state.education_list:
                    if not edu.get("institution") or not edu.get("degree"):
                        continue
                    
                    edu_data = {
                        "institution": edu["institution"],
                        "degree": edu["degree"],
                        "field_of_study": edu["field_of_study"],
                        "start_year": edu["start_year"],
                        "end_year": edu["end_year"],
                        "grade": edu["grade"]
                    }
                    
                    if edu.get("id"):
                        response = requests.put(
                            f"{API_BASE}/candidate/education/{edu['id']}",
                            json=edu_data,
                            headers=auth_headers(),
                            timeout=10
                        )
                    else:
                        response = requests.post(
                            f"{API_BASE}/candidate/education",
                            json=edu_data,
                            headers=auth_headers(),
                            timeout=10
                        )
                    
                    if response.status_code in [200, 201]:
                        saved_count += 1
                    else:
                        st.error(f"Failed to save education: {response.text}")
                
                if saved_count > 0:
                    st.success(f"{saved_count} education record(s) saved ✅")
                    st.session_state.edit_education = False
                    st.session_state.profile_loaded = False
                    st.rerun()
                    
            except Exception as e:
                st.error(f"Error saving education: {str(e)}")
    
    with col2:
        if st.button("❌ Cancel", key="cancel_education", use_container_width=True):
            st.session_state.edit_education = False
            st.rerun()





# -------------------------------------------------
# PROJECTS SECTION (Similar pattern)
# -------------------------------------------------
st.divider()
# -------------------------------------------------
# PROJECTS
# -------------------------------------------------
st.markdown('<div class="section-header">📂 Projects</div>', unsafe_allow_html=True)

# ===============================
# VIEW MODE
# ===============================
if not st.session_state.edit_projects:
    if projects and isinstance(projects, list):
        for p in projects:
            st.markdown(f"""
            <div style='background:#f8f9fa;padding:16px;border-radius:8px;margin-bottom:12px;'>
                <h4 style='margin:0;'>{p.get('title', 'N/A')}</h4>
                <p style='margin:4px 0;'><b>Tech Stack:</b> {p.get('technologies_used', '—')}</p>
                <p>{p.get('description') or ''}</p>
                {f"<a href='{p.get('project_url')}' target='_blank'>🔗 View Project</a>" if p.get('project_url') else ""}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("💡 Add your projects to showcase your practical work")

    if st.button("✏️ Edit Projects", key="edit_projects_btn"):
        project_list = []

        if projects:
            for p in projects:
                project_list.append({
                    "id": p.get("id"),
                    "title": p.get("title", ""),
                    "technologies_used": p.get("technologies_used", ""),
                    "description": p.get("description", ""),
                    "project_url": p.get("project_url", ""),
                })

        if not project_list:
            project_list.append({
                "id": None,
                "title": "",
                "technologies_used": "",
                "description": "",
                "project_url": "",
            })

        st.session_state.project_list = project_list
        st.session_state.edit_projects = True
        st.rerun()

# ===============================
# EDIT MODE
# ===============================
else:
    st.markdown("### ✏️ Edit Projects")
    delete_project_index = None

    with st.form("projects_form"):
        for i, proj in enumerate(st.session_state.project_list):
            with st.expander(
                f"Project {i + 1}: {proj.get('title') or 'New Project'}",
                expanded=True
            ):
                st.session_state.project_list[i]["title"] =st.text_input(
                    "Project Title",
                    proj.get("title", ""),
                    max_chars=150,
                    help="Maximum 150 characters",
                    key=f"proj_title_{i}"
                )
                MAX_TECH = 200

                tech = st.text_input(
                    "Technologies Used",
                    proj.get("technologies_used", ""),
                    max_chars=MAX_TECH,
                    key=f"proj_tech_{i}"
                )

                st.session_state.project_list[i]["technologies_used"] = tech


                st.session_state.project_list[i]["project_url"] =st.text_input(
                    "Project URL (optional)",
                    proj.get("project_url", ""),
                    max_chars=300,
                    help="Maximum 300 characters",
                    key=f"proj_url_{i}"
                )
                MAX_PROJECT_DESC = 500

                desc = st.text_area(
                    "Description",
                    proj.get("description") or "",
                    height=120,
                    max_chars=MAX_PROJECT_DESC,
                    key=f"proj_desc_{i}"
                )
                # 🗑️ DELETE PROJECT (FORM SAFE)
                if proj.get("id"):
                    if st.form_submit_button(
                        "🗑️ Delete This Project",
                        key=f"del_proj_{i}"
                    ):
                        delete_project_index = i
                desc_len = len(desc) if desc else 0
                st.caption(f"{desc_len}/{MAX_PROJECT_DESC} characters")


                st.session_state.project_list[i]["description"] = desc

        submitted = st.form_submit_button("💾 Save Projects")
        # ---------------- DELETE PROJECT HANDLER ----------------
        if delete_project_index is not None:
            proj = st.session_state.project_list[delete_project_index]

            res = requests.delete(
                f"{API_BASE}/candidate/projects/{proj['id']}",
                headers=auth_headers(),
            )

            if res.status_code == 204:
                st.success("Project deleted successfully ✅")
                st.session_state.profile_loaded = False
                st.session_state.edit_projects = False
                st.rerun()
                st.stop()
            else:
                st.error(res.text)

        if submitted and delete_project_index is None:
            count = 0
            for proj in st.session_state.project_list:
                if not proj["title"]:
                    continue

                payload = {
                    "title": proj["title"],
                    "technologies_used": proj["technologies_used"],
                    "description": proj["description"],
                    "project_url": proj["project_url"],
                }

                if proj.get("id"):
                    res = requests.put(
                        f"{API_BASE}/candidate/projects/{proj['id']}",
                        json=payload,
                        headers=auth_headers(),
                    )
                else:
                    res = requests.post(
                        f"{API_BASE}/candidate/projects",
                        json=payload,
                        headers=auth_headers(),
                    )

                if res.status_code in (200, 201):
                    count += 1

            st.success(f"{count} project(s) saved ✅")
            st.session_state.edit_projects = False
            st.session_state.profile_loaded = False
            st.rerun()

    # ➕ ADD PROJECT (OUTSIDE FORM)
    MAX_PROJECTS = 5

    if st.button("➕ Add Another Project", key="add_project"):
        if len(st.session_state.project_list) >= MAX_PROJECTS:
            st.error("❌ Maximum 5 projects allowed")
        else:
            st.session_state.project_list.append({
                "id": None,
                "title": "",
                "technologies_used": "",
                "description": "",
                "project_url": "",
            })
            st.rerun()

st.divider()

# Add a refresh button at the bottom
if st.button("🔄 Refresh Profile Data", key="refresh_profile"):
    st.session_state.profile_loaded = False
    st.rerun()
