import streamlit as st
from streamlit_autorefresh import st_autorefresh
import streamlit.components.v1 as components
st.set_page_config(page_title="BigSnapshot NCAAW Edge Finder", page_icon="🏀", layout="wide")
from auth import require_auth
require_auth()
st_autorefresh(interval=30000, key="ncaaw_datarefresh")
import uuid, re, requests, pytz
import requests as req_ga
from datetime import datetime, timedelta

# ============================================================
# GA4 TRACKING
# ============================================================
def send_ga4_event(page_title, page_path):
    try:
        url = "https://www.google-analytics.com/mp/collect?measurement_id=G-NQKY5VQ376&api_secret=n4oBJjH7RXi0dA7aQo2CZA"
        payload = {"client_id": str(uuid.uuid4()), "events": [{"name": "page_view", "params": {"page_title": page_title, "page_location": "https://bigsnapshot.streamlit.app" + page_path}}]}
        req_ga.post(url, json=payload, timeout=2)
    except:
        pass
send_ga4_event("BigSnapshot NCAAW Edge Finder", "/NCAAW")

# ============================================================
# TIMEZONE + CONSTANTS
# ============================================================
eastern = pytz.timezone("US/Eastern")
now = datetime.now(eastern)
VERSION = "1.0"
LEAGUE_AVG_TOTAL = 135
GAME_MINUTES = 40
HALF_MINUTES = 20
THRESHOLDS = [120.5, 125.5, 130.5, 135.5, 140.5, 145.5, 150.5, 155.5, 160.5]
HOME_COURT_ADV = 4.0
MIN_UNDERDOG_LEAD = 8
MIN_SPREAD_BRACKET = 8
MAX_NO_PRICE = 85
MIN_WP_EDGE = 8
LEAD_BY_HALF = {1: 8, 2: 12}
KALSHI_GAME_LINK = "https://kalshi.com/sports/basketball/college-basketball-w/games"
KALSHI_SPREAD_LINK = "https://kalshi.com/sports/basketball/college-basketball-w/spreads"

# ============================================================
# SESSION STATE
# ============================================================
if 'ncaaw_positions' not in st.session_state:
    st.session_state.ncaaw_positions = []
if 'ncaaw_sniper_alerts' not in st.session_state:
    st.session_state.ncaaw_sniper_alerts = []
if 'ncaaw_comeback_alerts' not in st.session_state:
    st.session_state.ncaaw_comeback_alerts = []
if 'ncaaw_comeback_tracking' not in st.session_state:
    st.session_state.ncaaw_comeback_tracking = {}
if 'ncaaw_alerted_games' not in st.session_state:
    st.session_state.ncaaw_alerted_games = set()
if 'ncaaw_comeback_alerted' not in st.session_state:
    st.session_state.ncaaw_comeback_alerted = set()

# ============================================================
# HELPER FUNCTIONS
# ============================================================
def get_team_color(game, side):
    return game.get(f'{side}_color', '#555555')

def american_to_implied_prob(odds):
    if odds is None or odds == 0:
        return None
    if odds > 0:
        return 100.0 / (odds + 100.0)
    else:
        return abs(odds) / (abs(odds) + 100.0)

def speak_play(text):
    clean = re.sub(r'[^\w\s.,!?-]', '', str(text))
    js = f"""
    <script>
    (function() {{
        if (window.lastSpoken === `{clean}`) return;
        window.lastSpoken = `{clean}`;
        var u = new SpeechSynthesisUtterance(`{clean}`);
        u.rate = 1.1;
        window.speechSynthesis.speak(u);
    }})();
    </script>
    """
    components.html(js, height=0)

def calc_minutes_elapsed(period, clock_str):
    try:
        parts = str(clock_str).split(":")
        if len(parts) == 2:
            mins_left = int(parts[0])
            secs_left = int(parts[1])
        else:
            mins_left = 0
            secs_left = 0
        time_left = mins_left + secs_left / 60.0
        if period <= 2:
            elapsed = (period - 1) * HALF_MINUTES + (HALF_MINUTES - time_left)
        else:
            ot_period = period - 2
            elapsed = GAME_MINUTES + (ot_period - 1) * 5 + (5 - time_left)
        return max(0, elapsed)
    except:
        return 0

def calc_projection(total_score, minutes_elapsed):
    if minutes_elapsed <= 0:
        return LEAGUE_AVG_TOTAL
    rate = total_score / minutes_elapsed
    proj = rate * GAME_MINUTES
    return max(100, min(200, proj))

def get_pace_label(pace):
    if pace < 2.8:
        return "🐢 SLOW", "#3498db"
    elif pace < 3.2:
        return "⚡ AVG", "#f39c12"
    elif pace < 3.6:
        return "🔥 FAST", "#e74c3c"
    else:
        return "💥 SHOOTOUT", "#ff00ff"

def parse_record(s):
    try:
        parts = str(s).strip().split("-")
        return (int(parts[0]), int(parts[1]))
    except:
        return (0, 0)

def get_favorite_side(home_record, away_record, home_ml=0, home_rank=99, away_rank=99):
    if home_ml != 0:
        if home_ml < 0:
            return "home"
        else:
            return "away"
    if home_rank < away_rank:
        return "home"
    elif away_rank < home_rank:
        return "away"
    hw, hl = parse_record(home_record)
    aw, al = parse_record(away_record)
    home_pct = hw / (hw + hl) if (hw + hl) > 0 else 0
    away_pct = aw / (aw + al) if (aw + al) > 0 else 0
    if home_pct >= away_pct:
        return "home"
    return "away"

def _parse_win_pct(record_str):
    try:
        clean = re.sub(r'\(.*?\)', '', str(record_str)).strip()
        parts = clean.split("-")
        w = int(parts[0])
        l = int(parts[1])
        return w / (w + l) if (w + l) > 0 else 0.5
    except:
        return 0.5

def remove_position(pos_id):
    st.session_state.ncaaw_positions = [p for p in st.session_state.ncaaw_positions if p.get('id') != pos_id]

# ============================================================
# ESPN DATA FETCHERS
# ============================================================
@st.cache_data(ttl=30)
def fetch_espn_games():
    today_str = now.strftime("%Y%m%d")
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/womens-college-basketball/scoreboard?dates={today_str}&limit=200&groups=50"
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
    except:
        return []
    games = []
    for evt in data.get("events", []):
        try:
            comp = evt["competitions"][0]
            status_obj = comp.get("status", {})
            state = status_obj.get("type", {}).get("state", "pre")
            detail = status_obj.get("type", {}).get("shortDetail", "")
            period = status_obj.get("period", 0)
            clock = status_obj.get("displayClock", "0:00")
            teams = comp.get("competitors", [])
            home_team = None
            away_team = None
            for t in teams:
                if t.get("homeAway") == "home":
                    home_team = t
                elif t.get("homeAway") == "away":
                    away_team = t
            if not home_team or not away_team:
                continue
            def extract_team(t):
                team_data = t.get("team", {})
                abbr = team_data.get("abbreviation", "???")
                name = team_data.get("displayName", abbr)
                short = team_data.get("shortDisplayName", name)
                logo = team_data.get("logo", "")
                color = team_data.get("color", "555555")
                if color and not color.startswith("#"):
                    color = "#" + color
                score = int(t.get("score", 0))
                record = "0-0"
                for rec in t.get("records", []):
                    if rec.get("type") == "total":
                        record = rec.get("summary", "0-0")
                        break
                rank = 99
                if t.get("curatedRank", {}).get("current", 99) < 99:
                    rank = t["curatedRank"]["current"]
                return abbr, name, short, logo, color, score, record, rank
            h_abbr, h_name, h_short, h_logo, h_color, h_score, h_record, h_rank = extract_team(home_team)
            a_abbr, a_name, a_short, a_logo, a_color, a_score, a_record, a_rank = extract_team(away_team)
            odds_data = comp.get("odds", [{}])
            home_ml = 0
            away_ml = 0
            spread_val = 0
            ou_val = 0
            if odds_data and len(odds_data) > 0:
                od = odds_data[0]
                home_ml = od.get("homeTeamOdds", {}).get("moneyLine", 0) or 0
                away_ml = od.get("awayTeamOdds", {}).get("moneyLine", 0) or 0
                spread_val = od.get("spread", 0) or 0
                ou_val = od.get("overUnder", 0) or 0
            linescores_home = []
            for ls in home_team.get("linescores", []):
                linescores_home.append(int(ls.get("value", 0)))
            linescores_away = []
            for ls in away_team.get("linescores", []):
                linescores_away.append(int(ls.get("value", 0)))
            game_id = evt.get("id", "")
            game = {
                "game_id": game_id,
                "state": state,
                "detail": detail,
                "period": period,
                "clock": clock,
                "home_abbr": h_abbr,
                "home_name": h_name,
                "home_short": h_short,
                "home_logo": h_logo,
                "home_color": h_color,
                "home_score": h_score,
                "home_record": h_record,
                "home_rank": h_rank,
                "away_abbr": a_abbr,
                "away_name": a_name,
                "away_short": a_short,
                "away_logo": a_logo,
                "away_color": a_color,
                "away_score": a_score,
                "away_record": a_record,
                "away_rank": a_rank,
                "home_ml": home_ml,
                "away_ml": away_ml,
                "spread": spread_val,
                "over_under": ou_val,
                "linescores_home": linescores_home,
                "linescores_away": linescores_away,
            }
            games.append(game)
        except:
            continue
    return games

@st.cache_data(ttl=300)
def fetch_game_summary(game_id):
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/womens-college-basketball/summary?event={game_id}"
    try:
        r = requests.get(url, timeout=10)
        return r.json()
    except:
        return {}

@st.cache_data(ttl=20)
def fetch_espn_win_prob(game_id):
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/womens-college-basketball/summary?event={game_id}"
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        wp_list = data.get("winprobability", [])
        if wp_list:
            last = wp_list[-1]
            return last.get("homeWinPercentage", 0.5)
        return 0.5
    except:
        return 0.5

def parse_predictor(summary):
    try:
        pred = summary.get("predictor", {})
        home_prob = pred.get("homeTeam", {}).get("gameProjection", 0)
        away_prob = pred.get("awayTeam", {}).get("gameProjection", 0)
        return float(home_prob) / 100.0, float(away_prob) / 100.0
    except:
        return 0.5, 0.5

def parse_team_stats_from_summary(summary):
    stats = {"home": {}, "away": {}}
    try:
        boxscore = summary.get("boxscore", {})
        teams_box = boxscore.get("teams", [])
        for i, t in enumerate(teams_box):
            side = "away" if i == 0 else "home"
            team_stats = {}
            for stat_group in t.get("statistics", []):
                for s in stat_group if isinstance(stat_group, list) else [stat_group]:
                    name = s.get("name", "")
                    val = s.get("displayValue", "0")
                    team_stats[name] = val
            stats[side] = team_stats
    except:
        pass
    return stats

def _get_team_leaders(summary, home_away):
    leaders = []
    try:
        boxscore = summary.get("boxscore", {})
        players_list = boxscore.get("players", [])
        idx = 1 if home_away == "home" else 0
        if idx < len(players_list):
            team_players = players_list[idx]
            for stat_group in team_players.get("statistics", []):
                for athlete in stat_group.get("athletes", []):
                    name = athlete.get("athlete", {}).get("displayName", "")
                    pts = 0
                    for s in athlete.get("stats", []):
                        pass
                    stats_list = athlete.get("stats", [])
                    if stats_list and len(stats_list) > 0:
                        try:
                            pts = int(stats_list[-1]) if stats_list[-1].isdigit() else 0
                        except:
                            pts = 0
                    leaders.append({"name": name, "pts": pts})
        leaders.sort(key=lambda x: x["pts"], reverse=True)
        return leaders[:3]
    except:
        return []

def _is_star_player(player_name, leaders_list):
    for ld in leaders_list:
        if player_name.lower() in ld.get("name", "").lower() or ld.get("name", "").lower() in player_name.lower():
            return True
    return False

@st.cache_data(ttl=300)
def fetch_injuries():
    injuries = {}
    try:
        url = "https://site.api.espn.com/apis/site/v2/sports/basketball/womens-college-basketball/injuries"
        r = requests.get(url, timeout=10)
        data = r.json()
        for team_entry in data.get("items", []):
            team_ref = team_entry.get("team", {})
            abbr = team_ref.get("abbreviation", "???")
            team_injuries = []
            for inj in team_entry.get("injuries", []):
                name = inj.get("athlete", {}).get("displayName", "Unknown")
                status_val = inj.get("status", "Unknown")
                team_injuries.append({"name": name, "status": status_val})
            if team_injuries:
                injuries[abbr] = team_injuries
    except:
        pass
    return injuries

@st.cache_data(ttl=300)
def fetch_yesterday_teams():
    b2b = set()
    try:
        yesterday = now - timedelta(days=1)
        ystr = yesterday.strftime("%Y%m%d")
        url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/womens-college-basketball/scoreboard?dates={ystr}&limit=200&groups=50"
        r = requests.get(url, timeout=10)
        data = r.json()
        for evt in data.get("events", []):
            comp = evt.get("competitions", [{}])[0]
            for t in comp.get("competitors", []):
                abbr = t.get("team", {}).get("abbreviation", "")
                if abbr:
                    b2b.add(abbr)
    except:
        pass
    return b2b

@st.cache_data(ttl=30)
def fetch_plays(game_id):
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/womens-college-basketball/summary?event={game_id}"
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        plays = []
        for play_grp in data.get("plays", []):
            if isinstance(play_grp, dict):
                plays.append(play_grp)
            elif isinstance(play_grp, list):
                plays.extend(play_grp)
        return plays
    except:
        return []

# ============================================================
# KALSHI DATA FETCHERS (PUBLIC, NO AUTH)
# ============================================================
@st.cache_data(ttl=60)
def fetch_kalshi_ml():
    out = {}
    try:
        cursor = None
        while True:
            url = "https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXNCAAWBGAME&status=open&limit=200"
            if cursor:
                url += f"&cursor={cursor}"
            r = requests.get(url, timeout=10)
            data = r.json()
            markets = data.get("markets", [])
            for m in markets:
                ticker = m.get("ticker", "")
                title = m.get("title", "")
                yes_ask = m.get("yes_ask", 0)
                no_ask = m.get("no_ask", 0)
                yes_bid = m.get("yes_bid", 0)
                no_bid = m.get("no_bid", 0)
                volume = m.get("volume", 0)
                out[ticker] = {
                    "ticker": ticker,
                    "title": title,
                    "yes_ask": yes_ask,
                    "no_ask": no_ask,
                    "yes_bid": yes_bid,
                    "no_bid": no_bid,
                    "volume": volume,
                }
            cursor = data.get("cursor", None)
            if not cursor or len(markets) < 200:
                break
    except:
        pass
    return out

@st.cache_data(ttl=60)
def fetch_kalshi_spreads_raw():
    out = {}
    try:
        cursor = None
        while True:
            url = "https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXNCAAWBSPREAD&status=open&limit=200"
            if cursor:
                url += f"&cursor={cursor}"
            r = requests.get(url, timeout=10)
            data = r.json()
            markets = data.get("markets", [])
            for m in markets:
                ticker = m.get("ticker", "")
                title = m.get("title", "")
                subtitle = m.get("subtitle", "")
                yes_ask = m.get("yes_ask", 0)
                no_ask = m.get("no_ask", 0)
                yes_bid = m.get("yes_bid", 0)
                no_bid = m.get("no_bid", 0)
                volume = m.get("volume", 0)
                floor_val = m.get("floor_strike", None)
                cap_val = m.get("cap_strike", None)
                out[ticker] = {
                    "ticker": ticker,
                    "title": title,
                    "subtitle": subtitle,
                    "yes_ask": yes_ask,
                    "no_ask": no_ask,
                    "yes_bid": yes_bid,
                    "no_bid": no_bid,
                    "volume": volume,
                    "floor": floor_val,
                    "cap": cap_val,
                }
            cursor = data.get("cursor", None)
            if not cursor or len(markets) < 200:
                break
    except:
        pass
    return out

def find_spread_markets_for_game(spread_dict, home_abbr, away_abbr, home_name="", away_name=""):
    matches = []
    search_terms = [home_abbr.upper(), away_abbr.upper()]
    if home_name:
        search_terms.append(home_name.upper())
    if away_name:
        search_terms.append(away_name.upper())
    for ticker, m in spread_dict.items():
        title_up = m.get("title", "").upper()
        sub_up = m.get("subtitle", "").upper()
        combined = title_up + " " + sub_up
        home_found = any(term in combined for term in [home_abbr.upper(), home_name.upper()] if term)
        away_found = any(term in combined for term in [away_abbr.upper(), away_name.upper()] if term)
        if home_found or away_found:
            matches.append(m)
    return matches

def find_ml_price_for_team(kalshi_ml_dict, team_abbr, team_name=""):
    for ticker, m in kalshi_ml_dict.items():
        title_up = m.get("title", "").upper()
        if team_abbr.upper() in title_up or (team_name and team_name.upper() in title_up):
            return m
    return None

# ============================================================
# 9-FACTOR EDGE MODEL
# ============================================================
def calc_advanced_edge(game, b2b_teams, summary=None, injuries=None):
    factors = []
    home_abbr = game.get("home_abbr", "")
    away_abbr = game.get("away_abbr", "")
    home_record = game.get("home_record", "0-0")
    away_record = game.get("away_record", "0-0")
    home_rank = game.get("home_rank", 99)
    away_rank = game.get("away_rank", 99)
    home_ml = game.get("home_ml", 0)
    away_ml = game.get("away_ml", 0)
    fav_side = get_favorite_side(home_record, away_record, home_ml, home_rank, away_rank)
    fav_label = game.get("home_short", home_abbr) if fav_side == "home" else game.get("away_short", away_abbr)
    dog_label = game.get("away_short", away_abbr) if fav_side == "home" else game.get("home_short", home_abbr)

    # Factor 1: Record Gap
    hw, hl = parse_record(home_record)
    aw, al = parse_record(away_record)
    home_pct = hw / (hw + hl) if (hw + hl) > 0 else 0.5
    away_pct = aw / (aw + al) if (aw + al) > 0 else 0.5
    gap = abs(home_pct - away_pct)
    if gap > 0.3:
        pts = 15
    elif gap > 0.2:
        pts = 10
    elif gap > 0.1:
        pts = 5
    else:
        pts = 0
    factors.append({"name": "Record Gap", "pts": pts, "detail": f"{home_record} vs {away_record} ({gap:.0%} gap)"})

    # Factor 2: Ranking Gap
    rank_gap = abs(home_rank - away_rank)
    if home_rank < 26 or away_rank < 26:
        if rank_gap >= 20:
            pts = 15
        elif rank_gap >= 10:
            pts = 10
        elif rank_gap >= 5:
            pts = 5
        else:
            pts = 0
    else:
        pts = 0
    h_rk = f"#{home_rank}" if home_rank < 26 else "NR"
    a_rk = f"#{away_rank}" if away_rank < 26 else "NR"
    factors.append({"name": "Ranking Gap", "pts": pts, "detail": f"{h_rk} vs {a_rk}"})

    # Factor 3: Home Court
    if fav_side == "home":
        pts = 10
        detail = f"{fav_label} has home court + favored"
    else:
        pts = 0
        detail = f"Favorite {fav_label} is away"
    factors.append({"name": "Home Court", "pts": pts, "detail": detail})

    # Factor 4: Back-to-Back
    dog_abbr = away_abbr if fav_side == "home" else home_abbr
    fav_abbr = home_abbr if fav_side == "home" else away_abbr
    if dog_abbr in b2b_teams and fav_abbr not in b2b_teams:
        pts = 10
        detail = f"{dog_label} on B2B, {fav_label} rested"
    elif fav_abbr in b2b_teams and dog_abbr not in b2b_teams:
        pts = -5
        detail = f"{fav_label} on B2B (edge reduced)"
    else:
        pts = 0
        detail = "No B2B advantage"
    factors.append({"name": "Back-to-Back", "pts": pts, "detail": detail})

    # Factor 5: Moneyline Gap
    home_imp = american_to_implied_prob(home_ml)
    away_imp = american_to_implied_prob(away_ml)
    if home_imp and away_imp:
        ml_gap = abs(home_imp - away_imp)
        if ml_gap > 0.4:
            pts = 15
        elif ml_gap > 0.25:
            pts = 10
        elif ml_gap > 0.15:
            pts = 5
        else:
            pts = 0
        detail = f"ML gap: {ml_gap:.0%} (Home {home_ml:+}, Away {away_ml:+})"
    else:
        pts = 0
        ml_gap = 0
        detail = "No ML data"
    factors.append({"name": "Moneyline Gap", "pts": pts, "detail": detail})

    # Factor 6: Spread Size
    spread = abs(game.get("spread", 0))
    if spread >= 15:
        pts = 15
    elif spread >= 10:
        pts = 10
    elif spread >= 6:
        pts = 5
    else:
        pts = 0
    factors.append({"name": "Spread Size", "pts": pts, "detail": f"Spread: {spread:.1f}"})

    # Factor 7: Injury Impact
    inj_pts = 0
    inj_detail = "No significant injuries"
    if injuries:
        dog_abbr_key = away_abbr if fav_side == "home" else home_abbr
        fav_abbr_key = home_abbr if fav_side == "home" else away_abbr
        fav_inj = injuries.get(fav_abbr_key, [])
        dog_inj = injuries.get(dog_abbr_key, [])
        fav_out = [i for i in fav_inj if "out" in str(i.get("status", "")).lower()]
        dog_out = [i for i in dog_inj if "out" in str(i.get("status", "")).lower()]
        if summary:
            fav_side_key = "home" if fav_side == "home" else "away"
            dog_side_key = "away" if fav_side == "home" else "home"
            fav_leaders = _get_team_leaders(summary, fav_side_key)
            dog_leaders = _get_team_leaders(summary, dog_side_key)
            fav_star_out = any(_is_star_player(i.get("name", ""), fav_leaders) for i in fav_out)
            dog_star_out = any(_is_star_player(i.get("name", ""), dog_leaders) for i in dog_out)
        else:
            fav_star_out = False
            dog_star_out = False
        if fav_star_out:
            inj_pts = 15
            inj_detail = f"{fav_label} star player OUT"
        elif len(fav_out) >= 2:
            inj_pts = 10
            inj_detail = f"{fav_label} has {len(fav_out)} players out"
        elif len(fav_out) >= 1:
            inj_pts = 5
            inj_detail = f"{fav_label} has player(s) out"
        if dog_star_out:
            inj_pts = max(0, inj_pts - 10)
            inj_detail += f" | {dog_label} star also out"
    factors.append({"name": "Injury Impact", "pts": inj_pts, "detail": inj_detail})

    # Factor 8: ESPN Predictor
    pred_pts = 0
    pred_detail = "No predictor data"
    if summary:
        home_prob, away_prob = parse_predictor(summary)
        fav_prob = home_prob if fav_side == "home" else away_prob
        if fav_prob > 0.75:
            pred_pts = 10
        elif fav_prob > 0.6:
            pred_pts = 5
        else:
            pred_pts = 0
        pred_detail = f"{fav_label} ESPN win prob: {fav_prob:.0%}"
    factors.append({"name": "ESPN Predictor", "pts": pred_pts, "detail": pred_detail})

    # Factor 9: Over/Under Context
    ou = game.get("over_under", 0)
    if ou > 0:
        if ou >= 155:
            pts = 5
            detail = f"O/U {ou} — High-scoring expected (more variance)"
        elif ou <= 120:
            pts = 10
            detail = f"O/U {ou} — Low total favors favorite control"
        else:
            pts = 5
            detail = f"O/U {ou}"
    else:
        pts = 0
        detail = "No O/U data"
    factors.append({"name": "O/U Context", "pts": pts, "detail": detail})

    total_pts = sum(f["pts"] for f in factors)
    max_pts = 105
    edge_pct = max(0, min(100, total_pts / max_pts * 100))

    if edge_pct >= 75:
        grade = "A+"
    elif edge_pct >= 60:
        grade = "A"
    elif edge_pct >= 50:
        grade = "B+"
    elif edge_pct >= 40:
        grade = "B"
    elif edge_pct >= 25:
        grade = "C"
    else:
        grade = "D"

    return {
        "factors": factors,
        "total_pts": total_pts,
        "max_pts": max_pts,
        "edge_pct": edge_pct,
        "grade": grade,
        "fav_side": fav_side,
        "fav_label": fav_label,
        "dog_label": dog_label,
    }

# ============================================================
# POSSESSION TRACKER
# ============================================================
def infer_possession(plays, home_abbr, away_abbr):
    if not plays:
        return None, None
    last_play = None
    if isinstance(plays, list):
        for p in reversed(plays):
            if isinstance(p, dict):
                last_play = p
                break
    if not last_play:
        return None, None
    text = last_play.get("text", "")
    team_ref = last_play.get("team", {})
    team_id = team_ref.get("id", "") if isinstance(team_ref, dict) else ""
    play_type = last_play.get("type", {}).get("text", "").lower() if isinstance(last_play.get("type"), dict) else ""
    score_val = last_play.get("scoreValue", 0)

    possession = None
    turnover_kw = ["turnover", "steal", "violation", "kicked"]
    made_kw = ["made", "free throw"]
    miss_reb_kw = ["rebound"]

    text_lower = text.lower()
    if any(kw in text_lower for kw in turnover_kw):
        if home_abbr.lower() in text_lower:
            possession = away_abbr
        elif away_abbr.lower() in text_lower:
            possession = home_abbr
        else:
            possession = "unknown"
    elif any(kw in text_lower for kw in made_kw):
        if home_abbr.lower() in text_lower:
            possession = away_abbr
        elif away_abbr.lower() in text_lower:
            possession = home_abbr
    elif any(kw in text_lower for kw in miss_reb_kw):
        if "offensive" in text_lower:
            if home_abbr.lower() in text_lower:
                possession = home_abbr
            else:
                possession = away_abbr
        else:
            if home_abbr.lower() in text_lower:
                possession = home_abbr
            else:
                possession = away_abbr

    return possession, last_play

# ============================================================
# SPREAD SNIPER + COMEBACK LOGIC
# ============================================================
def check_spread_sniper(game, spread_list, kalshi_ml_dict):
    if game.get("state") != "in":
        return
    game_id = game.get("game_id", "")
    if game_id in st.session_state.ncaaw_alerted_games:
        return
    period = game.get("period", 0)
    if period < 1 or period > 2:
        return
    home_score = game.get("home_score", 0)
    away_score = game.get("away_score", 0)
    lead = abs(home_score - away_score)
    threshold = LEAD_BY_HALF.get(period, 12)
    if lead < threshold:
        return
    leader_abbr = game.get("home_abbr") if home_score > away_score else game.get("away_abbr")
    leader_name = game.get("home_short") if home_score > away_score else game.get("away_short")
    trailer_abbr = game.get("away_abbr") if home_score > away_score else game.get("home_abbr")
    trailer_name = game.get("away_short") if home_score > away_score else game.get("home_short")
    relevant_spreads = find_spread_markets_for_game(
        {t: s for t, s in zip(spread_list.keys(), spread_list.values())},
        game.get("home_abbr", ""), game.get("away_abbr", ""),
        game.get("home_name", ""), game.get("away_name", "")
    )
    best_snipe = None
    for sp in relevant_spreads:
        no_ask = sp.get("no_ask", 0)
        if 0 < no_ask <= MAX_NO_PRICE:
            floor_val = sp.get("floor", None)
            cap_val = sp.get("cap", None)
            if floor_val is not None and cap_val is not None:
                bracket_size = abs(cap_val - floor_val)
                if bracket_size >= MIN_SPREAD_BRACKET:
                    if best_snipe is None or no_ask < best_snipe["no_ask"]:
                        best_snipe = {
                            "ticker": sp["ticker"],
                            "title": sp["title"],
                            "no_ask": no_ask,
                            "floor": floor_val,
                            "cap": cap_val,
                        }
    if best_snipe:
        alert = {
            "game_id": game_id,
            "leader": leader_name,
            "trailer": trailer_name,
            "lead": lead,
            "period": period,
            "ticker": best_snipe["ticker"],
            "title": best_snipe["title"],
            "no_price": best_snipe["no_ask"],
            "floor": best_snipe["floor"],
            "cap": best_snipe["cap"],
            "time": now.strftime("%I:%M %p"),
        }
        st.session_state.ncaaw_sniper_alerts.append(alert)
        st.session_state.ncaaw_alerted_games.add(game_id)

def check_comeback(game, kalshi_ml_dict):
    if game.get("state") != "in":
        return
    game_id = game.get("game_id", "")
    home_score = game.get("home_score", 0)
    away_score = game.get("away_score", 0)
    lead = abs(home_score - away_score)
    if lead < MIN_UNDERDOG_LEAD:
        if game_id in st.session_state.ncaaw_comeback_tracking:
            del st.session_state.ncaaw_comeback_tracking[game_id]
        return
    leader_abbr = game.get("home_abbr") if home_score > away_score else game.get("away_abbr")
    leader_name = game.get("home_short") if home_score > away_score else game.get("away_short")
    trailer_abbr = game.get("away_abbr") if home_score > away_score else game.get("home_abbr")
    trailer_name = game.get("away_short") if home_score > away_score else game.get("home_short")
    home_ml_val = game.get("home_ml", 0)
    away_ml_val = game.get("away_ml", 0)
    fav_side = get_favorite_side(
        game.get("home_record", "0-0"), game.get("away_record", "0-0"),
        home_ml_val, game.get("home_rank", 99), game.get("away_rank", 99)
    )
    fav_abbr = game.get("home_abbr") if fav_side == "home" else game.get("away_abbr")
    if leader_abbr == fav_abbr:
        if game_id in st.session_state.ncaaw_comeback_tracking:
            del st.session_state.ncaaw_comeback_tracking[game_id]
        return
    if game_id not in st.session_state.ncaaw_comeback_tracking:
        st.session_state.ncaaw_comeback_tracking[game_id] = {
            "peak_lead": lead,
            "leader": leader_name,
            "trailer": trailer_name,
            "leader_abbr": leader_abbr,
            "trailer_abbr": trailer_abbr,
        }
    else:
        tracked = st.session_state.ncaaw_comeback_tracking[game_id]
        if lead > tracked["peak_lead"]:
            tracked["peak_lead"] = lead
        comeback_amt = tracked["peak_lead"] - lead
        if comeback_amt >= 6 and game_id not in st.session_state.ncaaw_comeback_alerted:
            trailer_ml = find_ml_price_for_team(kalshi_ml_dict, tracked["trailer_abbr"], tracked["trailer"])
            no_price = trailer_ml.get("no_ask", 0) if trailer_ml else 0
            alert = {
                "game_id": game_id,
                "leader": tracked["leader"],
                "trailer": tracked["trailer"],
                "peak_lead": tracked["peak_lead"],
                "current_lead": lead,
                "comeback_pts": comeback_amt,
                "no_price": no_price,
                "time": now.strftime("%I:%M %p"),
            }
            st.session_state.ncaaw_comeback_alerts.append(alert)
            st.session_state.ncaaw_comeback_alerted.add(game_id)

# ============================================================
# MOBILE CSS
# ============================================================
MOBILE_CSS = """
<style>
@media (max-width: 768px) {
    .block-container { padding: 0.5rem 0.5rem !important; }
    h1 { font-size: 1.3rem !important; }
    h2 { font-size: 1.1rem !important; }
    h3 { font-size: 1rem !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 2px; }
    .stTabs [data-baseweb="tab"] { padding: 4px 8px; font-size: 0.75rem; }
    div[data-testid="column"] { padding: 0 2px !important; }
    .stExpander { font-size: 0.85rem; }
}
.score-card {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    border-radius: 12px;
    padding: 15px;
    margin: 5px 0;
    border: 1px solid #333;
}
.factor-bar {
    height: 8px;
    border-radius: 4px;
    background: #333;
    margin: 3px 0;
}
.factor-fill {
    height: 100%;
    border-radius: 4px;
}
.sniper-alert {
    background: linear-gradient(135deg, #1a0a2e 0%, #2d1b4e 100%);
    border: 2px solid #9b59b6;
    border-radius: 12px;
    padding: 15px;
    margin: 10px 0;
    animation: pulse 2s infinite;
}
.comeback-alert {
    background: linear-gradient(135deg, #0a2e1a 0%, #1b4e2d 100%);
    border: 2px solid #27ae60;
    border-radius: 12px;
    padding: 15px;
    margin: 10px 0;
    animation: pulse 2s infinite;
}
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.85; }
}
.edge-grade {
    font-size: 2rem;
    font-weight: 900;
    text-align: center;
    padding: 10px;
    border-radius: 10px;
    margin: 5px 0;
}
.pos-card {
    background: #1a1a2e;
    border-radius: 10px;
    padding: 12px;
    margin: 5px 0;
    border: 1px solid #444;
}
</style>
"""

# ============================================================
# VISUAL COMPONENTS
# ============================================================
def render_scoreboard(game):
    state = game.get("state", "pre")
    detail = game.get("detail", "")
    home_abbr = game.get("home_abbr", "???")
    away_abbr = game.get("away_abbr", "???")
    home_score = game.get("home_score", 0)
    away_score = game.get("away_score", 0)
    home_color = get_team_color(game, "home")
    away_color = get_team_color(game, "away")
    home_logo = game.get("home_logo", "")
    away_logo = game.get("away_logo", "")
    home_rank = game.get("home_rank", 99)
    away_rank = game.get("away_rank", 99)
    home_record = game.get("home_record", "0-0")
    away_record = game.get("away_record", "0-0")
    ls_home = game.get("linescores_home", [])
    ls_away = game.get("linescores_away", [])

    h_rank_badge = f'<span style="background:#FFD700;color:#000;padding:1px 6px;border-radius:8px;font-size:0.7rem;font-weight:700;margin-right:4px;">#{home_rank}</span>' if home_rank < 26 else ""
    a_rank_badge = f'<span style="background:#FFD700;color:#000;padding:1px 6px;border-radius:8px;font-size:0.7rem;font-weight:700;margin-right:4px;">#{away_rank}</span>' if away_rank < 26 else ""

    if state == "in":
        status_html = f'<span style="color:#00ff88;font-weight:700;">🟢 LIVE — {detail}</span>'
    elif state == "post":
        status_html = f'<span style="color:#aaa;">FINAL — {detail}</span>'
    else:
        status_html = f'<span style="color:#f0c040;">{detail}</span>'

    half_headers = ""
    half_scores_home = ""
    half_scores_away = ""
    if ls_home:
        for i in range(len(ls_home)):
            label = f"H{i+1}" if i < 2 else f"OT{i-1}"
            half_headers += f'<th style="padding:2px 8px;color:#888;font-size:0.75rem;">{label}</th>'
            half_scores_home += f'<td style="padding:2px 8px;color:#ccc;font-size:0.8rem;text-align:center;">{ls_home[i]}</td>'
        for i in range(len(ls_away)):
            half_scores_away += f'<td style="padding:2px 8px;color:#ccc;font-size:0.8rem;text-align:center;">{ls_away[i] if i < len(ls_away) else ""}</td>'

    h_logo_img = f'<img src="{home_logo}" style="width:28px;height:28px;margin-right:6px;vertical-align:middle;">' if home_logo else ""
    a_logo_img = f'<img src="{away_logo}" style="width:28px;height:28px;margin-right:6px;vertical-align:middle;">' if away_logo else ""

    html = f"""
    <div class="score-card">
        <div style="text-align:center;margin-bottom:8px;">{status_html}</div>
        <table style="width:100%;border-collapse:collapse;">
            <tr>
                <th style="text-align:left;width:40%;"></th>
                {half_headers}
                <th style="padding:2px 8px;color:#888;font-size:0.75rem;">T</th>
            </tr>
            <tr>
                <td style="text-align:left;">
                    {a_logo_img}{a_rank_badge}
                    <span style="color:{away_color};font-weight:700;font-size:1rem;">{away_abbr}</span>
                    <span style="color:#888;font-size:0.75rem;margin-left:4px;">{away_record}</span>
                </td>
                {half_scores_away}
                <td style="padding:2px 8px;font-weight:900;font-size:1.2rem;color:{'#fff' if away_score >= home_score else '#888'};text-align:center;">{away_score}</td>
            </tr>
            <tr>
                <td style="text-align:left;">
                    {h_logo_img}{h_rank_badge}
                    <span style="color:{home_color};font-weight:700;font-size:1rem;">{home_abbr}</span>
                    <span style="color:#888;font-size:0.75rem;margin-left:4px;">{home_record}</span>
                </td>
                {half_scores_home}
                <td style="padding:2px 8px;font-weight:900;font-size:1.2rem;color:{'#fff' if home_score >= away_score else '#888'};text-align:center;">{home_score}</td>
            </tr>
        </table>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_college_court(game, last_play):
    home_color = get_team_color(game, "home")
    away_color = get_team_color(game, "away")
    home_abbr = game.get("home_abbr", "HOME")
    away_abbr = game.get("away_abbr", "AWAY")
    play_text = ""
    play_badge = ""
    if last_play:
        play_text = last_play.get("text", "")[:80]
        play_badge = get_play_badge(last_play)

    svg = f"""
    <svg viewBox="0 0 500 260" style="width:100%;max-width:500px;margin:auto;display:block;">
        <rect x="10" y="10" width="480" height="240" rx="8" fill="#2d5016" stroke="#fff" stroke-width="2"/>
        <line x1="250" y1="10" x2="250" y2="250" stroke="#fff" stroke-width="1.5" stroke-dasharray="6,4"/>
        <circle cx="250" cy="130" r="35" fill="none" stroke="#fff" stroke-width="1.5"/>
        <rect x="10" y="60" width="80" height="140" rx="0" fill="none" stroke="#fff" stroke-width="1.5"/>
        <rect x="410" y="60" width="80" height="140" rx="0" fill="none" stroke="#fff" stroke-width="1.5"/>
        <path d="M 90 90 A 40 40 0 0 1 90 170" fill="none" stroke="#fff" stroke-width="1.5"/>
        <path d="M 410 90 A 40 40 0 0 0 410 170" fill="none" stroke="#fff" stroke-width="1.5"/>
        <rect x="10" y="100" width="25" height="60" rx="0" fill="none" stroke="#fff" stroke-width="1"/>
        <rect x="465" y="100" width="25" height="60" rx="0" fill="none" stroke="#fff" stroke-width="1"/>
        <text x="60" y="35" fill="{away_color}" font-size="14" font-weight="700" text-anchor="middle">{away_abbr}</text>
        <text x="440" y="35" fill="{home_color}" font-size="14" font-weight="700" text-anchor="middle">{home_abbr}</text>
        <text x="250" y="245" fill="#fff" font-size="9" text-anchor="middle" opacity="0.8">{play_text}</text>
        {play_badge}
    </svg>
    """
    st.markdown(svg, unsafe_allow_html=True)

def get_play_badge(last_play):
    if not last_play:
        return ""
    play_type = ""
    if isinstance(last_play.get("type"), dict):
        play_type = last_play["type"].get("text", "").lower()
    score_val = last_play.get("scoreValue", 0)
    icon, color = get_play_icon(play_type, score_val)
    if not icon:
        return ""
    return f'<text x="250" y="140" fill="{color}" font-size="28" text-anchor="middle">{icon}</text>'

def get_play_icon(play_type, score_value):
    pt = str(play_type).lower()
    if score_value == 3:
        return "🎯", "#FFD700"
    elif score_value == 2:
        return "🏀", "#00ff88"
    elif score_value == 1:
        return "🎯", "#87CEEB"
    elif "block" in pt:
        return "🖐️", "#ff4444"
    elif "steal" in pt or "turnover" in pt:
        return "💨", "#ff8800"
    elif "rebound" in pt:
        return "📏", "#aaaaaa"
    elif "foul" in pt:
        return "⚠️", "#ffcc00"
    elif "timeout" in pt:
        return "⏸️", "#ffffff"
    return "", ""

# ============================================================
# TIEBREAKER PANEL — Parse plays for turnovers per team/half
# ============================================================
def calc_tiebreaker_stats(plays, home_abbr, away_abbr):
    stats = {
        "home": {"name": home_abbr, "turnovers": 0, "steals": 0, "made_fg": 0, "missed_fg": 0, "rebounds": 0, "assists": 0, "by_half": {}},
        "away": {"name": away_abbr, "turnovers": 0, "steals": 0, "made_fg": 0, "missed_fg": 0, "rebounds": 0, "assists": 0, "by_half": {}},
    }
    if not plays:
        return stats
    for p in plays:
        if not isinstance(p, dict):
            continue
        text = p.get("text", "").lower()
        period = p.get("period", {}).get("number", 0) if isinstance(p.get("period"), dict) else 0
        if period == 0:
            period = p.get("period", 0) if isinstance(p.get("period"), (int, float)) else 0
        if period <= 2:
            half_key = f"H{period}"
        elif period > 2:
            half_key = f"OT{period - 2}"
        else:
            half_key = "H1"
        team_id = ""
        if isinstance(p.get("team"), dict):
            team_id = p["team"].get("id", "")
        home_lower = home_abbr.lower()
        away_lower = away_abbr.lower()
        is_home = home_lower in text
        is_away = away_lower in text
        if not is_home and not is_away:
            continue
        side = "home" if is_home and not is_away else "away" if is_away and not is_home else None
        if side is None:
            if "turnover" in text:
                words = text.split()
                for i, w in enumerate(words):
                    if "turnover" in w:
                        before = " ".join(words[:i]).lower()
                        if home_lower in before:
                            side = "home"
                        elif away_lower in before:
                            side = "away"
                        break
            if side is None:
                continue
        if half_key not in stats[side]["by_half"]:
            stats[side]["by_half"][half_key] = {"turnovers": 0, "steals": 0, "made_fg": 0, "missed_fg": 0, "rebounds": 0, "assists": 0}
        h = stats[side]["by_half"][half_key]
        if "turnover" in text:
            stats[side]["turnovers"] += 1
            h["turnovers"] += 1
        if "steal" in text:
            other = "away" if side == "home" else "home"
            stats[other]["steals"] += 1
            if half_key not in stats[other]["by_half"]:
                stats[other]["by_half"][half_key] = {"turnovers": 0, "steals": 0, "made_fg": 0, "missed_fg": 0, "rebounds": 0, "assists": 0}
            stats[other]["by_half"][half_key]["steals"] += 1
        if "made" in text and ("three" in text or "jumper" in text or "layup" in text or "dunk" in text or "hook" in text or "tip" in text or "shot" in text or "pointer" in text or "free throw" in text):
            stats[side]["made_fg"] += 1
            h["made_fg"] += 1
        if "missed" in text or "miss" in text:
            stats[side]["missed_fg"] += 1
            h["missed_fg"] += 1
        if "rebound" in text:
            stats[side]["rebounds"] += 1
            h["rebounds"] += 1
        if "assist" in text:
            stats[side]["assists"] += 1
            h["assists"] += 1
    return stats

def render_tiebreaker_panel(stats, home_abbr, away_abbr):
    home = stats["home"]
    away = stats["away"]
    categories = [
        ("Turnovers", away["turnovers"], home["turnovers"], True),
        ("Steals", away["steals"], home["steals"], False),
        ("Rebounds", away["rebounds"], home["rebounds"], False),
        ("Assists", away["assists"], home["assists"], False),
    ]
    away_wins = 0
    home_wins = 0
    rows_html = ""
    all_halves = sorted(set(list(home.get("by_half", {}).keys()) + list(away.get("by_half", {}).keys())))
    for cat_name, a_val, h_val, lower_better in categories:
        if lower_better:
            a_edge = a_val < h_val
            h_edge = h_val < a_val
        else:
            a_edge = a_val > h_val
            h_edge = h_val > a_val
        if a_edge:
            away_wins += 1
        elif h_edge:
            home_wins += 1
        a_color = "#00ff88" if a_edge else "#ff4444" if h_edge else "#888"
        h_color = "#00ff88" if h_edge else "#ff4444" if a_edge else "#888"
        edge_marker_a = " ✅" if a_edge else ""
        edge_marker_h = " ✅" if h_edge else ""
        rows_html += '<tr style="border-bottom:1px solid #333;">'
        rows_html += f'<td style="padding:4px 8px;color:#aaa;font-size:clamp(11px,2.5vw,13px);">{cat_name}</td>'
        rows_html += f'<td style="padding:4px 8px;text-align:center;color:{a_color};font-weight:700;font-size:clamp(12px,2.8vw,14px);">{a_val}{edge_marker_a}</td>'
        rows_html += f'<td style="padding:4px 8px;text-align:center;color:{h_color};font-weight:700;font-size:clamp(12px,2.8vw,14px);">{h_val}{edge_marker_h}</td>'
        rows_html += '</tr>'
    half_rows = ""
    for hk in all_halves:
        a_to = away.get("by_half", {}).get(hk, {}).get("turnovers", 0)
        h_to = home.get("by_half", {}).get(hk, {}).get("turnovers", 0)
        a_c = "#00ff88" if a_to < h_to else "#ff4444" if a_to > h_to else "#888"
        h_c = "#00ff88" if h_to < a_to else "#ff4444" if h_to > a_to else "#888"
        half_rows += '<tr style="border-bottom:1px solid #222;">'
        half_rows += f'<td style="padding:3px 8px;color:#666;font-size:clamp(10px,2.2vw,12px);">TO in {hk}</td>'
        half_rows += f'<td style="padding:3px 8px;text-align:center;color:{a_c};font-size:clamp(10px,2.2vw,12px);">{a_to}</td>'
        half_rows += f'<td style="padding:3px 8px;text-align:center;color:{h_c};font-size:clamp(10px,2.2vw,12px);">{h_to}</td>'
        half_rows += '</tr>'
    if away_wins > home_wins:
        verdict = f"Lean {away_abbr} ({away_wins}-{home_wins} on tiebreakers)"
        v_color = "#00ff88"
    elif home_wins > away_wins:
        verdict = f"Lean {home_abbr} ({home_wins}-{away_wins} on tiebreakers)"
        v_color = "#00ff88"
    else:
        verdict = f"Even {away_wins}-{home_wins} — true coin flip"
        v_color = "#f0c040"
    html = '<div style="max-width:100%;box-sizing:border-box;background:linear-gradient(135deg,#1a1a2e,#16213e);border-radius:10px;padding:12px;margin:8px 0;border:1px solid #f0c040;">'
    html += '<div style="color:#f0c040;font-weight:700;font-size:clamp(13px,3vw,16px);margin-bottom:8px;">⚖️ TIEBREAKER PANEL (game within 5 pts)</div>'
    html += '<table style="width:100%;border-collapse:collapse;table-layout:fixed;">'
    html += '<tr style="border-bottom:1px solid #444;">'
    html += f'<th style="text-align:left;padding:4px 8px;color:#888;font-size:clamp(10px,2.5vw,12px);width:35%;">Stat</th>'
    html += f'<th style="text-align:center;padding:4px 8px;color:#888;font-size:clamp(10px,2.5vw,12px);">{away_abbr}</th>'
    html += f'<th style="text-align:center;padding:4px 8px;color:#888;font-size:clamp(10px,2.5vw,12px);">{home_abbr}</th>'
    html += '</tr>'
    html += rows_html
    html += half_rows
    html += '</table>'
    html += f'<div style="margin-top:8px;color:{v_color};font-weight:700;font-size:clamp(12px,3vw,15px);">{verdict}</div>'
    html += '</div>'
    return html

# === END PART A — PASTE PART B BELOW THIS LINE ===
# ============================================================
# PART B — UI LAYER (paste below Part A)
# ============================================================

# --- Fetch All Data ---
games = fetch_espn_games()
kalshi_ml_data = fetch_kalshi_ml()
injuries = fetch_injuries()
b2b_teams = fetch_yesterday_teams()

# --- Categorize Games ---
live_games = [g for g in games if g.get('state') == 'in']
scheduled_games = [g for g in games if g.get('state') == 'pre']
final_games = [g for g in games if g.get('state') == 'post']

# --- Run Comeback Checks on Live Games ---
for g in live_games:
    check_comeback(g, kalshi_ml_data)

# --- Inject CSS ---
st.markdown(MOBILE_CSS, unsafe_allow_html=True)

# --- Header ---
st.title("BIGSNAPSHOT NCAAW EDGE FINDER")
st.caption(f"v{VERSION} | {now.strftime('%A %B %d, %Y %I:%M %p ET')} | NCAA Women's Basketball | 9-Factor Edge + Cushion Scanner + SHARK")

mc1, mc2, mc3, mc4 = st.columns(4)
mc1.metric("Today's Games", len(games))
mc2.metric("Live Now", len(live_games))
mc3.metric("Scheduled", len(scheduled_games))
mc4.metric("Final", len(final_games))

# ============================================================
# PACE SCANNER (always visible)
# ============================================================
if live_games:
    pace_games = []
    for g in live_games:
        period = g.get("period", 0)
        clock = g.get("clock", "0:00")
        mins_el = calc_minutes_elapsed(period, clock)
        if mins_el >= 4:
            total_sc = g.get("home_score", 0) + g.get("away_score", 0)
            pace = total_sc / mins_el if mins_el > 0 else 0
            proj = calc_projection(total_sc, mins_el)
            label, color = get_pace_label(pace)
            pace_games.append({
                "game": g,
                "mins": mins_el,
                "total": total_sc,
                "pace": pace,
                "proj": proj,
                "label": label,
                "color": color,
            })
    if pace_games:
        pace_games.sort(key=lambda x: x["pace"], reverse=True)
        st.markdown("### 📊 Live Pace Scanner")
        pace_html = '<div style="max-width:100%;overflow-x:auto;">'
        pace_html += '<table style="width:100%;border-collapse:collapse;table-layout:fixed;">'
        pace_html += '<tr style="border-bottom:1px solid #444;">'
        pace_html += '<th style="text-align:left;padding:4px;color:#aaa;font-size:clamp(10px,2.5vw,13px);">Game</th>'
        pace_html += '<th style="text-align:center;padding:4px;color:#aaa;font-size:clamp(10px,2.5vw,13px);">Score</th>'
        pace_html += '<th style="text-align:center;padding:4px;color:#aaa;font-size:clamp(10px,2.5vw,13px);">Min</th>'
        pace_html += '<th style="text-align:center;padding:4px;color:#aaa;font-size:clamp(10px,2.5vw,13px);">Pace</th>'
        pace_html += '<th style="text-align:center;padding:4px;color:#aaa;font-size:clamp(10px,2.5vw,13px);">Proj</th>'
        pace_html += '<th style="text-align:center;padding:4px;color:#aaa;font-size:clamp(10px,2.5vw,13px);">Tempo</th>'
        pace_html += '</tr>'
        for pg in pace_games:
            gg = pg["game"]
            away_c = get_team_color(gg, "away")
            home_c = get_team_color(gg, "home")
            pace_html += f'<tr style="border-bottom:1px solid #333;">'
            pace_html += f'<td style="padding:4px;font-size:clamp(11px,2.8vw,14px);"><span style="color:{away_c};font-weight:700;">{gg.get("away_abbr","")}</span> @ <span style="color:{home_c};font-weight:700;">{gg.get("home_abbr","")}</span></td>'
            pace_html += f'<td style="text-align:center;padding:4px;font-size:clamp(11px,2.8vw,14px);color:#fff;font-weight:700;">{gg.get("away_score",0)}-{gg.get("home_score",0)}</td>'
            pace_html += f'<td style="text-align:center;padding:4px;font-size:clamp(11px,2.8vw,14px);color:#ccc;">{pg["mins"]:.1f}</td>'
            pace_html += f'<td style="text-align:center;padding:4px;font-size:clamp(11px,2.8vw,14px);color:{pg["color"]};font-weight:700;">{pg["pace"]:.2f}</td>'
            pace_html += f'<td style="text-align:center;padding:4px;font-size:clamp(11px,2.8vw,14px);color:#fff;font-weight:700;">{pg["proj"]:.0f}</td>'
            pace_html += f'<td style="text-align:center;padding:4px;font-size:clamp(11px,2.8vw,14px);color:{pg["color"]};font-weight:700;">{pg["label"]}</td>'
            pace_html += '</tr>'
        pace_html += '</table></div>'
        st.markdown(pace_html, unsafe_allow_html=True)
        st.markdown("")

# ============================================================
# TABS (4 tabs — no Spread Sniper)
# ============================================================
tab_edge, tab_live, tab_cushion, tab_shark = st.tabs(["Edge Finder", "Live Monitor", "Cushion Scanner", "🦈 SHARK"])

# ============================================================
# TAB 1: EDGE FINDER
# ============================================================
with tab_edge:
    st.markdown("### 🎯 Pre-Game 9-Factor Edge Model")
    st.caption("Analyzes record gap, ranking gap, home court, B2B, moneyline, spread, injuries, ESPN predictor, and O/U context")

    # --- Section A: Strong + Moderate Edges ---
    pre_games = [g for g in games if g.get('state') == 'pre']
    if pre_games:
        edge_results = []
        for g in pre_games:
            summary = None
            try:
                summary = fetch_game_summary(g.get("game_id", ""))
            except:
                pass
            edge = calc_advanced_edge(g, b2b_teams, summary=summary, injuries=injuries)
            edge_results.append({"game": g, "edge": edge, "summary": summary})
        edge_results.sort(key=lambda x: x["edge"]["edge_pct"], reverse=True)

        strong = [e for e in edge_results if e["edge"]["edge_pct"] >= 60]
        moderate = [e for e in edge_results if 40 <= e["edge"]["edge_pct"] < 60]

        if strong:
            st.markdown("#### 🔥 STRONG EDGES (A or A+)")
            for er in strong:
                g = er["game"]
                edge = er["edge"]
                home_c = get_team_color(g, "home")
                away_c = get_team_color(g, "away")
                h_rank = g.get("home_rank", 99)
                a_rank = g.get("away_rank", 99)
                h_rk = f"#{h_rank} " if h_rank < 26 else ""
                a_rk = f"#{a_rank} " if a_rank < 26 else ""

                grade_colors = {"A+": "#00ff88", "A": "#00cc66", "B+": "#f0c040", "B": "#f09040", "C": "#ff4444", "D": "#888"}
                g_color = grade_colors.get(edge["grade"], "#888")

                card_html = f"""
                <div style="max-width:100%;box-sizing:border-box;overflow-x:hidden;background:linear-gradient(135deg,#1a1a2e,#16213e);border-radius:12px;padding:15px;margin:8px 0;border-left:4px solid {g_color};">
                    <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;">
                        <div style="font-size:clamp(14px,3.5vw,18px);font-weight:700;">
                            <span style="color:{away_c};">{a_rk}{g.get('away_abbr','')}</span>
                            <span style="color:#888;"> @ </span>
                            <span style="color:{home_c};">{h_rk}{g.get('home_abbr','')}</span>
                        </div>
                        <div style="font-size:clamp(22px,5vw,32px);font-weight:900;color:{g_color};">{edge.get('grade','')}</div>
                    </div>
                    <div style="color:#aaa;font-size:clamp(11px,2.5vw,13px);margin:4px 0;">
                        Edge: {edge.get('edge_pct',0):.0f}% | Fav: {edge.get('fav_label','')} | {g.get('detail','')}
                    </div>
                    <div style="margin-top:8px;">
                """
                for f in edge.get("factors", []):
                    f_pts = f.get("pts", 0)
                    max_f = 15
                    pct = max(0, min(100, f_pts / max_f * 100)) if max_f > 0 else 0
                    bar_color = "#00ff88" if f_pts >= 10 else "#f0c040" if f_pts >= 5 else "#555"
                    card_html += f"""
                        <div style="display:flex;align-items:center;margin:3px 0;font-size:clamp(10px,2.5vw,12px);">
                            <span style="color:#aaa;width:110px;min-width:80px;">{f.get('name','')}</span>
                            <div style="flex:1;height:8px;background:#333;border-radius:4px;margin:0 6px;">
                                <div style="width:{pct}%;height:100%;background:{bar_color};border-radius:4px;"></div>
                            </div>
                            <span style="color:{bar_color};font-weight:700;min-width:25px;text-align:right;">{f_pts}</span>
                        </div>
                    """
                card_html += "</div></div>"
                st.markdown(card_html, unsafe_allow_html=True)

        if moderate:
            st.markdown("#### ⚡ MODERATE EDGES (B+)")
            for er in moderate:
                g = er["game"]
                edge = er["edge"]
                home_c = get_team_color(g, "home")
                away_c = get_team_color(g, "away")
                h_rank = g.get("home_rank", 99)
                a_rank = g.get("away_rank", 99)
                h_rk = f"#{h_rank} " if h_rank < 26 else ""
                a_rk = f"#{a_rank} " if a_rank < 26 else ""
                g_color = "#f0c040"

                card_html = f"""
                <div style="max-width:100%;box-sizing:border-box;overflow-x:hidden;background:linear-gradient(135deg,#1a1a2e,#16213e);border-radius:12px;padding:15px;margin:8px 0;border-left:4px solid {g_color};">
                    <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;">
                        <div style="font-size:clamp(14px,3.5vw,18px);font-weight:700;">
                            <span style="color:{away_c};">{a_rk}{g.get('away_abbr','')}</span>
                            <span style="color:#888;"> @ </span>
                            <span style="color:{home_c};">{h_rk}{g.get('home_abbr','')}</span>
                        </div>
                        <div style="font-size:clamp(22px,5vw,32px);font-weight:900;color:{g_color};">{edge.get('grade','')}</div>
                    </div>
                    <div style="color:#aaa;font-size:clamp(11px,2.5vw,13px);margin:4px 0;">
                        Edge: {edge.get('edge_pct',0):.0f}% | Fav: {edge.get('fav_label','')} | {g.get('detail','')}
                    </div>
                </div>
                """
                st.markdown(card_html, unsafe_allow_html=True)

        if not strong and not moderate:
            st.info("No strong or moderate edges detected for upcoming games.")
    else:
        st.info("No pre-game matchups available right now.")

    st.markdown("---")

    # --- Section B: Vegas vs Kalshi Mispricing ---
    st.markdown("### 💰 Vegas vs Kalshi Mispricing Alert")
    misprice_found = False
    for g in pre_games:
        home_ml = g.get("home_ml", 0)
        away_ml = g.get("away_ml", 0)
        home_imp = american_to_implied_prob(home_ml)
        away_imp = american_to_implied_prob(away_ml)
        if not home_imp or not away_imp:
            continue
        home_kalshi = find_ml_price_for_team(kalshi_ml_data, g.get("home_abbr", ""), g.get("home_name", ""))
        away_kalshi = find_ml_price_for_team(kalshi_ml_data, g.get("away_abbr", ""), g.get("away_name", ""))

        for side, vegas_imp, kalshi_m, abbr in [
            ("home", home_imp, home_kalshi, g.get("home_abbr", "")),
            ("away", away_imp, away_kalshi, g.get("away_abbr", "")),
        ]:
            if kalshi_m:
                yes_ask = kalshi_m.get("yes_ask", 0)
                if yes_ask > 0:
                    kalshi_imp = yes_ask / 100.0
                    diff = vegas_imp - kalshi_imp
                    if abs(diff) >= 0.05:
                        misprice_found = True
                        direction = "CHEAPER on Kalshi ✅" if diff > 0 else "EXPENSIVE on Kalshi ⚠️"
                        d_color = "#00ff88" if diff > 0 else "#ff4444"
                        st.markdown(f"""
                        <div style="max-width:100%;box-sizing:border-box;background:#1a1a2e;border-radius:10px;padding:12px;margin:6px 0;border-left:3px solid {d_color};">
                            <span style="color:#fff;font-weight:700;font-size:clamp(13px,3vw,16px);">{abbr}</span>
                            <span style="color:#aaa;font-size:clamp(11px,2.5vw,13px);"> — Vegas: {vegas_imp:.0%} | Kalshi: {kalshi_imp:.0%} | Gap: {abs(diff):.0%}</span><br>
                            <span style="color:{d_color};font-weight:700;font-size:clamp(12px,2.8vw,14px);">{direction}</span>
                        </div>
                        """, unsafe_allow_html=True)
    if not misprice_found:
        st.info("No significant Vegas vs Kalshi mispricings detected (>5% gap).")

    st.markdown("---")

    # --- Section C: Injury Report ---
    st.markdown("### 🏥 Injury Report")
    if injuries:
        today_abbrs = set()
        for g in games:
            today_abbrs.add(g.get("home_abbr", ""))
            today_abbrs.add(g.get("away_abbr", ""))
        relevant_inj = {k: v for k, v in injuries.items() if k in today_abbrs}
        if relevant_inj:
            for team_abbr, inj_list in sorted(relevant_inj.items()):
                inj_strs = []
                for inj in inj_list:
                    inj_strs.append(f"{inj.get('name', 'Unknown')} ({inj.get('status', '?')})")
                st.markdown(f"**{team_abbr}**: {', '.join(inj_strs)}")
        else:
            st.info("No injuries reported for today's teams.")
    else:
        st.info("No injury data available.")

    st.markdown("---")

    # --- Section D: Position Tracker ---
    st.markdown("### 📋 Position Tracker")
    with st.expander("➕ Add Position", expanded=False):
        pt_cols = st.columns([2, 1, 1, 1])
        all_teams = []
        for g in games:
            all_teams.append(g.get("home_abbr", ""))
            all_teams.append(g.get("away_abbr", ""))
        all_teams = sorted(set(all_teams))
        if all_teams:
            sel_team = pt_cols[0].selectbox("Team", all_teams, key="ncaaw_pos_team")
            sel_side = pt_cols[1].selectbox("Side", ["YES", "NO"], key="ncaaw_pos_side")
            sel_price = pt_cols[2].number_input("Entry ¢", min_value=1, max_value=99, value=50, key="ncaaw_pos_price")
            sel_contracts = pt_cols[3].number_input("Contracts", min_value=1, max_value=1000, value=10, key="ncaaw_pos_contracts")
            if st.button("Add Position", key="ncaaw_pos_add", use_container_width=True):
                new_pos = {
                    "id": str(uuid.uuid4())[:8],
                    "team": sel_team,
                    "side": sel_side,
                    "price": sel_price,
                    "contracts": sel_contracts,
                    "type": "Moneyline",
                    "time": now.strftime("%I:%M %p"),
                }
                st.session_state.ncaaw_positions.append(new_pos)
                st.rerun()

    if st.session_state.ncaaw_positions:
        for pos in st.session_state.ncaaw_positions:
            cost = pos.get("price", 0) * pos.get("contracts", 0)
            max_profit = (100 - pos.get("price", 0)) * pos.get("contracts", 0) if pos.get("side") == "YES" else pos.get("price", 0) * pos.get("contracts", 0)
            pos_html = f"""
            <div class="pos-card" style="max-width:100%;box-sizing:border-box;">
                <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;">
                    <span style="color:#fff;font-weight:700;font-size:clamp(13px,3vw,16px);">{pos.get('team','')} — {pos.get('side','')} @ {pos.get('price',0)}¢</span>
                    <span style="color:#aaa;font-size:clamp(10px,2.5vw,12px);">ML | {pos.get('contracts',0)} contracts</span>
                </div>
                <div style="color:#aaa;font-size:clamp(10px,2.5vw,12px);margin-top:4px;">
                    Cost: ${cost/100:.2f} | Max Profit: ${max_profit/100:.2f} | Added: {pos.get('time','')}
                </div>
            </div>
            """
            st.markdown(pos_html, unsafe_allow_html=True)
            if st.button(f"Remove {pos.get('id','')}", key=f"ncaaw_pos_rm_{pos.get('id','')}", use_container_width=True):
                remove_position(pos.get("id", ""))
                st.rerun()
    else:
        st.info("No positions tracked. Add one above.")

    st.markdown("---")

    # --- Section E: All Games Today ---
    st.markdown("### 📅 All Games Today")
    if games:
        for g in games:
            state = g.get("state", "pre")
            home_c = get_team_color(g, "home")
            away_c = get_team_color(g, "away")
            h_rank = g.get("home_rank", 99)
            a_rank = g.get("away_rank", 99)
            h_rk = f"#{h_rank} " if h_rank < 26 else ""
            a_rk = f"#{a_rank} " if a_rank < 26 else ""
            if state == "in":
                badge = "🟢 LIVE"
            elif state == "post":
                badge = "✅ FINAL"
            else:
                badge = f"🕐 {g.get('detail', 'Scheduled')}"
            row_html = f"""
            <div style="max-width:100%;box-sizing:border-box;background:#111;border-radius:8px;padding:8px 12px;margin:4px 0;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;">
                <div style="font-size:clamp(12px,3vw,15px);">
                    <span style="color:{away_c};font-weight:700;">{a_rk}{g.get('away_abbr','')}</span>
                    <span style="color:#888;"> @ </span>
                    <span style="color:{home_c};font-weight:700;">{h_rk}{g.get('home_abbr','')}</span>
                </div>
                <div style="font-size:clamp(11px,2.5vw,13px);">
                    <span style="color:{'#00ff88' if state == 'in' else '#aaa'};">{badge}</span>
                    {'<span style="color:#fff;font-weight:700;margin-left:8px;">' + str(g.get("away_score",0)) + '-' + str(g.get("home_score",0)) + '</span>' if state != 'pre' else ''}
                </div>
            </div>
            """
            st.markdown(row_html, unsafe_allow_html=True)
    else:
        st.info("No games scheduled today.")

    st.link_button("🔗 Kalshi NCAAW Games", KALSHI_GAME_LINK, use_container_width=True)

# ============================================================
# TAB 2: LIVE MONITOR
# ============================================================
with tab_live:
    st.markdown("### 📺 Live Game Monitor")
    if live_games:
        for g in live_games:
            game_id = g.get("game_id", "")
            render_scoreboard(g)

            # Fetch plays and summary
            plays = fetch_plays(game_id)
            possession, last_play = infer_possession(plays, g.get("home_abbr", ""), g.get("away_abbr", ""))

            col_court, col_info = st.columns([1, 1])
            with col_court:
                render_college_court(g, last_play)
                if last_play:
                    play_text = last_play.get("text", "")
                    st.caption(f"📢 {play_text[:120]}")
                if possession:
                    poss_color = get_team_color(g, "home") if possession == g.get("home_abbr") else get_team_color(g, "away")
                    st.markdown(f'<span style="color:{poss_color};font-weight:700;">🏀 Possession: {possession}</span>', unsafe_allow_html=True)

            with col_info:
                # Pace
                period = g.get("period", 0)
                clock = g.get("clock", "0:00")
                mins_el = calc_minutes_elapsed(period, clock)
                total_sc = g.get("home_score", 0) + g.get("away_score", 0)
                if mins_el >= 2:
                    pace = total_sc / mins_el
                    proj = calc_projection(total_sc, mins_el)
                    label, color = get_pace_label(pace)
                    st.markdown(f"""
                    <div style="max-width:100%;box-sizing:border-box;background:#1a1a2e;border-radius:8px;padding:10px;margin:4px 0;">
                        <span style="color:#aaa;font-size:clamp(10px,2.5vw,12px);">Pace:</span>
                        <span style="color:{color};font-weight:700;font-size:clamp(13px,3vw,16px);">{pace:.2f} pts/min {label}</span><br>
                        <span style="color:#aaa;font-size:clamp(10px,2.5vw,12px);">Projected Total:</span>
                        <span style="color:#fff;font-weight:700;font-size:clamp(13px,3vw,16px);">{proj:.0f}</span>
                    </div>
                    """, unsafe_allow_html=True)

                # Win Probability
                wp = fetch_espn_win_prob(game_id)
                home_wp = wp * 100
                away_wp = (1 - wp) * 100
                home_c = get_team_color(g, "home")
                away_c = get_team_color(g, "away")
                st.markdown(f"""
                <div style="max-width:100%;box-sizing:border-box;background:#1a1a2e;border-radius:8px;padding:10px;margin:4px 0;">
                    <span style="color:#aaa;font-size:clamp(10px,2.5vw,12px);">Win Probability:</span><br>
                    <span style="color:{away_c};font-weight:700;font-size:clamp(12px,2.8vw,14px);">{g.get('away_abbr','')}: {away_wp:.0f}%</span>
                    <span style="color:#888;"> | </span>
                    <span style="color:{home_c};font-weight:700;font-size:clamp(12px,2.8vw,14px);">{g.get('home_abbr','')}: {home_wp:.0f}%</span>
                </div>
                """, unsafe_allow_html=True)

                # ML Edge
                for side in ["home", "away"]:
                    abbr = g.get(f"{side}_abbr", "")
                    ml_val = g.get(f"{side}_ml", 0)
                    vegas_imp = american_to_implied_prob(ml_val)
                    kalshi_m = find_ml_price_for_team(kalshi_ml_data, abbr, g.get(f"{side}_name", ""))
                    if vegas_imp and kalshi_m:
                        yes_ask = kalshi_m.get("yes_ask", 0)
                        if yes_ask > 0:
                            kalshi_imp = yes_ask / 100.0
                            diff = vegas_imp - kalshi_imp
                            if abs(diff) >= 0.03:
                                d_color = "#00ff88" if diff > 0 else "#ff4444"
                                tag = "CHEAP" if diff > 0 else "EXPENSIVE"
                                st.markdown(f'<span style="color:{d_color};font-size:clamp(11px,2.5vw,13px);">💰 {abbr}: {tag} on Kalshi (Vegas {vegas_imp:.0%} vs Kalshi {kalshi_imp:.0%})</span>', unsafe_allow_html=True)

                # Comeback Tracker
                if game_id in st.session_state.ncaaw_comeback_tracking:
                    trk = st.session_state.ncaaw_comeback_tracking[game_id]
                    current_lead = abs(g.get("home_score", 0) - g.get("away_score", 0))
                    comeback_amt = trk.get("peak_lead", 0) - current_lead
                    if comeback_amt > 0:
                        st.markdown(f"""
                        <div style="max-width:100%;box-sizing:border-box;background:#0a2e1a;border:1px solid #27ae60;border-radius:8px;padding:8px;margin:4px 0;">
                            <span style="color:#27ae60;font-weight:700;font-size:clamp(11px,2.5vw,13px);">🔄 COMEBACK: {trk.get('trailer','')} cut {comeback_amt} pts (peak deficit: {trk.get('peak_lead',0)}, now: {current_lead})</span>
                        </div>
                        """, unsafe_allow_html=True)

            # Tiebreaker Panel — full width, below columns (close games ≤5 pts)
            lead = abs(g.get("home_score", 0) - g.get("away_score", 0))
            mins_el_tb = calc_minutes_elapsed(g.get("period", 0), g.get("clock", "0:00"))
            if lead <= 5 and mins_el_tb >= 4:
                tb_stats = calc_tiebreaker_stats(plays, g.get("home_abbr", ""), g.get("away_abbr", ""))
                tb_html = render_tiebreaker_panel(tb_stats, g.get("home_abbr", ""), g.get("away_abbr", ""))
                st.markdown(tb_html, unsafe_allow_html=True)

            # TTS Toggle
            tts_key = f"ncaaw_tts_{game_id}"
            tts_on = st.checkbox("🔊 Play-by-Play Audio", key=tts_key)
            if tts_on and last_play:
                speak_play(last_play.get("text", ""))

            # Recent Plays
            with st.expander(f"📜 Recent Plays — {g.get('away_abbr','')} @ {g.get('home_abbr','')}", expanded=False):
                if plays:
                    recent = plays[-15:] if len(plays) > 15 else plays
                    for p in reversed(recent):
                        p_text = p.get("text", "")
                        p_clock = p.get("clock", {}).get("displayValue", "") if isinstance(p.get("clock"), dict) else str(p.get("clock", ""))
                        p_score_val = p.get("scoreValue", 0)
                        if p_score_val:
                            st.markdown(f"🏀 **{p_clock}** — {p_text} (+{p_score_val})")
                        else:
                            st.markdown(f"⏱️ **{p_clock}** — {p_text}")
                else:
                    st.info("No play data available.")

            st.markdown("---")
    else:
        st.info("No live games right now. Check back during game times!")

    st.link_button("🔗 Kalshi NCAAW Games", KALSHI_GAME_LINK, use_container_width=True)

# ============================================================
# TAB 3: CUSHION SCANNER
# ============================================================
with tab_cushion:
    st.markdown("### 🛡️ Cushion Scanner")
    st.caption("Find games where one team has a comfortable lead — look for cheap NO contracts on the trailing team's moneyline.")

    cush_filter = st.selectbox("Filter", ["All Live", "Home Leading", "Away Leading"], key="ncaaw_cushion_filter")
    cush_min = st.slider("Minimum Lead", min_value=1, max_value=30, value=6, key="ncaaw_cushion_min")

    cushion_games = []
    for g in live_games:
        lead = abs(g.get("home_score", 0) - g.get("away_score", 0))
        if lead >= cush_min:
            home_leading = g.get("home_score", 0) > g.get("away_score", 0)
            if cush_filter == "Home Leading" and not home_leading:
                continue
            if cush_filter == "Away Leading" and home_leading:
                continue
            cushion_games.append((g, lead, home_leading))

    cushion_games.sort(key=lambda x: x[1], reverse=True)

    if cushion_games:
        for g, lead, home_leading in cushion_games:
            leader = g.get("home_abbr", "") if home_leading else g.get("away_abbr", "")
            trailer = g.get("away_abbr", "") if home_leading else g.get("home_abbr", "")
            leader_c = get_team_color(g, "home" if home_leading else "away")
            trailer_c = get_team_color(g, "away" if home_leading else "home")
            period = g.get("period", 0)
            clock = g.get("clock", "0:00")
            p_label = f"H{period}" if period <= 2 else f"OT{period - 2}"

            trailer_ml = find_ml_price_for_team(kalshi_ml_data, trailer, g.get("away_name" if home_leading else "home_name", ""))
            trailer_yes = trailer_ml.get("yes_ask", 0) if trailer_ml else 0
            trailer_no = trailer_ml.get("no_ask", 0) if trailer_ml else 0

            cush_html = f"""
            <div style="max-width:100%;box-sizing:border-box;background:linear-gradient(135deg,#1a1a2e,#16213e);border-radius:12px;padding:14px;margin:8px 0;border-left:4px solid {leader_c};">
                <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;">
                    <div style="font-size:clamp(14px,3.5vw,18px);font-weight:700;">
                        <span style="color:{leader_c};">{leader}</span>
                        <span style="color:#00ff88;"> +{lead}</span>
                        <span style="color:#888;"> over </span>
                        <span style="color:{trailer_c};">{trailer}</span>
                    </div>
                    <span style="color:#aaa;font-size:clamp(11px,2.5vw,13px);">{p_label} {clock}</span>
                </div>
                <div style="color:#aaa;font-size:clamp(11px,2.5vw,13px);margin-top:6px;">
                    Score: {g.get('away_score',0)}-{g.get('home_score',0)} |
                    {trailer} YES: {trailer_yes}¢ | NO: {trailer_no}¢
                </div>
            </div>
            """
            st.markdown(cush_html, unsafe_allow_html=True)
    else:
        st.info(f"No games with a {cush_min}+ point lead right now.")

    # Comeback Alerts
    if st.session_state.ncaaw_comeback_alerts:
        st.markdown("---")
        st.markdown("#### 🔄 Comeback Alerts")
        for cb in reversed(st.session_state.ncaaw_comeback_alerts[-10:]):
            cb_html = f"""
            <div class="comeback-alert" style="max-width:100%;box-sizing:border-box;">
                <div style="font-size:clamp(14px,3.5vw,18px);font-weight:700;color:#27ae60;">🔄 COMEBACK DETECTED</div>
                <div style="color:#fff;font-size:clamp(12px,3vw,15px);margin:6px 0;">
                    {cb.get('trailer','')} closing in! Peak deficit: {cb.get('peak_lead',0)} → Now: {cb.get('current_lead',0)} ({cb.get('comeback_pts',0)} pts recovered)
                </div>
                <div style="color:#aaa;font-size:clamp(11px,2.5vw,13px);">
                    {cb.get('trailer','')} ML NO: {cb.get('no_price',0)}¢ | {cb.get('time','')}
                </div>
            </div>
            """
            st.markdown(cb_html, unsafe_allow_html=True)

    st.link_button("🔗 Kalshi NCAAW Games", KALSHI_GAME_LINK, use_container_width=True)

# ============================================================
# TAB 4: 🦈 SHARK
# ============================================================
with tab_shark:
    st.markdown("### 🦈 SHARK — Smart Hedge & Autolock Recognition Kit")
    st.caption("Late-game lock detection: Find games where one team has a commanding lead with little time left. Buy NO on the trailing team's moneyline.")

    SHARK_MIN_LEAD = 7
    SHARK_MINUTES_LEFT = 5.0

    shark_games = []
    for g in live_games:
        period = g.get("period", 0)
        clock = g.get("clock", "0:00")
        mins_el = calc_minutes_elapsed(period, clock)
        mins_left = GAME_MINUTES - mins_el
        lead = abs(g.get("home_score", 0) - g.get("away_score", 0))
        if lead >= SHARK_MIN_LEAD and mins_left <= SHARK_MINUTES_LEFT and mins_left >= 0:
            home_leading = g.get("home_score", 0) > g.get("away_score", 0)
            shark_games.append({
                "game": g,
                "lead": lead,
                "mins_left": mins_left,
                "mins_el": mins_el,
                "home_leading": home_leading,
            })

    shark_games.sort(key=lambda x: x["lead"], reverse=True)

    # Shark Filters
    st.markdown("#### 🦈 SHARK Scanner")
    shark_side_filter = st.selectbox("Leader Filter", ["All", "Home Leading", "Away Leading"], key="ncaaw_shark_side")
    shark_min_lead = st.slider("Min SHARK Lead", min_value=5, max_value=25, value=SHARK_MIN_LEAD, key="ncaaw_shark_min")

    filtered_sharks = []
    for sg in shark_games:
        if sg["lead"] < shark_min_lead:
            continue
        if shark_side_filter == "Home Leading" and not sg["home_leading"]:
            continue
        if shark_side_filter == "Away Leading" and sg["home_leading"]:
            continue
        filtered_sharks.append(sg)

    if filtered_sharks:
        for sg in filtered_sharks:
            g = sg["game"]
            lead = sg["lead"]
            mins_left = sg["mins_left"]
            home_leading = sg["home_leading"]
            leader_abbr = g.get("home_abbr", "") if home_leading else g.get("away_abbr", "")
            trailer_abbr = g.get("away_abbr", "") if home_leading else g.get("home_abbr", "")
            leader_c = get_team_color(g, "home" if home_leading else "away")
            trailer_c = get_team_color(g, "away" if home_leading else "home")
            period = g.get("period", 0)
            clock = g.get("clock", "0:00")
            p_label = f"H{period}" if period <= 2 else f"OT{period - 2}"

            trailer_ml = find_ml_price_for_team(kalshi_ml_data, trailer_abbr, g.get("away_name" if home_leading else "home_name", ""))
            trailer_yes = trailer_ml.get("yes_ask", 0) if trailer_ml else 0
            trailer_no = trailer_ml.get("no_ask", 0) if trailer_ml else 0

            confidence = "🟢 HIGH" if lead >= 15 and mins_left <= 2 else "🟡 MEDIUM" if lead >= 10 else "🔴 WATCH"
            conf_color = "#00ff88" if "HIGH" in confidence else "#f0c040" if "MEDIUM" in confidence else "#ff4444"

            shark_html = f"""
            <div style="max-width:100%;box-sizing:border-box;background:linear-gradient(135deg,#0a1628,#1a2a4a);border-radius:12px;padding:15px;margin:8px 0;border:2px solid {conf_color};">
                <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;">
                    <div>
                        <span style="font-size:clamp(16px,4vw,22px);font-weight:900;color:{leader_c};">🦈 {leader_abbr} +{lead}</span>
                        <span style="color:#888;font-size:clamp(12px,3vw,15px);"> over </span>
                        <span style="color:{trailer_c};font-weight:700;font-size:clamp(14px,3.5vw,18px);">{trailer_abbr}</span>
                    </div>
                    <div style="text-align:right;">
                        <span style="color:{conf_color};font-weight:700;font-size:clamp(12px,3vw,15px);">{confidence}</span><br>
                        <span style="color:#aaa;font-size:clamp(10px,2.5vw,13px);">{p_label} {clock} | {mins_left:.1f} min left</span>
                    </div>
                </div>
                <div style="color:#aaa;font-size:clamp(11px,2.5vw,13px);margin-top:8px;">
                    Score: {g.get('away_score',0)}-{g.get('home_score',0)} |
                    {trailer_abbr} YES: {trailer_yes}¢ | NO: {trailer_no}¢
                </div>
                <div style="margin-top:6px;color:#888;font-size:clamp(10px,2.2vw,12px);">
                    💡 If {leader_abbr} holds, {trailer_abbr} YES → $0. Buy NO on {trailer_abbr} ML if price is right.
                </div>
            </div>
            """
            st.markdown(shark_html, unsafe_allow_html=True)

            # Expander with court + plays
            with st.expander(f"🦈 {g.get('away_abbr','')} @ {g.get('home_abbr','')} — Plays & Court", expanded=False):
                plays = fetch_plays(g.get("game_id", ""))
                possession, last_play = infer_possession(plays, g.get("home_abbr", ""), g.get("away_abbr", ""))
                render_college_court(g, last_play)
                if last_play:
                    st.caption(f"📢 {last_play.get('text', '')[:120]}")
                tts_shark_key = f"ncaaw_shark_tts_{g.get('game_id','')}"
                tts_shark = st.checkbox("🔊 Audio", key=tts_shark_key)
                if tts_shark and last_play:
                    speak_play(last_play.get("text", ""))
                if plays:
                    recent = plays[-10:] if len(plays) > 10 else plays
                    for p in reversed(recent):
                        p_text = p.get("text", "")
                        p_clock = p.get("clock", {}).get("displayValue", "") if isinstance(p.get("clock"), dict) else str(p.get("clock", ""))
                        p_sv = p.get("scoreValue", 0)
                        if p_sv:
                            st.markdown(f"🏀 **{p_clock}** — {p_text} (+{p_sv})")
                        else:
                            st.markdown(f"⏱️ **{p_clock}** — {p_text}")
    else:
        st.info(f"No SHARK opportunities right now (need {shark_min_lead}+ lead with ≤{SHARK_MINUTES_LEFT:.0f} min left).")

    st.markdown("---")

    # Shark Pace Scanner
    st.markdown("#### 🦈 SHARK Pace Scanner")
    if live_games:
        shark_pace = []
        for g in live_games:
            period = g.get("period", 0)
            clock = g.get("clock", "0:00")
            mins_el = calc_minutes_elapsed(period, clock)
            if mins_el >= 4:
                total_sc = g.get("home_score", 0) + g.get("away_score", 0)
                pace = total_sc / mins_el
                proj = calc_projection(total_sc, mins_el)
                label, color = get_pace_label(pace)
                shark_pace.append({"game": g, "pace": pace, "proj": proj, "label": label, "color": color, "mins": mins_el})
        shark_pace.sort(key=lambda x: x["pace"], reverse=True)
        if shark_pace:
            for sp in shark_pace:
                gg = sp["game"]
                away_c = get_team_color(gg, "away")
                home_c = get_team_color(gg, "home")
                sp_html = f"""
                <div style="max-width:100%;box-sizing:border-box;background:#111;border-radius:8px;padding:8px 12px;margin:4px 0;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;">
                    <span style="font-size:clamp(12px,3vw,15px);">
                        <span style="color:{away_c};font-weight:700;">{gg.get('away_abbr','')}</span>
                        <span style="color:#888;"> @ </span>
                        <span style="color:{home_c};font-weight:700;">{gg.get('home_abbr','')}</span>
                    </span>
                    <span style="color:{sp['color']};font-weight:700;font-size:clamp(12px,3vw,15px);">{sp['pace']:.2f} pts/min {sp['label']} | Proj: {sp['proj']:.0f}</span>
                </div>
                """
                st.markdown(sp_html, unsafe_allow_html=True)
        else:
            st.info("Not enough game time elapsed for pace data.")
    else:
        st.info("No live games for pace scanning.")

    st.link_button("🔗 Kalshi NCAAW Games", KALSHI_GAME_LINK, use_container_width=True)

# ============================================================
# FOOTER
# ============================================================
st.divider()
st.caption(f"v{VERSION} | Educational only | Not financial advice")
st.caption("Stay small. Stay quiet. Win.")
