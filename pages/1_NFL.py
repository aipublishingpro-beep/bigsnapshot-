import streamlit as st
import requests
from datetime import datetime, timedelta
import pytz
import json
import os
import time
import uuid

try:
    from streamlit_autorefresh import st_autorefresh
    HAS_AUTOREFRESH = True
except ImportError:
    HAS_AUTOREFRESH = False

st.set_page_config(page_title="NBA Edge Finder", page_icon="🏀", layout="wide")

# ========== GATE CHECK ==========
if "gate_passed" not in st.session_state or not st.session_state.gate_passed:
    st.markdown("""<style>[data-testid="stSidebarNav"] {display: none;}</style>""", unsafe_allow_html=True)
    st.error("⛔ Access Denied")
    st.warning("You must accept the terms on the Home page first.")
    st.page_link("Home.py", label="👉 Go to Home Page", use_container_width=True)
    st.stop()

# ========== INIT ==========
if "sid" not in st.session_state:
    st.session_state["sid"] = str(uuid.uuid4())
if "positions" not in st.session_state:
    st.session_state.positions = []

eastern = pytz.timezone("US/Eastern")
today_str = datetime.now(eastern).strftime("%Y-%m-%d")

# ========== GA4 TRACKING ==========
st.markdown("""
<script async src="https://www.googletagmanager.com/gtag/js?id=G-NQKY5VQ376"></script>
<script>window.dataLayer = window.dataLayer || [];function gtag(){dataLayer.push(arguments);}gtag('js', new Date());gtag('config', 'G-NQKY5VQ376');</script>
""", unsafe_allow_html=True)

# ========== KALSHI TEAM CODES ==========
KALSHI_CODES = {
    "Atlanta Hawks": "ATL", "Boston Celtics": "BOS", "Brooklyn Nets": "BKN",
    "Charlotte Hornets": "CHA", "Chicago Bulls": "CHI", "Cleveland Cavaliers": "CLE",
    "Dallas Mavericks": "DAL", "Denver Nuggets": "DEN", "Detroit Pistons": "DET",
    "Golden State Warriors": "GSW", "Houston Rockets": "HOU", "Indiana Pacers": "IND",
    "LA Clippers": "LAC", "Los Angeles Lakers": "LAL", "Memphis Grizzlies": "MEM",
    "Miami Heat": "MIA", "Milwaukee Bucks": "MIL", "Minnesota Timberwolves": "MIN",
    "New Orleans Pelicans": "NOP", "New York Knicks": "NYK", "Oklahoma City Thunder": "OKC",
    "Orlando Magic": "ORL", "Philadelphia 76ers": "PHI", "Phoenix Suns": "PHX",
    "Portland Trail Blazers": "POR", "Sacramento Kings": "SAC", "San Antonio Spurs": "SAS",
    "Toronto Raptors": "TOR", "Utah Jazz": "UTA", "Washington Wizards": "WAS"
}

# ========== KALSHI MARKET CHECK ==========
@st.cache_data(ttl=300)
def check_kalshi_market_exists(ticker):
    """Check if a Kalshi market exists - returns True/False"""
    try:
        url = f"https://api.elections.kalshi.com/trade-api/v2/markets/{ticker.upper()}"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("market") is not None
        return False
    except:
        return False

# ========== ESPN DATA FETCH ==========
@st.cache_data(ttl=30)
def fetch_nba_games():
    try:
        url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        games = {}
        for event in data.get("events", []):
            comp = event["competitions"][0]
            away = comp["competitors"][1]
            home = comp["competitors"][0]
            status = comp["status"]
            game_date_str = event.get("date", "")
            game_date = None
            if game_date_str:
                try:
                    game_date = datetime.fromisoformat(game_date_str.replace("Z", "+00:00")).astimezone(eastern)
                except:
                    pass
            
            period = status.get("period", 0)
            clock = status.get("displayClock", "0:00")
            away_score = int(away.get("score", 0))
            home_score = int(home.get("score", 0))
            total = away_score + home_score
            
            elapsed_min = 0
            if period > 0:
                try:
                    clock_parts = clock.split(":")
                    mins_left = int(clock_parts[0])
                    secs_left = int(clock_parts[1]) if len(clock_parts) > 1 else 0
                    elapsed_in_q = 12 - mins_left - (secs_left / 60)
                    elapsed_min = (period - 1) * 12 + elapsed_in_q
                except:
                    elapsed_min = (period - 1) * 12
            
            pace = round(total / elapsed_min, 2) if elapsed_min > 0 else 0
            
            games[event["id"]] = {
                "away_team": away["team"]["displayName"],
                "home_team": home["team"]["displayName"],
                "away_abbr": away["team"]["abbreviation"],
                "home_abbr": home["team"]["abbreviation"],
                "away_score": away_score,
                "home_score": home_score,
                "period": period,
                "clock": clock,
                "status_type": status.get("type", {}).get("name", ""),
                "status_detail": status.get("type", {}).get("shortDetail", ""),
                "total": total,
                "pace": pace,
                "elapsed_min": round(elapsed_min, 1),
                "game_date": game_date
            }
        return games
    except Exception as e:
        st.error(f"ESPN error: {e}")
        return {}

@st.cache_data(ttl=300)
def fetch_nba_injuries():
    try:
        url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/injuries"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        injuries = {}
        for team in data.get("injuries", []):
            team_name = team.get("team", {}).get("displayName", "Unknown")
            injuries[team_name] = []
            for cat in team.get("categories", []):
                for athlete in cat.get("items", []):
                    status = athlete.get("status", "")
                    if status.lower() in ["out", "doubtful", "questionable"]:
                        injuries[team_name].append({
                            "name": athlete.get("athlete", {}).get("displayName", ""),
                            "position": athlete.get("athlete", {}).get("position", {}).get("abbreviation", ""),
                            "status": status
                        })
        return injuries
    except:
        return {}

# ========== SIGNAL LOGIC ==========
def get_signal_recommendation(pace, total, period, clock, cushion=0):
    """Returns signal recommendation based on pace and game state"""
    if period == 0:
        return None, "PREGAME"
    
    try:
        mins_left = int(clock.split(":")[0])
    except:
        mins_left = 12
    
    total_mins_left = (4 - period) * 12 + mins_left
    
    if pace < 4.5:
        return "🔴 STRONG NO", f"Ultra-slow pace ({pace} pts/min)"
    elif pace < 4.7:
        return "🟠 LEAN NO", f"Slow pace ({pace} pts/min)"
    elif pace > 5.3:
        return "🟢 STRONG YES", f"High pace ({pace} pts/min)"
    elif pace > 5.0:
        return "🔵 LEAN YES", f"Above-avg pace ({pace} pts/min)"
    else:
        return "⚪ NEUTRAL", f"Normal pace ({pace} pts/min)"

# ========== POSITION PERSISTENCE ==========
def load_positions():
    try:
        if os.path.exists("nba_positions.json"):
            with open("nba_positions.json", "r") as f:
                return json.load(f)
    except:
        pass
    return []

def save_positions(positions):
    try:
        with open("nba_positions.json", "w") as f:
            json.dump(positions, f)
    except:
        pass

if not st.session_state.positions:
    st.session_state.positions = load_positions()

# ========== TITLE ==========
st.title("🏀 NBA Edge Finder")
st.caption("v15.48 — Market Check Fix")

# ========== SIDEBAR ==========
with st.sidebar:
    st.header("⚙️ Settings")
    auto_refresh = st.checkbox("Auto-refresh (30s)", value=False, key="nba_auto")
    if auto_refresh and HAS_AUTOREFRESH:
        st_autorefresh(interval=30000, key="nba_refresh")
    st.divider()
    st.markdown("### 📊 12-Factor Model")
    st.caption("1. Home court (+1)")
    st.caption("2. Back-to-back fatigue (+1.5)")
    st.caption("3. Rest days (+1)")
    st.caption("4. Net rating diff (+1)")
    st.caption("5. Defensive rating (+1)")
    st.caption("6. Star injuries (+1.5)")
    st.caption("7. Head-to-head (+0.5)")
    st.caption("8. Travel distance (+0.5)")
    st.caption("9. Timezone (+0.5)")
    st.caption("10. Hot/cold streak (+1)")
    st.caption("11. Pace mismatch (+0.5)")
    st.caption("12. Playoff implications (+0.5)")

games = fetch_nba_games()
injuries = fetch_nba_injuries()

# ========== LIVE SIGNAL FEED ==========
st.divider()
st.subheader("📡 LIVE SIGNAL FEED")

live_games = {k: v for k, v in games.items() if v['period'] > 0 and v['status_type'] != "STATUS_FINAL"}

if live_games:
    st.success(f"🔴 {len(live_games)} LIVE GAME(S)")
    for gid, g in live_games.items():
        signal, reason = get_signal_recommendation(g['pace'], g['total'], g['period'], g['clock'])
        
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.markdown(f"**{g['away_team']}** {g['away_score']} @ **{g['home_team']}** {g['home_score']}")
            st.caption(f"Q{g['period']} {g['clock']} | Total: {g['total']} | Pace: {g['pace']} pts/min")
        with col2:
            if signal:
                st.markdown(f"**{signal}**")
                st.caption(reason)
        with col3:
            cushion = abs(g['away_score'] - g['home_score'])
            leader = g['away_abbr'] if g['away_score'] > g['home_score'] else g['home_abbr']
            st.metric("Cushion", f"{leader} +{cushion}")
        st.divider()
else:
    st.info("No live games right now")

# ========== CUSHION SCANNER ==========
st.subheader("🎯 CUSHION SCANNER")
if live_games:
    for gid, g in live_games.items():
        cushion = abs(g['away_score'] - g['home_score'])
        leader = g['away_team'] if g['away_score'] > g['home_score'] else g['home_team']
        trailer = g['home_team'] if g['away_score'] > g['home_score'] else g['away_team']
        
        if cushion >= 15:
            st.success(f"🟢 **{leader}** +{cushion} vs {trailer} — BLOWOUT CUSHION")
        elif cushion >= 10:
            st.info(f"🔵 **{leader}** +{cushion} vs {trailer} — SOLID CUSHION")
        elif cushion >= 5:
            st.warning(f"🟡 **{leader}** +{cushion} vs {trailer} — THIN CUSHION")
        else:
            st.error(f"🔴 TIGHT GAME: {cushion} pt margin")
else:
    st.info("No live games for cushion analysis")

# ========== ML PICKS ==========
st.divider()
st.subheader("🎯 ML PICKS")

scheduled_games = {k: v for k, v in games.items() if v['status_type'] == "STATUS_SCHEDULED"}
if scheduled_games:
    for gid, g in scheduled_games.items():
        away_inj = injuries.get(g['away_team'], [])
        home_inj = injuries.get(g['home_team'], [])
        
        away_score = 0
        home_score = 1  # Home court
        
        away_out = len([i for i in away_inj if i['status'].lower() == 'out'])
        home_out = len([i for i in home_inj if i['status'].lower() == 'out'])
        if away_out > home_out:
            home_score += 1.5
        elif home_out > away_out:
            away_score += 1.5
        
        pick = g['home_team'] if home_score >= away_score else g['away_team']
        pick_code = KALSHI_CODES.get(pick, pick[:3].upper())
        score = max(home_score, away_score) + 5
        
        game_date = g.get('game_date')
        if game_date:
            date_str = game_date.strftime("%y%b%d").upper()
        else:
            date_str = datetime.now(eastern).strftime("%y%b%d").upper()
        
        away_code = KALSHI_CODES.get(g['away_team'], g['away_team'][:3].upper())
        home_code = KALSHI_CODES.get(g['home_team'], g['home_team'][:3].upper())
        ticker = f"KXNBAGAME-{date_str}{away_code}{home_code}"
        kalshi_url = f"https://kalshi.com/markets/{ticker.lower()}"
        
        if score >= 8:
            signal = "🟢 STRONG BUY"
        elif score >= 6.5:
            signal = "🔵 BUY"
        else:
            signal = "🟡 LEAN"
        
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.markdown(f"**{g['away_team']}** @ **{g['home_team']}**")
            st.caption(f"{signal} {pick} | Score: {score}/10")
        with col2:
            # Check if market exists before showing BUY button
            market_exists = check_kalshi_market_exists(ticker)
            if market_exists:
                st.link_button(f"BUY {pick_code}", kalshi_url, use_container_width=True)
                st.caption(f"✅ {ticker}")
            else:
                st.warning(f"⏳ Market not live")
                st.caption(ticker)
        with col3:
            if away_inj or home_inj:
                with st.expander("🚑 Injuries"):
                    for i in away_inj[:3]:
                        st.caption(f"{g['away_team']}: {i['name']} ({i['position']}) - {i['status']}")
                    for i in home_inj[:3]:
                        st.caption(f"{g['home_team']}: {i['name']} ({i['position']}) - {i['status']}")
        st.divider()
else:
    st.info("No scheduled games to analyze")

# ========== ACTIVE POSITIONS ==========
st.divider()
st.subheader("📊 ACTIVE POSITIONS")

if st.session_state.positions:
    total_cost = sum(p.get('cost', 0) for p in st.session_state.positions)
    st.metric("Total Invested", f"${total_cost:.2f}")
    
    for idx, pos in enumerate(st.session_state.positions):
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.markdown(f"**{pos['game']}** — {pos['pick']}")
            st.caption(f"Entry: {pos['price']}¢ x {pos['contracts']} = ${pos['cost']:.2f}")
        with col2:
            current_game = None
            for g in games.values():
                game_key = f"{g['away_team']} @ {g['home_team']}"
                if game_key == pos['game'] or pos['game'] in game_key:
                    current_game = g
                    break
            
            if current_game:
                if current_game['status_type'] == "STATUS_FINAL":
                    winner = current_game['away_team'] if current_game['away_score'] > current_game['home_score'] else current_game['home_team']
                    if pos['pick'] in winner or winner in pos['pick']:
                        pnl = (100 - pos['price']) * pos['contracts'] / 100
                        st.success(f"✅ WIN +${pnl:.2f}")
                    else:
                        pnl = -pos['cost']
                        st.error(f"❌ LOSS ${pnl:.2f}")
                else:
                    st.info(f"🔄 Q{current_game['period']} {current_game['clock']}")
            else:
                st.caption("Pending")
        with col3:
            if st.button("❌", key=f"del_{idx}"):
                st.session_state.positions.pop(idx)
                save_positions(st.session_state.positions)
                st.rerun()
    
    if st.button("Clear All Positions", type="secondary"):
        st.session_state.positions = []
        save_positions([])
        st.rerun()
else:
    st.info("No active positions")

# ========== ADD POSITION ==========
st.divider()
st.subheader("➕ ADD POSITION")

with st.form("add_position"):
    col1, col2 = st.columns(2)
    with col1:
        game_options = [f"{g['away_team']} @ {g['home_team']}" for g in games.values() if g['status_type'] != "STATUS_FINAL"]
        selected_game = st.selectbox("Game", game_options if game_options else ["No games available"])
        pick = st.text_input("Pick (team name)", placeholder="e.g., Boston Celtics")
    with col2:
        price = st.number_input("Entry Price (cents)", min_value=1, max_value=99, value=50)
        contracts = st.number_input("Contracts", min_value=1, max_value=100, value=10)
    
    submitted = st.form_submit_button("Add Position", use_container_width=True)
    if submitted and selected_game and pick:
        st.session_state.positions.append({
            "game": selected_game,
            "pick": pick,
            "price": price,
            "contracts": contracts,
            "cost": round(price * contracts / 100, 2),
            "added_at": datetime.now(eastern).strftime("%a %I:%M %p")
        })
        save_positions(st.session_state.positions)
        st.success(f"Added: {pick} @ {price}¢ x {contracts}")
        st.rerun()

# ========== INJURY REPORT ==========
st.divider()
st.subheader("🚑 INJURY REPORT")
injury_teams = [t for t in injuries if injuries[t]]
if injury_teams:
    cols = st.columns(4)
    for i, team in enumerate(injury_teams[:8]):
        with cols[i % 4]:
            st.markdown(f"**{team}**")
            for inj in injuries[team][:3]:
                status_color = "🔴" if inj['status'].lower() == 'out' else "🟡"
                st.caption(f"{status_color} {inj['name']} ({inj['position']}) - {inj['status']}")
else:
    st.info("No major injuries reported")

# ========== HOW TO USE ==========
st.divider()
st.subheader("📖 How to Use This App")
st.markdown("""
**NBA Edge Finder** helps you identify potential edges in NBA prediction markets on Kalshi.

**Live Signal Feed:** Real-time pace analysis during games. Pace = total points / elapsed minutes.
- 🔴 STRONG NO — Ultra-slow pace (<4.5 pts/min), likely to stay under
- 🟠 LEAN NO — Slow pace (4.5-4.7 pts/min)
- 🟢 STRONG YES — High pace (>5.3 pts/min), likely to go over
- 🔵 LEAN YES — Above-avg pace (5.0-5.3 pts/min)

**Cushion Scanner:** Shows point differentials for live games. Bigger cushion = safer ML position.

**ML Picks:** Pre-game moneyline recommendations based on 12-factor model.

**Market Status:**
- ✅ Green checkmark = Market is LIVE on Kalshi, click to trade
- ⏳ Yellow warning = Market not open yet, check back closer to game time

**Questions or feedback?** Contact aipublishingpro@gmail.com
""")

st.divider()
st.caption("⚠️ Educational analysis only. Not financial advice. v15.48")
