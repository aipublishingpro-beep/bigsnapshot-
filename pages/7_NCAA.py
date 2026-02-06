import streamlit as st
st.set_page_config(page_title="BigSnapshot NCAA Edge Finder", page_icon="🏀", layout="wide")

import requests, json, time, hashlib, base64, datetime as dt
from datetime import datetime, timedelta, timezone
from streamlit_autorefresh import st_autorefresh

try:
    from auth import create_kalshi_signature
except ImportError:
    def create_kalshi_signature(*a, **k):
        return "", ""

# ── GA4 ───────────────────────────────────────────────────────────────
GA4_MID = "G-XXXXXXXXXX"
GA4_SECRET = ""
def send_ga4(event_name, params=None):
    if not GA4_SECRET: return
    try:
        cid = hashlib.md5(st.session_state.get("session_id", "ncaa").encode()).hexdigest()
        requests.post(
            "https://www.google-analytics.com/mp/collect?measurement_id=" + GA4_MID + "&api_secret=" + GA4_SECRET,
            json={"client_id": cid, "events": [{"name": event_name, "params": params or {}}]}, timeout=2)
    except Exception: pass

st_autorefresh(interval=30_000, limit=10000, key="ncaa_refresh")

# ── Config ────────────────────────────────────────────────────────────
VERSION = "2.0"
LEAGUE_AVG_TOTAL = 135
THRESHOLDS = [120.5, 125.5, 130.5, 135.5, 140.5, 145.5, 150.5, 155.5, 160.5]
HOME_COURT_ADV = 4.0
GAME_MINUTES = 40
HALVES = 2
HALF_MINUTES = 20
KALSHI_BASE = "https://trading-api.kalshi.com/trade-api/v2"
KALSHI_HEADERS = {"Content-Type": "application/json"}

if "session_id" not in st.session_state:
    st.session_state["session_id"] = hashlib.md5(str(time.time()).encode()).hexdigest()[:12]
if "positions" not in st.session_state:
    st.session_state["positions"] = {}
if "kalshi_token" not in st.session_state:
    st.session_state["kalshi_token"] = None

TEAM_COLORS = {
    "DUKE": "#003087", "UNC": "#7BAFD4", "KU": "#0051BA", "UK": "#0033A0",
    "GONZ": "#002967", "HOU": "#C8102E", "AUB": "#0C2340", "TENN": "#FF8200",
    "PUR": "#CEB888", "ALA": "#9E1B32", "BAY": "#154734", "ARIZ": "#CC0033",
    "MARQ": "#003366", "CONN": "#000E2F", "IOWA": "#FFCD00", "MSU": "#18453B",
    "CREI": "#005CA9", "ILL": "#E84A27", "FLOR": "#0021A5", "TEX": "#BF5700",
    "UCLA": "#2D68C4", "WIS": "#C5050C", "ORE": "#154733", "MICH": "#00274C",
    "ISU": "#C8102E", "TXAM": "#500000", "OHST": "#BB0000", "NCST": "#CC0000",
    "PITT": "#003594", "OKLA": "#841617", "ARK": "#9D2235", "LSU": "#461D7C",
}
def get_team_color(abbr):
    return TEAM_COLORS.get(abbr.upper(), "#555555") if abbr else "#555555"

def get_kalshi_headers():
    token = st.session_state.get("kalshi_token")
    if token: return {**KALSHI_HEADERS, "Authorization": "Bearer " + token}
    return KALSHI_HEADERS

def american_to_implied_prob(odds):
    if odds is None or odds == 0: return 0.0
    if odds > 0: return 100.0 / (odds + 100.0)
    return abs(odds) / (abs(odds) + 100.0)

def calc_minutes_elapsed(period, clock_str):
    try:
        if not clock_str:
            return max(0, ((period or 1) - 1)) * HALF_MINUTES
        parts = clock_str.replace(" ", "").split(":")
        if len(parts) == 2:
            mins_left, secs_left = int(parts[0]), int(parts[1])
        else:
            mins_left, secs_left = 0, 0
        elapsed = HALF_MINUTES - mins_left - (secs_left / 60.0)
        return (max(0, ((period or 1) - 1)) * HALF_MINUTES) + max(0, elapsed)
    except Exception: return 0.0

def get_kalshi_game_link(date_str, away_abbr, home_abbr):
    d = str(date_str or datetime.now(timezone.utc).strftime("%Y%m%d"))
    return "https://kalshi.com/markets/kxncaagame/college-basketball-game/kxncaagame-" + d + str(away_abbr or "").upper() + str(home_abbr or "").upper()

def calc_projection(home_score, away_score, minutes_elapsed):
    total = home_score + away_score
    if minutes_elapsed <= 0: return LEAGUE_AVG_TOTAL
    cur_pace = total / minutes_elapsed
    lg_pace = LEAGUE_AVG_TOTAL / GAME_MINUTES
    pct = minutes_elapsed / GAME_MINUTES
    if pct < 0.15: blend = 0.3
    elif pct < 0.5: blend = 0.5 + (pct - 0.15) * 1.0
    else: blend = 0.85 + (pct - 0.5) * 0.3
    blend = min(blend, 0.98)
    return round(((cur_pace * blend) + (lg_pace * (1 - blend))) * GAME_MINUTES, 1)

def get_pace_label(ppm):
    if ppm >= 4.0: return "VERY HIGH"
    if ppm >= 3.6: return "HIGH"
    if ppm >= 3.2: return "AVERAGE"
    if ppm >= 2.8: return "LOW"
    return "VERY LOW"

# ══════════════════════════════════════════════════════════════════════
# DATA FETCHERS
# ══════════════════════════════════════════════════════════════════════

def fetch_espn_games():
    games = []
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    url = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard?dates=" + today + "&limit=200&groups=50"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code != 200: return games
        data = r.json()
        for event in data.get("events", []):
            comp = event.get("competitions", [{}])[0]
            competitors = comp.get("competitors", [])
            if len(competitors) < 2: continue
            home = away = None
            for c in competitors:
                if c.get("homeAway") == "home": home = c
                elif c.get("homeAway") == "away": away = c
            if not home or not away: continue
            ht, at = home.get("team", {}), away.get("team", {})
            status = event.get("status", {})
            state = status.get("type", {}).get("state", "pre")
            period = status.get("period", 0)
            clock = status.get("displayClock", "")
            conf_name = ""
            notes = event.get("notes", [])
            if notes: conf_name = notes[0].get("headline", "")
            # Parse records
            home_record = home.get("records", [{}])[0].get("summary", "") if home.get("records") else ""
            away_record = away.get("records", [{}])[0].get("summary", "") if away.get("records") else ""
            game = {
                "id": str(event.get("id", "")),
                "name": event.get("name", ""),
                "shortName": event.get("shortName", ""),
                "state": state, "period": period, "clock": clock,
                "home_team": ht.get("displayName", ""), "home_abbr": ht.get("abbreviation", ""),
                "home_score": int(home.get("score", 0) or 0), "home_id": str(ht.get("id", "")),
                "home_color": "#" + str(ht.get("color", "555555")),
                "home_rank": home.get("curatedRank", {}).get("current", 99),
                "home_record": home_record,
                "away_team": at.get("displayName", ""), "away_abbr": at.get("abbreviation", ""),
                "away_score": int(away.get("score", 0) or 0), "away_id": str(at.get("id", "")),
                "away_color": "#" + str(at.get("color", "555555")),
                "away_rank": away.get("curatedRank", {}).get("current", 99),
                "away_record": away_record,
                "broadcast": "", "venue": comp.get("venue", {}).get("fullName", ""),
                "conference": conf_name, "odds": {}, "minutes_elapsed": 0.0,
            }
            odds_list = comp.get("odds", [])
            if odds_list:
                o = odds_list[0]
                game["odds"] = {
                    "spread": o.get("spread", ""), "overUnder": o.get("overUnder", ""),
                    "home_ml": o.get("homeTeamOdds", {}).get("moneyLine", ""),
                    "away_ml": o.get("awayTeamOdds", {}).get("moneyLine", ""),
                }
            bcasts = comp.get("broadcasts", [])
            if bcasts:
                names = []
                for b in bcasts:
                    for n in b.get("names", []): names.append(n)
                game["broadcast"] = ", ".join(names)
            if state == "in":
                game["minutes_elapsed"] = calc_minutes_elapsed(period, clock)
            games.append(game)
    except Exception as e:
        st.error("ESPN fetch error: " + str(e))
    return games

# ── ESPN GAME SUMMARY — BPI PREDICTOR + TEAM STATS ──────────────────
@st.cache_data(ttl=300)
def fetch_game_summary(game_id):
    """Fetch ESPN summary for a game — includes predictor (BPI win %), team stats, and odds."""
    try:
        url = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/summary?event=" + str(game_id)
        r = requests.get(url, timeout=10)
        if r.status_code != 200: return None
        return r.json()
    except Exception: return None

def parse_predictor(summary):
    """Extract ESPN BPI win probabilities from game summary."""
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
    """Extract team season stats from game summary boxscore or season stats."""
    if not summary: return {}, {}
    home_stats, away_stats = {}, {}
    # Try boxscore for season averages
    boxscore = summary.get("boxscore", {})
    teams = boxscore.get("teams", [])
    for t in teams:
        team_data = t.get("team", {})
        abbr = team_data.get("abbreviation", "")
        stats_list = t.get("statistics", [])
        parsed = {}
        for s in stats_list:
            name = s.get("name", "")
            val = s.get("displayValue", "0")
            try:
                parsed[name] = float(val)
            except (ValueError, TypeError):
                parsed[name] = val
        ha = t.get("homeAway", "")
        if ha == "home": home_stats = parsed
        elif ha == "away": away_stats = parsed
    return home_stats, away_stats

# ── ESPN TEAM SEASON STATS ───────────────────────────────────────────
@st.cache_data(ttl=600)
def fetch_team_stats(team_id):
    """Fetch full season stats for a team: PPG, opp PPG, FG%, TO, REB."""
    try:
        url = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/teams/" + str(team_id) + "?enable=stats"
        r = requests.get(url, timeout=10)
        if r.status_code != 200: return {}
        data = r.json()
        team = data.get("team", {})
        stats_raw = {}
        # Season stats come in team.record.items or team.statistics
        for stat_group in team.get("record", {}).get("items", []):
            for s in stat_group.get("stats", []):
                stats_raw[s.get("name", "")] = s.get("value", 0)
        # Also check nextEvent statistics
        for stat_entry in team.get("statistics", []):
            if isinstance(stat_entry, dict):
                stats_raw[stat_entry.get("name", "")] = stat_entry.get("value", 0)
        return stats_raw
    except Exception:
        return {}

# ── KALSHI FETCHERS ───────────────────────────────────────────────────
def fetch_kalshi_ml():
    markets = {}
    try:
        headers = get_kalshi_headers()
        r = requests.get(KALSHI_BASE + "/markets?series_ticker=KXNCAAGAME&limit=200&status=open", headers=headers, timeout=10)
        if r.status_code == 200:
            for m in r.json().get("markets", []):
                t = m.get("ticker", "")
                markets[t] = {"ticker": t, "title": m.get("title", ""),
                    "yes_price": m.get("yes_ask", 0) or m.get("last_price", 0),
                    "no_price": m.get("no_ask", 0), "volume": m.get("volume", 0)}
    except Exception: pass
    return markets

def fetch_kalshi_spreads():
    markets = {}
    try:
        headers = get_kalshi_headers()
        r = requests.get(KALSHI_BASE + "/markets?series_ticker=KXNCAASPREAD&limit=200&status=open", headers=headers, timeout=10)
        if r.status_code == 200:
            for m in r.json().get("markets", []):
                t = m.get("ticker", "")
                markets[t] = {"ticker": t, "title": m.get("title", ""),
                    "yes_price": m.get("yes_ask", 0) or m.get("last_price", 0),
                    "no_price": m.get("no_ask", 0), "volume": m.get("volume", 0)}
    except Exception: pass
    return markets

def fetch_injuries():
    injuries = {}
    try:
        r = requests.get("https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/injuries", timeout=10)
        if r.status_code == 200:
            for tb in r.json().get("items", []):
                tn = tb.get("team", {}).get("displayName", "Unknown")
                ta = tb.get("team", {}).get("abbreviation", "")
                plist = []
                for inj in tb.get("injuries", []):
                    ath = inj.get("athlete", {})
                    plist.append({"name": ath.get("displayName", "Unknown"),
                        "position": ath.get("position", {}).get("abbreviation", ""),
                        "status": inj.get("status", ""),
                        "detail": inj.get("longComment", inj.get("shortComment", ""))})
                if plist: injuries[ta] = {"team": tn, "players": plist}
    except Exception: pass
    return injuries

def fetch_yesterday_teams():
    b2b = set()
    try:
        y = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y%m%d")
        r = requests.get("https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard?dates=" + y + "&limit=200", timeout=10)
        if r.status_code == 200:
            for ev in r.json().get("events", []):
                for comp in ev.get("competitions", []):
                    for c in comp.get("competitors", []):
                        a = c.get("team", {}).get("abbreviation", "")
                        if a: b2b.add(a.upper())
    except Exception: pass
    return b2b

# ══════════════════════════════════════════════════════════════════════
# EDGE MODEL — 7-FACTOR NCAA PREGAME EDGE CALCULATOR
# ══════════════════════════════════════════════════════════════════════

def calc_advanced_edge(game, b2b_teams, summary=None, injuries=None):
    """
    9-factor edge model:
    1. ESPN BPI win probability (ESPN's own model — SOS, pace, travel, altitude)
    2. Vegas implied probability vs BPI mismatch
    3. Home court advantage (weighted)
    4. Team record / win %
    5. Ranking gap
    6. Back-to-back fatigue
    7. Offensive vs defensive matchup (PPG)
    8. Injury impact (star players OUT = real penalty)
    9. 3-point shooting differential
    Returns dict with edge details and a composite score.
    """
    edges = []
    score = 0.0  # positive = lean home, negative = lean away
    ha = game.get("home_abbr", "").upper()
    aa = game.get("away_abbr", "").upper()

    # ── Factor 1: ESPN BPI Predictor ──────────────────────────────────
    bpi = None
    if summary:
        bpi = parse_predictor(summary)
    if bpi:
        home_bpi = bpi.get("home_win_pct", 0.5)
        away_bpi = bpi.get("away_win_pct", 0.5)
        edges.append("ESPN BPI: " + game["home_team"] + " " + "{:.0%}".format(home_bpi) +
                     " | " + game["away_team"] + " " + "{:.0%}".format(away_bpi))
        # BPI is heavily weighted — it already incorporates efficiency, SOS, pace, travel
        bpi_edge = (home_bpi - 0.5) * 20  # scale to points
        score += bpi_edge
    else:
        edges.append("ESPN BPI: unavailable")

    # ── Factor 2: Vegas implied vs BPI mismatch ──────────────────────
    home_ml = game.get("odds", {}).get("home_ml")
    if home_ml and bpi:
        try:
            vegas_prob = american_to_implied_prob(float(home_ml))
            bpi_prob = bpi.get("home_win_pct", 0.5)
            gap = bpi_prob - vegas_prob
            if abs(gap) >= 0.03:
                who = game["home_team"] if gap > 0 else game["away_team"]
                edges.append("BPI vs VEGAS GAP: " + "{:.1%}".format(abs(gap)) + " edge on " + who)
                score += gap * 15
        except (ValueError, TypeError): pass

    # ── Factor 3: Home court advantage ────────────────────────────────
    edges.append("Home court: " + game["home_team"] + " +" + str(HOME_COURT_ADV))
    score += HOME_COURT_ADV / 2  # ~2 points of edge

    # ── Factor 4: Record / win percentage ─────────────────────────────
    home_rec = game.get("home_record", "")
    away_rec = game.get("away_record", "")
    home_wpct = _parse_win_pct(home_rec)
    away_wpct = _parse_win_pct(away_rec)
    if home_wpct is not None and away_wpct is not None:
        rec_edge = (home_wpct - away_wpct) * 10
        score += rec_edge
        edges.append("Records: " + game["home_team"] + " (" + home_rec + " | " +
                     "{:.0%}".format(home_wpct) + ") vs " + game["away_team"] + " (" +
                     away_rec + " | " + "{:.0%}".format(away_wpct) + ")")

    # ── Factor 5: Ranking gap ─────────────────────────────────────────
    hr = game.get("home_rank", 99)
    ar = game.get("away_rank", 99)
    if hr <= 25 or ar <= 25:
        if hr <= 25 and ar <= 25:
            rank_edge = (ar - hr) * 0.3  # higher rank number = worse
            edges.append("Ranked matchup: #" + str(hr) + " vs #" + str(ar))
        elif hr <= 25:
            rank_edge = 3.0
            edges.append(game["home_team"] + " ranked #" + str(hr) + " (unranked opponent)")
        else:
            rank_edge = -3.0
            edges.append(game["away_team"] + " ranked #" + str(ar) + " (unranked opponent)")
        score += rank_edge

    # ── Factor 6: Back-to-back fatigue ────────────────────────────────
    if ha in b2b_teams:
        edges.append("FATIGUE: " + game["home_team"] + " on B2B")
        score -= 2.0
    if aa in b2b_teams:
        edges.append("FATIGUE: " + game["away_team"] + " on B2B")
        score += 2.0

    # ── Factor 7: Offensive/Defensive matchup from summary ────────────
    home_stats, away_stats = {}, {}
    if summary:
        home_stats, away_stats = parse_team_stats_from_summary(summary)
        h_ppg = home_stats.get("avgPoints", home_stats.get("points", 0))
        a_ppg = away_stats.get("avgPoints", away_stats.get("points", 0))
        if h_ppg and a_ppg:
            try:
                h_ppg, a_ppg = float(h_ppg), float(a_ppg)
                ppg_edge = (h_ppg - a_ppg) * 0.3
                score += ppg_edge
                edges.append("Scoring: " + game["home_team"] + " " + "{:.1f}".format(h_ppg) +
                             " PPG vs " + game["away_team"] + " " + "{:.1f}".format(a_ppg) + " PPG")
            except (ValueError, TypeError): pass

    # ── Factor 8: Injury impact (star players OUT) ────────────────────
    if injuries:
        # Get leading scorers from summary if available
        home_leaders = _get_team_leaders(summary, "home")
        away_leaders = _get_team_leaders(summary, "away")

        home_inj = injuries.get(ha, {}).get("players", [])
        away_inj = injuries.get(aa, {}).get("players", [])

        home_out = [p for p in home_inj if "out" in (p.get("status", "") or "").lower()]
        away_out = [p for p in away_inj if "out" in (p.get("status", "") or "").lower()]
        home_dtd = [p for p in home_inj if "day" in (p.get("status", "") or "").lower() or "doubt" in (p.get("status", "") or "").lower()]
        away_dtd = [p for p in away_inj if "day" in (p.get("status", "") or "").lower() or "doubt" in (p.get("status", "") or "").lower()]

        for p in home_out:
            pname = p.get("name", "")
            is_star = _is_star_player(pname, home_leaders)
            if is_star:
                edges.append("INJURY [STAR OUT]: " + game["home_team"] + " - " + pname + " (OUT)")
                score -= 4.0  # big penalty for star player out
            else:
                edges.append("INJURY [OUT]: " + game["home_team"] + " - " + pname)
                score -= 1.0
        for p in home_dtd:
            edges.append("INJURY [DTD]: " + game["home_team"] + " - " + p.get("name", ""))
            score -= 0.5

        for p in away_out:
            pname = p.get("name", "")
            is_star = _is_star_player(pname, away_leaders)
            if is_star:
                edges.append("INJURY [STAR OUT]: " + game["away_team"] + " - " + pname + " (OUT)")
                score += 4.0  # big boost for opponent when star is out
            else:
                edges.append("INJURY [OUT]: " + game["away_team"] + " - " + pname)
                score += 1.0
        for p in away_dtd:
            edges.append("INJURY [DTD]: " + game["away_team"] + " - " + p.get("name", ""))
            score += 0.5

    # ── Factor 9: 3-point shooting differential ──────────────────────
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
                # A team shooting 38% vs 30% from 3 is a significant edge
                three_edge = pct_gap * 0.15 + made_gap * 0.3
                score += three_edge
                edges.append("3PT: " + game["home_team"] + " " + "{:.1f}".format(h_3pct) + "% (" +
                             "{:.1f}".format(h_3pm) + " made/gm) vs " + game["away_team"] + " " +
                             "{:.1f}".format(a_3pct) + "% (" + "{:.1f}".format(a_3pm) + " made/gm)")
                if abs(pct_gap) >= 5:
                    who = game["home_team"] if pct_gap > 0 else game["away_team"]
                    edges.append("3PT EDGE: " + who + " has " + "{:.1f}".format(abs(pct_gap)) + "% shooting advantage from deep")
        except (ValueError, TypeError): pass

    # ── Composite verdict ─────────────────────────────────────────────
    if abs(score) >= 8:
        strength = "STRONG"
    elif abs(score) >= 4:
        strength = "MODERATE"
    elif abs(score) >= 1.5:
        strength = "LEAN"
    else:
        strength = "TOSS-UP"

    if score > 0:
        pick = game["home_team"]
        side = "HOME"
    else:
        pick = game["away_team"]
        side = "AWAY"

    edges.insert(0, "EDGE: " + strength + " " + side + " (" + pick + ") | Score: " + "{:+.1f}".format(score))

    return {"edges": edges, "score": score, "pick": pick, "side": side, "strength": strength, "bpi": bpi}

def _parse_win_pct(record_str):
    """Parse '18-3' into win percentage."""
    try:
        if not record_str or "-" not in record_str: return None
        parts = record_str.split("-")
        w, l = int(parts[0]), int(parts[1].split(" ")[0])
        total = w + l
        if total == 0: return None
        return w / total
    except Exception: return None

def _get_team_leaders(summary, home_away):
    """Extract top scorers from ESPN summary leaders section."""
    leaders = []
    if not summary: return leaders
    try:
        for leader_group in summary.get("leaders", []):
            team_data = leader_group.get("team", {})
            # Match by homeAway field or by position in array
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
    """Check if injured player is a team leader (top 3 scorer)."""
    if not leaders_list or not player_name: return False
    pname = player_name.lower().strip()
    for i, leader in enumerate(leaders_list[:3]):
        lname = leader.get("name", "").lower().strip()
        # Fuzzy match — last name match is enough
        p_parts = pname.split()
        l_parts = lname.split()
        if p_parts and l_parts:
            if p_parts[-1] == l_parts[-1]:
                return True
            if pname in lname or lname in pname:
                return True
    return False

def fetch_plays(game_id):
    plays = []
    try:
        url = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/summary?event=" + str(game_id)
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            for item in data.get("plays", []):
                plays.append({"text": item.get("text", ""),
                    "period": item.get("period", {}).get("number", 0),
                    "clock": item.get("clock", {}).get("displayValue", ""),
                    "score": item.get("scoreValue", 0),
                    "team_id": str(item.get("team", {}).get("id", "")),
                    "type": item.get("type", {}).get("text", "")})
    except Exception: pass
    return plays

def remove_position(ticker):
    if ticker in st.session_state["positions"]:
        del st.session_state["positions"][ticker]

# ══════════════════════════════════════════════════════════════════════
# PART 2: DISPLAY FUNCTIONS + LIVE EDGE MONITOR
# ══════════════════════════════════════════════════════════════════════

def render_scoreboard(g):
    state = g["state"]
    ha, aa = g["home_abbr"], g["away_abbr"]
    hc = g.get("home_color", get_team_color(ha))
    ac = g.get("away_color", get_team_color(aa))
    hr = "#" + str(g["home_rank"]) + " " if g.get("home_rank", 99) <= 25 else ""
    ar = "#" + str(g["away_rank"]) + " " if g.get("away_rank", 99) <= 25 else ""
    h_rec = " (" + g.get("home_record", "") + ")" if g.get("home_record") else ""
    a_rec = " (" + g.get("away_record", "") + ")" if g.get("away_record") else ""
    if state == "in":
        p = g.get("period", 0)
        hl = "H" + str(p) if p <= 2 else "OT" + str(p - 2)
        status_html = "<span style='color:#e74c3c;font-weight:700'>LIVE " + hl + " " + str(g.get("clock", "")) + "</span>"
    elif state == "post":
        status_html = "<span style='color:#888'>FINAL</span>"
    else:
        status_html = "<span style='color:#aaa'>" + str(g.get("broadcast", "TBD")) + "</span>"
    conf = g.get("conference", "")
    conf_html = "<div style='font-size:10px;color:#888;margin-bottom:2px'>" + conf + "</div>" if conf else ""
    venue = g.get("venue", "")
    venue_html = "<div style='font-size:10px;color:#777'>" + venue + "</div>" if venue else ""
    html = (
        "<div style='background:#1a1a2e;border-radius:10px;padding:12px;margin:6px 0;"
        "border-left:4px solid " + ac + ";border-right:4px solid " + hc + "'>"
        + conf_html +
        "<div style='display:flex;justify-content:space-between;align-items:center'>"
        "<div style='text-align:left;flex:1'>"
        "<div style='font-size:11px;color:" + ac + "'>" + ar + str(g["away_team"]) + a_rec + "</div>"
        "<div style='font-size:22px;font-weight:700;color:white'>" + str(g["away_score"]) + "</div>"
        "</div>"
        "<div style='text-align:center;flex:1'>" + status_html + "</div>"
        "<div style='text-align:right;flex:1'>"
        "<div style='font-size:11px;color:" + hc + "'>" + hr + str(g["home_team"]) + h_rec + "</div>"
        "<div style='font-size:22px;font-weight:700;color:white'>" + str(g["home_score"]) + "</div>"
        "</div></div>" + venue_html + "</div>"
    )
    st.markdown(html, unsafe_allow_html=True)

def get_play_badge(play_type):
    badges = {"three": ("3PT", "#e74c3c"), "dunk": ("DUNK", "#e67e22"), "steal": ("STL", "#2ecc71"),
        "block": ("BLK", "#9b59b6"), "turnover": ("TO", "#e74c3c"), "foul": ("FOUL", "#f39c12"),
        "free throw": ("FT", "#3498db"), "rebound": ("REB", "#1abc9c")}
    for key, (lbl, color) in badges.items():
        if key in (play_type or "").lower(): return lbl, color
    return "PLAY", "#555"

def get_play_icon(text):
    t = (text or "").lower()
    if "three" in t or "3pt" in t: return "[3PT]"
    if "dunk" in t: return "[DUNK]"
    if "steal" in t: return "[STL]"
    if "block" in t: return "[BLK]"
    if "turnover" in t: return "[TO]"
    if "foul" in t: return "[FOUL]"
    if "free throw" in t: return "[FT]"
    if "rebound" in t: return "[REB]"
    return ">"

def infer_possession(plays, home_abbr, away_abbr, home_name, away_name, home_id="", away_id=""):
    """Infer who has the ball from recent play-by-play. Returns (team_name, side) or (None, None)."""
    if not plays: return None, None
    h_ab, a_ab = home_abbr.lower(), away_abbr.lower()
    h_nm, a_nm = home_name.lower(), away_name.lower()
    h_id, a_id = str(home_id), str(away_id)

    def _match_home(tid, txt):
        tid = str(tid)
        return tid == h_id or h_ab in txt or h_nm in txt

    def _match_away(tid, txt):
        tid = str(tid)
        return tid == a_id or a_ab in txt or a_nm in txt

    for p in reversed(plays[-12:]):
        tid = str(p.get("team_id", ""))
        txt = (p.get("text", "") or "").lower()
        ptype = (p.get("type", "") or "").lower()
        # Steal — stealer has ball
        if "steal" in ptype or "steal" in txt:
            if _match_home(tid, txt): return home_name, "home"
            if _match_away(tid, txt): return away_name, "away"
        # Turnover — skip, let next play resolve
        if "turnover" in ptype or "turnover" in txt: continue
        # Made shot — other team inbounds
        if "made" in txt or "make" in ptype:
            if _match_home(tid, txt): return away_name, "away"
            if _match_away(tid, txt): return home_name, "home"
        # Rebound — that team has ball
        if "rebound" in ptype or "rebound" in txt:
            if _match_home(tid, txt): return home_name, "home"
            if _match_away(tid, txt): return away_name, "away"
        # Foul — skip, ambiguous
        if "foul" in ptype or "foul" in txt: continue
        # Missed shot — check for rebound next, skip
        if "missed" in txt or "miss" in ptype: continue
        # Fallback: last team to act
        if _match_home(tid, txt): return home_name, "home"
        if _match_away(tid, txt): return away_name, "away"
    return None, None

def render_court(home_abbr, away_abbr, score_home=0, score_away=0, poss_name=None, poss_side=None):
    ball_x = 375 if poss_side == "home" else 125 if poss_side == "away" else -100
    ball_vis = "visible" if poss_side in ("home", "away") else "hidden"
    svg = (
        "<svg viewBox='0 0 500 280' style='width:100%;max-width:500px;background:#1a1a2e;border-radius:8px'>"
        "<rect x='25' y='15' width='450' height='230' fill='none' stroke='#444' stroke-width='2' rx='5'/>"
        "<line x1='250' y1='15' x2='250' y2='245' stroke='#444' stroke-width='1.5'/>"
        "<circle cx='250' cy='130' r='35' fill='none' stroke='#444' stroke-width='1.5'/>"
        "<rect x='25' y='70' width='80' height='120' fill='none' stroke='#444' stroke-width='1'/>"
        "<rect x='395' y='70' width='80' height='120' fill='none' stroke='#444' stroke-width='1'/>"
        "<text x='125' y='135' text-anchor='middle' fill='#aaa' font-size='16' font-weight='700'>" + str(away_abbr) + "</text>"
        "<text x='375' y='135' text-anchor='middle' fill='#aaa' font-size='16' font-weight='700'>" + str(home_abbr) + "</text>"
        "<text x='125' y='155' text-anchor='middle' fill='white' font-size='20' font-weight='700'>" + str(score_away) + "</text>"
        "<text x='375' y='155' text-anchor='middle' fill='white' font-size='20' font-weight='700'>" + str(score_home) + "</text>"
        "<text x='" + str(ball_x) + "' y='270' text-anchor='middle' fill='#f1c40f' font-size='13' font-weight='700' visibility='" + ball_vis + "'>BALL</text>"
        "</svg>"
    )
    st.markdown(svg, unsafe_allow_html=True)
    if poss_name:
        st.markdown("<div style='text-align:center;padding:2px;color:#f1c40f;font-size:13px;font-weight:700'>" + str(poss_name) + " BALL</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
# MAIN PAGE LAYOUT
# ══════════════════════════════════════════════════════════════════════
st.markdown("## BIGSNAPSHOT NCAA EDGE FINDER")
st.caption("v" + VERSION + " | " + datetime.now(timezone.utc).strftime("%A %b %d, %Y | %H:%M UTC") + " | NCAA Men's Basketball | 9-Factor Edge Model")

all_games = fetch_espn_games()
kalshi_ml = fetch_kalshi_ml()
kalshi_spreads = fetch_kalshi_spreads()
injuries = fetch_injuries()
b2b_teams = fetch_yesterday_teams()

live_games = [g for g in all_games if g["state"] == "in"]
scheduled_games = [g for g in all_games if g["state"] == "pre"]
final_games = [g for g in all_games if g["state"] == "post"]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Today's Games", len(all_games))
c2.metric("Live", len(live_games))
c3.metric("Scheduled", len(scheduled_games))
c4.metric("Final", len(final_games))
st.divider()

# ── VEGAS vs KALSHI MISPRICING ALERT ─────────────────────────────────
mispricings = []
for g in all_games:
    if g["state"] != "pre": continue
    home_ml = g.get("odds", {}).get("home_ml")
    if not home_ml: continue
    try: home_ml = float(home_ml)
    except (TypeError, ValueError): continue
    espn_prob = american_to_implied_prob(home_ml)
    if espn_prob <= 0: continue
    ha_up = g.get("home_abbr", "").upper()
    aa_up = g.get("away_abbr", "").upper()
    # Also check BPI for triple-source comparison
    summary = fetch_game_summary(g["id"])
    bpi = parse_predictor(summary) if summary else None
    bpi_prob = bpi.get("home_win_pct", 0) if bpi else 0
    for ticker, mk in kalshi_ml.items():
        t_upper = ticker.upper()
        if ha_up in t_upper and aa_up in t_upper:
            yp = mk.get("yes_price", 0) or 0
            kalshi_prob = yp / 100.0 if yp > 1 else yp
            diff = abs(espn_prob - kalshi_prob)
            if diff >= 0.05:
                mp = {"game": g["shortName"], "espn_prob": espn_prob,
                    "kalshi_prob": kalshi_prob, "diff": diff, "ticker": ticker,
                    "home": g["home_team"]}
                if bpi_prob > 0:
                    mp["bpi_prob"] = bpi_prob
                mispricings.append(mp)
            break

if mispricings:
    st.markdown("### VEGAS vs KALSHI MISPRICING ALERTS")
    for mp in sorted(mispricings, key=lambda x: -x["diff"]):
        diff_pct = mp["diff"] * 100
        line = ("**" + str(mp["game"]) + "** -- Vegas: " + "{:.0%}".format(mp["espn_prob"]) +
            " | Kalshi: " + "{:.0%}".format(mp["kalshi_prob"]))
        if mp.get("bpi_prob"):
            line += " | ESPN BPI: " + "{:.0%}".format(mp["bpi_prob"])
        line += " (**" + "{:.1f}".format(diff_pct) + "% gap**) | `" + str(mp["ticker"]) + "`"
        st.markdown(line)
    st.divider()

# ── LIVE EDGE MONITOR ────────────────────────────────────────────────
if live_games:
    st.markdown("### LIVE EDGE MONITOR")
    for g in live_games:
        mins = g.get("minutes_elapsed", 0)
        total = g["home_score"] + g["away_score"]
        pace_per_min = total / max(mins, 0.5)
        projection = calc_projection(g["home_score"], g["away_score"], mins)
        pace_label = get_pace_label(pace_per_min)
        pct_done = mins / GAME_MINUTES * 100
        period = g.get("period", 0)
        half_str = "H" + str(period) if period <= 2 else "OT" + str(period - 2)

        exp_label = (str(g["away_abbr"]) + " " + str(g["away_score"]) + " @ " +
            str(g["home_abbr"]) + " " + str(g["home_score"]) + " -- " + half_str + " " + str(g["clock"]))
        with st.expander(exp_label, expanded=True):
            render_scoreboard(g)
            plays = fetch_plays(g["id"])

            # Possession inference from plays using team names
            poss_name, poss_side = infer_possession(
                plays, g["home_abbr"], g["away_abbr"],
                g["home_team"], g["away_team"],
                g.get("home_id", ""), g.get("away_id", ""))

            lc, rc = st.columns(2)
            with lc:
                render_court(g["home_abbr"], g["away_abbr"],
                    score_home=g["home_score"], score_away=g["away_score"],
                    poss_name=poss_name, poss_side=poss_side)
            with rc:
                st.markdown("**Pace:** " + "{:.2f}".format(pace_per_min) + " pts/min " + pace_label)
                st.markdown("**Projected Total:** " + str(projection))
                st.markdown("**Game Progress:** " + "{:.0f}".format(pct_done) + "% (" + "{:.1f}".format(mins) + "/" + str(GAME_MINUTES) + " min)")
                lead = g["home_score"] - g["away_score"]
                if lead > 0:
                    st.markdown("**Lead:** " + str(g["home_team"]) + " +" + str(lead))
                elif lead < 0:
                    st.markdown("**Lead:** " + str(g["away_team"]) + " +" + str(abs(lead)))
                else:
                    st.markdown("**Lead:** TIE")
                espn_ou = g.get("odds", {}).get("overUnder")
                if espn_ou:
                    try:
                        ou_val = float(espn_ou)
                        diff = projection - ou_val
                        if abs(diff) >= 5:
                            direction = "OVER" if diff > 0 else "UNDER"
                            st.markdown("**Totals Edge:** Proj " + str(projection) + " vs Line " + str(ou_val) + " -> **" + direction + " (" + "{:+.1f}".format(diff) + ")**")
                    except (ValueError, TypeError): pass

            if plays:
                st.markdown("**Recent Plays:**")
                for p in plays[-6:]:
                    icon = get_play_icon(p.get("type", ""))
                    hp = "H" + str(p["period"]) if p.get("period", 0) <= 2 else "OT" + str(p["period"] - 2)
                    st.markdown("<span style='color:#888;font-size:12px'>" + hp + " " + str(p.get("clock", "")) + " " + icon + " " + str(p.get("text", "")) + "</span>", unsafe_allow_html=True)

            today_str = datetime.now(timezone.utc).strftime("%Y%m%d")
            link = get_kalshi_game_link(today_str, g["away_abbr"], g["home_abbr"])
            st.markdown("[Trade on Kalshi](" + link + ")")
    st.divider()

# ══════════════════════════════════════════════════════════════════════
# PART 3: SCANNERS, TRACKERS, FOOTER
# ══════════════════════════════════════════════════════════════════════

# ── CUSHION SCANNER (Totals) ─────────────────────────────────────────
if live_games:
    st.markdown("### CUSHION SCANNER -- Totals")
    cs_games = [str(g["away_abbr"]) + " @ " + str(g["home_abbr"]) for g in live_games]
    cs_sel = st.selectbox("Game", ["ALL GAMES"] + cs_games, key="cs_game")
    cs_c1, cs_c2 = st.columns(2)
    cs_min = cs_c1.slider("Min minutes elapsed", 0, 40, 5, key="cs_min")
    cs_side = cs_c2.selectbox("Side", ["Both", "Over", "Under"], key="cs_side")

    for g in live_games:
        label = str(g["away_abbr"]) + " @ " + str(g["home_abbr"])
        if cs_sel != "ALL GAMES" and cs_sel != label: continue
        mins = g.get("minutes_elapsed", 0)
        if mins < cs_min: continue
        total = g["home_score"] + g["away_score"]
        remaining = GAME_MINUTES - mins

        for thresh in THRESHOLDS:
            needed_over = thresh - total
            if cs_side in ["Both", "Over"] and needed_over > 0 and remaining > 0:
                rate_needed = needed_over / remaining
                pace_now = total / max(mins, 0.5)
                cushion = pace_now - rate_needed
                if cushion > 1.0: safety = "FORTRESS"
                elif cushion > 0.4: safety = "SAFE"
                elif cushion > 0.0: safety = "TIGHT"
                else: safety = "RISKY"
                if remaining <= 6: safety += " SHARK MODE"
                st.markdown(
                    "**" + label + "** OVER " + str(thresh) + " -- Need " + "{:.0f}".format(needed_over) +
                    " in " + "{:.0f}".format(remaining) + "min (" + "{:.2f}".format(rate_needed) +
                    "/min) | Pace " + "{:.2f}".format(pace_now) + "/min | **" + safety + "**")
            if cs_side in ["Both", "Under"] and remaining > 0:
                projected_final = total + (remaining * (total / max(mins, 0.5)))
                under_cushion = thresh - projected_final
                if under_cushion > 10: u_safety = "FORTRESS"
                elif under_cushion > 4: u_safety = "SAFE"
                elif under_cushion > 0: u_safety = "TIGHT"
                else: u_safety = "RISKY"
                if projected_final < thresh:
                    if remaining <= 6: u_safety += " SHARK MODE"
                    st.markdown(
                        "**" + label + "** UNDER " + str(thresh) + " -- Proj " +
                        "{:.0f}".format(projected_final) + " vs Line " + str(thresh) + " | **" + u_safety + "**")
    st.divider()

# ── PACE SCANNER ─────────────────────────────────────────────────────
if live_games:
    st.markdown("### PACE SCANNER")
    for g in live_games:
        mins = g.get("minutes_elapsed", 0)
        if mins < 2: continue
        total = g["home_score"] + g["away_score"]
        pace = total / max(mins, 0.5)
        proj = calc_projection(g["home_score"], g["away_score"], mins)
        plabel = get_pace_label(pace)
        period = g.get("period", 0)
        half_str = "H" + str(period) if period <= 2 else "OT" + str(period - 2)
        pct = mins / GAME_MINUTES * 100
        col1, col2, col3 = st.columns([2, 1, 1])
        col1.markdown("**" + str(g["away_abbr"]) + " " + str(g["away_score"]) + " @ " + str(g["home_abbr"]) + " " + str(g["home_score"]) + "** | " + half_str + " " + str(g["clock"]))
        col2.markdown("Pace: **" + "{:.2f}".format(pace) + "**/min " + plabel)
        col3.markdown("Proj: **" + str(proj) + "** | " + "{:.0f}".format(pct) + "% done")
        st.progress(min(pct / 100, 1.0))
        espn_ou = g.get("odds", {}).get("overUnder")
        if espn_ou:
            try:
                ou_val = float(espn_ou)
                diff = proj - ou_val
                if abs(diff) >= 5:
                    arrow = "OVER" if diff > 0 else "UNDER"
                    st.markdown("-> Proj " + str(proj) + " vs Line " + str(ou_val) + ": **" + arrow + " (" + "{:+.1f}".format(diff) + ")**")
            except (ValueError, TypeError): pass
    st.divider()

# ── PRE-GAME ALIGNMENT (9-Factor Edge Model) ─────────────────────────
if scheduled_games:
    st.markdown("### PRE-GAME ALIGNMENT -- 9-Factor Edge Model")
    st.caption("ESPN BPI + Vegas + Home Court + Records + Rankings + B2B + Scoring + Injuries + 3PT")

    if st.button("ADD ALL PRE-GAME PICKS", key="add_all_pre"):
        for g in scheduled_games:
            ticker = "KXNCAAGAME-" + str(g["away_abbr"]) + str(g["home_abbr"])
            if ticker not in st.session_state["positions"]:
                summary = fetch_game_summary(g["id"])
                edge = calc_advanced_edge(g, b2b_teams, summary=summary, injuries=injuries)
                st.session_state["positions"][ticker] = {
                    "ticker": ticker, "game": g["shortName"],
                    "side": edge.get("side", "HOME"), "type": "ML",
                    "contracts": 1, "price": 50, "edges": edge.get("edges", []),
                    "game_id": g["id"], "home_abbr": g["home_abbr"], "away_abbr": g["away_abbr"]}
        st.rerun()

    for idx, g in enumerate(scheduled_games):
        summary = fetch_game_summary(g["id"])
        edge = calc_advanced_edge(g, b2b_teams, summary=summary, injuries=injuries)
        edge_list = edge.get("edges", [])
        strength = edge.get("strength", "TOSS-UP")
        pick = edge.get("pick", "")
        sc = edge.get("score", 0)

        # Color code by strength
        if strength == "STRONG": badge_color = "#2ecc71"
        elif strength == "MODERATE": badge_color = "#f39c12"
        elif strength == "LEAN": badge_color = "#3498db"
        else: badge_color = "#888"

        hr = "#" + str(g["home_rank"]) + " " if g.get("home_rank", 99) <= 25 else ""
        ar = "#" + str(g["away_rank"]) + " " if g.get("away_rank", 99) <= 25 else ""
        spread = g.get("odds", {}).get("spread", "N/A")
        ou = g.get("odds", {}).get("overUnder", "N/A")

        with st.container():
            st.markdown(
                "<div style='background:#1a1a2e;border-radius:8px;padding:10px;margin:8px 0;"
                "border-left:4px solid " + badge_color + "'>"
                "<span style='color:" + badge_color + ";font-weight:700;font-size:14px'>" + strength + "</span> "
                "<span style='color:white;font-weight:700'>" + ar + str(g["away_team"]) + " @ " + hr + str(g["home_team"]) + "</span>"
                "<br><span style='color:#aaa;font-size:12px'>Spread: " + str(spread) + " | O/U: " + str(ou) + " | " + str(g.get("broadcast", "")) + "</span>"
                "</div>", unsafe_allow_html=True)

            for e in edge_list:
                if "EDGE:" in e:
                    st.markdown("**" + e + "**")
                elif "STAR OUT" in e:
                    st.markdown("<span style='color:#e74c3c;font-weight:700'>" + e + "</span>", unsafe_allow_html=True)
                elif "3PT EDGE" in e:
                    st.markdown("<span style='color:#3498db;font-weight:700'>" + e + "</span>", unsafe_allow_html=True)
                elif "BPI vs VEGAS GAP" in e:
                    st.markdown("<span style='color:#2ecc71;font-weight:700'>" + e + "</span>", unsafe_allow_html=True)
                else:
                    st.markdown("  " + e)

            today_str = datetime.now(timezone.utc).strftime("%Y%m%d")
            link = get_kalshi_game_link(today_str, g["away_abbr"], g["home_abbr"])
            st.markdown("[Trade on Kalshi](" + link + ")")
            st.markdown("---")
    st.divider()

# ── INJURY REPORT ────────────────────────────────────────────────────
if injuries:
    st.markdown("### INJURY REPORT")
    today_abbrs = set()
    for g in all_games:
        today_abbrs.add(g["home_abbr"].upper())
        today_abbrs.add(g["away_abbr"].upper())
    shown = False
    for abbr, data in injuries.items():
        if abbr.upper() not in today_abbrs: continue
        shown = True
        st.markdown("**" + str(data["team"]) + "**")
        for p in data["players"]:
            s = (p["status"] or "").lower()
            if "out" in s: marker = "[OUT]"
            elif "day" in s or "doubt" in s: marker = "[DTD]"
            else: marker = "[ACTIVE]"
            st.markdown("  " + marker + " " + str(p["name"]) + " (" + str(p["position"]) + ") -- " + str(p["status"]) + ": " + str(p.get("detail", "")))
    if not shown:
        st.info("No injuries reported for today's teams.")
    st.divider()

# ── POSITION TRACKER ─────────────────────────────────────────────────
st.markdown("### POSITION TRACKER")
with st.expander("ADD NEW POSITION"):
    game_opts = [str(g["away_abbr"]) + " @ " + str(g["home_abbr"]) for g in all_games]
    if game_opts:
        p_game = st.selectbox("Game", game_opts, key="pt_game")
        p_c1, p_c2 = st.columns(2)
        p_type = p_c1.selectbox("Bet Type", ["ML", "Totals", "Spread"], key="pt_type")
        p_side = p_c2.selectbox("Side", ["HOME", "AWAY", "OVER", "UNDER"], key="pt_side")
        p_c3, p_c4 = st.columns(2)
        p_contracts = p_c3.number_input("Contracts", 1, 500, 10, key="pt_contracts")
        p_price = p_c4.number_input("Price (cents)", 1, 99, 50, key="pt_price")
        if st.button("ADD POSITION", key="pt_add"):
            sel_idx = game_opts.index(p_game)
            g = all_games[sel_idx]
            ticker = "KXNCAAGAME-" + p_side + "-" + str(g["away_abbr"]) + str(g["home_abbr"])
            st.session_state["positions"][ticker] = {
                "ticker": ticker, "game": p_game, "side": p_side,
                "type": p_type, "contracts": p_contracts, "price": p_price,
                "game_id": g["id"], "home_abbr": g["home_abbr"], "away_abbr": g["away_abbr"]}
            st.rerun()

if st.session_state["positions"]:
    total_cost = 0
    total_payout = 0
    for ticker, pos in list(st.session_state["positions"].items()):
        cost = pos["contracts"] * pos["price"]
        payout = pos["contracts"] * 100
        total_cost += cost
        total_payout += payout
        live_score = ""
        for g in all_games:
            if g.get("home_abbr") == pos.get("home_abbr") and g.get("away_abbr") == pos.get("away_abbr"):
                if g["state"] == "in": live_score = " | LIVE " + str(g["away_score"]) + "-" + str(g["home_score"])
                elif g["state"] == "post": live_score = " | FINAL " + str(g["away_score"]) + "-" + str(g["home_score"])
                break
        pc1, pc2 = st.columns([4, 1])
        pc1.markdown(
            "**" + str(pos["game"]) + "** -- " + str(pos["side"]) + " " + str(pos["type"]) + live_score + "  \n" +
            str(pos["contracts"]) + "x @ " + str(pos["price"]) + "c = $" + "{:.2f}".format(cost / 100) + " -> $" + "{:.2f}".format(payout / 100))
        if pc2.button("Delete", key="del_" + str(ticker)):
            remove_position(ticker)
            st.rerun()
    st.markdown("**Portfolio:** $" + "{:.2f}".format(total_cost / 100) + " invested -> $" + "{:.2f}".format(total_payout / 100) + " max payout")
    if st.button("CLEAR ALL POSITIONS", key="clear_all"):
        st.session_state["positions"] = {}
        st.rerun()
else:
    st.info("No positions tracked. Add one above.")
st.divider()

# ── ALL GAMES TODAY ──────────────────────────────────────────────────
st.markdown("### ALL GAMES TODAY")
conf_groups = {}
for g in all_games:
    conf = g.get("conference", "") or "Other"
    conf_groups.setdefault(conf, []).append(g)

for conf_name in sorted(conf_groups.keys()):
    games_in_conf = conf_groups[conf_name]
    if conf_name and conf_name != "Other":
        st.markdown("**" + conf_name + "**")
    for g in games_in_conf:
        hr = "#" + str(g["home_rank"]) + " " if g.get("home_rank", 99) <= 25 else ""
        ar = "#" + str(g["away_rank"]) + " " if g.get("away_rank", 99) <= 25 else ""
        h_rec = " (" + g.get("home_record", "") + ")" if g.get("home_record") else ""
        a_rec = " (" + g.get("away_record", "") + ")" if g.get("away_record") else ""
        if g["state"] == "in":
            p = g.get("period", 0)
            hs = "H" + str(p) if p <= 2 else "OT" + str(p - 2)
            st.markdown("LIVE **" + ar + str(g["away_team"]) + a_rec + " " + str(g["away_score"]) + "** @ **" + hr + str(g["home_team"]) + h_rec + " " + str(g["home_score"]) + "** -- " + hs + " " + str(g["clock"]))
        elif g["state"] == "post":
            st.markdown("FINAL **" + ar + str(g["away_team"]) + a_rec + " " + str(g["away_score"]) + "** @ **" + hr + str(g["home_team"]) + h_rec + " " + str(g["home_score"]) + "**")
        else:
            spread = str(g.get("odds", {}).get("spread", ""))
            ou = str(g.get("odds", {}).get("overUnder", ""))
            bcast = str(g.get("broadcast", ""))
            parts = []
            if spread: parts.append("Spread: " + spread)
            if ou: parts.append("O/U: " + ou)
            if bcast: parts.append(bcast)
            st.markdown("SCHED **" + ar + str(g["away_team"]) + a_rec + "** @ **" + hr + str(g["home_team"]) + h_rec + "** -- " + " | ".join(parts))
st.divider()

# ── Footer ───────────────────────────────────────────────────────────
st.markdown(
    "<div style='text-align:center;color:#555;font-size:12px;padding:20px'>"
    "BigSnapshot NCAA Edge Finder v" + VERSION + " | 9-Factor Edge Model | "
    "ESPN BPI + Vegas + Home Court + Records + Rankings + B2B + Scoring + Injuries + 3PT | "
    "For entertainment and research only | Not financial advice | "
    "<a href='https://bigsnapshot.com' style='color:#888'>bigsnapshot.com</a>"
    "</div>", unsafe_allow_html=True)
