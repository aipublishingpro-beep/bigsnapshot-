import streamlit as st

st.set_page_config(page_title="BigSnapshot", page_icon="📊", layout="wide")

st.title("📊 BigSnapshot Edge Finders")
st.success("Welcome! Choose a tool from the sidebar.")

st.markdown("### 🔥 Live Tools")

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("🏀 NBA", use_container_width=True):
        st.switch_page("pages/2_NBA.py")
    if st.button("🏈 NFL", use_container_width=True):
        st.switch_page("pages/1_NFL.py")

with col2:
    if st.button("🏒 NHL", use_container_width=True):
        st.switch_page("pages/3_NHL.py")
    if st.button("🌡️ Temp", use_container_width=True):
        st.switch_page("pages/5_Temp.py")

with col3:
    if st.button("🎓 NCAA", use_container_width=True):
        st.switch_page("pages/7_NCAA.py")
    if st.button("⚽ Soccer", use_container_width=True):
        st.switch_page("pages/8_Soccer.py")

with col4:
    if st.button("📊 Economics", use_container_width=True):
        st.switch_page("pages/9_Economics.py")

st.markdown("---")
st.markdown("📧 **Comments or suggestions?** aipublishingpro@gmail.com")
st.caption("⚠️ For educational and entertainment purposes only. This is not financial advice. We are not responsible for any betting or trading decisions you make.")
st.caption("© 2026 BigSnapshot. All rights reserved.")
