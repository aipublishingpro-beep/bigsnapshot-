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
# We do NOT hardcode all 350+ teams. ESPN API gives us names/abbreviations.
# This dict is cosmetic — for colored badges on marquee teams.
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
    """Clean play-by-play text for display."""
    if not play_text:
        return ""
    return play_text.strip()

def calc_minutes_elapsed(period, clock_str):
    """NCAA: 2 halves of 20 min each. Clock counts down from 20:00."""
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
    """Build Kalshi market link from ticker."""
    if ticker:
        return f"https://kalshi.com/markets/{ticker}"
    return "https://kalshi.com"

# ── ESPN Fetch ────────────────────────────────────────────────────────
def fetch_espn_games():
    """Fetch today's NCAA men's basketball games from ESPN API."""
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
            # Conference info
            home_conf = ht.get("conferenceId", "")
            away_conf = at.get("conferenceId", "")
            conf_name = ""
            notes = event.get("notes", [])
            if notes:
                conf_name = notes[0].get("headline", "")
            game = {
                "id": event.get("id", ""),
                "name": event.get("name", ""),
                "shortName": event.get("shortName", ""),
                "state": state,
                "period": period,
                "clock": clock,
                "home_team": ht.get("displayName", ht.get("shortDisplayName", "")),
                "home_abbr": ht.get("abbreviation", ""),
                "home_score": int(home.get("score", 0) or 0),
                "home_id": ht.get("id", ""),
                "home_color": f"#{ht.get('color', '555555')}",
                "home_logo": ht.get("logo", ""),
                "home_rank": home.get("curatedRank", {}).get("current", 99),
                "away_team": at.get("displayName", at.get("shortDisplayName", "")),
                "away_abbr": at.get("abbreviation", ""),
                "away_score": int(away.get("score", 0) or 0),
                "away_id": at.get("id", ""),
                "away_color": f"#{at.get('color', '555555')}",
                "away_logo": at.get("logo", ""),
                "away_rank": away.get("curatedRank", {}).get("current", 99),
                "broadcast": "",
                "venue": competition.get("venue", {}).get("fullName", ""),
                "conference": conf_name,
                "odds": {},
                "minutes_elapsed": 0.0,
            }
            # Parse odds if available
            odds_list = competition.get("odds", [])
            if odds_list:
                o = odds_list[0]
                game["odds"] = {
                    "spread": o.get("spread", ""),
                    "overUnder": o.get("overUnder", ""),
                    "home_ml": o.get("homeTeamOdds", {}).get("moneyLine", ""),
                    "away_ml": o.get("awayTeamOdds", {}).get("moneyLine", ""),
                }
            # Broadcasts
            bcasts = competition.get("broadcasts", [])
            if bcasts:
                names = []
                for b in bcasts:
                    for n in b.get("names", []):
                        names.append(n)
                game["broadcast"] = ", ".join(names)
            # Minutes elapsed for live games
            if state == "in":
                game["minutes_elapsed"] = calc_minutes_elapsed(period, clock)
            games.append(game)
    except Exception as e:
        st.error(f"ESPN fetch error: {e}")
    return games

# ── Kalshi ML Fetch ───────────────────────────────────────────────────
def fetch_kalshi_ml():
    """Fetch NCAA moneyline markets from Kalshi."""
    markets = {}
    try:
        headers = get_kalshi_headers()
        url = f"{KALSHI_BASE}/markets?series_ticker=KXNCAAGAME&limit=200&status=open"
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            for m in r.json().get("markets", []):
                ticker = m.get("ticker", "")
                title = m.get("title", "")
                yes_price = m.get("yes_ask", 0) or m.get("last_price", 0)
                no_price = m.get("no_ask", 0)
                markets[ticker] = {
                    "ticker": ticker,
                    "title": title,
                    "yes_price": yes_price,
                    "no_price": no_price,
                    "volume": m.get("volume", 0),
                    "open_interest": m.get("open_interest", 0),
                }
    except Exception:
        pass
    return markets

# ── Kalshi Spreads Fetch ──────────────────────────────────────────────
def fetch_kalshi_spreads():
    """Fetch NCAA spread markets from Kalshi."""
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
    """Fetch NCAA basketball injuries from ESPN."""
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
                    injuries[team_abbr] = {
                        "team": team_name,
                        "players": team_injuries,
                    }
    except Exception:
        pass
    return injuries

# ── Yesterday Teams Fetch ────────────────────────────────────────────
def fetch_yesterday_teams():
    """Fetch which teams played yesterday (back-to-back detection)."""
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

# ── PART 2: Display Functions + Live Edge Monitor ────────────────────

def render_scoreboard(g):
    """Render HTML scoreboard card for a game."""
    state = g["state"]
    ha = g["home_abbr"]
    aa = g["away_abbr"]
    hc = g.get("home_color", get_team_color(ha))
    ac = g.get("away_color", get_team_color(aa))
    hr = f"#{g['home_rank']} " if g.get("home_rank", 99) <= 25 else ""
    ar = f"#{g['away_rank']} " if g.get("away_rank", 99) <= 25 else ""
    if state == "in":
        period = g.get("period", 0)
        clock = g.get("clock", "")
        half_label = f"H{period}" if period <= 2 else f"OT{period-2}"
        status_html = f"<span style='color:#e74c3c;font-weight:700'>🔴 {half_label} {clock}</span>"
    elif state == "post":
        status_html = "<span style='color:#888'>FINAL</span>"
    else:
        status_html = f"<span style='color:#aaa'>{g.get('broadcast','TBD')}</span>"
    conf = g.get("conference", "")
    conf_html = f"<div style='font-size:10px;color:#888;margin-bottom:2px'>{conf}</div>" if conf else ""
    venue = g.get("venue", "")
    venue_html = f"<div style='font-size:10px;color:#777'>{venue}</div>" if venue else ""
    html = f"""
    <div style='background:#1a1a2e;border-radius:10px;padding:12px;margin:6px 0;border-left:4px solid {ac};border-right:4px solid {hc}'>
        {conf_html}
        <div style='display:flex;justify-content:space-between;align-items:center'>
            <div style='text-align:left;flex:1'>
                <div style='font-size:11px;color:{ac}'>{ar}{g['away_team']}</div>
                <div style='font-size:22px;font-weight:700;color:white'>{g['away_score']}</div>
            </div>
            <div style='text-align:center;flex:1'>
                {status_html}
            </div>
            <div style='text-align:right;flex:1'>
                <div style='font-size:11px;color:{hc}'>{hr}{g['home_team']}</div>
                <div style='font-size:22px;font-weight:700;color:white'>{g['home_score']}</div>
            </div>
        </div>
        {venue_html}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def get_play_badge(play_type):
    badges = {
        "three": ("🎯", "#e74c3c"), "dunk": ("🔨", "#e67e22"), "steal": ("🤏", "#2ecc71"),
        "block": ("🚫", "#9b59b6"), "turnover": ("💀", "#e74c3c"), "foul": ("⚠️", "#f39c12"),
        "free throw": ("🎁", "#3498db"), "rebound": ("🏀", "#1abc9c"),
    }
    for key, (emoji, color) in badges.items():
        if key in (play_type or "").lower():
            return emoji, color
    return "▶️", "#555"

def infer_possession(plays, home_abbr, away_abbr, home_name, away_name):
    """Infer possession from last play-by-play text using team_id and text matching."""
    if not plays:
        return None
    # Walk backwards through recent plays to find possession
    for p in reversed(plays[-10:]):
        tid = p.get("team_id", "")
        text = (p.get("text", "") or "").lower()
        ptype = (p.get("type", "") or "").lower()
        # Turnovers/steals flip possession
        if "steal" in ptype or "steal" in text:
            # The team that stole it has the ball
            if tid:
                return tid
        if "turnover" in ptype or "turnover" in text:
            # Opposite team now has ball — skip, let next play resolve
            continue
        # Made/missed shots, free throws, rebounds — team_id from ESPN is who acted
        # After a made basket, the OTHER team gets the ball
        if "made" in text or "make" in ptype:
            # Opponent inbounds
            if tid == home_abbr or home_abbr.lower() in text or home_name.lower() in text:
                return "away"
            elif tid == away_abbr or away_abbr.lower() in text or away_name.lower() in text:
                return "home"
        # Rebound = that team has ball
        if "rebound" in ptype or "rebound" in text:
            if tid == home_abbr or home_abbr.lower() in text or home_name.lower() in text:
                return "home"
            elif tid == away_abbr or away_abbr.lower() in text or away_name.lower() in text:
                return "away"
        # Foul — fouled team usually shoots or gets ball
        if "foul" in ptype or "foul" in text:
            continue
        # Generic: if team_id matches, they last touched it
        if tid:
            return tid
    return None

def resolve_possession_label(poss, home_abbr, away_abbr, home_id="", away_id=""):
    """Convert raw possession inference to display label."""
    if poss is None:
        return None, None
    p = str(poss).lower()
    if p == "home" or p == home_id or home_abbr.lower() in p:
        return home_abbr, "home"
    if p == "away" or p == away_id or away_abbr.lower() in p:
        return away_abbr, "away"
    return None, None

def render_court(home_abbr, away_abbr, last_play="", score_home=0, score_away=0, possession_abbr=None, possession_side=None):
    """Render generic basketball court SVG with possession indicator."""
    # Ball indicator positions
    ball_x = 375 if possession_side == "home" else 125 if possession_side == "away" else -100
    ball_vis = "visible" if possession_side in ("home", "away") else "hidden"
    svg = f"""
    <svg viewBox="0 0 500 280" style="width:100%;max-width:500px;background:#1a1a2e;border-radius:8px">
        <rect x="25" y="15" width="450" height="230" fill="none" stroke="#444" stroke-width="2" rx="5"/>
        <line x1="250" y1="15" x2="250" y2="245" stroke="#444" stroke-width="1.5"/>
        <circle cx="250" cy="130" r="35" fill="none" stroke="#444" stroke-width="1.5"/>
        <rect x="25" y="70" width="80" height="120" fill="none" stroke="#444" stroke-width="1"/>
        <rect x="395" y="70" width="80" height="120" fill="none" stroke="#444" stroke-width="1"/>
        <text x="125" y="135" text-anchor="middle" fill="#aaa" font-size="16" font-weight="700">{away_abbr}</text>
        <text x="375" y="135" text-anchor="middle" fill="#aaa" font-size="16" font-weight="700">{home_abbr}</text>
        <text x="125" y="155" text-anchor="middle" fill="white" font-size="20" font-weight="700">{score_away}</text>
        <text x="375" y="155" text-anchor="middle" fill="white" font-size="20" font-weight="700">{score_home}</text>
        <text x="{ball_x}" y="270" text-anchor="middle" fill="#f1c40f" font-size="13" font-weight="700" visibility="{ball_vis}">🏀 BALL</text>
    </svg>
    """
    st.markdown(svg, unsafe_allow_html=True)
    if possession_abbr:
        st.markdown(f"<div style='text-align:center;padding:2px;color:#f1c40f;font-size:13px;font-weight:700'>🏀 {possession_abbr} BALL</div>", unsafe_allow_html=True)
    if last_play:
        emoji, color = get_play_badge(last_play)
        st.markdown(f"<div style='text-align:center;padding:4px;color:{color};font-size:13px'>{emoji} {last_play}</div>", unsafe_allow_html=True)

def get_play_icon(text):
    t = (text or "").lower()
    if "three" in t or "3pt" in t: return "🎯"
    if "dunk" in t: return "🔨"
    if "steal" in t: return "🤏"
    if "block" in t: return "🚫"
    if "turnover" in t: return "💀"
    if "foul" in t: return "⚠️"
    if "free throw" in t: return "🎁"
    if "rebound" in t: return "🏀"
    return "▶️"

def get_kalshi_game_link(date_str, away_abbr, home_abbr):
    """Build Kalshi NCAA game URL."""
    d = date_str or datetime.now(timezone.utc).strftime("%Y%m%d")
    aa = (away_abbr or "").upper()
    ha = (home_abbr or "").upper()
    return f"https://kalshi.com/markets/kxncaagame/college-basketball-game/kxncaagame-{d}{aa}{ha}"

def calc_projection(home_score, away_score, minutes_elapsed):
    """Blended pace projection for NCAA (40-min game)."""
    total = home_score + away_score
    if minutes_elapsed <= 0:
        return LEAGUE_AVG_TOTAL
    current_pace = total / minutes_elapsed
    league_pace = LEAGUE_AVG_TOTAL / GAME_MINUTES
    pct_done = minutes_elapsed / GAME_MINUTES
    # Blend: weight current pace more as game progresses
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
    """NCAA pace labels — college pace ~2.8-4.0 pts/min."""
    if pts_per_min >= 4.0: return "🔥 VERY HIGH"
    if pts_per_min >= 3.6: return "⬆️ HIGH"
    if pts_per_min >= 3.2: return "➡️ AVERAGE"
    if pts_per_min >= 2.8: return "⬇️ LOW"
    return "🧊 VERY LOW"

def calc_pregame_edge(game, b2b_teams):
    """Simplified pre-game edge for NCAA. Home court = +4."""
    edges = []
    ha = game.get("home_abbr", "").upper()
    aa = game.get("away_abbr", "").upper()
    # Home court advantage
    edges.append(f"🏠 Home court: {game['home_team']} +{HOME_COURT_ADV}")
    # Ranked team check
    if game.get("home_rank", 99) <= 25:
        edges.append(f"📊 {game['home_team']} ranked #{game['home_rank']}")
    if game.get("away_rank", 99) <= 25:
        edges.append(f"📊 {game['away_team']} ranked #{game['away_rank']}")
    # Back-to-back
    if ha in b2b_teams:
        edges.append(f"⚠️ {game['home_team']} on B2B")
    if aa in b2b_teams:
        edges.append(f"⚠️ {game['away_team']} on B2B")
    return edges

def fetch_plays(game_id):
    """Fetch play-by-play from ESPN NCAA endpoint."""
    plays = []
    try:
        url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/summary?event={game_id}"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            for item in data.get("plays", []):
                plays.append({
                    "text": item.get("text", ""),
                    "period": item.get("period", {}).get("number", 0),
                    "clock": item.get("clock", {}).get("displayValue", ""),
                    "score": item.get("scoreValue", 0),
                    "team_id": item.get("team", {}).get("id", ""),
                    "type": item.get("type", {}).get("text", ""),
                })
    except Exception:
        pass
    return plays

def remove_position(ticker):
    if ticker in st.session_state["positions"]:
        del st.session_state["positions"][ticker]

# ── MAIN PAGE LAYOUT ─────────────────────────────────────────────────
st.markdown("## 🏀 BIGSNAPSHOT NCAA EDGE FINDER")
st.caption(f"v{VERSION} · {datetime.now(timezone.utc).strftime('%A %b %d, %Y · %H:%M UTC')} · NCAA Men's Basketball")

# Fetch all data
all_games = fetch_espn_games()
kalshi_ml = fetch_kalshi_ml()
kalshi_spreads = fetch_kalshi_spreads()
injuries = fetch_injuries()
b2b_teams = fetch_yesterday_teams()

live_games = [g for g in all_games if g["state"] == "in"]
scheduled_games = [g for g in all_games if g["state"] == "pre"]
final_games = [g for g in all_games if g["state"] == "post"]

# Metrics
c1, c2, c3, c4 = st.columns(4)
c1.metric("Today's Games", len(all_games))
c2.metric("🔴 Live", len(live_games))
c3.metric("🕐 Scheduled", len(scheduled_games))
c4.metric("✅ Final", len(final_games))

st.divider()

# ── VEGAS vs KALSHI MISPRICING ALERT ─────────────────────────────────
mispricings = []
for g in all_games:
    if g["state"] != "pre":
        continue
    espn_ml_home = g.get("odds", {}).get("home_ml")
    if not espn_ml_home:
        continue
    espn_prob = american_to_implied_prob(espn_ml_home)
    if espn_prob <= 0:
        continue
    # Try to match to Kalshi ML market
    ha = g.get("home_abbr", "").upper()
    aa = g.get("away_abbr", "").upper()
    for ticker, mk in kalshi_ml.items():
        t_upper = ticker.upper()
        if ha in t_upper and aa in t_upper:
            kalshi_prob = mk.get("yes_price", 0) / 100.0 if mk.get("yes_price", 0) > 1 else mk.get("yes_price", 0)
            diff = abs(espn_prob - kalshi_prob)
            if diff >= 0.05:
                mispricings.append({
                    "game": g["shortName"],
                    "espn_prob": espn_prob,
                    "kalshi_prob": kalshi_prob,
                    "diff": diff,
                    "ticker": ticker,
                    "home": g["home_team"],
                })
            break

if mispricings:
    st.markdown("### ⚡ VEGAS vs KALSHI MISPRICING ALERTS")
    for mp in sorted(mispricings, key=lambda x: -x["diff"]):
        diff_pct = mp["diff"] * 100
        st.markdown(
            f"**{mp['game']}** — Vegas: {mp['espn_prob']:.0%} → Kalshi: {mp['kalshi_prob']:.0%} "
            f"(**{diff_pct:.1f}% gap**) · `{mp['ticker']}`"
        )
    st.divider()

# ── LIVE EDGE MONITOR ────────────────────────────────────────────────
if live_games:
    st.markdown("### 🔴 LIVE EDGE MONITOR")
    for g in live_games:
        mins = g.get("minutes_elapsed", 0)
        total = g["home_score"] + g["away_score"]
        pace_per_min = total / max(mins, 0.5)
        projection = calc_projection(g["home_score"], g["away_score"], mins)
        pace_label = get_pace_label(pace_per_min)
        pct_done = mins / GAME_MINUTES * 100

        period = g.get("period", 0)
        half_str = f"H{period}" if period <= 2 else f"OT{period - 2}"

        with st.expander(f"{'🔴'} {g['away_abbr']} {g['away_score']} @ {g['home_abbr']} {g['home_score']} — {half_str} {g['clock']}", expanded=True):
            render_scoreboard(g)

            # Fetch plays early for possession inference
            plays = fetch_plays(g["id"])

            # Possession inference from plays
            poss_abbr, poss_side = None, None
            if plays:
                raw_poss = infer_possession(plays, g["home_abbr"], g["away_abbr"], g["home_team"], g["away_team"])
                poss_abbr, poss_side = resolve_possession_label(raw_poss, g["home_abbr"], g["away_abbr"], g.get("home_id",""), g.get("away_id",""))

            lc, rc = st.columns(2)
            with lc:
                render_court(g["home_abbr"], g["away_abbr"], score_home=g["home_score"], score_away=g["away_score"], possession_abbr=poss_abbr, possession_side=poss_side)
            with rc:
                st.markdown(f"**Pace:** {pace_per_min:.2f} pts/min {pace_label}")
                st.markdown(f"**Projected Total:** {projection}")
                st.markdown(f"**Game Progress:** {pct_done:.0f}% ({mins:.1f}/{GAME_MINUTES} min)")
                lead = g["home_score"] - g["away_score"]
                if lead > 0:
                    st.markdown(f"**Lead:** {g['home_team']} +{lead}")
                elif lead < 0:
                    st.markdown(f"**Lead:** {g['away_team']} +{abs(lead)}")
                else:
                    st.markdown("**Lead:** TIE")

                # Totals edge check
                espn_ou = g.get("odds", {}).get("overUnder")
                if espn_ou:
                    try:
                        ou_val = float(espn_ou)
                        diff = projection - ou_val
                        if abs(diff) >= 5:
                            direction = "OVER ⬆️" if diff > 0 else "UNDER ⬇️"
                            st.markdown(f"**Totals Edge:** Proj {projection} vs Line {ou_val} → **{direction} ({diff:+.1f})**")
                    except ValueError:
                        pass

            # Play-by-play
            if plays:
                st.markdown("**Recent Plays:**")
                for p in plays[-6:]:
                    icon = get_play_icon(p.get("type", ""))
                    half_p = f"H{p['period']}" if p.get("period", 0) <= 2 else f"OT{p['period']-2}"
                    st.markdown(f"<span style='color:#888;font-size:12px'>{half_p} {p.get('clock','')} {icon} {p.get('text','')}</span>", unsafe_allow_html=True)

            # Kalshi link
            today_str = datetime.now(timezone.utc).strftime("%Y%m%d")
            link = get_kalshi_game_link(today_str, g["away_abbr"], g["home_abbr"])
            st.link_button("📈 Trade on Kalshi", link)

    st.divider()

# ── PART 3: Scanners, Trackers, Footer ───────────────────────────────

# ── 🎯 CUSHION SCANNER (Totals) ─────────────────────────────────────
if live_games:
    st.markdown("### 🎯 CUSHION SCANNER — Totals")
    cs_games = [f"{g['away_abbr']} @ {g['home_abbr']}" for g in live_games]
    cs_sel = st.selectbox("Game", ["ALL GAMES"] + cs_games, key="cs_game")
    cs_c1, cs_c2 = st.columns(2)
    cs_min = cs_c1.slider("Min minutes elapsed", 0, 40, 5, key="cs_min")
    cs_side = cs_c2.selectbox("Side", ["Both", "Over", "Under"], key="cs_side")

    for g in live_games:
        label = f"{g['away_abbr']} @ {g['home_abbr']}"
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
            needed_under = total - thresh
            # Over cushion
            if cs_side in ["Both", "Over"] and needed_over > 0 and remaining > 0:
                rate_needed = needed_over / remaining
                pace_now = total / max(mins, 0.5)
                cushion = pace_now - rate_needed
                if cushion > 1.0:
                    safety = "🏰 FORTRESS"
                elif cushion > 0.4:
                    safety = "✅ SAFE"
                elif cushion > 0.0:
                    safety = "⚠️ TIGHT"
                else:
                    safety = "🔴 RISKY"
                if remaining <= 6:
                    safety += " 🦈 SHARK MODE"
                st.markdown(
                    f"**{label}** OVER {thresh} — Need {needed_over:.0f} in {remaining:.0f}min "
                    f"({rate_needed:.2f}/min) · Pace {pace_now:.2f}/min · **{safety}**"
                )
            # Under cushion
            if cs_side in ["Both", "Under"] and remaining > 0:
                max_pts = remaining * 4.0  # college max ~4 pts/min burst
                projected_final = total + (remaining * (total / max(mins, 0.5)))
                under_cushion = thresh - projected_final
                if under_cushion > 10:
                    u_safety = "🏰 FORTRESS"
                elif under_cushion > 4:
                    u_safety = "✅ SAFE"
                elif under_cushion > 0:
                    u_safety = "⚠️ TIGHT"
                else:
                    u_safety = "🔴 RISKY"
                if projected_final < thresh and cs_side in ["Both", "Under"]:
                    if remaining <= 6:
                        u_safety += " 🦈 SHARK MODE"
                    st.markdown(
                        f"**{label}** UNDER {thresh} — Proj {projected_final:.0f} vs Line {thresh} · **{u_safety}**"
                    )
    st.divider()

# ── 📈 PACE SCANNER ─────────────────────────────────────────────────
if live_games:
    st.markdown("### 📈 PACE SCANNER")
    for g in live_games:
        mins = g.get("minutes_elapsed", 0)
        if mins < 2:
            continue
        total = g["home_score"] + g["away_score"]
        pace = total / max(mins, 0.5)
        proj = calc_projection(g["home_score"], g["away_score"], mins)
        label = get_pace_label(pace)
        period = g.get("period", 0)
        half_str = f"H{period}" if period <= 2 else f"OT{period - 2}"
        pct = mins / GAME_MINUTES * 100

        col1, col2, col3 = st.columns([2, 1, 1])
        col1.markdown(f"**{g['away_abbr']} {g['away_score']} @ {g['home_abbr']} {g['home_score']}** · {half_str} {g['clock']}")
        col2.markdown(f"Pace: **{pace:.2f}**/min {label}")
        col3.markdown(f"Proj: **{proj}** · {pct:.0f}% done")

        # Progress bar
        st.progress(min(pct / 100, 1.0))

        espn_ou = g.get("odds", {}).get("overUnder")
        if espn_ou:
            try:
                ou_val = float(espn_ou)
                diff = proj - ou_val
                if abs(diff) >= 5:
                    arrow = "⬆️ OVER" if diff > 0 else "⬇️ UNDER"
                    st.markdown(f"→ Proj {proj} vs Line {ou_val}: **{arrow} ({diff:+.1f})**")
            except ValueError:
                pass
    st.divider()

# ── 🎯 PRE-GAME ALIGNMENT ───────────────────────────────────────────
if scheduled_games:
    st.markdown("### 🎯 PRE-GAME ALIGNMENT")

    # Add all button
    if st.button("➕ ADD ALL PRE-GAME PICKS", key="add_all_pre"):
        for g in scheduled_games:
            ticker = f"KXNCAAGAME-{g['away_abbr']}{g['home_abbr']}"
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

    for g in scheduled_games:
        edges = calc_pregame_edge(g, b2b_teams)
        hr = f"#{g['home_rank']} " if g.get("home_rank", 99) <= 25 else ""
        ar = f"#{g['away_rank']} " if g.get("away_rank", 99) <= 25 else ""
        spread = g.get("odds", {}).get("spread", "N/A")
        ou = g.get("odds", {}).get("overUnder", "N/A")

        with st.container():
            lc, rc = st.columns([3, 1])
            with lc:
                st.markdown(f"**{ar}{g['away_team']} @ {hr}{g['home_team']}**")
                st.markdown(f"Spread: {spread} · O/U: {ou} · {g.get('broadcast', '')}")
                for e in edges:
                    st.markdown(f"  {e}")
            with rc:
                today_str = datetime.now(timezone.utc).strftime("%Y%m%d")
                link = get_kalshi_game_link(today_str, g["away_abbr"], g["home_abbr"])
                st.link_button("📈 Kalshi", link, key=f"pre_{g['id']}")
            st.markdown("---")
    st.divider()

# ── 🏥 INJURY REPORT ────────────────────────────────────────────────
if injuries:
    st.markdown("### 🏥 INJURY REPORT")
    today_abbrs = set()
    for g in all_games:
        today_abbrs.add(g["home_abbr"].upper())
        today_abbrs.add(g["away_abbr"].upper())

    shown = False
    for abbr, data in injuries.items():
        if abbr.upper() not in today_abbrs:
            continue
        shown = True
        st.markdown(f"**{data['team']}**")
        for p in data["players"]:
            status_emoji = "🔴" if "out" in (p["status"] or "").lower() else "🟡" if "day" in (p["status"] or "").lower() or "doubt" in (p["status"] or "").lower() else "🟢"
            st.markdown(f"  {status_emoji} {p['name']} ({p['position']}) — {p['status']}: {p.get('detail','')}")
    if not shown:
        st.info("No injuries reported for today's teams.")
    st.divider()

# ── 📊 POSITION TRACKER ─────────────────────────────────────────────
st.markdown("### 📊 POSITION TRACKER")

with st.expander("➕ ADD NEW POSITION"):
    game_opts = [f"{g['away_abbr']} @ {g['home_abbr']}" for g in all_games]
    if game_opts:
        p_game = st.selectbox("Game", game_opts, key="pt_game")
        p_c1, p_c2 = st.columns(2)
        p_type = p_c1.selectbox("Bet Type", ["ML", "Totals", "Spread"], key="pt_type")
        p_side = p_c2.selectbox("Side", ["HOME", "AWAY", "OVER", "UNDER"], key="pt_side")
        p_c3, p_c4 = st.columns(2)
        p_contracts = p_c3.number_input("Contracts", 1, 500, 10, key="pt_contracts")
        p_price = p_c4.number_input("Price (¢)", 1, 99, 50, key="pt_price")
        if st.button("ADD POSITION", key="pt_add"):
            idx = game_opts.index(p_game)
            g = all_games[idx]
            ticker = f"KXNCAAGAME-{p_side}-{g['away_abbr']}{g['home_abbr']}"
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
        # Find matching live game
        live_score = ""
        for g in all_games:
            if g.get("home_abbr") == pos.get("home_abbr") and g.get("away_abbr") == pos.get("away_abbr"):
                if g["state"] == "in":
                    live_score = f" · 🔴 {g['away_score']}-{g['home_score']}"
                elif g["state"] == "post":
                    live_score = f" · ✅ {g['away_score']}-{g['home_score']} FINAL"
                break

        pc1, pc2, pc3 = st.columns([3, 1, 1])
        pc1.markdown(
            f"**{pos['game']}** — {pos['side']} {pos['type']}{live_score}  \n"
            f"{pos['contracts']}x @ {pos['price']}¢ = ${cost/100:.2f} → ${payout/100:.2f}"
        )
        today_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        link = get_kalshi_game_link(today_str, pos.get("away_abbr", ""), pos.get("home_abbr", ""))
        pc2.link_button("📈", link, key=f"pos_{ticker}")
        if pc3.button("🗑️", key=f"del_{ticker}"):
            remove_position(ticker)
            st.rerun()

    st.markdown(f"**Portfolio:** ${total_cost/100:.2f} invested → ${total_payout/100:.2f} max payout")
    if st.button("🗑️ CLEAR ALL POSITIONS", key="clear_all"):
        st.session_state["positions"] = {}
        st.rerun()
else:
    st.info("No positions tracked. Add one above.")

st.divider()

# ── 📋 ALL GAMES TODAY ──────────────────────────────────────────────
st.markdown("### 📋 ALL GAMES TODAY")

# Group by conference
conf_groups = {}
for g in all_games:
    conf = g.get("conference", "") or "Other"
    conf_groups.setdefault(conf, []).append(g)

for conf_name in sorted(conf_groups.keys()):
    games_in_conf = conf_groups[conf_name]
    if conf_name and conf_name != "Other":
        st.markdown(f"**{conf_name}**")
    for g in games_in_conf:
        hr = f"#{g['home_rank']} " if g.get("home_rank", 99) <= 25 else ""
        ar = f"#{g['away_rank']} " if g.get("away_rank", 99) <= 25 else ""
        if g["state"] == "in":
            period = g.get("period", 0)
            half_str = f"H{period}" if period <= 2 else f"OT{period - 2}"
            st.markdown(
                f"🔴 **{ar}{g['away_team']} {g['away_score']}** @ **{hr}{g['home_team']} {g['home_score']}** — {half_str} {g['clock']}"
            )
        elif g["state"] == "post":
            st.markdown(
                f"✅ **{ar}{g['away_team']} {g['away_score']}** @ **{hr}{g['home_team']} {g['home_score']}** — FINAL"
            )
        else:
            spread = g.get("odds", {}).get("spread", "")
            ou = g.get("odds", {}).get("overUnder", "")
            bcast = g.get("broadcast", "")
            extras = " · ".join(filter(None, [f"Spread: {spread}" if spread else "", f"O/U: {ou}" if ou else "", bcast]))
            st.markdown(f"🕐 **{ar}{g['away_team']}** @ **{hr}{g['home_team']}** — {extras}")

st.divider()

# ── Footer ───────────────────────────────────────────────────────────
st.markdown(
    f"<div style='text-align:center;color:#555;font-size:12px;padding:20px'>"
    f"🏀 BigSnapshot NCAA Edge Finder v{VERSION} · For entertainment & research only · Not financial advice · "
    f"<a href='https://bigsnapshot.com' style='color:#888'>bigsnapshot.com</a>"
    f"</div>",
    unsafe_allow_html=True
)
