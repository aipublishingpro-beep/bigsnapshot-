import streamlit as st
from streamlit_js_eval import streamlit_js_eval

st.set_page_config(page_title="BigSnapshot", page_icon="🎯", layout="wide")

# ============================================================
# 🔐 AUTH BOOTSTRAP — READ FROM LOCALSTORAGE ON EVERY LOAD
# ============================================================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.user_type = None

stored_auth = streamlit_js_eval(
    js_expressions="localStorage.getItem('bigsnapshot_auth')",
    key="auth_bootstrap_home"
)

if stored_auth and stored_auth not in ["", "null", None]:
    st.session_state.authenticated = True
    st.session_state.user_type = stored_auth

# ============================================================
# 🔐 PASSWORD CONFIG
# ============================================================
VALID_PASSWORD = "snapcrackle2026"

# ============================================================
# STYLES
# ============================================================
st.markdown("""
<style>
    .main-header { font-size: 2.5em; font-weight: bold; color: #fff; text-align: center; margin-bottom: 10px; }
    .sub-header { color: #888; text-align: center; margin-bottom: 30px; }
    .tool-card { background: linear-gradient(135deg, #0f172a, #1e293b); padding: 20px; border-radius: 12px; border: 1px solid #334155; margin-bottom: 15px; }
    .tool-title { font-size: 1.3em; font-weight: bold; color: #fff; margin-bottom: 8px; }
    .tool-desc { color: #94a3b8; font-size: 0.9em; }
    .status-badge { background: #22c55e; color: #000; padding: 3px 8px; border-radius: 4px; font-size: 0.75em; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# MAIN UI
# ============================================================
st.markdown('<div class="main-header">🎯 BigSnapshot</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Prediction Market Edge Tools</div>', unsafe_allow_html=True)

# ============================================================
# NOT LOGGED IN → SHOW LOGIN FORM
# ============================================================
if not st.session_state.authenticated:
    st.markdown("---")
    st.subheader("🔐 Subscriber Login")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        password = st.text_input("Enter access code:", type="password", key="login_password")
        
        if st.button("🔓 Unlock Access", use_container_width=True, type="primary"):
            if password == VALID_PASSWORD:
                # ✅ WRITE TO LOCALSTORAGE
                streamlit_js_eval(
                    js_expressions="localStorage.setItem('bigsnapshot_auth', 'Paid Subscriber')",
                    key="set_auth"
                )
                st.session_state.authenticated = True
                st.session_state.user_type = "Paid Subscriber"
                st.rerun()
            else:
                st.error("❌ Invalid access code")
    
    st.markdown("---")
    st.caption("Need access? Contact support.")
    st.stop()

# ============================================================
# LOGGED IN → SHOW DASHBOARD
# ============================================================
st.success(f"✅ Logged in as: {st.session_state.user_type}")

# Logout button
col1, col2, col3 = st.columns([2, 1, 2])
with col2:
    if st.button("🚪 Logout", use_container_width=True):
        # ✅ CLEAR LOCALSTORAGE
        streamlit_js_eval(
            js_expressions="localStorage.removeItem('bigsnapshot_auth')",
            key="clear_auth"
        )
        st.session_state.authenticated = False
        st.session_state.user_type = None
        st.rerun()

st.markdown("---")

# ============================================================
# TOOL CARDS
# ============================================================
st.subheader("🛠️ Your Tools")

tools = [
    {"name": "🏀 NBA Edge Finder", "desc": "ML picks, live tracking, streaks", "page": "pages/1_NBA.py", "status": "LIVE"},
    {"name": "🏈 NFL Edge Finder", "desc": "Coming soon", "page": "pages/2_NFL.py", "status": "SOON"},
    {"name": "🏀 NCAA Basketball", "desc": "Coming soon", "page": "pages/3_NCAA.py", "status": "SOON"},
    {"name": "🏒 NHL Edge Finder", "desc": "Coming soon", "page": "pages/4_NHL.py", "status": "SOON"},
    {"name": "⚾ MLB Edge Finder", "desc": "Coming soon", "page": "pages/5_MLB.py", "status": "SOON"},
    {"name": "⚽ Soccer Edge Finder", "desc": "Coming soon", "page": "pages/6_Soccer.py", "status": "SOON"},
    {"name": "📊 Economics", "desc": "Coming soon", "page": "pages/7_Econ.py", "status": "SOON"},
]

cols = st.columns(2)
for i, tool in enumerate(tools):
    with cols[i % 2]:
        status_color = "#22c55e" if tool["status"] == "LIVE" else "#64748b"
        st.markdown(f"""
        <div class="tool-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div class="tool-title">{tool['name']}</div>
                <span style="background: {status_color}; color: #000; padding: 3px 8px; border-radius: 4px; font-size: 0.75em; font-weight: bold;">{tool['status']}</span>
            </div>
            <div class="tool-desc">{tool['desc']}</div>
        </div>
        """, unsafe_allow_html=True)
        
        if tool["status"] == "LIVE":
            if st.button(f"Open {tool['name'].split()[1]}", key=f"open_{i}", use_container_width=True):
                st.switch_page(tool["page"])

st.markdown("---")
st.caption("© 2025 BigSnapshot. All rights reserved.")
