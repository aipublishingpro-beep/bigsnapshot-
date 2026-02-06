import streamlit as st
st.set_page_config(page_title="BigSnapshot NCAA Edge Finder", page_icon="🏀", layout="wide")

import requests, json, time, hashlib, base64, datetime as dt
from datetime import datetime, timedelta, timezone
from streamlit_autorefresh import st_autorefresh

# ── Auth ──────────────────────────────────────────────────────────────
try:
    from auth import create_kalshi_signature
except ImportError:
    def create_kalshi_signature(*a, **k):
        return "", ""

# ── GA4 Analytics ─────────────────────────────────────────────────────
GA4_MID = "G-XXXXXXXXXX"
GA4_SECRET = ""

def send_ga4(event_name, params=None):
    if not GA4_SECRET:
        return
    try:
        cid = hashlib.md5(st.session_state.get("session_id", "ncaa").encode()).hexdigest()
        requests.post(
            f"https://www.google-analytics.com/mp/collect?measurement_id={GA4_MID}&api_secret={GA4_SECRET}",
            json={"client_id": cid, "events": [{"name": event_name, "params": params or {}}]},
            timeout=2
        )
    except Exception:
        pass

# ── Autorefresh ───────────────────────────────────────────────────────
st_autorefresh(interval=30_000, limit=10000, key="ncaa_refresh")

# ── Config ────────────────────────────────────────────────────────────
VERSION = "1.0"
LEAGUE_AVG_TOTAL = 135
THRESHOLDS = [120.5, 125.5, 130.5, 135.5, 140.5, 145.5, 150.5, 155.5, 160.5]
HOME_COURT_ADV = 4.0
GAME_MINUTES = 40
HALVES = 2
HALF_MINUTES = 20

KALSHI_BASE = "https://trading-api.kalshi.com/trade-api/v2"
KALSHI_HEADERS = {"Content-Type": "application/json"}

# ── Session state ─────────────────────────────────────────────────────
if "session_id" not in st.session_state:
    st.session_state["session_id"] = hashlib.md5(str(time.time()).encode()).hexdigest()[:12]
if "positions" not in st.session_state:
    st.session_state["positions"] = {}
if "kalshi_token" not in st.session_state:
    st.session_state["kalshi_token"] = None

# ── Top 25 / Power Conference team colors (display only) ─────────────
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

# ── Kalshi auth ───────────────────────────────────────────────────────
def get_kalshi_headers():
    token = st.session_state.get("kalshi_token")
    if token:
        return {**KALSHI_HEADERS, "Authorization": f"Bearer {token}"}
    return KALSHI_HEADERS

def kalshi_login(email, password):
    try:
        r = requests.post(f"{KALSHI_BASE}/login", json={"email": email, "password": password}, timeout=10)
        if r.status_code == 200:
            st.session_state["kalshi_token"] = r.json().get("token")
            return True
    except Exception:
        pass
    return False

# ── Helper functions ──────────────────────────────────────────────────
def american_to_implied_prob(odds):
    if odds is None or odds == 0:
        return 0.0
    if odds > 0:
        return 100.0 / (odds + 100.0)
    return abs(odds) / (abs(odds) + 100.0)

def speak_play(play_text):
    if not play_text:
        return ""
    return play_text.strip()

def calc_minutes_elapsed(period, clock_str):
    try:
        if not clock_str:
            completed_halves = max(0, (period or 1) - 1)
            return completed_halves * HALF_MINUTES
        parts = clock_str.replace(" ", "").split(":")
        if len(parts) == 2:
            mins_left = int(parts[0])
            secs_left = int(parts[1])
        else:
            mins_left, secs_left = 0, 0
        elapsed_this_half = HALF_MINUTES - mins_left - (secs_left / 60.0)
        completed_halves = max(0, (period or 1) - 1)
        return (completed_halves * HALF_MINUTES) + max(0, elapsed_this_half)
    except Exception:
        return 0.0

def build_kalshi_game_link(ticker):
    if ticker:
        return f"https://kalshi.com/markets/{ticker}"
    return "https://kalshi.com"

# ── ESPN Fetch ────────────────────────────────────────────────────────
def fetch_espn_games():
    games = []
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard?dates={today}&limit=200"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return games
        data = r.json()
        for event in data.get("events", []):
            competition = event.get("competitions", [{}])[0]
            competitors = competition.get("competitors", [])
            if len(competitors) < 2:
                continue
            home = away = None
            for c in competitors:
                if c.get("homeAway") == "home":
                    home = c
                elif c.get("homeAway") == "away":
                    away = c
            if not home or not away:
                continue
            ht = home.get("team", {})
            at = away.get("team", {})
            status = event.get("status", {})
            state = status.get("type", {}).get("state", "pre")
            period = status.get("period", 0)
            clock = status.get("displayClock", "")
            conf_name = ""
            notes = event.get("notes", [])
            if notes:
                conf_name = notes[0].get("headline", "")
            game = {
                "id": str(event.get("id", "")),
                "name": event.get("name", ""),
                "shortName": event.get("shortName", ""),
                "state": state,
                "period": period,
                "clock": clock,
                "home_team": ht.get("displayName", ht.get("shortDisplayName", "")),
                "home_abbr": ht.get("abbreviation", ""),
                "home_score": int(home.get("score", 0) or 0),
                "home_id": str(ht.get("id", "")),
                "home_color": "#" + str(ht.get("color", "555555")),
                "home_logo": ht.get("logo", ""),
                "home_rank": home.get("curatedRank", {}).get("current", 99),
                "away_team": at.get("displayName", at.get("shortDisplayName", "")),
                "away_abbr": at.get("abbreviation", ""),
                "away_score": int(away.get("score", 0) or 0),
                "away_id": str(at.get("id", "")),
                "away_color": "#" + str(at.get("color", "555555")),
                "away_logo": at.get("logo", ""),
                "away_rank": away.get("curatedRank", {}).get("current", 99),
                "broadcast": "",
                "venue": competition.get("venue", {}).get("fullName", ""),
                "conference": conf_name,
                "odds": {},
                "minutes_elapsed": 0.0,
            }
            odds_list = competition.get("odds", [])
            if odds_list:
                o = odds_list[0]
                game["odds"] = {
                    "spread": o.get("spread", ""),
                    "overUnder": o.get("overUnder", ""),
                    "home_ml": o.get("homeTeamOdds", {}).get("moneyLine", ""),
                    "away_ml": o.get("awayTeamOdds", {}).get("moneyLine", ""),
                }
            bcasts = competition.get("broadcasts", [])
            if bcasts:
                names = []
                for b in bcasts:
                    for n in b.get("names", []):
                        names.append(n)
                game["broadcast"] = ", ".join(names)
            if state == "in":
                game["minutes_elapsed"] = calc_minutes_elapsed(period, clock)
            games.append(game)
    except Exception as e:
        st.error(f"ESPN fetch error: {e}")
    return games

# ── Kalshi ML Fetch ───────────────────────────────────────────────────
def fetch_kalshi_ml():
    markets = {}
    try:
        headers = get_kalshi_headers()
        url = f"{KALSHI_BASE}/markets?series_ticker=KXNCAAGAME&limit=200&status=open"
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            for m in r.json().get("markets", []):
                ticker = m.get("ticker", "")
                markets[ticker] = {
                    "ticker": ticker,
                    "title": m.get("title", ""),
                    "yes_price": m.get("yes_ask", 0) or m.get("last_price", 0),
                    "no_price": m.get("no_ask", 0),
                    "volume": m.get("volume", 0),
                    "open_interest": m.get("open_interest", 0),
                }
    except Exception:
        pass
    return markets

# ── Kalshi Spreads Fetch ──────────────────────────────────────────────
def fetch_kalshi_spreads():
    markets = {}
    try:
        headers = get_kalshi_headers()
        url = f"{KALSHI_BASE}/markets?series_ticker=KXNCAASPREAD&limit=200&status=open"
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            for m in r.json().get("markets", []):
                ticker = m.get("ticker", "")
                markets[ticker] = {
                    "ticker": ticker,
                    "title": m.get("title", ""),
                    "yes_price": m.get("yes_ask", 0) or m.get("last_price", 0),
                    "no_price": m.get("no_ask", 0),
                    "volume": m.get("volume", 0),
                }
    except Exception:
        pass
    return markets

# ── Injuries Fetch ────────────────────────────────────────────────────
def fetch_injuries():
    injuries = {}
    try:
        url = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/injuries"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            for team_block in r.json().get("items", []):
                team_name = team_block.get("team", {}).get("displayName", "Unknown")
                team_abbr = team_block.get("team", {}).get("abbreviation", "")
                team_injuries = []
                for inj in team_block.get("injuries", []):
                    athlete = inj.get("athlete", {})
                    team_injuries.append({
                        "name": athlete.get("displayName", "Unknown"),
                        "position": athlete.get("position", {}).get("abbreviation", ""),
                        "status": inj.get("status", ""),
                        "detail": inj.get("longComment", inj.get("shortComment", "")),
                    })
                if team_injuries:
                    injuries[team_abbr] = {"team": team_name, "players": team_injuries}
    except Exception:
        pass
    return injuries

# ── Yesterday Teams Fetch ────────────────────────────────────────────
def fetch_yesterday_teams():
    b2b = set()
    try:
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y%m%d")
        url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard?dates={yesterday}&limit=200"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            for event in r.json().get("events", []):
                for comp in event.get("competitions", []):
                    for c in comp.get("competitors", []):
                        abbr = c.get("team", {}).get("abbreviation", "")
                        if abbr:
                            b2b.add(abbr.upper())
    except Exception:
        pass
    return b2b

# ── Display Functions ────────────────────────────────────────────────

def render_scoreboard(g):
    state = g["state"]
    ha = g["home_abbr"]
    aa = g["away_abbr"]
    hc = g.get("home_color", get_team_color(ha))
    ac = g.get("away_color", get_team_color(aa))
    hr = "#" + str(g['home_rank']) + " " if g.get("home_rank", 99) <= 25 else ""
    ar = "#" + str(g['away_rank']) + " " if g.get("away_rank", 99) <= 25 else ""
    if state == "in":
        period = g.get("period", 0)
        clock = g.get("clock", "")
        half_label = "H" + str(period) if period <= 2 else "OT" + str(period - 2)
        status_html = "<span style='color:#e74c3c;font-weight:700'>LIVE " + half_label + " " + str(clock) + "</span>"
    elif state == "post":
        status_html = "<span style='color:#888'>FINAL</span>"
    else:
        status_html = "<span style='color:#aaa'>" + str(g.get('broadcast', 'TBD')) + "</span>"
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
        "<div style='font-size:11px;color:" + ac + "'>" + ar + str(g['away_team']) + "</div>"
        "<div style='font-size:22px;font-weight:700;color:white'>" + str(g['away_score']) + "</div>"
        "</div>"
        "<div style='text-align:center;flex:1'>" + status_html + "</div>"
        "<div style='text-align:right;flex:1'>"
        "<div style='font-size:11px;color:" + hc + "'>" + hr + str(g['home_team']) + "</div>"
        "<div style='font-size:22px;font-weight:700;color:white'>" + str(g['home_score']) + "</div>"
        "</div></div>" + venue_html + "</div>"
    )
    st.markdown(html, unsafe_allow_html=True)

def get_play_badge(play_type):
    badges = {
        "three": ("3PT", "#e74c3c"), "dunk": ("DUNK", "#e67e22"), "steal": ("STL", "#2ecc71"),
        "block": ("BLK", "#9b59b6"), "turnover": ("TO", "#e74c3c"), "foul": ("FOUL", "#f39c12"),
        "free throw": ("FT", "#3498db"), "rebound": ("REB", "#1abc9c"),
    }
    for key, (lbl, color) in badges.items():
        if key in (play_type or "").lower():
            return lbl, color
    return "PLAY", "#555"

def infer_possession(plays, home_abbr, away_abbr, home_name, away_name):
    if not plays:
        return None
    for p in reversed(plays[-10:]):
        tid = str(p.get("team_id", ""))
        text = (p.get("text", "") or "").lower()
        ptype = (p.get("type", "") or "").lower()
        if "steal" in ptype or "steal" in text:
            if tid:
                return tid
        if "turnover" in ptype or "turnover" in text:
            continue
        if "made" in text or "make" in ptype:
            if tid == home_abbr or home_abbr.lower() in text or home_name.lower() in text:
                return "away"
            elif tid == away_abbr or away_abbr.lower() in text or away_name.lower() in text:
                return "home"
        if "rebound" in ptype or "rebound" in text:
            if tid == home_abbr or home_abbr.lower() in text or home_name.lower() in text:
                return "home"
            elif tid == away_abbr or away_abbr.lower() in text or away_name.lower() in text:
                return "away"
        if "foul" in ptype or "foul" in text:
            continue
        if tid:
            return tid
    return None

def resolve_possession_label(poss, home_abbr, away_abbr, home_id="", away_id=""):
    if poss is None:
        return None, None
    p = str(poss).lower()
    if p == "home" or p == home_id.lower() or home_abbr.lower() in p:
        return home_abbr, "home"
    if p == "away" or p == away_id.lower() or away_abbr.lower() in p:
        return away_abbr, "away"
    return None, None

def render_court(home_abbr, away_abbr, score_home=0, score_away=0, possession_abbr=None, possession_side=None):
    ball_x = 375 if possession_side == "home" else 125 if possession_side == "away" else -100
    ball_vis = "visible" if possession_side in ("home", "away") else "hidden"
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
    if possession_abbr:
        st.markdown("<div style='text-align:center;padding:2px;color:#f1c40f;font-size:13px;font-weight:700'>" + str(possession_abbr) + " BALL</div>", unsafe_allow_html=True)

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

def get_kalshi_game_link(date_str, away_abbr, home_abbr):
    d = str(date_str or datetime.now(timezone.utc).strftime("%Y%m%d"))
    aa = str(away_abbr or "").upper()
    ha = str(home_abbr or "").upper()
    return "https://kalshi.com/markets/kxncaagame/college-basketball-game/kxncaagame-" + d + aa + ha

def calc_projection(home_score, away_score, minutes_elapsed):
    total = home_score + away_score
    if minutes_elapsed <= 0:
        return LEAGUE_AVG_TOTAL
    current_pace = total / minutes_elapsed
    league_pace = LEAGUE_AVG_TOTAL / GAME_MINUTES
    pct_done = minutes_elapsed / GAME_MINUTES
    if pct_done < 0.15:
        blend = 0.3
    elif pct_done < 0.5:
        blend = 0.5 + (pct_done - 0.15) * 1.0
    else:
        blend = 0.85 + (pct_done - 0.5) * 0.3
    blend = min(blend, 0.98)
    blended_pace = (current_pace * blend) + (league_pace * (1 - blend))
    return round(blended_pace * GAME_MINUTES, 1)

def get_pace_label(pts_per_min):
    if pts_per_min >= 4.0: return "VERY HIGH"
    if pts_per_min >= 3.6: return "HIGH"
    if pts_per_min >= 3.2: return "AVERAGE"
    if pts_per_min >= 2.8: return "LOW"
    return "VERY LOW"

def calc_pregame_edge(game, b2b_teams):
    edges = []
    ha = game.get("home_abbr", "").upper()
    aa = game.get("away_abbr", "").upper()
    edges.append("Home court: " + str(game['home_team']) + " +" + str(HOME_COURT_ADV))
    if game.get("home_rank", 99) <= 25:
        edges.append(str(game['home_team']) + " ranked #" + str(game['home_rank']))
    if game.get("away_rank", 99) <= 25:
        edges.append(str(game['away_team']) + " ranked #" + str(game['away_rank']))
    if ha in b2b_teams:
        edges.append(str(game['home_team']) + " on B2B")
    if aa in b2b_teams:
        edges.append(str(game['away_team']) + " on B2B")
    return edges

def fetch_plays(game_id):
    plays = []
    try:
        url = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/summary?event=" + str(game_id)
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            for item in data.get("plays", []):
                plays.append({
                    "text": item.get("text", ""),
                    "period": item.get("period", {}).get("number", 0),
                    "clock": item.get("clock", {}).get("displayValue", ""),
                    "score": item.get("scoreValue", 0),
                    "team_id": str(item.get("team", {}).get("id", "")),
                    "type": item.get("type", {}).get("text", ""),
                })
    except Exception:
        pass
    return plays

def remove_position(ticker):
    if ticker in st.session_state["positions"]:
        del st.session_state["positions"][ticker]

# ══════════════════════════════════════════════════════════════════════
# MAIN PAGE LAYOUT
# ══════════════════════════════════════════════════════════════════════
st.markdown("## BIGSNAPSHOT NCAA EDGE FINDER")
st.caption("v" + VERSION + " | " + datetime.now(timezone.utc).strftime("%A %b %d, %Y | %H:%M UTC") + " | NCAA Men's Basketball")

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
    if g["state"] != "pre":
        continue
    espn_ml_home = g.get("odds", {}).get("home_ml")
    if not espn_ml_home:
        continue
    try:
        espn_ml_home = float(espn_ml_home)
    except (TypeError, ValueError):
        continue
    espn_prob = american_to_implied_prob(espn_ml_home)
    if espn_prob <= 0:
        continue
    ha = g.get("home_abbr", "").upper()
    aa = g.get("away_abbr", "").upper()
    for ticker, mk in kalshi_ml.items():
        t_upper = ticker.upper()
        if ha in t_upper and aa in t_upper:
            yp = mk.get("yes_price", 0) or 0
            kalshi_prob = yp / 100.0 if yp > 1 else yp
            diff = abs(espn_prob - kalshi_prob)
            if diff >= 0.05:
                mispricings.append({
                    "game": g["shortName"], "espn_prob": espn_prob,
                    "kalshi_prob": kalshi_prob, "diff": diff,
                    "ticker": ticker, "home": g["home_team"],
                })
            break

if mispricings:
    st.markdown("### VEGAS vs KALSHI MISPRICING ALERTS")
    for mp in sorted(mispricings, key=lambda x: -x["diff"]):
        diff_pct = mp["diff"] * 100
        st.markdown(
            "**" + str(mp['game']) + "** -- Vegas: " + "{:.0%}".format(mp['espn_prob']) +
            " -> Kalshi: " + "{:.0%}".format(mp['kalshi_prob']) +
            " (**" + "{:.1f}".format(diff_pct) + "% gap**) | `" + str(mp['ticker']) + "`"
        )
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

        exp_label = str(g['away_abbr']) + " " + str(g['away_score']) + " @ " + str(g['home_abbr']) + " " + str(g['home_score']) + " -- " + half_str + " " + str(g['clock'])
        with st.expander(exp_label, expanded=True):
            render_scoreboard(g)
            plays = fetch_plays(g["id"])

            poss_abbr, poss_side = None, None
            if plays:
                raw_poss = infer_possession(plays, g["home_abbr"], g["away_abbr"], g["home_team"], g["away_team"])
                poss_abbr, poss_side = resolve_possession_label(raw_poss, g["home_abbr"], g["away_abbr"], g.get("home_id", ""), g.get("away_id", ""))

            lc, rc = st.columns(2)
            with lc:
                render_court(g["home_abbr"], g["away_abbr"], score_home=g["home_score"], score_away=g["away_score"], possession_abbr=poss_abbr, possession_side=poss_side)
            with rc:
                st.markdown("**Pace:** " + "{:.2f}".format(pace_per_min) + " pts/min " + pace_label)
                st.markdown("**Projected Total:** " + str(projection))
                st.markdown("**Game Progress:** " + "{:.0f}".format(pct_done) + "% (" + "{:.1f}".format(mins) + "/" + str(GAME_MINUTES) + " min)")
                lead = g["home_score"] - g["away_score"]
                if lead > 0:
                    st.markdown("**Lead:** " + str(g['home_team']) + " +" + str(lead))
                elif lead < 0:
                    st.markdown("**Lead:** " + str(g['away_team']) + " +" + str(abs(lead)))
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
                    except (ValueError, TypeError):
                        pass

            if plays:
                st.markdown("**Recent Plays:**")
                for p in plays[-6:]:
                    icon = get_play_icon(p.get("type", ""))
                    hp = "H" + str(p['period']) if p.get("period", 0) <= 2 else "OT" + str(p['period'] - 2)
                    st.markdown("<span style='color:#888;font-size:12px'>" + hp + " " + str(p.get('clock', '')) + " " + icon + " " + str(p.get('text', '')) + "</span>", unsafe_allow_html=True)

            today_str = datetime.now(timezone.utc).strftime("%Y%m%d")
            link = get_kalshi_game_link(today_str, g["away_abbr"], g["home_abbr"])
            st.markdown("[Trade on Kalshi](" + link + ")")

    st.divider()

# ── CUSHION SCANNER (Totals) ─────────────────────────────────────────
if live_games:
    st.markdown("### CUSHION SCANNER -- Totals")
    cs_games = [str(g['away_abbr']) + " @ " + str(g['home_abbr']) for g in live_games]
    cs_sel = st.selectbox("Game", ["ALL GAMES"] + cs_games, key="cs_game")
    cs_c1, cs_c2 = st.columns(2)
    cs_min = cs_c1.slider("Min minutes elapsed", 0, 40, 5, key="cs_min")
    cs_side = cs_c2.selectbox("Side", ["Both", "Over", "Under"], key="cs_side")

    for g in live_games:
        label = str(g['away_abbr']) + " @ " + str(g['home_abbr'])
        if cs_sel != "ALL GAMES" and cs_sel != label:
            continue
        mins = g.get("minutes_elapsed", 0)
        if mins < cs_min:
            continue
        total = g["home_score"] + g["away_score"]
        proj = calc_projection(g["home_score"], g["away_score"], mins)
        remaining = GAME_MINUTES - mins

        for thresh in THRESHOLDS:
            needed_over = thresh - total
            if cs_side in ["Both", "Over"] and needed_over > 0 and remaining > 0:
                rate_needed = needed_over / remaining
                pace_now = total / max(mins, 0.5)
                cushion = pace_now - rate_needed
                if cushion > 1.0:
                    safety = "FORTRESS"
                elif cushion > 0.4:
                    safety = "SAFE"
                elif cushion > 0.0:
                    safety = "TIGHT"
                else:
                    safety = "RISKY"
                if remaining <= 6:
                    safety += " SHARK MODE"
                st.markdown(
                    "**" + label + "** OVER " + str(thresh) + " -- Need " + "{:.0f}".format(needed_over) +
                    " in " + "{:.0f}".format(remaining) + "min (" + "{:.2f}".format(rate_needed) +
                    "/min) | Pace " + "{:.2f}".format(pace_now) + "/min | **" + safety + "**"
                )
            if cs_side in ["Both", "Under"] and remaining > 0:
                projected_final = total + (remaining * (total / max(mins, 0.5)))
                under_cushion = thresh - projected_final
                if under_cushion > 10:
                    u_safety = "FORTRESS"
                elif under_cushion > 4:
                    u_safety = "SAFE"
                elif under_cushion > 0:
                    u_safety = "TIGHT"
                else:
                    u_safety = "RISKY"
                if projected_final < thresh:
                    if remaining <= 6:
                        u_safety += " SHARK MODE"
                    st.markdown(
                        "**" + label + "** UNDER " + str(thresh) + " -- Proj " +
                        "{:.0f}".format(projected_final) + " vs Line " + str(thresh) + " | **" + u_safety + "**"
                    )
    st.divider()

# ── PACE SCANNER ─────────────────────────────────────────────────────
if live_games:
    st.markdown("### PACE SCANNER")
    for g in live_games:
        mins = g.get("minutes_elapsed", 0)
        if mins < 2:
            continue
        total = g["home_score"] + g["away_score"]
        pace = total / max(mins, 0.5)
        proj = calc_projection(g["home_score"], g["away_score"], mins)
        label = get_pace_label(pace)
        period = g.get("period", 0)
        half_str = "H" + str(period) if period <= 2 else "OT" + str(period - 2)
        pct = mins / GAME_MINUTES * 100

        col1, col2, col3 = st.columns([2, 1, 1])
        col1.markdown("**" + str(g['away_abbr']) + " " + str(g['away_score']) + " @ " + str(g['home_abbr']) + " " + str(g['home_score']) + "** | " + half_str + " " + str(g['clock']))
        col2.markdown("Pace: **" + "{:.2f}".format(pace) + "**/min " + label)
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
            except (ValueError, TypeError):
                pass
    st.divider()

# ── PRE-GAME ALIGNMENT ──────────────────────────────────────────────
if scheduled_games:
    st.markdown("### PRE-GAME ALIGNMENT")

    if st.button("ADD ALL PRE-GAME PICKS", key="add_all_pre"):
        for g in scheduled_games:
            ticker = "KXNCAAGAME-" + str(g['away_abbr']) + str(g['home_abbr'])
            if ticker not in st.session_state["positions"]:
                edges = calc_pregame_edge(g, b2b_teams)
                st.session_state["positions"][ticker] = {
                    "ticker": ticker, "game": g["shortName"],
                    "side": "HOME" if g.get("home_rank", 99) <= g.get("away_rank", 99) else "AWAY",
                    "type": "ML", "contracts": 1, "price": 50,
                    "edges": edges, "game_id": g["id"],
                    "home_abbr": g["home_abbr"], "away_abbr": g["away_abbr"],
                }
        st.rerun()

    for idx, g in enumerate(scheduled_games):
        edges = calc_pregame_edge(g, b2b_teams)
        hr = "#" + str(g['home_rank']) + " " if g.get("home_rank", 99) <= 25 else ""
        ar = "#" + str(g['away_rank']) + " " if g.get("away_rank", 99) <= 25 else ""
        spread = g.get("odds", {}).get("spread", "N/A")
        ou = g.get("odds", {}).get("overUnder", "N/A")

        with st.container():
            lc, rc = st.columns([3, 1])
            with lc:
                st.markdown("**" + ar + str(g['away_team']) + " @ " + hr + str(g['home_team']) + "**")
                st.markdown("Spread: " + str(spread) + " | O/U: " + str(ou) + " | " + str(g.get('broadcast', '')))
                for e in edges:
                    st.markdown("  " + e)
            with rc:
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
        if abbr.upper() not in today_abbrs:
            continue
        shown = True
        st.markdown("**" + str(data['team']) + "**")
        for p in data["players"]:
            s = (p["status"] or "").lower()
            if "out" in s:
                status_marker = "[OUT]"
            elif "day" in s or "doubt" in s:
                status_marker = "[DTD]"
            else:
                status_marker = "[OK]"
            st.markdown("  " + status_marker + " " + str(p['name']) + " (" + str(p['position']) + ") -- " + str(p['status']) + ": " + str(p.get('detail', '')))
    if not shown:
        st.info("No injuries reported for today's teams.")
    st.divider()

# ── POSITION TRACKER ─────────────────────────────────────────────────
st.markdown("### POSITION TRACKER")

with st.expander("ADD NEW POSITION"):
    game_opts = [str(g['away_abbr']) + " @ " + str(g['home_abbr']) for g in all_games]
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
            ticker = "KXNCAAGAME-" + p_side + "-" + str(g['away_abbr']) + str(g['home_abbr'])
            st.session_state["positions"][ticker] = {
                "ticker": ticker, "game": p_game, "side": p_side,
                "type": p_type, "contracts": p_contracts, "price": p_price,
                "game_id": g["id"], "home_abbr": g["home_abbr"], "away_abbr": g["away_abbr"],
            }
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
                if g["state"] == "in":
                    live_score = " | LIVE " + str(g['away_score']) + "-" + str(g['home_score'])
                elif g["state"] == "post":
                    live_score = " | FINAL " + str(g['away_score']) + "-" + str(g['home_score'])
                break

        pc1, pc2, pc3 = st.columns([3, 1, 1])
        pc1.markdown(
            "**" + str(pos['game']) + "** -- " + str(pos['side']) + " " + str(pos['type']) + live_score + "  \n" +
            str(pos['contracts']) + "x @ " + str(pos['price']) + "c = $" + "{:.2f}".format(cost / 100) + " -> $" + "{:.2f}".format(payout / 100)
        )
        today_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        link = get_kalshi_game_link(today_str, pos.get("away_abbr", ""), pos.get("home_abbr", ""))
        pc2.markdown("[Kalshi](" + link + ")")
        if pc3.button("Delete", key="del_" + str(ticker)):
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
        hr = "#" + str(g['home_rank']) + " " if g.get("home_rank", 99) <= 25 else ""
        ar = "#" + str(g['away_rank']) + " " if g.get("away_rank", 99) <= 25 else ""
        if g["state"] == "in":
            period = g.get("period", 0)
            half_str = "H" + str(period) if period <= 2 else "OT" + str(period - 2)
            st.markdown(
                "LIVE **" + ar + str(g['away_team']) + " " + str(g['away_score']) + "** @ **" +
                hr + str(g['home_team']) + " " + str(g['home_score']) + "** -- " + half_str + " " + str(g['clock'])
            )
        elif g["state"] == "post":
            st.markdown(
                "FINAL **" + ar + str(g['away_team']) + " " + str(g['away_score']) + "** @ **" +
                hr + str(g['home_team']) + " " + str(g['home_score']) + "**"
            )
        else:
            spread = str(g.get("odds", {}).get("spread", ""))
            ou = str(g.get("odds", {}).get("overUnder", ""))
            bcast = str(g.get("broadcast", ""))
            parts = []
            if spread:
                parts.append("Spread: " + spread)
            if ou:
                parts.append("O/U: " + ou)
            if bcast:
                parts.append(bcast)
            extras = " | ".join(parts)
            st.markdown("SCHED **" + ar + str(g['away_team']) + "** @ **" + hr + str(g['home_team']) + "** -- " + extras)

st.divider()

# ── Footer ───────────────────────────────────────────────────────────
st.markdown(
    "<div style='text-align:center;color:#555;font-size:12px;padding:20px'>"
    "BigSnapshot NCAA Edge Finder v" + VERSION + " | For entertainment and research only | Not financial advice | "
    "<a href='https://bigsnapshot.com' style='color:#888'>bigsnapshot.com</a>"
    "</div>",
    unsafe_allow_html=True
)
