import streamlit as st
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="NBA Edge Finder", page_icon="🏀", layout="wide")

st_autorefresh(interval=24000, key="datarefresh")

import uuid
import requests as req_ga

def send_ga4_event(page_title, page_path):
    try:
        url = f"https://www.google-analytics.com/mp/collect?measurement_id=G-NQKY5VQ376&api_secret=n4oBJjH7RXi3dA7aQo2CZA"
        payload = {"client_id": str(uuid.uuid4()), "events": [{"name": "page_view", "params": {"page_title": page_title, "page_location": f"https://bigsnapshot.streamlit.app{page_path}"}}]}
        req_ga.post(url, json=payload, timeout=2)
    except: pass

send_ga4_event("NBA Edge Finder", "/NBA")

import extra_streamlit_components as stx

cookie_manager = stx.CookieManager()

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

saved_auth = cookie_manager.get("authenticated")
if saved_auth == "true":
    st.session_state.authenticated = True

if not st.session_state.authenticated:
    st.switch_page("Home.py")

import requests
import json
import os
from datetime import datetime, timedelta
import pytz

eastern = pytz.timezone("US/Eastern")
now = datetime.now(eastern)

MIN_MINUTES_FOR_PROJECTION = 6

TEAM_STATS = {
    "Atlanta": {"net": -3.2, "pace": 100.5, "home_pct": 0.52, "tier": "weak"},
    "Boston": {"net": 11.2, "pace": 99.8, "home_pct": 0.78, "tier": "elite"},
    "Brooklyn": {"net": -4.5, "pace": 98.2, "home_pct": 0.42, "tier": "weak"},
    "Charlotte": {"net": -6.8, "pace": 99.5, "home_pct": 0.38, "tier": "weak"},
    "Chicago": {"net": -2.1, "pace": 98.8, "home_pct": 0.48, "tier": "weak"},
    "Cleveland": {"net": 8.5, "pace": 97.2, "home_pct": 0.75, "tier": "elite"},
    "Dallas": {"net": 4.2, "pace": 99.0, "home_pct": 0.62, "tier": "good"},
    "Denver": {"net": 5.8, "pace": 98.5, "home_pct": 0.72, "tier": "good"},
    "Detroit": {"net": -8.2, "pace": 97.8, "home_pct": 0.32, "tier": "weak"},
    "Golden State": {"net": 3.5, "pace": 100.2, "home_pct": 0.65, "tier": "good"},
    "Houston": {"net": 1.2, "pace": 101.5, "home_pct": 0.55, "tier": "mid"},
    "Indiana": {"net": 2.8, "pace": 103.5, "home_pct": 0.58, "tier": "mid"},
    "LA Clippers": {"net": 1.5, "pace": 98.0, "home_pct": 0.55, "tier": "mid"},
    "LA Lakers": {"net": 2.2, "pace": 99.5, "home_pct": 0.58, "tier": "mid"},
    "Memphis": {"net": 4.5, "pace": 100.8, "home_pct": 0.68, "tier": "good"},
    "Miami": {"net": 3.8, "pace": 97.5, "home_pct": 0.65, "tier": "good"},
    "Milwaukee": {"net": 5.2, "pace": 99.2, "home_pct": 0.70, "tier": "good"},
    "Minnesota": {"net": 7.5, "pace": 98.8, "home_pct": 0.72, "tier": "elite"},
    "New Orleans": {"net": 1.8, "pace": 100.0, "home_pct": 0.55, "tier": "mid"},
    "New York": {"net": 6.2, "pace": 98.5, "home_pct": 0.68, "tier": "good"},
    "Oklahoma City": {"net": 12.5, "pace": 99.8, "home_pct": 0.82, "tier": "elite"},
    "Orlando": {"net": 3.2, "pace": 97.0, "home_pct": 0.62, "tier": "good"},
    "Philadelphia": {"net": 2.5, "pace": 98.2, "home_pct": 0.58, "tier": "mid"},
    "Phoenix": {"net": 2.0, "pace": 99.0, "home_pct": 0.60, "tier": "mid"},
    "Portland": {"net": -5.5, "pace": 99.5, "home_pct": 0.40, "tier": "weak"},
    "Sacramento": {"net": 0.8, "pace": 101.2, "home_pct": 0.55, "tier": "mid"},
    "San Antonio": {"net": -4.8, "pace": 100.5, "home_pct": 0.42, "tier": "weak"},
    "Toronto": {"net": -1.5, "pace": 98.8, "home_pct": 0.48, "tier": "weak"},
    "Utah": {"net": -7.5, "pace": 100.2, "home_pct": 0.35, "tier": "weak"},
    "Washington": {"net": -6.2, "pace": 101.0, "home_pct": 0.38, "tier": "weak"}
}

STARS = {
    "Nikola Jokic": ("Denver", 3), "Shai Gilgeous-Alexander": ("Oklahoma City", 3),
    "Giannis Antetokounmpo": ("Milwaukee", 3), "Luka Doncic": ("Dallas", 3),
    "Joel Embiid": ("Philadelphia", 3), "Jayson Tatum": ("Boston", 3),
    "Stephen Curry": ("Golden State", 3), "Kevin Durant": ("Phoenix", 3),
    "LeBron James": ("LA Lakers", 3), "Anthony Edwards": ("Minnesota", 3),
    "Ja Morant": ("Memphis", 3), "Donovan Mitchell": ("Cleveland", 3),
    "Trae Young": ("Atlanta", 3), "Devin Booker": ("Phoenix", 3),
    "Jaylen Brown": ("Boston", 2), "Anthony Davis": ("LA Lakers", 2),
    "Damian Lillard": ("Milwaukee", 2), "Kyrie Irving": ("Dallas", 2),
    "Jimmy Butler": ("Miami", 2), "Bam Adebayo": ("Miami", 2),
    "Tyrese Haliburton": ("Indiana", 2), "De'Aaron Fox": ("Sacramento", 2),
    "Jalen Brunson": ("New York", 2), "Chet Holmgren": ("Oklahoma City", 2),
    "Paolo Banchero": ("Orlando", 2), "Franz Wagner": ("Orlando", 2),
    "Victor Wembanyama": ("San Antonio", 2), "Evan Mobley": ("Cleveland", 2),
    "Zion Williamson": ("New Orleans", 2), "LaMelo Ball": ("Charlotte", 2),
    "Cade Cunningham": ("Detroit", 2), "Tyrese Maxey": ("Philadelphia", 2),
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

THRESHOLDS = [210.5, 215.5, 220.5, 225.5, 230.5, 235.5, 240.5, 242.5, 245.5, 250.5, 255.5]

H2H_EDGES = {
    ("Boston", "Philadelphia"): "Boston", ("Boston", "New York"): "Boston",
    ("Cleveland", "Chicago"): "Cleveland", ("Oklahoma City", "Utah"): "Oklahoma City",
    ("Denver", "Portland"): "Denver", ("Milwaukee", "Indiana"): "Milwaukee",
    ("Golden State", "Portland"): "Golden State", ("LA Lakers", "San Antonio"): "LA Lakers",
    ("Miami", "Atlanta"): "Miami", ("Phoenix", "Sacramento"): "Phoenix",
    ("Minnesota", "Charlotte"): "Minnesota", ("Dallas", "Houston"): "Dallas",
    ("Memphis", "New Orleans"): "Memphis",
}

TEAM_LOCATIONS = {
    "Boston": "ET", "Brooklyn": "ET", "New York": "ET", "Philadelphia": "ET", "Toronto": "ET",
    "Atlanta": "ET", "Charlotte": "ET", "Miami": "ET", "Orlando": "ET", "Washington": "ET",
    "Chicago": "CT", "Cleveland": "ET", "Detroit": "ET", "Indiana": "ET", "Milwaukee": "CT",
    "Dallas": "CT", "Houston": "CT", "Memphis": "CT", "New Orleans": "CT", "San Antonio": "CT",
    "Denver": "MT", "Minnesota": "CT", "Oklahoma City": "CT", "Portland": "PT", "Utah": "MT",
    "Golden State": "PT", "LA Clippers": "PT", "LA Lakers": "PT", "Phoenix": "MT", "Sacramento": "PT",
}

def is_cross_country(team1, team2):
    loc1, loc2 = TEAM_LOCATIONS.get(team1, ""), TEAM_LOCATIONS.get(team2, "")
    return (loc1 == "ET" and loc2 == "PT") or (loc1 == "PT" and loc2 == "ET")

def get_h2h_edge(home, away):
    if (home, away) in H2H_EDGES: return H2H_EDGES[(home, away)]
    if (away, home) in H2H_EDGES: return H2H_EDGES[(away, home)]
    return None

def get_conviction(mins, lead):
    abs_lead = abs(lead)
    if mins >= 44:
        if abs_lead >= 10: return "🟢🟢🟢 VERY HIGH", "#00ff00"
        elif abs_lead >= 5: return "🟢🟢 HIGH", "#00ff00"
        else: return "🟡 MEDIUM", "#cccc00"
    if mins >= 36:
        if abs_lead >= 15: return "🟢🟢 HIGH", "#00ff00"
        elif abs_lead >= 10: return "🟢 GOOD", "#88cc00"
        elif abs_lead >= 5: return "🟡 MEDIUM", "#cccc00"
        else: return "🔴 LOW", "#ff6666"
    if mins >= 24:
        if abs_lead >= 12: return "🟢 GOOD", "#88cc00"
        elif abs_lead >= 8: return "🟡 MEDIUM", "#cccc00"
        else: return "🔴 LOW", "#ff6666"
    if mins >= 12:
        if abs_lead >= 10: return "🟡 MEDIUM", "#cccc00"
        else: return "🔴 LOW", "#ff6666"
    return "🔴 LOW", "#ff6666"

def get_pace_label(pace):
    if pace is None: return ""
    if pace > 5.0: return "🔥 FAST"
    elif pace < 4.2: return "🐢 SLOW"
    return "⚖️ AVG"

def get_safe_projection(total, mins):
    if mins < MIN_MINUTES_FOR_PROJECTION: return None, None
    pace = total / mins if mins > 0 else 0
    projected = round(pace * 48)
    return projected, round(pace, 2)

def get_totals_thresholds(projected):
    if projected is None: return None, None, None, None
    no_idx = next((i for i, t in enumerate(THRESHOLDS) if t > projected), len(THRESHOLDS)-1)
    safe_no_idx = min(no_idx + 1, len(THRESHOLDS) - 1)
    safe_no = THRESHOLDS[safe_no_idx]
    no_cushion = safe_no - projected
    yes_idx = next((i for i in range(len(THRESHOLDS)-1, -1, -1) if THRESHOLDS[i] < projected), 0)
    safe_yes_idx = max(yes_idx - 1, 0)
    safe_yes = THRESHOLDS[safe_yes_idx]
    yes_cushion = projected - safe_yes
    return safe_no, no_cushion, safe_yes, yes_cushion

@st.cache_data(ttl=24)
def fetch_games():
    today = datetime.now(eastern).strftime('%Y%m%d')
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={today}"
    try:
        data = requests.get(url, timeout=10).json()
        games = []
        for event in data.get("events", []):
            comp = event.get("competitions", [{}])[0]
            competitors = comp.get("competitors", [])
            if len(competitors) < 2: continue
            home, away = None, None
            for c in competitors:
                name = TEAM_ABBREVS.get(c.get("team", {}).get("displayName", ""), "")
                score = int(c.get("score", 0) or 0)
                if c.get("homeAway") == "home": home = {"team": name, "score": score}
                else: away = {"team": name, "score": score}
            status = event.get("status", {})
            game_time = event.get("date", "")
            try:
                game_dt = datetime.fromisoformat(game_time.replace("Z", "+00:00"))
                game_dt_eastern = game_dt.astimezone(eastern)
                time_str = game_dt_eastern.strftime("%I:%M %p")
            except:
                time_str, game_dt_eastern = "", None
            games.append({"home": home["team"], "away": away["team"], "home_score": home["score"], "away_score": away["score"], "status": status.get("type", {}).get("name", ""), "period": status.get("period", 0), "clock": status.get("displayClock", ""), "time": time_str, "datetime": game_dt_eastern})
        return games
    except: return []

@st.cache_data(ttl=120)
def fetch_injuries():
    injuries = {}
    try:
        data = requests.get("https://site.api.espn.com/apis/site/v2/sports/basketball/nba/injuries", timeout=10).json()
        for team_data in data.get("injuries", []):
            team = TEAM_ABBREVS.get(team_data.get("displayName", ""), "")
            if not team: continue
            injuries[team] = []
            for player in team_data.get("injuries", []):
                name = player.get("athlete", {}).get("displayName", "")
                status = player.get("status", "").upper()
                if name and "OUT" in status: injuries[team].append(name)
        return injuries
    except: return {}

@st.cache_data(ttl=3600)
def fetch_rest_days():
    rest = {"b2b": set(), "rested": set()}
    try:
        for days_ago in [1, 2, 3]:
            date = (datetime.now(eastern) - timedelta(days=days_ago)).strftime('%Y%m%d')
            data = requests.get(f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={date}", timeout=5).json()
            for event in data.get("events", []):
                for c in event.get("competitions", [{}])[0].get("competitors", []):
                    team = TEAM_ABBREVS.get(c.get("team", {}).get("displayName", ""), "")
                    if team:
                        if days_ago == 1: rest["b2b"].add(team)
                        elif days_ago >= 2 and team not in rest["b2b"]: rest["rested"].add(team)
        return rest
    except: return {"b2b": set(), "rested": set()}

@st.cache_data(ttl=600)
def fetch_news():
    try:
        data = requests.get("https://site.api.espn.com/apis/site/v2/sports/basketball/nba/news", timeout=10).json()
        return [{"headline": item.get("headline", ""), "description": item.get("description", ""), "link": item.get("links", {}).get("web", {}).get("href", "")} for item in data.get("articles", [])[:8]]
    except: return []

@st.cache_data(ttl=1800)
def fetch_team_record():
    form = {}
    try:
        for days_ago in range(14):
            date = (datetime.now(eastern) - timedelta(days=days_ago)).strftime('%Y%m%d')
            data = requests.get(f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={date}", timeout=5).json()
            for event in data.get("events", []):
                if event.get("status", {}).get("type", {}).get("name", "") != "STATUS_FINAL": continue
                comp = event.get("competitions", [{}])[0]
                competitors = comp.get("competitors", [])
                if len(competitors) < 2: continue
                home_team, away_team, home_score, away_score = None, None, 0, 0
                for c in competitors:
                    team = TEAM_ABBREVS.get(c.get("team", {}).get("displayName", ""), "")
                    score = int(c.get("score", 0) or 0)
                    if c.get("homeAway") == "home": home_team, home_score = team, score
                    else: away_team, away_score = team, score
                if home_team and away_team:
                    home_won = home_score > away_score
                    if home_team not in form: form[home_team] = []
                    if away_team not in form: form[away_team] = []
                    form[home_team].insert(0, "W" if home_won else "L")
                    form[away_team].insert(0, "L" if home_won else "W")
        for team in form: form[team] = form[team][-5:]
        return form
    except: return {}

def get_record_display(form_list):
    if not form_list: return "—"
    return "".join(["🟢" if r == "W" else "🔴" for r in form_list])

def get_streak(form_list):
    if not form_list: return ""
    current = form_list[-1]
    count = sum(1 for r in reversed(form_list) if r == current)
    return f"{current}{count}"

def get_minutes_played(period, clock, status):
    if status == "STATUS_FINAL": return 48 if period <= 4 else 48 + (period - 4) * 5
    if status == "STATUS_HALFTIME": return 24
    if period == 0: return 0
    try:
        parts = str(clock).split(':')
        mins = int(parts[0])
        secs = int(float(parts[1])) if len(parts) > 1 else 0
        time_left = mins + secs/60
        if period <= 4: return (period - 1) * 12 + (12 - time_left)
        else: return 48 + (period - 5) * 5 + (5 - time_left)
    except: return (period - 1) * 12 if period <= 4 else 48 + (period - 5) * 5

def calc_live_ml_alignment(game):
    home, away = game['home'], game['away']
    home_score, away_score = game['home_score'], game['away_score']
    total = home_score + away_score
    mins = get_minutes_played(game['period'], game['clock'], game['status'])
    if mins < 6: return None
    lead_home = home_score - away_score
    if abs(lead_home) < 5: return None
    live_score = 50
    if abs(lead_home) >= 20: live_score += 25 if lead_home > 0 else -25
    elif abs(lead_home) >= 15: live_score += 18 if lead_home > 0 else -18
    elif abs(lead_home) >= 10: live_score += 12 if lead_home > 0 else -12
    elif abs(lead_home) >= 5: live_score += 6 if lead_home > 0 else -6
    if mins >= 36:
        if abs(lead_home) >= 10: live_score += 15 if lead_home > 0 else -15
        elif abs(lead_home) >= 5: live_score += 8 if lead_home > 0 else -8
    elif mins >= 24:
        if abs(lead_home) >= 15: live_score += 8 if lead_home > 0 else -8
    pace = total / mins if mins > 0 else 0
    if pace > 5.0 and abs(lead_home) >= 10: live_score += -4 if lead_home > 0 else 4
    elif pace < 4.2 and abs(lead_home) >= 10: live_score += 3 if lead_home > 0 else -3
    if live_score >= 55: pick, alignment = home, live_score
    elif live_score <= 45: pick, alignment = away, 100 - live_score
    else: return None
    return {'pick': pick, 'opponent': away if pick == home else home, 'alignment': round(alignment), 'lead': lead_home if pick == home else -lead_home, 'mins': mins, 'period': game['period'], 'clock': game['clock'], 'home': home, 'away': away, 'home_score': home_score, 'away_score': away_score, 'pace': round(pace, 2)}

def calc_edge(home, away, injuries, rest):
    home_pts, away_pts = 0, 0
    home_reasons, away_reasons = [], []
    h_stats, a_stats = TEAM_STATS.get(home, {}), TEAM_STATS.get(away, {})
    h_net, a_net = h_stats.get("net", 0), a_stats.get("net", 0)
    home_out, away_out = injuries.get(home, []), injuries.get(away, [])
    for star, (team, tier) in STARS.items():
        if team == home and any(star.lower() in p.lower() for p in home_out):
            away_pts += 5 if tier == 3 else 3; away_reasons.append(f"{star.split()[-1]} OUT")
        if team == away and any(star.lower() in p.lower() for p in away_out):
            home_pts += 5 if tier == 3 else 3; home_reasons.append(f"{star.split()[-1]} OUT")
    h_b2b, a_b2b = home in rest.get("b2b", set()), away in rest.get("b2b", set())
    h_rested, a_rested = home in rest.get("rested", set()), away in rest.get("rested", set())
    if a_b2b and not h_b2b: home_pts += 4; home_reasons.append("Opp B2B")
    elif h_b2b and not a_b2b: away_pts += 4; away_reasons.append("Opp B2B")
    if h_rested and a_b2b: home_pts += 2; home_reasons.append("Rested")
    elif a_rested and h_b2b: away_pts += 2; away_reasons.append("Rested")
    if a_b2b and is_cross_country(away, home): home_pts += 2; home_reasons.append("Travel fatigue")
    elif h_b2b and is_cross_country(home, away): away_pts += 2; away_reasons.append("Travel fatigue")
    h2h_winner = get_h2h_edge(home, away)
    if h2h_winner == home: home_pts += 1.5; home_reasons.append("H2H edge")
    elif h2h_winner == away: away_pts += 1.5; away_reasons.append("H2H edge")
    net_gap = h_net - a_net
    if net_gap >= 15: home_pts += 3; home_reasons.append(f"Net +{net_gap:.0f}")
    elif net_gap >= 10: home_pts += 2; home_reasons.append(f"Net +{net_gap:.0f}")
    elif net_gap >= 5: home_pts += 1; home_reasons.append(f"Net +{net_gap:.0f}")
    elif net_gap <= -15: away_pts += 3; away_reasons.append(f"Net +{-net_gap:.0f}")
    elif net_gap <= -10: away_pts += 2; away_reasons.append(f"Net +{-net_gap:.0f}")
    elif net_gap <= -5: away_pts += 1; away_reasons.append(f"Net +{-net_gap:.0f}")
    if home == "Denver": home_pts += 1.5; home_reasons.append("Altitude")
    h_pace, a_pace = h_stats.get("pace", 99), a_stats.get("pace", 99)
    if h_pace >= 101 and a_pace <= 98: home_pts += 1.5; home_reasons.append("Pace edge")
    elif a_pace >= 101 and h_pace <= 98: away_pts += 1.5; away_reasons.append("Pace edge")
    h_tier, a_tier = h_stats.get("tier", "mid"), a_stats.get("tier", "mid")
    if h_tier == "weak" and a_tier in ["elite", "good"]: away_pts += 1.5; away_reasons.append("Weak home")
    if a_tier == "elite" and h_tier != "elite": away_pts += 1; away_reasons.append("Elite road")
    base_score = max(25, min(85, 50 + (net_gap * 1.5)))
    total_pts = home_pts + away_pts
    if total_pts > 0:
        if home_pts > away_pts:
            edge_score = min(90, base_score + (home_pts / total_pts) * 15)
            pick, reasons, edge = home, home_reasons, home_pts - away_pts
        else:
            edge_score = min(90, (100 - base_score) + (away_pts / total_pts) * 15)
            pick, reasons, edge = away, away_reasons, away_pts - home_pts
    else:
        if base_score >= 55: pick, edge_score, reasons, edge = home, base_score, ["Better team"], 0
        elif base_score <= 45: pick, edge_score, reasons, edge = away, 100 - base_score, ["Better team"], 0
        else: return None
    return {"pick": pick, "opponent": away if pick == home else home, "edge_score": round(edge_score), "edge_pts": round(edge, 1), "reasons": reasons[:4], "home": home, "away": away, "is_home": pick == home}

def build_kalshi_url(away, home):
    return f"https://kalshi.com/markets/kxnbagame/kxnbagame-{datetime.now(eastern).strftime('%y%b%d').upper()}{KALSHI_CODES.get(away, 'XXX')}{KALSHI_CODES.get(home, 'XXX')}"

def build_kalshi_totals_url(away, home):
    return f"https://kalshi.com/markets/kxnbatotal/kxnbatotal-{datetime.now(eastern).strftime('%y%b%d').upper()}{KALSHI_CODES.get(away, 'XXX')}{KALSHI_CODES.get(home, 'XXX')}"

POSITIONS_FILE = "nba_positions.json"

def load_positions():
    try:
        if os.path.exists(POSITIONS_FILE):
            with open(POSITIONS_FILE, 'r') as f: return json.load(f)
    except: pass
    return []

def save_positions(positions):
    try:
        with open(POSITIONS_FILE, 'w') as f: json.dump(positions, f, indent=2)
    except: pass

# UI
st.title("🏀 NBA EDGE FINDER")
st.caption(f"v4.1 | {now.strftime('%b %d, %Y %I:%M %p ET')} | Auto-refresh 24s")

st.markdown('<div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); border: 1px solid #e94560; border-radius: 8px; padding: 12px 16px; margin-bottom: 16px;"><p style="color: #e94560; font-weight: 600; margin: 0 0 6px 0;">⚠️ IMPORTANT DISCLAIMER</p><p style="color: #ccc; font-size: 0.85em; margin: 0; line-height: 1.5;">This is <strong>not</strong> a predictive model. The Edge Score shows how many factors currently favor one side — it is <strong>not</strong> a win probability. We show the edge, <strong>you make the call</strong>.</p></div>', unsafe_allow_html=True)

with st.sidebar:
    st.header("📊 EDGE LEGEND")
    st.markdown("**Pre-Game:**"); st.success("🟢 **75+** — Multiple factors"); st.info("🟡 **60-74** — Several factors"); st.warning("⚪ **Below 60** — Few factors")
    st.markdown("---"); st.header("🔴 LIVE EDGE"); st.markdown("**75+** — Strong lead + time"); st.markdown("**60-74** — Clear advantage"); st.markdown("**TOO EARLY** — Under 6 min"); st.markdown("**TOO CLOSE** — Lead under 5")
    st.markdown("---"); st.header("🎯 CONVICTION"); st.markdown("🟢🟢🟢 VERY HIGH"); st.markdown("🟢🟢 HIGH"); st.markdown("🟢 GOOD"); st.markdown("🟡 MEDIUM"); st.markdown("🔴 LOW")

games = fetch_games()
injuries = fetch_injuries()
rest = fetch_rest_days()
team_record = fetch_team_record()

if "positions" not in st.session_state: st.session_state.positions = load_positions()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Today's Games", len(games))
c2.metric("🔴 Live Now", len([g for g in games if g['status'] in ['STATUS_IN_PROGRESS', 'STATUS_HALFTIME']]))
c3.metric("B2B Teams", len(rest.get("b2b", set())))
c4.metric("Last Update", now.strftime("%I:%M:%S %p"))

st.divider()

# LIVE EDGE MONITOR
live_games = [g for g in games if g['status'] in ['STATUS_IN_PROGRESS', 'STATUS_HALFTIME']]

if live_games:
    st.subheader("🔴 LIVE EDGE MONITOR")
    st.markdown('<div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); border: 1px solid #4a9eff; border-radius: 8px; padding: 12px 16px; margin-bottom: 16px;"><p style="color: #4a9eff; font-weight: 600; margin: 0 0 6px 0;">📊 REAL-TIME FACTOR ALIGNMENT</p><p style="color: #ccc; font-size: 0.85em; margin: 0; line-height: 1.5;">We show the edge — <strong>you make the call</strong>. Updates every 24 seconds.</p></div>', unsafe_allow_html=True)
    
    live_edges = []
    for g in live_games:
        ml_live = calc_live_ml_alignment(g)
        mins = get_minutes_played(g['period'], g['clock'], g['status'])
        lead = g['home_score'] - g['away_score']
        live_edges.append({'game': g, 'ml': ml_live, 'alignment': ml_live['alignment'] if ml_live else 50, 'mins': mins, 'lead': lead})
    live_edges.sort(key=lambda x: x['alignment'], reverse=True)
    
    positions_by_game = {pos['game']: pos for pos in st.session_state.positions}
    
    for item in live_edges:
        g = item['game']
        ml = item['ml']
        mins, lead = item['mins'], item['lead']
        kalshi_url = build_kalshi_url(g['away'], g['home'])
        kalshi_totals_url = build_kalshi_totals_url(g['away'], g['home'])
        game_key = f"{g['away']}@{g['home']}"
        user_pos = positions_by_game.get(game_key)
        total = g['home_score'] + g['away_score']
        projected, pace = get_safe_projection(total, mins)
        conviction_text, conviction_color = get_conviction(mins, lead)
        pace_label = get_pace_label(pace)
        time_display = "HALFTIME" if g['status'] == 'STATUS_HALFTIME' else f"Q{g['period']} {g['clock']}"
        
        # Build totals line
        if user_pos and user_pos.get('type') == 'totals' and projected:
            pos_pick = user_pos.get('pick', '')
            pos_side = 'YES' if 'YES' in pos_pick.upper() else 'NO'
            pos_line = float(pos_pick.split()[-1]) if pos_pick else 230.5
            pos_price, pos_contracts = user_pos.get('price', 50), user_pos.get('contracts', 1)
            pos_cushion = projected - pos_line if pos_side == 'YES' else pos_line - projected
            if pos_cushion >= 20: pos_status, pos_color = "🟢🟢🟢 LOCKED", "#00ff00"
            elif pos_cushion >= 10: pos_status, pos_color = "🟢🟢 VERY SAFE", "#00ff00"
            elif pos_cushion >= 5: pos_status, pos_color = "🟢 SAFE", "#88cc00"
            elif pos_cushion >= 0: pos_status, pos_color = "🟡 CLOSE", "#cccc00"
            elif pos_cushion >= -5: pos_status, pos_color = "🟠 RISKY", "#ff9900"
            else: pos_status, pos_color = "🔴 DANGER", "#ff6666"
            totals_line = f'<span style="color: {pos_color}; font-weight: bold; font-size: 1.2em;">MY BET: {pos_side} {pos_line} → {pos_status} ({pos_cushion:+.0f})</span> | <span style="color: #888;">Proj: {projected} | {pos_contracts}x @ {pos_price}¢</span>'
        elif projected:
            safe_no, no_cushion, safe_yes, yes_cushion = get_totals_thresholds(projected)
            if no_cushion >= 10: no_label = f'<span style="color: #00ff00; font-weight: bold;">🟢 NO {safe_no} (+{no_cushion}) SAFE</span>'
            elif no_cushion >= 5: no_label = f'<span style="color: #88cc00;">🟡 NO {safe_no} (+{no_cushion})</span>'
            elif no_cushion >= 0: no_label = f'<span style="color: #888;">⚪ NO {safe_no} (+{no_cushion})</span>'
            else: no_label = f'<span style="color: #ff6666;">🔴 NO {safe_no} ({no_cushion}) AVOID</span>'
            if yes_cushion >= 10: yes_label = f'<span style="color: #00ff00; font-weight: bold;">🟢 YES {safe_yes} (+{yes_cushion}) SAFE</span>'
            elif yes_cushion >= 5: yes_label = f'<span style="color: #88cc00;">🟡 YES {safe_yes} (+{yes_cushion})</span>'
            elif yes_cushion >= 0: yes_label = f'<span style="color: #888;">⚪ YES {safe_yes} (+{yes_cushion})</span>'
            else: yes_label = f'<span style="color: #ff6666;">🔴 YES {safe_yes} ({yes_cushion}) AVOID</span>'
            totals_line = f'<span style="color: #888;">Proj: {projected}</span> | {no_label} | {yes_label}'
        else:
            totals_line = f'<span style="color: #666;">⏳ Totals after {MIN_MINUTES_FOR_PROJECTION} min</span>'
        
        if ml:
            alignment, pick, ml_lead = ml['alignment'], ml['pick'], ml['lead']
            if alignment >= 75: border_color, bg_color = "#00ff00", "#0d1f0d"
            elif alignment >= 60: border_color, bg_color = "#88cc00", "#1a1f0d"
            else: border_color, bg_color = "#cccc00", "#1f1f0d"
            card_html = f'<div style="background: linear-gradient(135deg, #1a1a1a 0%, {bg_color} 100%); border: 2px solid {border_color}; border-radius: 10px; padding: 16px; margin: 10px 0;">'
            card_html += f'<div style="display: flex; justify-content: space-between; align-items: center;"><div><span style="color: #fff; font-size: 1.1em; font-weight: bold;">{g["away"]} @ {g["home"]}</span><span style="color: #888; margin-left: 12px;">{time_display}</span></div><div><span style="color: #fff; font-size: 1.2em; font-weight: bold;">{g["away_score"]} - {g["home_score"]}</span></div></div>'
            card_html += f'<div style="margin-top: 12px; display: flex; justify-content: space-between; align-items: center;"><div><span style="color: #aaa;">Edge:</span><span style="color: {border_color}; font-size: 1.3em; font-weight: bold; margin-left: 8px;">{pick}</span><span style="color: #888; margin-left: 8px;">({ml_lead:+d} lead)</span><span style="color: #666; margin-left: 8px;">{pace_label}</span></div><div><span style="background: {border_color}; color: #000; padding: 6px 14px; border-radius: 6px; font-weight: bold; font-size: 1.1em;">{alignment}/100</span></div></div>'
            card_html += f'<div style="margin-top: 8px;"><span style="color: {conviction_color}; font-weight: bold;">{conviction_text}</span></div>'
            card_html += f'<div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid #333;">{totals_line}</div></div>'
            st.markdown(card_html, unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)
            with col1: st.link_button(f"🎯 {pick} ML", kalshi_url)
            with col2: st.link_button(f"⬇️ NO {get_totals_thresholds(projected)[0] if projected else ''}", kalshi_totals_url)
            with col3: st.link_button(f"⬆️ YES {get_totals_thresholds(projected)[2] if projected else ''}", kalshi_totals_url)
        else:
            edge_status = "TOO EARLY" if mins < 6 else "TOO CLOSE"
            card_html = '<div style="background: #1a1a1a; border: 1px solid #555; border-radius: 10px; padding: 16px; margin: 10px 0;">'
            card_html += f'<div style="display: flex; justify-content: space-between; align-items: center;"><div><span style="color: #fff; font-size: 1.1em; font-weight: bold;">{g["away"]} @ {g["home"]}</span><span style="color: #888; margin-left: 12px;">{time_display}</span></div><div><span style="color: #fff; font-size: 1.2em; font-weight: bold;">{g["away_score"]} - {g["home_score"]}</span></div></div>'
            card_html += f'<div style="margin-top: 12px; display: flex; justify-content: space-between; align-items: center;"><div><span style="color: #888;">ML Edge: {edge_status}</span><span style="color: #666; margin-left: 8px;">({lead:+d})</span><span style="color: #666; margin-left: 8px;">{pace_label}</span></div><div><span style="background: #555; color: #aaa; padding: 6px 14px; border-radius: 6px; font-weight: bold;">—/100</span></div></div>'
            card_html += f'<div style="margin-top: 8px;"><span style="color: {conviction_color}; font-weight: bold;">{conviction_text}</span></div>'
            card_html += f'<div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid #333;">{totals_line}</div></div>'
            st.markdown(card_html, unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)
            with col1: st.link_button("👀 VIEW ML", kalshi_url)
            with col2: st.link_button(f"⬇️ NO {get_totals_thresholds(projected)[0] if projected else ''}", kalshi_totals_url)
            with col3: st.link_button(f"⬆️ YES {get_totals_thresholds(projected)[2] if projected else ''}", kalshi_totals_url)
        
        # Quick add position
        if not user_pos:
            with st.expander("➕ Track My Bet"):
                qa_cols = st.columns([1, 1, 1, 1])
                with qa_cols[0]: qa_side = st.radio("Side", ["YES", "NO"], horizontal=True, key=f"qa_side_{game_key}")
                with qa_cols[1]: qa_line = st.selectbox("Line", THRESHOLDS, index=6, key=f"qa_line_{game_key}")
                with qa_cols[2]: qa_price = st.number_input("¢", 1, 99, 50, key=f"qa_price_{game_key}")
                with qa_cols[3]: qa_qty = st.number_input("Qty", 1, 100, 1, key=f"qa_qty_{game_key}")
                if st.button("✅ ADD", key=f"qa_add_{game_key}", type="primary", use_container_width=True):
                    st.session_state.positions.append({"game": game_key, "type": "totals", "pick": f"{qa_side} {qa_line}", "price": qa_price, "contracts": qa_qty})
                    save_positions(st.session_state.positions)
                    st.rerun()
        st.markdown("")
    st.divider()

# STAR INJURIES
st.subheader("🏥 STAR INJURIES")
today_teams = set(g["home"] for g in games) | set(g["away"] for g in games)
star_injuries = sorted([{"star": star, "team": team, "tier": tier} for star, (team, tier) in STARS.items() if team in today_teams and team in injuries and any(star.lower() in p.lower() for p in injuries[team])], key=lambda x: -x["tier"])
if star_injuries:
    for inj in star_injuries[:6]: st.error(f"{'⭐' * inj['tier']} **{inj['star']}** — OUT ({inj['team']})")
else: st.info("No major star injuries for today's games")
b2b_today = [t for t in rest.get("b2b", set()) if t in today_teams]
if b2b_today: st.warning(f"🛏️ **B2B TEAMS:** {', '.join(sorted(b2b_today))}")

st.divider()

# NBA NEWS
st.subheader("📰 NBA NEWS")
news = fetch_news()
if news:
    for article in news[:6]: st.markdown(f"**[{article['headline']}]({article['link']})**" if article["link"] else f"**{article['headline']}**")
else: st.info("No news available")

st.divider()

# PRE-GAME ALIGNMENT
st.subheader("🎯 PRE-GAME ALIGNMENT")
st.markdown('<div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); border: 1px solid #4a9eff; border-radius: 8px; padding: 12px 16px; margin-bottom: 16px;"><p style="color: #4a9eff; font-weight: 600; margin: 0 0 6px 0;">📊 ALL SCHEDULED GAMES</p><p style="color: #ccc; font-size: 0.85em; margin: 0;">We show the edge — <strong>you make the call</strong>. Sorted by game time.</p></div>', unsafe_allow_html=True)

picks = []
for g in games:
    if g["status"] != "STATUS_SCHEDULED": continue
    result = calc_edge(g["home"], g["away"], injuries, rest)
    if result:
        result.update({"status": g["status"], "period": g["period"], "clock": g["clock"], "home_score": g["home_score"], "away_score": g["away_score"], "time": g.get("time", ""), "datetime": g.get("datetime")})
        picks.append(result)
    else:
        picks.append({"pick": None, "edge_score": 50, "reasons": ["No clear edge"], "home": g["home"], "away": g["away"], "time": g.get("time", ""), "datetime": g.get("datetime")})
picks.sort(key=lambda x: x["datetime"] if x["datetime"] else datetime.max.replace(tzinfo=eastern))

for p in picks:
    kalshi_url = build_kalshi_url(p["away"], p["home"])
    if p["pick"]:
        edge_score = p["edge_score"]
        if edge_score >= 75: border_color, bg_color = "#00ff00", "#0d1f0d"
        elif edge_score >= 60: border_color, bg_color = "#88cc00", "#1a1f0d"
        else: border_color, bg_color = "#cccc00", "#1f1f0d"
        st.markdown(f'<div style="background: linear-gradient(135deg, #1a1a1a 0%, {bg_color} 100%); border: 2px solid {border_color}; border-radius: 10px; padding: 16px; margin: 10px 0;"><div style="display: flex; justify-content: space-between; align-items: center;"><div><span style="color: #fff; font-size: 1.1em; font-weight: bold;">{p["away"]} @ {p["home"]}</span><span style="color: #888; margin-left: 12px;">{p.get("time", "")}</span></div><div><span style="background: {border_color}; color: #000; padding: 6px 14px; border-radius: 6px; font-weight: bold;">{edge_score}/100</span></div></div><div style="margin-top: 12px;"><span style="color: #aaa;">Edge:</span><span style="color: {border_color}; font-size: 1.3em; font-weight: bold; margin-left: 8px;">{p["pick"]}</span><span style="color: #888; margin-left: 15px;">{" • ".join(p["reasons"])}</span></div></div>', unsafe_allow_html=True)
        st.link_button(f"🎯 EDGE: {p['pick']} — BUY ON KALSHI", kalshi_url)
    else:
        st.markdown(f'<div style="background: #1a1a1a; border: 1px solid #555; border-radius: 10px; padding: 16px; margin: 10px 0;"><div style="display: flex; justify-content: space-between; align-items: center;"><div><span style="color: #fff; font-size: 1.1em; font-weight: bold;">{p["away"]} @ {p["home"]}</span><span style="color: #888; margin-left: 12px;">{p.get("time", "")}</span></div><div><span style="background: #555; color: #aaa; padding: 6px 14px; border-radius: 6px; font-weight: bold;">—/100</span></div></div><div style="margin-top: 12px;"><span style="color: #888;">Edge: TOO CLOSE — No clear advantage</span></div></div>', unsafe_allow_html=True)
        st.link_button(f"👀 VIEW {p['away']} @ {p['home']} ON KALSHI", kalshi_url)
    st.markdown("")

if not picks: st.info("No scheduled games right now.")

st.divider()

# TODAY'S GAMES
st.subheader("📺 TODAY'S GAMES — 5 Day Record")
for g in games:
    home, away = g["home"], g["away"]
    h_net, a_net = TEAM_STATS.get(home, {}).get("net", 0), TEAM_STATS.get(away, {}).get("net", 0)
    h_rec, a_rec = team_record.get(home, []), team_record.get(away, [])
    if g["status"] == "STATUS_FINAL": status = f"✅ {home if g['home_score'] > g['away_score'] else away} wins"
    elif g["status"] == "STATUS_HALFTIME": status = "⏸️ HALFTIME"
    elif g["status"] == "STATUS_IN_PROGRESS": status = f"🔴 Q{g['period']} {g['clock']}"
    else: status = "Scheduled"
    st.markdown(f"**{away}** ({a_net:+.1f}) {get_record_display(a_rec)} {get_streak(a_rec)} — {g['away_score']} @ {g['home_score']} — **{home}** ({h_net:+.1f}) {get_record_display(h_rec)} {get_streak(h_rec)} | {status}")

st.divider()

# POSITION TRACKER
st.subheader("📈 ACTIVE POSITIONS")
games_dict = {f"{g['away']}@{g['home']}": g for g in games}
if st.session_state.positions:
    for idx, pos in enumerate(st.session_state.positions):
        gk, g = pos['game'], games_dict.get(pos['game'])
        if not g: continue
        price, contracts, pos_type = pos.get('price', 50), pos.get('contracts', 1), pos.get('type', 'ml')
        cost, potential = round(price * contracts / 100, 2), round((100 - price) * contracts / 100, 2)
        pick, parts = pos.get('pick', ''), gk.split("@")
        mins = get_minutes_played(g['period'], g['clock'], g['status'])
        is_final, is_live = g['status'] == "STATUS_FINAL", g['status'] in ["STATUS_IN_PROGRESS", "STATUS_HALFTIME"]
        total = g['home_score'] + g['away_score']
        
        if pos_type == 'totals':
            threshold = float(pick.split()[-1]) if pick else 230.5
            side = 'YES' if 'YES' in pick.upper() else 'NO'
            if is_final:
                won = (total > threshold) if side == 'YES' else (total < threshold)
                label, status_color = ("✅ WON", "success") if won else ("❌ LOST", "error")
                pnl = f"+${potential:.2f}" if won else f"-${cost:.2f}"
            elif is_live and mins > 0:
                pace_val = total / mins
                projected = round(total + pace_val * (48 - mins))
                cushion = projected - threshold if side == 'YES' else threshold - projected
                if cushion >= 15: label, status_color = "🟢 VERY SAFE", "success"
                elif cushion >= 8: label, status_color = "🟢 ON TRACK", "success"
                elif cushion >= 3: label, status_color = "🟡 CLOSE", "warning"
                elif cushion >= -5: label, status_color = "🟠 RISKY", "warning"
                else: label, status_color = "🔴 DANGER", "error"
                pnl = f"Proj: {projected} vs {threshold} ({cushion:+.0f}) | Win: +${potential:.2f}"
            else:
                label, status_color, pnl = "⏳ PENDING", "info", f"Win: +${potential:.2f}"
        else:
            pick_score = g['home_score'] if pick == parts[1] else g['away_score']
            opp_score = g['away_score'] if pick == parts[1] else g['home_score']
            ml_lead = pick_score - opp_score
            if is_final:
                won = pick_score > opp_score
                label, status_color = ("✅ WON", "success") if won else ("❌ LOST", "error")
                pnl = f"+${potential:.2f}" if won else f"-${cost:.2f}"
            elif is_live:
                if ml_lead >= 20 and mins >= 36: label, status_color = "🟢 VERY SAFE", "success"
                elif ml_lead >= 15: label, status_color = "🟢 CRUISING", "success"
                elif ml_lead >= 8: label, status_color = "🟢 ON TRACK", "success"
                elif ml_lead >= 1: label, status_color = "🟡 CLOSE", "warning"
                elif ml_lead == 0: label, status_color = "🟡 TIED", "warning"
                elif ml_lead >= -7: label, status_color = "🟠 RISKY", "warning"
                elif ml_lead >= -14: label, status_color = "🔴 WARNING", "error"
                else: label, status_color = "🔴 DANGER", "error"
                pnl = f"Lead: {ml_lead:+d} | Win: +${potential:.2f}"
            else:
                label, status_color, pnl = "⏳ PENDING", "info", f"Win: +${potential:.2f}"
        
        status = "FINAL" if is_final else "HALFTIME" if g['status'] == "STATUS_HALFTIME" else f"Q{g['period']} {g['clock']}" if g['period'] > 0 else "Scheduled"
        type_label = "TOTAL" if pos_type == "totals" else "ML"
        if status_color == "success": st.success(f"**{gk.replace('@', ' @ ')}** | {status} | **{label}**")
        elif status_color == "error": st.error(f"**{gk.replace('@', ' @ ')}** | {status} | **{label}**")
        elif status_color == "warning": st.warning(f"**{gk.replace('@', ' @ ')}** | {status} | **{label}**")
        else: st.info(f"**{gk.replace('@', ' @ ')}** | {status} | **{label}**")
        st.caption(f"🎯 {type_label}: {pick} | {contracts}x @ {price}¢ | {pnl}")
        if st.button("🗑️ Delete", key=f"del_{idx}"):
            st.session_state.positions.pop(idx)
            save_positions(st.session_state.positions)
            st.rerun()
        st.markdown("---")
    if st.button("🗑️ Clear All Positions", use_container_width=True):
        st.session_state.positions = []
        save_positions(st.session_state.positions)
        st.rerun()
else:
    st.info("No active positions — use '➕ Track My Bet' on live games above")

st.caption("⚠️ Educational only. Not financial advice. Edge Score ≠ win probability. v4.1")
