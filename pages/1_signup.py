import streamlit as st
import boto3
import os
from dotenv import load_dotenv

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
load_dotenv()
st.set_page_config(
    page_title="Create Account | NMK Recruitment Portal",
    layout="wide"
)

AWS_REGION = os.getenv("AWS_REGION")
COGNITO_CLIENT_ID = os.getenv("COGNITO_CLIENT_ID")

cognito = boto3.client("cognito-idp", region_name=AWS_REGION)

# --------------------------------------------------
# SESSION STATE DEFAULTS
# --------------------------------------------------
defaults = {
    "signup_role": "user",
    "signup_full_name": "",
    "signup_email": "",
    "signup_phone": "",
    "signup_password": "",
    "signup_company_name": "",
    "signup_industry": "",
    "signup_website": "",
    "signup_location": "",
    "signup_designation": "",
    "signup_success": False,
    "show_verify": False,
    "verify_success": False,
}
for k, v in defaults.items():
    st.session_state.setdefault(k, v)

# --------------------------------------------------
# GLOBAL STYLES
# --------------------------------------------------
st.markdown(
    """
    <style>
        .block-container {
            max-width: 1200px;
            padding-top: 2.5rem;
        }

        /* ===============================
           CREATE ACCOUNT (FORM SUBMIT)
           =============================== */
        div[data-testid="stFormSubmitButton"] > button {
            background: linear-gradient(135deg, #2563eb, #1e40af) !important;
            color: #ffffff !important;
            border-radius: 12px !important;
            height: 48px !important;
            font-size: 16px !important;
            font-weight: 600 !important;
            border: none !important;
            width: 100% !important;
            box-shadow: 0 10px 25px rgba(37, 99, 235, 0.35) !important;
            transition: all 0.25s ease-in-out !important;
        }

        div[data-testid="stFormSubmitButton"] > button:hover {
            background: linear-gradient(135deg, #1d4ed8, #1e3a8a) !important;
            transform: translateY(-2px);
            box-shadow: 0 14px 32px rgba(37, 99, 235, 0.45) !important;
        }

        /* ===============================
           VERIFY EMAIL BUTTON
           =============================== */
        div[data-testid="stForm"] div.stButton > button {
            background: linear-gradient(135deg, #22c55e, #15803d) !important;
            color: white !important;
            border-radius: 12px !important;
            height: 46px !important;
            font-weight: 600 !important;
            border: none !important;
            box-shadow: 0 8px 20px rgba(22, 163, 74, 0.35) !important;
        }

        div[data-testid="stForm"] div.stButton > button:hover {
            background: linear-gradient(135deg, #16a34a, #14532d) !important;
            transform: translateY(-1px);
        }

        /* ===============================
           BACK TO LOGIN (SECONDARY)
           =============================== */
        button[kind="secondary"] {
            background: linear-gradient(135deg, #0f172a, #020617) !important;
            color: #f9fafb !important;
            border-radius: 12px !important;
            height: 44px !important;
            font-weight: 500 !important;
            border: none !important;
            box-shadow: 0 8px 18px rgba(15, 23, 42, 0.4) !important;
        }

        button[kind="secondary"]:hover {
            background: linear-gradient(135deg, #020617, #000000) !important;
            transform: translateY(-1px);
        }
    </style>
    """,
    unsafe_allow_html=True,
)




# --------------------------------------------------
# LOGO
# --------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGO_PATH = os.path.join(BASE_DIR, "assets", "nmk_logo.png")

col_logo, col_space = st.columns([2, 8])

with col_logo:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=260)
    elif os.path.exists(os.path.join("assets", "nmk_logo.png")):
        st.image(os.path.join("assets", "nmk_logo.png"), width=260)
    else:
        st.warning("NMK logo not found")

# --------------------------------------------------
# TITLE
# --------------------------------------------------
st.markdown(
    "<h1 style='text-align:center; margin-top: 1rem;'>NMK Recruitment Portal</h1>",
    unsafe_allow_html=True,
)

st.markdown(
    "<h3 style='text-align:center; color:#555; font-weight:500;'>Create Account</h3>",
    unsafe_allow_html=True,
)

# --------------------------------------------------
# SUCCESS MESSAGES
# --------------------------------------------------
if st.session_state.signup_success:
    st.success("🎉 Account created successfully on NMK Recruitment Portal")
    st.info("Please check your registered email for the verification code.")

if st.session_state.verify_success:
    st.success("✅ Email verified successfully")
    st.info("You can now login to NMK Recruitment Portal.")

# --------------------------------------------------
# SIGNUP FORM
# --------------------------------------------------
role = st.selectbox(
    "Role *",
    ["user", "recruiter"],
    key="signup_role",
)
if role == "recruiter":
    st.info(
        "ℹ️ **Recruiter Registration Notice**\n\n"
        "If you are signing up as a recruiter, you must use your official "
        "**@nmkglobalinc.com** email address.\n\n"
        "Example: **example@nmkglobalinc.com**"
    )
with st.form("signup_form"):
    full_name = st.text_input("Full Name *", key="signup_full_name")
    email = st.text_input("Email Address *", key="signup_email")
    phone = st.text_input("Phone Number (+91XXXXXXXXXX)", key="signup_phone")
    password = st.text_input("Password *", type="password", key="signup_password")

    # Recruiter-only fields
    company_name = industry = website = location = designation = ""

    if role == "recruiter":
        st.divider()
        st.subheader("Company Details")

        company_name = st.text_input("Company Name *", key="signup_company_name")
        industry = st.text_input("Industry *", key="signup_industry")
        website = st.text_input("Company Website", key="signup_website")
        location = st.text_input("Company Location *", key="signup_location")
        designation = st.text_input("Your Designation *", key="signup_designation")

    submit = st.form_submit_button("Create Account", use_container_width=True,)

# --------------------------------------------------
# SIGNUP HANDLER
# --------------------------------------------------
if submit:
    if not full_name.strip() or not email.strip() or not password.strip():
        st.error("Please fill all required fields (*)")
        st.stop()

    if role == "recruiter":
        if not email.lower().endswith("@nmkglobalinc.com"):
            st.error("Recruiter email must be an @nmkglobalinc.com address")
            st.stop()

        if not company_name or not industry or not location or not designation:
            st.error("Please fill all mandatory recruiter fields")
            st.stop()

    try:
        cognito.sign_up(
            ClientId=COGNITO_CLIENT_ID,
            Username=email.strip(),
            Password=password,
            UserAttributes=[
                {"Name": "email", "Value": email.strip()},
                {"Name": "custom:full_name", "Value": full_name.strip()},
                {"Name": "phone_number", "Value": phone.strip()},
                {"Name": "custom:role", "Value": role},
                {"Name": "custom:company_name", "Value": company_name.strip()},
                {"Name": "custom:industry", "Value": industry.strip()},
                {"Name": "custom:website", "Value": website.strip()},
                {"Name": "custom:location", "Value": location.strip()},
                {"Name": "custom:designation", "Value": designation.strip()},
            ],
        )

        st.session_state.signup_success = True
        st.session_state.show_verify = True
        st.session_state.verify_success = False
        st.rerun()

    except cognito.exceptions.UsernameExistsException:
        st.warning("⚠️ Account already exists. Please verify your email or login.")
    except Exception as e:
        st.error(str(e))

# --------------------------------------------------
# VERIFY EMAIL SECTION
# --------------------------------------------------
if st.session_state.show_verify:
    st.divider()
    st.subheader("Verify Email")

    with st.form("verify_form", clear_on_submit=True):
        verify_email = st.text_input("Email used during signup")
        code = st.text_input("Verification Code")
        verify = st.form_submit_button("Verify Email")

    if verify:
        if not verify_email.strip() or not code.strip():
            st.error("Please enter both email and verification code")
            st.stop()

        try:
            cognito.confirm_sign_up(
                ClientId=COGNITO_CLIENT_ID,
                Username=verify_email.strip(),
                ConfirmationCode=code.strip(),
            )

            st.session_state.verify_success = True
            st.session_state.show_verify = False
            st.session_state.signup_success = False
            st.rerun()

        except Exception as e:
            st.error(str(e))

# --------------------------------------------------
# BACK TO LOGIN
# --------------------------------------------------
st.write("")
if st.button("← Back to Login", use_container_width=True, type="secondary"):
    st.switch_page("pages/login.py")
