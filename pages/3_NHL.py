import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="NHL Edge Finder", page_icon="🏒", layout="wide")

# ============================================================
# GA4 ANALYTICS - MUST BE RIGHT AFTER set_page_config
# ============================================================
components.html("""
<script async src="https://www.googletagmanager.com/gtag/js?id=G-1T35YHHYBC"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-1T35YHHYBC', { send_page_view: true });
</script>
""", height=0)

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
    "Anaheim Ducks": "ANA", "Arizona Coyotes": "ARI", "Boston Bruins": "BOS",
    "Buffalo Sabres": "BUF", "Calgary Flames": "CGY", "Carolina Hurricanes": "CAR",
    "Chicago Blackhawks": "CHI", "Colorado Avalanche": "COL", "Columbus Blue Jackets": "CBJ",
    "Dallas Stars": "DAL", "Detroit Red Wings": "DET", "Edmonton Oilers": "EDM",
    "Florida Panthers": "FLA", "Los Angeles Kings": "LAK", "Minnesota Wild": "MIN",
    "Montreal Canadiens": "MTL", "Nashville Predators": "NSH", "New Jersey Devils": "NJD",
    "New York Islanders": "NYI", "New York Rangers": "NYR", "Ottawa Senators": "OTT",
    "Philadelphia Flyers": "PHI", "Pittsburgh Penguins": "PIT", "San Jose Sharks": "SJS",
    "Seattle Kraken": "SEA", "St. Louis Blues": "STL", "Tampa Bay Lightning": "TBL",
    "Toronto Maple Leafs": "TOR", "Utah Hockey Club": "UTA", "Vancouver Canucks": "VAN",
    "Vegas Golden Knights": "VGK", "Washington Capitals": "WSH", "Winnipeg Jets": "WPG"
}

KALSHI_CODES = {
    "ANA": "ana", "ARI": "ari", "BOS": "bos", "BUF": "buf", "CGY": "cgy",
    "CAR": "car", "CHI": "chi", "COL": "col", "CBJ": "cbj", "DAL": "dal",
    "DET": "det", "EDM": "edm", "FLA": "fla", "LAK": "lak", "MIN": "min",
    "MTL": "mtl", "NSH": "nsh", "NJD": "njd", "NYI": "nyi", "NYR": "nyr",
    "OTT": "ott", "PHI": "phi", "PIT": "pit", "SJS": "sjs", "SEA": "sea",
    "STL": "stl", "TBL": "tbl", "TOR": "tor", "UTA": "uta", "VAN": "van",
    "VGK": "vgk", "WSH": "wsh", "WPG": "wpg"
}

TEAM_FULL_NAMES = {v: k for k, v in TEAM_ABBREVS.items()}

# ============================================================
# TEAM STATS (Updated Jan 2026)
# ============================================================
TEAM_STATS = {
    "ANA": {"win_pct": 0.380, "home_win_pct": 0.420, "goals_for": 2.65, "goals_against": 3.35, "pp_pct": 17.8, "pk_pct": 76.5},
    "BOS": {"win_pct": 0.580, "home_win_pct": 0.650, "goals_for": 3.10, "goals_against": 2.70, "pp_pct": 22.5, "pk_pct": 82.0},
    "BUF": {"win_pct": 0.450, "home_win_pct": 0.500, "goals_for": 2.85, "goals_against": 3.05, "pp_pct": 19.5, "pk_pct": 78.5},
    "CGY": {"win_pct": 0.520, "home_win_pct": 0.580, "goals_for": 2.95, "goals_against": 2.85, "pp_pct": 21.8, "pk_pct": 81.2},
    "CAR": {"win_pct": 0.600, "home_win_pct": 0.680, "goals_for": 3.25, "goals_against": 2.55, "pp_pct": 24.2, "pk_pct": 84.5},
    "CHI": {"win_pct": 0.350, "home_win_pct": 0.400, "goals_for": 2.55, "goals_against": 3.45, "pp_pct": 16.5, "pk_pct": 75.0},
    "COL": {"win_pct": 0.620, "home_win_pct": 0.720, "goals_for": 3.42, "goals_against": 2.65, "pp_pct": 26.8, "pk_pct": 82.5},
    "CBJ": {"win_pct": 0.400, "home_win_pct": 0.450, "goals_for": 2.70, "goals_against": 3.25, "pp_pct": 18.2, "pk_pct": 77.0},
    "DAL": {"win_pct": 0.580, "home_win_pct": 0.650, "goals_for": 3.05, "goals_against": 2.65, "pp_pct": 23.5, "pk_pct": 83.0},
    "DET": {"win_pct": 0.480, "home_win_pct": 0.540, "goals_for": 2.90, "goals_against": 2.95, "pp_pct": 20.5, "pk_pct": 79.5},
    "EDM": {"win_pct": 0.580, "home_win_pct": 0.650, "goals_for": 3.35, "goals_against": 2.85, "pp_pct": 28.5, "pk_pct": 80.5},
    "FLA": {"win_pct": 0.600, "home_win_pct": 0.680, "goals_for": 3.28, "goals_against": 2.72, "pp_pct": 24.5, "pk_pct": 81.2},
    "LAK": {"win_pct": 0.540, "home_win_pct": 0.600, "goals_for": 2.95, "goals_against": 2.78, "pp_pct": 21.0, "pk_pct": 80.0},
    "MIN": {"win_pct": 0.560, "home_win_pct": 0.640, "goals_for": 3.18, "goals_against": 2.75, "pp_pct": 23.5, "pk_pct": 82.8},
    "MTL": {"win_pct": 0.420, "home_win_pct": 0.480, "goals_for": 2.75, "goals_against": 3.15, "pp_pct": 18.8, "pk_pct": 77.5},
    "NSH": {"win_pct": 0.480, "home_win_pct": 0.550, "goals_for": 2.82, "goals_against": 2.92, "pp_pct": 19.8, "pk_pct": 79.0},
    "NJD": {"win_pct": 0.540, "home_win_pct": 0.600, "goals_for": 3.08, "goals_against": 2.92, "pp_pct": 24.2, "pk_pct": 79.5},
    "NYI": {"win_pct": 0.500, "home_win_pct": 0.560, "goals_for": 2.92, "goals_against": 2.88, "pp_pct": 20.8, "pk_pct": 84.2},
    "NYR": {"win_pct": 0.560, "home_win_pct": 0.620, "goals_for": 3.28, "goals_against": 2.72, "pp_pct": 26.2, "pk_pct": 81.8},
    "OTT": {"win_pct": 0.480, "home_win_pct": 0.540, "goals_for": 2.95, "goals_against": 3.05, "pp_pct": 21.5, "pk_pct": 78.0},
    "PHI": {"win_pct": 0.440, "home_win_pct": 0.500, "goals_for": 2.72, "goals_against": 3.18, "pp_pct": 18.5, "pk_pct": 77.2},
    "PIT": {"win_pct": 0.520, "home_win_pct": 0.580, "goals_for": 3.05, "goals_against": 2.88, "pp_pct": 22.8, "pk_pct": 80.1},
    "SJS": {"win_pct": 0.320, "home_win_pct": 0.380, "goals_for": 2.45, "goals_against": 3.55, "pp_pct": 17.2, "pk_pct": 75.8},
    "SEA": {"win_pct": 0.480, "home_win_pct": 0.540, "goals_for": 2.78, "goals_against": 3.05, "pp_pct": 19.5, "pk_pct": 77.8},
    "STL": {"win_pct": 0.480, "home_win_pct": 0.540, "goals_for": 2.88, "goals_against": 2.98, "pp_pct": 20.2, "pk_pct": 78.5},
    "TBL": {"win_pct": 0.560, "home_win_pct": 0.620, "goals_for": 3.15, "goals_against": 2.82, "pp_pct": 25.5, "pk_pct": 81.5},
    "TOR": {"win_pct": 0.580, "home_win_pct": 0.660, "goals_for": 3.22, "goals_against": 2.82, "pp_pct": 25.2, "pk_pct": 80.5},
    "UTA": {"win_pct": 0.420, "home_win_pct": 0.480, "goals_for": 2.68, "goals_against": 3.12, "pp_pct": 18.0, "pk_pct": 76.5},
    "VAN": {"win_pct": 0.500, "home_win_pct": 0.560, "goals_for": 3.05, "goals_against": 3.02, "pp_pct": 22.5, "pk_pct": 79.8},
    "VGK": {"win_pct": 0.600, "home_win_pct": 0.700, "goals_for": 3.35, "goals_against": 2.58, "pp_pct": 25.8, "pk_pct": 83.5},
    "WPG": {"win_pct": 0.620, "home_win_pct": 0.700, "goals_for": 3.38, "goals_against": 2.55, "pp_pct": 24.8, "pk_pct": 82.5},
    "WSH": {"win_pct": 0.540, "home_win_pct": 0.600, "goals_for": 3.02, "goals_against": 2.88, "pp_pct": 21.5, "pk_pct": 78.2},
}

# ============================================================
# HELPER FUNCTIONS
# ============================================================
def build_kalshi_url(away_abbr, home_abbr):
    today = datetime.now(eastern)
    date_str = today.strftime("%y%b%d").upper()
    away_code = KALSHI_CODES.get(away_abbr, away_abbr.lower())
    home_code = KALSHI_CODES.get(home_abbr, home_abbr.lower())
    ticker = f"KXNHLGAME-{date_str}{away_code.upper()}{home_code.upper()}"
    return f"https://kalshi.com/markets/kxnhlgame/{ticker.lower()}"

def get_injury_impact(team_abbr, injuries):
    """Returns (out_count, impact_score)"""
    team_inj = injuries.get(team_abbr, [])
    out_count = len([i for i in team_inj if 'out' in i.get('status', '').lower()])
    return out_count, out_count * 2

# ============================================================
# STRONG PICK GATE FUNCTIONS (NHL-specific thresholds)
# Gates only apply to LIVE games - scheduled games auto-pass
# ============================================================
def get_match_stability(home_abbr, away_abbr, injuries, yesterday_teams):
    """
    NHL Match Stability Check
    Returns: (stability_label, stability_color, is_stable, flags)
    """
    instability_score = 0
    flags = []
    
    # Check injuries (3+ out = unstable)
    home_out, home_impact = get_injury_impact(home_abbr, injuries)
    away_out, away_impact = get_injury_impact(away_abbr, injuries)
    if home_out >= 3 or away_out >= 3:
        instability_score += 2
        flags.append("⚠️ Key OUT")
    
    # Check B2B (both teams B2B = chaos)
    home_b2b = home_abbr in yesterday_teams
    away_b2b = away_abbr in yesterday_teams
    if home_b2b and away_b2b:
        instability_score += 2
        flags.append("⚠️ Both B2B")
    
    # Check coin flip matchups (win% within 5%)
    home_win = TEAM_STATS.get(home_abbr, {}).get('win_pct', 0.5)
    away_win = TEAM_STATS.get(away_abbr, {}).get('win_pct', 0.5)
    if abs(home_win - away_win) < 0.05:
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
    NHL Cushion Tier Check (LIVE GAMES ONLY)
    Returns: (tier_label, tier_color, is_wide)
    """
    home_abbr = game_data.get('home_abbr')
    away_abbr = game_data.get('away_abbr')
    
    # Live: Use actual score
    home_score = game_data.get('home_score', 0)
    away_score = game_data.get('away_score', 0)
    
    if pick_team == home_abbr:
        lead = home_score - away_score
    else:
        lead = away_score - home_score
    
    wide_threshold = 2  # NHL: 2 goals = safe
    
    if lead >= wide_threshold:
        return "🟢 WIDE", "#00ff00", True
    elif lead >= 0:
        return "🟡 NARROW", "#ffaa00", False
    else:
        return "🔴 NEGATIVE", "#ff4444", False

def get_pace_direction(game_data):
    """
    NHL Pace Direction Check (LIVE GAMES ONLY)
    Returns: (pace_label, pace_color, is_positive)
    NHL: P3 with 1 goal or less = NEGATIVE
    """
    period = game_data.get('period', 0)
    home_score = game_data.get('home_score', 0)
    away_score = game_data.get('away_score', 0)
    diff = abs(home_score - away_score)
    
    is_late = period >= 3
    close_threshold = 1  # NHL: 1 goal = danger zone
    
    if is_late and diff <= close_threshold:
        return "🔴 NEGATIVE", "#ff4444", False
    elif period >= 2:
        return "🟡 NEUTRAL", "#ffaa00", True
    else:
        return "🟢 CONTROLLED", "#00ff00", True

def check_strong_pick_eligible(game_key, pick_team, game_data, injuries, yesterday_teams):
    """Check if pick passes all 3 gates for Strong Pick status
    NOTE: Gates only apply to LIVE games. Scheduled games auto-pass."""
    
    # Scheduled games auto-pass - gates only for live games
    if game_data.get('status_type') == "STATUS_SCHEDULED":
        return True, [], {
            "stability": ("✅ PRE-GAME", "#00ff00", True, []),
            "cushion": ("✅ PRE-GAME", "#00ff00", True),
            "pace": ("✅ PRE-GAME", "#00ff00", True)
        }
    
    home_abbr = game_data.get('home_abbr')
    away_abbr = game_data.get('away_abbr')
    
    stability_label, stability_color, is_stable, stability_flags = get_match_stability(
        home_abbr, away_abbr, injuries, yesterday_teams
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
# ESPN API - REAL DATA
# ============================================================
@st.cache_data(ttl=60)
def fetch_nhl_games():
    today_date = datetime.now(eastern).strftime('%Y%m%d')
    url = f"https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard?dates={today_date}"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        games = {}
        for event in data.get("events", []):
            comp = event.get("competitions", [{}])[0]
            competitors = comp.get("competitors", [])
            if len(competitors) < 2:
                continue
            home_team, away_team = None, None
            home_score, away_score = 0, 0
            home_abbr, away_abbr = "", ""
            for c in competitors:
                full_name = c.get("team", {}).get("displayName", "")
                abbr = TEAM_ABBREVS.get(full_name, c.get("team", {}).get("abbreviation", ""))
                score = int(c.get("score", 0) or 0)
                if c.get("homeAway") == "home":
                    home_team, home_score, home_abbr = full_name, score, abbr
                else:
                    away_team, away_score, away_abbr = full_name, score, abbr
            status_obj = event.get("status", {})
            status_type = status_obj.get("type", {}).get("name", "STATUS_SCHEDULED")
            clock = status_obj.get("displayClock", "")
            period = status_obj.get("period", 0)
            game_key = f"{away_abbr}@{home_abbr}"
            games[game_key] = {
                "away_team": away_team, "home_team": home_team,
                "away_abbr": away_abbr, "home_abbr": home_abbr,
                "away_score": away_score, "home_score": home_score,
                "total": away_score + home_score,
                "period": period, "clock": clock, "status_type": status_type
            }
        return games
    except Exception as e:
        st.error(f"ESPN API error: {e}")
        return {}

@st.cache_data(ttl=300)
def fetch_yesterday_teams():
    yesterday = (datetime.now(eastern) - timedelta(days=1)).strftime('%Y%m%d')
    url = f"https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard?dates={yesterday}"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        teams = set()
        for event in data.get("events", []):
            comp = event.get("competitions", [{}])[0]
            for c in comp.get("competitors", []):
                full_name = c.get("team", {}).get("displayName", "")
                abbr = TEAM_ABBREVS.get(full_name, "")
                if abbr:
                    teams.add(abbr)
        return teams
    except:
        return set()

@st.cache_data(ttl=300)
def fetch_nhl_injuries():
    injuries = {}
    try:
        url = "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/injuries"
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
                    if name:
                        injuries[team_abbr].append({"name": name, "status": status})
    except:
        pass
    return injuries

@st.cache_data(ttl=300)
def fetch_nhl_news():
    try:
        url = "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/news?limit=5"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        articles = []
        for article in data.get("articles", [])[:5]:
            articles.append({
                "headline": article.get("headline", ""),
                "link": article.get("links", {}).get("web", {}).get("href", "")
            })
        return articles
    except:
        return []

@st.cache_data(ttl=300)
def fetch_team_records():
    records = {}
    try:
        url = "https://site.api.espn.com/apis/v2/sports/hockey/nhl/standings"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        for group in data.get("children", []):
            for team_standing in group.get("standings", {}).get("entries", []):
                team_name = team_standing.get("team", {}).get("displayName", "")
                abbr = TEAM_ABBREVS.get(team_name, "")
                if not abbr:
                    continue
                stats = {s.get("name"): s.get("value") for s in team_standing.get("stats", [])}
                streak_val = stats.get("streak", 0)
                streak_type = "W" if streak_val > 0 else "L"
                records[abbr] = {
                    "wins": int(stats.get("wins", 0)),
                    "losses": int(stats.get("losses", 0)),
                    "otl": int(stats.get("otLosses", 0)),
                    "streak": abs(int(streak_val)),
                    "streak_type": streak_type
                }
    except:
        pass
    return records

# ============================================================
# ML SCORING MODEL
# ============================================================
def calc_ml_score(home_abbr, away_abbr, yesterday_teams, injuries):
    home = TEAM_STATS.get(home_abbr, {})
    away = TEAM_STATS.get(away_abbr, {})
    
    score_home, score_away = 0, 0
    reasons_home, reasons_away = [], []
    
    home_b2b = home_abbr in yesterday_teams
    away_b2b = away_abbr in yesterday_teams
    if away_b2b and not home_b2b:
        score_home += 1.0
        reasons_home.append("🛏️ Opp B2B")
    elif home_b2b and not away_b2b:
        score_away += 1.0
        reasons_away.append("🛏️ Opp B2B")
    
    home_win = home.get('win_pct', 0.5)
    away_win = away.get('win_pct', 0.5)
    if home_win - away_win > 0.10:
        score_home += 1.0
        reasons_home.append(f"📊 {int(home_win*100)}% W")
    elif away_win - home_win > 0.10:
        score_away += 1.0
        reasons_away.append(f"📊 {int(away_win*100)}% W")
    
    score_home += 1.0
    home_hw = home.get('home_win_pct', 0.55)
    reasons_home.append(f"🏠 {int(home_hw*100)}%")
    
    home_gf = home.get('goals_for', 2.8)
    away_gf = away.get('goals_for', 2.8)
    if home_gf - away_gf > 0.3:
        score_home += 1.0
        reasons_home.append(f"🥅 {home_gf:.2f} GF")
    elif away_gf - home_gf > 0.3:
        score_away += 1.0
        reasons_away.append(f"🥅 {away_gf:.2f} GF")
    
    home_ga = home.get('goals_against', 2.9)
    away_ga = away.get('goals_against', 2.9)
    if away_ga - home_ga > 0.3:
        score_home += 1.0
        reasons_home.append(f"🛡️ {home_ga:.2f} GA")
    elif home_ga - away_ga > 0.3:
        score_away += 1.0
        reasons_away.append(f"🛡️ {away_ga:.2f} GA")
    
    home_pp = home.get('pp_pct', 20)
    away_pp = away.get('pp_pct', 20)
    if home_pp - away_pp > 4:
        score_home += 0.5
        reasons_home.append(f"⚡ {home_pp:.1f}% PP")
    elif away_pp - home_pp > 4:
        score_away += 0.5
        reasons_away.append(f"⚡ {away_pp:.1f}% PP")
    
    home_pk = home.get('pk_pct', 80)
    away_pk = away.get('pk_pct', 80)
    if home_pk - away_pk > 3:
        score_home += 0.5
        reasons_home.append(f"🚫 {home_pk:.1f}% PK")
    elif away_pk - home_pk > 3:
        score_away += 0.5
        reasons_away.append(f"🚫 {away_pk:.1f}% PK")
    
    home_inj = len([i for i in injuries.get(home_abbr, []) if 'out' in i.get('status', '').lower()])
    away_inj = len([i for i in injuries.get(away_abbr, []) if 'out' in i.get('status', '').lower()])
    if away_inj > home_inj + 1:
        score_home += 1.5
        reasons_home.append(f"🏥 {away_inj} OUT")
    elif home_inj > away_inj + 1:
        score_away += 1.5
        reasons_away.append(f"🏥 {home_inj} OUT")
    
    total = score_home + score_away
    if total > 0:
        home_final = round((score_home / total) * 10, 1)
        away_final = round((score_away / total) * 10, 1)
    else:
        home_final, away_final = 5.0, 5.0
    
    if home_final >= away_final:
        return home_abbr, home_final, reasons_home[:4]
    else:
        return away_abbr, away_final, reasons_away[:4]

def get_signal_tier(score):
    if score >= 8.0:
        return "🔒 STRONG", "#00ff00"
    elif score >= 6.5:
        return "🔵 BUY", "#00aaff"
    elif score >= 5.5:
        return "🟡 LEAN", "#ffff00"
    else:
        return "⚪ PASS", "#888888"

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
                      if p.get('sport') == 'NHL' and today_str in p.get('timestamp', '')])
    st.markdown(f"""
**Next ML#:** ML-{get_next_ml_number():03d}  
**Today's Tags:** {today_tags}
""")
    st.divider()
    
    st.header("📖 SIGNAL TIERS")
    st.markdown("""
🔒 **STRONG** → 8.0+ <span style="color:#888;font-size:0.8em;">Tracked</span>

🔵 **BUY** → 6.5-7.9 <span style="color:#888;font-size:0.8em;">Info only</span>

🟡 **LEAN** → 5.5-6.4 <span style="color:#888;font-size:0.8em;">Slight edge</span>

⚪ **PASS** → Below 5.5 <span style="color:#888;font-size:0.8em;">No edge</span>
""", unsafe_allow_html=True)
    st.divider()
    
    st.header("🔗 KALSHI")
    st.markdown('<a href="https://kalshi.com/?search=nhl" target="_blank" style="color: #00aaff;">NHL Markets ↗</a>', unsafe_allow_html=True)
    st.divider()
    st.caption(f"v{VERSION}")

# ============================================================
# MAIN
# ============================================================
st.title("🏒 NHL EDGE FINDER")
st.caption(f"v{VERSION} | {now.strftime('%I:%M:%S %p ET')} | Real ESPN Data")

games = fetch_nhl_games()
yesterday_teams = fetch_yesterday_teams()
injuries = fetch_nhl_injuries()
news = fetch_nhl_news()
team_records = fetch_team_records()

if not games:
    st.warning("No NHL games scheduled today.")
    st.stop()

# Filter yesterday teams to only include today's teams
today_teams = set()
for gk in games.keys():
    parts = gk.split("@")
    today_teams.add(parts[0])
    today_teams.add(parts[1])
yesterday_teams = yesterday_teams.intersection(today_teams)

live_games = {k: v for k, v in games.items() if v['period'] > 0 and v['status_type'] != "STATUS_FINAL"}
final_games = {k: v for k, v in games.items() if v['status_type'] == "STATUS_FINAL"}
scheduled_games = {k: v for k, v in games.items() if v['status_type'] == "STATUS_SCHEDULED"}

# ============================================================
# ⏰ STATUS BAR
# ============================================================
if live_games:
    st.success(f"⏰ **{len(live_games)} GAME{'S' if len(live_games) > 1 else ''} LIVE NOW** | {len(final_games)} Final | {len(scheduled_games)} Scheduled")
else:
    st.info(f"📅 **{len(games)} game{'s' if len(games) > 1 else ''} scheduled today** | {len(final_games)} Final")

# ============================================================
# 📊 STATS ROW
# ============================================================
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Games Today", len(games))
with col2:
    st.metric("Live Now", len(live_games))
with col3:
    b2b_count = len(yesterday_teams)
    st.metric("B2B Teams", b2b_count)
with col4:
    st.metric("Today's Record", "—")

# ============================================================
# 📖 LEGEND BOX
# ============================================================
st.markdown("""
<div style="background: #1a1a2e; border-radius: 8px; padding: 10px 15px; margin: 10px 0;">
    <span style="color: #00ff00;">🔒 STRONG 8.0+</span> &nbsp;|&nbsp;
    <span style="color: #00aaff;">🔵 BUY 6.5+</span> &nbsp;|&nbsp;
    <span style="color: #ffff00;">🟡 LEAN 5.5+</span> &nbsp;|&nbsp;
    <span style="color: #888;">⚪ PASS &lt;5.5</span>
</div>
""", unsafe_allow_html=True)

st.divider()

# ============================================================
# 🏷️ TODAY'S STRONG PICKS
# ============================================================
today_strong = [p for p in st.session_state.strong_picks.get('picks', []) 
                if p.get('sport') == 'NHL' and today_str in p.get('timestamp', '')]

if today_strong:
    st.subheader("🏷️ TODAY'S STRONG PICKS")
    for pick in today_strong:
        ml_num = pick.get('ml_number', 0)
        game_key = pick.get('game', '')
        pick_team = pick.get('pick', '')
        
        result_text = "⏳ Pending"
        result_color = "#888"
        for gk, g in games.items():
            if gk == game_key:
                if g['status_type'] == "STATUS_FINAL":
                    home_score = g['home_score']
                    away_score = g['away_score']
                    winner = g['home_abbr'] if home_score > away_score else g['away_abbr']
                    if winner == pick_team:
                        result_text = f"✅ WIN ({away_score}-{home_score})"
                        result_color = "#22c55e"
                    else:
                        result_text = f"❌ LOSS ({away_score}-{home_score})"
                        result_color = "#ef4444"
                elif g['status_type'] != "STATUS_SCHEDULED":
                    result_text = f"🔴 LIVE P{g.get('period', 0)}"
                    result_color = "#f59e0b"
                break
        
        st.markdown(f"""<div style="background:#0f172a;padding:12px 16px;border-radius:8px;margin-bottom:8px;border-left:4px solid {result_color};"><span style="color:#ffd700;font-weight:bold;">ML-{ml_num:03d}</span><span style="color:#fff;margin-left:12px;font-weight:600;">{pick_team}</span><span style="color:#666;margin-left:8px;">({game_key})</span><span style="color:{result_color};float:right;">{result_text}</span></div>""", unsafe_allow_html=True)
    st.divider()

# ============================================================
# 🎯 BUILD ML RESULTS
# ============================================================
ml_results = []
for game_key, g in games.items():
    away_abbr = g["away_abbr"]
    home_abbr = g["home_abbr"]
    
    pick, score, reasons = calc_ml_score(home_abbr, away_abbr, yesterday_teams, injuries)
    tier, color = get_signal_tier(score)
    
    opponent = away_abbr if pick == home_abbr else home_abbr
    kalshi_url = build_kalshi_url(away_abbr, home_abbr)
    
    # Build game_data for Strong Pick check
    game_data = {
        "home_abbr": home_abbr,
        "away_abbr": away_abbr,
        "home_score": g["home_score"],
        "away_score": g["away_score"],
        "status_type": g["status_type"],
        "period": g.get("period", 0)
    }
    
    # Check Strong Pick eligibility
    is_tracked = score >= 8.0
    strong_eligible, block_reasons, gate_results = check_strong_pick_eligible(
        game_key, pick, game_data, injuries, yesterday_teams
    )
    
    ml_results.append({
        "pick": pick,
        "opponent": opponent,
        "score": score,
        "tier": tier,
        "color": color,
        "reasons": reasons,
        "kalshi_url": kalshi_url,
        "game_key": game_key,
        "status": g["status_type"],
        "away_abbr": away_abbr,
        "home_abbr": home_abbr,
        "is_tracked": is_tracked,
        "strong_eligible": strong_eligible,
        "block_reasons": block_reasons,
        "gate_results": gate_results
    })

ml_results.sort(key=lambda x: x["score"], reverse=True)

# ============================================================
# 💰 TOP PICK OF THE DAY
# ============================================================
if ml_results and ml_results[0]["score"] >= 6.5:
    top = ml_results[0]
    top_reasons = ' • '.join(top['reasons'])
    st.markdown(f"""<div style="background:linear-gradient(135deg,#064e3b,#022c22);border-radius:12px;padding:20px;margin-bottom:20px;border:2px solid #10b981;"><div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;"><div><span style="color:#10b981;font-size:0.9em;">💰 TOP PICK OF THE DAY</span><h2 style="color:#fff;margin:5px 0;">{top['pick']} <span style="color:#888;font-weight:normal;">vs {top['opponent']}</span></h2><span style="color:{top['color']};font-size:1.3em;font-weight:bold;">{top['score']}/10</span><span style="color:#888;margin-left:15px;">{top_reasons}</span></div><a href="{top['kalshi_url']}" target="_blank" style="text-decoration:none;"><button style="background:linear-gradient(135deg,#16a34a,#22c55e);color:white;padding:12px 28px;border:none;border-radius:8px;font-size:1em;font-weight:700;cursor:pointer;">BUY {top['pick']} →</button></a></div></div>""", unsafe_allow_html=True)

# ============================================================
# 🔥 HOT STREAKS + ❄️ FADE ALERTS
# ============================================================
hot_teams = []
cold_teams = []
for team in today_teams:
    rec = team_records.get(team, {})
    streak = rec.get("streak", 0)
    streak_type = rec.get("streak_type", "")
    if streak >= 4 and streak_type == "W":
        hot_teams.append((team, streak))
    elif streak >= 4 and streak_type == "L":
        cold_teams.append((team, streak))

col1, col2 = st.columns(2)
with col1:
    if hot_teams:
        hot_str = " • ".join([f"**{t}** ({s}W)" for t, s in sorted(hot_teams, key=lambda x: -x[1])])
        st.success(f"🔥 **HOT STREAKS:** {hot_str}")
with col2:
    if cold_teams:
        cold_str = " • ".join([f"**{t}** ({s}L)" for t, s in sorted(cold_teams, key=lambda x: -x[1])])
        st.error(f"❄️ **FADE ALERT:** {cold_str}")

st.divider()

# ============================================================
# 🎯 ML PICKS
# ============================================================
st.subheader("🎯 ML PICKS")

shown = 0
for r in ml_results:
    if r["score"] < 5.5:
        continue
    shown += 1
    reasons_str = " • ".join(r["reasons"]) if r["reasons"] else ""
    
    existing_tag = get_strong_pick_for_game(r["game_key"])
    tag_html = ""
    if existing_tag:
        tag_html = f'<span style="background:#ffd700;color:#000;padding:2px 8px;border-radius:4px;font-size:0.75em;margin-left:10px;">ML-{existing_tag["ml_number"]:03d}</span>'
    
    st.markdown(f"""<div style="display:flex;align-items:center;justify-content:space-between;background:linear-gradient(135deg,#0f172a,#020617);padding:12px 15px;margin-bottom:8px;border-radius:8px;border-left:4px solid {r['color']};"><div><span style="font-weight:bold;color:#fff;font-size:1.1em;">{r['pick']}</span><span style="color:#666;"> vs {r['opponent']}</span><span style="color:{r['color']};font-weight:bold;margin-left:12px;">{r['score']}/10</span>{tag_html}<span style="color:#888;font-size:0.85em;margin-left:12px;">{reasons_str}</span></div><a href="{r['kalshi_url']}" target="_blank" style="text-decoration:none;"><button style="background-color:#16a34a;color:white;padding:8px 16px;border:none;border-radius:6px;font-size:0.9em;font-weight:600;cursor:pointer;">BUY {r['pick']}</button></a></div>""", unsafe_allow_html=True)
    
    # Strong Pick Button - show for 8.0+ that pass gates and aren't already tagged
    if r["is_tracked"] and r["strong_eligible"] and not existing_tag and r["status"] != "STATUS_FINAL":
        if st.button(f"➕ Add Strong Pick", key=f"strong_{r['game_key']}", use_container_width=True):
            ml_num = add_strong_pick(r["game_key"], r["pick"], "NHL")
            st.success(f"✅ Tagged ML-{ml_num:03d}: {r['pick']} ({r['game_key']})")
            st.rerun()
    # Show block reason only for LIVE games that fail gates
    elif r["is_tracked"] and not r["strong_eligible"] and not existing_tag and r["status"] != "STATUS_SCHEDULED":
        st.markdown(f"<div style='color:#ff6666;font-size:0.75em;margin-bottom:8px;margin-left:14px'>⚠️ Strong Pick blocked: {', '.join(r['block_reasons'])}</div>", unsafe_allow_html=True)

if shown == 0:
    st.info("No strong picks today. All games are close to toss-ups.")

st.divider()

# ============================================================
# 📰 BREAKING NEWS
# ============================================================
st.subheader("📰 BREAKING NEWS")
if news:
    for article in news[:4]:
        if article["link"]:
            st.markdown(f"• [{article['headline']}]({article['link']})")
        else:
            st.markdown(f"• {article['headline']}")
else:
    st.caption("No recent news available")

st.divider()

# ============================================================
# 🏥 INJURY REPORT
# ============================================================
st.subheader("🏥 INJURY REPORT")

injury_shown = False
cols = st.columns(4)
col_idx = 0

for team in sorted(today_teams):
    team_inj = injuries.get(team, [])
    key_injuries = [i for i in team_inj if 'out' in i.get('status', '').lower()]
    if key_injuries:
        with cols[col_idx % 4]:
            st.markdown(f"**{team}**")
            for inj in key_injuries[:3]:
                st.caption(f"🔴 {inj['name']}")
        col_idx += 1
        injury_shown = True

if not injury_shown:
    st.info("✅ No major injuries reported for today's teams")

if yesterday_teams:
    st.info(f"📅 **Back-to-Back:** {', '.join(sorted(yesterday_teams))}")

st.divider()

# ============================================================
# 📺 ALL GAMES
# ============================================================
st.subheader("📺 ALL GAMES")

cols = st.columns(4)
for i, (gk, g) in enumerate(games.items()):
    with cols[i % 4]:
        st.markdown(f"**{g['away_abbr']}** {g['away_score']} @ **{g['home_abbr']}** {g['home_score']}")
        if g['status_type'] == "STATUS_FINAL":
            st.caption("FINAL")
        elif g['period'] > 0:
            st.caption(f"P{g['period']} {g['clock']}")
        else:
            st.caption("Scheduled")

st.divider()

# ============================================================
# 📖 HOW TO USE
# ============================================================
with st.expander("📖 How to Use This App", expanded=False):
    st.markdown("""
**What is NHL Edge Finder?**

This tool analyzes NHL games and identifies moneyline betting opportunities on Kalshi prediction markets.

**Understanding the Signals:**

🔒 **STRONG (8.0+):** High confidence pick — eligible for Strong Pick tagging

🔵 **BUY (6.5-7.9):** Good edge detected

🟡 **LEAN (5.5-6.4):** Slight edge

⚪ **PASS (Below 5.5):** No clear edge

**Strong Pick System:**

All 🔒 STRONG (8.0+) pre-game picks get the "Add Strong Pick" button.

For **LIVE games**, picks must pass 3 gates:

1. **🛡️ Cushion Gate** — Must have 2+ goal lead
2. **⏱️ Pace Gate** — Not in P3 within 1 goal
3. **🔬 Match Gate** — No extreme instability factors

**Key Indicators:**

🛏️ **Opp B2B:** Opponent playing back-to-back games

🏠 **Home Ice:** Home team advantage percentage

🏥 **Injuries:** Key players out for opponent

🔥 **Hot Streak:** Team on 4+ game win streak

❄️ **Fade Alert:** Team on 4+ game losing streak

**Trading:**

Click BUY to open the Kalshi market for that game.
""")

st.divider()
st.caption(f"⚠️ Educational only. Not financial advice. v{VERSION}")
