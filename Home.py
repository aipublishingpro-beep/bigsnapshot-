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

from streamlit_js_eval import streamlit_js_eval

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
# 🔐 PASSWORD & STRIPE CONFIG
# ============================================================
VALID_PASSWORD = "snapcrackle2026"
STRIPE_LINK = "https://buy.stripe.com/14A00lcgHe9oaIodx65Rm00"

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
# CHECK IF COMING FROM STRIPE PAYMENT
# ============================================================
from_payment = st.query_params.get("paid") == "thankyou"

# ============================================================
# NOT LOGGED IN → SHOW MARKETING LANDING PAGE
# ============================================================
if not st.session_state.authenticated:
    
    # ============ HERO SECTION ============
    st.markdown("""
    <div style="text-align: center; padding: 60px 20px 30px 20px;">
        <div style="font-size: 70px; margin-bottom: 15px;">🎯</div>
        <h1 style="font-size: 52px; font-weight: 800; color: #fff; margin-bottom: 10px;">BigSnapshot</h1>
        <p style="color: #888; font-size: 20px; margin-bottom: 10px;">Prediction Market Edge Finder</p>
        <p style="color: #555; font-size: 14px;">Structural analysis for Kalshi markets</p>
    </div>
    """, unsafe_allow_html=True)
    
    # ============ VALUE PROP ============
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
    
    # ============ STRIPE PAYMENT SECTION ============
    if from_payment:
        st.markdown("""
        <div style="max-width: 500px; margin: 30px auto; padding: 30px; background: linear-gradient(135deg, #1a3a2a 0%, #2a4a3a 100%); border-radius: 16px; border: 2px solid #22c55e; text-align: center;">
            <p style="color: #22c55e; font-size: 24px; font-weight: 700; margin-bottom: 15px;">✅ Payment Successful!</p>
            <p style="color: #ccc; font-size: 16px; margin-bottom: 20px;">Your access password is:</p>
            <code style="background: #000; color: #22c55e; padding: 15px 30px; border-radius: 8px; font-size: 24px; font-weight: bold; display: inline-block;">snapcrackle2026</code>
            <p style="color: #888; font-size: 14px; margin-top: 20px;">Enter this password below to unlock all tools.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="max-width: 500px; margin: 30px auto; padding: 30px; background: linear-gradient(135deg, #1a3a2a 0%, #2a4a3a 100%); border-radius: 16px; border: 1px solid #3a5a4a; text-align: center;">
            <p style="color: #22c55e; font-size: 18px; font-weight: 700; margin-bottom: 10px;">🔓 Private Early Access</p>
            <p style="color: #ccc; font-size: 14px; margin-bottom: 20px;">
                Get full access to all prediction market edge tools.<br><strong>$49.99 one-time</strong>. Refund available if not a fit.
            </p>
            <a href="{STRIPE_LINK}" target="_blank">
                <button style="background-color:#22c55e; color:black; padding:16px 40px; border:none; border-radius:10px; font-size:18px; font-weight:700; cursor:pointer;">
                    🔓 Unlock All Tools – $49.99
                </button>
            </a>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ============ LIVE TOOLS PREVIEW (MARKETING) ============
    st.markdown("### 🔥 Live Tools")
    
    st.markdown("""
    <div style="display: flex; justify-content: center; gap: 15px; flex-wrap: wrap; padding: 20px;">
        <div style="background: linear-gradient(135deg, #2a3a2a 0%, #3a4a3a 100%); border-radius: 16px; padding: 25px; width: 140px; text-align: center; border: 2px solid #22c55e;">
            <div style="font-size: 50px; margin-bottom: 10px;">🏀</div>
            <h3 style="color: #4ade80; margin-bottom: 5px;">NBA</h3>
            <span style="background:#22c55e;color:#000;padding:4px 12px;border-radius:20px;font-size:12px;font-weight:700">LIVE</span>
        </div>
        <div style="background: linear-gradient(135deg, #2a3a2a 0%, #3a4a3a 100%); border-radius: 16px; padding: 25px; width: 140px; text-align: center; border: 2px solid #22c55e;">
            <div style="font-size: 50px; margin-bottom: 10px;">🏈</div>
            <h3 style="color: #4ade80; margin-bottom: 5px;">NFL</h3>
            <span style="background:#22c55e;color:#000;padding:4px 12px;border-radius:20px;font-size:12px;font-weight:700">LIVE</span>
        </div>
        <div style="background: linear-gradient(135deg, #2a3a2a 0%, #3a4a3a 100%); border-radius: 16px; padding: 25px; width: 140px; text-align: center; border: 2px solid #22c55e;">
            <div style="font-size: 50px; margin-bottom: 10px;">🏒</div>
            <h3 style="color: #4ade80; margin-bottom: 5px;">NHL</h3>
            <span style="background:#22c55e;color:#000;padding:4px 12px;border-radius:20px;font-size:12px;font-weight:700">LIVE</span>
        </div>
        <div style="background: linear-gradient(135deg, #2a3a2a 0%, #3a4a3a 100%); border-radius: 16px; padding: 25px; width: 140px; text-align: center; border: 2px solid #22c55e;">
            <div style="font-size: 50px; margin-bottom: 10px;">🎓</div>
            <h3 style="color: #4ade80; margin-bottom: 5px;">NCAA</h3>
            <span style="background:#22c55e;color:#000;padding:4px 12px;border-radius:20px;font-size:12px;font-weight:700">LIVE</span>
        </div>
        <div style="background: linear-gradient(135deg, #2a3a2a 0%, #3a4a3a 100%); border-radius: 16px; padding: 25px; width: 140px; text-align: center; border: 2px solid #22c55e;">
            <div style="font-size: 50px; margin-bottom: 10px;">⚽</div>
            <h3 style="color: #4ade80; margin-bottom: 5px;">Soccer</h3>
            <span style="background:#22c55e;color:#000;padding:4px 12px;border-radius:20px;font-size:12px;font-weight:700">LIVE</span>
        </div>
        <div style="background: linear-gradient(135deg, #2a3a2a 0%, #3a4a3a 100%); border-radius: 16px; padding: 25px; width: 140px; text-align: center; border: 2px solid #22c55e;">
            <div style="font-size: 50px; margin-bottom: 10px;">🌡️</div>
            <h3 style="color: #4ade80; margin-bottom: 5px;">Temp</h3>
            <span style="background:#22c55e;color:#000;padding:4px 12px;border-radius:20px;font-size:12px;font-weight:700">LIVE</span>
        </div>
        <div style="background: linear-gradient(135deg, #2a3a2a 0%, #3a4a3a 100%); border-radius: 16px; padding: 25px; width: 140px; text-align: center; border: 2px solid #22c55e;">
            <div style="font-size: 50px; margin-bottom: 10px;">📈</div>
            <h3 style="color: #4ade80; margin-bottom: 5px;">Economics</h3>
            <span style="background:#4ade80;color:#000;padding:4px 12px;border-radius:20px;font-size:12px;font-weight:700">NEW</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # ============ COMING SOON (MARKETING) ============
    st.markdown("### 🚧 Coming Soon")
    st.markdown("""
    <div style="display: flex; justify-content: center; gap: 15px; flex-wrap: wrap; padding: 20px;">
        <div style="background: linear-gradient(135deg, #2a2a2a 0%, #3a3a3a 100%); border-radius: 12px; padding: 20px; width: 140px; text-align: center; border: 1px solid #4a4a4a; opacity: 0.7;">
            <div style="font-size: 35px; margin-bottom: 8px;">⚾</div>
            <h4 style="color: #888; margin: 0;">MLB</h4>
        </div>
        <div style="background: linear-gradient(135deg, #2a2a2a 0%, #3a3a3a 100%); border-radius: 12px; padding: 20px; width: 140px; text-align: center; border: 1px solid #4a4a4a; opacity: 0.7;">
            <div style="font-size: 35px; margin-bottom: 8px;">🏛️</div>
            <h4 style="color: #888; margin: 0;">Politics</h4>
        </div>
        <div style="background: linear-gradient(135deg, #2a2a2a 0%, #3a3a3a 100%); border-radius: 12px; padding: 20px; width: 140px; text-align: center; border: 1px solid #4a4a4a; opacity: 0.7;">
            <div style="font-size: 35px; margin-bottom: 8px;">🎬</div>
            <h4 style="color: #888; margin: 0;">Entertainment</h4>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # ============ BOTTOM LINE + SECOND CTA ============
    st.markdown("""
    <div style="text-align: center; padding: 40px 20px; max-width: 700px; margin: 0 auto;">
        <p style="color: #888; font-size: 1.2em; margin-bottom: 20px;">
            BigSnapshot doesn't help you chase wins. It helps you make fewer bad decisions.
        </p>
        <p style="color: #fff; font-weight: bold; font-size: 1.3em;">That's where real edge comes from.</p>
    </div>
    """, unsafe_allow_html=True)
    
    if not from_payment:
        st.markdown(f"""
        <div style="text-align: center; margin: 30px 0;">
            <a href="{STRIPE_LINK}" target="_blank">
                <button style="background-color:#22c55e; color:black; padding:16px 40px; border:none; border-radius:10px; font-size:18px; font-weight:700; cursor:pointer;">
                    🔓 Unlock All Tools – $49.99
                </button>
            </a>
            <p style="color: #888; font-size: 13px; margin-top: 12px;">One-time payment. Refund available if not a fit.</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ============ PASSWORD ENTRY ============
    st.markdown("""
    <div style="max-width: 400px; margin: 30px auto; text-align: center;">
        <p style="color: #888; font-size: 14px; margin-bottom: 15px;">Already paid? Enter your access code below.</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        password = st.text_input("🔑 Enter Access Code", type="password", key="login_password")
        
        if st.button("🔓 LOGIN", use_container_width=True, type="primary"):
            if password.lower() == VALID_PASSWORD.lower():
                streamlit_js_eval(
                    js_expressions="localStorage.setItem('bigsnapshot_auth', 'Paid Subscriber')",
                    key="set_auth"
                )
                st.session_state.authenticated = True
                st.session_state.user_type = "Paid Subscriber"
                st.rerun()
            else:
                st.error("❌ Invalid access code")
    
    # ============ FOOTER ============
    st.markdown("""
    <div style="text-align: center; padding: 40px 20px;">
        <p style="color: #555; font-size: 12px;">
            Request a refund within 7 days. No questions asked.
        </p>
        <p style="color: #555; font-size: 12px;">
            ⚠️ For entertainment only. Not financial advice.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.stop()

# ============================================================
# AUTHENTICATED - SHOW APP HUB
# ============================================================
st.markdown("## 🎯 BigSnapshot")
st.success(f"✅ Logged in as: {st.session_state.user_type}")

st.markdown("---")

# ============ LIVE TOOLS - CLICKABLE BUTTONS ============
st.subheader("🔥 Live Tools")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("### 🏀 NBA")
    if st.button("OPEN NBA", use_container_width=True, type="primary", key="nav_nba"):
        st.switch_page("pages/2_NBA.py")

with col2:
    st.markdown("### 🏈 NFL")
    if st.button("OPEN NFL", use_container_width=True, type="primary", key="nav_nfl"):
        st.switch_page("pages/1_NFL.py")

with col3:
    st.markdown("### 🏒 NHL")
    if st.button("OPEN NHL", use_container_width=True, type="primary", key="nav_nhl"):
        st.switch_page("pages/3_NHL.py")

with col4:
    st.markdown("### 🎓 NCAA")
    if st.button("OPEN NCAA", use_container_width=True, type="primary", key="nav_ncaa"):
        st.switch_page("pages/7_NCAA.py")

col5, col6, col7, col8 = st.columns(4)

with col5:
    st.markdown("### ⚽ Soccer")
    if st.button("OPEN SOCCER", use_container_width=True, type="primary", key="nav_soccer"):
        st.switch_page("pages/8_Soccer.py")

with col6:
    st.markdown("### 🌡️ Temp")
    if st.button("OPEN TEMP", use_container_width=True, type="primary", key="nav_temp"):
        st.switch_page("pages/5_Temp.py")

with col7:
    st.markdown("### 📈 Econ")
    if st.button("OPEN ECONOMICS", use_container_width=True, type="primary", key="nav_econ"):
        st.switch_page("pages/9_Economics.py")

with col8:
    st.markdown("### ⚾ MLB")
    st.button("COMING MARCH 2026", use_container_width=True, disabled=True, key="nav_mlb")

st.markdown("---")

# ============ COMING SOON ============
st.caption("🚧 Coming Soon: Politics • Entertainment")

st.markdown("---")

# ============ LOGOUT ============
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("🚪 Logout", use_container_width=True):
        streamlit_js_eval(
            js_expressions="localStorage.removeItem('bigsnapshot_auth')",
            key="clear_auth"
        )
        st.session_state.authenticated = False
        st.session_state.user_type = None
        st.rerun()

# ============ FOOTER ============
st.markdown("""
<div style="text-align: center; padding: 20px;">
    <p style="color: #555; font-size: 12px;">⚠️ For entertainment only. Not financial advice.</p>
</div>
""", unsafe_allow_html=True)
