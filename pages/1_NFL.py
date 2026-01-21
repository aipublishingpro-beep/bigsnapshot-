import streamlit as st
import requests
from datetime import datetime, timedelta
import pytz
import json
import os
import time
import uuid
from styles import apply_styles
import extra_streamlit_components as stx

try:
    from streamlit_autorefresh import st_autorefresh
    HAS_AUTOREFRESH = True
except ImportError:
    HAS_AUTOREFRESH = False

st.set_page_config(page_title="NFL Edge Finder", page_icon="🏈", layout="wide")

apply_styles()

# ============================================================
# COOKIE MANAGER FOR PERSISTENT LOGIN
# ============================================================
cookie_manager = stx.CookieManager()

# ============================================================
# SESSION STATE FOR AUTH
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
# AUTH CHECK
# ============================================================
if not st.session_state.authenticated:
    st.warning("⚠️ Please log in from the Home page first.")
    st.page_link("Home.py", label="🏠 Go to Home", use_container_width=True)
    st.stop()

# ============================================================
# GA4 TRACKING
# ============================================================
st.markdown("""
<script async src="https://www.googletagmanager.com/gtag/js?id=G-NQKY5VQ376"></script>
<script>window.dataLayer = window.dataLayer || [];function gtag(){dataLayer.push(arguments);}gtag('js', new Date());gtag('config', 'G-NQKY5VQ376');</script>
""", unsafe_allow_html=True)

# ============================================================
# MOBILE CSS
# ============================================================
st.markdown("""
<style>
@media (max-width: 768px) {
    .stColumns > div {
        flex: 1 1 100% !important;
        min-width: 100% !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.2rem !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.8rem !important;
    }
    h1 { font-size: 1.5rem !important; }
    h2 { font-size: 1.2rem !important; }
    h3 { font-size: 1rem !important; }
    button {
        padding: 8px 12px !important;
        font-size: 0.85em !important;
    }
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# REST OF YOUR EXISTING CODE STARTS HERE
# ============================================================
if "sid" not in st.session_state:
    st.session_state["sid"] = str(uuid.uuid4())
if "last_ball_positions" not in st.session_state:
    st.session_state.last_ball_positions = {}

eastern = pytz.timezone("US/Eastern")
today_str = datetime.now(eastern).strftime("%Y-%m-%d")

# ... REST OF YOUR FILE CONTINUES UNCHANGED ...
