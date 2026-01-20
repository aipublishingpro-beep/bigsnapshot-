import streamlit as st
import requests
from datetime import datetime, timedelta
import pytz
import math

st.set_page_config(page_title="NBA Edge Finder", page_icon="🎯", layout="wide")

# ========== HIDE MENUS ==========
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.stDeployButton {display: none;}
[data-testid="stToolbar"] {display: none;}
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

# ========== GA4 ==========
st.markdown("""
<script async src="https://www.googletagmanager.com/gtag/js?id=G-NQKY5VQ376"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());gtag('config','G-NQKY5VQ376');</script>
""", unsafe_allow_html=True)

# ========== SIDEBAR LEGENDS ==========
with st.sidebar:
    st.header("🎯 ML Signal Legend")
    st.markdown("""
    🟢 **STRONG BUY** → 8.0+
    
    🔵 **BUY** → 6.5-7.9
    
    🟡 **LEAN** → 5.5-6.4
    
    ⚪ **WEAK / NO EDGE** → Below 5.5
    """)
    
    st.divider()
    
    st.header("📊 Market Pressure")
    st.markdown("""
    🟢 **CONFIRMING** → Market agrees
    
    🟡 **NEUTRAL** → No clear flow
    
    🔴 **FADING** → Market disagrees
    """)
    
    st.divider()
    
    st.header("🔥 Pace Legend")
    st.markdown("""
    🟢 **SLOW** → Under 4.5 pts/min
    
    🟡 **AVG** → 4.5-4.8 pts/min
    
    🟠 **FAST** → 4.8-5.2 pts/min
    
    🔴 **SHOOTOUT** → Over 5.2 pts/min
    """)
    
    st.divider()
    
    st.header("🎯 Cushion Guide")
    st.markdown("""
    **+15** → 🟢 Safe cushion
    
    **+10-14** → 🔵 Good cushion
    
    **+6-9** → 🟡 Thin cushion
    
    **<6** → 🔴 No edge
    """)
    
    st.divider()
    st.caption("v16.0 | 8-Factor ML + Market Pressure")

# ========== SESSION STATE ==========
if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = False
if 'positions' not in st.session_state:
    st.session_state.positions = []

if st.session_state.auto_refresh:
    st.markdown('<meta http-equiv="refresh" content="30">', unsafe_allow_html=True)
    auto_status = "🔄 Auto ON"
else:
    auto_status = "⏸️ Auto OFF"

# ========== TIMEZONE ==========
eastern = pytz.timezone('US/Eastern')
now = datetime.now(eastern)
today_str = now.strftime("%Y-%m-%d")

# ========== TEAM MAPPINGS ==========
TEAM_ABBREVS = {
    "Atlanta Hawks": "Atlanta", "Boston Celtics": "Boston", "Brooklyn Nets": "Brooklyn",
    "Charlotte Hornets": "Charlotte", "Chicago Bulls": "Chicago", "Cleveland Cavaliers": "Cleveland",
    "Dallas Mavericks": "Dallas", "Denver Nuggets": "Denver", "Detroit Pistons": "Detroit",
    "Golden State Warriors": "Golden State", "Houston Rockets": "Houston", "Indiana Pacers": "Indiana",
    "LA Clippers": "LA Clippers", "Los Angeles Clippers": "LA Clippers",
    "LA Lakers": "LA Lakers", "Los Angeles Lakers": "LA Lakers",
    "Memphis Grizzlies": "Memphis", "Miami Heat": "Miami", "Milwaukee Bucks": "Milwaukee",
    "Minnesota Timberwolves": "Minnesota", "New Orleans Pelicans": "New Orleans",
    "New York Knicks": "New York", "Oklahoma City Thunder": "Oklahoma City",
    "Orlando Magic": "Orlando", "Philadelphia 76ers": "Philadelphia", "Phoenix Suns": "Phoenix",
    "Portland Trail Blazers": "Portland", "Sacramento Kings": "Sacramento",
    "San Antonio Spurs": "San Antonio", "Toronto Raptors": "Toronto",
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

# ========== TEAM STATS (8-FACTOR ML DATA - WEIGHTS HIDDEN) ==========
TEAM_STATS = {
    "Atlanta": {"net_rtg": -3.2, "def_rank": 26, "home_win_pct": 0.52, "lat": 33.757, "lon": -84.396},
    "Boston": {"net_rtg": 9.8, "def_rank": 4, "home_win_pct": 0.76, "lat": 42.366, "lon": -71.062},
    "Brooklyn": {"net_rtg": -7.5, "def_rank": 22, "home_win_pct": 0.45, "lat": 40.683, "lon": -73.975},
    "Charlotte": {"net_rtg": -8.1, "def_rank": 23, "home_win_pct": 0.38, "lat": 35.225, "lon": -80.839},
    "Chicago": {"net_rtg": -4.2, "def_rank": 24, "home_win_pct": 0.48, "lat": 41.881, "lon": -87.674},
    "Cleveland": {"net_rtg": 7.2, "def_rank": 3, "home_win_pct": 0.78, "lat": 41.496, "lon": -81.688},
    "Dallas": {"net_rtg": -1.5, "def_rank": 18, "home_win_pct": 0.55, "lat": 32.790, "lon": -96.810},
    "Denver": {"net_rtg": 3.8, "def_rank": 12, "home_win_pct": 0.68, "lat": 39.749, "lon": -104.999},
    "Detroit": {"net_rtg": -5.8, "def_rank": 21, "home_win_pct": 0.42, "lat": 42.341, "lon": -83.055},
    "Golden State": {"net_rtg": 2.1, "def_rank": 10, "home_win_pct": 0.62, "lat": 37.768, "lon": -122.388},
    "Houston": {"net_rtg": 4.5, "def_rank": 8, "home_win_pct": 0.65, "lat": 29.751, "lon": -95.362},
    "Indiana": {"net_rtg": 1.2, "def_rank": 25, "home_win_pct": 0.58, "lat": 39.764, "lon": -86.156},
    "LA Clippers": {"net_rtg": -0.8, "def_rank": 14, "home_win_pct": 0.52, "lat": 34.043, "lon": -118.267},
    "LA Lakers": {"net_rtg": 1.5, "def_rank": 15, "home_win_pct": 0.60, "lat": 34.043, "lon": -118.267},
    "Memphis": {"net_rtg": 4.2, "def_rank": 9, "home_win_pct": 0.66, "lat": 35.138, "lon": -90.051},
    "Miami": {"net_rtg": 0.5, "def_rank": 11, "home_win_pct": 0.58, "lat": 25.781, "lon": -80.188},
    "Milwaukee": {"net_rtg": 2.8, "def_rank": 13, "home_win_pct": 0.62, "lat": 43.045, "lon": -87.917},
    "Minnesota": {"net_rtg": 3.5, "def_rank": 5, "home_win_pct": 0.64, "lat": 44.980, "lon": -93.276},
    "New Orleans": {"net_rtg": -9.2, "def_rank": 27, "home_win_pct": 0.40, "lat": 29.949, "lon": -90.082},
    "New York": {"net_rtg": 6.5, "def_rank": 6, "home_win_pct": 0.72, "lat": 40.751, "lon": -73.994},
    "Oklahoma City": {"net_rtg": 11.2, "def_rank": 1, "home_win_pct": 0.82, "lat": 35.463, "lon": -97.515},
    "Orlando": {"net_rtg": 2.2, "def_rank": 2, "home_win_pct": 0.60, "lat": 28.539, "lon": -81.384},
    "Philadelphia": {"net_rtg": -2.5, "def_rank": 16, "home_win_pct": 0.50, "lat": 39.901, "lon": -75.172},
    "Phoenix": {"net_rtg": 0.8, "def_rank": 17, "home_win_pct": 0.55, "lat": 33.446, "lon": -112.071},
    "Portland": {"net_rtg": -7.8, "def_rank": 28, "home_win_pct": 0.38, "lat": 45.532, "lon": -122.667},
    "Sacramento": {"net_rtg": -1.2, "def_rank": 20, "home_win_pct": 0.52, "lat": 38.580, "lon": -121.500},
    "San Antonio": {"net_rtg": -5.5, "def_rank": 19, "home_win_pct": 0.55, "lat": 29.427, "lon": -98.438},
    "Toronto": {"net_rtg": -6.5, "def_rank": 29, "home_win_pct": 0.42, "lat": 43.643, "lon": -79.379},
    "Utah": {"net_rtg": -5.2, "def_rank": 30, "home_win_pct": 0.35, "lat": 40.768, "lon": -111.901},
    "Washington": {"net_rtg": -10.5, "def_rank": 31, "home_win_pct": 0.28, "lat": 38.898, "lon": -77.021}
}

STAR_PLAYERS = {
    "Atlanta": ["Trae Young", "Jalen Johnson"], "Boston": ["Jayson Tatum", "Jaylen Brown"],
    "Brooklyn": ["Cam Thomas"], "Charlotte": ["LaMelo Ball", "Brandon Miller"],
    "Chicago": ["Zach LaVine", "Coby White"], "Cleveland": ["Donovan Mitchell", "Darius Garland", "Evan Mobley"],
    "Dallas": ["Luka Doncic", "Kyrie Irving"], "Denver": ["Nikola Jokic", "Jamal Murray"],
    "Detroit": ["Cade Cunningham", "Jaden Ivey"], "Golden State": ["Stephen Curry", "Draymond Green"],
    "Houston": ["Jalen Green", "Alperen Sengun"], "Indiana": ["Tyrese Haliburton", "Pascal Siakam"],
    "LA Clippers": ["James Harden", "Kawhi Leonard"], "LA Lakers": ["LeBron James", "Anthony Davis"],
    "Memphis": ["Ja Morant", "Jaren Jackson Jr."], "Miami": ["Jimmy Butler", "Bam Adebayo"],
    "Milwaukee": ["Giannis Antetokounmpo", "Damian Lillard"], "Minnesota": ["Anthony Edwards", "Rudy Gobert"],
    "New Orleans": ["Zion Williamson", "Brandon Ingram"], "New York": ["Jalen Brunson", "Karl-Anthony Towns"],
    "Oklahoma City": ["Shai Gilgeous-Alexander", "Chet Holmgren"], "Orlando": ["Paolo Banchero", "Franz Wagner"],
    "Philadelphia": ["Joel Embiid", "Tyrese Maxey"], "Phoenix": ["Kevin Durant", "Devin Booker"],
    "Portland": ["Anfernee Simons", "Scoot Henderson"], "Sacramento": ["De'Aaron Fox", "Domantas Sabonis"],
    "San Antonio": ["Victor Wembanyama", "Devin Vassell"], "Toronto": ["Scottie Barnes", "RJ Barrett"],
    "Utah": ["Lauri Markkanen", "Keyonte George"], "Washington": ["Jordan Poole", "Kyle Kuzma"]
}

# ========== HELPER FUNCTIONS ==========
def get_minutes_played(period, clock, status_type):
    if status_type == "STATUS_FINAL":
        return 48
    if status_type == "STATUS_HALFTIME":
        return 24
    if period == 0:
        return 0
    try:
        if ':' in str(clock):
            parts = str(clock).split(':')
            mins_left = int(parts[0])
            secs_left = int(float(parts[1])) if len(parts) > 1 else 0
        else:
            mins_left = 0
            secs_left = float(clock) if clock else 0
        time_left_in_period = mins_left + secs_left / 60
        if period <= 4:
            return (period - 1) * 12 + (12 - time_left_in_period)
        else:
            return 48 + (period - 5) * 5 + (5 - time_left_in_period)
    except:
        return (period - 1) * 12 if period <= 4 else 48

def calc_distance_miles(lat1, lon1, lat2, lon2):
    R = 3959
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

# ========== KALSHI MARKET FUNCTIONS ==========
@st.cache_data(ttl=120)
def fetch_kalshi_market(ticker):
    try:
        url = f"https://api.elections.kalshi.com/trade-api/v2/markets/{ticker.upper()}"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            market = data.get("market", {})
            if market:
                return {
                    "yes_price": market.get("yes_bid", 0),
                    "no_price": market.get("no_bid", 0),
                    "last_price": market.get("last_price", 0),
                    "volume": market.get("volume", 0),
                    "open_interest": market.get("open_interest", 0),
                    "exists": True
                }
        return {"exists": False}
    except:
        return {"exists": False}

@st.cache_data(ttl=300)
def fetch_kalshi_history(ticker):
    try:
        url = f"https://api.elections.kalshi.com/trade-api/v2/markets/{ticker.upper()}/history"
        params = {"limit": 50}
        resp = requests.get(url, params=params, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("history", [])
        return []
    except:
        return []

def calc_market_pressure(ticker, pick_team, home_team):
    market = fetch_kalshi_market(ticker)
    if not market.get("exists"):
        return None, "NO DATA", "#888888"
    
    history = fetch_kalshi_history(ticker)
    if len(history) < 2:
        return market, "NEUTRAL", "#ffaa00"
    
    recent_prices = [h.get("yes_price", 50) for h in history[:10]]
    older_prices = [h.get("yes_price", 50) for h in history[10:20]] if len(history) > 10 else recent_prices
    
    avg_recent = sum(recent_prices) / len(recent_prices) if recent_prices else 50
    avg_older = sum(older_prices) / len(older_prices) if older_prices else 50
    
    price_move = avg_recent - avg_older
    
    pick_is_home = pick_team == home_team
    
    if pick_is_home:
        if price_move > 3:
            return market, "CONFIRMING", "#00ff00"
        elif price_move < -3:
            return market, "FADING", "#ff4444"
        else:
            return market, "NEUTRAL", "#ffaa00"
    else:
        if price_move < -3:
            return market, "CONFIRMING", "#00ff00"
        elif price_move > 3:
            return market, "FADING", "#ff4444"
        else:
            return market, "NEUTRAL", "#ffaa00"

# ========== FETCH ESPN GAMES ==========
@st.cache_data(ttl=60)
def fetch_espn_scores(date_key=None):
    games = {}
    try:
        url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        for event in data.get("events", []):
            comp = event.get("competitions", [{}])[0]
            competitors = comp.get("competitors", [])
            if len(competitors) < 2:
                continue
            home_team, away_team, home_score, away_score = None, None, 0, 0
            for c in competitors:
                full_name = c.get("team", {}).get("displayName", "")
                team_name = TEAM_ABBREVS.get(full_name, full_name)
                score = int(c.get("score", 0) or 0)
                if c.get("homeAway") == "home":
                    home_team, home_score = team_name, score
                else:
                    away_team, away_score = team_name, score
            if not home_team or not away_team:
                continue
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
    except Exception as e:
        st.error(f"Error fetching games: {e}")
    return games

@st.cache_data(ttl=3600)
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
                full_name = c.get("team", {}).get("displayName", "")
                team_name = TEAM_ABBREVS.get(full_name, full_name)
                teams.add(team_name)
        return teams
    except:
        return set()

@st.cache_data(ttl=300)
def fetch_espn_injuries():
    injuries = {}
    try:
        url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/injuries"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        for team_data in data.get("injuries", []):
            team_name = team_data.get("displayName", "")
            if not team_name:
                team_name = team_data.get("team", {}).get("displayName", "")
            team_key = TEAM_ABBREVS.get(team_name, team_name)
            if not team_key:
                continue
            injuries[team_key] = []
            for player in team_data.get("injuries", []):
                name = player.get("athlete", {}).get("displayName", "")
                if not name:
                    name = player.get("displayName", "")
                status = player.get("status", "")
                if not status:
                    status = player.get("type", {}).get("description", "")
                if name:
                    injuries[team_key].append({"name": name, "status": status})
    except:
        pass
    return injuries

# ========== 8-FACTOR ML SCORING (WEIGHTS HIDDEN) ==========
def calc_ml_score(away_team, home_team, injuries, yesterday_teams):
    away_stats = TEAM_STATS.get(away_team, {})
    home_stats = TEAM_STATS.get(home_team, {})
    
    if not away_stats or not home_stats:
        return None, 0, []
    
    score_home = 0.0
    score_away = 0.0
    factors = []
    
    away_b2b = away_team in yesterday_teams
    home_b2b = home_team in yesterday_teams
    
    if away_b2b and not home_b2b:
        score_home += 1.0
        factors.append(("🛏️", "Rest Edge"))
    elif home_b2b and not away_b2b:
        score_away += 1.0
        factors.append(("🛏️", "Rest Edge"))
    
    net_diff = home_stats.get("net_rtg", 0) - away_stats.get("net_rtg", 0)
    if net_diff > 5:
        score_home += 1.0
        factors.append(("📊", "Net Rating"))
    elif net_diff < -5:
        score_away += 1.0
        factors.append(("📊", "Net Rating"))
    
    home_def_rank = home_stats.get("def_rank", 15)
    away_def_rank = away_stats.get("def_rank", 15)
    if home_def_rank <= 5:
        score_home += 1.0
        factors.append(("🛡️", "Elite Defense"))
    if away_def_rank <= 5:
        score_away += 1.0
        factors.append(("🛡️", "Elite Defense"))
    
    score_home += 1.0
    factors.append(("🏠", "Home Court"))
    
    def calc_injury_score(team, team_injuries):
        stars = STAR_PLAYERS.get(team, [])
        total = 0.0
        star_out = None
        for inj in team_injuries:
            name = inj.get("name", "").lower()
            status = inj.get("status", "").lower()
            is_star = any(s.lower() in name for s in stars)
            if "out" in status:
                total += 4.0 if is_star else 1.0
                if is_star and not star_out:
                    star_out = inj.get("name", "")
            elif "gtd" in status or "questionable" in status or "doubtful" in status:
                total += 2.5 if is_star else 0.5
        return total, star_out
    
    away_inj_score, away_star_out = calc_injury_score(away_team, injuries.get(away_team, []))
    home_inj_score, home_star_out = calc_injury_score(home_team, injuries.get(home_team, []))
    inj_diff = away_inj_score - home_inj_score
    
    if inj_diff > 3:
        score_home += 1.0
        if away_star_out:
            factors.append(("🏥", f"{away_star_out.split()[-1]} OUT"))
        else:
            factors.append(("🏥", "Injury Edge"))
    elif inj_diff < -3:
        score_away += 1.0
        if home_star_out:
            factors.append(("🏥", f"{home_star_out.split()[-1]} OUT"))
        else:
            factors.append(("🏥", "Injury Edge"))
    
    away_lat = away_stats.get("lat", 0)
    away_lon = away_stats.get("lon", 0)
    home_lat = home_stats.get("lat", 0)
    home_lon = home_stats.get("lon", 0)
    distance = calc_distance_miles(away_lat, away_lon, home_lat, home_lon)
    if distance > 2000:
        score_home += 1.0
        factors.append(("✈️", "Travel"))
    
    home_win_pct = home_stats.get("home_win_pct", 0.5)
    if home_win_pct > 0.65:
        score_home += 0.8
        factors.append(("🔥", "Home Dominance"))
    
    if home_team == "Denver":
        score_home += 1.0
        factors.append(("🏔️", "Altitude"))
    
    total = score_home + score_away
    if total == 0:
        return None, 0, []
    
    home_final = (score_home / total) * 10
    away_final = (score_away / total) * 10
    
    if home_final >= away_final:
        return home_team, round(home_final, 1), factors
    else:
        return away_team, round(away_final, 1), factors

def get_signal_tier(score):
    if score >= 8.0:
        return "🟢 STRONG BUY", "#00ff00"
    elif score >= 6.5:
        return "🔵 BUY", "#00aaff"
    elif score >= 5.5:
        return "🟡 LEAN", "#ffff00"
    else:
        return "⚪ WEAK", "#888888"

# ========== FETCH DATA ==========
games = fetch_espn_scores(date_key=today_str)
game_list = sorted(list(games.keys()))
yesterday_teams_raw = fetch_yesterday_teams()
injuries = fetch_espn_injuries()

today_teams = set()
for gk in games.keys():
    parts = gk.split("@")
    today_teams.add(parts[0])
    today_teams.add(parts[1])
yesterday_teams = yesterday_teams_raw.intersection(today_teams)

# ========== HEADER ==========
st.title("🎯 NBA EDGE FINDER")
hdr1, hdr2, hdr3 = st.columns([3, 1, 1])
hdr1.caption(f"{auto_status} | {now.strftime('%I:%M:%S %p ET')} | v16.0")
if hdr2.button("🔄 Auto" if not st.session_state.auto_refresh else "⏹️ Stop", use_container_width=True):
    st.session_state.auto_refresh = not st.session_state.auto_refresh
    st.rerun()
if hdr3.button("🔄 Refresh", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

st.divider()

# ========== ML PICKS (SHOWS ALL GAMES) ==========
st.subheader("🎯 ML PICKS")

ml_results = []
for gk in game_list:
    g = games[gk]
    away, home = g['away_team'], g['home_team']
    pick, score, factors = calc_ml_score(away, home, injuries, yesterday_teams)
    
    if pick:
        pick_code = KALSHI_CODES.get(pick, "XXX")
        date_code = now.strftime("%y%b%d").upper()
        away_code = KALSHI_CODES.get(away, "XXX")
        home_code = KALSHI_CODES.get(home, "XXX")
        ticker = f"KXNBAGAME-{date_code}{away_code}{home_code}"
        
        market, pressure_label, pressure_color = calc_market_pressure(ticker, pick, home)
        
        ml_results.append({
            "game": gk, "pick": pick, "score": score, "factors": factors,
            "away": away, "home": home, "status": g['status_type'],
            "ticker": ticker, "market": market,
            "pressure_label": pressure_label, "pressure_color": pressure_color
        })

ml_results.sort(key=lambda x: x['score'], reverse=True)

if ml_results:
    for r in ml_results:
        if r['score'] >= 8.0:
            border_color = "#00ff00"
        elif r['score'] >= 6.5:
            border_color = "#00aaff"
        elif r['score'] >= 5.5:
            border_color = "#ffff00"
        else:
            border_color = "#888888"
        
        factor_icons = " ".join([f[0] for f in r['factors'][:4]])
        opponent = r['away'] if r['pick'] == r['home'] else r['home']
        pick_code = KALSHI_CODES.get(r['pick'], "XXX")
        kalshi_url = f"https://kalshi.com/markets/{r['ticker'].lower()}"
        
        market_info = ""
        if r['market'] and r['market'].get('exists'):
            yes_price = r['market'].get('yes_price', 0)
            market_info = f" | {yes_price}¢"
        
        st.markdown(f"""
        <div style="display: flex; align-items: center; background: #1a1a2e; border-left: 4px solid {border_color}; padding: 12px 16px; margin-bottom: 8px; border-radius: 4px;">
            <div style="flex: 1;">
                <span style="font-weight: bold; color: white;">{r['pick']}</span>
                <span style="color: #888;"> vs {opponent}</span>
                <span style="color: {border_color}; font-weight: bold; margin-left: 8px;">{r['score']}/10</span>
                <span style="color: #888; font-size: 0.9em;"> {factor_icons}</span>
                <span style="background: {r['pressure_color']}22; color: {r['pressure_color']}; padding: 2px 8px; border-radius: 4px; font-size: 0.8em; margin-left: 8px;">{r['pressure_label']}{market_info}</span>
            </div>
            <div>
                <a href="{kalshi_url}" target="_blank" style="background: #00aa00; color: white; padding: 8px 16px; border-radius: 4px; text-decoration: none; font-weight: bold;">BUY {pick_code}</a>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander(f"📈 {r['pick']} Line Movement", expanded=False):
            history = fetch_kalshi_history(r['ticker'])
            if history and len(history) > 1:
                import pandas as pd
                df = pd.DataFrame(history)
                if 'yes_price' in df.columns and 'ts' in df.columns:
                    df['time'] = pd.to_datetime(df['ts'], unit='s')
                    df = df.sort_values('time')
                    st.line_chart(df.set_index('time')['yes_price'], use_container_width=True)
                    st.caption(f"Volume: {r['market'].get('volume', 'N/A')} | OI: {r['market'].get('open_interest', 'N/A')}")
                else:
                    st.info("Chart data unavailable")
            else:
                st.info("No price history available")
    
    st.markdown(f"""
    <div style="text-align: center; margin-top: 16px;">
        <span style="color: #888;">➕ {len(ml_results)} Picks Available</span>
    </div>
    """, unsafe_allow_html=True)
else:
    st.info("No games scheduled for today")

st.divider()

# ========== CUSHION SCANNER ==========
st.subheader("🎯 CUSHION SCANNER")

THRESHOLDS = [210.5, 215.5, 220.5, 225.5, 230.5, 235.5, 240.5, 245.5, 250.5, 255.5]

cush_col1, cush_col2 = st.columns(2)
cush_min = cush_col1.selectbox("Min minutes", [6, 9, 12, 15, 18], index=0, key="cush_min")
cush_side = cush_col2.selectbox("Side", ["NO", "YES"], key="cush_side")
is_no = cush_side == "NO"

cushion_data = []
live_count = 0
for gk, g in games.items():
    mins = get_minutes_played(g['period'], g['clock'], g['status_type'])
    if g['status_type'] != "STATUS_FINAL" and g['period'] > 0:
        live_count += 1
    if mins < cush_min or g['status_type'] == "STATUS_FINAL":
        continue
    
    total = g['total']
    pace = total / mins if mins > 0 else 0
    proj = round(pace * 48)
    
    if is_no:
        candidates = [t for t in THRESHOLDS if t > proj]
        if len(candidates) >= 2:
            bet_line = candidates[1]
        elif len(candidates) == 1:
            bet_line = candidates[0]
        else:
            continue
        cushion = bet_line - proj
    else:
        candidates = [t for t in THRESHOLDS if t < proj]
        if len(candidates) >= 2:
            bet_line = candidates[-2]
        elif len(candidates) == 1:
            bet_line = candidates[0]
        else:
            continue
        cushion = proj - bet_line
    
    if cushion >= 6:
        cushion_data.append({
            "game": gk, "total": total, "proj": proj, "bet_line": bet_line,
            "cushion": cushion, "pace": pace, "mins": mins,
            "period": g['period'], "clock": g['clock']
        })

cushion_data.sort(key=lambda x: x['cushion'], reverse=True)

st.caption(f"🏀 {len(games)} games | {live_count} live")

if cushion_data:
    for cd in cushion_data:
        if cd['pace'] < 4.5:
            pace_label, pace_color = "SLOW", "#00ff00"
            pace_icon = "✅"
        elif cd['pace'] < 4.8:
            pace_label, pace_color = "AVG", "#ffaa00"
            pace_icon = "⚠️"
        elif cd['pace'] < 5.2:
            pace_label, pace_color = "FAST", "#ff8800"
            pace_icon = "⚠️"
        else:
            pace_label, pace_color = "SHOOTOUT", "#ff4444"
            pace_icon = "🔴"
        
        if cd['cushion'] >= 15:
            cush_color = "#00ff00"
        elif cd['cushion'] >= 10:
            cush_color = "#00aaff"
        elif cd['cushion'] >= 6:
            cush_color = "#ffaa00"
        else:
            cush_color = "#888888"
        
        status = f"Q{cd['period']} {cd['clock']}"
        side_label = "NO" if is_no else "YES"
        
        st.markdown(f"""
        <div style="display: flex; align-items: center; background: #1a1a2e; border-left: 4px solid {cush_color}; padding: 12px 16px; margin-bottom: 8px; border-radius: 4px;">
            <div style="flex: 1;">
                <span style="font-weight: bold; color: white;">{cd['game'].replace('@', ' @ ')}</span>
                <span style="color: #888; margin-left: 8px;">{status}</span>
            </div>
            <div style="display: flex; align-items: center; gap: 16px;">
                <span style="color: #888;">Total: <b style="color: white;">{cd['total']}</b></span>
                <span style="color: #888;">Proj: <b style="color: white;">{cd['proj']}</b></span>
                <span style="background: #ff6600; color: white; padding: 4px 12px; border-radius: 4px; font-weight: bold;">🎯 {side_label} {cd['bet_line']}</span>
                <span style="color: {cush_color}; font-weight: bold;">+{cd['cushion']:.1f}</span>
                <span style="color: {pace_color};">{pace_icon} {pace_label} {cd['pace']:.2f}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info(f"No games with {cush_min}+ min and 6+ cushion")

st.divider()

# ========== PACE SCANNER ==========
st.subheader("🔥 PACE SCANNER")

pace_data = []
for gk, g in games.items():
    mins = get_minutes_played(g['period'], g['clock'], g['status_type'])
    if mins >= 6:
        pace = round(g['total'] / mins, 2)
        proj = round(pace * 48)
        pace_data.append({
            "game": gk, "pace": pace, "proj": proj, "total": g['total'], "mins": mins,
            "period": g['period'], "clock": g['clock'], "final": g['status_type'] == "STATUS_FINAL"
        })

pace_data.sort(key=lambda x: x['pace'])

if pace_data:
    for p in pace_data:
        if p['pace'] < 4.5:
            lbl, icon = "SLOW", "🟢"
        elif p['pace'] < 4.8:
            lbl, icon = "AVG", "🟡"
        elif p['pace'] < 5.2:
            lbl, icon = "FAST", "🟠"
        else:
            lbl, icon = "SHOOTOUT", "🔴"
        status = "FINAL" if p['final'] else f"Q{p['period']} {p['clock']}"
        st.markdown(f"**{p['game'].replace('@', ' @ ')}** — {p['total']}pts/{p['mins']:.0f}min — **{p['pace']}/min** {icon} **{lbl}** — Proj: {p['proj']} — {status}")
else:
    st.info("No games with 6+ minutes played yet")

st.divider()

# ========== INJURY REPORT ==========
st.subheader("🏥 INJURY REPORT")

injury_cards = []
for team in sorted(today_teams):
    team_inj = injuries.get(team, [])
    stars = STAR_PLAYERS.get(team, [])
    for inj in team_inj:
        name = inj.get("name", "")
        status = inj.get("status", "").upper()
        is_star = any(s.lower() in name.lower() for s in stars)
        
        star_rating = 0
        if is_star:
            if stars and name.lower() in stars[0].lower():
                star_rating = 3
            else:
                star_rating = 2
        
        if any(s in status for s in ["OUT", "DTD", "DAY-TO-DAY", "GTD", "QUESTIONABLE", "DOUBTFUL"]):
            if "OUT" in status:
                status_label = "OUT"
                status_color = "#ff4444"
            elif "DTD" in status or "DAY-TO-DAY" in status:
                status_label = "DTD"
                status_color = "#ff8800"
            elif "GTD" in status or "QUESTIONABLE" in status:
                status_label = "GTD"
                status_color = "#ffaa00"
            elif "DOUBTFUL" in status:
                status_label = "DTD"
                status_color = "#ff6600"
            else:
                status_label = status[:3]
                status_color = "#ff8800"
            
            if any(x in status for x in ["ANKLE", "KNEE", "LEG", "FOOT", "HAMSTRING", "CALF", "ACHILLES"]):
                inj_icon = "🦴"
            elif any(x in status for x in ["SHOULDER", "ARM", "WRIST", "HAND", "FINGER"]):
                inj_icon = "🦴"
            elif any(x in status for x in ["BACK", "HIP", "CORE"]):
                inj_icon = "🔥"
            elif any(x in status for x in ["ILLNESS", "SICK", "FLU"]):
                inj_icon = "🤒"
            elif any(x in status for x in ["REST", "MANAGEMENT"]):
                inj_icon = "🛡️"
            else:
                inj_icon = "🔥"
            
            injury_cards.append({
                "name": name, "team": team, "status_label": status_label,
                "status_color": status_color, "star_rating": star_rating, "icon": inj_icon
            })

injury_cards.sort(key=lambda x: (-x['star_rating'], x['team']))

if injury_cards:
    cols = st.columns(3)
    for i, card in enumerate(injury_cards):
        with cols[i % 3]:
            stars_display = "⭐ " * card['star_rating'] if card['star_rating'] > 0 else ""
            st.markdown(f"""
            <div style="background: #1a1a2e; border-left: 4px solid {card['status_color']}; padding: 10px 14px; margin-bottom: 8px; border-radius: 4px;">
                <div style="color: white; font-weight: bold;">{stars_display}{card['name']} {card['icon']}</div>
                <div><span style="color: {card['status_color']}; font-weight: bold;">{card['status_label']}</span><span style="color: #888;"> • {card['team']}</span></div>
            </div>
            """, unsafe_allow_html=True)
else:
    st.info("No injuries reported for today's teams")

st.divider()

# ========== POSITION TRACKER ==========
st.subheader("📊 POSITION TRACKER")

with st.expander("➕ Add Position"):
    c1, c2, c3, c4 = st.columns(4)
    pos_game = c1.selectbox("Game", game_list if game_list else ["No games"])
    pos_pick = c2.text_input("Pick", placeholder="NYK")
    pos_price = c3.number_input("Price ¢", min_value=1, max_value=99, value=50)
    pos_contracts = c4.number_input("Contracts", min_value=1, value=10)
    
    if st.button("Add Position"):
        st.session_state.positions.append({
            "game": pos_game, "pick": pos_pick, "price": pos_price,
            "contracts": pos_contracts, "added": now.strftime("%H:%M")
        })
        st.success(f"Added: {pos_pick} @ {pos_price}¢ x{pos_contracts}")
        st.rerun()

if st.session_state.positions:
    for i, pos in enumerate(st.session_state.positions):
        c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
        c1.write(f"**{pos['game']}** → {pos['pick']}")
        c2.write(f"Entry: {pos['price']}¢ x {pos['contracts']}")
        c3.write(f"Cost: ${pos['price'] * pos['contracts'] / 100:.2f}")
        if c4.button("❌", key=f"del_{i}"):
            st.session_state.positions.pop(i)
            st.rerun()
    
    if st.button("🗑️ Clear All"):
        st.session_state.positions = []
        st.rerun()
else:
    st.info("No positions tracked")

st.divider()

# ========== ALL GAMES ==========
st.subheader("📺 ALL GAMES")

if games:
    cols = st.columns(4)
    for i, (k, g) in enumerate(games.items()):
        with cols[i % 4]:
            st.write(f"**{g['away_team']}** {g['away_score']}")
            st.write(f"🏠 **{g['home_team']}** {g['home_score']}")
            status = "FINAL" if g['status_type'] == "STATUS_FINAL" else f"Q{g['period']} {g['clock']}" if g['period'] > 0 else "SCHEDULED"
            st.caption(f"{status} | {g['total']} pts")
else:
    st.info("No games today")

st.divider()

# ========== HOW TO USE ==========
st.subheader("📖 How to Use NBA Edge Finder")

with st.expander("🎯 ML Picks — Moneyline Strategy", expanded=False):
    st.markdown("""
    **What it does:** Analyzes 8 factors to find moneyline value on Kalshi NBA markets.
    
    **The 8 Factors:**
    - 🛏️ **Rest Edge** — Back-to-back detection (tired teams lose)
    - 📊 **Net Rating** — Offensive minus defensive efficiency differential
    - 🛡️ **Elite Defense** — Top 5 defensive teams get bonus
    - 🏠 **Home Court** — Built-in home advantage
    - 🏥 **Injury Impact** — Star player availability weighted heavily
    - ✈️ **Travel Fatigue** — Cross-country trips (2000+ miles) penalized
    - 🔥 **Home Dominance** — Teams with 65%+ home win rate
    - 🏔️ **Altitude** — Denver's 5280ft advantage
    
    **Signal Tiers:**
    - 🟢 **STRONG BUY (8.0+)** — Multiple factors aligned, high confidence
    - 🔵 **BUY (6.5-7.9)** — Good edge, worth sizing up
    - 🟡 **LEAN (5.5-6.4)** — Slight edge, smaller position
    - ⚪ **WEAK (<5.5)** — No clear edge, pass or fade
    
    **Market Pressure:**
    - 🟢 **CONFIRMING** — Kalshi price moving toward our pick
    - 🟡 **NEUTRAL** — No clear money flow
    - 🔴 **FADING** — Market disagrees (caution or contrarian opportunity)
    
    **Best Practice:** Wait for 🟢 STRONG BUY + 🟢 CONFIRMING for highest conviction plays.
    """)

with st.expander("🎯 Cushion Scanner — Live Totals Strategy", expanded=False):
    st.markdown("""
    **What it does:** Finds live games where the projected total has a big cushion to available Kalshi lines.
    
    **How it works:**
    1. Calculates current scoring pace (points per minute)
    2. Projects final total based on pace × 48 minutes
    3. Finds the 2nd available threshold above/below projection
    4. Shows cushion (buffer between projection and bet line)
    
    **Cushion Guide:**
    - **+15 or more** → 🟢 Safe cushion, high confidence
    - **+10 to +14** → 🔵 Good cushion, solid bet
    - **+6 to +9** → 🟡 Thin cushion, proceed with caution
    - **Below +6** → 🔴 No edge, don't chase
    
    **Pace Warning System:**
    - 🟢 **SLOW (<4.5/min)** — Safe for NO bets
    - 🟡 **AVG (4.5-4.8/min)** — Normal pace
    - 🟠 **FAST (4.8-5.2/min)** — Caution on NO bets
    - 🔴 **SHOOTOUT (>5.2/min)** — Avoid NO, consider YES
    
    **Best Practice:** Look for +10 cushion minimum with 🟢 SLOW pace for NO bets.
    """)

with st.expander("🔥 Pace Scanner — Totals Projection", expanded=False):
    st.markdown("""
    **What it does:** Shows real-time scoring pace for all live games to identify totals opportunities.
    
    **How to read it:**
    - **Pace** = Total points ÷ Minutes played
    - **Projection** = Pace × 48 (regulation minutes)
    
    **Strategy:**
    - Games starting SLOW often stay slow (defensive matchups)
    - Games starting FAST can explode (track for YES opportunities)
    - Compare projection to Kalshi lines for edge
    
    **Pro tip:** Sort by pace to quickly find slowest/fastest games.
    """)

with st.expander("🏥 Injury Report — Impact Analysis", expanded=False):
    st.markdown("""
    **What it does:** Shows all injuries for today's teams, weighted by star impact.
    
    **Star Ratings:**
    - ⭐⭐⭐ = Franchise player (massive impact)
    - ⭐⭐ = All-star caliber (significant impact)
    - No stars = Role player (minimal impact)
    
    **Status Codes:**
    - **OUT** — Confirmed not playing
    - **GTD** — Game-time decision (50/50)
    - **DTD** — Day-to-day (likely out)
    
    **How ML Picks use injuries:** Star player OUT adds major weight to opposing team. Check injury report before placing bets.
    """)

with st.expander("📊 Position Tracker — Trade Management", expanded=False):
    st.markdown("""
    **What it does:** Track your Kalshi positions and calculate P&L.
    
    **How to use:**
    1. Click "Add Position" after entering a trade
    2. Enter the game, your pick, entry price, and contracts
    3. View your cost basis and track results
    
    **Pro tip:** Use this to manage position sizing across multiple games.
    """)

st.divider()

st.caption("⚠️ For entertainment only. Not financial advice. v16.0 | 8-Factor ML + Market Pressure")
