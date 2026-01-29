import streamlit as st
import requests

st.title("Post a Job")

if "id_token" not in st.session_state:
    st.warning("Please login first")
    st.stop()

title = st.text_input("Job Title")
description = st.text_area("Job Description")
location = st.text_input("Location")

min_exp = st.number_input("Min Experience", min_value=0.0, step=0.5)
max_exp = st.number_input("Max Experience", min_value=0.0, step=0.5)

salary_min = st.number_input("Salary Min", min_value=0.0, step=1000.0)
salary_max = st.number_input("Salary Max", min_value=0.0, step=1000.0)

employment_type = st.selectbox("Employment Type", ["Full-time", "Part-time", "Contract"])

if st.button("Post Job"):
    headers = {"Authorization": f"Bearer {st.session_state['id_token']}"}

    payload = {
        "title": title,
        "description": description,
        "location": location,
        "min_experience": min_exp,
        "max_experience": max_exp,
        "salary_min": salary_min,
        "salary_max": salary_max,
        "employment_type": employment_type,
    }

    # ✅ IMPORTANT FIX: /jobs/ (with slash)
    res = requests.post("http://127.0.0.1:8000/jobs/", headers=headers, json=payload)

    if res.status_code == 201:
        st.success("Job posted successfully ✅")
        st.json(res.json())
    else:
        st.error(f"{res.status_code} - {res.text}")
