import streamlit as st

st.set_page_config(page_title="BigSnapshot", page_icon="🎯", layout="wide")

# ============================================================
# DO NOT CALL require_auth() HERE - THIS IS THE LOGIN PAGE
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
VALID_PASSWORDS = {
    "WILLIE1228": "Owner",
    "SNAPCRACKLE2026": "Paid Subscriber",
}
STRIPE_LINK = "https://buy.stripe.com/8wMaGP5pSgGU5NYfZ2"

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
    
    # ============ FREE TEMP BUTTON (COSTCO CHICKEN) ============
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #3a2a1a 0%, #4a3a2a 100%); border-radius: 16px; border: 2px solid #f97316;">
            <div style="font-size: 50px; margin-bottom: 10px;">🌡️</div>
            <h3 style="color: #f97316; margin-bottom: 10px;">Try It Free</h3>
            <p style="color: #ccc; font-size: 14px; margin-bottom: 15px;">See how we detect edge in temperature markets — no signup required.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🌡️ TRY TEMP EDGE FINDER FREE", use_container_width=True, type="secondary", key="free_temp"):
            st.switch_page("pages/5_Temp.py")
    
    st.markdown("---")
    
    # ============ STRIPE CTA ============
    st.markdown(f"""
    <div style="text-align: center; padding: 30px;">
        <h3 style="color: #fff; margin-bottom: 10px;">Ready for the full toolkit?</h3>
        <p style="color: #888; margin-bottom: 20px;">
            Get access to all edge finders: NBA, NFL, NHL, NCAA, Soccer, Economics and more.<br>
            Refund available if not a fit.
        </p>
        <a href="{STRIPE_LINK}" target="_blank">
            <button style="background-color:#22c55e; color:black; padding:16px 40px; border:none; border-radius:10px; font-size:18px; font-weight:700; cursor:pointer;">
                🔓 Unlock All Tools – $49.99/month
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
        <div style="background: linear-gradient(135deg, #3a2a1a 0%, #4a3a2a 100%); border-radius: 16px; padding: 25px; width: 140px; text-align: center; border: 2px solid #f97316;">
            <div style="font-size: 50px; margin-bottom: 10px;">🌡️</div>
            <h3 style="color: #f97316; margin-bottom: 5px;">Temp</h3>
            <span style="background:#f97316;color:#000;padding:4px 12px;border-radius:20px;font-size:12px;font-weight:700">FREE</span>
        </div>
        <div style="background: linear-gradient(135deg, #2a3a2a 0%, #3a4a3a 100%); border-radius: 16px; padding: 25px; width: 140px; text-align: center; border: 2px solid #22c55e;">
            <div style="font-size: 50px; margin-bottom: 10px;">⚽</div>
            <h3 style="color: #4ade80; margin-bottom: 5px;">Soccer</h3>
            <span style="background:#22c55e;color:#000;padding:4px 12px;border-radius:20px;font-size:12px;font-weight:700">LIVE</span>
        </div>
        <div style="background: linear-gradient(135deg, #2a3a2a 0%, #3a4a3a 100%); border-radius: 16px; padding: 25px; width: 140px; text-align: center; border: 2px solid #3b82f6;">
            <div style="font-size: 50px; margin-bottom: 10px;">📊</div>
            <h3 style="color: #60a5fa; margin-bottom: 5px;">Economics</h3>
            <span style="background:#3b82f6;color:#fff;padding:4px 12px;border-radius:20px;font-size:12px;font-weight:700">NEW</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # ============ COMING SOON ============
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
    
    # ============ BOTTOM CTA ============
    st.markdown(f"""
    <div style="text-align: center; padding: 30px;">
        <p style="color: #888; font-size: 18px; margin-bottom: 20px;">
            Fewer bad decisions = Fewer bad trades.<br>
            <span style="color: #4ade80;">That's the edge.</span>
        </p>
        <a href="{STRIPE_LINK}" target="_blank">
            <button style="background-color:#22c55e; color:black; padding:16px 40px; border:none; border-radius:10px; font-size:18px; font-weight:700; cursor:pointer;">
                💳 Get Access – $49.99/month
            </button>
        </a>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ============ PASSWORD REVEAL (after Stripe) ============
    if from_payment:
        st.success("✅ Payment received! Your password is: **SNAPCRACKLE2026**")
        st.info("Enter it below to access all tools.")
    
    # ============ PASSWORD ENTRY ============
    st.markdown("### 🔑 Already Paid?")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        password = st.text_input("Enter your password", type="password", placeholder="Password")
        if st.button("🔓 LOGIN", use_container_width=True, type="primary"):
            if password.upper() in VALID_PASSWORDS:
                st.session_state.authenticated = True
                st.session_state.user_type = VALID_PASSWORDS[password.upper()]
                # Save to localStorage for persistence
                streamlit_js_eval(
                    js_expressions=f"localStorage.setItem('bigsnapshot_auth', '{st.session_state.user_type}')",
                    key="save_auth"
                )
                st.rerun()
            else:
                st.error("❌ Invalid password")
    
    # ============ FOOTER ============
    st.markdown("""
    <div style="text-align: center; padding: 40px 20px; margin-top: 20px;">
        <p style="color: #888; font-size: 13px; margin-bottom: 15px;">
            <strong>💳 Refund Policy:</strong> Not satisfied? Request a refund within 7 days. No questions asked.
        </p>
        <p style="color: #555; font-size: 12px;">
            ⚠️ For entertainment only. Not financial advice.
        </p>
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# LOGGED IN → SHOW APP HUB
# ============================================================
else:
    st.title("🎯 BigSnapshot")
    st.success(f"✅ Logged in as: {st.session_state.user_type}")
    
    st.markdown("### 🔥 Live Tools")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("🏀 NBA Edge", use_container_width=True):
            st.switch_page("pages/2_NBA.py")
        if st.button("🏈 NFL Edge", use_container_width=True):
            st.switch_page("pages/1_NFL.py")
    with col2:
        if st.button("🏒 NHL Edge", use_container_width=True):
            st.switch_page("pages/3_NHL.py")
        if st.button("⚽ Soccer Edge", use_container_width=True):
            st.switch_page("pages/8_Soccer.py")
    with col3:
        if st.button("🎓 NCAA Edge", use_container_width=True):
            st.switch_page("pages/7_NCAA.py")
        if st.button("📊 Economics", use_container_width=True):
            st.switch_page("pages/9_Economics.py")
    with col4:
        if st.button("🌡️ Temp Edge (FREE)", use_container_width=True):
            st.switch_page("pages/5_Temp.py")
    
    st.markdown("### 🚧 Coming Soon")
    st.markdown("⚾ MLB • 🏛️ Politics • 🎬 Entertainment")
    
    st.divider()
    
    if st.button("🚪 Logout"):
        streamlit_js_eval(js_expressions="localStorage.removeItem('bigsnapshot_auth')", key="logout")
        st.session_state.authenticated = False
        st.session_state.user_type = None
        st.rerun()
    
    # Footer
    st.markdown("""
    <div style="text-align: center; padding: 20px;">
        <p style="color: #555; font-size: 12px;">
            ⚠️ For entertainment only. Not financial advice.
        </p>
    </div>
    """, unsafe_allow_html=True)
