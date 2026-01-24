import streamlit as st

st.set_page_config(page_title="BigSnapshot", page_icon="🎯", layout="wide")

# ============================================================
# GA4 ANALYTICS - SERVER SIDE
# ============================================================
import uuid
import requests as req_ga
import time  # ← added for cookie retry

def send_ga4_event(page_title, page_path):
    try:
        url = f"https://www.google-analytics.com/mp/collect?measurement_id=G-NQKY5VQ376&api_secret=n4oBJjH7RXi3dA7aQo2CZA"
        payload = {"client_id": str(uuid.uuid4()), "events": [{"name": "page_view", "params": {"page_title": page_title, "page_location": f"https://bigsnapshot.streamlit.app{page_path}"}}]}
        req_ga.post(url, json=payload, timeout=2)
    except: pass

send_ga4_event("BigSnapshot Home", "/")

# ============================================================
# COOKIE AUTH - IMPROVED READ & SET
# ============================================================
import extra_streamlit_components as stx
from datetime import datetime, timedelta

cookie_manager = stx.CookieManager(key="bigsnapshot_auth_manager")

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.user_type = None

# ────────────────────────────────────────────────
# IMPROVED COOKIE READ: retry to handle JS init delay
# ────────────────────────────────────────────────
saved_auth = None
for attempt in range(5):  # try up to 5 times (~1.2s total max)
    saved_auth = cookie_manager.get("authenticated")
    if saved_auth is not None:
        break
    time.sleep(0.25)

# Debug (uncomment if still having refresh logout issues)
# st.write("DEBUG - cookie value read:", saved_auth)
# st.write("DEBUG - session authenticated before set:", st.session_state.authenticated)

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
    <div style
