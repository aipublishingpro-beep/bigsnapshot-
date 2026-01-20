import streamlit as st
from datetime import datetime
import pytz

st.set_page_config(page_title="BigSnapshot", page_icon="📊", layout="wide")

# ========== HIDE STREAMLIT STUFF ==========
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.stDeployButton {display: none;}
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
    st.markdown("""
    <div style="text-align: center; padding: 40px 20px;">
        <div style="font-size: 60px;">📊</div>
        <h1 style="font-size: 48px; font-weight: 800; margin: 10px 0;">BigSnapshot</h1>
        <p style="color: #888; font-size: 18px;">Prediction Market Edge Finder</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Beta signup callout
    st.markdown("""
    <div style="max-width: 500px; margin: 20px auto; padding: 25px;
                background: linear-gradient(135deg, #1a3a2a 0%, #2a4a3a 100%);
                border-radius: 16px; border: 1px solid #3a5a4a; text-align: center;">
        <p style="color: #00c853; font-size: 18px; font-weight: 700; margin-bottom: 10px;">
            🚀 NOW IN PRIVATE BETA
        </p>
        <p style="color: #ccc; font-size: 14px; margin-bottom: 15px;">
            Want access? Email us to request a beta invite.
        </p>
        <a href="mailto:aipublishingpro@gmail.com?subject=BigSnapshot%20Beta%20Request&body=I%20would%20like%20to%20join%20the%20BigSnapshot%20beta%20program."
           style="display: inline-block; background: #00c853; color: #000; padding: 12px 30px;
                  border-radius: 8px; font-weight: 700; text-decoration: none; font-size: 14px;">
            📧 REQUEST BETA ACCESS
        </a>
    </div>
    """, unsafe_allow_html=True)
    
    # Password entry
    st.markdown("<p style='text-align:center; color:#888; margin-top:30px;'>Already a beta tester? Enter password:</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        password = st.text_input("Password", type="password", key="login_pw", label_visibility="collapsed", placeholder="Enter password")
        
        if st.button("🔓 UNLOCK", use_container_width=True, type="primary"):
            if password.upper() in VALID_PASSWORDS:
                st.session_state.gate_passed = True
                st.session_state.user_role = VALID_PASSWORDS[password.upper()]
                st.rerun()
            else:
                st.error("❌ Invalid password")
        
        st.markdown("<p style='text-align:center; color:#555; font-size:11px; margin-top:15px;'>Contact aipublishingpro@gmail.com for access</p>", unsafe_allow_html=True)
    
    st.stop()

# ========== AUTHENTICATED - SHOW APP HUB ==========
st.markdown("""
<div style="text-align: center; padding: 30px 20px 20px 20px;">
    <h1 style="font-size: 42px; font-weight: 800; margin-bottom: 5px;">📊 BigSnapshot</h1>
    <p style="color: #888; font-size: 16px;">Select an app below</p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ========== APP CARDS ==========
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div style='background:linear-gradient(135deg,#1a1a2e,#0a0a1e);padding:30px;border-radius:20px;border:2px solid #00aa00;text-align:center;min-height:200px'>
    <div style='font-size:3em'>🏈</div>
    <div style='font-size:1.4em;color:#00aa00;font-weight:bold;margin-top:10px'>NFL Edge Finder</div>
    <div style='color:#888;margin-top:8px;font-size:0.85em'>10-Factor Model</div>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/1_NFL.py", label="🏈 Open NFL", use_container_width=True)

with col2:
    st.markdown("""
    <div style='background:linear-gradient(135deg,#1a2e1a,#0a1e0a);padding:30px;border-radius:20px;border:2px solid #ff6600;text-align:center;min-height:200px'>
    <div style='font-size:3em'>🏀</div>
    <div style='font-size:1.4em;color:#ff6600;font-weight:bold;margin-top:10px'>NBA Edge Finder</div>
    <div style='color:#888;margin-top:8px;font-size:0.85em'>12-Factor Model</div>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/2_NBA.py", label="🏀 Open NBA", use_container_width=True)

with col3:
    st.markdown("""
    <div style='background:linear-gradient(135deg,#1a1a2e,#0a0a1e);padding:30px;border-radius:20px;border:2px solid #4dabf7;text-align:center;min-height:200px'>
    <div style='font-size:3em'>🏒</div>
    <div style='font-size:1.4em;color:#4dabf7;font-weight:bold;margin-top:10px'>NHL Edge Finder</div>
    <div style='color:#888;margin-top:8px;font-size:0.85em'>10-Factor Model</div>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/3_NHL.py", label="🏒 Open NHL", use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

col4, col5, col6 = st.columns(3)

with col4:
    st.markdown("""
    <div style='background:linear-gradient(135deg,#2e1a2e,#1e0a1e);padding:30px;border-radius:20px;border:2px solid #e040fb;text-align:center;min-height:200px'>
    <div style='font-size:3em'>🌡️</div>
    <div style='font-size:1.4em;color:#e040fb;font-weight:bold;margin-top:10px'>Temp Edge Finder</div>
    <div style='color:#888;margin-top:8px;font-size:0.85em'>NWS vs Kalshi</div>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/5_Temp.py", label="🌡️ Open Temp", use_container_width=True)

with col5:
    st.markdown("""
    <div style='background:linear-gradient(135deg,#2e2e1a,#1e1e0a);padding:30px;border-radius:20px;border:2px solid #555;text-align:center;min-height:200px;opacity:0.6'>
    <div style='font-size:3em'>⚾</div>
    <div style='font-size:1.4em;color:#888;font-weight:bold;margin-top:10px'>MLB Edge Finder</div>
    <div style='color:#666;margin-top:8px;font-size:0.85em'>Coming Soon</div>
    </div>
    """, unsafe_allow_html=True)
    st.button("⚾ Coming Soon", use_container_width=True, disabled=True, key="mlb_btn")

with col6:
    st.markdown("""
    <div style='background:linear-gradient(135deg,#2e2e1a,#1e1e0a);padding:30px;border-radius:20px;border:2px solid #555;text-align:center;min-height:200px;opacity:0.6'>
    <div style='font-size:3em'>🗳️</div>
    <div style='font-size:1.4em;color:#888;font-weight:bold;margin-top:10px'>Politics Edge Finder</div>
    <div style='color:#666;margin-top:8px;font-size:0.85em'>Coming Summer 2026</div>
    </div>
    """, unsafe_allow_html=True)
    st.button("🗳️ Coming Soon", use_container_width=True, disabled=True, key="pol_btn")

st.markdown("---")

# Footer
st.markdown(f"""
<div style="text-align: center; padding: 20px; color: #555;">
    <p style="font-size: 12px;">⚠️ For entertainment only. Not financial advice.</p>
    <p style="font-size: 11px;">📧 aipublishingpro@gmail.com | bigsnapshot.com</p>
    <p style="font-size: 10px; color: #444;">{now.strftime('%I:%M %p ET')} | {now.strftime('%B %d, %Y')}</p>
</div>
""", unsafe_allow_html=True)
