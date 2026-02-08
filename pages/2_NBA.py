import streamlit as st
from streamlit_autorefresh import st_autorefresh
import streamlit.components.v1 as components

st.set_page_config(page_title="BigSnapshot NBA Edge Finder", page_icon="🏀", layout="wide")

from auth import require_auth
require_auth()

st_autorefresh(interval=24000, key="datarefresh")

import uuid, re
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

VERSION = "12.1"
LEAGUE_AVG_TOTAL = 225
THRESHOLDS = [210.5, 215.5, 220.5, 225.5, 230.5, 235.5, 240.5, 245.5]
HOME_COURT_ADV = 3.0
GAME_MINUTES = 48
MIN_UNDERDOG_LEAD = 7
MIN_SPREAD_BRACKET = 10
MAX_NO_PRICE = 85
MIN_WP_EDGE = 8
LEAD_BY_QUARTER = {1: 7, 2: 8, 3: 10, 4: 13}

if 'positions' not in st.session_state:
    st.session_state.positions = []
if 'sniper_alerts' not in st.session_state:
    st.session_state.sniper_alerts = []
if 'comeback_alerts' not in st.session_state:
    st.session_state.comeback_alerts = []
if 'comeback_tracking' not in st.session_state:
    st.session_state.comeback_tracking = {}
if 'alerted_games' not in st.session_state:
    st.session_state.alerted_games = set()
if 'comeback_alerted' not in st.session_state:
    st.session_state.comeback_alerted = set()

TEAM_ABBREVS = {"Atlanta Hawks": "Atlanta", "Boston Celtics": "Boston", "Brooklyn Nets": "Brooklyn", "Charlotte Hornets": "Charlotte", "Chicago Bulls": "Chicago", "Cleveland Cavaliers": "Cleveland", "Dallas Mavericks": "Dallas", "Denver Nuggets": "Denver", "Detroit Pistons": "Detroit", "Golden State Warriors": "Golden State", "Houston Rockets": "Houston", "Indiana Pacers": "Indiana", "LA Clippers": "LA Clippers", "Los Angeles Clippers": "LA Clippers", "LA Lakers": "LA Lakers", "Los Angeles Lakers": "LA Lakers", "Memphis Grizzlies": "Memphis", "Miami Heat": "Miami", "Milwaukee Bucks": "Milwaukee", "Minnesota Timberwolves": "Minnesota", "New Orleans Pelicans": "New Orleans", "New York Knicks": "New York", "Oklahoma City Thunder": "Oklahoma City", "Orlando Magic": "Orlando", "Philadelphia 76ers": "Philadelphia", "Phoenix Suns": "Phoenix", "Portland Trail Blazers": "Portland", "Sacramento Kings": "Sacramento", "San Antonio Spurs": "San Antonio", "Toronto Raptors": "Toronto", "Utah Jazz": "Utah", "Washington Wizards": "Washington", "MIL": "Milwaukee", "PHI": "Philadelphia", "BOS": "Boston", "NYK": "New York", "CLE": "Cleveland", "ORL": "Orlando", "ATL": "Atlanta", "MIA": "Miami", "CHI": "Chicago", "BKN": "Brooklyn", "TOR": "Toronto", "IND": "Indiana", "DET": "Detroit", "CHA": "Charlotte", "WAS": "Washington", "OKC": "Oklahoma City", "HOU": "Houston", "MEM": "Memphis", "DAL": "Dallas", "DEN": "Denver", "MIN": "Minnesota", "LAC": "LA Clippers", "LAL": "LA Lakers", "SAC": "Sacramento", "PHX": "Phoenix", "GSW": "Golden State", "POR": "Portland", "UTA": "Utah", "SAS": "San Antonio", "NOP": "New Orleans"}

KALSHI_CODES = {"Atlanta": "ATL", "Boston": "BOS", "Brooklyn": "BKN", "Charlotte": "CHA", "Chicago": "CHI", "Cleveland": "CLE", "Dallas": "DAL", "Denver": "DEN", "Detroit": "DET", "Golden State": "GSW", "Houston": "HOU", "Indiana": "IND", "LA Clippers": "LAC", "LA Lakers": "LAL", "Memphis": "MEM", "Miami": "MIA", "Milwaukee": "MIL", "Minnesota": "MIN", "New Orleans": "NOP", "New York": "NYK", "Oklahoma City": "OKC", "Orlando": "ORL", "Philadelphia": "PHI", "Phoenix": "PHX", "Portland": "POR", "Sacramento": "SAC", "San Antonio": "SAS", "Toronto": "TOR", "Utah": "UTA", "Washington": "WAS"}

TEAM_COLORS = {"Atlanta": "#E03A3E", "Boston": "#007A33", "Brooklyn": "#000000", "Charlotte": "#1D1160", "Chicago": "#CE1141", "Cleveland": "#860038", "Dallas": "#00538C", "Denver": "#0E2240", "Detroit": "#C8102E", "Golden State": "#1D428A", "Houston": "#CE1141", "Indiana": "#002D62", "LA Clippers": "#C8102E", "LA Lakers": "#552583", "Memphis": "#5D76A9", "Miami": "#98002E", "Milwaukee": "#00471B", "Minnesota": "#0C2340", "New Orleans": "#0C2340", "New York": "#006BB6", "Oklahoma City": "#007AC1", "Orlando": "#0077C0", "Philadelphia": "#006BB6", "Phoenix": "#1D1160", "Portland": "#E03A3E", "Sacramento": "#5A2D81", "San Antonio": "#C4CED4", "Toronto": "#CE1141", "Utah": "#002B5C", "Washington": "#002B5C"}

ESPN_TEAM_IDS = {"Atlanta": "1", "Boston": "2", "Brooklyn": "17", "Charlotte": "30", "Chicago": "4", "Cleveland": "5", "Dallas": "6", "Denver": "7", "Detroit": "8", "Golden State": "9", "Houston": "10", "Indiana": "11", "LA Clippers": "12", "LA Lakers": "13", "Memphis": "29", "Miami": "14", "Milwaukee": "15", "Minnesota": "16", "New Orleans": "3", "New York": "18", "Oklahoma City": "25", "Orlando": "19", "Philadelphia": "20", "Phoenix": "21", "Portland": "22", "Sacramento": "23", "San Antonio": "24", "Toronto": "28", "Utah": "26", "Washington": "27"}

# ============================================================
# SHARED HELPERS
# ============================================================
def american_to_implied_prob(odds):
    if odds is None: return None
    if odds > 0: return 100 / (odds + 100)
    else: return abs(odds) / (abs(odds) + 100)

def speak_play(text):
    clean_text = text.replace("'", "").replace('"', '').replace('\n', ' ')[:100]
    js = f'''<script>if(!window.lastSpoken||window.lastSpoken!=="{clean_text}"){{window.lastSpoken="{clean_text}";var u=new SpeechSynthesisUtterance("{clean_text}");u.rate=1.1;window.speechSynthesis.speak(u);}}</script>'''
    components.html(js, height=0)

def get_kalshi_game_link(away, home):
    away_code = KALSHI_CODES.get(away, "XXX").lower()
    home_code = KALSHI_CODES.get(home, "XXX").lower()
    date_str = datetime.now(eastern).strftime('%y%b%d').lower()
    return "https://kalshi.com/markets/kxnbagame/professional-basketball-game/kxnbagame-" + date_str + away_code + home_code

def get_kalshi_spread_link(away, home):
    away_code = KALSHI_CODES.get(away, "XXX").lower()
    home_code = KALSHI_CODES.get(home, "XXX").lower()
    date_str = datetime.now(eastern).strftime('%y%b%d').lower()
    return "https://kalshi.com/markets/kxnbaspread/nba-spread/kxnbaspread-" + date_str + away_code + home_code

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

def parse_record(s):
    try:
        p = s.split("-")
        return int(p[0]), int(p[1])
    except:
        return 0, 0

def get_favorite_side(hr, ar, hml=0):
    if hml != 0:
        return "home" if hml < 0 else "away"
    hw, hl = parse_record(hr)
    aw, al = parse_record(ar)
    hp = hw / (hw + hl) if (hw + hl) > 0 else 0.5
    ap = aw / (aw + al) if (aw + al) > 0 else 0.5
    return "home" if hp >= ap else "away"

def _parse_win_pct(record_str):
    try:
        if not record_str or "-" not in record_str: return None
        parts = record_str.split("-")
        w = int(parts[0])
        l = int(parts[1].split(" ")[0])
        total = w + l
        if total == 0: return None
        return w / total
    except Exception: return None

# ============================================================
# ESPN DATA FETCHERS
# ============================================================
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
            home_id, away_id = "", ""
            home_abbrev, away_abbrev = "", ""
            home_full, away_full = "", ""
            for c in competitors:
                full_name = c.get("team", {}).get("displayName", "")
                team_name = TEAM_ABBREVS.get(full_name, full_name)
                score = int(c.get("score", 0) or 0)
                records = c.get("records", [])
                record = records[0].get("summary", "") if records else ""
                team_id = str(c.get("team", {}).get("id", ""))
                abbrev = c.get("team", {}).get("abbreviation", "")
                if c.get("homeAway") == "home":
                    home_team, home_score, home_record, home_id = team_name, score, record, team_id
                    home_abbrev, home_full = abbrev, full_name
                else:
                    away_team, away_score, away_record, away_id = team_name, score, record, team_id
                    away_abbrev, away_full = abbrev, full_name
            status = event.get("status", {}).get("type", {}).get("name", "STATUS_SCHEDULED")
            state = event.get("status", {}).get("type", {}).get("state", "pre")
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
            home_ml = 0
            if odds_data and len(odds_data) > 0:
                odds = odds_data[0]
                vegas_odds = {"spread": odds.get("spread"), "overUnder": odds.get("overUnder"),
                    "homeML": odds.get("homeTeamOdds", {}).get("moneyLine"),
                    "awayML": odds.get("awayTeamOdds", {}).get("moneyLine")}
                home_ml = odds.get("homeTeamOdds", {}).get("moneyLine", 0) or 0
            games.append({"away": away_team, "home": home_team,
                "away_score": away_score, "home_score": home_score,
                "away_record": away_record, "home_record": home_record,
                "away_id": away_id, "home_id": home_id,
                "away_abbrev": away_abbrev, "home_abbrev": home_abbrev,
                "away_full": away_full, "home_full": home_full,
                "status": status, "state": state, "period": period, "clock": clock,
                "minutes_played": minutes_played,
                "total_score": home_score + away_score, "game_id": game_id,
                "vegas_odds": vegas_odds, "home_ml": home_ml,
                "game_time": game_time_str, "game_datetime": game_datetime_str})
        return games
    except Exception as e:
        st.error("ESPN fetch error: " + str(e))
        return []

@st.cache_data(ttl=300)
def fetch_game_summary(game_id):
    try:
        url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary?event=" + str(game_id)
        r = requests.get(url, timeout=10)
        if r.status_code != 200: return None
        return r.json()
    except Exception: return None

@st.cache_data(ttl=20)
def fetch_espn_win_prob(game_id):
    try:
        url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary?event=" + str(game_id)
        r = requests.get(url, timeout=8)
        if r.status_code != 200: return None
        data = r.json()
        wp = data.get("winprobability", [])
        if wp:
            return wp[-1].get("homeWinPercentage", 0.5) * 100
        pred = data.get("predictor", {})
        if pred:
            return float(pred.get("homeTeam", {}).get("gameProjection", 50))
        return None
    except: return None

def parse_predictor(summary):
    if not summary: return None
    pred = summary.get("predictor", {})
    if not pred: return None
    home_proj = pred.get("homeTeam", {})
    away_proj = pred.get("awayTeam", {})
    return {
        "home_win_pct": float(home_proj.get("gameProjection", 0)) / 100.0,
        "away_win_pct": float(away_proj.get("gameProjection", 0)) / 100.0,
        "home_team": home_proj.get("team", {}).get("abbreviation", ""),
        "away_team": away_proj.get("team", {}).get("abbreviation", ""),
    }

def parse_team_stats_from_summary(summary):
    if not summary: return {}, {}
    home_stats, away_stats = {}, {}
    boxscore = summary.get("boxscore", {})
    teams = boxscore.get("teams", [])
    for t in teams:
        stats_list = t.get("statistics", [])
        parsed = {}
        for s in stats_list:
            name = s.get("name", "")
            val = s.get("displayValue", "0")
            try: parsed[name] = float(val)
            except (ValueError, TypeError): parsed[name] = val
        ha = t.get("homeAway", "")
        if ha == "home": home_stats = parsed
        elif ha == "away": away_stats = parsed
    return home_stats, away_stats

def _get_team_leaders(summary, home_away):
    leaders = []
    if not summary: return leaders
    try:
        for leader_group in summary.get("leaders", []):
            for cat in leader_group.get("leaders", []):
                if cat.get("name", "").lower() in ("points", "rating"):
                    for athlete_entry in cat.get("leaders", []):
                        athlete = athlete_entry.get("athlete", {})
                        display = athlete.get("displayName", "")
                        ppg = athlete_entry.get("displayValue", "0")
                        if display:
                            leaders.append({"name": display, "value": ppg})
    except Exception: pass
    return leaders

def _is_star_player(player_name, leaders_list):
    if not leaders_list or not player_name: return False
    pname = player_name.lower().strip()
    for i, leader in enumerate(leaders_list[:3]):
        lname = leader.get("name", "").lower().strip()
        p_parts = pname.split()
        l_parts = lname.split()
        if p_parts and l_parts:
            if p_parts[-1] == l_parts[-1]: return True
            if pname in lname or lname in pname: return True
    return False

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
    url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary?event=" + str(game_id)
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        plays = []
        for p in data.get("plays", [])[-15:]:
            plays.append({"text": p.get("text", ""),
                "period": p.get("period", {}).get("number", 0),
                "clock": p.get("clock", {}).get("displayValue", ""),
                "score_value": p.get("scoreValue", 0),
                "play_type": p.get("type", {}).get("text", ""),
                "team_id": str(p.get("team", {}).get("id", ""))})
        return plays[-10:]
    except: return []

# ============================================================
# KALSHI DATA (public, no auth)
# ============================================================
@st.cache_data(ttl=60)
def fetch_kalshi_ml():
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
            yes_price = yes_ask if yes_ask > 0 else (yes_bid if yes_bid > 0 else 50)
            yes_team_code = yes_team_code.upper()
            if yes_team_code == home_code.upper():
                home_implied, away_implied = yes_price, 100 - yes_price
            else:
                away_implied, home_implied = yes_price, 100 - yes_price
            if game_key not in markets:
                markets[game_key] = {"away_code": away_code, "home_code": home_code,
                    "yes_team_code": yes_team_code, "ticker": ticker,
                    "yes_bid": yes_bid, "yes_ask": yes_ask, "yes_price": yes_price,
                    "away_implied": away_implied, "home_implied": home_implied}
        return markets
    except Exception as e:
        st.error("Kalshi ML fetch error: " + str(e))
        return {}

@st.cache_data(ttl=60)
def fetch_kalshi_spreads():
    url = "https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXNBASPREAD&status=open&limit=200"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        spreads = {}
        spread_list = []
        for m in data.get("markets", []):
            ticker = m.get("ticker", "")
            yes_bid = m.get("yes_bid", 0) or 0
            yes_ask = m.get("yes_ask", 0) or 0
            ti = (m.get("title", "") or "").lower()
            if "wins by" in ti or "spread" in ti or "margin" in ti:
                spread_list.append(m)
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
                            game_key = away_code + "@" + home_code
                            spread_line, spread_team = None, None
                            if "-" in spread_info:
                                sp_parts = spread_info.rsplit("-", 1)
                                if len(sp_parts) == 2:
                                    spread_team = sp_parts[0].upper()
                                    try: spread_line = "-" + sp_parts[1]
                                    except: pass
                            elif "+" in spread_info:
                                sp_parts = spread_info.split("+", 1)
                                if len(sp_parts) == 2:
                                    spread_team = sp_parts[0].upper()
                                    try: spread_line = "+" + sp_parts[1]
                                    except: pass
                            if spread_line and spread_team:
                                if game_key not in spreads: spreads[game_key] = []
                                spreads[game_key].append({"line": spread_line, "team_code": spread_team,
                                    "ticker": ticker, "yes_bid": yes_bid, "yes_ask": yes_ask,
                                    "yes_price": yes_ask if yes_ask > 0 else (yes_bid if yes_bid > 0 else 50)})
        return spreads, spread_list
    except: return {}, []

def find_spread_markets_for_game(ha, aa, hn, an, spread_list):
    matches = []
    hab, aab = ha.lower(), aa.lower()
    hnl, anl = hn.lower(), an.lower()
    hc = hnl.split()[0] if hnl else ""
    ac = anl.split()[0] if anl else ""
    for m in spread_list:
        ti = (m.get("title", "") or "").lower()
        sub = (m.get("subtitle", "") or "").lower()
        comb = ti + " " + sub
        gm = False
        if (hab in comb or hnl in comb or hc in comb):
            if (aab in comb or anl in comb or ac in comb):
                gm = True
        if not gm:
            tk = (m.get("ticker", "") or "").lower()
            if hab in tk and aab in tk:
                gm = True
        if not gm: continue
        sv, sts = None, None
        if hab in ti or hnl in ti or hc in ti:
            if "wins by" in ti: sts = "home"
        if aab in ti or anl in ti or ac in ti:
            if "wins by" in ti: sts = "away"
        nums = re.findall(r'(?:over|more than|by)\s+([\d.]+)', ti)
        if nums:
            sv = float(nums[0])
        else:
            rm = re.findall(r'by\s+(\d+)\s*[-\u2013]\s*(\d+)', ti)
            if rm:
                sv = float(rm[0][0])
            else:
                an2 = re.findall(r'([\d.]+)', ti)
                for n in an2:
                    v = float(n)
                    if 1 <= v <= 50:
                        sv = v
                        break
        yp = m.get("yes_ask", 0) or m.get("last_price", 50)
        nb, na = m.get("no_bid", 0), m.get("no_ask", 0)
        np2 = na if na > 0 else (100 - yp) if yp else 0
        matches.append({
            "ticker": m.get("ticker", ""), "title": m.get("title", ""),
            "spread_val": sv, "spread_team_side": sts,
            "yes_price": yp, "yes_bid": m.get("yes_bid", 0),
            "no_price": np2, "no_bid": nb, "no_ask": na,
            "last_price": m.get("last_price", 0), "volume": m.get("volume", 0)
        })
    matches.sort(key=lambda x: x.get("spread_val") or 0, reverse=True)
    return matches

def find_ml_price_for_team(ha, aa, fs, kalshi_ml_data):
    hau, aau = ha.upper(), aa.upper()
    fc = hau if fs == "home" else aau
    for tk, m in kalshi_ml_data.items():
        t = tk.upper()
        if hau in t and aau in t:
            if t.endswith("-" + fc):
                return m["yes_price"], tk
            else:
                return 100 - m["yes_price"], tk
    return None, None

# ============================================================
# EDGE MODEL (9-Factor)
# ============================================================
def calc_advanced_edge(game, b2b_teams, summary=None, injuries=None):
    edges = []
    score = 0.0
    home = game.get("home", "")
    away = game.get("away", "")
    bpi = None
    if summary:
        bpi = parse_predictor(summary)
    if bpi:
        home_bpi = bpi.get("home_win_pct", 0.5)
        away_bpi = bpi.get("away_win_pct", 0.5)
        edges.append("ESPN BPI: " + home + " " + "{:.0%}".format(home_bpi) + " | " + away + " " + "{:.0%}".format(away_bpi))
        bpi_edge = (home_bpi - 0.5) * 20
        score += bpi_edge
    else:
        edges.append("ESPN BPI: unavailable")
    home_ml = game.get("vegas_odds", {}).get("homeML")
    if home_ml and bpi:
        try:
            vegas_prob = american_to_implied_prob(float(home_ml))
            bpi_prob = bpi.get("home_win_pct", 0.5)
            gap = bpi_prob - vegas_prob
            if abs(gap) >= 0.03:
                who = home if gap > 0 else away
                edges.append("BPI vs VEGAS GAP: " + "{:.1%}".format(abs(gap)) + " edge on " + who)
                score += gap * 15
        except (ValueError, TypeError): pass
    edges.append("Home court: " + home + " +" + str(HOME_COURT_ADV))
    score += HOME_COURT_ADV / 2
    home_rec = game.get("home_record", "")
    away_rec = game.get("away_record", "")
    home_wpct = _parse_win_pct(home_rec)
    away_wpct = _parse_win_pct(away_rec)
    if home_wpct is not None and away_wpct is not None:
        rec_edge = (home_wpct - away_wpct) * 10
        score += rec_edge
        edges.append("Records: " + home + " (" + home_rec + " | " + "{:.0%}".format(home_wpct) + ") vs " + away + " (" + away_rec + " | " + "{:.0%}".format(away_wpct) + ")")
    home_stats, away_stats = {}, {}
    if summary:
        home_stats, away_stats = parse_team_stats_from_summary(summary)
        h_ppg = home_stats.get("avgPoints", home_stats.get("points", 0))
        a_ppg = away_stats.get("avgPoints", away_stats.get("points", 0))
        h_opp = home_stats.get("avgPointsAgainst", home_stats.get("pointsAgainst", 0))
        a_opp = away_stats.get("avgPointsAgainst", away_stats.get("pointsAgainst", 0))
        try:
            h_ppg, a_ppg = float(h_ppg), float(a_ppg)
            h_opp, a_opp = float(h_opp), float(a_opp)
            if h_ppg > 0 and a_ppg > 0:
                h_net = h_ppg - h_opp
                a_net = a_ppg - a_opp
                net_edge = (h_net - a_net) * 0.3
                score += net_edge
                edges.append("Net Rating: " + home + " " + "{:+.1f}".format(h_net) + " vs " + away + " " + "{:+.1f}".format(a_net))
        except (ValueError, TypeError): pass
    if home in b2b_teams:
        edges.append("FATIGUE: " + home + " on B2B")
        score -= 2.5
    if away in b2b_teams:
        edges.append("FATIGUE: " + away + " on B2B")
        score += 2.5
    if home_stats or away_stats:
        h_ppg = home_stats.get("avgPoints", home_stats.get("points", 0))
        a_ppg = away_stats.get("avgPoints", away_stats.get("points", 0))
        try:
            h_ppg, a_ppg = float(h_ppg), float(a_ppg)
            if h_ppg > 0 and a_ppg > 0:
                ppg_edge = (h_ppg - a_ppg) * 0.3
                score += ppg_edge
                edges.append("Scoring: " + home + " " + "{:.1f}".format(h_ppg) + " PPG vs " + away + " " + "{:.1f}".format(a_ppg) + " PPG")
        except (ValueError, TypeError): pass
    if injuries:
        home_leaders = _get_team_leaders(summary, "home")
        away_leaders = _get_team_leaders(summary, "away")
        home_inj = injuries.get(home, [])
        away_inj = injuries.get(away, [])
        home_out = [p for p in home_inj if "out" in (p.get("status", "") or "").lower()]
        away_out = [p for p in away_inj if "out" in (p.get("status", "") or "").lower()]
        home_dtd = [p for p in home_inj if "day" in (p.get("status", "") or "").lower() or "doubt" in (p.get("status", "") or "").lower()]
        away_dtd = [p for p in away_inj if "day" in (p.get("status", "") or "").lower() or "doubt" in (p.get("status", "") or "").lower()]
        for p in home_out:
            pname = p.get("name", "")
            is_star = _is_star_player(pname, home_leaders)
            if is_star:
                edges.append("INJURY [STAR OUT]: " + home + " - " + pname + " (OUT)")
                score -= 4.0
            else:
                edges.append("INJURY [OUT]: " + home + " - " + pname)
                score -= 1.0
        for p in home_dtd:
            edges.append("INJURY [DTD]: " + home + " - " + p.get("name", ""))
            score -= 0.5
        for p in away_out:
            pname = p.get("name", "")
            is_star = _is_star_player(pname, away_leaders)
            if is_star:
                edges.append("INJURY [STAR OUT]: " + away + " - " + pname + " (OUT)")
                score += 4.0
            else:
                edges.append("INJURY [OUT]: " + away + " - " + pname)
                score += 1.0
        for p in away_dtd:
            edges.append("INJURY [DTD]: " + away + " - " + p.get("name", ""))
            score += 0.5
    if home_stats or away_stats:
        h_3pct = home_stats.get("threePointFieldGoalPct", home_stats.get("threePointPct", 0))
        a_3pct = away_stats.get("threePointFieldGoalPct", away_stats.get("threePointPct", 0))
        h_3pm = home_stats.get("avgThreePointFieldGoalsMade", home_stats.get("threePointFieldGoalsMade", 0))
        a_3pm = away_stats.get("avgThreePointFieldGoalsMade", away_stats.get("threePointFieldGoalsMade", 0))
        try:
            h_3pct, a_3pct = float(h_3pct), float(a_3pct)
            h_3pm, a_3pm = float(h_3pm), float(a_3pm)
            if h_3pct > 0 and a_3pct > 0:
                pct_gap = h_3pct - a_3pct
                made_gap = h_3pm - a_3pm
                three_edge = pct_gap * 0.15 + made_gap * 0.3
                score += three_edge
                edges.append("3PT: " + home + " " + "{:.1f}".format(h_3pct) + "% (" + "{:.1f}".format(h_3pm) + "/gm) vs " + away + " " + "{:.1f}".format(a_3pct) + "% (" + "{:.1f}".format(a_3pm) + "/gm)")
                if abs(pct_gap) >= 3:
                    who = home if pct_gap > 0 else away
                    edges.append("3PT EDGE: " + who + " has " + "{:.1f}".format(abs(pct_gap)) + "% advantage from deep")
        except (ValueError, TypeError): pass
    if abs(score) >= 8: strength = "STRONG"
    elif abs(score) >= 4: strength = "MODERATE"
    elif abs(score) >= 1.5: strength = "LEAN"
    else: strength = "TOSS-UP"
    if score > 0: pick, side = home, "HOME"
    else: pick, side = away, "AWAY"
    edges.insert(0, "EDGE: " + strength + " " + side + " (" + pick + ") | Score: " + "{:+.1f}".format(score))
    return {"edges": edges, "score": score, "pick": pick, "side": side, "strength": strength, "bpi": bpi}

# ============================================================
# POSSESSION + COURT
# ============================================================
def infer_possession(plays, away, home):
    if not plays: return None, None
    last_play = plays[-1]
    play_text = (last_play.get("text", "") or "").lower()
    team_id = str(last_play.get("team_id", ""))
    acting_team = None
    away_id = ESPN_TEAM_IDS.get(away, "")
    home_id = ESPN_TEAM_IDS.get(home, "")
    if team_id and team_id == away_id:
        acting_team = away
    elif team_id and team_id == home_id:
        acting_team = home
    if not acting_team:
        away_code = KALSHI_CODES.get(away, "XXX").lower()
        home_code = KALSHI_CODES.get(home, "XXX").lower()
        if away.lower() in play_text or away_code in play_text:
            acting_team = away
        elif home.lower() in play_text or home_code in play_text:
            acting_team = home
    if not acting_team: return None, None
    other_team = home if acting_team == away else away
    if last_play.get("score_value", 0) > 0 or "makes" in play_text:
        return other_team, "-> " + KALSHI_CODES.get(other_team, other_team[:3].upper())
    if "defensive rebound" in play_text:
        return acting_team, KALSHI_CODES.get(acting_team, acting_team[:3].upper()) + " BALL"
    if "offensive rebound" in play_text:
        return acting_team, KALSHI_CODES.get(acting_team, acting_team[:3].upper()) + " BALL"
    if "turnover" in play_text or "steal" in play_text:
        return other_team, "-> " + KALSHI_CODES.get(other_team, other_team[:3].upper())
    if "misses" in play_text:
        return None, "LOOSE"
    if "foul" in play_text:
        return other_team, "FT " + KALSHI_CODES.get(other_team, other_team[:3].upper())
    return acting_team, KALSHI_CODES.get(acting_team, acting_team[:3].upper()) + " BALL"

def render_scoreboard(away, home, away_score, home_score, period, clock, away_record="", home_record=""):
    away_code = KALSHI_CODES.get(away, away[:3].upper())
    home_code = KALSHI_CODES.get(home, home[:3].upper())
    away_color = TEAM_COLORS.get(away, "#666")
    home_color = TEAM_COLORS.get(home, "#666")
    period_text = "Q" + str(period) if period <= 4 else "OT" + str(period - 4)
    html = "<div style='background:#0f172a;border-radius:12px;padding:20px;margin-bottom:8px'>"
    html += "<div style='text-align:center;color:#ffd700;font-weight:bold;font-size:22px;margin-bottom:16px'>" + period_text + " - " + clock + "</div>"
    html += "<table style='width:100%;border-collapse:collapse;color:#fff'>"
    html += "<tr style='border-bottom:2px solid #333'>"
    html += "<td style='padding:16px;text-align:left;width:70%'><span style='color:" + away_color + ";font-weight:bold;font-size:28px'>" + away_code + "</span>"
    html += "<span style='color:#666;font-size:14px;margin-left:12px'>" + away_record + "</span></td>"
    html += "<td style='padding:16px;text-align:right;font-weight:bold;font-size:52px;color:#fff'>" + str(away_score) + "</td></tr>"
    html += "<tr><td style='padding:16px;text-align:left;width:70%'><span style='color:" + home_color + ";font-weight:bold;font-size:28px'>" + home_code + "</span>"
    html += "<span style='color:#666;font-size:14px;margin-left:12px'>" + home_record + "</span></td>"
    html += "<td style='padding:16px;text-align:right;font-weight:bold;font-size:52px;color:#fff'>" + str(home_score) + "</td></tr>"
    html += "</table></div>"
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
        return '<rect x="175" y="25" width="150" height="30" fill="#ef4444" rx="6"/><text x="250" y="46" fill="#fff" font-size="14" font-weight="bold" text-anchor="middle">MISSED</text>'
    elif "block" in play_text:
        return '<rect x="175" y="25" width="150" height="30" fill="#f97316" rx="6"/><text x="250" y="46" fill="#fff" font-size="14" font-weight="bold" text-anchor="middle">BLOCKED!</text>'
    elif "turnover" in play_text or "steal" in play_text:
        return '<rect x="175" y="25" width="150" height="30" fill="#f97316" rx="6"/><text x="250" y="46" fill="#fff" font-size="14" font-weight="bold" text-anchor="middle">TURNOVER</text>'
    elif "rebound" in play_text:
        return '<rect x="175" y="25" width="150" height="30" fill="#3b82f6" rx="6"/><text x="250" y="46" fill="#fff" font-size="14" font-weight="bold" text-anchor="middle">REBOUND</text>'
    elif "foul" in play_text:
        return '<rect x="175" y="25" width="150" height="30" fill="#eab308" rx="6"/><text x="250" y="46" fill="#fff" font-size="14" font-weight="bold" text-anchor="middle">FOUL</text>'
    elif "timeout" in play_text:
        return '<rect x="175" y="25" width="150" height="30" fill="#a855f7" rx="6"/><text x="250" y="46" fill="#fff" font-size="14" font-weight="bold" text-anchor="middle">TIMEOUT</text>'
    return ""

def render_nba_court(away, home, away_score, home_score, period, clock, last_play=None):
    away_color = TEAM_COLORS.get(away, "#666")
    home_color = TEAM_COLORS.get(home, "#666")
    away_code = KALSHI_CODES.get(away, "AWY")
    home_code = KALSHI_CODES.get(home, "HME")
    period_text = "Q" + str(period) if period <= 4 else "OT" + str(period - 4)
    play_badge = get_play_badge(last_play)
    svg = "<div style='background:#1a1a2e;border-radius:12px;padding:10px;'>"
    svg += "<svg viewBox='0 0 500 280' style='width:100%;max-width:500px;'>"
    svg += "<rect x='20' y='20' width='460' height='200' fill='#2d4a22' stroke='#fff' stroke-width='2' rx='8'/>"
    svg += "<circle cx='250' cy='120' r='35' fill='none' stroke='#fff' stroke-width='2'/>"
    svg += "<circle cx='250' cy='120' r='4' fill='#fff'/>"
    svg += "<line x1='250' y1='20' x2='250' y2='220' stroke='#fff' stroke-width='2'/>"
    svg += "<path d='M 20 50 Q 100 120 20 190' fill='none' stroke='#fff' stroke-width='2'/>"
    svg += "<rect x='20' y='70' width='70' height='100' fill='none' stroke='#fff' stroke-width='2'/>"
    svg += "<circle cx='90' cy='120' r='25' fill='none' stroke='#fff' stroke-width='2'/>"
    svg += "<circle cx='35' cy='120' r='8' fill='none' stroke='#ff6b35' stroke-width='3'/>"
    svg += "<path d='M 480 50 Q 400 120 480 190' fill='none' stroke='#fff' stroke-width='2'/>"
    svg += "<rect x='410' y='70' width='70' height='100' fill='none' stroke='#fff' stroke-width='2'/>"
    svg += "<circle cx='410' cy='120' r='25' fill='none' stroke='#fff' stroke-width='2'/>"
    svg += "<circle cx='465' cy='120' r='8' fill='none' stroke='#ff6b35' stroke-width='3'/>"
    svg += play_badge
    svg += "<rect x='40' y='228' width='90' height='48' fill='" + away_color + "' rx='6'/>"
    svg += "<text x='85' y='250' fill='#fff' font-size='14' font-weight='bold' text-anchor='middle'>" + away_code + "</text>"
    svg += "<text x='85' y='270' fill='#fff' font-size='18' font-weight='bold' text-anchor='middle'>" + str(away_score) + "</text>"
    svg += "<rect x='370' y='228' width='90' height='48' fill='" + home_color + "' rx='6'/>"
    svg += "<text x='415' y='250' fill='#fff' font-size='14' font-weight='bold' text-anchor='middle'>" + home_code + "</text>"
    svg += "<text x='415' y='270' fill='#fff' font-size='18' font-weight='bold' text-anchor='middle'>" + str(home_score) + "</text>"
    svg += "<text x='250' y='258' fill='#fff' font-size='16' font-weight='bold' text-anchor='middle'>" + period_text + " " + clock + "</text>"
    svg += "</svg></div>"
    return svg

def get_play_icon(play_type, score_value):
    play_lower = play_type.lower() if play_type else ""
    if score_value > 0 or "made" in play_lower: return "B", "#22c55e"
    elif "miss" in play_lower or "block" in play_lower: return "X", "#ef4444"
    elif "rebound" in play_lower: return "R", "#3b82f6"
    elif "turnover" in play_lower or "steal" in play_lower: return "T", "#f97316"
    elif "foul" in play_lower: return "F", "#eab308"
    elif "timeout" in play_lower: return "TO", "#a855f7"
    return "-", "#888"

def remove_position(pos_id):
    st.session_state.positions = [p for p in st.session_state.positions if p['id'] != pos_id]

# ============================================================
# SPREAD SNIPER LOGIC
# ============================================================
def check_spread_sniper(game, spread_list, kalshi_ml_data):
    gid = game["game_id"]
    if gid in st.session_state.alerted_games: return None
    h_score, a_score = game["home_score"], game["away_score"]
    sd = h_score - a_score
    fs = get_favorite_side(game.get("home_record", ""), game.get("away_record", ""), game.get("home_ml", 0))
    ds = "away" if fs == "home" else "home"
    dl = sd if ds == "home" else -sd
    req = LEAD_BY_QUARTER.get(game["period"], MIN_UNDERDOG_LEAD)
    if dl < req: return None
    ha = game.get("home_abbrev", KALSHI_CODES.get(game["home"], "XXX"))
    aa = game.get("away_abbrev", KALSHI_CODES.get(game["away"], "XXX"))
    hn = game.get("home_full", game["home"])
    an = game.get("away_full", game["away"])
    spreads = find_spread_markets_for_game(ha, aa, hn, an, spread_list)
    actionable = []
    for s in spreads:
        sv = s.get("spread_val")
        if sv is None or sv < MIN_SPREAD_BRACKET: continue
        if s["spread_team_side"] and s["spread_team_side"] != fs: continue
        np = s["no_price"]
        if np <= 0: np = 100 - s["yes_price"] if s["yes_price"] else 0
        if np >= MAX_NO_PRICE or np <= 0: continue
        actionable.append({**s, "swing_needed": dl + (sv or 0), "effective_no_price": np})
    actionable.sort(key=lambda x: x["effective_no_price"])
    st.session_state.alerted_games.add(gid)
    hwp = fetch_espn_win_prob(gid)
    fwp, wpe = None, None
    if hwp is not None:
        fwp = hwp if fs == "home" else 100 - hwp
        fml_price, _ = find_ml_price_for_team(ha, aa, fs, kalshi_ml_data)
        if fml_price:
            wpe = round(fwp - fml_price, 1)
    fav_name = game["home"] if fs == "home" else game["away"]
    dog_name = game["away"] if fs == "home" else game["home"]
    fav_abbrev = ha if fs == "home" else aa
    dog_abbrev = aa if fs == "home" else ha
    fav_record = game["home_record"] if fs == "home" else game["away_record"]
    dog_record = game["away_record"] if fs == "home" else game["home_record"]
    return {
        "game": game, "dog_side": ds, "fav_side": fs, "dog_lead": dl,
        "spreads": actionable, "no_markets": len(spreads) == 0,
        "fav_wp": fwp, "wp_edge": wpe, "required": req,
        "fav_name": fav_name, "dog_name": dog_name,
        "fav_abbrev": fav_abbrev, "dog_abbrev": dog_abbrev,
        "fav_record": fav_record, "dog_record": dog_record
    }

def check_comeback(game, kalshi_ml_data):
    gid = game["game_id"]
    if game["state"] != "in": return None
    h_score, a_score = game["home_score"], game["away_score"]
    sd = h_score - a_score
    fs = get_favorite_side(game.get("home_record", ""), game.get("away_record", ""), game.get("home_ml", 0))
    fd = -sd if fs == "home" else sd
    COMEBACK_MIN_DEFICIT = 10
    COMEBACK_TRIGGER_WITHIN = 2
    if fd >= COMEBACK_MIN_DEFICIT:
        if gid not in st.session_state.comeback_tracking:
            st.session_state.comeback_tracking[gid] = {"max_deficit": fd, "fav_side": fs}
        elif fd > st.session_state.comeback_tracking[gid]["max_deficit"]:
            st.session_state.comeback_tracking[gid]["max_deficit"] = fd
    if gid in st.session_state.comeback_alerted or gid not in st.session_state.comeback_tracking:
        return None
    md = st.session_state.comeback_tracking[gid]["max_deficit"]
    fs = st.session_state.comeback_tracking[gid]["fav_side"]
    fm = sd if fs == "home" else -sd
    if fm < -COMEBACK_TRIGGER_WITHIN: return None
    ha = game.get("home_abbrev", KALSHI_CODES.get(game["home"], "XXX"))
    aa = game.get("away_abbrev", KALSHI_CODES.get(game["away"], "XXX"))
    fp, mt = find_ml_price_for_team(ha, aa, fs, kalshi_ml_data)
    hwp = fetch_espn_win_prob(gid)
    fwp = None
    if hwp is not None:
        fwp = hwp if fs == "home" else 100 - hwp
    fav_name = game["home"] if fs == "home" else game["away"]
    fav_abbrev = ha if fs == "home" else aa
    st.session_state.comeback_alerted.add(gid)
    return {
        "game": game, "fav_side": fs, "max_deficit": md, "fav_margin": fm,
        "fav_price": fp, "ml_ticker": mt, "fav_wp": fwp,
        "fav_name": fav_name, "fav_abbrev": fav_abbrev
    }

# ============================================================
# FETCH ALL DATA
# ============================================================
games = fetch_espn_games()
kalshi_ml_data = fetch_kalshi_ml()
kalshi_spreads_parsed, kalshi_spread_list = fetch_kalshi_spreads()
injuries = fetch_injuries()
b2b_teams = fetch_yesterday_teams()

live_games = [g for g in games if g['status'] in ['STATUS_IN_PROGRESS', 'STATUS_HALFTIME', 'STATUS_END_PERIOD'] or (g['period'] > 0 and g['status'] not in ['STATUS_FINAL', 'STATUS_FULL_TIME'])]
scheduled_games = [g for g in games if g['status'] == 'STATUS_SCHEDULED' and g['period'] == 0]
final_games = [g for g in games if g['status'] in ['STATUS_FINAL', 'STATUS_FULL_TIME']]

# ============================================================
# HEADER
# ============================================================
st.title("BIGSNAPSHOT NBA EDGE FINDER")
st.caption("v" + VERSION + " | " + now.strftime('%b %d, %Y %I:%M %p ET') + " | 9-Factor Edge + Spread Sniper + Comeback Scanner")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Today's Games", len(games))
c2.metric("Live Now", len(live_games))
c3.metric("Scheduled", len(scheduled_games))
c4.metric("Final", len(final_games))
st.divider()

# ============================================================
# TAB LAYOUT
# ============================================================
tab_edge, tab_spread, tab_live, tab_cushion = st.tabs(["Edge Finder", "Spread Sniper", "Live Monitor", "Cushion Scanner"])

# ============================================================
# TAB 1: EDGE FINDER (Pre-Game + Mispricing + Injuries + Positions)
# ============================================================
with tab_edge:
    # PACE SCANNER
    st.subheader("PACE SCANNER")
    pace_data = []
    for g in live_games:
        if g['minutes_played'] >= 6:
            pace = g['total_score'] / g['minutes_played']
            pace_data.append({"game": g['away'] + " @ " + g['home'], "status": "Q" + str(g['period']) + " " + g['clock'], "total": g['total_score'], "pace": pace, "pace_label": get_pace_label(pace)[0], "pace_color": get_pace_label(pace)[1], "proj": calc_projection(g['total_score'], g['minutes_played'])})
    pace_data.sort(key=lambda x: x['pace'])
    if pace_data:
        for pd_item in pace_data:
            pc1, pc2, pc3, pc4 = st.columns([3, 2, 2, 2])
            with pc1: st.markdown("**" + pd_item['game'] + "**")
            with pc2: st.write(pd_item['status'] + " | " + str(pd_item['total']) + " pts")
            with pc3: st.markdown("<span style='color:" + pd_item['pace_color'] + ";font-weight:bold'>" + pd_item['pace_label'] + "</span>", unsafe_allow_html=True)
            with pc4: st.write("Proj: " + str(pd_item['proj']))
    else:
        st.info("No live games with 6+ minutes played")
    st.divider()

    # PRE-GAME EDGE MODEL
    st.subheader("PRE-GAME ALIGNMENT — 9-Factor Edge Model")
    with st.expander("How Edges Are Rated"):
        st.markdown("Our model analyzes 9 live data points for each game: ESPN BPI win probability, BPI vs Vegas gap, home court advantage, win percentage from records, net rating, back-to-back fatigue, PPG offensive matchup, injury impact (star detection), and 3PT shooting differential.\n\n**Edge Score** is a composite where each factor adds or subtracts points. Positive = lean HOME, negative = lean AWAY.\n\n| Rating | Score | Meaning |\n|--------|-------|----------|\n| **STRONG** | 8+ | Multiple factors aligned, high conviction |\n| **MODERATE** | 4-8 | Solid edge with supporting data |\n| LEAN | 1.5-4 | Slight edge, filtered out |\n| TOSS-UP | <1.5 | No clear edge, filtered out |\n\nOnly **STRONG** and **MODERATE** games are shown.")
    st.caption("ESPN BPI + Vegas + Live Stats | Only showing STRONG + MODERATE edges")
    edge_games = []
    for g in scheduled_games:
        summary = fetch_game_summary(g["game_id"])
        edge = calc_advanced_edge(g, b2b_teams, summary=summary, injuries=injuries)
        if edge.get("strength") in ("STRONG", "MODERATE"):
            edge_games.append((g, edge))
    edge_games.sort(key=lambda x: (0 if x[1].get("strength") == "STRONG" else 1, -abs(x[1].get("score", 0))))
    if not edge_games:
        st.info("No STRONG or MODERATE edges found today. All games are LEAN or TOSS-UP.")
    else:
        st.markdown("**" + str(len(edge_games)) + " actionable edges** out of " + str(len(scheduled_games)) + " scheduled games")
        if st.button("ADD ALL EDGE PICKS", key="add_all_pre"):
            for g, edge in edge_games:
                game_key = g['away'] + "@" + g['home']
                if not any(p['game'] == game_key for p in st.session_state.positions):
                    st.session_state.positions.append({"game": game_key, "pick": edge.get("pick", ""), "type": "ML", "line": "-", "price": 50, "contracts": 10, "link": get_kalshi_game_link(g['away'], g['home']), "id": str(uuid.uuid4())[:8]})
            st.rerun()
        for idx, (g, edge) in enumerate(edge_games):
            edge_list = edge.get("edges", [])
            strength = edge.get("strength", "TOSS-UP")
            pick = edge.get("pick", "")
            sc = edge.get("score", 0)
            badge_color = "#2ecc71" if strength == "STRONG" else "#f39c12" if strength == "MODERATE" else "#888"
            spread = str(g.get("vegas_odds", {}).get("spread", "N/A"))
            ou = str(g.get("vegas_odds", {}).get("overUnder", "N/A"))
            box_html = "<div style='background:#1a1a2e;border-radius:8px;padding:10px;margin:8px 0;border-left:4px solid " + badge_color + "'>"
            box_html += "<span style='color:" + badge_color + ";font-weight:700;font-size:14px'>" + strength + "</span> "
            box_html += "<span style='color:white;font-weight:700'>" + g["away"] + " @ " + g["home"] + "</span>"
            box_html += "<br><span style='color:#aaa;font-size:12px'>Spread: " + spread + " | O/U: " + ou
            if g.get("game_datetime"): box_html += " | " + g["game_datetime"]
            box_html += "</span><br><span style='color:" + badge_color + ";font-size:12px'>PICK: " + edge.get("side", "") + " (" + pick + ") | Score: " + "{:+.1f}".format(sc) + "</span></div>"
            st.markdown(box_html, unsafe_allow_html=True)
            bc1, bc2 = st.columns(2)
            with bc1: st.link_button("Trade on Kalshi", get_kalshi_game_link(g['away'], g['home']), use_container_width=True)
            with bc2:
                game_key = g['away'] + "@" + g['home']
                if any(p['game'] == game_key for p in st.session_state.positions): st.success("Tracked")
                elif st.button("Track", key="pre_" + game_key):
                    st.session_state.positions.append({"game": game_key, "pick": pick, "type": "ML", "line": "-", "price": 50, "contracts": 10, "link": get_kalshi_game_link(g['away'], g['home']), "id": str(uuid.uuid4())[:8]})
                    st.rerun()
            with st.expander("View Breakdown"):
                for e in edge_list:
                    if "STAR OUT" in e or "INJURY" in e: st.markdown("<span style='color:#e74c3c;font-weight:700'>" + e + "</span>", unsafe_allow_html=True)
                    elif "3PT EDGE" in e: st.markdown("<span style='color:#3498db;font-weight:700'>" + e + "</span>", unsafe_allow_html=True)
                    elif "BPI vs VEGAS GAP" in e or "GAP" in e: st.markdown("<span style='color:#2ecc71;font-weight:700'>" + e + "</span>", unsafe_allow_html=True)
                    elif "FATIGUE" in e: st.markdown("<span style='color:#e67e22;font-weight:700'>" + e + "</span>", unsafe_allow_html=True)
                    else: st.markdown("- " + e)
            st.markdown("---")
    st.divider()

    # VEGAS vs KALSHI MISPRICING
    st.subheader("VEGAS vs KALSHI MISPRICING ALERT")
    st.caption("Buy when Kalshi underprices Vegas favorite | 5%+ gap = edge")
    mispricings = []
    for g in games:
        if g['status'] in ['STATUS_FINAL', 'STATUS_FULL_TIME']: continue
        away, home = g['away'], g['home']
        vegas = g.get('vegas_odds', {})
        away_code = KALSHI_CODES.get(away, "XXX")
        home_code = KALSHI_CODES.get(home, "XXX")
        kalshi_data = kalshi_ml_data.get(away_code + "@" + home_code, {})
        if not kalshi_data: continue
        home_ml_val, away_ml_val, spread_val = vegas.get('homeML'), vegas.get('awayML'), vegas.get('spread')
        if home_ml_val and away_ml_val:
            vegas_home_prob = american_to_implied_prob(home_ml_val) * 100
            vegas_away_prob = american_to_implied_prob(away_ml_val) * 100
            total = vegas_home_prob + vegas_away_prob
            vegas_home_prob = vegas_home_prob / total * 100
            vegas_away_prob = vegas_away_prob / total * 100
        elif spread_val:
            try:
                vegas_home_prob = max(10, min(90, 50 - (float(spread_val) * 2.8)))
                vegas_away_prob = 100 - vegas_home_prob
            except: continue
        else: continue
        kalshi_home_prob = kalshi_data.get('home_implied', 50)
        kalshi_away_prob = kalshi_data.get('away_implied', 50)
        summary = fetch_game_summary(g["game_id"])
        bpi = parse_predictor(summary) if summary else None
        bpi_prob = bpi.get("home_win_pct", 0) * 100 if bpi else 0
        home_edge = vegas_home_prob - kalshi_home_prob
        away_edge = vegas_away_prob - kalshi_away_prob
        if home_edge >= 5 or away_edge >= 5:
            if home_edge >= away_edge:
                team, vp, kp, edge = home, vegas_home_prob, kalshi_home_prob, home_edge
                action = "YES" if kalshi_data.get('yes_team_code', '').upper() == home_code.upper() else "NO"
            else:
                team, vp, kp, edge = away, vegas_away_prob, kalshi_away_prob, away_edge
                action = "YES" if kalshi_data.get('yes_team_code', '').upper() == away_code.upper() else "NO"
            mp = {'game': g, 'team': team, 'vegas_prob': vp, 'kalshi_prob': kp, 'edge': edge, 'action': action}
            if bpi_prob > 0: mp['bpi_prob'] = bpi_prob
            mispricings.append(mp)
    mispricings.sort(key=lambda x: x['edge'], reverse=True)
    if mispricings:
        st.success(str(len(mispricings)) + " mispricing opportunities found!")
        for mp in mispricings:
            g = mp['game']
            edge_color = "#ff6b6b" if mp['edge'] >= 10 else ("#22c55e" if mp['edge'] >= 7 else "#eab308")
            edge_label = "STRONG" if mp['edge'] >= 10 else ("GOOD" if mp['edge'] >= 7 else "EDGE")
            action_color = "#22c55e" if mp['action'] == "YES" else "#ef4444"
            status_text = "Q" + str(g['period']) + " " + g['clock'] if g['period'] > 0 else (g.get('game_datetime', 'Scheduled') or 'Scheduled')
            st.markdown("**" + g['away'] + " @ " + g['home'] + "** | " + status_text)
            box_html = "<div style='background:#0f172a;padding:16px;border-radius:10px;border:2px solid " + edge_color + ";margin-bottom:12px'>"
            box_html += "<div style='font-size:1.4em;font-weight:bold;color:#fff;margin-bottom:8px'>BUY <span style='color:" + action_color + ";background:" + action_color + "22;padding:4px 12px;border-radius:6px'>" + mp['action'] + "</span> on Kalshi</div>"
            box_html += "<div style='color:#aaa;margin-bottom:12px'>" + mp['action'] + " = " + mp['team'] + " wins</div>"
            box_html += "<table style='width:100%;text-align:center;color:#fff'><tr style='color:#888'><td>Vegas</td><td>Kalshi</td>"
            if mp.get('bpi_prob'): box_html += "<td>ESPN BPI</td>"
            box_html += "<td>EDGE</td></tr><tr style='font-size:1.3em;font-weight:bold'><td>" + str(round(mp['vegas_prob'])) + "%</td><td>" + str(round(mp['kalshi_prob'])) + "c</td>"
            if mp.get('bpi_prob'): box_html += "<td>" + str(round(mp['bpi_prob'])) + "%</td>"
            box_html += "<td style='color:" + edge_color + "'>+" + str(round(mp['edge'])) + "%</td></tr></table></div>"
            st.markdown(box_html, unsafe_allow_html=True)
            st.link_button("BUY " + mp['action'] + " (" + mp['team'] + ")", get_kalshi_game_link(g['away'], g['home']), use_container_width=True)
            st.markdown("---")
    else:
        st.info("No mispricings found (need 5%+ gap between Vegas and Kalshi)")
    st.divider()

    # INJURY REPORT
    st.subheader("INJURY REPORT")
    today_teams = set([g['away'] for g in games] + [g['home'] for g in games])
    injury_found = False
    for team in sorted(today_teams):
        team_injuries = injuries.get(team, [])
        out_players = [p for p in team_injuries if "out" in (p.get("status", "") or "").lower()]
        dtd_players = [p for p in team_injuries if "day" in (p.get("status", "") or "").lower() or "doubt" in (p.get("status", "") or "").lower()]
        if out_players or dtd_players:
            injury_found = True
            for p in out_players: st.markdown("**" + team + "**: [OUT] " + p['name'] + " - " + p['status'])
            for p in dtd_players: st.markdown("**" + team + "**: [DTD] " + p['name'] + " - " + p['status'])
    if not injury_found: st.info("No injuries reported for today's teams.")
    st.divider()

    # POSITION TRACKER
    st.subheader("POSITION TRACKER")
    today_games_list = [(g['away'] + " @ " + g['home'], g['away'], g['home']) for g in games]
    with st.expander("ADD NEW POSITION", expanded=False):
        if today_games_list:
            ac1, ac2 = st.columns(2)
            with ac1:
                game_sel = st.selectbox("Select Game", [tg[0] for tg in today_games_list], key="add_game")
                sel_game = next((tg for tg in today_games_list if tg[0] == game_sel), None)
            with ac2:
                bet_type = st.selectbox("Bet Type", ["ML (Moneyline)", "Totals (Over/Under)", "Spread"], key="add_type")
            ac3, ac4 = st.columns(2)
            with ac3:
                if bet_type == "ML (Moneyline)": pick = st.selectbox("Pick", [sel_game[1], sel_game[2]] if sel_game else [], key="add_pick")
                elif bet_type == "Spread": pick = st.selectbox("Pick Team", [sel_game[1], sel_game[2]] if sel_game else [], key="add_pick")
                else: pick = st.selectbox("Pick", ["YES (Over)", "NO (Under)"], key="add_totals_pick")
            with ac4:
                if "Totals" in bet_type: line = st.selectbox("Line", THRESHOLDS, key="add_line")
                elif bet_type == "Spread":
                    spread_options = ["-1.5", "-2.5", "-3.5", "-4.5", "-5.5", "-6.5", "-7.5", "-8.5", "-9.5", "-10.5", "+1.5", "+2.5", "+3.5", "+4.5", "+5.5", "+6.5", "+7.5", "+8.5", "+9.5", "+10.5"]
                    line = st.selectbox("Spread Line", spread_options, index=5, key="add_spread_line")
                else: line = "-"
            ac5, ac6, ac7 = st.columns(3)
            with ac5: entry_price = st.number_input("Entry Price (c)", 1, 99, 50, key="add_price")
            with ac6: contracts = st.number_input("Contracts", 1, 10000, 10, key="add_contracts")
            with ac7:
                cost = entry_price * contracts / 100
                st.metric("Cost", "$" + "{:.2f}".format(cost))
                st.caption("Win: +$" + "{:.2f}".format(contracts - cost))
            if st.button("ADD POSITION", use_container_width=True, key="add_pos_btn"):
                if sel_game:
                    if bet_type == "ML (Moneyline)": pos_type, pos_pick, pos_line = "ML", pick, "-"
                    elif bet_type == "Spread": pos_type, pos_pick, pos_line = "Spread", pick, str(line)
                    else: pos_type, pos_pick, pos_line = "Totals", pick.split()[0], str(line)
                    st.session_state.positions.append({"game": sel_game[1] + "@" + sel_game[2], "pick": pos_pick, "type": pos_type, "line": pos_line, "price": entry_price, "contracts": contracts, "link": get_kalshi_game_link(sel_game[1], sel_game[2]), "id": str(uuid.uuid4())[:8]})
                    st.success("Added!")
                    st.rerun()
    if st.session_state.positions:
        st.markdown("---")
        for idx, pos in enumerate(st.session_state.positions):
            current = next((g for g in games if g['away'] + "@" + g['home'] == pos['game']), None)
            pc1, pc2, pc3, pc4, pc5 = st.columns([2.5, 1.5, 1.5, 1.5, 1])
            with pc1:
                st.markdown("**" + pos['game'] + "**")
                if current:
                    if current['period'] > 0 and current['status'] not in ['STATUS_FINAL', 'STATUS_FULL_TIME']: st.caption("LIVE Q" + str(current['period']) + " " + current['clock'] + " | " + str(current['away_score']) + "-" + str(current['home_score']))
                    elif current['status'] in ['STATUS_FINAL', 'STATUS_FULL_TIME']: st.caption("FINAL " + str(current['away_score']) + "-" + str(current['home_score']))
                    else: st.caption("Scheduled")
            with pc2:
                if pos['type'] == "ML": st.write(pos['pick'] + " ML")
                else: st.write(pos['pick'] + " " + str(pos['line']))
            with pc3:
                st.write(str(pos.get('contracts', 10)) + " @ " + str(pos.get('price', 50)) + "c")
                st.caption("$" + "{:.2f}".format(pos.get('price', 50) * pos.get('contracts', 10) / 100))
            with pc4: st.link_button("Kalshi", pos['link'], use_container_width=True)
            with pc5:
                if st.button("X", key="del_" + pos['id']):
                    remove_position(pos['id'])
                    st.rerun()
        st.markdown("---")
        if st.button("CLEAR ALL POSITIONS", use_container_width=True, type="primary"):
            st.session_state.positions = []
            st.rerun()
    else:
        st.caption("No positions tracked yet.")

    # ALL GAMES TODAY
    st.divider()
    st.subheader("ALL GAMES TODAY")
    for g in games:
        if g['status'] in ['STATUS_FINAL', 'STATUS_FULL_TIME']:
            status = "FINAL: " + str(g['away_score']) + "-" + str(g['home_score'])
            color = "#666"
        elif g['period'] > 0:
            status = "LIVE Q" + str(g['period']) + " " + g['clock'] + " | " + str(g['away_score']) + "-" + str(g['home_score'])
            color = "#22c55e"
        else:
            status = (g.get('game_datetime', 'TBD') or 'TBD') + " | Spread: " + str(g.get('vegas_odds', {}).get('spread', 'N/A'))
            color = "#888"
        st.markdown("<div style='background:#1e1e2e;padding:12px;border-radius:8px;margin-bottom:8px;border-left:3px solid " + color + "'><b style='color:#fff'>" + g['away'] + " @ " + g['home'] + "</b><br><span style='color:" + color + "'>" + status + "</span></div>", unsafe_allow_html=True)
