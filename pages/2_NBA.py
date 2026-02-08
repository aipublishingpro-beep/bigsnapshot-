import streamlit as st
from streamlit_autorefresh import st_autorefresh
import streamlit.components.v1 as components
st.set_page_config(page_title="BigSnapshot NBA Edge Finder", page_icon="🏀", layout="wide")
from auth import require_auth
require_auth()
st_autorefresh(interval=24000, key="datarefresh")
import uuid, re, requests, pytz
import requests as req_ga
from datetime import datetime, timedelta

# ── GA4 Tracking ──
def send_ga4_event(page_title, page_path):
    try:
        url = "https://www.google-analytics.com/mp/collect?measurement_id=G-NQKY5VQ376&api_secret=n4oBJjH7RXi0dA7aQo2CZA"
        payload = {"client_id": str(uuid.uuid4()), "events": [{"name": "page_view", "params": {"page_title": page_title, "page_location": "https://bigsnapshot.streamlit.app" + page_path}}]}
        req_ga.post(url, json=payload, timeout=2)
    except: pass
send_ga4_event("BigSnapshot NBA Edge Finder", "/NBA")

# ── Timezone + Constants ──
eastern = pytz.timezone("US/Eastern")
now = datetime.now(eastern)
VERSION = "12.1"
LEAGUE_AVG_TOTAL = 225
THRESHOLDS = [210.5, 215.5, 220.5, 225.5, 230.5, 235.5, 240.5, 245.5]
HOME_COURT_ADV = 3.0
MIN_UNDERDOG_LEAD = 7
MIN_SPREAD_BRACKET = 10
MAX_NO_PRICE = 85
MIN_WP_EDGE = 8
LEAD_BY_QUARTER = {1: 7, 2: 8, 3: 10, 4: 13}

# ── Session State ──
if 'positions' not in st.session_state: st.session_state.positions = []
if 'sniper_alerts' not in st.session_state: st.session_state.sniper_alerts = []
if 'comeback_alerts' not in st.session_state: st.session_state.comeback_alerts = []
if 'comeback_tracking' not in st.session_state: st.session_state.comeback_tracking = {}
if 'alerted_games' not in st.session_state: st.session_state.alerted_games = set()
if 'comeback_alerted' not in st.session_state: st.session_state.comeback_alerted = set()

# ── TEAM_ABBREVS ──
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
    "San Antonio Spurs": "San Antonio", "Toronto Raptors": "Toronto", "Utah Jazz": "Utah",
    "Washington Wizards": "Washington",
    "MIL": "Milwaukee", "PHI": "Philadelphia", "BOS": "Boston", "NYK": "New York",
    "CLE": "Cleveland", "ORL": "Orlando", "ATL": "Atlanta", "MIA": "Miami",
    "CHI": "Chicago", "BKN": "Brooklyn", "TOR": "Toronto", "IND": "Indiana",
    "DET": "Detroit", "CHA": "Charlotte", "WAS": "Washington", "OKC": "Oklahoma City",
    "HOU": "Houston", "MEM": "Memphis", "DAL": "Dallas", "DEN": "Denver",
    "MIN": "Minnesota", "LAC": "LA Clippers", "LAL": "LA Lakers", "SAC": "Sacramento",
    "PHX": "Phoenix", "GSW": "Golden State", "POR": "Portland", "UTA": "Utah",
    "SAS": "San Antonio", "NOP": "New Orleans",
}

# ── KALSHI_CODES ──
KALSHI_CODES = {
    "Atlanta": "ATL", "Boston": "BOS", "Brooklyn": "BKN", "Charlotte": "CHA",
    "Chicago": "CHI", "Cleveland": "CLE", "Dallas": "DAL", "Denver": "DEN",
    "Detroit": "DET", "Golden State": "GSW", "Houston": "HOU", "Indiana": "IND",
    "LA Clippers": "LAC", "LA Lakers": "LAL", "Memphis": "MEM", "Miami": "MIA",
    "Milwaukee": "MIL", "Minnesota": "MIN", "New Orleans": "NOP", "New York": "NYK",
    "Oklahoma City": "OKC", "Orlando": "ORL", "Philadelphia": "PHI", "Phoenix": "PHX",
    "Portland": "POR", "Sacramento": "SAC", "San Antonio": "SAS", "Toronto": "TOR",
    "Utah": "UTA", "Washington": "WAS",
}

# ── TEAM_COLORS ──
TEAM_COLORS = {
    "Atlanta": "#E03A3E", "Boston": "#007A33", "Brooklyn": "#000000", "Charlotte": "#1D1160",
    "Chicago": "#CE1141", "Cleveland": "#860038", "Dallas": "#00538C", "Denver": "#0E2240",
    "Detroit": "#C8102E", "Golden State": "#1D428A", "Houston": "#CE1141", "Indiana": "#002D62",
    "LA Clippers": "#C8102E", "LA Lakers": "#552583", "Memphis": "#5D76A9", "Miami": "#98002E",
    "Milwaukee": "#00471B", "Minnesota": "#0C2340", "New Orleans": "#0C2340", "New York": "#006BB6",
    "Oklahoma City": "#007AC1", "Orlando": "#0077C0", "Philadelphia": "#006BB6", "Phoenix": "#1D1160",
    "Portland": "#E03A3E", "Sacramento": "#5A2D81", "San Antonio": "#C4CED4", "Toronto": "#CE1141",
    "Utah": "#002B5C", "Washington": "#002B5C",
}

# ── ESPN_TEAM_IDS ──
ESPN_TEAM_IDS = {
    "Atlanta": "1", "Boston": "2", "Brooklyn": "17", "Charlotte": "30", "Chicago": "4",
    "Cleveland": "5", "Dallas": "6", "Denver": "7", "Detroit": "8", "Golden State": "9",
    "Houston": "10", "Indiana": "11", "LA Clippers": "12", "LA Lakers": "13", "Memphis": "29",
    "Miami": "14", "Milwaukee": "15", "Minnesota": "16", "New Orleans": "3", "New York": "18",
    "Oklahoma City": "25", "Orlando": "19", "Philadelphia": "20", "Phoenix": "21", "Portland": "22",
    "Sacramento": "23", "San Antonio": "24", "Toronto": "28", "Utah": "26", "Washington": "27",
}

# ── Helper Functions ──

def american_to_implied_prob(odds):
    if odds is None:
        return None
    if odds > 0:
        return 100 / (odds + 100)
    else:
        return abs(odds) / (abs(odds) + 100)

def speak_play(text):
    clean = text.replace('"', '').replace("'", "").replace("\n", " ")[:100]
    js = f"""
    <script>
    (function(){{
        if(window.lastSpoken==='{clean}') return;
        window.lastSpoken='{clean}';
        var u=new SpeechSynthesisUtterance('{clean}');
        u.rate=1.1;
        window.speechSynthesis.speak(u);
    }})();
    </script>
    """
    components.html(js, height=0)

def get_kalshi_game_link(away, home):
    ac = KALSHI_CODES.get(away, "").lower()
    hc = KALSHI_CODES.get(home, "").lower()
    d = datetime.now(eastern).strftime('%y%b%d').lower()
    return f"https://kalshi.com/markets/kxnbagame/professional-basketball-game/kxnbagame-{d}{ac}{hc}"

def get_kalshi_spread_link(away, home):
    ac = KALSHI_CODES.get(away, "").lower()
    hc = KALSHI_CODES.get(home, "").lower()
    d = datetime.now(eastern).strftime('%y%b%d').lower()
    return f"https://kalshi.com/markets/kxnbaspread/nba-spread/kxnbaspread-{d}{ac}{hc}"

def calc_projection(total_score, minutes_played):
    if minutes_played >= 8:
        pace = total_score / minutes_played
        weight = min(1.0, (minutes_played - 8) / 16)
        blended = (pace * weight) + ((225 / 48) * (1 - weight))
        return max(185, min(265, round(blended * 48)))
    elif minutes_played >= 6:
        pace = total_score / minutes_played
        return max(185, min(265, round(((pace * 0.3) + ((225 / 48) * 0.7)) * 48)))
    else:
        return 225

def get_pace_label(pace):
    if pace < 4.2:
        return "🐢 SLOW", "#22c55e"
    elif pace < 4.5:
        return "⚖️ AVG", "#eab308"
    elif pace < 5.0:
        return "🔥 FAST", "#f97316"
    else:
        return "💥 SHOOTOUT", "#ef4444"

def parse_record(s):
    try:
        parts = s.split("-")
        return (int(parts[0]), int(parts[1]))
    except:
        return (0, 0)

def get_favorite_side(home_record, away_record, home_ml=0):
    if home_ml != 0:
        return "home" if home_ml < 0 else "away"
    hw, hl = parse_record(home_record)
    aw, al = parse_record(away_record)
    h_pct = hw / (hw + hl) if (hw + hl) > 0 else 0.5
    a_pct = aw / (aw + al) if (aw + al) > 0 else 0.5
    return "home" if h_pct >= a_pct else "away"

def _parse_win_pct(record_str):
    try:
        parts = record_str.strip().split()[0].split("-")
        w, l = int(parts[0]), int(parts[1])
        return w / (w + l) if (w + l) > 0 else None
    except:
        return None

def remove_position(pos_id):
    st.session_state.positions = [p for p in st.session_state.positions if p.get('id') != pos_id]

# ── ESPN Data Fetchers ──

@st.cache_data(ttl=30)
def fetch_espn_games():
    try:
        today = datetime.now(eastern).strftime("%Y%m%d")
        url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={today}"
        data = requests.get(url, timeout=10).json()
        games = []
        for event in data.get("events", []):
            comp = event["competitions"][0]
            teams = comp["competitors"]
            away_team = teams[1] if teams[0].get("homeAway") == "home" else teams[0]
            home_team = teams[0] if teams[0].get("homeAway") == "home" else teams[1]
            away_full = away_team["team"].get("displayName", "")
            home_full = home_team["team"].get("displayName", "")
            away = TEAM_ABBREVS.get(away_full, TEAM_ABBREVS.get(away_team["team"].get("abbreviation", ""), away_full))
            home = TEAM_ABBREVS.get(home_full, TEAM_ABBREVS.get(home_team["team"].get("abbreviation", ""), home_full))
            away_score = int(away_team.get("score", 0) or 0)
            home_score = int(home_team.get("score", 0) or 0)
            away_rec = away_team.get("records", [{}])[0].get("summary", "0-0") if away_team.get("records") else "0-0"
            home_rec = home_team.get("records", [{}])[0].get("summary", "0-0") if home_team.get("records") else "0-0"
            status_obj = event.get("status", {})
            status_type = status_obj.get("type", {})
            state = status_type.get("state", "pre")
            status = status_type.get("name", "STATUS_SCHEDULED")
            period = status_obj.get("period", 0)
            clock_str = status_obj.get("displayClock", "0:00")
            # Calculate minutes played
            minutes_played = 0
            if state == "in":
                completed_periods = max(0, period - 1)
                if period <= 4:
                    mins_per = 12
                else:
                    mins_per = 5
                completed_mins = 0
                for p in range(1, completed_periods + 1):
                    completed_mins += 12 if p <= 4 else 5
                try:
                    cparts = clock_str.replace(" ", "").split(":")
                    remaining = float(cparts[0]) + float(cparts[1]) / 60 if len(cparts) == 2 else float(cparts[0])
                except:
                    remaining = 0
                current_period_length = 12 if period <= 4 else 5
                minutes_played = completed_mins + (current_period_length - remaining)
            elif state == "post":
                minutes_played = 48
            total_score = away_score + home_score
            # Vegas odds
            vegas = {}
            home_ml = 0
            try:
                odds_list = comp.get("odds", [])
                if odds_list:
                    o = odds_list[0]
                    vegas = {
                        "spread": o.get("details", ""),
                        "overUnder": o.get("overUnder", 0),
                        "homeML": o.get("homeTeamOdds", {}).get("moneyLine", 0),
                        "awayML": o.get("awayTeamOdds", {}).get("moneyLine", 0),
                    }
                    home_ml = vegas.get("homeML", 0) or 0
            except:
                pass
            # Game time
            gt_raw = event.get("date", "")
            try:
                gt_dt = datetime.strptime(gt_raw, "%Y-%m-%dT%H:%MZ").replace(tzinfo=pytz.utc).astimezone(eastern)
                game_time = gt_dt.strftime("%-I:%M %p ET")
                game_datetime = gt_dt.strftime("%Y-%m-%d %H:%M")
            except:
                game_time = ""
                game_datetime = ""
            games.append({
                "away": away, "home": home,
                "away_score": away_score, "home_score": home_score,
                "away_record": away_rec, "home_record": home_rec,
                "away_id": away_team["team"].get("id", ""),
                "home_id": home_team["team"].get("id", ""),
                "away_abbrev": away_team["team"].get("abbreviation", ""),
                "home_abbrev": home_team["team"].get("abbreviation", ""),
                "away_full": away_full, "home_full": home_full,
                "status": status, "state": state,
                "period": period, "clock": clock_str,
                "minutes_played": minutes_played,
                "total_score": total_score,
                "game_id": event.get("id", ""),
                "vegas_odds": vegas,
                "home_ml": home_ml,
                "game_time": game_time, "game_datetime": game_datetime,
            })
        return games
    except:
        return []

@st.cache_data(ttl=300)
def fetch_game_summary(game_id):
    try:
        url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary?event={game_id}"
        return requests.get(url, timeout=10).json()
    except:
        return None

@st.cache_data(ttl=20)
def fetch_espn_win_prob(game_id):
    try:
        url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary?event={game_id}"
        data = requests.get(url, timeout=10).json()
        try:
            wp = data["winprobability"]
            if wp:
                return wp[-1]["homeWinPercentage"] * 100
        except:
            pass
        try:
            return float(data["predictor"]["homeTeam"]["gameProjection"])
        except:
            pass
    except:
        pass
    return None

def parse_predictor(summary):
    try:
        pred = summary.get("predictor", {})
        h = float(pred.get("homeTeam", {}).get("gameProjection", 50))
        a = float(pred.get("awayTeam", {}).get("gameProjection", 50))
        return h / 100, a / 100
    except:
        return 0.5, 0.5

def parse_team_stats_from_summary(summary):
    home_stats = {}
    away_stats = {}
    try:
        teams = summary.get("boxscore", {}).get("teams", [])
        for t in teams:
            is_home = t.get("homeAway", "") == "home"
            stats_dict = home_stats if is_home else away_stats
            for s in t.get("statistics", []):
                stats_dict[s.get("name", "")] = s.get("displayValue", "0")
    except:
        pass
    return home_stats, away_stats

def _get_team_leaders(summary, home_away):
    leaders = []
    try:
        for team_block in summary.get("leaders", []):
            if team_block.get("team", {}).get("homeAway") == home_away:
                for cat in team_block.get("leaders", []):
                    if cat.get("name") in ("points", "rating"):
                        for leader in cat.get("leaders", [])[:3]:
                            name = leader.get("athlete", {}).get("displayName", "")
                            if name:
                                leaders.append(name)
    except:
        pass
    return leaders

def _is_star_player(player_name, leaders_list):
    try:
        last = player_name.strip().split()[-1].lower()
        for l in leaders_list[:3]:
            if l.strip().split()[-1].lower() == last:
                return True
    except:
        pass
    return False

@st.cache_data(ttl=300)
def fetch_injuries():
    injuries = {}
    try:
        url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/injuries"
        data = requests.get(url, timeout=10).json()
        for team_block in data.get("items", []):
            team_name_raw = team_block.get("team", {}).get("displayName", "")
            team_short = TEAM_ABBREVS.get(team_name_raw, team_name_raw)
            team_injuries = []
            for athlete in team_block.get("injuries", []):
                name = athlete.get("athlete", {}).get("displayName", "Unknown")
                status = athlete.get("status", "Unknown")
                team_injuries.append({"name": name, "status": status})
            if team_injuries:
                injuries[team_short] = team_injuries
    except:
        pass
    return injuries

@st.cache_data(ttl=300)
def fetch_yesterday_teams():
    try:
        yesterday = (datetime.now(eastern) - timedelta(days=1)).strftime("%Y%m%d")
        url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={yesterday}"
        data = requests.get(url, timeout=10).json()
        teams = set()
        for event in data.get("events", []):
            for comp in event.get("competitions", []):
                for team in comp.get("competitors", []):
                    full = team["team"].get("displayName", "")
                    short = TEAM_ABBREVS.get(full, full)
                    teams.add(short)
        return teams
    except:
        return set()

@st.cache_data(ttl=30)
def fetch_plays(game_id):
    try:
        url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary?event={game_id}"
        data = requests.get(url, timeout=10).json()
        plays_raw = []
        for drive in data.get("plays", []):
            if isinstance(drive, dict):
                plays_raw.append(drive)
            elif isinstance(drive, list):
                plays_raw.extend(drive)
        plays_raw = plays_raw[-15:]
        result = []
        for p in plays_raw[-10:]:
            text = p.get("text", "")
            period = p.get("period", {}).get("number", 0) if isinstance(p.get("period"), dict) else p.get("period", 0)
            clock = p.get("clock", {}).get("displayValue", "") if isinstance(p.get("clock"), dict) else p.get("clock", "")
            score_val = p.get("scoreValue", 0)
            play_type = p.get("type", {}).get("text", "") if isinstance(p.get("type"), dict) else ""
            team_id = ""
            if p.get("team"):
                team_id = str(p["team"].get("id", ""))
            result.append({
                "text": text, "period": period, "clock": clock,
                "score_value": score_val, "play_type": play_type, "team_id": team_id,
            })
        return result
    except:
        return []

# ── Kalshi Data Fetchers (PUBLIC) ──

@st.cache_data(ttl=60)
def fetch_kalshi_ml():
    try:
        url = "https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXNBAGAME&limit=100&status=open"
        data = requests.get(url, timeout=10).json()
        result = {}
        for m in data.get("markets", []):
            ticker = m.get("ticker", "")
            title = m.get("title", "")
            subtitle = m.get("subtitle", "")
            yes_bid = m.get("yes_bid", 0) or 0
            yes_ask = m.get("yes_ask", 0) or 0
            yes_price = m.get("last_price", 0) or yes_bid
            # Parse team codes from ticker: KXNBAGAME-{date}{away3}{home3}
            match = re.search(r'kxnbagame-\w+?([a-z]{3})([a-z]{3})$', ticker.lower())
            if not match:
                continue
            away_code = match.group(1).upper()
            home_code = match.group(2).upper()
            # Determine which team is YES
            yes_team_code = ""
            if title:
                for code, name in KALSHI_CODES.items():
                    if name == away_code or code.upper() == away_code:
                        if code.lower() in title.lower() or name.lower() in title.lower():
                            yes_team_code = away_code
                            break
                if not yes_team_code:
                    yes_team_code = away_code
            away_implied = 0
            home_implied = 0
            if yes_team_code == away_code:
                away_implied = yes_price
                home_implied = 100 - yes_price if yes_price else 0
            else:
                home_implied = yes_price
                away_implied = 100 - yes_price if yes_price else 0
            away_short = TEAM_ABBREVS.get(away_code, away_code)
            home_short = TEAM_ABBREVS.get(home_code, home_code)
            key = f"{away_short}@{home_short}"
            result[key] = {
                "away_code": away_code, "home_code": home_code,
                "yes_team_code": yes_team_code, "ticker": ticker,
                "yes_bid": yes_bid, "yes_ask": yes_ask, "yes_price": yes_price,
                "away_implied": away_implied, "home_implied": home_implied,
            }
        return result
    except:
        return {}

@st.cache_data(ttl=60)
def fetch_kalshi_spreads_raw():
    spreads = {}
    spread_list = []
    try:
        url = "https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXNBASPREAD&limit=200&status=open"
        data = requests.get(url, timeout=10).json()
        for m in data.get("markets", []):
            ticker = m.get("ticker", "")
            title = (m.get("title", "") or "").lower()
            subtitle = (m.get("subtitle", "") or "").lower()
            if "wins by" in title or "spread" in title or "margin" in title or "wins by" in subtitle or "spread" in subtitle:
                spread_list.append(m)
            match = re.search(r'kxnbaspread-\w+?([a-z]{3})([a-z]{3})', ticker.lower())
            if match:
                away_code = match.group(1).upper()
                home_code = match.group(2).upper()
                away_short = TEAM_ABBREVS.get(away_code, away_code)
                home_short = TEAM_ABBREVS.get(home_code, home_code)
                key = f"{away_short}@{home_short}"
                if key not in spreads:
                    spreads[key] = []
                spreads[key].append({
                    "ticker": ticker, "title": m.get("title", ""),
                    "yes_price": m.get("last_price", 0) or 0,
                    "yes_bid": m.get("yes_bid", 0) or 0,
                    "yes_ask": m.get("yes_ask", 0) or 0,
                    "no_bid": m.get("no_bid", 0) or 0,
                    "no_ask": m.get("no_ask", 0) or 0,
                })
    except:
        pass
    return spreads, spread_list

def find_spread_markets_for_game(home_abbrev, away_abbrev, home_name, away_name, spread_list):
    matches = []
    ha = home_abbrev.lower()
    aa = away_abbrev.lower()
    hn = home_name.lower()
    an = away_name.lower()
    for m in spread_list:
        ticker = (m.get("ticker", "") or "").lower()
        title = (m.get("title", "") or "").lower()
        subtitle = (m.get("subtitle", "") or "").lower()
        combined = f"{ticker} {title} {subtitle}"
        if (ha in combined or hn in combined) and (aa in combined or an in combined):
            # Extract spread value
            spread_val = None
            pat1 = re.search(r'(?:over|more than|by)\s+([\d.]+)', title)
            if pat1:
                spread_val = float(pat1.group(1))
            else:
                pat2 = re.search(r'(\d+\.?\d*)\s*[-–to]+\s*(\d+\.?\d*)', title)
                if pat2:
                    spread_val = (float(pat2.group(1)) + float(pat2.group(2))) / 2
                else:
                    pat3 = re.search(r'\b([1-9]\d?(?:\.\d+)?)\b', title)
                    if pat3:
                        v = float(pat3.group(1))
                        if 1 <= v <= 50:
                            spread_val = v
            if spread_val is None:
                continue
            yes_price = m.get("last_price", 0) or m.get("yes_bid", 0) or 0
            no_ask = m.get("no_ask", 0)
            no_price = no_ask if no_ask else (100 - yes_price if yes_price else 0)
            # Determine which team
            team_side = None
            if ha in title or hn in title:
                team_side = "home"
            elif aa in title or an in title:
                team_side = "away"
            matches.append({
                "ticker": m.get("ticker", ""),
                "title": m.get("title", ""),
                "spread_val": spread_val,
                "yes_price": yes_price,
                "no_price": no_price,
                "no_ask": no_ask,
                "team_side": team_side,
            })
    matches.sort(key=lambda x: x["spread_val"], reverse=True)
    return matches

def find_ml_price_for_team(home_abbrev, away_abbrev, fav_side, kalshi_ml_data):
    ha = home_abbrev.upper()
    aa = away_abbrev.upper()
    for key, val in kalshi_ml_data.items():
        tk = val.get("ticker", "").upper()
        if ha in tk and aa in tk:
            fav_code = ha if fav_side == "home" else aa
            if tk.endswith(fav_code):
                return val.get("yes_price", None), val.get("ticker", None)
            else:
                yp = val.get("yes_price", 0)
                return (100 - yp if yp else None), val.get("ticker", None)
    return None, None

# ── 9-Factor Edge Model ──

def calc_advanced_edge(game, b2b_teams, summary=None, injuries=None):
    edges = []
    total = 0.0
    home = game["home"]
    away = game["away"]
    home_rec = game.get("home_record", "0-0")
    away_rec = game.get("away_record", "0-0")

    # 1. ESPN BPI
    bpi_home, bpi_away = 0.5, 0.5
    if summary:
        bpi_home, bpi_away = parse_predictor(summary)
    bpi_edge = (bpi_home - 0.5) * 20
    edges.append({"factor": "ESPN BPI", "value": round(bpi_edge, 1), "detail": f"Home {bpi_home:.0%} / Away {bpi_away:.0%}"})
    total += bpi_edge

    # 2. BPI vs Vegas gap
    home_ml = game.get("home_ml", 0)
    vegas_implied = american_to_implied_prob(home_ml) if home_ml else None
    if vegas_implied and bpi_home:
        gap = (bpi_home - vegas_implied) * 100
        if abs(gap) >= 3:
            gap_edge = gap * 0.15
            edges.append({"factor": "BPI vs Vegas Gap", "value": round(gap_edge, 1), "detail": f"Gap: {gap:+.1f}%"})
            total += gap_edge
        else:
            edges.append({"factor": "BPI vs Vegas Gap", "value": 0.0, "detail": "Aligned"})
    else:
        edges.append({"factor": "BPI vs Vegas Gap", "value": 0.0, "detail": "N/A"})

    # 3. Home court
    hca = HOME_COURT_ADV / 2
    edges.append({"factor": "Home Court", "value": round(hca, 1), "detail": f"+{hca:.1f} pts"})
    total += hca

    # 4. Records
    h_pct = _parse_win_pct(home_rec) or 0.5
    a_pct = _parse_win_pct(away_rec) or 0.5
    rec_edge = (h_pct - a_pct) * 10
    edges.append({"factor": "Records", "value": round(rec_edge, 1), "detail": f"Home {h_pct:.3f} / Away {a_pct:.3f}"})
    total += rec_edge

    # 5. Net rating
    net_edge = 0.0
    if summary:
        home_stats, away_stats = parse_team_stats_from_summary(summary)
        try:
            h_off = float(home_stats.get("avgPoints", home_stats.get("points", "0")).replace(",", ""))
            h_def = float(away_stats.get("avgPoints", away_stats.get("points", "0")).replace(",", ""))
            a_off = float(away_stats.get("avgPoints", away_stats.get("points", "0")).replace(",", ""))
            a_def = float(home_stats.get("avgPoints", home_stats.get("points", "0")).replace(",", ""))
            h_net = h_off - h_def
            a_net = a_off - a_def
            net_edge = (h_net - a_net) * 0.3
        except:
            pass
    edges.append({"factor": "Net Rating", "value": round(net_edge, 1), "detail": f"{net_edge:+.1f}"})
    total += net_edge

    # 6. B2B fatigue
    b2b_edge = 0.0
    if home in b2b_teams:
        b2b_edge -= 2.5
    if away in b2b_teams:
        b2b_edge += 2.5
    detail_b2b = ""
    if home in b2b_teams and away in b2b_teams:
        detail_b2b = "Both B2B"
    elif home in b2b_teams:
        detail_b2b = f"{home} B2B"
    elif away in b2b_teams:
        detail_b2b = f"{away} B2B"
    else:
        detail_b2b = "Neither B2B"
    edges.append({"factor": "B2B Fatigue", "value": round(b2b_edge, 1), "detail": detail_b2b})
    total += b2b_edge

    # 7. PPG
    ppg_edge = 0.0
    if summary:
        try:
            home_stats, away_stats = parse_team_stats_from_summary(summary)
            h_ppg = float(home_stats.get("avgPoints", "0").replace(",", ""))
            a_ppg = float(away_stats.get("avgPoints", "0").replace(",", ""))
            ppg_edge = (h_ppg - a_ppg) * 0.3
        except:
            pass
    edges.append({"factor": "PPG Gap", "value": round(ppg_edge, 1), "detail": f"{ppg_edge:+.1f}"})
    total += ppg_edge

    # 8. Injuries
    inj_edge = 0.0
    inj_detail = "N/A"
    if injuries:
        home_leaders = _get_team_leaders(summary, "home") if summary else []
        away_leaders = _get_team_leaders(summary, "away") if summary else []
        home_inj = injuries.get(home, [])
        away_inj = injuries.get(away, [])
        parts = []
        for inj in home_inj:
            status = (inj.get("status", "") or "").lower()
            name = inj.get("name", "")
            is_star = _is_star_player(name, home_leaders)
            if "out" in status:
                inj_edge -= 4.0 if is_star else 1.0
                parts.append(f"{name} OUT{'⭐' if is_star else ''}")
            elif "day" in status or "dtd" in status:
                inj_edge -= 0.5
                parts.append(f"{name} DTD")
        for inj in away_inj:
            status = (inj.get("status", "") or "").lower()
            name = inj.get("name", "")
            is_star = _is_star_player(name, away_leaders)
            if "out" in status:
                inj_edge += 4.0 if is_star else 1.0
                parts.append(f"{name} OUT{'⭐' if is_star else ''}")
            elif "day" in status or "dtd" in status:
                inj_edge += 0.5
                parts.append(f"{name} DTD")
        inj_detail = ", ".join(parts[:4]) if parts else "No key injuries"
    edges.append({"factor": "Injuries", "value": round(inj_edge, 1), "detail": inj_detail})
    total += inj_edge

    # 9. 3PT
    tpt_edge = 0.0
    if summary:
        try:
            home_stats, away_stats = parse_team_stats_from_summary(summary)
            h3 = home_stats.get("threePointFieldGoalPct", "0")
            a3 = away_stats.get("threePointFieldGoalPct", "0")
            h3m = home_stats.get("threePointFieldGoalsMade", "0")
            a3m = away_stats.get("threePointFieldGoalsMade", "0")
            pct_gap = float(h3) - float(a3)
            made_gap = float(h3m) - float(a3m)
            tpt_edge = pct_gap * 0.15 + made_gap * 0.3
        except:
            pass
    edges.append({"factor": "3PT", "value": round(tpt_edge, 1), "detail": f"{tpt_edge:+.1f}"})
    total += tpt_edge

    # Strength
    abs_total = abs(total)
    if abs_total >= 8:
        strength = "🔴 STRONG"
    elif abs_total >= 4:
        strength = "🟡 MODERATE"
    elif abs_total >= 1.5:
        strength = "🟢 LEAN"
    else:
        strength = "⚪ TOSS-UP"

    side = "home" if total >= 0 else "away"
    pick = home if side == "home" else away

    return {
        "edges": edges, "score": round(total, 1), "pick": pick,
        "side": side, "strength": strength, "bpi": bpi_home,
    }

# ── Possession Tracker ──

def infer_possession(plays, away, home):
    if not plays:
        return None, None
    last = plays[-1]
    text = (last.get("text", "") or "").lower()
    play_type = (last.get("play_type", "") or "").lower()
    team_id = str(last.get("team_id", ""))
    # PRIMARY: match team_id to ESPN_TEAM_IDS
    acting_team = None
    if team_id:
        for name, eid in ESPN_TEAM_IDS.items():
            if str(eid) == team_id:
                acting_team = name
                break
    # FALLBACK: text matching
    if not acting_team:
        home_lower = home.lower()
        away_lower = away.lower()
        home_code = KALSHI_CODES.get(home, "").lower()
        away_code = KALSHI_CODES.get(away, "").lower()
        if home_lower in text or home_code in text:
            acting_team = home
        elif away_lower in text or away_code in text:
            acting_team = away
    if not acting_team:
        return "UNKNOWN", None
    other_team = home if acting_team == away else away
    # Determine possession from play type
    if any(w in play_type for w in ["made", "makes", "dunk", "layup"]) or any(w in text for w in ["makes", "made shot", "dunk", "layup"]):
        return other_team, f"⬆️ {other_team} ball (after score)"
    if "defensive rebound" in text or "defensive rebound" in play_type:
        return acting_team, f"🏀 {acting_team} ball (def rebound)"
    if "offensive rebound" in text or "offensive rebound" in play_type:
        return acting_team, f"🏀 {acting_team} ball (off rebound)"
    if any(w in text for w in ["turnover", "steal"]) or "turnover" in play_type:
        return other_team, f"🔄 {other_team} ball (turnover)"
    if "miss" in text or "miss" in play_type:
        return "LOOSE", "🔁 LOOSE BALL (miss)"
    if "foul" in text or "foul" in play_type:
        return other_team, f"⚖️ {other_team} FT"
    return acting_team, f"🏀 {acting_team} ball"

# ── MOBILE CSS ──
MOBILE_CSS = """
<style>
@media(max-width:600px){
  .sb-score{font-size:36px!important}
  .sb-team{font-size:20px!important}
  .sb-period{font-size:16px!important}
  .alert-box{padding:10px!important;font-size:13px!important}
  .edge-box{padding:8px!important}
  table{font-size:13px!important}
  td{padding:8px!important}
}
</style>
"""

# ── Visual Components ──

def render_scoreboard(away, home, away_score, home_score, period, clock, away_record, home_record):
    ac = TEAM_COLORS.get(away, "#888")
    hc = TEAM_COLORS.get(home, "#888")
    aa = KALSHI_CODES.get(away, away[:3].upper())
    ha = KALSHI_CODES.get(home, home[:3].upper())
    period_text = f"Q{period}" if period <= 4 else f"OT{period - 4}" if period > 4 else ""
    html = f"""
    {MOBILE_CSS}
    <div style="background:#0f172a;border-radius:12px;padding:16px;max-width:100%;box-sizing:border-box;overflow-x:hidden">
      <div style="text-align:center;color:#fbbf24;font-weight:bold;font-size:clamp(16px,3vw,22px);margin-bottom:8px" class="sb-period">
        {period_text} {clock}
      </div>
      <table style="width:100%;table-layout:fixed;border-collapse:collapse">
        <tr style="border-bottom:1px solid #334155">
          <td style="color:{ac};font-weight:bold;font-size:clamp(18px,4vw,28px);padding:8px;word-wrap:break-word" class="sb-team">{aa}</td>
          <td style="color:#94a3b8;font-size:clamp(12px,2vw,16px);padding:8px">{away_record}</td>
          <td style="color:white;font-weight:bold;font-size:clamp(32px,8vw,52px);text-align:right;padding:8px" class="sb-score">{away_score}</td>
        </tr>
        <tr>
          <td style="color:{hc};font-weight:bold;font-size:clamp(18px,4vw,28px);padding:8px;word-wrap:break-word" class="sb-team">{ha}</td>
          <td style="color:#94a3b8;font-size:clamp(12px,2vw,16px);padding:8px">{home_record}</td>
          <td style="color:white;font-weight:bold;font-size:clamp(32px,8vw,52px);text-align:right;padding:8px" class="sb-score">{home_score}</td>
        </tr>
      </table>
    </div>
    """
    components.html(html, height=180)

def get_play_badge(last_play):
    if not last_play:
        return ""
    text = (last_play.get("text", "") or "").lower()
    play_type = (last_play.get("play_type", "") or "").lower()
    sv = last_play.get("score_value", 0)
    color = "#888"
    label = ""
    if "three" in text or "3pt" in text or sv == 3:
        color, label = "#22c55e", "3PT MADE!"
    elif any(w in text for w in ["makes", "made", "dunk", "layup"]) or sv > 0:
        if "free throw" in text:
            color, label = "#22c55e", "FT MADE"
        else:
            color, label = "#22c55e", "BUCKET!"
    elif "miss" in text:
        color, label = "#ef4444", "MISSED"
    elif "block" in text:
        color, label = "#f97316", "BLOCKED!"
    elif "turnover" in text or "steal" in text:
        color, label = "#f97316", "TURNOVER"
    elif "rebound" in text:
        color, label = "#3b82f6", "REBOUND"
    elif "foul" in text:
        color, label = "#eab308", "FOUL"
    elif "timeout" in text:
        color, label = "#a855f7", "TIMEOUT"
    if not label:
        return ""
    return f'<rect x="175" y="25" width="150" height="30" rx="6" fill="{color}" opacity="0.9"/><text x="250" y="45" text-anchor="middle" fill="white" font-size="13" font-weight="bold">{label}</text>'

def render_nba_court(away, home, away_score, home_score, period, clock, last_play):
    ac = TEAM_COLORS.get(away, "#888")
    hc = TEAM_COLORS.get(home, "#888")
    aa = KALSHI_CODES.get(away, away[:3].upper())
    ha = KALSHI_CODES.get(home, home[:3].upper())
    period_text = f"Q{period}" if period <= 4 else f"OT{period - 4}" if period > 4 else ""
    badge = get_play_badge(last_play)
    html = f"""
    {MOBILE_CSS}
    <div style="background:#1a1a2e;border-radius:12px;padding:12px;text-align:center;max-width:100%;box-sizing:border-box;overflow-x:hidden">
      <svg viewBox="0 0 500 280" style="width:100%;max-width:500px">
        <!-- Court -->
        <rect x="20" y="20" width="460" height="200" fill="#2d4a22" stroke="white" stroke-width="2" rx="8"/>
        <!-- Center -->
        <circle cx="250" cy="120" r="35" fill="none" stroke="white" stroke-width="1.5"/>
        <circle cx="250" cy="120" r="4" fill="white"/>
        <line x1="250" y1="20" x2="250" y2="220" stroke="white" stroke-width="1.5"/>
        <!-- Left 3pt arc -->
        <path d="M 20 50 Q 100 120 20 190" fill="none" stroke="white" stroke-width="1.5"/>
        <!-- Left key -->
        <rect x="20" y="70" width="70" height="100" fill="none" stroke="white" stroke-width="1.5"/>
        <!-- Left FT circle -->
        <circle cx="90" cy="120" r="25" fill="none" stroke="white" stroke-width="1" stroke-dasharray="4,4"/>
        <!-- Left hoop -->
        <circle cx="35" cy="120" r="8" fill="none" stroke="#ff6b35" stroke-width="3"/>
        <!-- Right 3pt arc -->
        <path d="M 480 50 Q 400 120 480 190" fill="none" stroke="white" stroke-width="1.5"/>
        <!-- Right key -->
        <rect x="410" y="70" width="70" height="100" fill="none" stroke="white" stroke-width="1.5"/>
        <!-- Right FT circle -->
        <circle cx="410" cy="120" r="25" fill="none" stroke="white" stroke-width="1" stroke-dasharray="4,4"/>
        <!-- Right hoop -->
        <circle cx="465" cy="120" r="8" fill="none" stroke="#ff6b35" stroke-width="3"/>
        <!-- Badge -->
        {badge}
        <!-- Away team box -->
        <rect x="40" y="228" width="90" height="48" rx="8" fill="{ac}"/>
        <text x="85" y="250" text-anchor="middle" fill="white" font-size="14" font-weight="bold">{aa}</text>
        <text x="85" y="270" text-anchor="middle" fill="white" font-size="18" font-weight="bold">{away_score}</text>
        <!-- Home team box -->
        <rect x="370" y="228" width="90" height="48" rx="8" fill="{hc}"/>
        <text x="415" y="250" text-anchor="middle" fill="white" font-size="14" font-weight="bold">{ha}</text>
        <text x="415" y="270" text-anchor="middle" fill="white" font-size="18" font-weight="bold">{home_score}</text>
        <!-- Period/Clock -->
        <text x="250" y="258" text-anchor="middle" fill="#ccc" font-size="14">{period_text} {clock}</text>
      </svg>
    </div>
    """
    components.html(html, height=320)

def get_play_icon(play_type, score_value):
    pt = (play_type or "").lower()
    if score_value and score_value > 0:
        return ("B", "#22c55e")
    if "miss" in pt:
        return ("X", "#ef4444")
    if "rebound" in pt:
        return ("R", "#3b82f6")
    if "turnover" in pt or "steal" in pt:
        return ("T", "#f97316")
    if "foul" in pt:
        return ("F", "#eab308")
    if "timeout" in pt:
        return ("TO", "#a855f7")
    return ("-", "#888")

# === END PART A — PASTE PART B BELOW THIS LINE ===
# ── PART B: UI LAYER — paste directly below Part A ──

# ── 1. Fetch All Data ──
games = fetch_espn_games()
kalshi_ml_data = fetch_kalshi_ml()
kalshi_spreads_parsed, kalshi_spread_list = fetch_kalshi_spreads_raw()
injuries = fetch_injuries()
b2b_teams = fetch_yesterday_teams()

# ── 2. Categorize Games ──
live_games = [g for g in games if g['status'] in ['STATUS_IN_PROGRESS','STATUS_HALFTIME','STATUS_END_PERIOD'] or (g['period']>0 and g['status'] not in ['STATUS_FINAL','STATUS_FULL_TIME'])]
scheduled_games = [g for g in games if g['status']=='STATUS_SCHEDULED' and g['period']==0]
final_games = [g for g in games if g['status'] in ['STATUS_FINAL','STATUS_FULL_TIME']]

# ── 3. Run Sniper + Comeback Checks ──
for g in live_games:
    sniper_result = check_spread_sniper(g, kalshi_spread_list, kalshi_ml_data)
    if sniper_result:
        st.session_state.sniper_alerts.append(sniper_result)
    comeback_result = check_comeback(g, kalshi_ml_data)
    if comeback_result:
        st.session_state.comeback_alerts.append(comeback_result)

# ── 4. Header ──
st.title("BIGSNAPSHOT NBA EDGE FINDER")
st.caption(f"v{VERSION} | {now.strftime('%A, %B %d %Y %-I:%M %p ET')} | 9-Factor Edge + Spread Sniper + Comeback Scanner")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Today's Games", len(games))
c2.metric("Live Now", len(live_games))
c3.metric("Scheduled", len(scheduled_games))
c4.metric("Final", len(final_games))
st.divider()

# ── 5. PACE SCANNER ──
st.subheader("PACE SCANNER")
pace_data = []
for g in live_games:
    if g['minutes_played'] >= 6:
        ts = g['total_score']
        mp = g['minutes_played']
        pace = round(ts / mp, 2) if mp > 0 else 0
        plabel, pcolor = get_pace_label(pace)
        proj = calc_projection(ts, mp)
        pace_data.append({
            "name": f"{g['away']} @ {g['home']}",
            "status": f"Q{g['period']} {g['clock']}" if g['period'] <= 4 else f"OT{g['period']-4} {g['clock']}",
            "total": ts, "pace": pace, "pace_label": plabel, "pace_color": pcolor, "proj": proj
        })
pace_data.sort(key=lambda x: x['pace'])
if pace_data:
    for pd_item in pace_data:
        pc1, pc2, pc3, pc4 = st.columns(4)
        pc1.markdown(f"**{pd_item['name']}**")
        pc2.markdown(f"{pd_item['status']} | {pd_item['total']} pts")
        pc3.markdown(f"<span style='color:{pd_item['pace_color']}'>{pd_item['pace_label']} ({pd_item['pace']:.2f})</span>", unsafe_allow_html=True)
        pc4.markdown(f"Proj: **{pd_item['proj']}**")
else:
    st.info("No live games with 6+ minutes played")
st.divider()

# ── 6. Create Tabs ──
tab_edge, tab_spread, tab_live, tab_cushion = st.tabs(["Edge Finder", "Spread Sniper", "Live Monitor", "Cushion Scanner"])

# ════════════════════════════════════════════════
# TAB 1: EDGE FINDER
# ════════════════════════════════════════════════
with tab_edge:
    # Section A: Pre-Game 9-Factor Edge Model
    st.subheader("PRE-GAME ALIGNMENT — 9-Factor Edge Model")
    with st.expander("How Edges Are Rated"):
        st.markdown("""
**9 Factors Analyzed:**
1. ESPN BPI — pre-game win probability
2. BPI vs Vegas Gap — when BPI disagrees with the line
3. Home Court — standard home advantage
4. Records — season win percentage comparison
5. Net Rating — offensive vs defensive efficiency gap
6. B2B Fatigue — back-to-back schedule penalty
7. PPG Gap — scoring output difference
8. Injuries — star/role player availability impact
9. 3PT — three-point shooting edge

**Strength Table:**
| Score | Rating |
|-------|--------|
| ≥ 8.0 | 🔴 STRONG |
| ≥ 4.0 | 🟡 MODERATE |
| ≥ 1.5 | 🟢 LEAN |
| < 1.5 | ⚪ TOSS-UP |

Only STRONG and MODERATE edges are shown below.
""")
    st.caption("ESPN BPI + Vegas + Live Stats | Only showing STRONG + MODERATE edges")

    edge_results = []
    for g in scheduled_games:
        summary = fetch_game_summary(g['game_id'])
        edge = calc_advanced_edge(g, b2b_teams, summary=summary, injuries=injuries)
        if edge['strength'] in ['🔴 STRONG', '🟡 MODERATE']:
            edge_results.append({"game": g, "edge": edge, "summary": summary})

    edge_results.sort(key=lambda x: (0 if 'STRONG' in x['edge']['strength'] else 1, -abs(x['edge']['score'])))

    if not edge_results:
        st.info("No STRONG or MODERATE edges found in today's scheduled games.")
    else:
        st.markdown(f"**{len(edge_results)} actionable edge(s) found**")
        if st.button("ADD ALL EDGE PICKS", key="add_all_edges", use_container_width=True):
            for er in edge_results:
                g = er['game']
                e = er['edge']
                pos = {
                    'id': str(uuid.uuid4()), 'game': f"{g['away']} @ {g['home']}",
                    'pick': e['pick'], 'type': 'ML', 'line': '-',
                    'entry': 50, 'contracts': 10, 'away': g['away'], 'home': g['home'],
                    'game_id': g['game_id']
                }
                st.session_state.positions.append(pos)
            st.rerun()

        for er in edge_results:
            g = er['game']
            e = er['edge']
            border_color = "#22c55e" if "STRONG" in e['strength'] else "#f97316"
            spread_str = g['vegas_odds'].get('spread', 'N/A')
            ou_str = g['vegas_odds'].get('overUnder', 'N/A')
            st.markdown(f"""
<div style="border-left:4px solid {border_color};background:#1a1a2e;padding:clamp(8px,2vw,16px);border-radius:8px;margin-bottom:8px;max-width:100%;box-sizing:border-box;overflow-x:hidden">
  <span style="background:{border_color};color:white;padding:2px 8px;border-radius:4px;font-size:clamp(11px,2.5vw,14px);font-weight:bold">{e['strength']}</span>
  <span style="color:white;font-size:clamp(14px,3.5vw,18px);font-weight:bold;margin-left:8px">{g['away']} @ {g['home']}</span><br>
  <span style="color:#94a3b8;font-size:clamp(11px,2.5vw,14px)">Spread: {spread_str} | O/U: {ou_str} | {g['game_time']}</span><br>
  <span style="color:#fbbf24;font-size:clamp(14px,3.5vw,18px);font-weight:bold">PICK: {e['pick']} ({e['score']:+.1f})</span>
</div>
""", unsafe_allow_html=True)
            ec1, ec2 = st.columns(2)
            with ec1:
                link = get_kalshi_game_link(g['away'], g['home'])
                st.link_button("Trade on Kalshi", link, use_container_width=True)
            with ec2:
                already = any(p.get('game_id') == g['game_id'] for p in st.session_state.positions)
                if already:
                    st.success("Tracked ✓")
                else:
                    if st.button("Track", key=f"track_{g['game_id']}", use_container_width=True):
                        st.session_state.positions.append({
                            'id': str(uuid.uuid4()), 'game': f"{g['away']} @ {g['home']}",
                            'pick': e['pick'], 'type': 'ML', 'line': '-',
                            'entry': 50, 'contracts': 10, 'away': g['away'], 'home': g['home'],
                            'game_id': g['game_id']
                        })
                        st.rerun()
            with st.expander("View Breakdown"):
                for edge_item in e['edges']:
                    val = edge_item['value']
                    fname = edge_item['factor']
                    detail = edge_item['detail']
                    if "injur" in fname.lower() and ("star" in detail.lower() or "out" in detail.lower()):
                        color = "#e74c3c"
                        prefix = "🔴 "
                    elif "3pt" in fname.lower():
                        color = "#3498db"
                        prefix = "🔵 "
                    elif "gap" in fname.lower():
                        color = "#2ecc71"
                        prefix = "🟢 "
                    elif "fatigue" in fname.lower() or "b2b" in fname.lower():
                        color = "#e67e22"
                        prefix = "🟠 "
                    else:
                        color = "#ccc"
                        prefix = "- "
                    st.markdown(f"<span style='color:{color}'>{prefix}{fname}: {val:+.1f} — {detail}</span>", unsafe_allow_html=True)
            st.divider()

    # Section B: Vegas vs Kalshi Mispricing Alert
    st.subheader("VEGAS vs KALSHI MISPRICING ALERT")
    st.caption("Comparing Vegas implied probabilities to Kalshi prices — edges ≥5% shown")
    mispricing_list = []
    for g in games:
        if g['status'] in ['STATUS_FINAL', 'STATUS_FULL_TIME']:
            continue
        key = f"{g['away']}@{g['home']}"
        home_ml = g.get('home_ml', 0)
        away_ml = g.get('vegas_odds', {}).get('awayML', 0)
        vegas_home_pct = None
        vegas_away_pct = None
        if home_ml and away_ml:
            h_raw = american_to_implied_prob(home_ml)
            a_raw = american_to_implied_prob(away_ml)
            if h_raw and a_raw:
                total_raw = h_raw + a_raw
                vegas_home_pct = round((h_raw / total_raw) * 100, 1)
                vegas_away_pct = round((a_raw / total_raw) * 100, 1)
        elif g.get('vegas_odds', {}).get('spread'):
            spread_str = str(g['vegas_odds']['spread'])
            try:
                spread_num = float(re.search(r'[-+]?\d+\.?\d*', spread_str).group())
                vegas_home_pct = max(10, min(90, round(50 - spread_num * 2.8, 1)))
                vegas_away_pct = round(100 - vegas_home_pct, 1)
            except:
                continue
        else:
            continue
        kalshi_info = kalshi_ml_data.get(key, {})
        kalshi_home = kalshi_info.get('home_implied', 0)
        kalshi_away = kalshi_info.get('away_implied', 0)
        if not kalshi_home and not kalshi_away:
            continue
        summary_mp = fetch_game_summary(g['game_id'])
        bpi_home_pct, bpi_away_pct = (0.5, 0.5)
        if summary_mp:
            bpi_home_pct, bpi_away_pct = parse_predictor(summary_mp)
        home_gap = vegas_home_pct - kalshi_home if kalshi_home else 0
        away_gap = vegas_away_pct - kalshi_away if kalshi_away else 0
        if abs(home_gap) >= 5:
            side_label = "HOME" if home_gap > 0 else "AWAY"
            buy_action = "YES" if home_gap > 0 else "NO"
            team_pick = g['home'] if home_gap > 0 else g['away']
            mispricing_list.append({
                "game": g, "key": key, "edge": abs(home_gap),
                "vegas_pct": vegas_home_pct if home_gap > 0 else vegas_away_pct,
                "kalshi_price": kalshi_home if home_gap > 0 else kalshi_away,
                "bpi_pct": round(bpi_home_pct * 100, 1) if home_gap > 0 else round(bpi_away_pct * 100, 1),
                "buy_action": buy_action, "team": team_pick, "side": side_label,
                "ticker": kalshi_info.get('ticker', '')
            })
        elif abs(away_gap) >= 5:
            side_label = "AWAY" if away_gap > 0 else "HOME"
            buy_action = "YES" if away_gap > 0 else "NO"
            team_pick = g['away'] if away_gap > 0 else g['home']
            mispricing_list.append({
                "game": g, "key": key, "edge": abs(away_gap),
                "vegas_pct": vegas_away_pct if away_gap > 0 else vegas_home_pct,
                "kalshi_price": kalshi_away if away_gap > 0 else kalshi_home,
                "bpi_pct": round(bpi_away_pct * 100, 1) if away_gap > 0 else round(bpi_home_pct * 100, 1),
                "buy_action": buy_action, "team": team_pick, "side": side_label,
                "ticker": kalshi_info.get('ticker', '')
            })

    mispricing_list.sort(key=lambda x: x['edge'], reverse=True)
    if not mispricing_list:
        st.info("No mispricings ≥5% detected right now.")
    else:
        for mp in mispricing_list:
            g = mp['game']
            edge_val = mp['edge']
            if edge_val >= 10:
                edge_color = "#ff6b6b"
                edge_tag = "STRONG"
            elif edge_val >= 7:
                edge_color = "#22c55e"
                edge_tag = "GOOD"
            else:
                edge_color = "#eab308"
                edge_tag = "EDGE"
            action_color = "#22c55e" if mp['buy_action'] == "YES" else "#ef4444"
            status_text = f"Q{g['period']} {g['clock']}" if g['state'] == 'in' else g.get('game_time', 'Scheduled')
            st.markdown(f"""
<div style="background:#1a1a2e;padding:clamp(8px,2vw,16px);border-radius:8px;border-left:4px solid {edge_color};margin-bottom:8px;max-width:100%;box-sizing:border-box;overflow-x:hidden">
  <div style="color:white;font-size:clamp(14px,3.5vw,18px);font-weight:bold;word-wrap:break-word">{g['away']} @ {g['home']} <span style="color:#94a3b8;font-size:clamp(11px,2.5vw,14px)">{status_text}</span></div>
  <div style="margin-top:6px">
    <span style="background:{action_color};color:white;padding:2px 8px;border-radius:4px;font-weight:bold;font-size:clamp(11px,2.5vw,14px)">BUY {mp['buy_action']} {mp['team']}</span>
    <span style="background:{edge_color};color:white;padding:2px 8px;border-radius:4px;font-weight:bold;margin-left:4px;font-size:clamp(11px,2.5vw,14px)">{edge_tag} +{edge_val:.1f}%</span>
  </div>
  <table style="width:100%;table-layout:fixed;margin-top:8px;color:#ccc;font-size:clamp(11px,2.5vw,14px)">
    <tr><td>Vegas</td><td>Kalshi</td><td>BPI</td><td>Edge</td></tr>
    <tr style="color:white;font-weight:bold"><td>{mp['vegas_pct']:.1f}%</td><td>{mp['kalshi_price']}¢</td><td>{mp['bpi_pct']:.1f}%</td><td style="color:{edge_color}">+{edge_val:.1f}%</td></tr>
  </table>
</div>
""", unsafe_allow_html=True)
            link = get_kalshi_game_link(g['away'], g['home'])
            st.link_button(f"Trade {mp['team']} on Kalshi", link, use_container_width=True)

    # Section C: Injury Report
    st.subheader("INJURY REPORT")
    today_teams = set()
    for g in games:
        today_teams.add(g['away'])
        today_teams.add(g['home'])
    has_injuries = False
    for team in sorted(today_teams):
        team_inj = injuries.get(team, [])
        if not team_inj:
            continue
        out_players = [i for i in team_inj if 'out' in (i.get('status', '') or '').lower()]
        dtd_players = [i for i in team_inj if 'day' in (i.get('status', '') or '').lower() or 'doubtful' in (i.get('status', '') or '').lower()]
        if out_players or dtd_players:
            has_injuries = True
            for p in out_players:
                st.markdown(f"**{team}** [OUT] {p['name']} — {p.get('status', '')}")
            for p in dtd_players:
                st.markdown(f"**{team}** [DTD] {p['name']} — {p.get('status', '')}")
    if not has_injuries:
        st.info("No significant injuries reported for today's games.")

    # Section D: Position Tracker
    st.subheader("POSITION TRACKER")
    with st.expander("ADD NEW POSITION", expanded=False):
        game_options = [f"{g['away']} @ {g['home']}" for g in games]
        if game_options:
            pt1, pt2 = st.columns(2)
            with pt1:
                sel_game = st.selectbox("Game", game_options, key="pos_game")
            with pt2:
                bet_type = st.selectbox("Bet Type", ["ML", "Totals", "Spread"], key="pos_type")
            matched_game = next((g for g in games if f"{g['away']} @ {g['home']}" == sel_game), None)
            pt3, pt4 = st.columns(2)
            with pt3:
                if bet_type == "ML":
                    pick_opts = [matched_game['away'], matched_game['home']] if matched_game else ["Team A", "Team B"]
                    pick = st.selectbox("Pick", pick_opts, key="pos_pick")
                elif bet_type == "Totals":
                    pick = st.selectbox("Pick", ["YES (Over)", "NO (Under)"], key="pos_pick")
                else:
                    pick_opts = [matched_game['away'], matched_game['home']] if matched_game else ["Team A", "Team B"]
                    pick = st.selectbox("Pick", pick_opts, key="pos_pick")
            with pt4:
                if bet_type == "Totals":
                    line = st.selectbox("Line", [str(t) for t in THRESHOLDS], key="pos_line")
                elif bet_type == "Spread":
                    line = st.selectbox("Line", ["5.5", "7.5", "10.5", "13.5", "15.5", "20.5"], key="pos_line")
                else:
                    line = "-"
                    st.text_input("Line", value="-", disabled=True, key="pos_line_ml")
            pt5, pt6 = st.columns(2)
            with pt5:
                entry = st.number_input("Entry Price (¢)", min_value=1, max_value=99, value=50, key="pos_entry")
            with pt6:
                contracts = st.number_input("Contracts", min_value=1, max_value=10000, value=10, key="pos_contracts")
            cost = round(entry * contracts / 100, 2)
            win = round((100 - entry) * contracts / 100, 2)
            st.caption(f"Cost: ${cost:.2f} | Win: ${win:.2f}")
            if st.button("ADD POSITION", key="add_pos", use_container_width=True):
                st.session_state.positions.append({
                    'id': str(uuid.uuid4()), 'game': sel_game,
                    'pick': pick, 'type': bet_type, 'line': line if bet_type != "ML" else "-",
                    'entry': entry, 'contracts': contracts,
                    'away': matched_game['away'] if matched_game else "",
                    'home': matched_game['home'] if matched_game else "",
                    'game_id': matched_game['game_id'] if matched_game else ""
                })
                st.rerun()
        else:
            st.info("No games available to track.")

    if st.session_state.positions:
        for pos in st.session_state.positions:
            p1, p2, p3, p4, p5 = st.columns([3, 2, 2, 2, 1])
            with p1:
                st.markdown(f"**{pos['game']}**")
                mg = next((g for g in games if g.get('game_id') == pos.get('game_id')), None)
                if mg and mg['state'] == 'in':
                    st.caption(f"LIVE Q{mg['period']} {mg['clock']} | {mg['away_score']}-{mg['home_score']}")
            with p2:
                line_str = f" {pos['line']}" if pos['line'] != "-" else ""
                st.markdown(f"{pos['pick']} {pos['type']}{line_str}")
            with p3:
                cost = round(pos['entry'] * pos['contracts'] / 100, 2)
                st.markdown(f"{pos['contracts']}x @ {pos['entry']}¢")
                st.caption(f"${cost:.2f}")
            with p4:
                link = get_kalshi_game_link(pos.get('away', ''), pos.get('home', ''))
                st.link_button("Kalshi", link, use_container_width=True)
            with p5:
                if st.button("X", key=f"del_{pos['id']}", use_container_width=True):
                    remove_position(pos['id'])
                    st.rerun()
        if st.button("CLEAR ALL POSITIONS", key="clear_all_pos", use_container_width=True):
            st.session_state.positions = []
            st.rerun()
    else:
        st.caption("No positions tracked yet.")

    # Section E: All Games Today
    st.subheader("ALL GAMES TODAY")
    for g in games:
        if g['status'] in ['STATUS_FINAL', 'STATUS_FULL_TIME']:
            border = "#666"
            info_str = f"FINAL: {g['away_score']}-{g['home_score']}"
        elif g['state'] == 'in':
            border = "#22c55e"
            ptext = f"Q{g['period']}" if g['period'] <= 4 else f"OT{g['period']-4}"
            info_str = f"LIVE {ptext} {g['clock']} | {g['away_score']}-{g['home_score']}"
        else:
            border = "#888"
            spread_str = g.get('vegas_odds', {}).get('spread', '')
            info_str = f"{g.get('game_datetime', '')} | {spread_str}"
        st.markdown(f"""
<div style="border-left:4px solid {border};padding:clamp(6px,2vw,12px);margin-bottom:4px;max-width:100%;box-sizing:border-box;overflow-x:hidden">
  <span style="color:white;font-size:clamp(13px,3vw,16px);font-weight:bold;word-wrap:break-word">{g['away']} @ {g['home']}</span>
  <span style="color:#94a3b8;font-size:clamp(11px,2.5vw,14px);margin-left:8px">{info_str}</span>
</div>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════
# TAB 2: SPREAD SNIPER
# ════════════════════════════════════════════════
with tab_spread:
    # Section A: Spread Sniper Alerts
    st.subheader("SPREAD SNIPER — LIVE ALERTS")
    with st.expander("How Spread Sniping Works"):
        st.markdown("""
**Strategy:** When the underdog builds a big lead, the favorite's spread markets become cheap. We buy NO on large spreads, betting the favorite won't win by that much (because they're currently losing).

**Quarter Thresholds (underdog lead required to fire):**
| Quarter | Lead Required |
|---------|--------------|
| Q1 | 7+ points |
| Q2 | 8+ points |
| Q3 | 10+ points |
| Q4 | 13+ points |

**Bracket Rating:**
| NO Price | Rating |
|----------|--------|
| ≤ 40¢ | 🔥 FIRE |
| 41-60¢ | ✅ GOOD |
| 61-75¢ | ⚠️ OK |
| 76-85¢ | 🟠 WARN |
""")
    st.caption(f"Scanning live games for underdog leads meeting quarter thresholds")

    if st.session_state.sniper_alerts:
        for alert in st.session_state.sniper_alerts:
            ag = alert['game']
            ptext = f"Q{ag['period']}" if ag['period'] <= 4 else f"OT{ag['period']-4}"
            st.markdown(f"""
<div style="border-left:4px solid #ef4444;background:#1a1a2e;padding:clamp(8px,2vw,16px);border-radius:8px;margin-bottom:8px;max-width:100%;box-sizing:border-box;overflow-x:hidden" class="alert-box">
  <div style="color:#ef4444;font-size:clamp(16px,4vw,22px);font-weight:bold">🎯 SPREAD SNIPER — {ptext} {ag['clock']}</div>
  <div style="color:white;font-size:clamp(14px,3.5vw,18px);margin-top:4px">{ag['away']} {ag['away_score']} — {ag['home']} {ag['home_score']}</div>
  <div style="color:#fbbf24;font-size:clamp(12px,3vw,16px);margin-top:4px">
    {alert['dog_name']} ({alert['dog_abbrev']}) leads by {alert['dog_lead']} | Record: {alert.get('dog_record','')}
  </div>
  <div style="color:#94a3b8;font-size:clamp(11px,2.5vw,14px)">
    Favorite: {alert['fav_name']} ({alert['fav_abbrev']}) | Record: {alert.get('fav_record','')}
  </div>
</div>
""", unsafe_allow_html=True)
            if alert.get('fav_wp'):
                wp = alert['fav_wp']
                wp_edge = alert.get('wp_edge', 0)
                wp_color = "#22c55e" if wp_edge >= MIN_WP_EDGE else "#eab308"
                st.markdown(f"<span style='color:{wp_color}'>ESPN WP: {wp:.0f}% | WP Edge: {wp_edge:+.0f}%</span>", unsafe_allow_html=True)

            if alert.get('no_markets'):
                st.warning("No spread markets found — check Kalshi manually")
            elif not alert.get('spreads'):
                st.info(f"All bracket NO prices exceed {MAX_NO_PRICE}¢ ceiling")
            else:
                st.markdown("**ACTIONABLE BRACKETS:**")
                best = None
                for sp in alert['spreads']:
                    no_price = sp.get('effective_no_price', sp.get('no_price', 0))
                    swing = sp.get('spread_val', 0) + alert.get('dog_lead', 0)
                    if no_price <= 40:
                        tag, tcolor = "🔥 FIRE", "#ef4444"
                    elif no_price <= 60:
                        tag, tcolor = "✅ GOOD", "#22c55e"
                    elif no_price <= 75:
                        tag, tcolor = "⚠️ OK", "#eab308"
                    else:
                        tag, tcolor = "🟠 WARN", "#f97316"
                    st.markdown(f"""
<div style="background:#0f172a;padding:clamp(6px,2vw,12px);border-radius:6px;margin-bottom:4px;max-width:100%;box-sizing:border-box;overflow-x:hidden">
  <span style="background:{tcolor};color:white;padding:2px 6px;border-radius:4px;font-size:clamp(10px,2vw,13px);font-weight:bold">{tag}</span>
  <span style="color:white;font-size:clamp(12px,3vw,15px);margin-left:6px;word-wrap:break-word">{sp.get('title','')} | NO: {no_price}¢ | Swing: {swing:.0f}</span>
</div>
""", unsafe_allow_html=True)
                    if best is None or no_price < best.get('no_price', 999):
                        best = {'title': sp.get('title', ''), 'no_price': no_price, 'spread_val': sp.get('spread_val', 0)}

                if best:
                    st.markdown(f"""
<div style="border-left:4px solid #22c55e;background:#0f2a1a;padding:clamp(8px,2vw,12px);border-radius:8px;margin-top:8px;max-width:100%;box-sizing:border-box;overflow-x:hidden">
  <span style="color:#22c55e;font-weight:bold;font-size:clamp(12px,3vw,16px)">BEST BET: {best['title']} — NO @ {best['no_price']}¢</span>
</div>
""", unsafe_allow_html=True)

            link = get_kalshi_spread_link(ag['away'], ag['home'])
            st.link_button("Trade Spread on Kalshi", link, use_container_width=True)
            st.divider()
    else:
        st.info("No spread sniper alerts yet — scanning every 24 seconds...")

    # Section B: Comeback Scanner
    st.subheader("COMEBACK SCANNER")
    st.caption("Tracking favorites who fall behind by 10+ points — fires when they close within 2")

    if st.session_state.comeback_tracking:
        st.markdown("**Currently Tracking:**")
        for gid, ct in st.session_state.comeback_tracking.items():
            mg = next((g for g in live_games if g['game_id'] == gid), None)
            if not mg:
                continue
            fav_side = ct.get('fav_side', 'home')
            fav_name = mg['home'] if fav_side == 'home' else mg['away']
            fav_abbrev = KALSHI_CODES.get(fav_name, fav_name[:3].upper())
            fav_score = mg['home_score'] if fav_side == 'home' else mg['away_score']
            opp_score = mg['away_score'] if fav_side == 'home' else mg['home_score']
            margin = fav_score - opp_score
            if margin > 0:
                status_str = f"leads by {margin}"
            elif margin == 0:
                status_str = "TIED"
            else:
                status_str = f"down {abs(margin)}"
            color = "#22c55e" if margin >= 0 else "#eab308"
            fired = "🔔 FIRED" if gid in st.session_state.comeback_alerted else ""
            st.markdown(f"<span style='color:{color}'>{fav_abbrev} — was down {ct['max_deficit']}, now {status_str} {fired}</span>", unsafe_allow_html=True)

    if st.session_state.comeback_alerts:
        for ca in st.session_state.comeback_alerts:
            cg = ca['game']
            ptext = f"Q{cg['period']}" if cg['period'] <= 4 else f"OT{cg['period']-4}"
            margin = ca.get('fav_margin', 0)
            if margin > 0:
                status_word = f"NOW LEADS BY {margin}"
            elif margin == 0:
                status_word = "NOW TIED"
            else:
                status_word = f"CLOSING IN (down {abs(margin)})"
            price = ca.get('fav_price')
            price_str = ""
            if price:
                if price <= 55:
                    price_str = f"<span style='color:#ef4444;font-weight:bold'>Kalshi ML: {price}¢ — MARKET LAGGING!</span>"
                elif price <= 70:
                    price_str = f"<span style='color:#eab308;font-weight:bold'>Kalshi ML: {price}¢</span>"
                else:
                    price_str = f"<span style='color:#ccc'>Kalshi ML: {price}¢</span>"
            wp_str = ""
            if ca.get('fav_wp'):
                wp_str = f"<div style='color:#22c55e;font-size:clamp(11px,2.5vw,14px)'>ESPN WP: {ca['fav_wp']:.0f}%</div>"
            st.markdown(f"""
<div style="border-left:4px solid #22c55e;background:#1a1a2e;padding:clamp(8px,2vw,16px);border-radius:8px;margin-bottom:8px;max-width:100%;box-sizing:border-box;overflow-x:hidden" class="alert-box">
  <div style="color:#22c55e;font-size:clamp(16px,4vw,22px);font-weight:bold">🔄 COMEBACK — {ptext} {cg['clock']}</div>
  <div style="color:white;font-size:clamp(14px,3.5vw,18px);margin-top:4px">{cg['away']} {cg['away_score']} — {cg['home']} {cg['home_score']}</div>
  <div style="color:#fbbf24;font-size:clamp(12px,3vw,16px);margin-top:4px">WAS DOWN {ca['max_deficit']} — {status_word}</div>
  <div style="margin-top:4px;font-size:clamp(12px,3vw,16px)">{price_str}</div>
  {wp_str}
  <div style="color:white;font-size:clamp(12px,3vw,15px);margin-top:6px">BUY <b>{ca['fav_name']}</b> ML if price hasn't caught up</div>
</div>
""", unsafe_allow_html=True)
            link = get_kalshi_game_link(cg['away'], cg['home'])
            st.link_button(f"Trade {ca['fav_name']} ML on Kalshi", link, use_container_width=True)
            st.divider()
    elif not st.session_state.comeback_tracking:
        st.info("Monitoring for favorite deficits of 10+ points...")

# ════════════════════════════════════════════════
# TAB 3: LIVE MONITOR
# ════════════════════════════════════════════════
with tab_live:
    st.subheader("LIVE EDGE MONITOR")
    if live_games:
        for g in live_games:
            st.markdown(f"### {g['away']} @ {g['home']}")
            render_scoreboard(g['away'], g['home'], g['away_score'], g['home_score'], g['period'], g['clock'], g['away_record'], g['home_record'])

            plays = fetch_plays(g['game_id'])
            lc1, lc2 = st.columns([3, 2])
            with lc1:
                last_play = plays[-1] if plays else None
                render_nba_court(g['away'], g['home'], g['away_score'], g['home_score'], g['period'], g['clock'], last_play)
                poss_team, poss_desc = infer_possession(plays, g['away'], g['home'])
                if poss_team and poss_desc:
                    poss_color = TEAM_COLORS.get(poss_team, "#888") if poss_team not in ["UNKNOWN", "LOOSE"] else "#eab308"
                    st.markdown(f"""
<div style="text-align:center;padding:6px;max-width:100%;box-sizing:border-box">
  <span style="color:{poss_color};font-weight:bold;font-size:clamp(12px,3vw,16px)">{poss_desc}</span>
</div>
""", unsafe_allow_html=True)

            with lc2:
                st.markdown("**LAST 10 PLAYS**")
                tts_on = st.checkbox("🔊 TTS", key=f"tts_{g['game_id']}")
                for idx, play in enumerate(reversed(plays)):
                    icon_letter, icon_color = get_play_icon(play.get('play_type', ''), play.get('score_value', 0))
                    ptext = f"Q{play['period']}" if play.get('period', 0) <= 4 else f"OT{play['period']-4}"
                    display_text = play.get('text', '')[:60]
                    st.markdown(f"""
<div style="border-left:3px solid {icon_color};padding:4px 8px;margin-bottom:3px;max-width:100%;box-sizing:border-box;overflow-x:hidden">
  <span style="color:{icon_color};font-weight:bold;font-size:clamp(11px,2.5vw,14px)">{icon_letter}</span>
  <span style="color:#94a3b8;font-size:clamp(10px,2vw,12px)">{ptext} {play.get('clock','')}</span>
  <span style="color:#ccc;font-size:clamp(11px,2.5vw,13px);word-wrap:break-word"> {display_text}</span>
</div>
""", unsafe_allow_html=True)
                    if idx == 0 and tts_on and display_text:
                        speak_play(display_text)

            # Pace stats + trade signals
            if g['minutes_played'] >= 6:
                ts = g['total_score']
                mp = g['minutes_played']
                pace = round(ts / mp, 2) if mp > 0 else 0
                proj = calc_projection(ts, mp)
                plabel, pcolor = get_pace_label(pace)
                lead = abs(g['home_score'] - g['away_score'])
                leader = g['home'] if g['home_score'] >= g['away_score'] else g['away']
                st.markdown(f"""
<div style="background:#0f172a;padding:clamp(8px,2vw,16px);border-radius:8px;display:flex;flex-wrap:wrap;gap:16px;justify-content:center;max-width:100%;box-sizing:border-box;overflow-x:hidden">
  <div style="text-align:center"><div style="color:#94a3b8;font-size:clamp(10px,2vw,12px)">Score</div><div style="color:white;font-weight:bold;font-size:clamp(14px,3.5vw,18px)">{ts}</div></div>
  <div style="text-align:center"><div style="color:#94a3b8;font-size:clamp(10px,2vw,12px)">Pace</div><div style="color:{pcolor};font-weight:bold;font-size:clamp(14px,3.5vw,18px)">{plabel} ({pace:.2f})</div></div>
  <div style="text-align:center"><div style="color:#94a3b8;font-size:clamp(10px,2vw,12px)">Projection</div><div style="color:white;font-weight:bold;font-size:clamp(14px,3.5vw,18px)">{proj}</div></div>
  <div style="text-align:center"><div style="color:#94a3b8;font-size:clamp(10px,2vw,12px)">Lead</div><div style="color:white;font-weight:bold;font-size:clamp(14px,3.5vw,18px)">{leader} +{lead}</div></div>
</div>
""", unsafe_allow_html=True)

                # MONEYLINE
                if lead >= 10:
                    ml_label = "STRONG" if lead >= 15 else "GOOD"
                    ml_link = get_kalshi_game_link(g['away'], g['home'])
                    st.link_button(f"🏀 {leader} ML — {ml_label} LEAD +{lead}", ml_link, use_container_width=True)
                else:
                    st.caption("Moneyline: Wait for larger lead (10+)")

                # TOTALS
                tc1, tc2 = st.columns(2)
                with tc1:
                    st.markdown("**YES (Over)**")
                    yes_found = False
                    rec_set = False
                    for thresh in sorted(THRESHOLDS):
                        cushion = proj - thresh
                        if cushion >= 6:
                            if cushion >= 20:
                                safety, scolor = "FORTRESS", "#22c55e"
                            elif cushion >= 12:
                                safety, scolor = "SAFE", "#22c55e"
                            else:
                                safety, scolor = "TIGHT", "#eab308"
                            rec_badge = ""
                            if not rec_set and cushion >= 12:
                                rec_badge = " *REC"
                                rec_set = True
                            st.markdown(f"<span style='color:{scolor}'>{safety} YES {thresh} | +{cushion:.0f}{rec_badge}</span>", unsafe_allow_html=True)
                            yes_found = True
                    if yes_found:
                        tl = get_kalshi_game_link(g['away'], g['home'])
                        st.link_button("Trade YES on Kalshi", tl, use_container_width=True)
                    else:
                        st.caption("No YES edges (cushion <6)")

                with tc2:
                    st.markdown("**NO (Under)**")
                    no_found = False
                    rec_set = False
                    for thresh in sorted(THRESHOLDS, reverse=True):
                        cushion = thresh - proj
                        if cushion >= 6:
                            if cushion >= 20:
                                safety, scolor = "FORTRESS", "#22c55e"
                            elif cushion >= 12:
                                safety, scolor = "SAFE", "#22c55e"
                            else:
                                safety, scolor = "TIGHT", "#eab308"
                            rec_badge = ""
                            if not rec_set and cushion >= 12:
                                rec_badge = " *REC"
                                rec_set = True
                            st.markdown(f"<span style='color:{scolor}'>{safety} NO {thresh} | +{cushion:.0f}{rec_badge}</span>", unsafe_allow_html=True)
                            no_found = True
                    if no_found:
                        tl = get_kalshi_game_link(g['away'], g['home'])
                        st.link_button("Trade NO on Kalshi", tl, use_container_width=True)
                    else:
                        st.caption("No NO edges (cushion <6)")
            else:
                st.caption("Waiting for 6+ minutes of play for pace data...")
            st.divider()
    else:
        st.info("No live games right now — check back during game time!")

# ════════════════════════════════════════════════
# TAB 4: CUSHION SCANNER
# ════════════════════════════════════════════════
with tab_cushion:
    st.subheader("CUSHION SCANNER (Totals)")
    cs1, cs2, cs3 = st.columns(3)
    with cs1:
        game_opts = ["All Games"] + [f"{g['away']} @ {g['home']}" for g in games]
        cush_game = st.selectbox("Game", game_opts, key="cush_game")
    with cs2:
        min_time = st.selectbox("Min Play Time", [8, 12, 16, 20, 24], index=1, key="cush_time")
    with cs3:
        cush_side = st.selectbox("Side", ["NO (Under)", "YES (Over)"], key="cush_side")

    is_no = "NO" in cush_side
    cushion_results = []

    for g in games:
        if g['status'] in ['STATUS_FINAL', 'STATUS_FULL_TIME']:
            continue
        if cush_game != "All Games" and f"{g['away']} @ {g['home']}" != cush_game:
            continue
        mp = g['minutes_played']
        proj = LEAGUE_AVG_TOTAL
        has_pace = False
        if mp >= 8:
            proj = calc_projection(g['total_score'], mp)
            has_pace = True
        elif g.get('vegas_odds', {}).get('overUnder'):
            try:
                proj = float(g['vegas_odds']['overUnder'])
            except:
                pass

        if has_pace and mp < min_time and cush_game == "All Games":
            continue

        thresholds_sorted = sorted(THRESHOLDS, reverse=True) if is_no else sorted(THRESHOLDS)
        single_game = cush_game != "All Games"
        rec_set = False
        for thresh in thresholds_sorted:
            cushion = (thresh - proj) if is_no else (proj - thresh)
            if cushion >= 6 or single_game:
                if cushion >= 20:
                    safety, scolor = "FORTRESS", "#22c55e"
                elif cushion >= 12:
                    safety, scolor = "SAFE", "#22c55e"
                elif cushion >= 6:
                    safety, scolor = "TIGHT", "#eab308"
                else:
                    safety, scolor = "RISKY", "#ef4444"
                is_rec = False
                if not rec_set and cushion >= 12:
                    is_rec = True
                    rec_set = True
                ptext_cs = ""
                if g['state'] == 'in':
                    ptext_cs = f"Q{g['period']} {g['clock']}" if g['period'] <= 4 else f"OT{g['period']-4} {g['clock']}"
                else:
                    ptext_cs = g.get('game_time', 'Sched')
                cushion_results.append({
                    "game": f"{g['away']} @ {g['home']}",
                    "status": ptext_cs, "proj": proj, "thresh": thresh,
                    "cushion": cushion, "safety": safety, "scolor": scolor,
                    "is_live": g['state'] == 'in', "is_rec": is_rec,
                    "away": g['away'], "home": g['home'],
                })

    safety_order = {"FORTRESS": 0, "SAFE": 1, "TIGHT": 2, "RISKY": 3}
    cushion_results.sort(key=lambda x: (0 if x['is_live'] else 1, safety_order.get(x['safety'], 9), -x['cushion']))

    max_show = 20 if cush_game != "All Games" else 10
    if cushion_results:
        for cr in cushion_results[:max_show]:
            cc1, cc2, cc3, cc4 = st.columns([3, 2, 2, 2])
            with cc1:
                rec_badge = " ⭐ REC" if cr['is_rec'] else ""
                st.markdown(f"**{cr['game']}**{rec_badge}")
                st.caption(cr['status'])
            with cc2:
                side_label = "NO" if is_no else "YES"
                st.markdown(f"Proj: {cr['proj']:.0f} | {side_label} {cr['thresh']}")
            with cc3:
                st.markdown(f"<span style='color:{cr['scolor']};font-weight:bold'>{cr['safety']} +{cr['cushion']:.0f}</span>", unsafe_allow_html=True)
            with cc4:
                link = get_kalshi_game_link(cr['away'], cr['home'])
                st.link_button("BUY", link, use_container_width=True)
        if is_no:
            st.caption("NO bets: go HIGH for safety — bigger number = more cushion")
        else:
            st.caption("YES bets: go LOW for safety — smaller number = more cushion")
    else:
        st.info("No cushion opportunities found with current filters.")

# ── 11. Footer ──
st.divider()
st.caption(f"v{VERSION} | Educational only | Not financial advice")
st.caption("Stay small. Stay quiet. Win.")

