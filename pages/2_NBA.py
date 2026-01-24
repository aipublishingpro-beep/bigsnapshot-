cookie_manager.set(
    "authenticated", 
    "true", 
    expires_at=datetime.now() + timedelta(days=30),
    key="set_auth_cookie",
    path="/",                # important on Streamlit Cloud
    domain=None              # or your custom domain if any
)
st.session_state.authenticated = True
st.switch_page("YourMainPage.py")  # or st.rerun()
