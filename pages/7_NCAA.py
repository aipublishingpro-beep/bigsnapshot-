import streamlit as st
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="BigSnapshot NCAA Edge Finder", page_icon="🎓", layout="wide")

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

send_ga4_event("BigSnapshot NCAA Edge Finder", "/NCAA")

import requests
from datetime import datetime, timedelta
import pytz

eastern = pytz.timezone("US/Eastern")
now = datetime.now(eastern)

VERSION = "12.0"
LEAGUE_AVG_TOTAL = 145
THRESHOLDS = [120.5, 125.5, 130.5, 135.5, 140.5, 145.5, 150.5, 155.5, 160.5, 165.5, 170.5]

if 'positions' not in st.session_state:
    st.session_state.positions = []

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
}

POWER_CONFERENCES = {"SEC", "Big Ten", "Big 12", "ACC", "Big East"}
HIGH_MAJOR = {"American Athletic", "Mountain West", "Atlantic 10", "West Coast", "Missouri Valley"}

def american_to_implied_prob(odds):
    if odds is None: return None
    if odds > 0: return 100 / (odds + 100)
    else: return abs(odds) / (abs(odds) + 100)

@st.cache_data(ttl=30)
def fetch_espn_games():
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
            home_record, away_record = "", ""
            home_conf, away_conf = "", ""
            
            for c in competitors:
                team_data = c.get("team", {})
                full_name = team_data.get("displayName", team_data.get("name", ""))
                abbrev = team_data.get("abbreviation", full_name[:4]).upper()
                score = int(c.get("score", 0) or 0)
                records = c.get("records", [])
                record = records[0].get("summary", "") if records else ""
                conf = ""
                for rec in records:
                    if rec.get("type") == "conference":
                        conf = rec.get("name", "")
                        break
                
                if c.get("homeAway") == "home":
                    home_team, home_score, home_abbrev = full_name, score, abbrev
                    home_record, home_conf = record, conf
                else:
                    away_team, away_score, away_abbrev = full_name, score, abbrev
                    away_record, away_conf = record, conf
            
            status = event.get("status", {}).get("type", {}).get("name", "STATUS_SCHEDULED")
            period = event.get("status", {}).get("period", 0)
            clock = event.get("status", {}).get("displayClock", "")
            game_id = event.get("id", "")
            
            minutes_played = 0
            if period > 0:
                if period <= 2:
                    completed_halves = (period - 1) * 20
                    if clock:
                        try:
                            if ":" in clock:
                                mins_left = int(clock.split(":")[0])
                                minutes_played = completed_halves + (20 - mins_left)
                            elif clock == "0.0" or clock == "0":
                                minutes_played = completed_halves + 20
                            else:
                                minutes_played = completed_halves + 20
                        except:
                            minutes_played = completed_halves + 20
                    else:
                        minutes_played = completed_halves
                else:
                    minutes_played = 40 + (period - 2) * 5
            
            odds_data = comp.get("odds", [])
            vegas_odds = {}
            if odds_data and len(odds_data) > 0:
                odds = odds_data[0]
                vegas_odds = {"spread": odds.get("spread"), "overUnder": odds.get("overUnder"),
                    "homeML": odds.get("homeTeamOdds", {}).get("moneyLine"),
                    "awayML": odds.get("awayTeamOdds", {}).get("moneyLine")}
            
            game_date = event.get("date", "")
            game_time_str = ""
            game_datetime_str = ""
            if game_date:
                try:
                    game_dt = datetime.fromisoformat(game_date.replace("Z", "+00:00"))
                    game_dt_eastern = game_dt.astimezone(eastern)
                    game_time_str = game_dt_eastern.strftime("%I:%M %p ET")
                    game_datetime_str = game_dt_eastern.strftime("%b %d, %I:%M %p ET")
                except:
                    game_time_str = ""
                    game_datetime_str = ""
            
            games.append({
                "away": away_team, "home": home_team,
                "away_abbrev": away_abbrev, "home_abbrev": home_abbrev,
                "away_score": away_score, "home_score": home_score,
                "away_record": away_record, "home_record": home_record,
                "away_conf": away_conf, "home_conf": home_conf,
                "status": status, "period": period, "clock": clock,
                "minutes_played": minutes_played,
                "total_score": home_score + away_score,
                "game_id": game_id, "vegas_odds": vegas_odds,
                "game_time": game_time_str,
                "game_datetime": game_datetime_str
            })
        return games
    except Exception as e:
        st.error("ESPN fetch error: " + str(e))
        return []

@st.cache_data(ttl=60)
def fetch_kalshi_ml():
    url = "https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXNCAAMBGAME&status=open&limit=200"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        markets = {}
        for m in data.get("markets", []):
            ticker = m.get("ticker", "")
            if "KXNCAAMBGAME-" not in ticker: continue
            yes_bid, yes_ask = m.get("yes_bid", 0) or 0, m.get("yes_ask", 0) or 0
            yes_price = yes_ask if yes_ask > 0 else (yes_bid if yes_bid > 0 else 50)
            markets[ticker] = {"ticker": ticker, "yes_bid": yes_bid, "yes_ask": yes_ask, "yes_price": yes_price}
        return markets
    except Exception as e:
        st.error("Kalshi ML fetch error: " + str(e))
        return {}

@st.cache_data(ttl=300)
def fetch_yesterday_teams():
    yesterday = (datetime.now(eastern) - timedelta(days=1)).strftime('%Y%m%d')
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard?dates={yesterday}&limit=100"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        teams_played = set()
        for event in data.get("events", []):
            comp = event.get("competitions", [{}])[0]
            for c in comp.get("competitors", []):
                abbrev = c.get("team", {}).get("abbreviation", "").upper()
                teams_played.add(abbrev)
        return teams_played
    except:
        return set()

@st.cache_data(ttl=25)
def fetch_plays_and_linescores(game_id, known_away="", known_home=""):
    """Fetch plays AND period-by-period scoring - NCAA v12.0 ENHANCED"""
    if not game_id: 
        return [], "", {}, []
    
    try:
        url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/summary?event={game_id}"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        
        # Get plays (existing code - keep as is)
        all_plays = data.get("plays", [])
        plays = []
        for p in all_plays[-15:]:
            team_data = p.get("team", {})
            team_abbrev = ""
            if isinstance(team_data, dict):
                team_abbrev = team_data.get("abbreviation", "") or team_data.get("displayName", "")
            plays.append({
                "text": p.get("text", ""),
                "period": p.get("period", {}).get("number", 0),
                "clock": p.get("clock", {}).get("displayValue", ""),
                "score_value": p.get("scoreValue", 0),
                "play_type": p.get("type", {}).get("text", ""),
                "team": team_abbrev.upper() if team_abbrev else ""
            })
        
        # Get possession (existing code - keep as is)
        poss_team = ""
        situation = data.get("situation", {})
        if situation:
            poss_text = situation.get("possessionText", "") or ""
            poss_team = poss_text.split()[0] if poss_text else ""
        
        # Get records (existing code - keep as is)
        half_scores = {"away_record": "", "home_record": ""}
        header = data.get("header", {})
        competitions = header.get("competitions", [{}])
        if competitions:
            for comp in competitions[0].get("competitors", []):
                record = comp.get("record", [{}])
                record_str = record[0].get("summary", "") if record else ""
                if comp.get("homeAway") == "home":
                    half_scores["home_record"] = record_str
                else:
                    half_scores["away_record"] = record_str
        
        # **NEW: DUAL-PATH period score fetching**
        linescores = []
        away_line = []
        home_line = []
        
        # PATH 1: boxscore.teams[].statistics[] - MOST RELIABLE
        box_score = data.get("boxscore", {})
        teams = box_score.get("teams", [])
        
        for team in teams:
            team_ha = team.get("homeAway", "")
            team_stats = team.get("statistics", [])
            
            for stat_group in team_stats:
                if stat_group.get("name") == "linescores":
                    line = []
                    for period_stat in stat_group.get("stats", []):
                        try:
                            val = period_stat.get("value", 0)
                            line.append(int(float(val)) if val else 0)
                        except:
                            line.append(0)
                    
                    if team_ha == "home":
                        home_line = line
                    else:
                        away_line = line
                    break
        
        # PATH 2: header.competitions[].competitors[].linescores[] - BACKUP
        if not away_line and not home_line and competitions:
            for comp in competitions[0].get("competitors", []):
                comp_linescores = comp.get("linescores", [])
                if comp_linescores:
                    line = []
                    for ls in comp_linescores:
                        try:
                            val = ls.get("value", 0)
                            line.append(int(float(val)) if val else 0)
                        except:
                            line.append(0)
                    
                    if comp.get("homeAway") == "home":
                        home_line = line
                    else:
                        away_line = line
        
        # Build linescores array
        max_periods = max(len(away_line), len(home_line))
        if max_periods > 0:
            for i in range(max_periods):
                period_name = f"H{i+1}" if i < 2 else f"OT{i-1}"
                away_pts = away_line[i] if i < len(away_line) else 0
                home_pts = home_line[i] if i < len(home_line) else 0
                linescores.append({
                    "period": period_name,
                    "away": away_pts,
                    "home": home_pts
                })
        
        return plays[-10:], poss_team, half_scores, linescores
        
    except Exception as e:
        return [], "", {}, []

def render_scoreboard_ncaa(away_abbrev, home_abbrev, away_score, home_score, period, clock, half_scores, linescores):
    """Render scoreboard with half-by-half breakdown - NCAA v12.0"""
    away_color = TEAM_COLORS.get(away_abbrev, "#666")
    home_color = TEAM_COLORS.get(home_abbrev, "#666")
    away_record = half_scores.get("away_record", "")
    home_record = half_scores.get("home_record", "")
    period_text = f"H{period}" if period <= 2 else f"OT{period-2}"
    
    # FALLBACK: No period scores available
    if not linescores or len(linescores) == 0:
        return f'''<div style="background:#0f172a;border-radius:12px;padding:20px;margin-bottom:8px">
        <div style="text-align:center;color:#ffd700;font-weight:bold;font-size:22px;margin-bottom:16px">{period_text} - {clock}</div>
        <table style="width:100%;border-collapse:collapse;color:#fff">
        <tr style="border-bottom:2px solid #333">
            <td style="padding:16px;text-align:left;width:70%">
                <span style="color:{away_color};font-weight:bold;font-size:28px">{away_abbrev}</span>
                <span style="color:#666;font-size:14px;margin-left:12px">{away_record}</span>
            </td>
            <td style="padding:16px;text-align:right;font-weight:bold;font-size:52px;color:#fff">{away_score}</td>
        </tr>
        <tr>
            <td style="padding:16px;text-align:left;width:70%">
                <span style="color:{home_color};font-weight:bold;font-size:28px">{home_abbrev}</span>
                <span style="color:#666;font-size:14px;margin-left:12px">{home_record}</span>
            </td>
            <td style="padding:16px;text-align:right;font-weight:bold;font-size:52px;color:#fff">{home_score}</td>
        </tr>
        </table>
        <div style="text-align:center;color:#888;font-size:12px;margin-top:12px">⏳ Period scores loading...</div>
        </div>'''
    
    # Build period headers and scores
    period_headers = ""
    away_period_scores = ""
    home_period_scores = ""
    
    for ls in linescores:
        period_headers += f'<th style="padding:8px;text-align:center;color:#888;font-size:14px">{ls["period"]}</th>'
        away_period_scores += f'<td style="padding:8px;text-align:center;color:#fff;font-size:18px;font-weight:bold">{ls["away"]}</td>'
        home_period_scores += f'<td style="padding:8px;text-align:center;color:#fff;font-size:18px;font-weight:bold">{ls["home"]}</td>'
    
    # Full scoreboard with H1, H2, OT breakdown
    return f'''<div style="background:#0f172a;border-radius:12px;padding:20px;margin-bottom:8px">
    <div style="text-align:center;color:#ffd700;font-weight:bold;font-size:22px;margin-bottom:16px">{period_text} - {clock}</div>
    <table style="width:100%;border-collapse:collapse;color:#fff">
    <thead>
        <tr style="border-bottom:1px solid #333">
            <th style="padding:8px;text-align:left;width:35%;color:#888;font-size:14px">TEAM</th>
            {period_headers}
            <th style="padding:8px;text-align:center;color:#ffd700;font-size:16px;font-weight:bold">TOTAL</th>
        </tr>
    </thead>
    <tbody>
    <tr style="border-bottom:2px solid #333">
        <td style="padding:16px;text-align:left">
            <span style="color:{away_color};font-weight:bold;font-size:24px">{away_abbrev}</span>
            <span style="color:#666;font-size:12px;margin-left:8px">{away_record}</span>
        </td>
        {away_period_scores}
        <td style="padding:16px;text-align:center;font-weight:bold;font-size:42px;color:#fff">{away_score}</td>
    </tr>
    <tr>
        <td style="padding:16px;text-align:left">
            <span style="color:{home_color};font-weight:bold;font-size:24px">{home_abbrev}</span>
            <span style="color:#666;font-size:12px;margin-left:8px">{home_record}</span>
        </td>
        {home_period_scores}
        <td style="padding:16px;text-align:center;font-weight:bold;font-size:42px;color:#fff">{home_score}</td>
    </tr>
    </tbody>
    </table></div>'''

def render_ncaa_court(away_abbrev, home_abbrev, away_score, home_score, possession, period, clock):
    away_color = TEAM_COLORS.get(away_abbrev, "#666666")
    home_color = TEAM_COLORS.get(home_abbrev, "#666666")
    poss_away = "visible" if possession == away_abbrev else "hidden"
    poss_home = "visible" if possession == home_abbrev else "hidden"
    period_text = f"H{period}" if period <= 2 else f"OT{period-2}"
    
    svg = f'''<div style="background:#1a1a2e;border-radius:12px;padding:10px;">
<svg viewBox="0 0 500 280" style="width:100%;max-width:500px;">
<rect x="20" y="20" width="460" height="200" fill="#2d4a22" stroke="#fff" stroke-width="2" rx="8"/>
<circle cx="250" cy="120" r="35" fill="none" stroke="#fff" stroke-width="2"/>
<circle cx="250" cy="120" r="4" fill="#fff"/>
<line x1="250" y1="20" x2="250" y2="220" stroke="#fff" stroke-width="2"/>
<path d="M 20 50 Q 100 120 20 190" fill="none" stroke="#fff" stroke-width="2"/>
<rect x="20" y="70" width="70" height="100" fill="none" stroke="#fff" stroke-width="2"/>
<circle cx="90" cy="120" r="25" fill="none" stroke="#fff" stroke-width="2"/>
<circle cx="35" cy="120" r="8" fill="none" stroke="#ff6b35" stroke-width="3"/>
<path d="M 480 50 Q 400 120 480 190" fill="none" stroke="#fff" stroke-width="2"/>
<rect x="410" y="70" width="70" height="100" fill="none" stroke="#fff" stroke-width="2"/>
<circle cx="410" cy="120" r="25" fill="none" stroke="#fff" stroke-width="2"/>
<circle cx="465" cy="120" r="8" fill="none" stroke="#ff6b35" stroke-width="3"/>
<rect x="40" y="228" width="90" height="48" fill="{away_color}" rx="6"/>
<text x="85" y="250" fill="#fff" font-size="12" font-weight="bold" text-anchor="middle">{away_abbrev[:6]}</text>
<text x="85" y="270" fill="#fff" font-size="18" font-weight="bold" text-anchor="middle">{away_score}</text>
<circle cx="135" cy="252" r="8" fill="#ffd700" visibility="{poss_away}"/>
<rect x="370" y="228" width="90" height="48" fill="{home_color}" rx="6"/>
<text x="415" y="250" fill="#fff" font-size="12" font-weight="bold" text-anchor="middle">{home_abbrev[:6]}</text>
<text x="415" y="270" fill="#fff" font-size="18" font-weight="bold" text-anchor="middle">{home_score}</text>
<circle cx="365" cy="252" r="8" fill="#ffd700" visibility="{poss_home}"/>
<text x="250" y="258" fill="#fff" font-size="16" font-weight="bold" text-anchor="middle">{period_text} {clock}</text>
</svg>
</div>'''
    return svg

def get_play_icon(play_type, score_value):
    play_lower = play_type.lower() if play_type else ""
    if score_value > 0 or "made" in play_lower: return "🏀", "#22c55e"
    elif "miss" in play_lower or "block" in play_lower: return "❌", "#ef4444"
    elif "rebound" in play_lower: return "📥", "#3b82f6"
    elif "turnover" in play_lower or "steal" in play_lower: return "🔄", "#f97316"
    elif "foul" in play_lower: return "🚨", "#eab308"
    elif "timeout" in play_lower: return "⏸️", "#a855f7"
    return "•", "#888"

def get_kalshi_game_link(away_abbrev, home_abbrev):
    t1 = ''.join(c for c in str(away_abbrev).upper() if c.isalpha())[:4]
    t2 = ''.join(c for c in str(home_abbrev).upper() if c.isalpha())[:4]
    date_str = datetime.now(eastern).strftime('%y%b%d').upper()
    ticker = f"KXNCAAMBGAME-{date_str}{t1}{t2}"
    return f"https://kalshi.com/markets/kxncaambgame/mens-college-basketball-mens-game/{ticker.lower()}"

def calc_projection(total_score, minutes_played):
    if minutes_played >= 5:
        pace = total_score / minutes_played
        weight = min(1.0, (minutes_played - 5) / 15)
        blended_pace = (pace * weight) + ((LEAGUE_AVG_TOTAL / 40) * (1 - weight))
        return max(100, min(200, round(blended_pace * 40)))
    return LEAGUE_AVG_TOTAL

def get_pace_label(pace):
    if pace < 3.2: return "🐢 SLOW", "#22c55e"
    elif pace < 3.5: return "⚖️ AVG", "#eab308"
    elif pace < 3.8: return "🔥 FAST", "#f97316"
    return "💥 SHOOTOUT", "#ef4444"

def get_conference_tier(conf_name):
    if not conf_name: return 3
    if any(p in conf_name for p in POWER_CONFERENCES): return 1
    if any(h in conf_name for h in HIGH_MAJOR): return 2
    return 3

def calc_pregame_edge(g, b2b_teams):
    away_abbrev, home_abbrev = g['away_abbrev'], g['home_abbrev']
    away_conf, home_conf = g.get('away_conf', ''), g.get('home_conf', '')
    away_record, home_record = g.get('away_record', ''), g.get('home_record', '')
    
    score = 50
    score += 3
    
    home_tier = get_conference_tier(home_conf)
    away_tier = get_conference_tier(away_conf)
    if home_tier < away_tier: score += 5
    elif away_tier < home_tier: score -= 5
    
    try:
        h_wins, h_losses = map(int, home_record.split("-")[:2]) if home_record else (0, 0)
        a_wins, a_losses = map(int, away_record.split("-")[:2]) if away_record else (0, 0)
        h_pct = h_wins / (h_wins + h_losses) if (h_wins + h_losses) > 0 else 0.5
        a_pct = a_wins / (a_wins + a_losses) if (a_wins + a_losses) > 0 else 0.5
        score += (h_pct - a_pct) * 20
    except: pass
    
    if away_abbrev in b2b_teams: score += 4
    if home_abbrev in b2b_teams: score -= 4
    
    return max(0, min(100, round(score)))

def remove_position(pos_id):
    st.session_state.positions = [p for p in st.session_state.positions if p['id'] != pos_id]

# ============================================================
# FETCH DATA
# ============================================================
games = fetch_espn_games()
kalshi_ml = fetch_kalshi_ml()
b2b_teams = fetch_yesterday_teams()

live_games = [g for g in games if g['status'] in ['STATUS_IN_PROGRESS', 'STATUS_HALFTIME', 'STATUS_END_PERIOD'] or (g['period'] > 0 and g['status'] not in ['STATUS_FINAL', 'STATUS_FULL_TIME'])]
scheduled_games = [g for g in games if g['status'] == 'STATUS_SCHEDULED' and g['period'] == 0]
final_games = [g for g in games if g['status'] in ['STATUS_FINAL', 'STATUS_FULL_TIME']]

# ============================================================
# HEADER
# ============================================================
st.title("🎓 BIGSNAPSHOT NCAA EDGE FINDER")
st.caption(f"v{VERSION} • {now.strftime('%b %d, %Y %I:%M %p ET')} • College Basketball Edge Detector")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Today's Games", len(games))
c2.metric("Live Now", len(live_games))
c3.metric("Scheduled", len(scheduled_games))
c4.metric("Final", len(final_games))

st.divider()

# ============================================================
# VEGAS vs KALSHI MISPRICING ALERT
# ============================================================
st.subheader("💰 VEGAS vs KALSHI MISPRICING ALERT")
st.caption("Buy when Kalshi underprices Vegas favorite • 5%+ gap = edge")

mispricings = []
for g in games:
    if g['status'] in ['STATUS_FINAL', 'STATUS_FULL_TIME']: continue
    away_abbrev, home_abbrev = g['away_abbrev'], g['home_abbrev']
    vegas = g.get('vegas_odds', {})
    
    home_ml, away_ml, spread = vegas.get('homeML'), vegas.get('awayML'), vegas.get('spread')
    if home_ml and away_ml:
        vegas_home_prob = american_to_implied_prob(home_ml) * 100
        vegas_away_prob = american_to_implied_prob(away_ml) * 100
        total = vegas_home_prob + vegas_away_prob
        vegas_home_prob, vegas_away_prob = vegas_home_prob / total * 100, vegas_away_prob / total * 100
    elif spread:
        try:
            vegas_home_prob = max(10, min(90, 50 - (float(spread) * 2.8)))
            vegas_away_prob = 100 - vegas_home_prob
        except: continue
    else: continue
    
    edge_score = calc_pregame_edge(g, b2b_teams)
    kalshi_home_prob = edge_score
    kalshi_away_prob = 100 - edge_score
    
    home_edge = vegas_home_prob - kalshi_home_prob
    away_edge = vegas_away_prob - kalshi_away_prob
    
    if home_edge >= 5 or away_edge >= 5:
        if home_edge >= away_edge:
            team, team_abbrev = g['home'], home_abbrev
            vegas_prob, kalshi_prob, edge = vegas_home_prob, kalshi_home_prob, home_edge
            action = "YES"
        else:
            team, team_abbrev = g['away'], away_abbrev
            vegas_prob, kalshi_prob, edge = vegas_away_prob, kalshi_away_prob, away_edge
            action = "YES"
        mispricings.append({'game': g, 'team': team, 'team_abbrev': team_abbrev,
            'vegas_prob': vegas_prob, 'kalshi_prob': kalshi_prob, 'edge': edge, 'action': action})

mispricings.sort(key=lambda x: x['edge'], reverse=True)

if mispricings:
    mp_col1, mp_col2 = st.columns([3, 1])
    with mp_col1:
        st.success(f"🔥 {len(mispricings)} mispricing opportunities found!")
    with mp_col2:
        if st.button(f"➕ ADD ALL ({len(mispricings)})", key="add_all_mispricing", use_container_width=True):
            added = 0
            for mp in mispricings:
                g = mp['game']
                game_key = f"{g['away_abbrev']}@{g['home_abbrev']}"
                if not any(pos['game'] == game_key for pos in st.session_state.positions):
                    st.session_state.positions.append({"game": game_key, "pick": f"{mp['action']} ({mp['team_abbrev']})",
                        "type": "ML", "line": "-", "price": round(mp['kalshi_prob']), "contracts": 10,
                        "link": get_kalshi_game_link(g['away_abbrev'], g['home_abbrev']), "id": str(uuid.uuid4())[:8]})
                    added += 1
            st.toast(f"✅ Added {added} positions!")
            st.rerun()
    
    for mp in mispricings[:10]:
        g = mp['game']
        game_key = f"{g['away_abbrev']}@{g['home_abbrev']}"
        edge_color = "#ff6b6b" if mp['edge'] >= 10 else ("#22c55e" if mp['edge'] >= 7 else "#eab308")
        edge_label = "🔥 STRONG" if mp['edge'] >= 10 else ("🟢 GOOD" if mp['edge'] >= 7 else "🟡 EDGE")
        action_color = "#22c55e"
        status_text = f"H{g['period']} {g['clock']}" if g['period'] > 0 else (g.get('game_datetime', 'Scheduled') or 'Scheduled')
        
        col1, col2 = st.columns([3, 1])
        with col1: st.markdown(f"**{g['away_abbrev']} @ {g['home_abbrev']}** • {status_text}")
        with col2: st.markdown(f"<span style='color:{edge_color};font-weight:bold'>{edge_label} +{round(mp['edge'])}%</span>", unsafe_allow_html=True)
        
        st.markdown(f"""<div style="background:#0f172a;padding:16px;border-radius:10px;border:2px solid {edge_color};margin-bottom:12px">
<div style="font-size:1.4em;font-weight:bold;color:#fff;margin-bottom:8px">🎯 BUY <span style="color:{action_color};background:{action_color}22;padding:4px 12px;border-radius:6px">{mp['action']}</span> on Kalshi</div>
<div style="color:#aaa;margin-bottom:12px">{mp['action']} = {mp['team_abbrev']} wins</div>
<table style="width:100%;text-align:center;color:#fff"><tr style="color:#888"><td>Vegas</td><td>Model</td><td>EDGE</td></tr>
<tr style="font-size:1.3em;font-weight:bold"><td>{round(mp['vegas_prob'])}%</td><td>{round(mp['kalshi_prob'])}%</td><td style="color:{edge_color}">+{round(mp['edge'])}%</td></tr></table></div>""", unsafe_allow_html=True)
        
        bc1, bc2 = st.columns(2)
        with bc1: st.link_button(f"🎯 BUY {mp['action']} ({mp['team_abbrev']})", get_kalshi_game_link(g['away_abbrev'], g['home_abbrev']), use_container_width=True)
        with bc2:
            already = any(pos['game'] == game_key for pos in st.session_state.positions)
            if already: st.success("✅ Tracked")
            elif st.button("➕ Track", key=f"mp_{game_key}"):
                st.session_state.positions.append({"game": game_key, "pick": f"{mp['action']} ({mp['team_abbrev']})", "type": "ML",
                    "line": "-", "price": round(mp['kalshi_prob']), "contracts": 10,
                    "link": get_kalshi_game_link(g['away_abbrev'], g['home_abbrev']), "id": str(uuid.uuid4())[:8]})
                st.rerun()
else:
    st.info("🔍 No mispricings found (need 5%+ gap between Vegas & Model)")

st.divider()

# ============================================================
# LIVE EDGE MONITOR
# ============================================================
st.subheader("🎮 LIVE EDGE MONITOR")

if live_games:
    for g in live_games:
        away_abbrev, home_abbrev = g['away_abbrev'], g['home_abbrev']
        total, mins, game_id = g['total_score'], g['minutes_played'], g['game_id']
        plays, poss_team, half_scores, linescores = fetch_plays_and_linescores(game_id, away_abbrev, home_abbrev)
        
        st.markdown(f"### {g['away']} @ {g['home']}")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown(render_scoreboard_ncaa(away_abbrev, home_abbrev, g['away_score'], g['home_score'], g['period'], g['clock'], half_scores, linescores), unsafe_allow_html=True)
        
        with col2:
            st.markdown("**📋 LAST 10 PLAYS**")
            if plays:
                for p in reversed(plays):
                    icon, color = get_play_icon(p['play_type'], p['score_value'])
                    play_text = p['text'][:60] if p['text'] else "Play"
                    period_label = f"H{p['period']}" if p['period'] <= 2 else f"OT{p['period']-2}"
                    st.markdown(f"<div style='padding:4px 8px;margin:2px 0;background:#1e1e2e;border-radius:4px;border-left:3px solid {color}'><span style='color:{color}'>{icon}</span> {period_label} {p['clock']} • {play_text}</div>", unsafe_allow_html=True)
            else:
                st.caption("Waiting for plays...")
        
        if mins >= 5:
            proj = calc_projection(total, mins)
            pace = total / mins if mins > 0 else 0
            pace_label, pace_color = get_pace_label(pace)
            lead = g['home_score'] - g['away_score']
            leader = home_abbrev if g['home_score'] > g['away_score'] else away_abbrev
            kalshi_link = get_kalshi_game_link(away_abbrev, home_abbrev)
            
            st.markdown(f"<div style='background:#1e1e2e;padding:12px;border-radius:8px;margin-top:8px'><b>Score:</b> {total} pts in {mins} min • <b>Pace:</b> <span style='color:{pace_color}'>{pace_label}</span> ({pace:.1f}/min)<br><b>Projection:</b> {proj} pts • <b>Lead:</b> {leader} +{abs(lead)}</div>", unsafe_allow_html=True)
            
            st.markdown("**🎯 MONEYLINE**")
            if abs(lead) >= 8:
                ml_pick = leader
                ml_confidence = "🔥 STRONG" if abs(lead) >= 12 else "🟢 GOOD"
                st.link_button(f"{ml_confidence} BUY YES ({ml_pick} ML) • Lead +{abs(lead)}", kalshi_link, use_container_width=True)
            else:
                st.caption(f"⏳ Wait for larger lead (currently {leader} +{abs(lead)})")
            
            st.markdown("**📊 TOTALS**")
            
            yes_lines = [(t, proj - t) for t in sorted(THRESHOLDS) if proj - t >= 6]
            no_lines = [(t, t - proj) for t in sorted(THRESHOLDS, reverse=True) if t - proj >= 6]
            
            tc1, tc2 = st.columns(2)
            with tc1:
                st.markdown("<span style='color:#22c55e;font-weight:bold'>🟢 YES (Over)</span>", unsafe_allow_html=True)
                if yes_lines:
                    for line, cushion in yes_lines[:3]:
                        safety = "🔥" if cushion >= 15 else ("✅" if cushion >= 10 else "🟡")
                        st.link_button(f"{safety} YES {line} (+{int(cushion)} cushion)", kalshi_link, use_container_width=True)
                else:
                    st.caption("No safe YES lines (need 6+ cushion)")
            
            with tc2:
                st.markdown("<span style='color:#ef4444;font-weight:bold'>🔴 NO (Under)</span>", unsafe_allow_html=True)
                if no_lines:
                    for line, cushion in no_lines[:3]:
                        safety = "🔥" if cushion >= 15 else ("✅" if cushion >= 10 else "🟡")
                        st.link_button(f"{safety} NO {line} (+{int(cushion)} cushion)", kalshi_link, use_container_width=True)
                else:
                    st.caption("No safe NO lines (need 6+ cushion)")
        else:
            st.caption("⏳ Waiting for 5+ minutes...")
        
        st.divider()
else:
    st.info("No live games right now")

# ============================================================
# CUSHION SCANNER
# ============================================================
st.subheader("🎯 CUSHION SCANNER (Totals)")

all_game_options = ["All Games"] + [f"{g['away_abbrev']} @ {g['home_abbrev']}" for g in games]
cush_col1, cush_col2, cush_col3 = st.columns(3)
with cush_col1:
    selected_game = st.selectbox("Select Game:", all_game_options, key="cush_game")
with cush_col2:
    min_mins = st.selectbox("Min minutes:", [0, 5, 8, 10, 12, 15], index=0, key="cush_mins")
with cush_col3:
    side_choice = st.selectbox("Side:", ["NO (Under)", "YES (Over)"], key="cush_side")

cushion_data = []
for g in games:
    if g['status'] in ['STATUS_FINAL', 'STATUS_FULL_TIME']: continue
    game_name = f"{g['away_abbrev']} @ {g['home_abbrev']}"
    if selected_game != "All Games" and game_name != selected_game: continue
    if g['minutes_played'] < min_mins: continue
    
    total, mins = g['total_score'], g['minutes_played']
    if mins < 1:
        proj = LEAGUE_AVG_TOTAL
        pace_label, pace_color = "⏳ PRE", "#888"
    else:
        proj = calc_projection(total, mins)
        pace = total / mins
        pace_label, pace_color = get_pace_label(pace)
    
    for thresh in THRESHOLDS:
        cushion = (thresh - proj) if side_choice == "NO (Under)" else (proj - thresh)
        if cushion >= 6 or (selected_game != "All Games"):
            cushion_data.append({"game": game_name, "status": f"H{g['period']} {g['clock']}" if g['period'] > 0 else "Scheduled",
                "proj": proj, "line": thresh, "cushion": cushion, "pace": pace_label,
                "link": get_kalshi_game_link(g['away_abbrev'], g['home_abbrev']), "mins": mins})

cushion_data.sort(key=lambda x: x['cushion'], reverse=True)
if cushion_data:
    max_results = 20 if selected_game != "All Games" else 10
    for cd in cushion_data[:max_results]:
        cc1, cc2, cc3, cc4 = st.columns([3, 1, 1, 2])
        with cc1:
            st.markdown(f"**{cd['game']}** • {cd['status']}")
            if cd['mins'] > 0:
                st.caption(f"{cd['pace']} • {cd['mins']} min played")
        with cc2: st.write(f"Proj: {cd['proj']} | Line: {cd['line']}")
        with cc3:
            cushion_color = "#22c55e" if cd['cushion'] >= 6 else ("#eab308" if cd['cushion'] >= 0 else "#ef4444")
            st.markdown(f"<span style='color:{cushion_color};font-weight:bold'>{'+' if cd['cushion'] >= 0 else ''}{round(cd['cushion'])}</span>", unsafe_allow_html=True)
        with cc4: st.link_button(f"BUY {'NO' if 'NO' in side_choice else 'YES'} {cd['line']}", cd['link'], use_container_width=True)
else:
    if selected_game != "All Games":
        st.info(f"Select a side and see all lines for {selected_game}")
    else:
        st.info("No cushion opportunities found (need 6+ cushion)")

st.divider()

# ============================================================
# PACE SCANNER
# ============================================================
st.subheader("📈 PACE SCANNER")
pace_data = []
for g in games:
    if g['minutes_played'] >= 5:
        pace = g['total_score'] / g['minutes_played']
        pace_label, pace_color = get_pace_label(pace)
        pace_data.append({"game": f"{g['away_abbrev']} @ {g['home_abbrev']}", 
            "status": f"H{g['period']} {g['clock']}" if g['period'] > 0 else "Scheduled",
            "total": g['total_score'], "pace": pace, "pace_label": pace_label,
            "pace_color": pace_color, "proj": calc_projection(g['total_score'], g['minutes_played'])})

pace_data.sort(key=lambda x: x['pace'])
if pace_data:
    for pd in pace_data:
        pc1, pc2, pc3, pc4 = st.columns([3, 2, 2, 2])
        with pc1: st.markdown(f"**{pd['game']}**")
        with pc2: st.write(f"{pd['status']} • {pd['total']} pts")
        with pc3: st.markdown(f"<span style='color:{pd['pace_color']};font-weight:bold'>{pd['pace_label']}</span>", unsafe_allow_html=True)
        with pc4: st.write(f"Proj: {pd['proj']}")
else:
    st.info("No live games with 5+ minutes played")

st.divider()

# ============================================================
# PRE-GAME ALIGNMENT (FIXED)
# ============================================================
with st.expander("🎯 PRE-GAME ALIGNMENT (Speculative)", expanded=True):
    st.caption("Model prediction for scheduled games • Click ➕ to add to tracker")
    
    if scheduled_games:
        all_picks = []
        for g in scheduled_games:
            edge_score = calc_pregame_edge(g, b2b_teams)
            away_abbrev, home_abbrev = g['away_abbrev'], g['home_abbrev']
            if edge_score >= 70: pick, edge_label, edge_color = home_abbrev, "🟢 STRONG", "#22c55e"
            elif edge_score >= 60: pick, edge_label, edge_color = home_abbrev, "🟢 GOOD", "#22c55e"
            elif edge_score <= 30: pick, edge_label, edge_color = away_abbrev, "🟢 STRONG", "#22c55e"
            elif edge_score <= 40: pick, edge_label, edge_color = away_abbrev, "🟢 GOOD", "#22c55e"
            else: pick, edge_label, edge_color = "WAIT", "🟡 NEUTRAL", "#eab308"
            all_picks.append({"away_abbrev": away_abbrev, "home_abbrev": home_abbrev, "pick": pick, "edge_label": edge_label, "edge_color": edge_color})
        
        actionable = [p for p in all_picks if p['pick'] != "WAIT"]
        if actionable:
            add_col1, add_col2 = st.columns([3, 1])
            with add_col1: st.caption(f"📊 {len(actionable)} actionable picks out of {len(all_picks)} games")
            with add_col2:
                if st.button(f"➕ ADD ALL ({len(actionable)})", key="add_all_pregame", use_container_width=True):
                    added = 0
                    for p in actionable:
                        game_key = f"{p['away_abbrev']}@{p['home_abbrev']}"
                        if not any(pos['game'] == game_key for pos in st.session_state.positions):
                            st.session_state.positions.append({"game": game_key, "pick": p['pick'], "type": "ML", "line": "-",
                                "price": 50, "contracts": 10, "link": get_kalshi_game_link(p['away_abbrev'], p['home_abbrev']), "id": str(uuid.uuid4())[:8]})
                            added += 1
                    st.toast(f"✅ Added {added} positions!")
                    st.rerun()
            st.markdown("---")
        
        for p in all_picks[:20]:
            pg1, pg2, pg3, pg4 = st.columns([2.5, 1, 2, 1])
            game_datetime = next((g.get('game_datetime', '') for g in scheduled_games if g['away_abbrev'] == p['away_abbrev'] and g['home_abbrev'] == p['home_abbrev']), '')
            with pg1:
                st.markdown(f"**{p['away_abbrev']} @ {p['home_abbrev']}**")
                if game_datetime:
                    st.caption(game_datetime)
            with pg2:
                st.markdown(f"<span style='color:{p['edge_color']}'>{p['edge_label']}</span>", unsafe_allow_html=True)
            with pg3:
                if p['pick'] != "WAIT":
                    st.link_button(f"🎯 {p['pick']} ML", get_kalshi_game_link(p['away_abbrev'], p['home_abbrev']), use_container_width=True)
                else:
                    st.caption("Wait for better edge")
            with pg4:
                if p['pick'] != "WAIT":
                    game_key = f"{p['away_abbrev']}@{p['home_abbrev']}"
                    if any(pos['game'] == game_key for pos in st.session_state.positions):
                        st.caption("✅ Tracked")
                    elif st.button("➕", key=f"quick_{p['away_abbrev']}_{p['home_abbrev']}"):
                        st.session_state.positions.append({"game": game_key, "pick": p['pick'], "type": "ML", "line": "-",
                            "price": 50, "contracts": 10, "link": get_kalshi_game_link(p['away_abbrev'], p['home_abbrev']), "id": str(uuid.uuid4())[:8]})
                        st.rerun()
    else:
        st.info("No scheduled games")

st.divider()

# ============================================================
# POSITION TRACKER
# ============================================================
st.subheader("📊 POSITION TRACKER")

today_games = [(f"{g['away_abbrev']} @ {g['home_abbrev']}", g['away_abbrev'], g['home_abbrev']) for g in games]

with st.expander("➕ ADD NEW POSITION", expanded=False):
    if today_games:
        ac1, ac2 = st.columns(2)
        with ac1:
            game_sel = st.selectbox("Select Game", [g[0] for g in today_games], key="add_game")
            sel_game = next((g for g in today_games if g[0] == game_sel), None)
        with ac2: bet_type = st.selectbox("Bet Type", ["ML (Moneyline)", "Totals (Over/Under)"], key="add_type")
        
        ac3, ac4 = st.columns(2)
        with ac3:
            if bet_type == "ML (Moneyline)": pick = st.selectbox("Pick", [sel_game[1], sel_game[2]] if sel_game else [], key="add_pick")
            else: pick = st.selectbox("Pick", ["YES (Over)", "NO (Under)"], key="add_totals_pick")
        with ac4: line = st.selectbox("Line", THRESHOLDS, key="add_line") if "Totals" in bet_type else "-"
        
        ac5, ac6, ac7 = st.columns(3)
        with ac5: entry_price = st.number_input("Entry Price (¢)", 1, 99, 50, key="add_price")
        with ac6: contracts = st.number_input("Contracts", 1, 10000, 10, key="add_contracts")
        with ac7:
            cost = entry_price * contracts / 100
            st.metric("Cost", f"${cost:.2f}")
            st.caption(f"Win: +${contracts - cost:.2f}")
        
        if st.button("✅ ADD POSITION", use_container_width=True, key="add_pos_btn"):
            if sel_game:
                st.session_state.positions.append({"game": f"{sel_game[1]}@{sel_game[2]}",
                    "pick": pick if "ML" in bet_type else pick.split()[0], "type": "ML" if "ML" in bet_type else "Totals",
                    "line": "-" if "ML" in bet_type else str(line), "price": entry_price, "contracts": contracts,
                    "link": get_kalshi_game_link(sel_game[1], sel_game[2]), "id": str(uuid.uuid4())[:8]})
                st.success("Added!")
                st.rerun()

if st.session_state.positions:
    st.markdown("---")
    for idx, pos in enumerate(st.session_state.positions):
        current = next((g for g in games if f"{g['away_abbrev']}@{g['home_abbrev']}" == pos['game']), None)
        
        edit_key = f"editing_{pos['id']}"
        is_editing = st.session_state.get(edit_key, False)
        
        if is_editing:
            st.markdown(f"**✏️ Editing: {pos['game']}**")
            ec1, ec2 = st.columns(2)
            with ec1:
                new_type = st.selectbox("Bet Type", ["ML", "Totals"], index=0 if pos['type']=="ML" else 1, key=f"edit_type_{pos['id']}")
            with ec2:
                if new_type == "ML":
                    parts = pos['game'].split("@")
                    new_pick = st.selectbox("Pick", [parts[0], parts[1]], index=[parts[0], parts[1]].index(pos['pick']) if pos['pick'] in parts else 0, key=f"edit_pick_{pos['id']}")
                    new_line = "-"
                else:
                    new_pick = st.selectbox("Pick", ["YES", "NO"], index=0 if pos.get('pick','YES')=="YES" else 1, key=f"edit_pick_{pos['id']}")
                    new_line = st.selectbox("Line", THRESHOLDS, index=THRESHOLDS.index(float(pos['line'])) if pos['line'] != "-" and float(pos['line']) in THRESHOLDS else 5, key=f"edit_line_{pos['id']}")
            
            ec3, ec4 = st.columns(2)
            with ec3:
                new_price = st.number_input("Entry Price (¢)", 1, 99, pos.get('price', 50), key=f"edit_price_{pos['id']}")
            with ec4:
                new_contracts = st.number_input("Contracts", 1, 10000, pos.get('contracts', 10), key=f"edit_contracts_{pos['id']}")
            
            ec5, ec6, ec7 = st.columns(3)
            with ec5:
                if st.button("💾 SAVE", key=f"save_{pos['id']}", use_container_width=True):
                    st.session_state.positions[idx]['type'] = new_type
                    st.session_state.positions[idx]['pick'] = new_pick
                    st.session_state.positions[idx]['line'] = str(new_line) if new_type == "Totals" else "-"
                    st.session_state.positions[idx]['price'] = new_price
                    st.session_state.positions[idx]['contracts'] = new_contracts
                    st.session_state[edit_key] = False
                    st.rerun()
            with ec6:
                if st.button("❌ CANCEL", key=f"cancel_{pos['id']}", use_container_width=True):
                    st.session_state[edit_key] = False
                    st.rerun()
            with ec7:
                cost = new_price * new_contracts / 100
                st.metric("Cost", f"${cost:.2f}")
            st.markdown("---")
        else:
            pc1, pc2, pc3, pc4, pc5, pc6 = st.columns([2.2, 1.3, 1.3, 1.2, 1, 1])
            with pc1:
                st.markdown(f"**{pos['game']}**")
                if current:
                    if current['period'] > 0:
                        period_label = f"H{current['period']}" if current['period'] <= 2 else f"OT{current['period']-2}"
                        st.caption(f"🔴 LIVE {period_label} {current['clock']} | {current['away_score']}-{current['home_score']}")
                    elif current['status'] in ['STATUS_FINAL', 'STATUS_FULL_TIME']:
                        st.caption(f"✅ FINAL {current['away_score']}-{current['home_score']}")
                    else:
                        st.caption("⏳ Scheduled")
            with pc2:
                st.write(f"🎯 {pos['pick']} {pos['type']}" if pos['type']=="ML" else f"📊 {pos['pick']} {pos['line']}")
            with pc3:
                st.write(f"{pos.get('contracts',10)} @ {pos.get('price',50)}¢")
                st.caption(f"${pos.get('price',50)*pos.get('contracts',10)/100:.2f}")
            with pc4:
                st.link_button("🔗 Kalshi", pos['link'], use_container_width=True)
            with pc5:
                if st.button("✏️", key=f"edit_{pos['id']}", help="Edit position"):
                    st.session_state[edit_key] = True
                    st.rerun()
            with pc6:
                if st.button("🗑️", key=f"del_{pos['id']}"):
                    remove_position(pos['id'])
                    st.rerun()
    
    st.markdown("---")
    if st.button("🗑️ CLEAR ALL POSITIONS", use_container_width=True, type="primary"):
        st.session_state.positions = []
        st.rerun()
else:
    st.caption("No positions tracked yet. Use ➕ ADD ALL buttons above or add manually.")

st.divider()

# ============================================================
# ALL GAMES TODAY
# ============================================================
st.subheader("📋 ALL GAMES TODAY")
for g in games[:30]:
    if g['status'] in ['STATUS_FINAL', 'STATUS_FULL_TIME']:
        status, color = f"FINAL: {g['away_score']}-{g['home_score']}", "#666"
    elif g['period'] > 0:
        period_label = f"H{g['period']}" if g['period'] <= 2 else f"OT{g['period']-2}"
        status, color = f"LIVE {period_label} {g['clock']} | {g['away_score']}-{g['home_score']}", "#22c55e"
    else:
        game_datetime = g.get('game_datetime', 'TBD')
        spread = g.get('vegas_odds',{}).get('spread','N/A')
        status, color = f"{game_datetime} | Spread: {spread}", "#888"
    st.markdown(f"<div style='background:#1e1e2e;padding:12px;border-radius:8px;margin-bottom:8px;border-left:3px solid {color}'><b style='color:#fff'>{g['away_abbrev']} @ {g['home_abbrev']}</b><br><span style='color:{color}'>{status}</span></div>", unsafe_allow_html=True)

st.divider()

# ============================================================
# HOW TO USE THIS APP
# ============================================================
with st.expander("📖 HOW TO USE THIS APP", expanded=False):
    st.markdown("""
## 🎯 QUICK START GUIDE

### What This App Does
This app finds **edges** in NCAA basketball prediction markets. It compares Vegas odds with model projections to find mispricings on Kalshi.

---

### 📍 SECTION GUIDE

| Section | What It Does | When To Use |
|---------|--------------|-------------|
| 💰 **Mispricing Alert** | Shows Vegas vs Model gaps ≥5% | Check before games start |
| 🎮 **Live Edge Monitor** | Court, scores, play-by-play, totals projections | During live games |
| 🎯 **Cushion Scanner** | Finds safe totals bets with buffer from projection | Mid-game (H2) |
| 📈 **Pace Scanner** | Shows scoring pace (SLOW/FAST) for all live games | Mid-game totals |
| 🎯 **Pre-Game Alignment** | Model picks for scheduled games | Before tipoff |
| 📊 **Position Tracker** | Track your bets, see live status | All day |

---

### 📊 PACE LABELS (Totals) - NCAA

| Label | Pace | Totals Strategy |
|-------|------|-----------------|
| 🐢 **SLOW** | <3.2 pts/min | Lean UNDER / BUY NO |
| ⚖️ **AVG** | 3.2-3.5 pts/min | Wait for clarity |
| 🔥 **FAST** | 3.5-3.8 pts/min | Lean OVER / BUY YES |
| 💥 **SHOOTOUT** | >3.8 pts/min | Strong OVER / BUY YES |

---

### 💰 HOW TO BET ON KALSHI

1. **YES** = You think the event WILL happen (team wins, total goes OVER)
2. **NO** = You think the event WON'T happen (team loses, total stays UNDER)
3. **Price** = Cost in cents (50¢ = 50% implied probability)
4. **Profit** = 100¢ - Price (buy at 40¢, win 60¢ profit)

---

### 🏀 NCAA vs NBA DIFFERENCES

- **Game Length**: 40 minutes (2 halves) vs NBA's 48 minutes (4 quarters)
- **Average Total**: ~145 points vs NBA's ~225 points
- **Pace**: 3.2-3.8 pts/min vs NBA's 4.2-5.0 pts/min
- **Thresholds**: 120.5-170.5 vs NBA's 210.5-245.5

---

### ⚠️ DISCLAIMER

This app is for **educational purposes only**. Not financial advice. Past performance doesn't guarantee future results. Only bet what you can afford to lose.

**Stay small. Stay quiet. Win.**
""")

st.caption(f"v{VERSION} • Educational only • Not financial advice")
st.caption("Stay small. Stay quiet. Win.")get('game_datetime', 'TBD')
        spread = g.get('vegas_odds',{}).get('spread','N/A')
        status, color = f"{game_datetime} | Spread: {spread}", "#888"
    st.markdown(f"<div style='background:#1e1e2e;padding:12px;border-radius:8px;margin-bottom:8px;border-left:3px solid {color}'><b style='color:#fff'>{g['away_abbrev']} @ {g['home_abbrev']}</b><br><span style='color:{color}'>{status}</span></div>", unsafe_allow_html=True)

st.divider()

# ============================================================
# HOW TO USE THIS APP
# ============================================================
with st.expander("📖 HOW TO USE THIS APP", expanded=False):
    st.markdown("""
## 🎯 QUICK START GUIDE

### What This App Does
This app finds **edges** in NCAA basketball prediction markets. It compares Vegas odds with model projections to find mispricings on Kalshi.

---

### 📍 SECTION GUIDE

| Section | What It Does | When To Use |
|---------|--------------|-------------|
| 💰 **Mispricing Alert** | Shows Vegas vs Model gaps ≥5% | Check before games start |
| 🎮 **Live Edge Monitor** | Court, scores, play-by-play, totals projections | During live games |
| 🎯 **Cushion Scanner** | Finds safe totals bets with buffer from projection | Mid-game (H2) |
| 📈 **Pace Scanner** | Shows scoring pace (SLOW/FAST) for all live games | Mid-game totals |
| 🎯 **Pre-Game Alignment** | Model picks for scheduled games | Before tipoff |
| 📊 **Position Tracker** | Track your bets, see live status | All day |

---

### 📊 PACE LABELS (Totals) - NCAA

| Label | Pace | Totals Strategy |
|-------|------|-----------------|
| 🐢 **SLOW** | <3.2 pts/min | Lean UNDER / BUY NO |
| ⚖️ **AVG** | 3.2-3.5 pts/min | Wait for clarity |
| 🔥 **FAST** | 3.5-3.8 pts/min | Lean OVER / BUY YES |
| 💥 **SHOOTOUT** | >3.8 pts/min | Strong OVER / BUY YES |

---

### 💰 HOW TO BET ON KALSHI

1. **YES** = You think the event WILL happen (team wins, total goes OVER)
2. **NO** = You think the event WON'T happen (team loses, total stays UNDER)
3. **Price** = Cost in cents (50¢ = 50% implied probability)
4. **Profit** = 100¢ - Price (buy at 40¢, win 60¢ profit)

---

### 🏀 NCAA vs NBA DIFFERENCES

- **Game Length**: 40 minutes (2 halves) vs NBA's 48 minutes (4 quarters)
- **Average Total**: ~145 points vs NBA's ~225 points
- **Pace**: 3.2-3.8 pts/min vs NBA's 4.2-5.0 pts/min
- **Thresholds**: 120.5-170.5 vs NBA's 210.5-245.5

---

### ⚠️ DISCLAIMER

This app is for **educational purposes only**. Not financial advice. Past performance doesn't guarantee future results. Only bet what you can afford to lose.

**Stay small. Stay quiet. Win.**
""")

st.caption(f"v{VERSION} • Educational only • Not financial advice")
st.caption("Stay small. Stay quiet. Win.")get('game_datetime', 'TBD')
       get('vegas_odds',{}).get('spread','N/A')
        status, color = f"{game_datetime} | Spread: {spread}", "#888"
    st.markdown(f"<div style='background:#1e1e2e;padding:12px;border-radius:8px;margin-bottom:8px;border-left:3px solid {color}'><b style='color:#fff'>{g['away_abbrev']} @ {g['home_abbrev']}</b><br><span style='color:{color}'>{status}</span></div>", unsafe_allow_html=True)

st.divider()

# ============================================================
# HOW TO USE THIS APP
# ============================================================
with st.expander("📖 HOW TO USE THIS APP", expanded=False):
    st.markdown("""
## 🎯 QUICK START GUIDE

### What This App Does
This app finds **edges** in NCAA basketball prediction markets. It compares Vegas odds with model projections to find mispricings on Kalshi.

---

### 📍 SECTION GUIDE

| Section | What It Does | When To Use |
|---------|--------------|-------------|
| 💰 **Mispricing Alert** | Shows Vegas vs Model gaps ≥5% | Check before games start |
| 🎮 **Live Edge Monitor** | Court, scores, play-by-play, totals projections | During live games |
| 🎯 **Cushion Scanner** | Finds safe totals bets with buffer from projection | Mid-game (H2) |
| 📈 **Pace Scanner** | Shows scoring pace (SLOW/FAST) for all live games | Mid-game totals |
| 🎯 **Pre-Game Alignment** | Model picks for scheduled games | Before tipoff |
| 📊 **Position Tracker** | Track your bets, see live status | All day |

---

### 📊 PACE LABELS (Totals) - NCAA

| Label | Pace | Totals Strategy |
|-------|------|-----------------|
| 🐢 **SLOW** | <3.2 pts/min | Lean UNDER / BUY NO |
| ⚖️ **AVG** | 3.2-3.5 pts/min | Wait for clarity |
| 🔥 **FAST** | 3.5-3.8 pts/min | Lean OVER / BUY YES |
| 💥 **SHOOTOUT** | >3.8 pts/min | Strong OVER / BUY YES |

---

### 💰 HOW TO BET ON KALSHI

1. **YES** = You think the event WILL happen (team wins, total goes OVER)
2. **NO** = You think the event WON'T happen (team loses, total stays UNDER)
3. **Price** = Cost in cents (50¢ = 50% implied probability)
4. **Profit** = 100¢ - Price (buy at 40¢, win 60¢ profit)

---

### 🏀 NCAA vs NBA DIFFERENCES

- **Game Length**: 40 minutes (2 halves) vs NBA's 48 minutes (4 quarters)
- **Average Total**: ~145 points vs NBA's ~225 points
- **Pace**: 3.2-3.8 pts/min vs NBA's 4.2-5.0 pts/min
- **Thresholds**: 120.5-170.5 vs NBA's 210.5-245.5

---

### ⚠️ DISCLAIMER

This app is for **educational purposes only**. Not financial advice. Past performance doesn't guarantee future results. Only bet what you can afford to lose.

**Stay small. Stay quiet. Win.**
""")

st.caption(f"v{VERSION} • Educational only • Not financial advice")
st.caption("Stay small. Stay quiet. Win.")
