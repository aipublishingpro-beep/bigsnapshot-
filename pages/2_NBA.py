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
        url = "https://www.google-analytics.com/mp/collect?measurement_id=G-NQKY5VQ376&api_secret=n4oBJjH7RXi3dA7aQo2CZA"
        payload = {"client_id": str(uuid.uuid4()), "events": [{"name": "page_view", "params": {"page_title": page_title, "page_location": "https://bigsnapshot.streamlit.app" + page_path}}]}
        req_ga.post(url, json=payload, timeout=2)
    except: pass

send_ga4_event("BigSnapshot NBA Edge Finder", "/NBA")

import requests
from datetime import datetime, timedelta
import pytz

eastern = pytz.timezone("US/Eastern")
now = datetime.now(eastern)

VERSION = "7.8"
LEAGUE_AVG_TOTAL = 225
THRESHOLDS = [210.5, 215.5, 220.5, 225.5, 230.5, 235.5, 240.5, 245.5]

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
    "Oklahoma City": {"net": 12.0, "pace": 98.8}, "Cleveland": {"net": 10.5, "pace": 97.2},
    "Boston": {"net": 9.5, "pace": 99.8}, "Denver": {"net": 7.8, "pace": 98.5},
    "New York": {"net": 5.5, "pace": 97.5}, "Houston": {"net": 5.2, "pace": 99.5},
    "LA Lakers": {"net": 4.5, "pace": 98.5}, "Phoenix": {"net": 4.0, "pace": 98.2},
    "Minnesota": {"net": 4.0, "pace": 98.2}, "Golden State": {"net": 3.5, "pace": 100.2},
    "Dallas": {"net": 3.0, "pace": 99.0}, "Milwaukee": {"net": 2.5, "pace": 98.8},
    "Miami": {"net": 2.0, "pace": 97.2}, "Philadelphia": {"net": 1.5, "pace": 97.5},
    "Sacramento": {"net": 1.0, "pace": 100.5}, "Orlando": {"net": 0.5, "pace": 96.8},
    "LA Clippers": {"net": 0.0, "pace": 97.8}, "Indiana": {"net": -0.5, "pace": 102.5},
    "Memphis": {"net": -1.0, "pace": 99.8}, "San Antonio": {"net": -1.5, "pace": 99.2},
    "Detroit": {"net": -2.0, "pace": 99.5}, "Atlanta": {"net": -2.5, "pace": 100.5},
    "Chicago": {"net": -3.0, "pace": 98.8}, "Toronto": {"net": -3.5, "pace": 97.8},
    "Brooklyn": {"net": -5.0, "pace": 98.2}, "Portland": {"net": -5.5, "pace": 98.8},
    "Charlotte": {"net": -6.5, "pace": 99.5}, "Utah": {"net": -7.0, "pace": 98.5},
    "New Orleans": {"net": -8.0, "pace": 99.0}, "Washington": {"net": -10.0, "pace": 100.8},
}

STAR_PLAYERS = {
    "Boston": ["Jayson Tatum", "Jaylen Brown"], "Cleveland": ["Donovan Mitchell", "Darius Garland"],
    "Oklahoma City": ["Shai Gilgeous-Alexander", "Chet Holmgren"], "New York": ["Jalen Brunson", "Karl-Anthony Towns"],
    "Milwaukee": ["Giannis Antetokounmpo", "Damian Lillard"], "Denver": ["Nikola Jokic", "Jamal Murray"],
    "Minnesota": ["Anthony Edwards", "Rudy Gobert"], "Dallas": ["Luka Doncic", "Kyrie Irving"],
    "Phoenix": ["Kevin Durant", "Devin Booker"], "LA Lakers": ["LeBron James", "Anthony Davis"],
    "Golden State": ["Stephen Curry"], "Miami": ["Bam Adebayo", "Tyler Herro"],
    "Philadelphia": ["Joel Embiid", "Tyrese Maxey"], "Memphis": ["Ja Morant"],
    "New Orleans": ["Zion Williamson"], "Sacramento": ["Domantas Sabonis", "De'Aaron Fox"],
    "Indiana": ["Tyrese Haliburton", "Pascal Siakam"], "Orlando": ["Paolo Banchero", "Franz Wagner"],
    "Houston": ["Jalen Green", "Alperen Sengun"], "Atlanta": ["Trae Young"],
    "Charlotte": ["LaMelo Ball"], "Detroit": ["Cade Cunningham"],
    "San Antonio": ["Victor Wembanyama"], "LA Clippers": ["James Harden", "Kawhi Leonard"],
}

STAR_TIERS = {
    "Nikola Jokic": 3, "Shai Gilgeous-Alexander": 3, "Giannis Antetokounmpo": 3, "Luka Doncic": 3,
    "Joel Embiid": 3, "Jayson Tatum": 3, "LeBron James": 3, "Stephen Curry": 3, "Kevin Durant": 3,
    "Anthony Edwards": 3, "Donovan Mitchell": 2, "Jaylen Brown": 2, "Damian Lillard": 2,
    "Anthony Davis": 2, "Kyrie Irving": 2, "Devin Booker": 2, "Ja Morant": 2, "Trae Young": 2,
    "Tyrese Haliburton": 2, "De'Aaron Fox": 2, "Jalen Brunson": 2, "Paolo Banchero": 2,
    "Victor Wembanyama": 2, "LaMelo Ball": 2, "Cade Cunningham": 2, "Tyrese Maxey": 2,
}

def american_to_implied_prob(odds):
    if odds is None:
        return None
    if odds > 0:
        return 100 / (odds + 100)
    else:
        return abs(odds) / (abs(odds) + 100)

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
            status = event.get("status", {}).get("type", {}).get("name", "STATUS_SCHEDULED")
            period = event.get("status", {}).get("period", 0)
            clock = event.get("status", {}).get("displayClock", "")
            game_id = event.get("id", "")
            minutes_played = 0
            if period > 0:
                if period <= 4:
                    completed_quarters = (period - 1) * 12
                    if clock and ":" in clock:
                        try:
                            parts = clock.split(":")
                            mins_left = int(parts[0])
                            minutes_played = completed_quarters + (12 - mins_left)
                        except:
                            minutes_played = completed_quarters
                else:
                    minutes_played = 48 + (period - 4) * 5
            odds_data = comp.get("odds", [])
            vegas_odds = {}
            if odds_data and len(odds_data) > 0:
                odds = odds_data[0]
                vegas_odds = {
                    "spread": odds.get("spread"),
                    "overUnder": odds.get("overUnder"),
                    "homeML": odds.get("homeTeamOdds", {}).get("moneyLine"),
                    "awayML": odds.get("awayTeamOdds", {}).get("moneyLine"),
                    "provider": odds.get("provider", {}).get("name", "Unknown")
                }
            games.append({
                "away": away_team, "home": home_team, "away_score": away_score, "home_score": home_score,
                "status": status, "period": period, "clock": clock, "minutes_played": minutes_played,
                "total_score": home_score + away_score, "game_id": game_id, "vegas_odds": vegas_odds
            })
        return games
    except Exception as e:
        st.error("ESPN fetch error: " + str(e))
        return []

@st.cache_data(ttl=60)
def fetch_kalshi_ml():
    url = "https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXNBAGAME&status=open&limit=200"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        markets = {}
        for m in data.get("markets", []):
            ticker = m.get("ticker", "")
            if "KXNBAGAME-" not in ticker:
                continue
            parts = ticker.replace("KXNBAGAME-", "")
            if "-" not in parts:
                continue
            main_part, yes_team_code = parts.rsplit("-", 1)
            if len(main_part) < 13:
                continue
            teams_part = main_part[7:]
            away_code = teams_part[:3]
            home_code = teams_part[3:6]
            game_key = away_code + "@" + home_code
            yes_bid = m.get("yes_bid", 0) or 0
            yes_ask = m.get("yes_ask", 0) or 0
            if yes_ask > 0:
                yes_price = yes_ask
            elif yes_bid > 0:
                yes_price = yes_bid
            else:
                yes_price = 50
            yes_team_code = yes_team_code.upper()
            if yes_team_code == home_code.upper():
                home_implied = yes_price
                away_implied = 100 - yes_price
            else:
                away_implied = yes_price
                home_implied = 100 - yes_price
            if game_key not in markets:
                markets[game_key] = {
                    "away_code": away_code, "home_code": home_code, "yes_team_code": yes_team_code,
                    "ticker": ticker, "yes_bid": yes_bid, "yes_ask": yes_ask,
                    "yes_price": yes_price, "away_implied": away_implied, "home_implied": home_implied
                }
        return markets
    except Exception as e:
        st.error("Kalshi ML fetch error: " + str(e))
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
            if not team_key:
                continue
            injuries[team_key] = []
            for player in team_data.get("injuries", []):
                name = player.get("athlete", {}).get("displayName", "")
                status = player.get("status", "")
                if name:
                    injuries[team_key].append({"name": name, "status": status})
        return injuries
    except:
        return {}

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
                team_name = TEAM_ABBREVS.get(full_name, full_name)
                teams_played.add(team_name)
        return teams_played
    except:
        return set()

@st.cache_data(ttl=30)
def fetch_plays(game_id):
    if not game_id:
        return [], ""
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary?event={game_id}"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        plays_data = data.get("plays", [])
        plays = []
        for p in plays_data[-15:]:
            text = p.get("text", "")
            period = p.get("period", {}).get("number", 0)
            clock = p.get("clock", {}).get("displayValue", "")
            score_value = p.get("scoreValue", 0)
            play_type = p.get("type", {}).get("text", "")
            team_id = p.get("team", {}).get("id", "")
            plays.append({
                "text": text, "period": period, "clock": clock,
                "score_value": score_value, "play_type": play_type, "team_id": team_id
            })
        situation = data.get("situation", {})
        poss_team_id = situation.get("possession", "")
        return plays[-10:], poss_team_id
    except:
        return [], ""

def render_nba_court(away, home, away_score, home_score, possession, period, clock):
    away_color = TEAM_COLORS.get(away, "#666")
    home_color = TEAM_COLORS.get(home, "#666")
    away_code = KALSHI_CODES.get(away, "AWY")
    home_code = KALSHI_CODES.get(home, "HME")
    poss_away = "visible" if possession == away else "hidden"
    poss_home = "visible" if possession == home else "hidden"
    period_text = f"Q{period}" if period <= 4 else f"OT{period-4}"
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
        <rect x="60" y="270" width="80" height="40" fill="{away_color}" rx="6"/>
        <text x="100" y="290" fill="#fff" font-size="14" font-weight="bold" text-anchor="middle">{away_code}</text>
        <text x="100" y="305" fill="#fff" font-size="12" text-anchor="middle">{away_score}</text>
        <circle cx="145" cy="290" r="8" fill="#ffd700" visibility="{poss_away}"/>
        <rect x="360" y="270" width="80" height="40" fill="{home_color}" rx="6"/>
        <text x="400" y="290" fill="#fff" font-size="14" font-weight="bold" text-anchor="middle">{home_code}</text>
        <text x="400" y="305" fill="#fff" font-size="12" text-anchor="middle">{home_score}</text>
        <circle cx="355" cy="290" r="8" fill="#ffd700" visibility="{poss_home}"/>
        <text x="250" y="295" fill="#fff" font-size="16" font-weight="bold" text-anchor="middle">{period_text} {clock}</text>
    </svg>
    '''
    return svg

def get_play_icon(play_type, score_value):
    play_lower = play_type.lower() if play_type else ""
    if score_value > 0 or "made" in play_lower or "dunk" in play_lower:
        return "🏀", "#22c55e"
    elif "miss" in play_lower or "block" in play_lower:
        return "❌", "#ef4444"
    elif "rebound" in play_lower:
        return "📥", "#3b82f6"
    elif "turnover" in play_lower or "steal" in play_lower:
        return "🔄", "#f97316"
    elif "foul" in play_lower:
        return "🚨", "#eab308"
    elif "timeout" in play_lower:
        return "⏸️", "#a855f7"
    else:
        return "•", "#888"

def get_kalshi_game_link(away, home):
    """Build correct Kalshi game URL - ALL markets (ML, Spread, Totals) are on same page"""
    away_code = KALSHI_CODES.get(away, "XXX").lower()
    home_code = KALSHI_CODES.get(home, "XXX").lower()
    date_str = datetime.now(eastern).strftime('%y%b%d').lower()  # 26jan26
    ticker = f"kxnbagame-{date_str}{away_code}{home_code}"
    return f"https://kalshi.com/markets/kxnbagame/professional-basketball-game/{ticker}"

def get_kalshi_ml_link(away, home):
    """ML link - same as game page"""
    return get_kalshi_game_link(away, home)

def get_kalshi_totals_link(away, home, line=None):
    """Totals link - same as game page (totals are on the same page)"""
    return get_kalshi_game_link(away, home)

def calc_projection(total_score, minutes_played):
    if minutes_played >= 8:
        pace = total_score / minutes_played
        weight = min(1.0, (minutes_played - 8) / 16)
        blended_pace = (pace * weight) + ((LEAGUE_AVG_TOTAL / 48) * (1 - weight))
        proj = round(blended_pace * 48)
        return max(185, min(265, proj))
    elif minutes_played >= 6:
        pace = total_score / minutes_played
        proj = round(((pace * 0.3) + ((LEAGUE_AVG_TOTAL / 48) * 0.7)) * 48)
        return max(185, min(265, proj))
    else:
        return LEAGUE_AVG_TOTAL

def get_pace_label(pace):
    if pace < 4.2:
        return "🐢 SLOW", "#22c55e"
    elif pace < 4.5:
        return "⚖️ AVG", "#eab308"
    elif pace < 5.0:
        return "🔥 FAST", "#f97316"
    else:
        return "💥 SHOOTOUT", "#ef4444"

def calc_pregame_edge(away, home, injuries, b2b_teams):
    away_stats = TEAM_STATS.get(away, {"net": 0, "pace": 98})
    home_stats = TEAM_STATS.get(home, {"net": 0, "pace": 98})
    net_diff = home_stats["net"] - away_stats["net"] + 3
    score = 50 + (net_diff * 2)
    away_inj = injuries.get(away, [])
    home_inj = injuries.get(home, [])
    for inj in away_inj:
        if inj["name"] in STAR_TIERS:
            tier = STAR_TIERS[inj["name"]]
            if tier == 3:
                score += 5
            elif tier == 2:
                score += 3
    for inj in home_inj:
        if inj["name"] in STAR_TIERS:
            tier = STAR_TIERS[inj["name"]]
            if tier == 3:
                score -= 5
            elif tier == 2:
                score -= 3
    if away in b2b_teams:
        score += 3
    if home in b2b_teams:
        score -= 3
    return max(0, min(100, round(score)))

def add_position(game_key, pick, bet_type, line, link):
    pos = {"game": game_key, "pick": pick, "type": bet_type, "line": line, "link": link, "id": str(uuid.uuid4())[:8]}
    st.session_state.positions.append(pos)

def remove_position(pos_id):
    st.session_state.positions = [p for p in st.session_state.positions if p['id'] != pos_id]

# ============================================================
# FETCH DATA
# ============================================================
games = fetch_espn_games()
kalshi_ml = fetch_kalshi_ml()
injuries = fetch_injuries()
b2b_teams = fetch_yesterday_teams()

live_games = [g for g in games if g['status'] in ['STATUS_IN_PROGRESS', 'STATUS_HALFTIME', 'STATUS_END_PERIOD'] or (g['period'] > 0 and g['status'] not in ['STATUS_FINAL', 'STATUS_FULL_TIME'])]
scheduled_games = [g for g in games if g['status'] == 'STATUS_SCHEDULED' and g['period'] == 0]
final_games = [g for g in games if g['status'] in ['STATUS_FINAL', 'STATUS_FULL_TIME']]

# ============================================================
# HEADER
# ============================================================
st.title("🏀 BIGSNAPSHOT NBA EDGE FINDER")
st.caption(f"v{VERSION} • {now.strftime('%b %d, %Y %I:%M %p ET')} • Vegas vs Kalshi Mispricing Detector")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Today's Games", len(games))
c2.metric("Live Now", len(live_games))
c3.metric("Scheduled", len(scheduled_games))
c4.metric("Final", len(final_games))

st.divider()

# ============================================================
# VEGAS vs KALSHI MISPRICING ALERT (NEW FEATURE)
# ============================================================
st.subheader("💰 VEGAS vs KALSHI MISPRICING ALERT")
st.caption("Buy when Kalshi underprices Vegas favorite • 5%+ gap = edge")

mispricings = []
for g in games:
    if g['status'] in ['STATUS_FINAL', 'STATUS_FULL_TIME']:
        continue
    away = g['away']
    home = g['home']
    vegas = g.get('vegas_odds', {})
    away_code = KALSHI_CODES.get(away, "XXX")
    home_code = KALSHI_CODES.get(home, "XXX")
    kalshi_key = away_code + "@" + home_code
    kalshi_data = kalshi_ml.get(kalshi_key, {})
    
    if not kalshi_data:
        continue
    
    vegas_home_prob = None
    vegas_away_prob = None
    home_ml = vegas.get('homeML')
    away_ml = vegas.get('awayML')
    spread = vegas.get('spread')
    
    if home_ml and away_ml:
        vegas_home_prob = american_to_implied_prob(home_ml) * 100
        vegas_away_prob = american_to_implied_prob(away_ml) * 100
        total = vegas_home_prob + vegas_away_prob
        vegas_home_prob = vegas_home_prob / total * 100
        vegas_away_prob = vegas_away_prob / total * 100
    elif spread:
        try:
            spread_val = float(spread)
            vegas_home_prob = 50 - (spread_val * 2.8)
            vegas_home_prob = max(10, min(90, vegas_home_prob))
            vegas_away_prob = 100 - vegas_home_prob
        except:
            continue
    else:
        continue
    
    kalshi_home_prob = kalshi_data.get('home_implied', 50)
    kalshi_away_prob = kalshi_data.get('away_implied', 50)
    home_edge = vegas_home_prob - kalshi_home_prob
    away_edge = vegas_away_prob - kalshi_away_prob
    
    if home_edge >= 5 or away_edge >= 5:
        if home_edge >= away_edge:
            team = home
            vegas_prob = vegas_home_prob
            kalshi_prob = kalshi_home_prob
            edge = home_edge
            yes_team = kalshi_data.get('yes_team_code', '')
            action = "YES" if yes_team.upper() == home_code.upper() else "NO"
        else:
            team = away
            vegas_prob = vegas_away_prob
            kalshi_prob = kalshi_away_prob
            edge = away_edge
            yes_team = kalshi_data.get('yes_team_code', '')
            action = "YES" if yes_team.upper() == away_code.upper() else "NO"
        
        mispricings.append({
            'game': g, 'team': team, 'vegas_prob': vegas_prob, 'kalshi_prob': kalshi_prob,
            'edge': edge, 'action': action, 'spread': spread
        })

mispricings.sort(key=lambda x: x['edge'], reverse=True)

if mispricings:
    for mp in mispricings:
        g = mp['game']
        game_key = g['away'] + "@" + g['home']
        
        if mp['edge'] >= 10:
            edge_color = "#ff6b6b"
            edge_label = "🔥 STRONG"
        elif mp['edge'] >= 7:
            edge_color = "#22c55e"
            edge_label = "🟢 GOOD"
        else:
            edge_color = "#eab308"
            edge_label = "🟡 EDGE"
        
        action_color = "#22c55e" if mp['action'] == "YES" else "#ef4444"
        status_text = f"Q{g['period']} {g['clock']}" if g['period'] > 0 else "Scheduled"
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**{g['away']} @ {g['home']}** • {status_text}")
        with col2:
            st.markdown(f"<span style='color:{edge_color};font-weight:bold'>{edge_label} +{round(mp['edge'])}%</span>", unsafe_allow_html=True)
        
        st.markdown(f"""<div style="background:#0f172a;padding:16px;border-radius:10px;border:2px solid {edge_color};margin-bottom:12px">
<div style="font-size:1.4em;font-weight:bold;color:#fff;margin-bottom:8px">
🎯 BUY <span style="color:{action_color};background:{action_color}22;padding:4px 12px;border-radius:6px">{mp['action']}</span> on Kalshi
</div>
<div style="color:#aaa;margin-bottom:12px">{mp['action']} = {mp['team']} wins</div>
<table style="width:100%;text-align:center;color:#fff">
<tr style="color:#888"><td>Vegas</td><td>Kalshi</td><td>EDGE</td></tr>
<tr style="font-size:1.3em;font-weight:bold">
<td>{round(mp['vegas_prob'])}%</td>
<td>{round(mp['kalshi_prob'])}¢</td>
<td style="color:{edge_color}">+{round(mp['edge'])}%</td>
</tr>
</table>
</div>""", unsafe_allow_html=True)
        
        bc1, bc2, bc3 = st.columns(3)
        with bc1:
            st.link_button(f"🎯 BUY {mp['action']} ({mp['team']})", get_kalshi_ml_link(g['away'], g['home']), use_container_width=True)
        with bc2:
            if st.button("➕ Track", key=f"mp_{game_key}"):
                add_position(game_key, f"{mp['action']} ({mp['team']})", "ML", "-", get_kalshi_ml_link(g['away'], g['home']))
                st.rerun()
else:
    st.info("🔍 No mispricings found (need 5%+ gap between Vegas & Kalshi)")

st.divider()

# ============================================================
# LIVE EDGE MONITOR WITH COURT + PLAY-BY-PLAY
# ============================================================
st.subheader("🎮 LIVE EDGE MONITOR")

if live_games:
    for g in live_games:
        away = g['away']
        home = g['home']
        total = g['total_score']
        mins = g['minutes_played']
        game_id = g['game_id']
        
        plays, poss_team_id = fetch_plays(game_id)
        possession = ""
        if poss_team_id:
            for team_name, code in KALSHI_CODES.items():
                if code.lower() in str(poss_team_id).lower() or team_name.lower() in str(poss_team_id).lower():
                    possession = team_name
                    break
        
        st.markdown(f"### {away} @ {home}")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown(render_nba_court(away, home, g['away_score'], g['home_score'], possession, g['period'], g['clock']), unsafe_allow_html=True)
        
        with col2:
            st.markdown("**📋 LAST 10 PLAYS**")
            if plays:
                for p in reversed(plays):
                    icon, color = get_play_icon(p['play_type'], p['score_value'])
                    st.markdown(f"<div style='padding:4px 8px;margin:2px 0;background:#1e1e2e;border-radius:4px;border-left:3px solid {color}'><span style='color:{color}'>{icon}</span> Q{p['period']} {p['clock']} • {p['text'][:60]}</div>", unsafe_allow_html=True)
            else:
                st.caption("Waiting for plays...")
        
        if mins >= 6:
            proj = calc_projection(total, mins)
            pace = total / mins if mins > 0 else 0
            pace_label, pace_color = get_pace_label(pace)
            lead = g['home_score'] - g['away_score']
            leader = home if lead > 0 else away
            
            st.markdown(f"""
<div style="background:#1e1e2e;padding:12px;border-radius:8px;margin-top:8px">
<b>Score:</b> {total} pts in {mins} min • <b>Pace:</b> <span style="color:{pace_color}">{pace_label}</span> ({pace:.1f}/min)<br>
<b>Projection:</b> {proj} pts • <b>Lead:</b> {leader} +{abs(lead)}
</div>
""", unsafe_allow_html=True)
            
            safe_no = next((t for t in sorted(THRESHOLDS, reverse=True) if t >= proj + 8), None)
            safe_yes = next((t for t in sorted(THRESHOLDS) if t <= proj - 6), None)
            
            tc1, tc2 = st.columns(2)
            totals_link = get_kalshi_totals_link(away, home)
            if safe_no:
                with tc1:
                    st.link_button(f"🔴 BUY NO {safe_no}", totals_link, use_container_width=True)
            if safe_yes:
                with tc2:
                    st.link_button(f"🟢 BUY YES {safe_yes}", totals_link, use_container_width=True)
        else:
            st.caption("⏳ Waiting for 6+ minutes of game time...")
        
        st.divider()
else:
    st.info("No live games right now")

# ============================================================
# CUSHION SCANNER
# ============================================================
st.subheader("🎯 CUSHION SCANNER (Totals)")
st.caption("Find safe totals bets with cushion from projection")

min_mins = st.selectbox("Minimum minutes played:", [6, 9, 12, 15, 18], index=1, key="cush_mins")
side_choice = st.selectbox("Side:", ["NO (Under)", "YES (Over)"], key="cush_side")

cushion_data = []
for g in live_games:
    if g['minutes_played'] < min_mins:
        continue
    total = g['total_score']
    mins = g['minutes_played']
    proj = calc_projection(total, mins)
    pace = total / mins if mins > 0 else 0
    pace_label, pace_color = get_pace_label(pace)
    
    for thresh in THRESHOLDS:
        if side_choice == "NO (Under)":
            cushion = thresh - proj
            if cushion >= 6:
                cushion_data.append({
                    "game": f"{g['away']} @ {g['home']}",
                    "status": f"Q{g['period']} {g['clock']}",
                    "total": total,
                    "proj": proj,
                    "line": thresh,
                    "cushion": cushion,
                    "pace": pace_label,
                    "pace_color": pace_color,
                    "link": get_kalshi_totals_link(g['away'], g['home']),
                    "away": g['away'],
                    "home": g['home']
                })
        else:
            cushion = proj - thresh
            if cushion >= 6:
                cushion_data.append({
                    "game": f"{g['away']} @ {g['home']}",
                    "status": f"Q{g['period']} {g['clock']}",
                    "total": total,
                    "proj": proj,
                    "line": thresh,
                    "cushion": cushion,
                    "pace": pace_label,
                    "pace_color": pace_color,
                    "link": get_kalshi_totals_link(g['away'], g['home'], thresh),
                    "away": g['away'],
                    "home": g['home']
                })

cushion_data.sort(key=lambda x: x['cushion'], reverse=True)

if cushion_data:
    for cd in cushion_data[:10]:
        cc1, cc2, cc3, cc4 = st.columns([3, 1, 1, 2])
        with cc1:
            st.markdown(f"**{cd['game']}** • {cd['status']}")
        with cc2:
            st.markdown(f"Proj: {cd['proj']} | Line: {cd['line']}")
        with cc3:
            st.markdown(f"<span style='color:#22c55e;font-weight:bold'>+{round(cd['cushion'])}</span>", unsafe_allow_html=True)
        with cc4:
            action = "NO" if side_choice == "NO (Under)" else "YES"
            st.link_button(f"BUY {action} {cd['line']}", cd['link'], use_container_width=True)
else:
    st.info("No cushion opportunities found with current filters")

st.divider()

# ============================================================
# PACE SCANNER
# ============================================================
st.subheader("📈 PACE SCANNER")
st.caption("Track scoring pace across all live games")

pace_data = []
for g in live_games:
    if g['minutes_played'] >= 6:
        total = g['total_score']
        mins = g['minutes_played']
        pace = total / mins if mins > 0 else 0
        proj = calc_projection(total, mins)
        pace_label, pace_color = get_pace_label(pace)
        pace_data.append({
            "game": f"{g['away']} @ {g['home']}",
            "status": f"Q{g['period']} {g['clock']}",
            "total": total,
            "mins": mins,
            "pace": pace,
            "pace_label": pace_label,
            "pace_color": pace_color,
            "proj": proj,
            "away": g['away'],
            "home": g['home']
        })

pace_data.sort(key=lambda x: x['pace'])

if pace_data:
    for pd in pace_data:
        pc1, pc2, pc3, pc4 = st.columns([3, 2, 2, 2])
        with pc1:
            st.markdown(f"**{pd['game']}**")
        with pc2:
            st.markdown(f"{pd['status']} • {pd['total']} pts")
        with pc3:
            st.markdown(f"<span style='color:{pd['pace_color']};font-weight:bold'>{pd['pace_label']}</span>", unsafe_allow_html=True)
        with pc4:
            st.markdown(f"Proj: {pd['proj']}")
else:
    st.info("No live games with 6+ minutes played")

st.divider()

# ============================================================
# PRE-GAME ALIGNMENT
# ============================================================
with st.expander("🎯 PRE-GAME ALIGNMENT (Speculative)", expanded=True):
    st.caption("Model prediction for scheduled games • Not financial advice")
    
    if scheduled_games:
        for g in scheduled_games:
            away = g['away']
            home = g['home']
            edge_score = calc_pregame_edge(away, home, injuries, b2b_teams)
            
            if edge_score >= 70:
                pick = home
                edge_label = "🟢 STRONG"
                edge_color = "#22c55e"
            elif edge_score >= 60:
                pick = home
                edge_label = "🟢 GOOD"
                edge_color = "#22c55e"
            elif edge_score <= 30:
                pick = away
                edge_label = "🟢 STRONG"
                edge_color = "#22c55e"
            elif edge_score <= 40:
                pick = away
                edge_label = "🟢 GOOD"
                edge_color = "#22c55e"
            else:
                pick = "WAIT"
                edge_label = "🟡 NEUTRAL"
                edge_color = "#eab308"
            
            pg1, pg2, pg3 = st.columns([3, 1, 2])
            with pg1:
                st.markdown(f"**{away} @ {home}**")
            with pg2:
                st.markdown(f"<span style='color:{edge_color}'>{edge_label}</span>", unsafe_allow_html=True)
            with pg3:
                if pick != "WAIT":
                    st.link_button(f"🎯 {pick} ML", get_kalshi_ml_link(away, home), use_container_width=True)
                else:
                    st.caption("Wait for better edge")
    else:
        st.info("No scheduled games")

st.divider()

# ============================================================
# INJURY REPORT
# ============================================================
st.subheader("🏥 INJURY REPORT")
st.caption("Star player injuries affecting today's games")

today_teams = set()
for g in games:
    today_teams.add(g['away'])
    today_teams.add(g['home'])

injury_found = False
for team in sorted(today_teams):
    team_injuries = injuries.get(team, [])
    star_injuries = [inj for inj in team_injuries if inj['name'] in STAR_PLAYERS.get(team, [])]
    if star_injuries:
        injury_found = True
        for inj in star_injuries:
            tier = STAR_TIERS.get(inj['name'], 1)
            tier_emoji = "⭐⭐⭐" if tier == 3 else ("⭐⭐" if tier == 2 else "⭐")
            st.markdown(f"**{team}**: {tier_emoji} {inj['name']} - {inj['status']}")

if not injury_found:
    st.info("No star player injuries reported for today's games")

st.divider()

# ============================================================
# POSITION TRACKER
# ============================================================
st.subheader("📊 POSITION TRACKER")

if st.session_state.positions:
    for pos in st.session_state.positions:
        pc1, pc2, pc3, pc4 = st.columns([3, 2, 2, 1])
        with pc1:
            st.write(f"**{pos['game']}**")
        with pc2:
            st.write(f"{pos['pick']} {pos['type']}")
        with pc3:
            st.link_button("🔗 Buy", pos['link'], use_container_width=True)
        with pc4:
            if st.button("❌", key=f"del_{pos['id']}"):
                remove_position(pos['id'])
                st.rerun()
    if st.button("🗑️ Clear All"):
        st.session_state.positions = []
        st.rerun()
else:
    st.caption("No positions tracked yet")

st.divider()

# ============================================================
# ALL GAMES TODAY
# ============================================================
st.subheader("📋 ALL GAMES TODAY")

for g in games:
    away = g['away']
    home = g['home']
    vegas = g.get('vegas_odds', {})
    spread = vegas.get('spread', 'N/A')
    
    if g['status'] in ['STATUS_FINAL', 'STATUS_FULL_TIME']:
        status = f"FINAL: {g['away_score']}-{g['home_score']}"
        color = "#666"
    elif g['period'] > 0:
        status = f"LIVE Q{g['period']} {g['clock']} | {g['away_score']}-{g['home_score']}"
        color = "#22c55e"
    else:
        status = f"Scheduled | Spread: {spread}"
        color = "#888"
    
    st.markdown(f"<div style='background:#1e1e2e;padding:12px;border-radius:8px;margin-bottom:8px;border-left:3px solid {color}'><b style='color:#fff'>{away} @ {home}</b><br><span style='color:{color}'>{status}</span></div>", unsafe_allow_html=True)

st.divider()

# ============================================================
# DEBUG SECTION
# ============================================================
with st.expander("🔍 DEBUG: Verify Raw API Data", expanded=False):
    st.warning("Cross-check these numbers against Kalshi website!")
    for g in games:
        if g['status'] in ['STATUS_FINAL', 'STATUS_FULL_TIME']:
            continue
        away = g['away']
        home = g['home']
        away_code = KALSHI_CODES.get(away, "XXX")
        home_code = KALSHI_CODES.get(home, "XXX")
        kalshi_key = away_code + "@" + home_code
        kalshi_data = kalshi_ml.get(kalshi_key, {})
        vegas = g.get('vegas_odds', {})
        
        st.subheader(f"{away} @ {home}")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Vegas (ESPN):**")
            spread = vegas.get('spread')
            home_ml = vegas.get('homeML')
            away_ml = vegas.get('awayML')
            st.write(f"Spread: {spread}")
            st.write(f"Home ML: {home_ml}")
            st.write(f"Away ML: {away_ml}")
            if home_ml and away_ml:
                home_prob = american_to_implied_prob(home_ml) * 100
                away_prob = american_to_implied_prob(away_ml) * 100
                total = home_prob + away_prob
                st.success(f"{home}: {round(home_prob/total*100)}% | {away}: {round(away_prob/total*100)}%")
            elif spread:
                spread_val = float(spread)
                home_prob = 50 - (spread_val * 2.8)
                home_prob = max(10, min(90, home_prob))
                st.info(f"{home} (from spread): {round(home_prob)}%")
        
        with col2:
            st.markdown("**Kalshi:**")
            if kalshi_data:
                yes_team = kalshi_data.get('yes_team_code', '?')
                st.write(f"Market: Will {yes_team} win?")
                st.write(f"YES ask: {kalshi_data.get('yes_ask', 0)}¢")
                st.write(f"YES bid: {kalshi_data.get('yes_bid', 0)}¢")
                home_imp = kalshi_data.get('home_implied', 0)
                away_imp = kalshi_data.get('away_implied', 0)
                st.success(f"{home}: {round(home_imp)}% | {away}: {round(away_imp)}%")
            else:
                st.error("No Kalshi data found")
        st.divider()

st.caption(f"v{VERSION} • Educational only • Not financial advice")
st.caption("Stay small. Stay quiet. Win.")
