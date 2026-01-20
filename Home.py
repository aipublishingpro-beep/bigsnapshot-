import streamlit as st

st.set_page_config(
    page_title="BigSnapshot — Smarter Sports Betting Decisions",
    page_icon="📊",
    layout="wide"
)

# ========== SEO META TAGS ==========
st.markdown("""
<head>
<title>BigSnapshot — Smarter Sports Betting Decisions</title>
<meta name="description" content="BigSnapshot helps serious bettors make cleaner decisions by compressing model signals, market pressure, and context into one screen. No hype. No noise. Just clarity.">
<meta name="keywords" content="sports betting analytics, NBA betting tools, NFL betting tools, NHL betting tools, betting edge finder, Kalshi trading, market line movement, sharp money, BigSnapshot">
<meta name="robots" content="index, follow">
<link rel="canonical" href="https://www.bigsnapshot.com">
<meta property="og:title" content="BigSnapshot — Smarter Sports Betting Decisions">
<meta property="og:description" content="One screen. Less noise. Better betting decisions. Decision compression for serious sports bettors.">
<meta property="og:url" content="https://www.bigsnapshot.com">
<meta property="og:type" content="website">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="BigSnapshot — Smarter Sports Betting Decisions">
<meta name="twitter:description" content="One screen. Less noise. Better betting decisions.">
</head>
""", unsafe_allow_html=True)

# ========== HIDE STREAMLIT UI ==========
st.markdown("""<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.stDeployButton {display: none;}
[data-testid="stToolbar"] {display: none;}
[data-testid="stSidebar"] {display: none;}
.block-container {padding-top: 2rem; padding-left: 1rem; padding-right: 1rem;}
@media (max-width: 768px) {
    .block-container {padding-left: 0.5rem; padding-right: 0.5rem;}
    h1 {font-size: 1.8em !important;}
    h2 {font-size: 1.4em !important;}
    h3 {font-size: 1.2em !important;}
    p {font-size: 1em !important;}
    [data-testid="column"] {width: 100% !important; flex: 100% !important; min-width: 100% !important;}
    .stButton > button {width: 100% !important;}
}
@media (max-width: 480px) {
    h1 {font-size: 1.5em !important;}
    .block-container {padding-left: 0.3rem; padding-right: 0.3rem;}
}
</style>""", unsafe_allow_html=True)

# ========== GA4 ==========
st.markdown("""
<script async src="https://www.googletagmanager.com/gtag/js?id=G-NQKY5VQ376"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());gtag('config','G-NQKY5VQ376');</script>
""", unsafe_allow_html=True)

# ========== SESSION STATE ==========
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'show_preview' not in st.session_state:
    st.session_state.show_preview = False

# ========== PASSWORD (CHANGE THIS) ==========
BETA_PASSWORD = "BIGSNAP2026"

# ========== MAIN LOGIC ==========

# Show app hub if authenticated OR preview mode
if st.session_state.authenticated or st.session_state.show_preview:
    
    # Header based on mode
    if st.session_state.authenticated:
        st.success("✅ **BETA ACCESS UNLOCKED** — Welcome!")
        col1, col2 = st.columns([6, 1])
        with col2:
            if st.button("🚪 Logout"):
                st.session_state.authenticated = False
                st.rerun()
    else:
        st.warning("👀 **PREVIEW MODE** — Limited access. Join beta for full features!")
        col1, col2 = st.columns([6, 1])
        with col2:
            if st.button("← Back"):
                st.session_state.show_preview = False
                st.rerun()
    
    st.title("📊 BigSnapshot")
    st.caption("Decision compression for serious bettors")
    
    st.divider()
    
    # App Cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style="background: #1a1a2e; border-radius: 12px; padding: 24px; text-align: center; border: 1px solid #333;">
            <span style="font-size: 3em;">🏈</span>
            <h3 style="color: #fff; margin: 15px 0 10px 0;">NFL Edge Finder</h3>
            <p style="color: #888; font-size: 0.9em;">10-factor ML + Market Pressure</p>
        </div>
        """, unsafe_allow_html=True)
        st.link_button("Launch NFL →", "/NFL", use_container_width=True)
    
    with col2:
        st.markdown("""
        <div style="background: #1a1a2e; border-radius: 12px; padding: 24px; text-align: center; border: 1px solid #333;">
            <span style="font-size: 3em;">🏀</span>
            <h3 style="color: #fff; margin: 15px 0 10px 0;">NBA Edge Finder</h3>
            <p style="color: #888; font-size: 0.9em;">8-factor ML + Market Pressure</p>
        </div>
        """, unsafe_allow_html=True)
        st.link_button("Launch NBA →", "/NBA", use_container_width=True)
    
    with col3:
        st.markdown("""
        <div style="background: #1a1a2e; border-radius: 12px; padding: 24px; text-align: center; border: 1px solid #333;">
            <span style="font-size: 3em;">🏒</span>
            <h3 style="color: #fff; margin: 15px 0 10px 0;">NHL Edge Finder</h3>
            <p style="color: #888; font-size: 0.9em;">10-factor ML + Market Pressure</p>
        </div>
        """, unsafe_allow_html=True)
        st.link_button("Launch NHL →", "/NHL", use_container_width=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col4, col5, col6 = st.columns(3)
    
    with col4:
        st.markdown("""
        <div style="background: #1a1a2e; border-radius: 12px; padding: 24px; text-align: center; border: 1px solid #333;">
            <span style="font-size: 3em;">⚾</span>
            <h3 style="color: #fff; margin: 15px 0 10px 0;">MLB Edge Finder</h3>
            <p style="color: #888; font-size: 0.9em;">Pitcher matchups + Weather</p>
        </div>
        """, unsafe_allow_html=True)
        st.link_button("Launch MLB →", "/MLB", use_container_width=True)
    
    with col5:
        st.markdown("""
        <div style="background: #1a1a2e; border-radius: 12px; padding: 24px; text-align: center; border: 1px solid #333;">
            <span style="font-size: 3em;">🌡️</span>
            <h3 style="color: #fff; margin: 15px 0 10px 0;">Temp Edge Finder</h3>
            <p style="color: #888; font-size: 0.9em;">NWS forecast vs Kalshi pricing</p>
        </div>
        """, unsafe_allow_html=True)
        st.link_button("Launch Temp →", "/Temp", use_container_width=True)
    
    with col6:
        st.markdown("""
        <div style="background: #1a1a2e; border-radius: 12px; padding: 24px; text-align: center; border: 1px solid #333;">
            <span style="font-size: 3em;">🗳️</span>
            <h3 style="color: #fff; margin: 15px 0 10px 0;">Politics Edge</h3>
            <p style="color: #888; font-size: 0.9em;">Coming Soon</p>
        </div>
        """, unsafe_allow_html=True)
        st.button("Coming Soon", use_container_width=True, disabled=True)
    
    st.divider()
    
    st.markdown("""
    <div style="text-align: center; padding: 20px;">
        <p style="color: #666; font-size: 0.9em;">
            ⚠️ For entertainment only. Not financial advice.<br>
            📧 aipublishingpro@gmail.com
        </p>
    </div>
    """, unsafe_allow_html=True)

# ========== LANDING PAGE ==========
else:
    # Hero
    st.markdown("""
    <div style="text-align: center; padding: 40px 20px;">
        <h1 style="font-size: 3em; margin-bottom: 0; color: #fff;">Stop Switching Tabs.</h1>
        <h1 style="font-size: 3em; margin-top: 0; color: #00d4ff;">Start Making Cleaner Decisions.</h1>
        <p style="font-size: 1.3em; color: #888; max-width: 700px; margin: 20px auto;">
            BigSnapshot is a decision-compression tool for serious sports bettors. It pulls the signals that matter into one screen—so you spend less time hunting and more time deciding.
        </p>
        <p style="color: #666; font-size: 1.1em;">No hype. No picks shoved in your face. Just clarity.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # JOIN BETA button
    st.markdown("""
    <div style="text-align: center; margin: 20px 0;">
        <a href="mailto:aipublishingpro@gmail.com?subject=BigSnapshot%20Beta%20Request&body=I%20want%20to%20join%20the%20BigSnapshot%20beta.%0A%0AMy%20name%3A%20%0AMarkets%20I%20trade%3A%20" 
           style="background: #00ff88; color: #000; padding: 16px 40px; border-radius: 8px; text-decoration: none; font-weight: bold; font-size: 1.2em;">
            📧 JOIN BETA
        </a>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # PASSWORD LOGIN SECTION
    st.markdown("""
    <div style="text-align: center; margin: 30px 0 10px 0;">
        <p style="color: #888; font-size: 1em;">🔐 Already a beta tester?</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        password_input = st.text_input("Password", type="password", placeholder="Enter your beta password", label_visibility="collapsed")
        if st.button("🔓 UNLOCK ACCESS", use_container_width=True, type="primary"):
            if password_input == BETA_PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            elif password_input:
                st.error("❌ Wrong password. Email us if you forgot it.")
            else:
                st.warning("Please enter your password")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # PREVIEW button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("👀 PREVIEW APP (Limited)", use_container_width=True):
            st.session_state.show_preview = True
            st.rerun()
        st.caption("Preview features before signing up")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Benefits section
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1a1a2e, #16213e); border-radius: 16px; padding: 40px; margin: 40px 0;">
        <h2 style="color: #fff; text-align: center; margin-bottom: 30px;">One Screen. One Flow. Zero Noise.</h2>
        <p style="color: #aaa; text-align: center; max-width: 600px; margin: 0 auto 30px auto;">
            Most bettors lose edge before they even place a bet—switching between odds, stats, line movement, news, and gut instinct. BigSnapshot fixes that.
        </p>
        <div style="display: flex; justify-content: center; gap: 40px; flex-wrap: wrap;">
            <div style="text-align: center;">
                <span style="font-size: 2em;">🎯</span>
                <p style="color: #fff; margin: 10px 0 5px 0; font-weight: bold;">Where the edge is</p>
                <p style="color: #888; font-size: 0.9em;">Clear signals, not noise</p>
            </div>
            <div style="text-align: center;">
                <span style="font-size: 2em;">📊</span>
                <p style="color: #fff; margin: 10px 0 5px 0; font-weight: bold;">Market agrees or resists</p>
                <p style="color: #888; font-size: 0.9em;">Know before you commit</p>
            </div>
            <div style="text-align: center;">
                <span style="font-size: 2em;">⚡</span>
                <p style="color: #fff; margin: 10px 0 5px 0; font-weight: bold;">What deserves attention</p>
                <p style="color: #888; font-size: 0.9em;">And what doesn't</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Footer
    st.markdown("""
    <div style="text-align: center; padding: 40px 20px; margin-top: 40px; border-top: 1px solid #333;">
        <p style="color: #666; font-size: 0.9em;">
            Built for serious bettors. Not a pick app. Not a casino toy.<br>
            📧 aipublishingpro@gmail.com
        </p>
    </div>
    """, unsafe_allow_html=True)
