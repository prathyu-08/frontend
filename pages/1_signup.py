import streamlit as st
import boto3
import os
from dotenv import load_dotenv

load_dotenv()

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
st.set_page_config(page_title="Signup", layout="centered")

AWS_REGION = os.getenv("AWS_REGION")
COGNITO_CLIENT_ID = os.getenv("COGNITO_CLIENT_ID")

cognito = boto3.client("cognito-idp", region_name=AWS_REGION)

st.title("Create Account")

# --------------------------------------------------
# SIGNUP FORM
# --------------------------------------------------
with st.form("signup_form"):
    full_name = st.text_input("Full Name")
    email = st.text_input("Email")
    phone = st.text_input("Phone (+91XXXXXXXXXX)")
    password = st.text_input("Password", type="password")

    role = st.selectbox("Role", options=["user", "recruiter"])

    # Recruiter-only fields
    company_name = industry = website = location = designation = ""

    if role == "recruiter":
        st.subheader("Company Details")
        company_name = st.text_input("Company Name")
        industry = st.text_input("Industry")
        website = st.text_input("Company Website")
        location = st.text_input("Company Location")
        designation = st.text_input("Your Designation")

    submit = st.form_submit_button("Sign Up")

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

        st.success("Signup successful 🎉")
        st.info("Please check your email for the verification code.")

    except Exception as e:
        st.error(str(e))

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
