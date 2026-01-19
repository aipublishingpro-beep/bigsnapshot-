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
# GATE CHECK
# ============================================
st.title("📊 Big Snapshot")

cb1 = st.checkbox("I understand this is not financial advice and I am responsible for my own trades.")
cb2 = st.checkbox("I understand this free beta may end or change at any time.")
cb3 = st.checkbox("I confirm that I am 18 years or older.")

if cb1 and cb2 and cb3:
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
        st.markdown(
            '<a href="/NFL" target="_self">'
            '<button style="background-color: #28a745; color: white; padding: 12px 24px; '
            'border: none; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; '
            'width: 100%;">🏈 Open NFL Edge Finder</button></a>',
            unsafe_allow_html=True
        )
    
    # ========== NBA COLUMN ==========
    with col2:
        st.markdown("## 🏀 NBA")
        st.markdown("""
        - Live scores & pace tracking
        - Cushion scanner
        - Position management
        - Kalshi market links
        """)
        st.markdown(
            '<a href="/NBA" target="_self">'
            '<button style="background-color: #28a745; color: white; padding: 12px 24px; '
            'border: none; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; '
            'width: 100%;">🏀 Open NBA Edge Finder</button></a>',
            unsafe_allow_html=True
        )
    
    # ========== TEMP COLUMN ==========
    with col3:
        st.markdown("## 🌡️ Temperature")
        st.markdown("""
        - NWS forecast comparison
        - High & Low temp markets
        - Edge detection
        - Kalshi market links
        """)
        st.markdown(
            '<a href="/Temp" target="_self">'
            '<button style="background-color: #28a745; color: white; padding: 12px 24px; '
            'border: none; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; '
            'width: 100%;">🌡️ Open Temp Edge Finder</button></a>',
            unsafe_allow_html=True
        )
    
    st.divider()
    st.caption("⚠️ For entertainment only. Not financial advice. | bigsnapshot.com")
    st.caption("📧 Contact: aipublishingpro@gmail.com")
