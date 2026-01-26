import streamlit as st
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="BigSnapshot NBA Edge Finder", page_icon="🏀", layout="wide")

# ============================================================
# AUTH
# ============================================================
from auth import require_auth
require_auth()

# Auto-refresh every 24 seconds
st_autorefresh(interval=24000, key="datarefresh")

# ============================================================
# GA4 ANALYTICS
# ============================================================
import uuid
import requests as req_ga

def send_ga4_event(page_title, page_path):
    try:
        url = f"https://www.google-analytics.com/mp/collect?measurement_id=G-NQKY5VQ376&api_secret=n4oBJjH7RXi3dA7aQo2CZA"
        payload = {"client_id": str(uuid.uuid4()), "events": [{"name": "page_view", "params": {"page_title": page_title, "page_location": f"https://bigsnapshot.streamlit.app{page_path}"}}]}
        req_ga.post(url, json=payload, timeout=2)
    except: pass

send_ga4_event("BigSnapshot NBA Edge Finder", "/NBA")

import requests
from datetime import datetime, timedelta
import pytz

eastern = pytz.timezone("US/Eastern")
now = datetime.now(eastern)

VERSION = "7.2"
LEAGUE_AVG_TOTAL = 225

# ============================================================
# INITIALIZE SESSION STATE
# ============================================================
if 'positions' not in st.session_state:
    st.session_state.positions = []

# ============================================================
# TEAM DATA
# ============================================================
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

# Reverse lookup
KALSHI_TO_TEAM = {v: k for k, v in KALSHI_CODES.items()}

# TEAM_STATS - UPDATED FOR 2025-26 SEASON (as of Jan 26, 2026)
# Net ratings estimated from win% differential: (W-L)/(W+L) * 15
TEAM_STATS = {
    "Oklahoma City": {"net": 12.0, "pace": 98.8, "tier": "elite"},    # 37-9
    "Detroit": {"net": 10.5, "pace": 99.5, "tier": "elite"},          # 32-11
    "San Antonio": {"net": 8.5, "pace": 99.2, "tier": "elite"},       # 31-14
    "Denver": {"net": 7.8, "pace": 98.5, "tier": "elite"},            # 31-15
    "Boston": {"net": 5.5, "pace": 99.8, "tier": "good"},             # 28-17
    "Toronto": {"net": 4.8, "pace": 97.8, "tier": "good"},            # 28-19
    "Houston": {"net": 5.2, "pace": 99.5, "tier": "good"},            # 27-16
    "LA Lakers": {"net": 4.5, "pace": 98.5, "tier": "good"},          # 27-17
    "Phoenix": {"net": 4.0, "pace": 98.2, "tier": "good"},            # 27-18
    "Minnesota": {"net": 4.0, "pace": 98.2, "tier": "good"},          # 27-18
    "New York": {"net": 4.0, "pace": 97.5, "tier": "good"},           # 27-18
    "Cleveland": {"net": 3.5, "pace": 97.2, "tier": "good"},          # 27-20
    "Golden State": {"net": 2.0, "pace": 100.2, "tier": "mid"},       # 25-21
    "Philadelphia": {"net": 2.5, "pace": 97.5, "tier": "mid"},        # 24-20
    "Miami": {"net": 1.5, "pace": 97.2, "tier": "mid"},               # 24-22
    "Chicago": {"net": 1.0, "pace": 98.8, "tier": "mid"},             # 23-22
    "Portland": {"net": 0.0, "pace": 98.8, "tier": "mid"},            # 23-23
    "Orlando": {"net": 1.2, "pace": 96.8, "tier": "mid"},             # 23-21
    "Atlanta": {"net": -1.5, "pace": 100.5, "tier": "mid"},           # 22-25
    "LA Clippers": {"net": -2.0, "pace": 97.8, "tier": "weak"},       # 20-24
    "Dallas": {"net": -3.5, "pace": 99.0, "tier": "weak"},            # 19-27
    "Memphis": {"net": -4.0, "pace": 99.8, "tier": "weak"},           # 18-25
    "Milwaukee": {"net": -4.5, "pace": 98.8, "tier": "weak"},         # 18-26
    "Charlotte": {"net": -5.5, "pace": 99.5, "tier": "weak"},         # 18-28
    "Utah": {"net": -7.0, "pace": 98.5, "tier": "weak"},              # 15-31
    "Sacramento": {"net": -9.5, "pace": 100.5, "tier": "tank"},       # 12-34
    "Brooklyn": {"net": -8.5, "pace": 98.2, "tier": "tank"},          # 12-31
    "Indiana": {"net": -10.5, "pace": 102.5, "tier": "tank"},         # 11-35
    "New Orleans": {"net": -11.0, "pace": 99.0, "tier": "tank"},      # 11-36
    "Washington": {"net": -11.5, "pace": 100.8, "tier": "tank"},      # 10-34
}

# STAR_PLAYERS - UPDATED FOR 2025-26 SEASON (post-trades)
STAR_PLAYERS = {
    "Boston": ["Jayson Tatum", "Jaylen Brown", "Derrick White"],
    "Cleveland": ["Donovan Mitchell", "Darius Garland", "Evan Mobley"],
    "Oklahoma City": ["Shai Gilgeous-Alexander", "Chet Holmgren", "Jalen Williams"],
    "New York": ["Jalen Brunson", "Karl-Anthony Towns", "Mikal Bridges", "OG Anunoby"],
    "Milwaukee": ["Giannis Antetokounmpo", "Damian Lillard"],
    "Denver": ["Nikola Jokic", "Jamal Murray", "Michael Porter Jr"],
    "Minnesota": ["Anthony Edwards", "Rudy Gobert", "Julius Randle"],
    "Dallas": ["Luka Doncic", "Kyrie Irving"],
    "Phoenix": ["Kevin Durant", "Devin Booker", "Bradley Beal"],
    "LA Lakers": ["LeBron James", "Anthony Davis"],
    "Golden State": ["Stephen Curry", "Draymond Green"],
    "Miami": ["Bam Adebayo", "Tyler Herro"],  # Jimmy Butler injured
    "Philadelphia": ["Joel Embiid", "Tyrese Maxey", "Paul George"],
    "LA Clippers": ["James Harden", "Norman Powell"],  # Kawhi out
    "Memphis": ["Ja Morant", "Jaren Jackson Jr"],
    "New Orleans": ["Zion Williamson", "Brandon Ingram"],
    "Sacramento": ["Domantas Sabonis", "Keegan Murray"],  # De'Aaron Fox traded
    "Indiana": ["Pascal Siakam", "Bennedict Mathurin"],  # Haliburton injured
    "Orlando": ["Paolo Banchero", "Franz Wagner"],
    "Houston": ["Jalen Green", "Alperen Sengun", "Fred VanVleet"],
    "Atlanta": ["Jalen Johnson", "Onyeka Okongwu", "CJ McCollum"],  # Trae Young traded
    "Chicago": ["Zach LaVine", "Coby White"],
    "Charlotte": ["LaMelo Ball", "Brandon Miller"],
    "Detroit": ["Cade Cunningham", "Jalen Duren"],
    "Toronto": ["Scottie Barnes", "RJ Barrett", "Brandon Ingram"],
    "Brooklyn": ["Cam Thomas", "Dennis Schroder"],
    "San Antonio": ["Victor Wembanyama", "De'Aaron Fox", "Stephon Castle"],  # Fox acquired
    "Utah": ["Lauri Markkanen", "Collin Sexton"],
    "Portland": ["Anfernee Simons", "Deni Avdija", "Scoot Henderson"],
    "Washington": ["Jordan Poole", "Kyle Kuzma", "Khris Middleton"],
}

STAR_TIERS = {
    "Nikola Jokic": 3, "Shai Gilgeous-Alexander": 3, "Giannis Antetokounmpo": 3,
    "Luka Doncic": 3, "Joel Embiid": 3, "Jayson Tatum": 3, "LeBron James": 3,
    "Stephen Curry": 3, "Kevin Durant": 3, "Anthony Edwards": 3,
    "Donovan Mitchell": 2, "Jaylen Brown": 2, "Damian Lillard": 2, "Jimmy Butler": 2,
    "Anthony Davis": 2, "Kyrie Irving": 2, "Devin Booker": 2, "Ja Morant": 2,
    "Trae Young": 2, "Zion Williamson": 2, "Tyrese Haliburton": 2, "De'Aaron Fox": 2,
    "Jalen Brunson": 2, "Chet Holmgren": 2, "Paolo Banchero": 2, "Franz Wagner": 2,
    "Victor Wembanyama": 2, "Evan Mobley": 2, "LaMelo Ball": 2, "Cade Cunningham": 2,
    "Tyrese Maxey": 2, "Bam Adebayo": 2, "Karl-Anthony Towns": 2,
}

# ============================================================
# FETCH FUNCTIONS
# ============================================================
@st.cache_data(ttl=30)
def fetch_espn_games():
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
                full_name = c.get("team", {}).get("displayName", "")
                team_name = TEAM_ABBREVS.get(full_name, full_name)
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
            
            minutes_played = 0
            if period > 0:
                if period <= 4:
                    completed_quarters = (period - 1) * 12
                    if clock:
                        try:
                            if ":" in clock:
                                parts = clock.split(":")
                                mins_left = int(parts[0])
                                secs_left = float(parts[1]) if len(parts) > 1 else 0
                            else:
                                mins_left = 0
                                secs_left = float(clock)
                            minutes_played = completed_quarters + (12 - mins_left - secs_left/60)
                        except:
                            minutes_played = completed_quarters
                else:
                    minutes_played = 48 + (period - 4) * 5
            
            games.append({
                "away": away_team, "home": home_team,
                "away_score": away_score, "home_score": home_score,
                "status": status, "period": period, "clock": clock,
                "minutes_played": minutes_played, "total_score": home_score + away_score
            })
        return games
    except Exception as e:
        st.error(f"ESPN fetch error: {e}")
        return []

@st.cache_data(ttl=60)
def fetch_kalshi_totals():
    """Fetch real Kalshi totals brackets"""
    url = "https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXNBATOTAL&status=open&limit=200"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        markets = {}
        for m in data.get("markets", []):
            ticker = m.get("ticker", "")
            # Parse ticker: KXNBATOTAL-26JAN26PORBOS
            if "KXNBATOTAL-" not in ticker:
                continue
            
            # Extract game info
            parts = ticker.replace("KXNBATOTAL-", "")
            # Format: 26JAN26PORBOS
            if len(parts) >= 13:
                date_part = parts[:7]  # 26JAN26
                teams_part = parts[7:]  # PORBOS
                away_code = teams_part[:3]
                home_code = teams_part[3:6]
                
                game_key = f"{away_code}@{home_code}"
                
                # Get threshold from subtitle or title
                subtitle = m.get("subtitle", "")
                # Format: "Over 224.5 points scored"
                threshold = None
                if "Over " in subtitle:
                    try:
                        threshold = float(subtitle.split("Over ")[1].split(" ")[0])
                    except:
                        pass
                
                if threshold:
                    if game_key not in markets:
                        markets[game_key] = {
                            "away_code": away_code,
                            "home_code": home_code,
                            "date": date_part,
                            "thresholds": [],
                            "ticker_base": f"KXNBATOTAL-{date_part}{away_code}{home_code}"
                        }
                    markets[game_key]["thresholds"].append({
                        "line": threshold,
                        "ticker": ticker,
                        "yes_price": m.get("yes_bid", 50),
                        "no_price": m.get("no_bid", 50)
                    })
        
        # Sort thresholds for each game
        for game_key in markets:
            markets[game_key]["thresholds"].sort(key=lambda x: x["line"])
        
        return markets
    except Exception as e:
        st.error(f"Kalshi fetch error: {e}")
        return {}

@st.cache_data(ttl=300)
def fetch_injuries():
    url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/injuries"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        injuries = {}
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
        return injuries
    except:
        return {}

@st.cache_data(ttl=300)
def fetch_yesterday_teams():
    yesterday = (datetime.now(eastern) - timedelta(days=1)).strftime('%Y%m%d')
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

# ============================================================
# HELPER FUNCTIONS
# ============================================================
def get_injury_names(team_injuries):
    names = []
    for inj in team_injuries:
        if isinstance(inj, dict):
            status = str(inj.get("status", "")).upper()
            if "OUT" in status or "DOUBT" in status:
                names.append(inj.get("name", "").lower())
    return names

def calc_projection(game):
    """Calculate projected total based on current pace"""
    mins = game['minutes_played']
    total = game['total_score']
    
    if mins >= 8:
        pace = total / mins
        weight = min(1.0, (mins - 8) / 16)
        blended_pace = (pace * weight) + ((LEAGUE_AVG_TOTAL / 48) * (1 - weight))
        proj = round(blended_pace * 48)
    elif mins >= 6:
        pace = total / mins
        proj = round(((pace * 0.3) + ((LEAGUE_AVG_TOTAL / 48) * 0.7)) * 48)
    else:
        proj = LEAGUE_AVG_TOTAL
    
    return max(185, min(280, proj))

def get_pace_info(game):
    """Get pace label and value"""
    mins = game['minutes_played']
    total = game['total_score']
    
    if mins <= 0:
        return 0, "⏳ WAITING", "#888"
    
    pace = round(total / mins, 2)
    
    if pace > 5.2:
        return pace, "🚀 SHOOTOUT", "#ff0000"
    elif pace > 4.8:
        return pace, "🔥 FAST", "#ff8800"
    elif pace > 4.2:
        return pace, "⚖️ AVG", "#ffff00"
    else:
        return pace, "🐢 SLOW", "#00ff00"

def find_recommended_bracket(thresholds, projection, bet_type, cushion_levels=2):
    """Find recommended bracket with cushion built in"""
    if not thresholds:
        return None, None, None
    
    lines = [t["line"] for t in thresholds]
    
    if bet_type == "NO":
        # For NO (under): find threshold above projection, then go higher for cushion
        above = [l for l in lines if l > projection]
        if not above:
            return None, None, None
        # Get 1-2 levels above the tight line
        tight_idx = lines.index(above[0])
        rec_idx = min(tight_idx + cushion_levels, len(lines) - 1)
        rec_line = lines[rec_idx]
        cushion = rec_line - projection
        return rec_line, cushion, thresholds[rec_idx]
    
    else:  # YES
        # For YES (over): find threshold below projection, then go lower for cushion
        below = [l for l in lines if l < projection]
        if not below:
            return None, None, None
        # Get 1-2 levels below the tight line
        tight_idx = lines.index(below[-1])
        rec_idx = max(tight_idx - cushion_levels, 0)
        rec_line = lines[rec_idx]
        cushion = projection - rec_line
        return rec_line, cushion, thresholds[rec_idx]

def calc_live_edge(game, injuries, b2b_teams):
    away, home = game['away'], game['home']
    lead = game['home_score'] - game['away_score']
    
    # Base from net rating
    home_net = TEAM_STATS.get(home, {}).get("net", 0)
    away_net = TEAM_STATS.get(away, {}).get("net", 0)
    base = 50 + ((home_net - away_net) * 1.5) + 2.5
    
    if away in b2b_teams: base += 3
    if home in b2b_teams: base -= 2
    
    home_out = get_injury_names(injuries.get(home, []))
    away_out = get_injury_names(injuries.get(away, []))
    for star in STAR_PLAYERS.get(home, []):
        if any(star.lower() in n for n in home_out):
            base -= STAR_TIERS.get(star, 1) * 2
    for star in STAR_PLAYERS.get(away, []):
        if any(star.lower() in n for n in away_out):
            base += STAR_TIERS.get(star, 1) * 2
    
    # Live adjustments
    mins = game['minutes_played']
    period = game['period']
    live_adj = 0
    if abs(lead) >= 20: live_adj = 25 if lead > 0 else -25
    elif abs(lead) >= 15: live_adj = 18 if lead > 0 else -18
    elif abs(lead) >= 10: live_adj = 12 if lead > 0 else -12
    elif abs(lead) >= 5: live_adj = 6 if lead > 0 else -6
    
    if period == 4:
        if abs(lead) >= 10: live_adj += 15 if lead > 0 else -15
        elif abs(lead) >= 5: live_adj += 8 if lead > 0 else -8
    
    final_score = max(15, min(92, base + live_adj))
    live_pick = home if lead > 0 else away if lead < 0 else (home if base >= 50 else away)
    
    return {"pick": live_pick, "score": int(final_score), "lead": lead}

# ============================================================
# KALSHI LINKS (CORRECT FORMAT - UPPERCASE)
# ============================================================
def get_kalshi_ml_link(away, home):
    away_code = KALSHI_CODES.get(away, "XXX").upper()
    home_code = KALSHI_CODES.get(home, "XXX").upper()
    date_str = datetime.now(eastern).strftime('%y%b%d').upper()
    ticker = f"KXNBAGAME-{date_str}{away_code}{home_code}"
    return f"https://kalshi.com/markets/KXNBAGAME/{ticker}"

def get_kalshi_totals_link(away, home):
    away_code = KALSHI_CODES.get(away, "XXX").upper()
    home_code = KALSHI_CODES.get(home, "XXX").upper()
    date_str = datetime.now(eastern).strftime('%y%b%d').upper()
    ticker = f"KXNBATOTAL-{date_str}{away_code}{home_code}"
    return f"https://kalshi.com/markets/KXNBATOTAL/{ticker}"

def get_kalshi_spread_link(away, home):
    away_code = KALSHI_CODES.get(away, "XXX").upper()
    home_code = KALSHI_CODES.get(home, "XXX").upper()
    date_str = datetime.now(eastern).strftime('%y%b%d').upper()
    ticker = f"KXNBASPREAD-{date_str}{away_code}{home_code}"
    return f"https://kalshi.com/markets/KXNBASPREAD/{ticker}"

# ============================================================
# POSITION TRACKER
# ============================================================
def add_position(game_key, pick, bet_type, line, link):
    pos = {"game": game_key, "pick": pick, "type": bet_type, "line": line, "link": link, "id": str(uuid.uuid4())[:8]}
    st.session_state.positions.append(pos)

def remove_position(pos_id):
    st.session_state.positions = [p for p in st.session_state.positions if p['id'] != pos_id]

def clear_all_positions():
    st.session_state.positions = []

# ============================================================
# SIDEBAR LEGEND
# ============================================================
with st.sidebar:
    st.header("📖 BIGSNAPSHOT EDGE GUIDE")
    st.markdown("""
### ML Score Guide
| Score | Label | Action |
|-------|-------|--------|
| **70+** | 🟢 STRONG | Best edge |
| **60-69** | 🟢 GOOD | Worth it |
| **50-59** | 🟡 MODERATE | Wait |
| **<50** | ⚪ WEAK | Skip |

---
### Pace Guide (Totals)
| Pace | Label | Bet |
|------|-------|-----|
| <4.2 | 🐢 SLOW | BUY NO |
| 4.2-4.8 | ⚖️ AVG | WAIT |
| 4.8-5.2 | 🔥 FAST | BUY YES |
| >5.2 | 🚀 SHOOTOUT | BUY YES |

---
### Cushion Guide
We recommend **1-2 levels** above/below projection for safety.

| Bet | Cushion |
|-----|---------|
| NO | Threshold ABOVE proj |
| YES | Threshold BELOW proj |

Bigger cushion = safer bet, lower payout.
""")
    st.divider()
    st.caption(f"v{VERSION} BIGSNAPSHOT")

# ============================================================
# FETCH DATA
# ============================================================
games = fetch_espn_games()
kalshi_totals = fetch_kalshi_totals()
injuries = fetch_injuries()
b2b_teams = fetch_yesterday_teams()

today_teams = set()
for g in games:
    today_teams.add(g['away'])
    today_teams.add(g['home'])

live_games = [g for g in games if g['status'] in ['STATUS_IN_PROGRESS', 'STATUS_HALFTIME', 'STATUS_END_PERIOD'] or (g['period'] > 0 and g['status'] not in ['STATUS_FINAL', 'STATUS_FULL_TIME'])]
scheduled_games = [g for g in games if g['status'] == 'STATUS_SCHEDULED' and g['period'] == 0]
final_games = [g for g in games if g['status'] in ['STATUS_FINAL', 'STATUS_FULL_TIME']]

# ============================================================
# HEADER
# ============================================================
st.title("🏀 BIGSNAPSHOT NBA EDGE FINDER")
st.caption(f"v{VERSION} • {now.strftime('%b %d, %Y %I:%M %p ET')} • Auto-refresh: 24s")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Today's Games", len(games))
c2.metric("Live Now", len(live_games))
c3.metric("Scheduled", len(scheduled_games))
c4.metric("Final", len(final_games))

st.divider()

# ============================================================
# 🏥 INJURY REPORT
# ============================================================
st.subheader("🏥 INJURY REPORT")

injured_stars = []
for team, team_injuries in injuries.items():
    if team not in today_teams: continue
    for inj in team_injuries:
        name = inj.get("name", "") if isinstance(inj, dict) else str(inj)
        status = str(inj.get("status", "")).upper() if isinstance(inj, dict) else "OUT"
        if "OUT" in status or "DOUBT" in status:
            tier = STAR_TIERS.get(name, 0)
            if tier == 0:
                for star_name in STAR_TIERS:
                    if star_name.lower() in name.lower():
                        tier = STAR_TIERS[star_name]
                        break
            if tier > 0:
                injured_stars.append({"name": name, "team": team, "status": "OUT" if "OUT" in status else "DOUBT", "tier": tier})

injured_stars.sort(key=lambda x: (-x['tier'], x['team']))

if injured_stars:
    cols = st.columns(3)
    for i, inj in enumerate(injured_stars):
        with cols[i % 3]:
            stars = "⭐" * inj['tier']
            status_color = "#ff4444" if inj['status'] == "OUT" else "#ffaa00"
            st.markdown(f"""<div style="background:linear-gradient(135deg,#1a1a2e,#2a1a2a);padding:10px;border-radius:6px;border-left:3px solid {status_color};margin-bottom:6px">
                <div style="color:#fff;font-weight:bold">{stars} {inj['name']}</div>
                <div style="color:{status_color};font-size:0.85em">{inj['status']} • {inj['team']}</div>
            </div>""", unsafe_allow_html=True)
else:
    st.info("No major star injuries for today's games")

st.divider()

# ============================================================
# 🔴 LIVE EDGE MONITOR
# ============================================================
if live_games:
    st.subheader("🔴 LIVE EDGE MONITOR")
    st.caption("Real-time ML edges • Updates every 24 seconds")
    
    for g in sorted(live_games, key=lambda x: calc_live_edge(x, injuries, b2b_teams)['score'], reverse=True):
        edge = calc_live_edge(g, injuries, b2b_teams)
        mins = g['minutes_played']
        game_key = f"{g['away']}@{g['home']}"
        
        if mins < 6:
            status_label, status_color = "⏳ TOO EARLY", "#888"
        elif abs(edge['lead']) < 3:
            status_label, status_color = "⚖️ TOO CLOSE", "#ffa500"
        elif edge['score'] >= 70:
            status_label, status_color = f"🟢 STRONG {edge['score']}", "#22c55e"
        elif edge['score'] >= 60:
            status_label, status_color = f"🟢 GOOD {edge['score']}", "#22c55e"
        else:
            status_label, status_color = f"🟡 {edge['score']}", "#eab308"
        
        lead_display = f"+{edge['lead']}" if edge['lead'] > 0 else str(edge['lead'])
        leader = g['home'] if edge['lead'] > 0 else g['away'] if edge['lead'] < 0 else "TIED"
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1e1e2e 0%, #2a2a3e 100%); border-radius: 12px; padding: 16px; margin-bottom: 8px; border: 1px solid #444;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="color: #fff; font-size: 1.1em; font-weight: 600;">{g['away']} @ {g['home']}</span>
                <span style="color: #ff6b6b; font-size: 0.9em;">Q{g['period']} {g['clock']}</span>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="color: #fff; font-size: 1.4em; font-weight: 700;">{g['away_score']} - {g['home_score']}</span>
                <span style="color: {status_color}; font-weight: 600;">{status_label}</span>
            </div>
            <div style="color: #aaa; font-size: 0.9em; margin-top: 6px;">
                Edge: <strong style="color: #fff;">{leader}</strong> ({lead_display})
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        bc1, bc2, bc3, bc4 = st.columns(4)
        with bc1:
            st.link_button(f"🎯 {edge['pick']} ML", get_kalshi_ml_link(g['away'], g['home']), use_container_width=True)
        with bc2:
            st.link_button("📊 SPREAD", get_kalshi_spread_link(g['away'], g['home']), use_container_width=True)
        with bc3:
            st.link_button("📈 TOTALS", get_kalshi_totals_link(g['away'], g['home']), use_container_width=True)
        with bc4:
            if st.button("➕ Track", key=f"add_live_{game_key}"):
                add_position(game_key, edge['pick'], "ML", "-", get_kalshi_ml_link(g['away'], g['home']))
                st.rerun()
        st.markdown("---")
else:
    st.info("🕐 No live games right now. Check back when games tip off!")

st.divider()

# ============================================================
# 🎯 CUSHION SCANNER (TOTALS WITH REAL KALSHI BRACKETS)
# ============================================================
st.subheader("🎯 CUSHION SCANNER")
st.caption("Totals recommendations with built-in safety cushion • Uses real Kalshi brackets")

cushion_min = st.selectbox("Min minutes played", [6, 9, 12, 15, 18], index=1, key="cushion_min")

cushion_results = []
for g in live_games:
    mins = g['minutes_played']
    if mins < cushion_min:
        continue
    
    away_code = KALSHI_CODES.get(g['away'], "XXX")
    home_code = KALSHI_CODES.get(g['home'], "XXX")
    game_key_kalshi = f"{away_code}@{home_code}"
    
    kalshi_data = kalshi_totals.get(game_key_kalshi, {})
    thresholds = kalshi_data.get("thresholds", [])
    
    if not thresholds:
        continue
    
    projection = calc_projection(g)
    pace_val, pace_label, pace_color = get_pace_info(g)
    
    # Determine bet direction based on pace
    if pace_val < 4.2:
        bet_type = "NO"
        rec_line, cushion, bracket_data = find_recommended_bracket(thresholds, projection, "NO", 2)
    elif pace_val > 4.8:
        bet_type = "YES"
        rec_line, cushion, bracket_data = find_recommended_bracket(thresholds, projection, "YES", 2)
    else:
        bet_type = None
        rec_line, cushion, bracket_data = None, None, None
    
    cushion_results.append({
        'game': g,
        'away': g['away'],
        'home': g['home'],
        'projection': projection,
        'pace_val': pace_val,
        'pace_label': pace_label,
        'pace_color': pace_color,
        'bet_type': bet_type,
        'rec_line': rec_line,
        'cushion': cushion,
        'bracket_data': bracket_data,
        'thresholds': thresholds
    })

# Sort by cushion (biggest first for actionable, then others)
cushion_results.sort(key=lambda x: (x['cushion'] or 0), reverse=True)

if cushion_results:
    for r in cushion_results:
        g = r['game']
        game_key = f"{r['away']}@{r['home']}"
        
        if r['bet_type'] and r['rec_line'] and r['cushion']:
            # Actionable recommendation
            if r['bet_type'] == "NO":
                rec_text = f"BUY NO @ {r['rec_line']}"
                rec_explain = f"Pace is SLOW → Game likely stays UNDER {r['rec_line']}"
                btn_color = "#22c55e"
            else:
                rec_text = f"BUY YES @ {r['rec_line']}"
                rec_explain = f"Pace is FAST → Game likely goes OVER {r['rec_line']}"
                btn_color = "#f97316"
            
            st.markdown(f"""<div style="background:#0f172a;padding:14px;margin-bottom:8px;border-radius:10px;border-left:4px solid {btn_color}">
                <div style="display:flex;justify-content:space-between;align-items:center">
                    <b style="color:#fff;font-size:1.1em">{r['away']} @ {r['home']}</b>
                    <span style="color:#888">Q{g['period']} {g['clock']} • {g['total_score']} pts</span>
                </div>
                <div style="color:#aaa;margin-top:8px">
                    Proj: <b style="color:#fff">{r['projection']}</b> • 
                    <span style="color:{r['pace_color']}">{r['pace_label']} ({r['pace_val']}/min)</span>
                </div>
                <div style="margin-top:10px;padding:10px;background:#1a2744;border-radius:6px">
                    <div style="color:{btn_color};font-size:1.2em;font-weight:bold">🎯 {rec_text}</div>
                    <div style="color:#888;font-size:0.85em;margin-top:4px">{rec_explain}</div>
                    <div style="color:#fff;margin-top:6px">Cushion: <b style="color:{btn_color}">+{r['cushion']:.1f}</b> points of safety</div>
                </div>
            </div>""", unsafe_allow_html=True)
            
            b1, b2, b3 = st.columns(3)
            with b1:
                st.link_button(f"🎯 {rec_text}", get_kalshi_totals_link(r['away'], r['home']), use_container_width=True)
            with b2:
                st.link_button("📊 All Brackets", get_kalshi_totals_link(r['away'], r['home']), use_container_width=True)
            with b3:
                if st.button("➕ Track", key=f"cush_{game_key}"):
                    add_position(game_key, r['bet_type'], "TOTAL", r['rec_line'], get_kalshi_totals_link(r['away'], r['home']))
                    st.rerun()
        else:
            # Neutral pace - no recommendation
            st.markdown(f"""<div style="background:#0f172a;padding:14px;margin-bottom:8px;border-radius:10px;border-left:4px solid #888">
                <div style="display:flex;justify-content:space-between;align-items:center">
                    <b style="color:#fff;font-size:1.1em">{r['away']} @ {r['home']}</b>
                    <span style="color:#888">Q{g['period']} {g['clock']} • {g['total_score']} pts</span>
                </div>
                <div style="color:#aaa;margin-top:8px">
                    Proj: <b style="color:#fff">{r['projection']}</b> • 
                    <span style="color:{r['pace_color']}">{r['pace_label']} ({r['pace_val']}/min)</span>
                </div>
                <div style="margin-top:10px;padding:10px;background:#1a2744;border-radius:6px">
                    <div style="color:#888;font-size:1em">⏳ WAIT — Pace is neutral, no clear edge</div>
                </div>
            </div>""", unsafe_allow_html=True)
        
        st.markdown("")
else:
    st.info(f"No games with {cushion_min}+ minutes played yet")

st.divider()

# ============================================================
# 📊 PACE SCANNER (VISUAL OVERVIEW)
# ============================================================
st.subheader("📊 PACE SCANNER")
st.caption("Quick visual of all live game paces")

pace_results = []
for g in live_games:
    mins = g['minutes_played']
    if mins < 3:
        continue
    
    projection = calc_projection(g)
    pace_val, pace_label, pace_color = get_pace_info(g)
    
    pace_results.append({
        'away': g['away'], 'home': g['home'],
        'total': g['total_score'], 'mins': mins,
        'pace_val': pace_val, 'pace_label': pace_label, 'pace_color': pace_color,
        'projection': projection,
        'period': g['period'], 'clock': g['clock']
    })

pace_results.sort(key=lambda x: x['pace_val'])

if pace_results:
    for r in pace_results:
        st.markdown(f"""<div style="background:#0f172a;padding:10px 14px;margin-bottom:6px;border-radius:8px;border-left:4px solid {r['pace_color']}">
        <b style="color:#fff">{r['away']} @ {r['home']}</b> 
        <span style="color:#888">Q{r['period']} {r['clock']} • {r['total']} pts in {r['mins']:.0f} min</span>
        <span style="color:{r['pace_color']};font-weight:bold;margin-left:12px">{r['pace_val']:.2f}/min {r['pace_label']}</span>
        <span style="color:#888;margin-left:12px">Proj: <b style="color:#fff">{r['projection']}</b></span>
        </div>""", unsafe_allow_html=True)
else:
    st.info("No live games to track yet")

st.divider()

# ============================================================
# 📊 POSITION TRACKER
# ============================================================
st.subheader("📊 POSITION TRACKER")

if st.session_state.positions:
    for pos in st.session_state.positions:
        line_display = f" @ {pos['line']}" if pos['line'] != "-" else ""
        pc1, pc2, pc3, pc4 = st.columns([3, 2, 2, 1])
        with pc1:
            st.write(f"**{pos['game']}**")
        with pc2:
            st.write(f"{pos['pick']} {pos['type']}{line_display}")
        with pc3:
            st.link_button("🔗 Buy", pos['link'], use_container_width=True)
        with pc4:
            if st.button("❌", key=f"del_{pos['id']}"):
                remove_position(pos['id'])
                st.rerun()
    
    if st.button("🗑️ Clear All Positions"):
        clear_all_positions()
        st.rerun()
else:
    st.caption("No positions tracked. Click ➕ Track on any recommendation to add.")

st.divider()

# ============================================================
# 🎯 PRE-GAME ALIGNMENT (SPECULATIVE)
# ============================================================
if scheduled_games:
    with st.expander("🎯 PRE-GAME ALIGNMENT (Speculative)", expanded=True):
        st.caption("⚠️ Pre-game picks are speculative. Live edges are more reliable.")
        
        for g in scheduled_games:
            away, home = g['away'], g['home']
            game_key = f"{away}@{home}"
            
            home_net = TEAM_STATS.get(home, {}).get("net", 0)
            away_net = TEAM_STATS.get(away, {}).get("net", 0)
            base = 50 + ((home_net - away_net) * 1.5) + 2.5
            
            if away in b2b_teams: base += 3
            if home in b2b_teams: base -= 2
            
            base = max(15, min(85, base))
            pick = home if base >= 50 else away
            score = int(base) if base >= 50 else int(100 - base)
            
            if score >= 70:
                score_color, border_color = "#22c55e", "#22c55e"
            elif score >= 60:
                score_color, border_color = "#22c55e", "#22c55e"
            elif score >= 50:
                score_color, border_color = "#eab308", "#eab308"
            else:
                score_color, border_color = "#888", "#444"
            
            b2b_away = "😴" if away in b2b_teams else ""
            b2b_home = "😴" if home in b2b_teams else ""
            
            st.markdown(f"""
            <div style="background: #1e1e2e; border-radius: 10px; padding: 14px; margin-bottom: 10px; border-left: 4px solid {border_color};">
                <div style="display: flex; justify-content: space-between;">
                    <span style="color: #fff; font-weight: 600;">{b2b_away}{away} @ {home}{b2b_home}</span>
                    <span style="color: {score_color}; font-weight: 600;">{score}/100 → {pick}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            cols = st.columns(4)
            cols[0].link_button(f"🎯 {pick}", get_kalshi_ml_link(away, home), use_container_width=True)
            cols[1].link_button("📊 SPREAD", get_kalshi_spread_link(away, home), use_container_width=True)
            cols[2].link_button("📈 TOTALS", get_kalshi_totals_link(away, home), use_container_width=True)
            if cols[3].button("➕", key=f"add_pre_{game_key}"):
                add_position(game_key, pick, "ML", "-", get_kalshi_ml_link(away, home))
                st.rerun()

st.divider()

# ============================================================
# 📖 HOW TO USE
# ============================================================
with st.expander("📖 HOW TO USE BIGSNAPSHOT NBA EDGE FINDER", expanded=False):
    st.markdown(f"""
## 🏀 BIGSNAPSHOT v{VERSION}

### Focus: LIVE EDGES + CUSHION SCANNER

Pre-game picks are speculative. **Real edges appear during live games.**

---

### 🔴 LIVE EDGE MONITOR (ML Picks)
| Score | Label | Action |
|-------|-------|--------|
| 70+ | 🟢 STRONG | Best edge |
| 60-69 | 🟢 GOOD | Worth it |
| 50-59 | 🟡 MODERATE | Wait |

**Wait for 6+ minutes** before trusting the edge.

---

### 🎯 CUSHION SCANNER (Totals)
This is where we protect you with **built-in cushion**.

| Pace | Direction | Recommendation |
|------|-----------|----------------|
| 🐢 SLOW (<4.2) | Under | BUY NO @ threshold ABOVE projection |
| 🔥 FAST (>4.8) | Over | BUY YES @ threshold BELOW projection |
| ⚖️ AVG | Neutral | WAIT |

**Cushion = safety buffer.** We recommend 1-2 levels away from tight line.

Example: Proj=222, SLOW pace → BUY NO @ 230.5 (+8.5 cushion)

---

### 📊 PACE SCANNER
Quick visual of all game paces. Use to spot opportunities.

---

### ⚠️ REMEMBER
- Bigger cushion = safer but lower payout
- Only bet when pace confirms direction
- Not financial advice

**Stay small. Stay quiet. Win.**
""")

st.caption(f"⚠️ Educational only. Not financial advice. BigSnapshot v{VERSION}")
st.caption("Stay small. Stay quiet. Win.")
