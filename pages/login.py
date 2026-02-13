import streamlit as st
import boto3
import os
import requests
from dotenv import load_dotenv

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(page_title="Login | NMK Recruitment Portal", layout="centered")

load_dotenv()

AWS_REGION = os.getenv("AWS_REGION")
COGNITO_CLIENT_ID = os.getenv("COGNITO_CLIENT_ID")
API_BASE = "http://127.0.0.1:8000"

cognito = boto3.client("cognito-idp", region_name=AWS_REGION)

# --------------------------------------------------
# SESSION STATE DEFAULTS
# --------------------------------------------------
if "show_reset" not in st.session_state:
    st.session_state.show_reset = False

# --------------------------------------------------
# GLOBAL STYLES
# --------------------------------------------------
st.markdown(
    """
    <style>
        /* Page container */
        .block-container {
            max-width: 420px;
            padding-top: 1.6rem;
        }


        /* Login card */
        div[data-testid="stForm"] {
            background: #ffffff;
            padding: 26px;
            border-radius: 18px;
            box-shadow: 0 12px 32px rgba(0, 0, 0, 0.08);
            border: 1px solid #e5e7eb;
        }

        /* Labels */
        label {
            font-weight: 500 !important;
            color: #374151 !important;
        }

        /* Inputs */
        input {
            background-color: #f3f4f6 !important;
            border-radius: 10px !important;
            height: 42px !important;
            padding-left: 12px !important;
            border: 1px solid #e5e7eb !important;
        }

        input:focus {
            background-color: #ffffff !important;
            border-color: #2563eb !important;
            box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.2) !important;
        }

        /* Login button */
        div[data-testid="stFormSubmitButton"] > button {
            background: linear-gradient(135deg, #2563eb, #1e40af) !important;
            color: white !important;
            border-radius: 12px !important;
            height: 44px !important;
            font-size: 15px !important;
            font-weight: 600 !important;
            border: none !important;
            width: 100% !important;
            box-shadow: 0 10px 22px rgba(37, 99, 235, 0.35) !important;
            transition: all 0.25s ease-in-out !important;
        }

        div[data-testid="stFormSubmitButton"] > button:hover {
            background: linear-gradient(135deg, #1d4ed8, #1e3a8a) !important;
            transform: translateY(-2px);
        }

        /* Secondary buttons */
        button[kind="secondary"] {
        border-radius: 10px !important;
            background: linear-gradient(135deg, #3b82f6, #2563eb) !important;
            color: #ffffff !important;
            font-weight: 600 !important;
            border: none !important;
            padding: 10px 18px !important;
            box-shadow: 0 8px 20px rgba(37, 99, 235, 0.35);
            transition: all 0.2s ease-in-out;
        }

        button[kind="secondary"]:hover {
            background: linear-gradient(135deg, #2563eb, #1e40af) !important;
            transform: translateY(-1px);
            box-shadow: 0 12px 28px rgba(37, 99, 235, 0.45);
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------
# LOGO
# --------------------------------------------------
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.abspath(os.path.join(CURRENT_DIR, "..", "assets", "nmk_logo.png"))

st.markdown("<div style='text-align:center; margin-top:20px;'>", unsafe_allow_html=True)

if os.path.exists(LOGO_PATH):
    st.image(LOGO_PATH, width=180)

st.markdown(
    """
    <h1 style='margin-top:16px; margin-bottom:6px; font-weight:700;'>
        NMK Recruitment Portal
    </h1>
    <p style='font-size:18px; color:#4b5563; margin-bottom:24px;'>
        Login
    </p>
    """,
    unsafe_allow_html=True
)

st.markdown("</div>", unsafe_allow_html=True)


# --------------------------------------------------
# LOGIN UI
# --------------------------------------------------
if not st.session_state.show_reset:

    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")

    if submit:
        if not email.strip() or not password.strip():
            st.error("Please enter email and password")
            st.stop()

        try:
            response = cognito.initiate_auth(
                ClientId=COGNITO_CLIENT_ID,
                AuthFlow="USER_PASSWORD_AUTH",
                AuthParameters={
                    "USERNAME": email.strip(),
                    "PASSWORD": password,
                },
            )

            auth_result = response["AuthenticationResult"]
            id_token = auth_result["IdToken"]
            access_token = auth_result["AccessToken"]

            st.session_state["id_token"] = id_token
            st.session_state["access_token"] = access_token

            backend_res = requests.post(
                f"{API_BASE}/auth/complete-login",
                headers={"Authorization": f"Bearer {id_token}"},
            )

            if backend_res.status_code != 200:
                st.error("Backend sync failed")
                st.text(backend_res.text)
                st.session_state.clear()
                st.stop()

            data = backend_res.json()
            st.session_state["user_id"] = data.get("user_id")
            st.session_state["role"] = data.get("role")
            st.session_state["recruiter_id"] = data.get("recruiter_id")

            st.success("Login successful")

            if data.get("role") == "recruiter":
                st.switch_page("pages/recruiter_dashboard.py")
            else:
                st.switch_page("pages/3_candidate_profile.py")

            st.stop()

        except cognito.exceptions.UserNotConfirmedException:
            st.error("Please verify your email before logging in.")
        except cognito.exceptions.NotAuthorizedException:
            st.error("Invalid email or password.")
        except Exception as e:
            st.error(f"Login failed: {e}")

    st.divider()

    if st.button("👤 Create Account", use_container_width=True):
        st.switch_page("pages/1_signup.py")

    if st.button("Forgot Password?", type="secondary"):
        st.session_state.show_reset = True
        st.rerun()

# --------------------------------------------------
# RESET PASSWORD
# --------------------------------------------------
if st.session_state.show_reset:
    st.subheader("Reset Password")

    email = st.text_input("Registered Email")
    code = st.text_input("Verification Code")
    new_password = st.text_input("New Password", type="password")
    confirm_password = st.text_input("Confirm New Password", type="password")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Send Reset Code"):
            if not email.strip():
                st.error("Email is required")
                st.stop()

            try:
                cognito.forgot_password(
                    ClientId=COGNITO_CLIENT_ID,
                    Username=email.strip(),
                )
                st.success("Reset code sent to your email")
            except Exception as e:
                st.error(str(e))

    with col2:
        if st.button("Reset Password"):
            if not email.strip() or not code.strip() or not new_password.strip():
                st.error("All fields are required")
                st.stop()

            if new_password != confirm_password:
                st.error("Passwords do not match")
                st.stop()

            try:
                cognito.confirm_forgot_password(
                    ClientId=COGNITO_CLIENT_ID,
                    Username=email.strip(),
                    ConfirmationCode=code.strip(),
                    Password=new_password,
                )

                st.success("Password reset successful")
                st.session_state.show_reset = False
                st.info("You can now login")

            except Exception as e:
                st.error(str(e))

    if st.button("← Back to Login", type="secondary"):
        st.session_state.show_reset = False
        st.rerun()
