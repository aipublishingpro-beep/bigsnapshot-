import streamlit as st
from streamlit_autorefresh import st_autorefresh
import streamlit.components.v1 as components
import time as _time

st.set_page_config(page_title="BigSnapshot NBA Edge Finder", page_icon="🏀", layout="wide")

from auth import require_auth
require_auth()

st_autorefresh(interval=24000, key="datarefresh")

import uuid
import requests as req_ga

def send_ga4_event(page_title, page_path):
    try:
        url = "https://www.google-analytics.com/mp/collect?measurement_id=G-NQKY5VQ376&api_secret=n4oBJjH7RXi0dA7aQo2CZA"
        payload = {"client_id": str(uuid.uuid4()), "events": [{"name": "page_view", "params": {"page_title": page_title, "page_location": "https://bigsnapshot.streamlit.app" + page_path}}]}
        req_ga.post(url, json=payload, timeout=2)
    except: pass

send_ga4_event("BigSnapshot NBA Edge Finder", "/NBA")

import requests
from datetime import datetime, timedelta
import pytz

eastern = pytz.timezone("US/Eastern")
now = datetime.now(eastern)

VERSION = "12.0"
LEAGUE_AVG_TOTAL = 225
THRESHOLDS = [210.5, 215.5, 220.5, 225.5, 230.5, 235.5, 240.5, 245.5]

if 'positions' not in st.session_state:
    st.session_state.positions = []

TEAM_ABBREVS = {"Atlanta Hawks": "Atlanta", "Boston Celtics": "Boston", "Brooklyn Nets": "Brooklyn", "Charlotte Hornets": "Charlotte", "Chicago Bulls": "Chicago", "Cleveland Cavaliers": "Cleveland", "Dallas Mavericks": "Dallas", "Denver Nuggets": "Denver", "Detroit Pistons": "Detroit", "Golden State Warriors": "Golden State", "Houston Rockets": "Houston", "Indiana Pacers": "Indiana", "LA Clippers": "LA Clippers", "Los Angeles Clippers": "LA Clippers", "LA Lakers": "LA Lakers", "Los Angeles Lakers": "LA Lakers", "Memphis Grizzlies": "Memphis", "Miami Heat": "Miami", "Milwaukee Bucks": "Milwaukee", "Minnesota Timberwolves": "Minnesota", "New Orleans Pelicans": "New Orleans", "New York Knicks": "New York", "Oklahoma City Thunder": "Oklahoma City", "Orlando Magic": "Orlando", "Philadelphia 76ers": "Philadelphia", "Phoenix Suns": "Phoenix", "Portland Trail Blazers": "Portland", "Sacramento Kings": "Sacramento", "San Antonio Spurs": "San Antonio", "Toronto Raptors": "Toronto", "Utah Jazz": "Utah", "Washington Wizards": "Washington", "MIL": "Milwaukee", "PHI": "Philadelphia", "BOS": "Boston", "NYK": "New York", "CLE": "Cleveland", "ORL": "Orlando", "ATL": "Atlanta", "MIA": "Miami", "CHI": "Chicago", "BKN": "Brooklyn", "TOR": "Toronto", "IND": "Indiana", "DET": "Detroit", "CHA": "Charlotte", "WAS": "Washington", "OKC": "Oklahoma City", "HOU": "Houston", "MEM": "Memphis", "DAL": "Dallas", "DEN": "Denver", "MIN": "Minnesota", "LAC": "LA Clippers", "LAL": "LA Lakers", "SAC": "Sacramento", "PHX": "Phoenix", "GSW": "Golden State", "POR": "Portland", "UTA": "Utah", "SAS": "San Antonio", "NOP": "New Orleans"}

KALSHI_CODES = {"Atlanta": "ATL", "Boston": "BOS", "Brooklyn": "BKN", "Charlotte": "CHA", "Chicago": "CHI", "Cleveland": "CLE", "Dallas": "DAL", "Denver": "DEN", "Detroit": "DET", "Golden State": "GSW", "Houston": "HOU", "Indiana": "IND", "LA Clippers": "LAC", "LA Lakers": "LAL", "Memphis": "MEM", "Miami": "MIA", "Milwaukee": "MIL", "Minnesota": "MIN", "New Orleans": "NOP", "New York": "NYK", "Oklahoma City": "OKC", "Orlando": "ORL", "Philadelphia": "PHI", "Phoenix": "PHX", "Portland": "POR", "Sacramento": "SAC", "San Antonio": "SAS", "Toronto": "TOR", "Utah": "UTA", "Washington": "WAS"}

TEAM_COLORS = {"Atlanta": "#E03A3E", "Boston": "#007A33", "Brooklyn": "#000000", "Charlotte": "#1D1160", "Chicago": "#CE1141", "Cleveland": "#860038", "Dallas": "#00538C", "Denver": "#0E2240", "Detroit": "#C8102E", "Golden State": "#1D428A", "Houston": "#CE1141", "Indiana": "#002D62", "LA Clippers": "#C8102E", "LA Lakers": "#552583", "Memphis": "#5D76A9", "Miami": "#98002E", "Milwaukee": "#00471B", "Minnesota": "#0C2340", "New Orleans": "#0C2340", "New York": "#006BB6", "Oklahoma City": "#007AC1", "Orlando": "#0077C0", "Philadelphia": "#006BB6", "Phoenix": "#1D1160", "Portland": "#E03A3E", "Sacramento": "#5A2D81", "San Antonio": "#C4CED4", "Toronto": "#CE1141", "Utah": "#002B5C", "Washington": "#002B5C"}

TEAM_STATS = {"Oklahoma City": {"net": 12.0, "pace": 98.8}, "Cleveland": {"net": 10.5, "pace": 97.2}, "Boston": {"net": 9.5, "pace": 99.8}, "Denver": {"net": 7.8, "pace": 98.5}, "New York": {"net": 5.5, "pace": 97.5}, "Houston": {"net": 5.2, "pace": 99.5}, "LA Lakers": {"net": 4.5, "pace": 98.5}, "Phoenix": {"net": 4.0, "pace": 98.2}, "Minnesota": {"net": 4.0, "pace": 98.2}, "Golden State": {"net": 3.5, "pace": 100.2}, "Dallas": {"net": 3.0, "pace": 99.0}, "Milwaukee": {"net": 2.5, "pace": 98.8}, "Miami": {"net": 2.0, "pace": 97.2}, "Philadelphia": {"net": 1.5, "pace": 97.5}, "Sacramento": {"net": 1.0, "pace": 100.5}, "Orlando": {"net": 0.5, "pace": 96.8}, "LA Clippers": {"net": 0.0, "pace": 97.8}, "Indiana": {"net": -0.5, "pace": 102.5}, "Memphis": {"net": -1.0, "pace": 99.8}, "San Antonio": {"net": -1.5, "pace": 99.2}, "Detroit": {"net": -2.0, "pace": 99.5}, "Atlanta": {"net": -2.5, "pace": 100.5}, "Chicago": {"net": -3.0, "pace": 98.8}, "Toronto": {"net": -3.5, "pace": 97.8}, "Brooklyn": {"net": -5.0, "pace": 98.2}, "Portland": {"net": -5.5, "pace": 98.8}, "Charlotte": {"net": -6.5, "pace": 99.5}, "Utah": {"net": -7.0, "pace": 98.5}, "New Orleans": {"net": -8.0, "pace": 99.0}, "Washington": {"net": -10.0, "pace": 100.8}}

STAR_PLAYERS = {"Boston": ["Jayson Tatum", "Jaylen Brown"], "Cleveland": ["Donovan Mitchell", "Darius Garland"], "Oklahoma City": ["Shai Gilgeous-Alexander", "Chet Holmgren"], "New York": ["Jalen Brunson", "Karl-Anthony Towns"], "Milwaukee": ["Giannis Antetokounmpo", "Damian Lillard"], "Denver": ["Nikola Jokic", "Jamal Murray"], "Minnesota": ["Anthony Edwards", "Rudy Gobert"], "Dallas": ["Luka Doncic", "Kyrie Irving"], "Phoenix": ["Kevin Durant", "Devin Booker"], "LA Lakers": ["LeBron James", "Anthony Davis"], "Golden State": ["Stephen Curry"], "Miami": ["Bam Adebayo", "Tyler Herro"], "Philadelphia": ["Joel Embiid", "Tyrese Maxey"], "Memphis": ["Ja Morant"], "New Orleans": ["Zion Williamson"], "Sacramento": ["Domantas Sabonis", "De'Aaron Fox"], "Indiana": ["Tyrese Haliburton", "Pascal Siakam"], "Orlando": ["Paolo Banchero", "Franz Wagner"], "Houston": ["Jalen Green", "Alperen Sengun"], "Atlanta": ["Trae Young"], "Charlotte": ["LaMelo Ball"], "Detroit": ["Cade Cunningham"], "San Antonio": ["Victor Wembanyama"], "LA Clippers": ["James Harden", "Kawhi Leonard"]}

STAR_TIERS = {"Nikola Jokic": 3, "Shai Gilgeous-Alexander": 3, "Giannis Antetokounmpo": 3, "Luka Doncic": 3, "Joel Embiid": 3, "Jayson Tatum": 3, "LeBron James": 3, "Stephen Curry": 3, "Kevin Durant": 3, "Anthony Edwards": 3, "Donovan Mitchell": 2, "Jaylen Brown": 2, "Damian Lillard": 2, "Anthony Davis": 2, "Kyrie Irving": 2, "Devin Booker": 2, "Ja Morant": 2, "Trae Young": 2, "Tyrese Haliburton": 2, "De'Aaron Fox": 2, "Jalen Brunson": 2, "Paolo Banchero": 2, "Victor Wembanyama": 2, "LaMelo Ball": 2, "Cade Cunningham": 2, "Tyrese Maxey": 2}

PLAYER_TEAMS = {"Jalen Brunson": "New York", "Karl-Anthony Towns": "New York", "OG Anunoby": "New York", "Mikal Bridges": "New York", "Josh Hart": "New York", "Miles McBride": "New York", "Donte DiVincenzo": "New York", "Mitchell Robinson": "New York", "Precious Achiuwa": "New York", "Landry Shamet": "New York", "Domantas Sabonis": "Sacramento", "De'Aaron Fox": "Sacramento", "Keegan Murray": "Sacramento", "Malik Monk": "Sacramento", "DeMar DeRozan": "Sacramento", "Kevin Huerter": "Sacramento", "Trey Lyles": "Sacramento", "Keon Ellis": "Sacramento", "Russell Westbrook": "Sacramento", "Dylan Cardwell": "Sacramento", "Jayson Tatum": "Boston", "Jaylen Brown": "Boston", "Derrick White": "Boston", "Jrue Holiday": "Boston", "Kristaps Porzingis": "Boston", "Al Horford": "Boston", "Payton Pritchard": "Boston", "Sam Hauser": "Boston", "Donovan Mitchell": "Cleveland", "Darius Garland": "Cleveland", "Evan Mobley": "Cleveland", "Jarrett Allen": "Cleveland", "Max Strus": "Cleveland", "Caris LeVert": "Cleveland", "Shai Gilgeous-Alexander": "Oklahoma City", "Chet Holmgren": "Oklahoma City", "Jalen Williams": "Oklahoma City", "Lu Dort": "Oklahoma City", "Isaiah Hartenstein": "Oklahoma City", "Alex Caruso": "Oklahoma City", "Giannis Antetokounmpo": "Milwaukee", "Damian Lillard": "Milwaukee", "Khris Middleton": "Milwaukee", "Brook Lopez": "Milwaukee", "Bobby Portis": "Milwaukee", "Pat Connaughton": "Milwaukee", "Nikola Jokic": "Denver", "Jamal Murray": "Denver", "Michael Porter Jr.": "Denver", "Aaron Gordon": "Denver", "Christian Braun": "Denver", "Luka Doncic": "Dallas", "Kyrie Irving": "Dallas", "PJ Washington": "Dallas", "Daniel Gafford": "Dallas", "Dereck Lively II": "Dallas", "Klay Thompson": "Dallas", "Anthony Edwards": "Minnesota", "Rudy Gobert": "Minnesota", "Julius Randle": "Minnesota", "Jaden McDaniels": "Minnesota", "Mike Conley": "Minnesota", "Naz Reid": "Minnesota", "Kevin Durant": "Phoenix", "Devin Booker": "Phoenix", "Bradley Beal": "Phoenix", "Jusuf Nurkic": "Phoenix", "Grayson Allen": "Phoenix", "LeBron James": "LA Lakers", "Anthony Davis": "LA Lakers", "Austin Reaves": "LA Lakers", "D'Angelo Russell": "LA Lakers", "Rui Hachimura": "LA Lakers", "Stephen Curry": "Golden State", "Draymond Green": "Golden State", "Andrew Wiggins": "Golden State", "Jonathan Kuminga": "Golden State", "Brandin Podziemski": "Golden State", "Bam Adebayo": "Miami", "Tyler Herro": "Miami", "Jimmy Butler": "Miami", "Terry Rozier": "Miami", "Jaime Jaquez Jr.": "Miami", "Joel Embiid": "Philadelphia", "Tyrese Maxey": "Philadelphia", "Paul George": "Philadelphia", "Caleb Martin": "Philadelphia", "Kelly Oubre Jr.": "Philadelphia", "Ja Morant": "Memphis", "Jaren Jackson Jr.": "Memphis", "Desmond Bane": "Memphis", "Marcus Smart": "Memphis", "Zion Williamson": "New Orleans", "Brandon Ingram": "New Orleans", "CJ McCollum": "New Orleans", "Trey Murphy III": "New Orleans", "Trae Young": "Atlanta", "Jalen Johnson": "Atlanta", "De'Andre Hunter": "Atlanta", "Clint Capela": "Atlanta", "LaMelo Ball": "Charlotte", "Miles Bridges": "Charlotte", "Brandon Miller": "Charlotte", "Mark Williams": "Charlotte", "Cade Cunningham": "Detroit", "Jaden Ivey": "Detroit", "Ausar Thompson": "Detroit", "Jalen Duren": "Detroit", "Victor Wembanyama": "San Antonio", "Devin Vassell": "San Antonio", "Jeremy Sochan": "San Antonio", "Keldon Johnson": "San Antonio", "James Harden": "LA Clippers", "Kawhi Leonard": "LA Clippers", "Norman Powell": "LA Clippers", "Ivica Zubac": "LA Clippers", "Tyrese Haliburton": "Indiana", "Pascal Siakam": "Indiana", "Myles Turner": "Indiana", "Aaron Nesmith": "Indiana", "Benedict Mathurin": "Indiana", "Paolo Banchero": "Orlando", "Franz Wagner": "Orlando", "Jalen Suggs": "Orlando", "Wendell Carter Jr.": "Orlando", "Moritz Wagner": "Orlando", "Jalen Green": "Houston", "Alperen Sengun": "Houston", "Jabari Smith Jr.": "Houston", "Fred VanVleet": "Houston", "Dillon Brooks": "Houston", "Anfernee Simons": "Portland", "Scoot Henderson": "Portland", "Jerami Grant": "Portland", "Deandre Ayton": "Portland", "Lauri Markkanen": "Utah", "Collin Sexton": "Utah", "Jordan Clarkson": "Utah", "John Collins": "Utah", "Kyle Kuzma": "Washington", "Jordan Poole": "Washington", "Bilal Coulibaly": "Washington", "Cameron Johnson": "Brooklyn", "Mikal Bridges": "Brooklyn", "Cam Thomas": "Brooklyn", "Nic Claxton": "Brooklyn", "Scottie Barnes": "Toronto", "RJ Barrett": "Toronto", "Immanuel Quickley": "Toronto", "Jakob Poeltl": "Toronto"}

def american_to_implied_prob(odds):
    if odds is None: return None
    if odds > 0: return 100 / (odds + 100)
    else: return abs(odds) / (abs(odds) + 100)

def speak_play(text):
    clean_text = text.replace("'", "").replace('"', '').replace('\n', ' ')[:100]
    js = f'''<script>if(!window.lastSpoken||window.lastSpoken!=="{clean_text}"){{window.lastSpoken="{clean_text}";var u=new SpeechSynthesisUtterance("{clean_text}");u.rate=1.1;window.speechSynthesis.speak(u);}}</script>'''
    components.html(js, height=0)

@st.cache_data(ttl=30)
def fetch_espn_games():
    today = datetime.now(eastern).strftime('%Y%m%d')
    url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates=" + today
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        games = []
        for event in data.get("events", []):
            comp = event.get("competitions", [{}])[0]
            competitors = comp.get("competitors", [])
            if len(competitors) < 2: continue
            home_team, away_team, home_score, away_score = None, None, 0, 0
            home_record, away_record = "", ""
            for c in competitors:
                full_name = c.get("team", {}).get("displayName", "")
                team_name = TEAM_ABBREVS.get(full_name, full_name)
                score = int(c.get("score", 0) or 0)
                records = c.get("records", [])
                record = records[0].get("summary", "") if records else ""
                if c.get("homeAway") == "home":
                    home_team, home_score, home_record = team_name, score, record
                else:
                    away_team, away_score, away_record = team_name, score, record
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
                                minutes_played = completed_quarters + (12 - int(clock.split(":")[0]))
                            else:
                                minutes_played = completed_quarters + 12
                        except:
                            minutes_played = completed_quarters + 12
                    else:
                        minutes_played = completed_quarters
                else:
                    minutes_played = 48 + (period - 4) * 5
            game_date = event.get("date", "")
            game_time_str, game_datetime_str = "", ""
            if game_date:
                try:
                    game_dt = datetime.fromisoformat(game_date.replace("Z", "+00:00")).astimezone(eastern)
                    game_time_str = game_dt.strftime("%I:%M %p ET")
                    game_datetime_str = game_dt.strftime("%b %d, %I:%M %p ET")
                except: pass
            odds_data = comp.get("odds", [])
            vegas_odds = {}
            if odds_data and len(odds_data) > 0:
                odds = odds_data[0]
                vegas_odds = {"spread": odds.get("spread"), "overUnder": odds.get("overUnder"), "homeML": odds.get("homeTeamOdds", {}).get("moneyLine"), "awayML": odds.get("awayTeamOdds", {}).get("moneyLine")}
            games.append({"away": away_team, "home": home_team, "away_score": away_score, "home_score": home_score, "away_record": away_record, "home_record": home_record, "status": status, "period": period, "clock": clock, "minutes_played": minutes_played, "total_score": home_score + away_score, "game_id": game_id, "vegas_odds": vegas_odds, "game_time": game_time_str, "game_datetime": game_datetime_str})
        return games
    except Exception as e:
        st.error("ESPN fetch error: " + str(e))
        return []

def fetch_kalshi_ml(force_refresh=False):
    cache_key = "nba_kalshi_data"
    time_key = "nba_kalshi_time"
    if not force_refresh and cache_key in st.session_state and time_key in st.session_state:
        age = _time.time() - st.session_state[time_key]
        if age < 15:
            return st.session_state[cache_key]
    url = "https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXNBAGAME&status=open&limit=200"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        markets = {}
        for m in data.get("markets", []):
            ticker = m.get("ticker", "")
            if "KXNBAGAME-" not in ticker: continue
            parts = ticker.replace("KXNBAGAME-", "")
            if "-" not in parts: continue
            main_part, yes_team_code = parts.rsplit("-", 1)
            if len(main_part) < 13: continue
            teams_part = main_part[7:]
            away_code, home_code = teams_part[:3], teams_part[3:6]
            game_key = away_code + "@" + home_code
            yes_bid = m.get("yes_bid", 0) or 0
            yes_ask = m.get("yes_ask", 0) or 0
            last_price = m.get("last_price", 0) or 0
            yes_price = yes_ask or last_price or yes_bid
            if yes_price == 0:
                continue
            yes_team_code = yes_team_code.upper()
            if yes_team_code == home_code.upper():
                home_implied, away_implied = yes_price, 100 - yes_price
            else:
                away_implied, home_implied = yes_price, 100 - yes_price
            if game_key not in markets:
                markets[game_key] = {"away_code": away_code, "home_code": home_code, "yes_team_code": yes_team_code, "ticker": ticker, "yes_bid": yes_bid, "yes_ask": yes_ask, "yes_price": yes_price, "away_implied": away_implied, "home_implied": home_implied}
        st.session_state[cache_key] = markets
        st.session_state[time_key] = _time.time()
        return markets
    except Exception as e:
        st.error("Kalshi ML fetch error: " + str(e))
        return st.session_state.get(cache_key, {})

def fetch_kalshi_spreads(force_refresh=False):
    cache_key = "nba_kalshi_spread_data"
    time_key = "nba_kalshi_spread_time"
    if not force_refresh and cache_key in st.session_state and time_key in st.session_state:
        age = _time.time() - st.session_state[time_key]
        if age < 15:
            return st.session_state[cache_key]
    url = "https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXNBASPREAD&status=open&limit=200"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        spreads = {}
        for m in data.get("markets", []):
            ticker = m.get("ticker", "")
            yes_bid = m.get("yes_bid", 0) or 0
            yes_ask = m.get("yes_ask", 0) or 0
            last_price = m.get("last_price", 0) or 0
            if "KXNBASPREAD-" in ticker:
                parts = ticker.replace("KXNBASPREAD-", "")
                if len(parts) >= 13:
                    date_part = parts[:7]
                    rest = parts[7:]
                    if "-" in rest:
                        game_teams, spread_info = rest.split("-", 1)
                        if len(game_teams) >= 6:
                            away_code = game_teams[:3].upper()
                            home_code = game_teams[3:6].upper()
                            game_key = f"{away_code}@{home_code}"
                            spread_line, spread_team = None, None
                            if "-" in spread_info:
                                sp_parts = spread_info.rsplit("-", 1)
                                if len(sp_parts) == 2:
                                    spread_team = sp_parts[0].upper()
                                    try: spread_line = f"-{sp_parts[1]}"
                                    except: pass
                            elif "+" in spread_info:
                                sp_parts = spread_info.split("+", 1)
                                if len(sp_parts) == 2:
                                    spread_team = sp_parts[0].upper()
                                    try: spread_line = f"+{sp_parts[1]}"
                                    except: pass
                            if spread_line and spread_team:
                                sp_price = yes_ask or last_price or yes_bid
                                if sp_price == 0:
                                    continue
                                if game_key not in spreads:
                                    spreads[game_key] = []
                                spreads[game_key].append({"line": spread_line, "team_code": spread_team, "ticker": ticker, "yes_bid": yes_bid, "yes_ask": yes_ask, "yes_price": sp_price})
        st.session_state[cache_key] = spreads
        st.session_state[time_key] = _time.time()
        return spreads
    except:
        return st.session_state.get(cache_key, {})

def get_kalshi_freshness():
    time_key = "nba_kalshi_time"
    if time_key not in st.session_state:
        return "🔴 No Data", 999
    age = _time.time() - st.session_state[time_key]
    if age < 15:
        return "🟢 Live", age
    elif age < 60:
        return "🟡 " + str(int(age)) + "s ago", age
    else:
        return "🔴 Stale (" + str(int(age)) + "s)", age

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
                name = player.get("athlete", {}).get("displayName", "")
                status = player.get("status", "")
                if name: injuries[team_key].append({"name": name, "status": status})
        return injuries
    except: return {}

@st.cache_data(ttl=300)
def fetch_yesterday_teams():
    yesterday = (datetime.now(eastern) - timedelta(days=1)).strftime('%Y%m%d')
    url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates=" + yesterday
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        teams_played = set()
        for event in data.get("events", []):
            comp = event.get("competitions", [{}])[0]
            for c in comp.get("competitors", []):
                full_name = c.get("team", {}).get("displayName", "")
                teams_played.add(TEAM_ABBREVS.get(full_name, full_name))
        return teams_played
    except: return set()

@st.cache_data(ttl=30)
def fetch_plays(game_id):
    if not game_id: return []
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary?event={game_id}"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        plays = []
        for p in data.get("plays", [])[-15:]:
            plays.append({"text": p.get("text", ""), "period": p.get("period", {}).get("number", 0), "clock": p.get("clock", {}).get("displayValue", ""), "score_value": p.get("scoreValue", 0), "play_type": p.get("type", {}).get("text", "")})
        return plays[-10:]
    except: return []

def get_team_from_play(play_text, away, home):
    if not play_text: return None
    play_text_lower = play_text.lower()
    for player, team in PLAYER_TEAMS.items():
        if player.lower() in play_text_lower:
            if team == away or team == home:
                return team
    return None

def infer_possession(plays, away, home):
    if not plays: return None, None
    last_play = plays[-1]
    play_text = (last_play.get("text", "") or "").lower()
    acting_team = get_team_from_play(last_play.get("text", ""), away, home)
    if not acting_team: return None, None
    other_team = home if acting_team == away else away
    if last_play.get("score_value", 0) > 0 or "makes" in play_text:
        return other_team, f"→ {KALSHI_CODES.get(other_team, other_team[:3].upper())}"
    if "defensive rebound" in play_text:
        return acting_team, f"🏀 {KALSHI_CODES.get(acting_team, acting_team[:3].upper())}"
    if "offensive rebound" in play_text:
        return acting_team, f"🏀 {KALSHI_CODES.get(acting_team, acting_team[:3].upper())}"
    if "turnover" in play_text or "steal" in play_text:
        return other_team, f"→ {KALSHI_CODES.get(other_team, other_team[:3].upper())}"
    if "misses" in play_text:
        return None, "⏳ LOOSE"
    if "foul" in play_text:
        return other_team, f"FT {KALSHI_CODES.get(other_team, other_team[:3].upper())}"
    return acting_team, f"🏀 {KALSHI_CODES.get(acting_team, acting_team[:3].upper())}"

def render_scoreboard(away, home, away_score, home_score, period, clock, away_record="", home_record=""):
    away_code = KALSHI_CODES.get(away, away[:3].upper())
    home_code = KALSHI_CODES.get(home, home[:3].upper())
    away_color = TEAM_COLORS.get(away, "#666")
    home_color = TEAM_COLORS.get(home, "#666")
    period_text = f"Q{period}" if period <= 4 else f"OT{period-4}"
    html = '<div style="background:#0f172a;border-radius:12px;padding:20px;margin-bottom:8px">'
    html += '<div style="text-align:center;color:#ffd700;font-weight:bold;font-size:22px;margin-bottom:16px">'
    html += period_text + " - " + clock + '</div>'
    html += '<table style="width:100%;border-collapse:collapse;color:#fff">'
    html += '<tr style="border-bottom:2px solid #333">'
    html += '<td style="padding:16px;text-align:left;width:70%">'
    html += '<span style="color:' + away_color + ';font-weight:bold;font-size:28px">' + away_code + '</span>'
    html += '<span style="color:#666;font-size:14px;margin-left:12px">' + away_record + '</span></td>'
    html += '<td style="padding:16px;text-align:right;font-weight:bold;font-size:52px;color:#fff">' + str(away_score) + '</td></tr>'
    html += '<tr><td style="padding:16px;text-align:left;width:70%">'
    html += '<span style="color:' + home_color + ';font-weight:bold;font-size:28px">' + home_code + '</span>'
    html += '<span style="color:#666;font-size:14px;margin-left:12px">' + home_record + '</span></td>'
    html += '<td style="padding:16px;text-align:right;font-weight:bold;font-size:52px;color:#fff">' + str(home_score) + '</td></tr>'
    html += '</table></div>'
    return html

def get_play_badge(last_play):
    if not last_play: return ""
    play_text = (last_play.get("text", "") or "").lower()
    score_value = last_play.get("score_value", 0)
    if score_value == 3 or ("three point" in play_text and "makes" in play_text):
        return '<rect x="175" y="25" width="150" height="30" fill="#22c55e" rx="6"/><text x="250" y="46" fill="#fff" font-size="14" font-weight="bold" text-anchor="middle">3PT MADE!</text>'
    elif score_value == 2 or ("makes" in play_text and any(w in play_text for w in ["layup", "dunk", "shot", "jumper", "hook"])):
        return '<rect x="175" y="25" width="150" height="30" fill="#22c55e" rx="6"/><text x="250" y="46" fill="#fff" font-size="14" font-weight="bold" text-anchor="middle">BUCKET!</text>'
    elif score_value == 1 or ("makes" in play_text and "free throw" in play_text):
        return '<rect x="175" y="25" width="150" height="30" fill="#22c55e" rx="6"/><text x="250" y="46" fill="#fff" font-size="14" font-weight="bold" text-anchor="middle">FT MADE</text>'
    elif "misses" in play_text:
        if "three point" in play_text:
            return '<rect x="175" y="25" width="150" height="30" fill="#ef4444" rx="6"/><text x="250" y="46" fill="#fff" font-size="14" font-weight="bold" text-anchor="middle">3PT MISS</text>'
        elif "free throw" in play_text:
            return '<rect x="175" y="25" width="150" height="30" fill="#ef4444" rx="6"/><text x="250" y="46" fill="#fff" font-size="14" font-weight="bold" text-anchor="middle">FT MISS</text>'
        else:
            return '<rect x="175" y="25" width="150" height="30" fill="#ef4444" rx="6"/><text x="250" y="46" fill="#fff" font-size="14" font-weight="bold" text-anchor="middle">MISSED SHOT</text>'
    elif "block" in play_text:
        return '<rect x="175" y="25" width="150" height="30" fill="#f97316" rx="6"/><text x="250" y="46" fill="#fff" font-size="14" font-weight="bold" text-anchor="middle">BLOCKED!</text>'
    elif "turnover" in play_text or "steal" in play_text:
        return '<rect x="175" y="25" width="150" height="30" fill="#f97316" rx="6"/><text x="250" y="46" fill="#fff" font-size="14" font-weight="bold" text-anchor="middle">TURNOVER</text>'
    elif "offensive rebound" in play_text:
        return '<rect x="175" y="25" width="150" height="30" fill="#3b82f6" rx="6"/><text x="250" y="46" fill="#fff" font-size="14" font-weight="bold" text-anchor="middle">OFF REBOUND</text>'
    elif "defensive rebound" in play_text:
        return '<rect x="175" y="25" width="150" height="30" fill="#3b82f6" rx="6"/><text x="250" y="46" fill="#fff" font-size="14" font-weight="bold" text-anchor="middle">DEF REBOUND</text>'
    elif "rebound" in play_text:
        return '<rect x="175" y="25" width="150" height="30" fill="#3b82f6" rx="6"/><text x="250" y="46" fill="#fff" font-size="14" font-weight="bold" text-anchor="middle">REBOUND</text>'
    elif "foul" in play_text:
        return '<rect x="175" y="25" width="150" height="30" fill="#eab308" rx="6"/><text x="250" y="46" fill="#000" font-size="14" font-weight="bold" text-anchor="middle">FOUL</text>'
    elif "timeout" in play_text:
        return '<rect x="175" y="25" width="150" height="30" fill="#a855f7" rx="6"/><text x="250" y="46" fill="#fff" font-size="14" font-weight="bold" text-anchor="middle">TIMEOUT</text>'
    return ""

def render_nba_court(away, home, away_score, home_score, period, clock, last_play=None):
    away_color = TEAM_COLORS.get(away, "#666")
    home_color = TEAM_COLORS.get(home, "#666")
    away_code = KALSHI_CODES.get(away, "AWY")
    home_code = KALSHI_CODES.get(home, "HME")
    period_text = f"Q{period}" if period <= 4 else f"OT{period-4}"
    play_badge = get_play_badge(last_play)
    svg = '<div style="background:#1a1a2e;border-radius:12px;padding:10px;">'
    svg += '<svg viewBox="0 0 500 280" style="width:100%;max-width:500px;">'
    svg += '<rect x="20" y="20" width="460" height="200" fill="#2d4a22" stroke="#fff" stroke-width="2" rx="8"/>'
    svg += '<circle cx="250" cy="120" r="35" fill="none" stroke="#fff" stroke-width="2"/>'
    svg += '<circle cx="250" cy="120" r="4" fill="#fff"/>'
    svg += '<line x1="250" y1="20" x2="250" y2="220" stroke="#fff" stroke-width="2"/>'
    svg += '<path d="M 20 50 Q 100 120 20 190" fill="none" stroke="#fff" stroke-width="2"/>'
    svg += '<rect x="20" y="70" width="70" height="100" fill="none" stroke="#fff" stroke-width="2"/>'
    svg += '<circle cx="90" cy="120" r="25" fill="none" stroke="#fff" stroke-width="2"/>'
    svg += '<circle cx="35" cy="120" r="8" fill="none" stroke="#ff6b35" stroke-width="3"/>'
    svg += '<path d="M 480 50 Q 400 120 480 190" fill="none" stroke="#fff" stroke-width="2"/>'
    svg += '<rect x="410" y="70" width="70" height="100" fill="none" stroke="#fff" stroke-width="2"/>'
    svg += '<circle cx="410" cy="120" r="25" fill="none" stroke="#fff" stroke-width="2"/>'
    svg += '<circle cx="465" cy="120" r="8" fill="none" stroke="#ff6b35" stroke-width="3"/>'
    svg += play_badge
    svg += '<rect x="40" y="228" width="90" height="48" fill="' + away_color + '" rx="6"/>'
    svg += '<text x="85" y="250" fill="#fff" font-size="14" font-weight="bold" text-anchor="middle">' + away_code + '</text>'
    svg += '<text x="85" y="270" fill="#fff" font-size="18" font-weight="bold" text-anchor="middle">' + str(away_score) + '</text>'
    svg += '<rect x="370" y="228" width="90" height="48" fill="' + home_color + '" rx="6"/>'
    svg += '<text x="415" y="250" fill="#fff" font-size="14" font-weight="bold" text-anchor="middle">' + home_code + '</text>'
    svg += '<text x="415" y="270" fill="#fff" font-size="18" font-weight="bold" text-anchor="middle">' + str(home_score) + '</text>'
    svg += '<text x="250" y="258" fill="#fff" font-size="16" font-weight="bold" text-anchor="middle">' + period_text + ' ' + clock + '</text>'
    svg += '</svg></div>'
    return svg

def get_play_icon(play_type, score_value):
    play_lower = play_type.lower() if play_type else ""
    if score_value > 0 or "made" in play_lower: return "🏀", "#22c55e"
    elif "miss" in play_lower or "block" in play_lower: return "❌", "#ef4444"
    elif "rebound" in play_lower: return "📥", "#3b82f6"
    elif "turnover" in play_lower or "steal" in play_lower: return "🔄", "#f97316"
    elif "foul" in play_lower: return "🚨", "#eab308"
    elif "timeout" in play_lower: return "⏸️", "#a855f7"
    return "•", "#888"

def get_kalshi_game_link(away, home):
    away_code = KALSHI_CODES.get(away, "XXX").lower()
    home_code = KALSHI_CODES.get(home, "XXX").lower()
    date_str = datetime.now(eastern).strftime('%y%b%d').lower()
    return f"https://kalshi.com/markets/kxnbagame/professional-basketball-game/kxnbagame-{date_str}{away_code}{home_code}"

def calc_projection(total_score, minutes_played):
    if minutes_played >= 8:
        pace = total_score / minutes_played
        weight = min(1.0, (minutes_played - 8) / 16)
        blended_pace = (pace * weight) + ((LEAGUE_AVG_TOTAL / 48) * (1 - weight))
        return max(185, min(265, round(blended_pace * 48)))
    elif minutes_played >= 6:
        pace = total_score / minutes_played
        return max(185, min(265, round(((pace * 0.3) + ((LEAGUE_AVG_TOTAL / 48) * 0.7)) * 48)))
    return LEAGUE_AVG_TOTAL

def get_pace_label(pace):
    if pace < 4.2: return "🐢 SLOW", "#22c55e"
    elif pace < 4.5: return "⚖️ AVG", "#eab308"
    elif pace < 5.0: return "🔥 FAST", "#f97316"
    return "💥 SHOOTOUT", "#ef4444"

def calc_pregame_edge(away, home, injuries, b2b_teams):
    away_stats = TEAM_STATS.get(away, {"net": 0, "pace": 98})
    home_stats = TEAM_STATS.get(home, {"net": 0, "pace": 98})
    score = 50 + ((home_stats["net"] - away_stats["net"] + 3) * 2)
    for inj in injuries.get(away, []):
        if inj["name"] in STAR_TIERS: score += 5 if STAR_TIERS[inj["name"]] == 3 else 3
    for inj in injuries.get(home, []):
        if inj["name"] in STAR_TIERS: score -= 5 if STAR_TIERS[inj["name"]] == 3 else 3
    if away in b2b_teams: score += 3
    if home in b2b_teams: score -= 3
    return max(0, min(100, round(score)))

def remove_position(pos_id):
    st.session_state.positions = [p for p in st.session_state.positions if p['id'] != pos_id]
    games = fetch_espn_games()
kalshi_ml = fetch_kalshi_ml()
kalshi_spreads = fetch_kalshi_spreads()
injuries = fetch_injuries()
b2b_teams = fetch_yesterday_teams()

live_games = [g for g in games if g['status'] in ['STATUS_IN_PROGRESS', 'STATUS_HALFTIME', 'STATUS_END_PERIOD'] or (g['period'] > 0 and g['status'] not in ['STATUS_FINAL', 'STATUS_FULL_TIME'])]
scheduled_games = [g for g in games if g['status'] == 'STATUS_SCHEDULED' and g['period'] == 0]
final_games = [g for g in games if g['status'] in ['STATUS_FINAL', 'STATUS_FULL_TIME']]

st.title("🏀 BIGSNAPSHOT NBA EDGE FINDER")
st.caption(f"v{VERSION} • {now.strftime('%b %d, %Y %I:%M %p ET')} • Vegas vs Kalshi Mispricing Detector")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Today's Games", len(games)); c2.metric("Live Now", len(live_games)); c3.metric("Scheduled", len(scheduled_games)); c4.metric("Final", len(final_games))
st.divider()

st.subheader("💰 VEGAS vs KALSHI MISPRICING ALERT")
fresh_label, fresh_age = get_kalshi_freshness()
fr1, fr2, fr3 = st.columns([2, 1, 1])
with fr1: st.caption("Buy when Kalshi underprices Vegas favorite • 10%+ gap = edge"); st.caption("⚠️ ESPN = soft book. Sharp line may differ.")
with fr2: st.markdown(f"**Kalshi Data:** {fresh_label}")
with fr3:
    if st.button("🔄 Refresh Kalshi Prices", key="refresh_kalshi_ml"):
        kalshi_ml = fetch_kalshi_ml(force_refresh=True); kalshi_spreads = fetch_kalshi_spreads(force_refresh=True); st.rerun()

mispricings = []
for g in games:
    if g['status'] in ['STATUS_FINAL', 'STATUS_FULL_TIME']: continue
    away, home = g['away'], g['home']
    vegas = g.get('vegas_odds', {})
    away_code, home_code = KALSHI_CODES.get(away, "XXX"), KALSHI_CODES.get(home, "XXX")
    kalshi_data = kalshi_ml.get(away_code + "@" + home_code, {})
    if not kalshi_data: continue
    home_ml, away_ml, spread = vegas.get('homeML'), vegas.get('awayML'), vegas.get('spread')
    if home_ml and away_ml:
        vhp = american_to_implied_prob(home_ml) * 100; vap = american_to_implied_prob(away_ml) * 100
        tot = vhp + vap; vhp = vhp / tot * 100; vap = vap / tot * 100
    elif spread:
        try: vhp = max(10, min(90, 50 - (float(spread) * 2.8))); vap = 100 - vhp
        except: continue
    else: continue
    khp, kap = kalshi_data.get('home_implied', 50), kalshi_data.get('away_implied', 50)
    if khp >= 90 or kap >= 90: continue
    he, ae = vhp - khp, vap - kap
    if he >= 10 or ae >= 10:
        if he >= ae:
            team, vp, kp, edge = home, vhp, khp, he
            action = "YES" if kalshi_data.get('yes_team_code', '').upper() == home_code.upper() else "NO"
        else:
            team, vp, kp, edge = away, vap, kap, ae
            action = "YES" if kalshi_data.get('yes_team_code', '').upper() == away_code.upper() else "NO"
        mispricings.append({'game': g, 'team': team, 'vegas_prob': vp, 'kalshi_prob': kp, 'edge': edge, 'action': action})
mispricings.sort(key=lambda x: x['edge'], reverse=True)

if mispricings:
    mp1, mp2 = st.columns([3, 1])
    with mp1: st.success(f"🔥 {len(mispricings)} mispricing opportunities found!")
    with mp2:
        if st.button(f"➕ ADD ALL ({len(mispricings)})", key="add_all_mispricing", use_container_width=True):
            added = 0
            for mp in mispricings:
                gm = mp['game']; gk = f"{gm['away']}@{gm['home']}"
                if not any(pos['game'] == gk for pos in st.session_state.positions):
                    st.session_state.positions.append({"game": gk, "pick": f"{mp['action']} ({mp['team']})", "type": "ML", "line": "-", "price": round(mp['kalshi_prob']), "contracts": 10, "link": get_kalshi_game_link(gm['away'], gm['home']), "id": str(uuid.uuid4())[:8]}); added += 1
            st.toast(f"✅ Added {added} positions!"); st.rerun()
    for mp in mispricings:
        g = mp['game']; gk = f"{g['away']}@{g['home']}"
        ec = "#ff6b6b" if mp['edge'] >= 15 else ("#22c55e" if mp['edge'] >= 12 else "#eab308")
        el = "🔥 STRONG" if mp['edge'] >= 15 else ("🟢 GOOD" if mp['edge'] >= 12 else "🟡 EDGE")
        ac = "#22c55e" if mp['action'] == "YES" else "#ef4444"
        st_txt = f"Q{g['period']} {g['clock']}" if g['period'] > 0 else (g.get('game_datetime', 'Scheduled') or 'Scheduled')
        cl1, cl2 = st.columns([3, 1])
        with cl1: st.markdown(f"**{g['away']} @ {g['home']}** • {st_txt}")
        with cl2: st.markdown(f"<span style='color:{ec};font-weight:bold'>{el} +{round(mp['edge'])}%</span>", unsafe_allow_html=True)
        h = '<div style="background:#0f172a;padding:16px;border-radius:10px;border:2px solid ' + ec + ';margin-bottom:12px">'
        h += '<div style="font-size:1.4em;font-weight:bold;color:#fff;margin-bottom:8px">🎯 BUY <span style="color:' + ac + ';background:' + ac + '22;padding:4px 12px;border-radius:6px">' + mp['action'] + '</span> on Kalshi</div>'
        h += '<div style="color:#aaa;margin-bottom:12px">' + mp['action'] + ' = ' + mp['team'] + ' wins</div>'
        h += '<table style="width:100%;text-align:center;color:#fff"><tr style="color:#888"><td>Vegas</td><td>Kalshi</td><td>EDGE</td></tr>'
        h += '<tr style="font-size:1.3em;font-weight:bold"><td>' + str(round(mp['vegas_prob'])) + '%</td><td>' + str(round(mp['kalshi_prob'])) + '¢</td>'
        h += '<td style="color:' + ec + '">+' + str(round(mp['edge'])) + '%</td></tr></table></div>'
        st.markdown(h, unsafe_allow_html=True)
        b1, b2 = st.columns(2)
        with b1: st.link_button(f"🎯 BUY {mp['action']} ({mp['team']})", get_kalshi_game_link(g['away'], g['home']), use_container_width=True)
        with b2:
            if any(pos['game'] == gk for pos in st.session_state.positions): st.success("✅ Tracked")
            elif st.button("➕ Track", key=f"mp_{gk}"):
                st.session_state.positions.append({"game": gk, "pick": f"{mp['action']} ({mp['team']})", "type": "ML", "line": "-", "price": round(mp['kalshi_prob']), "contracts": 10, "link": get_kalshi_game_link(g['away'], g['home']), "id": str(uuid.uuid4())[:8]}); st.rerun()
else:
    st.info("🔍 No mispricings found (need 10%+ gap between Vegas & Kalshi, excludes 90¢+ markets)")
st.divider()

st.subheader("🎮 LIVE EDGE MONITOR")
if live_games:
    for g in live_games:
        away, home, total, mins, game_id = g['away'], g['home'], g['total_score'], g['minutes_played'], g['game_id']
        plays = fetch_plays(game_id)
        st.markdown(f"### {away} @ {home}")
        st.markdown(render_scoreboard(away, home, g['away_score'], g['home_score'], g['period'], g['clock'], g.get('away_record', ''), g.get('home_record', '')), unsafe_allow_html=True)
        col1, col2 = st.columns([1, 1])
        with col1:
            last_play = plays[-1] if plays else None
            st.markdown(render_nba_court(away, home, g['away_score'], g['home_score'], g['period'], g['clock'], last_play), unsafe_allow_html=True)
            poss_team, poss_text = infer_possession(plays, away, home)
            if poss_text:
                pc = TEAM_COLORS.get(poss_team, "#ffd700") if poss_team else "#888"
                st.markdown(f"<div style='text-align:center;padding:8px;background:#1a1a2e;border-radius:6px;margin-top:4px'><span style='color:{pc};font-size:1.3em;font-weight:bold'>{poss_text} BALL</span></div>", unsafe_allow_html=True)
        with col2:
            st.markdown("**📋 LAST 10 PLAYS**")
            tts_on = st.checkbox("🔊 Announce plays", key=f"tts_{game_id}")
            if plays:
                for i, p in enumerate(reversed(plays)):
                    icon, color = get_play_icon(p['play_type'], p['score_value'])
                    pt = p['text'][:60] if p['text'] else "Play"
                    st.markdown(f"<div style='padding:4px 8px;margin:2px 0;background:#1e1e2e;border-radius:4px;border-left:3px solid {color}'><span style='color:{color}'>{icon}</span> Q{p['period']} {p['clock']} • {pt}</div>", unsafe_allow_html=True)
                    if i == 0 and tts_on and p['text']: speak_play(f"Q{p['period']} {p['clock']}. {p['text']}")
            else: st.caption("Waiting for plays...")
        if mins >= 6:
            proj = calc_projection(total, mins); pace = total / mins if mins > 0 else 0
            pace_label, pace_color = get_pace_label(pace)
            lead = g['home_score'] - g['away_score']; leader = home if g['home_score'] > g['away_score'] else away
            kl = get_kalshi_game_link(away, home)
            st.markdown(f"<div style='background:#1e1e2e;padding:12px;border-radius:8px;margin-top:8px'><b>Score:</b> {total} pts in {mins} min • <b>Pace:</b> <span style='color:{pace_color}'>{pace_label}</span> ({pace:.1f}/min)<br><b>Projection:</b> {proj} pts • <b>Lead:</b> {leader} +{abs(lead)}</div>", unsafe_allow_html=True)
            ac2, hc2 = KALSHI_CODES.get(away, "XXX"), KALSHI_CODES.get(home, "XXX")
            kd = kalshi_ml.get(ac2 + "@" + hc2, {})
            st.markdown("**🎯 MONEYLINE**")
            if abs(lead) >= 10:
                ml_pick = leader; ml_conf = "🔥 STRONG" if abs(lead) >= 15 else "🟢 GOOD"
                if kd:
                    if leader == home: ml_act = "YES" if kd.get('yes_team_code', '').upper() == hc2.upper() else "NO"
                    else: ml_act = "YES" if kd.get('yes_team_code', '').upper() == ac2.upper() else "NO"
                    st.link_button(f"{ml_conf} BUY {ml_act} ({ml_pick} ML) • Lead +{abs(lead)}", kl, use_container_width=True)
                else: st.link_button(f"{ml_conf} {ml_pick} ML • Lead +{abs(lead)}", kl, use_container_width=True)
            else: st.caption(f"⏳ Wait for larger lead (currently {leader} +{abs(lead)})")
            st.markdown("**📊 TOTALS**")
            yes_lines = [(t, proj - t) for t in sorted(THRESHOLDS) if proj - t >= 6]
            no_lines = [(t, t - proj) for t in sorted(THRESHOLDS, reverse=True) if t - proj >= 6]
            tc1, tc2 = st.columns(2)
            with tc1:
                st.markdown("<span style='color:#22c55e;font-weight:bold'>🟢 YES (Over) — go LOW</span>", unsafe_allow_html=True)
                if yes_lines:
                    for i, (line, cush) in enumerate(yes_lines[:3]):
                        sf = "🔒 FORTRESS" if cush >= 20 else ("✅ SAFE" if cush >= 12 else "🎯 TIGHT")
                        rc = " ⭐REC" if i == 0 and cush >= 12 else ""
                        st.link_button(f"{sf} YES {line} (+{int(cush)}){rc}", kl, use_container_width=True)
                else: st.caption("No safe YES lines (need 6+ cushion)")
            with tc2:
                st.markdown("<span style='color:#ef4444;font-weight:bold'>🔴 NO (Under) — go HIGH</span>", unsafe_allow_html=True)
                if no_lines:
                    for i, (line, cush) in enumerate(no_lines[:3]):
                        sf = "🔒 FORTRESS" if cush >= 20 else ("✅ SAFE" if cush >= 12 else "🎯 TIGHT")
                        rc = " ⭐REC" if i == 0 and cush >= 12 else ""
                        st.link_button(f"{sf} NO {line} (+{int(cush)}){rc}", kl, use_container_width=True)
                else: st.caption("No safe NO lines (need 6+ cushion)")
        else: st.caption("⏳ Waiting for 6+ minutes...")
        st.divider()
else: st.info("No live games right now")

st.subheader("🎯 CUSHION SCANNER (Totals)")
all_game_options = ["All Games"] + [f"{g['away']} @ {g['home']}" for g in games]
cc1, cc2, cc3 = st.columns(3)
with cc1: selected_game = st.selectbox("Select Game:", all_game_options, key="cush_game")
with cc2: min_mins = st.selectbox("Min PLAY TIME:", [8, 12, 16, 20, 24], index=1, key="cush_mins")
with cc3: side_choice = st.selectbox("Side:", ["NO (Under)", "YES (Over)"], key="cush_side")
if min_mins == 8: st.info("🦈 SHARK MODE: 8 min played = early entry. Only buy if cushion ≥12 (✅ SAFE or 🔒 FORTRESS)")
elif min_mins == 12: st.info("✅ SMART MONEY: 12 min played = pace locked. Cushion ≥6 is tradeable.")

cushion_data = []
for g in games:
    if g['status'] in ['STATUS_FINAL', 'STATUS_FULL_TIME']: continue
    gn = f"{g['away']} @ {g['home']}"
    if selected_game != "All Games" and gn != selected_game: continue
    if g['minutes_played'] < min_mins: continue
    total, mins = g['total_score'], g['minutes_played']
    vou = g.get('vegas_odds', {}).get('overUnder')
    if mins >= 8: proj = calc_projection(total, mins); pl = get_pace_label(total / mins)[0]; st2 = f"Q{g['period']} {g['clock']}" if g['period'] > 0 else "Live"
    elif vou:
        try: proj = round(float(vou)); pl = "📊 VEGAS"; st2 = "Scheduled" if mins == 0 else f"Q{g['period']} {g['clock']} (early)"
        except: proj = LEAGUE_AVG_TOTAL; pl = "⏳ PRE"; st2 = "Scheduled"
    else: proj = LEAGUE_AVG_TOTAL; pl = "⏳ PRE"; st2 = "Scheduled"
    ts = sorted(THRESHOLDS) if side_choice == "YES (Over)" else sorted(THRESHOLDS, reverse=True)
    for idx, thresh in enumerate(ts):
        cush = (thresh - proj) if side_choice == "NO (Under)" else (proj - thresh)
        if cush >= 6 or (selected_game != "All Games"):
            sl = "🔒 FORTRESS" if cush >= 20 else ("✅ SAFE" if cush >= 12 else ("🎯 TIGHT" if cush >= 6 else "⚠️ RISKY"))
            cushion_data.append({"game": gn, "status": st2, "proj": proj, "line": thresh, "cushion": cush, "pace": pl, "link": get_kalshi_game_link(g['away'], g['home']), "mins": mins, "is_live": mins >= 8, "safety": sl, "is_recommended": idx == 0 and cush >= 12})

so = {"🔒 FORTRESS": 0, "✅ SAFE": 1, "🎯 TIGHT": 2, "⚠️ RISKY": 3}
cushion_data.sort(key=lambda x: (not x['is_live'], so.get(x['safety'], 3), -x['cushion']))
if cushion_data:
    direction = "go LOW for safety" if side_choice == "YES (Over)" else "go HIGH for safety"
    st.caption(f"💡 {side_choice.split()[0]} bets: {direction}")
    mr = 20 if selected_game != "All Games" else 10
    for cd in cushion_data[:mr]:
        d1, d2, d3, d4 = st.columns([3, 1.2, 1.3, 2])
        with d1:
            rb = " ⭐REC" if cd.get('is_recommended') else ""
            st.markdown(f"**{cd['game']}** • {cd['status']}{rb}")
            if cd['mins'] > 0: st.caption(f"{cd['pace']} • {cd['mins']} min played")
            else: st.caption(f"{cd['pace']} O/U: {cd['proj']}")
        with d2: st.write(f"Proj: {cd['proj']} | Line: {cd['line']}")
        with d3:
            cx = "#22c55e" if cd['cushion'] >= 12 else ("#eab308" if cd['cushion'] >= 6 else "#ef4444")
            st.markdown(f"<span style='color:{cx};font-weight:bold'>{cd['safety']}<br>+{round(cd['cushion'])}</span>", unsafe_allow_html=True)
        with d4: st.link_button(f"BUY {'NO' if 'NO' in side_choice else 'YES'} {cd['line']}", cd['link'], use_container_width=True)
else:
    if selected_game != "All Games": st.info(f"Select a side and see all lines for {selected_game}")
    else:
        lc = sum(1 for g in games if g['minutes_played'] >= min_mins and g['status'] not in ['STATUS_FINAL', 'STATUS_FULL_TIME'])
        if lc == 0: st.info(f"⏳ No games have reached {min_mins}+ min play time yet. Waiting for tip-off...")
        else: st.info(f"No {side_choice.split()[0]} opportunities with 6+ cushion. Try switching sides or wait for pace to develop.")
st.divider()

st.subheader("📈 PACE SCANNER")
pace_data = [{"game": f"{g['away']} @ {g['home']}", "status": f"Q{g['period']} {g['clock']}", "total": g['total_score'], "pace": g['total_score']/g['minutes_played'], "pace_label": get_pace_label(g['total_score']/g['minutes_played'])[0], "pace_color": get_pace_label(g['total_score']/g['minutes_played'])[1], "proj": calc_projection(g['total_score'], g['minutes_played'])} for g in live_games if g['minutes_played'] >= 6]
pace_data.sort(key=lambda x: x['pace'])
if pace_data:
    for pd in pace_data:
        p1, p2, p3, p4 = st.columns([3, 2, 2, 2])
        with p1: st.markdown(f"**{pd['game']}**")
        with p2: st.write(f"{pd['status']} • {pd['total']} pts")
        with p3: st.markdown(f"<span style='color:{pd['pace_color']};font-weight:bold'>{pd['pace_label']}</span>", unsafe_allow_html=True)
        with p4: st.write(f"Proj: {pd['proj']}")
else: st.info("No live games with 6+ minutes played")
st.divider()

with st.expander("🎯 PRE-GAME ALIGNMENT (Speculative)", expanded=True):
    st.caption("Model prediction for scheduled games • Click ➕ to add to tracker")
    if scheduled_games:
        all_picks = []
        for g in scheduled_games:
            away, home = g['away'], g['home']
            es = calc_pregame_edge(away, home, injuries, b2b_teams)
            if es >= 70: pick, el, ecc = home, "🟢 STRONG", "#22c55e"
            elif es >= 60: pick, el, ecc = home, "🟢 GOOD", "#22c55e"
            elif es <= 30: pick, el, ecc = away, "🟢 STRONG", "#22c55e"
            elif es <= 40: pick, el, ecc = away, "🟢 GOOD", "#22c55e"
            else: pick, el, ecc = "WAIT", "🟡 NEUTRAL", "#eab308"
            all_picks.append({"away": away, "home": home, "pick": pick, "edge_label": el, "edge_color": ecc})
        actionable = [p for p in all_picks if p['pick'] != "WAIT"]
        if actionable:
            a1, a2 = st.columns([3, 1])
            with a1: st.caption(f"📊 {len(actionable)} actionable picks out of {len(all_picks)} games")
            with a2:
                if st.button(f"➕ ADD ALL ({len(actionable)})", key="add_all_pregame", use_container_width=True):
                    added = 0
                    for p in actionable:
                        gk = f"{p['away']}@{p['home']}"
                        if not any(pos['game'] == gk for pos in st.session_state.positions):
                            st.session_state.positions.append({"game": gk, "pick": p['pick'], "type": "ML", "line": "-", "price": 50, "contracts": 10, "link": get_kalshi_game_link(p['away'], p['home']), "id": str(uuid.uuid4())[:8]}); added += 1
                    st.toast(f"✅ Added {added} positions!"); st.rerun()
            st.markdown("---")
        for p in all_picks:
            pg1, pg2, pg3, pg4 = st.columns([2.5, 1, 2, 1])
            gdt = next((g.get('game_datetime', '') for g in scheduled_games if g['away'] == p['away'] and g['home'] == p['home']), '')
            with pg1: st.markdown(f"**{p['away']} @ {p['home']}**"); st.caption(gdt) if gdt else None
            with pg2: st.markdown(f"<span style='color:{p['edge_color']}'>{p['edge_label']}</span>", unsafe_allow_html=True)
            with pg3:
                if p['pick'] != "WAIT": st.link_button(f"🎯 {p['pick']} ML", get_kalshi_game_link(p['away'], p['home']), use_container_width=True)
                else: st.caption("Wait for better edge")
            with pg4:
                if p['pick'] != "WAIT":
                    gk = f"{p['away']}@{p['home']}"
                    if any(pos['game'] == gk for pos in st.session_state.positions): st.caption("✅ Tracked")
                    elif st.button("➕", key=f"quick_{p['away']}_{p['home']}"):
                        st.session_state.positions.append({"game": gk, "pick": p['pick'], "type": "ML", "line": "-", "price": 50, "contracts": 10, "link": get_kalshi_game_link(p['away'], p['home']), "id": str(uuid.uuid4())[:8]}); st.rerun()
    else: st.info("No scheduled games")
st.divider()

st.subheader("🏥 INJURY REPORT")
today_teams = set([g['away'] for g in games] + [g['home'] for g in games])
injury_found = False
for team in sorted(today_teams):
    for inj in injuries.get(team, []):
        if inj['name'] in STAR_PLAYERS.get(team, []):
            injury_found = True; tier = STAR_TIERS.get(inj['name'], 1)
            st.markdown(f"**{team}**: {'⭐⭐⭐' if tier==3 else '⭐⭐' if tier==2 else '⭐'} {inj['name']} - {inj['status']}")
if not injury_found: st.info("No star player injuries reported")
st.divider()

st.subheader("📊 POSITION TRACKER")
today_games = [(f"{g['away']} @ {g['home']}", g['away'], g['home']) for g in games]
with st.expander("➕ ADD NEW POSITION", expanded=False):
    if today_games:
        ac1, ac2 = st.columns(2)
        with ac1: game_sel = st.selectbox("Select Game", [g[0] for g in today_games], key="add_game"); sel_game = next((g for g in today_games if g[0] == game_sel), None)
        with ac2: bet_type = st.selectbox("Bet Type", ["ML (Moneyline)", "Totals (Over/Under)", "Spread"], key="add_type")
        ac3, ac4 = st.columns(2)
        with ac3:
            if bet_type == "ML (Moneyline)": pick = st.selectbox("Pick", [sel_game[1], sel_game[2]] if sel_game else [], key="add_pick")
            elif bet_type == "Spread": pick = st.selectbox("Pick Team", [sel_game[1], sel_game[2]] if sel_game else [], key="add_pick")
            else: pick = st.selectbox("Pick", ["YES (Over)", "NO (Under)"], key="add_totals_pick")
        with ac4:
            if bet_type == "Spread":
                if sel_game:
                    aw_c = KALSHI_CODES.get(sel_game[1], "XXX"); hm_c = KALSHI_CODES.get(sel_game[2], "XXX")
                    gsk = f"{aw_c}@{hm_c}"; ksl = kalshi_spreads.get(gsk, [])
                    if ksl:
                        so2 = [f"{sp['line']} ({sp['team_code']}) @ {sp['yes_price']}¢" for sp in ksl]
                        line = st.selectbox("Kalshi Spreads", so2, key="add_spread_line"); line = line.split()[0] if line else "-7.5"
                    else:
                        spo = ["-1.5", "-2.5", "-3.5", "-4.5", "-5.5", "-6.5", "-7.5", "-8.5", "-9.5", "-10.5", "-11.5", "-12.5", "+1.5", "+2.5", "+3.5", "+4.5", "+5.5", "+6.5", "+7.5", "+8.5", "+9.5", "+10.5", "+11.5", "+12.5"]
                        line = st.selectbox("Spread Line (Manual)", spo, index=5, key="add_spread_line")
                else: line = "-7.5"
            elif "Totals" in bet_type: line = st.selectbox("Line", THRESHOLDS, key="add_line")
            else: line = "-"
        ac5, ac6, ac7 = st.columns(3)
        with ac5: entry_price = st.number_input("Entry Price (¢)", 1, 99, 50, key="add_price")
        with ac6: contracts = st.number_input("Contracts", 1, 10000, 10, key="add_contracts")
        with ac7: cost = entry_price * contracts / 100; st.metric("Cost", f"${cost:.2f}"); st.caption(f"Win: +${contracts - cost:.2f}")
        if st.button("✅ ADD POSITION", use_container_width=True, key="add_pos_btn"):
            if sel_game:
                if bet_type == "ML (Moneyline)": pt, pp, pl2 = "ML", pick, "-"
                elif bet_type == "Spread": pt, pp, pl2 = "Spread", pick, str(line)
                else: pt, pp, pl2 = "Totals", pick.split()[0], str(line)
                st.session_state.positions.append({"game": f"{sel_game[1]}@{sel_game[2]}", "pick": pp, "type": pt, "line": pl2, "price": entry_price, "contracts": contracts, "link": get_kalshi_game_link(sel_game[1], sel_game[2]), "id": str(uuid.uuid4())[:8]}); st.success("Added!"); st.rerun()

if st.session_state.positions:
    st.markdown("---")
    for idx, pos in enumerate(st.session_state.positions):
        cur = next((g for g in games if f"{g['away']}@{g['home']}" == pos['game']), None)
        q1, q2, q3, q4, q5 = st.columns([2.5, 1.5, 1.5, 1.5, 1])
        with q1:
            st.markdown(f"**{pos['game']}**")
            if cur:
                if cur['period'] > 0: st.caption(f"🔴 LIVE Q{cur['period']} {cur['clock']} | {cur['away_score']}-{cur['home_score']}")
                elif cur['status'] in ['STATUS_FINAL', 'STATUS_FULL_TIME']: st.caption(f"✅ FINAL {cur['away_score']}-{cur['home_score']}")
                else: st.caption("⏳ Scheduled")
        with q2: st.write(f"🎯 {pos['pick']} ML" if pos['type']=="ML" else (f"📏 {pos['pick']} {pos['line']}" if pos['type']=="Spread" else f"📊 {pos['pick']} {pos['line']}"))
        with q3: st.write(f"{pos.get('contracts',10)} @ {pos.get('price',50)}¢"); st.caption(f"${pos.get('price',50)*pos.get('contracts',10)/100:.2f}")
        with q4: st.link_button("🔗 Kalshi", pos['link'], use_container_width=True)
        with q5:
            if st.button("🗑️", key=f"del_{pos['id']}"): remove_position(pos['id']); st.rerun()
    st.markdown("---")
    if st.button("🗑️ CLEAR ALL POSITIONS", use_container_width=True, type="primary"): st.session_state.positions = []; st.rerun()
else: st.caption("No positions tracked yet. Use ➕ ADD ALL buttons above or add manually.")
st.divider()

st.subheader("📋 ALL GAMES TODAY")
for g in games:
    if g['status'] in ['STATUS_FINAL', 'STATUS_FULL_TIME']: status, color = f"FINAL: {g['away_score']}-{g['home_score']}", "#666"
    elif g['period'] > 0: status, color = f"LIVE Q{g['period']} {g['clock']} | {g['away_score']}-{g['home_score']}", "#22c55e"
    else: status, color = f"{g.get('game_datetime', 'TBD')} | Spread: {g.get('vegas_odds',{}).get('spread','N/A')}", "#888"
    h2 = '<div style="background:#1e1e2e;padding:12px;border-radius:8px;margin-bottom:8px;border-left:3px solid ' + color + '">'
    h2 += '<b style="color:#fff">' + g['away'] + ' @ ' + g['home'] + '</b><br>'
    h2 += '<span style="color:' + color + '">' + status + '</span></div>'
    st.markdown(h2, unsafe_allow_html=True)

st.divider()
st.caption(f"v{VERSION} • Educational only • Not financial advice")
st.caption("Stay small. Stay quiet. Win.")
