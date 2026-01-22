import streamlit as st
from auth import require_auth

require_auth()

from styles import apply_styles

st.set_page_config(
    page_title="MLB Edge Finder | BigSnapshot",
    page_icon="⚾",
    layout="wide"
)

apply_styles()

# ============================================================
# GA4 TRACKING
# ============================================================
st.markdown("""
<script async src="https://www.googletagmanager.com/gtag/js?id=G-NQKY5VQ376"></script>
<script>window.dataLayer = window.dataLayer || [];function gtag(){dataLayer.push(arguments);}gtag('js', new Date());gtag('config', 'G-NQKY5VQ376');</script>
""", unsafe_allow_html=True)

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
# PAGE-SPECIFIC CSS
# ============================================================
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(180deg, #0a0a0f 0%, #1a1a2e 100%);
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# COMING SOON PAGE
# ============================================================
st.markdown("""
<div style="text-align: center; padding: 80px 20px;">
    <div style="font-size: 80px; margin-bottom: 20px;">⚾</div>
    <h1 style="font-size: 48px; font-weight: 800; color: #fff; margin-bottom: 15px;">
        MLB Edge Finder
    </h1>
    <p style="color: #888; font-size: 22px; margin-bottom: 40px;">
        Coming Soon — 2026 Season
    </p>
    <div style="background: linear-gradient(135deg, #1e1e2e 0%, #2a2a3e 100%); 
                border-radius: 16px; padding: 40px; max-width: 600px; margin: 0 auto;
                border: 1px solid #333;">
        <p style="color: #4dabf7; font-size: 18px; font-weight: 600; margin-bottom: 20px;">
            ⚾ March 2026
        </p>
        <p style="color: #ccc; font-size: 16px; line-height: 1.7; margin-bottom: 25px;">
            MLB Edge Finder will activate when the 2026 baseball season begins 
            and Kalshi has active MLB markets.
        </p>
        <p style="color: #888; font-size: 14px; line-height: 1.6;">
            <strong>What's Coming:</strong><br>
            • Starting pitcher analysis (ERA, WHIP, K/9)<br>
            • Bullpen fatigue tracking<br>
            • Team OPS splits (vs LHP/RHP)<br>
            • Ballpark factors<br>
            • 12-factor edge model
        </p>
    </div>
</div>
""", unsafe_allow_html=True)

# Timeline
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 20px;">
    <h3 style="color: #fff; margin-bottom: 20px;">📅 2026 MLB Timeline</h3>
    <div style="display: flex; justify-content: center; gap: 40px; flex-wrap: wrap;">
        <div style="text-align: center;">
            <p style="color: #4dabf7; font-size: 24px; margin: 0;">Feb 2026</p>
            <p style="color: #888; font-size: 14px;">Spring Training</p>
        </div>
        <div style="text-align: center;">
            <p style="color: #4dabf7; font-size: 24px; margin: 0;">Mar - Oct 2026</p>
            <p style="color: #888; font-size: 14px;">Regular Season</p>
        </div>
        <div style="text-align: center;">
            <p style="color: #4dabf7; font-size: 24px; margin: 0;">Oct 2026</p>
            <p style="color: #888; font-size: 14px;">Playoffs</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Footer
st.markdown("---")
st.caption("⚾ MLB Edge Finder | BigSnapshot.com")
st.caption("Check back in Spring 2026 for live markets!")
st.caption("⚠️ Not financial advice.")
