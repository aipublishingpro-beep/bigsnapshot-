import streamlit as st
from streamlit_autorefresh import st_autorefresh
import streamlit.components.v1 as components

st.set_page_config(page_title="BigSnapshot NBA Edge Finder", page_icon="🏀", layout="wide")

from auth import require_auth
require_auth()

st_autorefresh(interval=24000, key="datarefresh")

import uuid
import requests
from datetime import datetime, timedelta
import pytz

eastern = pytz.timezone("US/Eastern")
now = datetime.now(eastern)

VERSION = "12.0"
LEAGUE_AVG_TOTAL = 225
THRESHOLDS = [210.5, 215.5, 220.5, 225.5, 230.5, 235.5, 240.5, 245.5]

if 'positions' not in st.session_state:
    st.session_state.positions = []

TEAM_ABBREVS = {
    "Atlanta Hawks": "Atlanta", "Boston Celtics": "Boston", "Brooklyn Nets": "Brooklyn",
    "Charlotte Hornets": "Charlotte", "Chicago Bulls": "Chicago", "Cleveland Cavaliers": "Cleveland",
    "Dallas Mavericks": "Dallas", "Denver Nuggets": "Denver", "Detroit Pistons": "Detroit",
    "Golden State Warriors": "Golden State", "Houston Rockets": "Houston", "Indiana Pacers": "Indiana",
    "LA Clippers": "LA Clippers", "Los Angeles Clippers": "LA Clippers", "LA Lakers": "LA Lakers",
    "Los Angeles Lakers": "LA Lakers", "Memphis Grizzlies": "Memphis", "Miami Heat": "Miami",
    "Milwaukee Bucks": "Milwaukee", "Minnesota Timberwolves": "Minnesota", "New Orleans Pelicans": "New Orleans",
    "New York Knicks": "New York", "Oklahoma City Thunder": "Oklahoma City", "Orlando Magic": "Orlando",
    "Philadelphia 76ers": "Philadelphia", "Phoenix Suns": "Phoenix", "Portland Trail Blazers": "Portland",
    "Sacramento Kings": "Sacramento", "San Antonio Spurs": "San Antonio", "Toronto Raptors": "Toronto",
    "Utah Jazz": "Utah", "Washington Wizards": "Washington"
}

KALSHI_CODES = {
    "Atlanta": "ATL", "Boston": "BOS", "Brooklyn": "BKN", "Charlotte": "CHA", "Chicago": "CHI",
    "Cleveland": "CLE", "Dallas": "DAL", "Denver": "DEN", "Detroit": "DET", "Golden State": "GSW",
    "Houston": "HOU", "Indiana": "IND", "LA Clippers": "LAC", "LA Lakers": "LAL", "Memphis": "MEM",
    "Miami": "MIA", "Milwaukee": "MIL", "Minnesota": "MIN", "New Orleans": "NOP", "New York": "NYK",
    "Oklahoma City": "OKC", "Orlando": "ORL", "Philadelphia": "PHI", "Phoenix": "PHX", "Portland": "POR",
    "Sacramento": "SAC", "San Antonio": "SAS", "Toronto": "TOR", "Utah": "UTA", "Washington": "WAS"
}

TEAM_COLORS = {
    "Atlanta": "#E03A3E", "Boston": "#007A33", "Brooklyn": "#000000", "Charlotte": "#1D1160",
    "Chicago": "#CE1141", "Cleveland": "#860038", "Dallas": "#00538C", "Denver": "#0E2240",
    "Detroit": "#C8102E", "Golden State": "#1D428A", "Houston": "#CE1141", "Indiana": "#002D62",
    "LA Clippers": "#C8102E", "LA Lakers": "#552583", "Memphis": "#5D76A9", "Miami": "#98002E",
    "Milwaukee": "#00471B", "Minnesota": "#0C2340", "New Orleans": "#0C2340", "New York": "#006BB6",
    "Oklahoma City": "#007AC1", "Orlando": "#0077C0", "Philadelphia": "#006BB6", "Phoenix": "#1D1160",
    "Portland": "#E03A3E", "Sacramento": "#5A2D81", "San Antonio": "#C4CED4", "Toronto": "#CE1141",
    "Utah": "#002B5C", "Washington": "#002B5C"
}

def american_to_implied_prob(odds):
    if odds is None or odds == 0: return 0.5
    if odds > 0: return 100 / (odds + 100)
    else: return abs(odds) / (abs(odds) + 100)
def fetch_espn_games():
    today = datetime.now(eastern).strftime('%Y%m%d')
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={today}"
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
                team_name = TEAM_ABBREVS.get(full_name, full_name)
                score = int(c.get("score", 0) or 0)
                records = c.get("records", [])
                record = records[0].get("summary", "") if records else ""
                if c.get("homeAway") == "home":
                    home_team, home_score, home_record = team_name, score, record
                else:
                    away_team, away_score, away_record = team_name, score, record
            status = event.get("status", {}).get("type", {}).get("name", "STATUS_SCHEDULED")
            period = event.get("status", {}).get("period", 0)
            clock = event.get("status", {}).get("displayClock", "")
            game_id = event.get("id", "")
            minutes_played = 0
            if period > 0:
                if period <= 4:
                    completed_quarters = (period - 1) * 12
                    if clock:
                        try:
                            if ":" in clock:
                                minutes_played = completed_quarters + (12 - int(clock.split(":")[0]))
                            else:
                                minutes_played = completed_quarters + 12
                        except:
                            minutes_played = completed_quarters + 12
                    else:
                        minutes_played = completed_quarters
                else:
                    minutes_played = 48 + (period - 4) * 5
            games.append({
                "away": away_team, "home": home_team,
                "away_score": away_score, "home_score": home_score,
                "away_record": away_record, "home_record": home_record,
                "status": status, "period": period, "clock": clock,
                "minutes_played": minutes_played,
                "total_score": home_score + away_score,
                "game_id": game_id
            })
        return games
    except Exception as e:
        st.error("ESPN fetch error: " + str(e))
        return []

def fetch_kalshi_ml(force_refresh=False):
    if not force_refresh and 'nba_kalshi_data' in st.session_state and 'nba_kalshi_time' in st.session_state:
        age = (datetime.now(eastern) - st.session_state.nba_kalshi_time).total_seconds()
        if age < 15:
            return st.session_state.nba_kalshi_data

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
            main_part, yes_team_code = parts.rsplit("-", 1)
            if len(main_part) < 13: continue
            teams_part = main_part[7:]
            away_code = teams_part[:3].upper()
            home_code = teams_part[3:6].upper()
            game_key = away_code + "@" + home_code

            yes_bid = m.get("yes_bid", 0) or 0
            yes_ask = m.get("yes_ask", 0) or 0
            last_price = m.get("last_price", 0) or 0
            yes_price = yes_ask if yes_ask > 0 else (last_price if last_price > 0 else (yes_bid if yes_bid > 0 else 0))

            markets[game_key] = {
                "away_code": away_code,
                "home_code": home_code,
                "yes_team_code": yes_team_code.upper(),
                "ticker": ticker,
                "yes_bid": yes_bid,
                "yes_ask": yes_ask,
                "yes_price": yes_price,
                "last_price": last_price
            }
        st.session_state.nba_kalshi_data = markets
        st.session_state.nba_kalshi_time = datetime.now(eastern)
        return markets
    except Exception as e:
        st.error(f"Kalshi fetch error: {e}")
        return st.session_state.get('nba_kalshi_data', {})

def find_kalshi_price_for_game(kalshi_data, away, home, team):
    a_lower = away.lower()
    h_lower = home.lower()
    t_lower = team.lower()
    for game_key, m in kalshi_data.items():
        if (a_lower in game_key.lower() or h_lower in game_key.lower()) and t_lower in game_key.lower():
            return m.get("yes_price", 0)
    return 0

def get_kalshi_game_link(away, home):
    away_code = KALSHI_CODES.get(away, "XXX").lower()
    home_code = KALSHI_CODES.get(home, "XXX").lower()
    date_str = datetime.now(eastern).strftime('%y%b%d').lower()
    return f"https://kalshi.com/markets/kxnbagame/professional-basketball-game/kxnbagame-{date_str}{away_code}{home_code}"
def render_scoreboard(away, home, away_score, home_score, period, clock, away_record="", home_record=""):
    away_code = KALSHI_CODES.get(away, away[:3].upper())
    home_code = KALSHI_CODES.get(home, home[:3].upper())
    away_color = TEAM_COLORS.get(away, "#666")
    home_color = TEAM_COLORS.get(home, "#666")
    period_text = f"Q{period}" if period <= 4 else f"OT{period-4}"
    return f'''<div style="background:#0f172a;border-radius:12px;padding:20px;margin-bottom:8px">
    <div style="text-align:center;color:#ffd700;font-weight:bold;font-size:22px;margin-bottom:16px">{period_text} - {clock}</div>
    <table style="width:100%;border-collapse:collapse;color:#fff">
    <tr style="border-bottom:2px solid #333">
        <td style="padding:16px;text-align:left;width:70%"><span style="color:{away_color};font-weight:bold;font-size:28px">{away_code}</span><span style="color:#666;font-size:14px;margin-left:12px">{away_record}</span></td>
        <td style="padding:16px;text-align:right;font-weight:bold;font-size:52px;color:#fff">{away_score}</td>
    </tr>
    <tr>
        <td style="padding:16px;text-align:left;width:70%"><span style="color:{home_color};font-weight:bold;font-size:28px">{home_code}</span><span style="color:#666;font-size:14px;margin-left:12px">{home_record}</span></td>
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
    elif "defensive rebound" in play_text:
        return '<rect x="175" y="25" width="150" height="30" fill="#3b82f6" rx="6"/><text x="250" y="46" fill="#fff" font-size="14" font-weight="bold" text-anchor="middle">DEF REBOUND</text>'
    elif "rebound" in play_text:
        return '<rect x="175" y="25" width="150" height="30" fill="#3b82f6" rx="6"/><text x="250" y="46" fill="#fff" font-size="14" font-weight="bold" text-anchor="middle">REBOUND</text>'
    elif "foul" in play_text:
        return '<rect x="175" y="25" width="150" height="30" fill="#eab308" rx="6"/><text x="250" y="46" fill="#000" font-size="14" font-weight="bold" text-anchor="middle">FOUL</text>'
    elif "timeout" in play_text:
        return '<rect x="175" y="25" width="150" height="30" fill="#a855f7" rx="6"/><text x="250" y="46" fill="#fff" font-size="14" font-weight="bold" text-anchor="middle">TIMEOUT</text>'
    return ""

def render_nba_court(away, home, away_score, home_score, period, clock, last_play=None):
    away_color = TEAM_COLORS.get(away, "#666")
    home_color = TEAM_COLORS.get(home, "#666")
    away_code = KALSHI_CODES.get(away, away[:3].upper())
    home_code = KALSHI_CODES.get(home, home[:3].upper())
    period_text = f"Q{period}" if period <= 4 else f"OT{period-4}"
    play_badge = get_play_badge(last_play)
    return f'''<div style="background:#1a1a2e;border-radius:12px;padding:10px;"><svg viewBox="0 0 500 280" style="width:100%;max-width:500px;"><rect x="20" y="20" width="460" height="200" fill="#2d4a22" stroke="#fff" stroke-width="2" rx="8"/><circle cx="250" cy="120" r="35" fill="none" stroke="#fff" stroke-width="2"/><circle cx="250" cy="120" r="4" fill="#fff"/><line x1="250" y1="20" x2="250" y2="220" stroke="#fff" stroke-width="2"/><path d="M 20 50 Q 100 120 20 190" fill="none" stroke="#fff" stroke-width="2"/><rect x="20" y="70" width="70" height="100" fill="none" stroke="#fff" stroke-width="2"/><circle cx="90" cy="120" r="25" fill="none" stroke="#fff" stroke-width="2"/><circle cx="35" cy="120" r="8" fill="none" stroke="#ff6b35" stroke-width="3"/><path d="M 480 50 Q 400 120 480 190" fill="none" stroke="#fff" stroke-width="2"/><rect x="410" y="70" width="70" height="100" fill="none" stroke="#fff" stroke-width="2"/><circle cx="410" cy="120" r="25" fill="none" stroke="#fff" stroke-width="2"/><circle cx="465" cy="120" r="8" fill="none" stroke="#ff6b35" stroke-width="3"/>{play_badge}<rect x="40" y="228" width="90" height="48" fill="{away_color}" rx="6"/><text x="85" y="250" fill="#fff" font-size="14" font-weight="bold" text-anchor="middle">{away_code}</text><text x="85" y="270" fill="#fff" font-size="18" font-weight="bold" text-anchor="middle">{away_score}</text><rect x="370" y="228" width="90" height="48" fill="{home_color}" rx="6"/><text x="415" y="250" fill="#fff" font-size="14" font-weight="bold" text-anchor="middle">{home_code}</text><text x="415" y="270" fill="#fff" font-size="18" font-weight="bold" text-anchor="middle">{home_score}</text><text x="250" y="258" fill="#fff" font-size="16" font-weight="bold" text-anchor="middle">{period_text} {clock}</text></svg></div>'''

def get_play_icon(play_type, score_value):
    play_lower = play_type.lower() if play_type else ""
    if score_value > 0 or "made" in play_lower: return "🏀", "#22c55e"
    elif "miss" in play_lower or "block" in play_lower: return "❌", "#ef4444"
    elif "rebound" in play_lower: return "📥", "#3b82f6"
    elif "turnover" in play_lower or "steal" in play_lower: return "🔄", "#f97316"
    elif "foul" in play_lower: return "🚨", "#eab308"
    elif "timeout" in play_lower: return "⏸️", "#a855f7"
    return "•", "#888"
games = fetch_espn_games()
kalshi_ml = fetch_kalshi_ml()

live_games = [g for g in games if g['status'] in ['STATUS_IN_PROGRESS', 'STATUS_HALFTIME', 'STATUS_END_PERIOD'] or (g['period'] > 0 and g['status'] not in ['STATUS_FINAL', 'STATUS_FULL_TIME'])]
scheduled_games = [g for g in games if g['status'] == 'STATUS_SCHEDULED' and g['period'] == 0]
final_games = [g for g in games if g['status'] in ['STATUS_FINAL', 'STATUS_FULL_TIME']]

st.title("🏀 BIGSNAPSHOT NBA EDGE FINDER")
st.caption(f"v{VERSION} • {now.strftime('%b %d, %Y %I:%M %p ET')} • Vegas vs Kalshi Mispricing Detector")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Today's Games", len(games))
c2.metric("Live Now", len(live_games))
c3.metric("Scheduled", len(scheduled_games))
c4.metric("Final", len(final_games))

st.divider()

st.subheader("💰 VEGAS vs KALSHI MISPRICING ALERT")

refresh_col1, refresh_col2 = st.columns([3, 1])
with refresh_col1:
    kalshi_time = st.session_state.get('nba_kalshi_time')
    if kalshi_time:
        age = (datetime.now(eastern) - kalshi_time).total_seconds()
        freshness = f"🟢 {int(age)}s ago" if age < 30 else (f"🟡 {int(age)}s ago" if age < 60 else f"🔴 {int(age)}s ago — STALE")
        st.caption(f"Kalshi data: {freshness} • ESPN odds: soft book (not sharp)")
    else:
        st.caption("Kalshi data: not loaded yet")
with refresh_col2:
    if st.button("🔄 Refresh Kalshi Prices Now", key="refresh_nba_kalshi"):
        _ = fetch_kalshi_ml(force_refresh=True)
        st.success("Kalshi refreshed!")
        st.rerun()

st.caption("Buy when Kalshi underprices Vegas favorite • 5%+ gap = real edge • ⚠️ ESPN odds are soft book")

mispricings = []
for g in games:
    if g['status'] in ['STATUS_FINAL', 'STATUS_FULL_TIME']: continue
    away, home = g['away'], g['home']
    vegas = g.get('vegas_odds', {})
    home_ml = vegas.get('homeML')
    away_ml = vegas.get('awayML')
    spread = vegas.get('spread')

    vegas_home_prob = american_to_implied_prob(home_ml) * 100 if home_ml else 0
    vegas_away_prob = american_to_implied_prob(away_ml) * 100 if away_ml else 0
    if vegas_home_prob + vegas_away_prob > 0:
        total = vegas_home_prob + vegas_away_prob
        vegas_home_prob = (vegas_home_prob / total) * 100
        vegas_away_prob = (vegas_away_prob / total) * 100

    kalshi_home_price = find_kalshi_price_for_game(kalshi_ml, g['away'], g['home'], g['home'])
    kalshi_away_price = find_kalshi_price_for_game(kalshi_ml, g['away'], g['home'], g['away'])

    if kalshi_home_price == 0 and kalshi_away_price == 0: continue

    home_edge = vegas_home_prob - kalshi_home_price if kalshi_home_price > 0 else 0
    away_edge = vegas_away_prob - kalshi_away_price if kalshi_away_price > 0 else 0

    if (home_edge >= 10 and kalshi_home_price < 90) or (away_edge >= 10 and kalshi_away_price < 90):
        if home_edge >= away_edge:
            team, vegas_prob, kalshi_price, edge = g['home'], vegas_home_prob, kalshi_home_price, home_edge
        else:
            team, vegas_prob, kalshi_price, edge = g['away'], vegas_away_prob, kalshi_away_price, away_edge

        kalshi_link = get_kalshi_game_link(g['away'], g['home'])
        mispricings.append({
            'game': g, 'team': team, 'vegas_prob': vegas_prob,
            'kalshi_price': kalshi_price, 'edge': edge, 'link': kalshi_link
        })

mispricings.sort(key=lambda x: x['edge'], reverse=True)

if mispricings:
    st.success(f"🔥 {len(mispricings)} real mispricing opportunities found!")
    for mp in mispricings:
        g = mp['game']
        edge_color = "#ff6b6b" if mp['edge'] >= 15 else ("#22c55e" if mp['edge'] >= 10 else "#eab308")
        edge_label = "🔥 STRONG" if mp['edge'] >= 15 else ("🟢 GOOD" if mp['edge'] >= 10 else "🟡 EDGE")
        status_text = f"Q{g['period']} {g['clock']}" if g['period'] > 0 else g.get('game_datetime', 'Scheduled')
        
        st.markdown(f"**{g['away']} @ {g['home']}** • {status_text}")
        st.markdown(f"""
        <div style="background:#0f172a;padding:16px;border-radius:10px;border:2px solid {edge_color};margin-bottom:12px">
            <div style="font-size:1.4em;font-weight:bold;color:#fff;margin-bottom:8px">
                🎯 BUY <span style="color:#22c55e">{mp['team']}</span> on Kalshi
            </div>
            <table style="width:100%;text-align:center;color:#fff">
                <tr style="color:#888"><td>Vegas Implied</td><td>Kalshi Price</td><td>EDGE</td></tr>
                <tr style="font-size:1.3em;font-weight:bold">
                    <td>{round(mp['vegas_prob'])}%</td>
                    <td>{round(mp['kalshi_price'])}¢</td>
                    <td style="color:{edge_color}">+{round(mp['edge'])}%</td>
                </tr>
            </table>
        </div>
        """, unsafe_allow_html=True)
        st.link_button(f"🎯 BUY {mp['team']} on Kalshi", mp['link'], use_container_width=True)
else:
    st.info("🔍 No real mispricings right now (need 10%+ gap AND Kalshi price < 90¢)")

st.divider()
st.subheader("🎮 LIVE EDGE MONITOR")

if live_games:
    for g in live_games:
        away, home, total, mins, game_id = g['away'], g['home'], g['total_score'], g['minutes_played'], g['game_id']
        plays = fetch_plays(game_id)
        st.markdown(f"### {away} @ {home}")
        st.markdown(render_scoreboard(away, home, g['away_score'], g['home_score'], g['period'], g['clock'], g.get('away_record', ''), g.get('home_record', '')), unsafe_allow_html=True)
        col1, col2 = st.columns([1, 1])
        with col1:
            last_play = plays[-1] if plays else None
            st.markdown(render_nba_court(away, home, g['away_score'], g['home_score'], g['period'], g['clock'], last_play), unsafe_allow_html=True)
            poss_team, poss_text = infer_possession(plays, away, home)
            if poss_text:
                poss_color = TEAM_COLORS.get(poss_team, "#ffd700") if poss_team else "#888"
                st.markdown(f"<div style='text-align:center;padding:8px;background:#1a1a2e;border-radius:6px;margin-top:4px'><span style='color:{poss_color};font-size:1.3em;font-weight:bold'>{poss_text} BALL</span></div>", unsafe_allow_html=True)
        with col2:
            st.markdown("**📋 LAST 10 PLAYS**")
            tts_on = st.checkbox("🔊 Announce plays", key=f"tts_{game_id}")
            if plays:
                for i, p in enumerate(reversed(plays)):
                    icon, color = get_play_icon(p['play_type'], p['score_value'])
                    play_text = p['text'][:60] if p['text'] else "Play"
                    st.markdown(f"<div style='padding:4px 8px;margin:2px 0;background:#1e1e2e;border-radius:4px;border-left:3px solid {color}'><span style='color:{color}'>{icon}</span> Q{p['period']} {p['clock']} • {play_text}</div>", unsafe_allow_html=True)
                    if i == 0 and tts_on and p['text']:
                        speak_play(f"Q{p['period']} {p['clock']}. {p['text']}")
            else:
                st.caption("Waiting for plays...")
        if mins >= 6:
            proj = calc_projection(total, mins)
            pace = total / mins if mins > 0 else 0
            pace_label, pace_color = get_pace_label(pace)
            lead = g['home_score'] - g['away_score']
            leader = home if g['home_score'] > g['away_score'] else away
            kalshi_link = get_kalshi_game_link(away, home)
            st.markdown(f"<div style='background:#1e1e2e;padding:12px;border-radius:8px;margin-top:8px'><b>Score:</b> {total} pts in {mins} min • <b>Pace:</b> <span style='color:{pace_color}'>{pace_label}</span> ({pace:.1f}/min)<br><b>Projection:</b> {proj} pts • <b>Lead:</b> {leader} +{abs(lead)}</div>", unsafe_allow_html=True)
            away_code, home_code = KALSHI_CODES.get(away, "XXX"), KALSHI_CODES.get(home, "XXX")
            kalshi_data = kalshi_ml.get(away_code + "@" + home_code, {})
            st.markdown("**🎯 MONEYLINE**")
            if abs(lead) >= 10:
                ml_pick = leader
                ml_confidence = "🔥 STRONG" if abs(lead) >= 15 else "🟢 GOOD"
                if kalshi_data:
                    if leader == home: ml_action = "YES" if kalshi_data.get('yes_team_code', '').upper() == home_code.upper() else "NO"
                    else: ml_action = "YES" if kalshi_data.get('yes_team_code', '').upper() == away_code.upper() else "NO"
                    st.link_button(f"{ml_confidence} BUY {ml_action} ({ml_pick} ML) • Lead +{abs(lead)}", kalshi_link, use_container_width=True)
                else: st.link_button(f"{ml_confidence} {ml_pick} ML • Lead +{abs(lead)}", kalshi_link, use_container_width=True)
            else: st.caption(f"⏳ Wait for larger lead (currently {leader} +{abs(lead)})")
            st.markdown("**📊 TOTALS**")
            yes_lines = [(t, proj - t) for t in sorted(THRESHOLDS) if proj - t >= 6]
            no_lines = [(t, t - proj) for t in sorted(THRESHOLDS, reverse=True) if t - proj >= 6]
            tc1, tc2 = st.columns(2)
            with tc1:
                st.markdown("<span style='color:#22c55e;font-weight:bold'>🟢 YES (Over) — go LOW</span>", unsafe_allow_html=True)
                if yes_lines:
                    for i, (line, cushion) in enumerate(yes_lines[:3]):
                        safety = "🔒 FORTRESS" if cushion >= 20 else ("✅ SAFE" if cushion >= 12 else "🎯 TIGHT")
                        rec = " ⭐REC" if i == 0 and cushion >= 12 else ""
                        st.link_button(f"{safety} YES {line} (+{int(cushion)}){rec}", kalshi_link, use_container_width=True)
                else: st.caption("No safe YES lines")
            with tc2:
                st.markdown("<span style='color:#ef4444;font-weight:bold'>🔴 NO (Under) — go HIGH</span>", unsafe_allow_html=True)
                if no_lines:
                    for i, (line, cushion) in enumerate(no_lines[:3]):
                        safety = "🔒 FORTRESS" if cushion >= 20 else ("✅ SAFE" if cushion >= 12 else "🎯 TIGHT")
                        rec = " ⭐REC" if i == 0 and cushion >= 12 else ""
                        st.link_button(f"{safety} NO {line} (+{int(cushion)}){rec}", kalshi_link, use_container_width=True)
                else: st.caption("No safe NO lines")
        else: st.caption("⏳ Waiting for 6+ minutes...")
        st.divider()
else:
    st.info("No live games right now")

st.divider()

st.caption(f"v{VERSION} • Educational only • Not financial advice")
st.caption("Stay small. Stay quiet. Win.")
st.divider()
