import streamlit as st
from streamlit_js_eval import streamlit_js_eval
import time

def require_auth():
    """
    Single source of truth for authentication.
    Must be called BEFORE any UI rendering on protected pages.
    Uses localStorage for persistence across refreshes.
    """
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.user_type = None
    
    # Already authenticated this session - skip check
    if st.session_state.authenticated:
        return
    
    # Track if we've already tried to read localStorage
    if "auth_checked" not in st.session_state:
        st.session_state.auth_checked = False
    
    # Read from localStorage (async - returns None on first render)
    stored_auth = streamlit_js_eval(
        js_expressions="localStorage.getItem('bigsnapshot_auth')",
        key="auth_check_protected"
    )
    
    # If we got a valid auth from localStorage
    if stored_auth and stored_auth not in ["", "null", None]:
        st.session_state.authenticated = True
        st.session_state.user_type = stored_auth
        st.session_state.auth_checked = True
        return
    
    # First render - localStorage hasn't returned yet, wait for rerun
    if not st.session_state.auth_checked and stored_auth is None:
        st.session_state.auth_checked = True
        time.sleep(0.1)  # Brief pause for JS to execute
        st.rerun()
    
    # Not authenticated - block access
    st.warning("⚠️ Please log in from the Home page first.")
    if st.button("🏠 Go to Home"):
        st.switch_page("Home.py")
    st.stop()
