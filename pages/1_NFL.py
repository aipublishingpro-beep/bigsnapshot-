import streamlit as st
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="NFL Edge Finder", page_icon="🏈", layout="wide")

# ============================================================
# AUTH
# ============================================================
from auth import require_auth
require_auth()

# Auto-refresh every 30 seconds
st_autorefresh(interval=30000, key="nfl_refresh")

# ============================================================
# GA4 ANALYTICS
# ============================================================
import uuid
import requests as req_ga

def send_ga4_event(page_title, page_path):
    try:
        url = "https://www.google-analytics.com/mp/collect?measurement_id=G-NQKY5VQ376&api_secret=n4oBJjH7RXi3dA7aQo2CZA"
        payload = {"client_id": str(uuid.uuid4()), "events": [{"name": "page_view", "params": {"page_title": page_title, "page_location": "https://bigsnapshot.streamlit.app" + page_path}}]}
        req_ga.post(url, json=payload, timeout=2)
    except:
        pass

send_ga4_event("NFL Edge Finder", "/NFL")

import requests
import json
import os
from datetime import datetime, timedelta
import pytz

eastern = pytz.timezone("US/Eastern")
now = datetime.now(eastern)

VERSION = "21.0"

# ============================================================
# SESSION STATE
# ============================================================
if "last_ball_positions" not in st.session_state:
    st.session_state.last_ball_positions = {}

# ============================================================
# TEAM DATA
# ============================================================
TEAM_ABBREVS = {
    "Arizona Cardinals": "ARI", "Atlanta Falcons": "ATL", "Baltimore Ravens": "BAL",
    "Buffalo Bills": "BUF", "Carolina Panthers": "CAR", "Chicago Bears": "CHI",
    "Cincinnati Bengals": "CIN", "Cleveland Browns": "CLE", "Dallas Cowboys": "DAL",
    "Denver Broncos": "DEN", "Detroit Lions": "DET", "Green Bay Packers": "GB",
    "Houston Texans": "HOU", "Indianapolis Colts": "IND", "Jacksonville Jaguars": "JAX",
    "Kansas City Chiefs": "KC", "Las Vegas Raiders": "LV", "Los Angeles Chargers": "LAC",
    "Los Angeles Rams": "LAR", "Miami Dolphins": "MIA", "Minnesota Vikings": "MIN",
    "New England Patriots": "NE", "New Orleans Saints": "NO", "New York Giants": "NYG",
    "New York Jets": "NYJ", "Philadelphia Eagles": "PHI", "Pittsburgh Steelers": "PIT",
    "San Francisco 49ers": "SF", "Seattle Seahawks": "SEA", "Tampa Bay Buccaneers": "TB",
    "Tennessee Titans": "TEN", "Washington Commanders": "WAS"
}

ABBREV_TO_FULL = {v: k for k, v in TEAM_ABBREVS.items()}

KALSHI_CODES = {
    "ARI": "ARI", "ATL": "ATL", "BAL": "BAL", "BUF": "BUF", "CAR": "CAR",
    "CHI": "CHI", "CIN": "CIN", "CLE": "CLE", "DAL": "DAL", "DEN": "DEN",
    "DET": "DET", "GB": "GB", "HOU": "HOU", "IND": "IND", "JAX": "JAX",
    "KC": "KC", "LV": "LV", "LAC": "LAC", "LAR": "LA", "MIA": "MIA",
    "MIN": "MIN", "NE": "NE", "NO": "NO", "NYG": "NYG", "NYJ": "NYJ",
    "PHI": "PHI", "PIT": "PIT", "SF": "SF", "SEA": "SEA", "TB": "TB",
    "TEN": "TEN", "WAS": "WAS"
}

TEAM_STATS = {
    "ARI": {"net": -12.5, "pace": 24.2, "home_pct": 0.42, "tier": "weak"},
    "ATL": {"net": 2.5, "pace": 25.8, "home_pct": 0.55, "tier": "mid"},
    "BAL": {"net": 15.5, "pace": 27.2, "home_pct": 0.72, "tier": "elite"},
    "BUF": {"net": 18.2, "pace": 26.5, "home_pct": 0.78, "tier": "elite"},
    "CAR": {"net": -18.5, "pace": 21.5, "home_pct": 0.35, "tier": "weak"},
    "CHI": {"net": -8.5, "pace": 22.8, "home_pct": 0.45, "tier": "weak"},
    "CIN": {"net": 5.8, "pace": 25.2, "home_pct": 0.58, "tier": "good"},
    "CLE": {"net": -25.0, "pace": 20.5, "home_pct": 0.38, "tier": "weak"},
    "DAL": {"net": -5.2, "pace": 24.0, "home_pct": 0.52, "tier": "mid"},
    "DEN": {"net": 8.5, "pace": 23.8, "home_pct": 0.65, "tier": "good"},
    "DET": {"net": 22.5, "pace": 28.5, "home_pct": 0.78, "tier": "elite"},
    "GB": {"net": 12.2, "pace": 25.5, "home_pct": 0.70, "tier": "elite"},
    "HOU": {"net": 10.5, "pace": 24.8, "home_pct": 0.68, "tier": "good"},
    "IND": {"net": -2.5, "pace": 23.5, "home_pct": 0.55, "tier": "mid"},
    "JAX": {"net": -8.5, "pace": 22.2, "home_pct": 0.45, "tier": "weak"},
    "KC": {"net": 18.5, "pace": 26.8, "home_pct": 0.82, "tier": "elite"},
    "LV": {"net": -10.2, "pace": 22.5, "home_pct": 0.42, "tier": "weak"},
    "LAC": {"net": 11.8, "pace": 24.5, "home_pct": 0.62, "tier": "good"},
    "LAR": {"net": 8.5, "pace": 25.0, "home_pct": 0.62, "tier": "good"},
    "MIA": {"net": -2.5, "pace": 26.0, "home_pct": 0.55, "tier": "mid"},
    "MIN": {"net": 12.5, "pace": 25.2, "home_pct": 0.68, "tier": "elite"},
    "NE": {"net": -12.5, "pace": 21.8, "home_pct": 0.42, "tier": "weak"},
    "NO": {"net": -8.8, "pace": 23.0, "home_pct": 0.48, "tier": "weak"},
    "NYG": {"net": -15.5, "pace": 21.2, "home_pct": 0.35, "tier": "weak"},
    "NYJ": {"net": -6.5, "pace": 22.5, "home_pct": 0.45, "tier": "weak"},
    "PHI": {"net": 14.8, "pace": 26.2, "home_pct": 0.75, "tier": "elite"},
    "PIT": {"net": 4.8, "pace": 23.8, "home_pct": 0.62, "tier": "mid"},
    "SF": {"net": -4.5, "pace": 24.5, "home_pct": 0.52, "tier": "mid"},
    "SEA": {"net": 6.5, "pace": 25.0, "home_pct": 0.62, "tier": "good"},
    "TB": {"net": 5.8, "pace": 24.8, "home_pct": 0.58, "tier": "good"},
    "TEN": {"net": -14.8, "pace": 21.5, "home_pct": 0.40, "tier": "weak"},
    "WAS": {"net": 8.5, "pace": 25.5, "home_pct": 0.62, "tier": "good"},
}

STAR_PLAYERS = {
    "BAL": ["Lamar Jackson", "Derrick Henry"], "BUF": ["Josh Allen", "James Cook"],
    "KC": ["Patrick Mahomes", "Travis Kelce"], "DET": ["Jared Goff", "Amon-Ra St. Brown", "Jahmyr Gibbs"],
    "PHI": ["Jalen Hurts", "Saquon Barkley", "AJ Brown"], "MIN": ["Sam Darnold", "Justin Jefferson"],
    "GB": ["Jordan Love", "Josh Jacobs"], "SF": ["Brock Purdy", "Christian McCaffrey"],
    "DAL": ["Dak Prescott", "CeeDee Lamb"], "MIA": ["Tua Tagovailoa", "Tyreek Hill"],
    "CIN": ["Joe Burrow", "Ja'Marr Chase"], "LAC": ["Justin Herbert", "JK Dobbins"],
    "HOU": ["CJ Stroud", "Nico Collins"], "DEN": ["Bo Nix", "Javonte Williams"],
    "SEA": ["Geno Smith", "DK Metcalf"], "TB": ["Baker Mayfield", "Mike Evans"],
    "LAR": ["Matthew Stafford", "Puka Nacua"], "WAS": ["Jayden Daniels", "Terry McLaurin"],
    "ATL": ["Kirk Cousins", "Bijan Robinson"], "PIT": ["Russell Wilson", "Najee Harris"],
    "IND": ["Anthony Richardson", "Jonathan Taylor"], "ARI": ["Kyler Murray", "Marvin Harrison Jr"],
    "CHI": ["Caleb Williams", "DJ Moore"], "JAX": ["Trevor Lawrence", "Travis Etienne"],
    "NYJ": ["Aaron Rodgers", "Breece Hall"], "LV": ["Aidan O'Connell", "Brock Bowers"],
    "NE": ["Drake Maye", "Rhamondre Stevenson"], "NYG": ["Daniel Jones", "Malik Nabers"],
    "NO": ["Derek Carr", "Alvin Kamara"], "CAR": ["Bryce Young", "Chuba Hubbard"],
    "CLE": ["Deshaun Watson", "Nick Chubb"], "TEN": ["Will Levis", "Tony Pollard"],
}

STAR_TIERS = {
    "Patrick Mahomes": 3, "Josh Allen": 3, "Lamar Jackson": 3, "Jalen Hurts": 3, "Joe Burrow": 3,
    "Travis Kelce": 2, "Tyreek Hill": 2, "Justin Jefferson": 2, "CeeDee Lamb": 2, "Ja'Marr Chase": 2,
    "Derrick Henry": 2, "Saquon Barkley": 2, "Christian McCaffrey": 2,
    "AJ Brown": 2, "Amon-Ra St. Brown": 2, "DK Metcalf": 2, "Puka Nacua": 2,
    "Justin Herbert": 2, "CJ Stroud": 2, "Jayden Daniels": 2, "Jared Goff": 2,
    "Brock Purdy": 1, "Jordan Love": 1, "Dak Prescott": 1, "Tua Tagovailoa": 1,
    "Matthew Stafford": 1, "Baker Mayfield": 1, "Geno Smith": 1, "Kirk Cousins": 1,
}

THRESHOLDS = [37.5, 40.5, 43.5, 45.5, 47.5, 49.5, 51.5, 54.5, 57.5]

# ============================================================
# PLAY-BY-PLAY ICONS
# ============================================================
PLAY_ICONS = {
    "touchdown": "🏈", "field goal": "🥅", "punt": "📤", "interception": "🔴",
    "fumble": "🔴", "sack": "⚠️", "incomplete": "✕", "rush": "🏃",
    "pass": "🎯", "penalty": "🟡", "timeout": "⏸️", "kickoff": "⚡",
    "two-point": "2️⃣", "safety": "⚡", "extra point": "➕",
}

def get_play_icon(play_text):
    t = play_text.lower()
    if "touchdown" in t: return "🏈", "#ffd700"
    if "field goal" in t and ("good" in t or "made" in t): return "🥅", "#22c55e"
    if "field goal" in t and ("no good" in t or "miss" in t or "blocked" in t): return "❌", "#ff4444"
    if "intercept" in t: return "🔴", "#ff4444"
    if "fumble" in t: return "🔴", "#ff4444"
    if "sack" in t: return "⚠️", "#ff8800"
    if "incomplete" in t: return "✕", "#ff4444"
    if "punt" in t: return "📤", "#888"
    if "kickoff" in t or "kicks off" in t: return "⚡", "#aaa"
    if "penalty" in t: return "🟡", "#eab308"
    if "timeout" in t: return "⏸️", "#aaa"
    if "two-point" in t: return "2️⃣", "#22c55e"
    if "extra point" in t: return "➕", "#22c55e"
    if "rush" in t or "ran " in t or "up the middle" in t or "left end" in t or "right end" in t: return "🏃", "#3b82f6"
    if "pass" in t or "to " in t: return "🎯", "#22c55e"
    return "▶️", "#888"

# ============================================================
# FOOTBALL FIELD VISUALIZATION
# ============================================================
def detect_scoring_play(last_play):
    if not last_play:
        return False, None, None
    play_text = (last_play.get("text", "") or "").lower()
    play_type = last_play.get("type", {}).get("text", "").lower() if isinstance(last_play.get("type"), dict) else ""
    is_scoring = last_play.get("scoringPlay", False)
    if is_scoring or "touchdown" in play_text or "touchdown" in play_type:
        return True, "touchdown", play_text
    elif "field goal" in play_text or "field goal" in play_type:
        if "good" in play_text or "made" in play_text:
            return True, "field_goal", play_text
    elif "safety" in play_text:
        return True, "safety", play_text
    return False, None, play_text

def get_smart_ball_position(poss_text, possession_team, yards_to_endzone, is_home_possession,
                            last_play, period, clock, home_team, away_team, game_key,
                            home_abbrev, away_abbrev):
    last_known = st.session_state.last_ball_positions.get(game_key, {})

    if poss_text and possession_team:
        try:
            parts = poss_text.strip().split()
            if len(parts) >= 2:
                side_team = parts[0].upper()
                yard_line = int(parts[1])
                if side_team == home_abbrev.upper():
                    ball_yard = 100 - yard_line
                elif side_team == away_abbrev.upper():
                    ball_yard = yard_line
                else:
                    if is_home_possession is not None and yards_to_endzone is not None:
                        ball_yard = yards_to_endzone if is_home_possession else 100 - yards_to_endzone
                    else:
                        ball_yard = last_known.get('ball_yard', 50)
                st.session_state.last_ball_positions[game_key] = {
                    'ball_yard': ball_yard, 'poss_team': possession_team, 'poss_text': poss_text
                }
                return ball_yard, "normal", possession_team, poss_text
        except (ValueError, IndexError):
            pass

    is_scoring, score_type, _ = detect_scoring_play(last_play)
    if is_scoring:
        if last_known.get('poss_team'):
            scoring_team = last_known.get('poss_team')
            ball_yard = 100 if scoring_team == home_team else 0
        else:
            last_yard = last_known.get('ball_yard', 50)
            ball_yard = 100 if last_yard > 50 else 0
        score_emoji = "🏈" if score_type == "touchdown" else "🥅" if score_type == "field_goal" else "⚡"
        return ball_yard, "scoring", None, score_emoji + " " + score_type.upper().replace('_', ' ')

    if last_play:
        play_text = (last_play.get("text", "") or "").lower()
        if "kickoff" in play_text or "kicks off" in play_text:
            return 65, "kickoff", None, "⚡ KICKOFF"
        elif "punts" in play_text:
            return 50, "between_plays", None, "📤 PUNT"

    if period > 0:
        if clock == "0:00":
            return last_known.get('ball_yard', 50), "between_plays", None, "⏱️ End of Quarter"
        if last_known.get('ball_yard') is not None:
            return last_known.get('ball_yard'), "between_plays", last_known.get('poss_team'), "Between Plays"

    return 50, "between_plays", None, ""

def render_football_field(ball_yard, down, distance, possession_team, away_team, home_team,
                          yards_to_endzone=None, poss_text=None, display_mode="normal", last_play=None):
    away_code = KALSHI_CODES.get(away_team, away_team[:3].upper() if away_team else "AWY")
    home_code = KALSHI_CODES.get(home_team, home_team[:3].upper() if home_team else "HME")

    play_status_html = ""
    is_incomplete = False
    if last_play:
        pt = (last_play.get("text", "") or "").lower()
        if "incomplete" in pt:
            is_incomplete = True
            play_status_html = '<div style="position:absolute;left:50%;top:15%;transform:translateX(-50%);background:#ff4444;color:#fff;padding:2px 10px;border-radius:4px;font-size:12px;font-weight:bold;z-index:10">✕ INCOMPLETE</div>'
        elif "intercepted" in pt or "intercept" in pt:
            is_incomplete = True
            play_status_html = '<div style="position:absolute;left:50%;top:15%;transform:translateX(-50%);background:#ff4444;color:#fff;padding:2px 10px;border-radius:4px;font-size:12px;font-weight:bold;z-index:10">🔴 INTERCEPTED</div>'
        elif "fumble" in pt:
            play_status_html = '<div style="position:absolute;left:50%;top:15%;transform:translateX(-50%);background:#ff4444;color:#fff;padding:2px 10px;border-radius:4px;font-size:12px;font-weight:bold;z-index:10">🔴 FUMBLE</div>'
        elif "touchdown" in pt:
            play_status_html = '<div style="position:absolute;left:50%;top:15%;transform:translateX(-50%);background:#ffd700;color:#000;padding:2px 10px;border-radius:4px;font-size:12px;font-weight:bold;z-index:10">🏈 TOUCHDOWN</div>'
        elif "field goal" in pt and ("good" in pt or "made" in pt):
            play_status_html = '<div style="position:absolute;left:50%;top:15%;transform:translateX(-50%);background:#22c55e;color:#fff;padding:2px 10px;border-radius:4px;font-size:12px;font-weight:bold;z-index:10">🥅 FIELD GOAL</div>'
        elif "sacked" in pt:
            play_status_html = '<div style="position:absolute;left:50%;top:15%;transform:translateX(-50%);background:#ff8800;color:#fff;padding:2px 10px;border-radius:4px;font-size:12px;font-weight:bold;z-index:10">⚠️ SACK</div>'
        elif "pass" in pt and ("to" in pt or "for" in pt) and "incomplete" not in pt and "sacked" not in pt:
            play_status_html = '<div style="position:absolute;left:50%;top:15%;transform:translateX(-50%);background:#22c55e;color:#fff;padding:2px 10px;border-radius:4px;font-size:12px;font-weight:bold;z-index:10">✓ COMPLETE</div>'
        elif "punt" in pt:
            play_status_html = '<div style="position:absolute;left:50%;top:15%;transform:translateX(-50%);background:#666;color:#fff;padding:2px 10px;border-radius:4px;font-size:12px;font-weight:bold;z-index:10">📤 PUNT</div>'
        elif "rush" in pt or "ran " in pt or "up the middle" in pt:
            play_status_html = '<div style="position:absolute;left:50%;top:15%;transform:translateX(-50%);background:#3b82f6;color:#fff;padding:2px 10px;border-radius:4px;font-size:12px;font-weight:bold;z-index:10">🏃 RUSH</div>'
        elif "penalty" in pt:
            play_status_html = '<div style="position:absolute;left:50%;top:15%;transform:translateX(-50%);background:#eab308;color:#000;padding:2px 10px;border-radius:4px;font-size:12px;font-weight:bold;z-index:10">🟡 PENALTY</div>'

    if display_mode == "scoring":
        situation = poss_text or "🏈 SCORE!"
        poss_display = "—"
        ball_loc = ""
        ball_style = "font-size:28px;text-shadow:0 0 20px #ffff00"
        direction_arrow = ""
    elif display_mode == "kickoff":
        situation = poss_text or "⚡ KICKOFF"
        poss_display = "—"
        ball_loc = ""
        ball_style = "font-size:24px;text-shadow:0 0 10px #fff"
        direction_arrow = ""
    elif display_mode == "between_plays" or not possession_team:
        situation = poss_text if poss_text else "Between Plays"
        poss_display = "—"
        ball_loc = ""
        ball_style = "font-size:24px;opacity:0.6;text-shadow:0 0 10px #fff"
        direction_arrow = ""
    else:
        situation = (str(down) + " & " + str(distance)) if down and distance else "—"
        poss_code = KALSHI_CODES.get(possession_team, possession_team[:3].upper() if possession_team else "???")
        if possession_team == home_team:
            poss_display = poss_code + " Ball"
            direction_arrow = "←"
        elif possession_team == away_team:
            poss_display = poss_code + " Ball"
            direction_arrow = "→"
        else:
            poss_display = poss_code + " Ball"
            direction_arrow = ""
        ball_loc = poss_text if poss_text else ""
        ball_style = "font-size:24px;text-shadow:0 0 10px #fff"

    red_zone_note = ""
    if yards_to_endzone and yards_to_endzone <= 20 and possession_team:
        red_zone_note = " 🔴 RED ZONE"

    ball_pct = 10 + (ball_yard * 0.8) if ball_yard is not None else 50
    ball_pct = max(10, min(90, ball_pct))

    arrow_html = ""
    if direction_arrow:
        if direction_arrow == "→":
            arrow_pct = min(ball_pct + 6, 88)
        else:
            arrow_pct = max(ball_pct - 6, 12)
        arrow_html = '<div style="position:absolute;left:' + str(arrow_pct) + '%;top:50%;transform:translate(-50%,-50%);color:#ffff00;font-size:20px;font-weight:bold;text-shadow:0 0 8px #000">' + direction_arrow + '</div>'

    x_html = ""
    if is_incomplete and direction_arrow:
        if direction_arrow == "→":
            x_pct = min(ball_pct + 15, 85)
        else:
            x_pct = max(ball_pct - 15, 15)
        x_html = '<div style="position:absolute;left:' + str(x_pct) + '%;top:50%;transform:translate(-50%,-50%);color:#ff4444;font-size:22px;font-weight:bold;text-shadow:0 0 6px #000">✕</div>'

    h = '<div style="background:#1a1a1a;padding:15px;border-radius:10px;margin:10px 0">'
    h += '<div style="text-align:center;margin-bottom:10px;font-size:1.1em">'
    h += '<span style="color:#00ff00;font-weight:bold">' + poss_display + '</span>'
    h += '<span style="color:#ff4444">' + red_zone_note + '</span></div>'
    h += '<div style="display:flex;justify-content:space-between;margin-bottom:8px">'
    h += '<span style="color:#aaa">' + ball_loc + '</span>'
    h += '<span style="color:#fff;font-weight:bold">' + situation + '</span></div>'
    h += '<div style="position:relative;height:70px;background:linear-gradient(90deg,#8B0000 0%,#8B0000 10%,#228B22 10%,#228B22 90%,#00008B 90%,#00008B 100%);border-radius:8px;overflow:hidden">'
    h += play_status_html
    for pct in [10, 18, 26, 34, 42]:
        h += '<div style="position:absolute;left:' + str(pct) + '%;top:0;bottom:0;width:1px;background:rgba(255,255,255,0.2)"></div>'
    h += '<div style="position:absolute;left:50%;top:0;bottom:0;width:2px;background:rgba(255,255,255,0.5)"></div>'
    for pct in [58, 66, 74, 82, 90]:
        h += '<div style="position:absolute;left:' + str(pct) + '%;top:0;bottom:0;width:1px;background:rgba(255,255,255,0.2)"></div>'
    h += '<div style="position:absolute;left:' + str(ball_pct) + '%;top:60%;transform:translate(-50%,-50%);' + ball_style + '">🏈</div>'
    h += arrow_html + x_html
    h += '<div style="position:absolute;left:5%;top:60%;transform:translate(-50%,-50%);color:#fff;font-weight:bold;font-size:14px">' + away_code + '</div>'
    h += '<div style="position:absolute;left:95%;top:60%;transform:translate(-50%,-50%);color:#fff;font-weight:bold;font-size:14px">' + home_code + '</div>'
    h += '</div>'
    h += '<div style="display:flex;justify-content:space-between;margin-top:5px;color:#888;font-size:11px">'
    h += '<span>← ' + away_code + ' EZ</span><span>10</span><span>20</span><span>30</span><span>40</span><span>50</span><span>40</span><span>30</span><span>20</span><span>10</span><span>' + home_code + ' EZ →</span>'
    h += '</div></div>'
    return h

# ============================================================
# FETCH FUNCTIONS
# ============================================================
@st.cache_data(ttl=30)
def fetch_games():
    """Fetch games - NO date filter so it catches Super Bowl / playoffs / any live game"""
    urls = [
        "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard",
    ]
    today_str = datetime.now(eastern).strftime('%Y%m%d')
    urls.append("https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates=" + today_str)

    all_event_ids = set()
    games = []

    for url in urls:
        try:
            resp = requests.get(url, timeout=10)
            data = resp.json()
            for event in data.get("events", []):
                eid = event.get("id", "")
                if eid in all_event_ids:
                    continue
                all_event_ids.add(eid)

                comp = event.get("competitions", [{}])[0]
                competitors = comp.get("competitors", [])
                if len(competitors) < 2:
                    continue

                home_team, away_team = None, None
                home_score, away_score = 0, 0
                home_abbrev, away_abbrev = "", ""

                for c in competitors:
                    full_name = c.get("team", {}).get("displayName", "")
                    abbr = TEAM_ABBREVS.get(full_name, c.get("team", {}).get("abbreviation", ""))
                    espn_abbr = c.get("team", {}).get("abbreviation", "")
                    score = int(c.get("score", 0) or 0)
                    if c.get("homeAway") == "home":
                        home_team = abbr
                        home_score = score
                        home_abbrev = espn_abbr
                    else:
                        away_team = abbr
                        away_score = score
                        away_abbrev = espn_abbr

                status = event.get("status", {}).get("type", {}).get("name", "STATUS_SCHEDULED")
                period = event.get("status", {}).get("period", 0)
                clock = event.get("status", {}).get("displayClock", "")
                detail = event.get("status", {}).get("type", {}).get("detail", "")

                game_date_str = event.get("date", "")
                game_date = None
                if game_date_str:
                    try:
                        game_date = datetime.fromisoformat(game_date_str.replace("Z", "+00:00")).astimezone(eastern)
                    except:
                        pass

                situation = comp.get("situation", {})
                poss_team_id = situation.get("possession", "")
                down = situation.get("down", 0)
                distance = situation.get("distance", 0)
                yard_line = situation.get("yardLine", 50)
                yards_to_endzone = situation.get("yardsToEndzone", 50)
                is_red_zone = situation.get("isRedZone", False)
                poss_text = situation.get("possessionText", "")
                last_play = situation.get("lastPlay", {})

                possession_team = None
                is_home_possession = None
                for c in competitors:
                    if c.get("team", {}).get("id") == poss_team_id:
                        poss_full = c.get("team", {}).get("displayName", "")
                        possession_team = TEAM_ABBREVS.get(poss_full, c.get("team", {}).get("abbreviation", ""))
                        is_home_possession = c.get("homeAway") == "home"
                        break

                minutes_played = 0
                if period > 0:
                    completed_quarters = (period - 1) * 15
                    if clock:
                        try:
                            parts = clock.split(":")
                            mins_left = int(parts[0])
                            minutes_played = completed_quarters + (15 - mins_left)
                        except:
                            minutes_played = completed_quarters

                # Halftime detection
                is_halftime = "halftime" in detail.lower() or (period == 2 and clock == "0:00")

                games.append({
                    "event_id": eid,
                    "away": away_team, "home": home_team,
                    "away_abbrev": away_abbrev, "home_abbrev": home_abbrev,
                    "away_score": away_score, "home_score": home_score,
                    "status": status, "period": period, "clock": clock,
                    "detail": detail, "is_halftime": is_halftime,
                    "minutes_played": minutes_played,
                    "total_score": home_score + away_score,
                    "game_date": game_date,
                    "possession_team": possession_team,
                    "is_home_possession": is_home_possession,
                    "down": down, "distance": distance,
                    "yard_line": yard_line, "yards_to_endzone": yards_to_endzone,
                    "is_red_zone": is_red_zone, "poss_text": poss_text,
                    "last_play": last_play
                })
        except Exception as e:
            st.error("ESPN fetch error: " + str(e))

    if not games:
        for days_ahead in range(1, 8):
            future_date = (datetime.now(eastern) + timedelta(days=days_ahead)).strftime('%Y%m%d')
            url2 = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates=" + future_date
            try:
                resp2 = requests.get(url2, timeout=5)
                data2 = resp2.json()
                if data2.get("events"):
                    for event in data2.get("events", []):
                        comp = event.get("competitions", [{}])[0]
                        competitors = comp.get("competitors", [])
                        if len(competitors) < 2:
                            continue
                        home_team, away_team = None, None
                        home_score, away_score = 0, 0
                        home_abbrev, away_abbrev = "", ""
                        for c in competitors:
                            full_name = c.get("team", {}).get("displayName", "")
                            abbr = TEAM_ABBREVS.get(full_name, c.get("team", {}).get("abbreviation", ""))
                            espn_abbr = c.get("team", {}).get("abbreviation", "")
                            score = int(c.get("score", 0) or 0)
                            if c.get("homeAway") == "home":
                                home_team = abbr
                                home_score = score
                                home_abbrev = espn_abbr
                            else:
                                away_team = abbr
                                away_score = score
                                away_abbrev = espn_abbr
                        status = event.get("status", {}).get("type", {}).get("name", "STATUS_SCHEDULED")
                        period = event.get("status", {}).get("period", 0)
                        clock = event.get("status", {}).get("displayClock", "")
                        detail = event.get("status", {}).get("type", {}).get("detail", "")
                        game_date_str = event.get("date", "")
                        game_date = None
                        if game_date_str:
                            try:
                                game_date = datetime.fromisoformat(game_date_str.replace("Z", "+00:00")).astimezone(eastern)
                            except:
                                pass
                        games.append({
                            "event_id": event.get("id", ""),
                            "away": away_team, "home": home_team,
                            "away_abbrev": away_abbrev, "home_abbrev": home_abbrev,
                            "away_score": away_score, "home_score": home_score,
                            "status": status, "period": period, "clock": clock,
                            "detail": detail, "is_halftime": False,
                            "minutes_played": 0, "total_score": 0,
                            "game_date": game_date,
                            "possession_team": None, "is_home_possession": None,
                            "down": 0, "distance": 0,
                            "yard_line": 50, "yards_to_endzone": 50,
                            "is_red_zone": False, "poss_text": "",
                            "last_play": {}
                        })
                    break
            except:
                continue
    return games

@st.cache_data(ttl=30)
def fetch_play_by_play(event_id):
    """Fetch last plays from ESPN summary endpoint"""
    if not event_id:
        return []
    url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/summary?event=" + str(event_id)
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        plays = []
        drives = data.get("drives", {}).get("previous", [])
        current = data.get("drives", {}).get("current", {})
        if current:
            drives.append(current)
        for drive in drives:
            for play in drive.get("plays", []):
                text = play.get("text", "")
                clock_val = play.get("clock", {}).get("displayValue", "")
                period_val = play.get("period", {}).get("number", 0)
                is_scoring = play.get("scoringPlay", False)
                if text:
                    plays.append({
                        "text": text,
                        "clock": clock_val,
                        "period": period_val,
                        "scoring": is_scoring
                    })
        return plays[-10:] if plays else []
    except:
        return []

@st.cache_data(ttl=300)
def fetch_injuries():
    url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/injuries"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        injuries = {}
        for team_data in data.get("injuries", []):
            team_name = team_data.get("team", {}).get("displayName", "")
            team_key = TEAM_ABBREVS.get(team_name, "")
            if not team_key:
                continue
            injuries[team_key] = []
            for cat in team_data.get("categories", []):
                for player in cat.get("items", []):
                    athlete = player.get("athlete", {})
                    name = athlete.get("displayName", "")
                    status = player.get("status", "")
                    pos = athlete.get("position", {}).get("abbreviation", "")
                    if name:
                        injuries[team_key].append({"name": name, "status": status, "pos": pos})
        return injuries
    except:
        return {}

@st.cache_data(ttl=300)
def fetch_nfl_news():
    url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/news?limit=10"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        articles = []
        for article in data.get("articles", []):
            headline = article.get("headline", "")
            description = article.get("description", "")
            published = article.get("published", "")
            link = article.get("links", {}).get("web", {}).get("href", "")
            time_ago = ""
            if published:
                try:
                    pub_dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
                    delta = datetime.now(pytz.UTC) - pub_dt
                    if delta.days > 0:
                        time_ago = str(delta.days) + "d ago"
                    elif delta.seconds >= 3600:
                        time_ago = str(delta.seconds // 3600) + "h ago"
                    else:
                        time_ago = str(delta.seconds // 60) + "m ago"
                except:
                    pass
            if headline:
                articles.append({
                    "headline": headline,
                    "description": description[:150] + "..." if len(description) > 150 else description,
                    "time_ago": time_ago, "link": link
                })
        return articles
    except:
        return []

# ============================================================
# EDGE CALCULATION
# ============================================================
def calc_pregame_edge(away, home, injuries):
    home_pts, away_pts = 0, 0
    factors_home, factors_away = [], []
    home_stats = TEAM_STATS.get(home, {})
    away_stats = TEAM_STATS.get(away, {})
    home_injuries = injuries.get(home, [])
    away_injuries = injuries.get(away, [])
    home_stars = STAR_PLAYERS.get(home, [])
    away_stars = STAR_PLAYERS.get(away, [])
    home_out = [str(inj.get("name", "")).lower() for inj in home_injuries if "OUT" in str(inj.get("status", "")).upper()]
    away_out = [str(inj.get("name", "")).lower() for inj in away_injuries if "OUT" in str(inj.get("status", "")).upper()]

    for star in home_stars:
        if any(star.lower() in n for n in home_out):
            tier = STAR_TIERS.get(star, 1)
            pts = 5 if tier == 3 else 3 if tier == 2 else 1
            away_pts += pts
            factors_away.append("🏥 " + star.split()[-1] + " OUT +" + str(pts))
    for star in away_stars:
        if any(star.lower() in n for n in away_out):
            tier = STAR_TIERS.get(star, 1)
            pts = 5 if tier == 3 else 3 if tier == 2 else 1
            home_pts += pts
            factors_home.append("🏥 " + star.split()[-1] + " OUT +" + str(pts))

    home_net = home_stats.get("net", 0)
    away_net = away_stats.get("net", 0)
    net_gap = home_net - away_net
    if net_gap >= 20:
        home_pts += 4; factors_home.append("📊 Net +20")
    elif net_gap >= 12:
        home_pts += 2.5; factors_home.append("📊 Net +12")
    elif net_gap >= 6:
        home_pts += 1.5; factors_home.append("📊 Net +6")
    elif net_gap <= -20:
        away_pts += 4; factors_away.append("📊 Net +20")
    elif net_gap <= -12:
        away_pts += 2.5; factors_away.append("📊 Net +12")
    elif net_gap <= -6:
        away_pts += 1.5; factors_away.append("📊 Net +6")

    home_pts += 2.5; factors_home.append("🏟️ Home")
    if away_stats.get("tier") == "elite" and home_stats.get("tier") == "weak":
        away_pts += 2; factors_away.append("🛫 Elite Road")

    base = 50 + (net_gap * 1.2)
    base = max(25, min(75, base))
    score = base + home_pts - away_pts
    score = max(10, min(90, score))

    if score >= 50:
        return home, int(score), factors_home
    else:
        return away, int(100 - score), factors_away

def calc_live_edge(game, injuries):
    away, home = game['away'], game['home']
    away_score, home_score = game['away_score'], game['home_score']
    period = game['period']
    minutes = game['minutes_played']
    total = game['total_score']
    lead = home_score - away_score

    pick, pregame_score, factors = calc_pregame_edge(away, home, injuries)

    pace = round(total / minutes, 2) if minutes > 0 else 0
    pace_label = "🔥 FAST" if pace > 1.0 else "⚖️ AVG" if pace > 0.7 else "🐢 SLOW"

    live_adj = 0
    if abs(lead) >= 21: live_adj = 30 if lead > 0 else -30
    elif abs(lead) >= 14: live_adj = 22 if lead > 0 else -22
    elif abs(lead) >= 10: live_adj = 15 if lead > 0 else -15
    elif abs(lead) >= 7: live_adj = 10 if lead > 0 else -10
    elif abs(lead) >= 3: live_adj = 5 if lead > 0 else -5

    if period == 4:
        if abs(lead) >= 14: live_adj += 20 if lead > 0 else -20
        elif abs(lead) >= 7: live_adj += 12 if lead > 0 else -12
    elif period == 3 and abs(lead) >= 14:
        live_adj += 8 if lead > 0 else -8

    final_score = pregame_score + live_adj if pick == home else (100 - pregame_score) + live_adj
    final_score = max(10, min(95, final_score))

    if lead > 0: live_pick = home
    elif lead < 0: live_pick = away
    else: live_pick = pick

    proj_total = round((total / minutes) * 60) if minutes >= 8 else 46

    return {
        "pick": live_pick, "score": int(final_score), "lead": lead,
        "pace": pace, "pace_label": pace_label, "proj_total": proj_total,
        "factors": factors
    }

# ============================================================
# KALSHI LINKS
# ============================================================
def get_kalshi_link():
    return "https://kalshi.com/sports/football/NFL"

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.header("📖 NFL EDGE GUIDE")
    st.markdown("""### Score Guide
| Score | Label | Action |
|-------|-------|--------|
| **70+** | 🟢 STRONG | Best bets |
| **60-69** | 🟢 GOOD | Worth it |
| **50-59** | 🟡 MODERATE | Wait |
| **<50** | ⚪ WEAK | Skip |

---
### Field Legend
- ◄ = Attacking LEFT (away EZ)
- ► = Attacking RIGHT (home EZ)
- 🔴 RED ZONE = Inside 20

---
### Pace Guide
| Pace | Label | Action |
|------|-------|--------|
| <0.7 | 🐢 SLOW | Buy NO |
| 0.7-1.0 | ⚖️ AVG | Wait |
| >1.0 | 🔥 FAST | Buy YES |""")
    st.divider()
    st.caption("v" + VERSION + " NFL EDGE")

# ============================================================
# FETCH DATA
# ============================================================
games = fetch_games()
injuries = fetch_injuries()
nfl_news = fetch_nfl_news()

today_teams = set()
for g in games:
    today_teams.add(g.get('away', ''))
    today_teams.add(g.get('home', ''))

live_games = [g for g in games if g['status'] == 'STATUS_IN_PROGRESS']
scheduled_games = [g for g in games if g['status'] == 'STATUS_SCHEDULED']
final_games = [g for g in games if g['status'] in ('STATUS_FINAL', 'STATUS_END_PERIOD')]
halftime_games = [g for g in games if g.get('is_halftime')]

# Treat halftime as live for display purposes
for g in games:
    if g.get('is_halftime') and g not in live_games:
        live_games.append(g)

# ============================================================
# UI HEADER
# ============================================================
st.title("🏈 NFL EDGE FINDER")
st.caption("v" + VERSION + " • " + now.strftime('%b %d, %Y %I:%M %p ET') + " • Auto-refresh: 30s")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Today's Games", len(games))
c2.metric("Live Now", len(live_games))
c3.metric("Scheduled", len(scheduled_games))
c4.metric("Final", len(final_games))

st.divider()

# ============================================================
# 🏥 INJURY REPORT
# ============================================================
st.subheader("🏥 INJURY REPORT")
injured_stars = []
for team, team_injuries in injuries.items():
    if team not in today_teams:
        continue
    for inj in team_injuries:
        name = inj.get("name", "")
        status = str(inj.get("status", "")).upper()
        if "OUT" in status or "DOUBT" in status:
            tier = 0
            for star_name, star_tier in STAR_TIERS.items():
                if star_name.lower() in name.lower():
                    tier = star_tier
                    break
            if tier > 0:
                injured_stars.append({"name": name, "team": team, "status": "OUT" if "OUT" in status else "DOUBT", "tier": tier})
injured_stars.sort(key=lambda x: (-x['tier'], x['team']))

if injured_stars:
    cols = st.columns(3)
    for i, inj in enumerate(injured_stars):
        with cols[i % 3]:
            stars = "⭐" * inj['tier']
            sc = "#ff4444" if inj['status'] == "OUT" else "#ffaa00"
            st.markdown('<div style="background:linear-gradient(135deg,#1a1a2e,#2a1a2a);padding:10px;border-radius:6px;border-left:3px solid ' + sc + ';margin-bottom:6px"><div style="color:#fff;font-weight:bold">' + stars + ' ' + inj['name'] + ' 🔥</div><div style="color:' + sc + ';font-size:0.85em">' + inj['status'] + ' • ' + inj['team'] + '</div></div>', unsafe_allow_html=True)
else:
    st.info("No major star injuries for today's games")

st.divider()

# ============================================================
# 📰 NFL NEWS
# ============================================================
st.subheader("📰 NFL NEWS")
if nfl_news:
    for article in nfl_news[:6]:
        hl = article.get("headline", "")
        desc = article.get("description", "")
        ta = article.get("time_ago", "")
        lnk = article.get("link", "")
        is_big = any(kw in hl.lower() for kw in ["super bowl", "playoff", "championship", "mvp", "trade", "injury"])
        bc = "#ffd700" if is_big else "#444"
        badge = "🏆 " if "super bowl" in hl.lower() else "🔥 " if is_big else ""
        link_html = '<a href="' + lnk + '" target="_blank" style="color:#4a9eff;font-size:0.8em;text-decoration:none">Read more →</a>' if lnk else ''
        st.markdown('<div style="background:linear-gradient(135deg,#1a1a2e,#16213e);padding:12px;border-radius:8px;border-left:3px solid ' + bc + ';margin-bottom:8px"><div style="color:#fff;font-weight:bold;font-size:1em">' + badge + hl + '</div><div style="color:#aaa;font-size:0.85em;margin-top:4px">' + desc + '</div><div style="display:flex;justify-content:space-between;margin-top:6px"><span style="color:#666;font-size:0.8em">' + ta + '</span>' + link_html + '</div></div>', unsafe_allow_html=True)
else:
    st.info("No NFL news available right now")

st.divider()

# ============================================================
# 🔴 LIVE EDGE MONITOR + FIELD + PLAY-BY-PLAY
# ============================================================
if live_games:
    st.subheader("🔴 LIVE EDGE MONITOR")
    st.markdown("*Real-time edge updates every 30 seconds.*")

    live_with_edge = []
    for g in live_games:
        edge = calc_live_edge(g, injuries)
        live_with_edge.append((g, edge))
    live_with_edge.sort(key=lambda x: x[1]['score'], reverse=True)

    for g, edge in live_with_edge:
        mins = g['minutes_played']
        game_key = g.get('away', '') + "@" + g.get('home', '')

        if g.get('is_halftime'):
            status_label = "⏸️ HALFTIME"
            status_color = "#ff6b6b"
        elif mins < 8:
            status_label = "⏳ TOO EARLY"
            status_color = "#888"
        elif abs(edge['lead']) < 3:
            status_label = "⚖️ TOO CLOSE"
            status_color = "#ffa500"
        elif edge['score'] >= 70:
            status_label = "🟢 STRONG " + str(edge['score']) + "/100"
            status_color = "#22c55e"
        elif edge['score'] >= 60:
            status_label = "🟢 GOOD " + str(edge['score']) + "/100"
            status_color = "#22c55e"
        else:
            status_label = "🟡 " + str(edge['score']) + "/100"
            status_color = "#eab308"

        lead_display = ("+" + str(edge['lead'])) if edge['lead'] > 0 else str(edge['lead'])
        leader = g['home'] if edge['lead'] > 0 else g['away'] if edge['lead'] < 0 else "TIED"

        safe_no = edge['proj_total'] + 6
        safe_yes = edge['proj_total'] - 4

        period_display = "HALF" if g.get('is_halftime') else "Q" + str(g['period'])

        # SCOREBOARD
        st.markdown('<div style="background:linear-gradient(135deg,#1e1e2e 0%,#2a2a3e 100%);border-radius:12px;padding:16px;margin-bottom:4px;border:1px solid #444"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px"><span style="color:#fff;font-size:1.1em;font-weight:600">' + str(g.get('away','')) + ' @ ' + str(g.get('home','')) + '</span><span style="color:#ff6b6b;font-size:0.9em">' + period_display + ' ' + str(g.get('clock','')) + '</span></div><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px"><span style="color:#fff;font-size:1.4em;font-weight:700">' + str(g.get('away_score',0)) + ' - ' + str(g.get('home_score',0)) + '</span><span style="color:' + status_color + ';font-weight:600">' + status_label + '</span></div><div style="color:#aaa;font-size:0.9em">Edge: <strong style="color:#fff">' + leader + '</strong> (' + lead_display + ') ' + str(edge.get('pace_label','')) + '</div></div>', unsafe_allow_html=True)

        # FOOTBALL FIELD + PLAY-BY-PLAY (two columns)
        col_field, col_plays = st.columns([3, 2])

        with col_field:
            ball_yard, display_mode, poss_team, status_text = get_smart_ball_position(
                poss_text=g.get('poss_text'), possession_team=g.get('possession_team'),
                yards_to_endzone=g.get('yards_to_endzone'), is_home_possession=g.get('is_home_possession'),
                last_play=g.get('last_play'), period=g['period'], clock=g['clock'],
                home_team=g['home'], away_team=g['away'], game_key=game_key,
                home_abbrev=g.get('home_abbrev', g['home']), away_abbrev=g.get('away_abbrev', g['away'])
            )
            field_html = render_football_field(
                ball_yard=ball_yard, down=g.get('down'), distance=g.get('distance'),
                possession_team=poss_team or g.get('possession_team'),
                away_team=g['away'], home_team=g['home'],
                yards_to_endzone=g.get('yards_to_endzone'),
                poss_text=status_text if display_mode != "normal" else g.get('poss_text'),
                display_mode=display_mode, last_play=g.get('last_play')
            )
            st.markdown(field_html, unsafe_allow_html=True)

            # Last play text
            lp = g.get('last_play', {})
            if lp and lp.get('text'):
                pt = str(lp.get('text', ''))[:120]
                st.markdown('<div style="background:#0a0a15;padding:8px 12px;border-radius:6px;margin-bottom:8px;border-left:3px solid #444"><span style="color:#888;font-size:0.85em">📺 ' + pt + '</span></div>', unsafe_allow_html=True)

        with col_plays:
            st.markdown("**📋 Last 10 Plays**")
            plays = fetch_play_by_play(g.get('event_id'))
            if plays:
                for play in reversed(plays):
                    icon, color = get_play_icon(play.get('text', ''))
                    p_text = play.get('text', '')[:100]
                    p_time = "Q" + str(play.get('period', '')) + " " + str(play.get('clock', ''))
                    scoring_badge = ' <span style="color:#ffd700;font-weight:bold">★</span>' if play.get('scoring') else ''
                    st.markdown('<div style="background:#0f0f1a;padding:6px 8px;border-radius:4px;margin-bottom:3px;border-left:3px solid ' + color + '"><span style="font-size:0.8em"><span style="color:' + color + '">' + icon + '</span> <span style="color:#666">' + p_time + '</span> <span style="color:#ccc">' + p_text + '</span>' + scoring_badge + '</span></div>', unsafe_allow_html=True)
            else:
                st.caption("No play data yet")

        # Totals projection
        st.markdown('<div style="background:#333;border-radius:8px;padding:10px;margin-bottom:8px"><span style="color:#888">Proj: ' + str(edge['proj_total']) + '</span> | <span style="color:#22c55e">NO ' + str(safe_no) + '</span> | <span style="color:#f97316">YES ' + str(safe_yes) + '</span></div>', unsafe_allow_html=True)

        bc1, bc2, bc3 = st.columns(3)
        with bc1:
            st.link_button("🎯 " + str(edge['pick']) + " ML", get_kalshi_link(), use_container_width=True)
        with bc2:
            st.link_button("⬇️ NO " + str(safe_no), get_kalshi_link(), use_container_width=True)
        with bc3:
            st.link_button("⬆️ YES " + str(safe_yes), get_kalshi_link(), use_container_width=True)
        st.markdown("---")
else:
    st.info("🕐 No live games right now. NFL games typically on Sun/Mon/Thu.")

st.divider()

# ============================================================
# 🎯 CUSHION SCANNER
# ============================================================
st.subheader("🎯 CUSHION SCANNER")
st.caption("Find safe NO/YES totals in live games")

cs1, cs2 = st.columns([1, 1])
cush_min = cs1.selectbox("Min minutes", [8, 15, 20, 30], index=0, key="cush_min")
cush_side = cs2.selectbox("Side", ["NO", "YES"], key="cush_side")

cush_results = []
for g in live_games:
    mins = g['minutes_played']
    total = g['total_score']
    if mins < cush_min or mins <= 0:
        continue
    pace = total / mins
    remaining_min = max(60 - mins, 1)
    projected_final = round(total + pace * remaining_min)

    if cush_side == "NO":
        base_idx = next((i for i, t in enumerate(THRESHOLDS) if t > projected_final), len(THRESHOLDS) - 1)
        safe_idx = min(base_idx + 1, len(THRESHOLDS) - 1)
        safe_line = THRESHOLDS[safe_idx]
        cushion = safe_line - projected_final
    else:
        base_idx = next((i for i in range(len(THRESHOLDS) - 1, -1, -1) if THRESHOLDS[i] < projected_final), 0)
        safe_idx = max(base_idx - 1, 0)
        safe_line = THRESHOLDS[safe_idx]
        cushion = projected_final - safe_line

    if cushion < 4:
        continue

    if cush_side == "NO":
        if pace < 0.7: pace_status, pace_color = "✅ SLOW", "#00ff00"
        elif pace < 0.85: pace_status, pace_color = "⚠️ AVG", "#ffff00"
        else: pace_status, pace_color = "❌ FAST", "#ff0000"
    else:
        if pace > 1.0: pace_status, pace_color = "✅ FAST", "#00ff00"
        elif pace > 0.85: pace_status, pace_color = "⚠️ AVG", "#ffff00"
        else: pace_status, pace_color = "❌ SLOW", "#ff0000"

    cush_results.append({
        'away': g['away'], 'home': g['home'], 'total': total, 'mins': mins,
        'pace': pace, 'pace_status': pace_status, 'pace_color': pace_color,
        'projected': projected_final, 'cushion': cushion, 'safe_line': safe_line,
        'period': g['period'], 'clock': g['clock']
    })

cush_results.sort(key=lambda x: x['cushion'], reverse=True)

if cush_results:
    for r in cush_results:
        st.markdown('<div style="background:#0f172a;padding:10px 14px;margin-bottom:6px;border-radius:8px;border-left:3px solid ' + r['pace_color'] + '"><b style="color:#fff">' + r['away'] + ' @ ' + r['home'] + '</b> <span style="color:#888">Q' + str(r['period']) + ' ' + str(r['clock']) + ' • ' + str(r['total']) + 'pts/' + str(int(r['mins'])) + 'min</span> <span style="color:#888">Proj: <b style="color:#fff">' + str(r['projected']) + '</b></span> <span style="background:#ff8800;color:#000;padding:2px 8px;border-radius:4px;font-weight:bold;margin-left:8px">🎯 ' + str(r['safe_line']) + '</span> <span style="color:#00ff00;font-weight:bold;margin-left:8px">+' + str(int(r['cushion'])) + '</span> <span style="color:' + r['pace_color'] + ';margin-left:8px">' + r['pace_status'] + '</span></div>', unsafe_allow_html=True)
        st.link_button("BUY " + cush_side + " " + str(r['safe_line']), get_kalshi_link(), use_container_width=True)
else:
    st.info("No " + cush_side + " opportunities with 4+ cushion yet")

st.divider()

# ============================================================
# 🔥 PACE SCANNER
# ============================================================
st.subheader("🔥 PACE SCANNER")
st.caption("Track scoring pace for live games")

pace_data = []
for g in live_games:
    mins = g['minutes_played']
    if mins >= 8:
        pace = round(g['total_score'] / mins, 2)
        pace_data.append({
            "away": g['away'], "home": g['home'], "pace": pace,
            "proj": round(pace * 60), "total": g['total_score'], "mins": mins,
            "period": g['period'], "clock": g['clock']
        })
pace_data.sort(key=lambda x: x['pace'])

if pace_data:
    for p in pace_data:
        if p['pace'] < 0.7:
            lbl, clr = "🐢 SLOW", "#00ff00"
            rec_side = "NO"
            idx = min(next((i for i, t in enumerate(THRESHOLDS) if t > p['proj']), len(THRESHOLDS) - 1) + 1, len(THRESHOLDS) - 1)
            rec_line = THRESHOLDS[idx]
        elif p['pace'] < 0.85:
            lbl, clr = "⚖️ AVG", "#ffff00"
            rec_side, rec_line = None, None
        elif p['pace'] < 1.0:
            lbl, clr = "🔥 FAST", "#ff8800"
            rec_side = "YES"
            idx = max(next((i for i in range(len(THRESHOLDS) - 1, -1, -1) if THRESHOLDS[i] < p['proj']), 0) - 1, 0)
            rec_line = THRESHOLDS[idx]
        else:
            lbl, clr = "🚀 SHOOTOUT", "#ff0000"
            rec_side = "YES"
            idx = max(next((i for i in range(len(THRESHOLDS) - 1, -1, -1) if THRESHOLDS[i] < p['proj']), 0) - 1, 0)
            rec_line = THRESHOLDS[idx]

        st.markdown('<div style="background:#0f172a;padding:8px 12px;margin-bottom:4px;border-radius:6px;border-left:3px solid ' + clr + '"><b style="color:#fff">' + p['away'] + ' @ ' + p['home'] + '</b> <span style="color:#666;margin-left:10px">Q' + str(p['period']) + ' ' + str(p['clock']) + '</span> <span style="color:#888;margin-left:10px">' + str(p['total']) + 'pts/' + str(int(p['mins'])) + 'min</span> <span style="color:' + clr + ';font-weight:bold;margin-left:10px">' + str(p['pace']) + '/min ' + lbl + '</span> <span style="color:#888;margin-left:10px">Proj: <b style="color:#fff">' + str(p['proj']) + '</b></span></div>', unsafe_allow_html=True)
        if rec_side and rec_line:
            st.link_button("BUY " + rec_side + " " + str(rec_line), get_kalshi_link(), use_container_width=True)
else:
    st.info("No games with 8+ minutes played yet")

st.divider()

# ============================================================
# 🎯 PRE-GAME ALIGNMENT
# ============================================================
if scheduled_games:
    st.subheader("🎯 PRE-GAME ALIGNMENT")
    st.markdown("*Look for **70+** scores with multiple factors.*")

    games_with_edge = []
    for g in scheduled_games:
        pick, score, factors = calc_pregame_edge(g['away'], g['home'], injuries)
        games_with_edge.append((g, pick, score, factors))
    games_with_edge.sort(key=lambda x: x[2], reverse=True)

    for g, pick, score, factors in games_with_edge:
        if score >= 70: sc, tier, bc = "#22c55e", "🟢 STRONG", "#22c55e"
        elif score >= 60: sc, tier, bc = "#22c55e", "🟢 GOOD", "#22c55e"
        elif score >= 50: sc, tier, bc = "#eab308", "🟡 MODERATE", "#eab308"
        else: sc, tier, bc = "#888", "⚪ WEAK", "#444"

        fac_str = ' • '.join(factors[:3]) if factors else 'No strong factors'
        st.markdown('<div style="background:#1e1e2e;border-radius:10px;padding:14px;margin-bottom:10px;border-left:4px solid ' + bc + '"><div style="display:flex;justify-content:space-between"><span style="color:#fff;font-weight:600">' + str(g['away']) + ' @ ' + str(g['home']) + '</span><span style="color:' + sc + ';font-weight:600">' + tier + ' ' + str(score) + '/100</span></div><div style="color:#888;font-size:0.85em;margin-top:4px">Edge: <strong style="color:#fff">' + pick + '</strong> • ' + fac_str + '</div></div>', unsafe_allow_html=True)
        st.link_button("🎯 BUY " + pick + " → Kalshi NFL", get_kalshi_link(), use_container_width=True)
        st.caption("Find: " + str(g['away']) + " @ " + str(g['home']))

st.divider()

# ============================================================
# 📖 HOW TO USE
# ============================================================
with st.expander("📖 HOW TO USE", expanded=False):
    st.markdown("""### Edge Score Guide
| Score | Label | Action |
|-------|-------|--------|
| **70+** | 🟢 STRONG | Best opportunities |
| **60-69** | 🟢 GOOD | Worth considering |
| **50-59** | 🟡 MODERATE | Wait for live |
| **<50** | ⚪ WEAK | Skip |

---
### 🏈 Football Field
- **Ball position** updates every 30 seconds
- **◄** = Team attacking LEFT (toward away endzone)
- **►** = Team attacking RIGHT (toward home endzone)
- **🔴 RED ZONE** = Inside opponent's 20 yard line

---
### Play Badges on Field
- 🏈 TOUCHDOWN (gold)
- ✓ COMPLETE (green)
- ✕ INCOMPLETE (red)
- 🔴 INTERCEPTED / FUMBLE (red)
- ⚠️ SACK (orange)
- 🏃 RUSH (blue)
- 📤 PUNT (gray)
- 🥅 FIELD GOAL (green)
- 🟡 PENALTY (yellow)

---
### Play-by-Play Icons
- 🏈 = Touchdown
- 🥅 = Field Goal
- 🎯 = Completed Pass
- 🏃 = Rush
- ✕ = Incomplete
- 🔴 = Turnover
- ⚠️ = Sack
- 📤 = Punt
- 🟡 = Penalty
- ★ = Scoring Play

---
### NFL Pace Guide
| Pace | Label | Action |
|------|-------|--------|
| <0.7 | 🐢 SLOW | Buy NO |
| 0.7-0.85 | ⚖️ AVG | Wait |
| 0.85-1.0 | 🔥 FAST | Buy YES |
| >1.0 | 🚀 SHOOTOUT | Buy YES |

---
⚠️ Edge Score ≠ Win Probability
⚠️ Only risk what you can afford to lose""")

st.caption("⚠️ Educational only. Not financial advice. v" + VERSION)
