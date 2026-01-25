import streamlit as st
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="NBA Edge Finder", page_icon="🏀", layout="wide")

# Auto-refresh every 24 seconds (1 possession)
st_autorefresh(interval=24000, key="datarefresh")

# ============================================================
# GA4 ANALYTICS - SERVER SIDE
# ============================================================
import uuid
import requests as req_ga

def send_ga4_event(page_title, page_path):
    try:
        url = f"https://www.google-analytics.com/mp/collect?measurement_id=G-NQKY5VQ376&api_secret=n4oBJjH7RXi3dA7aQo2CZA"
        payload = {"client_id": str(uuid.uuid4()), "events": [{"name": "page_view", "params": {"page_title": page_title, "page_location": f"https://bigsnapshot.streamlit.app{page_path}"}}]}
        req_ga.post(url, json=payload, timeout=2)
    except: pass

send_ga4_event("NBA Edge Finder", "/NBA")

# ============================================================
# COOKIE AUTH CHECK
# ============================================================
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

# Check for owner mode
query_params = st.query_params
is_owner = query_params.get("mode") == "owner"

# ============================================================
# TEAM DATA
# ============================================================
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
    "Houston": {"net": 2.8, "pace": 98.0, "home_pct": 0.58, "tier": "mid"},
    "Indiana": {"net": 1.5, "pace": 102.5, "home_pct": 0.55, "tier": "mid"},
    "LA Clippers": {"net": 1.2, "pace": 97.5, "home_pct": 0.52, "tier": "mid"},
    "LA Lakers": {"net": 3.8, "pace": 99.2, "home_pct": 0.62, "tier": "good"},
    "Memphis": {"net": 2.5, "pace": 100.8, "home_pct": 0.58, "tier": "mid"},
    "Miami": {"net": 1.8, "pace": 96.8, "home_pct": 0.55, "tier": "mid"},
    "Milwaukee": {"net": 4.5, "pace": 99.5, "home_pct": 0.68, "tier": "good"},
    "Minnesota": {"net": 6.2, "pace": 98.2, "home_pct": 0.70, "tier": "good"},
    "New Orleans": {"net": -1.5, "pace": 99.8, "home_pct": 0.48, "tier": "weak"},
    "New York": {"net": 5.8, "pace": 97.5, "home_pct": 0.72, "tier": "good"},
    "Oklahoma City": {"net": 9.8, "pace": 98.8, "home_pct": 0.82, "tier": "elite"},
    "Orlando": {"net": 3.2, "pace": 96.5, "home_pct": 0.60, "tier": "mid"},
    "Philadelphia": {"net": 2.5, "pace": 97.8, "home_pct": 0.58, "tier": "mid"},
    "Phoenix": {"net": 1.8, "pace": 98.5, "home_pct": 0.55, "tier": "mid"},
    "Portland": {"net": -5.5, "pace": 99.0, "home_pct": 0.38, "tier": "weak"},
    "Sacramento": {"net": -0.5, "pace": 100.5, "home_pct": 0.52, "tier": "mid"},
    "San Antonio": {"net": -7.5, "pace": 99.8, "home_pct": 0.35, "tier": "weak"},
    "Toronto": {"net": -2.8, "pace": 98.5, "home_pct": 0.45, "tier": "weak"},
    "Utah": {"net": -6.2, "pace": 100.2, "home_pct": 0.38, "tier": "weak"},
    "Washington": {"net": -9.5, "pace": 101.5, "home_pct": 0.28, "tier": "weak"},
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

STAR_PLAYERS = {
    "Boston": ["Jayson Tatum", "Jaylen Brown"],
    "Cleveland": ["Donovan Mitchell", "Darius Garland", "Evan Mobley"],
    "Oklahoma City": ["Shai Gilgeous-Alexander", "Chet Holmgren", "Jalen Williams"],
    "Denver": ["Nikola Jokic", "Jamal Murray"],
    "Milwaukee": ["Giannis Antetokounmpo", "Damian Lillard"],
    "Minnesota": ["Anthony Edwards", "Rudy Gobert"],
    "New York": ["Jalen Brunson", "Karl-Anthony Towns"],
    "Phoenix": ["Kevin Durant", "Devin Booker", "Bradley Beal"],
    "LA Lakers": ["LeBron James", "Anthony Davis"],
    "Golden State": ["Stephen Curry", "Draymond Green"],
    "Dallas": ["Luka Doncic", "Kyrie Irving"],
    "Philadelphia": ["Joel Embiid", "Tyrese Maxey"],
    "Miami": ["Jimmy Butler", "Bam Adebayo"],
    "Memphis": ["Ja Morant", "Jaren Jackson Jr."],
    "New Orleans": ["Zion Williamson", "Brandon Ingram"],
    "Sacramento": ["De'Aaron Fox", "Domantas Sabonis"],
    "Indiana": ["Tyrese Haliburton", "Pascal Siakam"],
    "Orlando": ["Paolo Banchero", "Franz Wagner"],
    "LA Clippers": ["Kawhi Leonard", "Paul George"],
    "Houston": ["Jalen Green", "Alperen Sengun"],
    "San Antonio": ["Victor Wembanyama"],
    "Atlanta": ["Trae Young", "Dejounte Murray"],
    "Chicago": ["Zach LaVine", "DeMar DeRozan"],
    "Brooklyn": ["Mikal Bridges", "Cam Thomas"],
    "Charlotte": ["LaMelo Ball", "Brandon Miller"],
    "Detroit": ["Cade Cunningham", "Jaden Ivey"],
    "Portland": ["Anfernee Simons", "Scoot Henderson"],
    "Toronto": ["Scottie Barnes", "RJ Barrett"],
    "Utah": ["Lauri Markkanen", "Collin Sexton"],
    "Washington": ["Jordan Poole", "Kyle Kuzma"],
}

H2H_EDGES = {
    ("Boston", "Philadelphia"): 1.5, ("Boston", "New York"): 1.5, ("Milwaukee", "Chicago"): 1.5,
    ("Cleveland", "Detroit"): 1.5, ("Oklahoma City", "Utah"): 1.5, ("Denver", "Minnesota"): 1.5,
    ("LA Lakers", "LA Clippers"): 1.0, ("Golden State", "Sacramento"): 1.5, ("Phoenix", "Portland"): 1.5,
    ("Miami", "Orlando"): 1.5, ("Dallas", "San Antonio"): 1.5, ("Memphis", "New Orleans"): 1.0,
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

POSITIONS_FILE = "nba_positions.json"

THRESHOLDS = [210.5, 215.5, 220.5, 225.5, 230.5, 235.5, 240.5, 245.5, 250.5, 255.5]

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

if "positions" not in st.session_state:
    st.session_state.positions = load_positions()

# ============================================================
# FETCH FUNCTIONS
# ============================================================
@st.cache_data(ttl=24)
def fetch_games():
    """Fetch today's games from ESPN"""
    today = datetime.now(eastern).strftime('%Y%m%d')
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={today}"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        games = []
        for event in data.get("events", []):
            comp = event.get("competitions", [{}])[0]
            competitors = comp.get("competitors", [])
            if len(competitors) < 2: continue
            
            home_team, away_team = None, None
            home_score, away_score = 0, 0
            
            for c in competitors:
                team_name = TEAM_ABBREVS.get(c.get("team", {}).get("displayName", ""), c.get("team", {}).get("displayName", ""))
                score = int(c.get("score", 0) or 0)
                if c.get("homeAway") == "home":
                    home_team = team_name
                    home_score = score
                else:
                    away_team = team_name
                    away_score = score
            
            status = event.get("status", {}).get("type", {}).get("name", "STATUS_SCHEDULED")
            period = event.get("status", {}).get("period", 0)
            clock = event.get("status", {}).get("displayClock", "")
            game_time = event.get("date", "")
            
            # Calculate minutes played
            minutes_played = 0
            if period > 0:
                completed_quarters = (period - 1) * 12
                if clock:
                    try:
                        parts = clock.split(":")
                        mins_left = int(parts[0])
                        minutes_played = completed_quarters + (12 - mins_left)
                    except:
                        minutes_played = completed_quarters
            
            games.append({
                "away": away_team,
                "home": home_team,
                "away_score": away_score,
                "home_score": home_score,
                "status": status,
                "period": period,
                "clock": clock,
                "game_time": game_time,
                "minutes_played": minutes_played,
                "total_score": home_score + away_score
            })
        return games
    except Exception as e:
        st.error(f"ESPN fetch error: {e}")
        return []

@st.cache_data(ttl=300)
def fetch_injuries():
    """Fetch injury data from ESPN with status"""
    url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/injuries"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        injuries = {}
        for team_data in data.get("injuries", []):
            team_name = team_data.get("displayName", "")
            team_key = TEAM_ABBREVS.get(team_name, team_name)
            if not team_key:
                continue
            injuries[team_key] = []
            for player in team_data.get("injuries", []):
                athlete = player.get("athlete", {})
                name = athlete.get("displayName", "")
                status = player.get("status", "")
                if name:
                    injuries[team_key].append({"name": name, "status": status})
        return injuries
    except:
        return {}

@st.cache_data(ttl=300)
def fetch_injuries_simple():
    """Fetch injury data from ESPN - simple list of OUT players"""
    url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/injuries"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        injuries = {}
        for team in data.get("items", []):
            team_name = TEAM_ABBREVS.get(team.get("team", {}).get("displayName", ""), "")
            if not team_name:
                continue
            out_players = []
            for inj in team.get("injuries", []):
                status = inj.get("status", "")
                if status.lower() in ["out", "doubtful"]:
                    player = inj.get("athlete", {}).get("displayName", "")
                    if player:
                        out_players.append(player)
            injuries[team_name] = out_players
        return injuries
    except:
        return {}

@st.cache_data(ttl=300)
def fetch_yesterday_teams():
    """Get teams that played yesterday (B2B detection)"""
    yesterday = (datetime.now(eastern) - timedelta(days=1)).strftime('%Y%m%d')
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={yesterday}"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        teams = set()
        for event in data.get("events", []):
            for comp in event.get("competitions", []):
                for c in comp.get("competitors", []):
                    team_name = TEAM_ABBREVS.get(c.get("team", {}).get("displayName", ""), "")
                    if team_name:
                        teams.add(team_name)
        return teams
    except:
        return set()

# ============================================================
# EDGE CALCULATION
# ============================================================
def calc_pregame_edge(away, home, injuries, b2b_teams):
    """Calculate pre-game edge score (50 = neutral, higher = home favored)"""
    home_pts, away_pts = 0, 0
    factors_home, factors_away = [], []
    
    home_stats = TEAM_STATS.get(home, {})
    away_stats = TEAM_STATS.get(away, {})
    
    # B2B fatigue
    if away in b2b_teams:
        home_pts += 4
        factors_home.append("🛏️ Opp B2B +4")
    if home in b2b_teams:
        away_pts += 4
        factors_away.append("🛏️ Opp B2B +4")
    
    # Star injuries
    home_injuries = injuries.get(home, [])
    away_injuries = injuries.get(away, [])
    home_stars = STAR_PLAYERS.get(home, [])
    away_stars = STAR_PLAYERS.get(away, [])
    
    for star in home_stars:
        if any(star.lower() in inj.lower() for inj in home_injuries):
            away_pts += 5 if home_stars.index(star) == 0 else 3
            factors_away.append(f"🏥 {star.split()[-1]} OUT")
    
    for star in away_stars:
        if any(star.lower() in inj.lower() for inj in away_injuries):
            home_pts += 5 if away_stars.index(star) == 0 else 3
            factors_home.append(f"🏥 {star.split()[-1]} OUT")
    
    # Net rating gap
    net_gap = home_stats.get("net", 0) - away_stats.get("net", 0)
    if net_gap >= 15:
        home_pts += 3
        factors_home.append("📊 Net +15")
    elif net_gap >= 10:
        home_pts += 2
        factors_home.append("📊 Net +10")
    elif net_gap >= 5:
        home_pts += 1
        factors_home.append("📊 Net +5")
    elif net_gap <= -15:
        away_pts += 3
        factors_away.append("📊 Net +15")
    elif net_gap <= -10:
        away_pts += 2
        factors_away.append("📊 Net +10")
    elif net_gap <= -5:
        away_pts += 1
        factors_away.append("📊 Net +5")
    
    # H2H edge
    h2h = H2H_EDGES.get((home, away), 0)
    if h2h > 0:
        home_pts += h2h
        factors_home.append("🆚 H2H")
    h2h_rev = H2H_EDGES.get((away, home), 0)
    if h2h_rev > 0:
        away_pts += h2h_rev
        factors_away.append("🆚 H2H")
    
    # Denver altitude
    if home == "Denver":
        home_pts += 1.5
        factors_home.append("🏔️ Altitude")
    
    # Elite road team vs weak home
    if away_stats.get("tier") in ["elite", "good"] and home_stats.get("tier") == "weak":
        away_pts += 1.5
        factors_away.append("🛫 Elite Road")
    
    # Base score with net rating influence
    base = 50 + (net_gap * 1.5)
    base = max(25, min(75, base))
    
    # Apply factor points
    score = base + home_pts - away_pts
    score = max(10, min(90, score))
    
    if score >= 50:
        return home, int(score), factors_home
    else:
        return away, int(100 - score), factors_away

def calc_live_edge(game, injuries, b2b_teams):
    """Calculate live edge based on current score"""
    away, home = game['away'], game['home']
    away_score, home_score = game['away_score'], game['home_score']
    period = game['period']
    minutes = game['minutes_played']
    total = game['total_score']
    
    lead = home_score - away_score
    
    # Start with pregame edge
    pick, pregame_score, factors = calc_pregame_edge(away, home, injuries, b2b_teams)
    
    # Calculate pace
    pace = round(total / minutes, 2) if minutes > 0 else 0
    pace_label = "🔥 FAST" if pace > 5.0 else "⚖️ AVG" if pace > 4.2 else "🐢 SLOW"
    
    # Live adjustments
    live_adj = 0
    
    # Lead factor
    if abs(lead) >= 20:
        live_adj = 25 if lead > 0 else -25
    elif abs(lead) >= 15:
        live_adj = 18 if lead > 0 else -18
    elif abs(lead) >= 10:
        live_adj = 12 if lead > 0 else -12
    elif abs(lead) >= 5:
        live_adj = 6 if lead > 0 else -6
    
    # Quarter context
    if period == 4:
        if abs(lead) >= 10:
            live_adj += 15 if lead > 0 else -15
        elif abs(lead) >= 5:
            live_adj += 8 if lead > 0 else -8
    elif period == 3 and abs(lead) >= 15:
        live_adj += 8 if lead > 0 else -8
    
    # Pace adjustment
    if pace > 5.0 and abs(lead) >= 10:
        live_adj -= 4 if lead > 0 else 4  # Fast pace = leads less sticky
    elif pace < 4.2 and abs(lead) >= 10:
        live_adj += 3 if lead > 0 else -3  # Slow pace = leads more sticky
    
    # Calculate final score
    final_score = pregame_score + live_adj if pick == home else (100 - pregame_score) + live_adj
    final_score = max(10, min(95, final_score))
    
    # Determine pick
    if lead > 0:
        live_pick = home
    elif lead < 0:
        live_pick = away
    else:
        live_pick = pick
    
    # Project total
    if minutes >= 6:
        proj_total = round((total / minutes) * 48)
    else:
        proj_total = 220  # Default
    
    return {
        "pick": live_pick,
        "score": int(final_score),
        "lead": lead,
        "pace": pace,
        "pace_label": pace_label,
        "proj_total": proj_total,
        "factors": factors
    }

# ============================================================
# KALSHI LINKS
# ============================================================
def get_kalshi_ml_link(team):
    team_map = {
        "Atlanta": "ATL", "Boston": "BOS", "Brooklyn": "BKN", "Charlotte": "CHA",
        "Chicago": "CHI", "Cleveland": "CLE", "Dallas": "DAL", "Denver": "DEN",
        "Detroit": "DET", "Golden State": "GSW", "Houston": "HOU", "Indiana": "IND",
        "LA Clippers": "LAC", "LA Lakers": "LAL", "Memphis": "MEM", "Miami": "MIA",
        "Milwaukee": "MIL", "Minnesota": "MIN", "New Orleans": "NOP", "New York": "NYK",
        "Oklahoma City": "OKC", "Orlando": "ORL", "Philadelphia": "PHI", "Phoenix": "PHX",
        "Portland": "POR", "Sacramento": "SAC", "San Antonio": "SAS", "Toronto": "TOR",
        "Utah": "UTA", "Washington": "WAS"
    }
    abbrev = team_map.get(team, "")
    today = datetime.now(eastern).strftime('%y%b%d').upper()
    return f"https://kalshi.com/markets/kxnba/nba-regular-season-games?ticker=KXNBA-{today}-{abbrev}"

def get_kalshi_totals_link(away, home):
    team_map = {
        "Atlanta": "ATL", "Boston": "BOS", "Brooklyn": "BKN", "Charlotte": "CHA",
        "Chicago": "CHI", "Cleveland": "CLE", "Dallas": "DAL", "Denver": "DEN",
        "Detroit": "DET", "Golden State": "GSW", "Houston": "HOU", "Indiana": "IND",
        "LA Clippers": "LAC", "LA Lakers": "LAL", "Memphis": "MEM", "Miami": "MIA",
        "Milwaukee": "MIL", "Minnesota": "MIN", "New Orleans": "NOP", "New York": "NYK",
        "Oklahoma City": "OKC", "Orlando": "ORL", "Philadelphia": "PHI", "Phoenix": "PHX",
        "Portland": "POR", "Sacramento": "SAC", "San Antonio": "SAS", "Toronto": "TOR",
        "Utah": "UTA", "Washington": "WAS"
    }
    away_abbrev = team_map.get(away, "")
    home_abbrev = team_map.get(home, "")
    today = datetime.now(eastern).strftime('%y%b%d').upper()
    return f"https://kalshi.com/markets/kxnbao/nba-total-regular-season-game-points?ticker=KXNBAO-{today}-{away_abbrev}{home_abbrev}"

# ============================================================
# SIDEBAR LEGEND
# ============================================================
with st.sidebar:
    st.header("📖 ALIGNMENT GUIDE")
    st.markdown("""
    ### How To Read Scores
    
    | Score | Label | Action |
    |-------|-------|--------|
    | **70+** | 🟢 STRONG | Best opportunities |
    | **60-69** | 🟢 GOOD | Worth considering |
    | **50-59** | 🟡 MODERATE | Wait for live |
    | **Below 50** | ⚪ WEAK | Skip |
    
    ---
    
    ### Injury Impact
    
    | Stars | Impact |
    |-------|--------|
    | ⭐⭐⭐ | MVP out = +5 |
    | ⭐⭐ | All-Star = +3 |
    | ⭐ | Starter = +1 |
    
    ---
    
    ### What We Track
    
    - 🛏️ **Opp B2B** — +4
    - 📊 **Net Rating** — +1 to +3
    - 🏥 **Star OUT** — +3 to +5
    - 🆚 **H2H** — +1.5
    - 🏔️ **Altitude** — +1.5
    - 🛫 **Elite Road** — +1
    
    ---
    
    ### When To Act
    
    **Pre-Game:** Focus on 70+ STRONG
    
    **Live:** Wait for Q2 with 10+ lead and 🐢 SLOW pace
    
    ---
    
    ### Pace Guide
    
    | Pace | Label | Totals |
    |------|-------|--------|
    | <4.5 | 🐢 SLOW | Buy NO |
    | 4.5-4.8 | ⚖️ AVG | Wait |
    | 4.8-5.2 | 🔥 FAST | Buy YES |
    | >5.2 | 🚀 SHOOTOUT | Buy YES |
    
    ---
    
    ### Cushion Guide
    
    **+10 or more** = Very safe  
    **+6 to +9** = Safe  
    **Under +6** = Risky
    
    ---
    
    *We show the edge — you make the call.*
    """)
    st.divider()
    st.caption("v4.5 NBA EDGE")

# ============================================================
# UI
# ============================================================
st.title("🏀 NBA EDGE FINDER")
st.caption(f"v4.5 • {now.strftime('%b %d, %Y %I:%M %p ET')} • Auto-refresh: 24s")

# Fetch data
games = fetch_games()
injuries = fetch_injuries()
injuries_simple = fetch_injuries_simple()
b2b_teams = fetch_yesterday_teams()

# Get today's teams
today_teams = set()
for g in games:
    today_teams.add(g['away'])
    today_teams.add(g['home'])

# Separate games
live_games = [g for g in games if g['status'] == 'STATUS_IN_PROGRESS']
scheduled_games = [g for g in games if g['status'] == 'STATUS_SCHEDULED']
final_games = [g for g in games if g['status'] == 'STATUS_FINAL']

# Stats row
c1, c2, c3, c4 = st.columns(4)
c1.metric("Today's Games", len(games))
c2.metric("Live Now", len(live_games))
c3.metric("B2B Teams", len(b2b_teams))
c4.metric("Final", len(final_games))

st.divider()

# ============================================================
# 🏥 INJURY REPORT
# ============================================================
st.subheader("🏥 INJURY REPORT")

injured_stars = []
for team, team_injuries in injuries.items():
    if team not in today_teams:
        continue
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
                    "name": name, 
                    "team": team, 
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
                <div style="color:#fff;font-weight:bold">{stars} {inj['name']} 🔥</div>
                <div style="color:{status_color};font-size:0.85em">{inj['status']} • {inj['team']}</div>
            </div>""", unsafe_allow_html=True)
    
    if b2b_teams:
        b2b_today = b2b_teams.intersection(today_teams)
        if b2b_today:
            b2b_list = ", ".join(sorted(b2b_today))
            st.markdown(f"""<div style="background:#1a2a3a;padding:10px 14px;border-radius:6px;margin-top:10px">
                <span style="color:#38bdf8">🏨 B2B Teams:</span> <span style="color:#fff">{b2b_list}</span>
            </div>""", unsafe_allow_html=True)
else:
    if b2b_teams:
        b2b_today = b2b_teams.intersection(today_teams)
        if b2b_today:
            b2b_list = ", ".join(sorted(b2b_today))
            st.markdown(f"""<div style="background:#1a2a3a;padding:10px 14px;border-radius:6px">
                <span style="color:#38bdf8">🏨 B2B Teams:</span> <span style="color:#fff">{b2b_list}</span>
            </div>""", unsafe_allow_html=True)
        else:
            st.info("No major star injuries or B2B teams for today's games")
    else:
        st.info("No major star injuries reported for today's games")

st.divider()

# ============================================================
# 🔴 LIVE EDGE MONITOR
# ============================================================
if live_games:
    st.subheader("🔴 LIVE EDGE MONITOR")
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); border: 1px solid #4a9eff; border-radius: 8px; padding: 12px 16px; margin-bottom: 16px;">
    <p style="color: #4a9eff; font-weight: 600; margin: 0 0 6px 0;">📊 REAL-TIME FACTOR ALIGNMENT</p>
    <p style="color: #ccc; font-size: 0.85em; margin: 0; line-height: 1.5;">
    We show the edge — <strong>you make the call</strong>. Edge scores update every 24 seconds. Higher = more factors favor that side. This is <strong>not</strong> a prediction.
    </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sort by edge score
    live_with_edge = []
    for g in live_games:
        edge = calc_live_edge(g, injuries, b2b_teams)
        live_with_edge.append((g, edge))
    live_with_edge.sort(key=lambda x: x[1]['score'], reverse=True)
    
    for g, edge in live_with_edge:
        mins = g['minutes_played']
        
        # Status labels
        if mins < 6:
            status_label = "⏳ TOO EARLY"
            status_color = "#888"
        elif abs(edge['lead']) < 5:
            status_label = "⚖️ TOO CLOSE"
            status_color = "#ffa500"
        elif edge['score'] >= 75:
            status_label = f"🟢 {edge['score']}/100"
            status_color = "#22c55e"
        elif edge['score'] >= 60:
            status_label = f"🟡 {edge['score']}/100"
            status_color = "#eab308"
        else:
            status_label = f"⚪ {edge['score']}/100"
            status_color = "#888"
        
        # Build card
        lead_display = f"+{edge['lead']}" if edge['lead'] > 0 else str(edge['lead'])
        leader = g['home'] if edge['lead'] > 0 else g['away'] if edge['lead'] < 0 else "TIED"
        
        # Safe thresholds
        safe_no = edge['proj_total'] + 12
        safe_yes = edge['proj_total'] - 8
        no_cushion = safe_no - edge['proj_total']
        yes_cushion = edge['proj_total'] - safe_yes
        
        # Cushion color
        no_color = "#22c55e" if no_cushion >= 10 else "#9acd32" if no_cushion >= 5 else "#888"
        yes_color = "#22c55e" if yes_cushion >= 10 else "#9acd32" if yes_cushion >= 5 else "#888"
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1e1e2e 0%, #2a2a3e 100%); border-radius: 12px; padding: 16px; margin-bottom: 12px; border: 1px solid #444;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="color: #fff; font-size: 1.1em; font-weight: 600;">{g['away']} @ {g['home']}</span>
                <span style="color: #ff6b6b; font-size: 0.9em;">Q{g['period']} {g['clock']}</span>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <span style="color: #fff; font-size: 1.4em; font-weight: 700;">{g['away_score']} - {g['home_score']}</span>
                <span style="color: {status_color}; font-weight: 600;">{status_label}</span>
            </div>
            <div style="color: #aaa; font-size: 0.9em; margin-bottom: 10px;">
                Edge: <strong style="color: #fff;">{leader}</strong> ({lead_display}) {edge['pace_label']}
            </div>
            <div style="background: #333; border-radius: 8px; padding: 10px; margin-bottom: 12px;">
                <span style="color: #888;">Proj: {edge['proj_total']}</span> | 
                <span style="color: {no_color};">NO {safe_no} (+{no_cushion})</span> | 
                <span style="color: {yes_color};">YES {safe_yes} (+{yes_cushion})</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Buttons
        bc1, bc2, bc3 = st.columns(3)
        with bc1:
            st.link_button(f"🎯 {edge['pick']} ML", get_kalshi_ml_link(edge['pick']), use_container_width=True)
        with bc2:
            st.link_button(f"⬇️ NO {safe_no}", get_kalshi_totals_link(g['away'], g['home']), use_container_width=True)
        with bc3:
            st.link_button(f"⬆️ YES {safe_yes}", get_kalshi_totals_link(g['away'], g['home']), use_container_width=True)
        
        # Track position (owner only)
        if is_owner:
            with st.expander("📝 Track My Bet"):
                bet_type = st.selectbox("Type", ["ML", "OVER", "UNDER"], key=f"type_{g['away']}_{g['home']}")
                if bet_type == "ML":
                    team = st.selectbox("Team", [g['away'], g['home']], key=f"team_{g['away']}_{g['home']}")
                else:
                    line = st.number_input("Line", value=float(edge['proj_total']), step=0.5, key=f"line_{g['away']}_{g['home']}")
                price = st.number_input("Entry ¢", value=50, step=1, key=f"price_{g['away']}_{g['home']}")
                contracts = st.number_input("Contracts", value=10, step=1, key=f"contracts_{g['away']}_{g['home']}")
                if st.button("💾 Save", key=f"save_{g['away']}_{g['home']}"):
                    pos = {
                        "game": f"{g['away']}@{g['home']}",
                        "type": bet_type,
                        "team": team if bet_type == "ML" else None,
                        "line": line if bet_type != "ML" else None,
                        "price": price,
                        "contracts": contracts,
                        "time": now.strftime("%I:%M %p")
                    }
                    st.session_state.positions.append(pos)
                    save_positions(st.session_state.positions)
                    st.success("Saved!")
                    st.rerun()
        
        st.markdown("---")

else:
    st.info("🕐 No live games right now. Check back when games tip off.")

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
for g in live_games:
    mins = g['minutes_played']
    total = g['total_score']
    if mins < cush_min or mins <= 0:
        continue
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
    
    if cushion < 6:
        continue
    
    if cush_side == "NO":
        if pace < 4.5:
            pace_status, pace_color = "✅ SLOW", "#00ff00"
        elif pace < 4.8:
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
        'game': f"{g['away']}@{g['home']}", 
        'away': g['away'],
        'home': g['home'],
        'total': total, 
        'mins': mins, 
        'pace': pace,
        'pace_status': pace_status, 
        'pace_color': pace_color,
        'projected': projected_final, 
        'cushion': cushion,
        'safe_line': safe_line, 
        'period': g['period'], 
        'clock': g['clock']
    })

cush_results.sort(key=lambda x: x['cushion'], reverse=True)

if cush_results:
    for r in cush_results:
        kalshi_url = get_kalshi_totals_link(r['away'], r['home'])
        btn_color = "#00aa00" if cush_side == "NO" else "#cc6600"
        st.markdown(f"""<div style="display:flex;align-items:center;justify-content:space-between;background:#0f172a;padding:10px 14px;margin-bottom:6px;border-radius:8px;border-left:3px solid {r['pace_color']};flex-wrap:wrap;gap:8px">
        <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap">
            <b style="color:#fff">{r['away']} @ {r['home']}</b>
            <span style="color:#888">Q{r['period']} {r['clock']}</span>
            <span style="color:#888">{r['total']}pts/{r['mins']:.0f}min</span>
            <span style="color:#888">Proj: <b style="color:#fff">{r['projected']}</b></span>
            <span style="background:#ff8800;color:#000;padding:2px 8px;border-radius:4px;font-weight:bold">🎯 {r['safe_line']}</span>
            <span style="color:#00ff00;font-weight:bold">+{r['cushion']:.0f}</span>
            <span style="color:{r['pace_color']}">{r['pace_status']}</span>
        </div>
        </div>""", unsafe_allow_html=True)
        st.link_button(f"BUY {cush_side} {r['safe_line']}", kalshi_url, use_container_width=True)
else:
    st.info(f"No {cush_side} opportunities with 6+ cushion yet — need live games with 6+ minutes played")

st.divider()

# ============================================================
# 🔥 PACE SCANNER
# ============================================================
st.subheader("🔥 PACE SCANNER")
st.caption("Track scoring pace for all live games")

pace_data = []
for g in live_games:
    mins = g['minutes_played']
    if mins >= 6:
        pace = round(g['total_score'] / mins, 2)
        pace_data.append({
            "game": f"{g['away']}@{g['home']}",
            "away": g['away'],
            "home": g['home'],
            "pace": pace, 
            "proj": round(pace * 48), 
            "total": g['total_score'], 
            "mins": mins, 
            "period": g['period'], 
            "clock": g['clock']
        })

pace_data.sort(key=lambda x: x['pace'])

if pace_data:
    for p in pace_data:
        kalshi_url = get_kalshi_totals_link(p['away'], p['home'])
        
        if p['pace'] < 4.5:
            lbl, clr = "🐢 SLOW", "#00ff00"
            base_idx = next((i for i, t in enumerate(THRESHOLDS) if t > p['proj']), len(THRESHOLDS)-1)
            safe_idx = min(base_idx + 2, len(THRESHOLDS) - 1)
            rec_line = THRESHOLDS[safe_idx]
            rec_side = "NO"
            btn_color = "#00aa00"
        elif p['pace'] < 4.8:
            lbl, clr = "⚖️ AVG", "#ffff00"
            rec_line = None
            rec_side = None
            btn_color = None
        elif p['pace'] < 5.2:
            lbl, clr = "🔥 FAST", "#ff8800"
            base_idx = next((i for i in range(len(THRESHOLDS)-1, -1, -1) if THRESHOLDS[i] < p['proj']), 0)
            safe_idx = max(base_idx - 2, 0)
            rec_line = THRESHOLDS[safe_idx]
            rec_side = "YES"
            btn_color = "#cc6600"
        else:
            lbl, clr = "🚀 SHOOTOUT", "#ff0000"
            base_idx = next((i for i in range(len(THRESHOLDS)-1, -1, -1) if THRESHOLDS[i] < p['proj']), 0)
            safe_idx = max(base_idx - 2, 0)
            rec_line = THRESHOLDS[safe_idx]
            rec_side = "YES"
            btn_color = "#cc0000"
        
        st.markdown(f"""<div style="display:flex;align-items:center;justify-content:space-between;background:#0f172a;padding:8px 12px;margin-bottom:4px;border-radius:6px;border-left:3px solid {clr};flex-wrap:wrap;gap:8px">
        <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">
            <b style="color:#fff">{p['away']} @ {p['home']}</b>
            <span style="color:#666">Q{p['period']} {p['clock']}</span>
            <span style="color:#888">{p['total']}pts/{p['mins']:.0f}min</span>
            <span style="color:{clr};font-weight:bold">{p['pace']}/min {lbl}</span>
            <span style="color:#888">Proj: <b style="color:#fff">{p['proj']}</b></span>
        </div>
        </div>""", unsafe_allow_html=True)
        
        if rec_line and rec_side:
            st.link_button(f"BUY {rec_side} {rec_line}", kalshi_url, use_container_width=True)
else:
    st.info("No games with 6+ minutes played yet")

st.divider()

# ============================================================
# 🎯 PRE-GAME ALIGNMENT
# ============================================================
if scheduled_games:
    st.subheader("🎯 PRE-GAME ALIGNMENT")
    st.markdown("*Look for **60+** scores with multiple factors. Higher = more factors favor that side.*")
    
    # Sort by edge score (highest first)
    games_with_edge = []
    for g in scheduled_games:
        pick, score, factors = calc_pregame_edge(g['away'], g['home'], injuries, b2b_teams)
        games_with_edge.append((g, pick, score, factors))
    games_with_edge.sort(key=lambda x: x[2], reverse=True)
    
    for g, pick, score, factors in games_with_edge:
        # Color coding - 70+ STRONG, 60-69 GOOD, 50-59 MODERATE, <50 WEAK
        if score >= 70:
            score_color = "#22c55e"  # Bright green
            tier = "🟢 STRONG"
            border_color = "#22c55e"
        elif score >= 60:
            score_color = "#22c55e"  # Green
            tier = "🟢 GOOD"
            border_color = "#22c55e"
        elif score >= 50:
            score_color = "#eab308"  # Yellow
            tier = "🟡 MODERATE"
            border_color = "#eab308"
        else:
            score_color = "#888"  # Gray
            tier = "⚪ WEAK"
            border_color = "#444"
        
        st.markdown(f"""
        <div style="background: #1e1e2e; border-radius: 10px; padding: 14px; margin-bottom: 10px; border-left: 4px solid {border_color};">
            <div style="display: flex; justify-content: space-between;">
                <span style="color: #fff; font-weight: 600;">{g['away']} @ {g['home']}</span>
                <span style="color: {score_color}; font-weight: 600;">{tier} {score}/100</span>
            </div>
            <div style="color: #888; font-size: 0.85em; margin-top: 4px;">
                Edge: <strong style="color: #fff;">{pick}</strong> • {' • '.join(factors[:3]) if factors else 'No strong factors'}
            </div>
        </div>
        """, unsafe_allow_html=True)

# ============================================================
# 📊 ACTIVE POSITIONS (OWNER ONLY)
# ============================================================
if is_owner and st.session_state.positions:
    st.divider()
    st.subheader("📊 ACTIVE POSITIONS")
    
    for i, pos in enumerate(st.session_state.positions):
        game_key = pos.get("game", "")
        # Find live game
        live_game = None
        for g in live_games:
            if f"{g['away']}@{g['home']}" == game_key:
                live_game = g
                break
        
        if live_game:
            total = live_game['total_score']
            mins = live_game['minutes_played']
            pace = round(total / mins, 2) if mins > 0 else 0
            
            # Status
            if pos['type'] == "UNDER":
                if pace < 4.5:
                    status = "🟢 VERY SAFE"
                elif pace < 4.8:
                    status = "🟡 WARNING"
                else:
                    status = "🔴 DANGER"
            elif pos['type'] == "OVER":
                if pace > 5.2:
                    status = "🟢 VERY SAFE"
                elif pace > 4.8:
                    status = "🟡 WARNING"
                else:
                    status = "🔴 DANGER"
            else:
                lead = live_game['home_score'] - live_game['away_score']
                if pos['team'] == live_game['home']:
                    if lead >= 15:
                        status = "🟢 CRUISING"
                    elif lead >= 5:
                        status = "🟡 CLOSE"
                    else:
                        status = "🔴 BEHIND"
                else:
                    if lead <= -15:
                        status = "🟢 CRUISING"
                    elif lead <= -5:
                        status = "🟡 CLOSE"
                    else:
                        status = "🔴 BEHIND"
            
            st.markdown(f"**{game_key}** | {pos['type']} {pos.get('line', pos.get('team', ''))} @ {pos['price']}¢ x{pos['contracts']} | {status}")
        else:
            st.markdown(f"**{game_key}** | {pos['type']} {pos.get('line', pos.get('team', ''))} @ {pos['price']}¢ x{pos['contracts']}")
        
        if st.button("🗑️", key=f"del_{i}"):
            st.session_state.positions.pop(i)
            save_positions(st.session_state.positions)
            st.rerun()

# ============================================================
# FOOTER
# ============================================================
st.divider()

with st.expander("📖 HOW TO USE", expanded=False):
    st.markdown("""
    ### Edge Score Guide
    
    | Score | Label | Action |
    |-------|-------|--------|
    | **70+** | 🟢 STRONG | Best opportunities — multiple factors |
    | **60-69** | 🟢 GOOD | Worth considering — solid edge |
    | **50-59** | 🟡 MODERATE | Wait for live confirmation |
    | **Below 50** | ⚪ WEAK | Skip |
    | **TOO CLOSE** | ⚖️ | No clear edge — lead under 5 |
    | **TOO EARLY** | ⏳ | Under 6 minutes played |
    
    ---
    
    ### Injury Report Guide
    
    | Stars | Tier | Impact |
    |-------|------|--------|
    | ⭐⭐⭐ | MVP-level | +5 points to opponent edge |
    | ⭐⭐ | All-Star | +3 points to opponent edge |
    | ⭐ | Starter | +1 point to opponent edge |
    
    **Status colors:**
    - 🔴 **OUT** = Confirmed out
    - 🟠 **DTD** = Day-to-day (monitor)
    - 🟠 **DOUBT** = Doubtful to play
    
    ---
    
    ### Live Timing Guide
    
    | Quarter | Lead | Conviction |
    |---------|------|------------|
    | Q1 | Any | 🔴 LOW — don't enter |
    | Q2 | 10+ | 🟡 MEDIUM — enter if 🐢 SLOW pace |
    | Q3 | 12+ | 🟢 GOOD — sweet spot |
    | Q4 | 15+ | 🟢🟢 HIGH — but price may be high |
    
    **Sweet spot:** Q2 with 12+ lead and 🐢 SLOW pace
    
    ---
    
    ### Pace Guide
    
    | Pace | Label | Meaning |
    |------|-------|---------|
    | <4.5 pts/min | 🐢 SLOW | Leads stick — good for NO bets |
    | 4.5-4.8 | ⚖️ AVG | Normal game flow |
    | 4.8-5.2 pts/min | 🔥 FAST | Leads can evaporate — consider YES |
    | >5.2 pts/min | 🚀 SHOOTOUT | High scoring — buy YES |
    
    ---
    
    ### Cushion Scanner
    
    Finds safe totals opportunities based on projected final score:
    - **+10 cushion** = Very safe threshold
    - **+6 to +9** = Safe threshold  
    - **Under +6** = Not shown (too risky)
    
    Safe NO = 2 levels ABOVE projected  
    Safe YES = 2 levels BELOW projected
    
    ---
    
    ### Key Factors We Track
    
    - 🛏️ **Opp B2B** — Opponent on back-to-back (+4)
    - 📊 **Net Rating** — Team strength gap (+1 to +3)
    - 🏥 **Star OUT** — Key player injured (+3 to +5)
    - 🆚 **H2H** — Historical matchup edge (+1.5)
    - 🏔️ **Altitude** — Denver home advantage (+1.5)
    - 🛫 **Elite Road** — Strong team traveling (+1)
    
    ---
    
    ### Important Reminders
    
    ⚠️ Edge Score ≠ Win Probability  
    ⚠️ This is not a predictive model  
    ⚠️ Past performance doesn't guarantee results  
    ⚠️ Only risk what you can afford to lose  
    """)

st.caption("⚠️ Educational only. Not financial advice. Edge Score ≠ win probability. v4.5")
