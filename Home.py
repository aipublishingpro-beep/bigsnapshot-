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
# PASSWORD CONFIG
# ============================================================
VALID_PASSWORDS = {
    "WILLIE1228": "Owner",
    "SNAPCRACKLE2026": "Paid Subscriber",
}

# ============================================================
# STRIPE CONFIG
# ============================================================
STRIPE_LINK = "https://buy.stripe.com/14A00lcgHe9oaIodx65Rm00"
ACCESS_PASSWORD = "SNAPCRACKLE2026"
PAID_TOKEN = "thankyou"

# ============================================================
# DETECT STRIPE REDIRECT
# ============================================================
query_params = st.query_params
from_payment = query_params.get("paid") == PAID_TOKEN

# ============================================================
# CUSTOM CSS
# ============================================================
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stApp {background: linear-gradient(180deg, #0a0a0f 0%, #1a1a2e 100%);}
    @media (max-width: 768px) {
        h1 {font-size: 36px !important;}
        h2 {font-size: 22px !important;}
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# LOGGED OUT — MARKETING LANDING PAGE
# ============================================================
if not st.session_state.authenticated:
    
    # ============ HERO ============
    st.markdown("""
    <div style="text-align: center; padding: 60px 20px 30px 20px;">
        <div style="font-size: 70px; margin-bottom: 15px;">📊</div>
        <h1 style="font-size: 52px; font-weight: 800; color: #fff; margin-bottom: 10px;">BigSnapshot</h1>
        <p style="color: #888; font-size: 20px; margin-bottom: 10px;">Prediction Market Edge Finder</p>
        <p style="color: #555; font-size: 14px;">Structural analysis for Kalshi markets</p>
    </div>
    """, unsafe_allow_html=True)
    
    # ============ FREE TEMP BUTTON ============
    st.markdown("""
    <div style="text-align: center; margin: 20px 0 30px 0;">
        <p style="color: #f97316; font-size: 16px; font-weight: 600; margin-bottom: 12px;">🌡️ Want to see it in action first?</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🌡️ TRY TEMP EDGE FINDER FREE", use_container_width=True, type="secondary"):
            st.switch_page("pages/5_Temp.py")
    
    st.markdown("""
    <style>
    div[data-testid="stButton"] button[kind="secondary"] {
        background: linear-gradient(135deg, #3a2a1a 0%, #4a3a2a 100%) !important;
        border: 2px solid #f97316 !important;
        color: #f97316 !important;
        font-weight: 700 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
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
    
    # ============ FEWER BAD DECISIONS ============
    st.markdown("""
    <div style="text-align: center; padding: 30px 20px; max-width: 600px; margin: 0 auto;">
        <p style="color: #888; font-size: 1.1em; line-height: 1.8;">
            You don't need more action.<br>
            You need <span style="color: #fff; font-weight: bold;">fewer bad decisions</span>.
        </p>
        <p style="color: #888; font-size: 1em; margin-top: 15px;">
            BigSnapshot doesn't tell you what to bet. It helps you make fewer bad decisions.
        </p>
        <p style="color: #fff; font-weight: bold; font-size: 1.3em; margin-top: 20px;">That's where real edge comes from.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # ============ STRIPE BUTTON ============
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
    
    # ============ PASSWORD REVEAL AFTER PAYMENT ============
    if from_payment:
        st.markdown(f"""
        <div style="max-width: 500px; margin: 30px auto; padding: 25px;
                    background: linear-gradient(135deg, #1a3a2a 0%, #2a4a3a 100%);
                    border-radius: 16px; border: 2px solid #22c55e; text-align: center;">
            <p style="color: #22c55e; font-size: 20px; font-weight: 700; margin-bottom: 15px;">✅ Payment Received!</p>
            <p style="color: #ccc; font-size: 14px; margin-bottom: 15px;">Your access password is:</p>
            <code style="background: #111; color: #22c55e; padding: 12px 24px; border-radius: 8px; font-size: 18px; font-weight: bold; display: inline-block;">{ACCESS_PASSWORD}</code>
            <p style="color: #888; font-size: 12px; margin-top: 15px;">Enter this password below to unlock all tools.</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ============ LIVE TOOLS PREVIEW ============
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
        <div style="background: linear-gradient(135deg, #3a2a1a 0%, #4a3a2a 100%); border-radius: 16px; padding: 25px; width: 140px; text-align: center; border: 2px solid #f97316;">
            <div style="font-size: 50px; margin-bottom: 10px;">🌡️</div>
            <h3 style="color: #f97316; margin-bottom: 5px;">Temp</h3>
            <span style="background:#f97316;color:#000;padding:4px 12px;border-radius:20px;font-size:12px;font-weight:700">FREE</span>
        </div>
        <div style="background: linear-gradient(135deg, #2a3a2a 0%, #3a4a3a 100%); border-radius: 16px; padding: 25px; width: 140px; text-align: center; border: 2px solid #22c55e;">
            <div style="font-size: 50px; margin-bottom: 10px;">📈</div>
            <h3 style="color: #4ade80; margin-bottom: 5px;">Economics</h3>
            <span style="background:#fbbf24;color:#000;padding:4px 12px;border-radius:20px;font-size:12px;font-weight:700">NEW</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # ============ COMING SOON ============
    st.markdown("### 🚧 Coming Soon")
    
    st.markdown("""
    <div style="display: flex; justify-content: center; gap: 15px; flex-wrap: wrap; padding: 20px;">
        <div style="background: linear-gradient(135deg, #1a1a2a 0%, #2a2a3a 100%); border-radius: 16px; padding: 25px; width: 140px; text-align: center; border: 1px solid #444; opacity: 0.7;">
            <div style="font-size: 50px; margin-bottom: 10px;">⚾</div>
            <h3 style="color: #888; margin-bottom: 5px;">MLB</h3>
            <span style="background:#555;color:#fff;padding:4px 12px;border-radius:20px;font-size:12px;font-weight:700">SOON</span>
        </div>
        <div style="background: linear-gradient(135deg, #1a1a2a 0%, #2a2a3a 100%); border-radius: 16px; padding: 25px; width: 140px; text-align: center; border: 1px solid #444; opacity: 0.7;">
            <div style="font-size: 50px; margin-bottom: 10px;">⚽</div>
            <h3 style="color: #888; margin-bottom: 5px;">Soccer</h3>
            <span style="background:#555;color:#fff;padding:4px 12px;border-radius:20px;font-size:12px;font-weight:700">SOON</span>
        </div>
        <div style="background: linear-gradient(135deg, #1a1a2a 0%, #2a2a3a 100%); border-radius: 16px; padding: 25px; width: 140px; text-align: center; border: 1px solid #444; opacity: 0.7;">
            <div style="font-size: 50px; margin-bottom: 10px;">🏛️</div>
            <h3 style="color: #888; margin-bottom: 5px;">Politics</h3>
            <span style="background:#555;color:#fff;padding:4px 12px;border-radius:20px;font-size:12px;font-weight:700">SOON</span>
        </div>
        <div style="background: linear-gradient(135deg, #1a1a2a 0%, #2a2a3a 100%); border-radius: 16px; padding: 25px; width: 140px; text-align: center; border: 1px solid #444; opacity: 0.7;">
            <div style="font-size: 50px; margin-bottom: 10px;">🎬</div>
            <h3 style="color: #888; margin-bottom: 5px;">Entertainment</h3>
            <span style="background:#555;color:#fff;padding:4px 12px;border-radius:20px;font-size:12px;font-weight:700">SOON</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ============ SECOND CTA ============
    st.markdown(f"""
    <div style="text-align: center; margin: 30px 0;">
        <a href="{STRIPE_LINK}" target="_blank">
            <button style="background-color:#22c55e; color:black; padding:16px 40px; border:none; border-radius:10px; font-size:18px; font-weight:700; cursor:pointer;">
                🔓 Unlock All Tools – $49.99
            </button>
        </a>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ============ PASSWORD ENTRY ============
    st.markdown("""
    <div style="max-width: 400px; margin: 30px auto; text-align: center;">
        <p style="color: #888; font-size: 14px; margin-bottom: 15px;">
            Already paid? Enter your password below:
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        password_input = st.text_input("Password", type="password", label_visibility="collapsed", placeholder="Enter password")
        if st.button("🔓 UNLOCK", use_container_width=True, type="primary"):
            if password_input.upper() in VALID_PASSWORDS:
                user_type = VALID_PASSWORDS[password_input.upper()]
                streamlit_js_eval(
                    js_expressions=f"localStorage.setItem('bigsnapshot_auth', '{user_type}')",
                    key="set_auth_main"
                )
                st.session_state.authenticated = True
                st.session_state.user_type = user_type
                st.rerun()
            else:
                st.error("❌ Invalid password")
    
    # ============ REFUND POLICY FOOTER ============
    st.markdown("""
    <div style="text-align: center; padding: 40px 20px; margin-top: 20px;">
        <p style="color: #888; font-size: 13px; margin-bottom: 15px;">
            <strong>💳 Refund Policy:</strong> Not satisfied? Email aipublishingpro@gmail.com within 7 days for a full refund. No questions asked.
        </p>
        <p style="color: #555; font-size: 12px;">
            ⚠️ For entertainment only. Not financial advice.<br>
            📧 aipublishingpro@gmail.com
        </p>
        <p style="color: #444; font-size: 11px; margin-top: 10px;">
            Questions or feedback? Email aipublishingpro@gmail.com
        </p>
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# LOGGED IN — APP HUB
# ============================================================
else:
    st.markdown("""
    <div style="text-align: center; padding: 40px 20px;">
        <div style="font-size: 60px; margin-bottom: 15px;">📊</div>
        <h1 style="font-size: 42px; font-weight: 800; color: #fff; margin-bottom: 10px;">BigSnapshot</h1>
        <p style="color: #4ade80; font-size: 16px;">✅ Logged in as {}</p>
    </div>
    """.format(st.session_state.user_type), unsafe_allow_html=True)
    
    st.markdown("### 🔥 Your Tools")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #2a3a2a 0%, #3a4a3a 100%); border-radius: 16px; padding: 25px; text-align: center; border: 2px solid #22c55e;">
            <div style="font-size: 50px; margin-bottom: 10px;">🏀</div>
            <h3 style="color: #4ade80;">NBA</h3>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open NBA", use_container_width=True, key="nba_btn"):
            st.switch_page("pages/2_NBA.py")
    
    with col2:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #2a3a2a 0%, #3a4a3a 100%); border-radius: 16px; padding: 25px; text-align: center; border: 2px solid #22c55e;">
            <div style="font-size: 50px; margin-bottom: 10px;">🏈</div>
            <h3 style="color: #4ade80;">NFL</h3>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open NFL", use_container_width=True, key="nfl_btn"):
            st.switch_page("pages/3_NFL.py")
    
    with col3:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #2a3a2a 0%, #3a4a3a 100%); border-radius: 16px; padding: 25px; text-align: center; border: 2px solid #22c55e;">
            <div style="font-size: 50px; margin-bottom: 10px;">🏒</div>
            <h3 style="color: #4ade80;">NHL</h3>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open NHL", use_container_width=True, key="nhl_btn"):
            st.switch_page("pages/4_NHL.py")
    
    with col4:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #3a2a1a 0%, #4a3a2a 100%); border-radius: 16px; padding: 25px; text-align: center; border: 2px solid #f97316;">
            <div style="font-size: 50px; margin-bottom: 10px;">🌡️</div>
            <h3 style="color: #f97316;">Temp</h3>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open Temp", use_container_width=True, key="temp_btn"):
            st.switch_page("pages/5_Temp.py")
    
    st.markdown("---")
    
    # ============ LOGOUT BUTTON ============
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
    
    st.markdown("""
    <div style="text-align: center; padding: 40px 20px;">
        <p style="color: #555; font-size: 12px;">
            ⚠️ For entertainment only. Not financial advice.
        </p>
    </div>
    """, unsafe_allow_html=True)
