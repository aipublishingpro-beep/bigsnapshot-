import streamlit as st

st.set_page_config(page_title="BigSnapshot", page_icon="🎯", layout="wide")

# ============================================================
# GA4 ANALYTICS - SERVER SIDE
# ============================================================
import uuid
import requests as req_ga
import time

def send_ga4_event(page_title, page_path):
    try:
        url = "https://www.google-analytics.com/mp/collect?measurement_id=G-NQKY5VQ376&api_secret=n4oBJjH7RXi3dA7aQo2CZA"
        payload = {
            "client_id": str(uuid.uuid4()),
            "events": [{
                "name": "page_view",
                "params": {
                    "page_title": page_title,
                    "page_location": f"https://bigsnapshot.streamlit.app{page_path}"
                }
            }]
        }
        req_ga.post(url, json=payload, timeout=2)
    except:
        pass

send_ga4_event("BigSnapshot Home", "/")

# ============================================================
# COOKIE AUTH
# ============================================================
import extra_streamlit_components as stx
from datetime import datetime, timedelta

cookie_manager = stx.CookieManager(key="bigsnapshot_auth_manager")

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.user_type = None

saved_auth = None
for _ in range(5):
    saved_auth = cookie_manager.get("authenticated")
    if saved_auth is not None:
        break
    time.sleep(0.25)

if saved_auth == "true":
    st.session_state.authenticated = True
    st.session_state.user_type = "Paid Subscriber"

# ============================================================
# CONFIG
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
    h1 { font-size: 1.5rem !important; }
    h2 { font-size: 1.2rem !important; }
    h3 { font-size: 1rem !important; }
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# LANDING PAGE (NOT LOGGED IN)
# ============================================================
if not st.session_state.authenticated:

    # HERO
    st.markdown("""
    <div style="text-align:center;padding:60px 20px 30px 20px">
        <div style="font-size:70px;margin-bottom:15px">🎯</div>
        <h1 style="font-size:52px;font-weight:800;color:#fff;margin-bottom:10px">BigSnapshot</h1>
        <p style="color:#888;font-size:20px;margin-bottom:10px">Prediction Market Edge Finder</p>
        <p style="color:#555;font-size:14px">Structural analysis for Kalshi markets</p>
    </div>
    """, unsafe_allow_html=True)

    # VALUE PROP (FIXED — THIS WAS BROKEN)
    st.markdown("""
    <div style="max-width:900px;margin:0 auto;text-align:center;padding:20px">
        <h2 style="color:#fff;margin-bottom:10px">Find real edge in prediction markets</h2>
        <p style="color:#888;font-size:16px">
            BigSnapshot analyzes pricing behavior, market structure, and live game dynamics
            across Kalshi markets. No hype. No pick spam. Just probability and execution.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.stop()
