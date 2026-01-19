import streamlit as st

st.set_page_config(page_title="Big Snapshot", page_icon="📊", layout="wide")

# ========== GOOGLE ANALYTICS ==========
st.markdown("""
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-NQKY5VQ376"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-NQKY5VQ376');
</script>
""", unsafe_allow_html=True)

# ========== MAIN PAGE ==========
st.title("📊 BIG SNAPSHOT")
st.subheader("Sports Analytics Dashboard")

st.markdown("""
Welcome to Big Snapshot - your sports analytics hub for Kalshi prediction markets.

### Select a Sport:
""")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    ### 🏈 NFL
    - Live game tracking
    - Score updates  
    - Field position visualization
    - Kalshi market links
    """)
    st.page_link("pages/1_NFL.py", label="🏈 Open NFL Edge Finder", use_container_width=True)

with col2:
    st.markdown("""
    ### 🏀 NBA
    - Live scores & pace tracking
    - Cushion scanner
    - Position management
    - Kalshi market links
    """)
    st.page_link("pages/2_NBA.py", label="🏀 Open NBA Edge Finder", use_container_width=True)

st.divider()
st.caption("⚠️ For entertainment only. Not financial advice. | bigsnapshot.com")
