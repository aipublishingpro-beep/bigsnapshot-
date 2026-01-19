import streamlit as st

# ============================================
# BIGSNAPSHOT HOME PAGE
# ============================================

st.set_page_config(page_title="Big Snapshot", page_icon="📊", layout="wide")

# Hide Streamlit menu/footer/header
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.stDeployButton {display: none;}
[data-testid="stToolbar"] {display: none;}
</style>
""", unsafe_allow_html=True)

# GA4 Tracking
st.markdown("""
<script async src="https://www.googletagmanager.com/gtag/js?id=G-NQKY5VQ376"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-NQKY5VQ376');
</script>
""", unsafe_allow_html=True)

# ============================================
# INITIALIZE SESSION STATE
# ============================================
if "gate_passed" not in st.session_state:
    st.session_state.gate_passed = False

# ============================================
# GATE CHECK (5 CHECKBOXES)
# ============================================
st.title("📊 Big Snapshot")

if not st.session_state.gate_passed:
    st.warning("⚠️ Please confirm the following before accessing the tools:")
    
    cb1 = st.checkbox("I understand this is not financial advice and I am responsible for my own trades.")
    cb2 = st.checkbox("I understand past performance does not guarantee future results.")
    cb3 = st.checkbox("I will use this tool responsibly.")
    cb4 = st.checkbox("I am of legal age to participate in prediction markets in my jurisdiction.")
    cb5 = st.checkbox("I have read and accept the terms of use.")
    
    if cb1 and cb2 and cb3 and cb4 and cb5:
        if st.button("✅ Enter Big Snapshot", type="primary"):
            st.session_state.gate_passed = True
            st.rerun()
    else:
        st.info("Please check all 5 boxes above to continue.")
else:
    st.success("✅ You may proceed. Select a tool below:")
    
    st.divider()
    
    # ========== THREE COLUMNS: NFL, NBA, TEMP ==========
    col1, col2, col3 = st.columns(3)
    
    # ========== NFL COLUMN ==========
    with col1:
        st.markdown("## 🏈 NFL")
        st.markdown("""
        - Live game tracking
        - Score updates
        - Field position visualization
        - Kalshi market links
        """)
        if st.button("🏈 Open NFL Edge Finder", key="nfl_btn", type="primary", use_container_width=True):
            st.switch_page("pages/1_NFL.py")
    
    # ========== NBA COLUMN ==========
    with col2:
        st.markdown("## 🏀 NBA")
        st.markdown("""
        - Live scores & pace tracking
        - Cushion scanner
        - Position management
        - Kalshi market links
        """)
        if st.button("🏀 Open NBA Edge Finder", key="nba_btn", type="primary", use_container_width=True):
            st.switch_page("pages/2_NBA.py")
    
    # ========== TEMP COLUMN ==========
    with col3:
        st.markdown("## 🌡️ Temperature")
        st.markdown("""
        - NWS forecast comparison
        - High & Low temp markets
        - Edge detection
        - Kalshi market links
        """)
        if st.button("🌡️ Open Temp Edge Finder", key="temp_btn", type="primary", use_container_width=True):
            st.switch_page("pages/3_Temp.py")
    
    st.divider()
    st.caption("⚠️ For entertainment only. Not financial advice. | bigsnapshot.com")
    st.caption("📧 Contact: aipublishingpro@gmail.com")
