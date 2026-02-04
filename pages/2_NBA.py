import streamlit as st
from streamlit_autorefresh import st_autorefresh
import streamlit.components.v1 as components
import requests
from datetime import datetime, timedelta
import pytz
import uuid

st.set_page_config(page_title="BigSnapshot NBA Edge Finder", page_icon="🏀", layout="wide")

from auth import require_auth
require_auth()

st_autorefresh(interval=24000, key="datarefresh")

eastern = pytz.timezone("US/Eastern")
now = datetime.now(eastern)

VERSION = "11.3"   # updated version

# ====================== ALL YOUR DICTIONARIES ======================
TEAM_ABBREVS = { ... }          # ← paste your full TEAM_ABBREVS here (from original code)
KALSHI_CODES = { ... }          # ← paste your full KALSHI_CODES
TEAM_COLORS = { ... }           # ← paste if you want colors
# (I kept them short in this message — just copy the exact dicts from your old file)

# ====================== HELPER FUNCTIONS ======================
def american_to_implied_prob(odds):
    if odds is None: return None
    if odds > 0: return 100 / (odds + 100)
    else: return abs(odds) / (abs(odds) + 100)

def get_kalshi_game_link(away, home):
    away_code = KALSHI_CODES.get(away, "XXX").lower()
    home_code = KALSHI_CODES.get(home, "XXX").lower()
    date_str = datetime.now(eastern).strftime('%y%b%d').lower()
    return f"https://kalshi.com/markets/kxnbagame/professional-basketball-game/kxnbagame-{date_str}{away_code}{home_code}"

@st.cache_data(ttl=30)
def fetch_espn_games():
    today = datetime.now(eastern).strftime('%Y%m%d')
    url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates=" + today
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        games = []
        for event in data.get("events", []):
            # ... (same as your original fetch_espn_games — copy the whole function body from your old file)
            # I won't repeat 100 lines here, but keep your original exact code
        return games
    except Exception as e:
        st.error("ESPN fetch error: " + str(e))
        return []

@st.cache_data(ttl=30)
def fetch_game_boxscore(game_id):
    if not game_id: return {}
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary?event={game_id}"
    try:
        return requests.get(url, timeout=10).json()
    except:
        return {}

def get_made_att(stats_list, stat_name):
    for s in stats_list:
        if s.get("name") == stat_name:
            dv = s.get("displayValue", "0-0")
            if "-" in dv:
                try: return tuple(map(int, dv.split("-")))
                except: pass
    return 0, 0

def get_single_stat(stats_list, stat_name):
    for s in stats_list:
        if s.get("name") == stat_name:
            try: return int(s.get("displayValue", 0))
            except: return 0
    return 0

def calculate_net_rating(game):
    summary = fetch_game_boxscore(game.get("game_id"))
    if not summary: return 0.0, 0.0, 0.0, 0
    box = summary.get("boxscore", {})
    teams = box.get("teams", [])
    if len(teams) < 2: return 0.0, 0.0, 0.0, 0

    home_data = next((t for t in teams if t.get("homeAway") == "home"), teams[0])
    away_data = next((t for t in teams if t.get("homeAway") == "away"), teams[1])

    home_stats = home_data.get("statistics", [])
    away_stats = away_data.get("statistics", [])

    h_pts = game["home_score"]
    a_pts = game["away_score"]

    h_fgm, h_fga = get_made_att(home_stats, "Field Goals")
    h_ftm, h_fta = get_made_att(home_stats, "Free Throws")
    h_tov = get_single_stat(home_stats, "Turnovers")
    h_orb = get_single_stat(home_stats, "Offensive Rebounds")

    a_fgm, a_fga = get_made_att(away_stats, "Field Goals")
    a_ftm, a_fta = get_made_att(away_stats, "Free Throws")
    a_tov = get_single_stat(away_stats, "Turnovers")
    a_orb = get_single_stat(away_stats, "Offensive Rebounds")

    h_poss = h_fga + 0.44 * h_fta - h_orb + h_tov
    a_poss = a_fga + 0.44 * a_fta - a_orb + a_tov

    if h_poss < 5 or a_poss < 5:
        return 0.0, 0.0, 0.0, 0

    h_ortg = (h_pts / h_poss) * 100
    a_ortg = (a_pts / a_poss) * 100
    net = h_ortg - a_ortg
    poss = round((h_poss + a_poss) / 2)
    return round(h_ortg,1), round(a_ortg,1), round(net,1), poss

# ====================== FETCH DATA ONCE ======================
games = fetch_espn_games()
kalshi_ml = fetch_kalshi_ml()          # ← keep your original kalshi functions
kalshi_spreads = fetch_kalshi_spreads()
injuries = fetch_injuries()
b2b_teams = fetch_yesterday_teams()

live_games = [g for g in games if g['status'] in ['STATUS_IN_PROGRESS', 'STATUS_HALFTIME', 'STATUS_END_PERIOD'] or (g['period'] > 0 and g['status'] not in ['STATUS_FINAL', 'STATUS_FULL_TIME'])]

# ====================== TITLE ======================
st.title("🏀 BIGSNAPSHOT NBA EDGE FINDER")
st.caption(f"v{VERSION} • {now.strftime('%b %d, %Y %I:%M %p ET')}")

# ... (your original metrics, mispricing alert, LIVE EDGE MONITOR section — copy exactly as before) ...

st.divider()

# ====================== NEW QUARTER-END MONITOR ======================
st.subheader("🔔 LIVE QUARTER-END TRADING SIGNALS")
st.caption("Auto-detects 00:00 • Net Rating + Moneyline + Lead rules • Direct Kalshi links")

signals = []
for g in games:
    if g.get("clock") != "00:00" and g.get("status") not in ["STATUS_HALFTIME", "STATUS_END_PERIOD", "STATUS_FINAL"]:
        continue
    period = g.get("period", 0)
    if period == 0: continue

    h_ortg, a_ortg, net_rating, poss = calculate_net_rating(g)
    lead = g["home_score"] - g["away_score"]
    leader = g["home"] if lead > 0 else g["away"] if lead < 0 else None

    vegas = g.get("vegas_odds", {})
    home_ml = vegas.get("homeML")
    away_ml = vegas.get("awayML")
    fav_ml = min(home_ml or 999, away_ml or 999) if home_ml and away_ml else 999
    fav_team = g["home"] if (home_ml or 999) <= (away_ml or 999) else g["away"]

    signal_text = confidence = stars = ""
    conf_color = "#22c55e"

    if g["status"] in ["STATUS_FINAL", "STATUS_FULL_TIME"]:
        winner = g["home"] if g["home_score"] > g["away_score"] else g["away"]
        signal_text = f"🏆 FINAL → **{winner}**"
        confidence = "FORTRESS"
        stars = "⭐⭐⭐"
    elif period == 3 and abs(lead) >= 15:
        signal_text = f"🔒 BUY **{leader}** YES"
        if abs(lead) >= 25: confidence, stars = "FORTRESS", "⭐⭐⭐"
        elif abs(lead) >= 20: confidence, stars = "STRONG", "⭐⭐"
        else: confidence, stars = "GOOD", "⭐"
    elif period == 2 and abs(net_rating) >= 20 and fav_ml <= -150:
        if (net_rating > 0 and fav_team == g["home"]) or (net_rating < 0 and fav_team == g["away"]):
            signal_text = f"🔒 BUY **{fav_team}** YES"
            confidence = "FORTRESS" if abs(net_rating) >= 30 else "STRONG"
            stars = "⭐⭐⭐" if abs(net_rating) >= 30 else "⭐⭐"
    elif period == 1 and abs(net_rating) >= 15 and fav_ml <= -150:
        if (net_rating > 0 and fav_team == g["home"]) or (net_rating < 0 and fav_team == g["away"]):
            signal_text = f"🔒 BUY **{fav_team}** YES"
            confidence = "STRONG" if abs(net_rating) >= 20 else "GOOD"
            stars = "⭐⭐"

    if signal_text:
        link = get_kalshi_game_link(g["away"], g["home"])
        signals.append({
            "game": f"{g['away']} @ {g['home']}",
            "period": period,
            "signal": signal_text,
            "stars": stars,
            "confidence": confidence,
            "net": net_rating,
            "lead": lead,
            "poss": poss,
            "link": link,
            "conf_color": conf_color
        })

if signals:
    for s in sorted(signals, key=lambda x: -x["period"]):
        st.markdown(f"""
        <div style="background:#0f172a;padding:20px;border-radius:16px;border:3px solid {s['conf_color']};margin-bottom:20px">
            <div style="font-size:26px;font-weight:bold;color:#ffd700">{s['game']} • Q{s['period']} END</div>
            <div style="font-size:36px;margin:12px 0">{s['signal']} {s['stars']}</div>
            <div style="color:#ccc">Net Rating: <b>{s['net']}</b> Lead: <b>{s['lead']:+}</b> Poss: <b>{s['poss']}</b></div>
            <div style="margin-top:16px;color:{s['conf_color']};font-weight:bold">{s['confidence']} CONFIDENCE</div>
            <a href="{s['link']}" target="_blank" style="background:#22c55e;color:#000;padding:14px 32px;border-radius:10px;text-decoration:none;font-weight:bold;display:inline-block;margin-top:12px">🎯 BUY ON KALSHI</a>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("⏳ Waiting for quarter ends… Signals appear automatically at 00:00")

st.divider()

# ====================== REST OF YOUR ORIGINAL APP ======================
# Paste everything from your original script starting at:
# st.subheader("🎯 CUSHION SCANNER (Totals)")
# all the way to the very end (position tracker, all games today, footer)

# (Copy-paste your original code from that point onward here)

st.caption(f"v{VERSION} • Educational only • Not financial advice")
st.caption("Stay small. Stay quiet. Win.")
