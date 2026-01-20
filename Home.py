import streamlit as st

st.set_page_config(page_title="BigSnapshot", page_icon="📊", layout="wide")

# ========== HIDE STREAMLIT UI + MOBILE RESPONSIVE ==========
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
if 'show_apps' not in st.session_state:
    st.session_state.show_apps = False

# ========== LANDING PAGE ==========
if not st.session_state.show_apps:
    
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
    
    # CTA Buttons
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style="display: flex; gap: 16px; justify-content: center; flex-wrap: wrap;">
            <a href="mailto:aipublishingpro@gmail.com?subject=BigSnapshot%20Beta%20Request&body=I%20want%20to%20join%20the%20BigSnapshot%20beta.%0A%0AMy%20name%3A%20%0AMarkets%20I%20trade%3A%20" 
               style="background: #00ff88; color: #000; padding: 14px 32px; border-radius: 8px; text-decoration: none; font-weight: bold; font-size: 1.1em;">
                📧 JOIN BETA
            </a>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("👀 PREVIEW APP", use_container_width=True):
            st.session_state.show_apps = True
            st.rerun()
        st.caption("Preview the tools before signing up")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # One Screen Section
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
    
    # Benefits Grid
    st.markdown("<h2 style='text-align: center; color: #fff; margin: 40px 0 30px 0;'>Why BigSnapshot Is Different</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div style="background: #1a1a2e; border-radius: 12px; padding: 24px; margin-bottom: 16px; border-left: 4px solid #00d4ff;">
            <h3 style="color: #00d4ff; margin: 0 0 10px 0;">⏱️ Save Time on Every Slate</h3>
            <p style="color: #aaa; margin: 0;">No bouncing between sportsbooks, stats sites, and Twitter. Scan an entire slate in seconds.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div style="background: #1a1a2e; border-radius: 12px; padding: 24px; margin-bottom: 16px; border-left: 4px solid #00ff88;">
            <h3 style="color: #00ff88; margin: 0 0 10px 0;">🧠 Decision Compression</h3>
            <p style="color: #aaa; margin: 0;">Raw data distilled into clear signals. Analysis paralysis disappears. Your brain stays focused on sizing and discipline.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div style="background: #1a1a2e; border-radius: 12px; padding: 24px; margin-bottom: 16px; border-left: 4px solid #ffaa00;">
            <h3 style="color: #ffaa00; margin: 0 0 10px 0;">📈 Market Awareness</h3>
            <p style="color: #aaa; margin: 0;">Instantly know if the market supports your view or pushes back. Aware before you commit—not after.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div style="background: #1a1a2e; border-radius: 12px; padding: 24px; margin-bottom: 16px; border-left: 4px solid #ff6b6b;">
            <h3 style="color: #ff6b6b; margin: 0 0 10px 0;">🛑 Stops You From Chasing</h3>
            <p style="color: #aaa; margin: 0;">Late moves are obvious. Resistance is clearly flagged. The app naturally slows you down when chasing would hurt most.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="background: #1a1a2e; border-radius: 12px; padding: 24px; margin-bottom: 16px; border-left: 4px solid #aa88ff;">
            <h3 style="color: #aa88ff; margin: 0 0 10px 0;">🎚️ Discipline Built In</h3>
            <p style="color: #aaa; margin: 0;">No BUY/SELL hype. No flashing alerts. No forced picks. Encourages restraint instead of impulsive action.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div style="background: #1a1a2e; border-radius: 12px; padding: 24px; margin-bottom: 16px; border-left: 4px solid #ff88aa;">
            <h3 style="color: #ff88aa; margin: 0 0 10px 0;">👁️ Early Signal Visibility</h3>
            <p style="color: #aaa; margin: 0;">Spot early pressure before public noise takes over. Especially powerful in thinner markets.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div style="background: #1a1a2e; border-radius: 12px; padding: 24px; margin-bottom: 16px; border-left: 4px solid #88ddff;">
            <h3 style="color: #88ddff; margin: 0 0 10px 0;">✂️ Fewer Bad Bets</h3>
            <p style="color: #aaa; margin: 0;">Doesn't create more bets—filters out the bad versions of good ideas. Edge quality improves without trading more.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div style="background: #1a1a2e; border-radius: 12px; padding: 24px; margin-bottom: 16px; border-left: 4px solid #88ff88;">
            <h3 style="color: #88ff88; margin: 0 0 10px 0;">🔒 Human-in-the-Loop</h3>
            <p style="color: #aaa; margin: 0;">Doesn't bet for you. Doesn't override judgment. You stay in control at all times.</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Result Section
    st.markdown("""
    <div style="background: linear-gradient(135deg, #0f3460, #1a1a2e); border-radius: 16px; padding: 40px; margin: 40px 0; text-align: center;">
        <h2 style="color: #fff; margin-bottom: 20px;">The Result</h2>
        <div style="display: flex; justify-content: center; gap: 30px; flex-wrap: wrap; margin-bottom: 30px;">
            <span style="color: #00ff88; font-size: 1.1em;">✓ Less second-guessing</span>
            <span style="color: #00ff88; font-size: 1.1em;">✓ Less tilt</span>
            <span style="color: #00ff88; font-size: 1.1em;">✓ Fewer mistakes</span>
            <span style="color: #00ff88; font-size: 1.1em;">✓ More trust in your process</span>
        </div>
        <p style="color: #fff; font-size: 1.4em; font-weight: bold; margin: 0;">You don't bet more. You bet cleaner.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Bottom Line + CTA
    st.markdown("""
    <div style="text-align: center; padding: 40px 20px;">
        <p style="color: #888; font-size: 1.2em; max-width: 600px; margin: 0 auto 30px auto;">
            BigSnapshot doesn't help you chase wins. It helps you make fewer bad decisions.<br><br>
            <span style="color: #fff; font-weight: bold;">That's where real edge comes from.</span>
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Beta Signup
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1a472a, #0f3460); border-radius: 16px; padding: 40px; margin: 40px 0; text-align: center; border: 2px solid #00ff88;">
        <h2 style="color: #00ff88; margin-bottom: 10px;">🚀 Join the Beta</h2>
        <p style="color: #aaa; margin-bottom: 25px;">Get early access. Help shape the product. Lock in founder pricing.</p>
        <a href="mailto:aipublishingpro@gmail.com?subject=BigSnapshot%20Beta%20Request&body=I%20want%20to%20join%20the%20BigSnapshot%20beta.%0A%0AMy%20name%3A%20%0AMarkets%20I%20trade%3A%20" 
           style="background: #00ff88; color: #000; padding: 16px 40px; border-radius: 8px; text-decoration: none; font-weight: bold; font-size: 1.2em; display: inline-block;">
            📧 REQUEST BETA ACCESS
        </a>
        <p style="color: #666; margin-top: 20px; font-size: 0.9em;">Click above to send an email request</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Final CTA
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🚀 LAUNCH APP (PREVIEW)", use_container_width=True, type="primary", key="bottom_cta"):
            st.session_state.show_apps = True
            st.rerun()
    
    # Footer
    st.markdown("""
    <div style="text-align: center; padding: 40px 20px; margin-top: 40px; border-top: 1px solid #333;">
        <p style="color: #666; font-size: 0.9em;">
            Built for serious bettors. Not a pick app. Not a casino toy.<br>
            📧 aipublishingpro@gmail.com
        </p>
    </div>
    """, unsafe_allow_html=True)

# ========== APP HUB ==========
else:
    # Back button
    if st.button("← Back to Home"):
        st.session_state.show_apps = False
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
