import streamlit as st

st.set_page_config(page_title="BigSnapshot", page_icon="🎯", layout="wide")

# ============================================================
# GA4 ANALYTICS - SERVER SIDE
# ============================================================
import uuid
import requests as req_ga

def send_ga4_event(page_title, page_path):
    try:
        url = f"https://www.google-analytics.com/mp/collect?measurement_id=G-NQKY5VQ376&api_secret=n4oBJjH7RXi3dA7aQo2CZA"
        payload = {"client_id": str(uuid.uuid4()), "events": [{"name": "page_view", "params": {"page_title": page_title, "page_location": f"https://bigsnapshot.streamlit.app{page_path}"}}]}
        req_ga.post(url, json=payload, timeout=2)
    except: pass

send_ga4_event("Home", "/")

# ============================================================
# COOKIE AUTH SETUP
# ============================================================
import extra_streamlit_components as stx
from datetime import datetime, timedelta

cookie_manager = stx.CookieManager()

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.user_type = None

# Check for existing cookie
saved_auth = cookie_manager.get("authenticated")
if saved_auth == "true":
    st.session_state.authenticated = True
    st.session_state.user_type = "Paid Subscriber"

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
[data-testid="stSidebar"] { display: none; }
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
    
    # ============ LIVE TOOLS SECTION ============
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; margin-bottom: 20px;">
        <h2 style="color: #fff; font-size: 24px;">🔴 LIVE TOOLS</h2>
        <p style="color: #888;">Available now for subscribers</p>
    </div>
    """, unsafe_allow_html=True)
    
    live_col1, live_col2, live_col3 = st.columns(3)
    
    with live_col1:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #1a2a1a 0%, #2a3a2a 100%); border-radius: 12px; padding: 20px; text-align: center; border: 1px solid #22c55e; height: 180px;">
            <div style="font-size: 40px; margin-bottom: 8px;">🏀</div>
            <h4 style="color: #22c55e; margin-bottom: 4px;">NBA</h4>
            <span style="background: #22c55e; color: #000; padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: 700;">LIVE</span>
            <p style="color: #888; font-size: 12px; margin-top: 8px;">Live edge monitor, factor alignment, totals projections</p>
        </div>
        """, unsafe_allow_html=True)
    
    with live_col2:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #1a2a1a 0%, #2a3a2a 100%); border-radius: 12px; padding: 20px; text-align: center; border: 1px solid #22c55e; height: 180px;">
            <div style="font-size: 40px; margin-bottom: 8px;">🏈</div>
            <h4 style="color: #22c55e; margin-bottom: 4px;">NFL</h4>
            <span style="background: #22c55e; color: #000; padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: 700;">LIVE</span>
            <p style="color: #888; font-size: 12px; margin-top: 8px;">Playoff edge finder with live scoring</p>
        </div>
        """, unsafe_allow_html=True)
    
    with live_col3:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #1a2a1a 0%, #2a3a2a 100%); border-radius: 12px; padding: 20px; text-align: center; border: 1px solid #22c55e; height: 180px;">
            <div style="font-size: 40px; margin-bottom: 8px;">🏒</div>
            <h4 style="color: #22c55e; margin-bottom: 4px;">NHL</h4>
            <span style="background: #22c55e; color: #000; padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: 700;">LIVE</span>
            <p style="color: #888; font-size: 12px; margin-top: 8px;">Hockey edge finder with live updates</p>
        </div>
        """, unsafe_allow_html=True)
    
    # ============ COMING SOON SECTION ============
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; margin-bottom: 20px;">
        <h2 style="color: #fff; font-size: 24px;">🔜 COMING SOON</h2>
        <p style="color: #888;">More markets in development</p>
    </div>
    """, unsafe_allow_html=True)
    
    soon_col1, soon_col2, soon_col3, soon_col4 = st.columns(4)
    
    with soon_col1:
        st.markdown("""
        <div style="background: #1a1a2e; border-radius: 12px; padding: 15px; text-align: center; border: 1px solid #444; height: 120px;">
            <div style="font-size: 30px; margin-bottom: 5px;">⚾</div>
            <h4 style="color: #888; margin-bottom: 2px; font-size: 14px;">MLB</h4>
            <span style="color: #666; font-size: 10px;">March 2026</span>
        </div>
        """, unsafe_allow_html=True)
    
    with soon_col2:
        st.markdown("""
        <div style="background: #1a1a2e; border-radius: 12px; padding: 15px; text-align: center; border: 1px solid #444; height: 120px;">
            <div style="font-size: 30px; margin-bottom: 5px;">🎓</div>
            <h4 style="color: #888; margin-bottom: 2px; font-size: 14px;">NCAA</h4>
            <span style="color: #666; font-size: 10px;">March 2026</span>
        </div>
        """, unsafe_allow_html=True)
    
    with soon_col3:
        st.markdown("""
        <div style="background: #1a1a2e; border-radius: 12px; padding: 15px; text-align: center; border: 1px solid #444; height: 120px;">
            <div style="font-size: 30px; margin-bottom: 5px;">⚽</div>
            <h4 style="color: #888; margin-bottom: 2px; font-size: 14px;">Soccer</h4>
            <span style="color: #666; font-size: 10px;">Q2 2026</span>
        </div>
        """, unsafe_allow_html=True)
    
    with soon_col4:
        st.markdown("""
        <div style="background: #1a1a2e; border-radius: 12px; padding: 15px; text-align: center; border: 1px solid #444; height: 120px;">
            <div style="font-size: 30px; margin-bottom: 5px;">📊</div>
            <h4 style="color: #888; margin-bottom: 2px; font-size: 14px;">Economics</h4>
            <span style="color: #666; font-size: 10px;">Q2 2026</span>
        </div>
        """, unsafe_allow_html=True)
    
    # ============ STRIPE PAYMENT SECTION ============
    st.markdown("---")
    
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
            <a href="{STRIPE_LINK}" target="_blank" style="display: inline-block; background: #22c55e; color: #000; padding: 14px 28px; border-radius: 8px; text-decoration: none; font-weight: 700; font-size: 16px;">
                🔓 Unlock All Tools – $49.99
            </a>
            <p style="color: #666; font-size: 12px; margin-top: 15px;">Secure payment via Stripe</p>
        </div>
        """, unsafe_allow_html=True)
    
    # ============ PASSWORD LOGIN ============
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; margin-bottom: 15px;">
        <p style="color: #888; font-size: 14px;">Already have a password?</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        password = st.text_input("Enter password", type="password", key="login_password", label_visibility="collapsed", placeholder="Enter password...")
        if st.button("🔓 LOGIN", use_container_width=True, type="primary"):
            if password.lower() == VALID_PASSWORD.lower() or password.upper() == "WILLIE1228":
                cookie_manager.set("authenticated", "true", expires_at=datetime.now() + timedelta(days=30))
                st.session_state.authenticated = True
                st.session_state.user_type = "Owner" if password.upper() == "WILLIE1228" else "Paid Subscriber"
                st.rerun()
            else:
                st.error("Invalid password")
    
    # ============ FOOTER ============
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; padding: 20px;">
        <p style="color: #666; font-size: 12px;">
            © 2026 BigSnapshot | Built for Kalshi traders<br>
            <span style="color: #555;">Educational tool only. Not financial advice. Trade responsibly.</span>
        </p>
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# LOGGED IN → SHOW APP HUB
# ============================================================
else:
    st.markdown("""
    <div style="text-align: center; padding: 30px 20px;">
        <div style="font-size: 50px; margin-bottom: 10px;">🎯</div>
        <h1 style="font-size: 36px; color: #fff; margin-bottom: 5px;">BigSnapshot</h1>
        <p style="color: #22c55e; font-size: 14px;">✅ Logged in as {}</p>
    </div>
    """.format(st.session_state.user_type or "Subscriber"), unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; margin-bottom: 20px;">
        <h2 style="color: #fff; font-size: 24px;">SELECT A TOOL</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Tool buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #1a2a1a 0%, #2a3a2a 100%); border-radius: 12px; padding: 25px; text-align: center; border: 1px solid #22c55e;">
            <div style="font-size: 50px; margin-bottom: 10px;">🏀</div>
            <h3 style="color: #22c55e; margin-bottom: 5px;">NBA</h3>
            <p style="color: #888; font-size: 12px;">Live edge monitor & totals</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open NBA", use_container_width=True, key="btn_nba"):
            st.switch_page("pages/2_NBA.py")
    
    with col2:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #1a2a1a 0%, #2a3a2a 100%); border-radius: 12px; padding: 25px; text-align: center; border: 1px solid #22c55e;">
            <div style="font-size: 50px; margin-bottom: 10px;">🏈</div>
            <h3 style="color: #22c55e; margin-bottom: 5px;">NFL</h3>
            <p style="color: #888; font-size: 12px;">Playoff edge finder</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open NFL", use_container_width=True, key="btn_nfl"):
            st.switch_page("pages/1_NFL.py")
    
    with col3:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #1a2a1a 0%, #2a3a2a 100%); border-radius: 12px; padding: 25px; text-align: center; border: 1px solid #22c55e;">
            <div style="font-size: 50px; margin-bottom: 10px;">🏒</div>
            <h3 style="color: #22c55e; margin-bottom: 5px;">NHL</h3>
            <p style="color: #888; font-size: 12px;">Hockey edge finder</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open NHL", use_container_width=True, key="btn_nhl"):
            st.switch_page("pages/3_NHL.py")
    
    st.markdown("---")
    
    col4, col5 = st.columns(2)
    
    with col4:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #2a2a1a 0%, #3a3a2a 100%); border-radius: 12px; padding: 25px; text-align: center; border: 1px solid #f97316;">
            <div style="font-size: 50px; margin-bottom: 10px;">🌡️</div>
            <h3 style="color: #f97316; margin-bottom: 5px;">TEMP</h3>
            <p style="color: #888; font-size: 12px;">Temperature edge finder</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open Temp", use_container_width=True, key="btn_temp"):
            st.switch_page("pages/5_Temp.py")
    
    with col5:
        st.markdown("""
        <div style="background: #1a1a2e; border-radius: 12px; padding: 25px; text-align: center; border: 1px solid #444;">
            <div style="font-size: 50px; margin-bottom: 10px;">⚾</div>
            <h3 style="color: #888; margin-bottom: 5px;">MLB</h3>
            <p style="color: #666; font-size: 12px;">Coming March 2026</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Logout
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🚪 Logout", use_container_width=True):
            cookie_manager.delete("authenticated")
            st.session_state.authenticated = False
            st.session_state.user_type = None
            st.rerun()
    
    st.markdown("""
    <div style="text-align: center; padding: 20px;">
        <p style="color: #666; font-size: 12px;">
            © 2026 BigSnapshot | Educational tool only. Not financial advice.
        </p>
    </div>
    """, unsafe_allow_html=True)
