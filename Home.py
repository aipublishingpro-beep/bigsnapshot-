import streamlit as st

st.set_page_config(page_title="BigSnapshot", page_icon="🎯", layout="wide")

import streamlit.components.v1 as components
components.html("""
<script async src="https://www.googletagmanager.com/gtag/js?id=G-1T35YHHYBC"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-1T35YHHYBC', { send_page_view: true });
</script>
""", height=0)

# ============================================================
# MOBILE CSS
# ============================================================
st.markdown("""
<style>
@media (max-width: 768px) {
    .stColumns > div { flex: 1 1 100% !important; min-width: 100% !important; }
    [data-testid="stMetricValue"] { font-size: 1.2rem !important; }
    [data-testid="stMetricLabel"] { font-size: 0.8rem !important; }
    h1 { font-size: 1.5rem !important; }
    h2 { font-size: 1.2rem !important; }
    h3 { font-size: 1rem !important; }
    button { padding: 8px 12px !important; font-size: 0.85em !important; }
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# HERO SECTION
# ============================================================
st.markdown("""
<div style="text-align: center; padding: 40px 20px 20px 20px;">
    <div style="font-size: 70px; margin-bottom: 15px;">🎯</div>
    <h1 style="font-size: 52px; font-weight: 800; color: #fff; margin-bottom: 10px;">BigSnapshot</h1>
    <p style="color: #888; font-size: 20px; margin-bottom: 10px;">Prediction Market Edge Finder</p>
    <p style="color: #555; font-size: 14px;">Structural analysis for Kalshi markets</p>
</div>
""", unsafe_allow_html=True)

# ============================================================
# FREE SEASON BANNER
# ============================================================
st.markdown("""
<div style="text-align: center; padding: 20px; margin: 20px auto; max-width: 800px; background: linear-gradient(135deg, #1a3a1a 0%, #2a4a2a 100%); border-radius: 16px; border: 2px solid #22c55e;">
    <h2 style="color: #4ade80; margin-bottom: 10px;">🎉 FREE FOR 2025-26 SEASON</h2>
    <p style="color: #ccc; font-size: 16px; margin-bottom: 10px;">
        All tools are <strong>100% free</strong> while we build proof, gather feedback, and refine our edge-finding systems.
    </p>
    <p style="color: #f97316; font-size: 13px;">
        ⚠️ We reserve the right to implement paid subscriptions at any time.
    </p>
</div>
""", unsafe_allow_html=True)

# ============================================================
# VALUE PROP
# ============================================================
st.markdown("""
<div style="text-align: center; padding: 20px; max-width: 700px; margin: 0 auto;">
    <h2 style="color: #fff; font-size: 28px; margin-bottom: 15px;">Stop Switching Tabs. Start Making Cleaner Decisions.</h2>
    <p style="color: #888; font-size: 16px; line-height: 1.6;">
        BigSnapshot is a decision-compression tool for serious prediction market traders. 
        It pulls the signals that matter into one screen—so you spend less time hunting and more time deciding.
    </p>
    <p style="color: #666; font-size: 14px; margin-top: 15px;">No hype. No picks shoved in your face. Just clarity.</p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ============================================================
# LIVE TOOLS - ALL FREE
# ============================================================
st.markdown("### 🔥 Live Tools — All Free")

col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("🏀 NBA Edge", use_container_width=True, type="primary"):
        st.switch_page("pages/2_NBA.py")
    if st.button("🏈 NFL Edge", use_container_width=True, type="primary"):
        st.switch_page("pages/1_NFL.py")
with col2:
    if st.button("🏒 NHL Edge", use_container_width=True, type="primary"):
        st.switch_page("pages/3_NHL.py")
    if st.button("⚽ Soccer Edge", use_container_width=True, type="primary"):
        st.switch_page("pages/8_Soccer.py")
with col3:
    if st.button("🎓 NCAA Edge", use_container_width=True, type="primary"):
        st.switch_page("pages/7_NCAA.py")
    if st.button("🌡️ Temp Edge", use_container_width=True, type="primary"):
        st.switch_page("pages/5_Temp.py")
with col4:
    if st.button("📊 Economics", use_container_width=True, type="primary"):
        st.switch_page("pages/9_Economics.py")

# ============================================================
# TOOL CARDS (VISUAL)
# ============================================================
st.markdown("""
<div style="display: flex; justify-content: center; gap: 15px; flex-wrap: wrap; padding: 20px;">
    <div style="background: linear-gradient(135deg, #1a3a1a 0%, #2a4a2a 100%); border-radius: 16px; padding: 25px; width: 140px; height: 180px; text-align: center; border: 2px solid #22c55e; display: flex; flex-direction: column; justify-content: space-between; align-items: center;">
        <div style="font-size: 50px;">🏀</div>
        <h3 style="color: #4ade80; margin: 0;">NBA</h3>
        <span style="background:#22c55e;color:#000;padding:4px 12px;border-radius:20px;font-size:12px;font-weight:700">FREE</span>
    </div>
    <div style="background: linear-gradient(135deg, #1a3a1a 0%, #2a4a2a 100%); border-radius: 16px; padding: 25px; width: 140px; height: 180px; text-align: center; border: 2px solid #22c55e; display: flex; flex-direction: column; justify-content: space-between; align-items: center;">
        <div style="font-size: 50px;">🏈</div>
        <h3 style="color: #4ade80; margin: 0;">NFL</h3>
        <span style="background:#22c55e;color:#000;padding:4px 12px;border-radius:20px;font-size:12px;font-weight:700">FREE</span>
    </div>
    <div style="background: linear-gradient(135deg, #1a3a1a 0%, #2a4a2a 100%); border-radius: 16px; padding: 25px; width: 140px; height: 180px; text-align: center; border: 2px solid #22c55e; display: flex; flex-direction: column; justify-content: space-between; align-items: center;">
        <div style="font-size: 50px;">🏒</div>
        <h3 style="color: #4ade80; margin: 0;">NHL</h3>
        <span style="background:#22c55e;color:#000;padding:4px 12px;border-radius:20px;font-size:12px;font-weight:700">FREE</span>
    </div>
    <div style="background: linear-gradient(135deg, #1a3a1a 0%, #2a4a2a 100%); border-radius: 16px; padding: 25px; width: 140px; height: 180px; text-align: center; border: 2px solid #22c55e; display: flex; flex-direction: column; justify-content: space-between; align-items: center;">
        <div style="font-size: 50px;">🎓</div>
        <h3 style="color: #4ade80; margin: 0;">NCAA</h3>
        <span style="background:#22c55e;color:#000;padding:4px 12px;border-radius:20px;font-size:12px;font-weight:700">FREE</span>
    </div>
    <div style="background: linear-gradient(135deg, #1a3a1a 0%, #2a4a2a 100%); border-radius: 16px; padding: 25px; width: 140px; height: 180px; text-align: center; border: 2px solid #22c55e; display: flex; flex-direction: column; justify-content: space-between; align-items: center;">
        <div style="font-size: 50px;">⚽</div>
        <h3 style="color: #4ade80; margin: 0;">Soccer</h3>
        <span style="background:#22c55e;color:#000;padding:4px 12px;border-radius:20px;font-size:12px;font-weight:700">FREE</span>
    </div>
    <div style="background: linear-gradient(135deg, #1a3a1a 0%, #2a4a2a 100%); border-radius: 16px; padding: 25px; width: 140px; height: 180px; text-align: center; border: 2px solid #22c55e; display: flex; flex-direction: column; justify-content: space-between; align-items: center;">
        <div style="font-size: 50px;">🌡️</div>
        <h3 style="color: #4ade80; margin: 0;">Temp</h3>
        <span style="background:#22c55e;color:#000;padding:4px 12px;border-radius:20px;font-size:12px;font-weight:700">FREE</span>
    </div>
    <div style="background: linear-gradient(135deg, #1a3a1a 0%, #2a4a2a 100%); border-radius: 16px; padding: 25px; width: 140px; height: 180px; text-align: center; border: 2px solid #22c55e; display: flex; flex-direction: column; justify-content: space-between; align-items: center;">
        <div style="font-size: 50px;">📊</div>
        <h3 style="color: #4ade80; margin: 0;">Econ</h3>
        <span style="background:#22c55e;color:#000;padding:4px 12px;border-radius:20px;font-size:12px;font-weight:700">FREE</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# IN DEVELOPMENT NOTICE
# ============================================================
st.markdown("""
<div style="text-align: center; padding: 15px; margin: 20px auto; max-width: 600px; background: #1a1a2a; border-radius: 12px; border: 1px solid #3b82f6;">
    <p style="color: #60a5fa; font-size: 14px; margin: 0;">
        🔧 <strong>Note:</strong> NHL, Soccer, and Economics are in continued development. Features may change as we refine the edge-finding algorithms.
    </p>
</div>
""", unsafe_allow_html=True)

# ============================================================
# EMAIL SIGNUP
# ============================================================
st.markdown("""
<div style="text-align: center; padding: 25px; margin: 20px auto; max-width: 600px; background: linear-gradient(135deg, #1a2a4a 0%, #2a3a5a 100%); border-radius: 16px; border: 2px solid #22c55e;">
    <h3 style="color: #4ade80; margin: 0 0 10px 0;">📧 Get Notified</h3>
    <p style="color: #ccc; font-size: 14px; margin: 0 0 15px 0;">
        Want updates when we add features or launch paid plans?<br>
        <span style="color: #888; font-size: 12px;">We'll only email you for major updates. No spam.</span>
    </p>
    <a href="https://docs.google.com/forms/d/e/1FAIpQLSfBcRg-QSB1E150zW2TSIkaPEFkJFGB4xqyZszfEqvtzn_wAw/viewform" target="_blank" style="display: inline-block; background: #22c55e; color: black; padding: 12px 30px; border-radius: 8px; font-weight: 700; text-decoration: none; font-size: 16px;">
        ✉️ Sign Up for Updates
    </a>
    <p style="color: #666; font-size: 11px; margin: 15px 0 0 0;">
        Questions? Contact: <a href="mailto:aipublishingpro@gmail.com" style="color: #4ade80;">aipublishingpro@gmail.com</a>
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ============================================================
# COMING SOON
# ============================================================
st.markdown("### 🚧 Coming Soon")
st.markdown("""
<div style="display: flex; justify-content: center; gap: 15px; flex-wrap: wrap; padding: 20px;">
    <div style="background: #1a1a2a; border-radius: 16px; padding: 25px; width: 140px; text-align: center; border: 2px dashed #444;">
        <div style="font-size: 50px; margin-bottom: 10px;">⚾</div>
        <h3 style="color: #888; margin-bottom: 5px;">MLB</h3>
    </div>
    <div style="background: #1a1a2a; border-radius: 16px; padding: 25px; width: 140px; text-align: center; border: 2px dashed #444;">
        <div style="font-size: 50px; margin-bottom: 10px;">🏛️</div>
        <h3 style="color: #888; margin-bottom: 5px;">Politics</h3>
    </div>
    <div style="background: #1a1a2a; border-radius: 16px; padding: 25px; width: 140px; text-align: center; border: 2px dashed #444;">
        <div style="font-size: 50px; margin-bottom: 10px;">🎬</div>
        <h3 style="color: #888; margin-bottom: 5px;">Entertainment</h3>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ============================================================
# FOOTER
# ============================================================
st.markdown("""
<div style="text-align: center; padding: 30px 20px;">
    <p style="color: #888; font-size: 16px; margin-bottom: 15px;">
        Fewer bad decisions = Fewer bad trades.<br>
        <span style="color: #4ade80;">That's the edge.</span>
    </p>
    <p style="color: #f97316; font-size: 13px; margin-bottom: 15px;">
        ⚠️ Free during beta. We reserve the right to implement paid subscriptions at any time.
    </p>
    <p style="color: #555; font-size: 12px;">
        ⚠️ For entertainment and educational purposes only. Not financial advice.
    </p>
</div>
""", unsafe_allow_html=True)
