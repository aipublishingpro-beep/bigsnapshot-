import streamlit as st
import requests
from datetime import datetime, timedelta
import pytz
import json
import os
import base64
import time
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

st.set_page_config(page_title="NBA Edge Finder", page_icon="🎯", layout="wide")

# ========== DAILY DATE KEY ==========
today_str = datetime.now(pytz.timezone("US/Eastern")).strftime("%Y-%m-%d")

# ========== GOOGLE ANALYTICS ==========
st.markdown("""
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-NQKY5VQ376"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-NQKY5VQ376');
</script>
""", unsafe_allow_html=True)

# Fixed CSS
st.markdown("""
<style>
div[role="radiogroup"] label { cursor: pointer; }
div[role="radiogroup"] label span {
    padding: 8px 18px;
    border-radius: 10px;
    display: inline-block;
    font-weight: 700;
}
div[role="radiogroup"] input:checked + div span { box-shadow: inset 0 0 0 2px white; }
div[role="radiogroup"] label:nth-of-type(1) span {
    background: linear-gradient(135deg, #102a1a, #163a26);
    border: 2px solid #00ff88;
    color: #ccffee;
}
div[role="radiogroup"] label:nth-of-type(2) span {
    background: linear-gradient(135deg, #2a1515, #3a1a1a);
    border: 2px solid #ff4444;
    color: #ffcccc;
}
.stLinkButton > a {
    background-color: #00aa00 !important;
    border-color: #00aa00 !important;
    color: white !important;
}
.stLinkButton > a:hover {
    background-color: #00cc00 !important;
    border-color: #00cc00 !important;
}
</style>
""", unsafe_allow_html=True)

# ========== ENCRYPTION FUNCTIONS ==========
SALT = b'nba_edge_finder_2025'

def get_encryption_key(password: str) -> bytes:
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=SALT, iterations=100000)
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))

def encrypt_api_key(api_key: str, password: str) -> str:
    key = get_encryption_key(password)
    f = Fernet(key)
    return f.encrypt(api_key.encode()).decode()

def decrypt_api_key(encrypted_key: str, password: str) -> str:
    try:
        key = get_encryption_key(password)
        f = Fernet(key)
        return f.decrypt(encrypted_key.encode()).decode()
    except:
        return None

# ========== PERSISTENT STORAGE ==========
POSITIONS_FILE = "nba_positions.json"

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

# ========== SESSION STATE INIT ==========
st.session_state.setdefault("totals_side_radio", "NO (Under)")
st.session_state.setdefault("ml_pick_radio", None)
if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = False
if "positions" not in st.session_state:
    st.session_state.positions = load_positions()
if "selected_side" not in st.session_state:
    st.session_state.selected_side = "NO"
if "selected_threshold" not in st.session_state:
    st.session_state.selected_threshold = 225.5
if "selected_ml_pick" not in st.session_state:
    st.session_state.selected_ml_pick = None
if "editing_position" not in st.session_state:
    st.session_state.editing_position = None

# ========== LIVE SIGNAL FEED SESSION STATE ==========
if "drought_tracker" not in st.session_state:
    st.session_state.drought_tracker = {}  # {game_key: {"last_total": int, "last_change_time": datetime}}
if "pace_history" not in st.session_state:
    st.session_state.pace_history = {}  # {game_key: [{"time": datetime, "total": int, "mins": float}]}

# ========== DATE INVALIDATION ==========
if "snapshot_date" not in st.session_state or st.session_state["snapshot_date"] != today_str:
    st.session_state["snapshot_date"] = today_str
    st.session_state.pop("big_snapshot", None)
    st.session_state.drought_tracker = {}
    st.session_state.pace_history = {}

if st.session_state.auto_refresh:
    cache_buster = int(time.time()) + 30
    st.markdown(f'<meta http-equiv="refresh" content="30;url=?r={cache_buster}">', unsafe_allow_html=True)
    auto_status = "🔄 Auto-refresh ON (30s)"
else:
    auto_status = "⏸️ Auto-refresh OFF"

# ========== KALSHI TEAM CODES ==========
KALSHI_CODES = {
    "Atlanta": "atl", "Boston": "bos", "Brooklyn": "bkn", "Charlotte": "cha",
    "Chicago": "chi", "Cleveland": "cle", "Dallas": "dal", "Denver": "den",
    "Detroit": "det", "Golden State": "gsw", "Houston": "hou", "Indiana": "ind",
    "LA Clippers": "lac", "LA Lakers": "lal", "Memphis": "mem", "Miami": "mia",
    "Milwaukee": "mil", "Minnesota": "min", "New Orleans": "nop", "New York": "nyk",
    "Oklahoma City": "okc", "Orlando": "orl", "Philadelphia": "phi", "Phoenix": "phx",
    "Portland": "por", "Sacramento": "sac", "San Antonio": "sas", "Toronto": "tor",
    "Utah": "uta", "Washington": "was"
}

def build_kalshi_totals_url(away_team, home_team):
    away_code = KALSHI_CODES.get(away_team, "xxx").upper()
    home_code = KALSHI_CODES.get(home_team, "xxx").upper()
    today = datetime.now(pytz.timezone('US/Eastern'))
    date_str = today.strftime("%y%b%d").upper()
    ticker = f"KXNBATOTAL-{date_str}{away_code}{home_code}"
    return f"https://kalshi.com/markets/KXNBATOTAL/{ticker}"

def build_kalshi_ml_url(away_team, home_team):
    away_code = KALSHI_CODES.get(away_team, "xxx").upper()
    home_code = KALSHI_CODES.get(home_team, "xxx").upper()
    today = datetime.now(pytz.timezone('US/Eastern'))
    date_str = today.strftime("%y%b%d").upper()
    ticker = f"KXNBAGAME-{date_str}{away_code}{home_code}"
    return f"https://kalshi.com/markets/KXNBAGAME/{ticker}"

# ========== STAR PLAYERS DATABASE ==========
STAR_PLAYERS_DB = {
    "Atlanta": {"Trae Young": (3, "O"), "Dejounte Murray": (2, "B"), "Jalen Johnson": (2, "B")},
    "Boston": {"Jayson Tatum": (3, "B"), "Jaylen Brown": (3, "O"), "Derrick White": (2, "D"), "Kristaps Porzingis": (2, "B")},
    "Brooklyn": {"Mikal Bridges": (2, "B"), "Cam Thomas": (2, "O"), "Ben Simmons": (1, "D")},
    "Charlotte": {"LaMelo Ball": (3, "O"), "Brandon Miller": (2, "O"), "Miles Bridges": (2, "B")},
    "Chicago": {"Zach LaVine": (2, "O"), "DeMar DeRozan": (2, "O"), "Coby White": (2, "O")},
    "Cleveland": {"Donovan Mitchell": (3, "O"), "Darius Garland": (2, "O"), "Evan Mobley": (2, "D"), "Jarrett Allen": (2, "D")},
    "Dallas": {"Luka Doncic": (3, "O"), "Kyrie Irving": (3, "O"), "PJ Washington": (2, "D"), "Dereck Lively II": (2, "D")},
    "Denver": {"Nikola Jokic": (3, "B"), "Jamal Murray": (3, "O"), "Aaron Gordon": (2, "D"), "Michael Porter Jr.": (2, "O")},
    "Detroit": {"Cade Cunningham": (2, "O"), "Jaden Ivey": (2, "O"), "Jalen Duren": (1, "D")},
    "Golden State": {"Stephen Curry": (3, "O"), "Draymond Green": (2, "D"), "Andrew Wiggins": (2, "B"), "Klay Thompson": (2, "O")},
    "Houston": {"Jalen Green": (2, "O"), "Alperen Sengun": (2, "B"), "Fred VanVleet": (2, "O"), "Jabari Smith Jr.": (2, "D")},
    "Indiana": {"Tyrese Haliburton": (3, "O"), "Pascal Siakam": (2, "B"), "Myles Turner": (2, "D"), "Bennedict Mathurin": (2, "O")},
    "LA Clippers": {"Kawhi Leonard": (3, "B"), "Paul George": (3, "B"), "James Harden": (3, "O"), "Norman Powell": (2, "O")},
    "LA Lakers": {"LeBron James": (3, "B"), "Anthony Davis": (3, "B"), "Austin Reaves": (2, "O"), "D'Angelo Russell": (2, "O")},
    "Memphis": {"Ja Morant": (3, "O"), "Desmond Bane": (2, "O"), "Jaren Jackson Jr.": (2, "D"), "Marcus Smart": (2, "D")},
    "Miami": {"Jimmy Butler": (3, "B"), "Bam Adebayo": (3, "D"), "Tyler Herro": (2, "O"), "Terry Rozier": (2, "O")},
    "Milwaukee": {"Giannis Antetokounmpo": (3, "B"), "Damian Lillard": (3, "O"), "Khris Middleton": (2, "O"), "Brook Lopez": (2, "D")},
    "Minnesota": {"Anthony Edwards": (3, "O"), "Karl-Anthony Towns": (2, "O"), "Rudy Gobert": (3, "D"), "Jaden McDaniels": (2, "D")},
    "New Orleans": {"Zion Williamson": (3, "O"), "Brandon Ingram": (2, "O"), "CJ McCollum": (2, "O"), "Herb Jones": (2, "D")},
    "New York": {"Jalen Brunson": (3, "O"), "Julius Randle": (2, "B"), "RJ Barrett": (2, "O"), "Mitchell Robinson": (2, "D")},
    "Oklahoma City": {"Shai Gilgeous-Alexander": (3, "O"), "Chet Holmgren": (3, "D"), "Jalen Williams": (2, "B"), "Lu Dort": (2, "D")},
    "Orlando": {"Paolo Banchero": (3, "O"), "Franz Wagner": (2, "B"), "Wendell Carter Jr.": (2, "D"), "Jalen Suggs": (2, "D")},
    "Philadelphia": {"Joel Embiid": (3, "B"), "Tyrese Maxey": (2, "O"), "Tobias Harris": (2, "O")},
    "Phoenix": {"Kevin Durant": (3, "O"), "Devin Booker": (3, "O"), "Bradley Beal": (2, "O"), "Jusuf Nurkic": (2, "D")},
    "Portland": {"Anfernee Simons": (2, "O"), "Scoot Henderson": (2, "O"), "Jerami Grant": (2, "B")},
    "Sacramento": {"De'Aaron Fox": (3, "O"), "Domantas Sabonis": (3, "B"), "Keegan Murray": (2, "O"), "Malik Monk": (2, "O")},
    "San Antonio": {"Victor Wembanyama": (3, "B"), "Devin Vassell": (2, "O"), "Keldon Johnson": (2, "O")},
    "Toronto": {"Scottie Barnes": (2, "B"), "Pascal Siakam": (2, "B"), "RJ Barrett": (2, "O")},
    "Utah": {"Lauri Markkanen": (2, "O"), "Jordan Clarkson": (2, "O"), "Walker Kessler": (2, "D")},
    "Washington": {"Jordan Poole": (2, "O"), "Kyle Kuzma": (2, "O"), "Bilal Coulibaly": (1, "D")}
}

# ========== SIDEBAR ==========
with st.sidebar:
    st.header("🔗 KALSHI")
    st.caption("⚠️ NBA not on trade API yet")
    st.caption("Track here → Execute on web")
    st.divider()
    
    st.header("📖 ML LEGEND")
    st.markdown("🟢 **STRONG BUY** → 8.0+\n\n🔵 **BUY** → 6.5-7.9\n\n🟡 **LEAN** → 5.5-6.4\n\n⚪ **TOSS-UP** → 4.5-5.4")
    st.divider()
    
    st.header("🎯 10 ML FACTORS")
    st.markdown("""
| # | Factor | Max Pts |
|---|--------|---------|
| 1 | 🛏️ **Opp B2B** | +1.0 |
| 2 | 📊 **Net Rating** | +1.0 |
| 3 | 🛡️ **Top 5 DEF** | +1.0 |
| 4 | 🏠 **Home Court** | +1.0 |
| 5 | 🏥 **Star OUT** | +2.0 |
| 6 | ✈️ **Travel 2K+mi** | +1.0 |
| 7 | 📈 **Home Win %** | +0.8 |
| 8 | 🏔️ **Altitude** | +1.0 |
| 9 | 🔥 **Hot Streak** | +1.0 |
| 10 | 🆚 **H2H Edge** | +0.5 |
""")
    st.divider()
    
    st.header("🎯 CUSHION SCORING")
    st.markdown("""
**For NO (Under) bets:**

| Factor | Points |
|--------|--------|
| +20 cushion | +3 |
| +10-19 cushion | +2 |
| +6-9 cushion | +1 |
| SLOW pace | ✅ |
| AVG pace | ⚠️ |
| FAST pace | ❌ |

**For YES (Over) bets:**

| Factor | Points |
|--------|--------|
| +20 cushion | +3 |
| +10-19 cushion | +2 |
| +6-9 cushion | +1 |
| FAST pace | ✅ |
| AVG pace | ⚠️ |
| SLOW pace | ❌ |
""")
    st.divider()
    
    st.header("📡 SIGNAL LEGEND")
    st.markdown("""
**Drought:**
- NORMAL: <60s
- MODERATE: 60-120s  
- HIGH: >120s

**Momentum:**
- COOLING: pace dropping
- NEUTRAL: stable
- HEATING: pace rising
""")
    st.divider()
    st.caption("v15.44 SIGNAL")

# ========== TEAM DATA ==========
TEAM_ABBREVS = {
    "Atlanta Hawks": "Atlanta", "Boston Celtics": "Boston", "Brooklyn Nets": "Brooklyn",
    "Charlotte Hornets": "Charlotte", "Chicago Bulls": "Chicago", "Cleveland Cavaliers": "Cleveland",
    "Dallas Mavericks": "Dallas", "Denver Nuggets": "Denver", "Detroit Pistons": "Detroit",
    "Golden State Warriors": "Golden State", "Houston Rockets": "Houston", "Indiana Pacers": "Indiana",
    "LA Clippers": "LA Clippers", "Los Angeles Clippers": "LA Clippers", "LA Lakers": "LA Lakers",
    "Los Angeles Lakers": "LA Lakers", "Memphis Grizzlies": "Memphis", "Miami Heat": "Miami",
    "Milwaukee Bucks": "Milwaukee", "Minnesota Timberwolves": "Minnesota", "New Orleans Pelicans": "New Orleans",
    "New York Knicks": "New York", "Oklahoma City Thunder": "Oklahoma City", "Orlando Magic": "Orlando",
    "Philadelphia 76ers": "Philadelphia", "Phoenix Suns": "Phoenix", "Portland Trail Blazers": "Portland",
    "Sacramento Kings": "Sacramento", "San Antonio Spurs": "San Antonio", "Toronto Raptors": "Toronto",
    "Utah Jazz": "Utah", "Washington Wizards": "Washington"
}

TEAM_STATS = {
    "Atlanta": {"pace": 100.5, "def_rank": 26, "net_rating": -3.2, "home_win_pct": 0.52, "away_win_pct": 0.35, "division": "Southeast"},
    "Boston": {"pace": 99.8, "def_rank": 2, "net_rating": 11.2, "home_win_pct": 0.78, "away_win_pct": 0.65, "division": "Atlantic"},
    "Brooklyn": {"pace": 98.2, "def_rank": 22, "net_rating": -4.5, "home_win_pct": 0.42, "away_win_pct": 0.28, "division": "Atlantic"},
    "Charlotte": {"pace": 99.5, "def_rank": 28, "net_rating": -6.8, "home_win_pct": 0.38, "away_win_pct": 0.22, "division": "Southeast"},
    "Chicago": {"pace": 98.8, "def_rank": 20, "net_rating": -2.1, "home_win_pct": 0.48, "away_win_pct": 0.32, "division": "Central"},
    "Cleveland": {"pace": 97.2, "def_rank": 3, "net_rating": 8.5, "home_win_pct": 0.75, "away_win_pct": 0.58, "division": "Central"},
    "Dallas": {"pace": 99.0, "def_rank": 12, "net_rating": 4.2, "home_win_pct": 0.62, "away_win_pct": 0.48, "division": "Southwest"},
    "Denver": {"pace": 98.5, "def_rank": 10, "net_rating": 5.8, "home_win_pct": 0.72, "away_win_pct": 0.45, "division": "Northwest"},
    "Detroit": {"pace": 97.8, "def_rank": 29, "net_rating": -8.2, "home_win_pct": 0.32, "away_win_pct": 0.18, "division": "Central"},
    "Golden State": {"pace": 100.2, "def_rank": 8, "net_rating": 3.5, "home_win_pct": 0.65, "away_win_pct": 0.42, "division": "Pacific"},
    "Houston": {"pace": 101.5, "def_rank": 18, "net_rating": 1.2, "home_win_pct": 0.55, "away_win_pct": 0.38, "division": "Southwest"},
    "Indiana": {"pace": 103.5, "def_rank": 24, "net_rating": 2.8, "home_win_pct": 0.58, "away_win_pct": 0.42, "division": "Central"},
    "LA Clippers": {"pace": 98.0, "def_rank": 14, "net_rating": 1.5, "home_win_pct": 0.55, "away_win_pct": 0.40, "division": "Pacific"},
    "LA Lakers": {"pace": 99.5, "def_rank": 15, "net_rating": 2.2, "home_win_pct": 0.58, "away_win_pct": 0.42, "division": "Pacific"},
    "Memphis": {"pace": 100.8, "def_rank": 6, "net_rating": 4.5, "home_win_pct": 0.68, "away_win_pct": 0.48, "division": "Southwest"},
    "Miami": {"pace": 97.5, "def_rank": 5, "net_rating": 3.8, "home_win_pct": 0.65, "away_win_pct": 0.45, "division": "Southeast"},
    "Milwaukee": {"pace": 99.2, "def_rank": 9, "net_rating": 5.2, "home_win_pct": 0.70, "away_win_pct": 0.52, "division": "Central"},
    "Minnesota": {"pace": 98.8, "def_rank": 4, "net_rating": 7.5, "home_win_pct": 0.72, "away_win_pct": 0.55, "division": "Northwest"},
    "New Orleans": {"pace": 100.0, "def_rank": 16, "net_rating": 1.8, "home_win_pct": 0.55, "away_win_pct": 0.38, "division": "Southwest"},
    "New York": {"pace": 98.5, "def_rank": 7, "net_rating": 6.2, "home_win_pct": 0.68, "away_win_pct": 0.52, "division": "Atlantic"},
    "Oklahoma City": {"pace": 99.8, "def_rank": 1, "net_rating": 12.5, "home_win_pct": 0.82, "away_win_pct": 0.68, "division": "Northwest"},
    "Orlando": {"pace": 97.0, "def_rank": 11, "net_rating": 3.2, "home_win_pct": 0.62, "away_win_pct": 0.45, "division": "Southeast"},
    "Philadelphia": {"pace": 98.2, "def_rank": 13, "net_rating": 2.5, "home_win_pct": 0.58, "away_win_pct": 0.42, "division": "Atlantic"},
    "Phoenix": {"pace": 99.0, "def_rank": 17, "net_rating": 2.0, "home_win_pct": 0.60, "away_win_pct": 0.42, "division": "Pacific"},
    "Portland": {"pace": 99.5, "def_rank": 27, "net_rating": -5.5, "home_win_pct": 0.40, "away_win_pct": 0.25, "division": "Northwest"},
    "Sacramento": {"pace": 101.2, "def_rank": 19, "net_rating": 0.8, "home_win_pct": 0.55, "away_win_pct": 0.38, "division": "Pacific"},
    "San Antonio": {"pace": 100.5, "def_rank": 25, "net_rating": -4.8, "home_win_pct": 0.42, "away_win_pct": 0.28, "division": "Southwest"},
    "Toronto": {"pace": 98.8, "def_rank": 21, "net_rating": -1.5, "home_win_pct": 0.48, "away_win_pct": 0.32, "division": "Atlantic"},
    "Utah": {"pace": 100.2, "def_rank": 30, "net_rating": -7.5, "home_win_pct": 0.35, "away_win_pct": 0.22, "division": "Northwest"},
    "Washington": {"pace": 101.0, "def_rank": 23, "net_rating": -6.2, "home_win_pct": 0.38, "away_win_pct": 0.25, "division": "Southeast"}
}

TEAM_LOCATIONS = {
    "Atlanta": (33.757, -84.396), "Boston": (42.366, -71.062), "Brooklyn": (40.683, -73.976),
    "Charlotte": (35.225, -80.839), "Chicago": (41.881, -87.674), "Cleveland": (41.496, -81.688),
    "Dallas": (32.790, -96.810), "Denver": (39.749, -105.010), "Detroit": (42.341, -83.055),
    "Golden State": (37.768, -122.388), "Houston": (29.751, -95.362), "Indiana": (39.764, -86.156),
    "LA Clippers": (34.043, -118.267), "LA Lakers": (34.043, -118.267), "Memphis": (35.138, -90.051),
    "Miami": (25.781, -80.188), "Milwaukee": (43.045, -87.917), "Minnesota": (44.979, -93.276),
    "New Orleans": (29.949, -90.082), "New York": (40.751, -73.994), "Oklahoma City": (35.463, -97.515),
    "Orlando": (28.539, -81.384), "Philadelphia": (39.901, -75.172), "Phoenix": (33.446, -112.071),
    "Portland": (45.532, -122.667), "Sacramento": (38.580, -121.500), "San Antonio": (29.427, -98.438),
    "Toronto": (43.643, -79.379), "Utah": (40.768, -111.901), "Washington": (38.898, -77.021)
}

STAR_PLAYERS = {
    "Atlanta": ["Trae Young"], "Boston": ["Jayson Tatum", "Jaylen Brown"], "Brooklyn": ["Mikal Bridges"],
    "Charlotte": ["LaMelo Ball"], "Chicago": ["Zach LaVine", "DeMar DeRozan"],
    "Cleveland": ["Donovan Mitchell", "Darius Garland", "Evan Mobley"],
    "Dallas": ["Luka Doncic", "Kyrie Irving"], "Denver": ["Nikola Jokic", "Jamal Murray"],
    "Detroit": ["Cade Cunningham"], "Golden State": ["Stephen Curry", "Draymond Green"],
    "Houston": ["Jalen Green", "Alperen Sengun"], "Indiana": ["Tyrese Haliburton", "Pascal Siakam"],
    "LA Clippers": ["Kawhi Leonard", "Paul George"], "LA Lakers": ["LeBron James", "Anthony Davis"],
    "Memphis": ["Ja Morant", "Desmond Bane"], "Miami": ["Jimmy Butler", "Bam Adebayo"],
    "Milwaukee": ["Giannis Antetokounmpo", "Damian Lillard"],
    "Minnesota": ["Anthony Edwards", "Karl-Anthony Towns", "Rudy Gobert"],
    "New Orleans": ["Zion Williamson", "Brandon Ingram"], "New York": ["Jalen Brunson", "Julius Randle"],
    "Oklahoma City": ["Shai Gilgeous-Alexander", "Chet Holmgren", "Jalen Williams"],
    "Orlando": ["Paolo Banchero", "Franz Wagner"], "Philadelphia": ["Joel Embiid", "Tyrese Maxey"],
    "Phoenix": ["Kevin Durant", "Devin Booker", "Bradley Beal"], "Portland": ["Anfernee Simons"],
    "Sacramento": ["De'Aaron Fox", "Domantas Sabonis"], "San Antonio": ["Victor Wembanyama"],
    "Toronto": ["Scottie Barnes"], "Utah": ["Lauri Markkanen"], "Washington": ["Jordan Poole"]
}

def calc_distance(loc1, loc2):
    from math import radians, sin, cos, sqrt, atan2
    lat1, lon1 = radians(loc1[0]), radians(loc1[1])
    lat2, lon2 = radians(loc2[0]), radians(loc2[1])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    return 3959 * 2 * atan2(sqrt(a), sqrt(1-a))

def fetch_espn_scores(date_key=None):
    eastern = pytz.timezone('US/Eastern')
    today_date = datetime.now(eastern).strftime('%Y%m%d')
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={today_date}"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        games = {}
        for event in data.get("events", []):
            comp = event.get("competitions", [{}])[0]
            competitors = comp.get("competitors", [])
            if len(competitors) < 2: continue
            home_team, away_team, home_score, away_score = None, None, 0, 0
            for c in competitors:
                name = c.get("team", {}).get("displayName", "")
                team_name = TEAM_ABBREVS.get(name, name)
                score = int(c.get("score", 0) or 0)
                if c.get("homeAway") == "home":
                    home_team, home_score = team_name, score
                else:
                    away_team, away_score = team_name, score
            status_obj = event.get("status", {})
            status_type = status_obj.get("type", {}).get("name", "STATUS_SCHEDULED")
            clock = status_obj.get("displayClock", "")
            period = status_obj.get("period", 0)
            game_key = f"{away_team}@{home_team}"
            games[game_key] = {
                "away_team": away_team, "home_team": home_team,
                "away_score": away_score, "home_score": home_score,
                "total": away_score + home_score,
                "period": period, "clock": clock, "status_type": status_type
            }
        return games
    except:
        return {}

def fetch_yesterday_teams():
    yesterday = (datetime.now(pytz.timezone('US/Eastern')) - timedelta(days=1)).strftime('%Y%m%d')
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={yesterday}"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        teams_played = set()
        for event in data.get("events", []):
            comp = event.get("competitions", [{}])[0]
            for c in comp.get("competitors", []):
                full_name = c.get("team", {}).get("displayName", "")
                team_name = TEAM_ABBREVS.get(full_name, full_name)
                teams_played.add(team_name)
        return teams_played
    except:
        return set()

def fetch_espn_injuries():
    injuries = {}
    try:
        url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/injuries"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        injury_list = data.get("injuries", [])
        for team_data in injury_list:
            team_name = team_data.get("displayName", "")
            team_key = TEAM_ABBREVS.get(team_name, team_name)
            if not team_key:
                continue
            injuries[team_key] = []
            player_list = team_data.get("injuries", [])
            for player in player_list:
                athlete = player.get("athlete", {})
                name = athlete.get("displayName", "")
                status = player.get("status", "")
                if name:
                    injuries[team_key].append({"name": name, "status": status})
    except Exception as e:
        st.sidebar.error(f"Injury fetch error: {e}")
    return injuries

def fetch_team_record(team_name):
    """Fetch team's last 5 games record from ESPN"""
    try:
        team_ids = {
            "Atlanta": "1", "Boston": "2", "Brooklyn": "17", "Charlotte": "30",
            "Chicago": "4", "Cleveland": "5", "Dallas": "6", "Denver": "7",
            "Detroit": "8", "Golden State": "9", "Houston": "10", "Indiana": "11",
            "LA Clippers": "12", "LA Lakers": "13", "Memphis": "29", "Miami": "14",
            "Milwaukee": "15", "Minnesota": "16", "New Orleans": "3", "New York": "18",
            "Oklahoma City": "25", "Orlando": "19", "Philadelphia": "20", "Phoenix": "21",
            "Portland": "22", "Sacramento": "23", "San Antonio": "24", "Toronto": "28",
            "Utah": "26", "Washington": "27"
        }
        team_id = team_ids.get(team_name, "1")
        url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team_id}"
        resp = requests.get(url, timeout=5)
        data = resp.json()
        record = data.get("team", {}).get("record", {}).get("items", [{}])[0]
        stats = record.get("stats", [])
        
        streak_val = 0
        for stat in stats:
            if stat.get("name") == "streak":
                streak_str = stat.get("displayValue", "W0")
                if streak_str.startswith("W"):
                    streak_val = int(streak_str[1:]) if len(streak_str) > 1 else 0
                elif streak_str.startswith("L"):
                    streak_val = -int(streak_str[1:]) if len(streak_str) > 1 else 0
        
        return {"streak": streak_val}
    except:
        return {"streak": 0}

H2H_EDGES = {
    ("Boston", "Philadelphia"): 0.5,
    ("Boston", "New York"): 0.5,
    ("Milwaukee", "Chicago"): 0.5,
    ("Cleveland", "Detroit"): 0.5,
    ("Oklahoma City", "Utah"): 0.5,
    ("Denver", "Minnesota"): 0.5,
    ("LA Lakers", "LA Clippers"): 0.3,
    ("Golden State", "Sacramento"): 0.5,
    ("Phoenix", "Portland"): 0.5,
    ("Miami", "Orlando"): 0.5,
    ("Dallas", "San Antonio"): 0.5,
    ("Memphis", "New Orleans"): 0.3,
}

def get_star_tier(player_name, team):
    team_stars = STAR_PLAYERS_DB.get(team, {})
    for star_name, (tier, player_type) in team_stars.items():
        if star_name.lower() in player_name.lower() or player_name.lower() in star_name.lower():
            return tier, player_type
    return 0, None

def format_star_rating(tier):
    if tier == 3: return "⭐⭐⭐"
    elif tier == 2: return "⭐⭐"
    elif tier == 1: return "⭐"
    return ""

def format_player_type(player_type):
    if player_type == "O": return "🔥"
    elif player_type == "D": return "🛡️"
    elif player_type == "B": return "⚔️"
    return ""

def get_injury_score(team, injuries):
    team_injuries = injuries.get(team, [])
    stars = STAR_PLAYERS.get(team, [])
    score = 0
    out_stars = []
    for inj in team_injuries:
        name = inj.get("name", "")
        status = inj.get("status", "").upper()
        is_star = any(star.lower() in name.lower() for star in stars)
        if "OUT" in status:
            score += 4.0 if is_star else 1.0
            if is_star: out_stars.append(name)
        elif "DAY-TO-DAY" in status or "GTD" in status or "QUESTIONABLE" in status:
            score += 2.5 if is_star else 0.5
    return score, out_stars

def get_detailed_injuries(team, injuries):
    team_injuries = injuries.get(team, [])
    detailed = []
    for inj in team_injuries:
        name = inj.get("name", "")
        status = inj.get("status", "").upper()
        tier, player_type = get_star_tier(name, team)
        stars = format_star_rating(tier)
        type_emoji = format_player_type(player_type)
        if "OUT" in status:
            simple_status = "OUT"
        elif "DAY-TO-DAY" in status or "DAY TO DAY" in status or "DTD" in status:
            simple_status = "DTD"
        elif "QUESTIONABLE" in status or "GTD" in status:
            simple_status = "GTD"
        else:
            simple_status = status[:10] if status else "UNK"
        detailed.append({"name": name, "status": simple_status, "tier": tier, "stars": stars, "type_emoji": type_emoji})
    detailed.sort(key=lambda x: x['tier'], reverse=True)
    return detailed

def get_minutes_played(period, clock, status_type):
    if status_type == "STATUS_FINAL": return 48 if period <= 4 else 48 + (period - 4) * 5
    if status_type == "STATUS_HALFTIME": return 24
    if period == 0: return 0
    try:
        clock_str = str(clock)
        if ':' in clock_str:
            parts = clock_str.split(':')
            mins = int(parts[0])
            secs = int(float(parts[1])) if len(parts) > 1 else 0
        else:
            mins, secs = 0, float(clock_str) if clock_str else 0
        time_left = mins + secs/60
        if period <= 4: return (period - 1) * 12 + (12 - time_left)
        else: return 48 + (period - 5) * 5 + (5 - time_left)
    except:
        return (period - 1) * 12 if period <= 4 else 48 + (period - 5) * 5

def calc_ml_score(home_team, away_team, yesterday_teams, injuries):
    home = TEAM_STATS.get(home_team, {})
    away = TEAM_STATS.get(away_team, {})
    home_loc = TEAM_LOCATIONS.get(home_team, (0, 0))
    away_loc = TEAM_LOCATIONS.get(away_team, (0, 0))
    score_home, score_away = 0, 0
    reasons_home, reasons_away = [], []
    
    home_b2b = home_team in yesterday_teams
    away_b2b = away_team in yesterday_teams
    if away_b2b and not home_b2b:
        score_home += 1.0
        reasons_home.append("🛏️ Opp B2B")
    elif home_b2b and not away_b2b:
        score_away += 1.0
        reasons_away.append("🛏️ Opp B2B")
    
    home_net = home.get('net_rating', 0)
    away_net = away.get('net_rating', 0)
    net_diff = home_net - away_net
    if net_diff > 5:
        score_home += 1.0
        reasons_home.append(f"📊 Net +{home_net:.1f}")
    elif net_diff < -5:
        score_away += 1.0
        reasons_away.append(f"📊 Net +{away_net:.1f}")
    
    home_def = home.get('def_rank', 15)
    away_def = away.get('def_rank', 15)
    if home_def <= 5:
        score_home += 1.0
        reasons_home.append(f"🛡️ #{home_def} DEF")
    if away_def <= 5:
        score_away += 1.0
        reasons_away.append(f"🛡️ #{away_def} DEF")
    
    score_home += 1.0
    
    home_inj, home_stars = get_injury_score(home_team, injuries)
    away_inj, away_stars = get_injury_score(away_team, injuries)
    inj_diff = away_inj - home_inj
    if inj_diff > 3:
        score_home += 2.0
        if away_stars: reasons_home.append(f"🏥 {away_stars[0][:10]} OUT")
    elif inj_diff < -3:
        score_away += 2.0
        if home_stars: reasons_away.append(f"🏥 {home_stars[0][:10]} OUT")
    
    travel_miles = calc_distance(away_loc, home_loc)
    if travel_miles > 2000:
        score_home += 1.0
        reasons_home.append(f"✈️ {int(travel_miles)}mi")
    
    home_hw = home.get('home_win_pct', 0.5)
    reasons_home.append(f"🏠 {int(home_hw*100)}%")
    if home_hw > 0.65: score_home += 0.8
    
    if home_team == "Denver":
        score_home += 1.0
        reasons_home.append("🏔️ Altitude")
    
    home_record = fetch_team_record(home_team)
    away_record = fetch_team_record(away_team)
    home_streak = home_record.get('streak', 0)
    away_streak = away_record.get('streak', 0)
    
    if home_streak >= 3 and away_streak <= -2:
        score_home += 1.0
        reasons_home.append(f"🔥 W{home_streak}")
    elif away_streak >= 3 and home_streak <= -2:
        score_away += 1.0
        reasons_away.append(f"🔥 W{away_streak}")
    elif home_streak >= 4:
        score_home += 0.5
        reasons_home.append(f"🔥 W{home_streak}")
    elif away_streak >= 4:
        score_away += 0.5
        reasons_away.append(f"🔥 W{away_streak}")
    
    h2h_edge = H2H_EDGES.get((home_team, away_team), 0)
    if h2h_edge > 0:
        score_home += h2h_edge
        reasons_home.append("🆚 H2H")
    h2h_edge_rev = H2H_EDGES.get((away_team, home_team), 0)
    if h2h_edge_rev > 0:
        score_away += h2h_edge_rev
        reasons_away.append("🆚 H2H")
    
    total = score_home + score_away
    if total > 0:
        home_final = round((score_home / total) * 10, 1)
        away_final = round((score_away / total) * 10, 1)
    else:
        home_final, away_final = 5.0, 5.0
    
    if home_final >= away_final:
        return home_team, home_final, round((home_final - 5) * 4, 0), reasons_home[:4], home_stars, away_stars
    else:
        return away_team, away_final, round((away_final - 5) * 4, 0), reasons_away[:4], home_stars, away_stars

def get_signal_tier(score):
    if score >= 8.0: return "🟢 STRONG BUY", "#00ff00"
    elif score >= 6.5: return "🔵 BUY", "#00aaff"
    elif score >= 5.5: return "🟡 LEAN", "#ffff00"
    elif score >= 4.5: return "⚪ TOSS-UP", "#888888"
    else: return "🔴 SKIP", "#ff0000"

# ========== LIVE SIGNAL FEED FUNCTIONS ==========
def update_drought_tracker(game_key, current_total):
    """Track scoring droughts per game"""
    now = datetime.now(pytz.timezone('US/Eastern'))
    
    if game_key not in st.session_state.drought_tracker:
        st.session_state.drought_tracker[game_key] = {
            "last_total": current_total,
            "last_change_time": now
        }
        return 0, "NORMAL"
    
    tracker = st.session_state.drought_tracker[game_key]
    
    if current_total != tracker["last_total"]:
        tracker["last_total"] = current_total
        tracker["last_change_time"] = now
        return 0, "NORMAL"
    
    seconds_since = (now - tracker["last_change_time"]).total_seconds()
    
    if seconds_since < 60:
        return seconds_since, "NORMAL"
    elif seconds_since < 120:
        return seconds_since, "MODERATE"
    else:
        return seconds_since, "HIGH"

def update_pace_history(game_key, current_total, current_mins):
    """Track pace history for momentum detection"""
    now = datetime.now(pytz.timezone('US/Eastern'))
    
    if game_key not in st.session_state.pace_history:
        st.session_state.pace_history[game_key] = []
    
    history = st.session_state.pace_history[game_key]
    
    # Add current data point
    history.append({
        "time": now,
        "total": current_total,
        "mins": current_mins
    })
    
    # Keep only last 10 data points (roughly 5 min at 30s refresh)
    if len(history) > 10:
        st.session_state.pace_history[game_key] = history[-10:]

def get_momentum_signal(game_key, current_pace):
    """Calculate momentum direction based on pace history"""
    history = st.session_state.pace_history.get(game_key, [])
    
    if len(history) < 3:
        return "NEUTRAL", "#888888"
    
    # Get recent pace (last 3 samples) vs earlier pace
    recent_entries = history[-3:]
    earlier_entries = history[:-3] if len(history) > 3 else []
    
    if not earlier_entries:
        return "NEUTRAL", "#888888"
    
    # Calculate average pace for each window
    def calc_window_pace(entries):
        if len(entries) < 2:
            return None
        first, last = entries[0], entries[-1]
        mins_diff = last["mins"] - first["mins"]
        pts_diff = last["total"] - first["total"]
        if mins_diff > 0:
            return pts_diff / mins_diff
        return None
    
    recent_pace = calc_window_pace(recent_entries)
    earlier_pace = calc_window_pace(earlier_entries)
    
    if recent_pace is None or earlier_pace is None:
        return "NEUTRAL", "#888888"
    
    pace_delta = recent_pace - earlier_pace
    
    # Thresholds for meaningful change
    if pace_delta < -0.3:
        return "COOLING", "#00aaff"
    elif pace_delta > 0.3:
        return "HEATING", "#ff6600"
    else:
        return "NEUTRAL", "#888888"

def calc_required_pace(current_total, threshold, mins_played, side):
    """Calculate required pace to break the line"""
    remaining_mins = max(48 - mins_played, 0.1)
    
    if side == "NO":
        # For NO bet: required pace for total to go OVER (bad for us)
        points_needed = threshold - current_total + 0.5  # Need to exceed threshold
        required = points_needed / remaining_mins
        return max(required, 0), "OVER"
    else:
        # For YES bet: required pace for total to stay OVER (good for us)
        points_needed = threshold - current_total + 0.5
        required = points_needed / remaining_mins
        return max(required, 0), "OVER"

def format_drought_time(seconds):
    """Format seconds into M:SS display"""
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins}:{secs:02d}"

def get_cushion_status(cushion, side):
    """Get cushion status label and color"""
    if cushion >= 15:
        return "VERY SAFE", "#00ff00"
    elif cushion >= 8:
        return "GOOD", "#00ff00"
    elif cushion >= 3:
        return "ON TRACK", "#ffff00"
    elif cushion >= -3:
        return "WARNING", "#ff8800"
    else:
        return "AT RISK", "#ff0000"

def get_signal_recommendation(current_pace, projected, momentum, drought_level):
    """Generate actionable recommendation based on all signals"""
    THRESHOLDS = [210.5, 215.5, 220.5, 225.5, 230.5, 235.5, 240.5, 245.5, 250.5, 255.5, 260.5, 265.5, 270.5]
    
    # Score the signals for NO vs YES
    no_score = 0
    yes_score = 0
    
    # Pace scoring
    if current_pace < 4.5:
        no_score += 2   # Very slow = NO (under) - low scoring game
    elif current_pace < 4.8:
        no_score += 1   # Slow-ish = lean NO
    elif current_pace > 5.2:
        yes_score += 2  # Very fast = YES (over) - high scoring game
    elif current_pace > 4.9:
        yes_score += 1  # Fast-ish = lean YES
    
    # Momentum scoring
    if momentum == "COOLING":
        no_score += 2   # Offense slowing = NO (under)
    elif momentum == "HEATING":
        yes_score += 2  # Offense heating = YES (over)
    
    # Drought scoring
    if drought_level == "HIGH":
        no_score += 1   # Long drought = NO (scoring stopped)
    elif drought_level == "MODERATE":
        no_score += 0.5
    
    # Determine recommendation
    if no_score >= 3 and no_score > yes_score + 1:
        # Strong NO signal - find threshold above projected
        for t in THRESHOLDS:
            if t > projected + 5:
                cushion = t - projected
                return "NO", t, cushion, "#00ff00"
        return "NO", THRESHOLDS[-1], THRESHOLDS[-1] - projected, "#00ff00"
    
    elif yes_score >= 3 and yes_score > no_score + 1:
        # Strong YES signal - find threshold below projected
        for t in reversed(THRESHOLDS):
            if t < projected - 5:
                cushion = projected - t
                return "YES", t, cushion, "#00aaff"
        return "YES", THRESHOLDS[0], projected - THRESHOLDS[0], "#00aaff"
    
    else:
        # Mixed signals - no clear edge
        return "WAIT", None, 0, "#888888"

# ========== FETCH DATA ==========
games = fetch_espn_scores(date_key=today_str)
game_list = sorted(list(games.keys()))
yesterday_teams_raw = fetch_yesterday_teams()
injuries = fetch_espn_injuries()
now = datetime.now(pytz.timezone('US/Eastern'))

today_teams = set()
for game_key in games.keys():
    parts = game_key.split("@")
    today_teams.add(parts[0])
    today_teams.add(parts[1])
yesterday_teams = yesterday_teams_raw.intersection(today_teams)

# ========== UPDATE SIGNAL TRACKERS ==========
for game_key, g in games.items():
    mins = get_minutes_played(g['period'], g['clock'], g['status_type'])
    if g['status_type'] not in ["STATUS_FINAL", "STATUS_SCHEDULED"] and mins > 0:
        update_drought_tracker(game_key, g['total'])
        update_pace_history(game_key, g['total'], mins)

# ============================================================
# ========== TITLE - TOP OF PAGE ==========
# ============================================================
st.title("🎯 NBA EDGE FINDER")

# ============================================================
# ========== ACTIVE POSITIONS ==========
# ============================================================
st.subheader("📈 ACTIVE POSITIONS")

hdr1, hdr2, hdr3 = st.columns([3, 1, 1])
hdr1.caption(f"{auto_status} | {now.strftime('%I:%M:%S %p ET')} | v15.44 SIGNAL")
if hdr2.button("🔄 Auto" if not st.session_state.auto_refresh else "⏹️ Stop", use_container_width=True):
    st.session_state.auto_refresh = not st.session_state.auto_refresh
    st.rerun()
if hdr3.button("🔄 Refresh", use_container_width=True):
    st.query_params["r"] = str(int(time.time()))
    st.rerun()

if st.session_state.positions:
    for idx, pos in enumerate(st.session_state.positions):
        game_key = pos['game']
        g = games.get(game_key)
        price = pos.get('price', 50)
        contracts = pos.get('contracts', 1)
        cost = round(price * contracts / 100, 2)
        pos_type = pos.get('type', 'totals')
        potential_win = round((100 - price) * contracts / 100, 2)
        
        if g:
            total = g['total']
            mins = get_minutes_played(g['period'], g['clock'], g['status_type'])
            is_final = g['status_type'] == "STATUS_FINAL"
            game_status = "FINAL" if is_final else f"Q{g['period']} {g['clock']}"
            
            if pos_type == 'ml':
                pick = pos.get('pick', '')
                parts = game_key.split("@")
                away_team, home_team = parts[0], parts[1]
                home_score, away_score = g['home_score'], g['away_score']
                pick_score = home_score if pick == home_team else away_score
                opp_score = away_score if pick == home_team else home_score
                lead = pick_score - opp_score
                
                if is_final:
                    won = pick_score > opp_score
                    status_label = "✅ WON!" if won else "❌ LOST"
                    status_color = "#00ff00" if won else "#ff0000"
                    pnl = f"+${potential_win:.2f}" if won else f"-${cost:.2f}"
                    pnl_color = "#00ff00" if won else "#ff0000"
                elif mins > 0:
                    if lead >= 15: status_label, status_color = "🟢 CRUISING", "#00ff00"
                    elif lead >= 8: status_label, status_color = "🟢 LEADING", "#00ff00"
                    elif lead >= 1: status_label, status_color = "🟡 AHEAD", "#ffff00"
                    elif lead >= -5: status_label, status_color = "🟠 CLOSE", "#ff8800"
                    else: status_label, status_color = "🔴 BEHIND", "#ff0000"
                    pnl, pnl_color = f"Win: +${potential_win:.2f}", "#888"
                else:
                    status_label, status_color = "⏳ WAITING", "#888"
                    lead = 0
                    pnl, pnl_color = f"Win: +${potential_win:.2f}", "#888"
                
                tracking_line = ""
                if pos.get('added_at'):
                    tracking_line = f"<div style='margin-top:5px;color:#666;font-size:0.85em'>⏰ Added: {pos.get('added_at')} | Score: {pos.get('score', 'N/A')}/10"
                    if pos.get('morning_price'):
                        move = pos['morning_price'] - price
                        move_color = "#00ff00" if move > 0 else "#ff0000"
                        tracking_line += f" | 🌅 AM: <span style='color:{move_color}'>{pos['morning_price']}¢ ({'+' if move > 0 else ''}{move}¢)</span>"
                    tracking_line += "</div>"
                
                st.markdown(f"<div style='background:linear-gradient(135deg,#1a1a2e,#16213e);padding:15px;border-radius:10px;border:2px solid {status_color};margin-bottom:10px'><div style='display:flex;justify-content:space-between'><div><b style='color:#fff;font-size:1.2em'>{game_key.replace('@', ' @ ')}</b> <span style='color:#888'>{game_status}</span></div><b style='color:{status_color};font-size:1.3em'>{status_label}</b></div><div style='margin-top:10px;color:#aaa'>🎯 ML: <b style='color:#fff'>{pick}</b> | 💵 {contracts}x @ {price}¢ (${cost:.2f}) | 📊 {pick_score}-{opp_score} | Lead: <b style='color:{status_color}'>{lead:+d}</b> | <span style='color:{pnl_color}'>{pnl}</span></div>{tracking_line}</div>", unsafe_allow_html=True)
            else:
                projected = round((total / mins) * 48) if mins > 0 else None
                cushion = (pos['threshold'] - projected) if pos.get('side') == "NO" and projected else ((projected - pos['threshold']) if projected else 0)
                
                if is_final:
                    won = (total < pos['threshold']) if pos.get('side') == "NO" else (total > pos['threshold'])
                    status_label = "✅ WON!" if won else "❌ LOST"
                    status_color = "#00ff00" if won else "#ff0000"
                    pnl = f"+${potential_win:.2f}" if won else f"-${cost:.2f}"
                    pnl_color = "#00ff00" if won else "#ff0000"
                elif projected:
                    if cushion >= 15: status_label, status_color = "🟢 VERY SAFE", "#00ff00"
                    elif cushion >= 8: status_label, status_color = "🟢 GOOD", "#00ff00"
                    elif cushion >= 3: status_label, status_color = "🟡 ON TRACK", "#ffff00"
                    elif cushion >= -3: status_label, status_color = "🟠 WARNING", "#ff8800"
                    else: status_label, status_color = "🔴 AT RISK", "#ff0000"
                    pnl, pnl_color = f"Win: +${potential_win:.2f}", "#888"
                else:
                    status_label, status_color = "⏳ WAITING", "#888"
                    pnl, pnl_color = f"Win: +${potential_win:.2f}", "#888"
                
                st.markdown(f"<div style='background:linear-gradient(135deg,#1a1a2e,#16213e);padding:15px;border-radius:10px;border:2px solid {status_color};margin-bottom:10px'><div style='display:flex;justify-content:space-between'><div><b style='color:#fff;font-size:1.2em'>{game_key.replace('@', ' @ ')}</b> <span style='color:#888'>{game_status}</span></div><b style='color:{status_color};font-size:1.3em'>{status_label}</b></div><div style='margin-top:10px;color:#aaa'>📊 {pos.get('side', 'NO')} {pos.get('threshold', 0)} | 💵 {contracts}x @ {price}¢ | Proj: <b style='color:#fff'>{projected if projected else '—'}</b> | Cushion: <b style='color:{status_color}'>{cushion:+.0f}</b> | <span style='color:{pnl_color}'>{pnl}</span></div></div>", unsafe_allow_html=True)
            
            btn1, btn2, btn3 = st.columns([3, 1, 1])
            parts = game_key.split("@")
            kalshi_url = build_kalshi_ml_url(parts[0], parts[1]) if pos_type == 'ml' else build_kalshi_totals_url(parts[0], parts[1])
            btn1.link_button("🔗 Trade on Kalshi", kalshi_url, use_container_width=True)
            if btn2.button("✏️", key=f"edit_{idx}"):
                st.session_state.editing_position = idx if st.session_state.editing_position != idx else None
                st.rerun()
            if btn3.button("🗑️", key=f"del_{idx}"):
                st.session_state.positions.pop(idx)
                st.session_state.editing_position = None
                save_positions(st.session_state.positions)
                st.rerun()
            
            if st.session_state.editing_position == idx:
                with st.container():
                    st.markdown("##### ✏️ Edit Position")
                    e1, e2, e3, e4 = st.columns(4)
                    new_price = e1.number_input("Entry ¢", min_value=1, max_value=99, value=pos.get('price', 50), key=f"price_{idx}")
                    new_contracts = e2.number_input("Contracts", min_value=1, value=pos.get('contracts', 1), key=f"contracts_{idx}")
                    new_morning = e3.number_input("🌅 AM ¢", min_value=0, max_value=99, value=pos.get('morning_price') or 0, key=f"morning_{idx}", help="Enter morning price to track move")
                    
                    if pos_type == 'totals':
                        new_threshold = e4.number_input("Line", min_value=180.0, max_value=280.0, value=float(pos.get('threshold', 225.5)), step=0.5, key=f"threshold_{idx}")
                        side_options = ["NO", "YES"]
                        current_side = pos.get('side', 'NO')
                        new_side = st.radio("Side", side_options, index=side_options.index(current_side), horizontal=True, key=f"side_{idx}")
                    else:
                        parts = game_key.split("@")
                        pick_options = [parts[1], parts[0]]
                        current_pick = pos.get('pick', parts[1])
                        pick_idx = pick_options.index(current_pick) if current_pick in pick_options else 0
                        new_pick = e4.radio("Pick", pick_options, index=pick_idx, horizontal=True, key=f"pick_{idx}")
                    
                    save_col, cancel_col = st.columns(2)
                    if save_col.button("💾 Save", key=f"save_{idx}", use_container_width=True, type="primary"):
                        st.session_state.positions[idx]['price'] = new_price
                        st.session_state.positions[idx]['contracts'] = new_contracts
                        st.session_state.positions[idx]['cost'] = round(new_price * new_contracts / 100, 2)
                        st.session_state.positions[idx]['morning_price'] = new_morning if new_morning > 0 else None
                        if pos_type == 'totals':
                            st.session_state.positions[idx]['threshold'] = new_threshold
                            st.session_state.positions[idx]['side'] = new_side
                        else:
                            st.session_state.positions[idx]['pick'] = new_pick
                        st.session_state.editing_position = None
                        save_positions(st.session_state.positions)
                        st.rerun()
                    if cancel_col.button("❌ Cancel", key=f"cancel_{idx}", use_container_width=True):
                        st.session_state.editing_position = None
                        st.rerun()
                    st.divider()
        else:
            st.markdown(f"<div style='background:#1a1a2e;padding:15px;border-radius:10px;border:1px solid #444;margin-bottom:10px;color:#888'>{game_key.replace('@', ' @ ')} — ⏳ Game not started</div>", unsafe_allow_html=True)
            btn1, btn2 = st.columns([4, 1])
            if btn2.button("🗑️", key=f"del_{idx}"):
                st.session_state.positions.pop(idx)
                save_positions(st.session_state.positions)
                st.rerun()
    
    if st.button("🗑️ Clear All", use_container_width=True):
        st.session_state.positions = []
        st.session_state.editing_position = None
        save_positions(st.session_state.positions)
        st.rerun()
else:
    st.info("No positions — add below")

st.divider()

# ============================================================
# ========== LIVE SIGNAL FEED ==========
# ============================================================
st.subheader("📡 LIVE SIGNAL FEED")

live_games = []
for game_key, g in games.items():
    mins = get_minutes_played(g['period'], g['clock'], g['status_type'])
    if g['status_type'] not in ["STATUS_FINAL", "STATUS_SCHEDULED"] and mins >= 6:
        live_games.append((game_key, g, mins))

if live_games:
    for game_key, g, mins in live_games:
        total = g['total']
        current_pace = round(total / mins, 2) if mins > 0 else 0
        projected = round(current_pace * 48) if mins > 0 else 0
        
        # Get signals
        drought_secs, drought_level = update_drought_tracker(game_key, total)
        momentum, momentum_color = get_momentum_signal(game_key, current_pace)
        
        # Drought color
        if drought_level == "HIGH":
            drought_color = "#ff0000"
        elif drought_level == "MODERATE":
            drought_color = "#ffaa00"
        else:
            drought_color = "#00ff00"
        
        # Find if user has position on this game
        user_position = None
        for pos in st.session_state.positions:
            if pos.get('game') == game_key and pos.get('type') == 'totals':
                user_position = pos
                break
        
        # Build signal card
        game_status = f"Q{g['period']} {g['clock']}"
        
        # Get recommendation
        rec_side, rec_threshold, rec_cushion, rec_color = get_signal_recommendation(current_pace, projected, momentum, drought_level)
        
        with st.expander(f"📡 {game_key.replace('@', ' @ ')} — {game_status}", expanded=False):
            # RECOMMENDATION BOX - TOP AND CENTER
            if rec_side != "WAIT":
                st.markdown(f"""
                <div style='background:linear-gradient(135deg,#1a3a1a,#0f2a0f);padding:15px;border-radius:10px;border:2px solid {rec_color};margin-bottom:12px;text-align:center'>
                <div style='color:#888;font-size:0.85em'>🎯 SIGNAL RECOMMENDATION</div>
                <div style='color:{rec_color};font-size:1.8em;font-weight:bold'>BUY {rec_side} {rec_threshold}</div>
                <div style='color:#888;font-size:0.9em'>Cushion: +{rec_cushion:.0f} pts</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style='background:linear-gradient(135deg,#2a2a2a,#1a1a1a);padding:15px;border-radius:10px;border:2px solid #555;margin-bottom:12px;text-align:center'>
                <div style='color:#888;font-size:0.85em'>🎯 SIGNAL RECOMMENDATION</div>
                <div style='color:#888;font-size:1.5em;font-weight:bold'>⚠️ NO CLEAR EDGE</div>
                <div style='color:#666;font-size:0.9em'>Mixed signals - wait for better setup</div>
                </div>
                """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"""
                <div style='background:#0f172a;padding:12px;border-radius:8px;margin-bottom:8px'>
                <div style='color:#888;font-size:0.85em'>CURRENT PACE</div>
                <div style='color:#fff;font-size:1.4em;font-weight:bold'>{current_pace} pts/min</div>
                <div style='color:#666;font-size:0.85em'>Projected: {projected} pts</div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div style='background:#0f172a;padding:12px;border-radius:8px'>
                <div style='color:#888;font-size:0.85em'>SCORING DROUGHT</div>
                <div style='color:{drought_color};font-size:1.4em;font-weight:bold'>{format_drought_time(drought_secs)}</div>
                <div style='color:{drought_color};font-size:0.85em'>{drought_level}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div style='background:#0f172a;padding:12px;border-radius:8px;margin-bottom:8px'>
                <div style='color:#888;font-size:0.85em'>MOMENTUM</div>
                <div style='color:{momentum_color};font-size:1.4em;font-weight:bold'>{momentum}</div>
                <div style='color:#666;font-size:0.85em'>{'Offense slowing' if momentum == 'COOLING' else 'Offense heating up' if momentum == 'HEATING' else 'Stable pace'}</div>
                </div>
                """, unsafe_allow_html=True)
                
                # Required pace (if user has totals position)
                if user_position:
                    threshold = user_position.get('threshold', 225.5)
                    side = user_position.get('side', 'NO')
                    required_pace, direction = calc_required_pace(total, threshold, mins, side)
                    
                    # Color based on comparison to current pace
                    if side == "NO":
                        if required_pace > current_pace + 0.5:
                            req_color = "#00ff00"
                        elif required_pace > current_pace:
                            req_color = "#ffff00"
                        else:
                            req_color = "#ff0000"
                    else:
                        if required_pace < current_pace - 0.5:
                            req_color = "#00ff00"
                        elif required_pace < current_pace:
                            req_color = "#ffff00"
                        else:
                            req_color = "#ff0000"
                    
                    st.markdown(f"""
                    <div style='background:#0f172a;padding:12px;border-radius:8px'>
                    <div style='color:#888;font-size:0.85em'>REQUIRED PACE TO LOSE</div>
                    <div style='color:{req_color};font-size:1.4em;font-weight:bold'>{required_pace:.2f} pts/min</div>
                    <div style='color:#666;font-size:0.85em'>{side} {threshold} position</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style='background:#0f172a;padding:12px;border-radius:8px'>
                    <div style='color:#888;font-size:0.85em'>GAME TOTAL</div>
                    <div style='color:#fff;font-size:1.4em;font-weight:bold'>{total} pts</div>
                    <div style='color:#666;font-size:0.85em'>{mins:.1f} min played</div>
                    </div>
                    """, unsafe_allow_html=True)
else:
    st.info("No live games with 6+ minutes played")

st.divider()

# ========== INJURY REPORT ==========
st.subheader("🏥 INJURY REPORT")

with st.sidebar:
    total_injuries = sum(len(v) for v in injuries.values())
    st.caption(f"📊 {total_injuries} injuries loaded")

if game_list:
    teams_playing = set()
    for game_key in game_list:
        parts = game_key.split("@")
        teams_playing.add(parts[0])
        teams_playing.add(parts[1])
    
    star_injuries = []
    for team in sorted(teams_playing):
        team_injuries = get_detailed_injuries(team, injuries)
        for inj in team_injuries:
            if inj['tier'] >= 2:
                star_injuries.append((team, inj))
    
    if star_injuries:
        cols = st.columns(3)
        for idx, (team, inj) in enumerate(star_injuries):
            with cols[idx % 3]:
                status_color = "#ff0000" if inj['status'] == "OUT" else "#ffaa00"
                st.markdown(f"<div style='background:linear-gradient(135deg,#2a1a1a,#1a1a2e);padding:10px;border-radius:8px;border-left:4px solid {status_color};margin-bottom:8px'><b style='color:#fff'>{inj['stars']} {inj['name']}</b> {inj['type_emoji']}<br><span style='color:{status_color}'>{inj['status']}</span> • {team}</div>", unsafe_allow_html=True)
    else:
        st.info("✅ No key star injuries for today's games")
else:
    st.info("No games scheduled")

if yesterday_teams:
    st.info(f"📅 **B2B**: {', '.join(sorted(yesterday_teams))}")

st.divider()

# ========== ML PICKS ==========
st.subheader("🎯 ML PICKS")

ml_results = []
for game_key, g in games.items():
    away = g["away_team"]
    home = g["home_team"]
    try:
        pick, score, edge, reasons, home_stars, away_stars = calc_ml_score(home, away, yesterday_teams, injuries)
        tier, color = get_signal_tier(score)
        ml_results.append({"pick": pick, "score": score, "color": color, "reasons": reasons, "away": away, "home": home})
    except:
        continue

ml_results.sort(key=lambda x: x["score"], reverse=True)

for r in ml_results:
    if r["score"] < 5.5: continue
    kalshi_url = build_kalshi_ml_url(r["away"], r["home"])
    reasons = " • ".join(r["reasons"])
    st.markdown(f"""<div style="display:flex;align-items:center;justify-content:space-between;background:linear-gradient(135deg,#0f172a,#020617);padding:6px 12px;margin-bottom:4px;border-radius:6px;border-left:3px solid {r['color']}"><div><b style="color:#fff">{r['pick']}</b> <span style="color:#666">vs {r['away'] if r['pick']==r['home'] else r['home']}</span> <span style="color:#38bdf8">{r['score']}/10</span> <span style="color:#777;font-size:0.8em">{reasons}</span></div><a href="{kalshi_url}" target="_blank" style="background:#16a34a;color:#fff;padding:4px 10px;border-radius:5px;font-size:0.8em;text-decoration:none;font-weight:600">BUY {r['pick']}</a></div>""", unsafe_allow_html=True)

strong_picks = [r for r in ml_results if r["score"] >= 6.5]
if strong_picks:
    if st.button(f"➕ Add {len(strong_picks)} Picks", use_container_width=True):
        added = 0
        for r in strong_picks:
            game_key = f"{r['away']}@{r['home']}"
            if not any(p.get('game') == game_key and p.get('pick') == r['pick'] for p in st.session_state.positions):
                st.session_state.positions.append({"game": game_key, "type": "ml", "pick": r['pick'], "price": 50, "contracts": 1, "cost": 0.50})
                added += 1
        if added:
            save_positions(st.session_state.positions)
            st.rerun()

st.divider()

# ========== ADD POSITION ==========
st.subheader("➕ ADD POSITION")

game_options = ["Select..."] + [gk.replace("@", " @ ") for gk in game_list]
selected_game = st.selectbox("Game", game_options)

if selected_game != "Select...":
    parts = selected_game.replace(" @ ", "@").split("@")
    col1, col2 = st.columns(2)
    col1.link_button("🔗 ML", build_kalshi_ml_url(parts[0], parts[1]), use_container_width=True)
    col2.link_button("🔗 Totals", build_kalshi_totals_url(parts[0], parts[1]), use_container_width=True)

market_type = st.radio("Type", ["Moneyline", "Totals"], horizontal=True)

p1, p2, p3 = st.columns(3)

if market_type == "Totals":
    with p1:
        yes_no = st.radio("Side", ["NO", "YES"], horizontal=True)
        st.session_state.selected_side = yes_no
    st.session_state.selected_threshold = st.number_input("Line", min_value=180.0, max_value=280.0, value=225.5, step=0.5)
else:
    with p1:
        if selected_game != "Select...":
            parts = selected_game.replace(" @ ", "@").split("@")
            st.session_state.selected_ml_pick = st.radio("Pick", [parts[1], parts[0]], horizontal=True)

price_paid = p2.number_input("Price ¢", min_value=1, max_value=99, value=50)
contracts = p3.number_input("Contracts", min_value=1, value=1)

if st.button("✅ ADD", use_container_width=True, type="primary"):
    if selected_game == "Select...":
        st.error("Select a game!")
    else:
        game_key = selected_game.replace(" @ ", "@")
        if market_type == "Moneyline":
            st.session_state.positions.append({"game": game_key, "type": "ml", "pick": st.session_state.selected_ml_pick, "price": price_paid, "contracts": contracts, "cost": round(price_paid * contracts / 100, 2)})
        else:
            st.session_state.positions.append({"game": game_key, "type": "totals", "side": st.session_state.selected_side, "threshold": st.session_state.selected_threshold, "price": price_paid, "contracts": contracts, "cost": round(price_paid * contracts / 100, 2)})
        save_positions(st.session_state.positions)
        st.rerun()

st.divider()

# ========== CUSHION SCANNER ==========
st.subheader("🎯 CUSHION SCANNER")

THRESHOLDS = [210.5, 215.5, 220.5, 225.5, 230.5, 235.5, 240.5, 245.5, 250.5, 255.5]

cs1, cs2 = st.columns([1, 1])
cush_min = cs1.selectbox("Min minutes", [6, 9, 12, 15, 18], index=0, key="cush_min_select")
cush_side = cs2.selectbox("Side", ["NO", "YES"], key="cush_side_select")

live_count = sum(1 for g in games.values() if g['status_type'] not in ["STATUS_FINAL", "STATUS_SCHEDULED"])
st.caption(f"📊 {len(games)} games | {live_count} live")

cush_results = []

for gk, g in games.items():
    mins = get_minutes_played(g['period'], g['clock'], g['status_type'])
    total = g['total']
    
    if g['status_type'] == "STATUS_FINAL":
        continue
    if mins < cush_min:
        continue
    if mins <= 0:
        continue
    
    pace = total / mins
    remaining_min = max(48 - mins, 1)
    projected_final = round(total + pace * remaining_min)
    
    if cush_side == "NO":
        tight_line = None
        safe_line = None
        for i, t in enumerate(THRESHOLDS):
            if t > projected_final:
                tight_line = t
                if i + 1 < len(THRESHOLDS):
                    safe_line = THRESHOLDS[i + 1]
                else:
                    safe_line = tight_line
                break
        if not tight_line:
            tight_line = THRESHOLDS[-1]
            safe_line = tight_line
        cushion = safe_line - projected_final
    else:
        tight_line = None
        safe_line = None
        for i in range(len(THRESHOLDS) - 1, -1, -1):
            if THRESHOLDS[i] < projected_final:
                tight_line = THRESHOLDS[i]
                if i - 1 >= 0:
                    safe_line = THRESHOLDS[i - 1]
                else:
                    safe_line = tight_line
                break
        if not tight_line:
            tight_line = THRESHOLDS[0]
            safe_line = tight_line
        cushion = projected_final - safe_line
    
    if cushion < 6:
        continue
    
    if cush_side == "NO":
        if pace < 4.6:
            pace_status, pace_color = "✅ SLOW", "#00ff00"
        elif pace < 4.9:
            pace_status, pace_color = "⚠️ AVG", "#ffff00"
        else:
            pace_status, pace_color = "❌ FAST", "#ff0000"
    else:
        if pace > 5.1:
            pace_status, pace_color = "✅ FAST", "#00ff00"
        elif pace > 4.8:
            pace_status, pace_color = "⚠️ AVG", "#ffff00"
        else:
            pace_status, pace_color = "❌ SLOW", "#ff0000"
    
    cush_results.append({
        'game': gk, 'total': total, 'mins': mins, 'pace': pace,
        'pace_status': pace_status, 'pace_color': pace_color,
        'projected': projected_final, 'cushion': cushion,
        'safe_line': safe_line, 'period': g['period'], 'clock': g['clock']
    })

cush_results.sort(key=lambda x: x['cushion'], reverse=True)

if cush_results:
    for r in cush_results:
        status_txt = f"Q{r['period']} {r['clock']}"
        st.markdown(f"""<div style="display:flex;align-items:center;justify-content:space-between;background:linear-gradient(135deg,#0f172a,#020617);padding:8px 12px;margin-bottom:4px;border-radius:6px;border-left:3px solid {r['pace_color']}">
        <div><b style="color:#fff">{r['game'].replace('@', ' @ ')}</b> <span style="color:#666">{status_txt}</span></div>
        <div style="display:flex;gap:15px;align-items:center">
        <span style="color:#888">Total: <b style="color:#fff">{r['total']}</b></span>
        <span style="color:#888">Proj: <b style="color:#fff">{r['projected']}</b></span>
        <span style="background:#ff6600;color:#000;padding:2px 8px;border-radius:4px;font-weight:bold">🎯 {cush_side} {r['safe_line']}</span>
        <span style="color:#00ff00;font-weight:bold">+{r['cushion']}</span>
        <span style="color:{r['pace_color']}">{r['pace_status']} {r['pace']:.2f}</span>
        </div></div>""", unsafe_allow_html=True)
else:
    st.info(f"No {cush_side} opportunities with 6+ cushion")

st.divider()

# ========== PACE SCANNER ==========
st.subheader("🔥 PACE SCANNER")

pace_data = []
for gk, g in games.items():
    mins = get_minutes_played(g['period'], g['clock'], g['status_type'])
    if mins >= 6:
        pace = round(g['total'] / mins, 2)
        proj = round(pace * 48)
        pace_data.append({"game": gk, "pace": pace, "proj": proj, "total": g['total'], "mins": mins, "period": g['period'], "clock": g['clock'], "final": g['status_type'] == "STATUS_FINAL"})

pace_data.sort(key=lambda x: x['pace'])

if pace_data:
    for p in pace_data:
        if p['pace'] < 4.5: lbl, clr = "🟢 SLOW", "#00ff00"
        elif p['pace'] < 4.8: lbl, clr = "🟡 AVG", "#ffff00"
        elif p['pace'] < 5.2: lbl, clr = "🟠 FAST", "#ff8800"
        else: lbl, clr = "🔴 SHOOTOUT", "#ff0000"
        status = "FINAL" if p['final'] else f"Q{p['period']} {p['clock']}"
        st.markdown(f"**{p['game'].replace('@', ' @ ')}** — {p['total']}pts/{p['mins']:.0f}min — **{p['pace']}/min** <span style='color:{clr}'>**{lbl}**</span> — Proj: **{p['proj']}** — {status}", unsafe_allow_html=True)
else:
    st.info("No games with 6+ min")

st.divider()

# ========== ALL GAMES ==========
st.subheader("📺 ALL GAMES")
if games:
    cols = st.columns(4)
    for i, (k, g) in enumerate(games.items()):
        with cols[i % 4]:
            st.write(f"**{g['away_team']}** {g['away_score']}")
            st.write(f"**{g['home_team']}** {g['home_score']}")
            status = "FINAL" if g['status_type'] == "STATUS_FINAL" else f"Q{g['period']} {g['clock']}"
            st.caption(f"{status} | {g['total']} pts")
else:
    st.info("No games today")

st.divider()
st.caption("⚠️ Entertainment only. Not financial advice. v15.44 SIGNAL")
