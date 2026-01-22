import streamlit as st
from streamlit_js_eval import streamlit_js_eval

def require_auth():
    """
    Single source of truth for authentication.
    Must be called BEFORE any UI rendering on protected pages.
    """
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.user_type = None

    # Skip localStorage check if already authenticated this session
    if st.session_state.authenticated:
        return

    stored_auth = streamlit_js_eval(
        js_expressions="localStorage.getItem('bigsnapshot_auth')",
        key="auth_bootstrap"
    )

    if stored_auth and stored_auth not in ["", "null", None]:
        st.session_state.authenticated = True
        st.session_state.user_type = stored_auth
        return

    # Not authenticated - block access
    st.warning("⚠️ Please log in from the Home page first.")
    if st.button("🏠 Go to Home"):
        st.switch_page("Home.py")
    st.stop()
