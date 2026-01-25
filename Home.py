import streamlit as st

st.set_page_config(page_title="BigSnapshot", page_icon="🎯", layout="wide")

# ============================================================
# DO NOT CALL require_auth() HERE - THIS IS THE LOGIN PAGE
# ============================================================

from streamlit_js_eval import streamlit_js_eval

# Initialize session state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.user_type = None

# Check localStorage for existing auth
stored_auth = streamlit_js_eval(
    js_expressions="localStorage.getItem('bigsnapshot_auth')",
    key="home_auth_check"
)

if stored_auth and stored_auth not in ["", "null", None]:
    st.session_state.authenticated = True
    st.session_state.user_type = stored_auth

# Password
VALID_PASSWORDS = {
    "WILLIE1228": "Owner",
    "SNAPCRACKLE2026": "Paid Subscriber",
}

# ============================================================
# LOGGED IN VIEW
# ============================================================
if st.session_state.authenticated:
    st.title("🎯 BigSnapshot")
    st.success(f"✅ Logged in as: {st.session_state.user_type}")
    
    st.markdown("### 🔥 Live Tools")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🏀 NBA Edge", use_container_width=True):
            st.switch_page("pages/2_NBA.py")
        if st.button("🏈 NFL Edge", use_container_width=True):
            st.switch_page("pages/1_NFL.py")
        if st.button("🏒 NHL Edge", use_container_width=True):
            st.switch_page("pages/3_NHL.py")
    with col2:
        if st.button("⚾ MLB Edge", use_container_width=True):
            st.switch_page("pages/4_MLB.py")
        if st.button("⚽ Soccer Edge", use_container_width=True):
            st.switch_page("pages/8_Soccer.py")
        if st.button("🏈 NCAA Edge", use_container_width=True):
            st.switch_page("pages/7_NCAA.py")
    with col3:
        if st.button("🌡️ Temp Edge (FREE)", use_container_width=True):
            st.switch_page("pages/5_Temp.py")
        if st.button("📊 Economics", use_container_width=True):
            st.switch_page("pages/9_Economics.py")
    
    st.divider()
    
    if st.button("🚪 Logout"):
        streamlit_js_eval(js_expressions="localStorage.removeItem('bigsnapshot_auth')", key="logout")
        st.session_state.authenticated = False
        st.session_state.user_type = None
        st.rerun()

# ============================================================
# LOGIN VIEW (NOT LOGGED IN)
# ============================================================
else:
    st.title("🎯 BigSnapshot")
    st.markdown("### Edge-Finding Tools for Prediction Markets")
    
    st.divider()
    
    # Marketing
    st.markdown("""
    <div style="text-align: center; padding: 20px;">
        <h2 style="color: #fff;">Stop Switching Tabs. Start Making Cleaner Decisions.</h2>
        <p style="color: #888;">BigSnapshot compresses your research into one screen.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Stripe button
    st.markdown("""
    <div style="text-align: center; margin: 30px 0;">
        <a href="https://buy.stripe.com/8wMaGP5pSgGU5NYfZ2" target="_blank" style="background: linear-gradient(90deg, #00C853, #00E676); color: #000; padding: 15px 40px; border-radius: 8px; text-decoration: none; font-weight: bold; font-size: 18px;">💳 Get Access — $49.99/month</a>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # Free Temp button
    st.markdown("""
    <div style="text-align: center; margin: 20px 0;">
        <p style="color: #888;">Want to try before you buy?</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🌡️ Try Temp Edge Finder FREE", use_container_width=True, type="secondary"):
            st.switch_page("pages/5_Temp.py")
    
    st.divider()
    
    # Password entry
    st.markdown("### 🔑 Already Paid?")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        password = st.text_input("Enter your password", type="password", placeholder="Password")
        if st.button("🔓 LOGIN", use_container_width=True, type="primary"):
            if password.upper() in VALID_PASSWORDS:
                st.session_state.authenticated = True
                st.session_state.user_type = VALID_PASSWORDS[password.upper()]
                # Save to localStorage
                streamlit_js_eval(
                    js_expressions=f"localStorage.setItem('bigsnapshot_auth', '{st.session_state.user_type}')",
                    key="save_auth"
                )
                st.rerun()
            else:
                st.error("❌ Invalid password")
    
    st.divider()
    st.caption("Questions? Email support@bigsnapshot.com")
