import streamlit as st
import requests
from datetime import datetime, timedelta
import pytz
import time
import json

st.set_page_config(page_title="NBA Edge Finder", page_icon="🏀", layout="wide")

st.markdown("""
<script async src="https://www.googletagmanager.com/gtag/js?id=G-NQKY5VQ376"></script>
<script>window.dataLayer = window.dataLayer || [];function gtag(){dataLayer.push(arguments);}gtag('js', new Date());gtag('config', 'G-NQKY5VQ376');</script>
""", unsafe_allow_html=True)

if 'authenticated' not in st.session_state or not st.session_state.authenticated:
    st.warning("⚠️ Please log in from the Home page first.")
    st.page_link("Home.py", label="🏠 Go to Home", use_container_width=True)
    st.stop()

today_str = datetime.now(pytz.timezone("US/Eastern")).strftime("%Y-%m-%d")
POSITIONS_FILE = "positions.json"

def load_positions():
    try:
        with open(POSITIONS_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def save_positions(positions):
    try:
        with open(POSITIONS_FILE, 'w') as f:
            json.dump(positions, f)
    except:
        pass

st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
div[role="radiogroup"] label { cursor: pointer; }
div[role="radiogroup"] label span { padding: 8px 18px; border-radius: 10px; display: inline-block; font-weight: 700; }
div[role="radiogroup"] input:checked + div span { box-shadow: inset 0 0 0 2px white; }
div[role="radiogroup"] label:nth-of-type(1) span { background: linear-gradient(135deg, #102a1a, #163a26); border: 2px solid #00ff88; color: #ccffee; }
div[role="radiogroup"] label:nth-of-type(2) span { background: linear-gradient(135deg, #2a1515, #3a1a1a); border: 2px solid #ff4444; color: #ffcccc; }
.buy-btn { display: inline-block; padding: 5px 12px; border-radius: 5px; text-decoration: none; font-weight: bold; font-size: 0.85em; margin-left: 8px; }
.buy-no { background: #00aa00; color: #fff; }
.buy-yes { background: #cc6600; color: #fff; }
.buy-btn:hover { opacity: 0.85; }
</style>
""", unsafe_allow_html=True)

if 'auto_refresh' not in st.session_state: st.session_state.auto_refresh = False
if "positions" not in st.session_state: st.session_state.positions = load_positions()
if "selected_side" not in st.session_state: st.session_state.selected_side = "NO"
if "selected_threshold" not in st.session_state: st.session_state.selected_threshold = 225.5
if "selected_ml_pick" not in st.session_state: st.session_state.selected_ml_pick = None

if st.session_state.auto_refresh:
    st.markdown(f'<meta http-equiv="refresh" content="30;url=?r={int(time.time())+30}">', unsafe_allow_html=True)
    auto_status = "🔄 Auto-refresh ON (30s)"
else:
    auto_status = "⏸️ Auto-refresh OFF"

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
    "Atlanta": {"pace": 100.5, "def_rank": 26, "net_rating": -3.2, "home_win_pct": 0.52},
    "Boston": {"pace": 99.8, "def_rank": 2, "net_rating": 11.2, "home_win_pct": 0.78},
    "Brooklyn": {"pace": 98.2, "def_rank": 22, "net_rating": -4.5, "home_win_pct": 0.42},
    "Charlotte": {"pace": 99.5, "def_rank": 28, "net_rating": -6.8, "home_win_pct": 0.38},
    "Chicago": {"pace": 98.8, "def_rank": 20, "net_rating": -2.1, "home_win_pct": 0.48},
    "Cleveland": {"pace": 97.2, "def_rank": 3, "net_rating": 8.5, "home_win_pct": 0.75},
    "Dallas": {"pace": 99.0, "def_rank": 12, "net_rating": 4.2, "home_win_pct": 0.62},
    "Denver": {"pace": 98.5, "def_rank": 10, "net_rating": 5.8, "home_win_pct": 0.72},
    "Detroit": {"pace": 97.8, "def_rank": 29, "net_rating": -8.2, "home_win_pct": 0.32},
    "Golden State": {"pace": 100.2, "def_rank": 8, "net_rating": 3.5, "home_win_pct": 0.65},
    "Houston": {"pace": 101.5, "def_rank": 18, "net_rating": 1.2, "home_win_pct": 0.55},
    "Indiana": {"pace": 103.5, "def_rank": 24, "net_rating": 2.8, "home_win_pct": 0.58},
    "LA Clippers": {"pace": 98.0, "def_rank": 14, "net_rating": 1.5, "home_win_pct": 0.55},
    "LA Lakers": {"pace": 99.5, "def_rank": 15, "net_rating": 2.2, "home_win_pct": 0.58},
    "Memphis": {"pace": 100.8, "def_rank": 6, "net_rating": 4.5, "home_win_pct": 0.68},
    "Miami": {"pace": 97.5, "def_rank": 5, "net_rating": 3.8, "home_win_pct": 0.65},
    "Milwaukee": {"pace": 99.2, "def_rank": 9, "net_rating": 5.2, "home_win_pct": 0.70},
    "Minnesota": {"pace": 98.8, "def_rank": 4, "net_rating": 7.5, "home_win_pct": 0.72},
    "New Orleans": {"pace": 100.0, "def_rank": 16, "net_rating": 1.8, "home_win_pct": 0.55},
    "New York": {"pace": 98.5, "def_rank": 7, "net_rating": 6.2, "home_win_pct": 0.68},
    "Oklahoma City": {"pace": 99.8, "def_rank": 1, "net_rating": 12.5, "home_win_pct": 0.82},
    "Orlando": {"pace": 97.0, "def_rank": 11, "net_rating": 3.2, "home_win_pct": 0.62},
    "Philadelphia": {"pace": 98.2, "def_rank": 13, "net_rating": 2.5, "home_win_pct": 0.58},
    "Phoenix": {"pace": 99.0, "def_rank": 17, "net_rating": 2.0, "home_win_pct": 0.60},
    "Portland": {"pace": 99.5, "def_rank": 27, "net_rating": -5.5, "home_win_pct": 0.40},
    "Sacramento": {"pace": 101.2, "def_rank": 19, "net_rating": 0.8, "home_win_pct": 0.55},
    "San Antonio": {"pace": 100.5, "def_rank": 25, "net_rating": -4.8, "home_win_pct": 0.42},
    "Toronto": {"pace": 98.8, "def_rank": 21, "net_rating": -1.5, "home_win_pct": 0.48},
    "Utah": {"pace": 100.2, "def_rank": 30, "net_rating": -7.5, "home_win_pct": 0.35},
    "Washington": {"pace": 101.0, "def_rank": 23, "net_rating": -6.2, "home_win_pct": 0.38}
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

H2H_EDGES = {
    ("Boston", "Philadelphia"): 0.5, ("Boston", "New York"): 0.5, ("Milwaukee", "Chicago"): 0.5,
    ("Cleveland", "Detroit"): 0.5, ("Oklahoma City", "Utah"): 0.5, ("Denver", "Minnesota"): 0.5,
    ("LA Lakers", "LA Clippers"): 0.3, ("Golden State", "Sacramento"): 0.5, ("Phoenix", "Portland"): 0.5,
    ("Miami", "Orlando"): 0.5, ("Dallas", "San Antonio"): 0.5, ("Memphis", "New Orleans"): 0.3,
}

with st.sidebar:
    st.page_link("Home.py", label="🏠 Home", use_container_width=True)
    st.divider()
    st.header("🔗 KALSHI")
    st.caption("⚠️ NBA not on trade API yet")
    st.divider()
    st.caption("v15.57 🛡️+2 SAFE")

def build_kalshi_ml_url(away_team, home_team):
    away_code = KALSHI_CODES.get(away_team, "xxx").upper()
    home_code = KALSHI_CODES.get(home_team, "xxx").upper()
    today = datetime.now(pytz.timezone('US/Eastern'))
    date_str = today.strftime("%y%b%d").upper()
    return f"https://kalshi.com/markets/KXNBAGAME/KXNBAGAME-{date_str}{away_code}{home_code}"

def build_kalshi_totals_url(away_team, home_team):
    away_code = KALSHI_CODES.get(away_team, "xxx").upper()
    home_code = KALSHI_CODES.get(home_team, "xxx").upper()
    today = datetime.now(pytz.timezone('US/Eastern'))
    date_str = today.strftime("%y%b%d").upper()
    return f"https://kalshi.com/markets/KXNBATOTAL/KXNBATOTAL-{date_str}{away_code}{home_code}"

def calc_distance(loc1, loc2):
    from math import radians, sin, cos, sqrt, atan2
    lat1, lon1 = radians(loc1[0]), radians(loc1[1])
    lat2, lon2 = radians(loc2[0]), radians(loc2[1])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    return 3959 * 2 * atan2(sqrt(a), sqrt(1-a))

def fetch_espn_scores():
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
        for team_data in data.get("injuries", []):
            team_name = team_data.get("displayName", "")
            team_key = TEAM_ABBREVS.get(team_name, team_name)
            if not team_key: continue
            injuries[team_key] = []
            for player in team_data.get("injuries", []):
                athlete = player.get("athlete", {})
                name = athlete.get("displayName", "")
                status = player.get("status", "")
                if name:
                    injuries[team_key].append({"name": name, "status": status})
    except:
        pass
    return injuries

@st.cache_data(ttl=3600)
def fetch_all_team_forms():
    eastern = pytz.timezone('US/Eastern')
    team_results = {team: [] for team in TEAM_STATS.keys()}
    for days_ago in range(1, 15):
        all_done = all(len(r) >= 5 for r in team_results.values())
        if all_done: break
        check_date = (datetime.now(eastern) - timedelta(days=days_ago)).strftime('%Y%m%d')
        url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={check_date}"
        try:
            resp = requests.get(url, timeout=8)
            data = resp.json()
            for event in data.get("events", []):
                status = event.get("status", {}).get("type", {}).get("name", "")
                if status != "STATUS_FINAL": continue
                comp = event.get("competitions", [{}])[0]
                competitors = comp.get("competitors", [])
                if len(competitors) < 2: continue
                scores = {}
                for c in competitors:
                    full_name = c.get("team", {}).get("displayName", "")
                    team = TEAM_ABBREVS.get(full_name, full_name)
                    score = int(c.get("score", 0) or 0)
                    scores[team] = score
                teams = list(scores.keys())
                if len(teams) == 2:
                    t1, t2 = teams[0], teams[1]
                    s1, s2 = scores[t1], scores[t2]
                    if t1 in team_results and len(team_results[t1]) < 5:
                        team_results[t1].append("W" if s1 > s2 else "L")
                    if t2 in team_results and len(team_results[t2]) < 5:
                        team_results[t2].append("W" if s2 > s1 else "L")
        except:
            continue
    forms = {}
    for team, results in team_results.items():
        if results:
            form = "".join(results[:5])
            while len(form) < 5: form += "-"
            forms[team] = form
        else:
            forms[team] = "-----"
    return forms

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
    if away_team in yesterday_teams and home_team not in yesterday_teams:
        score_home += 1.0
        reasons_home.append("🛏️ Opp B2B")
    elif home_team in yesterday_teams and away_team not in yesterday_teams:
        score_away += 1.0
        reasons_away.append("🛏️ Opp B2B")
    home_net, away_net = home.get('net_rating', 0), away.get('net_rating', 0)
    if home_net - away_net > 5:
        score_home += 1.0
        reasons_home.append(f"📊 Net +{home_net:.1f}")
    elif away_net - home_net > 5:
        score_away += 1.0
        reasons_away.append(f"📊 Net +{away_net:.1f}")
    if home.get('def_rank', 15) <= 5:
        score_home += 1.0
        reasons_home.append(f"🛡️ #{home.get('def_rank')} DEF")
    if away.get('def_rank', 15) <= 5:
        score_away += 1.0
        reasons_away.append(f"🛡️ #{away.get('def_rank')} DEF")
    score_home += 1.0
    home_inj, home_stars = get_injury_score(home_team, injuries)
    away_inj, away_stars = get_injury_score(away_team, injuries)
    if away_inj - home_inj > 3:
        score_home += 2.0
        if away_stars: reasons_home.append(f"🏥 {away_stars[0][:10]} OUT")
    elif home_inj - away_inj > 3:
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
    h2h = H2H_EDGES.get((home_team, away_team), 0) or H2H_EDGES.get((away_team, home_team), 0)
    if H2H_EDGES.get((home_team, away_team), 0) > 0:
        score_home += h2h
        reasons_home.append("🆚 H2H")
    elif H2H_EDGES.get((away_team, home_team), 0) > 0:
        score_away += h2h
        reasons_away.append("🆚 H2H")
    total = score_home + score_away
    if total > 0:
        home_final = round((score_home / total) * 10, 1)
        away_final = round((score_away / total) * 10, 1)
    else:
        home_final, away_final = 5.0, 5.0
    if home_final >= away_final:
        return home_team, home_final, reasons_home[:4]
    else:
        return away_team, away_final, reasons_away[:4]

def get_signal_tier(score):
    if score >= 8.0: return "🟢 STRONG BUY", "#00ff00"
    elif score >= 6.5: return "🔵 BUY", "#00aaff"
    elif score >= 5.5: return "🟡 LEAN", "#ffff00"
    else: return "⚪ TOSS-UP", "#888888"

# FETCH DATA
games = fetch_espn_scores()
game_list = sorted(list(games.keys()))
yesterday_teams_raw = fetch_yesterday_teams()
injuries = fetch_espn_injuries()
team_forms = fetch_all_team_forms()
now = datetime.now(pytz.timezone('US/Eastern'))

today_teams = set()
for gk in games.keys():
    parts = gk.split("@")
    today_teams.add(parts[0])
    today_teams.add(parts[1])
yesterday_teams = yesterday_teams_raw.intersection(today_teams)

# HEADER
st.title("🏀 NBA EDGE FINDER")
hdr1, hdr2, hdr3 = st.columns([3, 1, 1])
hdr1.caption(f"{auto_status} | {now.strftime('%I:%M:%S %p ET')} | v15.57")
if hdr2.button("🔄 Auto" if not st.session_state.auto_refresh else "⏹️ Stop", use_container_width=True):
    st.session_state.auto_refresh = not st.session_state.auto_refresh
    st.rerun()
if hdr3.button("🔄 Refresh", use_container_width=True):
    st.rerun()

# ACTIVE POSITIONS
st.subheader("📈 ACTIVE POSITIONS")
if st.session_state.positions:
    for idx, pos in enumerate(st.session_state.positions):
        game_key = pos['game']
        g = games.get(game_key)
        if g:
            is_final = g['status_type'] == "STATUS_FINAL"
            game_status = "FINAL" if is_final else f"Q{g['period']} {g['clock']}"
            if pos.get('type') == 'ml':
                pick = pos.get('pick', '')
                parts = game_key.split("@")
                away_team, home_team = parts[0], parts[1]
                pick_score = g['home_score'] if pick == home_team else g['away_score']
                opp_score = g['away_score'] if pick == home_team else g['home_score']
                lead = pick_score - opp_score
                if is_final:
                    status_label, status_color = ("✅ WON", "#00ff00") if pick_score > opp_score else ("❌ LOST", "#ff0000")
                elif lead >= 15: status_label, status_color = "🟢 CRUISING", "#00ff00"
                elif lead >= 8: status_label, status_color = "🟢 LEADING", "#00cc00"
                elif lead >= 1: status_label, status_color = "🟡 AHEAD", "#ffff00"
                elif lead >= -5: status_label, status_color = "🟠 CLOSE", "#ff8800"
                else: status_label, status_color = "🔴 BEHIND", "#ff0000"
                col1, col2 = st.columns([10, 1])
                col1.markdown(f"""<div style="display:flex;align-items:center;justify-content:space-between;background:linear-gradient(135deg,#1a1a2e,#0f0f1a);padding:10px;margin-bottom:4px;border-radius:8px;border-left:4px solid {status_color}">
                <div><b style="color:#fff">ML: {pick}</b> <span style="color:#666">({game_key.replace('@',' @ ')})</span></div>
                <div style="display:flex;gap:15px;align-items:center">
                <span style="color:#888">{game_status}</span>
                <span style="color:#fff">{pick_score}-{opp_score}</span>
                <span style="color:{status_color};font-weight:bold">{status_label}</span>
                </div></div>""", unsafe_allow_html=True)
                if col2.button("🗑️", key=f"del_{idx}"):
                    st.session_state.positions.pop(idx)
                    save_positions(st.session_state.positions)
                    st.rerun()
            else:
                side = pos.get('side', 'NO')
                threshold = pos.get('threshold', 225.5)
                total = g['total']
                cushion = threshold - total if side == "NO" else total - threshold
                if is_final:
                    won = (side == "NO" and total < threshold) or (side == "YES" and total > threshold)
                    status_label, status_color = ("✅ WON", "#00ff00") if won else ("❌ LOST", "#ff0000")
                elif cushion >= 15: status_label, status_color = "🟢 VERY SAFE", "#00ff00"
                elif cushion >= 8: status_label, status_color = "🟢 LOOKING GOOD", "#00cc00"
                elif cushion >= 3: status_label, status_color = "🟡 ON TRACK", "#ffff00"
                elif cushion >= -3: status_label, status_color = "🟠 WARNING", "#ff8800"
                else: status_label, status_color = "🔴 AT RISK", "#ff0000"
                col1, col2 = st.columns([10, 1])
                col1.markdown(f"""<div style="display:flex;align-items:center;justify-content:space-between;background:linear-gradient(135deg,#1a1a2e,#0f0f1a);padding:10px;margin-bottom:4px;border-radius:8px;border-left:4px solid {status_color}">
                <div><b style="color:#fff">{side} {threshold}</b> <span style="color:#666">({game_key.replace('@',' @ ')})</span></div>
                <div style="display:flex;gap:15px;align-items:center">
                <span style="color:#888">{game_status}</span>
                <span style="color:#fff">Total: {total}</span>
                <span style="color:{status_color};font-weight:bold">{status_label} ({'+' if cushion >= 0 else ''}{cushion:.0f})</span>
                </div></div>""", unsafe_allow_html=True)
                if col2.button("🗑️", key=f"del_{idx}"):
                    st.session_state.positions.pop(idx)
                    save_positions(st.session_state.positions)
                    st.rerun()
    if st.button("🗑️ Clear All Positions", use_container_width=True):
        st.session_state.positions = []
        save_positions(st.session_state.positions)
        st.rerun()
else:
    st.info("No positions tracked — add from ML PICKS or form below")

st.divider()
if yesterday_teams:
    st.info(f"📅 **B2B**: {', '.join(sorted(yesterday_teams))}")
st.divider()

# ML PICKS WITH FORM
st.subheader("🎯 ML PICKS")
ml_results = []
for game_key, g in games.items():
    away, home = g["away_team"], g["home_team"]
    try:
        pick, score, reasons = calc_ml_score(home, away, yesterday_teams, injuries)
        tier, color = get_signal_tier(score)
        ml_results.append({"pick": pick, "score": score, "color": color, "reasons": reasons, "away": away, "home": home})
    except:
        continue

ml_results.sort(key=lambda x: x["score"], reverse=True)
for r in ml_results:
    if r["score"] < 5.5: continue
    opp_team = r["away"] if r["pick"] == r["home"] else r["home"]
    pick_form = team_forms.get(r["pick"], "-----")
    opp_form = team_forms.get(opp_team, "-----")
    kalshi_url = build_kalshi_ml_url(r["away"], r["home"])
    reasons = " • ".join(r["reasons"])
    pw = pick_form.count("W")
    ow = opp_form.count("W")
    pclr = "#00ff00" if pw >= 4 else "#88ff00" if pw >= 3 else "#ffff00" if pw >= 2 else "#ff4444"
    oclr = "#00ff00" if ow >= 4 else "#88ff00" if ow >= 3 else "#ffff00" if ow >= 2 else "#ff4444"
    st.markdown(f"""<div style="background:linear-gradient(135deg,#0f172a,#020617);padding:10px 14px;margin-bottom:6px;border-radius:8px;border-left:4px solid {r['color']}">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px">
        <div>
            <b style="color:#fff;font-size:1.1em">{r['pick']}</b> 
            <span style="color:#666">vs {opp_team}</span> 
            <span style="color:#38bdf8;font-weight:bold;margin-left:8px">{r['score']}/10</span>
        </div>
        <a href="{kalshi_url}" target="_blank" style="background:#16a34a;color:#fff;padding:6px 14px;border-radius:6px;text-decoration:none;font-weight:700">BUY {r['pick'][:3].upper()}</a>
    </div>
    <div style="display:flex;align-items:center;gap:15px">
        <span style="color:#888">📊 Form:</span>
        <span style="color:{pclr};font-weight:bold;font-family:monospace;font-size:1.1em;letter-spacing:2px">{pick_form}</span>
        <span style="color:#555">vs</span>
        <span style="color:{oclr};font-family:monospace;font-size:1.1em;letter-spacing:2px">{opp_form}</span>
        <span style="color:#666;font-size:0.85em">({pw}-{5-pw} vs {ow}-{5-ow})</span>
    </div>
    <div style="color:#777;font-size:0.85em;margin-top:4px">{reasons}</div>
    </div>""", unsafe_allow_html=True)

strong_picks = [r for r in ml_results if r["score"] >= 6.5]
if strong_picks:
    if st.button(f"➕ Add {len(strong_picks)} Picks", use_container_width=True):
        added = 0
        for r in strong_picks:
            game_key = f"{r['away']}@{r['home']}"
            if not any(p.get('game') == game_key and p.get('type') == 'ml' for p in st.session_state.positions):
                st.session_state.positions.append({"game": game_key, "type": "ml", "pick": r['pick'], "price": 50, "contracts": 1})
                added += 1
        if added > 0:
            save_positions(st.session_state.positions)
            st.success(f"✅ Added {added} picks")
            st.rerun()

st.divider()

# ADD POSITION
st.subheader("➕ ADD POSITION")
game_options = ["Select..."] + [gk.replace("@", " @ ") for gk in game_list]
selected_game = st.selectbox("Game", game_options)
if selected_game != "Select...":
    parts = selected_game.replace(" @ ", "@").split("@")
    st.link_button("🔗 View on Kalshi", build_kalshi_ml_url(parts[0], parts[1]), use_container_width=True)
market_type = st.radio("Type", ["Moneyline (Winner)", "Totals (Over/Under)"], horizontal=True)
p1, p2 = st.columns(2)
with p1:
    if selected_game != "Select..." and market_type == "Moneyline (Winner)":
        parts = selected_game.replace(" @ ", "@").split("@")
        st.session_state.selected_ml_pick = st.radio("Pick", [parts[1], parts[0]], horizontal=True)
    elif market_type == "Totals (Over/Under)":
        st.session_state.selected_side = st.radio("Side", ["NO", "YES"], horizontal=True)
with p2:
    if market_type == "Totals (Over/Under)":
        st.session_state.selected_threshold = st.number_input("Line", min_value=180.0, max_value=280.0, value=225.5, step=0.5)
if st.button("✅ ADD POSITION", use_container_width=True, type="primary"):
    if selected_game == "Select...":
        st.error("Select a game first!")
    else:
        game_key = selected_game.replace(" @ ", "@")
        if market_type == "Moneyline (Winner)":
            st.session_state.positions.append({"game": game_key, "type": "ml", "pick": st.session_state.selected_ml_pick, "price": 50, "contracts": 1})
        else:
            st.session_state.positions.append({"game": game_key, "type": "totals", "side": st.session_state.selected_side, "threshold": st.session_state.selected_threshold, "price": 50, "contracts": 1})
        save_positions(st.session_state.positions)
        st.rerun()

st.divider()

# CUSHION SCANNER
st.subheader("🎯 CUSHION SCANNER")
THRESHOLDS = [210.5, 215.5, 220.5, 225.5, 230.5, 235.5, 240.5, 245.5, 250.5, 255.5]
cs1, cs2 = st.columns(2)
cush_min = cs1.selectbox("Min minutes", [6, 9, 12, 15, 18], index=0)
cush_side = cs2.selectbox("Side", ["NO", "YES"])

cush_results = []
for gk, g in games.items():
    mins = get_minutes_played(g['period'], g['clock'], g['status_type'])
    if g['status_type'] == "STATUS_FINAL" or mins < cush_min or mins <= 0: continue
    pace = g['total'] / mins
    proj = round(g['total'] + pace * max(48 - mins, 1))
    if cush_side == "NO":
        # Find first threshold > proj, then go 2 brackets higher for safety
        base_idx = next((i for i, t in enumerate(THRESHOLDS) if t > proj), len(THRESHOLDS)-1)
        safe_idx = min(base_idx + 2, len(THRESHOLDS) - 1)
        safe_line = THRESHOLDS[safe_idx]
        cushion = safe_line - proj
        pace_ok = pace < 4.6
    else:
        # Find first threshold < proj, then go 2 brackets lower for safety
        base_idx = next((i for i in range(len(THRESHOLDS)-1, -1, -1) if THRESHOLDS[i] < proj), 0)
        safe_idx = max(base_idx - 2, 0)
        safe_line = THRESHOLDS[safe_idx]
        cushion = proj - safe_line
        pace_ok = pace > 5.1
    if cushion >= 6:
        cush_results.append({'game': gk, 'total': g['total'], 'proj': proj, 'cushion': cushion, 'safe_line': safe_line, 'pace': pace, 'pace_ok': pace_ok, 'period': g['period'], 'clock': g['clock']})

cush_results.sort(key=lambda x: x['cushion'], reverse=True)
if cush_results:
    for r in cush_results:
        pclr = "#00ff00" if r['pace_ok'] else "#ff4444"
        game_parts = r['game'].split('@')
        away_t, home_t = game_parts[0], game_parts[1]
        kalshi_url = build_kalshi_totals_url(away_t, home_t)
        btn_color = "#00aa00" if cush_side == "NO" else "#cc6600"
        btn_text = f"BUY {cush_side} {r['safe_line']}"
        
        st.markdown(f"""<div style="display:flex;align-items:center;justify-content:space-between;background:linear-gradient(135deg,#0f172a,#020617);padding:10px 14px;margin-bottom:6px;border-radius:8px;border-left:4px solid {pclr}">
        <div><b style="color:#fff">{r['game'].replace('@', ' @ ')}</b> <span style="color:#666">Q{r['period']} {r['clock']}</span></div>
        <div style="display:flex;gap:12px;align-items:center">
        <span style="color:#888">Total: <b style="color:#fff">{r['total']}</b></span>
        <span style="color:#888">Proj: <b style="color:#fff">{r['proj']}</b></span>
        <span style="color:#00ff00;font-weight:bold">+{r['cushion']:.0f}</span>
        <span style="color:{pclr}">{r['pace']:.2f}/min</span>
        <span style="color:#888;font-size:0.8em">🛡️+2</span>
        <a href="{kalshi_url}" target="_blank" style="background:{btn_color};color:#fff;padding:6px 14px;border-radius:6px;text-decoration:none;font-weight:bold">{btn_text}</a>
        </div></div>""", unsafe_allow_html=True)
else:
    st.info(f"No {cush_side} opportunities with 6+ cushion")

st.divider()

# PACE SCANNER
st.subheader("🔥 PACE SCANNER")
pace_data = []
for gk, g in games.items():
    mins = get_minutes_played(g['period'], g['clock'], g['status_type'])
    if mins >= 6:
        pace = round(g['total'] / mins, 2)
        pace_data.append({"game": gk, "pace": pace, "proj": round(pace * 48), "total": g['total'], "mins": mins, "period": g['period'], "clock": g['clock'], "final": g['status_type'] == "STATUS_FINAL"})

pace_data.sort(key=lambda x: x['pace'])
if pace_data:
    for p in pace_data:
        game_parts = p['game'].split('@')
        away_t, home_t = game_parts[0], game_parts[1]
        kalshi_url = build_kalshi_totals_url(away_t, home_t)
        status = "FINAL" if p['final'] else f"Q{p['period']} {p['clock']}"
        
        if p['pace'] < 4.5:
            lbl, clr = "🟢 SLOW", "#00ff00"
            base_idx = next((i for i, t in enumerate(THRESHOLDS) if t > p['proj']), len(THRESHOLDS)-1)
            safe_idx = min(base_idx + 2, len(THRESHOLDS) - 1)
            rec_line = THRESHOLDS[safe_idx]
            if not p['final']:
                st.markdown(f'''<div style="display:flex;align-items:center;justify-content:space-between;background:linear-gradient(135deg,#0f172a,#020617);padding:10px 14px;margin-bottom:6px;border-radius:8px;border-left:4px solid {clr}"><div><b style="color:#fff">{p['game'].replace('@', ' @ ')}</b> <span style="color:#666">{status}</span></div><div style="display:flex;gap:12px;align-items:center"><span style="color:#888">{p['total']}pts/{p['mins']:.0f}min</span><span style="color:{clr};font-weight:bold">{p['pace']}/min {lbl}</span><span style="color:#888">Proj: <b style="color:#fff">{p['proj']}</b></span><span style="color:#888;font-size:0.8em">🛡️+2</span><a href="{kalshi_url}" target="_blank" style="background:#00aa00;color:#fff;padding:6px 14px;border-radius:6px;text-decoration:none;font-weight:bold">BUY NO {rec_line}</a></div></div>''', unsafe_allow_html=True)
            else:
                st.markdown(f'''<div style="display:flex;align-items:center;justify-content:space-between;background:linear-gradient(135deg,#0f172a,#020617);padding:10px 14px;margin-bottom:6px;border-radius:8px;border-left:4px solid {clr}"><div><b style="color:#fff">{p['game'].replace('@', ' @ ')}</b> <span style="color:#666">{status}</span></div><div style="display:flex;gap:12px;align-items:center"><span style="color:#888">{p['total']}pts/{p['mins']:.0f}min</span><span style="color:{clr};font-weight:bold">{p['pace']}/min {lbl}</span><span style="color:#888">Proj: <b style="color:#fff">{p['proj']}</b></span></div></div>''', unsafe_allow_html=True)
        elif p['pace'] < 4.8:
            lbl, clr = "🟡 AVG", "#ffff00"
            st.markdown(f'''<div style="display:flex;align-items:center;justify-content:space-between;background:linear-gradient(135deg,#0f172a,#020617);padding:10px 14px;margin-bottom:6px;border-radius:8px;border-left:4px solid {clr}"><div><b style="color:#fff">{p['game'].replace('@', ' @ ')}</b> <span style="color:#666">{status}</span></div><div style="display:flex;gap:12px;align-items:center"><span style="color:#888">{p['total']}pts/{p['mins']:.0f}min</span><span style="color:{clr};font-weight:bold">{p['pace']}/min {lbl}</span><span style="color:#888">Proj: <b style="color:#fff">{p['proj']}</b></span></div></div>''', unsafe_allow_html=True)
        elif p['pace'] < 5.2:
            lbl, clr = "🟠 FAST", "#ff8800"
            base_idx = next((i for i in range(len(THRESHOLDS)-1, -1, -1) if THRESHOLDS[i] < p['proj']), 0)
            safe_idx = max(base_idx - 2, 0)
            rec_line = THRESHOLDS[safe_idx]
            if not p['final']:
                st.markdown(f'''<div style="display:flex;align-items:center;justify-content:space-between;background:linear-gradient(135deg,#0f172a,#020617);padding:10px 14px;margin-bottom:6px;border-radius:8px;border-left:4px solid {clr}"><div><b style="color:#fff">{p['game'].replace('@', ' @ ')}</b> <span style="color:#666">{status}</span></div><div style="display:flex;gap:12px;align-items:center"><span style="color:#888">{p['total']}pts/{p['mins']:.0f}min</span><span style="color:{clr};font-weight:bold">{p['pace']}/min {lbl}</span><span style="color:#888">Proj: <b style="color:#fff">{p['proj']}</b></span><span style="color:#888;font-size:0.8em">🛡️+2</span><a href="{kalshi_url}" target="_blank" style="background:#cc6600;color:#fff;padding:6px 14px;border-radius:6px;text-decoration:none;font-weight:bold">BUY YES {rec_line}</a></div></div>''', unsafe_allow_html=True)
            else:
                st.markdown(f'''<div style="display:flex;align-items:center;justify-content:space-between;background:linear-gradient(135deg,#0f172a,#020617);padding:10px 14px;margin-bottom:6px;border-radius:8px;border-left:4px solid {clr}"><div><b style="color:#fff">{p['game'].replace('@', ' @ ')}</b> <span style="color:#666">{status}</span></div><div style="display:flex;gap:12px;align-items:center"><span style="color:#888">{p['total']}pts/{p['mins']:.0f}min</span><span style="color:{clr};font-weight:bold">{p['pace']}/min {lbl}</span><span style="color:#888">Proj: <b style="color:#fff">{p['proj']}</b></span></div></div>''', unsafe_allow_html=True)
        else:
            lbl, clr = "🔴 SHOOTOUT", "#ff0000"
            base_idx = next((i for i in range(len(THRESHOLDS)-1, -1, -1) if THRESHOLDS[i] < p['proj']), 0)
            safe_idx = max(base_idx - 2, 0)
            rec_line = THRESHOLDS[safe_idx]
            if not p['final']:
                st.markdown(f'''<div style="display:flex;align-items:center;justify-content:space-between;background:linear-gradient(135deg,#0f172a,#020617);padding:10px 14px;margin-bottom:6px;border-radius:8px;border-left:4px solid {clr}"><div><b style="color:#fff">{p['game'].replace('@', ' @ ')}</b> <span style="color:#666">{status}</span></div><div style="display:flex;gap:12px;align-items:center"><span style="color:#888">{p['total']}pts/{p['mins']:.0f}min</span><span style="color:{clr};font-weight:bold">{p['pace']}/min {lbl}</span><span style="color:#888">Proj: <b style="color:#fff">{p['proj']}</b></span><span style="color:#888;font-size:0.8em">🛡️+2</span><a href="{kalshi_url}" target="_blank" style="background:#cc0000;color:#fff;padding:6px 14px;border-radius:6px;text-decoration:none;font-weight:bold">BUY YES {rec_line}</a></div></div>''', unsafe_allow_html=True)
            else:
                st.markdown(f'''<div style="display:flex;align-items:center;justify-content:space-between;background:linear-gradient(135deg,#0f172a,#020617);padding:10px 14px;margin-bottom:6px;border-radius:8px;border-left:4px solid {clr}"><div><b style="color:#fff">{p['game'].replace('@', ' @ ')}</b> <span style="color:#666">{status}</span></div><div style="display:flex;gap:12px;align-items:center"><span style="color:#888">{p['total']}pts/{p['mins']:.0f}min</span><span style="color:{clr};font-weight:bold">{p['pace']}/min {lbl}</span><span style="color:#888">Proj: <b style="color:#fff">{p['proj']}</b></span></div></div>''', unsafe_allow_html=True)
else:
    st.info("No games with 6+ min")

st.divider()

# ALL GAMES
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
st.subheader("📖 How to Use NBA Edge Finder")
with st.expander("🎯 ML Picks — Reading the Signals", expanded=False):
    st.markdown("""**Signal Tiers:** 🟢 STRONG BUY (8.0+), 🔵 BUY (6.5-7.9), 🟡 LEAN (5.5-6.4), ⚪ TOSS-UP (<5.5)
    
**Form Display (WWLWL):** Last 5 games. Green = Hot (4-5 wins), Red = Cold (0-1 wins)""")

with st.expander("📈 Active Positions — Tracking Your Bets", expanded=False):
    st.markdown("""**Position Status:** ✅ WON/LOST, 🟢 CRUISING (15+), 🟢 LEADING (8-14), 🟡 AHEAD (1-7), 🟠 CLOSE (within 5), 🔴 BEHIND (6+)""")

with st.expander("🎯 Cushion Scanner — Live Total Opportunities", expanded=False):
    st.markdown("""Finds live games where projected total has cushion from the line. Look for 6+ cushion with favorable pace.
    
**🛡️+2 = Safety buffer.** We recommend 2 brackets above/below projection for extra margin. Buy closer to projection at your own risk.""")

with st.expander("🔥 Pace Scanner — Game Flow", expanded=False):
    st.markdown("""**Pace Labels:** 🟢 SLOW (<4.5/min), 🟡 AVG (4.5-4.8/min), 🟠 FAST (4.8-5.2/min), 🔴 SHOOTOUT (5.2+/min)

**🛡️+2 = Safety buffer.** We recommend 2 brackets above/below projection for extra margin.""")

st.divider()
st.caption("⚠️ Entertainment only. Not financial advice. v15.57")
