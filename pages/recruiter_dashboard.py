import streamlit as st
import requests
from datetime import datetime

from auth import require_login, auth_headers, logout
from layout import render_sidebar

# ==================================================
# CONFIG
# ==================================================
API_BASE = "http://localhost:8000"

APPLICATION_STATUSES = [
    "applied",
    "shortlisted",
    "interview",
    "offered",
    "rejected",
]

STATUS_ICONS = {
    "applied": "🟡",
    "shortlisted": "🟢",
    "interview": "🔵",
    "offered": "🟣",
    "rejected": "🔴",
}

# ==================================================
# PAGE SETUP & AUTH
# ==================================================
st.set_page_config(page_title="Recruiter Dashboard", layout="wide")
require_login()

role = st.session_state.get("role")
if role != "recruiter":
    st.error("❌ Recruiter access only")
    st.stop()

render_sidebar()

# ==================================================
# PAGE HEADER
# ==================================================
st.title("🧑‍💼 Recruiter Dashboard")
st.caption("Post jobs, manage candidates, and track hiring progress")
st.divider()

# ==================================================
# SESSION STATE
# ==================================================
st.session_state.setdefault("reload_jobs", True)
st.session_state.setdefault("edit_job_id", None)
st.session_state.setdefault("selected_job_id", None)
st.session_state.setdefault("confirm_delete_job_id", None)
st.session_state.setdefault("view_mode", "dashboard") 
st.session_state.setdefault("app_form_job_id", None)
st.session_state.setdefault("app_form_questions", [])# dashboard or candidates
st.session_state.setdefault("share_job_id", None)

# ==================================================
# GLOBAL JOBS VARIABLE (USED ACROSS TABS)
# ==================================================
jobs = st.session_state.get("jobs", [])

# ==================================================
# FETCH INTERVIEWERS (for interview scheduling)
# ==================================================
interviewers_res = requests.get(
    f"{API_BASE}/interviewers",
    headers=auth_headers(),
)

if interviewers_res.status_code == 200:
    INTERVIEWERS = interviewers_res.json()
else:
    INTERVIEWERS = []
    st.warning("⚠️ Could not load interviewers list")

# ==================================================
# NAVIGATION TABS
# ==================================================
tab1, tab2 = st.tabs(["📋 Job Management", "👥 Candidate Management"])

with tab1:
    st.subheader("➕ Post a New Job")

    # ---- Job Description selector (OUTSIDE FORM but INSIDE TAB) ----
    desc_type = st.radio(
        "Job Description Type *",
        ["Text Editor", "Upload PDF / Word"],
        horizontal=True,
    )

    jd_file = None
    extracted_text = None   # ✅ FIX: define default

    if desc_type == "Upload PDF / Word":
        jd_file = st.file_uploader(
            "Upload Job Description (PDF / DOC / DOCX)",
            type=["pdf", "doc", "docx"],
            key="jd_file_uploader"
        )

    # ✅ FORM MUST BE HERE
    with st.form("post_job_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            title = st.text_input("Job Title *", placeholder="Backend Engineer")
            location = st.text_input("Location", placeholder="Bangalore / Remote")
            employment_type = st.selectbox(
                "Employment Type",
                ["Full-time", "Part-time", "Contract", "Internship"],
            )

        with col2:
            min_exp = st.number_input("Min Experience (Years)", 0.0, 30.0, 0.0, 0.5)
            max_exp = st.number_input("Max Experience (Years)", 0.0, 30.0, 5.0, 0.5)

        s1, s2 = st.columns(2)
        salary_min = s1.number_input("Salary Min (₹ LPA)", 0.0, step=0.5)
        salary_max = s2.number_input("Salary Max (₹ LPA)", 0.0, step=0.5)

        skills = st.text_input(
            "Skills * (comma separated)",
            placeholder="Python, FastAPI, PostgreSQL",
        )

        description_text = None
        if desc_type == "Text Editor":
            description_text = st.text_area(
                "Job Description *",
                height=160,
                placeholder="Responsibilities, requirements, benefits..."
            )

        submit = st.form_submit_button("🚀 Publish Job")
# ==================================================
# HANDLE SUBMIT (AFTER FORM)
# ==================================================
if submit:
    extracted_text = None  # ✅ always defined

    skill_list = [s.strip() for s in skills.split(",") if s.strip()]

    if not title:
        st.error("Job title is required")
        st.stop()

    if not skill_list:
        st.error("At least one skill is required")
        st.stop()

    if desc_type == "Text Editor" and not description_text:
        st.error("Job description text is required")
        st.stop()

    if desc_type == "Upload PDF / Word" and not jd_file:
        st.error("Please upload a job description file")
        st.stop()

    # ==================================================
    # 1️⃣ CREATE JOB FIRST (TEXT OR EMPTY)
    # ==================================================
    payload = {
        "title": title,
        "location": location,
        "min_experience": min_exp,
        "max_experience": max_exp,
        "salary_min": salary_min,
        "salary_max": salary_max,
        "employment_type": employment_type,
        "skills": skill_list,
        "description": description_text if desc_type == "Text Editor" else None,
        "description_file_key": None,
    }

    res = requests.post(
        f"{API_BASE}/jobs/",
        headers=auth_headers(),
        json=payload,
    )

    if res.status_code != 201:
        st.error(res.text)
        st.stop()

    created_job_id = res.json()["id"]  # ✅ NOW IT EXISTS

    # ==================================================
    # 2️⃣ UPLOAD JD FILE (ONLY IF PDF)
    # ==================================================
    if desc_type == "Upload PDF / Word":
        upload_res = requests.post(
            f"{API_BASE}/job-descriptions/upload",
            headers=auth_headers(),
            params={"job_id": created_job_id},
            files={
                "file": (
                    jd_file.name,
                    jd_file.getvalue(),
                    jd_file.type,
                )
            },
        )

        if upload_res.status_code != 200:
            st.error("Failed to upload job description file")
            st.stop()

    st.success("✅ Job posted successfully")
    st.session_state.reload_jobs = True
    st.rerun()


# ==================================================
# SECTION 2: MY JOB POSTINGS
# ==================================================
job_tab1, job_tab2 = st.tabs(["🧑‍💼 My Jobs", "🤝 Shared Jobs"])

# -------- Fetch jobs (only when needed) --------
if st.session_state.reload_jobs:
    res = requests.get(
        f"{API_BASE}/jobs/dashboard",
        headers=auth_headers(),
    )

    if res.status_code != 200:
        st.error("❌ Failed to load jobs")
        st.stop()

    data = res.json()
    st.session_state.owned_jobs = data.get("owned_jobs", [])
    st.session_state.shared_jobs = data.get("shared_jobs", [])
    st.session_state.reload_jobs = False

owned_jobs = st.session_state.get("owned_jobs", [])
shared_jobs = st.session_state.get("shared_jobs", [])
all_jobs = owned_jobs + shared_jobs
with job_tab1:
    jobs = owned_jobs
    # -------- No jobs case --------
    if not owned_jobs:
        st.info("ℹ️ You have not posted any jobs yet.")
    else:
        # -------- Filter --------
        filter_option = st.radio(
            "Filter Jobs",
            ["All", "Active", "Archived"],
            horizontal=True,
        )

        def visible(job):
            if filter_option == "All":
                return True
            if filter_option == "Active":
                return job.get("is_active", False)
            if filter_option == "Archived":
                return not job.get("is_active", True)
            return True
        
        for job in filter(visible, jobs):
                    with st.container():

                        # ================= JOB CARD =================
                        st.markdown(
                            """
                            <div style="
                                border:1px solid #e6e6e6;
                                border-radius:12px;
                                padding:18px;
                                margin-bottom:18px;
                                background-color:#ffffff;
                            ">
                            """,
                            unsafe_allow_html=True,
                        )

                        # Check if this job is in edit mode
                        if st.session_state.edit_job_id == job["id"]:
                            # EDIT MODE - Show form inline
                            st.markdown("### ✏️ Edit Job")

                            with st.form(f"inline_edit_{job['id']}"):
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    edit_title = st.text_input("Job Title", job["title"])
                                    edit_location = st.text_input("Location", job.get("location", ""))
                                    edit_employment_type = st.selectbox(
                                        "Employment Type",
                                        ["Full-time", "Part-time", "Contract", "Internship"],
                                        index=["Full-time", "Part-time", "Contract", "Internship"]
                                        .index(job.get("employment_type", "Full-time")),
                                    )
                                
                                with col2:
                                    edit_min_exp = st.number_input("Min Experience (Years)", value=job.get("min_experience", 0.0))
                                    edit_max_exp = st.number_input("Max Experience (Years)", value=job.get("max_experience", 0.0))

                                s1, s2 = st.columns(2)
                                edit_salary_min = s1.number_input("Salary Min (₹ LPA)", value=job.get("salary_min", 0.0))
                                edit_salary_max = s2.number_input("Salary Max (₹ LPA)", value=job.get("salary_max", 0.0))

                                edit_skills = st.text_input(
                                    "Skills (comma separated)",
                                    ", ".join(job.get("skills", []))
                                )

                                edit_description = st.text_area(
                                    "Job Description",
                                    job.get("description", ""),
                                    height=140
                                )

                                c1, c2 = st.columns(2)

                                if c1.form_submit_button("💾 Update Job"):
                                    requests.put(
                                        f"{API_BASE}/jobs/{job['id']}",
                                        headers=auth_headers(),
                                        json={
                                            "title": edit_title,
                                            "location": edit_location,
                                            "min_experience": edit_min_exp,
                                            "max_experience": edit_max_exp,
                                            "salary_min": edit_salary_min,
                                            "salary_max": edit_salary_max,
                                            "employment_type": edit_employment_type,
                                            "skills": [s.strip() for s in edit_skills.split(",") if s.strip()],
                                            "description": edit_description,
                                        },
                                    )
                                    st.session_state.edit_job_id = None
                                    st.session_state.reload_jobs = True
                                    st.rerun()

                                if c2.form_submit_button("❌ Cancel"):
                                    st.session_state.edit_job_id = None
                                    st.rerun()

                        else:
                            # VIEW MODE - Show job details
                            col1, col2 = st.columns([8, 4])

                            with col1:
                                st.markdown(f"## {job['title']}")
                                st.caption(
                                    f"📍 {job.get('location','N/A')} | "
                                    f"💼 {job.get('employment_type','N/A')} | "
                                    f"{'🟢 Active' if job.get('is_active') else '🔴 Archived'}"
                                )

                                st.markdown(
                                    f"""
                                    **Experience:** {job.get('min_experience',0)} – {job.get('max_experience',0)} yrs  
                                    **Salary:** ₹ {job.get('salary_min',0)} – {job.get('salary_max',0)} LPA  
                                    **Skills:** {", ".join(job.get("skills", []))}
                                    """
                                )

                                with st.expander("📄 View Job Description"):
                                    st.write(job.get("description") or "No description")

                            with col2:
                                st.markdown("### Actions")

                                if st.button("📝 Application Form", key=f"form_{job['id']}"):
                                    st.session_state.app_form_job_id = job["id"]
                                    st.session_state.app_form_questions = []
                                    st.switch_page("pages/recruiter_application_form.py")

                                if st.button("✏️ Edit Job", key=f"edit_{job['id']}"):
                                    st.session_state.edit_job_id = job["id"]
                                    st.rerun()

                                if st.button("👥 View Applicants", key=f"apps_{job['id']}"):
                                    if st.session_state.selected_job_id == job["id"]:
                                        is_shared_job = st.session_state.get("selected_job_is_shared", False)
                                        st.session_state.selected_job_id = None
                                    else:
                                        st.session_state.selected_job_id = job["id"]
                                        st.session_state.selected_job_is_shared = False
                                    st.rerun()

                                if job.get("recruiter_id") == st.session_state.get("recruiter_id"):
                                    if st.button("🤝 Share Job", key=f"share_{job['id']}"):
                                        st.session_state.share_job_id = job["id"]
                                        st.rerun()


                                # Archive / Unarchive
                                if job.get("is_active"):
                                    if st.button("🗑️ Archive", key=f"archive_{job['id']}"):
                                        requests.delete(
                                            f"{API_BASE}/jobs/{job['id']}",
                                            headers=auth_headers(),
                                        )
                                        st.session_state.reload_jobs = True
                                        st.rerun()
                                else:
                                    if st.button("♻️ Unarchive", key=f"unarchive_{job['id']}"):
                                        requests.put(
                                            f"{API_BASE}/jobs/{job['id']}/unarchive",
                                            headers=auth_headers(),
                                        )
                                        st.session_state.reload_jobs = True
                                        st.rerun()

                                # Permanent Delete (actually archive, backend-supported)
                                if st.button("❌ Delete Job", key=f"delete_{job['id']}"):
                                    st.session_state.confirm_delete_job_id = job["id"]

                                # Delete Confirmation
                                if st.session_state.confirm_delete_job_id == job["id"]:
                                    st.warning("⚠️ Are you sure you want to delete (archive) this job?")
                                    c1, c2 = st.columns(2)

                                    if c1.button("Cancel", key=f"cancel_{job['id']}"):
                                        st.session_state.confirm_delete_job_id = None
                                        st.rerun()

                                    if c2.button("Confirm Delete", key=f"confirm_{job['id']}"):
                                        res = requests.delete(
                                            f"{API_BASE}/jobs/{job['id']}/permanent",
                                            headers=auth_headers(),
                                        )

                                        if res.status_code in (200, 204):
                                            st.success("✅ Job permanently deleted")
                                            st.session_state.confirm_delete_job_id = None
                                            st.session_state.reload_jobs = True
                                            st.rerun()
                                        else:
                                            st.error(f"❌ Delete failed: {res.text}")


                                    
                                
                            
                        st.markdown("</div>", unsafe_allow_html=True)
                        # 🤝 SHARE JOB PANEL
                        if st.session_state.get("share_job_id") == job["id"]:

                            st.subheader("🤝 Share Job With Recruiters")

                            recruiters_res = requests.get(
                                f"{API_BASE}/admin/recruiters",
                                headers=auth_headers(),
                            )

                            if not recruiters_res.ok:
                                st.error("Failed to load recruiters")
                            else:
                                recruiters = recruiters_res.json()

                                # Exclude job owner
                                recruiter_map = {
                                    r["full_name"]: r["id"]
                                    for r in recruiters
                                    if r["id"] != job.get("recruiter_id")
                                }

                                selected_recruiters = st.multiselect(
                                    "Select recruiters",
                                    recruiter_map.keys(),
                                    key=f"share_select_{job['id']}"
                                )

                                col1, col2 = st.columns(2)

                                with col1:
                                    if st.button("❌ Cancel Sharing", key=f"cancel_share_{job['id']}"):
                                        st.session_state.share_job_id = None
                                        st.rerun()

                                with col2:
                                    if st.button("✅ Share Job Now", key=f"confirm_share_{job['id']}"):

                                        if not selected_recruiters:
                                            st.warning("Please select at least one recruiter")
                                        else:
                                            res = requests.post(
                                                f"{API_BASE}/job-shares/{job['id']}/share",
                                                headers=auth_headers(),
                                                json=[recruiter_map[name] for name in selected_recruiters],
                                            )

                                            if res.status_code == 200:
                                                st.success("✅ Job shared successfully")
                                                st.session_state.share_job_id = None
                                                st.rerun()
                                            else:
                                                st.error(res.text)

                                            
                        # ==================================================
                        # 👥 APPLICANTS VIEW (RENDERED ONCE)
                        # ==================================================
                        if st.session_state.selected_job_id == job["id"]:

                            st.divider()

                            col1, col2 = st.columns([8, 2])

                            with col1:
                                st.subheader("👥 Applicants")
                            job_id = st.session_state.selected_job_id

                            with col2:
                                if st.button(
                                    "❌ Close Applicants",
                                    key=f"close_applicants_{job_id}"
                                ):
                                    st.session_state.selected_job_id = None
                                    st.rerun()


                            

                            apps_res = requests.get(
                                f"{API_BASE}/applications/job/{job_id}",
                                headers=auth_headers(),
                            )

                            if apps_res.status_code == 200:
                                applications = apps_res.json().get("applicants", [])
                            else:
                                st.error("Failed to load applicants")
                                applications = []

                            if not applications:
                                st.info("ℹ️ No candidates have applied yet.")
                            else:
                                for app in applications:
                                    st.markdown(
                                        f"""
                                        **{STATUS_ICONS.get(app['status'], '⚪')} {app['candidate_name']}**  
                                        📧 {app['candidate_email']}  
                                        📞 {app.get('candidate_phone','-')}  
                                        🕒 {app.get('applied_at')}
                                        """
                                    )
                                    st.markdown("---")

                            st.markdown("</div>", unsafe_allow_html=True)

with job_tab2:
    jobs = st.session_state.get("shared_jobs", [])

    if not jobs:
        st.info("ℹ️ No jobs have been shared with you.")
    else:
        for job in jobs:
            with st.container():
                st.markdown(f"## 🤝 {job['title']}")
                st.caption(
                    f"📍 {job.get('location','N/A')} | "
                    f"💼 {job.get('employment_type','N/A')}"
                )

                st.markdown(
                    f"""
                    **Experience:** {job.get('min_experience',0)} – {job.get('max_experience',0)} yrs  
                    **Salary:** ₹ {job.get('salary_min',0)} – {job.get('salary_max',0)} LPA  
                    **Skills:** {", ".join(job.get("skills", []))}
                    """
                )

                if st.button("👥 View Applicants", key=f"shared_view_{job['id']}"):
                    st.session_state.selected_job_id = job["id"]
                    st.session_state.selected_job_is_shared = True
                    st.rerun()

# ==================================================
# TAB 2: CANDIDATE MANAGEMENT
# ==================================================
with tab2:
    st.subheader("👥 Candidates & Interview Management")
    st.subheader("➕ Manage Interviewers")

    with st.expander("Add New Interviewer"):
        with st.form("add_interviewer_form", clear_on_submit=True):
            name = st.text_input("Interviewer Name *")
            email = st.text_input("Interviewer Email *")

            if st.form_submit_button("Add Interviewer"):
                if not name or not email:
                    st.error("Name and Email are required")
                else:
                    res = requests.post(
                        f"{API_BASE}/interviewers",
                        headers=auth_headers(),
                        json={"name": name, "email": email},
                    )

                    if res.status_code == 201:
                        st.success("✅ Interviewer added successfully")
                        st.rerun()
                    else:
                        st.error(res.text)

    st.divider()

    if not (owned_jobs or shared_jobs):
        st.info("ℹ️ No jobs available.")
        st.stop()

    # ---------------- Job Selection ----------------
    job_map = {
        f"{job['title']} ({'Active' if job['is_active'] else 'Archived'})": job["id"]
        for job in (owned_jobs + shared_jobs)
    }

    selected_job = st.selectbox("Select Job", job_map.keys())
    job_id = job_map[selected_job]




    # ---------------- Fetch Recruiters ----------------
    recruiters_res = requests.get(
        f"{API_BASE}/admin/recruiters",
        headers=auth_headers(),
    )

    recruiters = recruiters_res.json() if recruiters_res.ok else []
    recruiter_map = {r["full_name"]: r["id"] for r in recruiters}

    # ---------------- Fetch Applications ----------------
    apps_res = requests.get(
        f"{API_BASE}/applications/job/{job_id}",
        headers=auth_headers(),
    )

    if not apps_res.ok:
        st.error(f"Failed to load candidates: {apps_res.text}")
        st.stop()

    data = apps_res.json()
    applications = data.get("applicants", [])

    # ✅ THIS IS NOT AN ERROR
    if not applications:
        st.info("ℹ️ No candidates have applied for this job yet.")
        st.stop()


    # ==================================================
    # CANDIDATE LOOP
    # ==================================================
    for app in applications:
        with st.container():
            col1, col2, col3 = st.columns([4, 3, 4])

            # ---------------- Candidate Info ----------------
            with col1:
                status = app.get("status", "applied").lower()
                icon = STATUS_ICONS.get(status, "⚪")

                st.markdown(f"**{icon} {app.get('candidate_name', 'Unknown')}**")
                st.write(f"📧 {app.get('candidate_email', '-')}")
                st.write(f"📞 {app.get('candidate_phone') or 'Not provided'}")

                assigned_name = app.get("assigned_recruiter_name")
                if assigned_name:
                    st.caption(f"👤 Assigned Recruiter: {assigned_name}")

                if st.button("👤 View Full Profile", key=f"profile_{app['application_id']}"):
                    st.session_state.selected_application_id = app["application_id"]
                    st.session_state.selected_candidate_id = app["candidate_id"] 
                    st.switch_page("pages/recruiter_candidate_profile.py")

            # ---------------- Applied Date ----------------
            with col2:
                st.write("🕒 Applied on")
                try:
                    dt = datetime.fromisoformat(app.get("applied_at"))
                    st.write(dt.strftime("%d %b %Y, %I:%M %p"))
                except Exception:
                    st.write(app.get("applied_at", "-"))

            # ---------------- Assignment + Status ----------------
            with col3:

                my_recruiter_id = st.session_state.get("recruiter_id")

                assignable_recruiters = {
                    name: rid
                    for name, rid in recruiter_map.items()
                    if rid != my_recruiter_id
                }

                if assignable_recruiters:
                    selected_recruiter = st.selectbox(
                        "Assign Recruiter",
                        assignable_recruiters.keys(),
                        key=f"assign_{app['application_id']}"
                    )

                    if st.button("✅ Assign", key=f"assign_btn_{app['application_id']}"):
                        res = requests.post(
                            f"{API_BASE}/admin/assign-applications",
                            headers=auth_headers(),
                            json={
                                "job_id": job_id,
                                "assignments": [{
                                    "application_id": app["application_id"],
                                    "recruiter_id": assignable_recruiters[selected_recruiter]
                                }]
                            }
                        )

                        if res.status_code == 200:
                            st.success("Recruiter assigned successfully")
                            st.rerun()
                        else:
                            st.error(res.text)


                # ---------- Status Update (UNCHANGED) ----------
                current_status = app.get("status", "applied").lower()
                if current_status not in APPLICATION_STATUSES:
                    current_status = "applied"

                st.write("📌 Application Status")

                new_status = st.selectbox(
                    "Update Status",
                    APPLICATION_STATUSES,
                    index=APPLICATION_STATUSES.index(current_status),
                    key=f"status_{app['application_id']}",
                )

                if st.button("💾 Save Status", key=f"save_{app['application_id']}"):
                    res = requests.put(
                        f"{API_BASE}/applications/{app['application_id']}/status",
                        headers=auth_headers(),
                        params={"status": new_status},
                    )

                    if res.status_code == 200:
                        st.success("✅ Status updated successfully")
                        st.rerun()
                    else:
                        st.error(res.text)

            st.divider()

                                
            # ==================================================
            # INTERVIEW SCHEDULING (ONLY IF SHORTLISTED)
            # ==================================================
            if current_status == "shortlisted":
                with st.expander("📅 Schedule Interview", expanded=False):
                    st.markdown("### Interview Scheduling")

                    # ---------------- Interview Mode ----------------
                    schedule_mode = st.radio(
                        "Interview Scheduling Type",
                        ["Direct Interview (No Slots)", "Slot-based Interview"],
                        key=f"mode_{app['application_id']}"
                    )

                    # ---------------- Interview Type ----------------
                    interview_type = st.selectbox(
                        "Interview Type",
                        ["online", "offline", "telephone"],
                        key=f"type_{app['application_id']}"
                    )

                    meeting_link = None
                    location = None

                    if interview_type == "online":
                        meeting_link = st.text_input(
                            "Meeting Link",
                            placeholder="https://meet.google.com/abc-defg-hij",
                            key=f"link_{app['application_id']}"
                        )
                    elif interview_type == "offline":
                        location = st.text_input(
                            "Interview Location",
                            placeholder="Office address or venue",
                            key=f"loc_{app['application_id']}"
                        )
                    else:
                        st.info("ℹ️ Interview will be conducted via phone call")

                    # ---------------- Interviewers ----------------
                    st.markdown("### 👥 Select Interviewers")

                    if not INTERVIEWERS:
                        st.warning("⚠️ No interviewers available. Please add interviewers first.")
                    else:
                        selected_interviewers = st.multiselect(
                            "Choose Interviewers",
                            options=INTERVIEWERS,
                            format_func=lambda i: f"{i['name']} ({i['email']})",
                            key=f"interviewers_{app['application_id']}",
                        )

                        if not selected_interviewers:
                            st.warning("⚠️ Please select at least one interviewer")

                        # ==================================================
                        # 🔹 DIRECT INTERVIEW
                        # ==================================================
                        if schedule_mode == "Direct Interview (No Slots)":
                            st.markdown("### 🕐 Direct Interview Schedule")

                            scheduled_at = st.datetime_input(
                                "Interview Date & Time",
                                key=f"direct_dt_{app['application_id']}"
                            )

                            if st.button(
                                "📤 Send Direct Interview Link",
                                key=f"send_direct_{app['application_id']}",
                                disabled=not selected_interviewers
                            ):
                                res = requests.post(
                                    f"{API_BASE}/interviews/schedule",
                                    headers=auth_headers(),
                                    json={
                                        "application_id": app["application_id"],
                                        "schedule_mode": "direct",
                                        "interview_type": interview_type,
                                        "scheduled_at": scheduled_at.isoformat(),
                                        "interviewer_ids": [i["id"] for i in selected_interviewers],
                                        "meeting_link": meeting_link,
                                        "location": location,
                                    },
                                )

                                if res.status_code == 200:
                                    st.success("✅ Interview link sent successfully")
                                    st.info("📩 Emails & calendar invites sent to candidate and interviewers")
                                    st.rerun()
                                else:
                                    st.error(res.text)

                        # ==================================================
                        # 🔹 SLOT-BASED INTERVIEW
                        # ==================================================
                        else:
                            st.markdown("### 🗓️ Slot-based Interview Schedule")

                            interview_date = st.date_input(
                                "Interview Date",
                                key=f"date_{app['application_id']}",
                            )

                            st.markdown("### ⏱ Available Time Slots")

                            slot_count = st.number_input(
                                "Number of Slots",
                                min_value=1,
                                max_value=5,
                                value=2,
                                key=f"slot_count_{app['application_id']}",
                            )

                            slots = []

                            for i in range(int(slot_count)):
                                c1, c2 = st.columns(2)
                                with c1:
                                    start = st.time_input(
                                        f"Slot {i+1} Start",
                                        key=f"start_{app['application_id']}_{i}",
                                    )
                                with c2:
                                    end = st.time_input(
                                        f"Slot {i+1} End",
                                        key=f"end_{app['application_id']}_{i}",
                                    )

                                slots.append({
                                    "start_time": start.strftime("%H:%M"),
                                    "end_time": end.strftime("%H:%M"),
                                })

                            if st.button(
                                "📤 Send Interview Slots",
                                key=f"send_slots_{app['application_id']}",
                                disabled=not selected_interviewers
                            ):
                                interview_res = requests.post(
                                    f"{API_BASE}/interviews/schedule",
                                    headers=auth_headers(),
                                    json={
                                        "application_id": app["application_id"],
                                        "schedule_mode": "slots",
                                        "interview_type": interview_type,
                                        "interviewer_ids": [i["id"] for i in selected_interviewers],
                                        "meeting_link": meeting_link,
                                        "location": location,
                                    },
                                )

                                if interview_res.status_code != 200:
                                    st.error(interview_res.text)
                                else:
                                    interview_id = interview_res.json()["interview_id"]

                                    slot_res = requests.post(
                                        f"{API_BASE}/interviews/slots/{interview_id}",
                                        headers=auth_headers(),
                                        params={"interview_date": str(interview_date)},
                                        json=slots,
                                    )

                                    if slot_res.status_code == 200:
                                        st.success("✅ Interview slots sent successfully")
                                        st.info("📩 Candidate has been notified to select a slot")
                                        st.session_state.reload_jobs = True
                                        st.rerun()
                                    else:
                                        st.error(slot_res.text)

            # ==================================================
            # INTERVIEW MANAGEMENT (AFTER SCHEDULED)
            # ==================================================
            if app.get("scheduled_at"):
                with st.expander("🗓️ Manage Scheduled Interview", expanded=True):
                    st.markdown("### Interview Management")

                    st.write(f"📅 Current Interview Time: {app.get('scheduled_at')}")

                    new_datetime = st.datetime_input(
                        "Reschedule Interview Date & Time",
                        key=f"reschedule_dt_{app['application_id']}"
                    )

                    col_r1, col_r2 = st.columns(2)

                    with col_r1:
                        if st.button(
                            "🔄 Reschedule Interview",
                            key=f"reschedule_btn_{app['application_id']}"
                        ):
                            res = requests.put(
                                f"{API_BASE}/interviews/reschedule/{app['application_id']}",
                                headers=auth_headers(),
                                params={
                                    "new_scheduled_at": new_datetime.isoformat()
                                }
                            )

                            if res.status_code == 200:
                                st.success("✅ Interview rescheduled successfully")
                                st.info("📩 Candidate and interviewers have been notified")
                                st.session_state.reload_jobs = True
                                st.rerun()
                            else:
                                st.error(res.text)

                    with col_r2:
                        if st.button(
                            "❌ Cancel Interview",
                            key=f"cancel_btn_{app['application_id']}"
                        ):
                            res = requests.put(
                                f"{API_BASE}/interviews/cancel/{app['application_id']}",
                                headers=auth_headers(),
                            )

                            if res.status_code == 200:
                                st.success("❌ Interview cancelled successfully")
                                st.rerun()
                            else:
                                st.error(res.text)

            st.markdown("---")
