import streamlit as st

def require_auth():
    """
    FREE SEASON - No authentication required.
    All tools are open to everyone.
    """
    # Auto-authenticate everyone
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = True
        st.session_state.user_type = "Free User"
    return
