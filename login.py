import streamlit as st
import boto3
import os
import requests
from dotenv import load_dotenv

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(page_title="Login", layout="centered")

load_dotenv()

AWS_REGION = os.getenv("AWS_REGION")
COGNITO_CLIENT_ID = os.getenv("COGNITO_CLIENT_ID")
API_BASE = "http://localhost:8000"

cognito = boto3.client("cognito-idp", region_name=AWS_REGION)

# --------------------------------------------------
# SESSION STATE DEFAULTS
# --------------------------------------------------
if "show_reset" not in st.session_state:
    st.session_state.show_reset = False

# --------------------------------------------------
# LOGIN UI
# --------------------------------------------------
st.title("🔐 Login")

if not st.session_state.show_reset:

    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")

    if submit:
        if not email or not password:
            st.error("Please enter email and password")
            st.stop()

        try:
            # 🔐 Step 1: Cognito authentication
            response = cognito.initiate_auth(
                ClientId=COGNITO_CLIENT_ID,
                AuthFlow="USER_PASSWORD_AUTH",
                AuthParameters={
                    "USERNAME": email,
                    "PASSWORD": password
                }
            )

            auth_result = response["AuthenticationResult"]

            # ✅ IMPORTANT: store BOTH tokens
            id_token = auth_result["IdToken"]
            access_token = auth_result["AccessToken"]

            st.session_state["id_token"] = id_token          # for backend sync
            st.session_state["access_token"] = access_token  # for API auth

            # 🔄 Step 2: Backend sync (uses ID TOKEN)
            backend_res = requests.post(
                f"{API_BASE}/auth/complete-login",
                headers={
                    "Authorization": f"Bearer {id_token}"
                }
            )

            if backend_res.status_code != 200:
                st.error("Backend sync failed")
                st.text(backend_res.text)
                st.session_state.clear()
                st.stop()

            # ✅ Step 3: Store backend user info
            data = backend_res.json()
            st.session_state["user_id"] = data.get("user_id")
            st.session_state["role"] = data.get("role")

            st.success("Login successful 🎉")

            # 👉 Redirect to job listings
            if data.get("role") == "recruiter":
                st.switch_page("pages/recruiter_dashboard.py")
            else:
                st.switch_page("pages/4_job_listings.py")

            st.stop()

        except cognito.exceptions.UserNotConfirmedException:
            st.error("Please verify your email before logging in.")

        except cognito.exceptions.NotAuthorizedException:
            st.error("Invalid email or password.")

        except Exception as e:
            st.error(f"Login failed: {e}")

    # --------------------------------------------------
    # FORGOT PASSWORD
    # --------------------------------------------------
    if st.button("Forgot Password?"):
        st.session_state.show_reset = True
        st.rerun()

# --------------------------------------------------
# RESET PASSWORD SECTION
# --------------------------------------------------
if st.session_state.show_reset:
    st.subheader("🔑 Reset Password")

    email = st.text_input("Registered Email")
    code = st.text_input("Verification Code")
    new_password = st.text_input("New Password", type="password")
    confirm_password = st.text_input("Confirm New Password", type="password")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Send Reset Code"):
            try:
                cognito.forgot_password(
                    ClientId=COGNITO_CLIENT_ID,
                    Username=email,
                )
                st.success("Reset code sent to your email 📩")
            except Exception as e:
                st.error(str(e))

    with col2:
        if st.button("Reset Password"):
            if new_password != confirm_password:
                st.error("Passwords do not match")
                st.stop()

            try:
                cognito.confirm_forgot_password(
                    ClientId=COGNITO_CLIENT_ID,
                    Username=email,
                    ConfirmationCode=code,
                    Password=new_password,
                )

                st.success("Password reset successful ✅")
                st.session_state.show_reset = False
                st.info("You can now login with your new password")

            except Exception as e:
                st.error(str(e))

    if st.button("⬅ Back to Login"):
        st.session_state.show_reset = False
        st.rerun()
