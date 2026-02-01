import streamlit as st
import requests
from auth import require_role, auth_headers
from layout import render_sidebar

API_BASE = "http://localhost:8000"

require_role("user")
render_sidebar()

job_id = st.session_state.get("apply_job_id")

if not job_id:
    st.error("No job selected")
    st.stop()

st.title("📝 Job Application Form")

# ---------------- FETCH QUESTIONS ----------------
res = requests.get(
    f"{API_BASE}/jobs/{job_id}/application-form",
    headers=auth_headers(),
)

questions = res.json() if res.status_code == 200 else []

if not questions:
    st.warning("This job does not have a custom application form.")

answers = {}

# ---------------- FORM ----------------
with st.form("apply_form"):
    for q in questions:
        label = q["question_text"] + (" *" if q["is_required"] else "")
        qid = q["id"]

        if q["field_type"] == "text":
            answers[qid] = st.text_input(label)

        elif q["field_type"] == "textarea":
            answers[qid] = st.text_area(label)

        elif q["field_type"] == "select":
            answers[qid] = st.selectbox(label, q["options"])

        elif q["field_type"] == "boolean":
            answers[qid] = st.checkbox(label)

    submit = st.form_submit_button("✅ Submit Application")

# ---------------- SUBMIT ----------------
if submit:
    for q in questions:
        if q["is_required"] and not answers.get(q["id"]):
            st.error(f"❌ {q['question_text']} is required")
            st.stop()

    payload = {
        "job_id": job_id,
        "answers": [
            {"question_id": k, "answer": str(v)}
            for k, v in answers.items()
        ],
    }

    res = requests.post(
        f"{API_BASE}/applications/apply",
        headers=auth_headers(),
        json=payload,
    )

    if res.status_code == 200:
        # ✅ 1. store success flag
        st.session_state.application_success = True

        # ✅ 2. mark job as applied
        st.session_state.setdefault("applied_jobs", set())
        st.session_state.applied_jobs.add(job_id)

        # ✅ 3. clear selected job
        st.session_state.apply_job_id = None

        # ✅ 4. redirect back to listings
        st.switch_page("pages/4_job_listings.py")
    else:
        st.error(res.text)
