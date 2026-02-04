import streamlit as st
import boto3
import os
from dotenv import load_dotenv

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
load_dotenv()
st.set_page_config(page_title="Create Account", layout="wide")

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
    </style>
    """,
    unsafe_allow_html=True,
)
# --------------------------------------------------
# LOGO
# --------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGO_PATH = os.path.join(BASE_DIR, "assets", "nmk_logo.png")


col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=400)
    elif os.path.exists(os.path.join("assets", "nmk_logo.png")):
        st.image(os.path.join("assets", "nmk_logo.png"), width=400)
    else:
        st.warning("Logo not found")
        
# --------------------------------------------------
# TITLE
# --------------------------------------------------
st.markdown(
    "<h1 style='text-align:center;'>Create Account</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='text-align:center;color:#666;'>Join NMK Recruitment Portal</p>",
    unsafe_allow_html=True,
)

# --------------------------------------------------
# SUCCESS MESSAGES
# --------------------------------------------------
if st.session_state.signup_success:
    st.success("🎉 Account created successfully!")
    st.info("Please check your email for the verification code.")

if st.session_state.verify_success:
    st.success("✅ Email verified successfully!")
    st.info("You can now login.")

# --------------------------------------------------
# SIGNUP FORM
# --------------------------------------------------
role = st.selectbox(
    "Role *",
    ["user", "recruiter"],
    key="signup_role",
)

with st.form("signup_form"):
    full_name = st.text_input("Full Name *", key="signup_full_name")
    email = st.text_input("Email Address *", key="signup_email")
    phone = st.text_input("Phone (+91XXXXXXXXXX)", key="signup_phone")
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

    submit = st.form_submit_button("Create Account", use_container_width=True)

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
            st.error("Please fill all recruiter mandatory fields")
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
        st.warning("⚠️ Account already exists. Please verify or login.")
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
if st.button("← Back to Login", use_container_width=True):
    st.switch_page("pages/login.py")
