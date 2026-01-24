import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="NBA Edge Finder", page_icon="🏀", layout="wide")

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
from datetime import datetime, timedelta
import pytz
import json
import os
import time
from styles import apply_styles, buy_button

apply_styles()

st.markdown("""
<style>
    @media (max-width: 768px) {
        .stApp { padding: 0.5rem; }
        h1 { font-size: 1.5rem !important; }
        h2 { font-size: 1.2rem !important; }
        div[data-testid="column"] { width: 100% !important; flex: 100% !important; min-width: 100% !important; }
        .stButton button { padding: 8px 12px !important; font-size: 14px !important; }
    }
</style>
""", unsafe_allow_html=True)

eastern = pytz.timezone("US/Eastern")
today_str = datetime.now(eastern).strftime("%Y-%m-%d")

POSITIONS_FILE = "nba_positions.json"
STRONG_PICKS_FILE = "strong_picks.json"

def load_positions():
    try:
        if os.path.exists(POSITIONS_FILE):
            with open(POSITIONS_FILE, 'r') as f:
                return json.load(f)
    except: pass
    return []

def save_positions(positions):
    try:
        with open(POSITIONS_FILE, 'w') as f:
            json.dump(positions, f, indent=2)
    except: pass

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

if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = False
if "positions" not in st.session_state:
    st.session_state.positions = load_positions()
if "editing_position" not in st.session_state:
    st.session_state.editing_position = None
if "strong_picks" not in st.session_state:
    st.session_state.strong_picks = load_strong_picks()

if st.session_state.auto_refresh:
    st.markdown(f'<meta http-equiv="refresh" content="30;url=?r={int(time.time()) + 30}">', unsafe_allow_html=True)
    auto_status = "🔄 Auto-refresh ON (30s)"
else:
    auto_status = "⏸️ Auto-refresh OFF"

KALSHI_CODES = {
    "Atlanta": "ATL", "Boston": "BOS", "Brooklyn": "BKN", "Charlotte": "CHA",
    "Chicago": "CHI", "Cleveland": "CLE", "Dallas": "DAL", "Denver": "DEN",
    "Detroit": "DET", "Golden State": "GSW", "Houston": "HOU", "Indiana": "IND",
    "LA Clippers": "LAC", "LA Lakers": "LAL", "Memphis": "MEM", "Miami": "MIA",
    "Milwaukee": "MIL", "Minnesota": "MIN", "New Orleans": "NOP", "New York": "NYK",
    "Oklahoma City": "OKC", "Orlando": "ORL", "Philadelphia": "PHI", "Phoenix": "PHX",
    "Portland": "POR", "Sacramento": "SAC", "San Antonio": "SAS", "Toronto": "TOR",
    "Utah": "UTA", "Washington": "WAS"
}

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
    "Atlanta": {"pace": 100.5, "def_rank": 26, "net_rating": -3.2, "home_win_pct": 0.52, "away_win_pct": 0.35},
    "Boston": {"pace": 99.8, "def_rank": 2, "net_rating": 11.2, "home_win_pct": 0.78, "away_win_pct": 0.65},
    "Brooklyn": {"pace": 98.2, "def_rank": 22, "net_rating": -4.5, "home_win_pct": 0.42, "away_win_pct": 0.28},
    "Charlotte": {"pace": 99.5, "def_rank": 28, "net_rating": -6.8, "home_win_pct": 0.38, "away_win_pct": 0.22},
    "Chicago": {"pace": 98.8, "def_rank": 20, "net_rating": -2.1, "home_win_pct": 0.48, "away_win_pct": 0.32},
    "Cleveland": {"pace": 97.2, "def_rank": 3, "net_rating": 8.5, "home_win_pct": 0.75, "away_win_pct": 0.58},
    "Dallas": {"pace": 99.0, "def_rank": 12, "net_rating": 4.2, "home_win_pct": 0.62, "away_win_pct": 0.48},
    "Denver": {"pace": 98.5, "def_rank": 10, "net_rating": 5.8, "home_win_pct": 0.72, "away_win_pct": 0.45},
    "Detroit": {"pace": 97.8, "def_rank": 29, "net_rating": -8.2, "home_win_pct": 0.32, "away_win_pct": 0.18},
    "Golden State": {"pace": 100.2, "def_rank": 8, "net_rating": 3.5, "home_win_pct": 0.65, "away_win_pct": 0.42},
    "Houston": {"pace": 101.5, "def_rank": 18, "net_rating": 1.2, "home_win_pct": 0.55, "away_win_pct": 0.38},
    "Indiana": {"pace": 103.5, "def_rank": 24, "net_rating": 2.8, "home_win_pct": 0.58, "away_win_pct": 0.42},
    "LA Clippers": {"pace": 98.0, "def_rank": 14, "net_rating": 1.5, "home_win_pct": 0.55, "away_win_pct": 0.40},
    "LA Lakers": {"pace": 99.5, "def_rank": 15, "net_rating": 2.2, "home_win_pct": 0.58, "away_win_pct": 0.42},
    "Memphis": {"pace": 100.8, "def_rank": 6, "net_rating": 4.5, "home_win_pct": 0.68, "away_win_pct": 0.48},
    "Miami": {"pace": 97.5, "def_rank": 5, "net_rating": 3.8, "home_win_pct": 0.65, "away_win_pct": 0.45},
    "Milwaukee": {"pace": 99.2, "def_rank": 9, "net_rating": 5.2, "home_win_pct": 0.70, "away_win_pct": 0.52},
    "Minnesota": {"pace": 98.8, "def_rank": 4, "net_rating": 7.5, "home_win_pct": 0.72, "away_win_pct": 0.55},
    "New Orleans": {"pace": 100.0, "def_rank": 16, "net_rating": 1.8, "home_win_pct": 0.55, "away_win_pct": 0.38},
    "New York": {"pace": 98.5, "def_rank": 7, "net_rating": 6.2, "home_win_pct": 0.68, "away_win_pct": 0.52},
    "Oklahoma City": {"pace": 99.8, "def_rank": 1, "net_rating": 12.5, "home_win_pct": 0.82, "away_win_pct": 0.68},
    "Orlando": {"pace": 97.0, "def_rank": 11, "net_rating": 3.2, "home_win_pct": 0.62, "away_win_pct": 0.45},
    "Philadelphia": {"pace": 98.2, "def_rank": 13, "net_rating": 2.5, "home_win_pct": 0.58, "away_win_pct": 0.42},
    "Phoenix": {"pace": 99.0, "def_rank": 17, "net_rating": 2.0, "home_win_pct": 0.60, "away_win_pct": 0.42},
    "Portland": {"pace": 99.5, "def_rank": 27, "net_rating": -5.5, "home_win_pct": 0.40, "away_win_pct": 0.25},
    "Sacramento": {"pace": 101.2, "def_rank": 19, "net_rating": 0.8, "home_win_pct": 0.55, "away_win_pct": 0.38},
    "San Antonio": {"pace": 100.5, "def_rank": 25, "net_rating": -4.8, "home_win_pct": 0.42, "away_win_pct": 0.28},
    "Toronto": {"pace": 98.8, "def_rank": 21, "net_rating": -1.5, "home_win_pct": 0.48, "away_win_pct": 0.32},
    "Utah": {"pace": 100.2, "def_rank": 30, "net_rating": -7.5, "home_win_pct": 0.35, "away_win_pct": 0.22},
    "Washington": {"pace": 101.0, "def_rank": 23, "net_rating": -6.2, "home_win_pct": 0.38, "away_win_pct": 0.25}
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

STAR_TIERS = {
    "Nikola Jokic": 3, "Shai Gilgeous-Alexander": 3, "Giannis Antetokounmpo": 3, "Luka Doncic": 3,
    "Joel Embiid": 3, "Jayson Tatum": 3, "Stephen Curry": 3, "Kevin Durant": 3, "LeBron James": 3,
    "Anthony Edwards": 3, "Ja Morant": 3, "Donovan Mitchell": 3, "Trae Young": 3, "Devin Booker": 3,
    "Jaylen Brown": 2, "Anthony Davis": 2, "Damian Lillard": 2, "Kyrie Irving": 2, "Jimmy Butler": 2,
    "Bam Adebayo": 2, "Tyrese Haliburton": 2, "De'Aaron Fox": 2, "Jalen Brunson": 2, "Chet Holmgren": 2,
    "Paolo Banchero": 2, "Franz Wagner": 2, "Scottie Barnes": 2, "Evan Mobley": 2, "Darius Garland": 2,
    "Zion Williamson": 2, "Brandon Ingram": 2, "LaMelo Ball": 2, "Cade Cunningham": 2, "Jalen Williams": 2,
    "Tyrese Maxey": 2, "Desmond Bane": 2, "Jamal Murray": 2, "Pascal Siakam": 2, "Lauri Markkanen": 2,
    "Victor Wembanyama": 2, "Alperen Sengun": 2, "Derrick White": 2, "Domantas Sabonis": 2,
    "Julius Randle": 1, "RJ Barrett": 1, "Mikal Bridges": 1, "Anfernee Simons": 1, "Jalen Green": 1,
    "Fred VanVleet": 1, "Scoot Henderson": 1, "Bennedict Mathurin": 1, "Keegan Murray": 1,
    "Zach LaVine": 1, "DeMar DeRozan": 1, "Kawhi Leonard": 1, "Paul George": 1, "Bradley Beal": 1,
    "Draymond Green": 1, "Karl-Anthony Towns": 1, "Rudy Gobert": 1, "Jordan Poole": 1
}

H2H_EDGES = {
    ("Boston", "Philadelphia"): 0.5, ("Boston", "New York"): 0.5,
    ("Milwaukee", "Chicago"): 0.5, ("Cleveland", "Detroit"): 0.5,
    ("Oklahoma City", "Utah"): 0.5, ("Denver", "Minnesota"): 0.5,
    ("LA Lakers", "LA Clippers"): 0.3, ("Golden State", "Sacramento"): 0.5,
    ("Phoenix", "Portland"): 0.5, ("Miami", "Orlando"): 0.5,
    ("Dallas", "San Antonio"): 0.5, ("Memphis", "New Orleans"): 0.3,
}

THRESHOLDS = [210.5, 215.5, 220.5, 225.5, 230.5, 235.5, 240.5, 245.5, 250.5, 255.5]

def escape_html(text):
    if not text: return ""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def build_kalshi_ml_url(away_team, home_team):
    away_code = KALSHI_CODES.get(away_team, "XXX")
    home_code = KALSHI_CODES.get(home_team, "XXX")
    date_str = datetime.now(eastern).strftime("%y%b%d").upper()
    ticker = f"KXNBAGAME-{date_str}{away_code}{home_code}"
    return f"https://kalshi.com/markets/KXNBAGAME/{ticker}"

def build_kalshi_totals_url(away_team, home_team):
    away_code = KALSHI_CODES.get(away_team, "XXX")
    home_code = KALSHI_CODES.get(home_team, "XXX")
    date_str = datetime.now(eastern).strftime("%y%b%d").upper()
    ticker = f"KXNBATOTAL-{date_str}{away_code}{home_code}"
    return f"https://kalshi.com/markets/KXNBATOTAL/{ticker}"

def calc_distance(loc1, loc2):
    from math import radians, sin, cos, sqrt, atan2
    lat1, lon1 = radians(loc1[0]), radians(loc1[1])
    lat2, lon2 = radians(loc2[0]), radians(loc2[1])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    return 3959 * 2 * atan2(sqrt(a), sqrt(1-a))

def fetch_espn_scores():
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
                if c.get("homeAway") == "home": home_team, home_score = team_name, score
                else: away_team, away_score = team_name, score
            status_obj = event.get("status", {})
            status_type = status_obj.get("type", {}).get("name", "STATUS_SCHEDULED")
            clock = status_obj.get("displayClock", "")
            period = status_obj.get("period", 0)
            game_key = f"{away_team}@{home_team}"
            games[game_key] = {
                "away_team": away_team, "home_team": home_team,
                "away_score": away_score, "home_score": home_score,
                "total": away_score + home_score, "period": period, "clock": clock, "status_type": status_type
            }
        return games
    except: return {}

def fetch_yesterday_teams():
    yesterday = (datetime.now(eastern) - timedelta(days=1)).strftime('%Y%m%d')
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={yesterday}"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        teams = set()
        for event in data.get("events", []):
            comp = event.get("competitions", [{}])[0]
            for c in comp.get("competitors", []):
                name = c.get("team", {}).get("displayName", "")
                teams.add(TEAM_ABBREVS.get(name, name))
        return teams
    except: return set()

def fetch_espn_injuries():
    injuries = {}
    try:
        url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/injuries"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        for team_data in data.get("injuries", []):
            team_name = team_data.get("displayName", "")
            team_key = TEAM_ABBREVS.get(team_name, team_name)
            if not team_key: continue
            injuries[team_key] = []
            for player in team_data.get("injuries", []):
                athlete = player.get("athlete", {})
                name = athlete.get("displayName", "")
                status = player.get("status", "")
                if name: injuries[team_key].append({"name": name, "status": status})
    except: pass
    return injuries

TEAM_IDS = {
    "Atlanta": "1", "Boston": "2", "Brooklyn": "17", "Charlotte": "30",
    "Chicago": "4", "Cleveland": "5", "Dallas": "6", "Denver": "7",
    "Detroit": "8", "Golden State": "9", "Houston": "10", "Indiana": "11",
    "LA Clippers": "12", "LA Lakers": "13", "Memphis": "29", "Miami": "14",
    "Milwaukee": "15", "Minnesota": "16", "New Orleans": "3", "New York": "18",
    "Oklahoma City": "25", "Orlando": "19", "Philadelphia": "20", "Phoenix": "21",
    "Portland": "22", "Sacramento": "23", "San Antonio": "24", "Toronto": "28",
    "Utah": "26", "Washington": "27"
}

@st.cache_data(ttl=3600)
def fetch_team_streak(team_name):
    try:
        team_id = TEAM_IDS.get(team_name, "1")
        url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team_id}"
        resp = requests.get(url, timeout=5)
        data = resp.json()
        record = data.get("team", {}).get("record", {}).get("items", [{}])[0]
        stats = record.get("stats", [])
        for stat in stats:
            if stat.get("name") == "streak":
                streak_str = stat.get("displayValue", "W0")
                if streak_str.startswith("W"):
                    return int(streak_str[1:]) if len(streak_str) > 1 else 0
                elif streak_str.startswith("L"):
                    return -int(streak_str[1:]) if len(streak_str) > 1 else 0
        return 0
    except:
        return 0

@st.cache_data(ttl=3600)
def fetch_all_team_streaks():
    streaks = {}
    for team in KALSHI_CODES.keys():
        streaks[team] = fetch_team_streak(team)
    return streaks

@st.cache_data(ttl=3600)
def fetch_last_5_records():
    last_5 = {}
    try:
        dates = [(datetime.now(eastern) - timedelta(days=i)).strftime('%Y%m%d') for i in range(1, 15)]
        team_games = {team: [] for team in KALSHI_CODES.keys()}
        for date in dates:
            url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={date}"
            resp = requests.get(url, timeout=5)
            data = resp.json()
            for event in data.get("events", []):
                status = event.get("status", {}).get("type", {}).get("name", "")
                if status != "STATUS_FINAL": continue
                comp = event.get("competitions", [{}])[0]
                competitors = comp.get("competitors", [])
                if len(competitors) < 2: continue
                for c in competitors:
                    team_name = TEAM_ABBREVS.get(c.get("team", {}).get("displayName", ""), "")
                    winner = c.get("winner", False)
                    if team_name in team_games:
                        team_games[team_name].append({"date": date, "win": winner})
        for team, games_list in team_games.items():
            games_list.sort(key=lambda x: x['date'], reverse=True)
            recent = games_list[:5]
            wins = sum(1 for g in recent if g['win'])
            form = "".join(["W" if g['win'] else "L" for g in recent])[::-1]
            last_5[team] = {"wins": wins, "losses": 5 - wins, "form": form if form else "-----", "hot": wins >= 4, "cold": wins <= 1}
    except: pass
    return last_5

def get_injury_impact(team, injuries):
    team_injuries = injuries.get(team, [])
    stars = STAR_PLAYERS.get(team, [])
    out_players, score = [], 0
    for inj in team_injuries:
        name, status = inj.get("name", ""), inj.get("status", "").upper()
        is_star = any(star.lower() in name.lower() for star in stars)
        if "OUT" in status:
            if is_star: score += 4.0; out_players.append(name)
            else: score += 1.0
    return out_players, score

def get_minutes_played(period, clock, status_type):
    if status_type == "STATUS_FINAL": return 48 if period <= 4 else 48 + (period - 4) * 5
    if status_type == "STATUS_HALFTIME": return 24
    if period == 0: return 0
    try:
        parts = str(clock).split(':')
        mins = int(parts[0])
        secs = int(float(parts[1])) if len(parts) > 1 else 0
        time_left = mins + secs/60
        if period <= 4: return (period - 1) * 12 + (12 - time_left)
        else: return 48 + (period - 5) * 5 + (5 - time_left)
    except: return (period - 1) * 12 if period <= 4 else 48 + (period - 5) * 5

def calc_ml_score(home_team, away_team, yesterday_teams, injuries, last_5):
    home, away = TEAM_STATS.get(home_team, {}), TEAM_STATS.get(away_team, {})
    home_loc, away_loc = TEAM_LOCATIONS.get(home_team, (0, 0)), TEAM_LOCATIONS.get(away_team, (0, 0))
    sh, sa = 0, 0
    rh, ra = [], []
    home_b2b, away_b2b = home_team in yesterday_teams, away_team in yesterday_teams
    if away_b2b and not home_b2b: sh += 1.0; rh.append("🛏️ Opp B2B")
    elif home_b2b and not away_b2b: sa += 1.0; ra.append("🛏️ Opp B2B")
    home_net, away_net = home.get('net_rating', 0), away.get('net_rating', 0)
    if home_net - away_net > 5: sh += 1.0; rh.append(f"📊 Net +{home_net:.1f}")
    elif away_net - home_net > 5: sa += 1.0; ra.append(f"📊 Net +{away_net:.1f}")
    home_def, away_def = home.get('def_rank', 15), away.get('def_rank', 15)
    if home_def <= 5: sh += 1.0; rh.append(f"🛡️ #{home_def} DEF")
    if away_def <= 5: sa += 1.0; ra.append(f"🛡️ #{away_def} DEF")
    sh += 1.0; rh.append("🏠 Home")
    home_out, home_inj = get_injury_impact(home_team, injuries)
    away_out, away_inj = get_injury_impact(away_team, injuries)
    if away_inj - home_inj > 3: sh += 2.0; rh.append(f"🏥 {escape_html(away_out[0][:10])} OUT" if away_out else "🏥 Opp Injured")
    elif home_inj - away_inj > 3: sa += 2.0; ra.append(f"🏥 {escape_html(home_out[0][:10])} OUT" if home_out else "🏥 Opp Injured")
    travel = calc_distance(away_loc, home_loc)
    if travel > 2000: sh += 1.0; rh.append(f"✈️ {int(travel)}mi")
    home_hw = home.get('home_win_pct', 0.5)
    if home_hw > 0.65: sh += 0.8; rh.append(f"🏟️ {int(home_hw*100)}%")
    if home_team == "Denver": sh += 1.0; rh.append("🏔️ Altitude")
    home_streak = fetch_team_streak(home_team)
    away_streak = fetch_team_streak(away_team)
    if home_streak >= 3 and away_streak <= -2:
        sh += 1.0; rh.append(f"🔥 W{home_streak}")
    elif away_streak >= 3 and home_streak <= -2:
        sa += 1.0; ra.append(f"🔥 W{away_streak}")
    elif home_streak >= 4:
        sh += 0.5; rh.append(f"🔥 W{home_streak}")
    elif away_streak >= 4:
        sa += 0.5; ra.append(f"🔥 W{away_streak}")
    h2h_edge = H2H_EDGES.get((home_team, away_team), 0)
    if h2h_edge > 0: sh += h2h_edge; rh.append("🆚 H2H")
    h2h_edge_rev = H2H_EDGES.get((away_team, home_team), 0)
    if h2h_edge_rev > 0: sa += h2h_edge_rev; ra.append("🆚 H2H")
    total = sh + sa
    hf = round((sh / total) * 10, 1) if total > 0 else 5.0
    af = round((sa / total) * 10, 1) if total > 0 else 5.0
    if hf >= af: return home_team, hf, rh[:4], home_out, away_out, home_net, away_net
    else: return away_team, af, ra[:4], home_out, away_out, home_net, away_net

def get_strong_pick_for_game(game_key):
    for pick in st.session_state.strong_picks.get("picks", []):
        if pick.get("game") == game_key: return pick
    return None

# FETCH DATA
games = fetch_espn_scores()
game_list = sorted(list(games.keys()))
yesterday_teams = fetch_yesterday_teams()
injuries = fetch_espn_injuries()
last_5 = fetch_last_5_records()
all_streaks = fetch_all_team_streaks()
now = datetime.now(eastern)

today_teams = set()
for gk in games.keys():
    parts = gk.split("@")
    today_teams.add(parts[0])
    today_teams.add(parts[1])
yesterday_teams = yesterday_teams.intersection(today_teams)

live_games = {k: v for k, v in games.items() if v['period'] > 0 and v['status_type'] != "STATUS_FINAL"}

# SIDEBAR
with st.sidebar:
    st.header("📖 ML LEGEND")
    st.markdown("""
🟢 **STRONG BUY** → 8.0+

🔵 **BUY** → 6.5-7.9

🟡 **LEAN** → 5.5-6.4

⚪ **TOSS-UP** → 4.5-5.4
""")
    st.divider()
    st.header("🎯 10 ML FACTORS")
    st.markdown("""
| # | Factor | Max |
|---|--------|-----|
| 1 | 🛏️ Opp B2B | +1.0 |
| 2 | 📊 Net Rating | +1.0 |
| 3 | 🛡️ Top 5 DEF | +1.0 |
| 4 | 🏠 Home | +1.0 |
| 5 | 🏥 Star OUT | +2.0 |
| 6 | ✈️ Travel | +1.0 |
| 7 | 🏟️ Home Win% | +0.8 |
| 8 | 🏔️ Altitude | +1.0 |
| 9 | 🔥 Hot/Cold | +1.0 |
| 10 | 🆚 H2H | +0.5 |
""")
    st.divider()
    st.caption("v18.7 NBA EDGE")

# TITLE
st.title("🏀 NBA EDGE FINDER")
st.caption(f"v18.7 • {now.strftime('%b %d, %Y %I:%M %p ET')}")

# STATS ROW
col1, col2, col3, col4 = st.columns(4)
with col1: st.metric("Today's Games", len(games))
with col2: st.metric("B2B Teams", len(yesterday_teams))
with col3: st.metric("Live Now", len(live_games))
with col4: st.metric("Positions", len(st.session_state.positions))

st.divider()

# ============================================================
# 🏥 INJURY REPORT
# ============================================================
st.subheader("🏥 INJURY REPORT")

injured_stars = []
for team, team_injuries in injuries.items():
    if team not in today_teams: continue
    for inj in team_injuries:
        name = inj.get("name", "")
        status = inj.get("status", "").upper()
        if "OUT" in status or "DTD" in status or "DOUBT" in status:
            tier = 0
            for star_name, star_tier in STAR_TIERS.items():
                if star_name.lower() in name.lower():
                    tier = star_tier
                    break
            if tier > 0:
                injured_stars.append({
                    "name": name, "team": team, 
                    "status": "OUT" if "OUT" in status else "DTD" if "DTD" in status else "DOUBT",
                    "tier": tier
                })

injured_stars.sort(key=lambda x: (-x['tier'], x['team']))

if injured_stars:
    cols = st.columns(3)
    for i, inj in enumerate(injured_stars):
        with cols[i % 3]:
            stars = "⭐" * inj['tier']
            status_color = "#ff4444" if inj['status'] == "OUT" else "#ffaa00"
            st.markdown(f"""<div style="background:linear-gradient(135deg,#1a1a2e,#2a1a2a);padding:10px;border-radius:6px;border-left:3px solid {status_color};margin-bottom:6px">
                <div style="color:#fff;font-weight:bold">{stars} {escape_html(inj['name'])} 🔥</div>
                <div style="color:{status_color};font-size:0.85em">{inj['status']} • {escape_html(inj['team'])}</div>
            </div>""", unsafe_allow_html=True)
    if yesterday_teams:
        b2b_list = ", ".join(sorted(yesterday_teams))
        st.markdown(f"""<div style="background:#1a2a3a;padding:10px 14px;border-radius:6px;margin-top:10px">
            <span style="color:#38bdf8">🏨 B2B:</span> <span style="color:#fff">{escape_html(b2b_list)}</span>
        </div>""", unsafe_allow_html=True)
else:
    st.info("No major injuries reported for today's games")

st.divider()

# ============================================================
# 🎯 ML PICKS
# ============================================================
st.subheader("🎯 ML PICKS")

if games:
    ml_results = []
    for gk, g in games.items():
        away, home = g["away_team"], g["home_team"]
        try:
            pick, score, reasons, home_out, away_out, home_net, away_net = calc_ml_score(home, away, yesterday_teams, injuries, last_5)
            is_home = pick == home
            opp = away if is_home else home
            ml_results.append({
                "pick": pick, "opp": opp, "score": score, "reasons": reasons,
                "away": away, "home": home, "game_key": gk,
                "home_win_pct": TEAM_STATS.get(pick, {}).get('home_win_pct', 0.5) if is_home else TEAM_STATS.get(pick, {}).get('away_win_pct', 0.5)
            })
        except: continue
    
    ml_results.sort(key=lambda x: x["score"], reverse=True)
    display_results = [r for r in ml_results if r["score"] >= 5.5]
    
    for r in display_results:
        kalshi_url = build_kalshi_ml_url(r["away"], r["home"])
        reasons_str = " • ".join([escape_html(reason) for reason in r["reasons"][:4]])
        win_pct = int(r["home_win_pct"] * 100)
        
        if r["score"] >= 8.0: border_color = "#00ff00"
        elif r["score"] >= 6.5: border_color = "#38bdf8"
        else: border_color = "#ffaa00"
        
        st.markdown(f"""<div style="display:flex;align-items:center;justify-content:space-between;background:#0f172a;padding:10px 14px;margin-bottom:6px;border-radius:6px;border-left:3px solid {border_color}">
<div style="flex:1">
<span style="color:#fff;font-weight:bold">{escape_html(r['pick'])}</span>
<span style="color:#666"> vs {escape_html(r['opp'])}</span>
<span style="color:#38bdf8;font-weight:bold;margin-left:8px">{r['score']}/10</span>
<span style="color:#888;margin-left:10px;font-size:0.85em">{reasons_str} • 🏟️ {win_pct}%</span>
</div>
<a href="{kalshi_url}" target="_blank" style="background:#00c853;color:#000;padding:8px 16px;border-radius:6px;font-weight:bold;text-decoration:none;white-space:nowrap">BUY {escape_html(r['pick'])}</a>
</div>""", unsafe_allow_html=True)
    
    existing_position_games = [p.get('game') for p in st.session_state.positions]
    untagged = [r for r in display_results if r["game_key"] not in existing_position_games]
    if untagged:
        st.markdown("")
        if st.button(f"➕ Add {len(untagged)} Picks to Positions", key="ml_add_all", use_container_width=True):
            for r in untagged:
                st.session_state.positions.append({
                    "game": r["game_key"], "type": "ml", "pick": r["pick"], "price": 50, "contracts": 1
                })
            save_positions(st.session_state.positions)
            st.success(f"✅ Added {len(untagged)} picks — scroll down to edit")
            st.rerun()
else:
    st.info("No games today — check back later!")

st.divider()

# ============================================================
# 🎯 CUSHION SCANNER
# ============================================================
st.subheader("🎯 CUSHION SCANNER")
st.caption("Find safe NO/YES totals opportunities in live games")

cs1, cs2 = st.columns([1, 1])
cush_min = cs1.selectbox("Min minutes", [6, 9, 12, 15, 18], index=0, key="cush_min")
cush_side = cs2.selectbox("Side", ["NO", "YES"], key="cush_side")

cush_results = []
for gk, g in games.items():
    mins = get_minutes_played(g['period'], g['clock'], g['status_type'])
    total = g['total']
    if g['status_type'] == "STATUS_FINAL": continue
    if mins < cush_min or mins <= 0: continue
    pace = total / mins
    remaining_min = max(48 - mins, 1)
    projected_final = round(total + pace * remaining_min)
    if cush_side == "NO":
        base_idx = next((i for i, t in enumerate(THRESHOLDS) if t > projected_final), len(THRESHOLDS)-1)
        safe_idx = min(base_idx + 2, len(THRESHOLDS) - 1)
        safe_line = THRESHOLDS[safe_idx]
        cushion = safe_line - projected_final
    else:
        base_idx = next((i for i in range(len(THRESHOLDS)-1, -1, -1) if THRESHOLDS[i] < projected_final), 0)
        safe_idx = max(base_idx - 2, 0)
        safe_line = THRESHOLDS[safe_idx]
        cushion = projected_final - safe_line
    if cushion < 6: continue
    if cush_side == "NO":
        if pace < 4.5: pace_status, pace_color = "✅ SLOW", "#00ff00"
        elif pace < 4.8: pace_status, pace_color = "⚠️ AVG", "#ffff00"
        else: pace_status, pace_color = "❌ FAST", "#ff0000"
    else:
        if pace > 5.1: pace_status, pace_color = "✅ FAST", "#00ff00"
        elif pace > 4.8: pace_status, pace_color = "⚠️ AVG", "#ffff00"
        else: pace_status, pace_color = "❌ SLOW", "#ff0000"
    cush_results.append({
        'game': gk, 'total': total, 'mins': mins, 'pace': pace,
        'pace_status': pace_status, 'pace_color': pace_color,
        'projected': projected_final, 'cushion': cushion,
        'safe_line': safe_line, 'period': g['period'], 'clock': g['clock']
    })

cush_results.sort(key=lambda x: x['cushion'], reverse=True)

if cush_results:
    for r in cush_results:
        game_parts = r['game'].split('@')
        kalshi_url = build_kalshi_totals_url(game_parts[0], game_parts[1])
        btn_color = "#00aa00" if cush_side == "NO" else "#cc6600"
        st.markdown(f"""<div style="display:flex;align-items:center;justify-content:space-between;background:#0f172a;padding:10px 14px;margin-bottom:6px;border-radius:8px;border-left:3px solid {r['pace_color']};flex-wrap:wrap;gap:8px">
        <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap">
            <b style="color:#fff">{escape_html(r['game'].replace('@', ' @ '))}</b>
            <span style="color:#888">Q{r['period']} {escape_html(str(r['clock']))}</span>
            <span style="color:#888">{r['total']}pts/{r['mins']:.0f}min</span>
            <span style="color:#888">Proj: <b style="color:#fff">{r['projected']}</b></span>
            <span style="background:#ff8800;color:#000;padding:2px 8px;border-radius:4px;font-weight:bold">🎯 {r['safe_line']}</span>
            <span style="color:#00ff00;font-weight:bold">+{r['cushion']:.0f}</span>
            <span style="color:{r['pace_color']}">{r['pace_status']}</span>
        </div>
        <a href="{kalshi_url}" target="_blank" style="background:{btn_color};color:#fff;padding:6px 14px;border-radius:6px;text-decoration:none;font-weight:bold">BUY {cush_side} {r['safe_line']}</a>
        </div>""", unsafe_allow_html=True)
else:
    st.info(f"No {cush_side} opportunities with 6+ cushion yet")

st.divider()

# ============================================================
# 🔥 PACE SCANNER
# ============================================================
st.subheader("🔥 PACE SCANNER")
st.caption("Track scoring pace for all live games")

pace_data = []
for gk, g in games.items():
    mins = get_minutes_played(g['period'], g['clock'], g['status_type'])
    if mins >= 6:
        pace = round(g['total'] / mins, 2)
        pace_data.append({
            "game": gk, "pace": pace, "proj": round(pace * 48), 
            "total": g['total'], "mins": mins, 
            "period": g['period'], "clock": g['clock'], 
            "final": g['status_type'] == "STATUS_FINAL"
        })

pace_data.sort(key=lambda x: x['pace'])

if pace_data:
    for p in pace_data:
        game_parts = p['game'].split('@')
        kalshi_url = build_kalshi_totals_url(game_parts[0], game_parts[1])
        if p['pace'] < 4.5:
            lbl, clr = "🟢 SLOW", "#00ff00"
            base_idx = next((i for i, t in enumerate(THRESHOLDS) if t > p['proj']), len(THRESHOLDS)-1)
            safe_idx = min(base_idx + 2, len(THRESHOLDS) - 1)
            rec_line = THRESHOLDS[safe_idx]
            btn_html = f'<a href="{kalshi_url}" target="_blank" style="background:#00aa00;color:#fff;padding:6px 14px;border-radius:6px;text-decoration:none;font-weight:bold">BUY NO {rec_line}</a>' if not p['final'] else ""
        elif p['pace'] < 4.8:
            lbl, clr = "🟡 AVG", "#ffff00"
            btn_html = ""
        elif p['pace'] < 5.2:
            lbl, clr = "🟠 FAST", "#ff8800"
            base_idx = next((i for i in range(len(THRESHOLDS)-1, -1, -1) if THRESHOLDS[i] < p['proj']), 0)
            safe_idx = max(base_idx - 2, 0)
            rec_line = THRESHOLDS[safe_idx]
            btn_html = f'<a href="{kalshi_url}" target="_blank" style="background:#cc6600;color:#fff;padding:6px 14px;border-radius:6px;text-decoration:none;font-weight:bold">BUY YES {rec_line}</a>' if not p['final'] else ""
        else:
            lbl, clr = "🔴 SHOOTOUT", "#ff0000"
            base_idx = next((i for i in range(len(THRESHOLDS)-1, -1, -1) if THRESHOLDS[i] < p['proj']), 0)
            safe_idx = max(base_idx - 2, 0)
            rec_line = THRESHOLDS[safe_idx]
            btn_html = f'<a href="{kalshi_url}" target="_blank" style="background:#cc0000;color:#fff;padding:6px 14px;border-radius:6px;text-decoration:none;font-weight:bold">BUY YES {rec_line}</a>' if not p['final'] else ""
        status = "FINAL" if p['final'] else f"Q{p['period']} {p['clock']}"
        st.markdown(f"""<div style="display:flex;align-items:center;justify-content:space-between;background:#0f172a;padding:8px 12px;margin-bottom:4px;border-radius:6px;border-left:3px solid {clr};flex-wrap:wrap;gap:8px">
        <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">
            <b style="color:#fff">{escape_html(p['game'].replace('@', ' @ '))}</b>
            <span style="color:#666">{status}</span>
            <span style="color:#888">{p['total']}pts/{p['mins']:.0f}min</span>
            <span style="color:{clr};font-weight:bold">{p['pace']}/min {lbl}</span>
            <span style="color:#888">Proj: <b style="color:#fff">{p['proj']}</b></span>
        </div>
        <div>{btn_html}</div>
        </div>""", unsafe_allow_html=True)
else:
    st.info("No games with 6+ minutes played yet")

st.divider()

# ============================================================
# 📈 ACTIVE POSITIONS
# ============================================================
st.subheader("📈 ACTIVE POSITIONS")

if st.session_state.positions:
    for idx, pos in enumerate(st.session_state.positions):
        gk = pos['game']
        g = games.get(gk)
        price, contracts = pos.get('price', 50), pos.get('contracts', 1)
        pos_type = pos.get('type', 'ml')
        cost = round(price * contracts / 100, 2)
        potential = round((100 - price) * contracts / 100, 2)
        
        if g:
            pick = pos.get('pick', '')
            parts = gk.split("@")
            if pos_type == 'ml':
                pick_score = g['home_score'] if pick == parts[1] else g['away_score']
                opp_score = g['away_score'] if pick == parts[1] else g['home_score']
                lead = pick_score - opp_score
            else:
                pick_score = g['total']
                opp_score = 0
                lead = 0
            
            is_final = g['status_type'] == "STATUS_FINAL"
            
            if pos_type == 'ml':
                if is_final:
                    won = pick_score > opp_score
                    label, clr = ("✅ WON", "#00ff00") if won else ("❌ LOST", "#ff0000")
                    pnl = f"+${potential:.2f}" if won else f"-${cost:.2f}"
                elif g['period'] > 0:
                    if lead >= 10: label, clr = "🟢 CRUISING", "#00ff00"
                    elif lead >= 0: label, clr = "🟡 CLOSE", "#ffff00"
                    else: label, clr = "🔴 BEHIND", "#ff0000"
                    pnl = f"Win: +${potential:.2f}"
                else:
                    label, clr = "⏳ PENDING", "#888"
                    pnl = f"Win: +${potential:.2f}"
            else:
                # TOTALS - Use pace-based labels
                threshold = float(str(pos.get('pick', '230.5')).split()[-1]) if pos.get('pick') else 230.5
                side = 'YES' if 'YES' in str(pos.get('pick', '')).upper() else 'NO'
                if is_final:
                    won = (g['total'] > threshold) if side == 'YES' else (g['total'] < threshold)
                    label, clr = ("✅ WON", "#00ff00") if won else ("❌ LOST", "#ff0000")
                    pnl = f"+${potential:.2f}" if won else f"-${cost:.2f}"
                elif g['period'] > 0:
                    mins = get_minutes_played(g['period'], g['clock'], g['status_type'])
                    pace_val = g['total'] / mins if mins > 0 else 0
                    # Pace-based status for totals
                    if side == 'NO':
                        if pace_val < 4.5: label, clr = "🟢 VERY SAFE", "#00ff00"
                        elif pace_val < 4.8: label, clr = "🟡 WARNING", "#ffff00"
                        else: label, clr = "🔴 DANGER", "#ff0000"
                    else:  # YES
                        if pace_val > 5.2: label, clr = "🟢 VERY SAFE", "#00ff00"
                        elif pace_val > 4.8: label, clr = "🟡 WARNING", "#ffff00"
                        else: label, clr = "🔴 DANGER", "#ff0000"
                    pnl = f"Win: +${potential:.2f}"
                else:
                    label, clr = "⏳ PENDING", "#888"
                    pnl = f"Win: +${potential:.2f}"
            
            status = "FINAL" if is_final else f"Q{g['period']} {g['clock']}" if g['period'] > 0 else "Scheduled"
            type_label = "ML" if pos_type == "ml" else "TOTAL"
            
            st.markdown(f"""<div style='background:#1a1a2e;padding:10px;border-radius:6px;border-left:3px solid {clr};margin-bottom:6px'>
                <div style='display:flex;justify-content:space-between'><b style='color:#fff'>{escape_html(gk.replace('@', ' @ '))}</b> <span style='color:#888'>{status}</span> <b style='color:{clr}'>{label}</b></div>
                <div style='color:#aaa;margin-top:4px;font-size:0.8em'>🎯 {type_label}: {escape_html(str(pick))} | {contracts}x @ {price}¢ | {pnl}</div></div>""", unsafe_allow_html=True)
            
            c1, c2, c3 = st.columns([2, 1, 1])
            with c2:
                if st.button("✏️ Edit", key=f"edit_{idx}"):
                    st.session_state.editing_position = idx if st.session_state.editing_position != idx else None
                    st.rerun()
            with c3:
                if st.button("🗑️", key=f"del_{idx}"):
                    st.session_state.positions.pop(idx)
                    save_positions(st.session_state.positions)
                    st.rerun()
            
            if st.session_state.editing_position == idx:
                ec1, ec2, ec3 = st.columns(3)
                with ec1: new_type = st.selectbox("Type", ["ml", "totals"], index=0 if pos_type == "ml" else 1, key=f"et_{idx}")
                with ec2: new_price = st.number_input("Price ¢", 1, 99, price, key=f"ep_{idx}")
                with ec3: new_contracts = st.number_input("Contracts", 1, 100, contracts, key=f"ec_{idx}")
                if new_type == "ml":
                    new_pick = st.radio("Pick", [parts[1], parts[0]], index=0 if pick == parts[1] else 1, horizontal=True, key=f"epk_{idx}")
                else:
                    tc1, tc2 = st.columns(2)
                    with tc1: side = st.radio("Side", ["YES", "NO"], horizontal=True, key=f"es_{idx}")
                    with tc2: line = st.selectbox("Line", THRESHOLDS, index=5, key=f"el_{idx}")
                    new_pick = f"{side} {line}"
                bc1, bc2 = st.columns(2)
                with bc1:
                    if st.button("💾 Save", key=f"sv_{idx}", type="primary", use_container_width=True):
                        st.session_state.positions[idx] = {"game": gk, "type": new_type, "pick": new_pick, "price": new_price, "contracts": new_contracts}
                        save_positions(st.session_state.positions)
                        st.session_state.editing_position = None
                        st.rerun()
                with bc2:
                    if st.button("❌ Cancel", key=f"cn_{idx}", use_container_width=True):
                        st.session_state.editing_position = None
                        st.rerun()
        else:
            st.markdown(f"<div style='background:#1a1a2e;padding:10px;border-radius:6px;border-left:3px solid #888;margin-bottom:6px;color:#888'>{escape_html(gk)} — Game not found</div>", unsafe_allow_html=True)
            if st.button("🗑️", key=f"del_old_{idx}"):
                st.session_state.positions.pop(idx)
                save_positions(st.session_state.positions)
                st.rerun()
    
    if st.button("🗑️ Clear All Positions", key="clear_all_pos", use_container_width=True):
        st.session_state.positions = []
        st.session_state.editing_position = None
        save_positions(st.session_state.positions)
        st.rerun()
else:
    st.info("No active positions — use 'Add Picks to Positions' above or add manually below")

st.divider()

# ============================================================
# ➕ ADD POSITION
# ============================================================
st.subheader("➕ ADD POSITION")

game_opts = ["Select..."] + [gk.replace("@", " @ ") for gk in game_list]
sel = st.selectbox("Game", game_opts, key="add_game_select")

if sel != "Select...":
    parts = sel.replace(" @ ", "@").split("@")
    pos_type = st.radio("Type", ["Moneyline", "Totals"], horizontal=True, key="add_type_radio")
    
    if pos_type == "Moneyline":
        p1, p2, p3 = st.columns(3)
        with p1: add_pick = st.radio("Pick", [parts[1], parts[0]], horizontal=True, key="add_pick_radio")
        price = p2.number_input("Price ¢", 1, 99, 50, key="add_price_ml")
        contracts = p3.number_input("Contracts", 1, 100, 1, key="add_qty_ml")
        if st.button("✅ ADD ML POSITION", key="add_ml_btn", use_container_width=True, type="primary"):
            gk = sel.replace(" @ ", "@")
            st.session_state.positions.append({"game": gk, "type": "ml", "pick": add_pick, "price": price, "contracts": contracts})
            save_positions(st.session_state.positions)
            st.rerun()
    else:
        t1, t2 = st.columns(2)
        with t1: side = st.radio("Side", ["YES", "NO"], horizontal=True, key="add_side_radio")
        with t2: line = st.selectbox("Line", THRESHOLDS, index=5, key="add_line_select")
        p2, p3 = st.columns(2)
        price = p2.number_input("Price ¢", 1, 99, 50, key="add_price_tot")
        contracts = p3.number_input("Contracts", 1, 100, 1, key="add_qty_tot")
        if st.button("✅ ADD TOTALS POSITION", key="add_tot_btn", use_container_width=True, type="primary"):
            gk = sel.replace(" @ ", "@")
            st.session_state.positions.append({"game": gk, "type": "totals", "pick": f"{side} {line}", "price": price, "contracts": contracts})
            save_positions(st.session_state.positions)
            st.rerun()

st.divider()

# ============================================================
# 📺 ALL GAMES
# ============================================================
st.subheader("📺 ALL GAMES")
if games:
    for gk, g in games.items():
        away, home = g['away_team'], g['home_team']
        if g['status_type'] == "STATUS_FINAL":
            winner = home if g['home_score'] > g['away_score'] else away
            status, clr = f"✅ {escape_html(winner)}", "#44ff44"
        elif g['period'] > 0:
            status, clr = f"🔴 Q{g['period']} {g['clock']}", "#ff4444"
        else:
            status, clr = "📅 Scheduled", "#888"
        st.markdown(f"""<div style="display:flex;justify-content:space-between;background:#0f172a;padding:8px 12px;margin-bottom:4px;border-radius:5px;border-left:2px solid {clr}">
            <div><b style="color:#fff">{escape_html(away)}</b> {g['away_score']} @ <b style="color:#fff">{escape_html(home)}</b> {g['home_score']}</div>
            <span style="color:{clr}">{status}</span>
        </div>""", unsafe_allow_html=True)
else:
    st.info("No games today")

st.divider()
st.caption("⚠️ Educational only. Not financial advice. v18.7")
