import streamlit as st
from streamlit_autorefresh import st_autorefresh
import streamlit.components.v1 as components

st.set_page_config(page_title="BigSnapshot NBA Edge Finder", page_icon="🏀", layout="wide")

from auth import require_auth
require_auth()

st_autorefresh(interval=24000, key="datarefresh")

import uuid
import time as _time
import requests
import requests as req_ga
from datetime import datetime, timedelta
import pytz

def send_ga4_event(page_title, page_path):
    try:
        url = "https://www.google-analytics.com/mp/collect?measurement_id=G-NQKY5VQ376&api_secret=n4oBJjH7RXi0dA7aQo2CZA"
        payload = {"client_id": str(uuid.uuid4()), "events": [{"name": "page_view", "params": {"page_title": page_title, "page_location": "https://bigsnapshot.streamlit.app" + page_path}}]}
        req_ga.post(url, json=payload, timeout=2)
    except: pass

send_ga4_event("BigSnapshot NBA Edge Finder", "/NBA")

eastern = pytz.timezone("US/Eastern")
now = datetime.now(eastern)

VERSION = "12.0"
LEAGUE_AVG_TOTAL = 225
THRESHOLDS = [210.5, 215.5, 220.5, 225.5, 230.5, 235.5, 240.5, 245.5]

if 'positions' not in st.session_state:
    st.session_state.positions = []

TEAM_ABBREVS = {
    "Atlanta Hawks": "Atlanta", "Boston Celtics": "Boston",
    "Brooklyn Nets": "Brooklyn", "Charlotte Hornets": "Charlotte",
    "Chicago Bulls": "Chicago", "Cleveland Cavaliers": "Cleveland",
    "Dallas Mavericks": "Dallas", "Denver Nuggets": "Denver",
    "Detroit Pistons": "Detroit", "Golden State Warriors": "Golden State",
    "Houston Rockets": "Houston", "Indiana Pacers": "Indiana",
    "LA Clippers": "LA Clippers", "Los Angeles Clippers": "LA Clippers",
    "LA Lakers": "LA Lakers", "Los Angeles Lakers": "LA Lakers",
    "Memphis Grizzlies": "Memphis", "Miami Heat": "Miami",
    "Milwaukee Bucks": "Milwaukee", "Minnesota Timberwolves": "Minnesota",
    "New Orleans Pelicans": "New Orleans", "New York Knicks": "New York",
    "Oklahoma City Thunder": "Oklahoma City", "Orlando Magic": "Orlando",
    "Philadelphia 76ers": "Philadelphia", "Phoenix Suns": "Phoenix",
    "Portland Trail Blazers": "Portland", "Sacramento Kings": "Sacramento",
    "San Antonio Spurs": "San Antonio", "Toronto Raptors": "Toronto",
    "Utah Jazz": "Utah", "Washington Wizards": "Washington",
    "MIL": "Milwaukee", "PHI": "Philadelphia", "BOS": "Boston",
    "NYK": "New York", "CLE": "Cleveland", "ORL": "Orlando",
    "ATL": "Atlanta", "MIA": "Miami", "CHI": "Chicago",
    "BKN": "Brooklyn", "TOR": "Toronto", "IND": "Indiana",
    "DET": "Detroit", "CHA": "Charlotte", "WAS": "Washington",
    "OKC": "Oklahoma City", "HOU": "Houston", "MEM": "Memphis",
    "DAL": "Dallas", "DEN": "Denver", "MIN": "Minnesota",
    "LAC": "LA Clippers", "LAL": "LA Lakers", "SAC": "Sacramento",
    "PHX": "Phoenix", "GSW": "Golden State", "POR": "Portland",
    "UTA": "Utah", "SAS": "San Antonio", "NOP": "New Orleans"
}

KALSHI_CODES = {
    "Atlanta": "ATL", "Boston": "BOS", "Brooklyn": "BKN",
    "Charlotte": "CHA", "Chicago": "CHI", "Cleveland": "CLE",
    "Dallas": "DAL", "Denver": "DEN", "Detroit": "DET",
    "Golden State": "GSW", "Houston": "HOU", "Indiana": "IND",
    "LA Clippers": "LAC", "LA Lakers": "LAL", "Memphis": "MEM",
    "Miami": "MIA", "Milwaukee": "MIL", "Minnesota": "MIN",
    "New Orleans": "NOP", "New York": "NYK", "Oklahoma City": "OKC",
    "Orlando": "ORL", "Philadelphia": "PHI", "Phoenix": "PHX",
    "Portland": "POR", "Sacramento": "SAC", "San Antonio": "SAS",
    "Toronto": "TOR", "Utah": "UTA", "Washington": "WAS"
}

TEAM_COLORS = {
    "Atlanta": "#E03A3E", "Boston": "#007A33", "Brooklyn": "#000000",
    "Charlotte": "#1D1160", "Chicago": "#CE1141", "Cleveland": "#860038",
    "Dallas": "#00538C", "Denver": "#0E2240", "Detroit": "#C8102E",
    "Golden State": "#1D428A", "Houston": "#CE1141", "Indiana": "#002D62",
    "LA Clippers": "#C8102E", "LA Lakers": "#552583", "Memphis": "#5D76A9",
    "Miami": "#98002E", "Milwaukee": "#00471B", "Minnesota": "#0C2340",
    "New Orleans": "#0C2340", "New York": "#006BB6",
    "Oklahoma City": "#007AC1", "Orlando": "#0077C0",
    "Philadelphia": "#006BB6", "Phoenix": "#1D1160",
    "Portland": "#E03A3E", "Sacramento": "#5A2D81",
    "San Antonio": "#C4CED4", "Toronto": "#CE1141",
    "Utah": "#002B5C", "Washington": "#002B5C"
}

TEAM_STATS = {
    "Oklahoma City": {"net": 12.0, "pace": 98.8},
    "Cleveland": {"net": 10.5, "pace": 97.2},
    "Boston": {"net": 9.5, "pace": 99.8},
    "Denver": {"net": 7.8, "pace": 98.5},
    "New York": {"net": 5.5, "pace": 97.5},
    "Houston": {"net": 5.2, "pace": 99.5},
    "LA Lakers": {"net": 4.5, "pace": 98.5},
    "Phoenix": {"net": 4.0, "pace": 98.2},
    "Minnesota": {"net": 4.0, "pace": 98.2},
    "Golden State": {"net": 3.5, "pace": 100.2},
    "Dallas": {"net": 3.0, "pace": 99.0},
    "Milwaukee": {"net": 2.5, "pace": 98.8},
    "Miami": {"net": 2.0, "pace": 97.2},
    "Philadelphia": {"net": 1.5, "pace": 97.5},
    "Sacramento": {"net": 1.0, "pace": 100.5},
    "Orlando": {"net": 0.5, "pace": 96.8},
    "LA Clippers": {"net": 0.0, "pace": 97.8},
    "Indiana": {"net": -0.5, "pace": 102.5},
    "Memphis": {"net": -1.0, "pace": 99.8},
    "San Antonio": {"net": -1.5, "pace": 99.2},
    "Detroit": {"net": -2.0, "pace": 99.5},
    "Atlanta": {"net": -2.5, "pace": 100.5},
    "Chicago": {"net": -3.0, "pace": 98.8},
    "Toronto": {"net": -3.5, "pace": 97.8},
    "Brooklyn": {"net": -5.0, "pace": 98.2},
    "Portland": {"net": -5.5, "pace": 98.8},
    "Charlotte": {"net": -6.5, "pace": 99.5},
    "Utah": {"net": -7.0, "pace": 98.5},
    "New Orleans": {"net": -8.0, "pace": 99.0},
    "Washington": {"net": -10.0, "pace": 100.8}
}
STAR_PLAYERS = {
    "Boston": ["Jayson Tatum", "Jaylen Brown"],
    "Cleveland": ["Donovan Mitchell", "Darius Garland"],
    "Oklahoma City": ["Shai Gilgeous-Alexander", "Chet Holmgren"],
    "New York": ["Jalen Brunson", "Karl-Anthony Towns"],
    "Milwaukee": ["Giannis Antetokounmpo", "Damian Lillard"],
    "Denver": ["Nikola Jokic", "Jamal Murray"],
    "Minnesota": ["Anthony Edwards", "Rudy Gobert"],
    "Dallas": ["Luka Doncic", "Kyrie Irving"],
    "Phoenix": ["Kevin Durant", "Devin Booker"],
    "LA Lakers": ["LeBron James", "Anthony Davis"],
    "Golden State": ["Stephen Curry"],
    "Miami": ["Bam Adebayo", "Tyler Herro"],
    "Philadelphia": ["Joel Embiid", "Tyrese Maxey"],
    "Memphis": ["Ja Morant"],
    "New Orleans": ["Zion Williamson"],
    "Sacramento": ["Domantas Sabonis", "De'Aaron Fox"],
    "Indiana": ["Tyrese Haliburton", "Pascal Siakam"],
    "Orlando": ["Paolo Banchero", "Franz Wagner"],
    "Houston": ["Jalen Green", "Alperen Sengun"],
    "Atlanta": ["Trae Young"], "Charlotte": ["LaMelo Ball"],
    "Detroit": ["Cade Cunningham"],
    "San Antonio": ["Victor Wembanyama"],
    "LA Clippers": ["James Harden", "Kawhi Leonard"]
}

STAR_TIERS = {
    "Nikola Jokic": 3, "Shai Gilgeous-Alexander": 3,
    "Giannis Antetokounmpo": 3, "Luka Doncic": 3,
    "Joel Embiid": 3, "Jayson Tatum": 3, "LeBron James": 3,
    "Stephen Curry": 3, "Kevin Durant": 3, "Anthony Edwards": 3,
    "Donovan Mitchell": 2, "Jaylen Brown": 2, "Damian Lillard": 2,
    "Anthony Davis": 2, "Kyrie Irving": 2, "Devin Booker": 2,
    "Ja Morant": 2, "Trae Young": 2, "Tyrese Haliburton": 2,
    "De'Aaron Fox": 2, "Jalen Brunson": 2, "Paolo Banchero": 2,
    "Victor Wembanyama": 2, "LaMelo Ball": 2,
    "Cade Cunningham": 2, "Tyrese Maxey": 2
}

PLAYER_TEAMS = {
    "Jalen Brunson": "New York", "Karl-Anthony Towns": "New York",
    "OG Anunoby": "New York", "Mikal Bridges": "New York",
    "Josh Hart": "New York", "Miles McBride": "New York",
    "Donte DiVincenzo": "New York", "Mitchell Robinson": "New York",
    "Precious Achiuwa": "New York", "Landry Shamet": "New York",
    "Domantas Sabonis": "Sacramento", "De'Aaron Fox": "Sacramento",
    "Keegan Murray": "Sacramento", "Malik Monk": "Sacramento",
    "DeMar DeRozan": "Sacramento", "Kevin Huerter": "Sacramento",
    "Trey Lyles": "Sacramento", "Keon Ellis": "Sacramento",
    "Russell Westbrook": "Sacramento", "Dylan Cardwell": "Sacramento",
    "Jayson Tatum": "Boston", "Jaylen Brown": "Boston",
    "Derrick White": "Boston", "Jrue Holiday": "Boston",
    "Kristaps Porzingis": "Boston", "Al Horford": "Boston",
    "Payton Pritchard": "Boston", "Sam Hauser": "Boston",
    "Donovan Mitchell": "Cleveland", "Darius Garland": "Cleveland",
    "Evan Mobley": "Cleveland", "Jarrett Allen": "Cleveland",
    "Max Strus": "Cleveland", "Caris LeVert": "Cleveland",
    "Shai Gilgeous-Alexander": "Oklahoma City",
    "Chet Holmgren": "Oklahoma City",
    "Jalen Williams": "Oklahoma City", "Lu Dort": "Oklahoma City",
    "Isaiah Hartenstein": "Oklahoma City",
    "Alex Caruso": "Oklahoma City",
    "Giannis Antetokounmpo": "Milwaukee",
    "Damian Lillard": "Milwaukee", "Khris Middleton": "Milwaukee",
    "Brook Lopez": "Milwaukee", "Bobby Portis": "Milwaukee",
    "Pat Connaughton": "Milwaukee",
    "Nikola Jokic": "Denver", "Jamal Murray": "Denver",
    "Michael Porter Jr.": "Denver", "Aaron Gordon": "Denver",
    "Christian Braun": "Denver",
    "Luka Doncic": "Dallas", "Kyrie Irving": "Dallas",
    "PJ Washington": "Dallas", "Daniel Gafford": "Dallas",
    "Dereck Lively II": "Dallas", "Klay Thompson": "Dallas",
    "Anthony Edwards": "Minnesota", "Rudy Gobert": "Minnesota",
    "Julius Randle": "Minnesota", "Jaden McDaniels": "Minnesota",
    "Mike Conley": "Minnesota", "Naz Reid": "Minnesota",
    "Kevin Durant": "Phoenix", "Devin Booker": "Phoenix",
    "Bradley Beal": "Phoenix", "Jusuf Nurkic": "Phoenix",
    "Grayson Allen": "Phoenix",
    "LeBron James": "LA Lakers", "Anthony Davis": "LA Lakers",
    "Austin Reaves": "LA Lakers", "D'Angelo Russell": "LA Lakers",
    "Rui Hachimura": "LA Lakers",
    "Stephen Curry": "Golden State", "Draymond Green": "Golden State",
    "Andrew Wiggins": "Golden State",
    "Jonathan Kuminga": "Golden State",
    "Brandin Podziemski": "Golden State",
    "Bam Adebayo": "Miami", "Tyler Herro": "Miami",
    "Jimmy Butler": "Miami", "Terry Rozier": "Miami",
    "Jaime Jaquez Jr.": "Miami",
    "Joel Embiid": "Philadelphia", "Tyrese Maxey": "Philadelphia",
    "Paul George": "Philadelphia", "Caleb Martin": "Philadelphia",
    "Kelly Oubre Jr.": "Philadelphia",
    "Ja Morant": "Memphis", "Jaren Jackson Jr.": "Memphis",
    "Desmond Bane": "Memphis", "Marcus Smart": "Memphis",
    "Zion Williamson": "New Orleans",
    "Brandon Ingram": "New Orleans", "CJ McCollum": "New Orleans",
    "Trey Murphy III": "New Orleans",
    "Trae Young": "Atlanta", "Jalen Johnson": "Atlanta",
    "De'Andre Hunter": "Atlanta", "Clint Capela": "Atlanta",
    "LaMelo Ball": "Charlotte", "Miles Bridges": "Charlotte",
    "Brandon Miller": "Charlotte", "Mark Williams": "Charlotte",
    "Cade Cunningham": "Detroit", "Jaden Ivey": "Detroit",
    "Ausar Thompson": "Detroit", "Jalen Duren": "Detroit",
    "Victor Wembanyama": "San Antonio",
    "Devin Vassell": "San Antonio",
    "Jeremy Sochan": "San Antonio",
    "Keldon Johnson": "San Antonio",
    "James Harden": "LA Clippers", "Kawhi Leonard": "LA Clippers",
    "Norman Powell": "LA Clippers", "Ivica Zubac": "LA Clippers",
    "Tyrese Haliburton": "Indiana", "Pascal Siakam": "Indiana",
    "Myles Turner": "Indiana", "Aaron Nesmith": "Indiana",
    "Benedict Mathurin": "Indiana",
    "Paolo Banchero": "Orlando", "Franz Wagner": "Orlando",
    "Jalen Suggs": "Orlando", "Wendell Carter Jr.": "Orlando",
    "Moritz Wagner": "Orlando",
    "Jalen Green": "Houston", "Alperen Sengun": "Houston",
    "Jabari Smith Jr.": "Houston", "Fred VanVleet": "Houston",
    "Dillon Brooks": "Houston",
    "Anfernee Simons": "Portland", "Scoot Henderson": "Portland",
    "Jerami Grant": "Portland", "Deandre Ayton": "Portland",
    "Lauri Markkanen": "Utah", "Collin Sexton": "Utah",
    "Jordan Clarkson": "Utah", "John Collins": "Utah",
    "Kyle Kuzma": "Washington", "Jordan Poole": "Washington",
    "Bilal Coulibaly": "Washington",
    "Cameron Johnson": "Brooklyn", "Mikal Bridges": "Brooklyn",
    "Cam Thomas": "Brooklyn", "Nic Claxton": "Brooklyn",
    "Scottie Barnes": "Toronto", "RJ Barrett": "Toronto",
    "Immanuel Quickley": "Toronto", "Jakob Poeltl": "Toronto"
}
def american_to_implied_prob(odds):
    if odds is None: return None
    if odds > 0: return 100 / (odds + 100)
    else: return abs(odds) / (abs(odds) + 100)

def speak_play(text):
    clean = text.replace("'", "").replace('"', '').replace('\n', ' ')[:100]
    js = '<script>'
    js += 'if(!window.lastSpoken||window.lastSpoken!=="' + clean + '"){'
    js += 'window.lastSpoken="' + clean + '";'
    js += 'var u=new SpeechSynthesisUtterance("' + clean + '");'
    js += 'u.rate=1.1;window.speechSynthesis.speak(u);}'
    js += '</script>'
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
                tn = TEAM_ABBREVS.get(full_name, full_name)
                sc = int(c.get("score", 0) or 0)
                recs = c.get("records", [])
                rec = recs[0].get("summary", "") if recs else ""
                if c.get("homeAway") == "home":
                    home_team, home_score, home_record = tn, sc, rec
                else:
                    away_team, away_score, away_record = tn, sc, rec
            status = event.get("status", {}).get("type", {}).get("name", "STATUS_SCHEDULED")
            period = event.get("status", {}).get("period", 0)
            clock = event.get("status", {}).get("displayClock", "")
            gid = event.get("id", "")
            mp = 0
            if period > 0:
                if period <= 4:
                    cq = (period - 1) * 12
                    if clock:
                        try:
                            if ":" in clock: mp = cq + (12 - int(clock.split(":")[0]))
                            else: mp = cq + 12
                        except: mp = cq + 12
                    else: mp = cq
                else: mp = 48 + (period - 4) * 5
            gd = event.get("date", "")
            gts, gdts = "", ""
            if gd:
                try:
                    gdt = datetime.fromisoformat(gd.replace("Z", "+00:00")).astimezone(eastern)
                    gts = gdt.strftime("%I:%M %p ET")
                    gdts = gdt.strftime("%b %d, %I:%M %p ET")
                except: pass
            odds_data = comp.get("odds", [])
            vegas = {}
            if odds_data and len(odds_data) > 0:
                od = odds_data[0]
                vegas = {"spread": od.get("spread"), "overUnder": od.get("overUnder"), "homeML": od.get("homeTeamOdds", {}).get("moneyLine"), "awayML": od.get("awayTeamOdds", {}).get("moneyLine")}
            games.append({"away": away_team, "home": home_team, "away_score": away_score, "home_score": home_score, "away_record": away_record, "home_record": home_record, "status": status, "period": period, "clock": clock, "minutes_played": mp, "total_score": home_score + away_score, "game_id": gid, "vegas_odds": vegas, "game_time": gts, "game_datetime": gdts})
        return games
    except Exception as e:
        st.error("ESPN fetch error: " + str(e))
        return []

# v12.0 FIX: Session state + 15s freshness + no default 50
def fetch_kalshi_ml(force_refresh=False):
    ck = "nba_kalshi_data"
    tk = "nba_kalshi_time"
    ts = _time.time()
    if not force_refresh and ck in st.session_state and tk in st.session_state:
        if ts - st.session_state[tk] < 15:
            return st.session_state[ck]
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
            main_part, ytc = parts.rsplit("-", 1)
            if len(main_part) < 13: continue
            tp = main_part[7:]
            ac, hc = tp[:3], tp[3:6]
            gk = ac + "@" + hc
            yb = m.get("yes_bid", 0) or 0
            ya = m.get("yes_ask", 0) or 0
            lp = m.get("last_price", 0) or 0
            # v12.0: ask > last_price > bid, skip if all zero
            if ya > 0: yp = ya
            elif lp > 0: yp = lp
            elif yb > 0: yp = yb
            else: continue
            ytc = ytc.upper()
            if ytc == hc.upper():
                hi, ai = yp, 100 - yp
            else:
                ai, hi = yp, 100 - yp
            if gk not in markets:
                markets[gk] = {"away_code": ac, "home_code": hc, "yes_team_code": ytc, "ticker": ticker, "yes_bid": yb, "yes_ask": ya, "last_price": lp, "yes_price": yp, "away_implied": ai, "home_implied": hi}
        st.session_state[ck] = markets
        st.session_state[tk] = ts
        return markets
    except Exception as e:
        st.error("Kalshi ML fetch error: " + str(e))
        if ck in st.session_state: return st.session_state[ck]
        return {}

# v12.0 FIX: Same session state fix for spreads
def fetch_kalshi_spreads(force_refresh=False):
    ck = "nba_kalshi_spread_data"
    tk = "nba_kalshi_spread_time"
    ts = _time.time()
    if not force_refresh and ck in st.session_state and tk in st.session_state:
        if ts - st.session_state[tk] < 15:
            return st.session_state[ck]
    url = "https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXNBASPREAD&status=open&limit=200"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        spreads = {}
        for m in data.get("markets", []):
            ticker = m.get("ticker", "")
            yb = m.get("yes_bid", 0) or 0
            ya = m.get("yes_ask", 0) or 0
            lp = m.get("last_price", 0) or 0
            if "KXNBASPREAD-" not in ticker: continue
            parts = ticker.replace("KXNBASPREAD-", "")
            if len(parts) < 13: continue
            rest = parts[7:]
            if "-" not in rest: continue
            gt, si = rest.split("-", 1)
            if len(gt) < 6: continue
            ac = gt[:3].upper()
            hc = gt[3:6].upper()
            gk = ac + "@" + hc
            sl, st2 = None, None
            if "-" in si:
                sp = si.rsplit("-", 1)
                if len(sp) == 2:
                    st2 = sp[0].upper()
                    try: sl = "-" + sp[1]
                    except: pass
            elif "+" in si:
                sp = si.split("+", 1)
                if len(sp) == 2:
                    st2 = sp[0].upper()
                    try: sl = "+" + sp[1]
                    except: pass
            if sl and st2:
                if ya > 0: sp_price = ya
                elif lp > 0: sp_price = lp
                elif yb > 0: sp_price = yb
                else: sp_price = 50
                if gk not in spreads: spreads[gk] = []
                spreads[gk].append({"line": sl, "team_code": st2, "ticker": ticker, "yes_bid": yb, "yes_ask": ya, "last_price": lp, "yes_price": sp_price})
        st.session_state[ck] = spreads
        st.session_state[tk] = ts
        return spreads
    except:
        if ck in st.session_state: return st.session_state[ck]
        return {}

@st.cache_data(ttl=300)
def fetch_injuries():
    url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/injuries"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        inj = {}
        for td in data.get("injuries", []):
            tn = td.get("displayName", "")
            tk = TEAM_ABBREVS.get(tn, tn)
            if not tk: continue
            inj[tk] = []
            for p in td.get("injuries", []):
                nm = p.get("athlete", {}).get("displayName", "")
                st2 = p.get("status", "")
                if nm: inj[tk].append({"name": nm, "status": st2})
        return inj
    except: return {}

@st.cache_data(ttl=300)
def fetch_yesterday_teams():
    yest = (datetime.now(eastern) - timedelta(days=1)).strftime('%Y%m%d')
    url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates=" + yest
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        tp = set()
        for event in data.get("events", []):
            comp = event.get("competitions", [{}])[0]
            for c in comp.get("competitors", []):
                fn = c.get("team", {}).get("displayName", "")
                tp.add(TEAM_ABBREVS.get(fn, fn))
        return tp
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
            plays.append({"text": p.get("text", ""), "period": p.get("period", {}).get("number", 0), "clock": p.get("clock", {}).get("displayValue", ""), "score_value": p.get("scoreValue", 0), "play_type": p.get("type", {}).get("text", "")})
        return plays[-10:]
    except: return []
        def get_team_from_play(play_text, away, home):
    if not play_text: return None
    ptl = play_text.lower()
    for player, team in PLAYER_TEAMS.items():
        if player.lower() in ptl:
            if team == away or team == home:
                return team
    return None

def infer_possession(plays, away, home):
    if not plays: return None, None
    lp = plays[-1]
    pt = (lp.get("text", "") or "").lower()
    at = get_team_from_play(lp.get("text", ""), away, home)
    if not at: return None, None
    ot = home if at == away else away
    if lp.get("score_value", 0) > 0 or "makes" in pt:
        return ot, "-> " + KALSHI_CODES.get(ot, ot[:3].upper())
    if "defensive rebound" in pt:
        return at, "🏀 " + KALSHI_CODES.get(at, at[:3].upper())
    if "offensive rebound" in pt:
        return at, "🏀 " + KALSHI_CODES.get(at, at[:3].upper())
    if "turnover" in pt or "steal" in pt:
        return ot, "-> " + KALSHI_CODES.get(ot, ot[:3].upper())
    if "misses" in pt:
        return None, "⏳ LOOSE"
    if "foul" in pt:
        return ot, "FT " + KALSHI_CODES.get(ot, ot[:3].upper())
    return at, "🏀 " + KALSHI_CODES.get(at, at[:3].upper())

def render_scoreboard(away, home, away_score, home_score, period, clock, away_record="", home_record=""):
    ac = KALSHI_CODES.get(away, away[:3].upper())
    hc = KALSHI_CODES.get(home, home[:3].upper())
    acol = TEAM_COLORS.get(away, "#666")
    hcol = TEAM_COLORS.get(home, "#666")
    pt = "Q" + str(period) if period <= 4 else "OT" + str(period - 4)
    h = '<div style="background:#0f172a;border-radius:12px;padding:20px;margin-bottom:8px">'
    h += '<div style="text-align:center;color:#ffd700;font-weight:bold;font-size:22px;margin-bottom:16px">'
    h += pt + " - " + str(clock) + '</div>'
    h += '<table style="width:100%;border-collapse:collapse;color:#fff">'
    h += '<tr style="border-bottom:2px solid #333">'
    h += '<td style="padding:16px;text-align:left;width:70%">'
    h += '<span style="color:' + acol + ';font-weight:bold;font-size:28px">' + ac + '</span>'
    h += '<span style="color:#666;font-size:14px;margin-left:12px">' + away_record + '</span></td>'
    h += '<td style="padding:16px;text-align:right;font-weight:bold;font-size:52px;color:#fff">'
    h += str(away_score) + '</td></tr>'
    h += '<tr><td style="padding:16px;text-align:left;width:70%">'
    h += '<span style="color:' + hcol + ';font-weight:bold;font-size:28px">' + hc + '</span>'
    h += '<span style="color:#666;font-size:14px;margin-left:12px">' + home_record + '</span></td>'
    h += '<td style="padding:16px;text-align:right;font-weight:bold;font-size:52px;color:#fff">'
    h += str(home_score) + '</td></tr></table></div>'
    return h

def get_play_badge(last_play):
    if not last_play: return ""
    pt = (last_play.get("text", "") or "").lower()
    sv = last_play.get("score_value", 0)
    if sv == 3 or ("three point" in pt and "makes" in pt):
        return '<rect x="175" y="25" width="150" height="30" fill="#22c55e" rx="6"/><text x="250" y="46" fill="#fff" font-size="14" font-weight="bold" text-anchor="middle">3PT MADE!</text>'
    elif sv == 2 or ("makes" in pt and any(w in pt for w in ["layup", "dunk", "shot", "jumper", "hook"])):
        return '<rect x="175" y="25" width="150" height="30" fill="#22c55e" rx="6"/><text x="250" y="46" fill="#fff" font-size="14" font-weight="bold" text-anchor="middle">BUCKET!</text>'
    elif sv == 1 or ("makes" in pt and "free throw" in pt):
        return '<rect x="175" y="25" width="150" height="30" fill="#22c55e" rx="6"/><text x="250" y="46" fill="#fff" font-size="14" font-weight="bold" text-anchor="middle">FT MADE</text>'
    elif "misses" in pt:
        if "three point" in pt:
            return '<rect x="175" y="25" width="150" height="30" fill="#ef4444" rx="6"/><text x="250" y="46" fill="#fff" font-size="14" font-weight="bold" text-anchor="middle">3PT MISS</text>'
        elif "free throw" in pt:
            return '<rect x="175" y="25" width="150" height="30" fill="#ef4444" rx="6"/><text x="250" y="46" fill="#fff" font-size="14" font-weight="bold" text-anchor="middle">FT MISS</text>'
        else:
            return '<rect x="175" y="25" width="150" height="30" fill="#ef4444" rx="6"/><text x="250" y="46" fill="#fff" font-size="14" font-weight="bold" text-anchor="middle">MISSED SHOT</text>'
    elif "block" in pt:
        return '<rect x="175" y="25" width="150" height="30" fill="#f97316" rx="6"/><text x="250" y="46" fill="#fff" font-size="14" font-weight="bold" text-anchor="middle">BLOCKED!</text>'
    elif "turnover" in pt or "steal" in pt:
        return '<rect x="175" y="25" width="150" height="30" fill="#f97316" rx="6"/><text x="250" y="46" fill="#fff" font-size="14" font-weight="bold" text-anchor="middle">TURNOVER</text>'
    elif "offensive rebound" in pt:
        return '<rect x="175" y="25" width="150" height="30" fill="#3b82f6" rx="6"/><text x="250" y="46" fill="#fff" font-size="14" font-weight="bold" text-anchor="middle">OFF REBOUND</text>'
    elif "defensive rebound" in pt:
        return '<rect x="175" y="25" width="150" height="30" fill="#3b82f6" rx="6"/><text x="250" y="46" fill="#fff" font-size="14" font-weight="bold" text-anchor="middle">DEF REBOUND</text>'
    elif "rebound" in pt:
        return '<rect x="175" y="25" width="150" height="30" fill="#3b82f6" rx="6"/><text x="250" y="46" fill="#fff" font-size="14" font-weight="bold" text-anchor="middle">REBOUND</text>'
    elif "foul" in pt:
        return '<rect x="175" y="25" width="150" height="30" fill="#eab308" rx="6"/><text x="250" y="46" fill="#000" font-size="14" font-weight="bold" text-anchor="middle">FOUL</text>'
    elif "timeout" in pt:
        return '<rect x="175" y="25" width="150" height="30" fill="#a855f7" rx="6"/><text x="250" y="46" fill="#fff" font-size="14" font-weight="bold" text-anchor="middle">TIMEOUT</text>'
    return ""

def render_nba_court(away, home, as2, hs, period, clock, last_play=None):
    acol = TEAM_COLORS.get(away, "#666")
    hcol = TEAM_COLORS.get(home, "#666")
    ac = KALSHI_CODES.get(away, "AWY")
    hc = KALSHI_CODES.get(home, "HME")
    pt = "Q" + str(period) if period <= 4 else "OT" + str(period - 4)
    pb = get_play_badge(last_play)
    s = '<svg viewBox="0 0 500 280" style="width:100%;max-width:500px;">'
    s += '<rect x="20" y="20" width="460" height="200" fill="#2d4a22" stroke="#fff" stroke-width="2" rx="8"/>'
    s += '<circle cx="250" cy="120" r="35" fill="none" stroke="#fff" stroke-width="2"/>'
    s += '<circle cx="250" cy="120" r="4" fill="#fff"/>'
    s += '<line x1="250" y1="20" x2="250" y2="220" stroke="#fff" stroke-width="2"/>'
    s += '<path d="M 20 50 Q 100 120 20 190" fill="none" stroke="#fff" stroke-width="2"/>'
    s += '<rect x="20" y="70" width="70" height="100" fill="none" stroke="#fff" stroke-width="2"/>'
    s += '<circle cx="90" cy="120" r="25" fill="none" stroke="#fff" stroke-width="2"/>'
    s += '<circle cx="35" cy="120" r="8" fill="none" stroke="#ff6b35" stroke-width="3"/>'
    s += '<path d="M 480 50 Q 400 120 480 190" fill="none" stroke="#fff" stroke-width="2"/>'
    s += '<rect x="410" y="70" width="70" height="100" fill="none" stroke="#fff" stroke-width="2"/>'
    s += '<circle cx="410" cy="120" r="25" fill="none" stroke="#fff" stroke-width="2"/>'
    s += '<circle cx="465" cy="120" r="8" fill="none" stroke="#ff6b35" stroke-width="3"/>'
    s += pb
    s += '<rect x="40" y="228" width="90" height="48" fill="' + acol + '" rx="6"/>'
    s += '<text x="85" y="250" fill="#fff" font-size="14" font-weight="bold" text-anchor="middle">' + ac + '</text>'
    s += '<text x="85" y="270" fill="#fff" font-size="18" font-weight="bold" text-anchor="middle">' + str(as2) + '</text>'
    s += '<rect x="370" y="228" width="90" height="48" fill="' + hcol + '" rx="6"/>'
    s += '<text x="415" y="250" fill="#fff" font-size="14" font-weight="bold" text-anchor="middle">' + hc + '</text>'
    s += '<text x="415" y="270" fill="#fff" font-size="18" font-weight="bold" text-anchor="middle">' + str(hs) + '</text>'
    s += '<text x="250" y="258" fill="#fff" font-size="16" font-weight="bold" text-anchor="middle">' + pt + ' ' + str(clock) + '</text>'
    s += '</svg>'
    return '<div style="background:#1a1a2e;border-radius:12px;padding:10px;">' + s + '</div>'

def get_play_icon(play_type, score_value):
    pl = play_type.lower() if play_type else ""
    if score_value > 0 or "made" in pl: return "🏀", "#22c55e"
    elif "miss" in pl or "block" in pl: return "❌", "#ef4444"
    elif "rebound" in pl: return "📥", "#3b82f6"
    elif "turnover" in pl or "steal" in pl: return "🔄", "#f97316"
    elif "foul" in pl: return "🚨", "#eab308"
    elif "timeout" in pl: return "⏸️", "#a855f7"
    return "•", "#888"

def get_kalshi_game_link(away, home):
    ac = KALSHI_CODES.get(away, "XXX").lower()
    hc = KALSHI_CODES.get(home, "XXX").lower()
    ds = datetime.now(eastern).strftime('%y%b%d').lower()
    return "https://kalshi.com/markets/kxnbagame/professional-basketball-game/kxnbagame-" + ds + ac + hc

def calc_projection(total_score, minutes_played):
    if minutes_played >= 8:
        pace = total_score / minutes_played
        weight = min(1.0, (minutes_played - 8) / 16)
        bp = (pace * weight) + ((LEAGUE_AVG_TOTAL / 48) * (1 - weight))
        return max(185, min(265, round(bp * 48)))
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
    ast = TEAM_STATS.get(away, {"net": 0, "pace": 98})
    hst = TEAM_STATS.get(home, {"net": 0, "pace": 98})
    sc = 50 + ((hst["net"] - ast["net"] + 3) * 2)
    for inj in injuries.get(away, []):
        if inj["name"] in STAR_TIERS:
            sc += 5 if STAR_TIERS[inj["name"]] == 3 else 3
    for inj in injuries.get(home, []):
        if inj["name"] in STAR_TIERS:
            sc -= 5 if STAR_TIERS[inj["name"]] == 3 else 3
    if away in b2b_teams: sc += 3
    if home in b2b_teams: sc -= 3
    return max(0, min(100, round(sc)))

def remove_position(pos_id):
    st.session_state.positions = [p for p in st.session_state.positions if p['id'] != pos_id]

def calculate_net_rating(game):
    mins = game.get('minutes_played', 0)
    if mins < 1: return 0, 0, 0, 0
    hs = game['home_score']
    as2 = game['away_score']
    epp = mins * 2.08
    poss = round(epp)
    if poss < 1: return 0, 0, 0, 0
    ho = (hs / epp) * 100
    ao = (as2 / epp) * 100
    nr = round(ho - ao, 1)
    return round(ho, 1), round(ao, 1), nr, poss

def get_kalshi_freshness():
    tk = "nba_kalshi_time"
    if tk not in st.session_state:
        return "🔴 No data", 999
    age = _time.time() - st.session_state[tk]
    if age < 15: return "🟢 Live (" + str(int(age)) + "s)", age
    elif age < 60: return "🟡 " + str(int(age)) + "s ago", age
    else: return "🔴 Stale (" + str(int(age)) + "s)", age
        # ═══════════════════════════════════════════════
# FETCH ALL DATA
# ═══════════════════════════════════════════════
games = fetch_espn_games()
kalshi_ml = fetch_kalshi_ml()
kalshi_spreads = fetch_kalshi_spreads()
injuries = fetch_injuries()
b2b_teams = fetch_yesterday_teams()

live_games = [g for g in games if g['status'] in ['STATUS_IN_PROGRESS', 'STATUS_HALFTIME', 'STATUS_END_PERIOD'] or (g['period'] > 0 and g['status'] not in ['STATUS_FINAL', 'STATUS_FULL_TIME'])]
scheduled_games = [g for g in games if g['status'] == 'STATUS_SCHEDULED' and g['period'] == 0]
final_games = [g for g in games if g['status'] in ['STATUS_FINAL', 'STATUS_FULL_TIME']]

st.title("🏀 BIGSNAPSHOT NBA EDGE FINDER")
st.caption("v" + VERSION + " • " + now.strftime('%b %d, %Y %I:%M %p ET') + " • Vegas vs Kalshi Mispricing Detector")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Today's Games", len(games))
c2.metric("Live Now", len(live_games))
c3.metric("Scheduled", len(scheduled_games))
c4.metric("Final", len(final_games))

st.divider()

# ═══════════════════════════════════════════════
# v12.0 MISPRICING ALERT — refresh + freshness + 10% + 90¢ filter
# ═══════════════════════════════════════════════
st.subheader("💰 VEGAS vs KALSHI MISPRICING ALERT")

ref1, ref2, ref3 = st.columns([1, 1, 2])
with ref1:
    if st.button("🔄 Refresh Kalshi Prices", key="refresh_nba", use_container_width=True):
        kalshi_ml = fetch_kalshi_ml(force_refresh=True)
        kalshi_spreads = fetch_kalshi_spreads(force_refresh=True)
        st.toast("✅ Kalshi prices refreshed!")
        st.rerun()
with ref2:
    ft, fa = get_kalshi_freshness()
    st.markdown("**Data:** " + ft)
with ref3:
    st.caption("⚠️ ESPN = soft book odds. Edge may be smaller. Verify on Kalshi.")

st.caption("Buy when Kalshi underprices Vegas • 10%+ gap = edge • Skips 90¢+ games")

mispricings = []
for g in games:
    if g['status'] in ['STATUS_FINAL', 'STATUS_FULL_TIME']: continue
    away, home = g['away'], g['home']
    vegas = g.get('vegas_odds', {})
    ac = KALSHI_CODES.get(away, "XXX")
    hc = KALSHI_CODES.get(home, "XXX")
    kd = kalshi_ml.get(ac + "@" + hc, {})
    if not kd: continue
    # v12.0: skip 90¢+ games
    kyp = kd.get('yes_price', 0)
    if kyp >= 90 or (100 - kyp) >= 90: continue
    hml, aml, sprd = vegas.get('homeML'), vegas.get('awayML'), vegas.get('spread')
    if hml and aml:
        vhp = american_to_implied_prob(hml) * 100
        vap = american_to_implied_prob(aml) * 100
        tot = vhp + vap
        vhp, vap = vhp / tot * 100, vap / tot * 100
    elif sprd:
        try: vhp = max(10, min(90, 50 - (float(sprd) * 2.8))); vap = 100 - vhp
        except: continue
    else: continue
    khp = kd.get('home_implied', 50)
    kap = kd.get('away_implied', 50)
    he, ae = vhp - khp, vap - kap
    # v12.0: 10% threshold
    if he >= 10 or ae >= 10:
        if he >= ae:
            team, vp, kp, edge = home, vhp, khp, he
            act = "YES" if kd.get('yes_team_code', '').upper() == hc.upper() else "NO"
        else:
            team, vp, kp, edge = away, vap, kap, ae
            act = "YES" if kd.get('yes_team_code', '').upper() == ac.upper() else "NO"
        mispricings.append({'game': g, 'team': team, 'vegas_prob': vp, 'kalshi_prob': kp, 'edge': edge, 'action': act})

mispricings.sort(key=lambda x: x['edge'], reverse=True)

if mispricings:
    mc1, mc2 = st.columns([3, 1])
    with mc1: st.success("🔥 " + str(len(mispricings)) + " mispricing opportunities found!")
    with mc2:
        if st.button("➕ ADD ALL (" + str(len(mispricings)) + ")", key="add_all_mispricing", use_container_width=True):
            added = 0
            for mp in mispricings:
                g2 = mp['game']
                gk = g2['away'] + "@" + g2['home']
                if not any(p['game'] == gk for p in st.session_state.positions):
                    st.session_state.positions.append({"game": gk, "pick": mp['action'] + " (" + mp['team'] + ")", "type": "ML", "line": "-", "price": round(mp['kalshi_prob']), "contracts": 10, "link": get_kalshi_game_link(g2['away'], g2['home']), "id": str(uuid.uuid4())[:8]})
                    added += 1
            st.toast("✅ Added " + str(added) + " positions!"); st.rerun()
    for mp in mispricings:
        g2 = mp['game']
        gk = g2['away'] + "@" + g2['home']
        if mp['edge'] >= 15: ecol, elab = "#ff6b6b", "🔥 STRONG"
        elif mp['edge'] >= 12: ecol, elab = "#22c55e", "🟢 GOOD"
        else: ecol, elab = "#eab308", "🟡 EDGE"
        acol = "#22c55e" if mp['action'] == "YES" else "#ef4444"
        if g2['period'] > 0: stxt = "Q" + str(g2['period']) + " " + str(g2['clock'])
        else: stxt = g2.get('game_datetime', 'Scheduled') or 'Scheduled'
        co1, co2 = st.columns([3, 1])
        with co1: st.markdown("**" + g2['away'] + " @ " + g2['home'] + "** • " + stxt)
        with co2: st.markdown('<span style="color:' + ecol + ';font-weight:bold">' + elab + ' +' + str(round(mp['edge'])) + '%</span>', unsafe_allow_html=True)
        ch = '<div style="background:#0f172a;padding:16px;border-radius:10px;border:2px solid ' + ecol + ';margin-bottom:12px">'
        ch += '<div style="font-size:1.4em;font-weight:bold;color:#fff;margin-bottom:8px">'
        ch += '🎯 BUY <span style="color:' + acol + ';background:' + acol + '22;padding:4px 12px;border-radius:6px">'
        ch += mp['action'] + '</span> on Kalshi</div>'
        ch += '<div style="color:#aaa;margin-bottom:12px">' + mp['action'] + ' = ' + mp['team'] + ' wins</div>'
        ch += '<table style="width:100%;text-align:center;color:#fff">'
        ch += '<tr style="color:#888"><td>Vegas</td><td>Kalshi</td><td>EDGE</td></tr>'
        ch += '<tr style="font-size:1.3em;font-weight:bold">'
        ch += '<td>' + str(round(mp['vegas_prob'])) + '%</td>'
        ch += '<td>' + str(round(mp['kalshi_prob'])) + '¢</td>'
        ch += '<td style="color:' + ecol + '">+' + str(round(mp['edge'])) + '%</td></tr></table>'
        ch += '<div style="color:#f97316;font-size:0.85em;margin-top:8px">⚠️ ESPN = soft book. Sharp line may differ.</div>'
        ch += '</div>'
        st.markdown(ch, unsafe_allow_html=True)
        bc1, bc2 = st.columns(2)
        with bc1: st.link_button("🎯 BUY " + mp['action'] + " (" + mp['team'] + ")", get_kalshi_game_link(g2['away'], g2['home']), use_container_width=True)
        with bc2:
            if any(p['game'] == gk for p in st.session_state.positions): st.success("✅ Tracked")
            elif st.button("➕ Track", key="mp_" + gk):
                st.session_state.positions.append({"game": gk, "pick": mp['action'] + " (" + mp['team'] + ")", "type": "ML", "line": "-", "price": round(mp['kalshi_prob']), "contracts": 10, "link": get_kalshi_game_link(g2['away'], g2['home']), "id": str(uuid.uuid4())[:8]}); st.rerun()
else:
    st.info("🔍 No mispricings (need 10%+ gap, excludes 90¢+ games)")

st.divider()

# ═══════════════════════════════════════════════
# LIVE EDGE MONITOR
# ═══════════════════════════════════════════════
st.subheader("🎮 LIVE EDGE MONITOR")

if live_games:
    for g in live_games:
        away, home = g['away'], g['home']
        total, mins, gid = g['total_score'], g['minutes_played'], g['game_id']
        plays = fetch_plays(gid)
        st.markdown("### " + away + " @ " + home)
        st.markdown(render_scoreboard(away, home, g['away_score'], g['home_score'], g['period'], g['clock'], g.get('away_record', ''), g.get('home_record', '')), unsafe_allow_html=True)
        col1, col2 = st.columns([1, 1])
        with col1:
            lp = plays[-1] if plays else None
            st.markdown(render_nba_court(away, home, g['away_score'], g['home_score'], g['period'], g['clock'], lp), unsafe_allow_html=True)
            pt, ptxt = infer_possession(plays, away, home)
            if ptxt:
                pc = TEAM_COLORS.get(pt, "#ffd700") if pt else "#888"
                ph
                # ═══════════════════════════════════════════════
# LIVE EDGE MONITOR
# ═══════════════════════════════════════════════
st.subheader("🎮 LIVE EDGE MONITOR")

if live_games:
    for g in live_games:
        away, home = g['away'], g['home']
        total, mins, gid = g['total_score'], g['minutes_played'], g['game_id']
        plays = fetch_plays(gid)
        st.markdown("### " + away + " @ " + home)
        st.markdown(render_scoreboard(away, home, g['away_score'], g['home_score'], g['period'], g['clock'], g.get('away_record', ''), g.get('home_record', '')), unsafe_allow_html=True)
        col1, col2 = st.columns([1, 1])
        with col1:
            lp = plays[-1] if plays else None
            st.markdown(render_nba_court(away, home, g['away_score'], g['home_score'], g['period'], g['clock'], lp), unsafe_allow_html=True)
            pt, ptxt = infer_possession(plays, away, home)
            if ptxt:
                pc = TEAM_COLORS.get(pt, "#ffd700") if pt else "#888"
                ph = '<div style="text-align:center;padding:8px;background:#1a1a2e;border-radius:6px;margin-top:4px">'
                ph += '<span style="color:' + pc + ';font-size:1.3em;font-weight:bold">'
                ph += ptxt + ' BALL</span></div>'
                st.markdown(ph, unsafe_allow_html=True)
        with col2:
            st.markdown("**📋 LAST 10 PLAYS**")
            tts_on = st.checkbox("🔊 Announce plays", key="tts_" + str(gid))
            if plays:
                for i, p in enumerate(reversed(plays)):
                    icon, color = get_play_icon(p['play_type'], p['score_value'])
                    ptx = p['text'][:60] if p['text'] else "Play"
                    ph = '<div style="padding:4px 8px;margin:2px 0;background:#1e1e2e;'
                    ph += 'border-radius:4px;border-left:3px solid ' + color + '">'
                    ph += '<span style="color:' + color + '">' + icon + '</span> '
                    ph += 'Q' + str(p['period']) + ' ' + str(p['clock']) + ' • ' + ptx + '</div>'
                    st.markdown(ph, unsafe_allow_html=True)
                    if i == 0 and tts_on and p['text']:
                        speak_play("Q" + str(p['period']) + " " + str(p['clock']) + ". " + p['text'])
            else:
                st.caption("Waiting for plays...")
        if mins >= 6:
            proj = calc_projection(total, mins)
            pace = total / mins if mins > 0 else 0
            pl, pcol = get_pace_label(pace)
            lead = g['home_score'] - g['away_score']
            leader = home if g['home_score'] > g['away_score'] else away
            klink = get_kalshi_game_link(away, home)
            ih = '<div style="background:#1e1e2e;padding:12px;border-radius:8px;margin-top:8px">'
            ih += '<b>Score:</b> ' + str(total) + ' pts in ' + str(mins) + ' min • '
            ih += '<b>Pace:</b> <span style="color:' + pcol + '">' + pl + '</span> '
            ih += '(' + str(round(pace, 1)) + '/min)<br>'
            ih += '<b>Projection:</b> ' + str(proj) + ' pts • '
            ih += '<b>Lead:</b> ' + leader + ' +' + str(abs(lead)) + '</div>'
            st.markdown(ih, unsafe_allow_html=True)
            ac = KALSHI_CODES.get(away, "XXX")
            hc = KALSHI_CODES.get(home, "XXX")
            kd = kalshi_ml.get(ac + "@" + hc, {})
            st.markdown("**🎯 MONEYLINE**")
            if abs(lead) >= 10:
                mlp = leader
                mlc = "🔥 STRONG" if abs(lead) >= 15 else "🟢 GOOD"
                if kd:
                    if leader == home:
                        mla = "YES" if kd.get('yes_team_code', '').upper() == hc.upper() else "NO"
                    else:
                        mla = "YES" if kd.get('yes_team_code', '').upper() == ac.upper() else "NO"
                    st.link_button(mlc + " BUY " + mla + " (" + mlp + " ML) • Lead +" + str(abs(lead)), klink, use_container_width=True)
                else:
                    st.link_button(mlc + " " + mlp + " ML • Lead +" + str(abs(lead)), klink, use_container_width=True)
            else:
                st.caption("⏳ Wait for larger lead (currently " + leader + " +" + str(abs(lead)) + ")")
            st.markdown("**📊 TOTALS**")
            yes_lines = [(t, proj - t) for t in sorted(THRESHOLDS) if proj - t >= 6]
            no_lines = [(t, t - proj) for t in sorted(THRESHOLDS, reverse=True) if t - proj >= 6]
            tc1, tc2 = st.columns(2)
            with tc1:
                st.markdown('<span style="color:#22c55e;font-weight:bold">🟢 YES (Over) — go LOW</span>', unsafe_allow_html=True)
                if yes_lines:
                    for i, (line, cush) in enumerate(yes_lines[:3]):
                        if cush >= 20: sf = "🔒 FORTRESS"
                        elif cush >= 12: sf = "✅ SAFE"
                        else: sf = "🎯 TIGHT"
                        rec = " ⭐REC" if i == 0 and cush >= 12 else ""
                        st.link_button(sf + " YES " + str(line) + " (+" + str(int(cush)) + ")" + rec, klink, use_container_width=True)
                else: st.caption("No safe YES lines (need 6+ cushion)")
            with tc2:
                st.markdown('<span style="color:#ef4444;font-weight:bold">🔴 NO (Under) — go HIGH</span>', unsafe_allow_html=True)
                if no_lines:
                    for i, (line, cush) in enumerate(no_lines[:3]):
                        if cush >= 20: sf = "🔒 FORTRESS"
                        elif cush >= 12: sf = "✅ SAFE"
                        else: sf = "🎯 TIGHT"
                        rec = " ⭐REC" if i == 0 and cush >= 12 else ""
                        st.link_button(sf + " NO " + str(line) + " (+" + str(int(cush)) + ")" + rec, klink, use_container_width=True)
                else: st.caption("No safe NO lines (need 6+ cushion)")
        else:
            st.caption("⏳ Waiting for 6+ minutes...")
        st.divider()
else:
    st.info("No live games right now")

st.divider()
# ═══════════════════════════════════════════════
# PRE-GAME ALIGNMENT
# ═══════════════════════════════════════════════
with st.expander("🎯 PRE-GAME ALIGNMENT (Speculative)", expanded=True):
    st.caption("Model prediction for scheduled games")
    if scheduled_games:
        all_picks = []
        for g in scheduled_games:
            away, home = g['away'], g['home']
            es = calc_pregame_edge(away, home, injuries, b2b_teams)
            if es >= 70: pick, el, ec = home, "🟢 STRONG", "#22c55e"
            elif es >= 60: pick, el, ec = home, "🟢 GOOD", "#22c55e"
            elif es <= 30: pick, el, ec = away, "🟢 STRONG", "#22c55e"
            elif es <= 40: pick, el, ec = away, "🟢 GOOD", "#22c55e"
            else: pick, el, ec = "WAIT", "🟡 NEUTRAL", "#eab308"
            all_picks.append({"away": away, "home": home, "pick": pick, "edge_label": el, "edge_color": ec})
        actionable = [p for p in all_picks if p['pick'] != "WAIT"]
        if actionable:
            a1, a2 = st.columns([3, 1])
            with a1: st.caption(str(len(actionable)) + " actionable picks out of " + str(len(all_picks)) + " games")
            with a2:
                if st.button("➕ ADD ALL (" + str(len(actionable)) + ")", key="add_all_pregame", use_container_width=True):
                    added = 0
                    for p in actionable:
                        gk = p['away'] + "@" + p['home']
                        if not any(pos['game'] == gk for pos in st.session_state.positions):
                            st.session_state.positions.append({"game": gk, "pick": p['pick'], "type": "ML", "line": "-", "price": 50, "contracts": 10, "link": get_kalshi_game_link(p['away'], p['home']), "id": str(uuid.uuid4())[:8]})
                            added += 1
                    st.toast("✅ Added " + str(added)); st.rerun()
            st.markdown("---")
        for p in all_picks:
            g1, g2, g3, g4 = st.columns([2.5, 1, 2, 1])
            gdt = ""
            for g in scheduled_games:
                if g['away'] == p['away'] and g['home'] == p['home']:
                    gdt = g.get('game_datetime', '')
                    break
            with g1:
                st.markdown("**" + p['away'] + " @ " + p['home'] + "**")
                if gdt: st.caption(gdt)
            with g2: st.markdown('<span style="color:' + p['edge_color'] + '">' + p['edge_label'] + '</span>', unsafe_allow_html=True)
            with g3:
                if p['pick'] != "WAIT":
                    st.link_button("🎯 " + p['pick'] + " ML", get_kalshi_game_link(p['away'], p['home']), use_container_width=True)
                else: st.caption("Wait for better edge")
            with g4:
                if p['pick'] != "WAIT":
                    gk = p['away'] + "@" + p['home']
                    if any(pos['game'] == gk for pos in st.session_state.positions): st.caption("✅ Tracked")
                    elif st.button("➕", key="quick_" + p['away'] + "_" + p['home']):
                        st.session_state.positions.append({"game": gk, "pick": p['pick'], "type": "ML", "line": "-", "price": 50, "contracts": 10, "link": get_kalshi_game_link(p['away'], p['home']), "id": str(uuid.uuid4())[:8]})
                        st.rerun()
    else: st.info("No scheduled games")

st.divider()

# ═══════════════════════════════════════════════
# INJURY REPORT
# ═══════════════════════════════════════════════
st.subheader("🏥 INJURY REPORT")
today_teams = set([g['away'] for g in games] + [g['home'] for g in games])
inj_found = False
for team in sorted(today_teams):
    for inj in injuries.get(team, []):
        if inj['name'] in STAR_PLAYERS.get(team, []):
            inj_found = True
            tier = STAR_TIERS.get(inj['name'], 1)
            if tier == 3: stars = "⭐⭐⭐"
            elif tier == 2: stars = "⭐⭐"
            else: stars = "⭐"
            st.markdown("**" + team + "**: " + stars + " " + inj['name'] + " - " + inj['status'])
if not inj_found: st.info("No star player injuries reported")

st.divider()

# ═══════════════════════════════════════════════
# POSITION TRACKER
# ═══════════════════════════════════════════════
st.subheader("📊 POSITION TRACKER")
today_gms = [(g['away'] + " @ " + g['home'], g['away'], g['home']) for g in games]

with st.expander("➕ ADD NEW POSITION", expanded=False):
    if today_gms:
        a1, a2 = st.columns(2)
        with a1:
            game_sel = st.selectbox("Select Game", [g[0] for g in today_gms], key="add_game")
            sg = next((g for g in today_gms if g[0] == game_sel), None)
        with a2: bt = st.selectbox("Bet Type", ["ML (Moneyline)", "Totals (Over/Under)", "Spread"], key="add_type")
        a3, a4 = st.columns(2)
        with a3:
            if bt == "ML (Moneyline)": pick = st.selectbox("Pick", [sg[1], sg[2]] if sg else [], key="add_pick")
            elif bt == "Spread": pick = st.selectbox("Pick Team", [sg[1], sg[2]] if sg else [], key="add_pick")
            else: pick = st.selectbox("Pick", ["YES (Over)", "NO (Under)"], key="add_totals_pick")
        with a4:
            if bt == "Spread":
                if sg:
                    sac = KALSHI_CODES.get(sg[1], "XXX")
                    shc = KALSHI_CODES.get(sg[2], "XXX")
                    sgk = sac + "@" + shc
                    ksl = kalshi_spreads.get(sgk, [])
                    if ksl:
                        sopts = [sp['line'] + " (" + sp['team_code'] + ") @ " + str(sp['yes_price']) + "¢" for sp in ksl]
                        line = st.selectbox("Kalshi Spreads", sopts, key="add_spread_line")
                        line = line.split()[0] if line else "-7.5"
                    else:
                        sopts = ["-1.5", "-2.5", "-3.5", "-4.5", "-5.5", "-6.5", "-7.5", "-8.5", "-9.5", "-10.5", "-11.5", "-12.5", "+1.5", "+2.5", "+3.5", "+4.5", "+5.5", "+6.5", "+7.5", "+8.5", "+9.5", "+10.5", "+11.5", "+12.5"]
                        line = st.selectbox("Spread Line", sopts, index=5, key="add_spread_line")
                else: line = "-7.5"
            elif "Totals" in bt: line = st.selectbox("Line", THRESHOLDS, key="add_line")
            else: line = "-"
        a5, a6, a7 = st.columns(3)
        with a5: ep = st.number_input("Entry Price (¢)", 1, 99, 50, key="add_price")
        with a6: ct = st.number_input("Contracts", 1, 10000, 10, key="add_contracts")
        with a7:
            cost = ep * ct / 100
            st.metric("Cost", "$" + str(round(cost, 2)))
            st.caption("Win: +$" + str(round(ct - cost, 2)))
        if st.button("✅ ADD POSITION", use_container_width=True, key="add_pos_btn"):
            if sg:
                if bt == "ML (Moneyline)": pt2, pp, pl2 = "ML", pick, "-"
                elif bt == "Spread": pt2, pp, pl2 = "Spread", pick, str(line)
                else: pt2, pp, pl2 = "Totals", pick.split()[0], str(line)
                st.session_state.positions.append({"game": sg[1] + "@" + sg[2], "pick": pp, "type": pt2, "line": pl2, "price": ep, "contracts": ct, "link": get_kalshi_game_link(sg[1], sg[2]), "id": str(uuid.uuid4())[:8]})
                st.success("Added!"); st.rerun()

if st.session_state.positions:
    st.markdown("---")
    for idx, pos in enumerate(st.session_state.positions):
        cur = next((g for g in games if g['away'] + "@" + g['home'] == pos['game']), None)
        p1, p2, p3, p4, p5 = st.columns([2.5, 1.5, 1.5, 1.5, 1])
        with p1:
            st.markdown("**" + pos['game'] + "**")
            if cur:
                if cur['period'] > 0:
                    st.caption("🔴 LIVE Q" + str(cur['period']) + " " + str(cur['clock']) + " | " + str(cur['away_score']) + "-" + str(cur['home_score']))
                elif cur['status'] in ['STATUS_FINAL', 'STATUS_FULL_TIME']:
                    st.caption("✅ FINAL " + str(cur['away_score']) + "-" + str(cur['home_score']))
                else: st.caption("⏳ Scheduled")
        with p2:
            if pos['type'] == "ML": st.write("🎯 " + pos['pick'] + " ML")
            elif pos['type'] == "Spread": st.write("📏 " + pos['pick'] + " " + pos['line'])
            else: st.write("📊 " + pos['pick'] + " " + pos['line'])
        with p3:
            st.write(str(pos.get('contracts', 10)) + " @ " + str(pos.get('price', 50)) + "¢")
            st.caption("$" + str(round(pos.get('price', 50) * pos.get('contracts', 10) / 100, 2)))
        with p4: st.link_button("🔗 Kalshi", pos['link'], use_container_width=True)
        with p5:
            if st.button("🗑️", key="del_" + pos['id']):
                remove_position(pos['id']); st.rerun()
    st.markdown("---")
    if st.button("🗑️ CLEAR ALL POSITIONS", use_container_width=True, type="primary"):
        st.session_state.positions = []; st.rerun()
else:
    st.caption("No positions tracked yet.")

st.divider()

# ═══════════════════════════════════════════════
# ALL GAMES TODAY
# ═══════════════════════════════════════════════
st.subheader("📋 ALL GAMES TODAY")
for g in games:
    if g['status'] in ['STATUS_FINAL', 'STATUS_FULL_TIME']:
        status = "FINAL: " + str(g['away_score']) + "-" + str(g['home_score'])
        color = "#666"
    elif g['period'] > 0:
        status = "LIVE Q" + str(g['period']) + " " + str(g['clock']) + " | " + str(g['away_score']) + "-" + str(g['home_score'])
        color = "#22c55e"
    else:
        status = str(g.get('game_datetime', 'TBD')) + " | Spread: " + str(g.get('vegas_odds', {}).get('spread', 'N/A'))
        color = "#888"
    gh = '<div style="background:#1e1e2e;padding:12px;border-radius:8px;'
    gh += 'margin-bottom:8px;border-left:3px solid ' + color + '">'
    gh += '<b style="color:#fff">' + g['away'] + ' @ ' + g['home'] + '</b><br>'
    gh += '<span style="color:' + color + '">' + status + '</span></div>'
    st.markdown(gh, unsafe_allow_html=True)

st.divider()
st.caption("v" + VERSION + " • Educational only • Not financial advice")
st.caption("Stay small. Stay quiet. Win.")
st.divider()
