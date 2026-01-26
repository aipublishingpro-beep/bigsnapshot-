import streamlit as st
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="BigSnapshot NBA Edge Finder", page_icon="🏀", layout="wide")

from auth import require_auth
require_auth()

st_autorefresh(interval=24000, key="datarefresh")

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

VERSION = "7.4"
LEAGUE_AVG_TOTAL = 225

if 'positions' not in st.session_state:
    st.session_state.positions = []

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

KALSHI_TO_TEAM = {v: k for k, v in KALSHI_CODES.items()}

TEAM_COLORS = {
    "Atlanta": "#E03A3E", "Boston": "#007A33", "Brooklyn": "#000000", "Charlotte": "#1D1160",
    "Chicago": "#CE1141", "Cleveland": "#860038", "Dallas": "#00538C", "Denver": "#0E2240",
    "Detroit": "#C8102E", "Golden State": "#1D428A", "Houston": "#CE1141", "Indiana": "#002D62",
    "LA Clippers": "#C8102E", "LA Lakers": "#552583", "Memphis": "#5D76A9", "Miami": "#98002E",
    "Milwaukee": "#00471B", "Minnesota": "#0C2340", "New Orleans": "#0C2340", "New York": "#006BB6",
    "Oklahoma City": "#007AC1", "Orlando": "#0077C0", "Philadelphia": "#006BB6", "Phoenix": "#1D1160",
    "Portland": "#E03A3E", "Sacramento": "#5A2D81", "San Antonio": "#C4CED4", "Toronto": "#CE1141",
    "Utah": "#002B5C", "Washington": "#002B5C"
}

TEAM_STATS = {
    "Oklahoma City": {"net": 12.0, "pace": 98.8, "tier": "elite"},
    "Detroit": {"net": 10.5, "pace": 99.5, "tier": "elite"},
    "San Antonio": {"net": 8.5, "pace": 99.2, "tier": "elite"},
    "Denver": {"net": 7.8, "pace": 98.5, "tier": "elite"},
    "Boston": {"net": 5.5, "pace": 99.8, "tier": "good"},
    "Toronto": {"net": 4.8, "pace": 97.8, "tier": "good"},
    "Houston": {"net": 5.2, "pace": 99.5, "tier": "good"},
    "LA Lakers": {"net": 4.5, "pace": 98.5, "tier": "good"},
    "Phoenix": {"net": 4.0, "pace": 98.2, "tier": "good"},
    "Minnesota": {"net": 4.0, "pace": 98.2, "tier": "good"},
    "New York": {"net": 4.0, "pace": 97.5, "tier": "good"},
    "Cleveland": {"net": 3.5, "pace": 97.2, "tier": "good"},
    "Golden State": {"net": 2.0, "pace": 100.2, "tier": "mid"},
    "Philadelphia": {"net": 2.5, "pace": 97.5, "tier": "mid"},
    "Miami": {"net": 1.5, "pace": 97.2, "tier": "mid"},
    "Chicago": {"net": 1.0, "pace": 98.8, "tier": "mid"},
    "Portland": {"net": 0.0, "pace": 98.8, "tier": "mid"},
    "Orlando": {"net": 1.2, "pace": 96.8, "tier": "mid"},
    "Atlanta": {"net": -1.5, "pace": 100.5, "tier": "mid"},
    "LA Clippers": {"net": -2.0, "pace": 97.8, "tier": "weak"},
    "Dallas": {"net": -3.5, "pace": 99.0, "tier": "weak"},
    "Memphis": {"net": -4.0, "pace": 99.8, "tier": "weak"},
    "Milwaukee": {"net": -4.5, "pace": 98.8, "tier": "weak"},
    "Charlotte": {"net": -5.5, "pace": 99.5, "tier": "weak"},
    "Utah": {"net": -7.0, "pace": 98.5, "tier": "weak"},
    "Sacramento": {"net": -9.5, "pace": 100.5, "tier": "tank"},
    "Brooklyn": {"net": -8.5, "pace": 98.2, "tier": "tank"},
    "Indiana": {"net": -10.5, "pace": 102.5, "tier": "tank"},
    "New Orleans": {"net": -11.0, "pace": 99.0, "tier": "tank"},
    "Washington": {"net": -11.5, "pace": 100.8, "tier": "tank"},
}

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
    "Miami": ["Bam Adebayo", "Tyler Herro"],
    "Philadelphia": ["Joel Embiid", "Tyrese Maxey", "Paul George"],
    "LA Clippers": ["James Harden", "Norman Powell"],
    "Memphis": ["Ja Morant", "Jaren Jackson Jr"],
    "New Orleans": ["Zion Williamson", "Brandon Ingram"],
    "Sacramento": ["Domantas Sabonis", "Keegan Murray"],
    "Indiana": ["Pascal Siakam", "Bennedict Mathurin"],
    "Orlando": ["Paolo Banchero", "Franz Wagner"],
    "Houston": ["Jalen Green", "Alperen Sengun", "Fred VanVleet"],
    "Atlanta": ["Jalen Johnson", "Onyeka Okongwu", "CJ McCollum"],
    "Chicago": ["Zach LaVine", "Coby White"],
    "Charlotte": ["LaMelo Ball", "Brandon Miller"],
    "Detroit": ["Cade Cunningham", "Jalen Duren"],
    "Toronto": ["Scottie Barnes", "RJ Barrett", "Brandon Ingram"],
    "Brooklyn": ["Cam Thomas", "Dennis Schroder"],
    "San Antonio": ["Victor Wembanyama", "De'Aaron Fox", "Stephon Castle"],
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
# VEGAS ODDS CONVERSION
# ============================================================
def american_to_implied_prob(odds):
    """Convert American odds to implied probability"""
    if odds is None:
        return None
    if odds > 0:
        return 100 / (odds + 100)
    else:
        return abs(odds) / (abs(odds) + 100)

def decimal_to_implied_prob(decimal_odds):
    """Convert decimal odds to implied probability"""
    if decimal_odds is None or decimal_odds <= 1:
        return None
    return 1 / decimal_odds

def spread_to_implied_prob(spread, home=True):
    """Convert point spread to rough implied ML probability
    Rule of thumb: Each point of spread ≈ 3% win probability"""
    base = 50
    adj = spread * 3
    if home:
        return min(95, max(5, base - adj))
    else:
        return min(95, max(5, base + adj))

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
            game_id = event.get("id", "")
            
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
            
            situation = comp.get("situation", {})
            possession = situation.get("possession", "")
            last_play = situation.get("lastPlay", {}).get("text", "")
            
            # Extract odds from ESPN
            odds_data = comp.get("odds", [{}])
            vegas_odds = {}
            if odds_data:
                odds = odds_data[0] if isinstance(odds_data, list) else odds_data
                vegas_odds = {
                    "spread": odds.get("spread"),
                    "overUnder": odds.get("overUnder"),
                    "homeML": odds.get("homeTeamOdds", {}).get("moneyLine"),
                    "awayML": odds.get("awayTeamOdds", {}).get("moneyLine"),
                    "provider": odds.get("provider", {}).get("name", "Unknown")
                }
            
            games.append({
                "away": away_team, "home": home_team,
                "away_score": away_score, "home_score": home_score,
                "status": status, "period": period, "clock": clock,
                "minutes_played": minutes_played, "total_score": home_score + away_score,
                "game_id": game_id, "possession": possession, "last_play": last_play,
                "vegas_odds": vegas_odds
            })
        return games
    except Exception as e:
        st.error(f"ESPN fetch error: {e}")
        return []

@st.cache_data(ttl=15)
def fetch_play_by_play(game_id):
    if not game_id:
        return []
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary?event={game_id}"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        plays = []
        all_plays = data.get("plays", [])
        recent_plays = all_plays[-10:] if len(all_plays) > 10 else all_plays
        recent_plays.reverse()
        
        for play in recent_plays:
            play_text = play.get("text", "")
            period = play.get("period", {}).get("number", 0)
            clock = play.get("clock", {}).get("displayValue", "")
            score_value = play.get("scoreValue", 0)
            team = play.get("team", {}).get("displayName", "")
            team_abbrev = TEAM_ABBREVS.get(team, team)
            
            play_type = "neutral"
            if score_value > 0:
                play_type = "score"
            elif "MISS" in play_text.upper() or "MISSED" in play_text.upper():
                play_type = "miss"
            elif "REBOUND" in play_text.upper():
                play_type = "rebound"
            elif "TURNOVER" in play_text.upper() or "STEAL" in play_text.upper():
                play_type = "turnover"
            elif "FOUL" in play_text.upper():
                play_type = "foul"
            elif "TIMEOUT" in play_text.upper():
                play_type = "timeout"
            
            plays.append({
                "text": play_text, "period": period, "clock": clock,
                "team": team_abbrev, "score_value": score_value, "play_type": play_type
            })
        return plays
    except:
        return []

@st.cache_data(ttl=60)
def fetch_kalshi_totals():
    url = "https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXNBATOTAL&status=open&limit=200"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        markets = {}
        for m in data.get("markets", []):
            ticker = m.get("ticker", "")
            if "KXNBATOTAL-" not in ticker:
                continue
            parts = ticker.replace("KXNBATOTAL-", "")
            if len(parts) >= 13:
                date_part = parts[:7]
                teams_part = parts[7:]
                away_code = teams_part[:3]
                home_code = teams_part[3:6]
                game_key = f"{away_code}@{home_code}"
                subtitle = m.get("subtitle", "")
                threshold = None
                if "Over " in subtitle:
                    try:
                        threshold = float(subtitle.split("Over ")[1].split(" ")[0])
                    except:
                        pass
                if threshold:
                    if game_key not in markets:
                        markets[game_key] = {
                            "away_code": away_code, "home_code": home_code,
                            "date": date_part, "thresholds": [],
                            "ticker_base": f"KXNBATOTAL-{date_part}{away_code}{home_code}"
                        }
                    markets[game_key]["thresholds"].append({
                        "line": threshold, "ticker": ticker,
                        "yes_price": m.get("yes_bid", 50), "no_price": m.get("no_bid", 50)
                    })
        for game_key in markets:
            markets[game_key]["thresholds"].sort(key=lambda x: x["line"])
        return markets
    except Exception as e:
        st.error(f"Kalshi fetch error: {e}")
        return {}

@st.cache_data(ttl=60)
def fetch_kalshi_ml():
    """Fetch Kalshi ML markets to compare with Vegas
    
    KALSHI MARKET STRUCTURE FOR NBA (UPDATED):
    - Ticker format: KXNBAGAME-{DATE}{AWAY}{HOME}-{TEAM}
    - Example: KXNBAGAME-26JAN26INDATL-ATL means "Will Atlanta win?"
    - The -ATL suffix tells us which team YES represents
    - YES = the team in the suffix wins
    - NO = the other team wins
    """
    url = "https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXNBAGAME&status=open&limit=200"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        markets = {}
        for m in data.get("markets", []):
            ticker = m.get("ticker", "")
            if "KXNBAGAME-" not in ticker:
                continue
            
            # Parse ticker - format: KXNBAGAME-{DATE}{AWAY}{HOME}-{TEAM_CODE}
            # Example: KXNBAGAME-26JAN26INDATL-ATL
            parts = ticker.replace("KXNBAGAME-", "")
            
            # Split by last hyphen to get team code
            if "-" in parts:
                main_part, yes_team_code = parts.rsplit("-", 1)
            else:
                continue  # Skip malformed tickers
            
            if len(main_part) >= 13:
                date_part = main_part[:7]  # 26JAN26
                teams_part = main_part[7:]  # INDATL
                away_code = teams_part[:3]  # IND
                home_code = teams_part[3:6]  # ATL
                game_key = f"{away_code}@{home_code}"
                
                # Get prices
                yes_bid = m.get("yes_bid", 0) or 0
                yes_ask = m.get("yes_ask", 0) or 0
                no_bid = m.get("no_bid", 0) or 0
                no_ask = m.get("no_ask", 0) or 0
                last_price = m.get("last_price", 0) or 0
                
                # Best estimate of YES price
                if yes_bid > 0 and yes_ask > 0:
                    yes_price = (yes_bid + yes_ask) / 2
                elif last_price > 0:
                    yes_price = last_price
                elif yes_bid > 0:
                    yes_price = yes_bid
                else:
                    yes_price = 50
                
                # CRITICAL: YES = the team in the suffix (yes_team_code)
                # Determine which team YES represents
                if yes_team_code.upper() == home_code.upper():
                    # YES = home team wins
                    home_implied = yes_price
                    away_implied = 100 - yes_price
                else:
                    # YES = away team wins
                    away_implied = yes_price
                    home_implied = 100 - yes_price
                
                markets[game_key] = {
                    "away_code": away_code, 
                    "home_code": home_code,
                    "yes_team_code": yes_team_code,
                    "ticker": ticker,
                    "yes_bid": yes_bid,
                    "yes_ask": yes_ask,
                    "no_bid": no_bid,
                    "no_ask": no_ask,
                    "last_price": last_price,
                    "yes_price": yes_price,
                    "away_implied": away_implied,
                    "home_implied": home_implied,
                }
        return markets
    except Exception as e:
        st.error(f"Kalshi ML fetch error: {e}")
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
# NBA COURT SVG
# ============================================================
def render_nba_court(away, home, away_score, home_score, possession, period, clock, last_play=""):
    away_color = TEAM_COLORS.get(away, "#666")
    home_color = TEAM_COLORS.get(home, "#666")
    away_code = KALSHI_CODES.get(away, "AWY")
    home_code = KALSHI_CODES.get(home, "HME")
    poss_away = "visible" if possession == away else "hidden"
    poss_home = "visible" if possession == home else "hidden"
    
    svg = f'''
    <svg viewBox="0 0 500 320" style="width:100%;max-width:500px;background:#1a1a2e;border-radius:12px;">
        <rect x="20" y="20" width="460" height="240" fill="#2d4a22" stroke="#fff" stroke-width="2" rx="8"/>
        <circle cx="250" cy="140" r="40" fill="none" stroke="#fff" stroke-width="2"/>
        <circle cx="250" cy="140" r="4" fill="#fff"/>
        <line x1="250" y1="20" x2="250" y2="260" stroke="#fff" stroke-width="2"/>
        <path d="M 20 60 Q 120 140 20 220" fill="none" stroke="#fff" stroke-width="2"/>
        <line x1="20" y1="60" x2="60" y2="60" stroke="#fff" stroke-width="2"/>
        <line x1="20" y1="220" x2="60" y2="220" stroke="#fff" stroke-width="2"/>
        <rect x="20" y="80" width="80" height="120" fill="none" stroke="#fff" stroke-width="2"/>
        <circle cx="100" cy="140" r="30" fill="none" stroke="#fff" stroke-width="2"/>
        <line x1="30" y1="125" x2="30" y2="155" stroke="#fff" stroke-width="3"/>
        <circle cx="40" cy="140" r="8" fill="none" stroke="#ff6b35" stroke-width="3"/>
        <path d="M 480 60 Q 380 140 480 220" fill="none" stroke="#fff" stroke-width="2"/>
        <line x1="480" y1="60" x2="440" y2="60" stroke="#fff" stroke-width="2"/>
        <line x1="480" y1="220" x2="440" y2="220" stroke="#fff" stroke-width="2"/>
        <rect x="400" y="80" width="80" height="120" fill="none" stroke="#fff" stroke-width="2"/>
        <circle cx="400" cy="140" r="30" fill="none" stroke="#fff" stroke-width="2"/>
        <line x1="470" y1="125" x2="470" y2="155" stroke="#fff" stroke-width="3"/>
        <circle cx="460" cy="140" r="8" fill="none" stroke="#ff6b35" stroke-width="3"/>
        <rect x="60" y="270" width="80" height="35" fill="{away_color}" rx="6"/>
        <text x="100" y="293" fill="#fff" font-size="16" font-weight="bold" text-anchor="middle">{away_code}</text>
        <text x="100" y="300" fill="#fff" font-size="10" text-anchor="middle" dy="8">{away_score}</text>
        <rect x="360" y="270" width="80" height="35" fill="{home_color}" rx="6"/>
        <text x="400" y="293" fill="#fff" font-size="16" font-weight="bold" text-anchor="middle">{home_code}</text>
        <text x="400" y="300" fill="#fff" font-size="10" text-anchor="middle" dy="8">{home_score}</text>
        <circle cx="145" cy="287" r="8" fill="#ffd700" visibility="{poss_away}"/>
        <circle cx="355" cy="287" r="8" fill="#ffd700" visibility="{poss_home}"/>
        <rect x="200" y="270" width="100" height="35" fill="#0f172a" rx="6" stroke="#444"/>
        <text x="250" y="285" fill="#ff6b6b" font-size="11" font-weight="bold" text-anchor="middle">Q{period}</text>
        <text x="250" y="300" fill="#fff" font-size="12" font-weight="bold" text-anchor="middle">{clock}</text>
    </svg>
    '''
    return svg

def get_play_color(play_type):
    colors = {"score": "#22c55e", "miss": "#ef4444", "rebound": "#3b82f6", "turnover": "#f97316", "foul": "#eab308", "timeout": "#8b5cf6", "neutral": "#94a3b8"}
    return colors.get(play_type, "#94a3b8")

def get_play_icon(play_type):
    icons = {"score": "🏀", "miss": "❌", "rebound": "📥", "turnover": "🔄", "foul": "🚨", "timeout": "⏸️", "neutral": "▶️"}
    return icons.get(play_type, "▶️")

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
    if not thresholds:
        return None, None, None
    lines = [t["line"] for t in thresholds]
    if bet_type == "NO":
        above = [l for l in lines if l > projection]
        if not above:
            return None, None, None
        tight_idx = lines.index(above[0])
        rec_idx = min(tight_idx + cushion_levels, len(lines) - 1)
        rec_line = lines[rec_idx]
        cushion = rec_line - projection
        return rec_line, cushion, thresholds[rec_idx]
    else:
        below = [l for l in lines if l < projection]
        if not below:
            return None, None, None
        tight_idx = lines.index(below[-1])
        rec_idx = max(tight_idx - cushion_levels, 0)
        rec_line = lines[rec_idx]
        cushion = projection - rec_line
        return rec_line, cushion, thresholds[rec_idx]

def calc_live_edge_with_vegas(game, injuries, b2b_teams, kalshi_ml):
    """Calculate edge comparing our model to BOTH Vegas and Kalshi
    
    CRITICAL DATA FLOW:
    1. ESPN gives us Vegas odds (homeML, awayML, spread)
    2. Kalshi gives us prediction market prices
    3. We compare Vegas implied prob to Kalshi implied prob
    4. Mispricing = Vegas - Kalshi (if positive, Kalshi is underpricing)
    """
    away, home = game['away'], game['home']
    lead = game['home_score'] - game['away_score']
    
    # Our model probability (same as before)
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
    
    mins = game['minutes_played']
    live_adj = 0
    if abs(lead) >= 20: live_adj = 25 if lead > 0 else -25
    elif abs(lead) >= 15: live_adj = 18 if lead > 0 else -18
    elif abs(lead) >= 10: live_adj = 12 if lead > 0 else -12
    elif abs(lead) >= 5: live_adj = 6 if lead > 0 else -6
    
    if game['period'] == 4:
        if abs(lead) >= 10: live_adj += 15 if lead > 0 else -15
        elif abs(lead) >= 5: live_adj += 8 if lead > 0 else -8
    
    our_home_prob = max(5, min(95, base + live_adj))
    our_away_prob = 100 - our_home_prob
    
    # ============================================================
    # VEGAS IMPLIED PROBABILITY (from ESPN)
    # ESPN homeML/awayML are American odds
    # If ML not available, use spread (each point ≈ 3% probability)
    # ============================================================
    vegas = game.get('vegas_odds', {})
    vegas_home_implied = None
    vegas_away_implied = None
    vegas_spread = vegas.get('spread')
    
    # Try moneyline first (most accurate)
    if vegas.get('homeML') and vegas.get('awayML'):
        home_ml = vegas['homeML']
        away_ml = vegas['awayML']
        vegas_home_implied = american_to_implied_prob(home_ml) * 100
        vegas_away_implied = american_to_implied_prob(away_ml) * 100
        # Normalize to remove vig (they won't sum to 100)
        total = vegas_home_implied + vegas_away_implied
        if total > 0:
            vegas_home_implied = (vegas_home_implied / total) * 100
            vegas_away_implied = (vegas_away_implied / total) * 100
    elif vegas_spread is not None:
        # Fallback to spread conversion
        # Spread is from home team perspective (negative = home favored)
        # Rule of thumb: each point of spread ≈ 2.5-3% win probability
        try:
            spread_val = float(vegas_spread)
            # Negative spread = home favored
            # -5.5 spread → home is ~66% favorite
            vegas_home_implied = 50 - (spread_val * 2.8)  # 2.8% per point
            vegas_home_implied = max(10, min(90, vegas_home_implied))
            vegas_away_implied = 100 - vegas_home_implied
        except:
            pass
    
    # ============================================================
    # KALSHI IMPLIED PROBABILITY
    # Kalshi: YES = AWAY team wins, so home_implied = 100 - yes_price
    # ============================================================
    away_code = KALSHI_CODES.get(away, "XXX")
    home_code = KALSHI_CODES.get(home, "XXX")
    kalshi_key = f"{away_code}@{home_code}"
    kalshi_data = kalshi_ml.get(kalshi_key, {})
    
    kalshi_home_implied = kalshi_data.get('home_implied')  # 100 - YES price
    kalshi_away_implied = kalshi_data.get('away_implied')  # YES price
    kalshi_subtitle = kalshi_data.get('subtitle', '')
    
    # ============================================================
    # CALCULATE EDGES
    # Edge = Vegas implied - Kalshi implied
    # Positive edge means Kalshi is underpricing that outcome
    # ============================================================
    vegas_edge_home = None
    vegas_edge_away = None
    
    if vegas_home_implied and kalshi_home_implied:
        vegas_edge_home = vegas_home_implied - kalshi_home_implied
        vegas_edge_away = vegas_away_implied - kalshi_away_implied
    
    # Determine best pick based on our model
    live_pick = home if our_home_prob >= 50 else away
    model_score = int(our_home_prob) if live_pick == home else int(our_away_prob)
    
    # Find best mispricing (Vegas vs Kalshi gap)
    best_edge = 0
    best_pick = live_pick
    edge_source = "MODEL"
    
    if vegas_edge_home is not None and vegas_edge_home > 5:
        if vegas_edge_home > best_edge:
            best_edge = vegas_edge_home
            best_pick = home
            edge_source = "KALSHI"
    if vegas_edge_away is not None and vegas_edge_away > 5:
        if vegas_edge_away > best_edge:
            best_edge = vegas_edge_away
            best_pick = away
            edge_source = "KALSHI"
    
    return {
        "pick": best_pick,
        "score": model_score,
        "lead": lead,
        "our_home_prob": our_home_prob,
        "our_away_prob": our_away_prob,
        "vegas_home_implied": vegas_home_implied,
        "vegas_away_implied": vegas_away_implied,
        "kalshi_home_implied": kalshi_home_implied,
        "kalshi_away_implied": kalshi_away_implied,
        "kalshi_subtitle": kalshi_subtitle,
        "vegas_edge_home": vegas_edge_home,
        "vegas_edge_away": vegas_edge_away,
        "best_edge": best_edge,
        "edge_source": edge_source,
        "vegas_spread": vegas_spread,
        "vegas_provider": vegas.get('provider', 'Unknown')
    }

# ============================================================
# KALSHI LINKS
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
### 🆕 v7.4: MISPRICING DETECTOR

**True Edge Formula:**
```
Your Model: 65%
Kalshi Price: 52¢
EDGE: +13% → BUY
```

---

### Edge Thresholds
| Edge | Label | Action |
|------|-------|--------|
| **+10%+** | 🔥 STRONG | Best value |
| **+5-10%** | 🟢 GOOD | Worth it |
| **<5%** | ⚪ NO EDGE | Skip |

---

### ML Score Guide
| Score | Label | Action |
|-------|-------|--------|
| **70+** | 🟢 STRONG | Best edge |
| **60-69** | 🟢 GOOD | Worth it |
| **50-59** | 🟡 MODERATE | Wait |

---

### Pace Guide (Totals)
| Pace | Label | Bet |
|------|-------|-----|
| <4.2 | 🐢 SLOW | BUY NO |
| 4.2-4.8 | ⚖️ AVG | WAIT |
| >4.8 | 🔥 FAST | BUY YES |
""")
    st.divider()
    st.caption(f"v{VERSION} BIGSNAPSHOT")

# ============================================================
# FETCH DATA
# ============================================================
games = fetch_espn_games()
kalshi_totals = fetch_kalshi_totals()
kalshi_ml = fetch_kalshi_ml()
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
st.caption(f"v{VERSION} • {now.strftime('%b %d, %Y %I:%M %p ET')} • Auto-refresh: 24s • **NEW: Vegas vs Kalshi Mispricing**")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Today's Games", len(games))
c2.metric("Live Now", len(live_games))
c3.metric("Scheduled", len(scheduled_games))
c4.metric("Final", len(final_games))

# ============================================================
# 🔍 DEBUG: RAW DATA VERIFICATION (ALWAYS VISIBLE)
# ============================================================
with st.expander("🔍 DEBUG: Click to verify raw API data", expanded=False):
    st.warning("Use this to cross-check against Kalshi website!")
    
    for g in games:
        if g['status'] in ['STATUS_FINAL', 'STATUS_FULL_TIME']:
            continue
            
        away, home = g['away'], g['home']
        away_code = KALSHI_CODES.get(away, "XXX")
        home_code = KALSHI_CODES.get(home, "XXX")
        kalshi_key = f"{away_code}@{home_code}"
        kalshi_data = kalshi_ml.get(kalshi_key, {})
        vegas = g.get('vegas_odds', {})
        
        st.markdown(f"### {away} @ {home}")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**ESPN/Vegas Raw:**")
            st.code(f"""Spread: {vegas.get('spread')}
Home ML: {vegas.get('homeML')}
Away ML: {vegas.get('awayML')}
Provider: {vegas.get('provider')}""")
            
            if vegas.get('homeML') and vegas.get('awayML'):
                home_imp = american_to_implied_prob(vegas['homeML']) * 100
                away_imp = american_to_implied_prob(vegas['awayML']) * 100
                total = home_imp + away_imp
                home_imp_norm = (home_imp / total) * 100
                away_imp_norm = (away_imp / total) * 100
                st.success(f"Vegas: {home} = {home_imp_norm:.1f}% | {away} = {away_imp_norm:.1f}%")
        
        with col2:
            st.markdown("**Kalshi Raw:**")
            st.code(f"""Ticker: {kalshi_data.get('ticker', 'NOT FOUND')}
Subtitle: {kalshi_data.get('subtitle', 'N/A')}
YES bid: {kalshi_data.get('yes_bid')}¢
YES ask: {kalshi_data.get('yes_ask')}¢
NO bid: {kalshi_data.get('no_bid')}¢
Last: {kalshi_data.get('last_price')}¢""")
            
            if kalshi_data.get('away_implied'):
                st.success(f"Kalshi: {home} (NO) = {kalshi_data.get('home_implied'):.1f}% | {away} (YES) = {kalshi_data.get('away_implied'):.1f}%")
        
        st.divider()

st.divider()

# ============================================================
# 💰 MISPRICING ALERT (NEW!)
# ============================================================
st.subheader("💰 MISPRICING ALERT")
st.caption("Vegas vs Kalshi comparison • Real edges where markets disagree")

mispricings = []
for g in games:
    if g['status'] in ['STATUS_FINAL', 'STATUS_FULL_TIME']:
        continue
    edge = calc_live_edge_with_vegas(g, injuries, b2b_teams, kalshi_ml)
    
    # Only show mispricings where we have BOTH Vegas and Kalshi data
    if edge['kalshi_home_implied'] is None or edge['vegas_home_implied'] is None:
        continue
    
    # Check for significant mispricings (Vegas vs Kalshi gap)
    # Edge = Vegas implied - Kalshi implied
    # Positive = Kalshi underpricing that team
    home_gap = edge['vegas_edge_home'] if edge['vegas_edge_home'] else 0
    away_gap = edge['vegas_edge_away'] if edge['vegas_edge_away'] else 0
    
    # Find the better mispricing
    if home_gap >= 5 or away_gap >= 5:
        if home_gap >= away_gap:
            mispriced_team = g['home']
            vegas_prob = edge['vegas_home_implied']
            kalshi_prob = edge['kalshi_home_implied']
            gap = home_gap
        else:
            mispriced_team = g['away']
            vegas_prob = edge['vegas_away_implied']
            kalshi_prob = edge['kalshi_away_implied']
            gap = away_gap
        
        mispricings.append({
            'game': g,
            'team': mispriced_team,
            'vegas_prob': vegas_prob,
            'kalshi_prob': kalshi_prob,
            'gap': gap,
            'vegas_spread': edge['vegas_spread'],
            'provider': edge['vegas_provider'],
            'kalshi_subtitle': edge.get('kalshi_subtitle', '')
        })

mispricings.sort(key=lambda x: x['gap'], reverse=True)

if mispricings:
    for mp in mispricings:
        g = mp['game']
        game_key = f"{g['away']}@{g['home']}"
        
        if mp['gap'] >= 10:
            edge_color = "#ff6b6b"
            edge_label = "🔥 STRONG EDGE"
        elif mp['gap'] >= 7:
            edge_color = "#22c55e"
            edge_label = "🟢 GOOD EDGE"
        else:
            edge_color = "#eab308"
            edge_label = "🟡 EDGE"
        
        status_text = f"Q{g['period']} {g['clock']}" if g['period'] > 0 else "Scheduled"
        spread_text = f"Spread: {mp['vegas_spread']}" if mp['vegas_spread'] else ""
        
        # CRITICAL: Determine YES or NO for Kalshi
        # Kalshi NBA: YES = AWAY wins, NO = HOME wins
        if mp['team'] == g['home']:
            kalshi_action = "NO"
            kalshi_color = "#ef4444"  # Red for NO
            # For home team, kalshi price should be home_implied (100 - yes_price)
            kalshi_price_display = mp['kalshi_prob']
        else:
            kalshi_action = "YES"
            kalshi_color = "#22c55e"  # Green for YES
            # For away team, kalshi price is away_implied (yes_price)
            kalshi_price_display = mp['kalshi_prob']
        
        # Use columns for cleaner display
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**{g['away']} @ {g['home']}** • {status_text}")
        with col2:
            st.markdown(f"<span style='color:{edge_color};font-weight:bold'>{edge_label}</span>", unsafe_allow_html=True)
        
        # Main recommendation box with CLEAR YES/NO instruction
        st.markdown(f"""<div style="background:#0f172a;padding:16px;border-radius:10px;border:2px solid {edge_color};margin-bottom:8px">
<div style="color:#fff;font-size:1.4em;font-weight:bold;margin-bottom:8px">
🎯 BUY <span style="color:{kalshi_color};background:{kalshi_color}22;padding:4px 12px;border-radius:6px">{kalshi_action}</span> on Kalshi
</div>
<div style="color:#aaa;font-size:0.95em;margin-bottom:12px">{kalshi_action} = {mp['team']} wins</div>
<table style="width:100%;text-align:center;color:#fff">
<tr style="color:#888;font-size:0.85em">
<td>Vegas says {mp['team']}</td>
<td>Kalshi {kalshi_action} price</td>
<td>EDGE</td>
</tr>
<tr style="font-size:1.3em;font-weight:bold">
<td>{mp['vegas_prob']:.0f}%</td>
<td>{kalshi_price_display:.0f}¢</td>
<td style="color:{edge_color}">+{mp['gap']:.0f}%</td>
</tr>
</table>
<div style="color:#888;font-size:0.9em;margin-top:10px;padding:8px;background:#1a2744;border-radius:6px">
💡 Vegas thinks {mp['team']} has {mp['vegas_prob']:.0f}% chance, but Kalshi only prices it at {kalshi_price_display:.0f}¢
</div>
<div style="color:#666;font-size:0.85em;margin-top:8px;text-align:center">{spread_text}</div>
</div>""", unsafe_allow_html=True)
        
        bc1, bc2, bc3 = st.columns(3)
        with bc1:
            st.link_button(f"🎯 BUY {kalshi_action} ({mp['team']})", get_kalshi_ml_link(g['away'], g['home']), use_container_width=True)
        with bc2:
            st.link_button("📊 SPREAD", get_kalshi_spread_link(g['away'], g['home']), use_container_width=True)
        with bc3:
            if st.button("➕ Track", key=f"mp_{game_key}"):
                add_position(game_key, f"{kalshi_action} ({mp['team']})", "ML", "-", get_kalshi_ml_link(g['away'], g['home']))
                st.rerun()
else:
    st.info("🔍 No significant mispricings detected (need 5%+ gap between Vegas & Kalshi)")

st.divider()

# ============================================================
# 🔍 DEBUG: RAW DATA VERIFICATION
# ============================================================
with st.expander("🔍 DEBUG: Raw Data Verification (Click to verify data accuracy)", expanded=False):
    st.caption("Use this to verify the app is pulling correct data from APIs")
    
    for g in games[:5]:  # Show first 5 games
        away, home = g['away'], g['home']
        away_code = KALSHI_CODES.get(away, "XXX")
        home_code = KALSHI_CODES.get(home, "XXX")
        kalshi_key = f"{away_code}@{home_code}"
        kalshi_data = kalshi_ml.get(kalshi_key, {})
        vegas = g.get('vegas_odds', {})
        
        st.markdown(f"### {away} @ {home}")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**ESPN/Vegas Raw Data:**")
            st.write(f"- Spread: {vegas.get('spread')}")
            st.write(f"- Over/Under: {vegas.get('overUnder')}")
            st.write(f"- Home ML: {vegas.get('homeML')}")
            st.write(f"- Away ML: {vegas.get('awayML')}")
            st.write(f"- Provider: {vegas.get('provider')}")
            if vegas.get('homeML'):
                home_imp = american_to_implied_prob(vegas['homeML']) * 100
                away_imp = american_to_implied_prob(vegas['awayML']) * 100
                st.write(f"- **Vegas Home Implied: {home_imp:.1f}%**")
                st.write(f"- **Vegas Away Implied: {away_imp:.1f}%**")
        
        with col2:
            st.markdown("**Kalshi Raw Data:**")
            st.write(f"- Ticker: {kalshi_data.get('ticker', 'NOT FOUND')}")
            st.write(f"- Subtitle: {kalshi_data.get('subtitle', 'N/A')}")
            st.write(f"- YES bid: {kalshi_data.get('yes_bid')}¢")
            st.write(f"- YES ask: {kalshi_data.get('yes_ask')}¢")
            st.write(f"- NO bid: {kalshi_data.get('no_bid')}¢")
            st.write(f"- Last price: {kalshi_data.get('last_price')}¢")
            st.write(f"- **Away Implied ({away}): {kalshi_data.get('away_implied', 'N/A')}%**")
            st.write(f"- **Home Implied ({home}): {kalshi_data.get('home_implied', 'N/A')}%**")
        
        st.markdown("---")

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
    st.caption("Real-time ML edges with Vegas comparison • Updates every 24 seconds")
    
    for g in sorted(live_games, key=lambda x: calc_live_edge_with_vegas(x, injuries, b2b_teams, kalshi_ml)['score'], reverse=True):
        edge = calc_live_edge_with_vegas(g, injuries, b2b_teams, kalshi_ml)
        mins = g['minutes_played']
        game_key = f"{g['away']}@{g['home']}"
        
        if mins < 6:
            status_label, status_color = "⏳ TOO EARLY", "#888"
        elif abs(edge['lead']) < 3:
            status_label, status_color = "⚖️ TOO CLOSE", "#ffa500"
        elif edge['best_edge'] >= 10:
            status_label, status_color = f"🔥 +{edge['best_edge']:.0f}% EDGE", "#ff6b6b"
        elif edge['best_edge'] >= 5:
            status_label, status_color = f"🟢 +{edge['best_edge']:.0f}% EDGE", "#22c55e"
        elif edge['score'] >= 70:
            status_label, status_color = f"🟢 STRONG {edge['score']}", "#22c55e"
        elif edge['score'] >= 60:
            status_label, status_color = f"🟢 GOOD {edge['score']}", "#22c55e"
        else:
            status_label, status_color = f"🟡 {edge['score']}", "#eab308"
        
        lead_display = f"+{edge['lead']}" if edge['lead'] > 0 else str(edge['lead'])
        leader = g['home'] if edge['lead'] > 0 else g['away'] if edge['lead'] < 0 else "TIED"
        
        # Build odds comparison text
        odds_text = ""
        if edge['vegas_home_implied'] and edge['kalshi_home_implied']:
            odds_text = f"Vegas: {g['home']} {edge['vegas_home_implied']:.0f}% | Kalshi: {edge['kalshi_home_implied']:.0f}¢"
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1e1e2e 0%, #2a2a3e 100%); border-radius: 12px; padding: 16px; margin-bottom: 8px; border: 1px solid #444;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="color: #fff; font-size: 1.2em; font-weight: 600;">{g['away']} @ {g['home']}</span>
                <span style="color: {status_color}; font-weight: 600;">{status_label}</span>
            </div>
            <div style="color: #aaa; font-size: 0.9em;">
                Lead: <strong style="color: #fff;">{leader}</strong> ({lead_display}) • {mins:.0f} min played
            </div>
            <div style="color: #666; font-size: 0.85em; margin-top: 4px;">{odds_text}</div>
        </div>
        """, unsafe_allow_html=True)
        
        court_col, pbp_col = st.columns([1, 1])
        
        with court_col:
            court_svg = render_nba_court(g['away'], g['home'], g['away_score'], g['home_score'],
                g.get('possession', ''), g['period'], g['clock'], g.get('last_play', ''))
            st.markdown(court_svg, unsafe_allow_html=True)
        
        with pbp_col:
            st.markdown("**📋 LAST 10 PLAYS**")
            plays = fetch_play_by_play(g.get('game_id', ''))
            if plays:
                for play in plays[:10]:
                    icon = get_play_icon(play['play_type'])
                    color = get_play_color(play['play_type'])
                    play_text = play['text'][:42] + "..." if len(play['text']) > 45 else play['text']
                    st.markdown(f"""<div style="background:#0f172a;padding:6px 10px;margin-bottom:4px;border-radius:6px;border-left:3px solid {color};font-size:0.85em">
                        <span style="color:#888">Q{play['period']} {play['clock']}</span>
                        <span style="color:{color};margin-left:8px">{icon}</span>
                        <span style="color:#fff;margin-left:4px">{play_text}</span>
                    </div>""", unsafe_allow_html=True)
            else:
                st.caption("Play-by-play loading...")
        
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
# 🎯 CUSHION SCANNER
# ============================================================
st.subheader("🎯 CUSHION SCANNER")
st.caption("Totals recommendations with built-in safety cushion")

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
        'game': g, 'away': g['away'], 'home': g['home'],
        'projection': projection, 'pace_val': pace_val,
        'pace_label': pace_label, 'pace_color': pace_color,
        'bet_type': bet_type, 'rec_line': rec_line,
        'cushion': cushion, 'bracket_data': bracket_data,
        'thresholds': thresholds
    })

cushion_results.sort(key=lambda x: (x['cushion'] or 0), reverse=True)

if cushion_results:
    for r in cushion_results:
        g = r['game']
        game_key = f"{r['away']}@{r['home']}"
        if r['bet_type'] and r['rec_line'] and r['cushion']:
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
# 🎯 PRE-GAME ALIGNMENT WITH VEGAS
# ============================================================
if scheduled_games:
    with st.expander("🎯 PRE-GAME ALIGNMENT (With Vegas Comparison)", expanded=True):
        st.caption("⚠️ Pre-game picks with Vegas odds comparison")
        for g in scheduled_games:
            away, home = g['away'], g['home']
            game_key = f"{away}@{home}"
            edge = calc_live_edge_with_vegas(g, injuries, b2b_teams, kalshi_ml)
            
            pick = home if edge['our_home_prob'] >= 50 else away
            score = int(edge['our_home_prob']) if pick == home else int(edge['our_away_prob'])
            
            # Check for mispricing
            mispricing = ""
            mispricing_color = "#888"
            if edge['kalshi_home_implied'] and edge['vegas_home_implied']:
                if pick == home:
                    gap = edge['vegas_home_implied'] - edge['kalshi_home_implied']
                else:
                    gap = edge['vegas_away_implied'] - edge['kalshi_away_implied']
                if gap >= 5:
                    mispricing = f"+{gap:.0f}% vs Kalshi"
                    mispricing_color = "#22c55e" if gap >= 7 else "#eab308"
            
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
            
            vegas_text = ""
            if edge['vegas_spread']:
                vegas_text = f"Vegas: {edge['vegas_spread']} | "
            if edge['vegas_home_implied']:
                vegas_text += f"{home} {edge['vegas_home_implied']:.0f}%"
            
            st.markdown(f"""
            <div style="background: #1e1e2e; border-radius: 10px; padding: 14px; margin-bottom: 10px; border-left: 4px solid {border_color};">
                <div style="display: flex; justify-content: space-between;">
                    <span style="color: #fff; font-weight: 600;">{b2b_away}{away} @ {home}{b2b_home}</span>
                    <span style="color: {score_color}; font-weight: 600;">{score}% → {pick}</span>
                </div>
                <div style="color: #666; font-size: 0.85em; margin-top: 4px;">{vegas_text}</div>
                <div style="color: {mispricing_color}; font-size: 0.9em; margin-top: 2px;">{mispricing}</div>
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

### 🆕 NEW IN v7.4: VEGAS MISPRICING DETECTOR
The app now compares Vegas odds (from ESPN) to Kalshi prices to find real mispricings:

```
Vegas Implied: 65% (from spread/ML)
Kalshi Price: 52¢ (implied 52%)
MISPRICING: +13% → BUY YES on Kalshi
```

**Edge Thresholds:**
| Gap | Label | Action |
|-----|-------|--------|
| +10%+ | 🔥 STRONG | Best value |
| +5-10% | 🟢 GOOD | Worth it |
| <5% | ⚪ NO EDGE | Skip |

---

### 💰 MISPRICING ALERT
Shows games where Vegas and Kalshi disagree by 5%+. This is where the real edge lives.

### 🔴 LIVE EDGE MONITOR (ML Picks)
Now shows both model score AND Vegas comparison.

### 🎯 CUSHION SCANNER (Totals)
Same pace-based system with safety cushions.

---

### ⚠️ IMPORTANT
- Mispricings are the real edge (market inefficiency)
- Model score alone doesn't guarantee edge
- Wait for 5%+ gap before betting
- Not financial advice

**Stay small. Stay quiet. Win.**
""")

st.caption(f"⚠️ Educational only. Not financial advice. BigSnapshot v{VERSION}")
st.caption("Stay small. Stay quiet. Win.")
