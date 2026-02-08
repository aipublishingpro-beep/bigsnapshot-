import streamlit as st
from streamlit_autorefresh import st_autorefresh
import streamlit.components.v1 as components
st.set_page_config(page_title="BigSnapshot NCAA Edge Finder", page_icon="🏀", layout="wide")
from auth import require_auth
require_auth()
st_autorefresh(interval=30000, key="ncaa_datarefresh")
import uuid, re, requests, pytz
import requests as req_ga
from datetime import datetime, timedelta

# ── GA4 ──
def send_ga4_event(page_title, page_path):
    try:
        url = "https://www.google-analytics.com/mp/collect?measurement_id=G-NQKY5VQ376&api_secret=n4oBJjH7RXi0dA7aQo2CZA"
        payload = {"client_id": str(uuid.uuid4()), "events": [{"name": "page_view", "params": {"page_title": page_title, "page_location": "https://bigsnapshot.streamlit.app" + page_path}}]}
        req_ga.post(url, json=payload, timeout=2)
    except: pass
send_ga4_event("BigSnapshot NCAA Edge Finder", "/NCAA")

# ── Timezone + Constants ──
eastern = pytz.timezone("US/Eastern")
now = datetime.now(eastern)
VERSION = "3.0"
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
KALSHI_GAME_LINK = "https://kalshi.com/sports/basketball/college-basketball-m/games"
KALSHI_SPREAD_LINK = "https://kalshi.com/sports/basketball/college-basketball-m/spreads"

# ── Session State ──
if 'ncaa_positions' not in st.session_state: st.session_state.ncaa_positions = []
if 'ncaa_sniper_alerts' not in st.session_state: st.session_state.ncaa_sniper_alerts = []
if 'ncaa_comeback_alerts' not in st.session_state: st.session_state.ncaa_comeback_alerts = []
if 'ncaa_comeback_tracking' not in st.session_state: st.session_state.ncaa_comeback_tracking = {}
if 'ncaa_alerted_games' not in st.session_state: st.session_state.ncaa_alerted_games = set()
if 'ncaa_comeback_alerted' not in st.session_state: st.session_state.ncaa_comeback_alerted = set()

# ── Helper: get_team_color ──
def get_team_color(game, side):
    return game.get(f'{side}_color', '#555555')

# ── Helper: american_to_implied_prob ──
def american_to_implied_prob(odds):
    if odds is None or odds == 0:
        return None
    if odds > 0:
        return 100 / (odds + 100)
    else:
        return abs(odds) / (abs(odds) + 100)

# ── Helper: speak_play ──
def speak_play(text):
    clean = re.sub(r'["\'\n\r]', ' ', str(text))[:100]
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

# ── Helper: calc_minutes_elapsed ──
def calc_minutes_elapsed(period, clock_str):
    try:
        period = int(period) if period else 1
        if not clock_str or clock_str == "0:00":
            if period <= 2:
                return period * HALF_MINUTES
            else:
                return GAME_MINUTES + (period - 2) * 5
        parts = clock_str.replace(" ", "").split(":")
        minutes_left = int(parts[0])
        seconds_left = int(parts[1]) if len(parts) > 1 else 0
        remaining = minutes_left + seconds_left / 60.0
        if period == 1:
            half_length = HALF_MINUTES
            completed = 0
        elif period == 2:
            half_length = HALF_MINUTES
            completed = HALF_MINUTES
        else:
            half_length = 5
            completed = GAME_MINUTES + (period - 3) * 5
        elapsed = completed + (half_length - remaining)
        return max(0, elapsed)
    except:
        return 0

# ── Helper: calc_projection ──
def calc_projection(total_score, minutes_elapsed):
    if minutes_elapsed < 6:
        return LEAGUE_AVG_TOTAL
    pace = total_score / minutes_elapsed
    progress = minutes_elapsed / GAME_MINUTES
    if progress >= 0.50:
        weight = 0.98
    elif progress >= 0.15:
        weight = 0.3 + (progress - 0.15) / (0.50 - 0.15) * (0.98 - 0.3)
    else:
        weight = 0.3
    league_pace = LEAGUE_AVG_TOTAL / GAME_MINUTES
    blended_pace = weight * pace + (1 - weight) * league_pace
    proj = blended_pace * GAME_MINUTES
    return max(100, min(200, proj))

# ── Helper: get_pace_label ──
def get_pace_label(pace):
    if pace < 2.8:
        return "🐢 SLOW", "#22c55e"
    elif pace < 3.2:
        return "⚖️ AVG", "#eab308"
    elif pace < 3.6:
        return "🔥 FAST", "#f97316"
    else:
        return "💥 SHOOTOUT", "#ef4444"

# ── Helper: parse_record ──
def parse_record(s):
    try:
        parts = str(s).split("-")
        return (int(parts[0]), int(parts[1]))
    except:
        return (0, 0)

# ── Helper: get_favorite_side ──
def get_favorite_side(home_record, away_record, home_ml=0, home_rank=99, away_rank=99):
    if home_ml != 0:
        return "home" if home_ml < 0 else "away"
    if home_rank <= 25 and away_rank <= 25:
        return "home" if home_rank < away_rank else "away"
    if home_rank <= 25:
        return "home"
    if away_rank <= 25:
        return "away"
    hw, hl = parse_record(home_record)
    aw, al = parse_record(away_record)
    home_wpct = hw / (hw + hl) if (hw + hl) > 0 else 0
    away_wpct = aw / (aw + al) if (aw + al) > 0 else 0
    return "home" if home_wpct >= away_wpct else "away"

# ── Helper: _parse_win_pct ──
def _parse_win_pct(record_str):
    try:
        parts = str(record_str).strip().split(" ")[0].split("-")
        w, l = int(parts[0]), int(parts[1])
        return w / (w + l) if (w + l) > 0 else None
    except:
        return None

# ── Helper: remove_position ──
def remove_position(pos_id):
    st.session_state.ncaa_positions = [p for p in st.session_state.ncaa_positions if p.get('id') != pos_id]

# ── ESPN: fetch_espn_games ──
@st.cache_data(ttl=30)
def fetch_espn_games():
    try:
        today = datetime.now(eastern).strftime("%Y%m%d")
        url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard?dates={today}&limit=200&groups=50"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        games = []
        for event in data.get("events", []):
            try:
                comp = event["competitions"][0]
                competitors = comp.get("competitors", [])
                home_team_data = None
                away_team_data = None
                for c in competitors:
                    if c.get("homeAway") == "home":
                        home_team_data = c
                    else:
                        away_team_data = c
                if not home_team_data or not away_team_data:
                    continue
                ht = home_team_data.get("team", {})
                at = away_team_data.get("team", {})
                status_obj = event.get("status", {})
                status_type = status_obj.get("type", {})
                state = status_type.get("state", "pre")
                period = status_obj.get("period", 0)
                clock = status_obj.get("displayClock", "")
                status_detail = status_type.get("detail", "")
                home_score = int(home_team_data.get("score", 0) or 0)
                away_score = int(away_team_data.get("score", 0) or 0)
                home_record_str = ""
                away_record_str = ""
                for rec in home_team_data.get("records", []):
                    if rec.get("type") == "total":
                        home_record_str = rec.get("summary", "")
                        break
                for rec in away_team_data.get("records", []):
                    if rec.get("type") == "total":
                        away_record_str = rec.get("summary", "")
                        break
                home_color = "#" + ht.get("color", "555555")
                away_color = "#" + at.get("color", "555555")
                home_rank = home_team_data.get("curatedRank", {}).get("current", 99)
                away_rank = away_team_data.get("curatedRank", {}).get("current", 99)
                vegas = {}
                home_ml_val = 0
                odds_list = comp.get("odds", [])
                if odds_list:
                    o = odds_list[0]
                    vegas = {
                        "spread": o.get("details", ""),
                        "overUnder": o.get("overUnder", ""),
                        "homeML": o.get("homeTeamOdds", {}).get("moneyLine", 0),
                        "awayML": o.get("awayTeamOdds", {}).get("moneyLine", 0)
                    }
                    home_ml_val = vegas.get("homeML", 0) or 0
                conference = ""
                notes = comp.get("notes", [])
                if notes:
                    conference = notes[0].get("headline", "")
                venue_name = comp.get("venue", {}).get("fullName", "")
                broadcast = ""
                broadcasts = comp.get("broadcasts", [])
                if broadcasts:
                    names = [n.get("names", [""])[0] for n in broadcasts if n.get("names")]
                    broadcast = ", ".join(names)
                game_dt_str = event.get("date", "")
                game_time = ""
                game_datetime = ""
                if game_dt_str:
                    try:
                        utc_dt = datetime.strptime(game_dt_str[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=pytz.utc)
                        et_dt = utc_dt.astimezone(eastern)
                        game_time = et_dt.strftime("%-I:%M %p ET")
                        game_datetime = et_dt.strftime("%Y-%m-%d %H:%M")
                    except:
                        game_time = game_dt_str
                minutes_elapsed = calc_minutes_elapsed(period, clock) if state == "in" else 0
                g = {
                    "away_team": at.get("displayName", at.get("shortDisplayName", "")),
                    "home_team": ht.get("displayName", ht.get("shortDisplayName", "")),
                    "away_abbr": at.get("abbreviation", "").upper(),
                    "home_abbr": ht.get("abbreviation", "").upper(),
                    "away_score": away_score,
                    "home_score": home_score,
                    "away_record": away_record_str,
                    "home_record": home_record_str,
                    "away_id": str(at.get("id", "")),
                    "home_id": str(ht.get("id", "")),
                    "away_color": away_color,
                    "home_color": home_color,
                    "away_rank": away_rank if away_rank != 99 else 99,
                    "home_rank": home_rank if home_rank != 99 else 99,
                    "away_full": at.get("displayName", ""),
                    "home_full": ht.get("displayName", ""),
                    "status": status_detail,
                    "state": state,
                    "period": period,
                    "clock": clock,
                    "minutes_elapsed": minutes_elapsed,
                    "total_score": home_score + away_score,
                    "game_id": event.get("id", ""),
                    "vegas_odds": vegas,
                    "home_ml": home_ml_val,
                    "conference": conference,
                    "venue": venue_name,
                    "broadcast": broadcast,
                    "shortName": event.get("shortName", ""),
                    "game_time": game_time,
                    "game_datetime": game_datetime
                }
                games.append(g)
            except:
                continue
        return games
    except:
        return []

# ── ESPN: fetch_game_summary ──
@st.cache_data(ttl=300)
def fetch_game_summary(game_id):
    try:
        url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/summary?event={game_id}"
        resp = requests.get(url, timeout=10)
        return resp.json()
    except:
        return None

# ── ESPN: fetch_espn_win_prob ──
@st.cache_data(ttl=20)
def fetch_espn_win_prob(game_id):
    try:
        url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/summary?event={game_id}"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        wp = data.get("winprobability", [])
        if wp:
            return wp[-1].get("homeWinPercentage", 0.5) * 100
        pred = data.get("predictor", {})
        if pred:
            return float(pred.get("homeTeam", {}).get("gameProjection", 50))
        return None
    except:
        return None

# ── ESPN: parse_predictor ──
def parse_predictor(summary):
    if not summary:
        return None, None
    pred = summary.get("predictor", {})
    if not pred:
        return None, None
    home_pct = None
    away_pct = None
    ht = pred.get("homeTeam", {})
    at = pred.get("awayTeam", {})
    if ht:
        try:
            home_pct = float(ht.get("gameProjection", 0)) / 100.0
        except:
            home_pct = None
    if at:
        try:
            away_pct = float(at.get("gameProjection", 0)) / 100.0
        except:
            away_pct = None
    if home_pct is not None and away_pct is None:
        away_pct = 1.0 - home_pct
    if away_pct is not None and home_pct is None:
        home_pct = 1.0 - away_pct
    return home_pct, away_pct

# ── ESPN: parse_team_stats_from_summary ──
def parse_team_stats_from_summary(summary):
    home_stats = {}
    away_stats = {}
    if not summary:
        return home_stats, away_stats
    try:
        boxscore = summary.get("boxscore", {})
        teams = boxscore.get("teams", [])
        for t in teams:
            side = t.get("homeAway", "")
            stats_list = t.get("statistics", [])
            stats_dict = {}
            for s in stats_list:
                stats_dict[s.get("name", "")] = s.get("displayValue", "")
            if side == "home":
                home_stats = stats_dict
            else:
                away_stats = stats_dict
    except:
        pass
    return home_stats, away_stats

# ── ESPN: _get_team_leaders ──
def _get_team_leaders(summary, home_away):
    leaders = []
    if not summary:
        return leaders
    try:
        for leader_cat in summary.get("leaders", []):
            cat_name = leader_cat.get("name", "")
            if cat_name in ("points", "rating"):
                for team_leader in leader_cat.get("leaders", []):
                    if team_leader.get("homeAway") == home_away or team_leader.get("team", {}).get("homeAway") == home_away:
                        for entry in team_leader.get("leaders", [])[:3]:
                            athlete = entry.get("athlete", {})
                            name = athlete.get("displayName", "")
                            if name:
                                leaders.append(name)
    except:
        pass
    return leaders

# ── ESPN: _is_star_player ──
def _is_star_player(player_name, leaders_list):
    try:
        last_name = player_name.strip().split()[-1].lower()
        for leader in leaders_list[:3]:
            if leader.strip().split()[-1].lower() == last_name:
                return True
    except:
        pass
    return False

# ── ESPN: fetch_injuries ──
@st.cache_data(ttl=300)
def fetch_injuries():
    injury_dict = {}
    try:
        url = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/injuries"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        for team_entry in data.get("items", []):
            team_info = team_entry.get("team", {})
            abbr = team_info.get("abbreviation", "").upper()
            display = team_info.get("displayName", abbr)
            players = []
            for inj in team_entry.get("injuries", []):
                athlete = inj.get("athlete", {})
                players.append({
                    "name": athlete.get("displayName", "Unknown"),
                    "position": athlete.get("position", {}).get("abbreviation", ""),
                    "status": inj.get("status", ""),
                    "detail": inj.get("longComment", inj.get("shortComment", ""))
                })
            if players:
                injury_dict[abbr] = {"team": display, "players": players}
    except:
        pass
    return injury_dict

# ── ESPN: fetch_yesterday_teams ──
@st.cache_data(ttl=300)
def fetch_yesterday_teams():
    b2b = set()
    try:
        yest = (datetime.now(eastern) - timedelta(days=1)).strftime("%Y%m%d")
        url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard?dates={yest}&limit=200&groups=50"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        for event in data.get("events", []):
            for comp in event.get("competitions", []):
                for c in comp.get("competitors", []):
                    abbr = c.get("team", {}).get("abbreviation", "").upper()
                    if abbr:
                        b2b.add(abbr)
    except:
        pass
    return b2b

# ── ESPN: fetch_plays ──
@st.cache_data(ttl=30)
def fetch_plays(game_id):
    try:
        url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/summary?event={game_id}"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        plays_raw = []
        for drive in data.get("plays", []):
            if isinstance(drive, dict):
                plays_raw.append(drive)
            elif isinstance(drive, list):
                plays_raw.extend(drive)
        last_15 = plays_raw[-15:] if len(plays_raw) >= 15 else plays_raw
        result = []
        for p in last_15[-10:]:
            text = p.get("text", "")
            period = p.get("period", {}).get("number", 0) if isinstance(p.get("period"), dict) else p.get("period", 0)
            clock = p.get("clock", {}).get("displayValue", "") if isinstance(p.get("clock"), dict) else p.get("clock", "")
            sv = p.get("scoreValue", 0)
            pt = p.get("type", {}).get("text", "") if isinstance(p.get("type"), dict) else str(p.get("type", ""))
            tid = ""
            if p.get("team"):
                tid = str(p["team"].get("id", "")) if isinstance(p["team"], dict) else str(p["team"])
            result.append({
                "text": text,
                "period": period,
                "clock": clock,
                "score_value": sv,
                "play_type": pt,
                "team_id": tid
            })
        return result
    except:
        return []

# ── Kalshi: fetch_kalshi_ml ──
@st.cache_data(ttl=60)
def fetch_kalshi_ml():
    ml = {}
    try:
        url = "https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXNCAAGAME&limit=200&status=open"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        for m in data.get("markets", []):
            ticker = m.get("ticker", "")
            yes_price = m.get("yes_bid", 0) or 0
            no_price = 100 - yes_price if yes_price else 0
            ml[ticker] = {
                "ticker": ticker,
                "title": m.get("title", ""),
                "yes_price": yes_price,
                "no_price": no_price,
                "volume": m.get("volume", 0)
            }
    except:
        pass
    return ml

# ── Kalshi: fetch_kalshi_spreads_raw ──
@st.cache_data(ttl=60)
def fetch_kalshi_spreads_raw():
    spreads = {}
    spread_list = []
    try:
        url = "https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXNCAASPREAD&limit=200&status=open"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        for m in data.get("markets", []):
            ticker = m.get("ticker", "")
            title = m.get("title", "").lower()
            subtitle = m.get("subtitle", "").lower()
            yes_price = m.get("yes_bid", 0) or 0
            no_price = 100 - yes_price if yes_price else 0
            spreads[ticker] = {
                "ticker": ticker,
                "title": m.get("title", ""),
                "subtitle": m.get("subtitle", ""),
                "yes_price": yes_price,
                "no_price": no_price,
                "volume": m.get("volume", 0)
            }
            if any(kw in title or kw in subtitle for kw in ["wins by", "spread", "margin"]):
                spread_list.append(m)
    except:
        pass
    return spreads, spread_list

# ── Kalshi: find_spread_markets_for_game ──
def find_spread_markets_for_game(home_abbr, away_abbr, home_name, away_name, spread_list):
    matches = []
    ha = home_abbr.upper()
    aa = away_abbr.upper()
    hn = home_name.lower()
    an = away_name.lower()
    for m in spread_list:
        title = m.get("title", "")
        subtitle = m.get("subtitle", "")
        ticker = m.get("ticker", "")
        searchable = (title + " " + subtitle + " " + ticker).lower()
        if (ha.lower() in searchable or hn in searchable) and (aa.lower() in searchable or an in searchable):
            spread_val = 0
            spread_match = re.search(r'(\d+\.?\d*)\+?\s*points?', title.lower())
            if not spread_match:
                spread_match = re.search(r'by\s+(\d+\.?\d*)', title.lower())
            if spread_match:
                spread_val = float(spread_match.group(1))
            yes_price = m.get("yes_bid", 0) or 0
            no_price = 100 - yes_price if yes_price else 0
            matches.append({
                "ticker": ticker,
                "title": title,
                "subtitle": subtitle,
                "spread_val": spread_val,
                "yes_price": yes_price,
                "no_price": no_price,
                "volume": m.get("volume", 0)
            })
    matches.sort(key=lambda x: x["spread_val"], reverse=True)
    return matches

# ── Kalshi: find_ml_price_for_team ──
def find_ml_price_for_team(home_abbr, away_abbr, fav_side, kalshi_ml_dict):
    ha = home_abbr.upper()
    aa = away_abbr.upper()
    for ticker, info in kalshi_ml_dict.items():
        t_upper = ticker.upper()
        if ha in t_upper and aa in t_upper:
            if fav_side == "home":
                return info.get("yes_price"), ticker
            else:
                return info.get("no_price"), ticker
    return None, None

# ── 9-Factor Edge Model ──
def calc_advanced_edge(game, b2b_teams, summary=None, injuries=None):
    edges = []
    total_score = 0.0

    # Factor 1: ESPN BPI
    home_bpi, away_bpi = parse_predictor(summary)
    bpi_val = None
    if home_bpi is not None:
        bpi_val = home_bpi
        factor_score = (home_bpi - 0.5) * 20
        edges.append({"factor": "ESPN BPI", "value": round(factor_score, 1), "detail": f"Home {home_bpi*100:.0f}% / Away {away_bpi*100:.0f}%"})
        total_score += factor_score

    # Factor 2: BPI vs Vegas gap
    if home_bpi is not None and game.get("home_ml") and game["home_ml"] != 0:
        vegas_implied = american_to_implied_prob(game["home_ml"])
        if vegas_implied:
            gap = (home_bpi - vegas_implied) * 100
            if abs(gap) >= 3:
                factor_score = gap * 0.15
                edges.append({"factor": "BPI vs Vegas", "value": round(factor_score, 1), "detail": f"BPI {home_bpi*100:.0f}% vs Vegas {vegas_implied*100:.0f}% (gap {gap:+.1f}%)"})
                total_score += factor_score

    # Factor 3: Home court advantage
    hca_score = HOME_COURT_ADV / 2
    edges.append({"factor": "Home Court", "value": round(hca_score, 1), "detail": f"+{HOME_COURT_ADV} pts college HCA"})
    total_score += hca_score

    # Factor 4: Records
    hw, hl = parse_record(game.get("home_record", ""))
    aw, al = parse_record(game.get("away_record", ""))
    home_wpct = hw / (hw + hl) if (hw + hl) > 0 else 0.5
    away_wpct = aw / (aw + al) if (aw + al) > 0 else 0.5
    rec_score = (home_wpct - away_wpct) * 10
    edges.append({"factor": "Records", "value": round(rec_score, 1), "detail": f"Home .{home_wpct*1000:.0f} vs Away .{away_wpct*1000:.0f}"})
    total_score += rec_score

    # Factor 5: Ranking gap (NCAA-specific)
    home_rank = game.get("home_rank", 99)
    away_rank = game.get("away_rank", 99)
    if home_rank <= 25 or away_rank <= 25:
        if home_rank <= 25 and away_rank <= 25:
            rank_score = (away_rank - home_rank) * 0.3
            edges.append({"factor": "Ranking Gap", "value": round(rank_score, 1), "detail": f"#{home_rank} Home vs #{away_rank} Away"})
        elif home_rank <= 25:
            rank_score = 3.0
            edges.append({"factor": "Ranking Gap", "value": round(rank_score, 1), "detail": f"Home #{home_rank} ranked, Away unranked"})
        else:
            rank_score = -3.0
            edges.append({"factor": "Ranking Gap", "value": round(rank_score, 1), "detail": f"Away #{away_rank} ranked, Home unranked"})
        total_score += rank_score

    # Factor 6: B2B fatigue
    home_b2b = game.get("home_abbr", "") in b2b_teams
    away_b2b = game.get("away_abbr", "") in b2b_teams
    if home_b2b:
        edges.append({"factor": "B2B Fatigue", "value": -2.0, "detail": "Home on B2B"})
        total_score -= 2.0
    if away_b2b:
        edges.append({"factor": "B2B Fatigue", "value": 2.0, "detail": "Away on B2B"})
        total_score += 2.0

    # Factor 7: PPG from boxscore
    home_stats, away_stats = parse_team_stats_from_summary(summary)
    home_ppg_str = home_stats.get("avgPoints", home_stats.get("points", ""))
    away_ppg_str = away_stats.get("avgPoints", away_stats.get("points", ""))
    try:
        home_ppg = float(home_ppg_str)
        away_ppg = float(away_ppg_str)
        ppg_score = (home_ppg - away_ppg) * 0.3
        edges.append({"factor": "PPG", "value": round(ppg_score, 1), "detail": f"Home {home_ppg:.1f} vs Away {away_ppg:.1f}"})
        total_score += ppg_score
    except:
        pass

    # Factor 8: Injuries
    if injuries:
        home_abbr = game.get("home_abbr", "")
        away_abbr = game.get("away_abbr", "")
        home_leaders = _get_team_leaders(summary, "home")
        away_leaders = _get_team_leaders(summary, "away")
        home_inj = injuries.get(home_abbr, {}).get("players", [])
        away_inj = injuries.get(away_abbr, {}).get("players", [])
        inj_score = 0
        for p in home_inj:
            stat = p.get("status", "").lower()
            is_star = _is_star_player(p.get("name", ""), home_leaders)
            if "out" in stat:
                inj_score -= 4.0 if is_star else 1.0
            elif "day" in stat or "dtd" in stat or "doubtful" in stat:
                inj_score -= 0.5
        for p in away_inj:
            stat = p.get("status", "").lower()
            is_star = _is_star_player(p.get("name", ""), away_leaders)
            if "out" in stat:
                inj_score += 4.0 if is_star else 1.0
            elif "day" in stat or "dtd" in stat or "doubtful" in stat:
                inj_score += 0.5
        if inj_score != 0:
            edges.append({"factor": "Injuries", "value": round(inj_score, 1), "detail": f"Home: {len(home_inj)} injured, Away: {len(away_inj)} injured"})
            total_score += inj_score

    # Factor 9: 3PT shooting
    h3p = home_stats.get("threePointFieldGoalPct", home_stats.get("threePointPct", ""))
    a3p = away_stats.get("threePointFieldGoalPct", away_stats.get("threePointPct", ""))
    h3m = home_stats.get("threePointFieldGoalsMade", home_stats.get("threesMade", ""))
    a3m = away_stats.get("threePointFieldGoalsMade", away_stats.get("threesMade", ""))
    try:
        h3pf = float(h3p)
        a3pf = float(a3p)
        pct_gap = h3pf - a3pf
        three_score = pct_gap * 0.15
        try:
            h3mf = float(h3m)
            a3mf = float(a3m)
            three_score += (h3mf - a3mf) * 0.3
        except:
            pass
        edges.append({"factor": "3PT", "value": round(three_score, 1), "detail": f"Home {h3pf:.1f}% vs Away {a3pf:.1f}%"})
        total_score += three_score
    except:
        pass

    # Strength
    abs_score = abs(total_score)
    if abs_score >= 8:
        strength = "🔴 STRONG"
    elif abs_score >= 4:
        strength = "🟡 MODERATE"
    elif abs_score >= 1.5:
        strength = "🟢 LEAN"
    else:
        strength = "⚪ TOSS-UP"

    side = "home" if total_score >= 0 else "away"
    pick = game.get("home_team") if side == "home" else game.get("away_team")

    return {
        "edges": edges,
        "score": round(total_score, 1),
        "pick": pick,
        "side": side,
        "strength": strength,
        "bpi": bpi_val
    }

# ── Possession Tracker ──
def infer_possession(plays, home_abbr, away_abbr, home_name, away_name, home_id="", away_id=""):
    if not plays:
        return None, None
    last_team = None
    last_side = None
    for play in reversed(plays[-12:]):
        text = play.get("text", "").lower()
        pt = play.get("play_type", "").lower()
        tid = str(play.get("team_id", ""))
        acting_side = None
        acting_name = None
        if tid and home_id and away_id:
            if tid == home_id:
                acting_side = "home"
                acting_name = home_name
            elif tid == away_id:
                acting_side = "away"
                acting_name = away_name
        if not acting_side:
            if home_abbr.lower() in text or home_name.lower() in text:
                acting_side = "home"
                acting_name = home_name
            elif away_abbr.lower() in text or away_name.lower() in text:
                acting_side = "away"
                acting_name = away_name
        if not acting_side:
            continue
        other_side = "away" if acting_side == "home" else "home"
        other_name = away_name if acting_side == "home" else home_name
        if "steal" in pt or "steal" in text:
            return acting_name, acting_side
        if "turnover" in pt or "turnover" in text:
            continue
        if "made" in pt or "made" in text or play.get("score_value", 0) > 0:
            return other_name, other_side
        if "rebound" in pt or "rebound" in text:
            return acting_name, acting_side
        if "foul" in pt or "foul" in text:
            continue
        if "miss" in pt or "miss" in text:
            continue
        last_team = acting_name
        last_side = acting_side
    return last_team, last_side

# ── Spread Sniper ──
def check_spread_sniper(game, spread_list, kalshi_ml_dict):
    if game.get("state") != "in":
        return None
    game_id = game.get("game_id", "")
    if game_id in st.session_state.ncaa_alerted_games:
        return None
    period = game.get("period", 0)
    if period < 1:
        return None
    threshold = LEAD_BY_HALF.get(period, 12)
    home_score = game.get("home_score", 0)
    away_score = game.get("away_score", 0)
    diff = abs(home_score - away_score)
    if diff < threshold:
        return None
    leading_side = "home" if home_score > away_score else "away"
    leading_team = game.get(f"{leading_side}_team", "")
    trailing_side = "away" if leading_side == "home" else "home"
    trailing_team = game.get(f"{trailing_side}_team", "")
    spread_markets = find_spread_markets_for_game(
        game.get("home_abbr", ""), game.get("away_abbr", ""),
        game.get("home_team", ""), game.get("away_team", ""),
        spread_list
    )
    best = None
    for sm in spread_markets:
        if sm.get("no_price", 0) <= MAX_NO_PRICE and sm.get("spread_val", 0) >= MIN_SPREAD_BRACKET:
            if best is None or sm["spread_val"] > best["spread_val"]:
                best = sm
    if not best:
        return None
    st.session_state.ncaa_alerted_games.add(game_id)
    period_label = f"H{period}" if period <= 2 else f"OT{period-2}"
    alert = {
        "game_id": game_id,
        "time": datetime.now(eastern).strftime("%I:%M %p"),
        "leading_team": leading_team,
        "trailing_team": trailing_team,
        "score": f"{away_score}-{home_score}",
        "diff": diff,
        "period": period_label,
        "spread_val": best["spread_val"],
        "no_price": best["no_price"],
        "ticker": best["ticker"],
        "type": "sniper"
    }
    st.session_state.ncaa_sniper_alerts.insert(0, alert)
    return alert

# ── Comeback Tracker ──
def check_comeback(game, kalshi_ml_dict):
    if game.get("state") != "in":
        return None
    game_id = game.get("game_id", "")
    home_score = game.get("home_score", 0)
    away_score = game.get("away_score", 0)
    diff = abs(home_score - away_score)
    if diff >= 10:
        if game_id not in st.session_state.ncaa_comeback_tracking:
            leading_side = "home" if home_score > away_score else "away"
            st.session_state.ncaa_comeback_tracking[game_id] = {
                "leading_side": leading_side,
                "leading_team": game.get(f"{leading_side}_team", ""),
                "max_deficit": diff,
                "trailing_side": "away" if leading_side == "home" else "home"
            }
        else:
            tracked = st.session_state.ncaa_comeback_tracking[game_id]
            if diff > tracked["max_deficit"]:
                tracked["max_deficit"] = diff
        return None
    if game_id in st.session_state.ncaa_comeback_tracking and game_id not in st.session_state.ncaa_comeback_alerted:
        tracked = st.session_state.ncaa_comeback_tracking[game_id]
        if diff <= 2 and tracked["max_deficit"] >= 10:
            st.session_state.ncaa_comeback_alerted.add(game_id)
            trailing_side = tracked["trailing_side"]
            trailing_team = game.get(f"{trailing_side}_team", "")
            alert = {
                "game_id": game_id,
                "time": datetime.now(eastern).strftime("%I:%M %p"),
                "trailing_team": trailing_team,
                "leading_team": tracked["leading_team"],
                "was_down": tracked["max_deficit"],
                "score": f"{away_score}-{home_score}",
                "diff": diff,
                "type": "comeback"
            }
            st.session_state.ncaa_comeback_alerts.insert(0, alert)
            return alert
    return None

# ── Mobile CSS ──
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

# ── Visual: render_scoreboard ──
def render_scoreboard(game):
    away_color = get_team_color(game, "away")
    home_color = get_team_color(game, "home")
    state = game.get("state", "pre")
    away_rank = game.get("away_rank", 99)
    home_rank = game.get("home_rank", 99)
    away_prefix = f"<span style='color:#fbbf24;font-weight:700'>#{away_rank}</span> " if away_rank <= 25 else ""
    home_prefix = f"<span style='color:#fbbf24;font-weight:700'>#{home_rank}</span> " if home_rank <= 25 else ""
    conf = game.get("conference", "")
    conf_html = f"<div style='text-align:center;color:#94a3b8;font-size:12px;margin-bottom:6px'>{conf}</div>" if conf else ""
    if state == "in":
        period = game.get("period", 1)
        clock = game.get("clock", "")
        if period <= 2:
            period_label = f"H{period}"
        else:
            period_label = f"OT{period-2}"
        mid = f"<span style='color:#f87171;font-weight:700'>{period_label} {clock}</span>"
    elif state == "post":
        mid = "<span style='color:#94a3b8'>FINAL</span>"
    else:
        bc = game.get("broadcast", "")
        gt = game.get("game_time", "")
        mid = f"<span style='color:#94a3b8'>{gt}</span>"
        if bc:
            mid += f"<br><span style='color:#64748b;font-size:12px'>{bc}</span>"
    venue = game.get("venue", "")
    venue_html = f"<div style='text-align:center;color:#64748b;font-size:11px;margin-top:6px'>{venue}</div>" if venue else ""
    html = f"""
    {MOBILE_CSS}
    <div style="background:#0f172a;border-radius:12px;padding:16px;margin:8px 0;max-width:100%;box-sizing:border-box;overflow-x:hidden;border-left:4px solid {away_color};border-right:4px solid {home_color}">
    {conf_html}
    <div style="display:flex;align-items:center;justify-content:space-between;gap:8px;flex-wrap:wrap">
        <div style="flex:1;text-align:center;min-width:100px">
            <div class="sb-team" style="color:{away_color};font-size:clamp(16px,3.5vw,22px);font-weight:700">{away_prefix}{game.get('away_abbr','')}</div>
            <div style="color:#94a3b8;font-size:12px">{game.get('away_record','')}</div>
            <div class="sb-score" style="color:#fff;font-size:clamp(28px,5vw,52px);font-weight:800">{game.get('away_score',0)}</div>
        </div>
        <div style="text-align:center;min-width:60px" class="sb-period">
            <div style="font-size:clamp(13px,2.5vw,18px)">{mid}</div>
        </div>
        <div style="flex:1;text-align:center;min-width:100px">
            <div class="sb-team" style="color:{home_color};font-size:clamp(16px,3.5vw,22px);font-weight:700">{home_prefix}{game.get('home_abbr','')}</div>
            <div style="color:#94a3b8;font-size:12px">{game.get('home_record','')}</div>
            <div class="sb-score" style="color:#fff;font-size:clamp(28px,5vw,52px);font-weight:800">{game.get('home_score',0)}</div>
        </div>
    </div>
    {venue_html}
    </div>
    """
    components.html(html, height=200)

# ── Visual: get_play_badge ──
def get_play_badge(last_play):
    if not last_play:
        return ""
    pt = last_play.get("play_type", "").lower()
    sv = last_play.get("score_value", 0)
    text = last_play.get("text", "")[:40]
    if sv == 3:
        bg, label = "#22c55e", "THREE!"
    elif sv == 2:
        bg, label = "#3b82f6", "BUCKET"
    elif "dunk" in pt or "dunk" in text.lower():
        bg, label = "#a855f7", "DUNK!"
    elif "steal" in pt:
        bg, label = "#f59e0b", "STEAL"
    elif "block" in pt:
        bg, label = "#ef4444", "BLOCK"
    elif "turnover" in pt:
        bg, label = "#6b7280", "TO"
    elif "rebound" in pt:
        bg, label = "#06b6d4", "REB"
    elif "foul" in pt:
        bg, label = "#f97316", "FOUL"
    elif "free throw" in pt.lower() and sv > 0:
        bg, label = "#8b5cf6", "FT"
    else:
        bg, label = "#475569", "PLAY"
    svg = f"""
    <rect x="150" y="5" width="200" height="30" rx="6" fill="{bg}" opacity="0.9"/>
    <text x="250" y="25" text-anchor="middle" fill="#fff" font-size="13" font-weight="700">{label}: {text}</text>
    """
    return svg

# ── Visual: get_play_icon ──
def get_play_icon(play_type, score_value):
    pt = str(play_type).lower()
    if score_value == 3:
        return ("3", "#22c55e")
    elif score_value == 2:
        return ("2", "#3b82f6")
    elif "steal" in pt:
        return ("S", "#f59e0b")
    elif "block" in pt:
        return ("B", "#ef4444")
    elif "turnover" in pt:
        return ("T", "#6b7280")
    elif "rebound" in pt:
        return ("R", "#06b6d4")
    elif "foul" in pt:
        return ("F", "#f97316")
    elif score_value == 1:
        return ("1", "#8b5cf6")
    else:
        return ("•", "#475569")

# ── Visual: render_college_court ──
def render_college_court(game, last_play):
    away_color = get_team_color(game, "away")
    home_color = get_team_color(game, "home")
    period = game.get("period", 0)
    clock = game.get("clock", "")
    if period <= 2:
        period_label = f"H{period}"
    else:
        period_label = f"OT{period-2}"
    play_badge = get_play_badge(last_play)
    svg = f"""
    {MOBILE_CSS}
    <div style="max-width:100%;box-sizing:border-box;overflow-x:hidden;text-align:center">
    <svg viewBox="0 0 500 280" style="width:100%;max-width:500px;border-radius:10px;background:#1a1a2e">
        <!-- Court -->
        <rect x="20" y="20" width="460" height="200" rx="8" fill="#2d4a22" stroke="#fff" stroke-width="2"/>
        <!-- Half court line -->
        <line x1="250" y1="20" x2="250" y2="220" stroke="#fff" stroke-width="1.5" opacity="0.7"/>
        <!-- Center circle -->
        <circle cx="250" cy="120" r="30" fill="none" stroke="#fff" stroke-width="1.5" opacity="0.7"/>
        <!-- Left key (wider for college) -->
        <rect x="20" y="65" width="75" height="110" fill="none" stroke="#fff" stroke-width="1.5" opacity="0.7"/>
        <!-- Right key -->
        <rect x="405" y="65" width="75" height="110" fill="none" stroke="#fff" stroke-width="1.5" opacity="0.7"/>
        <!-- Left hoop -->
        <circle cx="40" cy="120" r="8" fill="none" stroke="#f97316" stroke-width="2"/>
        <!-- Right hoop -->
        <circle cx="460" cy="120" r="8" fill="none" stroke="#f97316" stroke-width="2"/>
        <!-- Period/Clock -->
        <text x="250" y="14" text-anchor="middle" fill="#f87171" font-size="13" font-weight="700">{period_label} {clock}</text>
        <!-- Away team box -->
        <rect x="60" y="235" width="150" height="35" rx="6" fill="{away_color}" opacity="0.85"/>
        <text x="135" y="257" text-anchor="middle" fill="#fff" font-size="14" font-weight="700">{game.get('away_abbr','')} {game.get('away_score',0)}</text>
        <!-- Home team box -->
        <rect x="290" y="235" width="150" height="35" rx="6" fill="{home_color}" opacity="0.85"/>
        <text x="365" y="257" text-anchor="middle" fill="#fff" font-size="14" font-weight="700">{game.get('home_abbr','')} {game.get('home_score',0)}</text>
        {play_badge}
    </svg>
    </div>
    """
    components.html(svg, height=310)

# === END PART A — PASTE PART B BELOW THIS LINE ===
# ═══════════════════════════════════════════════════════
# PART B — UI LAYER (paste below Part A)
# ═══════════════════════════════════════════════════════

# ── 1. Fetch All Data ──
games = fetch_espn_games()
kalshi_ml_data = fetch_kalshi_ml()
kalshi_spreads_parsed, kalshi_spread_list = fetch_kalshi_spreads_raw()
injuries = fetch_injuries()
b2b_teams = fetch_yesterday_teams()

# ── 2. Categorize Games ──
live_games = [g for g in games if g.get('state') == 'in']
scheduled_games = [g for g in games if g.get('state') == 'pre']
final_games = [g for g in games if g.get('state') == 'post']

# ── 3. Run Sniper + Comeback Checks ──
for g in live_games:
    sa = check_spread_sniper(g, kalshi_spread_list, kalshi_ml_data)
    ca = check_comeback(g, kalshi_ml_data)

# ── 4. Header ──
st.title("BIGSNAPSHOT NCAA EDGE FINDER")
st.caption(f"v{VERSION} | {now.strftime('%A %B %d, %Y %-I:%M %p ET')} | NCAA Men's Basketball | 9-Factor Edge + Spread Sniper + Comeback Scanner + SHARK")
hc1, hc2, hc3, hc4 = st.columns(4)
hc1.metric("Today's Games", len(games))
hc2.metric("Live Now", len(live_games))
hc3.metric("Scheduled", len(scheduled_games))
hc4.metric("Final", len(final_games))
st.divider()

# ── 5. PACE SCANNER ──
st.subheader("PACE SCANNER")
pace_data = []
for g in live_games:
    me = g.get('minutes_elapsed', 0)
    if me < 4:
        continue
    ts = g.get('total_score', 0)
    pace = ts / me if me > 0 else 0
    proj = calc_projection(ts, me)
    pl, pc = get_pace_label(pace)
    period = g.get('period', 1)
    clock = g.get('clock', '')
    if period <= 2:
        plabel = f"H{period}"
    else:
        plabel = f"OT{period-2}"
    ar = g.get('away_rank', 99)
    hr = g.get('home_rank', 99)
    away_badge = f"#{ar} " if ar <= 25 else ""
    home_badge = f"#{hr} " if hr <= 25 else ""
    gname = f"{away_badge}{g.get('away_abbr','')} @ {home_badge}{g.get('home_abbr','')}"
    pace_data.append({"name": gname, "status": f"{plabel} {clock}", "total": ts, "pace": pace, "pace_label": pl, "pace_color": pc, "proj": proj})

pace_data.sort(key=lambda x: x["pace"])
if pace_data:
    for pd_item in pace_data:
        pc1, pc2, pc3, pc4 = st.columns([3, 2, 2, 2])
        pc1.markdown(f"**{pd_item['name']}**")
        pc2.markdown(f"{pd_item['status']} | {pd_item['total']} pts")
        pc3.markdown(f"<span style='color:{pd_item['pace_color']};font-weight:700'>{pd_item['pace_label']}</span> ({pd_item['pace']:.2f}/min)", unsafe_allow_html=True)
        pc4.markdown(f"Proj: **{pd_item['proj']:.0f}**")
else:
    st.info("No live games with 4+ minutes played")
st.divider()

# ── 6. Tabs (5 tabs now) ──
tab_edge, tab_spread, tab_live, tab_cushion, tab_shark = st.tabs(["Edge Finder", "Spread Sniper", "Live Monitor", "Cushion Scanner", "🦈 SHARK"])

# ═══════════════════════════════════════════════════════
# TAB 1: EDGE FINDER
# ═══════════════════════════════════════════════════════
with tab_edge:

    st.subheader("PRE-GAME ALIGNMENT — 9-Factor Edge Model")
    with st.expander("How Edges Are Rated"):
        st.markdown("""
**9 factors scored and summed:**
1. **ESPN BPI** — Power Index win probability vs 50%
2. **BPI vs Vegas Gap** — When BPI disagrees with moneyline by 3%+
3. **Home Court** — College HCA is stronger (+4.0 pts)
4. **Records** — Win percentage comparison
5. **Ranking Gap** — AP Top 25 ranking advantage (college-specific)
6. **B2B Fatigue** — Back-to-back game penalty
7. **PPG** — Scoring average gap
8. **Injuries** — Star OUT = big swing, DTD = small
9. **3PT Shooting** — Percentage and volume gap

| Strength | Score |
|----------|-------|
| 🔴 STRONG | ≥ 8 |
| 🟡 MODERATE | ≥ 4 |
| 🟢 LEAN | ≥ 1.5 |
| ⚪ TOSS-UP | < 1.5 |

*Only STRONG and MODERATE edges shown. College has 50+ games/day — we filter the noise.*
""")
    st.caption("ESPN BPI + Vegas + Rankings + Situational | Only showing STRONG + MODERATE edges")

    edge_results = []
    for g in scheduled_games:
        summary = fetch_game_summary(g.get('game_id', ''))
        result = calc_advanced_edge(g, b2b_teams, summary=summary, injuries=injuries)
        if result.get('strength', '') in ('🔴 STRONG', '🟡 MODERATE'):
            edge_results.append({"game": g, "edge": result, "summary": summary})

    edge_results.sort(key=lambda x: (0 if '🔴' in x['edge'].get('strength', '') else 1, -abs(x['edge'].get('score', 0))))

    if not edge_results:
        st.info("No STRONG or MODERATE edges found in today's scheduled games.")
    else:
        st.markdown(f"**{len(edge_results)} actionable edges** out of {len(scheduled_games)} scheduled games")

        if st.button("📋 ADD ALL EDGE PICKS", key="ncaa_add_all_edges"):
            for er in edge_results:
                g = er["game"]
                e = er["edge"]
                pos = {
                    "id": str(uuid.uuid4()),
                    "game": f"{g.get('away_abbr','')} @ {g.get('home_abbr','')}",
                    "pick": e.get("pick", ""),
                    "side": e.get("side", ""),
                    "type": "ML",
                    "line": "",
                    "direction": "YES" if e.get("side") == "home" else "NO",
                    "score": e.get("score", 0),
                    "strength": e.get("strength", ""),
                    "time": now.strftime("%I:%M %p")
                }
                st.session_state.ncaa_positions.append(pos)
            st.success(f"Added {len(edge_results)} edge picks!")

        for er in edge_results:
            g = er["game"]
            e = er["edge"]
            strength = e.get("strength", "")
            border_color = "#22c55e" if "STRONG" in strength else "#f97316"
            score = e.get("score", 0)
            pick = e.get("pick", "")
            side = e.get("side", "")
            ar = g.get('away_rank', 99)
            hr = g.get('home_rank', 99)
            away_badge = f"#{ar} " if ar <= 25 else ""
            home_badge = f"#{hr} " if hr <= 25 else ""
            spread = g.get('vegas_odds', {}).get('spread', 'N/A')
            ou = g.get('vegas_odds', {}).get('overUnder', 'N/A')
            bc = g.get('broadcast', '')
            bc_html = f" | 📺 {bc}" if bc else ""

            html = f"""
            {MOBILE_CSS}
            <div style="background:#0f172a;border-left:4px solid {border_color};border-radius:8px;padding:clamp(8px,2vw,16px);margin:8px 0;max-width:100%;box-sizing:border-box;overflow-x:hidden">
                <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:6px">
                    <span style="background:{border_color};color:#000;padding:2px 10px;border-radius:12px;font-weight:700;font-size:clamp(11px,2.5vw,14px)">{strength}</span>
                    <span style="color:#94a3b8;font-size:clamp(11px,2.5vw,13px)">{g.get('game_time','')}{bc_html}</span>
                </div>
                <div style="color:#fff;font-size:clamp(16px,4vw,22px);font-weight:700;margin:8px 0">
                    {away_badge}{g.get('away_abbr','')} @ {home_badge}{g.get('home_abbr','')}
                </div>
                <div style="color:#94a3b8;font-size:clamp(11px,2.5vw,13px);margin-bottom:6px">
                    Spread: {spread} | O/U: {ou}
                </div>
                <div style="color:#22c55e;font-size:clamp(14px,3.5vw,18px);font-weight:700">
                    PICK: {pick} ({side.upper()}) → {score:+.1f}
                </div>
            </div>
            """
            st.markdown(html, unsafe_allow_html=True)

            bc1, bc2 = st.columns(2)
            with bc1:
                st.link_button("🔗 Trade on Kalshi", KALSHI_GAME_LINK, use_container_width=True)
            with bc2:
                if st.button("📌 Track", key=f"ncaa_track_{g.get('game_id','')}"):
                    pos = {
                        "id": str(uuid.uuid4()),
                        "game": f"{g.get('away_abbr','')} @ {g.get('home_abbr','')}",
                        "pick": pick,
                        "side": side,
                        "type": "ML",
                        "line": "",
                        "direction": "YES" if side == "home" else "NO",
                        "score": score,
                        "strength": strength,
                        "time": now.strftime("%I:%M %p")
                    }
                    st.session_state.ncaa_positions.append(pos)
                    st.success(f"Tracking {pick}!")

            with st.expander("View Breakdown"):
                for edge in e.get("edges", []):
                    f_name = edge.get("factor", "")
                    f_val = edge.get("value", 0)
                    f_detail = edge.get("detail", "")
                    if "injur" in f_name.lower():
                        ecolor = "#ef4444"
                    elif "3pt" in f_name.lower():
                        ecolor = "#3b82f6"
                    elif "bpi" in f_name.lower():
                        ecolor = "#22c55e"
                    elif "fatigue" in f_name.lower() or "b2b" in f_name.lower():
                        ecolor = "#f97316"
                    elif "rank" in f_name.lower():
                        ecolor = "#fbbf24"
                    else:
                        ecolor = "#94a3b8"
                    sign = "+" if f_val > 0 else ""
                    st.markdown(f"<span style='color:{ecolor};font-weight:700'>{f_name}: {sign}{f_val:.1f}</span> — {f_detail}", unsafe_allow_html=True)

            st.divider()

    # Section B: Vegas vs Kalshi Mispricing
    st.subheader("VEGAS vs KALSHI MISPRICING")
    st.caption("Comparing implied probabilities from Vegas moneylines vs Kalshi contract prices")
    mispricing_count = 0
    for g in scheduled_games:
        hml = g.get('home_ml', 0)
        aml = g.get('vegas_odds', {}).get('awayML', 0)
        if not hml or not aml:
            continue
        home_vegas_prob = american_to_implied_prob(hml)
        away_vegas_prob = american_to_implied_prob(aml)
        if not home_vegas_prob or not away_vegas_prob:
            continue
        fav_side = get_favorite_side(g.get('home_record',''), g.get('away_record',''), hml, g.get('home_rank',99), g.get('away_rank',99))
        kalshi_price, kalshi_ticker = find_ml_price_for_team(g.get('home_abbr',''), g.get('away_abbr',''), fav_side, kalshi_ml_data)
        if kalshi_price is None:
            continue
        vegas_prob = home_vegas_prob * 100 if fav_side == "home" else away_vegas_prob * 100
        kalshi_prob = kalshi_price
        edge = vegas_prob - kalshi_prob
        if abs(edge) < 5:
            continue

        summary_mp = fetch_game_summary(g.get('game_id', ''))
        bpi_home, bpi_away = parse_predictor(summary_mp)
        bpi_pct = (bpi_home * 100 if fav_side == "home" else bpi_away * 100) if bpi_home else None
        bpi_str = f"{bpi_pct:.0f}%" if bpi_pct else "N/A"

        mispricing_count += 1
        ar = g.get('away_rank', 99)
        hr = g.get('home_rank', 99)
        away_badge = f"#{ar} " if ar <= 25 else ""
        home_badge = f"#{hr} " if hr <= 25 else ""
        fav_team = g.get('home_abbr','') if fav_side == "home" else g.get('away_abbr','')
        action = "BUY YES" if edge > 0 else "BUY NO"
        action_color = "#22c55e" if edge > 0 else "#ef4444"

        html = f"""
        {MOBILE_CSS}
        <div style="background:#0f172a;border-left:4px solid {action_color};border-radius:8px;padding:clamp(8px,2vw,16px);margin:8px 0;max-width:100%;box-sizing:border-box;overflow-x:hidden">
            <div style="color:#fff;font-size:clamp(14px,3.5vw,18px);font-weight:700;margin-bottom:6px">
                {away_badge}{g.get('away_abbr','')} @ {home_badge}{g.get('home_abbr','')}
            </div>
            <div style="margin-bottom:6px">
                <span style="background:{action_color};color:#fff;padding:2px 10px;border-radius:12px;font-weight:700;font-size:clamp(11px,2.5vw,14px)">{action} {fav_team}</span>
            </div>
            <table style="width:100%;table-layout:fixed;color:#cbd5e1;font-size:clamp(12px,2.5vw,14px);border-collapse:collapse">
                <tr><td style="padding:4px">Vegas</td><td style="padding:4px;font-weight:700">{vegas_prob:.0f}%</td></tr>
                <tr><td style="padding:4px">Kalshi</td><td style="padding:4px;font-weight:700">{kalshi_prob:.0f}¢</td></tr>
                <tr><td style="padding:4px">BPI</td><td style="padding:4px;font-weight:700">{bpi_str}</td></tr>
                <tr><td style="padding:4px">Edge</td><td style="padding:4px;font-weight:700;color:{action_color}">{abs(edge):.1f}%</td></tr>
            </table>
        </div>
        """
        st.markdown(html, unsafe_allow_html=True)
        st.link_button("🔗 Trade on Kalshi", KALSHI_GAME_LINK, use_container_width=True)
        st.divider()

    if mispricing_count == 0:
        st.info("No significant mispricings detected (threshold: 5%+ edge).")

    # Section C: Injury Report
    st.subheader("INJURY REPORT")
    today_abbrs = set()
    for g in games:
        today_abbrs.add(g.get('home_abbr', ''))
        today_abbrs.add(g.get('away_abbr', ''))
    inj_shown = 0
    for abbr in sorted(today_abbrs):
        if abbr not in injuries:
            continue
        team_inj = injuries[abbr]
        players = team_inj.get("players", [])
        relevant = [p for p in players if any(kw in p.get("status","").lower() for kw in ("out", "day", "dtd", "doubtful"))]
        if not relevant:
            continue
        inj_shown += 1
        team_name = team_inj.get("team", abbr)
        st.markdown(f"**{team_name}**")
        for p in relevant:
            stat = p.get("status", "")
            color = "#ef4444" if "out" in stat.lower() else "#f59e0b"
            st.markdown(f"<span style='color:{color};font-weight:700'>{stat}</span> — {p.get('name','')} ({p.get('position','')}) — {p.get('detail','')}", unsafe_allow_html=True)
    if inj_shown == 0:
        st.info("No relevant injuries found for today's teams.")

    # Section D: Position Tracker
    st.subheader("POSITION TRACKER")
    with st.expander("➕ Add Position"):
        game_options = []
        for g in games:
            ar = g.get('away_rank', 99)
            hr = g.get('home_rank', 99)
            ab = f"#{ar} " if ar <= 25 else ""
            hb = f"#{hr} " if hr <= 25 else ""
            label = f"{ab}{g.get('away_abbr','')} @ {hb}{g.get('home_abbr','')} ({g.get('game_time','')})"
            game_options.append(label)
        if game_options:
            sel_game = st.selectbox("Game", game_options, key="ncaa_pos_game")
            bet_type = st.selectbox("Bet Type", ["ML", "Totals", "Spread"], key="ncaa_pos_type")
            direction = st.selectbox("Direction", ["YES", "NO"], key="ncaa_pos_dir")
            line_val = ""
            if bet_type == "Totals":
                line_val = st.selectbox("Line", [str(t) for t in THRESHOLDS], key="ncaa_pos_line")
            elif bet_type == "Spread":
                line_val = st.text_input("Spread value", key="ncaa_pos_spread")
            price = st.number_input("Entry price (¢)", min_value=1, max_value=99, value=50, key="ncaa_pos_price")
            contracts = st.number_input("Contracts", min_value=1, value=10, key="ncaa_pos_contracts")
            if st.button("Add Position", key="ncaa_pos_add"):
                pos = {
                    "id": str(uuid.uuid4()),
                    "game": sel_game,
                    "type": bet_type,
                    "direction": direction,
                    "line": line_val,
                    "price": price,
                    "contracts": contracts,
                    "time": now.strftime("%I:%M %p")
                }
                st.session_state.ncaa_positions.append(pos)
                st.success("Position added!")
        else:
            st.info("No games available.")

    if st.session_state.ncaa_positions:
        for p in st.session_state.ncaa_positions:
            line_str = f" | Line: {p.get('line','')}" if p.get('line') else ""
            price_str = f" | {p.get('price','')}¢" if p.get('price') else ""
            contracts_str = f" x{p.get('contracts','')}" if p.get('contracts') else ""
            st.markdown(f"**{p.get('game','')}** — {p.get('type','')} {p.get('direction','')}{line_str}{price_str}{contracts_str} ({p.get('time','')})")
            pc1, pc2 = st.columns(2)
            with pc1:
                st.link_button("🔗 Kalshi", KALSHI_GAME_LINK, use_container_width=True)
            with pc2:
                if st.button("🗑️ Remove", key=f"ncaa_rm_{p.get('id','')}"):
                    remove_position(p.get('id',''))
                    st.rerun()
        if st.button("🗑️ Clear All Positions", key="ncaa_clear_pos"):
            st.session_state.ncaa_positions = []
            st.rerun()
    else:
        st.info("No positions tracked yet.")

    # Section E: All Games Today
    st.subheader("ALL GAMES TODAY")
    conf_groups = {}
    for g in games:
        conf = g.get('conference', '') or "Other"
        if conf not in conf_groups:
            conf_groups[conf] = []
        conf_groups[conf].append(g)
    sorted_confs = sorted([c for c in conf_groups if c != "Other"]) + (["Other"] if "Other" in conf_groups else [])
    for conf in sorted_confs:
        st.markdown(f"**{conf}**")
        for g in conf_groups[conf]:
            ar = g.get('away_rank', 99)
            hr = g.get('home_rank', 99)
            ab = f"#{ar} " if ar <= 25 else ""
            hb = f"#{hr} " if hr <= 25 else ""
            state = g.get('state', 'pre')
            if state == "post":
                border = "#64748b"
                detail = f"FINAL: {g.get('away_score',0)}-{g.get('home_score',0)}"
            elif state == "in":
                border = "#22c55e"
                period = g.get('period', 1)
                clock = g.get('clock', '')
                plabel = f"H{period}" if period <= 2 else f"OT{period-2}"
                detail = f"LIVE {plabel} {clock} | {g.get('away_score',0)}-{g.get('home_score',0)}"
            else:
                border = "#334155"
                spread = g.get('vegas_odds', {}).get('spread', '')
                ou = g.get('vegas_odds', {}).get('overUnder', '')
                bc = g.get('broadcast', '')
                parts = []
                if spread:
                    parts.append(f"Spread: {spread}")
                if ou:
                    parts.append(f"O/U: {ou}")
                if bc:
                    parts.append(f"📺 {bc}")
                detail = " | ".join(parts) if parts else g.get('game_time', '')

            html = f"""
            <div style="background:#1e293b;border-left:3px solid {border};border-radius:6px;padding:clamp(6px,1.5vw,10px);margin:4px 0;max-width:100%;box-sizing:border-box;overflow-x:hidden">
                <span style="color:#fff;font-size:clamp(12px,3vw,15px);font-weight:600">{ab}{g.get('away_abbr','')} ({g.get('away_record','')}) @ {hb}{g.get('home_abbr','')} ({g.get('home_record','')})</span>
                <span style="color:#94a3b8;font-size:clamp(11px,2.5vw,13px);margin-left:8px">{detail}</span>
            </div>
            """
            st.markdown(html, unsafe_allow_html=True)
        st.markdown("")

# ═══════════════════════════════════════════════════════
# TAB 2: SPREAD SNIPER
# ═══════════════════════════════════════════════════════
with tab_spread:

    st.subheader("SPREAD SNIPER — LIVE ALERTS")
    with st.expander("How Spread Sniping Works"):
        st.markdown("""
**Strategy**: When a team builds a big lead, the market overreacts. Spread contracts for the trailing team become cheap — buy NO on the leading team covering a huge spread.

**Half Thresholds:**
| Period | Lead Required |
|--------|--------------|
| H1 | 8+ points |
| H2 / OT | 12+ points |

**Rating by NO price:**
| Rating | Price |
|--------|-------|
| 🔥 FIRE | ≤ 40¢ |
| ✅ GOOD | 41-60¢ |
| ⚠️ OK | 61-75¢ |
| 🟡 WARN | 76-85¢ |
""")

    if st.session_state.ncaa_sniper_alerts:
        for alert in st.session_state.ncaa_sniper_alerts[:10]:
            np = alert.get('no_price', 0)
            if np <= 40:
                rating, rc = "🔥 FIRE", "#ef4444"
            elif np <= 60:
                rating, rc = "✅ GOOD", "#22c55e"
            elif np <= 75:
                rating, rc = "⚠️ OK", "#f59e0b"
            else:
                rating, rc = "🟡 WARN", "#eab308"

            html = f"""
            {MOBILE_CSS}
            <div class="alert-box" style="background:#0f172a;border-left:4px solid {rc};border-radius:8px;padding:clamp(8px,2vw,16px);margin:8px 0;max-width:100%;box-sizing:border-box;overflow-x:hidden">
                <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:4px">
                    <span style="background:{rc};color:#000;padding:2px 10px;border-radius:12px;font-weight:700;font-size:clamp(11px,2.5vw,14px)">{rating}</span>
                    <span style="color:#94a3b8;font-size:clamp(10px,2vw,12px)">{alert.get('time','')}</span>
                </div>
                <div style="color:#fff;font-size:clamp(14px,3.5vw,18px);font-weight:700;margin:6px 0">
                    {alert.get('leading_team','')} leading by {alert.get('diff',0)}
                </div>
                <div style="color:#94a3b8;font-size:clamp(11px,2.5vw,13px)">
                    Score: {alert.get('score','')} | {alert.get('period','')} | Spread: {alert.get('spread_val',0)}+ pts
                </div>
                <div style="color:#22c55e;font-size:clamp(13px,3vw,16px);font-weight:700;margin-top:6px">
                    BUY NO @ {np}¢ on {alert.get('trailing_team','')} spread
                </div>
            </div>
            """
            st.markdown(html, unsafe_allow_html=True)
            st.link_button("🔗 Trade Spreads on Kalshi", KALSHI_SPREAD_LINK, use_container_width=True)
            st.divider()
    else:
        st.info("No spread sniper alerts yet. Monitoring live games for big leads...")

    # Comeback Scanner
    st.subheader("COMEBACK SCANNER")
    tracking_count = len(st.session_state.ncaa_comeback_tracking)
    if tracking_count:
        st.caption(f"Tracking {tracking_count} game(s) with 10+ point deficits")
        for gid, info in st.session_state.ncaa_comeback_tracking.items():
            st.markdown(f"🔍 **{info.get('leading_team','')}** was up by {info.get('max_deficit',0)} — watching {info.get('trailing_side','').upper()} team")

    if st.session_state.ncaa_comeback_alerts:
        for alert in st.session_state.ncaa_comeback_alerts[:10]:
            html = f"""
            {MOBILE_CSS}
            <div class="alert-box" style="background:#0f172a;border-left:4px solid #a855f7;border-radius:8px;padding:clamp(8px,2vw,16px);margin:8px 0;max-width:100%;box-sizing:border-box;overflow-x:hidden">
                <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:4px">
                    <span style="background:#a855f7;color:#fff;padding:2px 10px;border-radius:12px;font-weight:700;font-size:clamp(11px,2.5vw,14px)">🔄 COMEBACK</span>
                    <span style="color:#94a3b8;font-size:clamp(10px,2vw,12px)">{alert.get('time','')}</span>
                </div>
                <div style="color:#fff;font-size:clamp(14px,3.5vw,18px);font-weight:700;margin:6px 0">
                    {alert.get('trailing_team','')} was down {alert.get('was_down',0)} — now within {alert.get('diff',0)}!
                </div>
                <div style="color:#94a3b8;font-size:clamp(11px,2.5vw,13px)">
                    Score: {alert.get('score','')}
                </div>
            </div>
            """
            st.markdown(html, unsafe_allow_html=True)
            st.link_button("🔗 Trade on Kalshi", KALSHI_GAME_LINK, use_container_width=True)
            st.divider()
    else:
        if not tracking_count:
            st.info("No comebacks detected. Monitoring for 10+ point deficits...")

# ═══════════════════════════════════════════════════════
# TAB 3: LIVE MONITOR
# ═══════════════════════════════════════════════════════
with tab_live:

    st.subheader("LIVE EDGE MONITOR")
    if live_games:
        for g in live_games:
            ar = g.get('away_rank', 99)
            hr = g.get('home_rank', 99)
            ab = f"#{ar} " if ar <= 25 else ""
            hb = f"#{hr} " if hr <= 25 else ""
            st.markdown(f"### {ab}{g.get('away_abbr','')} @ {hb}{g.get('home_abbr','')}")
            render_scoreboard(g)

            plays = fetch_plays(g.get('game_id', ''))
            last_play = plays[-1] if plays else None

            lc1, lc2 = st.columns([3, 2])
            with lc1:
                render_college_court(g, last_play)
                poss_team, poss_side = infer_possession(plays, g.get('home_abbr',''), g.get('away_abbr',''), g.get('home_team',''), g.get('away_team',''), g.get('home_id',''), g.get('away_id',''))
                if poss_team:
                    poss_color = get_team_color(g, poss_side) if poss_side else "#94a3b8"
                    st.markdown(f"<div style='text-align:center;color:{poss_color};font-weight:700;font-size:clamp(12px,3vw,16px)'>🏀 {poss_team} ball</div>", unsafe_allow_html=True)
            with lc2:
                st.markdown("**LAST 10 PLAYS**")
                tts_on = st.checkbox("🔊 TTS", key=f"ncaa_tts_{g.get('game_id','')}")
                if plays:
                    for p in reversed(plays):
                        icon_letter, icon_color = get_play_icon(p.get("play_type", ""), p.get("score_value", 0))
                        period = p.get("period", 0)
                        plabel = f"H{period}" if period <= 2 else f"OT{period-2}"
                        st.markdown(f"<span style='color:{icon_color};font-weight:700;font-size:16px'>{icon_letter}</span> <span style='color:#94a3b8;font-size:11px'>{plabel} {p.get('clock','')}</span> {p.get('text','')}", unsafe_allow_html=True)
                    if tts_on and last_play:
                        speak_play(last_play.get("text", ""))
                else:
                    st.caption("No play data available yet.")

            me = g.get('minutes_elapsed', 0)
            if me >= 4:
                ts = g.get('total_score', 0)
                pace = ts / me if me > 0 else 0
                proj = calc_projection(ts, me)
                pl, pc = get_pace_label(pace)

                st.markdown(f"""
                <div style="background:#1e293b;border-radius:8px;padding:clamp(6px,2vw,12px);margin:8px 0;display:flex;justify-content:space-around;flex-wrap:wrap;gap:8px;max-width:100%;box-sizing:border-box;overflow-x:hidden">
                    <div style="text-align:center"><span style="color:#94a3b8;font-size:11px">Pace</span><br><span style="color:{pc};font-weight:700;font-size:clamp(14px,3vw,18px)">{pl}</span></div>
                    <div style="text-align:center"><span style="color:#94a3b8;font-size:11px">PPM</span><br><span style="color:#fff;font-weight:700;font-size:clamp(14px,3vw,18px)">{pace:.2f}</span></div>
                    <div style="text-align:center"><span style="color:#94a3b8;font-size:11px">Proj</span><br><span style="color:#fff;font-weight:700;font-size:clamp(14px,3vw,18px)">{proj:.0f}</span></div>
                    <div style="text-align:center"><span style="color:#94a3b8;font-size:11px">Total</span><br><span style="color:#fff;font-weight:700;font-size:clamp(14px,3vw,18px)">{ts}</span></div>
                </div>
                """, unsafe_allow_html=True)

                hs = g.get('home_score', 0)
                aws = g.get('away_score', 0)
                diff = abs(hs - aws)
                if diff >= 8:
                    leading_side = "home" if hs > aws else "away"
                    leading_team = g.get(f'{leading_side}_abbr', '')
                    label = "🔥 STRONG" if diff >= 12 else "✅ GOOD"
                    label_color = "#ef4444" if diff >= 12 else "#22c55e"
                    st.markdown(f"<div style='background:#0f172a;padding:8px;border-radius:8px;border-left:3px solid {label_color};margin:6px 0;max-width:100%;box-sizing:border-box'><span style='color:{label_color};font-weight:700'>{label} ML</span> — <span style='color:#fff;font-weight:700'>{leading_team}</span> leads by {diff}</div>", unsafe_allow_html=True)
                    st.link_button(f"🔗 {leading_team} ML on Kalshi", KALSHI_GAME_LINK, use_container_width=True)

                tc1, tc2 = st.columns(2)
                with tc1:
                    st.markdown("**YES (Over)**")
                    for t in THRESHOLDS:
                        cushion = proj - t
                        if cushion >= 6:
                            if cushion >= 20:
                                safety = "🏰 FORTRESS"
                            elif cushion >= 12:
                                safety = "🟢 SAFE"
                            else:
                                safety = "🟡 TIGHT"
                            st.markdown(f"Over {t}: proj {proj:.0f} | +{cushion:.0f} {safety}")
                with tc2:
                    st.markdown("**NO (Under)**")
                    for t in THRESHOLDS:
                        cushion = t - proj
                        if cushion >= 6:
                            if cushion >= 20:
                                safety = "🏰 FORTRESS"
                            elif cushion >= 12:
                                safety = "🟢 SAFE"
                            else:
                                safety = "🟡 TIGHT"
                            st.markdown(f"Under {t}: proj {proj:.0f} | +{cushion:.0f} {safety}")
            else:
                st.caption("⏳ Waiting for 4+ minutes of play data...")
            st.divider()
    else:
        st.info("No live games right now. Check back during game times!")

# ═══════════════════════════════════════════════════════
# TAB 4: CUSHION SCANNER
# ═══════════════════════════════════════════════════════
with tab_cushion:

    st.subheader("CUSHION SCANNER (Totals)")
    game_filter_options = ["All Live Games"]
    for g in live_games:
        ar = g.get('away_rank', 99)
        hr = g.get('home_rank', 99)
        ab = f"#{ar} " if ar <= 25 else ""
        hb = f"#{hr} " if hr <= 25 else ""
        game_filter_options.append(f"{ab}{g.get('away_abbr','')} @ {hb}{g.get('home_abbr','')} (ID:{g.get('game_id','')})")
    selected_filter = st.selectbox("Filter", game_filter_options, key="ncaa_cushion_filter")
    min_minutes = st.selectbox("Min play time", [4, 8, 12, 16, 20], index=1, key="ncaa_cushion_min")

    cushion_data = []
    target_games = live_games
    max_show = 10
    if selected_filter != "All Live Games":
        gid_match = re.search(r'ID:(\d+)', selected_filter)
        if gid_match:
            gid = gid_match.group(1)
            target_games = [g for g in live_games if g.get('game_id') == gid]
            max_show = 20

    for g in target_games:
        me = g.get('minutes_elapsed', 0)
        if me < min_minutes:
            continue
        ts = g.get('total_score', 0)
        proj = calc_projection(ts, me)
        ar = g.get('away_rank', 99)
        hr = g.get('home_rank', 99)
        ab = f"#{ar} " if ar <= 25 else ""
        hb = f"#{hr} " if hr <= 25 else ""
        gname = f"{ab}{g.get('away_abbr','')} @ {hb}{g.get('home_abbr','')}"
        for t in THRESHOLDS:
            over_cushion = proj - t
            under_cushion = t - proj
            if over_cushion >= 6:
                if over_cushion >= 20:
                    safety, sc = "🏰 FORTRESS", "#22c55e"
                elif over_cushion >= 12:
                    safety, sc = "🟢 SAFE", "#22c55e"
                else:
                    safety, sc = "🟡 TIGHT", "#eab308"
                cushion_data.append({"game": gname, "dir": "YES (Over)", "line": t, "proj": proj, "cushion": over_cushion, "safety": safety, "color": sc})
            if under_cushion >= 6:
                if under_cushion >= 20:
                    safety, sc = "🏰 FORTRESS", "#22c55e"
                elif under_cushion >= 12:
                    safety, sc = "🟢 SAFE", "#22c55e"
                else:
                    safety, sc = "🟡 TIGHT", "#eab308"
                cushion_data.append({"game": gname, "dir": "NO (Under)", "line": t, "proj": proj, "cushion": under_cushion, "safety": safety, "color": sc})

    cushion_data.sort(key=lambda x: -x["cushion"])
    if cushion_data:
        for item in cushion_data[:max_show]:
            html = f"""
            <div style="background:#1e293b;border-left:3px solid {item['color']};border-radius:6px;padding:clamp(6px,2vw,12px);margin:4px 0;max-width:100%;box-sizing:border-box;overflow-x:hidden">
                <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:4px">
                    <span style="color:#fff;font-weight:700;font-size:clamp(12px,3vw,15px)">{item['game']}</span>
                    <span style="color:{item['color']};font-weight:700;font-size:clamp(11px,2.5vw,14px)">{item['safety']}</span>
                </div>
                <div style="color:#94a3b8;font-size:clamp(11px,2.5vw,13px);margin-top:4px">
                    {item['dir']} {item['line']} | Proj: {item['proj']:.0f} | Cushion: +{item['cushion']:.0f}
                </div>
            </div>
            """
            st.markdown(html, unsafe_allow_html=True)
        st.link_button("🔗 Trade Totals on Kalshi", KALSHI_GAME_LINK, use_container_width=True)
    else:
        st.info(f"No cushion opportunities found with {min_minutes}+ minutes played.")

# ═══════════════════════════════════════════════════════
# TAB 5: 🦈 SHARK SCANNER
# ═══════════════════════════════════════════════════════
with tab_shark:

    SHARK_MIN_LEAD = 7
    SHARK_MINUTES_LEFT = 5.0

    st.subheader("🦈 SHARK SCANNER")
    st.caption("Games with 7+ point lead only | Court + plays in expander | SHARK = under 5 min left")

    with st.expander("How SHARK Works"):
        st.markdown("""
### The Strategy

1. **Only games with 7+ point lead** appear — close games are hidden
2. Look for **FORTRESS SHARK** and **SAFE SHARK** ratings near game end
3. A team down 7+ with 2-3 min left needs 3+ possessions plus stops
4. The total is basically locked — high confidence window

### Cushion Labels

| Label | Meaning |
|-------|---------|
| **FORTRESS** | Locked in, would need miracle to lose |
| **SAFE** | Comfortable, pace supports it |
| **TIGHT** | Close, could swing |
| **RISKY** | Against pace |
| **+ SHARK** | Under 5 min left — highest confidence |

### Why 7+ Lead Filter?

Close games (1-6 point leads) = chaos. Skip them. A 7+ lead with under 5 minutes is the sweet spot.
""")

    shark_games = []
    for g in live_games:
        lead = abs(g.get('home_score', 0) - g.get('away_score', 0))
        if lead >= SHARK_MIN_LEAD:
            shark_games.append(g)

    sc1, sc2, sc3 = st.columns(3)
    sc1.metric("Live Games", len(live_games))
    sc2.metric("7+ Lead (Tradeable)", len(shark_games))
    sc3.metric("Filtered Out", len(live_games) - len(shark_games))

    if not shark_games:
        st.info("No live games with 7+ point lead right now. Waiting for games to separate...")
    else:
        # ── SHARK Cushion Scanner ──
        st.markdown("### SHARK CUSHION SCANNER — Totals")
        st.caption("Only showing games with **7+ point lead** — close games filtered out")

        shark_game_labels = [f"{g.get('away_abbr','')} @ {g.get('home_abbr','')}" for g in shark_games]
        shark_sel = st.selectbox("Game", ["ALL GAMES"] + shark_game_labels, key="ncaa_shark_game")
        shark_c1, shark_c2 = st.columns(2)
        shark_min_slider = shark_c1.slider("Min minutes elapsed", 0, 40, 0, key="ncaa_shark_min")
        shark_side = shark_c2.selectbox("Side", ["Both", "Over", "Under"], key="ncaa_shark_side")

        shark_found = False
        for g in shark_games:
            label = f"{g.get('away_abbr','')} @ {g.get('home_abbr','')}"
            if shark_sel != "ALL GAMES" and shark_sel != label:
                continue
            mins = g.get('minutes_elapsed', 0)
            if mins < shark_min_slider:
                continue
            total = g.get('home_score', 0) + g.get('away_score', 0)
            period = g.get('period', 1)
            if period <= 2:
                total_game_mins = GAME_MINUTES
            else:
                total_game_mins = GAME_MINUTES + (period - 2) * 5
            remaining = total_game_mins - mins
            pace = total / max(mins, 0.5)
            is_shark = remaining <= SHARK_MINUTES_LEFT
            lead = abs(g.get('home_score', 0) - g.get('away_score', 0))
            leader = g.get('home_abbr', '') if g.get('home_score', 0) > g.get('away_score', 0) else g.get('away_abbr', '')

            for thresh in THRESHOLDS:
                needed_over = thresh - total
                if shark_side in ["Both", "Over"] and needed_over > 0 and remaining > 0:
                    rate_needed = needed_over / remaining
                    cushion = pace - rate_needed
                    if cushion > 1.0:
                        safety = "FORTRESS"
                    elif cushion > 0.4:
                        safety = "SAFE"
                    elif cushion > 0.0:
                        safety = "TIGHT"
                    else:
                        safety = "RISKY"
                    if is_shark:
                        safety += " 🦈 SHARK"
                    shark_found = True
                    st.markdown(f"**{label}** OVER {thresh} — Need {needed_over:.0f} in {remaining:.0f}min ({rate_needed:.2f}/min) | Pace {pace:.2f}/min | Lead: {leader} +{lead} | **{safety}**")

                if shark_side in ["Both", "Under"] and remaining > 0:
                    projected_final = total + (remaining * pace)
                    under_cushion = thresh - projected_final
                    if projected_final < thresh:
                        if under_cushion > 10:
                            u_safety = "FORTRESS"
                        elif under_cushion > 4:
                            u_safety = "SAFE"
                        elif under_cushion > 0:
                            u_safety = "TIGHT"
                        else:
                            u_safety = "RISKY"
                        if is_shark:
                            u_safety += " 🦈 SHARK"
                        shark_found = True
                        st.markdown(f"**{label}** UNDER {thresh} — Proj {projected_final:.0f} vs Line {thresh} | Cushion {under_cushion:.1f} pts | Lead: {leader} +{lead} | **{u_safety}**")

        if not shark_found:
            st.info("No SHARK cushion opportunities match the current filter.")
        st.divider()

        # ── SHARK Pace Scanner + Court + Plays ──
        st.markdown("### SHARK PACE SCANNER")
        st.caption("Only games with 7+ point lead | Click game to see court + plays")

        for g in shark_games:
            mins = g.get('minutes_elapsed', 0)
            if mins < 2:
                continue
            total = g.get('home_score', 0) + g.get('away_score', 0)
            period = g.get('period', 1)
            if period <= 2:
                total_game_mins = GAME_MINUTES
            else:
                total_game_mins = GAME_MINUTES + (period - 2) * 5
            remaining = total_game_mins - mins
            pace = total / max(mins, 0.5)
            proj = calc_projection(total, mins)
            plabel_pace, pcolor_pace = get_pace_label(pace)
            if period <= 2:
                hl = f"H{period}"
            else:
                hl = f"OT{period-2}"
            pct = mins / total_game_mins * 100
            is_shark = remaining <= SHARK_MINUTES_LEFT
            shark_tag = " 🦈 SHARK" if is_shark else ""
            lead = abs(g.get('home_score', 0) - g.get('away_score', 0))
            leader = g.get('home_abbr', '') if g.get('home_score', 0) > g.get('away_score', 0) else g.get('away_abbr', '')

            pcol1, pcol2, pcol3 = st.columns([2, 1, 1])
            pcol1.markdown(f"**{g.get('away_abbr','')} {g.get('away_score',0)} @ {g.get('home_abbr','')} {g.get('home_score',0)}** | {hl} {g.get('clock','')} | {leader} +{lead}{shark_tag}")
            pcol2.markdown(f"Pace: **{pace:.2f}**/min <span style='color:{pcolor_pace}'>{plabel_pace}</span>", unsafe_allow_html=True)
            pcol3.markdown(f"Proj: **{proj:.0f}** | {pct:.0f}% done")

            st.progress(min(pct / 100.0, 1.0))

            ou = g.get('vegas_odds', {}).get('overUnder', None)
            if ou:
                try:
                    ou_f = float(ou)
                    diff_ou = proj - ou_f
                    if abs(diff_ou) >= 5:
                        arrow = "OVER" if diff_ou > 0 else "UNDER"
                        st.markdown(f"→ Proj {proj:.0f} vs Line {ou_f}: **{arrow} ({diff_ou:+.1f})**")
                except (ValueError, TypeError):
                    pass

            st.link_button(f"🔗 Trade on Kalshi", KALSHI_GAME_LINK, use_container_width=True)

            exp_label = f"🏀 {g.get('away_abbr','')} @ {g.get('home_abbr','')} — Court + Plays"
            with st.expander(exp_label, expanded=False):
                render_scoreboard(g)

                plays = fetch_plays(g.get('game_id', ''))
                poss_name, poss_side = infer_possession(
                    plays, g.get('home_abbr',''), g.get('away_abbr',''),
                    g.get('home_team',''), g.get('away_team',''),
                    g.get('home_id',''), g.get('away_id',''))

                shark_lc, shark_rc = st.columns(2)
                with shark_lc:
                    render_college_court(g, plays[-1] if plays else None)
                    if poss_name:
                        poss_color = get_team_color(g, poss_side) if poss_side else "#94a3b8"
                        st.markdown(f"<div style='text-align:center;color:{poss_color};font-weight:700;font-size:clamp(12px,3vw,16px)'>🏀 {poss_name} ball</div>", unsafe_allow_html=True)
                with shark_rc:
                    st.markdown(f"**Pace:** {pace:.2f} pts/min {plabel_pace}")
                    st.markdown(f"**Projected Total:** {proj:.0f}")
                    st.markdown(f"**Remaining:** {remaining:.1f} min" + (" **🦈 SHARK MODE**" if is_shark else ""))
                    st.markdown(f"**Lead:** {leader} +{lead}")

                if plays:
                    st.markdown("**Recent Plays:**")
                    shark_tts = st.checkbox("🔊 Announce plays", key=f"ncaa_shark_tts_{g.get('game_id','')}")
                    last_8 = plays[-8:]
                    for idx_p, p in enumerate(last_8):
                        p_period = p.get("period", 0)
                        if isinstance(p_period, dict):
                            p_period = p_period.get("number", 0)
                        hp = f"H{p_period}" if p_period <= 2 else f"OT{p_period-2}"
                        p_clock = p.get("clock", "")
                        if isinstance(p_clock, dict):
                            p_clock = p_clock.get("displayValue", "")
                        p_text = p.get("text", "")
                        p_type = p.get("play_type", p.get("type", ""))
                        if isinstance(p_type, dict):
                            p_type = p_type.get("text", "")
                        icon_l, icon_c = get_play_icon(p_type, p.get("score_value", p.get("score", 0)))
                        st.markdown(f"<span style='color:{icon_c};font-weight:700;font-size:16px'>{icon_l}</span> <span style='color:#94a3b8;font-size:11px'>{hp} {p_clock}</span> {p_text}", unsafe_allow_html=True)
                        if idx_p == len(last_8) - 1 and shark_tts and p_text:
                            speak_play(f"{hp} {p_clock}. {p_text}")
                else:
                    st.info("No play-by-play data available yet.")

            st.markdown("---")

# ── Footer ──
st.divider()
st.caption(f"v{VERSION} | Educational only | Not financial advice")
st.caption("Stay small. Stay quiet. Win.")
