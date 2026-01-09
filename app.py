import streamlit as st
import requests

API_BASE = "http://127.0.0.1:8000"

st.set_page_config(page_title="Registration | Recruitment Portal", page_icon="📝")

st.title("📝 Recruitment Portal – Registration")

# ------------------ ROLE SELECTION ------------------
role = st.selectbox(
    "Select Role",
    ["user", "recruiter"]
)

st.divider()

# ------------------ COMMON FIELDS ------------------
username = st.text_input("Username")
full_name = st.text_input("Full Name")
email = st.text_input("Email")
phone_number = st.text_input("Phone Number")
password = st.text_input("Password", type="password")

# ------------------ RECRUITER FIELDS ------------------
company_name = company_website = company_location = designation = None

if role == "recruiter":
    st.subheader("🏢 Company Details")
    company_name = st.text_input("Company Name")
    company_website = st.text_input("Company Website")
    company_location = st.text_input("Company Location")
    designation = st.text_input("Designation")

st.divider()

# ------------------ REGISTER BUTTON ------------------
if st.button("Register"):
    if not username or not full_name or not email or not password:
        st.error("Please fill all required fields")
    else:
        try:
            if role == "recruiter":
                url = f"{API_BASE}/auth/register/recruiter"
                payload = {
                    "username": username,
                    "full_name": full_name,
                    "email": email,
                    "phone_number": phone_number,
                    "password": password,
                    "company_name": company_name,
                    "company_website": company_website,
                    "company_location": company_location,
                    "designation": designation
                }
            else:
                url = f"{API_BASE}/auth/register"
                payload = {
                    "username": username,
                    "full_name": full_name,
                    "email": email,
                    "phone_number": phone_number,
                    "password": password,
                    "role": role
                }

            response = requests.post(url, json=payload)

            if response.status_code in [200, 201]:
                st.success("✅ Registration successful!")
                st.json(response.json())
            else:
                st.error("❌ Registration failed")
                st.json(response.json())

        except Exception as e:
            st.error(f"Server error: {e}")
