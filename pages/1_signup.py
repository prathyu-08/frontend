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
# GLOBAL STYLES (WIDE SAAS LAYOUT)
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
    st.image(LOGO_PATH, width=400)

# --------------------------------------------------
# TITLE
# --------------------------------------------------
st.markdown(
    "<h1 style='text-align:center;margin-bottom:0;'>Create Account</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='text-align:center;color:#666;margin-bottom:30px;'>Join NMK Recruitment Portal</p>",
    unsafe_allow_html=True,
)

# --------------------------------------------------
# SIGNUP FORM
# --------------------------------------------------
role = st.selectbox("Role", ["user", "recruiter"])
with st.form("signup_form"):

    st.subheader("Basic Information")
    full_name = st.text_input("Full Name")
    email = st.text_input("Email Address")
    phone = st.text_input("Phone (+91XXXXXXXXXX)")
    password = st.text_input("Password", type="password")

    # Recruiter-only fields
    company_name = industry = website = location = designation = ""

    if role == "recruiter":
        st.divider()
        st.subheader("Company Details")

        company_name = st.text_input("Company Name")
        industry = st.text_input("Industry")
        website = st.text_input("Company Website")
        location = st.text_input("Company Location")
        designation = st.text_input("Your Designation")

    st.write("")
    submit = st.form_submit_button("Create Account", use_container_width=True)

# --------------------------------------------------
# SUBMIT HANDLER
# --------------------------------------------------
if submit:
    if not full_name.strip() or not email.strip() or not password.strip():
        st.error("Please fill all required fields")
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

                # recruiter-only attributes
                {"Name": "custom:company_name", "Value": company_name.strip()},
                {"Name": "custom:industry", "Value": industry.strip()},
                {"Name": "custom:website", "Value": website.strip()},
                {"Name": "custom:location", "Value": location.strip()},
                {"Name": "custom:designation", "Value": designation.strip()},
            ],
        )

        st.success("Account created successfully 🎉")
        st.info("Please check your email for the verification code.")

    except Exception as e:
        st.error(str(e))

# --------------------------------------------------
# BACK TO LOGIN
# --------------------------------------------------
st.write("")
if st.button("← Back to Login", use_container_width=True):
    st.switch_page("pages/login.py")

# --------------------------------------------------
# VERIFY EMAIL
# --------------------------------------------------
st.divider()
st.subheader("Verify Email")

with st.form("verify_form"):
    verify_email = st.text_input("Email used during signup")
    code = st.text_input("Verification Code")
    verify = st.form_submit_button("Verify")

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

        st.success("Email verified successfully ✅")
        st.info("You can now login.")

    except Exception as e:
        st.error(str(e))