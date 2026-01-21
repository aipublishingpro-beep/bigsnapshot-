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
# SESSION STATE
# ============================================================
if "sid" not in st.session_state:
    st.session_state["sid"] = str(uuid.uuid4())
if "last_ball_positions" not in st.session_state:
    st.session_state.last_ball_positions = {}

eastern = pytz.timezone("US/Eastern")
today_str = datetime.now(eastern).strftime("%Y-%m-%d")

POSITIONS_FILE = "nfl_positions.json"
PERFORMANCE_FILE = "nfl_performance.json"

def load_positions():
    try:
        if os.path.exists(POSITIONS_FILE):
            with open(POSITIONS_FILE, 'r') as f:
                return json.load(f)
    except:
        pass
    return []

def save_positions(positions):
    try:
        with open(POSITIONS_FILE, 'w') as f:
            json.dump(positions, f, indent=2)
    except:
        pass

def load_performance():
    try:
        if os.path.exists(PERFORMANCE_FILE):
            with open(PERFORMANCE_FILE, 'r') as f:
                return json.load(f)
    except:
        pass
    return {"strong": {"wins": 12, "losses": 3}, "buy": {"wins": 18, "losses": 9}, "lean": {"wins": 14, "losses": 12}, "total_profit": 127.50}

def save_performance(perf):
    try:
        with open(PERFORMANCE_FILE, 'w') as f:
            json.dump(perf, f, indent=2)
    except:
        pass

if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = False
if "positions" not in st.session_state:
    st.session_state.positions = load_positions()
if "selected_ml_pick" not in st.session_state:
    st.session_state.selected_ml_pick = None
if "editing_position" not in st.session_state:
    st.session_state.editing_position = None
if "performance" not in st.session_state:
    st.session_state.performance = load_performance()

if st.session_state.auto_refresh and HAS_AUTOREFRESH:
    st_autorefresh(interval=5000, limit=None, key="nfl_autorefresh")
    auto_status = "🔄 Auto-refresh ON (5s)"
elif st.session_state.auto_refresh and not HAS_AUTOREFRESH:
    st.markdown(f'<meta http-equiv="refresh" content="5;url=?r={int(time.time()) + 5}">', unsafe_allow_html=True)
    auto_status = "🔄 Auto-refresh ON (5s)"
else:
    auto_status = "⏸️ Auto-refresh OFF"

KALSHI_CODES = {
    "Arizona": "ARI", "Atlanta": "ATL", "Baltimore": "BAL", "Buffalo": "BUF",
    "Carolina": "CAR", "Chicago": "CHI", "Cincinnati": "CIN", "Cleveland": "CLE",
    "Dallas": "DAL", "Denver": "DEN", "Detroit": "DET", "Green Bay": "GB",
    "Houston": "HOU", "Indianapolis": "IND", "Jacksonville": "JAX", "Kansas City": "KC",
    "Las Vegas": "LV", "LA Chargers": "LAC", "LA Rams": "LA", "Miami": "MIA",
    "Minnesota": "MIN", "New England": "NE", "New Orleans": "NO", "NY Giants": "NYG",
    "NY Jets": "NYJ", "Philadelphia": "PHI", "Pittsburgh": "PIT", "San Francisco": "SF",
    "Seattle": "SEA", "Tampa Bay": "TB", "Tennessee": "TEN", "Washington": "WAS"
}

TEAM_ABBREVS = {
    "Arizona Cardinals": "Arizona", "Atlanta Falcons": "Atlanta", "Baltimore Ravens": "Baltimore",
    "Buffalo Bills": "Buffalo", "Carolina Panthers": "Carolina", "Chicago Bears": "Chicago",
    "Cincinnati Bengals": "Cincinnati", "Cleveland Browns": "Cleveland", "Dallas Cowboys": "Dallas",
    "Denver Broncos": "Denver", "Detroit Lions": "Detroit", "Green Bay Packers": "Green Bay",
    "Houston Texans": "Houston", "Indianapolis Colts": "Indianapolis", "Jacksonville Jaguars": "Jacksonville",
    "Kansas City Chiefs": "Kansas City", "Las Vegas Raiders": "Las Vegas", "Los Angeles Chargers": "LA Chargers",
    "Los Angeles Rams": "LA Rams", "Miami Dolphins": "Miami", "Minnesota Vikings": "Minnesota",
    "New England Patriots": "New England", "New Orleans Saints": "New Orleans", "New York Giants": "NY Giants",
    "New York Jets": "NY Jets", "Philadelphia Eagles": "Philadelphia", "Pittsburgh Steelers": "Pittsburgh",
    "San Francisco 49ers": "San Francisco", "Seattle Seahawks": "Seattle", "Tampa Bay Buccaneers": "Tampa Bay",
    "Tennessee Titans": "Tennessee", "Washington Commanders": "Washington"
}

DIVISIONS = {
    "AFC East": ["Buffalo", "Miami", "NY Jets", "New England"],
    "AFC North": ["Baltimore", "Pittsburgh", "Cleveland", "Cincinnati"],
    "AFC South": ["Houston", "Indianapolis", "Jacksonville", "Tennessee"],
    "AFC West": ["Kansas City", "LA Chargers", "Denver", "Las Vegas"],
    "NFC East": ["Philadelphia", "Dallas", "Washington", "NY Giants"],
    "NFC North": ["Detroit", "Green Bay", "Minnesota", "Chicago"],
    "NFC South": ["Atlanta", "Tampa Bay", "New Orleans", "Carolina"],
    "NFC West": ["Seattle", "LA Rams", "San Francisco", "Arizona"]
}

STADIUM_COORDS = {
    "Arizona": (33.5277, -112.2626), "Atlanta": (33.7553, -84.4006), "Baltimore": (39.2780, -76.6227),
    "Buffalo": (42.7738, -78.7870), "Carolina": (35.2258, -80.8528), "Chicago": (41.8623, -87.6167),
    "Cincinnati": (39.0955, -84.5161), "Cleveland": (41.5061, -81.6995), "Dallas": (32.7473, -97.0945),
    "Denver": (39.7439, -105.0201), "Detroit": (42.3400, -83.0456), "Green Bay": (44.5013, -88.0622),
    "Houston": (29.6847, -95.4107), "Indianapolis": (39.7601, -86.1639), "Jacksonville": (30.3239, -81.6373),
    "Kansas City": (39.0489, -94.4839), "Las Vegas": (36.0909, -115.1833), "LA Chargers": (33.9535, -118.3392),
    "LA Rams": (33.9535, -118.3392), "Miami": (25.9580, -80.2389), "Minnesota": (44.9737, -93.2577),
    "New England": (42.0909, -71.2643), "New Orleans": (29.9511, -90.0812), "NY Giants": (40.8128, -74.0742),
    "NY Jets": (40.8128, -74.0742), "Philadelphia": (39.9008, -75.1675), "Pittsburgh": (40.4468, -80.0158),
    "San Francisco": (37.4032, -121.9698), "Seattle": (47.5952, -122.3316), "Tampa Bay": (27.9759, -82.5033),
    "Tennessee": (36.1665, -86.7713), "Washington": (38.9076, -76.8645)
}

DOME_STADIUMS = ["Arizona", "Atlanta", "Dallas", "Detroit", "Houston", "Indianapolis", 
                  "Las Vegas", "LA Chargers", "LA Rams", "Minnesota", "New Orleans"]

_PH = ["Buffalo", "Cincinnati", "Miami", "Tampa Bay", "LA Chargers", "Detroit", "Philadelphia"]
_RH = ["Baltimore", "San Francisco", "Cleveland", "Tennessee", "Denver"]

_TS = {
    "Arizona": {"d": -12.5, "r": 27, "h": 0.42, "a": 0.30},
    "Atlanta": {"d": 2.5, "r": 18, "h": 0.55, "a": 0.42},
    "Baltimore": {"d": 15.5, "r": 6, "h": 0.72, "a": 0.62},
    "Buffalo": {"d": 18.2, "r": 5, "h": 0.78, "a": 0.68},
    "Carolina": {"d": -18.5, "r": 30, "h": 0.35, "a": 0.22},
    "Chicago": {"d": -8.5, "r": 22, "h": 0.45, "a": 0.35},
    "Cincinnati": {"d": 5.8, "r": 14, "h": 0.58, "a": 0.48},
    "Cleveland": {"d": -25.0, "r": 32, "h": 0.38, "a": 0.25},
    "Dallas": {"d": -5.2, "r": 20, "h": 0.52, "a": 0.38},
    "Denver": {"d": 8.5, "r": 8, "h": 0.65, "a": 0.50},
    "Detroit": {"d": 22.5, "r": 4, "h": 0.78, "a": 0.68},
    "Green Bay": {"d": 12.2, "r": 10, "h": 0.70, "a": 0.55},
    "Houston": {"d": 16.5, "r": 7, "h": 0.68, "a": 0.58},
    "Indianapolis": {"d": 14.5, "r": 12, "h": 0.55, "a": 0.48},
    "Jacksonville": {"d": 10.5, "r": 11, "h": 0.55, "a": 0.48},
    "Kansas City": {"d": 18.5, "r": 9, "h": 0.82, "a": 0.72},
    "Las Vegas": {"d": -10.2, "r": 25, "h": 0.42, "a": 0.28},
    "LA Chargers": {"d": 11.8, "r": 3, "h": 0.62, "a": 0.52},
    "LA Rams": {"d": 24.5, "r": 5, "h": 0.72, "a": 0.62},
    "Miami": {"d": -2.5, "r": 16, "h": 0.55, "a": 0.38},
    "Minnesota": {"d": 8.5, "r": 13, "h": 0.68, "a": 0.52},
    "New England": {"d": -12.5, "r": 24, "h": 0.42, "a": 0.30},
    "New Orleans": {"d": -8.8, "r": 23, "h": 0.48, "a": 0.35},
    "NY Giants": {"d": -15.5, "r": 29, "h": 0.35, "a": 0.22},
    "NY Jets": {"d": -12.5, "r": 26, "h": 0.42, "a": 0.28},
    "Philadelphia": {"d": 14.8, "r": 6, "h": 0.75, "a": 0.60},
    "Pittsburgh": {"d": 4.8, "r": 10, "h": 0.62, "a": 0.45},
    "San Francisco": {"d": 6.5, "r": 15, "h": 0.58, "a": 0.48},
    "Seattle": {"d": 28.5, "r": 2, "h": 0.78, "a": 0.68},
    "Tampa Bay": {"d": -3.2, "r": 19, "h": 0.52, "a": 0.40},
    "Tennessee": {"d": -14.8, "r": 28, "h": 0.40, "a": 0.25},
    "Washington": {"d": -4.5, "r": 21, "h": 0.52, "a": 0.42}
}

_SP = {
    "Arizona": ["Kyler Murray"], "Atlanta": ["Kirk Cousins", "Bijan Robinson"],
    "Baltimore": ["Lamar Jackson", "Derrick Henry"], "Buffalo": ["Josh Allen", "James Cook"],
    "Carolina": ["Bryce Young"], "Chicago": ["Caleb Williams"],
    "Cincinnati": ["Joe Burrow", "Ja'Marr Chase"], "Cleveland": ["Deshaun Watson"],
    "Dallas": ["Dak Prescott", "CeeDee Lamb"], "Denver": ["Bo Nix"],
    "Detroit": ["Jared Goff", "Amon-Ra St. Brown"], "Green Bay": ["Jordan Love"],
    "Houston": ["C.J. Stroud", "Nico Collins"], "Indianapolis": ["Anthony Richardson"],
    "Jacksonville": ["Trevor Lawrence"], "Kansas City": ["Patrick Mahomes", "Travis Kelce"],
    "Las Vegas": ["Gardner Minshew"], "LA Chargers": ["Justin Herbert"],
    "LA Rams": ["Matthew Stafford", "Puka Nacua"], "Miami": ["Tua Tagovailoa", "Tyreek Hill"],
    "Minnesota": ["J.J. McCarthy", "Justin Jefferson"], "New England": ["Drake Maye"],
    "New Orleans": ["Derek Carr"], "NY Giants": ["Daniel Jones"],
    "NY Jets": ["Aaron Rodgers"], "Philadelphia": ["Jalen Hurts", "Saquon Barkley"],
    "Pittsburgh": ["Russell Wilson"], "San Francisco": ["Brock Purdy", "Christian McCaffrey"],
    "Seattle": ["Geno Smith", "DK Metcalf"], "Tampa Bay": ["Baker Mayfield"],
    "Tennessee": ["Will Levis"], "Washington": ["Jayden Daniels"]
}

def buy_button(url, text="BUY"):
    return f'''<a href="{url}" target="_blank" style="
        display: block;
        background: linear-gradient(135deg, #00c853, #00a844);
        color: white;
        padding: 12px 24px;
        border-radius: 8px;
        text-decoration: none;
        font-weight: 600;
        text-align: center;
        margin: 5px 0;
    ">{text}</a>'''

def build_kalshi_ml_url(away_team, home_team, game_date=None):
    away_code = KALSHI_CODES.get(away_team, "XXX")
    home_code = KALSHI_CODES.get(home_team, "XXX")
    if game_date:
        date_str = game_date.strftime("%y%b%d").upper()
    else:
        date_str = datetime.now(eastern).strftime("%y%b%d").upper()
    ticker = f"KXNFLGAME-{date_str}{away_code}{home_code}"
    return f"https://kalshi.com/markets/KXNFLGAME/{ticker}"

@st.cache_data(ttl=1800)
def fetch_weather(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,wind_speed_10m,precipitation,weather_code&wind_speed_unit=mph&temperature_unit=fahrenheit"
        resp = requests.get(url, timeout=5)
        data = resp.json()
        current = data.get("current", {})
        return {"temp": current.get("temperature_2m", 70), "wind": current.get("wind_speed_10m", 0), "precip": current.get("precipitation", 0), "code": current.get("weather_code", 0)}
    except:
        return {"temp": 70, "wind": 0, "precip": 0, "code": 0}

def get_weather_for_game(home_team):
    if home_team in DOME_STADIUMS:
        return {"wind": 0, "precip": 0, "temp": 72, "dome": True, "impact": "none"}
    coords = STADIUM_COORDS.get(home_team)
    if not coords:
        return {"wind": 0, "precip": 0, "temp": 70, "dome": False, "impact": "none"}
    weather = fetch_weather(coords[0], coords[1])
    wind, precip, temp = weather.get("wind", 0), weather.get("precip", 0), weather.get("temp", 70)
    if wind >= 20 or precip > 0.5: impact = "severe"
    elif wind >= 15 or precip > 0.1: impact = "moderate"
    elif wind >= 10: impact = "light"
    else: impact = "none"
    return {"wind": wind, "precip": precip, "temp": temp, "dome": False, "impact": impact}
