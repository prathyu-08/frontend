import streamlit as st
import requests
from auth import require_login, auth_headers
from layout import render_sidebar

API_BASE = "http://localhost:8000"

st.set_page_config(page_title="Application Form Builder", layout="wide")
require_login()
render_sidebar()

st.title("📝 Application Form Builder")
st.caption("Create a customizable application form for each job")

# ==================================================
# FETCH RECRUITER JOBS
# ==================================================
jobs_res = requests.get(
    f"{API_BASE}/jobs/my",
    headers=auth_headers(),
)

if jobs_res.status_code != 200:
    st.error("Failed to load jobs")
    st.stop()

jobs = jobs_res.json()

if not jobs:
    st.info("You have not posted any jobs yet")
    st.stop()

job_map = {job["title"]: job["id"] for job in jobs}

selected_job_title = st.selectbox(
    "Select Job",
    job_map.keys(),
)

selected_job_id = job_map[selected_job_title]

st.divider()

# ==================================================
# SESSION STATE FOR QUESTIONS
# ==================================================
if "questions" not in st.session_state:
    st.session_state.questions = []

# ==================================================
# ADD QUESTION UI
# ==================================================
st.subheader("➕ Add Application Question")

q_col1, q_col2 = st.columns(2)

with q_col1:
    question_text = st.text_input("Question *")
    field_type = st.selectbox(
        "Field Type *",
        ["text", "textarea", "select", "boolean"],
    )

with q_col2:
    is_required = st.checkbox("Mandatory")
    order_index = st.number_input(
        "Order",
        min_value=0,
        step=1,
        value=len(st.session_state.questions),
    )

options = None
if field_type == "select":
    options = st.text_input(
        "Dropdown Options (comma separated)",
        placeholder="Immediate, 15 days, 30 days",
    )

if st.button("➕ Add Question"):
    if not question_text.strip():
        st.error("Question text is required")
    else:
        st.session_state.questions.append(
            {
                "question_text": question_text,
                "field_type": field_type,
                "options": [o.strip() for o in options.split(",")] if options else None,
                "is_required": is_required,
                "order_index": order_index,
            }
        )
        st.success("Question added")
        st.rerun()

st.divider()

# ==================================================
# SHOW CURRENT QUESTIONS
# ==================================================
st.subheader("📋 Current Application Form")

if not st.session_state.questions:
    st.info("No questions added yet")
else:
    for idx, q in enumerate(st.session_state.questions):
        with st.container():
            st.markdown(
                f"""
                **{idx + 1}. {q['question_text']}**
                - Type: `{q['field_type']}`
                - Required: `{q['is_required']}`
                """
            )

            if q["field_type"] == "select":
                st.write("Options:", ", ".join(q["options"] or []))

            if st.button("❌ Remove", key=f"remove_{idx}"):
                st.session_state.questions.pop(idx)
                st.rerun()

st.divider()

# ==================================================
# SAVE FORM TO BACKEND
# ==================================================
if st.button("💾 Save Application Form"):
    if not st.session_state.questions:
        st.error("Add at least one question before saving")
        st.stop()

    res = requests.post(
        f"{API_BASE}/jobs/{selected_job_id}/application-form",
        headers=auth_headers(),
        json=st.session_state.questions,
    )

    if res.status_code == 200:
        st.success("✅ Application form saved successfully")
        st.session_state.questions = []
    else:
        st.error(res.text)
