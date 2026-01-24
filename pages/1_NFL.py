import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="NFL Edge Finder", page_icon="🏈", layout="wide")

# ============================================================
# GA4 ANALYTICS - MUST BE RIGHT AFTER set_page_config
# ============================================================
GA_TRACKING_CODE = """
<script async src="https://www.googletagmanager.com/gtag/js?id=G-NQKY5VQ376"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-NQKY5VQ376', {
    page_title: 'NFL Edge Finder',
    page_location: 'https://bigsnapshot.streamlit.app/NFL',
    cookie_flags: 'SameSite=None;Secure',
    send_page_view: true
  });
</script>
"""
components.html(GA_TRACKING_CODE, height=1)

# ============================================================
# 🔐 AUTH CHECK — MUST BE AFTER GA
# ============================================================
from auth import require_auth
require_auth()

import requests
import json
import os
from datetime import datetime, timedelta
import pytz
from styles import apply_styles

apply_styles()

VERSION = "18.3"

# ============================================================
# STRONG PICKS SYSTEM
# ============================================================
STRONG_PICKS_FILE = "strong_picks.json"

def load_strong_picks():
    try:
        if os.path.exists(STRONG_PICKS_FILE):
            with open(STRONG_PICKS_FILE, 'r') as f:
                return json.load(f)
    except: pass
    return {"next_ml": 1, "picks": []}

def save_strong_picks(data):
    try:
        with open(STRONG_PICKS_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except: pass

if "strong_picks" not in st.session_state:
    st.session_state.strong_picks = load_strong_picks()

def get_next_ml_number():
    return st.session_state.strong_picks.get("next_ml", 1)

def add_strong_pick(game_key, pick_team, sport, price=50):
    ml_num = st.session_state.strong_picks.get("next_ml", 1)
    pick_data = {
        "ml_number": ml_num,
        "game": game_key,
        "pick": pick_team,
        "price": price,
        "timestamp": datetime.now(pytz.timezone('US/Eastern')).isoformat(),
        "sport": sport
    }
    st.session_state.strong_picks["picks"].append(pick_data)
    st.session_state.strong_picks["next_ml"] = ml_num + 1
    save_strong_picks(st.session_state.strong_picks)
    return ml_num

def get_strong_pick_for_game(game_key):
    for pick in st.session_state.strong_picks.get("picks", []):
        if pick.get("game") == game_key:
            return pick
    return None

def is_game_already_tagged(game_key):
    return get_strong_pick_for_game(game_key) is not None

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

eastern = pytz.timezone('US/Eastern')

# ============================================================
# TEAM MAPPINGS
# ============================================================
TEAM_ABBREVS = {
    "Arizona Cardinals": "ARI", "Atlanta Falcons": "ATL", "Baltimore Ravens": "BAL",
    "Buffalo Bills": "BUF", "Carolina Panthers": "CAR", "Chicago Bears": "CHI",
    "Cincinnati Bengals": "CIN", "Cleveland Browns": "CLE", "Dallas Cowboys": "DAL",
    "Denver Broncos": "DEN", "Detroit Lions": "DET", "Green Bay Packers": "GB",
    "Houston Texans": "HOU", "Indianapolis Colts": "IND", "Jacksonville Jaguars": "JAX",
    "Kansas City Chiefs": "KC", "Las Vegas Raiders": "LV", "Los Angeles Chargers": "LAC",
    "Los Angeles Rams": "LAR", "Miami Dolphins": "MIA", "Minnesota Vikings": "MIN",
    "New England Patriots": "NE", "New Orleans Saints": "NO", "New York Giants": "NYG",
    "New York Jets": "NYJ", "Philadelphia Eagles": "PHI", "Pittsburgh Steelers": "PIT",
    "San Francisco 49ers": "SF", "Seattle Seahawks": "SEA", "Tampa Bay Buccaneers": "TB",
    "Tennessee Titans": "TEN", "Washington Commanders": "WAS"
}

KALSHI_CODES = {
    "ARI": "ari", "ATL": "atl", "BAL": "bal", "BUF": "buf", "CAR": "car",
    "CHI": "chi", "CIN": "cin", "CLE": "cle", "DAL": "dal", "DEN": "den",
    "DET": "det", "GB": "gb", "HOU": "hou", "IND": "ind", "JAX": "jax",
    "KC": "kc", "LV": "lv", "LAC": "lac", "LAR": "lar", "MIA": "mia",
    "MIN": "min", "NE": "ne", "NO": "no", "NYG": "nyg", "NYJ": "nyj",
    "PHI": "phi", "PIT": "pit", "SF": "sf", "SEA": "sea", "TB": "tb",
    "TEN": "ten", "WAS": "was"
}

DOME_STADIUMS = ["ARI", "ATL", "DAL", "DET", "HOU", "IND", "LV", "LAC", "LAR", "MIN", "NO"]

# ============================================================
# TEAM STATS - POWER RATINGS, RECORDS, FORM
# ============================================================
TEAM_STATS = {
    "ARI": {"pwr": -12.5, "rank": 27, "home_win": 0.42, "record": "4-13", "form": "LLLWL"},
    "ATL": {"pwr": 2.5, "rank": 18, "home_win": 0.55, "record": "8-9", "form": "LWLWL"},
    "BAL": {"pwr": 15.5, "rank": 3, "home_win": 0.72, "record": "12-5", "form": "WWWLW"},
    "BUF": {"pwr": 18.2, "rank": 2, "home_win": 0.78, "record": "13-4", "form": "WWWWL"},
    "CAR": {"pwr": -18.5, "rank": 30, "home_win": 0.35, "record": "5-12", "form": "LLWLL"},
    "CHI": {"pwr": -8.5, "rank": 22, "home_win": 0.45, "record": "5-12", "form": "LLLLL"},
    "CIN": {"pwr": 5.8, "rank": 14, "home_win": 0.58, "record": "9-8", "form": "WWWWL"},
    "CLE": {"pwr": -25.0, "rank": 32, "home_win": 0.38, "record": "3-14", "form": "LLLLL"},
    "DAL": {"pwr": -5.2, "rank": 20, "home_win": 0.52, "record": "7-10", "form": "LLWLL"},
    "DEN": {"pwr": 8.5, "rank": 8, "home_win": 0.65, "record": "10-7", "form": "WLWWL"},
    "DET": {"pwr": 22.5, "rank": 1, "home_win": 0.78, "record": "15-2", "form": "WWWWW"},
    "GB": {"pwr": 12.2, "rank": 6, "home_win": 0.70, "record": "11-6", "form": "WWLWW"},
    "HOU": {"pwr": 10.5, "rank": 7, "home_win": 0.68, "record": "10-7", "form": "WLWWW"},
    "IND": {"pwr": -2.5, "rank": 16, "home_win": 0.55, "record": "8-9", "form": "LWLWL"},
    "JAX": {"pwr": -8.5, "rank": 23, "home_win": 0.45, "record": "4-13", "form": "LLLWL"},
    "KC": {"pwr": 18.5, "rank": 4, "home_win": 0.82, "record": "15-2", "form": "WWWWW"},
    "LV": {"pwr": -10.2, "rank": 25, "home_win": 0.42, "record": "4-13", "form": "LLLLW"},
    "LAC": {"pwr": 11.8, "rank": 5, "home_win": 0.62, "record": "11-6", "form": "WLWWW"},
    "LAR": {"pwr": 8.5, "rank": 9, "home_win": 0.62, "record": "10-7", "form": "WWLWW"},
    "MIA": {"pwr": -2.5, "rank": 17, "home_win": 0.55, "record": "8-9", "form": "WLLWL"},
    "MIN": {"pwr": 12.5, "rank": 5, "home_win": 0.68, "record": "14-3", "form": "WWWWL"},
    "NE": {"pwr": -12.5, "rank": 24, "home_win": 0.42, "record": "4-13", "form": "LLLLL"},
    "NO": {"pwr": -8.8, "rank": 21, "home_win": 0.48, "record": "5-12", "form": "LLLWL"},
    "NYG": {"pwr": -15.5, "rank": 29, "home_win": 0.35, "record": "3-14", "form": "LLLLL"},
    "NYJ": {"pwr": -6.5, "rank": 19, "home_win": 0.45, "record": "5-12", "form": "WLLLL"},
    "PHI": {"pwr": 14.8, "rank": 4, "home_win": 0.75, "record": "14-3", "form": "WWWWW"},
    "PIT": {"pwr": 4.8, "rank": 12, "home_win": 0.62, "record": "10-7", "form": "LLWWL"},
    "SF": {"pwr": -4.5, "rank": 18, "home_win": 0.52, "record": "6-11", "form": "LWLLL"},
    "SEA": {"pwr": 6.5, "rank": 10, "home_win": 0.62, "record": "10-7", "form": "WLWWL"},
    "TB": {"pwr": 5.8, "rank": 11, "home_win": 0.58, "record": "10-7", "form": "WWWLW"},
    "TEN": {"pwr": -14.8, "rank": 28, "home_win": 0.40, "record": "3-14", "form": "LLLLW"},
    "WAS": {"pwr": 8.5, "rank": 8, "home_win": 0.62, "record": "12-5", "form": "WWWWL"}
}

STADIUM_COORDS = {
    "ARI": (33.5277, -112.2626), "ATL": (33.7553, -84.4006), "BAL": (39.2780, -76.6227),
    "BUF": (42.7738, -78.7870), "CAR": (35.2258, -80.8528), "CHI": (41.8623, -87.6167),
    "CIN": (39.0955, -84.5161), "CLE": (41.5061, -81.6995), "DAL": (32.7473, -97.0945),
    "DEN": (39.7439, -105.0201), "DET": (42.3400, -83.0456), "GB": (44.5013, -88.0622),
    "HOU": (29.6847, -95.4107), "IND": (39.7601, -86.1639), "JAX": (30.3239, -81.6373),
    "KC": (39.0489, -94.4839), "LV": (36.0909, -115.1833), "LAC": (33.9535, -118.3392),
    "LAR": (33.9535, -118.3392), "MIA": (25.9580, -80.2389), "MIN": (44.9737, -93.2577),
    "NE": (42.0909, -71.2643), "NO": (29.9511, -90.0812), "NYG": (40.8128, -74.0742),
    "NYJ": (40.8128, -74.0742), "PHI": (39.9008, -75.1675), "PIT": (40.4468, -80.0158),
    "SF": (37.4032, -121.9698), "SEA": (47.5952, -122.3316), "TB": (27.9759, -82.5033),
    "TEN": (36.1665, -86.7713), "WAS": (38.9076, -76.8645)
}

# ============================================================
# HELPER FUNCTIONS
# ============================================================
def build_kalshi_url(away_abbr, home_abbr, game_date=None):
    if game_date:
        date_str = game_date.strftime("%y%b%d").upper()
    else:
        date_str = datetime.now(eastern).strftime("%y%b%d").upper()
    away_code = KALSHI_CODES.get(away_abbr, away_abbr.lower())
    home_code = KALSHI_CODES.get(home_abbr, home_abbr.lower())
    ticker = f"KXNFLGAME-{date_str}{away_code.upper()}{home_code.upper()}"
    return f"https://kalshi.com/markets/kxnflgame/{ticker.lower()}"

def format_form(form_str):
    if not form_str:
        return ""
    html = ""
    for c in form_str:
        if c == "W":
            html += '<span style="color:#22c55e;font-weight:bold;">W</span>'
        else:
            html += '<span style="color:#ef4444;font-weight:bold;">L</span>'
    return html

@st.cache_data(ttl=1800)
def fetch_weather(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,wind_speed_10m,precipitation&wind_speed_unit=mph&temperature_unit=fahrenheit"
        resp = requests.get(url, timeout=5)
        data = resp.json()
        current = data.get("current", {})
        return {"temp": current.get("temperature_2m", 70), "wind": current.get("wind_speed_10m", 0), "precip": current.get("precipitation", 0)}
    except:
        return {"temp": 70, "wind": 0, "precip": 0}

def get_weather_impact(home_abbr):
    if home_abbr in DOME_STADIUMS:
        return "🏠 Dome", "none"
    coords = STADIUM_COORDS.get(home_abbr)
    if not coords:
        return "", "none"
    w = fetch_weather(coords[0], coords[1])
    wind, precip = w.get("wind", 0), w.get("precip", 0)
    if wind >= 20 or precip > 0.5:
        return f"🌧️ {int(wind)}mph", "severe"
    elif wind >= 15 or precip > 0.1:
        return f"💨 {int(wind)}mph", "moderate"
    return "", "none"

def get_injury_impact(team_abbr, injuries):
    """Returns (out_count, impact_score) for key positions"""
    team_inj = injuries.get(team_abbr, [])
    key_pos = ["QB", "RB"]
    out_count = 0
    impact = 0
    for inj in team_inj:
        if 'out' in inj.get('status', '').lower():
            out_count += 1
            if inj.get('pos') in key_pos:
                impact += 4
            else:
                impact += 1
    return out_count, impact

# ============================================================
# STRONG PICK GATE FUNCTIONS (NFL-specific thresholds)
# ============================================================
def get_match_stability(home_abbr, away_abbr, injuries):
    """
    NFL Match Stability Check
    Returns: (stability_label, stability_color, is_stable, flags)
    """
    instability_score = 0
    flags = []
    
    # Check key injuries (QB/RB)
    home_out, home_impact = get_injury_impact(home_abbr, injuries)
    away_out, away_impact = get_injury_impact(away_abbr, injuries)
    if home_impact >= 4 or away_impact >= 4:
        instability_score += 2
        flags.append("⚠️ Key OUT")
    
    # Check extreme streaks (5+ game streaks in NFL are significant)
    home_form = TEAM_STATS.get(home_abbr, {}).get('form', '')
    away_form = TEAM_STATS.get(away_abbr, {}).get('form', '')
    home_streak = len(home_form) - len(home_form.lstrip(home_form[0])) if home_form else 0
    away_streak = len(away_form) - len(away_form.lstrip(away_form[0])) if away_form else 0
    if home_streak >= 5 or away_streak >= 5:
        instability_score += 1
        flags.append("⚠️ Streak Risk")
    
    # Check coin flip matchups (power rating within 3 pts)
    home_pwr = TEAM_STATS.get(home_abbr, {}).get('pwr', 0)
    away_pwr = TEAM_STATS.get(away_abbr, {}).get('pwr', 0)
    if abs(home_pwr - away_pwr) < 3:
        instability_score += 2
        flags.append("⚠️ Coin Flip")
    
    if instability_score >= 3:
        return "❌ UNSTABLE", "#ff4444", False, flags
    elif instability_score >= 1:
        return "⚠️ VOLATILE", "#ffaa00", True, flags
    else:
        return "✅ STABLE", "#00ff00", True, flags

def get_cushion_tier(game_data, pick_team):
    """
    NFL Cushion Tier Check
    Returns: (tier_label, tier_color, is_wide)
    NFL thresholds: home_advantage=2.5, wide_lead=7
    """
    home_abbr = game_data.get('home_abbr')
    away_abbr = game_data.get('away_abbr')
    
    if game_data.get('status_type') == "STATUS_SCHEDULED":
        home_pwr = TEAM_STATS.get(home_abbr, {}).get('pwr', 0)
        away_pwr = TEAM_STATS.get(away_abbr, {}).get('pwr', 0)
        home_advantage = 2.5
        
        if pick_team == home_abbr:
            diff = home_pwr - away_pwr + home_advantage
        else:
            diff = away_pwr - home_pwr - home_advantage
        
        if diff >= 10:
            return "🟢 WIDE", "#00ff00", True
        elif diff >= 3:
            return "🟡 NARROW", "#ffaa00", False
        else:
            return "🔴 NEGATIVE", "#ff4444", False
    else:
        home_score = game_data.get('home_score', 0)
        away_score = game_data.get('away_score', 0)
        
        if pick_team == home_abbr:
            lead = home_score - away_score
        else:
            lead = away_score - home_score
        
        wide_threshold = 7
        
        if lead >= wide_threshold:
            return "🟢 WIDE", "#00ff00", True
        elif lead >= 0:
            return "🟡 NARROW", "#ffaa00", False
        else:
            return "🔴 NEGATIVE", "#ff4444", False

def get_pace_direction(game_data):
    """
    NFL Pace Direction Check
    Returns: (pace_label, pace_color, is_positive)
    NFL: Q4 with 7pt or less = NEGATIVE
    """
    if game_data.get('status_type') == "STATUS_SCHEDULED":
        return "🟢 CONTROLLED", "#00ff00", True
    
    quarter = game_data.get('quarter', 0)
    home_score = game_data.get('home_score', 0)
    away_score = game_data.get('away_score', 0)
    diff = abs(home_score - away_score)
    
    is_late = quarter >= 4
    close_threshold = 7
    
    if is_late and diff <= close_threshold:
        return "🔴 NEGATIVE", "#ff4444", False
    elif quarter >= 3:
        return "🟡 NEUTRAL", "#ffaa00", True
    else:
        return "🟢 CONTROLLED", "#00ff00", True

def check_strong_pick_eligible(game_key, pick_team, game_data, injuries):
    """Check if pick passes all 3 gates for Strong Pick status"""
    home_abbr = game_data.get('home_abbr')
    away_abbr = game_data.get('away_abbr')
    
    stability_label, stability_color, is_stable, stability_flags = get_match_stability(
        home_abbr, away_abbr, injuries
    )
    cushion_label, cushion_color, is_wide = get_cushion_tier(game_data, pick_team)
    pace_label, pace_color, is_positive = get_pace_direction(game_data)
    
    reasons = []
    eligible = True
    
    if not is_wide:
        eligible = False
        reasons.append(f"Cushion: {cushion_label}")
    if not is_positive:
        eligible = False
        reasons.append(f"Pace: {pace_label}")
    if not is_stable:
        eligible = False
        reasons.append(f"Match: {stability_label}")
    
    return eligible, reasons, {
        "stability": (stability_label, stability_color, is_stable, stability_flags),
        "cushion": (cushion_label, cushion_color, is_wide),
        "pace": (pace_label, pace_color, is_positive)
    }

# ============================================================
# ESPN API FUNCTIONS
# ============================================================
@st.cache_data(ttl=300)
def fetch_nfl_news():
    try:
        url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/news?limit=5"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        articles = []
        for article in data.get("articles", [])[:3]:
            articles.append({
                "headline": article.get("headline", ""),
                "description": article.get("description", "")[:120] + "..." if article.get("description") else ""
            })
        return articles
    except:
        return []

@st.cache_data(ttl=60)
def fetch_nfl_scoreboard():
    url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        games = []
        week_info = data.get("week", {}).get("text", "Week")
        season_type = data.get("season", {}).get("type", {}).get("name", "")
        
        if not data.get("events"):
            for days_ahead in range(1, 8):
                future_date = (datetime.now(eastern) + timedelta(days=days_ahead)).strftime('%Y%m%d')
                url2 = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates={future_date}"
                try:
                    resp2 = requests.get(url2, timeout=5)
                    data2 = resp2.json()
                    if data2.get("events"):
                        data = data2
                        week_info = data2.get("week", {}).get("text", "Upcoming")
                        break
                except:
                    continue
        
        for event in data.get("events", []):
            comp = event.get("competitions", [{}])[0]
            competitors = comp.get("competitors", [])
            if len(competitors) < 2:
                continue
            
            home_team, away_team = {}, {}
            for c in competitors:
                full_name = c.get("team", {}).get("displayName", "")
                abbr = TEAM_ABBREVS.get(full_name, c.get("team", {}).get("abbreviation", ""))
                score = int(c.get("score", 0) or 0)
                record = ""
                if c.get("records"):
                    record = c["records"][0].get("summary", "")
                
                team_data = {
                    "name": full_name, "abbr": abbr, "score": score, "record": record
                }
                if c.get("homeAway") == "home":
                    home_team = team_data
                else:
                    away_team = team_data
            
            status_obj = event.get("status", {})
            status_type = status_obj.get("type", {}).get("name", "STATUS_SCHEDULED")
            status_detail = status_obj.get("type", {}).get("shortDetail", "")
            clock = status_obj.get("displayClock", "")
            period = status_obj.get("period", 0)
            game_date_str = event.get("date", "")
            
            games.append({
                "home": home_team, "away": away_team,
                "status_type": status_type, "status_detail": status_detail,
                "clock": clock, "quarter": period, "game_date": game_date_str
            })
        
        return games, week_info, season_type
    except Exception as e:
        return [], "", ""

@st.cache_data(ttl=300)
def fetch_nfl_injuries():
    injuries = {}
    try:
        url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/injuries"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        for team_data in data.get("injuries", []):
            team_name = team_data.get("team", {}).get("displayName", "")
            team_abbr = TEAM_ABBREVS.get(team_name, "")
            if not team_abbr:
                continue
            injuries[team_abbr] = []
            for cat in team_data.get("categories", []):
                for player in cat.get("items", []):
                    name = player.get("athlete", {}).get("displayName", "")
                    status = player.get("status", "")
                    pos = player.get("athlete", {}).get("position", {}).get("abbreviation", "")
                    if name:
                        injuries[team_abbr].append({"name": name, "status": status, "pos": pos})
    except:
        pass
    return injuries

# ============================================================
# ML SCORING MODEL
# ============================================================
def calc_ml_score(home_abbr, away_abbr, injuries):
    home = TEAM_STATS.get(home_abbr, {})
    away = TEAM_STATS.get(away_abbr, {})
    
    score_home, score_away = 0, 0
    reasons_home, reasons_away = [], []
    
    home_pwr = home.get('pwr', 0)
    away_pwr = away.get('pwr', 0)
    pwr_diff = home_pwr - away_pwr
    if pwr_diff > 10:
        score_home += 2.5
        reasons_home.append(f"📊 PWR +{pwr_diff:.0f}")
    elif pwr_diff > 5:
        score_home += 1.5
        reasons_home.append(f"📊 PWR +{pwr_diff:.0f}")
    elif pwr_diff < -10:
        score_away += 2.5
        reasons_away.append(f"📊 PWR +{-pwr_diff:.0f}")
    elif pwr_diff < -5:
        score_away += 1.5
        reasons_away.append(f"📊 PWR +{-pwr_diff:.0f}")
    
    home_hw = home.get('home_win', 0.5)
    if home_hw >= 0.65:
        score_home += 1.5
        reasons_home.append(f"🏟️ {int(home_hw*100)}% Home")
    else:
        score_home += 0.5
        reasons_home.append("🏟️ Home")
    
    home_rank = home.get('rank', 16)
    away_rank = away.get('rank', 16)
    if home_rank <= 8 and away_rank > 20:
        score_home += 1.5
        reasons_home.append(f"🏆 #{home_rank} PWR")
    elif away_rank <= 8 and home_rank > 20:
        score_away += 1.5
        reasons_away.append(f"🏆 #{away_rank} PWR")
    
    home_form = home.get('form', '')
    away_form = away.get('form', '')
    home_wins = home_form.count('W') if home_form else 0
    away_wins = away_form.count('W') if away_form else 0
    if home_wins >= 4:
        score_home += 1.0
        reasons_home.append("🔥 Hot")
    if away_wins >= 4:
        score_away += 1.0
        reasons_away.append("🔥 Hot")
    if home_wins <= 1:
        score_away += 0.5
    if away_wins <= 1:
        score_home += 0.5
    
    key_pos = ["QB", "RB"]
    home_key_out = len([i for i in injuries.get(home_abbr, []) if 'out' in i.get('status', '').lower() and i.get('pos') in key_pos])
    away_key_out = len([i for i in injuries.get(away_abbr, []) if 'out' in i.get('status', '').lower() and i.get('pos') in key_pos])
    if away_key_out > home_key_out:
        score_home += 2.0
        reasons_home.append(f"🏥 {away_key_out} key OUT")
    elif home_key_out > away_key_out:
        score_away += 2.0
        reasons_away.append(f"🏥 {home_key_out} key OUT")
    
    weather_str, impact = get_weather_impact(home_abbr)
    if impact == "severe":
        score_home += 1.0
        if weather_str:
            reasons_home.append(weather_str)
    
    total = score_home + score_away
    if total > 0:
        home_final = round((score_home / total) * 10, 1)
        away_final = round((score_away / total) * 10, 1)
    else:
        home_final, away_final = 5.0, 5.0
    
    if home_final >= away_final:
        return home_abbr, home_final, reasons_home[:4], True
    else:
        return away_abbr, away_final, reasons_away[:4], False

def get_signal_tier(score):
    if score >= 10.0:
        return "🔒 STRONG", "#22c55e"
    elif score >= 8.0:
        return "🔵 BUY", "#3b82f6"
    elif score >= 5.5:
        return "🟡 LEAN", "#eab308"
    else:
        return "⚪ PASS", "#6b7280"

# ============================================================
# SIDEBAR
# ============================================================
now = datetime.now(eastern)
today_str = now.strftime("%Y-%m-%d")

with st.sidebar:
    st.page_link("Home.py", label="🏠 Home", use_container_width=True)
    st.divider()
    
    st.header("🏷️ STRONG PICKS")
    today_tags = len([p for p in st.session_state.strong_picks.get('picks', []) 
                      if p.get('sport') == 'NFL' and today_str in p.get('timestamp', '')])
    st.markdown(f"""
**Next ML#:** ML-{get_next_ml_number():03d}  
**Today's Tags:** {today_tags}
""")
    st.divider()
    
    st.header("📖 SIGNAL TIERS")
    st.markdown("""
🔒 **STRONG** → 10.0 <span style="color:#888;font-size:0.8em;">Tracked</span>

🔵 **BUY** → 8.0-9.9 <span style="color:#888;font-size:0.8em;">Info only</span>

🟡 **LEAN** → 5.5-7.9 <span style="color:#888;font-size:0.8em;">Slight edge</span>

⚪ **PASS** → Below 5.5 <span style="color:#888;font-size:0.8em;">No edge</span>
""", unsafe_allow_html=True)
    st.divider()
    
    st.header("🔗 KALSHI")
    st.markdown('<a href="https://kalshi.com/?search=nfl" target="_blank" style="color: #00aaff;">NFL Markets ↗</a>', unsafe_allow_html=True)
    st.divider()
    st.caption(f"v{VERSION}")

# ============================================================
# MAIN CONTENT
# ============================================================
st.title("🏈 NFL EDGE FINDER")
st.caption(f"v{VERSION} | {now.strftime('%I:%M:%S %p ET')} | Real ESPN Data")

news = fetch_nfl_news()
games, week_info, season_type = fetch_nfl_scoreboard()
injuries = fetch_nfl_injuries()

st.divider()

# ============================================================
# 🏆 PLAYOFFS & SUPER BOWL INFO
# ============================================================
st.markdown("""
<div style="background: linear-gradient(135deg, #1a1a2e, #16213e); padding: 18px 22px; border-radius: 12px; border-left: 5px solid #ffd700; margin-bottom: 20px;">
    <div style="display: flex; justify-content: space-between; flex-wrap: wrap; gap: 15px;">
        <div>
            <span style="font-size: 1.4em; font-weight: bold; color: #ffd700;">🏆 SUPER BOWL LIX</span><br>
            <span style="color: #fff; font-size: 1.1em;">February 9, 2025</span><br>
            <span style="color: #aaa;">Caesars Superdome • New Orleans, LA</span>
        </div>
        <div style="text-align: right;">
            <span style="color: #888; font-size: 0.9em;">CONFERENCE CHAMPIONSHIPS</span><br>
            <span style="color: #fff;">January 26, 2025</span><br>
            <span style="color: #aaa;">AFC & NFC Title Games</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div style="background: #0f172a; padding: 15px 20px; border-radius: 10px; margin-bottom: 15px;">
    <div style="font-weight: bold; color: #3b82f6; margin-bottom: 10px;">🔵 AFC PLAYOFF BRACKET</div>
    <div style="display: flex; gap: 20px; flex-wrap: wrap; color: #ccc; font-size: 0.95em;">
        <div><span style="color: #ffd700;">1.</span> KC (15-2) — BYE</div>
        <div><span style="color: #c0c0c0;">2.</span> BUF (13-4) — BYE</div>
        <div><span style="color: #cd7f32;">3.</span> BAL (12-5)</div>
        <div>4. HOU (10-7)</div>
        <div>5. LAC (11-6)</div>
        <div>6. PIT (10-7)</div>
        <div>7. DEN (10-7)</div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div style="background: #0f172a; padding: 15px 20px; border-radius: 10px; margin-bottom: 15px;">
    <div style="font-weight: bold; color: #ef4444; margin-bottom: 10px;">🔴 NFC PLAYOFF BRACKET</div>
    <div style="display: flex; gap: 20px; flex-wrap: wrap; color: #ccc; font-size: 0.95em;">
        <div><span style="color: #ffd700;">1.</span> DET (15-2) — BYE</div>
        <div><span style="color: #c0c0c0;">2.</span> PHI (14-3) — BYE</div>
        <div><span style="color: #cd7f32;">3.</span> MIN (14-3)</div>
        <div>4. LAR (10-7)</div>
        <div>5. TB (10-7)</div>
        <div>6. WAS (12-5)</div>
        <div>7. GB (11-6)</div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div style="background: #1e293b; padding: 12px 18px; border-radius: 8px; margin-bottom: 15px;">
    <span style="font-weight: bold; color: #fff;">📅 KEY DATES</span>
    <span style="color: #888; margin-left: 20px;">Wild Card: Jan 11-13</span>
    <span style="color: #888; margin-left: 15px;">Divisional: Jan 18-19</span>
    <span style="color: #888; margin-left: 15px;">Conf Champ: Jan 26</span>
    <span style="color: #888; margin-left: 15px;">Pro Bowl: Feb 2</span>
    <span style="color: #ffd700; margin-left: 15px; font-weight: bold;">Super Bowl: Feb 9</span>
</div>
""", unsafe_allow_html=True)

# ============================================================
# 📰 BREAKING NEWS
# ============================================================
st.subheader("📰 BREAKING NEWS")

if news:
    for article in news:
        st.markdown(f"""
        <div style="background: #0f172a; padding: 12px 15px; margin-bottom: 8px; border-radius: 6px; border-left: 3px solid #3b82f6;">
            <div style="font-weight: 600; color: #fff;">{article['headline']}</div>
            <div style="color: #888; font-size: 0.85em; margin-top: 4px;">{article['description']}</div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("No breaking news available")

st.divider()

# ============================================================
# 🏷️ TODAY'S STRONG PICKS
# ============================================================
today_strong = [p for p in st.session_state.strong_picks.get('picks', []) 
                if p.get('sport') == 'NFL' and today_str in p.get('timestamp', '')]

if today_strong:
    st.subheader("🏷️ TODAY'S STRONG PICKS")
    for pick in today_strong:
        ml_num = pick.get('ml_number', 0)
        game_key = pick.get('game', '')
        pick_team = pick.get('pick', '')
        
        # Find current game status
        result_text = "⏳ Pending"
        result_color = "#888"
        for g in games:
            gk = f"{g['away'].get('abbr')}@{g['home'].get('abbr')}"
            if gk == game_key:
                if g['status_type'] == "STATUS_FINAL":
                    home_score = g['home'].get('score', 0)
                    away_score = g['away'].get('score', 0)
                    home_abbr = g['home'].get('abbr')
                    winner = home_abbr if home_score > away_score else g['away'].get('abbr')
                    if winner == pick_team:
                        result_text = f"✅ WIN ({away_score}-{home_score})"
                        result_color = "#22c55e"
                    else:
                        result_text = f"❌ LOSS ({away_score}-{home_score})"
                        result_color = "#ef4444"
                elif g['status_type'] == "STATUS_IN_PROGRESS":
                    result_text = f"🔴 LIVE Q{g.get('quarter', 0)}"
                    result_color = "#f59e0b"
                break
        
        st.markdown(f"""
        <div style="background: #0f172a; padding: 12px 16px; border-radius: 8px; margin-bottom: 8px; border-left: 4px solid {result_color};">
            <span style="color: #ffd700; font-weight: bold;">ML-{ml_num:03d}</span>
            <span style="color: #fff; margin-left: 12px; font-weight: 600;">{pick_team}</span>
            <span style="color: #666; margin-left: 8px;">({game_key})</span>
            <span style="color: {result_color}; float: right;">{result_text}</span>
        </div>
        """, unsafe_allow_html=True)
    st.divider()

# ============================================================
# 🎯 ML PICKS
# ============================================================
if week_info:
    st.subheader(f"🎯 ML PICKS")
else:
    st.subheader("🎯 ML PICKS")

if games:
    ml_results = []
    for g in games:
        home_abbr = g["home"].get("abbr", "")
        away_abbr = g["away"].get("abbr", "")
        if not home_abbr or not away_abbr:
            continue
        
        pick, score, reasons, is_home = calc_ml_score(home_abbr, away_abbr, injuries)
        tier_label, tier_color = get_signal_tier(score)
        opponent = away_abbr if is_home else home_abbr
        
        game_dt = None
        try:
            game_dt = datetime.fromisoformat(g["game_date"].replace("Z", "+00:00"))
            game_dt = game_dt.astimezone(eastern)
        except:
            pass
        
        game_key = f"{away_abbr}@{home_abbr}"
        
        # Build game_data for Strong Pick check
        game_data = {
            "home_abbr": home_abbr,
            "away_abbr": away_abbr,
            "home_score": g["home"].get("score", 0),
            "away_score": g["away"].get("score", 0),
            "status_type": g["status_type"],
            "quarter": g.get("quarter", 0)
        }
        
        # Check Strong Pick eligibility
        is_tracked = score >= 10.0
        strong_eligible, block_reasons, gate_results = check_strong_pick_eligible(
            game_key, pick, game_data, injuries
        )
        
        ml_results.append({
            "pick": pick, "opponent": opponent, "score": score,
            "tier_label": tier_label, "tier_color": tier_color,
            "reasons": reasons, "is_home": is_home,
            "status_type": g["status_type"], "status_detail": g["status_detail"],
            "game_dt": game_dt, "home_abbr": home_abbr, "away_abbr": away_abbr,
            "home_score": g["home"].get("score", 0), "away_score": g["away"].get("score", 0),
            "quarter": g.get("quarter", 0), "clock": g.get("clock", ""),
            "game_key": game_key, "is_tracked": is_tracked,
            "strong_eligible": strong_eligible, "block_reasons": block_reasons,
            "gate_results": gate_results
        })
    
    ml_results.sort(key=lambda x: x["score"], reverse=True)
    
    for r in ml_results:
        if r["score"] < 5.5:
            continue
        
        if r["status_type"] == "STATUS_FINAL":
            status_html = '<span style="background:#374151;color:#9ca3af;padding:2px 8px;border-radius:4px;font-size:0.75em;margin-left:10px;">FINAL</span>'
        elif r["status_type"] == "STATUS_IN_PROGRESS":
            status_html = f'<span style="background:#dc2626;color:#fff;padding:2px 8px;border-radius:4px;font-size:0.75em;margin-left:10px;">🔴 Q{r["quarter"]} {r["clock"]}</span>'
        else:
            status_html = '<span style="background:#1d4ed8;color:#fff;padding:2px 8px;border-radius:4px;font-size:0.75em;margin-left:10px;">📅 PRE</span>'
        
        reasons_html = ""
        for reason in r["reasons"]:
            reasons_html += f'<span style="color:#9ca3af;margin-right:8px;">{reason}</span>'
        
        pick_form = TEAM_STATS.get(r["pick"], {}).get("form", "")
        form_html = format_form(pick_form)
        
        kalshi_url = build_kalshi_url(r["away_abbr"], r["home_abbr"], r["game_dt"])
        
        # Check for existing tag
        existing_tag = get_strong_pick_for_game(r["game_key"])
        tag_html = ""
        if existing_tag:
            tag_html = f'<span style="background:#ffd700;color:#000;padding:2px 8px;border-radius:4px;font-size:0.75em;margin-left:10px;">ML-{existing_tag["ml_number"]:03d}</span>'
        
        st.markdown(f"""
        <div style="display: flex; align-items: center; justify-content: space-between; background: linear-gradient(135deg, #0f172a, #020617); padding: 14px 18px; margin-bottom: 10px; border-radius: 10px; border-left: 4px solid {r['tier_color']};">
            <div style="flex: 1;">
                <span style="background:{r['tier_color']}22;color:{r['tier_color']};padding:3px 10px;border-radius:4px;font-weight:600;font-size:0.85em;">{r['tier_label'].split()[0]}</span>
                <span style="font-weight: bold; color: #fff; font-size: 1.15em; margin-left: 12px;">{r['pick']}</span>
                <span style="color: #666;"> v {r['opponent']}</span>
                <span style="color: {r['tier_color']}; font-weight: bold; margin-left: 12px;">{r['score']}</span>
                {status_html}{tag_html}
                <br>
                <span style="margin-top: 6px; display: inline-block;">{reasons_html}</span>
                <span style="color: #555; margin-left: 10px;">{form_html}</span>
            </div>
            <a href="{kalshi_url}" target="_blank" style="text-decoration: none;">
                <button style="background: linear-gradient(135deg, #16a34a, #15803d); color: white; padding: 10px 20px; border: none; border-radius: 8px; font-weight: 600; cursor: pointer; font-size: 0.95em;">
                    BUY
                </button>
            </a>
        </div>
        """, unsafe_allow_html=True)
        
        # Strong Pick Button
        if r["is_tracked"] and r["strong_eligible"] and not existing_tag and r["status_type"] != "STATUS_FINAL":
            if st.button(f"➕ Add Strong Pick", key=f"strong_{r['game_key']}", use_container_width=True):
                ml_num = add_strong_pick(r["game_key"], r["pick"], "NFL")
                st.success(f"✅ Tagged ML-{ml_num:03d}: {r['pick']} ({r['game_key']})")
                st.rerun()
        elif r["is_tracked"] and not r["strong_eligible"] and not existing_tag:
            st.markdown(f"<div style='color:#ff6666;font-size:0.75em;margin-bottom:8px;margin-left:14px'>⚠️ Strong Pick blocked: {', '.join(r['block_reasons'])}</div>", unsafe_allow_html=True)
    
    tossups = [r for r in ml_results if r["score"] < 5.5]
    if tossups:
        with st.expander(f"⚪ TOSS-UPS ({len(tossups)} games)", expanded=False):
            for r in tossups:
                st.caption(f"{r['away_abbr']} @ {r['home_abbr']} — No clear edge")
else:
    st.info("No games scheduled for today. Showing upcoming week preview.")
    
    st.markdown("### 🏆 POWER RANKINGS")
    sorted_teams = sorted(TEAM_STATS.items(), key=lambda x: x[1].get('rank', 99))
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**TOP 10**")
        for abbr, stats in sorted_teams[:10]:
            rank = stats.get('rank', 99)
            form_html = format_form(stats.get('form', ''))
            st.markdown(f"{rank}. **{abbr}** ({stats.get('record', '')}) {form_html}", unsafe_allow_html=True)
    
    with col2:
        st.markdown("**MIDDLE 12**")
        for abbr, stats in sorted_teams[10:22]:
            rank = stats.get('rank', 99)
            st.markdown(f"{rank}. **{abbr}** ({stats.get('record', '')})", unsafe_allow_html=True)
    
    with col3:
        st.markdown("**BOTTOM 10**")
        for abbr, stats in sorted_teams[22:]:
            rank = stats.get('rank', 99)
            form_html = format_form(stats.get('form', ''))
            st.markdown(f"{rank}. **{abbr}** ({stats.get('record', '')}) {form_html}", unsafe_allow_html=True)

st.divider()

# ============================================================
# 📅 SCHEDULED GAMES
# ============================================================
st.subheader(f"📅 {week_info.upper() if week_info else 'SCHEDULED GAMES'}")

if games:
    cols = st.columns(3)
    for idx, g in enumerate(games):
        with cols[idx % 3]:
            home = g["home"]
            away = g["away"]
            home_form = format_form(TEAM_STATS.get(home.get("abbr", ""), {}).get("form", ""))
            away_form = format_form(TEAM_STATS.get(away.get("abbr", ""), {}).get("form", ""))
            
            game_time = ""
            try:
                gdt = datetime.fromisoformat(g["game_date"].replace("Z", "+00:00")).astimezone(eastern)
                game_time = gdt.strftime("%a %I:%M %p")
            except:
                pass
            
            if g["status_type"] == "STATUS_FINAL":
                score_line = f"{away.get('score', 0)} - {home.get('score', 0)}"
                status_badge = "FINAL"
            elif g["status_type"] == "STATUS_IN_PROGRESS":
                score_line = f"{away.get('score', 0)} - {home.get('score', 0)}"
                status_badge = f"Q{g.get('quarter', 0)} {g.get('clock', '')}"
            else:
                score_line = "vs"
                status_badge = game_time
            
            st.markdown(f"""
            <div style="background: #0f172a; padding: 12px; border-radius: 8px; margin-bottom: 10px; text-align: center;">
                <div style="color: #888; font-size: 0.8em; margin-bottom: 6px;">{status_badge}</div>
                <div><span style="font-weight: bold; color: #fff;">{away.get('abbr', '')}</span> <span style="color: #666;">{away.get('record', '')}</span> {away_form}</div>
                <div style="color: #666; margin: 4px 0;">{score_line}</div>
                <div><span style="font-weight: bold; color: #fff;">{home.get('abbr', '')}</span> <span style="color: #666;">{home.get('record', '')}</span> {home_form}</div>
            </div>
            """, unsafe_allow_html=True)
else:
    st.info("No games today. NFL games typically on Sun/Mon/Thu.")
    
    st.markdown("### 🏈 DIVISION STANDINGS")
    DIVISIONS = {
        "AFC East": ["BUF", "MIA", "NYJ", "NE"],
        "AFC North": ["BAL", "PIT", "CIN", "CLE"],
        "AFC South": ["HOU", "IND", "JAX", "TEN"],
        "AFC West": ["KC", "LAC", "DEN", "LV"],
        "NFC East": ["PHI", "WAS", "DAL", "NYG"],
        "NFC North": ["DET", "MIN", "GB", "CHI"],
        "NFC South": ["TB", "ATL", "NO", "CAR"],
        "NFC West": ["LAR", "SEA", "SF", "ARI"]
    }
    
    cols = st.columns(4)
    for idx, (div_name, teams) in enumerate(DIVISIONS.items()):
        with cols[idx % 4]:
            st.markdown(f"**{div_name}**")
            sorted_div = sorted(teams, key=lambda t: TEAM_STATS.get(t, {}).get('rank', 99))
            for team in sorted_div:
                record = TEAM_STATS.get(team, {}).get('record', '')
                form = format_form(TEAM_STATS.get(team, {}).get('form', ''))
                st.markdown(f"{team} ({record}) {form}", unsafe_allow_html=True)

st.divider()

# ============================================================
# 🏥 INJURY REPORT
# ============================================================
st.subheader("🏥 INJURY REPORT")

teams_playing = set(TEAM_STATS.keys())

injury_shown = False
cols = st.columns(4)
col_idx = 0

for team in sorted(teams_playing):
    team_inj = injuries.get(team, [])
    key_out = [i for i in team_inj if 'out' in i.get('status', '').lower()][:5]
    if key_out:
        with cols[col_idx % 4]:
            st.markdown(f"**{team}**")
            for inj in key_out:
                pos = inj.get('pos', '')
                pos_color = "#ef4444" if pos in ["QB", "RB"] else "#888"
                st.markdown(f'<span style="color:{pos_color};">🔴 {inj["name"]} ({pos})</span>', unsafe_allow_html=True)
        col_idx += 1
        injury_shown = True

if not injury_shown:
    st.info("✅ No major injuries reported for this week's teams")

st.divider()

# ============================================================
# 📖 LEGEND
# ============================================================
with st.expander("📖 How to Use This App", expanded=False):
    st.markdown("""
**Signal Tiers:**
- 🔒 **STRONG (10.0)** — Highest confidence, eligible for Strong Pick tagging
- 🔵 **BUY (8.0-9.9)** — Good edge detected
- 🟡 **LEAN (5.5-7.9)** — Slight edge
- ⚪ **PASS (Below 5.5)** — No clear edge, avoid

**Strong Pick System (3 Gates):**
Only 🔒 STRONG picks can become Strong Picks, and they must pass ALL 3 gates:
1. **🛡️ Cushion Gate** — Must be WIDE (10+ pt power advantage pre-game, or 7+ pt lead live)
2. **⏱️ Pace Gate** — Must be CONTROLLED/NEUTRAL (not Q4 within 7 pts)
3. **🔬 Match Gate** — Must be STABLE/VOLATILE (no coin flips, key injuries OK)

**Key Indicators:**
- 📊 **PWR** — Power rating differential
- 🏟️ **Home** — Home field advantage percentage
- 🏆 **PWR** — Power ranking position
- 🔥 **Hot** — Team on winning streak (4+ wins in last 5)
- 🏥 **OUT** — Key players (QB/RB) injured
- 🌧️ **Weather** — Severe conditions favor home team

**Trading:**
Click BUY to open the Kalshi market for that game.
""")

st.divider()
st.caption(f"⚠️ Educational only. Not financial advice. v{VERSION}")
