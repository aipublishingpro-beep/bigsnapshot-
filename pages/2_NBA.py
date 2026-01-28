import streamlit as st
from streamlit_autorefresh import st_autorefresh
import streamlit.components.v1 as components

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

VERSION = "10.2"
LEAGUE_AVG_TOTAL = 225
THRESHOLDS = [210.5, 215.5, 220.5, 225.5, 230.5, 235.5, 240.5, 245.5]

if 'positions' not in st.session_state:
    st.session_state.positions = []

TEAM_ABBREVS = {"Atlanta Hawks": "Atlanta", "Boston Celtics": "Boston", "Brooklyn Nets": "Brooklyn", "Charlotte Hornets": "Charlotte", "Chicago Bulls": "Chicago", "Cleveland Cavaliers": "Cleveland", "Dallas Mavericks": "Dallas", "Denver Nuggets": "Denver", "Detroit Pistons": "Detroit", "Golden State Warriors": "Golden State", "Houston Rockets": "Houston", "Indiana Pacers": "Indiana", "LA Clippers": "LA Clippers", "Los Angeles Clippers": "LA Clippers", "LA Lakers": "LA Lakers", "Los Angeles Lakers": "LA Lakers", "Memphis Grizzlies": "Memphis", "Miami Heat": "Miami", "Milwaukee Bucks": "Milwaukee", "Minnesota Timberwolves": "Minnesota", "New Orleans Pelicans": "New Orleans", "New York Knicks": "New York", "Oklahoma City Thunder": "Oklahoma City", "Orlando Magic": "Orlando", "Philadelphia 76ers": "Philadelphia", "Phoenix Suns": "Phoenix", "Portland Trail Blazers": "Portland", "Sacramento Kings": "Sacramento", "San Antonio Spurs": "San Antonio", "Toronto Raptors": "Toronto", "Utah Jazz": "Utah", "Washington Wizards": "Washington"}

KALSHI_CODES = {"Atlanta": "ATL", "Boston": "BOS", "Brooklyn": "BKN", "Charlotte": "CHA", "Chicago": "CHI", "Cleveland": "CLE", "Dallas": "DAL", "Denver": "DEN", "Detroit": "DET", "Golden State": "GSW", "Houston": "HOU", "Indiana": "IND", "LA Clippers": "LAC", "LA Lakers": "LAL", "Memphis": "MEM", "Miami": "MIA", "Milwaukee": "MIL", "Minnesota": "MIN", "New Orleans": "NOP", "New York": "NYK", "Oklahoma City": "OKC", "Orlando": "ORL", "Philadelphia": "PHI", "Phoenix": "PHX", "Portland": "POR", "Sacramento": "SAC", "San Antonio": "SAS", "Toronto": "TOR", "Utah": "UTA", "Washington": "WAS"}

TEAM_COLORS = {"Atlanta": "#E03A3E", "Boston": "#007A33", "Brooklyn": "#000000", "Charlotte": "#1D1160", "Chicago": "#CE1141", "Cleveland": "#860038", "Dallas": "#00538C", "Denver": "#0E2240", "Detroit": "#C8102E", "Golden State": "#1D428A", "Houston": "#CE1141", "Indiana": "#002D62", "LA Clippers": "#C8102E", "LA Lakers": "#552583", "Memphis": "#5D76A9", "Miami": "#98002E", "Milwaukee": "#00471B", "Minnesota": "#0C2340", "New Orleans": "#0C2340", "New York": "#006BB6", "Oklahoma City": "#007AC1", "Orlando": "#0077C0", "Philadelphia": "#006BB6", "Phoenix": "#1D1160", "Portland": "#E03A3E", "Sacramento": "#5A2D81", "San Antonio": "#C4CED4", "Toronto": "#CE1141", "Utah": "#002B5C", "Washington": "#002B5C"}

# Reverse lookup: abbreviation -> team color
ABBR_COLORS = {"ATL": "#E03A3E", "BOS": "#007A33", "BKN": "#000000", "CHA": "#1D1160", "CHI": "#CE1141", "CLE": "#860038", "DAL": "#00538C", "DEN": "#0E2240", "DET": "#C8102E", "GSW": "#1D428A", "HOU": "#CE1141", "IND": "#002D62", "LAC": "#C8102E", "LAL": "#552583", "MEM": "#5D76A9", "MIA": "#98002E", "MIL": "#00471B", "MIN": "#0C2340", "NOP": "#0C2340", "NYK": "#006BB6", "OKC": "#007AC1", "ORL": "#0077C0", "PHI": "#006BB6", "PHX": "#1D1160", "POR": "#E03A3E", "SAC": "#5A2D81", "SAS": "#C4CED4", "TOR": "#CE1141", "UTA": "#002B5C", "WAS": "#002B5C"}

TEAM_STATS = {"Oklahoma City": {"net": 12.0, "pace": 98.8}, "Cleveland": {"net": 10.5, "pace": 97.2}, "Boston": {"net": 9.5, "pace": 99.8}, "Denver": {"net": 7.8, "pace": 98.5}, "New York": {"net": 5.5, "pace": 97.5}, "Houston": {"net": 5.2, "pace": 99.5}, "LA Lakers": {"net": 4.5, "pace": 98.5}, "Phoenix": {"net": 4.0, "pace": 98.2}, "Minnesota": {"net": 4.0, "pace": 98.2}, "Golden State": {"net": 3.5, "pace": 100.2}, "Dallas": {"net": 3.0, "pace": 99.0}, "Milwaukee": {"net": 2.5, "pace": 98.8}, "Miami": {"net": 2.0, "pace": 97.2}, "Philadelphia": {"net": 1.5, "pace": 97.5}, "Sacramento": {"net": 1.0, "pace": 100.5}, "Orlando": {"net": 0.5, "pace": 96.8}, "LA Clippers": {"net": 0.0, "pace": 97.8}, "Indiana": {"net": -0.5, "pace": 102.5}, "Memphis": {"net": -1.0, "pace": 99.8}, "San Antonio": {"net": -1.5, "pace": 99.2}, "Detroit": {"net": -2.0, "pace": 99.5}, "Atlanta": {"net": -2.5, "pace": 100.5}, "Chicago": {"net": -3.0, "pace": 98.8}, "Toronto": {"net": -3.5, "pace": 97.8}, "Brooklyn": {"net": -5.0, "pace": 98.2}, "Portland": {"net": -5.5, "pace": 98.8}, "Charlotte": {"net": -6.5, "pace": 99.5}, "Utah": {"net": -7.0, "pace": 98.5}, "New Orleans": {"net": -8.0, "pace": 99.0}, "Washington": {"net": -10.0, "pace": 100.8}}

STAR_PLAYERS = {"Boston": ["Jayson Tatum", "Jaylen Brown"], "Cleveland": ["Donovan Mitchell", "Darius Garland"], "Oklahoma City": ["Shai Gilgeous-Alexander", "Chet Holmgren"], "New York": ["Jalen Brunson", "Karl-Anthony Towns"], "Milwaukee": ["Giannis Antetokounmpo", "Damian Lillard"], "Denver": ["Nikola Jokic", "Jamal Murray"], "Minnesota": ["Anthony Edwards", "Rudy Gobert"], "Dallas": ["Luka Doncic", "Kyrie Irving"], "Phoenix": ["Kevin Durant", "Devin Booker"], "LA Lakers": ["LeBron James", "Anthony Davis"], "Golden State": ["Stephen Curry"], "Miami": ["Bam Adebayo", "Tyler Herro"], "Philadelphia": ["Joel Embiid", "Tyrese Maxey"], "Memphis": ["Ja Morant"], "New Orleans": ["Zion Williamson"], "Sacramento": ["Domantas Sabonis", "De'Aaron Fox"], "Indiana": ["Tyrese Haliburton", "Pascal Siakam"], "Orlando": ["Paolo Banchero", "Franz Wagner"], "Houston": ["Jalen Green", "Alperen Sengun"], "Atlanta": ["Trae Young"], "Charlotte": ["LaMelo Ball"], "Detroit": ["Cade Cunningham"], "San Antonio": ["Victor Wembanyama"], "LA Clippers": ["James Harden", "Kawhi Leonard"]}

STAR_TIERS = {"Nikola Jokic": 3, "Shai Gilgeous-Alexander": 3, "Giannis Antetokounmpo": 3, "Luka Doncic": 3, "Joel Embiid": 3, "Jayson Tatum": 3, "LeBron James": 3, "Stephen Curry": 3, "Kevin Durant": 3, "Anthony Edwards": 3, "Donovan Mitchell": 2, "Jaylen Brown": 2, "Damian Lillard": 2, "Anthony Davis": 2, "Kyrie Irving": 2, "Devin Booker": 2, "Ja Morant": 2, "Trae Young": 2, "Tyrese Haliburton": 2, "De'Aaron Fox": 2, "Jalen Brunson": 2, "Paolo Banchero": 2, "Victor Wembanyama": 2, "LaMelo Ball": 2, "Cade Cunningham": 2, "Tyrese Maxey": 2}

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
            for c in competitors:
                full_name = c.get("team", {}).get("displayName", "")
                team_name = TEAM_ABBREVS.get(full_name, full_name)
                score = int(c.get("score", 0) or 0)
                if c.get("homeAway") == "home": home_team, home_score = team_name, score
                else: away_team, away_score = team_name, score
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
                            if ":" in clock: minutes_played = completed_quarters + (12 - int(clock.split(":")[0]))
                            else: minutes_played = completed_quarters + 12
                        except: minutes_played = completed_quarters + 12
                    else: minutes_played = completed_quarters
                else: minutes_played = 48 + (period - 4) * 5
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
            games.append({"away": away_team, "home": home_team, "away_score": away_score, "home_score": home_score, "status": status, "period": period, "clock": clock, "minutes_played": minutes_played, "total_score": home_score + away_score, "game_id": game_id, "vegas_odds": vegas_odds, "game_time": game_time_str, "game_datetime": game_datetime_str})
        return games
    except Exception as e: st.error("ESPN fetch error: " + str(e)); return []

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
            yes_bid, yes_ask = m.get("yes_bid", 0) or 0, m.get("yes_ask", 0) or 0
            yes_price = yes_ask if yes_ask > 0 else (yes_bid if yes_bid > 0 else 50)
            yes_team_code = yes_team_code.upper()
            if yes_team_code == home_code.upper(): home_implied, away_implied = yes_price, 100 - yes_price
            else: away_implied, home_implied = yes_price, 100 - yes_price
            if game_key not in markets:
                markets[game_key] = {"away_code": away_code, "home_code": home_code, "yes_team_code": yes_team_code, "ticker": ticker, "yes_bid": yes_bid, "yes_ask": yes_ask, "yes_price": yes_price, "away_implied": away_implied, "home_implied": home_implied}
        return markets
    except Exception as e: st.error("Kalshi ML fetch error: " + str(e)); return {}

@st.cache_data(ttl=60)
def fetch_kalshi_spreads():
    url = "https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXNBASPREAD&status=open&limit=200"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        spreads = {}
        for m in data.get("markets", []):
            ticker = m.get("ticker", "")
            yes_bid, yes_ask = m.get("yes_bid", 0) or 0, m.get("yes_ask", 0) or 0
            if "KXNBASPREAD-" in ticker:
                parts = ticker.replace("KXNBASPREAD-", "")
                if len(parts) >= 13:
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
                                if game_key not in spreads: spreads[game_key] = []
                                spreads[game_key].append({"line": spread_line, "team_code": spread_team, "ticker": ticker, "yes_bid": yes_bid, "yes_ask": yes_ask, "yes_price": yes_ask if yes_ask > 0 else (yes_bid if yes_bid > 0 else 50)})
        return spreads
    except: return {}

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
    if not game_id: return [], ""
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary?event={game_id}"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        plays = []
        for p in data.get("plays", [])[-15:]:
            team_data = p.get("team", {})
            team_abbr = team_data.get("abbreviation", "") if team_data else ""
            team_name = team_data.get("displayName", "") if team_data else ""
            team_short = TEAM_ABBREVS.get(team_name, team_name)
            plays.append({"text": p.get("text", ""), "period": p.get("period", {}).get("number", 0), "clock": p.get("clock", {}).get("displayValue", ""), "score_value": p.get("scoreValue", 0), "play_type": p.get("type", {}).get("text", ""), "team": team_short, "team_abbr": team_abbr})
        poss_team = ""
        if plays:
            for p in reversed(plays):
                if p.get("team_abbr"):
                    poss_team = p["team"]
                    break
        return plays[-10:], poss_team
    except: return [], ""

def render_nba_court(away, home, away_score, home_score, possession, period, clock):
    away_color, home_color = TEAM_COLORS.get(away, "#666"), TEAM_COLORS.get(home, "#666")
    away_code, home_code = KALSHI_CODES.get(away, "AWY"), KALSHI_CODES.get(home, "HME")
    poss_away = "visible" if possession == away else "hidden"
    poss_home = "visible" if possession == home else "hidden"
    period_text = f"Q{period}" if period <= 4 else f"OT{period-4}"
    return f'''<div style="background:#1a1a2e;border-radius:12px;padding:10px;"><svg viewBox="0 0 500 280" style="width:100%;max-width:500px;"><rect x="20" y="20" width="460" height="200" fill="#2d4a22" stroke="#fff" stroke-width="2" rx="8"/><circle cx="250" cy="120" r="35" fill="none" stroke="#fff" stroke-width="2"/><circle cx="250" cy="120" r="4" fill="#fff"/><line x1="250" y1="20" x2="250" y2="220" stroke="#fff" stroke-width="2"/><path d="M 20 50 Q 100 120 20 190" fill="none" stroke="#fff" stroke-width="2"/><rect x="20" y="70" width="70" height="100" fill="none" stroke="#fff" stroke-width="2"/><circle cx="90" cy="120" r="25" fill="none" stroke="#fff" stroke-width="2"/><circle cx="35" cy="120" r="8" fill="none" stroke="#ff6b35" stroke-width="3"/><path d="M 480 50 Q 400 120 480 190" fill="none" stroke="#fff" stroke-width="2"/><rect x="410" y="70" width="70" height="100" fill="none" stroke="#fff" stroke-width="2"/><circle cx="410" cy="120" r="25" fill="none" stroke="#fff" stroke-width="2"/><circle cx="465" cy="120" r="8" fill="none" stroke="#ff6b35" stroke-width="3"/><rect x="40" y="228" width="90" height="48" fill="{away_color}" rx="6"/><text x="85" y="250" fill="#fff" font-size="14" font-weight="bold" text-anchor="middle">{away_code}</text><text x="85" y="270" fill="#fff" font-size="18" font-weight="bold" text-anchor="middle">{away_score}</text><circle cx="135" cy="252" r="8" fill="#ffd700" visibility="{poss_away}"/><rect x="370" y="228" width="90" height="48" fill="{home_color}" rx="6"/><text x="415" y="250" fill="#fff" font-size="14" font-weight="bold" text-anchor="middle">{home_code}</text><text x="415" y="270" fill="#fff" font-size="18" font-weight="bold" text-anchor="middle">{home_score}</text><circle cx="365" cy="252" r="8" fill="#ffd700" visibility="{poss_home}"/><text x="250" y="258" fill="#fff" font-size="16" font-weight="bold" text-anchor="middle">{period_text} {clock}</text></svg></div>'''

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

# FETCH DATA
games = fetch_espn_games()
kalshi_ml = fetch_kalshi_ml()
kalshi_spreads = fetch_kalshi_spreads()
injuries = fetch_injuries()
b2b_teams = fetch_yesterday_teams()

live_games = [g for g in games if g['status'] in ['STATUS_IN_PROGRESS', 'STATUS_HALFTIME', 'STATUS_END_PERIOD'] or (g['period'] > 0 and g['status'] not in ['STATUS_FINAL', 'STATUS_FULL_TIME'])]
scheduled_games = [g for g in games if g['status'] == 'STATUS_SCHEDULED' and g['period'] == 0]
final_games = [g for g in games if g['status'] in ['STATUS_FINAL', 'STATUS_FULL_TIME']]

# HEADER
st.title("🏀 BIGSNAPSHOT NBA EDGE FINDER")
st.caption(f"v{VERSION} • {now.strftime('%b %d, %Y %I:%M %p ET')} • Vegas vs Kalshi Mispricing Detector")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Today's Games", len(games))
c2.metric("Live Now", len(live_games))
c3.metric("Scheduled", len(scheduled_games))
c4.metric("Final", len(final_games))

st.divider()

# VEGAS vs KALSHI MISPRICING ALERT
st.subheader("💰 VEGAS vs KALSHI MISPRICING ALERT")
st.caption("Buy when Kalshi underprices Vegas favorite • 5%+ gap = edge")

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
        vegas_home_prob = american_to_implied_prob(home_ml) * 100
        vegas_away_prob = american_to_implied_prob(away_ml) * 100
        total = vegas_home_prob + vegas_away_prob
        vegas_home_prob, vegas_away_prob = vegas_home_prob / total * 100, vegas_away_prob / total * 100
    elif spread:
        try: vegas_home_prob = max(10, min(90, 50 - (float(spread) * 2.8))); vegas_away_prob = 100 - vegas_home_prob
        except: continue
    else: continue
    kalshi_home_prob, kalshi_away_prob = kalshi_data.get('home_implied', 50), kalshi_data.get('away_implied', 50)
    home_edge, away_edge = vegas_home_prob - kalshi_home_prob, vegas_away_prob - kalshi_away_prob
    if home_edge >= 5 or away_edge >= 5:
        if home_edge >= away_edge:
            team, vegas_prob, kalshi_prob, edge = home, vegas_home_prob, kalshi_home_prob, home_edge
            action = "YES" if kalshi_data.get('yes_team_code', '').upper() == home_code.upper() else "NO"
        else:
            team, vegas_prob, kalshi_prob, edge = away, vegas_away_prob, kalshi_away_prob, away_edge
            action = "YES" if kalshi_data.get('yes_team_code', '').upper() == away_code.upper() else "NO"
        mispricings.append({'game': g, 'team': team, 'vegas_prob': vegas_prob, 'kalshi_prob': kalshi_prob, 'edge': edge, 'action': action})

mispricings.sort(key=lambda x: x['edge'], reverse=True)

if mispricings:
    mp_col1, mp_col2 = st.columns([3, 1])
    with mp_col1: st.success(f"🔥 {len(mispricings)} mispricing opportunities found!")
    with mp_col2:
        if st.button(f"➕ ADD ALL ({len(mispricings)})", key="add_all_mispricing", use_container_width=True):
            added = 0
            for mp in mispricings:
                g = mp['game']
                game_key = f"{g['away']}@{g['home']}"
                if not any(pos['game'] == game_key for pos in st.session_state.positions):
                    st.session_state.positions.append({"game": game_key, "pick": f"{mp['action']} ({mp['team']})", "type": "ML", "line": "-", "price": round(mp['kalshi_prob']), "contracts": 10, "link": get_kalshi_game_link(g['away'], g['home']), "id": str(uuid.uuid4())[:8]})
                    added += 1
            st.toast(f"✅ Added {added} positions!")
            st.rerun()
    for mp in mispricings:
        g = mp['game']
        game_key = f"{g['away']}@{g['home']}"
        edge_color = "#ff6b6b" if mp['edge'] >= 10 else ("#22c55e" if mp['edge'] >= 7 else "#eab308")
        edge_label = "🔥 STRONG" if mp['edge'] >= 10 else ("🟢 GOOD" if mp['edge'] >= 7 else "🟡 EDGE")
        action_color = "#22c55e" if mp['action'] == "YES" else "#ef4444"
        status_text = f"Q{g['period']} {g['clock']}" if g['period'] > 0 else (g.get('game_datetime', 'Scheduled') or 'Scheduled')
        col1, col2 = st.columns([3, 1])
        with col1: st.markdown(f"**{g['away']} @ {g['home']}** • {status_text}")
        with col2: st.markdown(f"<span style='color:{edge_color};font-weight:bold'>{edge_label} +{round(mp['edge'])}%</span>", unsafe_allow_html=True)
        st.markdown(f"""<div style="background:#0f172a;padding:16px;border-radius:10px;border:2px solid {edge_color};margin-bottom:12px"><div style="font-size:1.4em;font-weight:bold;color:#fff;margin-bottom:8px">🎯 BUY <span style="color:{action_color};background:{action_color}22;padding:4px 12px;border-radius:6px">{mp['action']}</span> on Kalshi</div><div style="color:#aaa;margin-bottom:12px">{mp['action']} = {mp['team']} wins</div><table style="width:100%;text-align:center;color:#fff"><tr style="color:#888"><td>Vegas</td><td>Kalshi</td><td>EDGE</td></tr><tr style="font-size:1.3em;font-weight:bold"><td>{round(mp['vegas_prob'])}%</td><td>{round(mp['kalshi_prob'])}¢</td><td style="color:{edge_color}">+{round(mp['edge'])}%</td></tr></table></div>""", unsafe_allow_html=True)
        bc1, bc2 = st.columns(2)
        with bc1: st.link_button(f"🎯 BUY {mp['action']} ({mp['team']})", get_kalshi_game_link(g['away'], g['home']), use_container_width=True)
        with bc2:
            already = any(pos['game'] == game_key for pos in st.session_state.positions)
            if already: st.success("✅ Tracked")
            elif st.button("➕ Track", key=f"mp_{game_key}"):
                st.session_state.positions.append({"game": game_key, "pick": f"{mp['action']} ({mp['team']})", "type": "ML", "line": "-", "price": round(mp['kalshi_prob']), "contracts": 10, "link": get_kalshi_game_link(g['away'], g['home']), "id": str(uuid.uuid4())[:8]})
                st.rerun()
else:
    st.info("🔍 No mispricings found (need 5%+ gap between Vegas & Kalshi)")

st.divider()

# LIVE EDGE MONITOR
st.subheader("🎮 LIVE EDGE MONITOR")

if live_games:
    for g in live_games:
        away, home, total, mins, game_id = g['away'], g['home'], g['total_score'], g['minutes_played'], g['game_id']
        plays, possession = fetch_plays(game_id)
        st.markdown(f"### {away} @ {home}")
        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown(render_nba_court(away, home, g['away_score'], g['home_score'], possession, g['period'], g['clock']), unsafe_allow_html=True)
        with col2:
            st.markdown("**📋 LAST 10 PLAYS**")
            tts_on = st.checkbox("🔊 Announce plays", key=f"tts_{game_id}")
            if plays:
                for i, p in enumerate(reversed(plays)):
                    icon, color = get_play_icon(p['play_type'], p['score_value'])
                    play_text = p['text'][:42] if p['text'] else "Play"
                    team_abbr = p.get('team_abbr', '')
                    team_color = ABBR_COLORS.get(team_abbr, '#555')
                    if team_abbr:
                        badge = f"<b style='color:#fff;background:{team_color};padding:2px 6px;border-radius:4px;margin-right:6px'>{team_abbr}</b>"
                    else:
                        badge = ""
                    st.markdown(f"<div style='padding:6px 10px;margin:3px 0;background:#1e1e2e;border-radius:6px;border-left:4px solid {team_color}'>{badge}<span style='color:{color}'>{icon}</span> Q{p['period']} {p['clock']} • {play_text}</div>", unsafe_allow_html=True)
                    if i == 0 and tts_on and p['text']:
                        speak_play(f"Q{p['period']} {p['clock']}. {p['text']}")
            else:
                st.caption("Waiting for plays...")
        if mins >= 6:
            proj = calc_projection(total, mins)
            pace = total / mins if mins > 0 else 0
            pace_label, pace_color = get_pace_label(pace)
            lead = g['home_score'] - g['away_score']
            leader = home if g['home_score'] > g['away_score'] else away
            kalshi_link = get_kalshi_game_link(away, home)
            st.markdown(f"<div style='background:#1e1e2e;padding:12px;border-radius:8px;margin-top:8px'><b>Score:</b> {total} pts in {mins} min • <b>Pace:</b> <span style='color:{pace_color}'>{pace_label}</span> ({pace:.1f}/min)<br><b>Projection:</b> {proj} pts • <b>Lead:</b> {leader} +{abs(lead)}</div>", unsafe_allow_html=True)
            away_code, home_code = KALSHI_CODES.get(away, "XXX"), KALSHI_CODES.get(home, "XXX")
            kalshi_data = kalshi_ml.get(away_code + "@" + home_code, {})
            st.markdown("**🎯 MONEYLINE**")
            if abs(lead) >= 10:
                ml_pick = leader
                ml_confidence = "🔥 STRONG" if abs(lead) >= 15 else "🟢 GOOD"
                if kalshi_data:
                    if leader == home: ml_action = "YES" if kalshi_data.get('yes_team_code', '').upper() == home_code.upper() else "NO"
                    else: ml_action = "YES" if kalshi_data.get('yes_team_code', '').upper() == away_code.upper() else "NO"
                    st.link_button(f"{ml_confidence} BUY {ml_action} ({ml_pick} ML) • Lead +{abs(lead)}", kalshi_link, use_container_width=True)
                else: st.link_button(f"{ml_confidence} {ml_pick} ML • Lead +{abs(lead)}", kalshi_link, use_container_width=True)
            else: st.caption(f"⏳ Wait for larger lead (currently {leader} +{abs(lead)})")
            st.markdown("**📊 TOTALS**")
            yes_lines = [(t, proj - t) for t in sorted(THRESHOLDS) if proj - t >= 6]
            no_lines = [(t, t - proj) for t in sorted(THRESHOLDS, reverse=True) if t - proj >= 6]
            tc1, tc2 = st.columns(2)
            with tc1:
                st.markdown("<span style='color:#22c55e;font-weight:bold'>🟢 YES (Over) — go LOW</span>", unsafe_allow_html=True)
                if yes_lines:
                    for i, (line, cushion) in enumerate(yes_lines[:3]):
                        if cushion >= 20: safety = "🔒 FORTRESS"
                        elif cushion >= 12: safety = "✅ SAFE"
                        else: safety = "🎯 TIGHT"
                        rec = " ⭐REC" if i == 0 and cushion >= 12 else ""
                        st.link_button(f"{safety} YES {line} (+{int(cushion)}){rec}", kalshi_link, use_container_width=True)
                else: st.caption("No safe YES lines (need 6+ cushion)")
            with tc2:
                st.markdown("<span style='color:#ef4444;font-weight:bold'>🔴 NO (Under) — go HIGH</span>", unsafe_allow_html=True)
                if no_lines:
                    for i, (line, cushion) in enumerate(no_lines[:3]):
                        if cushion >= 20: safety = "🔒 FORTRESS"
                        elif cushion >= 12: safety = "✅ SAFE"
                        else: safety = "🎯 TIGHT"
                        rec = " ⭐REC" if i == 0 and cushion >= 12 else ""
                        st.link_button(f"{safety} NO {line} (+{int(cushion)}){rec}", kalshi_link, use_container_width=True)
                else: st.caption("No safe NO lines (need 6+ cushion)")
        else: st.caption("⏳ Waiting for 6+ minutes...")
        st.divider()
else:
    st.info("No live games right now")

# CUSHION SCANNER
st.subheader("🎯 CUSHION SCANNER (Totals)")
all_game_options = ["All Games"] + [f"{g['away']} @ {g['home']}" for g in games]
cush_col1, cush_col2, cush_col3 = st.columns(3)
with cush_col1: selected_game = st.selectbox("Select Game:", all_game_options, key="cush_game")
with cush_col2: min_mins = st.selectbox("Min PLAY TIME:", [8, 12, 16, 20, 24], index=1, key="cush_mins")
with cush_col3: side_choice = st.selectbox("Side:", ["NO (Under)", "YES (Over)"], key="cush_side")

if min_mins == 8:
    st.info("🦈 SHARK MODE: 8 min played = early entry. Only buy if cushion ≥12 (✅ SAFE or 🔒 FORTRESS)")
elif min_mins == 12:
    st.info("✅ SMART MONEY: 12 min played = pace locked. Cushion ≥6 is tradeable.")

cushion_data = []
for g in games:
    if g['status'] in ['STATUS_FINAL', 'STATUS_FULL_TIME']: continue
    game_name = f"{g['away']} @ {g['home']}"
    if selected_game != "All Games" and game_name != selected_game: continue
    if g['minutes_played'] < min_mins: continue
    total, mins = g['total_score'], g['minutes_played']
    vegas_ou = g.get('vegas_odds', {}).get('overUnder')
    if mins >= 8:
        proj = calc_projection(total, mins)
        pace_label = get_pace_label(total / mins)[0]
        status_text = f"Q{g['period']} {g['clock']}" if g['period'] > 0 else "Live"
    elif vegas_ou:
        try:
            proj = round(float(vegas_ou))
            pace_label = "📊 VEGAS"
            status_text = "Scheduled" if mins == 0 else f"Q{g['period']} {g['clock']} (early)"
        except:
            proj = LEAGUE_AVG_TOTAL
            pace_label = "⏳ PRE"
            status_text = "Scheduled"
    else:
        proj = LEAGUE_AVG_TOTAL
        pace_label = "⏳ PRE"
        status_text = "Scheduled"
    if side_choice == "YES (Over)": thresh_sorted = sorted(THRESHOLDS)
    else: thresh_sorted = sorted(THRESHOLDS, reverse=True)
    for idx, thresh in enumerate(thresh_sorted):
        cushion = (thresh - proj) if side_choice == "NO (Under)" else (proj - thresh)
        if cushion >= 6 or (selected_game != "All Games"):
            if cushion >= 20: safety_label = "🔒 FORTRESS"
            elif cushion >= 12: safety_label = "✅ SAFE"
            elif cushion >= 6: safety_label = "🎯 TIGHT"
            else: safety_label = "⚠️ RISKY"
            cushion_data.append({"game": game_name, "status": status_text, "proj": proj, "line": thresh, "cushion": cushion, "pace": pace_label, "link": get_kalshi_game_link(g['away'], g['home']), "mins": mins, "is_live": mins >= 8, "safety": safety_label, "is_recommended": idx == 0 and cushion >= 12})

safety_order = {"🔒 FORTRESS": 0, "✅ SAFE": 1, "🎯 TIGHT": 2, "⚠️ RISKY": 3}
cushion_data.sort(key=lambda x: (not x['is_live'], safety_order.get(x['safety'], 3), -x['cushion']))
if cushion_data:
    direction = "go LOW for safety" if side_choice == "YES (Over)" else "go HIGH for safety"
    st.caption(f"💡 {side_choice.split()[0]} bets: {direction}")
    max_results = 20 if selected_game != "All Games" else 10
    for cd in cushion_data[:max_results]:
        cc1, cc2, cc3, cc4 = st.columns([3, 1.2, 1.3, 2])
        with cc1:
            rec_badge = " ⭐REC" if cd.get('is_recommended') else ""
            st.markdown(f"**{cd['game']}** • {cd['status']}{rec_badge}")
            if cd['mins'] > 0: st.caption(f"{cd['pace']} • {cd['mins']} min played")
            else: st.caption(f"{cd['pace']} O/U: {cd['proj']}")
        with cc2: st.write(f"Proj: {cd['proj']} | Line: {cd['line']}")
        with cc3:
            cushion_color = "#22c55e" if cd['cushion'] >= 12 else ("#eab308" if cd['cushion'] >= 6 else "#ef4444")
            st.markdown(f"<span style='color:{cushion_color};font-weight:bold'>{cd['safety']}<br>+{round(cd['cushion'])}</span>", unsafe_allow_html=True)
        with cc4: st.link_button(f"BUY {'NO' if 'NO' in side_choice else 'YES'} {cd['line']}", cd['link'], use_container_width=True)
else:
    if selected_game != "All Games": st.info(f"Select a side and see all lines for {selected_game}")
    else:
        live_count = sum(1 for g in games if g['minutes_played'] >= min_mins and g['status'] not in ['STATUS_FINAL', 'STATUS_FULL_TIME'])
        if live_count == 0: st.info(f"⏳ No games have reached {min_mins}+ min play time yet. Waiting for tip-off...")
        else: st.info(f"No {side_choice.split()[0]} opportunities with 6+ cushion. Try switching sides or wait for pace to develop.")

st.divider()

# PACE SCANNER
st.subheader("📈 PACE SCANNER")
pace_data = [{"game": f"{g['away']} @ {g['home']}", "status": f"Q{g['period']} {g['clock']}", "total": g['total_score'], "pace": g['total_score']/g['minutes_played'], "pace_label": get_pace_label(g['total_score']/g['minutes_played'])[0], "pace_color": get_pace_label(g['total_score']/g['minutes_played'])[1], "proj": calc_projection(g['total_score'], g['minutes_played'])} for g in live_games if g['minutes_played'] >= 6]
pace_data.sort(key=lambda x: x['pace'])
if pace_data:
    for pd in pace_data:
        pc1, pc2, pc3, pc4 = st.columns([3, 2, 2, 2])
        with pc1: st.markdown(f"**{pd['game']}**")
        with pc2: st.write(f"{pd['status']} • {pd['total']} pts")
        with pc3: st.markdown(f"<span style='color:{pd['pace_color']};font-weight:bold'>{pd['pace_label']}</span>", unsafe_allow_html=True)
        with pc4: st.write(f"Proj: {pd['proj']}")
else: st.info("No live games with 6+ minutes played")

st.divider()

# PRE-GAME ALIGNMENT
with st.expander("🎯 PRE-GAME ALIGNMENT (Speculative)", expanded=True):
    st.caption("Model prediction for scheduled games • Click ➕ to add to tracker")
    if scheduled_games:
        all_picks = []
        for g in scheduled_games:
            away, home = g['away'], g['home']
            edge_score = calc_pregame_edge(away, home, injuries, b2b_teams)
            if edge_score >= 70: pick, edge_label, edge_color = home, "🟢 STRONG", "#22c55e"
            elif edge_score >= 60: pick, edge_label, edge_color = home, "🟢 GOOD", "#22c55e"
            elif edge_score <= 30: pick, edge_label, edge_color = away, "🟢 STRONG", "#22c55e"
            elif edge_score <= 40: pick, edge_label, edge_color = away, "🟢 GOOD", "#22c55e"
            else: pick, edge_label, edge_color = "WAIT", "🟡 NEUTRAL", "#eab308"
            all_picks.append({"away": away, "home": home, "pick": pick, "edge_label": edge_label, "edge_color": edge_color})
        actionable = [p for p in all_picks if p['pick'] != "WAIT"]
        if actionable:
            add_col1, add_col2 = st.columns([3, 1])
            with add_col1: st.caption(f"📊 {len(actionable)} actionable picks out of {len(all_picks)} games")
            with add_col2:
                if st.button(f"➕ ADD ALL ({len(actionable)})", key="add_all_pregame", use_container_width=True):
                    added = 0
                    for p in actionable:
                        game_key = f"{p['away']}@{p['home']}"
                        if not any(pos['game'] == game_key for pos in st.session_state.positions):
                            st.session_state.positions.append({"game": game_key, "pick": p['pick'], "type": "ML", "line": "-", "price": 50, "contracts": 10, "link": get_kalshi_game_link(p['away'], p['home']), "id": str(uuid.uuid4())[:8]})
                            added += 1
                    st.toast(f"✅ Added {added} positions!")
                    st.rerun()
            st.markdown("---")
        for p in all_picks:
            pg1, pg2, pg3, pg4 = st.columns([2.5, 1, 2, 1])
            game_datetime = next((g.get('game_datetime', '') for g in scheduled_games if g['away'] == p['away'] and g['home'] == p['home']), '')
            with pg1:
                st.markdown(f"**{p['away']} @ {p['home']}**")
                if game_datetime: st.caption(game_datetime)
            with pg2: st.markdown(f"<span style='color:{p['edge_color']}'>{p['edge_label']}</span>", unsafe_allow_html=True)
            with pg3:
                if p['pick'] != "WAIT": st.link_button(f"🎯 {p['pick']} ML", get_kalshi_game_link(p['away'], p['home']), use_container_width=True)
                else: st.caption("Wait for better edge")
            with pg4:
                if p['pick'] != "WAIT":
                    game_key = f"{p['away']}@{p['home']}"
                    if any(pos['game'] == game_key for pos in st.session_state.positions): st.caption("✅ Tracked")
                    elif st.button("➕", key=f"quick_{p['away']}_{p['home']}"):
                        st.session_state.positions.append({"game": game_key, "pick": p['pick'], "type": "ML", "line": "-", "price": 50, "contracts": 10, "link": get_kalshi_game_link(p['away'], p['home']), "id": str(uuid.uuid4())[:8]})
                        st.rerun()
    else: st.info("No scheduled games")

st.divider()

# INJURY REPORT
st.subheader("🏥 INJURY REPORT")
today_teams = set([g['away'] for g in games] + [g['home'] for g in games])
injury_found = False
for team in sorted(today_teams):
    for inj in injuries.get(team, []):
        if inj['name'] in STAR_PLAYERS.get(team, []):
            injury_found = True
            tier = STAR_TIERS.get(inj['name'], 1)
            st.markdown(f"**{team}**: {'⭐⭐⭐' if tier==3 else '⭐⭐' if tier==2 else '⭐'} {inj['name']} - {inj['status']}")
if not injury_found: st.info("No star player injuries reported")

st.divider()

# POSITION TRACKER
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
                    away_code = KALSHI_CODES.get(sel_game[1], "XXX")
                    home_code = KALSHI_CODES.get(sel_game[2], "XXX")
                    game_spread_key = f"{away_code}@{home_code}"
                    kalshi_spread_list = kalshi_spreads.get(game_spread_key, [])
                    if kalshi_spread_list:
                        spread_options = [f"{sp['line']} ({sp['team_code']}) @ {sp['yes_price']}¢" for sp in kalshi_spread_list]
                        line = st.selectbox("Kalshi Spreads", spread_options, key="add_spread_line")
                        line = line.split()[0] if line else "-7.5"
                        st.caption(f"✅ {len(kalshi_spread_list)} spreads from Kalshi")
                    else:
                        spread_options = ["-1.5", "-2.5", "-3.5", "-4.5", "-5.5", "-6.5", "-7.5", "-8.5", "-9.5", "-10.5", "-11.5", "-12.5", "+1.5", "+2.5", "+3.5", "+4.5", "+5.5", "+6.5", "+7.5", "+8.5", "+9.5", "+10.5", "+11.5", "+12.5"]
                        line = st.selectbox("Spread Line (Manual)", spread_options, index=5, key="add_spread_line")
                        st.caption("⚠️ No Kalshi spreads found - manual entry")
                else: line = "-7.5"
            elif "Totals" in bet_type: line = st.selectbox("Line", THRESHOLDS, key="add_line")
            else: line = "-"
        ac5, ac6, ac7 = st.columns(3)
        with ac5: entry_price = st.number_input("Entry Price (¢)", 1, 99, 50, key="add_price")
        with ac6: contracts = st.number_input("Contracts", 1, 10000, 10, key="add_contracts")
        with ac7: cost = entry_price * contracts / 100; st.metric("Cost", f"${cost:.2f}"); st.caption(f"Win: +${contracts - cost:.2f}")
        if st.button("✅ ADD POSITION", use_container_width=True, key="add_pos_btn"):
            if sel_game:
                if bet_type == "ML (Moneyline)": pos_type, pos_pick, pos_line = "ML", pick, "-"
                elif bet_type == "Spread": pos_type, pos_pick, pos_line = "Spread", pick, str(line)
                else: pos_type, pos_pick, pos_line = "Totals", pick.split()[0], str(line)
                st.session_state.positions.append({"game": f"{sel_game[1]}@{sel_game[2]}", "pick": pos_pick, "type": pos_type, "line": pos_line, "price": entry_price, "contracts": contracts, "link": get_kalshi_game_link(sel_game[1], sel_game[2]), "id": str(uuid.uuid4())[:8]})
                st.success("Added!"); st.rerun()

if st.session_state.positions:
    st.markdown("---")
    for idx, pos in enumerate(st.session_state.positions):
        current = next((g for g in games if f"{g['away']}@{g['home']}" == pos['game']), None)
        edit_key = f"editing_{pos['id']}"
        is_editing = st.session_state.get(edit_key, False)
        if is_editing:
            st.markdown(f"**✏️ Editing: {pos['game']}**")
            ec1, ec2 = st.columns(2)
            type_options = ["ML", "Totals", "Spread"]
            current_type_idx = 0 if pos['type']=="ML" else (2 if pos['type']=="Spread" else 1)
            with ec1: new_type = st.selectbox("Bet Type", type_options, index=current_type_idx, key=f"edit_type_{pos['id']}")
            with ec2:
                if new_type == "ML":
                    parts = pos['game'].split("@")
                    new_pick = st.selectbox("Pick", [parts[0], parts[1]], index=[parts[0], parts[1]].index(pos['pick']) if pos['pick'] in parts else 0, key=f"edit_pick_{pos['id']}")
                    new_line = "-"
                elif new_type == "Spread":
                    parts = pos['game'].split("@")
                    new_pick = st.selectbox("Pick", [parts[0], parts[1]], index=[parts[0], parts[1]].index(pos['pick']) if pos['pick'] in parts else 0, key=f"edit_pick_{pos['id']}")
                    away_code = KALSHI_CODES.get(parts[0], "XXX")
                    home_code = KALSHI_CODES.get(parts[1], "XXX")
                    game_spread_key = f"{away_code}@{home_code}"
                    kalshi_spread_list = kalshi_spreads.get(game_spread_key, [])
                    if kalshi_spread_list:
                        spread_options = [sp['line'] for sp in kalshi_spread_list]
                        current_spread_idx = spread_options.index(pos['line']) if pos.get('line') in spread_options else 0
                        new_line = st.selectbox("Kalshi Spread", spread_options, index=current_spread_idx, key=f"edit_line_{pos['id']}")
                    else:
                        spread_options = ["-1.5", "-2.5", "-3.5", "-4.5", "-5.5", "-6.5", "-7.5", "-8.5", "-9.5", "-10.5", "-11.5", "-12.5", "+1.5", "+2.5", "+3.5", "+4.5", "+5.5", "+6.5", "+7.5", "+8.5", "+9.5", "+10.5", "+11.5", "+12.5"]
                        current_spread_idx = spread_options.index(pos['line']) if pos.get('line') in spread_options else 5
                        new_line = st.selectbox("Spread (Manual)", spread_options, index=current_spread_idx, key=f"edit_line_{pos['id']}")
                else:
                    new_pick = st.selectbox("Pick", ["YES", "NO"], index=0 if pos.get('pick','YES')=="YES" else 1, key=f"edit_pick_{pos['id']}")
                    new_line = st.selectbox("Line", THRESHOLDS, index=THRESHOLDS.index(float(pos['line'])) if pos['line'] != "-" and float(pos['line']) in THRESHOLDS else 3, key=f"edit_line_{pos['id']}")
            ec3, ec4 = st.columns(2)
            with ec3: new_price = st.number_input("Entry Price (¢)", 1, 99, pos.get('price', 50), key=f"edit_price_{pos['id']}")
            with ec4: new_contracts = st.number_input("Contracts", 1, 10000, pos.get('contracts', 10), key=f"edit_contracts_{pos['id']}")
            ec5, ec6, ec7 = st.columns(3)
            with ec5:
                if st.button("💾 SAVE", key=f"save_{pos['id']}", use_container_width=True):
                    st.session_state.positions[idx]['type'] = new_type
                    st.session_state.positions[idx]['pick'] = new_pick
                    st.session_state.positions[idx]['line'] = str(new_line) if new_type == "Totals" else "-"
                    st.session_state.positions[idx]['price'] = new_price
                    st.session_state.positions[idx]['contracts'] = new_contracts
                    st.session_state[edit_key] = False
                    st.rerun()
            with ec6:
                if st.button("❌ CANCEL", key=f"cancel_{pos['id']}", use_container_width=True): st.session_state[edit_key] = False; st.rerun()
            with ec7: cost = new_price * new_contracts / 100; st.metric("Cost", f"${cost:.2f}")
            st.markdown("---")
        else:
            pc1, pc2, pc3, pc4, pc5, pc6 = st.columns([2.2, 1.3, 1.3, 1.2, 1, 1])
            with pc1:
                st.markdown(f"**{pos['game']}**")
                if current:
                    if current['period'] > 0: st.caption(f"🔴 LIVE Q{current['period']} {current['clock']} | {current['away_score']}-{current['home_score']}")
                    elif current['status'] in ['STATUS_FINAL', 'STATUS_FULL_TIME']: st.caption(f"✅ FINAL {current['away_score']}-{current['home_score']}")
                    else: st.caption("⏳ Scheduled")
            with pc2: st.write(f"🎯 {pos['pick']} ML" if pos['type']=="ML" else (f"📏 {pos['pick']} {pos['line']}" if pos['type']=="Spread" else f"📊 {pos['pick']} {pos['line']}"))
            with pc3: st.write(f"{pos.get('contracts',10)} @ {pos.get('price',50)}¢"); st.caption(f"${pos.get('price',50)*pos.get('contracts',10)/100:.2f}")
            with pc4: st.link_button("🔗 Kalshi", pos['link'], use_container_width=True)
            with pc5:
                if st.button("✏️", key=f"edit_{pos['id']}", help="Edit position"): st.session_state[edit_key] = True; st.rerun()
            with pc6:
                if st.button("🗑️", key=f"del_{pos['id']}"): remove_position(pos['id']); st.rerun()
    st.markdown("---")
    if st.button("🗑️ CLEAR ALL POSITIONS", use_container_width=True, type="primary"): st.session_state.positions = []; st.rerun()
else: st.caption("No positions tracked yet. Use ➕ ADD ALL buttons above or add manually.")

st.divider()

# ALL GAMES TODAY
st.subheader("📋 ALL GAMES TODAY")
for g in games:
    if g['status'] in ['STATUS_FINAL', 'STATUS_FULL_TIME']: status, color = f"FINAL: {g['away_score']}-{g['home_score']}", "#666"
    elif g['period'] > 0: status, color = f"LIVE Q{g['period']} {g['clock']} | {g['away_score']}-{g['home_score']}", "#22c55e"
    else: status, color = f"{g.get('game_datetime', 'TBD')} | Spread: {g.get('vegas_odds',{}).get('spread','N/A')}", "#888"
    st.markdown(f"<div style='background:#1e1e2e;padding:12px;border-radius:8px;margin-bottom:8px;border-left:3px solid {color}'><b style='color:#fff'>{g['away']} @ {g['home']}</b><br><span style='color:{color}'>{status}</span></div>", unsafe_allow_html=True)

st.divider()
st.caption(f"v{VERSION} • Educational only • Not financial advice")
st.caption("Stay small. Stay quiet. Win.")
