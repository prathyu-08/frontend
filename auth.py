import streamlit as st

# -------------------------------
# LOGIN CHECK
# -------------------------------
def require_login():
    """
    Ensures user is authenticated.
    If not logged in, redirect to landing page.
    """
    if "id_token" not in st.session_state:
        st.switch_page("app.py")
        st.stop()

# -------------------------------
# ROLE CHECK
# -------------------------------
def require_role(role: str):
    """
    Ensures user has the required role.
    """
    require_login()
    if st.session_state.get("role") != role:
        st.error("⛔ Unauthorized access")
        st.stop()

# -------------------------------
# CURRENT USER
# -------------------------------
def get_current_user():
    """
    Returns current logged-in user info.
    """
    if "user_id" not in st.session_state:
        return None

    return {
        "user_id": st.session_state.get("user_id"),
        "role": st.session_state.get("role"),
    }

# -------------------------------
# AUTH HEADERS
# -------------------------------
def auth_headers():
    """
    Returns Authorization headers for backend API calls.
    """
    return {
        "Authorization": f"Bearer {st.session_state['id_token']}"
    }

# -------------------------------
# LOGOUT
# -------------------------------
def logout():
    """
    Clears session and redirects to landing page.
    """
    st.session_state.clear()
    st.switch_page("app.py")
