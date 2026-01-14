import streamlit as st
import requests

API_BASE = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="Recruitment Management Portal",
    page_icon="🎯",
    layout="centered"
)

st.title("🎯 Recruitment Management Portal")

# ------------------ SESSION STATE ------------------
if "page" not in st.session_state:
    st.session_state.page = "login"

if "token" not in st.session_state:
    st.session_state.token = None
    st.session_state.role = None
    st.session_state.username = None


# ------------------ NAVIGATION ------------------
def go_to(page):
    st.session_state.page = page
    st.rerun()


# ==================================================
# 🔐 LOGIN PAGE
# ==================================================
def login_page():
    st.subheader("🔐 Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        response = requests.post(
            f"{API_BASE}/login",
            data={"username": username, "password": password}
        )

        if response.status_code == 200:
            data = response.json()
            st.session_state.token = data["access_token"]
            st.session_state.role = data["role"]
            st.session_state.username = username
            st.success("Login successful")
            go_to("dashboard")
        else:
            st.error("Invalid username or password")

    st.divider()
    st.info("New user?")
    if st.button("Go to Registration"):
        go_to("register")


# ==================================================
# 📝 REGISTRATION PAGE
# ==================================================
def register_page():
    st.subheader("📝 Registration")

    role = st.selectbox("Select Role", ["user", "recruiter"])

    username = st.text_input("Username")
    full_name = st.text_input("Full Name")
    email = st.text_input("Email")
    phone_number = st.text_input("Phone Number")
    password = st.text_input("Password", type="password")

    company_name = company_website = company_location = designation = None

    if role == "recruiter":
        st.subheader("🏢 Company Details")
        company_name = st.text_input("Company Name")
        company_website = st.text_input("Company Website")
        company_location = st.text_input("Company Location")
        designation = st.text_input("Designation")

    if st.button("Register"):
        if not username or not full_name or not email or not password:
            st.error("Please fill all required fields")
            return

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
                "designation": designation,
            }
        else:
            url = f"{API_BASE}/auth/register"
            payload = {
                "username": username,
                "full_name": full_name,
                "email": email,
                "phone_number": phone_number,
                "password": password,
                "role": role,
            }

        response = requests.post(url, json=payload)

        if response.status_code in [200, 201]:
            st.success("✅ Registration successful")
            go_to("login")
        else:
            st.error(response.json())

    st.divider()
    if st.button("⬅ Back to Login"):
        go_to("login")


# ==================================================
# 🧑‍💼 HR DASHBOARD
# ==================================================
def hr_dashboard():
    st.subheader("🧑‍💼 HR Dashboard")
    st.write(f"👋 Welcome, **{st.session_state.username}**")

    st.divider()
    st.markdown("### 📧 Send Email to Candidate")

    candidate_email = st.text_input("Candidate Email")
    subject = st.text_input("Email Subject")
    message = st.text_area("Email Message")

    if st.button("Send Email"):
        headers = {
            "Authorization": f"Bearer {st.session_state.token}"
        }

        response = requests.post(
            f"{API_BASE}/recruiter/send-email",
            params={
                "candidate_email": candidate_email,
                "subject": subject,
                "message": message
            },
            headers=headers
        )

        if response.status_code == 200:
            st.success("✅ Email sent successfully")
        else:
            st.error(response.json())


# ==================================================
# 👤 CANDIDATE DASHBOARD
# ==================================================
def candidate_dashboard():
    st.subheader("👤 Candidate Dashboard")
    st.write(f"👋 Welcome, **{st.session_state.username}**")

    if st.button("📩 View Received Emails"):
        headers = {
            "Authorization": f"Bearer {st.session_state.token}"
        }

        response = requests.get(
            f"{API_BASE}/candidate/emails",
            headers=headers
        )

        if response.status_code == 200:
            emails = response.json()
            if not emails:
                st.info("No emails received yet.")
            else:
                for mail in emails:
                    st.divider()
                    st.subheader(mail["subject"])
                    st.write(mail["message"])
                    st.caption(f"🕒 Sent at: {mail['sent_at']}")
        else:
            st.error(response.json())


# ==================================================
# 🚪 LOGOUT
# ==================================================
def logout():
    st.session_state.token = None
    st.session_state.role = None
    st.session_state.username = None
    go_to("login")


# ==================================================
# 🧠 MAIN CONTROLLER
# ==================================================
if st.session_state.page == "login":
    login_page()

elif st.session_state.page == "register":
    register_page()

elif st.session_state.page == "dashboard":
    if st.session_state.role == "recruiter":
        hr_dashboard()
    elif st.session_state.role == "user":
        candidate_dashboard()

    st.divider()
    if st.button("🚪 Logout"):
        logout()
