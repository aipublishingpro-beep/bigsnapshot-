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

VERSION = "7.5"
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
            no_bid = m.get("no_bid", 0) or 0
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
                    "ticker": ticker, "yes_bid": yes_bid, "yes_ask": yes_ask, "no_bid": no_bid,
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

def get_kalshi_ml_link(away, home):
    away_code = KALSHI_CODES.get(away, "XXX").upper()
    home_code = KALSHI_CODES.get(home, "XXX").upper()
    date_str = datetime.now(eastern).strftime('%y%b%d').upper()
    return "https://kalshi.com/markets/kxnbagame/kxnbagame-" + date_str.lower() + away_code.lower() + home_code.lower()

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
st.caption("v" + VERSION + " • " + now.strftime('%b %d, %Y %I:%M %p ET') + " • Vegas vs Kalshi Mispricing Detector")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Today's Games", len(games))
c2.metric("Live Now", len(live_games))
c3.metric("Scheduled", len(scheduled_games))
c4.metric("Final", len(final_games))

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
        
        st.subheader(away + " @ " + home)
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Vegas (ESPN):**")
            spread = vegas.get('spread')
            home_ml = vegas.get('homeML')
            away_ml = vegas.get('awayML')
            st.write("Spread: " + str(spread))
            st.write("Home ML: " + str(home_ml))
            st.write("Away ML: " + str(away_ml))
            if home_ml and away_ml:
                home_prob = american_to_implied_prob(home_ml) * 100
                away_prob = american_to_implied_prob(away_ml) * 100
                total = home_prob + away_prob
                st.success(home + ": " + str(round(home_prob/total*100)) + "% | " + away + ": " + str(round(away_prob/total*100)) + "%")
            elif spread:
                spread_val = float(spread)
                home_prob = 50 - (spread_val * 2.8)
                home_prob = max(10, min(90, home_prob))
                st.info(home + " (from spread): " + str(round(home_prob)) + "%")
        
        with col2:
            st.markdown("**Kalshi:**")
            if kalshi_data:
                yes_team = kalshi_data.get('yes_team_code', '?')
                st.write("Market: Will " + yes_team + " win?")
                st.write("YES ask: " + str(kalshi_data.get('yes_ask', 0)) + "¢")
                st.write("YES bid: " + str(kalshi_data.get('yes_bid', 0)) + "¢")
                st.write("NO bid: " + str(kalshi_data.get('no_bid', 0)) + "¢")
                home_imp = kalshi_data.get('home_implied', 0)
                away_imp = kalshi_data.get('away_implied', 0)
                st.success(home + ": " + str(round(home_imp)) + "% | " + away + ": " + str(round(away_imp)) + "%")
            else:
                st.error("No Kalshi data found")
        st.divider()

st.divider()

# ============================================================
# MISPRICING ALERT
# ============================================================
st.subheader("💰 MISPRICING ALERT")
st.caption("Vegas vs Kalshi • Buy when Kalshi underprices Vegas favorite")

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
            if yes_team.upper() == home_code.upper():
                action = "YES"
            else:
                action = "NO"
        else:
            team = away
            vegas_prob = vegas_away_prob
            kalshi_prob = kalshi_away_prob
            edge = away_edge
            yes_team = kalshi_data.get('yes_team_code', '')
            if yes_team.upper() == away_code.upper():
                action = "YES"
            else:
                action = "NO"
        
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
        status_text = "Q" + str(g['period']) + " " + g['clock'] if g['period'] > 0 else "Scheduled"
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("**" + g['away'] + " @ " + g['home'] + "** • " + status_text)
        with col2:
            st.markdown("<span style='color:" + edge_color + ";font-weight:bold'>" + edge_label + " +" + str(round(mp['edge'])) + "%</span>", unsafe_allow_html=True)
        
        st.markdown("""<div style="background:#0f172a;padding:16px;border-radius:10px;border:2px solid """ + edge_color + """;margin-bottom:12px">
<div style="font-size:1.4em;font-weight:bold;color:#fff;margin-bottom:8px">
🎯 BUY <span style="color:""" + action_color + """;background:""" + action_color + """22;padding:4px 12px;border-radius:6px">""" + mp['action'] + """</span> on Kalshi
</div>
<div style="color:#aaa;margin-bottom:12px">""" + mp['action'] + """ = """ + mp['team'] + """ wins</div>
<table style="width:100%;text-align:center;color:#fff">
<tr style="color:#888"><td>Vegas</td><td>Kalshi</td><td>EDGE</td></tr>
<tr style="font-size:1.3em;font-weight:bold">
<td>""" + str(round(mp['vegas_prob'])) + """%</td>
<td>""" + str(round(mp['kalshi_prob'])) + """¢</td>
<td style="color:""" + edge_color + """">+""" + str(round(mp['edge'])) + """%</td>
</tr>
</table>
<div style="color:#888;margin-top:10px;padding:8px;background:#1a2744;border-radius:6px">
💡 Vegas: """ + mp['team'] + """ """ + str(round(mp['vegas_prob'])) + """% → Kalshi: """ + str(round(mp['kalshi_prob'])) + """¢ = BUY """ + mp['action'] + """
</div>
</div>""", unsafe_allow_html=True)
        
        bc1, bc2, bc3 = st.columns(3)
        with bc1:
            st.link_button("🎯 BUY " + mp['action'] + " (" + mp['team'] + ")", get_kalshi_ml_link(g['away'], g['home']), use_container_width=True)
        with bc2:
            if st.button("➕ Track", key="mp_" + game_key):
                add_position(game_key, mp['action'] + " (" + mp['team'] + ")", "ML", "-", get_kalshi_ml_link(g['away'], g['home']))
                st.rerun()
else:
    st.info("🔍 No mispricings found (need 5%+ gap between Vegas & Kalshi)")

st.divider()

# ============================================================
# POSITION TRACKER
# ============================================================
st.subheader("📊 POSITION TRACKER")

if st.session_state.positions:
    for pos in st.session_state.positions:
        pc1, pc2, pc3, pc4 = st.columns([3, 2, 2, 1])
        with pc1:
            st.write("**" + pos['game'] + "**")
        with pc2:
            st.write(pos['pick'] + " " + pos['type'])
        with pc3:
            st.link_button("🔗 Buy", pos['link'], use_container_width=True)
        with pc4:
            if st.button("❌", key="del_" + pos['id']):
                remove_position(pos['id'])
                st.rerun()
    if st.button("🗑️ Clear All"):
        st.session_state.positions = []
        st.rerun()
else:
    st.caption("No positions tracked yet")

st.divider()

# ============================================================
# ALL GAMES
# ============================================================
st.subheader("📋 ALL GAMES TODAY")

for g in games:
    away = g['away']
    home = g['home']
    vegas = g.get('vegas_odds', {})
    spread = vegas.get('spread', 'N/A')
    
    if g['status'] in ['STATUS_FINAL', 'STATUS_FULL_TIME']:
        status = "FINAL: " + str(g['away_score']) + "-" + str(g['home_score'])
        color = "#666"
    elif g['period'] > 0:
        status = "LIVE Q" + str(g['period']) + " " + g['clock'] + " | " + str(g['away_score']) + "-" + str(g['home_score'])
        color = "#22c55e"
    else:
        status = "Scheduled | Spread: " + str(spread)
        color = "#888"
    
    st.markdown("<div style='background:#1e1e2e;padding:12px;border-radius:8px;margin-bottom:8px;border-left:3px solid " + color + "'><b style='color:#fff'>" + away + " @ " + home + "</b><br><span style='color:" + color + "'>" + status + "</span></div>", unsafe_allow_html=True)

st.divider()
st.caption("v" + VERSION + " • Educational only • Not financial advice")
st.caption("Stay small. Stay quiet. Win.")
