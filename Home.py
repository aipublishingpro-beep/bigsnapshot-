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
st.subheader("Sports Analytics Dashboard - Public Beta")

st.markdown("""
Welcome to Big Snapshot - your sports analytics hub for Kalshi prediction markets.

### Before You Continue:
""")

# ========== CHECKBOXES ==========
cb1 = st.checkbox("I understand this tool provides market signals, not predictions.")
cb2 = st.checkbox("I understand signals may change as new information arrives.")
cb3 = st.checkbox("I understand this is not financial advice and I am responsible for my own trades.")
cb4 = st.checkbox("I understand this free beta may end or change at any time.")
cb5 = st.checkbox("I confirm that I am 18 years or older.")

all_checked = cb1 and cb2 and cb3 and cb4 and cb5

st.divider()

if all_checked:
    st.success("✅ You may proceed. Select a sport below:")
    
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
else:
    st.warning("⚠️ Please check all boxes above to continu
