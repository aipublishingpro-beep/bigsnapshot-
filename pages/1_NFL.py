import streamlit as st

st.set_page_config(page_title="NFL Edge Finder", page_icon="🏈", layout="wide")

# ============================================================
# 🔐 AUTH CHECK — MUST BE FIRST AFTER PAGE CONFIG
# ============================================================
from auth import require_auth
require_auth()

import requests
import json
import os
import time
from datetime import datetime, timedelta
import pytz
from styles import apply_styles

apply_styles()

VERSION = "19.0"

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
if "last_ball_positions" not in st.session_state:
    st.session_state.last_ball_positions = {}

def get_next_ml_number():
    return st.session_state.strong_picks.get("next_ml", 1)

def add_strong_pick(game_key, pick_team, sport, price=50):
    ml_num = st.session_state.strong_picks.get("next_ml", 1)
    pick_data = {
        "ml_number": ml_num, "game": game_key, "pick": pick_team,
        "price": price, "timestamp": datetime.now(pytz.timezone('US/Eastern')).isoformat(), "sport": sport
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
# TEAM STATS
# ============================================================
TEAM_STATS = {
    "ARI": {"pwr": -5.0, "rank": 22, "home_win": 0.45, "record": "6-11", "form": "LWLLL"},
    "ATL": {"pwr": -3.5, "rank": 20, "home_win": 0.48, "record": "7-10", "form": "WLLWL"},
    "BAL": {"pwr": 0.5, "rank": 17, "home_win": 0.50, "record": "4-5", "form": "WWWLL"},
    "BUF": {"pwr": 8.5, "rank": 8, "home_win": 0.68, "record": "10-7", "form": "WWLWL"},
    "CAR": {"pwr": 4.0, "rank": 13, "home_win": 0.55, "record": "10-7", "form": "WLWWL"},
    "CHI": {"pwr": 12.0, "rank": 4, "home_win": 0.72, "record": "12-5", "form": "WWLWW"},
    "CIN": {"pwr": -2.0, "rank": 19, "home_win": 0.48, "record": "3-6", "form": "LLWLL"},
    "CLE": {"pwr": -12.0, "rank": 30, "home_win": 0.35, "record": "2-7", "form": "LLLLL"},
    "DAL": {"pwr": -1.5, "rank": 18, "home_win": 0.50, "record": "3-5-1", "form": "LLWDL"},
    "DEN": {"pwr": 18.0, "rank": 1, "home_win": 0.82, "record": "14-3", "form": "WWWWW"},
    "DET": {"pwr": 2.0, "rank": 16, "home_win": 0.55, "record": "8-9", "form": "LWLLW"},
    "GB": {"pwr": 6.5, "rank": 10, "home_win": 0.62, "record": "10-7", "form": "WLWWL"},
    "HOU": {"pwr": 7.5, "rank": 9, "home_win": 0.65, "record": "10-7", "form": "WWLWW"},
    "IND": {"pwr": 5.0, "rank": 12, "home_win": 0.72, "record": "8-2", "form": "WWWWL"},
    "JAX": {"pwr": 6.0, "rank": 11, "home_win": 0.58, "record": "10-7", "form": "WLWLW"},
    "KC": {"pwr": -0.5, "rank": 15, "home_win": 0.52, "record": "5-4", "form": "LLWLW"},
    "LV": {"pwr": -8.0, "rank": 26, "home_win": 0.40, "record": "2-7", "form": "LLLLW"},
    "LAC": {"pwr": 8.0, "rank": 7, "home_win": 0.62, "record": "7-3", "form": "WWWLW"},
    "LAR": {"pwr": 10.0, "rank": 6, "home_win": 0.65, "record": "11-6", "form": "WLWWW"},
    "MIA": {"pwr": -6.0, "rank": 23, "home_win": 0.42, "record": "3-7", "form": "LLLWL"},
    "MIN": {"pwr": 3.0, "rank": 14, "home_win": 0.55, "record": "8-9", "form": "LWLWL"},
    "NE": {"pwr": 15.0, "rank": 2, "home_win": 0.75, "record": "14-3", "form": "WWWWW"},
    "NO": {"pwr": -7.5, "rank": 25, "home_win": 0.42, "record": "4-13", "form": "LLLWL"},
    "NYG": {"pwr": -10.0, "rank": 28, "home_win": 0.38, "record": "3-7", "form": "LLWLL"},
    "NYJ": {"pwr": -9.0, "rank": 27, "home_win": 0.38, "record": "2-8", "form": "LLLLL"},
    "PHI": {"pwr": 11.0, "rank": 5, "home_win": 0.70, "record": "7-2", "form": "WWWLW"},
    "PIT": {"pwr": 3.5, "rank": 13, "home_win": 0.58, "record": "5-4", "form": "LWWLL"},
    "SF": {"pwr": 5.5, "rank": 11, "home_win": 0.55, "record": "8-9", "form": "LWWLW"},
    "SEA": {"pwr": 16.0, "rank": 3, "home_win": 0.78, "record": "14-3", "form": "WWWWW"},
    "TB": {"pwr": 4.5, "rank": 14, "home_win": 0.58, "record": "10-7", "form": "WWLWW"},
    "TEN": {"pwr": -14.0, "rank": 31, "home_win": 0.35, "record": "1-8", "form": "LLLLL"},
    "WAS": {"pwr": -6.5, "rank": 24, "home_win": 0.45, "record": "3-7", "form": "LLLLL"}
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
# 🏈 FOOTBALL FIELD VISUALIZATION
# ============================================================
def detect_scoring_play(last_play):
    if not last_play:
        return False, None, None
    play_text = (last_play.get("text", "") or "").lower()
    scoring_type = last_play.get("scoringType", {})
    if scoring_type:
        score_name = scoring_type.get("name", "").lower()
        if "touchdown" in score_name:
            return True, "touchdown", "🏈"
        elif "field goal" in score_name:
            return True, "field_goal", "🥅"
        elif "safety" in score_name:
            return True, "safety", "⚡"
    if "touchdown" in play_text or " td " in play_text or play_text.startswith("td "):
        return True, "touchdown", "🏈"
    elif "field goal" in play_text or "fg good" in play_text:
        return True, "field_goal", "🥅"
    elif "safety" in play_text:
        return True, "safety", "⚡"
    return False, None, None

def get_smart_ball_position(game_data, game_key):
    poss_text = game_data.get("poss_text", "")
    possession_team = game_data.get("possession_team")
    home_team = game_data.get("home_abbr") or game_data.get("home_team")
    away_team = game_data.get("away_abbr") or game_data.get("away_team")
    home_abbrev = game_data.get("home_abbrev", home_team)
    away_abbrev = game_data.get("away_abbrev", away_team)
    is_home_possession = game_data.get("is_home_possession")
    yards_to_endzone = game_data.get("yards_to_endzone")
    last_play = game_data.get("last_play")
    period = game_data.get("period", 0) or game_data.get("quarter", 0)
    clock = game_data.get("clock", "")

    last_known = st.session_state.last_ball_positions.get(game_key, {})

    # CASE 1: Parse poss_text like "LAR 24"
    if poss_text and " " in poss_text:
        parts = poss_text.split()
        if len(parts) >= 2:
            try:
                side_team = parts[0].upper()
                yard_line = int(parts[1])
                ball_yard = 50

                if side_team == home_abbrev.upper():
                    ball_yard = 100 - yard_line
                elif side_team == away_abbrev.upper():
                    ball_yard = yard_line
                else:
                    if is_home_possession is not None and yards_to_endzone is not None:
                        ball_yard = yards_to_endzone if is_home_possession else 100 - yards_to_endzone
                    else:
                        ball_yard = last_known.get('ball_yard', 50)

                st.session_state.last_ball_positions[game_key] = {
                    'ball_yard': ball_yard, 'poss_team': possession_team, 'poss_text': poss_text
                }
                return ball_yard, "normal", possession_team, poss_text
            except (ValueError, IndexError):
                pass

    # CASE 2: Scoring play
    is_scoring, score_type, _ = detect_scoring_play(last_play)
    if is_scoring:
        if last_known.get('poss_team'):
            scoring_team = last_known.get('poss_team')
            ball_yard = 0 if scoring_team == home_team else 100
        else:
            last_yard = last_known.get('ball_yard', 50)
            ball_yard = 0 if last_yard < 50 else 100
        score_emoji = "🏈" if score_type == "touchdown" else "🥅" if score_type == "field_goal" else "⚡"
        return ball_yard, "scoring", None, f"{score_emoji} {score_type.upper().replace('_', ' ')}"

    # CASE 3: Kickoff/punt
    if last_play:
        play_text = (last_play.get("text", "") or "").lower()
        if "kickoff" in play_text or "kicks off" in play_text:
            return 65, "kickoff", None, "⚡ KICKOFF"
        elif "punts" in play_text:
            return 50, "between_plays", None, "📤 PUNT"

    # CASE 4: Game in progress, use last known
    if period > 0:
        if clock == "0:00":
            return last_known.get('ball_yard', 50), "between_plays", None, "⏱️ End of Quarter"
        if last_known.get('ball_yard') is not None:
            return last_known.get('ball_yard'), "between_plays", last_known.get('poss_team'), "Between Plays"

    # CASE 5: Default
    return 50, "between_plays", None, ""

def render_football_field(ball_yard, down, distance, possession_team, away_team, home_team,
                          yards_to_endzone=None, poss_text=None, display_mode="normal"):
    away_code = KALSHI_CODES.get(away_team, away_team[:3].upper() if away_team else "AWY")
    home_code = KALSHI_CODES.get(home_team, home_team[:3].upper() if home_team else "HME")

    if display_mode == "scoring":
        situation = poss_text or "🏈 SCORE!"
        poss_code = "—"
        ball_loc = ""
        direction = ""
        ball_style = "font-size:28px;text-shadow:0 0 20px #ffff00"
    elif display_mode == "kickoff":
        situation = poss_text or "⚡ KICKOFF"
        poss_code = "—"
        ball_loc = ""
        direction = ""
        ball_style = "font-size:24px;text-shadow:0 0 10px #fff"
    elif display_mode == "between_plays" or not possession_team:
        situation = poss_text if poss_text else "Between Plays"
        poss_code = "—"
        ball_loc = ""
        direction = ""
        ball_style = "font-size:24px;opacity:0.6;text-shadow:0 0 10px #fff"
    else:
        situation = f"{down} & {distance}" if down and distance else "—"
        poss_code = KALSHI_CODES.get(possession_team, possession_team[:3].upper() if possession_team else "???")
        ball_loc = poss_text if poss_text else ""
        is_home_poss = possession_team == home_team
        direction = "◀" if is_home_poss else "▶"
        ball_style = "font-size:24px;text-shadow:0 0 10px #fff"

    # Red zone note
    red_zone_note = ""
    if yards_to_endzone and yards_to_endzone <= 20 and possession_team:
        red_zone_note = ' <span style="color:#ff4444;font-weight:bold;">🔴 RED ZONE</span>'

    poss_display = f"🏈 {poss_code.upper()} Ball {direction}" if poss_code != "—" else f"🏈 {situation}"

    ball_yard = max(0, min(100, ball_yard))
    ball_pct = 10 + (ball_yard / 100) * 80

    return f"""<div style="background:#1a1a1a;padding:15px;border-radius:10px;margin:10px 0">
<div style="text-align:center;margin-bottom:10px;font-size:1.1em">
<span style="color:#00ff00;font-weight:bold">{poss_display}</span>{red_zone_note}</div>
<div style="display:flex;justify-content:space-between;margin-bottom:8px">
<span style="color:#aaa">{ball_loc}</span>
<span style="color:#fff;font-weight:bold">{situation}</span></div>
<div style="position:relative;height:60px;background:linear-gradient(90deg,#8B0000 0%,#8B0000 10%,#228B22 10%,#228B22 90%,#00008B 90%,#00008B 100%);border-radius:8px;overflow:hidden">
<div style="position:absolute;left:10%;top:0;bottom:0;width:1px;background:rgba(255,255,255,0.3)"></div>
<div style="position:absolute;left:20%;top:0;bottom:0;width:1px;background:rgba(255,255,255,0.3)"></div>
<div style="position:absolute;left:30%;top:0;bottom:0;width:1px;background:rgba(255,255,255,0.3)"></div>
<div style="position:absolute;left:40%;top:0;bottom:0;width:1px;background:rgba(255,255,255,0.3)"></div>
<div style="position:absolute;left:50%;top:0;bottom:0;width:2px;background:rgba(255,255,255,0.6)"></div>
<div style="position:absolute;left:60%;top:0;bottom:0;width:1px;background:rgba(255,255,255,0.3)"></div>
<div style="position:absolute;left:70%;top:0;bottom:0;width:1px;background:rgba(255,255,255,0.3)"></div>
<div style="position:absolute;left:80%;top:0;bottom:0;width:1px;background:rgba(255,255,255,0.3)"></div>
<div style="position:absolute;left:90%;top:0;bottom:0;width:1px;background:rgba(255,255,255,0.3)"></div>
<div style="position:absolute;left:{ball_pct}%;top:50%;transform:translate(-50%,-50%);{ball_style}">🏈</div>
<div style="position:absolute;left:5%;top:50%;transform:translate(-50%,-50%);color:#fff;font-weight:bold;font-size:14px">{away_code.upper()}</div>
<div style="position:absolute;left:95%;top:50%;transform:translate(-50%,-50%);color:#fff;font-weight:bold;font-size:14px">{home_code.upper()}</div></div>
<div style="display:flex;justify-content:space-between;margin-top:5px;color:#888;font-size:11px">
<span>← {away_code.upper()} EZ</span><span>10</span><span>20</span><span>30</span><span>40</span><span>50</span><span>40</span><span>30</span><span>20</span><span>10</span><span>{home_code.upper()} EZ →</span></div></div>"""

# ============================================================
# STRONG PICK GATE FUNCTIONS
# ============================================================
def get_match_stability(home_abbr, away_abbr, injuries):
    instability_score = 0
    flags = []
    home_out, home_impact = get_injury_impact(home_abbr, injuries)
    away_out, away_impact = get_injury_impact(away_abbr, injuries)
    if home_impact >= 4 or away_impact >= 4:
        instability_score += 2
        flags.append("⚠️ Key OUT")
    home_form = TEAM_STATS.get(home_abbr, {}).get('form', '')
    away_form = TEAM_STATS.get(away_abbr, {}).get('form', '')
    home_streak = len(home_form) - len(home_form.lstrip(home_form[0])) if home_form else 0
    away_streak = len(away_form) - len(away_form.lstrip(away_form[0])) if away_form else 0
    if home_streak >= 5 or away_streak >= 5:
        instability_score += 1
        flags.append("⚠️ Streak Risk")
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
        if lead >= 7:
            return "🟢 WIDE", "#00ff00", True
        elif lead >= 0:
            return "🟡 NARROW", "#ffaa00", False
        else:
            return "🔴 NEGATIVE", "#ff4444", False

def get_pace_direction(game_data):
    if game_data.get('status_type') == "STATUS_SCHEDULED":
        return "🟢 CONTROLLED", "#00ff00", True
    quarter = game_data.get('quarter', 0)
    home_score = game_data.get('home_score', 0)
    away_score = game_data.get('away_score', 0)
    diff = abs(home_score - away_score)
    if quarter >= 4 and diff <= 7:
        return "🔴 NEGATIVE", "#ff4444", False
    elif quarter >= 3:
        return "🟡 NEUTRAL", "#ffaa00", True
    else:
        return "🟢 CONTROLLED", "#00ff00", True

def check_strong_pick_eligible(game_key, pick_team, game_data, injuries):
    home_abbr = game_data.get('home_abbr')
    away_abbr = game_data.get('away_abbr')
    stability_label, stability_color, is_stable, stability_flags = get_match_stability(home_abbr, away_abbr, injuries)
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
# ESPN API FUNCTIONS (ENHANCED - with possession/field data)
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
            event_id = event.get("id", "")
            comp = event.get("competitions", [{}])[0]
            competitors = comp.get("competitors", [])
            if len(competitors) < 2:
                continue

            home_team, away_team = {}, {}
            home_id, away_id = "", ""
            home_abbrev, away_abbrev = "", ""
            for c in competitors:
                full_name = c.get("team", {}).get("displayName", "")
                abbr = TEAM_ABBREVS.get(full_name, c.get("team", {}).get("abbreviation", ""))
                espn_abbr = c.get("team", {}).get("abbreviation", abbr)
                score = int(c.get("score", 0) or 0)
                team_id = c.get("team", {}).get("id", "")
                record = ""
                if c.get("records"):
                    record = c["records"][0].get("summary", "")
                team_data = {
                    "name": full_name, "abbr": abbr, "score": score, "record": record,
                    "team_id": team_id, "espn_abbr": espn_abbr
                }
                if c.get("homeAway") == "home":
                    home_team = team_data
                    home_id = team_id
                    home_abbrev = espn_abbr
                else:
                    away_team = team_data
                    away_id = team_id
                    away_abbrev = espn_abbr

            status_obj = event.get("status", {})
            status_type = status_obj.get("type", {}).get("name", "STATUS_SCHEDULED")
            status_detail = status_obj.get("type", {}).get("shortDetail", "")
            clock = status_obj.get("displayClock", "")
            period = status_obj.get("period", 0)
            game_date_str = event.get("date", "")

            # Extract possession/field data from situation
            situation = comp.get("situation", {})
            possession_id = str(situation.get("possession", ""))
            down = situation.get("down", 0)
            distance = situation.get("distance", 0)
            yards_to_endzone = situation.get("yardLine", 0)
            is_red_zone = situation.get("isRedZone", False)
            poss_text = situation.get("possessionText", "")
            last_play = situation.get("lastPlay", {})

            possession_team = None
            is_home_possession = None
            if possession_id == home_id:
                possession_team = home_team.get("abbr")
                is_home_possession = True
            elif possession_id == away_id:
                possession_team = away_team.get("abbr")
                is_home_possession = False

            games.append({
                "event_id": event_id,
                "home": home_team, "away": away_team,
                "home_id": home_id, "away_id": away_id,
                "home_abbrev": home_abbrev, "away_abbrev": away_abbrev,
                "status_type": status_type, "status_detail": status_detail,
                "clock": clock, "quarter": period, "game_date": game_date_str,
                "possession_team": possession_team, "is_home_possession": is_home_possession,
                "down": down, "distance": distance, "yards_to_endzone": yards_to_endzone,
                "is_red_zone": is_red_zone, "poss_text": poss_text, "last_play": last_play
            })

        return games, week_info, season_type
    except Exception as e:
        return [], "", ""

@st.cache_data(ttl=60)
def fetch_play_by_play(event_id):
    url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/summary?event={event_id}"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        all_plays = []
        if "plays" in data:
            all_plays = data.get("plays", [])
        if not all_plays and "drives" in data:
            drives = data.get("drives", {})
            for drive in drives.get("previous", []):
                all_plays.extend(drive.get("plays", []))
            current = drives.get("current", {})
            if current:
                all_plays.extend(current.get("plays", []))
        if not all_plays:
            return []
        recent = list(reversed(all_plays[-5:] if len(all_plays) >= 5 else all_plays))
        plays = []
        for play in recent:
            play_text = play.get("text", "") or play.get("description", "") or ""
            is_scoring = play.get("scoringPlay", False)
            period_data = play.get("period", {})
            period = period_data.get("number", 0) if isinstance(period_data, dict) else (period_data or 0)
            clock_data = play.get("clock", {})
            clock = clock_data.get("displayValue", "") if isinstance(clock_data, dict) else str(clock_data or "")
            text_lower = play_text.lower()
            if is_scoring or "touchdown" in text_lower: icon = "🏈"
            elif "intercept" in text_lower or "fumble" in text_lower: icon = "🔴"
            elif "field goal" in text_lower: icon = "🥅"
            elif "punt" in text_lower or "kickoff" in text_lower: icon = "📤"
            elif "sack" in text_lower: icon = "💥"
            elif "incomplete" in text_lower: icon = "❌"
            elif "pass" in text_lower: icon = "🎯"
            elif any(x in text_lower for x in ["rush", "run ", "middle", "tackle", "guard", "end", "scramble"]): icon = "🏃"
            elif "kneel" in text_lower: icon = "🧎"
            elif "penalty" in text_lower: icon = "🚩"
            else: icon = "▶️"
            if play_text:
                plays.append({"text": play_text[:100] + "..." if len(play_text) > 100 else play_text,
                    "scoring": is_scoring, "period": period, "clock": clock, "icon": icon})
        return plays
    except:
        return []

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
    st.markdown(f"**Next ML#:** ML-{get_next_ml_number():03d}\n**Today's Tags:** {today_tags}")
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
            <span style="font-size: 1.4em; font-weight: bold; color: #ffd700;">🏆 SUPER BOWL LX</span><br>
            <span style="color: #fff; font-size: 1.1em;">February 8, 2026 • 6:30 PM ET</span><br>
            <span style="color: #aaa;">Levi's Stadium • Santa Clara, CA</span><br>
            <span style="color: #fff; font-size: 1.05em; margin-top: 6px; display: inline-block;">🦅 <b>SEA Seahawks (14-3)</b> vs <b>NE Patriots (14-3)</b> 🏴‍☠️</span><br>
            <span style="color: #ffd700;">SEA -4.5 • O/U 45.5 • NBC/Peacock</span>
        </div>
        <div style="text-align: right;">
            <span style="color: #888; font-size: 0.9em;">CONFERENCE CHAMPIONSHIPS</span><br>
            <span style="color: #fff;">NFC: SEA 41, SF 6</span><br>
            <span style="color: #fff;">AFC: NE 10, DEN 7</span><br>
            <span style="color: #aaa; font-size: 0.85em;">Halftime: Bad Bunny 🎶</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div style="background: #0f172a; padding: 15px 20px; border-radius: 10px; margin-bottom: 15px;">
    <div style="font-weight: bold; color: #3b82f6; margin-bottom: 10px;">🔵 AFC PLAYOFF BRACKET</div>
    <div style="display: flex; gap: 20px; flex-wrap: wrap; color: #ccc; font-size: 0.95em;">
        <div><span style="color: #ffd700;">1.</span> DEN (14-3) — BYE → W 33-30 OT vs BUF → <span style="color:#ef4444;">L 7-10 vs NE</span></div>
        <div><span style="color: #c0c0c0;">2.</span> <b style="color:#22c55e;">NE (14-3)</b> — W 16-3 vs LAC → W 28-16 vs HOU → <span style="color:#22c55e;">W 10-7 vs DEN → 🏆 SB LX</span></div>
        <div>3. JAX — L 24-27 vs BUF</div>
        <div>4. PIT — L 6-30 vs HOU</div>
        <div>5. HOU — W 30-6 vs PIT → L 16-28 vs NE</div>
        <div>6. BUF — W 27-24 vs JAX → L 30-33 OT vs DEN</div>
        <div>7. LAC — L 3-16 vs NE</div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div style="background: #0f172a; padding: 15px 20px; border-radius: 10px; margin-bottom: 15px;">
    <div style="font-weight: bold; color: #ef4444; margin-bottom: 10px;">🔴 NFC PLAYOFF BRACKET</div>
    <div style="display: flex; gap: 20px; flex-wrap: wrap; color: #ccc; font-size: 0.95em;">
        <div><span style="color: #ffd700;">1.</span> <b style="color:#22c55e;">SEA (14-3)</b> — BYE → W 31-27 vs LAR → <span style="color:#22c55e;">W 41-6 vs SF → 🏆 SB LX</span></div>
        <div><span style="color: #c0c0c0;">2.</span> CHI (12-5) — W 31-27 vs GB → L vs SF</div>
        <div>3. PHI — L vs SF</div>
        <div>4. CAR — L 31-34 vs LAR</div>
        <div>5. LAR — W 34-31 vs CAR → L 27-31 vs SEA</div>
        <div>6. SF — W vs PHI → W vs CHI → <span style="color:#ef4444;">L 6-41 vs SEA</span></div>
        <div>7. GB — L 27-31 vs CHI</div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div style="background: #1e293b; padding: 12px 18px; border-radius: 8px; margin-bottom: 15px;">
    <span style="font-weight: bold; color: #fff;">📅 RESULTS</span>
    <span style="color: #888; margin-left: 20px;">Wild Card: Jan 10-12 ✅</span>
    <span style="color: #888; margin-left: 15px;">Divisional: Jan 17-18 ✅</span>
    <span style="color: #888; margin-left: 15px;">Conf Champ: Jan 25 ✅</span>
    <span style="color: #ffd700; margin-left: 15px; font-weight: bold;">Super Bowl LX: Feb 8 — SEA vs NE</span>
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
# 🏈 LIVE GAMES — FOOTBALL FIELD + PLAY-BY-PLAY
# ============================================================
live_games = [g for g in games if g.get("status_type") == "STATUS_IN_PROGRESS"]

if live_games:
    st.subheader("🔴 LIVE GAMES")
    for g in live_games:
        home_abbr = g["home"].get("abbr", "")
        away_abbr = g["away"].get("abbr", "")
        game_key = f"{away_abbr}@{home_abbr}"

        st.markdown(f"""
        <div style="background:#0f172a;padding:12px 16px;border-radius:8px;border-left:4px solid #dc2626;margin-bottom:5px;">
            <span style="font-weight:bold;color:#fff;font-size:1.1em;">{away_abbr} {g['away'].get('score',0)}</span>
            <span style="color:#666;margin:0 8px;">@</span>
            <span style="font-weight:bold;color:#fff;font-size:1.1em;">{home_abbr} {g['home'].get('score',0)}</span>
            <span style="background:#dc2626;color:#fff;padding:2px 8px;border-radius:4px;font-size:0.75em;margin-left:12px;">🔴 Q{g.get('quarter',0)} {g.get('clock','')}</span>
        </div>
        """, unsafe_allow_html=True)

        # Build game_data for ball position
        game_data_field = {
            "home_abbr": home_abbr, "away_abbr": away_abbr,
            "home_abbrev": g.get("home_abbrev", home_abbr),
            "away_abbrev": g.get("away_abbrev", away_abbr),
            "home_team": home_abbr, "away_team": away_abbr,
            "possession_team": g.get("possession_team"),
            "is_home_possession": g.get("is_home_possession"),
            "yards_to_endzone": g.get("yards_to_endzone"),
            "poss_text": g.get("poss_text", ""),
            "last_play": g.get("last_play"),
            "period": g.get("quarter", 0),
            "clock": g.get("clock", "")
        }

        ball_yard, display_mode, poss_team, poss_display = get_smart_ball_position(game_data_field, game_key)

        field_html = render_football_field(
            ball_yard=ball_yard,
            down=g.get("down", 0),
            distance=g.get("distance", 0),
            possession_team=poss_team or g.get("possession_team"),
            away_team=away_abbr,
            home_team=home_abbr,
            yards_to_endzone=g.get("yards_to_endzone"),
            poss_text=poss_display,
            display_mode=display_mode
        )
        st.markdown(field_html, unsafe_allow_html=True)

        # Play-by-play
        event_id = g.get("event_id", "")
        if event_id:
            with st.expander("📋 Recent Plays", expanded=False):
                plays = fetch_play_by_play(event_id)
                if plays:
                    for play in plays:
                        bg = "#1a2e1a" if play.get("scoring") else "#0f172a"
                        st.markdown(f"""
                        <div style="background:{bg};padding:8px 12px;margin-bottom:4px;border-radius:6px;border-left:3px solid {'#22c55e' if play.get('scoring') else '#334155'};">
                            <span style="font-size:1.1em;">{play['icon']}</span>
                            <span style="color:#888;font-size:0.8em;margin-left:6px;">Q{play.get('period',0)} {play.get('clock','')}</span>
                            <span style="color:#ccc;margin-left:8px;font-size:0.85em;">{play['text']}</span>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.caption("No plays available yet")
