import streamlit as st
from streamlit_autorefresh import st_autorefresh
import streamlit.components.v1 as components
st.set_page_config(page_title="BigSnapshot WNBA Edge Finder", page_icon="🏀", layout="wide")
from auth import require_auth
require_auth()
st_autorefresh(interval=24000, key="datarefresh_wnba")
import uuid, re, requests, pytz
import requests as req_ga
from datetime import datetime, timedelta

def send_ga4_event(pt, pp):
    try:
        url = "https://www.google-analytics.com/mp/collect?measurement_id=G-NQKY5VQ376&api_secret=n4oBJjH7RXi0dA7aQo2CZA"
        req_ga.post(url, json={"client_id": str(uuid.uuid4()), "events": [{"name": "page_view", "params": {"page_title": pt, "page_location": "https://bigsnapshot.streamlit.app" + pp}}]}, timeout=2)
    except: pass
send_ga4_event("BigSnapshot WNBA Edge Finder", "/WNBA")

eastern = pytz.timezone("US/Eastern")
now = datetime.now(eastern)
VERSION = "1.0"
LEAGUE_AVG_TOTAL = 160
THRESHOLDS = [140.5, 145.5, 150.5, 155.5, 160.5, 165.5, 170.5, 175.5]
HOME_COURT_ADV = 2.0
MIN_UNDERDOG_LEAD = 5
MIN_SPREAD_BRACKET = 7
MAX_NO_PRICE = 85
MIN_WP_EDGE = 8
LEAD_BY_QUARTER = {1: 5, 2: 6, 3: 8, 4: 10}

if 'positions' not in st.session_state: st.session_state.positions = []
if 'sniper_alerts' not in st.session_state: st.session_state.sniper_alerts = []
if 'comeback_alerts' not in st.session_state: st.session_state.comeback_alerts = []
if 'comeback_tracking' not in st.session_state: st.session_state.comeback_tracking = {}
if 'alerted_games' not in st.session_state: st.session_state.alerted_games = set()
if 'comeback_alerted' not in st.session_state: st.session_state.comeback_alerted = set()

TEAM_ABBREVS = {
    "Atlanta Dream": "Atlanta", "Chicago Sky": "Chicago",
    "Connecticut Sun": "Connecticut", "Dallas Wings": "Dallas",
    "Golden State Valkyries": "Golden State", "Indiana Fever": "Indiana",
    "Las Vegas Aces": "Las Vegas", "Los Angeles Sparks": "Los Angeles",
    "Minnesota Lynx": "Minnesota", "New York Liberty": "New York",
    "Phoenix Mercury": "Phoenix", "Seattle Storm": "Seattle",
    "Washington Mystics": "Washington",
    "ATL": "Atlanta", "CHI": "Chicago", "CONN": "Connecticut",
    "DAL": "Dallas", "GS": "Golden State", "GSV": "Golden State",
    "IND": "Indiana", "LV": "Las Vegas", "LVA": "Las Vegas",
    "LA": "Los Angeles", "LAS": "Los Angeles",
    "MIN": "Minnesota", "NY": "New York", "NYL": "New York",
    "PHX": "Phoenix", "SEA": "Seattle", "WAS": "Washington",
}

KALSHI_CODES = {
    "Atlanta": "ATL", "Chicago": "CHI", "Connecticut": "CONN",
    "Dallas": "DAL", "Golden State": "GSV", "Indiana": "IND",
    "Las Vegas": "LVA", "Los Angeles": "LAS", "Minnesota": "MIN",
    "New York": "NYL", "Phoenix": "PHX", "Seattle": "SEA",
    "Washington": "WAS",
}

TEAM_COLORS = {
    "Atlanta": "#E31837", "Chicago": "#568FE3", "Connecticut": "#F05023",
    "Dallas": "#003DA5", "Golden State": "#552583", "Indiana": "#002D62",
    "Las Vegas": "#000000", "Los Angeles": "#552583", "Minnesota": "#236192",
    "New York": "#6ECEB2", "Phoenix": "#CB6015", "Seattle": "#2C5234",
    "Washington": "#E03A3E",
}

ESPN_TEAM_IDS = {
    "Atlanta": "1", "Chicago": "2", "Connecticut": "3",
    "Dallas": "4", "Golden State": "20", "Indiana": "5",
    "Las Vegas": "6", "Los Angeles": "7", "Minnesota": "8",
    "New York": "9", "Phoenix": "10", "Seattle": "11",
    "Washington": "12",
}

def american_to_implied_prob(odds):
    if odds is None: return None
    return 100 / (odds + 100) if odds > 0 else abs(odds) / (abs(odds) + 100)

def speak_play(text):
    c = text.replace('"', '').replace("'", "").replace("\n", " ")[:100]
    h = "<script>(function(){if(window.lastSpoken==='"
    h += c
    h += "')return;window.lastSpoken='"
    h += c
    h += "';var u=new SpeechSynthesisUtterance('"
    h += c
    h += "');u.rate=1.1;window.speechSynthesis.speak(u)})();</script>"
    components.html(h, height=0)

def get_kalshi_game_link(away, home):
    ac = KALSHI_CODES.get(away, "").lower()
    hc = KALSHI_CODES.get(home, "").lower()
    d = datetime.now(eastern).strftime('%y%b%d').lower()
    return "https://kalshi.com/markets/kxwnbagame/professional-basketball-game/kxwnbagame-" + d + ac + hc

def get_kalshi_spread_link(away, home):
    ac = KALSHI_CODES.get(away, "").lower()
    hc = KALSHI_CODES.get(home, "").lower()
    d = datetime.now(eastern).strftime('%y%b%d').lower()
    return "https://kalshi.com/markets/kxwnbaspread/wnba-spread/kxwnbaspread-" + d + ac + hc

def calc_projection(ts, mp):
    if mp >= 6:
        p = ts / mp
        w = min(1.0, (mp - 6) / 12)
        return max(120, min(200, round((p * w + (160 / 40) * (1 - w)) * 40)))
    elif mp >= 4:
        p = ts / mp
        return max(120, min(200, round(((p * 0.3) + ((160 / 40) * 0.7)) * 40)))
    return 160

def get_pace_label(pace):
    if pace < 3.5: return "🐢 SLOW", "#22c55e"
    elif pace < 4.0: return "⚖️ AVG", "#eab308"
    elif pace < 4.5: return "🔥 FAST", "#f97316"
    return "💥 SHOOTOUT", "#ef4444"

def parse_record(s):
    try:
        parts = s.split("-")
        return (int(parts[0]), int(parts[1]))
    except: return (0, 0)

def get_favorite_side(home_record, away_record, home_ml=0):
    if home_ml != 0: return "home" if home_ml < 0 else "away"
    hw, hl = parse_record(home_record)
    aw, al = parse_record(away_record)
    h_pct = hw / (hw + hl) if (hw + hl) > 0 else 0.5
    a_pct = aw / (aw + al) if (aw + al) > 0 else 0.5
    return "home" if h_pct >= a_pct else "away"

def _parse_win_pct(rs):
    try:
        parts = rs.strip().split()[0].split("-")
        w, l = int(parts[0]), int(parts[1])
        return w / (w + l) if (w + l) > 0 else None
    except: return None

def remove_position(pid):
    st.session_state.positions = [p for p in st.session_state.positions if p.get('id') != pid]

@st.cache_data(ttl=30)
def fetch_espn_games_wnba():
    try:
        today = datetime.now(eastern).strftime("%Y%m%d")
        url = "https://site.api.espn.com/apis/site/v2/sports/basketball/wnba/scoreboard?dates=" + today
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
            minutes_played = 0
            if state == "in":
                completed_periods = max(0, period - 1)
                completed_mins = 0
                for p in range(1, completed_periods + 1):
                    completed_mins += 10 if p <= 4 else 5
                try:
                    cparts = clock_str.replace(" ", "").split(":")
                    remaining = float(cparts[0]) + float(cparts[1]) / 60 if len(cparts) == 2 else float(cparts[0])
                except: remaining = 0
                current_period_length = 10 if period <= 4 else 5
                minutes_played = completed_mins + (current_period_length - remaining)
            elif state == "post": minutes_played = 40
            total_score = away_score + home_score
            vegas = {}
            home_ml = 0
            try:
                odds_list = comp.get("odds", [])
                if odds_list:
                    o = odds_list[0]
                    vegas = {"spread": o.get("details", ""), "overUnder": o.get("overUnder", 0), "homeML": o.get("homeTeamOdds", {}).get("moneyLine", 0), "awayML": o.get("awayTeamOdds", {}).get("moneyLine", 0)}
                    home_ml = vegas.get("homeML", 0) or 0
            except: pass
            gt_raw = event.get("date", "")
            try:
                gt_dt = datetime.strptime(gt_raw, "%Y-%m-%dT%H:%MZ").replace(tzinfo=pytz.utc).astimezone(eastern)
                game_time = gt_dt.strftime("%-I:%M %p ET")
                game_datetime = gt_dt.strftime("%Y-%m-%d %H:%M")
            except: game_time, game_datetime = "", ""
            games.append({"away": away, "home": home, "away_score": away_score, "home_score": home_score,
                "away_record": away_rec, "home_record": home_rec,
                "away_id": away_team["team"].get("id", ""), "home_id": home_team["team"].get("id", ""),
                "away_abbrev": away_team["team"].get("abbreviation", ""), "home_abbrev": home_team["team"].get("abbreviation", ""),
                "away_full": away_full, "home_full": home_full, "status": status, "state": state,
                "period": period, "clock": clock_str, "minutes_played": minutes_played, "total_score": total_score,
                "game_id": event.get("id", ""), "vegas_odds": vegas, "home_ml": home_ml,
                "game_time": game_time, "game_datetime": game_datetime})
        return games
    except: return []

@st.cache_data(ttl=300)
def fetch_game_summary_wnba(game_id):
    try:
        url = "https://site.api.espn.com/apis/site/v2/sports/basketball/wnba/summary?event=" + str(game_id)
        return requests.get(url, timeout=10).json()
    except: return None

@st.cache_data(ttl=20)
def fetch_espn_win_prob_wnba(game_id):
    try:
        url = "https://site.api.espn.com/apis/site/v2/sports/basketball/wnba/summary?event=" + str(game_id)
        data = requests.get(url, timeout=10).json()
        try:
            wp = data["winprobability"]
            if wp: return wp[-1]["homeWinPercentage"] * 100
        except: pass
        try: return float(data["predictor"]["homeTeam"]["gameProjection"])
        except: pass
    except: pass
    return None

def parse_predictor(summary):
    try:
        pred = summary.get("predictor", {})
        h = float(pred.get("homeTeam", {}).get("gameProjection", 50))
        a = float(pred.get("awayTeam", {}).get("gameProjection", 50))
        return h / 100, a / 100
    except: return 0.5, 0.5

def parse_team_stats_from_summary(summary):
    home_stats, away_stats = {}, {}
    try:
        teams = summary.get("boxscore", {}).get("teams", [])
        for t in teams:
            sd = home_stats if t.get("homeAway", "") == "home" else away_stats
            for s in t.get("statistics", []):
                sd[s.get("name", "")] = s.get("displayValue", "0")
    except: pass
    return home_stats, away_stats

def _get_team_leaders(summary, home_away):
    leaders = []
    try:
        for tb in summary.get("leaders", []):
            if tb.get("team", {}).get("homeAway") == home_away:
                for cat in tb.get("leaders", []):
                    if cat.get("name") in ("points", "rating"):
                        for l in cat.get("leaders", [])[:3]:
                            n = l.get("athlete", {}).get("displayName", "")
                            if n: leaders.append(n)
    except: pass
    return leaders

def _is_star_player(pn, ll):
    try:
        last = pn.strip().split()[-1].lower()
        for l in ll[:3]:
            if l.strip().split()[-1].lower() == last: return True
    except: pass
    return False

@st.cache_data(ttl=300)
def fetch_injuries_wnba():
    injuries = {}
    try:
        url = "https://site.api.espn.com/apis/site/v2/sports/basketball/wnba/injuries"
        data = requests.get(url, timeout=10).json()
        for tb in data.get("items", []):
            tn = TEAM_ABBREVS.get(tb.get("team", {}).get("displayName", ""), tb.get("team", {}).get("displayName", ""))
            ti = []
            for ath in tb.get("injuries", []):
                ti.append({"name": ath.get("athlete", {}).get("displayName", "Unknown"), "status": ath.get("status", "Unknown")})
            if ti: injuries[tn] = ti
    except: pass
    return injuries

@st.cache_data(ttl=300)
def fetch_yesterday_teams_wnba():
    try:
        yesterday = (datetime.now(eastern) - timedelta(days=1)).strftime("%Y%m%d")
        url = "https://site.api.espn.com/apis/site/v2/sports/basketball/wnba/scoreboard?dates=" + yesterday
        data = requests.get(url, timeout=10).json()
        teams = set()
        for event in data.get("events", []):
            for comp in event.get("competitions", []):
                for team in comp.get("competitors", []):
                    full = team["team"].get("displayName", "")
                    teams.add(TEAM_ABBREVS.get(full, full))
        return teams
    except: return set()

@st.cache_data(ttl=30)
def fetch_plays_wnba(game_id):
    try:
        url = "https://site.api.espn.com/apis/site/v2/sports/basketball/wnba/summary?event=" + str(game_id)
        data = requests.get(url, timeout=10).json()
        plays_raw = []
        for drive in data.get("plays", []):
            if isinstance(drive, dict): plays_raw.append(drive)
            elif isinstance(drive, list): plays_raw.extend(drive)
        plays_raw = plays_raw[-15:]
        result = []
        for p in plays_raw[-10:]:
            period = p.get("period", {}).get("number", 0) if isinstance(p.get("period"), dict) else p.get("period", 0)
            clock = p.get("clock", {}).get("displayValue", "") if isinstance(p.get("clock"), dict) else p.get("clock", "")
            play_type = p.get("type", {}).get("text", "") if isinstance(p.get("type"), dict) else ""
            team_id = str(p["team"].get("id", "")) if p.get("team") else ""
            result.append({"text": p.get("text", ""), "period": period, "clock": clock, "score_value": p.get("scoreValue", 0), "play_type": play_type, "team_id": team_id})
        return result
    except: return []

@st.cache_data(ttl=60)
def fetch_kalshi_ml_wnba():
    try:
        url = "https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXWNBAGAME&limit=100&status=open"
        data = requests.get(url, timeout=10).json()
        result = {}
        for m in data.get("markets", []):
            ticker = m.get("ticker", "")
            title = m.get("title", "")
            yes_bid = m.get("yes_bid", 0) or 0
            yes_price = m.get("last_price", 0) or yes_bid
            match = re.search(r'kxwnbagame-\w+?([a-z]{2,4})([a-z]{2,4})$', ticker.lower())
            if not match: continue
            away_code, home_code = match.group(1).upper(), match.group(2).upper()
            yes_team_code = ""
            if title:
                for code, name in KALSHI_CODES.items():
                    if name == away_code or code.upper() == away_code:
                        if code.lower() in title.lower() or name.lower() in title.lower():
                            yes_team_code = away_code
                            break
                if not yes_team_code: yes_team_code = away_code
            if yes_team_code == away_code:
                away_implied, home_implied = yes_price, (100 - yes_price if yes_price else 0)
            else:
                home_implied, away_implied = yes_price, (100 - yes_price if yes_price else 0)
            key = TEAM_ABBREVS.get(away_code, away_code) + "@" + TEAM_ABBREVS.get(home_code, home_code)
            result[key] = {"away_code": away_code, "home_code": home_code, "yes_team_code": yes_team_code, "ticker": ticker,
                "yes_bid": yes_bid, "yes_ask": m.get("yes_ask", 0) or 0, "yes_price": yes_price,
                "away_implied": away_implied, "home_implied": home_implied}
        return result
    except: return {}

@st.cache_data(ttl=60)
def fetch_kalshi_spreads_raw_wnba():
    spreads, spread_list = {}, []
    try:
        url = "https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXWNBASPREAD&limit=200&status=open"
        data = requests.get(url, timeout=10).json()
        for m in data.get("markets", []):
            ticker = m.get("ticker", "")
            title = (m.get("title", "") or "").lower()
            subtitle = (m.get("subtitle", "") or "").lower()
            if any(k in title or k in subtitle for k in ["wins by", "spread", "margin"]):
                spread_list.append(m)
            match = re.search(r'kxwnbaspread-\w+?([a-z]{2,4})([a-z]{2,4})', ticker.lower())
            if match:
                ac, hc = match.group(1).upper(), match.group(2).upper()
                key = TEAM_ABBREVS.get(ac, ac) + "@" + TEAM_ABBREVS.get(hc, hc)
                if key not in spreads: spreads[key] = []
                spreads[key].append({"ticker": ticker, "title": m.get("title", ""), "yes_price": m.get("last_price", 0) or 0,
                    "yes_bid": m.get("yes_bid", 0) or 0, "yes_ask": m.get("yes_ask", 0) or 0,
                    "no_bid": m.get("no_bid", 0) or 0, "no_ask": m.get("no_ask", 0) or 0})
    except: pass
    return spreads, spread_list

def find_spread_markets_for_game(ha, aa, hn, an, spread_list):
    matches = []
    ha_l, aa_l, hn_l, an_l = ha.lower(), aa.lower(), hn.lower(), an.lower()
    for m in spread_list:
        ticker = (m.get("ticker", "") or "").lower()
        title = (m.get("title", "") or "").lower()
        subtitle = (m.get("subtitle", "") or "").lower()
        combined = ticker + " " + title + " " + subtitle
        if (ha_l in combined or hn_l in combined) and (aa_l in combined or an_l in combined):
            spread_val = None
            pat1 = re.search(r'(?:over|more than|by)\s+([\d.]+)', title)
            if pat1: spread_val = float(pat1.group(1))
            else:
                pat2 = re.search(r'(\d+\.?\d*)\s*[-\u2013to]+\s*(\d+\.?\d*)', title)
                if pat2: spread_val = (float(pat2.group(1)) + float(pat2.group(2))) / 2
                else:
                    pat3 = re.search(r'\b([1-9]\d?(?:\.\d+)?)\b', title)
                    if pat3:
                        v = float(pat3.group(1))
                        if 1 <= v <= 50: spread_val = v
            if spread_val is None: continue
            yes_price = m.get("last_price", 0) or m.get("yes_bid", 0) or 0
            no_ask = m.get("no_ask", 0)
            no_price = no_ask if no_ask else (100 - yes_price if yes_price else 0)
            team_side = None
            if ha_l in title or hn_l in title: team_side = "home"
            elif aa_l in title or an_l in title: team_side = "away"
            matches.append({"ticker": m.get("ticker", ""), "title": m.get("title", ""), "spread_val": spread_val,
                "yes_price": yes_price, "no_price": no_price, "no_ask": no_ask, "team_side": team_side})
    matches.sort(key=lambda x: x["spread_val"], reverse=True)
    return matches

def find_ml_price_for_team(ha, aa, fav_side, kalshi_ml_data):
    ha_u, aa_u = ha.upper(), aa.upper()
    for key, val in kalshi_ml_data.items():
        tk = val.get("ticker", "").upper()
        if ha_u in tk and aa_u in tk:
            fav_code = ha_u if fav_side == "home" else aa_u
            if tk.endswith(fav_code): return val.get("yes_price", None), val.get("ticker", None)
            else:
                yp = val.get("yes_price", 0)
                return (100 - yp if yp else None), val.get("ticker", None)
    return None, None

def check_spread_sniper(g, spread_list, kalshi_ml_data):
    away = g.get('away', '')
    home = g.get('home', '')
    away_score = g.get('away_score', 0)
    home_score = g.get('home_score', 0)
    period = g.get('period', 0)
    game_id = g.get('game_id', '')
    away_rec = g.get('away_record', '0-0')
    home_rec = g.get('home_record', '0-0')
    home_ml = g.get('home_ml', 0)
    if game_id in st.session_state.alerted_games:
        return None
    fav_side = get_favorite_side(home_rec, away_rec, home_ml)
    if fav_side == "home":
        fav_name = home
        fav_score = home_score
        dog_name = away
        dog_score = away_score
        dog_record = away_rec
        fav_record = home_rec
    else:
        fav_name = away
        fav_score = away_score
        dog_name = home
        dog_score = home_score
        dog_record = home_rec
        fav_record = away_rec
    fav_abbrev = KALSHI_CODES.get(fav_name, fav_name[:3].upper())
    dog_abbrev = KALSHI_CODES.get(dog_name, dog_name[:3].upper())
    dog_lead = dog_score - fav_score
    if dog_lead <= 0:
        return None
    q = min(period, 4)
    if q < 1:
        return None
    required_lead = LEAD_BY_QUARTER.get(q, 10)
    if dog_lead < required_lead:
        return None
    fav_wp = None
    wp_edge = 0
    raw_wp = fetch_espn_win_prob_wnba(game_id)
    if raw_wp is not None:
        if fav_side == "home":
            fav_wp = raw_wp
        else:
            fav_wp = 100 - raw_wp
        wp_edge = fav_wp - 50
    ha_code = KALSHI_CODES.get(home, home[:3].upper())
    aa_code = KALSHI_CODES.get(away, away[:3].upper())
    spread_markets = find_spread_markets_for_game(ha_code, aa_code, home, away, spread_list)
    no_markets = len(spread_markets) == 0
    actionable = []
    for sm in spread_markets:
        spread_val = sm.get('spread_val', 0)
        if spread_val < MIN_SPREAD_BRACKET:
            continue
        no_price = sm.get('no_price', 0)
        no_ask = sm.get('no_ask', 0)
        effective_no = no_ask if no_ask and no_ask > 0 else no_price
        if effective_no > MAX_NO_PRICE:
            continue
        sm['effective_no_price'] = effective_no
        actionable.append(sm)
    actionable.sort(key=lambda x: x.get('effective_no_price', 999))
    st.session_state.alerted_games.add(game_id)
    return {
        'game': g, 'fav_name': fav_name, 'fav_abbrev': fav_abbrev,
        'fav_side': fav_side, 'fav_record': fav_record,
        'fav_wp': fav_wp, 'wp_edge': wp_edge,
        'dog_name': dog_name, 'dog_abbrev': dog_abbrev,
        'dog_lead': dog_lead, 'dog_record': dog_record,
        'spreads': actionable, 'no_markets': no_markets,
    }

def check_comeback(g, kalshi_ml_data):
    away = g.get('away', '')
    home = g.get('home', '')
    away_score = g.get('away_score', 0)
    home_score = g.get('home_score', 0)
    game_id = g.get('game_id', '')
    home_ml = g.get('home_ml', 0)
    away_rec = g.get('away_record', '0-0')
    home_rec = g.get('home_record', '0-0')
    fav_side = get_favorite_side(home_rec, away_rec, home_ml)
    if fav_side == "home":
        fav_name = home
        fav_score = home_score
        opp_score = away_score
    else:
        fav_name = away
        fav_score = away_score
        opp_score = home_score
    fav_margin = fav_score - opp_score
    if game_id in st.session_state.comeback_tracking:
        ct = st.session_state.comeback_tracking[game_id]
        current_deficit = opp_score - fav_score
        if current_deficit > ct.get('max_deficit', 0):
            ct['max_deficit'] = current_deficit
        st.session_state.comeback_tracking[game_id] = ct
    else:
        if fav_margin <= -10:
            st.session_state.comeback_tracking[game_id] = {
                'fav_side': fav_side, 'fav_name': fav_name,
                'max_deficit': abs(fav_margin),
            }
        return None
    ct = st.session_state.comeback_tracking.get(game_id, {})
    max_deficit = ct.get('max_deficit', 0)
    if max_deficit < 10:
        return None
    if fav_margin < -2:
        return None
    if game_id in st.session_state.comeback_alerted:
        return None
    fav_price = None
    key = away + "@" + home
    kalshi_info = kalshi_ml_data.get(key, {})
    if kalshi_info:
        if fav_side == "home":
            fav_price = kalshi_info.get('home_implied', 0)
        else:
            fav_price = kalshi_info.get('away_implied', 0)
    fav_wp = None
    raw_wp = fetch_espn_win_prob_wnba(game_id)
    if raw_wp is not None:
        if fav_side == "home":
            fav_wp = raw_wp
        else:
            fav_wp = 100 - raw_wp
    st.session_state.comeback_alerted.add(game_id)
    return {
        'game': g, 'fav_name': fav_name, 'fav_side': fav_side,
        'fav_margin': fav_margin, 'max_deficit': max_deficit,
        'fav_price': fav_price, 'fav_wp': fav_wp,
    }

# === END PART A ===
# ── PART B: EDGE MODEL + RENDERING + DATA FETCH + TABS 1-2 ──

def calc_advanced_edge(game, b2b_teams, summary=None, injuries=None):
    edges, total = [], 0.0
    home, away = game["home"], game["away"]
    home_rec, away_rec = game.get("home_record", "0-0"), game.get("away_record", "0-0")
    bpi_home, bpi_away = 0.5, 0.5
    if summary: bpi_home, bpi_away = parse_predictor(summary)
    bpi_edge = (bpi_home - 0.5) * 20
    edges.append({"factor": "ESPN BPI", "value": round(bpi_edge, 1), "detail": "Home " + str(round(bpi_home * 100)) + "% / Away " + str(round(bpi_away * 100)) + "%"})
    total += bpi_edge
    home_ml = game.get("home_ml", 0)
    vegas_implied = american_to_implied_prob(home_ml) if home_ml else None
    if vegas_implied and bpi_home:
        gap = (bpi_home - vegas_implied) * 100
        if abs(gap) >= 3:
            gap_edge = gap * 0.15
            edges.append({"factor": "BPI vs Vegas Gap", "value": round(gap_edge, 1), "detail": "Gap: " + ("+" if gap >= 0 else "") + str(round(gap, 1)) + "%"})
            total += gap_edge
        else: edges.append({"factor": "BPI vs Vegas Gap", "value": 0.0, "detail": "Aligned"})
    else: edges.append({"factor": "BPI vs Vegas Gap", "value": 0.0, "detail": "N/A"})
    hca = HOME_COURT_ADV / 2
    edges.append({"factor": "Home Court", "value": round(hca, 1), "detail": "+" + str(round(hca, 1)) + " pts"})
    total += hca
    h_pct = _parse_win_pct(home_rec) or 0.5
    a_pct = _parse_win_pct(away_rec) or 0.5
    rec_edge = (h_pct - a_pct) * 10
    edges.append({"factor": "Records", "value": round(rec_edge, 1), "detail": "Home " + str(round(h_pct, 3)) + " / Away " + str(round(a_pct, 3))})
    total += rec_edge
    net_edge = 0.0
    if summary:
        hs, aws = parse_team_stats_from_summary(summary)
        try:
            h_off = float(hs.get("avgPoints", hs.get("points", "0")).replace(",", ""))
            h_def = float(aws.get("avgPoints", aws.get("points", "0")).replace(",", ""))
            a_off = float(aws.get("avgPoints", aws.get("points", "0")).replace(",", ""))
            a_def = float(hs.get("avgPoints", hs.get("points", "0")).replace(",", ""))
            net_edge = ((h_off - h_def) - (a_off - a_def)) * 0.3
        except: pass
    edges.append({"factor": "Net Rating", "value": round(net_edge, 1), "detail": ("+" if net_edge >= 0 else "") + str(round(net_edge, 1))})
    total += net_edge
    b2b_edge = 0.0
    if home in b2b_teams: b2b_edge -= 2.5
    if away in b2b_teams: b2b_edge += 2.5
    if home in b2b_teams and away in b2b_teams: db = "Both B2B"
    elif home in b2b_teams: db = home + " B2B"
    elif away in b2b_teams: db = away + " B2B"
    else: db = "Neither B2B"
    edges.append({"factor": "B2B Fatigue", "value": round(b2b_edge, 1), "detail": db})
    total += b2b_edge
    ppg_edge = 0.0
    if summary:
        try:
            hs, aws = parse_team_stats_from_summary(summary)
            ppg_edge = (float(hs.get("avgPoints", "0").replace(",", "")) - float(aws.get("avgPoints", "0").replace(",", ""))) * 0.3
        except: pass
    edges.append({"factor": "PPG Gap", "value": round(ppg_edge, 1), "detail": ("+" if ppg_edge >= 0 else "") + str(round(ppg_edge, 1))})
    total += ppg_edge
    inj_edge, inj_detail = 0.0, "N/A"
    if injuries:
        home_leaders = _get_team_leaders(summary, "home") if summary else []
        away_leaders = _get_team_leaders(summary, "away") if summary else []
        parts = []
        for inj in injuries.get(home, []):
            st_l = (inj.get("status", "") or "").lower()
            nm = inj.get("name", "")
            star = _is_star_player(nm, home_leaders)
            if "out" in st_l: inj_edge -= 4.0 if star else 1.0; parts.append(nm + " OUT" + ("⭐" if star else ""))
            elif "day" in st_l or "dtd" in st_l: inj_edge -= 0.5; parts.append(nm + " DTD")
        for inj in injuries.get(away, []):
            st_l = (inj.get("status", "") or "").lower()
            nm = inj.get("name", "")
            star = _is_star_player(nm, away_leaders)
            if "out" in st_l: inj_edge += 4.0 if star else 1.0; parts.append(nm + " OUT" + ("⭐" if star else ""))
            elif "day" in st_l or "dtd" in st_l: inj_edge += 0.5; parts.append(nm + " DTD")
        inj_detail = ", ".join(parts[:4]) if parts else "No key injuries"
    edges.append({"factor": "Injuries", "value": round(inj_edge, 1), "detail": inj_detail})
    total += inj_edge
    tpt_edge = 0.0
    if summary:
        try:
            hs, aws = parse_team_stats_from_summary(summary)
            pct_gap = float(hs.get("threePointFieldGoalPct", "0")) - float(aws.get("threePointFieldGoalPct", "0"))
            made_gap = float(hs.get("threePointFieldGoalsMade", "0")) - float(aws.get("threePointFieldGoalsMade", "0"))
            tpt_edge = pct_gap * 0.15 + made_gap * 0.3
        except: pass
    edges.append({"factor": "3PT", "value": round(tpt_edge, 1), "detail": ("+" if tpt_edge >= 0 else "") + str(round(tpt_edge, 1))})
    total += tpt_edge
    at = abs(total)
    if at >= 8: strength = "🔴 STRONG"
    elif at >= 4: strength = "🟡 MODERATE"
    elif at >= 1.5: strength = "🟢 LEAN"
    else: strength = "⚪ TOSS-UP"
    side = "home" if total >= 0 else "away"
    return {"edges": edges, "score": round(total, 1), "pick": home if side == "home" else away, "side": side, "strength": strength, "bpi": bpi_home}

def infer_possession(plays, away, home):
    if not plays: return None, None
    last = plays[-1]
    text = (last.get("text", "") or "").lower()
    play_type = (last.get("play_type", "") or "").lower()
    team_id = str(last.get("team_id", ""))
    acting_team = None
    if team_id:
        for name, eid in ESPN_TEAM_IDS.items():
            if str(eid) == team_id: acting_team = name; break
    if not acting_team:
        hl, al = home.lower(), away.lower()
        hc, ac = KALSHI_CODES.get(home, "").lower(), KALSHI_CODES.get(away, "").lower()
        if hl in text or hc in text: acting_team = home
        elif al in text or ac in text: acting_team = away
    if not acting_team: return "UNKNOWN", None
    other = home if acting_team == away else away
    if any(w in play_type for w in ["made", "makes", "dunk", "layup"]) or any(w in text for w in ["makes", "made shot", "dunk", "layup"]): return other, "⬆️ " + other + " ball (after score)"
    if "defensive rebound" in text or "defensive rebound" in play_type: return acting_team, "🏀 " + acting_team + " ball (def rebound)"
    if "offensive rebound" in text or "offensive rebound" in play_type: return acting_team, "🏀 " + acting_team + " ball (off rebound)"
    if any(w in text for w in ["turnover", "steal"]) or "turnover" in play_type: return other, "🔄 " + other + " ball (turnover)"
    if "miss" in text or "miss" in play_type: return "LOOSE", "🔁 LOOSE BALL (miss)"
    if "foul" in text or "foul" in play_type: return other, "⚖️ " + other + " FT"
    return acting_team, "🏀 " + acting_team + " ball"

MOBILE_CSS = '<style>@media(max-width:600px){.sb-score{font-size:36px!important}.sb-team{font-size:20px!important}.sb-period{font-size:16px!important}.alert-box{padding:10px!important;font-size:13px!important}.edge-box{padding:8px!important}table{font-size:13px!important}td{padding:8px!important}}</style>'

def render_scoreboard(away, home, away_score, home_score, period, clock, away_record, home_record):
    ac, hc = TEAM_COLORS.get(away, "#888"), TEAM_COLORS.get(home, "#888")
    aa, ha_a = KALSHI_CODES.get(away, away[:3].upper()), KALSHI_CODES.get(home, home[:3].upper())
    pt = ""
    if period > 0 and period <= 4: pt = "Q" + str(period)
    elif period > 4: pt = "OT" + str(period - 4)
    h = MOBILE_CSS
    h += '<div style="background:#0f172a;border-radius:12px;padding:16px;max-width:100%;box-sizing:border-box;overflow-x:hidden">'
    h += '<div style="text-align:center;color:#fbbf24;font-weight:bold;font-size:clamp(16px,3vw,22px);margin-bottom:8px" class="sb-period">' + pt + ' ' + clock + '</div>'
    h += '<table style="width:100%;table-layout:fixed;border-collapse:collapse">'
    h += '<tr style="border-bottom:1px solid #334155">'
    h += '<td style="color:' + ac + ';font-weight:bold;font-size:clamp(18px,4vw,28px);padding:8px" class="sb-team">' + aa + '</td>'
    h += '<td style="color:#94a3b8;font-size:clamp(12px,2vw,16px);padding:8px">' + away_record + '</td>'
    h += '<td style="color:white;font-weight:bold;font-size:clamp(32px,8vw,52px);text-align:right;padding:8px" class="sb-score">' + str(away_score) + '</td></tr>'
    h += '<tr><td style="color:' + hc + ';font-weight:bold;font-size:clamp(18px,4vw,28px);padding:8px" class="sb-team">' + ha_a + '</td>'
    h += '<td style="color:#94a3b8;font-size:clamp(12px,2vw,16px);padding:8px">' + home_record + '</td>'
    h += '<td style="color:white;font-weight:bold;font-size:clamp(32px,8vw,52px);text-align:right;padding:8px" class="sb-score">' + str(home_score) + '</td></tr></table></div>'
    components.html(h, height=180)

def get_play_badge(last_play):
    if not last_play: return ""
    text = (last_play.get("text", "") or "").lower()
    sv = last_play.get("score_value", 0)
    color, label = "#888", ""
    if "three" in text or "3pt" in text or sv == 3: color, label = "#22c55e", "3PT MADE!"
    elif any(w in text for w in ["makes", "made", "dunk", "layup"]) or sv > 0:
        if "free throw" in text: color, label = "#22c55e", "FT MADE"
        else: color, label = "#22c55e", "BUCKET!"
    elif "miss" in text: color, label = "#ef4444", "MISSED"
    elif "block" in text: color, label = "#f97316", "BLOCKED!"
    elif "turnover" in text or "steal" in text: color, label = "#f97316", "TURNOVER"
    elif "rebound" in text: color, label = "#3b82f6", "REBOUND"
    elif "foul" in text: color, label = "#eab308", "FOUL"
    elif "timeout" in text: color, label = "#a855f7", "TIMEOUT"
    if not label: return ""
    r = '<rect x="175" y="25" width="150" height="30" rx="6" fill="' + color + '" opacity="0.9"/>'
    r += '<text x="250" y="45" text-anchor="middle" fill="white" font-size="13" font-weight="bold">' + label + '</text>'
    return r

def render_nba_court(away, home, away_score, home_score, period, clock, last_play):
    ac, hc = TEAM_COLORS.get(away, "#888"), TEAM_COLORS.get(home, "#888")
    aa, ha_a = KALSHI_CODES.get(away, away[:3].upper()), KALSHI_CODES.get(home, home[:3].upper())
    pt = ""
    if period > 0 and period <= 4: pt = "Q" + str(period)
    elif period > 4: pt = "OT" + str(period - 4)
    badge = get_play_badge(last_play)
    h = MOBILE_CSS
    h += '<div style="background:#1a1a2e;border-radius:12px;padding:12px;text-align:center;max-width:100%;box-sizing:border-box;overflow-x:hidden">'
    h += '<svg viewBox="0 0 500 280" style="width:100%;max-width:500px">'
    h += '<rect x="20" y="20" width="460" height="200" fill="#2d4a22" stroke="white" stroke-width="2" rx="8"/>'
    h += '<circle cx="250" cy="120" r="35" fill="none" stroke="white" stroke-width="1.5"/>'
    h += '<circle cx="250" cy="120" r="4" fill="white"/>'
    h += '<line x1="250" y1="20" x2="250" y2="220" stroke="white" stroke-width="1.5"/>'
    h += '<path d="M 20 50 Q 100 120 20 190" fill="none" stroke="white" stroke-width="1.5"/>'
    h += '<rect x="20" y="70" width="70" height="100" fill="none" stroke="white" stroke-width="1.5"/>'
    h += '<circle cx="90" cy="120" r="25" fill="none" stroke="white" stroke-width="1" stroke-dasharray="4,4"/>'
    h += '<circle cx="35" cy="120" r="8" fill="none" stroke="#ff6b35" stroke-width="3"/>'
    h += '<path d="M 480 50 Q 400 120 480 190" fill="none" stroke="white" stroke-width="1.5"/>'
    h += '<rect x="410" y="70" width="70" height="100" fill="none" stroke="white" stroke-width="1.5"/>'
    h += '<circle cx="410" cy="120" r="25" fill="none" stroke="white" stroke-width="1" stroke-dasharray="4,4"/>'
    h += '<circle cx="465" cy="120" r="8" fill="none" stroke="#ff6b35" stroke-width="3"/>'
    h += badge
    h += '<rect x="40" y="228" width="90" height="48" rx="8" fill="' + ac + '"/>'
    h += '<text x="85" y="250" text-anchor="middle" fill="white" font-size="14" font-weight="bold">' + aa + '</text>'
    h += '<text x="85" y="270" text-anchor="middle" fill="white" font-size="18" font-weight="bold">' + str(away_score) + '</text>'
    h += '<rect x="370" y="228" width="90" height="48" rx="8" fill="' + hc + '"/>'
    h += '<text x="415" y="250" text-anchor="middle" fill="white" font-size="14" font-weight="bold">' + ha_a + '</text>'
    h += '<text x="415" y="270" text-anchor="middle" fill="white" font-size="18" font-weight="bold">' + str(home_score) + '</text>'
    h += '<text x="250" y="258" text-anchor="middle" fill="#ccc" font-size="14">' + pt + ' ' + clock + '</text>'
    h += '</svg></div>'
    components.html(h, height=320)

def get_play_icon(play_type, score_value):
    pt = (play_type or "").lower()
    if score_value and score_value > 0: return ("B", "#22c55e")
    if "miss" in pt: return ("X", "#ef4444")
    if "rebound" in pt: return ("R", "#3b82f6")
    if "turnover" in pt or "steal" in pt: return ("T", "#f97316")
    if "foul" in pt: return ("F", "#eab308")
    if "timeout" in pt: return ("TO", "#a855f7")
    return ("-", "#888")

@st.cache_data(ttl=30)
def fetch_all_plays_wnba(game_id):
    try:
        url = "https://site.api.espn.com/apis/site/v2/sports/basketball/wnba/summary?event=" + str(game_id)
        data = requests.get(url, timeout=10).json()
        plays_raw = []
        for drive in data.get("plays", []):
            if isinstance(drive, dict): plays_raw.append(drive)
            elif isinstance(drive, list): plays_raw.extend(drive)
        return plays_raw
    except: return []

def calc_tiebreaker_stats(plays, home, away, home_id="", away_id=""):
    home_data = {"name": home, "turnovers": 0, "steals": 0, "rebounds": 0, "assists": 0, "made_fg": 0, "by_quarter": {}}
    away_data = {"name": away, "turnovers": 0, "steals": 0, "rebounds": 0, "assists": 0, "made_fg": 0, "by_quarter": {}}
    home_lower, away_lower = home.lower(), away.lower()
    home_code, away_code = KALSHI_CODES.get(home, "").lower(), KALSHI_CODES.get(away, "").lower()
    home_words = [w.lower() for w in home.split() if len(w) > 3]
    away_words = [w.lower() for w in away.split() if len(w) > 3]
    for p in plays:
        text = p.get("text", "") or ""
        text_lower = text.lower()
        period_raw = p.get("period", {})
        period_num = period_raw.get("number", 0) if isinstance(period_raw, dict) else (period_raw or 0)
        q_label = ("Q" + str(period_num)) if period_num <= 4 else ("OT" + str(period_num - 4))
        play_team = None
        espn_tid = str(p.get("team", {}).get("id", "")) if isinstance(p.get("team"), dict) else ""
        ha_field = p.get("homeAway", "")
        if espn_tid and home_id and espn_tid == str(home_id): play_team = "home"
        elif espn_tid and away_id and espn_tid == str(away_id): play_team = "away"
        elif ha_field == "home": play_team = "home"
        elif ha_field == "away": play_team = "away"
        else:
            if home_lower in text_lower or home_code in text_lower: play_team = "home"
            elif away_lower in text_lower or away_code in text_lower: play_team = "away"
            else:
                for hw in home_words:
                    if hw in text_lower: play_team = "home"; break
                if not play_team:
                    for aw in away_words:
                        if aw in text_lower: play_team = "away"; break
        if not play_team: continue
        acting = home_data if play_team == "home" else away_data
        other = away_data if play_team == "home" else home_data
        if q_label not in acting["by_quarter"]: acting["by_quarter"][q_label] = {"turnovers": 0, "steals": 0, "rebounds": 0, "assists": 0}
        if q_label not in other["by_quarter"]: other["by_quarter"][q_label] = {"turnovers": 0, "steals": 0, "rebounds": 0, "assists": 0}
        if "turnover" in text_lower:
            acting["turnovers"] += 1; acting["by_quarter"][q_label]["turnovers"] += 1
            other["steals"] += 1; other["by_quarter"][q_label]["steals"] += 1
        elif "steal" in text_lower:
            other["steals"] += 1; other["by_quarter"][q_label]["steals"] += 1
        if "rebound" in text_lower: acting["rebounds"] += 1; acting["by_quarter"][q_label]["rebounds"] += 1
        if "assist" in text_lower: acting["assists"] += 1; acting["by_quarter"][q_label]["assists"] += 1
        if "made" in text_lower: acting["made_fg"] += 1
    return {"home": home_data, "away": away_data}

def render_tiebreaker_panel(stats, home, away):
    h_d, a_d = stats.get("home", {}), stats.get("away", {})
    ha = KALSHI_CODES.get(home, home[:3].upper())
    aa = KALSHI_CODES.get(away, away[:3].upper())
    he, ae = 0, 0
    if h_d.get("turnovers", 0) < a_d.get("turnovers", 0): he += 1
    elif a_d.get("turnovers", 0) < h_d.get("turnovers", 0): ae += 1
    if h_d.get("steals", 0) > a_d.get("steals", 0): he += 1
    elif a_d.get("steals", 0) > h_d.get("steals", 0): ae += 1
    if h_d.get("rebounds", 0) > a_d.get("rebounds", 0): he += 1
    elif a_d.get("rebounds", 0) > h_d.get("rebounds", 0): ae += 1
    if h_d.get("assists", 0) > a_d.get("assists", 0): he += 1
    elif a_d.get("assists", 0) > h_d.get("assists", 0): ae += 1
    def _row(label, av, hv, lower_better=False):
        r = '<tr>'
        r += '<td style="color:#ccc;padding:4px 6px;font-size:clamp(11px,2.5vw,13px)">' + label + '</td>'
        if lower_better: a_win = av < hv; h_win = hv < av
        else: a_win = av > hv; h_win = hv > av
        a_c = "#00ff88" if a_win else ("#ff4444" if h_win else "#888")
        h_c = "#00ff88" if h_win else ("#ff4444" if a_win else "#888")
        am = " &#10004;" if a_win else ""
        hm = " &#10004;" if h_win else ""
        r += '<td style="color:' + a_c + ';text-align:center;padding:4px 6px;font-size:clamp(11px,2.5vw,13px)">' + str(av) + am + '</td>'
        r += '<td style="color:' + h_c + ';text-align:center;padding:4px 6px;font-size:clamp(11px,2.5vw,13px)">' + str(hv) + hm + '</td></tr>'
        return r
    o = '<div style="border:2px solid #f0c040;border-radius:10px;background:linear-gradient(135deg,#1a1a2e,#16213e);'
    o += 'padding:clamp(10px,2vw,16px);margin-top:10px;margin-bottom:10px;max-width:100%;box-sizing:border-box;overflow-x:hidden">'
    o += '<div style="text-align:center;color:#f0c040;font-weight:bold;font-size:clamp(13px,3vw,16px);margin-bottom:8px">'
    o += '&#9878; TIEBREAKER PANEL (game within 5 pts)</div>'
    o += '<table style="width:100%;table-layout:fixed;border-collapse:collapse">'
    o += '<tr style="border-bottom:1px solid #334155">'
    o += '<td style="color:#94a3b8;padding:4px 6px;font-weight:bold;font-size:clamp(11px,2.5vw,13px)">Stat</td>'
    o += '<td style="color:#94a3b8;padding:4px 6px;text-align:center;font-weight:bold;font-size:clamp(11px,2.5vw,13px)">' + aa + '</td>'
    o += '<td style="color:#94a3b8;padding:4px 6px;text-align:center;font-weight:bold;font-size:clamp(11px,2.5vw,13px)">' + ha + '</td></tr>'
    o += _row("Turnovers", a_d.get("turnovers", 0), h_d.get("turnovers", 0), lower_better=True)
    o += _row("Steals", a_d.get("steals", 0), h_d.get("steals", 0))
    o += _row("Rebounds", a_d.get("rebounds", 0), h_d.get("rebounds", 0))
    o += _row("Assists", a_d.get("assists", 0), h_d.get("assists", 0))
    all_qs = sorted(set(list(h_d.get("by_quarter", {}).keys()) + list(a_d.get("by_quarter", {}).keys())))
    for q in all_qs:
        hq = h_d.get("by_quarter", {}).get(q, {})
        aq = a_d.get("by_quarter", {}).get(q, {})
        o += _row("TO in " + q, aq.get("turnovers", 0), hq.get("turnovers", 0), lower_better=True)
    o += '</table>'
    if he > ae:
        o += '<div style="text-align:center;color:#00ff88;font-weight:bold;font-size:clamp(12px,3vw,15px);margin-top:8px">'
        o += 'Lean ' + ha + ' (' + str(he) + '-' + str(ae) + ' on tiebreakers)</div>'
    elif ae > he:
        o += '<div style="text-align:center;color:#00ff88;font-weight:bold;font-size:clamp(12px,3vw,15px);margin-top:8px">'
        o += 'Lean ' + aa + ' (' + str(ae) + '-' + str(he) + ' on tiebreakers)</div>'
    else:
        o += '<div style="text-align:center;color:#f0c040;font-weight:bold;font-size:clamp(12px,3vw,15px);margin-top:8px">'
        o += 'Even ' + str(he) + '-' + str(ae) + ' &#8212; true coin flip</div>'
    o += '</div>'
    return o

# ── Data Fetch Calls ──
games = fetch_espn_games_wnba()
kalshi_ml_data = fetch_kalshi_ml_wnba()
kalshi_spreads_parsed, kalshi_spread_list = fetch_kalshi_spreads_raw_wnba()
injuries = fetch_injuries_wnba()
b2b_teams = fetch_yesterday_teams_wnba()

live_games = [g for g in games if g.get('status') in ['STATUS_IN_PROGRESS', 'STATUS_HALFTIME', 'STATUS_END_PERIOD'] or (g.get('period', 0) > 0 and g.get('status') not in ['STATUS_FINAL', 'STATUS_FULL_TIME'])]
scheduled_games = [g for g in games if g.get('status') == 'STATUS_SCHEDULED' and g.get('period', 0) == 0]
final_games = [g for g in games if g.get('status') in ['STATUS_FINAL', 'STATUS_FULL_TIME']]

for g in live_games:
    sniper_result = check_spread_sniper(g, kalshi_spread_list, kalshi_ml_data)
    if sniper_result: st.session_state.sniper_alerts.append(sniper_result)
    comeback_result = check_comeback(g, kalshi_ml_data)
    if comeback_result: st.session_state.comeback_alerts.append(comeback_result)

st.title("BIGSNAPSHOT WNBA EDGE FINDER")
st.caption("v" + VERSION + " | " + now.strftime('%A, %B %d %Y %-I:%M %p ET') + " | 9-Factor Edge + Spread Sniper + Comeback Scanner")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Today's Games", len(games))
c2.metric("Live Now", len(live_games))
c3.metric("Scheduled", len(scheduled_games))
c4.metric("Final", len(final_games))
st.divider()

st.subheader("PACE SCANNER")
pace_data = []
for g in live_games:
    if g.get('minutes_played', 0) >= 6:
        ts = g.get('total_score', 0)
        mp = g.get('minutes_played', 0)
        pace = round(ts / mp, 2) if mp > 0 else 0
        plabel, pcolor = get_pace_label(pace)
        proj = calc_projection(ts, mp)
        pace_data.append({"name": g.get('away', '') + " @ " + g.get('home', ''),
            "status": ("Q" + str(g.get('period', 0)) + " " + g.get('clock', '')) if g.get('period', 0) <= 4 else ("OT" + str(g.get('period', 0) - 4) + " " + g.get('clock', '')),
            "total": ts, "pace": pace, "pace_label": plabel, "pace_color": pcolor, "proj": proj})
pace_data.sort(key=lambda x: x['pace'])
if pace_data:
    for pd_item in pace_data:
        pc1, pc2, pc3, pc4 = st.columns(4)
        pc1.markdown("**" + pd_item['name'] + "**")
        pc2.markdown(pd_item['status'] + " | " + str(pd_item['total']) + " pts")
        pc3.markdown("<span style='color:" + pd_item['pace_color'] + "'>" + pd_item['pace_label'] + " (" + str(round(pd_item['pace'], 2)) + ")</span>", unsafe_allow_html=True)
        pc4.markdown("Proj: **" + str(pd_item['proj']) + "**")
else: st.info("No live games with 6+ minutes played")
st.divider()

tab_edge, tab_spread, tab_live, tab_cushion = st.tabs(["Edge Finder", "Spread Sniper", "Live Monitor", "Cushion Scanner"])

# ════════════════════════════════════════════════
# TAB 1: EDGE FINDER
# ════════════════════════════════════════════════
with tab_edge:
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
        summary = fetch_game_summary_wnba(g.get('game_id'))
        edge = calc_advanced_edge(g, b2b_teams, summary=summary, injuries=injuries)
        if edge.get('strength') in ['🔴 STRONG', '🟡 MODERATE']:
            edge_results.append({"game": g, "edge": edge, "summary": summary})
    edge_results.sort(key=lambda x: (0 if 'STRONG' in x['edge'].get('strength', '') else 1, -abs(x['edge'].get('score', 0))))

    if not edge_results:
        st.info("No STRONG or MODERATE edges found in today's scheduled games.")
    else:
        st.markdown("**" + str(len(edge_results)) + " actionable edge(s) found**")
        if st.button("ADD ALL EDGE PICKS", key="add_all_edges", use_container_width=True):
            for er in edge_results:
                g = er['game']
                e = er['edge']
                st.session_state.positions.append({
                    'id': str(uuid.uuid4()), 'game': g['away'] + " @ " + g['home'],
                    'pick': e['pick'], 'type': 'ML', 'line': '-',
                    'entry': 50, 'contracts': 10, 'away': g['away'], 'home': g['home'],
                    'game_id': g['game_id']})
            st.rerun()

        for er in edge_results:
            g = er['game']
            e = er['edge']
            border_color = "#22c55e" if "STRONG" in e.get('strength', '') else "#f97316"
            spread_str = g.get('vegas_odds', {}).get('spread', 'N/A')
            ou_str = g.get('vegas_odds', {}).get('overUnder', 'N/A')
            h = '<div style="border-left:4px solid ' + border_color + ';background:#1a1a2e;padding:clamp(8px,2vw,16px);border-radius:8px;margin-bottom:8px;max-width:100%;box-sizing:border-box;overflow-x:hidden">'
            h += '<span style="background:' + border_color + ';color:white;padding:2px 8px;border-radius:4px;font-size:clamp(11px,2.5vw,14px);font-weight:bold">' + e.get('strength', '') + '</span>'
            h += '<span style="color:white;font-size:clamp(14px,3.5vw,18px);font-weight:bold;margin-left:8px">' + g['away'] + ' @ ' + g['home'] + '</span><br>'
            h += '<span style="color:#94a3b8;font-size:clamp(11px,2.5vw,14px)">Spread: ' + str(spread_str) + ' | O/U: ' + str(ou_str) + ' | ' + g.get('game_time', '') + '</span><br>'
            h += '<span style="color:#fbbf24;font-size:clamp(14px,3.5vw,18px);font-weight:bold">PICK: ' + e['pick'] + ' (' + ("+" if e['score'] >= 0 else "") + str(e['score']) + ')</span></div>'
            st.markdown(h, unsafe_allow_html=True)
            ec1, ec2 = st.columns(2)
            with ec1:
                link = get_kalshi_game_link(g['away'], g['home'])
                st.link_button("Trade on Kalshi", link, use_container_width=True)
            with ec2:
                already = any(p.get('game_id') == g.get('game_id') for p in st.session_state.positions)
                if already: st.success("Tracked ✓")
                else:
                    if st.button("Track", key="track_" + g.get('game_id', ''), use_container_width=True):
                        st.session_state.positions.append({
                            'id': str(uuid.uuid4()), 'game': g['away'] + " @ " + g['home'],
                            'pick': e['pick'], 'type': 'ML', 'line': '-',
                            'entry': 50, 'contracts': 10, 'away': g['away'], 'home': g['home'],
                            'game_id': g['game_id']})
                        st.rerun()
            with st.expander("View Breakdown"):
                for edge_item in e.get('edges', []):
                    val = edge_item.get('value', 0)
                    fname = edge_item.get('factor', '')
                    detail = edge_item.get('detail', '')
                    if "injur" in fname.lower() and ("star" in detail.lower() or "out" in detail.lower()): color, prefix = "#e74c3c", "🔴 "
                    elif "3pt" in fname.lower(): color, prefix = "#3498db", "🔵 "
                    elif "gap" in fname.lower(): color, prefix = "#2ecc71", "🟢 "
                    elif "fatigue" in fname.lower() or "b2b" in fname.lower(): color, prefix = "#e67e22", "🟠 "
                    else: color, prefix = "#ccc", "- "
                    st.markdown("<span style='color:" + color + "'>" + prefix + fname + ": " + ("+" if val >= 0 else "") + str(val) + " — " + detail + "</span>", unsafe_allow_html=True)
            st.divider()

    # Section B: Vegas vs Kalshi Mispricing Alert
    st.subheader("VEGAS vs KALSHI MISPRICING ALERT")
    st.caption("Comparing Vegas implied probabilities to Kalshi prices — edges ≥5% shown")
    mispricing_list = []
    for g in games:
        if g.get('status') in ['STATUS_FINAL', 'STATUS_FULL_TIME']: continue
        key = g.get('away', '') + "@" + g.get('home', '')
        home_ml = g.get('home_ml', 0)
        away_ml = g.get('vegas_odds', {}).get('awayML', 0)
        vegas_home_pct, vegas_away_pct = None, None
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
            except: continue
        else: continue
        kalshi_info = kalshi_ml_data.get(key, {})
        kalshi_home = kalshi_info.get('home_implied', 0)
        kalshi_away = kalshi_info.get('away_implied', 0)
        if not kalshi_home and not kalshi_away: continue
        summary_mp = fetch_game_summary_wnba(g.get('game_id'))
        bpi_home_pct, bpi_away_pct = 0.5, 0.5
        if summary_mp: bpi_home_pct, bpi_away_pct = parse_predictor(summary_mp)
        home_gap = vegas_home_pct - kalshi_home if kalshi_home else 0
        away_gap = vegas_away_pct - kalshi_away if kalshi_away else 0
        if abs(home_gap) >= 5:
            side_label = "HOME" if home_gap > 0 else "AWAY"
            buy_action = "YES" if home_gap > 0 else "NO"
            team_pick = g['home'] if home_gap > 0 else g['away']
            mispricing_list.append({"game": g, "key": key, "edge": abs(home_gap),
                "vegas_pct": vegas_home_pct if home_gap > 0 else vegas_away_pct,
                "kalshi_price": kalshi_home if home_gap > 0 else kalshi_away,
                "bpi_pct": round(bpi_home_pct * 100, 1) if home_gap > 0 else round(bpi_away_pct * 100, 1),
                "buy_action": buy_action, "team": team_pick, "side": side_label,
                "ticker": kalshi_info.get('ticker', '')})
        elif abs(away_gap) >= 5:
            side_label = "AWAY" if away_gap > 0 else "HOME"
            buy_action = "YES" if away_gap > 0 else "NO"
            team_pick = g['away'] if away_gap > 0 else g['home']
            mispricing_list.append({"game": g, "key": key, "edge": abs(away_gap),
                "vegas_pct": vegas_away_pct if away_gap > 0 else vegas_home_pct,
                "kalshi_price": kalshi_away if away_gap > 0 else kalshi_home,
                "bpi_pct": round(bpi_away_pct * 100, 1) if away_gap > 0 else round(bpi_home_pct * 100, 1),
                "buy_action": buy_action, "team": team_pick, "side": side_label,
                "ticker": kalshi_info.get('ticker', '')})
    mispricing_list.sort(key=lambda x: x.get('edge', 0), reverse=True)
    if not mispricing_list:
        st.info("No mispricings ≥5% detected right now.")
    else:
        for mp in mispricing_list:
            g = mp['game']
            edge_val = mp.get('edge', 0)
            if edge_val >= 10: edge_color, edge_tag = "#ff6b6b", "STRONG"
            elif edge_val >= 7: edge_color, edge_tag = "#22c55e", "GOOD"
            else: edge_color, edge_tag = "#eab308", "EDGE"
            action_color = "#22c55e" if mp.get('buy_action') == "YES" else "#ef4444"
            status_text = ("Q" + str(g.get('period', 0)) + " " + g.get('clock', '')) if g.get('state') == 'in' else g.get('game_time', 'Scheduled')
            h = '<div style="background:#1a1a2e;padding:clamp(8px,2vw,16px);border-radius:8px;border-left:4px solid ' + edge_color + ';margin-bottom:8px;max-width:100%;box-sizing:border-box;overflow-x:hidden">'
            h += '<div style="color:white;font-size:clamp(14px,3.5vw,18px);font-weight:bold;word-wrap:break-word">' + g.get('away', '') + ' @ ' + g.get('home', '') + ' <span style="color:#94a3b8;font-size:clamp(11px,2.5vw,14px)">' + status_text + '</span></div>'
            h += '<div style="margin-top:6px">'
            h += '<span style="background:' + action_color + ';color:white;padding:2px 8px;border-radius:4px;font-weight:bold;font-size:clamp(11px,2.5vw,14px)">BUY ' + mp.get('buy_action', '') + ' ' + mp.get('team', '') + '</span>'
            h += '<span style="background:' + edge_color + ';color:white;padding:2px 8px;border-radius:4px;font-weight:bold;margin-left:4px;font-size:clamp(11px,2.5vw,14px)">' + edge_tag + ' +' + str(round(edge_val, 1)) + '%</span></div>'
            h += '<table style="width:100%;table-layout:fixed;margin-top:8px;color:#ccc;font-size:clamp(11px,2.5vw,14px)">'
            h += '<tr><td>Vegas</td><td>Kalshi</td><td>BPI</td><td>Edge</td></tr>'
            h += '<tr style="color:white;font-weight:bold"><td>' + str(mp.get('vegas_pct', 0)) + '%</td><td>' + str(mp.get('kalshi_price', 0)) + '¢</td><td>' + str(mp.get('bpi_pct', 0)) + '%</td><td style="color:' + edge_color + '">+' + str(round(edge_val, 1)) + '%</td></tr>'
            h += '</table></div>'
            st.markdown(h, unsafe_allow_html=True)
            link = get_kalshi_game_link(g.get('away', ''), g.get('home', ''))
            st.link_button("Trade " + mp.get('team', '') + " on Kalshi", link, use_container_width=True)

    # Section C: Injury Report
    st.subheader("INJURY REPORT")
    today_teams = set()
    for g in games:
        today_teams.add(g.get('away', ''))
        today_teams.add(g.get('home', ''))
    has_injuries = False
    for team in sorted(today_teams):
        team_inj = injuries.get(team, [])
        if not team_inj: continue
        out_players = [i for i in team_inj if 'out' in (i.get('status', '') or '').lower()]
        dtd_players = [i for i in team_inj if 'day' in (i.get('status', '') or '').lower() or 'doubtful' in (i.get('status', '') or '').lower()]
        if out_players or dtd_players:
            has_injuries = True
            for p in out_players: st.markdown("**" + team + "** [OUT] " + p.get('name', '') + " — " + p.get('status', ''))
            for p in dtd_players: st.markdown("**" + team + "** [DTD] " + p.get('name', '') + " — " + p.get('status', ''))
    if not has_injuries: st.info("No significant injuries reported for today's games.")

    # Section D: Position Tracker
    st.subheader("POSITION TRACKER")
    with st.expander("ADD NEW POSITION", expanded=False):
        game_options = [g.get('away', '') + " @ " + g.get('home', '') for g in games]
        if game_options:
            pt1, pt2 = st.columns(2)
            with pt1: sel_game = st.selectbox("Game", game_options, key="pos_game")
            with pt2: bet_type = st.selectbox("Bet Type", ["ML", "Totals", "Spread"], key="pos_type")
            matched_game = next((g for g in games if g.get('away', '') + " @ " + g.get('home', '') == sel_game), None)
            pt3, pt4 = st.columns(2)
            with pt3:
                if bet_type == "ML":
                    pick_opts = [matched_game.get('away', ''), matched_game.get('home', '')] if matched_game else ["Team A", "Team B"]
                    pick = st.selectbox("Pick", pick_opts, key="pos_pick")
                elif bet_type == "Totals": pick = st.selectbox("Pick", ["YES (Over)", "NO (Under)"], key="pos_pick")
                else:
                    pick_opts = [matched_game.get('away', ''), matched_game.get('home', '')] if matched_game else ["Team A", "Team B"]
                    pick = st.selectbox("Pick", pick_opts, key="pos_pick")
            with pt4:
                if bet_type == "Totals": line = st.selectbox("Line", [str(t) for t in THRESHOLDS], key="pos_line")
                elif bet_type == "Spread": line = st.selectbox("Line", ["3.5", "5.5", "7.5", "10.5", "13.5", "15.5"], key="pos_line")
                else: line = "-"; st.text_input("Line", value="-", disabled=True, key="pos_line_ml")
            pt5, pt6 = st.columns(2)
            with pt5: entry = st.number_input("Entry Price (¢)", min_value=1, max_value=99, value=50, key="pos_entry")
            with pt6: contracts = st.number_input("Contracts", min_value=1, max_value=10000, value=10, key="pos_contracts")
            cost = round(entry * contracts / 100, 2)
            win = round((100 - entry) * contracts / 100, 2)
            st.caption("Cost: $" + str(cost) + " | Win: $" + str(win))
            if st.button("ADD POSITION", key="add_pos", use_container_width=True):
                st.session_state.positions.append({
                    'id': str(uuid.uuid4()), 'game': sel_game,
                    'pick': pick, 'type': bet_type, 'line': line if bet_type != "ML" else "-",
                    'entry': entry, 'contracts': contracts,
                    'away': matched_game.get('away', '') if matched_game else "",
                    'home': matched_game.get('home', '') if matched_game else "",
                    'game_id': matched_game.get('game_id', '') if matched_game else ""})
                st.rerun()
        else: st.info("No games available to track.")

    if st.session_state.positions:
        for pos in st.session_state.positions:
            p1, p2, p3, p4, p5 = st.columns([3, 2, 2, 2, 1])
            with p1:
                st.markdown("**" + pos.get('game', '') + "**")
                mg = next((g for g in games if g.get('game_id') == pos.get('game_id')), None)
                if mg and mg.get('state') == 'in':
                    st.caption("LIVE Q" + str(mg.get('period', 0)) + " " + mg.get('clock', '') + " | " + str(mg.get('away_score', 0)) + "-" + str(mg.get('home_score', 0)))
            with p2:
                line_str = " " + str(pos.get('line', '')) if pos.get('line') != "-" else ""
                st.markdown(str(pos.get('pick', '')) + " " + str(pos.get('type', '')) + line_str)
            with p3:
                cost = round(pos.get('entry', 0) * pos.get('contracts', 0) / 100, 2)
                st.markdown(str(pos.get('contracts', 0)) + "x @ " + str(pos.get('entry', 0)) + "¢")
                st.caption("$" + str(cost))
            with p4:
                link = get_kalshi_game_link(pos.get('away', ''), pos.get('home', ''))
                st.link_button("Kalshi", link, use_container_width=True)
            with p5:
                if st.button("X", key="del_" + pos.get('id', ''), use_container_width=True):
                    remove_position(pos.get('id'))
                    st.rerun()
        if st.button("CLEAR ALL POSITIONS", key="clear_all_pos", use_container_width=True):
            st.session_state.positions = []
            st.rerun()
    else: st.caption("No positions tracked yet.")

    # Section E: All Games Today
    st.subheader("ALL GAMES TODAY")
    for g in games:
        if g.get('status') in ['STATUS_FINAL', 'STATUS_FULL_TIME']:
            border = "#666"
            info_str = "FINAL: " + str(g.get('away_score', 0)) + "-" + str(g.get('home_score', 0))
        elif g.get('state') == 'in':
            border = "#22c55e"
            ptext = "Q" + str(g.get('period', 0)) if g.get('period', 0) <= 4 else "OT" + str(g.get('period', 0) - 4)
            info_str = "LIVE " + ptext + " " + g.get('clock', '') + " | " + str(g.get('away_score', 0)) + "-" + str(g.get('home_score', 0))
        else:
            border = "#888"
            info_str = g.get('game_datetime', '') + " | " + str(g.get('vegas_odds', {}).get('spread', ''))
        h = '<div style="border-left:4px solid ' + border + ';padding:clamp(6px,2vw,12px);margin-bottom:4px;max-width:100%;box-sizing:border-box;overflow-x:hidden">'
        h += '<span style="color:white;font-size:clamp(13px,3vw,16px);font-weight:bold;word-wrap:break-word">' + g.get('away', '') + ' @ ' + g.get('home', '') + '</span>'
        h += '<span style="color:#94a3b8;font-size:clamp(11px,2.5vw,14px);margin-left:8px">' + info_str + '</span></div>'
        st.markdown(h, unsafe_allow_html=True)

# ════════════════════════════════════════════════
# TAB 2: SPREAD SNIPER
# ════════════════════════════════════════════════
with tab_spread:
    st.subheader("SPREAD SNIPER — LIVE ALERTS")
    with st.expander("How Spread Sniping Works"):
        st.markdown("""
**Strategy:** When the underdog builds a big lead, the favorite's spread markets become cheap. We buy NO on large spreads, betting the favorite won't win by that much (because they're currently losing).

**Quarter Thresholds (underdog lead required to fire):**
| Quarter | Lead Required |
|---------|--------------|
| Q1 | 5+ points |
| Q2 | 6+ points |
| Q3 | 8+ points |
| Q4 | 10+ points |

**Bracket Rating:**
| NO Price | Rating |
|----------|--------|
| ≤ 40¢ | 🔥 FIRE |
| 41-60¢ | ✅ GOOD |
| 61-75¢ | ⚠️ OK |
| 76-85¢ | 🟠 WARN |
""")
    st.caption("Scanning live games for underdog leads meeting quarter thresholds")

    if st.session_state.sniper_alerts:
        for alert in st.session_state.sniper_alerts:
            ag = alert.get('game', {})
            ptext = "Q" + str(ag.get('period', 0)) if ag.get('period', 0) <= 4 else "OT" + str(ag.get('period', 0) - 4)
            h = '<div style="border-left:4px solid #ef4444;background:#1a1a2e;padding:clamp(8px,2vw,16px);border-radius:8px;margin-bottom:8px;max-width:100%;box-sizing:border-box;overflow-x:hidden" class="alert-box">'
            h += '<div style="color:#ef4444;font-size:clamp(16px,4vw,22px);font-weight:bold">🎯 SPREAD SNIPER — ' + ptext + ' ' + ag.get('clock', '') + '</div>'
            h += '<div style="color:white;font-size:clamp(14px,3.5vw,18px);margin-top:4px">' + ag.get('away', '') + ' ' + str(ag.get('away_score', 0)) + ' — ' + ag.get('home', '') + ' ' + str(ag.get('home_score', 0)) + '</div>'
            h += '<div style="color:#fbbf24;font-size:clamp(12px,3vw,16px);margin-top:4px">' + alert.get('dog_name', '') + ' (' + alert.get('dog_abbrev', '') + ') leads by ' + str(alert.get('dog_lead', 0)) + ' | Record: ' + alert.get('dog_record', '') + '</div>'
            h += '<div style="color:#94a3b8;font-size:clamp(11px,2.5vw,14px)">Favorite: ' + alert.get('fav_name', '') + ' (' + alert.get('fav_abbrev', '') + ') | Record: ' + alert.get('fav_record', '') + '</div></div>'
            st.markdown(h, unsafe_allow_html=True)
            if alert.get('no_markets'): st.warning("No spread markets found — check Kalshi manually")
            elif not alert.get('spreads'): st.info("All bracket NO prices exceed " + str(MAX_NO_PRICE) + "¢ ceiling")
            else:
                st.markdown("**ACTIONABLE BRACKETS:**")
                best = None
                for sp in alert.get('spreads', []):
                    no_price = sp.get('effective_no_price', sp.get('no_price', 0))
                    swing = sp.get('spread_val', 0) + alert.get('dog_lead', 0)
                    if no_price <= 40: tag, tcolor = "🔥 FIRE", "#ef4444"
                    elif no_price <= 60: tag, tcolor = "✅ GOOD", "#22c55e"
                    elif no_price <= 75: tag, tcolor = "⚠️ OK", "#eab308"
                    else: tag, tcolor = "🟠 WARN", "#f97316"
                    bh = '<div style="background:#0f172a;padding:clamp(6px,2vw,12px);border-radius:6px;margin-bottom:4px;max-width:100%;box-sizing:border-box;overflow-x:hidden">'
                    bh += '<span style="background:' + tcolor + ';color:white;padding:2px 6px;border-radius:4px;font-size:clamp(10px,2vw,13px);font-weight:bold">' + tag + '</span>'
                    bh += '<span style="color:white;font-size:clamp(12px,3vw,15px);margin-left:6px;word-wrap:break-word">' + sp.get('title', '') + ' | NO: ' + str(no_price) + '¢ | Swing: ' + str(round(swing)) + '</span></div>'
                    st.markdown(bh, unsafe_allow_html=True)
                    if best is None or no_price < best.get('no_price', 999):
                        best = {'title': sp.get('title', ''), 'no_price': no_price, 'spread_val': sp.get('spread_val', 0)}
                if best:
                    bh2 = '<div style="border-left:4px solid #22c55e;background:#0f2a1a;padding:clamp(8px,2vw,12px);border-radius:8px;margin-top:8px;max-width:100%;box-sizing:border-box;overflow-x:hidden">'
                    bh2 += '<span style="color:#22c55e;font-weight:bold;font-size:clamp(12px,3vw,16px)">BEST BET: ' + best['title'] + ' — NO @ ' + str(best['no_price']) + '¢</span></div>'
                    st.markdown(bh2, unsafe_allow_html=True)
            link = get_kalshi_spread_link(ag.get('away', ''), ag.get('home', ''))
            st.link_button("Trade Spread on Kalshi", link, use_container_width=True)
            st.divider()
    else: st.info("No spread sniper alerts yet — scanning every 24 seconds...")

    # Section B: Comeback Scanner
    st.subheader("COMEBACK SCANNER")
    st.caption("Tracking favorites who fall behind by 10+ points — fires when they close within 2")
    if st.session_state.comeback_tracking:
        st.markdown("**Currently Tracking:**")
        for gid, ct in st.session_state.comeback_tracking.items():
            mg = next((g for g in live_games if g.get('game_id') == gid), None)
            if not mg: continue
            fav_side = ct.get('fav_side', 'home')
            fav_name = mg.get('home') if fav_side == 'home' else mg.get('away')
            fav_abbrev = KALSHI_CODES.get(fav_name, (fav_name or "")[:3].upper())
            fav_score = mg.get('home_score', 0) if fav_side == 'home' else mg.get('away_score', 0)
            opp_score = mg.get('away_score', 0) if fav_side == 'home' else mg.get('home_score', 0)
            margin = fav_score - opp_score
            if margin > 0: status_str = "leads by " + str(margin)
            elif margin == 0: status_str = "TIED"
            else: status_str = "down " + str(abs(margin))
            color = "#22c55e" if margin >= 0 else "#eab308"
            fired = " 🔔 FIRED" if gid in st.session_state.comeback_alerted else ""
            st.markdown("<span style='color:" + color + "'>" + fav_abbrev + " — was down " + str(ct.get('max_deficit', 0)) + ", now " + status_str + fired + "</span>", unsafe_allow_html=True)

    if st.session_state.comeback_alerts:
        for ca in st.session_state.comeback_alerts:
            cg = ca.get('game', {})
            ptext = "Q" + str(cg.get('period', 0)) if cg.get('period', 0) <= 4 else "OT" + str(cg.get('period', 0) - 4)
            margin = ca.get('fav_margin', 0)
            if margin > 0: status_word = "NOW LEADS BY " + str(margin)
            elif margin == 0: status_word = "NOW TIED"
            else: status_word = "CLOSING IN (down " + str(abs(margin)) + ")"
            price = ca.get('fav_price')
            price_str = ""
            if price:
                if price <= 55: price_str = "<span style='color:#ef4444;font-weight:bold'>Kalshi ML: " + str(price) + "¢ — MARKET LAGGING!</span>"
                elif price <= 70: price_str = "<span style='color:#eab308;font-weight:bold'>Kalshi ML: " + str(price) + "¢</span>"
                else: price_str = "<span style='color:#ccc'>Kalshi ML: " + str(price) + "¢</span>"
            wp_str = ""
            if ca.get('fav_wp'): wp_str = "<div style='color:#22c55e;font-size:clamp(11px,2.5vw,14px)'>ESPN WP: " + str(round(ca['fav_wp'])) + "%</div>"
            ch = '<div style="border-left:4px solid #22c55e;background:#1a1a2e;padding:clamp(8px,2vw,16px);border-radius:8px;margin-bottom:8px;max-width:100%;box-sizing:border-box;overflow-x:hidden" class="alert-box">'
            ch += '<div style="color:#22c55e;font-size:clamp(16px,4vw,22px);font-weight:bold">🔄 COMEBACK — ' + ptext + ' ' + cg.get('clock', '') + '</div>'
            ch += '<div style="color:white;font-size:clamp(14px,3.5vw,18px);margin-top:4px">' + cg.get('away', '') + ' ' + str(cg.get('away_score', 0)) + ' — ' + cg.get('home', '') + ' ' + str(cg.get('home_score', 0)) + '</div>'
            ch += '<div style="color:#fbbf24;font-size:clamp(12px,3vw,16px);margin-top:4px">WAS DOWN ' + str(ca.get('max_deficit', 0)) + ' — ' + status_word + '</div>'
            ch += '<div style="margin-top:4px;font-size:clamp(12px,3vw,16px)">' + price_str + '</div>'
            ch += wp_str
            ch += '<div style="color:white;font-size:clamp(12px,3vw,15px);margin-top:6px">BUY <b>' + ca.get('fav_name', '') + '</b> ML if price hasn\'t caught up</div></div>'
            st.markdown(ch, unsafe_allow_html=True)
            link = get_kalshi_game_link(cg.get('away', ''), cg.get('home', ''))
            st.link_button("Trade " + ca.get('fav_name', '') + " ML on Kalshi", link, use_container_width=True)
            st.divider()
    elif not st.session_state.comeback_tracking:
        st.info("Monitoring for favorite deficits of 10+ points...")

# === END PART B ===('fav_wp'):
                wp = alert['fav_wp']
                wp_edge = alert.get('wp_edge', 0)
                wp_color = "#22c55e" if wp_edge >= MIN_WP_EDGE else "#eab308"
                st.markdown("<span style='color:" + wp_color + "'>ESPN WP: " + str(round(wp)) + "% | WP Edge: " + ("+" if wp_edge >= 0 else "") + str(round(wp_edge)) + "%</span>", unsafe_allow_html=True)
            if alert.get
      # ── PART C: TAB 3 (LIVE MONITOR) + TAB 4 (CUSHION SCANNER) + FOOTER ──

with tab_live:
    st.subheader("LIVE EDGE MONITOR")
    if live_games:
        for g in live_games:
            st.markdown("### " + g.get('away', '') + " @ " + g.get('home', ''))
            render_scoreboard(g.get('away', ''), g.get('home', ''), g.get('away_score', 0), g.get('home_score', 0), g.get('period', 0), g.get('clock', ''), g.get('away_record', ''), g.get('home_record', ''))
            plays = fetch_plays_wnba(g.get('game_id', ''))
            lc1, lc2 = st.columns([3, 2])
            with lc1:
                last_play = plays[-1] if plays else None
                render_nba_court(g.get('away', ''), g.get('home', ''), g.get('away_score', 0), g.get('home_score', 0), g.get('period', 0), g.get('clock', ''), last_play)
                poss_team, poss_desc = infer_possession(plays, g.get('away', ''), g.get('home', ''))
                if poss_team and poss_desc:
                    poss_color = TEAM_COLORS.get(poss_team, "#888") if poss_team not in ["UNKNOWN", "LOOSE"] else "#eab308"
                    st.markdown("<div style='text-align:center;padding:6px;max-width:100%;box-sizing:border-box'><span style='color:" + poss_color + ";font-weight:bold;font-size:clamp(12px,3vw,16px)'>" + poss_desc + "</span></div>", unsafe_allow_html=True)
            with lc2:
                st.markdown("**LAST 10 PLAYS**")
                tts_on = st.checkbox("🔊 TTS", key="tts_" + g.get('game_id', ''))
                for idx, play in enumerate(reversed(plays)):
                    icon_letter, icon_color = get_play_icon(play.get('play_type', ''), play.get('score_value', 0))
                    ptext = "Q" + str(play.get('period', 0)) if play.get('period', 0) <= 4 else "OT" + str(play.get('period', 0) - 4)
                    display_text = (play.get('text', '') or '')[:60]
                    ph = '<div style="border-left:3px solid ' + icon_color + ';padding:4px 8px;margin-bottom:3px;max-width:100%;box-sizing:border-box;overflow-x:hidden">'
                    ph += '<span style="color:' + icon_color + ';font-weight:bold;font-size:clamp(11px,2.5vw,14px)">' + icon_letter + '</span>'
                    ph += '<span style="color:#94a3b8;font-size:clamp(10px,2vw,12px)"> ' + ptext + ' ' + play.get('clock', '') + '</span>'
                    ph += '<span style="color:#ccc;font-size:clamp(11px,2.5vw,13px);word-wrap:break-word"> ' + display_text + '</span></div>'
                    st.markdown(ph, unsafe_allow_html=True)
                    if idx == 0 and tts_on and display_text:
                        speak_play(display_text)

            if g.get('minutes_played', 0) >= 6:
                ts = g.get('total_score', 0)
                mp = g.get('minutes_played', 0)
                pace = round(ts / mp, 2) if mp > 0 else 0
                proj = calc_projection(ts, mp)
                plabel, pcolor = get_pace_label(pace)
                lead = abs(g.get('home_score', 0) - g.get('away_score', 0))
                leader = g.get('home', '') if g.get('home_score', 0) >= g.get('away_score', 0) else g.get('away', '')
                sh = '<div style="background:#0f172a;padding:clamp(8px,2vw,16px);border-radius:8px;display:flex;flex-wrap:wrap;gap:16px;justify-content:center;max-width:100%;box-sizing:border-box;overflow-x:hidden">'
                sh += '<div style="text-align:center"><div style="color:#94a3b8;font-size:clamp(10px,2vw,12px)">Score</div><div style="color:white;font-weight:bold;font-size:clamp(14px,3.5vw,18px)">' + str(ts) + '</div></div>'
                sh += '<div style="text-align:center"><div style="color:#94a3b8;font-size:clamp(10px,2vw,12px)">Pace</div><div style="color:' + pcolor + ';font-weight:bold;font-size:clamp(14px,3.5vw,18px)">' + plabel + ' (' + str(pace) + ')</div></div>'
                sh += '<div style="text-align:center"><div style="color:#94a3b8;font-size:clamp(10px,2vw,12px)">Projection</div><div style="color:white;font-weight:bold;font-size:clamp(14px,3.5vw,18px)">' + str(proj) + '</div></div>'
                sh += '<div style="text-align:center"><div style="color:#94a3b8;font-size:clamp(10px,2vw,12px)">Lead</div><div style="color:white;font-weight:bold;font-size:clamp(14px,3.5vw,18px)">' + leader + ' +' + str(lead) + '</div></div></div>'
                st.markdown(sh, unsafe_allow_html=True)

                if lead >= 10:
                    ml_label = "STRONG" if lead >= 15 else "GOOD"
                    ml_link = get_kalshi_game_link(g.get('away', ''), g.get('home', ''))
                    st.link_button("🏀 " + leader + " ML — " + ml_label + " LEAD +" + str(lead), ml_link, use_container_width=True)
                else: st.caption("Moneyline: Wait for larger lead (10+)")

                tc1, tc2 = st.columns(2)
                with tc1:
                    st.markdown("**YES (Over)**")
                    yes_found = False
                    rec_set = False
                    for thresh in sorted(THRESHOLDS):
                        cushion = proj - thresh
                        if cushion >= 6:
                            if cushion >= 20: safety, scolor = "FORTRESS", "#22c55e"
                            elif cushion >= 12: safety, scolor = "SAFE", "#22c55e"
                            else: safety, scolor = "TIGHT", "#eab308"
                            rec_badge = ""
                            if not rec_set and cushion >= 12: rec_badge = " *REC"; rec_set = True
                            st.markdown("<span style='color:" + scolor + "'>" + safety + " YES " + str(thresh) + " | +" + str(round(cushion)) + rec_badge + "</span>", unsafe_allow_html=True)
                            yes_found = True
                    if yes_found:
                        tl = get_kalshi_game_link(g.get('away', ''), g.get('home', ''))
                        st.link_button("Trade YES on Kalshi", tl, use_container_width=True)
                    else: st.caption("No YES edges (cushion <6)")
                with tc2:
                    st.markdown("**NO (Under)**")
                    no_found = False
                    rec_set = False
                    for thresh in sorted(THRESHOLDS, reverse=True):
                        cushion = thresh - proj
                        if cushion >= 6:
                            if cushion >= 20: safety, scolor = "FORTRESS", "#22c55e"
                            elif cushion >= 12: safety, scolor = "SAFE", "#22c55e"
                            else: safety, scolor = "TIGHT", "#eab308"
                            rec_badge = ""
                            if not rec_set and cushion >= 12: rec_badge = " *REC"; rec_set = True
                            st.markdown("<span style='color:" + scolor + "'>" + safety + " NO " + str(thresh) + " | +" + str(round(cushion)) + rec_badge + "</span>", unsafe_allow_html=True)
                            no_found = True
                    if no_found:
                        tl = get_kalshi_game_link(g.get('away', ''), g.get('home', ''))
                        st.link_button("Trade NO on Kalshi", tl, use_container_width=True)
                    else: st.caption("No NO edges (cushion <6)")
            else: st.caption("Waiting for 6+ minutes of play for pace data...")

            lead_tb = abs(g.get('home_score', 0) - g.get('away_score', 0))
            if lead_tb <= 5 and g.get('minutes_played', 0) >= 6:
                all_plays = fetch_all_plays_wnba(g.get('game_id', ''))
                tb_stats = calc_tiebreaker_stats(all_plays, g.get('home', ''), g.get('away', ''), g.get('home_id', ''), g.get('away_id', ''))
                tb_html = render_tiebreaker_panel(tb_stats, g.get('home', ''), g.get('away', ''))
                st.markdown(tb_html, unsafe_allow_html=True)
            st.divider()
    else: st.info("No live games right now — check back during game time!")

# ════════════════════════════════════════════════
# TAB 4: CUSHION SCANNER
# ════════════════════════════════════════════════
with tab_cushion:
    st.subheader("CUSHION SCANNER (Totals)")
    cs1, cs2, cs3 = st.columns(3)
    with cs1:
        game_opts = ["All Games"] + [g.get('away', '') + " @ " + g.get('home', '') for g in games]
        cush_game = st.selectbox("Game", game_opts, key="cush_game")
    with cs2: min_time = st.selectbox("Min Play Time", [6, 8, 12, 16, 20], index=1, key="cush_time")
    with cs3: cush_side = st.selectbox("Side", ["NO (Under)", "YES (Over)"], key="cush_side")

    is_no = "NO" in cush_side
    cushion_results = []
    for g in games:
        if g.get('status') in ['STATUS_FINAL', 'STATUS_FULL_TIME']: continue
        if cush_game != "All Games" and (g.get('away', '') + " @ " + g.get('home', '')) != cush_game: continue
        mp = g.get('minutes_played', 0)
        proj = LEAGUE_AVG_TOTAL
        has_pace = False
        if mp >= 6:
            proj = calc_projection(g.get('total_score', 0), mp)
            has_pace = True
        elif g.get('vegas_odds', {}).get('overUnder'):
            try: proj = float(g['vegas_odds']['overUnder'])
            except: pass
        if has_pace and mp < min_time and cush_game == "All Games": continue
        thresholds_sorted = sorted(THRESHOLDS, reverse=True) if is_no else sorted(THRESHOLDS)
        single_game = cush_game != "All Games"
        rec_set = False
        for thresh in thresholds_sorted:
            cushion = (thresh - proj) if is_no else (proj - thresh)
            if cushion >= 6 or single_game:
                if cushion >= 20: safety, scolor = "FORTRESS", "#22c55e"
                elif cushion >= 12: safety, scolor = "SAFE", "#22c55e"
                elif cushion >= 6: safety, scolor = "TIGHT", "#eab308"
                else: safety, scolor = "RISKY", "#ef4444"
                is_rec = False
                if not rec_set and cushion >= 12: is_rec = True; rec_set = True
                ptext_cs = ""
                if g.get('state') == 'in':
                    ptext_cs = ("Q" + str(g.get('period', 0)) + " " + g.get('clock', '')) if g.get('period', 0) <= 4 else ("OT" + str(g.get('period', 0) - 4) + " " + g.get('clock', ''))
                else: ptext_cs = g.get('game_time', 'Sched')
                cushion_results.append({"game": g.get('away', '') + " @ " + g.get('home', ''),
                    "status": ptext_cs, "proj": proj, "thresh": thresh,
                    "cushion": cushion, "safety": safety, "scolor": scolor,
                    "is_live": g.get('state') == 'in', "is_rec": is_rec,
                    "away": g.get('away', ''), "home": g.get('home', '')})

    safety_order = {"FORTRESS": 0, "SAFE": 1, "TIGHT": 2, "RISKY": 3}
    cushion_results.sort(key=lambda x: (0 if x.get('is_live') else 1, safety_order.get(x.get('safety', ''), 9), -x.get('cushion', 0)))
    max_show = 20 if cush_game != "All Games" else 10
    if cushion_results:
        for cr in cushion_results[:max_show]:
            cc1, cc2, cc3, cc4 = st.columns([3, 2, 2, 2])
            with cc1:
                rec_badge = " ⭐ REC" if cr.get('is_rec') else ""
                st.markdown("**" + cr.get('game', '') + "**" + rec_badge)
                st.caption(cr.get('status', ''))
            with cc2:
                side_label = "NO" if is_no else "YES"
                st.markdown("Proj: " + str(round(cr.get('proj', 0))) + " | " + side_label + " " + str(cr.get('thresh', 0)))
            with cc3:
                st.markdown("<span style='color:" + cr.get('scolor', '#888') + ";font-weight:bold'>" + cr.get('safety', '') + " +" + str(round(cr.get('cushion', 0))) + "</span>", unsafe_allow_html=True)
            with cc4:
                link = get_kalshi_game_link(cr.get('away', ''), cr.get('home', ''))
                st.link_button("BUY", link, use_container_width=True)
        if is_no: st.caption("NO bets: go HIGH for safety — bigger number = more cushion")
        else: st.caption("YES bets: go LOW for safety — smaller number = more cushion")
    else: st.info("No cushion opportunities found with current filters.")

# ── Footer ──
st.divider()
st.caption("v" + VERSION + " | Educational only | Not financial advice")
st.caption("Stay small. Stay quiet. Win.")
