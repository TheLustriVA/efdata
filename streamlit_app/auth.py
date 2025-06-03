"""
Simple authentication for Streamlit app
For v1, using Streamlit's built-in secrets management
"""
import streamlit as st
import hashlib
import hmac

def check_authentication():
    """
    Check if user is authenticated and return username and tier
    Returns: (username, tier) or (None, "free")
    """
    # For v1, we'll use simple session state
    # In production, use streamlit-authenticator or similar
    
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.username = None
        st.session_state.user_tier = "free"
    
    # Show login form if requested
    if st.session_state.get("show_login", False):
        show_login_form()
    
    return st.session_state.username, st.session_state.user_tier

def show_login_form():
    """Display login form in a modal"""
    with st.form("login_form"):
        st.subheader("Login to EFData")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        
        if submitted:
            # For demo purposes - in production, check against database
            if verify_credentials(username, password):
                st.session_state.authenticated = True
                st.session_state.username = username
                st.session_state.user_tier = get_user_tier_from_db(username)
                st.session_state.show_login = False
                st.success("Successfully logged in!")
                st.rerun()
            else:
                st.error("Invalid credentials")

def verify_credentials(username, password):
    """Verify user credentials"""
    # For demo - in production, check hashed password in database
    demo_users = {
        "demo": "demo123",
        "premium": "premium123"
    }
    
    return username in demo_users and demo_users[username] == password

def get_user_tier_from_db(username):
    """Get user tier from database"""
    # For demo purposes
    tier_map = {
        "demo": "free",
        "premium": "paid"
    }
    return tier_map.get(username, "free")

def get_user_tier():
    """Get current user's tier"""
    return st.session_state.get("user_tier", "free")