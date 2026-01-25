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

cookie_manager = stx.CookieManager(key="nba_cookie")

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

try:
    saved_auth = cookie_manager.get("authenticated")
    if saved_auth == "true":
        st.session_state.authenticated = True
except:
    pass

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

KALSHI_ABBREVS = {
    "Atlanta": "ATL", "Boston": "BOS", "Brooklyn": "BKN", "Charlotte": "CHA",
    "Chicago": "CHI", "Cleveland": "CLE", "Dallas": "DAL", "Denver": "DEN",
    "Detroit": "DET", "Golden State": "GSW", "Houston": "HOU", "Indiana": "IND",
    "LA Clippers": "LAC", "LA Lakers": "LAL", "Memphis": "MEM", "Miami": "MIA",
    "Milwaukee": "MIL", "Minnesota": "MIN", "New Orleans": "NOP", "New York": "NYK",
    "Oklahoma City": "OKC", "Orlando": "ORL", "Philadelphia": "PHI", "Phoenix": "PHX",
    "Portland": "POR", "Sacramento": "SAC", "San Antonio": "SAS", "Toronto": "TOR",
    "Utah": "UTA", "Washington": "WAS"
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
    "Atlanta": ["Trae Young"],
    "Chicago": ["Zach LaVine", "DeMar DeRozan"],
    "Brooklyn": ["Mikal Bridges", "Cam Thomas"],
    "Charlotte": ["LaMelo Ball", "Brandon Miller"],
    "Detroit": ["Cade Cunningham", "Jaden Ivey"],
    "Portland": ["Anfernee Simons", "Scoot Henderson"],
    "Toronto": ["Scottie Barnes", "RJ Barrett"],
    "Utah": ["Lauri Markkanen", "Collin Sexton"],
    "Washington": ["Jordan Poole", "Kyle Kuzma"],
}

STAR_TIERS = {
    "Nikola Jokic": 3, "Shai Gilgeous-Alexander": 3, "Giannis Antetokounmpo": 3, "Luka Doncic": 3,
    "Joel Embiid": 3, "Jayson Tatum": 3, "Stephen Curry": 3, "Kevin Durant": 3, "LeBron James": 3,
    "Anthony Edwards": 3, "Ja Morant": 3, "Donovan Mitchell": 3, "Trae Young": 3, "Devin Booker": 3,
    "Jaylen Brown": 2, "Anthony Davis": 2, "Damian Lillard": 2, "Kyrie Irving": 2, "Jimmy Butler": 2,
    "Bam Adebayo": 2, "Tyrese Haliburton": 2, "De'Aaron Fox": 2, "Jalen Brunson": 2, "Chet Holmgren": 2,
    "Paolo Banchero": 2, "Franz Wagner": 2, "Scottie Barnes": 2, "Evan Mobley": 2, "Darius Garland": 2,
    "Zion Williamson": 2, "Brandon Ingram": 2, "LaMelo Ball": 2, "Cade Cunningham": 2, "Jalen Williams": 2,
    "Tyrese Maxey": 2, "Jamal Murray": 2, "Pascal Siakam": 2, "Lauri Markkanen": 2,
    "Victor Wembanyama": 2, "Alperen Sengun": 2, "Domantas Sabonis": 2,
    "Mikal Bridges": 1, "Anfernee Simons": 1, "Jalen Green": 1,
    "Zach LaVine": 1, "DeMar DeRozan": 1, "Kawhi Leonard": 1, "Paul George": 1, "Bradley Beal": 1,
    "Draymond Green": 1, "Karl-Anthony Towns": 1, "Rudy Gobert": 1, "Jordan Poole": 1
}

H2H_EDGES = {
    ("Boston", "Philadelphia"): 1.5, ("Boston", "New York"): 1.5, ("Milwaukee", "Chicago"): 1.5,
    ("Cleveland", "Detroit"): 1.5, ("Oklahoma City", "Utah"): 1.5, ("Denver", "Minnesota"): 1.5,
    ("LA Lakers", "LA Clippers"): 1.0, ("Golden State", "Sacramento"): 1.5, ("Phoenix", "Portland"): 1.5,
    ("Miami", "Orlando"): 1.5, ("Dallas", "San Antonio"): 1.5, ("Memphis", "New Orleans"): 1.0,
}

THRESHOLDS = [210.5, 215.5, 220.5, 225.5, 230.5, 235.5, 240.5, 245.5, 250.5, 255.5]

# ============================================================
# KALSHI API FUNCTIONS
# ============================================================
@st.cache_data(ttl=24)
def fetch_kalshi_prices():
    """Fetch current Kalshi NBA ML prices - REAL TIME (24s refresh)"""
    prices = {}
    today = datetime.now(eastern).strftime('%y%b%d').upper()
    
    try:
        # Kalshi trading API endpoint
        url = "https://trading-api.kalshi.com/trade-api/v2/markets"
        params = {"series_ticker": "KXNBA", "status": "open", "limit": 100}
        
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            markets = data.get("markets", [])
            
            for market in markets:
                ticker = market.get("ticker", "")
                # Format: KXNBA-25JAN26-BOS
                if today in ticker:
                    parts = ticker.split("-")
                    if len(parts) >= 3:
                        team_abbrev = parts[-1]
                        # Try different price fields
                        yes_price = market.get("yes_ask") or market.get("yes_bid") or market.get("last_price") or market.get("latest_yes_price")
                        no_price = market.get("no_ask") or market.get("no_bid")
                        
                        if yes_price:
                            # Convert to cents if needed
                            if yes_price <= 1:
                                yes_price = round(yes_price * 100)
                            if no_price and no_price <= 1:
                                no_price = round(no_price * 100)
                            
                            prices[team_abbrev] = {
                                "yes": int(yes_price),
                                "no": int(no_price) if no_price else None,
                                "ticker": ticker
                            }
    except Exception as e:
        # Silent fail - prices will show as unavailable
        pass
    
    return prices

@st.cache_data(ttl=300)
def fetch_vegas_odds():
    """Fetch Vegas odds from the-odds-api.com"""
    odds = {}
    
    # You can get a free API key at https://the-odds-api.com
    # Free tier: 500 requests/month
    API_KEY = os.environ.get("ODDS_API_KEY", "")
    
    if not API_KEY:
        return odds
    
    try:
        url = "https://api.the-odds-api.com/v4/sports/basketball_nba/odds/"
        params = {
            "apiKey": API_KEY,
            "regions": "us",
            "markets": "spreads,h2h",
            "oddsFormat": "american"
        }
        
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            for game in data:
                home = game.get("home_team", "")
                away = game.get("away_team", "")
                home_key = TEAM_ABBREVS.get(home, home)
                away_key = TEAM_ABBREVS.get(away, away)
                
                for bookmaker in game.get("bookmakers", []):
                    if bookmaker.get("key") in ["fanduel", "draftkings", "betmgm"]:
                        for market in bookmaker.get("markets", []):
                            if market.get("key") == "spreads":
                                for outcome in market.get("outcomes", []):
                                    team = TEAM_ABBREVS.get(outcome.get("name", ""), "")
                                    spread = outcome.get("point", 0)
                                    if team:
                                        odds[team] = {"spread": spread, "source": bookmaker.get("key")}
                        break
    except:
        pass
    
    return odds

def estimate_spread_from_stats(away, home):
    """Estimate spread from team stats when Vegas API unavailable"""
    home_stats = TEAM_STATS.get(home, {"net": 0})
    away_stats = TEAM_STATS.get(away, {"net": 0})
    
    # Home court = ~3 points
    # Net rating difference correlates to spread
    net_diff = home_stats.get("net", 0) - away_stats.get("net", 0)
    estimated_spread = round((net_diff * 0.5) + 3, 1)
    
    return estimated_spread

def spread_to_implied_prob(spread):
    """Convert point spread to implied win probability"""
    # Rough conversion: each point ≈ 2.5-3% win probability
    # Home team at -3 ≈ 62%, -5 ≈ 67%, -7 ≈ 72%, -10 ≈ 78%
    if spread <= -10:
        return 78
    elif spread <= -7:
        return 72 + ((-7 - spread) * 2)
    elif spread <= -5:
        return 67 + ((-5 - spread) * 2.5)
    elif spread <= -3:
        return 62 + ((-3 - spread) * 2.5)
    elif spread <= 0:
        return 50 + (abs(spread) * 4)
    elif spread <= 3:
        return 50 - (spread * 4)
    elif spread <= 5:
        return 38 - ((spread - 3) * 2.5)
    elif spread <= 7:
        return 33 - ((spread - 5) * 2.5)
    elif spread <= 10:
        return 28 - ((spread - 7) * 2)
    else:
        return 22

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
                "minutes_played": minutes_played,
                "total_score": home_score + away_score
            })
        return games
    except Exception as e:
        st.error(f"ESPN fetch error: {e}")
        return []

@st.cache_data(ttl=300)
def fetch_injuries():
    """Fetch injury data from ESPN"""
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
    
    home_out_names = []
    for inj in home_injuries:
        if isinstance(inj, dict):
            status = str(inj.get("status", "")).upper()
            if "OUT" in status or "DOUBT" in status:
                home_out_names.append(str(inj.get("name", "")).lower())
        else:
            home_out_names.append(str(inj).lower())
    
    away_out_names = []
    for inj in away_injuries:
        if isinstance(inj, dict):
            status = str(inj.get("status", "")).upper()
            if "OUT" in status or "DOUBT" in status:
                away_out_names.append(str(inj.get("name", "")).lower())
        else:
            away_out_names.append(str(inj).lower())
    
    for star in home_stars:
        if any(star.lower() in name for name in home_out_names):
            tier = STAR_TIERS.get(star, 1)
            pts = 5 if tier == 3 else 3 if tier == 2 else 1
            away_pts += pts
            factors_away.append(f"🏥 {star.split()[-1]} OUT +{pts}")
    
    for star in away_stars:
        if any(star.lower() in name for name in away_out_names):
            tier = STAR_TIERS.get(star, 1)
            pts = 5 if tier == 3 else 3 if tier == 2 else 1
            home_pts += pts
            factors_home.append(f"🏥 {star.split()[-1]} OUT +{pts}")
    
    # Net rating gap
    home_net = home_stats.get("net", 0)
    away_net = away_stats.get("net", 0)
    net_gap = home_net - away_net
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
    
    base = 50 + (net_gap * 1.5)
    base = max(25, min(75, base))
    
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
    
    pick, pregame_score, factors = calc_pregame_edge(away, home, injuries, b2b_teams)
    
    pace = round(total / minutes, 2) if minutes > 0 else 0
    pace_label = "🔥 FAST" if pace > 5.0 else "⚖️ AVG" if pace > 4.2 else "🐢 SLOW"
    
    live_adj = 0
    
    if abs(lead) >= 20:
        live_adj = 25 if lead > 0 else -25
    elif abs(lead) >= 15:
        live_adj = 18 if lead > 0 else -18
    elif abs(lead) >= 10:
        live_adj = 12 if lead > 0 else -12
    elif abs(lead) >= 5:
        live_adj = 6 if lead > 0 else -6
    
    if period == 4:
        if abs(lead) >= 10:
            live_adj += 15 if lead > 0 else -15
        elif abs(lead) >= 5:
            live_adj += 8 if lead > 0 else -8
    elif period == 3 and abs(lead) >= 15:
        live_adj += 8 if lead > 0 else -8
    
    if pace > 5.0 and abs(lead) >= 10:
        live_adj -= 4 if lead > 0 else 4
    elif pace < 4.2 and abs(lead) >= 10:
        live_adj += 3 if lead > 0 else -3
    
    final_score = pregame_score + live_adj if pick == home else (100 - pregame_score) + live_adj
    final_score = max(10, min(95, final_score))
    
    if lead > 0:
        live_pick = home
    elif lead < 0:
        live_pick = away
    else:
        live_pick = pick
    
    if minutes >= 6:
        proj_total = round((total / minutes) * 48)
    else:
        proj_total = 220
    
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
    abbrev = KALSHI_ABBREVS.get(team, "")
    today = datetime.now(eastern).strftime('%y%b%d').upper()
    return f"https://kalshi.com/markets/kxnba/nba-regular-season-games?ticker=KXNBA-{today}-{abbrev}"

def get_kalshi_totals_link(away, home):
    away_abbrev = KALSHI_ABBREVS.get(away, "")
    home_abbrev = KALSHI_ABBREVS.get(home, "")
    today = datetime.now(eastern).strftime('%y%b%d').upper()
    return f"https://kalshi.com/markets/kxnbao/nba-total-regular-season-game-points?ticker=KXNBAO-{today}-{away_abbrev}{home_abbrev}"

# ============================================================
# SIDEBAR LEGEND
# ============================================================
with st.sidebar:
    st.header("📖 EDGE GUIDE")
    st.markdown("""
### Price Gap Signals

| Gap | Signal | Action |
|-----|--------|--------|
| **+5¢+** | 🟢 STRONG | Buy now |
| **+3-4¢** | 🟢 VALUE | Good entry |
| **+1-2¢** | 🟡 THIN | Risky |
| **0 or -** | ⚪ NONE | Skip |

---

### Edge Score Guide

| Score | Label | Meaning |
|-------|-------|---------|
| **70+** | STRONG | Many factors aligned |
| **60-69** | GOOD | Worth watching |
| **50-59** | MODERATE | Mixed signals |
| **<50** | WEAK | Factors oppose |

---

### The Formula

**GAP = Vegas Implied % - Kalshi Price**

Vegas says 68% → Kalshi at 63¢  
GAP = +5¢ = 🟢 BUY

---

*We find the gap — you make the call.*
""")
    st.divider()
    st.caption("v5.0 NBA EDGE")

# ============================================================
# FETCH DATA
# ============================================================
games = fetch_games()
injuries = fetch_injuries()
b2b_teams = fetch_yesterday_teams()
kalshi_prices = fetch_kalshi_prices()
vegas_odds = fetch_vegas_odds()

# Get today's teams
today_teams = set()
for g in games:
    today_teams.add(g['away'])
    today_teams.add(g['home'])

# Separate games
live_games = [g for g in games if g['status'] == 'STATUS_IN_PROGRESS']
scheduled_games = [g for g in games if g['status'] == 'STATUS_SCHEDULED']
final_games = [g for g in games if g['status'] == 'STATUS_FINAL']

# ============================================================
# UI HEADER
# ============================================================
st.title("🏀 NBA EDGE FINDER")
st.caption(f"v5.0 • {now.strftime('%b %d, %Y %I:%M %p ET')} • ⚡ REAL-TIME: Scores + Kalshi every 24s")

# Stats row
c1, c2, c3, c4 = st.columns(4)
c1.metric("Today's Games", len(games))
c2.metric("Live Now", len(live_games))
c3.metric("B2B Teams", len(b2b_teams & today_teams))
kalshi_status = f"✅ {len(kalshi_prices)}" if kalshi_prices else "⚠️ 0"
c4.metric("Kalshi Prices", kalshi_status)

st.divider()

# ============================================================
# 💰 SPREAD EDGE - KALSHI vs VEGAS (PRE-GAME)
# ============================================================
st.markdown("""
<div style="background: linear-gradient(135deg, #1a472a 0%, #2d5a3d 100%); border-radius: 16px; padding: 20px; margin-bottom: 20px; border: 2px solid #22c55e;">
    <h2 style="color: #22c55e; margin: 0 0 8px 0;">💰 SPREAD EDGE — KALSHI vs VEGAS</h2>
    <p style="color: #aaa; margin: 0; font-size: 0.95em;">Find mispriced ML markets. GAP = Vegas Implied % minus Kalshi Price. Positive gap = BUY.</p>
</div>
""", unsafe_allow_html=True)

misprice_data = []

for g in scheduled_games:
    away, home = g['away'], g['home']
    
    # Get Kalshi prices
    home_abbrev = KALSHI_ABBREVS.get(home, "")
    away_abbrev = KALSHI_ABBREVS.get(away, "")
    
    home_kalshi = kalshi_prices.get(home_abbrev, {}).get("yes", None)
    away_kalshi = kalshi_prices.get(away_abbrev, {}).get("yes", None)
    
    # Get Vegas spread (or estimate)
    home_spread = vegas_odds.get(home, {}).get("spread", None)
    if home_spread is None:
        home_spread = -estimate_spread_from_stats(away, home)
        vegas_source = "EST"
    else:
        vegas_source = "VEGAS"
    
    # Calculate implied probabilities
    home_implied = spread_to_implied_prob(home_spread)
    away_implied = 100 - home_implied
    
    # Calculate gaps
    if home_kalshi:
        home_gap = home_implied - home_kalshi
    else:
        home_gap = None
    
    if away_kalshi:
        away_gap = away_implied - away_kalshi
    else:
        away_gap = None
    
    misprice_data.append({
        "away": away,
        "home": home,
        "home_spread": home_spread,
        "vegas_source": vegas_source,
        "home_implied": home_implied,
        "away_implied": away_implied,
        "home_kalshi": home_kalshi,
        "away_kalshi": away_kalshi,
        "home_gap": home_gap,
        "away_gap": away_gap
    })

# Sort by best gap opportunity
def best_gap(m):
    gaps = [g for g in [m['home_gap'], m['away_gap']] if g is not None]
    return max(gaps) if gaps else -999

misprice_data.sort(key=best_gap, reverse=True)

if misprice_data:
    for m in misprice_data:
        # Determine best pick
        home_gap = m['home_gap'] or 0
        away_gap = m['away_gap'] or 0
        
        if home_gap >= away_gap and home_gap > 0:
            best_pick = m['home']
            best_gap_val = home_gap
            best_kalshi = m['home_kalshi']
            best_implied = m['home_implied']
        elif away_gap > home_gap and away_gap > 0:
            best_pick = m['away']
            best_gap_val = away_gap
            best_kalshi = m['away_kalshi']
            best_implied = m['away_implied']
        else:
            best_pick = None
            best_gap_val = max(home_gap, away_gap)
            best_kalshi = None
            best_implied = None
        
        # Signal and color
        if best_gap_val >= 5:
            signal = "🟢 STRONG"
            border_color = "#22c55e"
        elif best_gap_val >= 3:
            signal = "🟢 VALUE"
            border_color = "#22c55e"
        elif best_gap_val >= 1:
            signal = "🟡 THIN"
            border_color = "#eab308"
        else:
            signal = "⚪ NO EDGE"
            border_color = "#444"
        
        # Format spread display
        spread_display = f"{m['home']} {m['home_spread']:+.1f}" if m['home_spread'] <= 0 else f"{m['away']} {-m['home_spread']:+.1f}"
        
        # Build display
        home_price_display = f"{m['home_kalshi']}¢" if m['home_kalshi'] else "—"
        away_price_display = f"{m['away_kalshi']}¢" if m['away_kalshi'] else "—"
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1e1e2e 0%, #2a2a3e 100%); border-radius: 12px; padding: 16px; margin-bottom: 12px; border-left: 4px solid {border_color};">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <span style="color: #fff; font-size: 1.1em; font-weight: 600;">{m['away']} @ {m['home']}</span>
                <span style="color: {border_color}; font-weight: 600;">{signal}</span>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 10px; margin-bottom: 10px;">
                <div style="text-align: center;">
                    <div style="color: #888; font-size: 0.75em;">SPREAD</div>
                    <div style="color: #fff; font-weight: 600;">{spread_display}</div>
                    <div style="color: #666; font-size: 0.7em;">{m['vegas_source']}</div>
                </div>
                <div style="text-align: center;">
                    <div style="color: #888; font-size: 0.75em;">IMPLIED</div>
                    <div style="color: #fff;">{m['home'][:3]} {m['home_implied']}%</div>
                    <div style="color: #aaa;">{m['away'][:3]} {m['away_implied']}%</div>
                </div>
                <div style="text-align: center;">
                    <div style="color: #888; font-size: 0.75em;">KALSHI</div>
                    <div style="color: #fff;">{m['home'][:3]} {home_price_display}</div>
                    <div style="color: #aaa;">{m['away'][:3]} {away_price_display}</div>
                </div>
                <div style="text-align: center;">
                    <div style="color: #888; font-size: 0.75em;">GAP</div>
                    <div style="color: {'#22c55e' if (m['home_gap'] or 0) > 0 else '#888'};">{m['home'][:3]} {'+' + str(m['home_gap']) + '¢' if m['home_gap'] and m['home_gap'] > 0 else '—'}</div>
                    <div style="color: {'#22c55e' if (m['away_gap'] or 0) > 0 else '#888'};">{m['away'][:3]} {'+' + str(m['away_gap']) + '¢' if m['away_gap'] and m['away_gap'] > 0 else '—'}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if best_pick and best_gap_val >= 3:
            st.link_button(f"🎯 BUY {best_pick} YES @ {best_kalshi}¢", get_kalshi_ml_link(best_pick), use_container_width=True)
        
        st.markdown("")

else:
    st.info("No scheduled games found")

# Big visual separator
st.markdown("""
<div style="background: linear-gradient(90deg, #22c55e, transparent, #22c55e); height: 3px; margin: 30px 0;"></div>
<div style="text-align: center; margin-bottom: 20px;">
    <span style="background: #0e1117; padding: 0 20px; color: #666; font-size: 0.9em;">⬇️ LIVE GAME TOOLS BELOW ⬇️</span>
</div>
""", unsafe_allow_html=True)

st.divider()

# ============================================================
# 🏥 INJURY REPORT
# ============================================================
st.markdown("""
<div style="background: linear-gradient(135deg, #3a1a3a 0%, #4a2a4a 100%); border-radius: 12px; padding: 16px; margin-bottom: 16px; border-left: 4px solid #a855f7;">
    <h3 style="color: #a855f7; margin: 0 0 4px 0;">🏥 INJURY REPORT</h3>
    <p style="color: #888; margin: 0; font-size: 0.85em;">Star players OUT = edge for opponent. ⭐⭐⭐ MVP +5 | ⭐⭐ All-Star +3 | ⭐ Starter +1</p>
</div>
""", unsafe_allow_html=True)

injured_stars = []
for team, team_injuries in injuries.items():
    if team not in today_teams:
        continue
    for inj in team_injuries:
        if isinstance(inj, dict):
            name = inj.get("name", "")
            status = str(inj.get("status", "")).upper()
        else:
            name = str(inj)
            status = "OUT"
        
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

b2b_today = b2b_teams & today_teams
if b2b_today:
    b2b_list = ", ".join(sorted(b2b_today))
    st.markdown(f"""<div style="background:#1a2a3a;padding:10px 14px;border-radius:6px;margin-top:10px">
        <span style="color:#38bdf8">🏨 B2B Teams:</span> <span style="color:#fff">{b2b_list}</span>
    </div>""", unsafe_allow_html=True)

if not injured_stars and not b2b_today:
    st.info("No major star injuries or B2B teams for today's games")

st.divider()

# ============================================================
# 🔴 LIVE EDGE MONITOR
# ============================================================
if live_games:
    st.markdown("""
    <div style="background: linear-gradient(135deg, #4a1a1a 0%, #6a2a2a 100%); border-radius: 16px; padding: 20px; margin-bottom: 20px; border: 2px solid #ff4444;">
        <h2 style="color: #ff4444; margin: 0 0 8px 0;">🔴 LIVE EDGE MONITOR</h2>
        <p style="color: #aaa; margin: 0; font-size: 0.95em;">Real-time updates every 24 seconds. Track leads, pace, and projected totals.</p>
    </div>
    """, unsafe_allow_html=True)
    
    live_with_edge = []
    for g in live_games:
        edge = calc_live_edge(g, injuries, b2b_teams)
        live_with_edge.append((g, edge))
    live_with_edge.sort(key=lambda x: x[1]['score'], reverse=True)
    
    for g, edge in live_with_edge:
        mins = g['minutes_played']
        
        if mins < 6:
            status_label = "⏳ TOO EARLY"
            status_color = "#888"
        elif abs(edge['lead']) < 5:
            status_label = "⚖️ TOO CLOSE"
            status_color = "#ffa500"
        elif edge['score'] >= 70:
            status_label = f"🟢 STRONG {edge['score']}/100"
            status_color = "#22c55e"
        elif edge['score'] >= 60:
            status_label = f"🟢 GOOD {edge['score']}/100"
            status_color = "#22c55e"
        else:
            status_label = f"🟡 {edge['score']}/100"
            status_color = "#eab308"
        
        lead_display = f"+{edge['lead']}" if edge['lead'] > 0 else str(edge['lead'])
        leader = g['home'] if edge['lead'] > 0 else g['away'] if edge['lead'] < 0 else "TIED"
        
        safe_no = edge['proj_total'] + 12
        safe_yes = edge['proj_total'] - 8
        
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
            <div style="background: #333; border-radius: 8px; padding: 10px;">
                <span style="color: #888;">Proj: {edge['proj_total']}</span> | 
                <span style="color: #22c55e;">NO {safe_no}</span> | 
                <span style="color: #f97316;">YES {safe_yes}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        bc1, bc2, bc3 = st.columns(3)
        with bc1:
            st.link_button(f"🎯 {edge['pick']} ML", get_kalshi_ml_link(edge['pick']), use_container_width=True)
        with bc2:
            st.link_button(f"⬇️ NO {safe_no}", get_kalshi_totals_link(g['away'], g['home']), use_container_width=True)
        with bc3:
            st.link_button(f"⬆️ YES {safe_yes}", get_kalshi_totals_link(g['away'], g['home']), use_container_width=True)
        
        st.markdown("---")
else:
    st.markdown("""
    <div style="background: linear-gradient(135deg, #4a1a1a 0%, #6a2a2a 100%); border-radius: 16px; padding: 20px; margin-bottom: 20px; border: 2px solid #ff4444;">
        <h2 style="color: #ff4444; margin: 0 0 8px 0;">🔴 LIVE EDGE MONITOR</h2>
        <p style="color: #aaa; margin: 0; font-size: 0.95em;">Real-time updates every 24 seconds. Track leads, pace, and projected totals.</p>
    </div>
    """, unsafe_allow_html=True)
    st.info("🕐 No live games right now. Check back when games tip off.")

st.divider()

# ============================================================
# 🎯 CUSHION SCANNER
# ============================================================
st.markdown("""
<div style="background: linear-gradient(135deg, #1a2a4a 0%, #2a3a5a 100%); border-radius: 12px; padding: 16px; margin-bottom: 16px; border-left: 4px solid #3b82f6;">
    <h3 style="color: #3b82f6; margin: 0 0 4px 0;">🎯 CUSHION SCANNER</h3>
    <p style="color: #888; margin: 0; font-size: 0.85em;">Find safe NO/YES totals with 6+ point buffer in live games</p>
</div>
""", unsafe_allow_html=True)

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
        'away': g['away'], 'home': g['home'],
        'total': total, 'mins': mins, 'pace': pace,
        'pace_status': pace_status, 'pace_color': pace_color,
        'projected': projected_final, 'cushion': cushion,
        'safe_line': safe_line, 'period': g['period'], 'clock': g['clock']
    })

cush_results.sort(key=lambda x: x['cushion'], reverse=True)

if cush_results:
    for r in cush_results:
        st.markdown(f"""<div style="background:#0f172a;padding:10px 14px;margin-bottom:6px;border-radius:8px;border-left:3px solid {r['pace_color']}">
        <b style="color:#fff">{r['away']} @ {r['home']}</b> 
        <span style="color:#888">Q{r['period']} {r['clock']} • {r['total']}pts/{r['mins']:.0f}min</span>
        <span style="color:#888">Proj: <b style="color:#fff">{r['projected']}</b></span>
        <span style="background:#ff8800;color:#000;padding:2px 8px;border-radius:4px;font-weight:bold;margin-left:8px">🎯 {r['safe_line']}</span>
        <span style="color:#00ff00;font-weight:bold;margin-left:8px">+{r['cushion']:.0f}</span>
        <span style="color:{r['pace_color']};margin-left:8px">{r['pace_status']}</span>
        </div>""", unsafe_allow_html=True)
        st.link_button(f"BUY {cush_side} {r['safe_line']}", get_kalshi_totals_link(r['away'], r['home']), use_container_width=True)
else:
    st.info(f"No {cush_side} opportunities with 6+ cushion yet")

st.divider()

# ============================================================
# 🔥 PACE SCANNER
# ============================================================
st.markdown("""
<div style="background: linear-gradient(135deg, #4a2a1a 0%, #5a3a2a 100%); border-radius: 12px; padding: 16px; margin-bottom: 16px; border-left: 4px solid #f97316;">
    <h3 style="color: #f97316; margin: 0 0 4px 0;">🔥 PACE SCANNER</h3>
    <p style="color: #888; margin: 0; font-size: 0.85em;">Track scoring pace — SLOW favors NO, FAST favors YES</p>
</div>
""", unsafe_allow_html=True)

pace_data = []
for g in live_games:
    mins = g['minutes_played']
    if mins >= 6:
        pace = round(g['total_score'] / mins, 2)
        pace_data.append({
            "away": g['away'], "home": g['home'],
            "pace": pace, "proj": round(pace * 48), 
            "total": g['total_score'], "mins": mins, 
            "period": g['period'], "clock": g['clock']
        })

pace_data.sort(key=lambda x: x['pace'])

if pace_data:
    for p in pace_data:
        if p['pace'] < 4.5:
            lbl, clr = "🐢 SLOW", "#00ff00"
            rec_side, rec_line = "NO", THRESHOLDS[min(next((i for i, t in enumerate(THRESHOLDS) if t > p['proj']), len(THRESHOLDS)-1) + 2, len(THRESHOLDS)-1)]
        elif p['pace'] < 4.8:
            lbl, clr = "⚖️ AVG", "#ffff00"
            rec_side, rec_line = None, None
        elif p['pace'] < 5.2:
            lbl, clr = "🔥 FAST", "#ff8800"
            rec_side, rec_line = "YES", THRESHOLDS[max(next((i for i in range(len(THRESHOLDS)-1, -1, -1) if THRESHOLDS[i] < p['proj']), 0) - 2, 0)]
        else:
            lbl, clr = "🚀 SHOOTOUT", "#ff0000"
            rec_side, rec_line = "YES", THRESHOLDS[max(next((i for i in range(len(THRESHOLDS)-1, -1, -1) if THRESHOLDS[i] < p['proj']), 0) - 2, 0)]
        
        st.markdown(f"""<div style="background:#0f172a;padding:8px 12px;margin-bottom:4px;border-radius:6px;border-left:3px solid {clr}">
        <b style="color:#fff">{p['away']} @ {p['home']}</b>
        <span style="color:#666;margin-left:10px">Q{p['period']} {p['clock']}</span>
        <span style="color:#888;margin-left:10px">{p['total']}pts/{p['mins']:.0f}min</span>
        <span style="color:{clr};font-weight:bold;margin-left:10px">{p['pace']}/min {lbl}</span>
        <span style="color:#888;margin-left:10px">Proj: <b style="color:#fff">{p['proj']}</b></span>
        </div>""", unsafe_allow_html=True)
        
        if rec_side and rec_line:
            st.link_button(f"BUY {rec_side} {rec_line}", get_kalshi_totals_link(p['away'], p['home']), use_container_width=True)
else:
    st.info("No games with 6+ minutes played yet")

st.divider()

# ============================================================
# 📖 HOW TO USE
# ============================================================
with st.expander("📖 HOW TO USE THIS APP", expanded=False):
    st.markdown("""
## 💰 MISPRICE SCANNER (Pre-Game)

**The Core Formula:**
```
GAP = Vegas Implied % - Kalshi Price
```

Vegas says team has 68% chance → Kalshi selling at 63¢ → GAP = +5¢ = BUY

| Gap | Signal | Action |
|-----|--------|--------|
| **+5¢+** | 🟢 STRONG | Best edge — buy now |
| **+3-4¢** | 🟢 VALUE | Good entry — worth it |
| **+1-2¢** | 🟡 THIN | Small edge — risky |
| **0 or -** | ⚪ NONE | No edge — skip |

**Why This Works:**
- Vegas lines set by sharps betting real money
- Kalshi prices set by recreational traders
- Injuries + news create LAG = your edge
- Buy the gap, sell +3¢ for profit

---

## 🔴 LIVE EDGE MONITOR (In-Game)

Real-time tracking every 24 seconds. Shows:
- Current score and lead
- Pace (points per minute)
- Projected total
- Safe NO/YES thresholds

| Score | Label | Meaning |
|-------|-------|---------|
| **70+** | STRONG | Many factors aligned |
| **60-69** | GOOD | Worth considering |
| **50-59** | MODERATE | Mixed signals |
| **<50** | WEAK | Skip |

**Live Timing:**
- Q1: ❌ Too early — don't enter
- Q2 with 10+ lead: 🟡 Medium — watch pace
- Q3 with 12+ lead: 🟢 Good — sweet spot
- Q4 with 15+ lead: 🟢🟢 High — price may be high

---

## 🎯 CUSHION SCANNER (In-Game Totals)

Finds safe over/under thresholds with buffer room.

**Cushion = Safe Line - Projected Total**

| Cushion | Safety |
|---------|--------|
| **+10+** | Very safe |
| **+6-9** | Safe |
| **<+6** | Not shown (risky) |

**Pace Alignment for NO bets:**
- 🐢 SLOW (<4.5/min) = ✅ Good for NO
- ⚖️ AVG (4.5-4.8) = ⚠️ Wait
- 🔥 FAST (>4.8) = ❌ Bad for NO

**Pace Alignment for YES bets:**
- 🚀 SHOOTOUT (>5.2) = ✅ Best for YES
- 🔥 FAST (4.8-5.2) = ✅ Good for YES
- ⚖️ AVG (4.5-4.8) = ⚠️ Wait
- 🐢 SLOW (<4.5) = ❌ Bad for YES

---

## 🔥 PACE SCANNER (In-Game Totals)

Shows real-time scoring pace for all live games.

**Pace = Total Points ÷ Minutes Played**

| Pace | Label | Projected | Action |
|------|-------|-----------|--------|
| <4.5 | 🐢 SLOW | ~216 | Buy NO |
| 4.5-4.8 | ⚖️ AVG | ~220-230 | Wait |
| 4.8-5.2 | 🔥 FAST | ~230-250 | Buy YES |
| >5.2 | 🚀 SHOOTOUT | ~250+ | Buy YES |

---

## 🏥 INJURY IMPACT

Star players missing = edge for opponent

| Tier | Examples | Impact |
|------|----------|--------|
| ⭐⭐⭐ MVP | Jokic, SGA, Giannis | +5 to opponent |
| ⭐⭐ All-Star | AD, Brunson, Haliburton | +3 to opponent |
| ⭐ Starter | Role players | +1 to opponent |

---

## 🏨 B2B (Back-to-Back)

Teams playing second night of back-to-back = fatigued

- B2B team gets -4 adjustment
- Opponent gets +4 boost
- Check B2B section for today's tired teams

---

## ⚡ REAL-TIME DATA

| Data | Refresh Rate |
|------|--------------|
| Game scores | 24 seconds |
| Kalshi prices | 24 seconds |
| Vegas odds | 5 minutes |
| Injuries | 5 minutes |

---

## 🎯 THE WORKFLOW

**Pre-Game:**
1. Check Misprice Scanner for +3¢+ gaps
2. Check Injury Report for star absences
3. Note B2B teams
4. Buy mispriced favorites

**In-Game:**
1. Wait for 6+ minutes played
2. Check Pace Scanner for slow/fast games
3. Use Cushion Scanner for safe totals
4. Live Edge Monitor for ML opportunities

**The Scalp:**
- Buy at gap price
- Sell at +3¢ profit
- Repeat

---

⚠️ **DISCLAIMER**

This tool shows edges — you make the call.

- Edge Score ≠ Win Probability
- This is NOT a predictive model
- Past performance ≠ future results
- Only risk what you can afford to lose
- Educational purposes only
- Not financial advice
""")

st.caption("⚠️ Educational only. Not financial advice. v5.0")
