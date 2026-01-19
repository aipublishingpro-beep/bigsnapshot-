import streamlit as st

st.set_page_config(page_title="Big Snapshot", page_icon="📊", layout="wide")

# ========== HIDE MENUS ==========
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.stDeployButton {display: none;}
[data-testid="stToolbar"] {display: none;}
</style>
""", unsafe_allow_html=True)

# ========== GA4 ==========
st.markdown("""
<script async src="https://www.googletagmanager.com/gtag/js?id=G-NQKY5VQ376"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());gtag('config','G-NQKY5VQ376');</script>
""", unsafe_allow_html=True)

# ========== PASSWORD GATE ==========
VALID_PASSWORDS = {
    "Willie1228": "Owner",
    "BETAUSER": "Beta Tester",
}

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.user_type = None

if not st.session_state.authenticated:
    st.title("📊 Big Snapshot")
    st.subheader("Sports Analytics for Kalshi Prediction Markets")
    
    st.divider()
    
    st.markdown("**Enter password to access:**")
    password = st.text_input("Password", type="password")
    
    if st.button("Enter", type="primary"):
        if password in VALID_PASSWORDS:
            st.session_state.authenticated = True
            st.session_state.user_type = VALID_PASSWORDS[password]
            st.rerun()
        else:
            st.error("❌ Invalid password")
    
    st.divider()
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); border: 2px solid #00ff00; padding: 30px; border-radius: 10px; text-align: center; margin-top: 20px;">
        <h2 style="color: #00ff00; margin-bottom: 10px;">🎯 Want FREE Access?</h2>
        <p style="color: white; font-size: 18px; margin-bottom: 15px;">Become a Beta Tester!</p>
        <p style="color: #00ff00; font-size: 24px; font-weight: bold;">📧 aipublishingpro@gmail.com</p>
        <p style="color: #888; font-size: 14px; margin-top: 10px;">Email for consideration and password</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ========== MAIN CONTENT (AFTER LOGIN) ==========
st.title("📊 Big Snapshot")
st.caption(f"Logged in as: {st.session_state.user_type}")

st.divider()

st.subheader("Select an Edge Finder:")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div style="background: #1a1a2e; border-left: 4px solid #00ff00; padding: 20px; border-radius: 4px; text-align: center;">
        <h2>🏀</h2>
        <h3 style="color: white;">NBA Edge Finder</h3>
        <p style="color: #888;">8-Factor ML Model</p>
        <p style="color: #00ff00;">✅ LIVE</p>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/2_🏀_NBA_Edge.py", label="Open NBA", use_container_width=True)

with col2:
    st.markdown("""
    <div style="background: #1a1a2e; border-left: 4px solid #00aaff; padding: 20px; border-radius: 4px; text-align: center;">
        <h2>🏈</h2>
        <h3 style="color: white;">NFL Edge Finder</h3>
        <p style="color: #888;">10-Factor ML Model</p>
        <p style="color: #00aaff;">✅ LIVE</p>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/1_🏈_NFL_Edge.py", label="Open NFL", use_container_width=True)

with col3:
    st.markdown("""
    <div style="background: #1a1a2e; border-left: 4px solid #ffaa00; padding: 20px; border-radius: 4px; text-align: center;">
        <h2>🌡️</h2>
        <h3 style="color: white;">Temp Edge Finder</h3>
        <p style="color: #888;">NWS Forecast Model</p>
        <p style="color: #ffaa00;">🔧 COMING SOON</p>
    </div>
    """, unsafe_allow_html=True)
    st.button("Coming Soon", disabled=True, use_container_width=True)

st.divider()

st.markdown("""
### How It Works

1. **Select an Edge Finder** above
2. **Review ML picks** based on our factor models
3. **Click BUY** to go directly to Kalshi market
4. **Track positions** and monitor live scores

### Disclaimer

⚠️ This tool provides market signals, not predictions. Not financial advice. For entertainment only.
""")

st.divider()
st.caption("📧 Feedback: aipublishingpro@gmail.com | v1.0")
