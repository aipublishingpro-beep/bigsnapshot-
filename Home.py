import streamlit as st
from datetime import datetime
import pytz

st.set_page_config(page_title="Big Snapshot", page_icon="📊", layout="wide")

# ========== HIDE STREAMLIT STUFF ==========
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.stDeployButton {display: none;}
[data-testid="stSidebarNav"] {display: none;}
</style>
""", unsafe_allow_html=True)

# ========== GA4 TRACKING ==========
st.markdown("""
<script async src="https://www.googletagmanager.com/gtag/js?id=G-NQKY5VQ376"></script>
<script>window.dataLayer = window.dataLayer || [];function gtag(){dataLayer.push(arguments);}gtag('js', new Date());gtag('config', 'G-NQKY5VQ376');</script>
""", unsafe_allow_html=True)

# ========== PASSWORD SYSTEM ==========
VALID_PASSWORDS = {
    "WILLIE1228": "Owner",
    "BETAUSER": "Beta Tester",
}

# ========== INIT SESSION STATE ==========
if "gate_passed" not in st.session_state:
    st.session_state.gate_passed = False
if "user_role" not in st.session_state:
    st.session_state.user_role = None

eastern = pytz.timezone("US/Eastern")
now = datetime.now(eastern)

# ========== LOGIN SCREEN ==========
if not st.session_state.gate_passed:
    st.title("📊 BIG SNAPSHOT")
    st.subheader("Sports & Weather Analytics for Kalshi")
    
    st.markdown("---")
    
    password_input = st.text_input("Enter Access Code:", type="password", key="pwd")
    
    if st.button("🔓 Enter", type="primary", use_container_width=True):
        if password_input.upper() in VALID_PASSWORDS:
            st.session_state.gate_passed = True
            st.session_state.user_role = VALID_PASSWORDS[password_input.upper()]
            st.rerun()
        elif password_input:
            st.error("❌ Invalid access code")
    
    st.markdown("---")
    
    # Beta signup callout
    st.markdown("""
    <div style="background:linear-gradient(135deg,#1a1a2e,#16213e);border-radius:12px;padding:20px;text-align:center;border:2px solid #ffd700;margin-top:20px">
        <h3 style="color:#ffd700;margin:0">🚀 Want Beta Access?</h3>
        <p style="color:#fff;margin:10px 0">Get early access to all Edge Finder tools</p>
        <p style="color:#888;font-size:0.9em">Email: <strong>aipublishingpro@gmail.com</strong></p>
    </div>
    """, unsafe_allow_html=True)
    
    st.stop()

# ========== LOGGED IN - SHOW DASHBOARD ==========
st.title("📊 BIG SNAPSHOT")
st.caption(f"Logged in as: {st.session_state.user_role}")

st.markdown("---")
st.subheader("Select an Edge Finder:")

# ========== THREE APP CARDS ==========
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div style="background:linear-gradient(135deg,#1a1a2e,#16213e);border-radius:12px;padding:25px;text-align:center;border-left:4px solid #00ff00;min-height:280px">
        <div style="font-size:3em;margin-bottom:10px">🏀</div>
        <h3 style="color:#fff;margin:0">NBA Edge Finder</h3>
        <p style="color:#888;font-size:0.9em;margin:10px 0">8-Factor ML Model</p>
        <p style="color:#00ff00;font-weight:bold">✅ LIVE</p>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/2_NBA.py", label="Open NBA", use_container_width=True)

with col2:
    st.markdown("""
    <div style="background:linear-gradient(135deg,#1a1a2e,#16213e);border-radius:12px;padding:25px;text-align:center;border-left:4px solid #00aaff;min-height:280px">
        <div style="font-size:3em;margin-bottom:10px">🏈</div>
        <h3 style="color:#fff;margin:0">NFL Edge Finder</h3>
        <p style="color:#888;font-size:0.9em;margin:10px 0">10-Factor ML Model</p>
        <p style="color:#00ff00;font-weight:bold">✅ LIVE</p>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/1_NFL.py", label="Open NFL", use_container_width=True)

with col3:
    st.markdown("""
    <div style="background:linear-gradient(135deg,#1a1a2e,#16213e);border-radius:12px;padding:25px;text-align:center;border-left:4px solid #ff6600;min-height:280px">
        <div style="font-size:3em;margin-bottom:10px">🌡️</div>
        <h3 style="color:#fff;margin:0">Temp Edge Finder</h3>
        <p style="color:#888;font-size:0.9em;margin:10px 0">NWS Forecast Model</p>
        <p style="color:#00ff00;font-weight:bold">✅ LIVE</p>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/3_Temp.py", label="Open Temp", use_container_width=True)

# ========== HOW IT WORKS ==========
st.markdown("---")
st.subheader("How It Works")
st.markdown("""
1. **Select an Edge Finder** — Choose NBA, NFL, or Temperature markets
2. **Review the signals** — Our models identify mispriced Kalshi contracts  
3. **Click BUY** — Direct links to Kalshi order pages
4. **Track positions** — Monitor your active trades in real-time
""")

# ========== BETA SIGNUP ==========
st.markdown("---")
st.markdown("""
<div style="background:linear-gradient(135deg,#2d1f3d,#1a1a2e);border-radius:12px;padding:25px;text-align:center;border:2px solid #ffd700">
    <h3 style="color:#ffd700;margin:0">🚀 Enjoying the Beta?</h3>
    <p style="color:#fff;margin:15px 0">Share feedback or invite friends to join</p>
    <p style="color:#888">Email: <strong>aipublishingpro@gmail.com</strong></p>
</div>
""", unsafe_allow_html=True)

# ========== FOOTER ==========
st.markdown("---")
col1, col2 = st.columns(2)
with col1:
    st.caption(f"🕐 {now.strftime('%I:%M %p ET')} | 📅 {now.strftime('%B %d, %Y')}")
with col2:
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.gate_passed = False
        st.session_state.user_role = None
        st.rerun()

st.caption("⚠️ Educational analysis only. Not financial advice. | bigsnapshot.com")
