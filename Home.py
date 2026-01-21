import streamlit as st
from styles import apply_styles
import extra_streamlit_components as stx

st.set_page_config(
    page_title="BigSnapshot | Prediction Market Edge Finder",
    page_icon="📊",
    layout="wide"
)

apply_styles()

# ============================================================
# COOKIE MANAGER FOR PERSISTENT LOGIN
# ============================================================
cookie_manager = stx.CookieManager()

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
# CHECK COOKIE FOR PERSISTENT LOGIN
# ============================================================
auth_cookie = cookie_manager.get("bigsnapshot_auth")
if auth_cookie and not st.session_state.authenticated:
    st.session_state.authenticated = True
    st.session_state.user_type = auth_cookie

# ============================================================
# PASSWORD CONFIG - PAID ACCESS ONLY
# ============================================================
VALID_PASSWORDS = {
    "WILLIE1228": "Owner",
    "SNAPCRACKLE2026": "Paid Subscriber",
}

# ============================================================
# STRIPE PAYMENT LINK + AUTO-REVEAL TOKEN
# ============================================================
STRIPE_LINK = "https://buy.stripe.com/14A00lcgHe9oaIodx65Rm00"
ACCESS_PASSWORD = "SNAPCRACKLE2026"
PAID_TOKEN = "thankyou"

# ============================================================
# DETECT STRIPE REDIRECT (query params)
# ============================================================
query_params = st.query_params
from_payment = query_params.get("paid") in ["true", PAID_TOKEN]
is_production_token = query_params.get("paid") == PAID_TOKEN

# ============================================================
# PAGE-SPECIFIC CSS
# ============================================================
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(180deg, #0a0a0f 0%, #1a1a2e 100%);
    }
    [data-testid="stSidebar"] {display: none;}
</style>
""", unsafe_allow_html=True)

# ============================================================
# LANDING PAGE (NOT LOGGED IN)
# ============================================================
if not st.session_state.authenticated:
    
    # ============ PAID USER FLOW - SKIP TO PASSWORD ============
    if from_payment:
        st.markdown("""
        <div style="text-align: center; padding: 50px 20px 20px 20px;">
            <div style="font-size: 60px; margin-bottom: 15px;">📊</div>
            <h1 style="font-size: 2.5em; color: #fff;">BigSnapshot</h1>
            <p style="color: #888; font-size: 1.1em;">Prediction Market Edge Finder</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.success("✅ Payment received. Enter your access password below.")
        
        if is_production_token:
            st.markdown("### 🔑 Your access password:")
            st.code(ACCESS_PASSWORD)
        
        st.markdown("---")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            password_input = st.text_input("Password", type="password", label_visibility="collapsed", placeholder="Enter password")
            if st.button("🔓 UNLOCK", use_container_width=True, type="primary"):
                if password_input.upper() in VALID_PASSWORDS:
                    st.session_state.authenticated = True
                    st.session_state.user_type = VALID_PASSWORDS[password_input.upper()]
                    cookie_manager.set("bigsnapshot_auth", VALID_PASSWORDS[password_input.upper()], max_age=30*24*60*60)
                    st.rerun()
                else:
                    st.error("❌ Invalid password")
        
        st.stop()
    
    # ============ REGULAR MARKETING FLOW ============
    
    # ============ HERO ============
    st.markdown("""
    <div style="text-align: center; padding: 50px 20px 20px 20px;">
        <div style="font-size: 60px; margin-bottom: 15px;">📊</div>
        <h1 style="font-size: 2.8em; margin-bottom: 0; color: #fff;">Stop Switching Tabs.</h1>
        <h1 style="font-size: 2.8em; margin-top: 5px; color: #00d4ff;">Start Making Cleaner Decisions.</h1>
        <p style="font-size: 1.2em; color: #888; max-width: 700px; margin: 25px auto;">
            BigSnapshot is a decision-compression tool for serious Kalshi bettors. It pulls the signals that matter into one screen—so you spend less time hunting and more time deciding.
        </p>
        <p style="color: #666; font-size: 1.1em;">No hype. No picks shoved in your face. Just clarity.</p>
        <p style="color: #555; font-size: 1em; margin-top: 20px;">Because edge disappears once everyone sees it.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # ============ FREE TEMP BUTTON ============
    st.markdown(
        """
        <div style="text-align: center; margin: 30px 0 15px 0;">
            <a href="/Temp" target="_self">
                <button style="
                    background-color:#f59e0b;
                    color:black;
                    padding:14px 36px;
                    border:none;
                    border-radius:10px;
                    font-size:16px;
                    font-weight:700;
                    cursor:pointer;
                ">
                    🌡️ Try Temp Edge Finder FREE
                </button>
            </a>
            <p style="color: #888; font-size: 12px; margin-top: 10px;">No signup required. See it in action.</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # ============ STRIPE BUY BUTTON (TOP) ============
    if not from_payment:
        st.markdown(
            f"""
            <div style="text-align: center; margin: 15px 0 30px 0;">
                <a href="{STRIPE_LINK}" target="_blank">
                    <button style="
                        background-color:#22c55e;
                        color:black;
                        padding:16px 40px;
                        border:none;
                        border-radius:10px;
                        font-size:18px;
                        font-weight:700;
                        cursor:pointer;
                    ">
                        🔓 Unlock All Tools – $49.99
                    </button>
                </a>
                <p style="color: #888; font-size: 13px; margin-top: 12px;">One-time payment. Refund available if not a fit.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    # ============ ONE SCREEN SECTION ============
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1a1a2e, #16213e); border-radius: 16px; padding: 40px; margin: 40px auto; max-width: 900px;">
        <h2 style="color: #fff; text-align: center; margin-bottom: 20px;">One Screen. One Flow. Zero Noise.</h2>
        <p style="color: #aaa; text-align: center; font-size: 1.1em; margin-bottom: 25px;">
            Most bettors lose edge before they even place a bet—switching between odds, stats, line movement, news, and gut instinct. BigSnapshot fixes that.
        </p>
        <div style="display: flex; justify-content: center; gap: 40px; flex-wrap: wrap;">
            <div style="text-align: center;">
                <span style="color: #00ff88; font-size: 1.1em;">✓ Where the edge is</span>
            </div>
            <div style="text-align: center;">
                <span style="color: #00ff88; font-size: 1.1em;">✓ Whether the market agrees or resists</span>
            </div>
            <div style="text-align: center;">
                <span style="color: #00ff88; font-size: 1.1em;">✓ What deserves attention—and what doesn't</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # ============ BENEFITS GRID ============
    st.markdown("### Why BigSnapshot Is Different")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div style="background: #1a1a2e; border-radius: 12px; padding: 24px; margin-bottom: 16px; border-left: 4px solid #00d4ff;">
            <h3 style="color: #00d4ff; margin: 0 0 10px 0;">⏱️ Save Time on Every Slate</h3>
            <p style="color: #aaa; margin: 0;">No bouncing between sportsbooks, stats sites, and Twitter. No manual cross-checking. Scan an entire slate in seconds.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div style="background: #1a1a2e; border-radius: 12px; padding: 24px; margin-bottom: 16px; border-left: 4px solid #ff6b6b;">
            <h3 style="color: #ff6b6b; margin: 0 0 10px 0;">🎯 Decision Compression</h3>
            <p style="color: #aaa; margin: 0;">Raw data is distilled into clear signals. You see what matters, not everything. Analysis paralysis disappears.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div style="background: #1a1a2e; border-radius: 12px; padding: 24px; margin-bottom: 16px; border-left: 4px solid #ffd93d;">
            <h3 style="color: #ffd93d; margin: 0 0 10px 0;">📊 Market Awareness</h3>
            <p style="color: #aaa; margin: 0;">Instantly know if the market supports your view. Instantly know when it's pushing back. You're aware before you commit.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div style="background: #1a1a2e; border-radius: 12px; padding: 24px; margin-bottom: 16px; border-left: 4px solid #a855f7;">
            <h3 style="color: #a855f7; margin: 0 0 10px 0;">🛑 Stops You From Chasing Steam</h3>
            <p style="color: #aaa; margin: 0;">Late moves are obvious. Resistance is clearly flagged. The app naturally slows you down when chasing would hurt you most.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="background: #1a1a2e; border-radius: 12px; padding: 24px; margin-bottom: 16px; border-left: 4px solid #4ade80;">
            <h3 style="color: #4ade80; margin: 0 0 10px 0;">🧘 Discipline Built In</h3>
            <p style="color: #aaa; margin: 0;">No BUY / SELL hype. No flashing alerts. No forced picks. BigSnapshot encourages restraint instead of impulsive action.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div style="background: #1a1a2e; border-radius: 12px; padding: 24px; margin-bottom: 16px; border-left: 4px solid #38bdf8;">
            <h3 style="color: #38bdf8; margin: 0 0 10px 0;">👀 Early Signal Visibility</h3>
            <p style="color: #aaa; margin: 0;">Spot early pressure before public noise takes over. Especially powerful in thinner markets. Timing improves without forcing volume.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div style="background: #1a1a2e; border-radius: 12px; padding: 24px; margin-bottom: 16px; border-left: 4px solid #f472b6;">
            <h3 style="color: #f472b6; margin: 0 0 10px 0;">✂️ Fewer Bad Bets, Same Good Bets</h3>
            <p style="color: #aaa; margin: 0;">The app doesn't create more bets. It filters out the bad versions of good ideas. Your edge quality improves without trading more.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div style="background: #1a1a2e; border-radius: 12px; padding: 24px; margin-bottom: 16px; border-left: 4px solid #88ff88;">
            <h3 style="color: #88ff88; margin: 0 0 10px 0;">⏳ Time Is the Real Edge</h3>
            <p style="color: #aaa; margin: 0;">Most edges don't fail — they get crowded. BigSnapshot helps you see pressure early, before the market fully reacts.</p>
        </div>
        """, unsafe_allow_html=True)
    
    # ============ RESULT SECTION ============
    st.markdown("""
    <div style="background: linear-gradient(135deg, #0f3460, #1a1a2e); border-radius: 16px; padding: 40px; margin: 40px auto; text-align: center; max-width: 900px;">
        <h2 style="color: #fff; margin-bottom: 20px;">The Result</h2>
        <div style="display: flex; justify-content: center; gap: 30px; flex-wrap: wrap; margin-bottom: 30px;">
            <span style="color: #00ff88; font-size: 1.1em;">✓ Less second-guessing</span>
            <span style="color: #00ff88; font-size: 1.1em;">✓ Less tilt</span>
            <span style="color: #00ff88; font-size: 1.1em;">✓ Fewer mistakes</span>
            <span style="color: #00ff88; font-size: 1.1em;">✓ More trust in your process</span>
        </div>
        <p style="color: #fff; font-size: 1.4em; font-weight: bold; margin: 0;">You don't bet more. You bet cleaner.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # ============ LIVE TOOLS (MARKETING) ============
    st.markdown("### 🎯 Live Tools")
    st.markdown("""
    <div style="display: flex; justify-content: center; gap: 20px; flex-wrap: wrap; padding: 20px;">
        <div style="background: linear-gradient(135deg, #1a2a4a 0%, #2a3a5a 100%); border-radius: 16px; padding: 30px; width: 220px; text-align: center; border: 1px solid #3a4a6a;">
            <div style="font-size: 45px; margin-bottom: 15px;">🏀</div>
            <h3 style="color: #fff; margin-bottom: 10px;">NBA Edge Finder</h3>
        </div>
        <div style="background: linear-gradient(135deg, #2a3a2a 0%, #3a4a3a 100%); border-radius: 16px; padding: 30px; width: 220px; text-align: center; border: 1px solid #4a5a4a;">
            <div style="font-size: 45px; margin-bottom: 15px;">🏈</div>
            <h3 style="color: #fff; margin-bottom: 10px;">NFL Edge Finder</h3>
        </div>
        <div style="background: linear-gradient(135deg, #2a2a3a 0%, #3a3a4a 100%); border-radius: 16px; padding: 30px; width: 220px; text-align: center; border: 1px solid #4a4a5a;">
            <div style="font-size: 45px; margin-bottom: 15px;">🏒</div>
            <h3 style="color: #fff; margin-bottom: 10px;">NHL Edge Finder</h3>
        </div>
        <div style="background: linear-gradient(135deg, #1a2a3a 0%, #2a3a4a 100%); border-radius: 16px; padding: 30px; width: 220px; text-align: center; border: 1px solid #3a4a5a;">
            <div style="font-size: 45px; margin-bottom: 15px;">🎓</div>
            <h3 style="color: #fff; margin-bottom: 10px;">NCAA Edge Finder</h3>
        </div>
        <div style="background: linear-gradient(135deg, #3a2a1a 0%, #4a3a2a 100%); border-radius: 16px; padding: 30px; width: 220px; text-align: center; border: 1px solid #f59e0b;">
            <div style="font-size: 45px; margin-bottom: 15px;">🌡️</div>
            <h3 style="color: #f59e0b; margin-bottom: 5px;">Temp Edge Finder</h3>
            <span style="background:#f59e0b;color:#000;padding:4px 12px;border-radius:20px;font-size:12px;font-weight:700">FREE</span>
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
            <div style="font-size: 35px; margin-bottom: 8px;">⚽</div>
            <h4 style="color: #888; margin: 0;">Soccer</h4>
        </div>
        <div style="background: linear-gradient(135deg, #2a2a2a 0%, #3a3a3a 100%); border-radius: 12px; padding: 20px; width: 140px; text-align: center; border: 1px solid #4a4a4a; opacity: 0.7;">
            <div style="font-size: 35px; margin-bottom: 8px;">🏛️</div>
            <h4 style="color: #888; margin: 0;">Politics</h4>
        </div>
        <div style="background: linear-gradient(135deg, #2a2a2a 0%, #3a3a3a 100%); border-radius: 12px; padding: 20px; width: 140px; text-align: center; border: 1px solid #4a4a4a; opacity: 0.7;">
            <div style="font-size: 35px; margin-bottom: 8px;">📈</div>
            <h4 style="color: #888; margin: 0;">Economics</h4>
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
        st.markdown(
            f"""
            <div style="text-align: center; margin: 30px 0;">
                <a href="{STRIPE_LINK}" target="_blank">
                    <button style="
                        background-color:#22c55e;
                        color:black;
                        padding:16px 40px;
                        border:none;
                        border-radius:10px;
                        font-size:18px;
                        font-weight:700;
                        cursor:pointer;
                    ">
                        🔓 Unlock All Tools – $49.99
                    </button>
                </a>
                <p style="color: #888; font-size: 13px; margin-top: 12px;">One-time payment. Refund available if not a fit.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    
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
                st.session_state.authenticated = True
                st.session_state.user_type = VALID_PASSWORDS[password_input.upper()]
                cookie_manager.set("bigsnapshot_auth", VALID_PASSWORDS[password_input.upper()], max_age=30*24*60*60)
                st.rerun()
            else:
                st.error("❌ Invalid password")
    
    # Footer
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
    
    st.stop()

# ============================================================
# AUTHENTICATED - SHOW APP HUB (LIVE TOOLS FIRST)
# ============================================================
st.title("📊 BigSnapshot")
st.caption("Prediction Market Edge Finder")

st.markdown("---")

# ============ LIVE TOOLS - PURE STREAMLIT ============
st.header("🔥 LIVE TOOLS")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.subheader("🏀 NBA")
    if st.button("OPEN NBA", use_container_width=True, type="primary", key="nav_nba"):
        st.switch_page("pages/2_NBA.py")

with col2:
    st.subheader("🏈 NFL")
    if st.button("OPEN NFL", use_container_width=True, type="primary", key="nav_nfl"):
        st.switch_page("pages/1_NFL.py")

with col3:
    st.subheader("🏒 NHL")
    if st.button("OPEN NHL", use_container_width=True, type="primary", key="nav_nhl"):
        st.switch_page("pages/3_NHL.py")

with col4:
    st.subheader("🎓 NCAA")
    if st.button("OPEN NCAA", use_container_width=True, type="primary", key="nav_ncaa"):
        st.switch_page("pages/7_NCAA.py")

with col5:
    st.subheader("🌡️ TEMP")
    if st.button("OPEN TEMP", use_container_width=True, type="primary", key="nav_temp"):
        st.switch_page("pages/5_Temp.py")

st.markdown("---")

# ============ COMING SOON - MINIMAL ============
st.caption("🚧 Coming Soon: MLB • Soccer • Politics • Economics • Entertainment")

st.markdown("---")

# Logout
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.user_type = None
        cookie_manager.delete("bigsnapshot_auth")
        st.rerun()

# Footer
st.markdown("""
<div style="text-align: center; padding: 20px;">
    <p style="color: #555; font-size: 12px;">
        ⚠️ For entertainment only. Not financial advice.
    </p>
</div>
""", unsafe_allow_html=True)
