import streamlit as st
from streamlit_autorefresh import st_autorefresh
import streamlit.components.v1 as components

st.set_page_config(page_title="BigSnapshot NCAA Edge Finder", page_icon="🎓", layout="wide")

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

send_ga4_event("BigSnapshot NCAA Edge Finder", "/NCAA")

import requests
from datetime import datetime, timedelta
import pytz

eastern = pytz.timezone("US/Eastern")
now = datetime.now(eastern)

VERSION = "13.0"
LEAGUE_AVG_TOTAL = 145
THRESHOLDS = [120.5, 125.5, 130.5, 135.5, 140.5, 145.5, 150.5, 155.5, 160.5, 165.5, 170.5]

if 'ncaa_positions' not in st.session_state:
    st.session_state.ncaa_positions = []

POWER_CONFERENCES = {"SEC", "Big Ten", "Big 12", "ACC", "Big East"}
HIGH_MAJOR = {"American Athletic", "Mountain West", "Atlantic 10", "West Coast", "Missouri Valley"}

TEAM_COLORS = {
    "DUKE": "#003087", "UNC": "#7BAFD4", "KANSAS": "#0051BA", "KENTUCKY": "#0033A0",
    "UCLA": "#2D68C4", "GONZ": "#002967", "ARIZ": "#CC0033", "PURDUE": "#CEB888",
    "TENN": "#FF8200", "CONN": "#000E2F", "HOUSTON": "#C8102E", "TEXAS": "#BF5700",
    "BAYLOR": "#154734", "AUBURN": "#0C2340", "MICH": "#00274C", "MSU": "#18453B",
    "NOVA": "#00205B", "CREIGH": "#005CA9", "MARQ": "#003366", "SDSU": "#A6192E",
    "FAU": "#003366", "MIAMI": "#F47321", "IND": "#990000", "IOWA": "#FFCD00",
    "ILLINOIS": "#13294B", "OHIOST": "#BB0000", "WISC": "#C5050C", "ORE": "#154733",
    "ALA": "#9E1B32", "ARK": "#9D2235", "LSU": "#461D7C", "MISS": "#14213D",
    "OKLA": "#841617", "TEXTECH": "#CC0000", "TCU": "#4D1979", "OKST": "#FF7300",
    "FLOR": "#0021A5", "NCST": "#CC0000", "WAKE": "#9E7E38", "CLEM": "#F56600",
    "PITT": "#003594", "LOU": "#AD0000", "VTECH": "#630031", "SYRA": "#F76900",
    "ND": "#0C2340", "BC": "#98002E", "STAN": "#8C1515", "WASH": "#4B2E83",
    "USC": "#990000", "COLO": "#CFB87C", "UTAH": "#CC0000", "PSU": "#041E42"
}

def escape_html(text):
    if not text: return ""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def american_to_implied_prob(odds):
    """FIXED: handles big negative ML correctly (-5000, -8000 etc)"""
    if odds is None or odds == 0: return 0.5
    if odds > 0: return 100 / (odds + 100)
    else: return abs(odds) / (abs(odds) + 100)

def build_kalshi_ncaa_url(away_abbrev, home_abbrev):
    """Build URL — tries to match actual Kalshi ticker first, falls back to constructed URL"""
    kalshi_data = st.session_state.get('ncaa_kalshi_data', {})
    a_lower = away_abbrev.lower()
    h_lower = home_abbrev.lower()
    for ticker, m in kalshi_data.items():
        title = (m.get("title", "") + " " + m.get("subtitle", "")).lower()
        if a_lower in title and h_lower in title:
            return f"https://kalshi.com/markets/kxncaambgame/mens-college-basketball-mens-game/{ticker.lower()}"
        if a_lower in ticker.lower() and h_lower in ticker.lower():
            return f"https://kalshi.com/markets/kxncaambgame/mens-college-basketball-mens-game/{ticker.lower()}"
    date_str = datetime.now(eastern).strftime("%y%b%d").lower()
    a = away_abbrev.lower().replace(" ", "").replace(".", "").replace("'", "")[:4]
    h = home_abbrev.lower().replace(" ", "").replace(".", "").replace("'", "")[:4]
    ticker = f"kxncaambgame-{date_str}{a}{h}"
    return f"https://kalshi.com/markets/kxncaambgame/mens-college-basketball-mens-game/{ticker}"

def get_conference_tier(conf_name):
    if not conf_name: return 3
    if any(p in str(conf_name) for p in POWER_CONFERENCES): return 1
    if any(h in str(conf_name) for h in HIGH_MAJOR): return 2
    return 3

def get_minutes_played_ncaa(period, clock, status_type):
    if status_type == "STATUS_FINAL": return 40
    if status_type == "STATUS_HALFTIME": return 20
    if period == 0: return 0
    try:
        parts = str(clock).split(':')
        mins = int(parts[0])
        secs = int(float(parts[1])) if len(parts) > 1 else 0
        time_left = mins + secs / 60
        if period == 1: return 20 - time_left
        elif period == 2: return 20 + (20 - time_left)
        else: return 40 + (period - 2) * 5 + (5 - time_left)
    except:
        return (period - 1) * 20 if period <= 2 else 40 + (period - 2) * 5

@st.cache_data(ttl=30)
def fetch_espn_ncaa_games():
    today = datetime.now(eastern).strftime('%Y%m%d')
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard?dates={today}&limit=100"
    try:
        resp = requests.get(url, timeout=15)
        data = resp.json()
        games = []
        for event in data.get("events", []):
            comp = event.get("competitions", [{}])[0]
            competitors = comp.get("competitors", [])
            if len(competitors) < 2: continue
            home_team, away_team, home_score, away_score = None, None, 0, 0
            home_abbrev, away_abbrev = "", ""
            home_rank, away_rank = 0, 0
            home_record, away_record = "", ""
            home_conf, away_conf = "", ""
            for c in competitors:
                team_data = c.get("team", {})
                name = team_data.get("displayName", team_data.get("name", ""))
                abbrev = team_data.get("abbreviation", name[:4].upper())
                score = int(c.get("score", 0) or 0)
                rank_obj = c.get("curatedRank", {})
                rank = rank_obj.get("current", 0) if rank_obj else 0
                if rank and rank > 25: rank = 0
                records = c.get("records", [])
                record = records[0].get("summary", "") if records else ""
                conf = ""
                if records and len(records) > 1:
                    conf = records[1].get("summary", "")
                if c.get("homeAway") == "home":
                    home_team, home_score, home_abbrev = name, score, abbrev
                    home_rank, home_record = rank, record
                    home_conf = team_data.get("conferenceId", "")
                else:
                    away_team, away_score, away_abbrev = name, score, abbrev
                    away_rank, away_record = rank, record
                    away_conf = team_data.get("conferenceId", "")
            status = event.get("status", {}).get("type", {}).get("name", "STATUS_SCHEDULED")
            period = event.get("status", {}).get("period", 0)
            clock = event.get("status", {}).get("displayClock", "")
            game_id = event.get("id", "")
            minutes_played = get_minutes_played_ncaa(period, clock, status)
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
            games.append({
                "away": away_team, "home": home_team,
                "away_abbrev": away_abbrev, "home_abbrev": home_abbrev,
                "away_score": away_score, "home_score": home_score,
                "away_record": away_record, "home_record": home_record,
                "away_rank": away_rank, "home_rank": home_rank,
                "away_conf": away_conf, "home_conf": home_conf,
                "status": status, "period": period, "clock": clock,
                "minutes_played": minutes_played,
                "total_score": home_score + away_score,
                "game_id": game_id, "vegas_odds": vegas_odds,
                "game_time": game_time_str, "game_datetime": game_datetime_str
            })
        return games
    except Exception as e:
        st.error("ESPN NCAA fetch error: " + str(e))
        return []

def fetch_kalshi_ncaa_ml(force_refresh=False):
    """NO CACHE — fetches fresh every run or on force refresh"""
    if not force_refresh and 'ncaa_kalshi_data' in st.session_state and 'ncaa_kalshi_time' in st.session_state:
        age = (datetime.now(eastern) - st.session_state.ncaa_kalshi_time).total_seconds()
        if age < 15:
            return st.session_state.ncaa_kalshi_data
    url = "https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXNCAAMBGAME&status=open&limit=200"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        markets = {}
        for m in data.get("markets", []):
            ticker = m.get("ticker", "")
            title = m.get("title", "")
            subtitle = m.get("subtitle", "")
            yes_bid = m.get("yes_bid", 0) or 0
            yes_ask = m.get("yes_ask", 0) or 0
            last_price = m.get("last_price", 0) or 0
            yes_price = yes_ask if yes_ask > 0 else (last_price if last_price > 0 else (yes_bid if yes_bid > 0 else 0))
            markets[ticker] = {
                "ticker": ticker, "title": title, "subtitle": subtitle,
                "yes_bid": yes_bid, "yes_ask": yes_ask, "yes_price": yes_price,
                "last_price": last_price
            }
        st.session_state.ncaa_kalshi_data = markets
        st.session_state.ncaa_kalshi_time = datetime.now(eastern)
        return markets
    except:
        return st.session_state.get('ncaa_kalshi_data', {})

def find_kalshi_price_for_game(kalshi_data, away_abbrev, home_abbrev, team_abbrev):
    """Search Kalshi markets for a specific game and team's YES price"""
    a_lower = away_abbrev.lower()
    h_lower = home_abbrev.lower()
    t_lower = team_abbrev.lower()
    for ticker, m in kalshi_data.items():
        search_text = (ticker + " " + m.get("title", "") + " " + m.get("subtitle", "")).lower()
        if (a_lower in search_text or a_lower[:3] in search_text) and (h_lower in search_text or h_lower[:3] in search_text):
            title_lower = m.get("title", "").lower()
            if t_lower in title_lower or t_lower[:3] in title_lower:
                return m.get("yes_price", 0)
            else:
                yes_p = m.get("yes_price", 0)
                if yes_p > 0: return 100 - yes_p
    return 0

@st.cache_data(ttl=300)
def fetch_ncaa_rankings():
    url = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/rankings"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        rankings = {}
        for ranking in data.get("rankings", []):
            if ranking.get("type", "") == "ap":
                for entry in ranking.get("ranks", []):
                    team = entry.get("team", {})
                    abbrev = team.get("abbreviation", "")
                    rank = entry.get("current", 0)
                    if abbrev: rankings[abbrev] = rank
                break
        return rankings
    except:
        return {}

@st.cache_data(ttl=30)
def fetch_ncaa_plays(game_id):
    if not game_id: return []
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/summary?event={game_id}"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        plays = []
        for p in data.get("plays", [])[-15:]:
            plays.append({
                "text": p.get("text", ""),
                "period": p.get("period", {}).get("number", 0),
                "clock": p.get("clock", {}).get("displayValue", ""),
                "score_value": p.get("scoreValue", 0),
                "play_type": p.get("type", {}).get("text", "")
            })
        return plays[-10:]
    except:
        return []

def speak_play(text):
    clean_text = text.replace("'", "").replace('"', '').replace('\n', ' ')[:100]
    js = f'''<script>if(!window.lastSpoken||window.lastSpoken!=="{clean_text}"){{window.lastSpoken="{clean_text}";var u=new SpeechSynthesisUtterance("{clean_text}");u.rate=1.1;window.speechSynthesis.speak(u);}}</script>'''
    components.html(js, height=0)
    # ═══════════════════════════════════════════════
# PART 2 — RENDERING + HELPERS (paste after Part 1)
# ═══════════════════════════════════════════════

def render_scoreboard(away, home, away_abbrev, home_abbrev, away_score, home_score, period, clock, away_rank=0, home_rank=0, away_record="", home_record=""):
    away_color = TEAM_COLORS.get(away_abbrev, "#666")
    home_color = TEAM_COLORS.get(home_abbrev, "#666")
    period_text = f"H{period}" if period <= 2 else f"OT{period-2}"
    rank_away = f"#{away_rank} " if away_rank > 0 else ""
    rank_home = f"#{home_rank} " if home_rank > 0 else ""
    return f'''<div style="background:#0f172a;border-radius:12px;padding:20px;margin-bottom:8px">
    <div style="text-align:center;color:#ffd700;font-weight:bold;font-size:22px;margin-bottom:16px">{period_text} - {clock}</div>
    <table style="width:100%;border-collapse:collapse;color:#fff">
    <tr style="border-bottom:2px solid #333">
        <td style="padding:16px;text-align:left;width:70%"><span style="color:{away_color};font-weight:bold;font-size:28px">{rank_away}{away_abbrev}</span><span style="color:#666;font-size:14px;margin-left:12px">{away_record}</span></td>
        <td style="padding:16px;text-align:right;font-weight:bold;font-size:52px;color:#fff">{away_score}</td>
    </tr>
    <tr>
        <td style="padding:16px;text-align:left;width:70%"><span style="color:{home_color};font-weight:bold;font-size:28px">{rank_home}{home_abbrev}</span><span style="color:#666;font-size:14px;margin-left:12px">{home_record}</span></td>
        <td style="padding:16px;text-align:right;font-weight:bold;font-size:52px;color:#fff">{home_score}</td>
    </tr>
    </table></div>'''

def get_play_badge(last_play):
    if not last_play: return ""
    play_text = (last_play.get("text", "") or "").lower()
    score_value = last_play.get("score_value", 0)
    if score_value == 3 or ("three point" in play_text and "makes" in play_text):
        return '<rect x="175" y="25" width="150" height="30" fill="#22c55e" rx="6"/><text x="250" y="46" fill="#fff" font-size="14" font-weight="bold" text-anchor="middle">3PT MADE!</text>'
    elif score_value == 2 or ("makes" in play_text and any(w in play_text for w in ["layup", "dunk", "shot", "jumper", "hook"])):
        return '<rect x="175" y="25" width="150" height="30" fill="#22c55e" rx="6"/><text x="250" y="46" fill="#fff" font-size="14" font-weight="bold" text-anchor="middle">BUCKET!</text>'
    elif score_value == 1 or ("makes" in play_text and "free throw" in play_text):
        return '<rect x="175" y="25" width="150" height="30" fill="#22c55e" rx="6"/><text x="250" y="46" fill="#fff" font-size="14" font-weight="bold" text-anchor="middle">FT MADE</text>'
    elif "misses" in play_text:
        if "three point" in play_text:
            return '<rect x="175" y="25" width="150" height="30" fill="#ef4444" rx="6"/><text x="250" y="46" fill="#fff" font-size="14" font-weight="bold" text-anchor="middle">3PT MISS</text>'
        elif "free throw" in play_text:
            return '<rect x="175" y="25" width="150" height="30" fill="#ef4444" rx="6"/><text x="250" y="46" fill="#fff" font-size="14" font-weight="bold" text-anchor="middle">FT MISS</text>'
        else:
            return '<rect x="175" y="25" width="150" height="30" fill="#ef4444" rx="6"/><text x="250" y="46" fill="#fff" font-size="14" font-weight="bold" text-anchor="middle">MISSED SHOT</text>'
    elif "block" in play_text:
        return '<rect x="175" y="25" width="150" height="30" fill="#f97316" rx="6"/><text x="250" y="46" fill="#fff" font-size="14" font-weight="bold" text-anchor="middle">BLOCKED!</text>'
    elif "turnover" in play_text or "steal" in play_text:
        return '<rect x="175" y="25" width="150" height="30" fill="#f97316" rx="6"/><text x="250" y="46" fill="#fff" font-size="14" font-weight="bold" text-anchor="middle">TURNOVER</text>'
    elif "offensive rebound" in play_text:
        return '<rect x="175" y="25" width="150" height="30" fill="#3b82f6" rx="6"/><text x="250" y="46" fill="#fff" font-size="14" font-weight="bold" text-anchor="middle">OFF REBOUND</text>'
    elif "rebound" in play_text:
        return '<rect x="175" y="25" width="150" height="30" fill="#3b82f6" rx="6"/><text x="250" y="46" fill="#fff" font-size="14" font-weight="bold" text-anchor="middle">REBOUND</text>'
    elif "foul" in play_text:
        return '<rect x="175" y="25" width="150" height="30" fill="#eab308" rx="6"/><text x="250" y="46" fill="#000" font-size="14" font-weight="bold" text-anchor="middle">FOUL</text>'
    elif "timeout" in play_text:
        return '<rect x="175" y="25" width="150" height="30" fill="#a855f7" rx="6"/><text x="250" y="46" fill="#fff" font-size="14" font-weight="bold" text-anchor="middle">TIMEOUT</text>'
    return ""

def render_ncaa_court(away_abbrev, home_abbrev, away_score, home_score, period, clock, last_play=None):
    away_color = TEAM_COLORS.get(away_abbrev, "#666")
    home_color = TEAM_COLORS.get(home_abbrev, "#666")
    period_text = f"H{period}" if period <= 2 else f"OT{period-2}"
    play_badge = get_play_badge(last_play)
    return f'''<div style="background:#1a1a2e;border-radius:12px;padding:10px;"><svg viewBox="0 0 500 280" style="width:100%;max-width:500px;"><rect x="20" y="20" width="460" height="200" fill="#2d4a22" stroke="#fff" stroke-width="2" rx="8"/><circle cx="250" cy="120" r="35" fill="none" stroke="#fff" stroke-width="2"/><circle cx="250" cy="120" r="4" fill="#fff"/><line x1="250" y1="20" x2="250" y2="220" stroke="#fff" stroke-width="2"/><path d="M 20 50 Q 100 120 20 190" fill="none" stroke="#fff" stroke-width="2"/><rect x="20" y="70" width="70" height="100" fill="none" stroke="#fff" stroke-width="2"/><circle cx="90" cy="120" r="25" fill="none" stroke="#fff" stroke-width="2"/><circle cx="35" cy="120" r="8" fill="none" stroke="#ff6b35" stroke-width="3"/><path d="M 480 50 Q 400 120 480 190" fill="none" stroke="#fff" stroke-width="2"/><rect x="410" y="70" width="70" height="100" fill="none" stroke="#fff" stroke-width="2"/><circle cx="410" cy="120" r="25" fill="none" stroke="#fff" stroke-width="2"/><circle cx="465" cy="120" r="8" fill="none" stroke="#ff6b35" stroke-width="3"/>{play_badge}<rect x="40" y="228" width="90" height="48" fill="{away_color}" rx="6"/><text x="85" y="250" fill="#fff" font-size="14" font-weight="bold" text-anchor="middle">{away_abbrev}</text><text x="85" y="270" fill="#fff" font-size="18" font-weight="bold" text-anchor="middle">{away_score}</text><rect x="370" y="228" width="90" height="48" fill="{home_color}" rx="6"/><text x="415" y="250" fill="#fff" font-size="14" font-weight="bold" text-anchor="middle">{home_abbrev}</text><text x="415" y="270" fill="#fff" font-size="18" font-weight="bold" text-anchor="middle">{home_score}</text><text x="250" y="258" fill="#fff" font-size="16" font-weight="bold" text-anchor="middle">{period_text} {clock}</text></svg></div>'''

def get_play_icon(play_type, score_value):
    play_lower = play_type.lower() if play_type else ""
    if score_value > 0 or "made" in play_lower: return "🏀", "#22c55e"
    elif "miss" in play_lower or "block" in play_lower: return "❌", "#ef4444"
    elif "rebound" in play_lower: return "📥", "#3b82f6"
    elif "turnover" in play_lower or "steal" in play_lower: return "🔄", "#f97316"
    elif "foul" in play_lower: return "🚨", "#eab308"
    elif "timeout" in play_lower: return "⏸️", "#a855f7"
    return "•", "#888"

def calc_projection(total_score, minutes_played):
    if minutes_played >= 8:
        pace = total_score / minutes_played
        weight = min(1.0, (minutes_played - 8) / 16)
        blended_pace = (pace * weight) + ((LEAGUE_AVG_TOTAL / 40) * (1 - weight))
        return max(100, min(200, round(blended_pace * 40)))
    elif minutes_played >= 6:
        pace = total_score / minutes_played
        return max(100, min(200, round(((pace * 0.3) + ((LEAGUE_AVG_TOTAL / 40) * 0.7)) * 40)))
    return LEAGUE_AVG_TOTAL

def get_pace_label(pace):
    if pace < 3.2: return "🐢 SLOW", "#22c55e"
    elif pace < 3.6: return "⚖️ AVG", "#eab308"
    elif pace < 4.0: return "🔥 FAST", "#f97316"
    return "💥 SHOOTOUT", "#ef4444"

def calc_pregame_edge_ncaa(home_rank, away_rank, home_conf_tier, away_conf_tier, home_record, away_record):
    score = 50
    score += 3
    if home_rank > 0 and away_rank == 0: score += 8
    elif away_rank > 0 and home_rank == 0: score -= 8
    elif home_rank > 0 and away_rank > 0:
        diff = away_rank - home_rank
        score += min(10, max(-10, diff // 2))
    if home_conf_tier < away_conf_tier: score += 4
    elif away_conf_tier < home_conf_tier: score -= 4
    try:
        hw = int(home_record.split("-")[0])
        hl = int(home_record.split("-")[1])
        aw = int(away_record.split("-")[0])
        al = int(away_record.split("-")[1])
        if hw + hl > 0 and aw + al > 0:
            h_pct = hw / (hw + hl)
            a_pct = aw / (aw + al)
            score += int((h_pct - a_pct) * 15)
    except: pass
    return max(0, min(100, round(score)))

def calculate_net_rating(game):
    mins = game.get('minutes_played', 0)
    if mins < 1: return 0, 0, 0, 0
    est_poss_per_team = mins * 1.6
    possessions = round(est_poss_per_team)
    if possessions < 1: return 0, 0, 0, 0
    home_ortg = (game['home_score'] / est_poss_per_team) * 100
    away_ortg = (game['away_score'] / est_poss_per_team) * 100
    net_rating = round(home_ortg - away_ortg, 1)
    return round(home_ortg, 1), round(away_ortg, 1), net_rating, possessions

def remove_ncaa_position(pos_id):
    st.session_state.ncaa_positions = [p for p in st.session_state.ncaa_positions if p['id'] != pos_id]
    # ═══════════════════════════════════════════════
# PART 3A — MAIN UI TOP HALF
# ═══════════════════════════════════════════════

games = fetch_espn_ncaa_games()
kalshi_ml = fetch_kalshi_ncaa_ml()
rankings = fetch_ncaa_rankings()

live_games = [g for g in games if g['status'] in ['STATUS_IN_PROGRESS', 'STATUS_HALFTIME', 'STATUS_END_PERIOD'] or (g['period'] > 0 and g['status'] not in ['STATUS_FINAL', 'STATUS_FULL_TIME'])]
scheduled_games = [g for g in games if g['status'] == 'STATUS_SCHEDULED' and g['period'] == 0]
final_games = [g for g in games if g['status'] in ['STATUS_FINAL', 'STATUS_FULL_TIME']]

st.title("🎓 BIGSNAPSHOT NCAA EDGE FINDER")
st.caption(f"v{VERSION} • {now.strftime('%b %d, %Y %I:%M %p ET')} • College Basketball Mispricing Detector")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Today's Games", len(games))
c2.metric("Live Now", len(live_games))
c3.metric("Scheduled", len(scheduled_games))
c4.metric("Final", len(final_games))

st.divider()

st.subheader("💰 VEGAS vs KALSHI MISPRICING ALERT")

refresh_col1, refresh_col2 = st.columns([3, 1])
with refresh_col1:
    kalshi_time = st.session_state.get('ncaa_kalshi_time')
    if kalshi_time:
        age = (datetime.now(eastern) - kalshi_time).total_seconds()
        if age < 30:
            freshness = f"🟢 {int(age)}s ago"
        elif age < 60:
            freshness = f"🟡 {int(age)}s ago"
        else:
            freshness = f"🔴 {int(age)}s ago — STALE"
        st.caption(f"Kalshi data: {freshness} • ESPN odds: soft book (not sharp)")
    else:
        st.caption("Kalshi data: not yet loaded")
with refresh_col2:
    if st.button("🔄 Refresh Kalshi Prices", key="refresh_kalshi"):
        kalshi_ml = fetch_kalshi_ncaa_ml(force_refresh=True)
        st.success("Kalshi refreshed!")
        st.rerun()

st.caption("Buy when Kalshi underprices Vegas favorite • 5%+ gap = real edge")

mispricings = []
for g in games:
    if g['status'] in ['STATUS_FINAL', 'STATUS_FULL_TIME']:
        continue
    vegas = g.get('vegas_odds', {})
    home_ml = vegas.get('homeML')
    away_ml = vegas.get('awayML')
    spread = vegas.get('spread')
    vegas_home_prob = 0
    vegas_away_prob = 0
    if home_ml and away_ml and home_ml != 0 and away_ml != 0:
        vegas_home_prob = american_to_implied_prob(home_ml) * 100
        vegas_away_prob = american_to_implied_prob(away_ml) * 100
        total = vegas_home_prob + vegas_away_prob
        if total > 0:
            vegas_home_prob = vegas_home_prob / total * 100
            vegas_away_prob = vegas_away_prob / total * 100
    elif spread:
        try:
            vegas_home_prob = max(10, min(90, 50 - (float(spread) * 2.8)))
            vegas_away_prob = 100 - vegas_home_prob
        except:
            continue
    else:
        continue
    kalshi_home_price = find_kalshi_price_for_game(kalshi_ml, g['away_abbrev'], g['home_abbrev'], g['home_abbrev'])
    kalshi_away_price = find_kalshi_price_for_game(kalshi_ml, g['away_abbrev'], g['home_abbrev'], g['away_abbrev'])
    if kalshi_home_price == 0 and kalshi_away_price == 0:
        continue
    home_edge = vegas_home_prob - kalshi_home_price if kalshi_home_price > 0 else 0
    away_edge = vegas_away_prob - kalshi_away_price if kalshi_away_price > 0 else 0
    pick_team = None
    pick_abbrev = None
    pick_vegas = 0
    pick_kalshi = 0
    pick_edge = 0
    if home_edge >= 5 and kalshi_home_price < 90 and home_edge >= away_edge:
        pick_team = g['home']
        pick_abbrev = g['home_abbrev']
        pick_vegas = vegas_home_prob
        pick_kalshi = kalshi_home_price
        pick_edge = home_edge
    elif away_edge >= 5 and kalshi_away_price < 90:
        pick_team = g['away']
        pick_abbrev = g['away_abbrev']
        pick_vegas = vegas_away_prob
        pick_kalshi = kalshi_away_price
        pick_edge = away_edge
    if pick_team:
        kalshi_link = build_kalshi_ncaa_url(g['away_abbrev'], g['home_abbrev'])
        mispricings.append({
            'game': g, 'team': pick_team, 'team_abbrev': pick_abbrev,
            'vegas_prob': pick_vegas, 'kalshi_price': pick_kalshi,
            'edge': pick_edge, 'link': kalshi_link
        })

mispricings.sort(key=lambda x: x['edge'], reverse=True)

if mispricings:
    st.success(f"🔥 {len(mispricings)} mispricing opportunities found!")
    for mp in mispricings:
        g = mp['game']
        if mp['edge'] >= 10:
            edge_color = "#ff6b6b"
            edge_label = "🔥 STRONG"
        elif mp['edge'] >= 7:
            edge_color = "#22c55e"
            edge_label = "🟢 GOOD"
        else:
            edge_color = "#eab308"
            edge_label = "🟡 EDGE"
        rank_a = ""
        rank_h = ""
        if g['away_rank'] > 0:
            rank_a = f"#{g['away_rank']} "
        if g['home_rank'] > 0:
            rank_h = f"#{g['home_rank']} "
        if g['period'] > 0:
            status_text = f"H{g['period']} {g['clock']}"
        else:
            status_text = g.get('game_datetime', 'Scheduled') or 'Scheduled'
        st.markdown(f"**{rank_a}{g['away_abbrev']} @ {rank_h}{g['home_abbrev']}** • {status_text}")
        alert_html = '<div style="background:#0f172a;padding:16px;border-radius:10px;'
        alert_html += f'border:2px solid {edge_color};margin-bottom:12px">'
        alert_html += f'<div style="font-size:1.4em;font-weight:bold;color:#fff;margin-bottom:8px">'
        alert_html += f'🎯 BUY <span style="color:#22c55e">{mp["team_abbrev"]}</span> on Kalshi</div>'
        alert_html += '<table style="width:100%;text-align:center;color:#fff">'
        alert_html += '<tr style="color:#888"><td>Vegas Implied</td><td>Kalshi Price</td><td>EDGE</td></tr>'
        alert_html += f'<tr style="font-size:1.3em;font-weight:bold"><td>{round(mp["vegas_prob"])}%</td>'
        alert_html += f'<td>{round(mp["kalshi_price"])}¢</td>'
        alert_html += f'<td style="color:{edge_color}">+{round(mp["edge"])}%</td></tr></table>'
        alert_html += '<div style="color:#888;font-size:0.8em;margin-top:8px">'
        alert_html += '⚠️ ESPN odds (soft book) — verify on Kalshi before buying</div></div>'
        st.markdown(alert_html, unsafe_allow_html=True)
        st.link_button(f"🎯 BUY {mp['team_abbrev']} on Kalshi", mp['link'], use_container_width=True)
else:
    st.info("🔍 No real mispricings found (need 5%+ gap AND Kalshi price < 90¢)")

st.divider()

st.subheader("🎮 LIVE EDGE MONITOR")

if live_games:
    for g in live_games:
        away = g['away']
        home = g['home']
        away_abbrev = g['away_abbrev']
        home_abbrev = g['home_abbrev']
        total = g['total_score']
        mins = g['minutes_played']
        game_id = g['game_id']
        plays = fetch_ncaa_plays(game_id)
        rank_a = ""
        rank_h = ""
        if g['away_rank'] > 0:
            rank_a = f"#{g['away_rank']} "
        if g['home_rank'] > 0:
            rank_h = f"#{g['home_rank']} "
        st.markdown(f"### {rank_a}{away_abbrev} @ {rank_h}{home_abbrev}")
        sb_html = render_scoreboard(away, home, away_abbrev, home_abbrev, g['away_score'], g['home_score'], g['period'], g['clock'], g['away_rank'], g['home_rank'], g.get('away_record', ''), g.get('home_record', ''))
        st.markdown(sb_html, unsafe_allow_html=True)
        col1, col2 = st.columns([1, 1])
        with col1:
            last_play = plays[-1] if plays else None
            court_html = render_ncaa_court(away_abbrev, home_abbrev, g['away_score'], g['home_score'], g['period'], g['clock'], last_play)
            st.markdown(court_html, unsafe_allow_html=True)
        with col2:
            st.markdown("**📋 LAST 10 PLAYS**")
            tts_on = st.checkbox("🔊 Announce plays", key=f"tts_{game_id}")
            if plays:
                for i, p in enumerate(reversed(plays)):
                    icon, color = get_play_icon(p['play_type'], p['score_value'])
                    play_text = p['text'][:60] if p['text'] else "Play"
                    play_html = f"<div style='padding:4px 8px;margin:2px 0;background:#1e1e2e;"
                    play_html += f"border-radius:4px;border-left:3px solid {color}'>"
                    play_html += f"<span style='color:{color}'>{icon}</span>"
                    play_html += f" H{p['period']} {p['clock']} • {play_text}</div>"
                    st.markdown(play_html, unsafe_allow_html=True)
                    if i == 0 and tts_on and p['text']:
                        speak_play(f"Half {p['period']} {p['clock']}. {p['text']}")
            else:
                st.caption("Waiting for plays...")
        if mins >= 6:
            proj = calc_projection(total, mins)
            pace = total / mins if mins > 0 else 0
            pace_label, pace_color = get_pace_label(pace)
            lead = g['home_score'] - g['away_score']
            if g['home_score'] > g['away_score']:
                leader = home_abbrev
            else:
                leader = away_abbrev
            kalshi_link = build_kalshi_ncaa_url(away_abbrev, home_abbrev)
            info_html = f"<div style='background:#1e1e2e;padding:12px;border-radius:8px;margin-top:8px'>"
            info_html += f"<b>Score:</b> {total} pts in {round(mins)} min • "
            info_html += f"<b>Pace:</b> <span style='color:{pace_color}'>{pace_label}</span> ({pace:.1f}/min)<br>"
            info_html += f"<b>Projection:</b> {proj} pts • <b>Lead:</b> {leader} +{abs(lead)}</div>"
            st.markdown(info_html, unsafe_allow_html=True)
            st.markdown("**🎯 MONEYLINE**")
            if abs(lead) >= 10:
                if abs(lead) >= 15:
                    ml_conf = "🔥 STRONG"
                else:
                    ml_conf = "🟢 GOOD"
                st.link_button(f"{ml_conf} BUY {leader} ML • Lead +{abs(lead)}", kalshi_link, use_container_width=True)
            else:
                st.caption(f"⏳ Wait for larger lead (currently {leader} +{abs(lead)})")
            st.markdown("**📊 TOTALS**")
            yes_lines = [(t, proj - t) for t in sorted(THRESHOLDS) if proj - t >= 6]
            no_lines = [(t, t - proj) for t in sorted(THRESHOLDS, reverse=True) if t - proj >= 6]
            tc1, tc2 = st.columns(2)
            with tc1:
                st.markdown("<span style='color:#22c55e;font-weight:bold'>🟢 YES (Over)</span>", unsafe_allow_html=True)
                if yes_lines:
                    for i, (line, cushion) in enumerate(yes_lines[:3]):
                        if cushion >= 20:
                            safety = "🔒 FORTRESS"
                        elif cushion >= 12:
                            safety = "✅ SAFE"
                        else:
                            safety = "🎯 TIGHT"
                        rec = " ⭐REC" if i == 0 and cushion >= 12 else ""
                        st.link_button(f"{safety} YES {line} (+{int(cushion)}){rec}", kalshi_link, use_container_width=True)
                else:
                    st.caption("No safe YES lines")
            with tc2:
                st.markdown("<span style='color:#ef4444;font-weight:bold'>🔴 NO (Under)</span>", unsafe_allow_html=True)
                if no_lines:
                    for i, (line, cushion) in enumerate(no_lines[:3]):
                        if cushion >= 20:
                            safety = "🔒 FORTRESS"
                        elif cushion >= 12:
                            safety = "✅ SAFE"
                        else:
                            safety = "🎯 TIGHT"
                        rec = " ⭐REC" if i == 0 and cushion >= 12 else ""
                        st.link_button(f"{safety} NO {line} (+{int(cushion)}){rec}", kalshi_link, use_container_width=True)
                else:
                    st.caption("No safe NO lines")
        else:
            st.caption("⏳ Waiting for 6+ minutes...")
        st.divider()
else:
    st.info("No live NCAA games right now")

st.divider()
# ═══════════════════════════════════════════════
# PART 3B — SECRET SAUCE + CUSHION + PACE + PREGAME + ALL GAMES
# ═══════════════════════════════════════════════

st.subheader("🔥 SECRET SAUCE EARLY EDGE")
st.caption("Early momentum at 10+ min • Pace + Net Rating")

secret_sauce = []
for g in live_games:
    mins = g.get('minutes_played', 0)
    if mins < 10 or mins > 16:
        continue
    h_ortg, a_ortg, net_rating, poss = calculate_net_rating(g)
    if poss < 14:
        continue
    pace = g['total_score'] / mins if mins > 0 else 0
    pace_label, pace_color = get_pace_label(pace)
    pace_dev = pace - 3.6
    leader = None
    if g['home_score'] > g['away_score']:
        leader = g['home_abbrev']
    elif g['away_score'] > g['home_score']:
        leader = g['away_abbrev']
    if not leader:
        continue
    if net_rating >= 16:
        if net_rating >= 20:
            confidence = "SECRET SAUCE"
            stars = "⭐⭐⭐"
        elif net_rating >= 18:
            confidence = "STRONG"
            stars = "⭐⭐"
        else:
            confidence = "GOOD"
            stars = "⭐"
        totals_side = ""
        if pace_dev >= 0.3:
            totals_side = " + OVER"
        elif pace_dev <= -0.3:
            totals_side = " + UNDER"
        kalshi_link = build_kalshi_ncaa_url(g['away_abbrev'], g['home_abbrev'])
        game_label = g['away_abbrev'] + " @ " + g['home_abbrev']
        signal_text = "🔒 BUY **" + leader + "** YES" + totals_side
        secret_sauce.append({
            "game": game_label, "mins": mins, "net": net_rating,
            "pace": pace, "pace_label": pace_label, "poss": poss,
            "signal": signal_text, "stars": stars,
            "confidence": confidence, "link": kalshi_link
        })

if secret_sauce:
    for s in sorted(secret_sauce, key=lambda x: -x['net']):
        ss_html = '<div style="background:#0f172a;padding:16px;border-radius:12px;'
        ss_html += 'border:3px solid #22c55e;margin-bottom:16px">'
        ss_html += '<div style="font-size:22px;font-weight:bold;color:#ffd700">'
        ss_html += s['game'] + '</div>'
        ss_html += '<div style="font-size:28px;margin:8px 0">'
        ss_html += s['signal'] + ' ' + s['stars'] + '</div>'
        ss_html += '<div style="color:#ccc">Net Rating: <b>' + str(s['net']) + '</b> '
        ss_html += 'Pace: ' + str(s['pace_label']) + ' (' + f"{s['pace']:.1f}" + '/min) '
        ss_html += 'Poss: <b>' + str(s['poss']) + '</b></div>'
        ss_html += '<div style="margin-top:12px;color:#22c55e;font-weight:bold">'
        ss_html += s['confidence'] + '</div>'
        ss_html += '<a href="' + s['link'] + '" target="_blank" '
        ss_html += 'style="background:#22c55e;color:#000;padding:12px 28px;border-radius:8px;'
        ss_html += 'text-decoration:none;font-weight:bold;display:inline-block;margin-top:12px">'
        ss_html += '🎯 BUY ON KALSHI</a></div>'
        st.markdown(ss_html, unsafe_allow_html=True)
else:
    st.info("No early edge games right now (need 10+ min & Net ≥16)")

st.divider()

st.subheader("🎯 CUSHION SCANNER (Totals)")
all_game_options = ["All Games"] + [g['away_abbrev'] + " @ " + g['home_abbrev'] for g in games]
cush_col1, cush_col2, cush_col3 = st.columns(3)
with cush_col1:
    selected_game = st.selectbox("Select Game:", all_game_options, key="ncaa_cush_game")
with cush_col2:
    min_mins = st.selectbox("Min PLAY TIME:", [6, 8, 10, 12, 16], index=2, key="ncaa_cush_mins")
with cush_col3:
    side_choice = st.selectbox("Side:", ["NO (Under)", "YES (Over)"], key="ncaa_cush_side")

cushion_data = []
for g in games:
    if g['status'] in ['STATUS_FINAL', 'STATUS_FULL_TIME']:
        continue
    game_name = g['away_abbrev'] + " @ " + g['home_abbrev']
    if selected_game != "All Games" and game_name != selected_game:
        continue
    if g['minutes_played'] < min_mins:
        continue
    total = g['total_score']
    mins = g['minutes_played']
    vegas_ou = g.get('vegas_odds', {}).get('overUnder')
    if mins >= 6:
        proj = calc_projection(total, mins)
        pace_label = get_pace_label(total / mins)[0]
        status_text = "H" + str(g['period']) + " " + str(g['clock'])
    elif vegas_ou:
        try:
            proj = round(float(vegas_ou))
            pace_label = "📊 VEGAS"
            status_text = "Scheduled"
        except:
            proj = LEAGUE_AVG_TOTAL
            pace_label = "⏳ PRE"
            status_text = "Scheduled"
    else:
        proj = LEAGUE_AVG_TOTAL
        pace_label = "⏳ PRE"
        status_text = "Scheduled"
    if side_choice == "YES (Over)":
        thresh_sorted = sorted(THRESHOLDS)
    else:
        thresh_sorted = sorted(THRESHOLDS, reverse=True)
    for idx, thresh in enumerate(thresh_sorted):
        if side_choice == "NO (Under)":
            cushion = thresh - proj
        else:
            cushion = proj - thresh
        if cushion >= 6 or selected_game != "All Games":
            if cushion >= 20:
                safety = "🔒 FORTRESS"
            elif cushion >= 12:
                safety = "✅ SAFE"
            elif cushion >= 6:
                safety = "🎯 TIGHT"
            else:
                safety = "⚠️ RISKY"
            kalshi_link = build_kalshi_ncaa_url(g['away_abbrev'], g['home_abbrev'])
            cushion_data.append({
                "game": game_name, "status": status_text, "proj": proj,
                "line": thresh, "cushion": cushion, "pace": pace_label,
                "link": kalshi_link, "mins": mins, "is_live": mins >= 6,
                "safety": safety,
                "is_recommended": idx == 0 and cushion >= 12
            })

safety_order = {"🔒 FORTRESS": 0, "✅ SAFE": 1, "🎯 TIGHT": 2, "⚠️ RISKY": 3}
cushion_data.sort(key=lambda x: (not x['is_live'], safety_order.get(x['safety'], 3), -x['cushion']))

if cushion_data:
    if side_choice == "YES (Over)":
        direction = "go LOW for safety"
    else:
        direction = "go HIGH for safety"
    side_word = side_choice.split()[0]
    st.caption("💡 " + side_word + " bets: " + direction)
    for cd in cushion_data[:15]:
        cc1, cc2, cc3, cc4 = st.columns([3, 1.2, 1.3, 2])
        with cc1:
            rec_badge = " ⭐REC" if cd.get('is_recommended') else ""
            st.markdown("**" + cd['game'] + "** • " + cd['status'] + rec_badge)
            st.caption(cd['pace'] + " • " + str(cd['mins']) + " min")
        with cc2:
            st.write("Proj: " + str(cd['proj']) + " | Line: " + str(cd['line']))
        with cc3:
            if cd['cushion'] >= 12:
                cushion_color = "#22c55e"
            elif cd['cushion'] >= 6:
                cushion_color = "#eab308"
            else:
                cushion_color = "#ef4444"
            cush_html = "<span style='color:" + cushion_color + ";font-weight:bold'>"
            cush_html += cd['safety'] + "<br>+" + str(round(cd['cushion'])) + "</span>"
            st.markdown(cush_html, unsafe_allow_html=True)
        with cc4:
            if "NO" in side_choice:
                btn_label = "BUY NO " + str(cd['line'])
            else:
                btn_label = "BUY YES " + str(cd['line'])
            st.link_button(btn_label, cd['link'], use_container_width=True)
else:
    st.info("⏳ No games at " + str(min_mins) + "+ min yet or no cushion opportunities.")

st.divider()

st.subheader("📈 PACE SCANNER")
pace_data = []
for g in live_games:
    if g['minutes_played'] >= 6:
        p = g['total_score'] / g['minutes_played']
        pl, pc = get_pace_label(p)
        pace_data.append({
            "game": g['away_abbrev'] + " @ " + g['home_abbrev'],
            "status": "H" + str(g['period']) + " " + str(g['clock']),
            "total": g['total_score'], "pace": p,
            "pace_label": pl, "pace_color": pc,
            "proj": calc_projection(g['total_score'], g['minutes_played'])
        })
pace_data.sort(key=lambda x: x['pace'])

if pace_data:
    for pd_item in pace_data:
        pc1, pc2, pc3, pc4 = st.columns([3, 2, 2, 2])
        with pc1:
            st.markdown("**" + pd_item['game'] + "**")
        with pc2:
            st.write(pd_item['status'] + " • " + str(pd_item['total']) + " pts")
        with pc3:
            pace_html = "<span style='color:" + pd_item['pace_color'] + ";font-weight:bold'>"
            pace_html += pd_item['pace_label'] + "</span>"
            st.markdown(pace_html, unsafe_allow_html=True)
        with pc4:
            st.write("Proj: " + str(pd_item['proj']))
else:
    st.info("No live games with 6+ minutes played")

st.divider()

with st.expander("🎯 PRE-GAME ALIGNMENT (Speculative)", expanded=True):
    st.caption("Rankings + Conference + Record")
    if scheduled_games:
        all_picks = []
        for g in scheduled_games:
            h_tier = get_conference_tier(g.get('home_conf', ''))
            a_tier = get_conference_tier(g.get('away_conf', ''))
            edge_score = calc_pregame_edge_ncaa(
                g['home_rank'], g['away_rank'], h_tier, a_tier,
                g.get('home_record', ''), g.get('away_record', '')
            )
            if edge_score >= 75:
                pick = g['home']
                pick_abbrev = g['home_abbrev']
                edge_label = "🟢 STRONG"
                edge_color = "#22c55e"
            elif edge_score >= 65:
                pick = g['home']
                pick_abbrev = g['home_abbrev']
                edge_label = "🟢 GOOD"
                edge_color = "#22c55e"
            elif edge_score <= 25:
                pick = g['away']
                pick_abbrev = g['away_abbrev']
                edge_label = "🟢 STRONG"
                edge_color = "#22c55e"
            elif edge_score <= 35:
                pick = g['away']
                pick_abbrev = g['away_abbrev']
                edge_label = "🟢 GOOD"
                edge_color = "#22c55e"
            else:
                pick = "WAIT"
                pick_abbrev = ""
                edge_label = "🟡 NEUTRAL"
                edge_color = "#eab308"
            all_picks.append({
                "away_abbrev": g['away_abbrev'], "home_abbrev": g['home_abbrev'],
                "away_rank": g['away_rank'], "home_rank": g['home_rank'],
                "pick": pick, "pick_abbrev": pick_abbrev,
                "edge_label": edge_label, "edge_color": edge_color,
                "game_datetime": g.get('game_datetime', '')
            })
        actionable = [p for p in all_picks if p['pick'] != "WAIT"]
        if actionable:
            st.caption("📊 " + str(len(actionable)) + " actionable picks out of " + str(len(all_picks)) + " games")
        for p in all_picks:
            pg1, pg2, pg3 = st.columns([3, 1.5, 2])
            rank_a = ""
            rank_h = ""
            if p['away_rank'] > 0:
                rank_a = "#" + str(p['away_rank']) + " "
            if p['home_rank'] > 0:
                rank_h = "#" + str(p['home_rank']) + " "
            with pg1:
                st.markdown("**" + rank_a + p['away_abbrev'] + " @ " + rank_h + p['home_abbrev'] + "**")
                if p['game_datetime']:
                    st.caption(p['game_datetime'])
            with pg2:
                label_html = "<span style='color:" + p['edge_color'] + "'>" + p['edge_label'] + "</span>"
                st.markdown(label_html, unsafe_allow_html=True)
            with pg3:
                if p['pick'] != "WAIT":
                    link = build_kalshi_ncaa_url(p['away_abbrev'], p['home_abbrev'])
                    st.link_button("🎯 " + p['pick_abbrev'] + " ML", link, use_container_width=True)
                else:
                    st.caption("Wait for better edge")
    else:
        st.info("No scheduled NCAA games")

st.divider()

st.subheader("📋 ALL GAMES TODAY")
for g in games:
    rank_a = ""
    rank_h = ""
    if g['away_rank'] > 0:
        rank_a = "#" + str(g['away_rank']) + " "
    if g['home_rank'] > 0:
        rank_h = "#" + str(g['home_rank']) + " "
    if g['status'] in ['STATUS_FINAL', 'STATUS_FULL_TIME']:
        status = "FINAL: " + str(g['away_score']) + "-" + str(g['home_score'])
        color = "#666"
    elif g['period'] > 0:
        status = "LIVE H" + str(g['period']) + " " + str(g['clock'])
        status += " | " + str(g['away_score']) + "-" + str(g['home_score'])
        color = "#22c55e"
    else:
        spread_val = g.get('vegas_odds', {}).get('spread', 'N/A')
        status = g.get('game_datetime', 'TBD') + " | Spread: " + str(spread_val)
        color = "#888"
    row_html = "<div style='background:#1e1e2e;padding:12px;border-radius:8px;"
    row_html += "margin-bottom:8px;border-left:3px solid " + color + "'>"
    row_html += "<b style='color:#fff'>" + rank_a + g['away_abbrev']
    row_html += " @ " + rank_h + g['home_abbrev'] + "</b><br>"
    row_html += "<span style='color:" + color + "'>" + status + "</span></div>"
    st.markdown(row_html, unsafe_allow_html=True)

st.divider()
st.caption("v" + VERSION + " • Educational only • Not financial advice")
st.caption("Stay small. Stay quiet. Win.")
st.divider()
