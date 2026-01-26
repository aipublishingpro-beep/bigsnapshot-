import streamlit as st

st.set_page_config(page_title="MLB Edge Finder", page_icon="⚾", layout="wide")

# ============================================================
# GA4 ANALYTICS
# ============================================================
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
# COMING SOON PAGE
# ============================================================
st.markdown("""
<div style="text-align: center; padding: 80px 20px;">
    <div style="font-size: 100px; margin-bottom: 20px;">⚾</div>
    <h1 style="color: #fff; font-size: 42px; margin-bottom: 10px;">MLB Edge Finder</h1>
    <div style="background: linear-gradient(135deg, #1a1a2a 0%, #2a2a3a 100%); border-radius: 16px; padding: 30px; max-width: 500px; margin: 30px auto; border: 2px dashed #3b82f6;">
        <h2 style="color: #3b82f6; margin-bottom: 15px;">🚧 Coming Soon</h2>
        <p style="color: #888; font-size: 16px; line-height: 1.6;">
            MLB Edge Finder is under development and will launch before the 2026 season.
        </p>
        <p style="color: #666; font-size: 14px; margin-top: 15px;">
            Expected: March 2026
        </p>
    </div>
</div>
""", unsafe_allow_html=True)

# Back to Home button
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("🏠 Back to Home", use_container_width=True, type="primary"):
        st.switch_page("Home.py")

st.markdown("""
<div style="text-align: center; padding: 40px 20px;">
    <p style="color: #555; font-size: 12px;">
        ⚠️ For entertainment and educational purposes only. Not financial advice.
    </p>
</div>
""", unsafe_allow_html=True)
