import streamlit as st

st.set_page_config(
    page_title="BigSnapshot | Prediction Market Edge Finder",
    page_icon="📊",
    layout="wide"
)

# ============================================================
# GA4 TRACKING
# ============================================================
st.markdown("""
<script async src="https://www.googletagmanager.com/gtag/js?id=G-NQKY5VQ376"></script>
<script>window.dataLayer = window.dataLayer || [];function gtag(){dataLayer.push(arguments);}gtag('js', new Date());gtag('config', 'G-NQKY5VQ376');</script>
""", unsafe_allow_html=True)

# ============================================================
# SESSION STATE
# ============================================================
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

# ============================================================
# PASSWORD CONFIG
# ============================================================
VALID_PASSWORDS = {
    "WILLIE1228": "Owner",
    "BETAUSER": "Beta Tester",
}

# ============================================================
# CUSTOM CSS
# ============================================================
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .stApp {
        background: linear-gradient(180deg, #0a0a0f 0%, #1a1a2e 100%);
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# LOGIN PAGE
# ============================================================
if not st.session_state.authenticated:
    st.markdown("""
    <div style="text-align: center; padding: 60px 20px 30px 20px;">
        <div style="font-size: 70px; margin-bottom: 15px;">📊</div>
        <h1 style="font-size: 52px; font-weight: 800; color: #fff; margin-bottom: 10px;">BigSnapshot</h1>
        <p style="color: #888; font-size: 20px; margin-bottom: 10px;">Prediction Market Edge Finder</p>
        <p style="color: #555; font-size: 14px;">Structural analysis for Kalshi markets</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="max-width: 500px; margin: 30px auto; padding: 30px;
                background: linear-gradient(135deg, #1a3a2a 0%, #2a4a3a 100%);
                border-radius: 16px; border: 1px solid #3a5a4a; text-align: center;">
        <p style="color: #00c853; font-size: 18px; font-weight: 700; margin-bottom: 10px;">🚀 NOW IN PRIVATE BETA</p>
        <p style="color: #ccc; font-size: 14px; margin-bottom: 20px;">Want access? Email us to request a beta invite.</p>
        <a href="mailto:aipublishingpro@gmail.com?subject=BigSnapshot%20Beta%20Request&body=I%20would%20like%20to%20join%20the%20BigSnapshot%20beta%20program."
           style="display: inline-block; background: #00c853; color: #000; padding: 12px 30px;
                  border-radius: 8px; font-weight: 700; text-decoration: none; font-size: 14px;">
            📧 REQUEST BETA ACCESS
        </a>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<p style="text-align:center; color:#888; margin-top:30px;">Already a beta tester? Enter your password:</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        password_input = st.text_input("Password", type="password", label_visibility="collapsed", placeholder="Enter password")
        if st.button("🔓 UNLOCK", use_container_width=True, type="primary"):
            if password_input.upper() in VALID_PASSWORDS:
                st.session_state.authenticated = True
                st.session_state.user_type = VALID_PASSWORDS[password_input.upper()]
                st.rerun()
            else:
                st.error("❌ Invalid password")
        st.markdown('<p style="text-align:center; color:#555; font-size:11px; margin-top:20px;">Contact aipublishingpro@gmail.com for access</p>', unsafe_allow_html=True)
    
    st.stop()

# ============================================================
# AUTHENTICATED - APP HUB
# ============================================================
st.markdown("""
<div style="text-align: center; padding: 40px 20px 20px 20px;">
    <div style="font-size: 60px; margin-bottom: 10px;">📊</div>
    <h1 style="font-size: 48px; font-weight: 800; color: #fff; margin-bottom: 5px;">BigSnapshot</h1>
    <p style="color: #888; font-size: 18px;">Prediction Market Edge Finder</p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ============================================================
# APP CARDS - ROW 1
# ============================================================
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div style='background:linear-gradient(135deg,#1a1a2e,#0a0a1e);padding:30px;border-radius:20px;border:2px solid #00aa00;text-align:center;min-height:200px;margin-bottom:10px'>
        <div style='font-size:3.5em'>🏈</div>
        <div style='font-size:1.5em;color:#00aa00;font-weight:bold;margin-top:15px'>NFL Edge Finder</div>
        <div style='color:#888;margin-top:10px;font-size:0.9em'>10-Factor Model</div>
        <div style='margin-top:15px'><span style='background:#00aa00;color:#000;padding:4px 12px;border-radius:12px;font-size:0.75em;font-weight:700'>LIVE</span></div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🏈 Open NFL", use_container_width=True, key="nfl_btn"):
        st.switch_page("pages/1_NFL.py")

with col2:
    st.markdown("""
    <div style='background:linear-gradient(135deg,#1a2e1a,#0a1e0a);padding:30px;border-radius:20px;border:2px solid #ff6600;text-align:center;min-height:200px;margin-bottom:10px'>
        <div style='font-size:3.5em'>🏀</div>
        <div style='font-size:1.5em;color:#ff6600;font-weight:bold;margin-top:15px'>NBA Edge Finder</div>
        <div style='color:#888;margin-top:10px;font-size:0.9em'>12-Factor Model</div>
        <div style='margin-top:15px'><span style='background:#ff6600;color:#000;padding:4px 12px;border-radius:12px;font-size:0.75em;font-weight:700'>LIVE</span></div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🏀 Open NBA", use_container_width=True, key="nba_btn"):
        st.switch_page("pages/2_NBA.py")

with col3:
    st.markdown("""
    <div style='background:linear-gradient(135deg,#1a1a2e,#0a0a1e);padding:30px;border-radius:20px;border:2px solid #4dabf7;text-align:center;min-height:200px;margin-bottom:10px'>
        <div style='font-size:3.5em'>🏒</div>
        <div style='font-size:1.5em;color:#4dabf7;font-weight:bold;margin-top:15px'>NHL Edge Finder</div>
        <div style='color:#888;margin-top:10px;font-size:0.9em'>10-Factor Model</div>
        <div style='margin-top:15px'><span style='background:#4dabf7;color:#000;padding:4px 12px;border-radius:12px;font-size:0.75em;font-weight:700'>LIVE</span></div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🏒 Open NHL", use_container_width=True, key="nhl_btn"):
        st.switch_page("pages/3_NHL.py")

st.markdown("<br>", unsafe_allow_html=True)

# ============================================================
# APP CARDS - ROW 2
# ============================================================
col4, col5, col6 = st.columns(3)

with col4:
    st.markdown("""
    <div style='background:linear-gradient(135deg,#2e1a2e,#1e0a1e);padding:30px;border-radius:20px;border:2px solid #e040fb;text-align:center;min-height:200px;margin-bottom:10px'>
        <div style='font-size:3.5em'>🌡️</div>
        <div style='font-size:1.5em;color:#e040fb;font-weight:bold;margin-top:15px'>Temp Edge Finder</div>
        <div style='color:#888;margin-top:10px;font-size:0.9em'>NWS vs Kalshi</div>
        <div style='margin-top:15px'><span style='background:#e040fb;color:#000;padding:4px 12px;border-radius:12px;font-size:0.75em;font-weight:700'>LIVE</span></div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🌡️ Open Temp", use_container_width=True, key="temp_btn"):
        st.switch_page("pages/5_Temp.py")

with col5:
    st.markdown("""
    <div style='background:linear-gradient(135deg,#2e2e1a,#1e1e0a);padding:30px;border-radius:20px;border:2px solid #555;text-align:center;min-height:200px;opacity:0.6;margin-bottom:10px'>
        <div style='font-size:3.5em'>⚾</div>
        <div style='font-size:1.5em;color:#888;font-weight:bold;margin-top:15px'>MLB Edge Finder</div>
        <div style='color:#666;margin-top:10px;font-size:0.9em'>Coming Soon</div>
        <div style='margin-top:15px'><span style='background:#555;color:#fff;padding:4px 12px;border-radius:12px;font-size:0.75em;font-weight:700'>SOON</span></div>
    </div>
    """, unsafe_allow_html=True)
    st.button("⚾ Coming Soon", use_container_width=True, disabled=True, key="mlb_btn")

with col6:
    st.markdown("""
    <div style='background:linear-gradient(135deg,#2e2e1a,#1e1e0a);padding:30px;border-radius:20px;border:2px solid #555;text-align:center;min-height:200px;opacity:0.6;margin-bottom:10px'>
        <div style='font-size:3.5em'>🗳️</div>
        <div style='font-size:1.5em;color:#888;font-weight:bold;margin-top:15px'>Politics Edge Finder</div>
        <div style='color:#666;margin-top:10px;font-size:0.9em'>Coming Summer 2026</div>
        <div style='margin-top:15px'><span style='background:#555;color:#fff;padding:4px 12px;border-radius:12px;font-size:0.75em;font-weight:700'>SOON</span></div>
    </div>
    """, unsafe_allow_html=True)
    st.button("🗳️ Coming Soon", use_container_width=True, disabled=True, key="pol_btn")

st.markdown("---")

# ============================================================
# HOW IT WORKS
# ============================================================
st.markdown("""
<div style="max-width: 800px; margin: 40px auto; padding: 30px; 
            background: linear-gradient(135deg, #1a2a3a 0%, #2a3a4a 100%);
            border-radius: 16px; border: 1px solid #3a4a5a;">
    <h3 style="color: #fff; font-size: 18px; margin-bottom: 20px; text-align: center;">⚡ How BigSnapshot Works</h3>
    <div style="display: flex; gap: 30px; flex-wrap: wrap; justify-content: center;">
        <div style="flex: 1; min-width: 200px; text-align: center;">
            <p style="color: #4dabf7; font-size: 24px; margin-bottom: 8px;">1</p>
            <p style="color: #ccc; font-size: 14px;">Pull live odds from Kalshi prediction markets</p>
        </div>
        <div style="flex: 1; min-width: 200px; text-align: center;">
            <p style="color: #4dabf7; font-size: 24px; margin-bottom: 8px;">2</p>
            <p style="color: #ccc; font-size: 14px;">Run structural analysis to find mispricings</p>
        </div>
        <div style="flex: 1; min-width: 200px; text-align: center;">
            <p style="color: #4dabf7; font-size: 24px; margin-bottom: 8px;">3</p>
            <p style="color: #ccc; font-size: 14px;">Surface edge opportunities before markets adjust</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# FOOTER
# ============================================================
st.markdown("""
<div style="text-align: center; padding: 40px 20px; color: #555;">
    <p style="font-size: 12px; margin-bottom: 8px;">⚠️ For entertainment and analysis only. Not financial advice.</p>
    <p style="font-size: 11px;">📧 aipublishingpro@gmail.com | bigsnapshot.com</p>
</div>
""", unsafe_allow_html=True)
