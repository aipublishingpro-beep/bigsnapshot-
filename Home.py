import streamlit as st

st.set_page_config(
    page_title="BigSnapshot | Prediction Market Edge Finder",
    page_icon="📊",
    layout="wide"
)

# ============================================================
# GA4 TRACKING
# ============================================================
st.markdown("""
<script async src="https://www.googletagmanager.com/gtag/js?id=G-NQKY5VQ376"></script>
<script>window.dataLayer = window.dataLayer || [];function gtag(){dataLayer.push(arguments);}gtag('js', new Date());gtag('config', 'G-NQKY5VQ376');</script>
""", unsafe_allow_html=True)

# ============================================================
# SESSION STATE
# ============================================================
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_type' not in st.session_state:
    st.session_state.user_type = None

# ============================================================
# PASSWORD CONFIG - PAID ACCESS ONLY
# ============================================================
VALID_PASSWORDS = {
    "WILLIE1228": "Owner",
    "SNAPCRACKLE2026": "Paid Subscriber",
}

# ============================================================
# STRIPE PAYMENT LINK
# ============================================================
STRIPE_LINK = "https://buy.stripe.com/14A00lcgHe9oaIodx65Rm00"

# ============================================================
# CUSTOM CSS
# ============================================================
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stApp {
        background: linear-gradient(180deg, #0a0a0f 0%, #1a1a2e 100%);
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# LOGIN PAGE
# ============================================================
if not st.session_state.authenticated:
    st.markdown("""
    <div style="text-align: center; padding: 60px 20px 30px 20px;">
        <div style="font-size: 70px; margin-bottom: 15px;">📊</div>
        <h1 style="font-size: 52px; font-weight: 800; color: #fff; margin-bottom: 10px;">BigSnapshot</h1>
        <p style="color: #888; font-size: 20px; margin-bottom: 10px;">Prediction Market Edge Finder</p>
        <p style="color: #555; font-size: 14px;">Structural analysis for Kalshi markets</p>
    </div>
    """, unsafe_allow_html=True)
    
    # ============ STRIPE PAYMENT SECTION ============
    st.markdown("""
    <div style="max-width: 500px; margin: 30px auto; padding: 30px;
                background: linear-gradient(135deg, #1a3a2a 0%, #2a4a3a 100%);
                border-radius: 16px; border: 1px solid #3a5a4a; text-align: center;">
        <p style="color: #00c853; font-size: 18px; font-weight: 700; margin-bottom: 10px;">🔓 Private Early Access</p>
        <p style="color: #ccc; font-size: 14px; margin-bottom: 20px;">
            Private early access. <strong>$49.99 one-time</strong>. Refund available if not a fit.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Stripe Button
    st.markdown(
        f"""
        <div style="text-align: center; margin: 20px 0;">
            <a href="{STRIPE_LINK}" target="_blank">
                <button style="
                    background-color:#22c55e;
                    color:black;
                    padding:14px 32px;
                    border:none;
                    border-radius:8px;
                    font-size:17px;
                    font-weight:700;
                    cursor:pointer;
                ">
                    Unlock Early Access – $49.99
                </button>
            </a>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    st.markdown("---")
    
    # ============ PASSWORD ENTRY FOR PAID USERS ============
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
                st.session_state.authenticated = True
                st.session_state.user_type = VALID_PASSWORDS[password_input.upper()]
                st.rerun()
            else:
                st.error("❌ Invalid password")
        
        st.markdown("""
        <p style="color: #555; font-size: 11px; margin-top: 20px; text-align: center;">
            Questions? aipublishingpro@gmail.com
        </p>
        """, unsafe_allow_html=True)
    
    st.stop()

# ============================================================
# AUTHENTICATED - SHOW APP HUB
# ============================================================
st.markdown("""
<div style="text-align: center; padding: 60px 20px 40px 20px;">
    <div style="font-size: 70px; margin-bottom: 15px;">📊</div>
    <h1 style="font-size: 52px; font-weight: 800; color: #fff; margin-bottom: 10px;">BigSnapshot</h1>
    <p style="color: #888; font-size: 20px; margin-bottom: 10px;">Prediction Market Edge Finder</p>
    <p style="color: #555; font-size: 14px;">Structural analysis for Kalshi markets</p>
</div>
""", unsafe_allow_html=True)

# Active App Cards
st.markdown("### 🎯 Live Tools")
st.markdown("""
<div style="display: flex; justify-content: center; gap: 20px; flex-wrap: wrap; padding: 20px;">
    <div style="background: linear-gradient(135deg, #1a2a4a 0%, #2a3a5a 100%); border-radius: 16px; padding: 30px; width: 280px; text-align: center; border: 1px solid #3a4a6a;">
        <div style="font-size: 50px; margin-bottom: 15px;">🏀</div>
        <h3 style="color: #fff; margin-bottom: 10px;">NBA Edge Finder</h3>
        <p style="color: #888; font-size: 14px;">12-factor analysis for NBA markets</p>
    </div>
    <div style="background: linear-gradient(135deg, #2a3a2a 0%, #3a4a3a 100%); border-radius: 16px; padding: 30px; width: 280px; text-align: center; border: 1px solid #4a5a4a;">
        <div style="font-size: 50px; margin-bottom: 15px;">🏈</div>
        <h3 style="color: #fff; margin-bottom: 10px;">NFL Edge Finder</h3>
        <p style="color: #888; font-size: 14px;">10-factor analysis for NFL markets</p>
    </div>
    <div style="background: linear-gradient(135deg, #3a2a2a 0%, #4a3a3a 100%); border-radius: 16px; padding: 30px; width: 280px; text-align: center; border: 1px solid #5a4a4a;">
        <div style="font-size: 50px; margin-bottom: 15px;">🌡️</div>
        <h3 style="color: #fff; margin-bottom: 10px;">Temp Edge Finder</h3>
        <p style="color: #888; font-size: 14px;">Weather market analysis</p>
    </div>
</div>
""", unsafe_allow_html=True)

# Navigation buttons
col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])
with col2:
    if st.button("🏀 Open NBA", use_container_width=True):
        st.switch_page("pages/2_NBA.py")
with col3:
    if st.button("🏈 Open NFL", use_container_width=True):
        st.switch_page("pages/1_NFL.py")
with col4:
    if st.button("🌡️ Open Temp", use_container_width=True):
        st.switch_page("pages/3_Temp.py")

# Logout
st.markdown("---")

# Coming Soon Cards
st.markdown("### 🚧 Coming Soon")
st.markdown("""
<div style="display: flex; justify-content: center; gap: 20px; flex-wrap: wrap; padding: 20px;">
    <div style="background: linear-gradient(135deg, #2a2a2a 0%, #3a3a3a 100%); border-radius: 16px; padding: 25px; width: 200px; text-align: center; border: 1px solid #4a4a4a; opacity: 0.7;">
        <div style="font-size: 40px; margin-bottom: 10px;">🏒</div>
        <h4 style="color: #888; margin-bottom: 5px;">NHL</h4>
    </div>
    <div style="background: linear-gradient(135deg, #2a2a2a 0%, #3a3a3a 100%); border-radius: 16px; padding: 25px; width: 200px; text-align: center; border: 1px solid #4a4a4a; opacity: 0.7;">
        <div style="font-size: 40px; margin-bottom: 10px;">⚾</div>
        <h4 style="color: #888; margin-bottom: 5px;">MLB</h4>
    </div>
    <div style="background: linear-gradient(135deg, #2a2a2a 0%, #3a3a3a 100%); border-radius: 16px; padding: 25px; width: 200px; text-align: center; border: 1px solid #4a4a4a; opacity: 0.7;">
        <div style="font-size: 40px; margin-bottom: 10px;">⚽</div>
        <h4 style="color: #888; margin-bottom: 5px;">Soccer</h4>
    </div>
    <div style="background: linear-gradient(135deg, #2a2a2a 0%, #3a3a3a 100%); border-radius: 16px; padding: 25px; width: 200px; text-align: center; border: 1px solid #4a4a4a; opacity: 0.7;">
        <div style="font-size: 40px; margin-bottom: 10px;">🏛️</div>
        <h4 style="color: #888; margin-bottom: 5px;">Politics</h4>
    </div>
    <div style="background: linear-gradient(135deg, #2a2a2a 0%, #3a3a3a 100%); border-radius: 16px; padding: 25px; width: 200px; text-align: center; border: 1px solid #4a4a4a; opacity: 0.7;">
        <div style="font-size: 40px; margin-bottom: 10px;">📈</div>
        <h4 style="color: #888; margin-bottom: 5px;">Economics</h4>
    </div>
    <div style="background: linear-gradient(135deg, #2a2a2a 0%, #3a3a3a 100%); border-radius: 16px; padding: 25px; width: 200px; text-align: center; border: 1px solid #4a4a4a; opacity: 0.7;">
        <div style="font-size: 40px; margin-bottom: 10px;">🎬</div>
        <h4 style="color: #888; margin-bottom: 5px;">Entertainment</h4>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.user_type = None
        st.rerun()
