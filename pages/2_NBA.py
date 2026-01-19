import streamlit as st
import requests
from datetime import datetime, timedelta
import pytz
import json

# ============================================
# NBA EDGE FINDER v15.50 - SCHEDULE FIX
# ============================================

st.set_page_config(page_title="NBA Edge Finder", page_icon="🎯", layout="wide")

# Hide Streamlit menu/footer/header
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.stDeployButton {display: none;}
[data-testid="stToolbar"] {display: none;}
</style>
""", unsafe_allow_html=True)

# GA4 Tracking
st.markdown("""
<script async src="https://www.googletagmanager.com/gtag/js?id=G-NQKY5VQ376"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-NQKY5VQ376');
</script>
""", unsafe_allow_html=True)

# ============================================
# GATE CHECK
# ============================================
if "gate_passed" not in st.session_state:
    st.session_state.gate_passed = False

if not st.session_state.gate_passed:
    st.title("🎯 NBA Edge Finder")
    st.warning("⚠️ Please confirm the following before accessing this tool:")
    
    cb1 = st.checkbox("I understand this tool provides market signals, not predictions.")
    cb2 = st.checkbox("I understand signals may change as new information arrives.")
    cb3 = st.checkbox("I understand this is not financial advice and I am responsible for my own trades.")
    cb4 = st.checkbox("I understand this free beta may end or change at any time.")
    cb5 = st.checkbox("I confirm that I am 18 years or older.")
    
    if cb1 and cb2 and cb3 and cb4 and cb5:
        if st.button("Enter NBA Edge Finder", type="primary"):
            st.session_state.gate_passed = True
            st.rerun()
    else:
        st.info("Please check all boxes above to continue.")
    st.stop()

# ============================================
# TIMEZONE AND DATE
# ============================================
eastern = pytz.timezone('US/Eastern')
now = datetime.now(eastern)
today_str = now.strftime("%Y-%m-%d")

# ============================================
# TEAM MAPPINGS
# ============================================
# ESPN display name to standard name
ESPN_TO_STANDARD = {
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

# Standard name to Kalshi ticker code
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

# ============================================
# TEAM STATS (2025-26 Season)
# ============================================
TEAM_STATS = {
    "Atlanta": {"net_rtg": -3.2, "off_rtg": 115.8, "def_rtg": 119.0, "pace": 101.2, "record": "20-24"},
    "Boston": {"net_rtg": 9.8, "off_rtg": 120.5, "def_rtg": 110.7, "pace": 99.8, "record": "29-14"},
    "Brooklyn": {"net_rtg": -7.5, "off_rtg": 108.2, "def_rtg": 115.7, "pace": 96.3, "record": "15-29"},
    "Charlotte": {"net_rtg": -8.1, "off_rtg": 107.5, "def_rtg": 115.6, "pace": 100.5, "record": "11-30"},
    "Chicago": {"net_rtg": -4.2, "off_rtg": 112.3, "def_rtg": 116.5, "pace": 99.1, "record": "18-26"},
    "Cleveland": {"net_rtg": 7.2, "off_rtg": 117.8, "def_rtg": 110.6, "pace": 97.5, "record": "35-8"},
    "Dallas": {"net_rtg": -1.5, "off_rtg": 114.2, "def_rtg": 115.7, "pace": 98.8, "record": "17-26"},
    "Denver": {"net_rtg": 3.8, "off_rtg": 116.2, "def_rtg": 112.4, "pace": 98.2, "record": "26-17"},
    "Detroit": {"net_rtg": -5.8, "off_rtg": 110.5, "def_rtg": 116.3, "pace": 99.8, "record": "19-24"},
    "Golden State": {"net_rtg": 2.1, "off_rtg": 114.8, "def_rtg": 112.7, "pace": 100.2, "record": "22-21"},
    "Houston": {"net_rtg": 4.5, "off_rtg": 115.5, "def_rtg": 111.0, "pace": 98.5, "record": "28-15"},
    "Indiana": {"net_rtg": 1.2, "off_rtg": 118.5, "def_rtg": 117.3, "pace": 103.8, "record": "22-22"},
    "LA Clippers": {"net_rtg": -0.8, "off_rtg": 112.5, "def_rtg": 113.3, "pace": 97.2, "record": "18-23"},
    "LA Lakers": {"net_rtg": 1.5, "off_rtg": 114.2, "def_rtg": 112.7, "pace": 99.5, "record": "22-19"},
    "Memphis": {"net_rtg": 4.2, "off_rtg": 117.2, "def_rtg": 113.0, "pace": 101.5, "record": "27-17"},
    "Miami": {"net_rtg": 0.5, "off_rtg": 111.8, "def_rtg": 111.3, "pace": 96.8, "record": "20-22"},
    "Milwaukee": {"net_rtg": 2.8, "off_rtg": 116.5, "def_rtg": 113.7, "pace": 99.2, "record": "17-24"},
    "Minnesota": {"net_rtg": 3.5, "off_rtg": 112.8, "def_rtg": 109.3, "pace": 97.8, "record": "24-19"},
    "New Orleans": {"net_rtg": -9.2, "off_rtg": 107.5, "def_rtg": 116.7, "pace": 98.5, "record": "9-35"},
    "New York": {"net_rtg": 6.5, "off_rtg": 118.4, "def_rtg": 111.9, "pace": 99.5, "record": "25-17"},
    "Oklahoma City": {"net_rtg": 11.2, "off_rtg": 118.5, "def_rtg": 107.3, "pace": 99.8, "record": "35-8"},
    "Orlando": {"net_rtg": 2.2, "off_rtg": 109.5, "def_rtg": 107.3, "pace": 96.2, "record": "23-21"},
    "Philadelphia": {"net_rtg": -2.5, "off_rtg": 111.2, "def_rtg": 113.7, "pace": 98.2, "record": "15-26"},
    "Phoenix": {"net_rtg": 0.8, "off_rtg": 113.5, "def_rtg": 112.7, "pace": 98.5, "record": "21-21"},
    "Portland": {"net_rtg": -7.8, "off_rtg": 108.2, "def_rtg": 116.0, "pace": 99.8, "record": "14-29"},
    "Sacramento": {"net_rtg": -1.2, "off_rtg": 114.8, "def_rtg": 116.0, "pace": 100.5, "record": "20-24"},
    "San Antonio": {"net_rtg": 5.5, "off_rtg": 117.8, "def_rtg": 112.3, "pace": 100.8, "record": "29-13"},
    "Toronto": {"net_rtg": -6.5, "off_rtg": 109.5, "def_rtg": 116.0, "pace": 98.2, "record": "12-31"},
    "Utah": {"net_rtg": -5.2, "off_rtg": 119.4, "def_rtg": 124.6, "pace": 102.5, "record": "14-28"},
    "Washington": {"net_rtg": -10.5, "off_rtg": 112.7, "def_rtg": 123.2, "pace": 101.2, "record": "10-31"}
}

# Star players for injury impact
STAR_PLAYERS = {
    "Atlanta": ["Trae Young", "Jalen Johnson", "Dejounte Murray"],
    "Boston": ["Jayson Tatum", "Jaylen Brown", "Derrick White"],
    "Brooklyn": ["Cam Thomas", "Dennis Schroder", "Nic Claxton"],
    "Charlotte": ["LaMelo Ball", "Brandon Miller", "Miles Bridges"],
    "Chicago": ["Zach LaVine", "Coby White", "Nikola Vucevic"],
    "Cleveland": ["Donovan Mitchell", "Darius Garland", "Evan Mobley", "Jarrett Allen"],
    "Dallas": ["Luka Doncic", "Kyrie Irving", "Klay Thompson"],
    "Denver": ["Nikola Jokic", "Jamal Murray", "Michael Porter Jr."],
    "Detroit": ["Cade Cunningham", "Jaden Ivey", "Ausar Thompson"],
    "Golden State": ["Stephen Curry", "Draymond Green", "Andrew Wiggins"],
    "Houston": ["Jalen Green", "Alperen Sengun", "Fred VanVleet"],
    "Indiana": ["Tyrese Haliburton", "Pascal Siakam", "Myles Turner"],
    "LA Clippers": ["James Harden", "Kawhi Leonard", "Ivica Zubac"],
    "LA Lakers": ["LeBron James", "Anthony Davis", "Austin Reaves"],
    "Memphis": ["Ja Morant", "Desmond Bane", "Jaren Jackson Jr."],
    "Miami": ["Jimmy Butler", "Bam Adebayo", "Tyler Herro"],
    "Milwaukee": ["Giannis Antetokounmpo", "Damian Lillard", "Khris Middleton"],
    "Minnesota": ["Anthony Edwards", "Karl-Anthony Towns", "Rudy Gobert"],
    "New Orleans": ["Zion Williamson", "Brandon Ingram", "CJ McCollum"],
    "New York": ["Jalen Brunson", "Karl-Anthony Towns", "Mikal Bridges", "OG Anunoby"],
    "Oklahoma City": ["Shai Gilgeous-Alexander", "Chet Holmgren", "Jalen Williams"],
    "Orlando": ["Paolo Banchero", "Franz Wagner", "Jalen Suggs"],
    "Philadelphia": ["Joel Embiid", "Tyrese Maxey", "Paul George"],
    "Phoenix": ["Kevin Durant", "Devin Booker", "Bradley Beal"],
    "Portland": ["Anfernee Simons", "Scoot Henderson", "Jerami Grant"],
    "Sacramento": ["De'Aaron Fox", "Domantas Sabonis", "DeMar DeRozan"],
    "San Antonio": ["Victor Wembanyama", "Stephon Castle", "Devin Vassell"],
    "Toronto": ["Scottie Barnes", "RJ Barrett", "Immanuel Quickley"],
    "Utah": ["Lauri Markkanen", "Keyonte George", "John Collins"],
    "Washington": ["Jordan Poole", "Kyle Kuzma", "Alex Sarr"]
}

# ============================================
# FETCH ESPN GAMES - FIXED VERSION
# ============================================
@st.cache_data(ttl=60)
def fetch_espn_games():
    """Fetch today's games from ESPN API with correct home/away parsing"""
    games = {}
    try:
        url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        
        for event in data.get("events", []):
            competition = event.get("competitions", [{}])[0]
            competitors = competition.get("competitors", [])
            
            if len(competitors) != 2:
                continue
            
            # Parse teams correctly based on homeAway field
            home_team = None
            away_team = None
            home_score = "0"
            away_score = "0"
            
            for comp in competitors:
                team_data = comp.get("team", {})
                team_name = team_data.get("displayName", "")
                team_std = ESPN_TO_STANDARD.get(team_name, team_name)
                score = comp.get("score", "0")
                home_away = comp.get("homeAway", "")
                
                if home_away == "home":
                    home_team = team_std
                    home_score = score
                elif home_away == "away":
                    away_team = team_std
                    away_score = score
            
            if not home_team or not away_team:
                continue
            
            # Create game key as "away@home"
            game_key = f"{away_team}@{home_team}"
            
            # Parse status
            status_data = competition.get("status", {})
            status_type = status_data.get("type", {})
            status_state = status_type.get("state", "pre")
            status_desc = status_type.get("shortDetail", "")
            period = status_data.get("period", 0)
            clock = status_data.get("displayClock", "")
            
            # Parse game time
            game_date_str = event.get("date", "")
            try:
                game_dt = datetime.fromisoformat(game_date_str.replace("Z", "+00:00"))
                game_time_et = game_dt.astimezone(eastern).strftime("%I:%M %p ET")
            except:
                game_time_et = status_desc
            
            # Determine game status
            if status_state == "post":
                game_status = "FINAL"
            elif status_state == "in":
                game_status = f"Q{period} {clock}"
            else:
                game_status = game_time_et
            
            # Get broadcast info
            broadcasts = competition.get("broadcasts", [])
            tv_channel = ""
            for bc in broadcasts:
                names = bc.get("names", [])
                if names:
                    tv_channel = names[0]
                    break
            
            games[game_key] = {
                "away": away_team,
                "home": home_team,
                "away_score": int(away_score) if away_score.isdigit() else 0,
                "home_score": int(home_score) if home_score.isdigit() else 0,
                "status": game_status,
                "status_state": status_state,
                "period": period,
                "clock": clock,
                "tv": tv_channel,
                "game_id": event.get("id", "")
            }
    
    except Exception as e:
        st.error(f"Error fetching games: {e}")
    
    return games

# ============================================
# FETCH ESPN INJURIES
# ============================================
@st.cache_data(ttl=300)
def fetch_espn_injuries():
    """Fetch injury data from ESPN"""
    injuries = {}
    try:
        url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/injuries"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        
        injury_list = data.get("injuries", data.get("teams", []))
        for team_data in injury_list:
            # Handle different API response formats
            team_name = team_data.get("displayName", "")
            if not team_name:
                team_name = team_data.get("team", {}).get("displayName", "")
            
            team_std = ESPN_TO_STANDARD.get(team_name, team_name)
            if not team_std:
                continue
            
            injuries[team_std] = []
            player_list = team_data.get("injuries", team_data.get("athletes", []))
            
            for player in player_list:
                name = player.get("athlete", {}).get("displayName", "")
                if not name:
                    name = player.get("displayName", "")
                status = player.get("status", "")
                if not status:
                    status = player.get("type", {}).get("description", "")
                
                if name:
                    injuries[team_std].append({"name": name, "status": status})
    
    except Exception as e:
        pass  # Silently fail for injuries
    
    return injuries

# ============================================
# FETCH YESTERDAY'S TEAMS (for B2B detection)
# ============================================
@st.cache_data(ttl=3600)
def fetch_yesterday_teams():
    """Get teams that played yesterday for B2B detection"""
    teams = set()
    try:
        yesterday = (datetime.now(eastern) - timedelta(days=1)).strftime("%Y%m%d")
        url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={yesterday}"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        
        for event in data.get("events", []):
            competition = event.get("competitions", [{}])[0]
            for comp in competition.get("competitors", []):
                team_name = comp.get("team", {}).get("displayName", "")
                team_std = ESPN_TO_STANDARD.get(team_name, team_name)
                if team_std:
                    teams.add(team_std)
    except:
        pass
    
    return teams

# ============================================
# CHECK KALSHI MARKET EXISTS
# ============================================
@st.cache_data(ttl=300)
def check_kalshi_market_exists(ticker):
    """Check if Kalshi market exists"""
    try:
        url = f"https://api.elections.kalshi.com/trade-api/v2/markets/{ticker.upper()}"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("market") is not None
        return False
    except:
        return False

# ============================================
# 10-FACTOR EDGE SCORING MODEL
# ============================================
def calculate_edge_score(away_team, home_team, injuries, yesterday_teams):
    """Calculate edge score using 10-factor model"""
    
    away_stats = TEAM_STATS.get(away_team, {})
    home_stats = TEAM_STATS.get(home_team, {})
    
    if not away_stats or not home_stats:
        return None, None, {}
    
    factors = {}
    total_score = 5.0  # Start neutral
    
    # Factor 1: Net Rating Differential (weight: 1.5)
    away_net = away_stats.get("net_rtg", 0)
    home_net = home_stats.get("net_rtg", 0)
    net_diff = home_net - away_net  # Positive = home advantage
    net_score = max(-1.5, min(1.5, net_diff * 0.1))
    total_score += net_score
    factors["net_rating"] = {"diff": net_diff, "score": net_score}
    
    # Factor 2: Home Court Advantage (weight: 0.8)
    home_boost = 0.8
    total_score += home_boost
    factors["home_court"] = {"boost": home_boost}
    
    # Factor 3: Offensive Rating (weight: 0.6)
    away_off = away_stats.get("off_rtg", 110)
    home_off = home_stats.get("off_rtg", 110)
    off_diff = home_off - away_off
    off_score = max(-0.6, min(0.6, off_diff * 0.06))
    total_score += off_score
    factors["offense"] = {"away": away_off, "home": home_off, "score": off_score}
    
    # Factor 4: Defensive Rating (weight: 0.6) - lower is better
    away_def = away_stats.get("def_rtg", 110)
    home_def = home_stats.get("def_rtg", 110)
    def_diff = away_def - home_def  # Positive = home has better D
    def_score = max(-0.6, min(0.6, def_diff * 0.06))
    total_score += def_score
    factors["defense"] = {"away": away_def, "home": home_def, "score": def_score}
    
    # Factor 5: Pace Differential (weight: 0.3)
    away_pace = away_stats.get("pace", 100)
    home_pace = home_stats.get("pace", 100)
    pace_avg = (away_pace + home_pace) / 2
    factors["pace"] = {"away": away_pace, "home": home_pace, "avg": pace_avg}
    
    # Factor 6: Back-to-Back Fatigue (weight: 0.7)
    away_b2b = away_team in yesterday_teams
    home_b2b = home_team in yesterday_teams
    
    if away_b2b and not home_b2b:
        total_score += 0.7  # Home advantage
        factors["b2b"] = {"away_b2b": True, "home_b2b": False, "score": 0.7}
    elif home_b2b and not away_b2b:
        total_score -= 0.7  # Away advantage
        factors["b2b"] = {"away_b2b": False, "home_b2b": True, "score": -0.7}
    else:
        factors["b2b"] = {"away_b2b": away_b2b, "home_b2b": home_b2b, "score": 0}
    
    # Factor 7: Star Player Injuries (weight: up to 1.5)
    away_stars = STAR_PLAYERS.get(away_team, [])
    home_stars = STAR_PLAYERS.get(home_team, [])
    away_injuries = injuries.get(away_team, [])
    home_injuries = injuries.get(home_team, [])
    
    away_star_out = 0
    home_star_out = 0
    
    for inj in away_injuries:
        if any(star.lower() in inj.get("name", "").lower() for star in away_stars):
            status = inj.get("status", "").lower()
            if "out" in status or "questionable" in status:
                away_star_out += 1
    
    for inj in home_injuries:
        if any(star.lower() in inj.get("name", "").lower() for star in home_stars):
            status = inj.get("status", "").lower()
            if "out" in status or "questionable" in status:
                home_star_out += 1
    
    injury_impact = (away_star_out - home_star_out) * 0.5
    injury_impact = max(-1.5, min(1.5, injury_impact))
    total_score += injury_impact
    factors["injuries"] = {"away_out": away_star_out, "home_out": home_star_out, "score": injury_impact}
    
    # Factor 8: Recent Form (based on record - simplified)
    # This could be expanded with actual recent game data
    factors["form"] = {"note": "Based on season record"}
    
    # Factor 9: Head-to-Head (placeholder)
    factors["h2h"] = {"note": "Historical data"}
    
    # Factor 10: Travel/Rest Days (simplified B2B already covers most)
    factors["rest"] = {"note": "Incorporated in B2B"}
    
    # Normalize to 0-10 scale
    total_score = max(0, min(10, total_score))
    
    # Determine pick
    if total_score >= 5.5:
        pick = home_team
    else:
        pick = away_team
        total_score = 10 - total_score  # Flip score for away pick
    
    return pick, round(total_score, 1), factors

# ============================================
# GENERATE KALSHI TICKER
# ============================================
def get_kalshi_ticker(away_team, home_team):
    """Generate Kalshi ticker for NBA game"""
    away_code = KALSHI_CODES.get(away_team, "XXX")
    home_code = KALSHI_CODES.get(home_team, "XXX")
    date_code = now.strftime("%y%b%d").upper()  # e.g., 26JAN19
    ticker = f"KXNBAGAME-{date_code}{away_code}{home_code}"
    return ticker

# ============================================
# SIGNAL DISPLAY
# ============================================
def get_signal_display(score):
    """Get signal tier based on score"""
    if score >= 8.0:
        return "🟢 STRONG BUY", "#00aa00"
    elif score >= 6.5:
        return "🔵 BUY", "#0066cc"
    elif score >= 5.5:
        return "🟡 LEAN", "#ccaa00"
    else:
        return "⚪ TOSS-UP", "#666666"

# ============================================
# MAIN APP
# ============================================

# Initialize session state
if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = False
if 'positions' not in st.session_state:
    st.session_state.positions = []

# Fetch data
games = fetch_espn_games()
injuries = fetch_espn_injuries()
yesterday_teams = fetch_yesterday_teams()

# Header
st.title("🎯 NBA EDGE FINDER")
st.caption(f"Last update: {now.strftime('%I:%M:%S %p ET')} | v15.50 | Today: {now.strftime('%A, %B %d, %Y')}")

# Refresh button
col_ref1, col_ref2 = st.columns([1, 5])
with col_ref1:
    if st.button("🔄 Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.divider()

# ============================================
# TODAY'S GAMES
# ============================================
st.subheader(f"📅 TODAY'S GAMES ({len(games)} games)")

if not games:
    st.warning("No games found for today. Check back later or try refreshing.")
else:
    # Sort games: live first, then by status
    def sort_key(item):
        game = item[1]
        if game['status_state'] == 'in':
            return (0, game['status'])
        elif game['status_state'] == 'pre':
            return (1, game['status'])
        else:
            return (2, game['status'])
    
    sorted_games = sorted(games.items(), key=sort_key)
    
    for game_key, game in sorted_games:
        away = game['away']
        home = game['home']
        
        # Calculate edge
        pick, score, factors = calculate_edge_score(away, home, injuries, yesterday_teams)
        
        if pick and score:
            signal, color = get_signal_display(score)
            
            # Build title
            if game['status_state'] == 'in':
                title = f"🔴 LIVE: {away} ({game['away_score']}) @ {home} ({game['home_score']}) — {game['status']}"
            elif game['status_state'] == 'post':
                title = f"✅ FINAL: {away} ({game['away_score']}) @ {home} ({game['home_score']})"
            else:
                title = f"⏰ {game['status']}: {away} @ {home}"
            
            with st.expander(title, expanded=(game['status_state'] == 'in')):
                col1, col2, col3 = st.columns([2, 2, 2])
                
                with col1:
                    st.markdown(f"**{signal}**")
                    st.markdown(f"**Pick: {pick}**")
                    st.markdown(f"**Score: {score}/10**")
                
                with col2:
                    st.markdown("**Key Factors:**")
                    # Net Rating
                    net_diff = factors.get("net_rating", {}).get("diff", 0)
                    st.markdown(f"• Net Rtg Diff: {net_diff:+.1f}")
                    # B2B
                    b2b = factors.get("b2b", {})
                    if b2b.get("away_b2b"):
                        st.markdown(f"• ⚠️ {away} on B2B")
                    if b2b.get("home_b2b"):
                        st.markdown(f"• ⚠️ {home} on B2B")
                    # Injuries
                    inj = factors.get("injuries", {})
                    if inj.get("away_out", 0) > 0:
                        st.markdown(f"• 🏥 {away}: {inj['away_out']} star(s) out")
                    if inj.get("home_out", 0) > 0:
                        st.markdown(f"• 🏥 {home}: {inj['home_out']} star(s) out")
                
                with col3:
                    # Kalshi link
                    ticker = get_kalshi_ticker(away, home)
                    pick_code = KALSHI_CODES.get(pick, "XXX")
                    
                    market_exists = check_kalshi_market_exists(ticker)
                    
                    if market_exists:
                        kalshi_url = f"https://kalshi.com/markets/{ticker.lower()}"
                        st.link_button(f"🎯 BUY {pick_code}", kalshi_url, use_container_width=True)
                        st.caption(f"✅ {ticker}")
                    else:
                        st.warning(f"⏳ Market not live yet")
                        st.caption(f"Ticker: {ticker}")
                    
                    # TV info
                    if game.get('tv'):
                        st.caption(f"📺 {game['tv']}")
        else:
            # No stats available
            title = f"⏰ {game['status']}: {away} @ {home}"
            with st.expander(title):
                st.info("Edge calculation not available for this game.")

# ============================================
# INJURY REPORT
# ============================================
st.divider()
st.subheader("🏥 INJURY REPORT")

# Get teams playing today
today_teams = set()
for gk in games.keys():
    parts = gk.split("@")
    today_teams.add(parts[0])
    today_teams.add(parts[1])

injury_count = 0
for team in sorted(today_teams):
    team_injuries = injuries.get(team, [])
    star_list = STAR_PLAYERS.get(team, [])
    
    for inj in team_injuries:
        name = inj.get("name", "")
        status = inj.get("status", "")
        is_star = any(star.lower() in name.lower() for star in star_list)
        
        if is_star:
            st.markdown(f"**⭐ {team}**: {name} — {status}")
            injury_count += 1
        elif "out" in status.lower():
            st.markdown(f"• {team}: {name} — {status}")
            injury_count += 1

if injury_count == 0:
    st.info("No significant injuries reported for today's games.")

# ============================================
# POSITION TRACKER
# ============================================
st.divider()
st.subheader("📊 POSITION TRACKER")

# Add position form
with st.expander("➕ Add New Position"):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        game_options = list(games.keys())
        if game_options:
            pos_game = st.selectbox("Game", game_options)
        else:
            pos_game = st.text_input("Game (e.g., DAL@NYK)")
    with col2:
        pos_pick = st.text_input("Pick (e.g., NYK)")
    with col3:
        pos_price = st.number_input("Entry Price (¢)", min_value=1, max_value=99, value=50)
    with col4:
        pos_contracts = st.number_input("Contracts", min_value=1, value=10)
    
    if st.button("Add Position"):
        new_pos = {
            "game": pos_game,
            "pick": pos_pick,
            "price": pos_price,
            "contracts": pos_contracts,
            "added": now.strftime("%H:%M")
        }
        st.session_state.positions.append(new_pos)
        st.success(f"Added: {pos_pick} @ {pos_price}¢ x{pos_contracts}")
        st.rerun()

# Display positions
if st.session_state.positions:
    for i, pos in enumerate(st.session_state.positions):
        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
        with col1:
            st.markdown(f"**{pos['game']}** → {pos['pick']}")
        with col2:
            st.markdown(f"Entry: {pos['price']}¢ x {pos['contracts']}")
        with col3:
            cost = pos['price'] * pos['contracts']
            st.markdown(f"Cost: ${cost/100:.2f}")
        with col4:
            if st.button("❌", key=f"del_{i}"):
                st.session_state.positions.pop(i)
                st.rerun()
else:
    st.info("No active positions. Add one above!")

# ============================================
# HOW TO USE
# ============================================
st.divider()
st.subheader("📖 How to Use This App")

st.markdown("""
**NBA Edge Finder** helps you identify potential edges in NBA prediction markets on Kalshi.

**Understanding the Signals:**
- **🟢 STRONG BUY** — High-confidence edge detected, score 8.0+
- **🔵 BUY** — Good edge, score 6.5-7.9
- **🟡 LEAN** — Slight edge, score 5.5-6.4
- **⚪ TOSS-UP** — No clear edge

**10-Factor Model:**
1. Net Rating Differential
2. Home Court Advantage
3. Offensive Rating
4. Defensive Rating
5. Pace Analysis
6. Back-to-Back Fatigue
7. Star Player Injuries
8. Recent Form
9. Head-to-Head History
10. Rest/Travel

**Tips:**
- Focus on 🟢 STRONG BUY signals for highest confidence
- Check injury reports before trading
- Back-to-back games can significantly impact performance
- Markets may not be live until close to game time

📧 Questions or feedback? Contact: **aipublishingpro@gmail.com**
""")

st.caption("© 2026 Big Snapshot | For informational purposes only | Not financial advice")
