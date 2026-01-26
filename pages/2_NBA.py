import streamlit as st
from streamlit_autorefresh import st_autorefresh
import requests
import json
import uuid
import pytz
from datetime import datetime, timedelta

st.set_page_config(page_title="🏀 Edge Finder", page_icon="🏀", layout="wide")

try:
    from auth import require_auth
    require_auth()
except:
    pass

st_autorefresh(interval=24000)

def send_ga4(page_title, page_path):
    try:
        requests.post(
            "https://www.google-analytics.com/mp/collect?measurement_id=G-NQKY5VQ376&api_secret=n4oBJjH7RXi3dA7aQo2CZA",
            json={"client_id": str(uuid.uuid4()), "events": [{"name": "page_view", "params": {"page_title": page_title, "page_location": page_path}}]},
            timeout=2
        )
    except:
        pass

send_ga4("Edge Finder", "/edge")

eastern = pytz.timezone("US/Eastern")
now = datetime.now(eastern)
VERSION = "6.0"
LEAGUE_AVG = 228.7

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
    "Atlanta": "ATL", "Boston": "BOS", "Brooklyn": "BKN", "Charlotte": "CHA",
    "Chicago": "CHI", "Cleveland": "CLE", "Dallas": "DAL", "Denver": "DEN",
    "Detroit": "DET", "Golden State": "GSW", "Houston": "HOU", "Indiana": "IND",
    "LA Clippers": "LAC", "LA Lakers": "LAL", "Memphis": "MEM",
    "Miami": "MIA", "Milwaukee": "MIL", "Minnesota": "MIN",
    "New Orleans": "NOP", "New York": "NYK", "Oklahoma City": "OKC",
    "Orlando": "ORL", "Philadelphia": "PHI", "Phoenix": "PHX",
    "Portland": "POR", "Sacramento": "SAC", "San Antonio": "SAS",
    "Toronto": "TOR", "Utah": "UTA", "Washington": "WAS"
}

TEAM_STATS = {
    "Atlanta": {"net": -3.2, "pace": 100.5, "home_pct": 0.52, "tier": "weak"},
    "Boston": {"net": 11.2, "pace": 99.8, "home_pct": 0.78, "tier": "elite"},
    "Brooklyn": {"net": -4.5, "pace": 98.2, "home_pct": 0.42, "tier": "weak"},
    "Charlotte": {"net": -6.8, "pace": 99.5, "home_pct": 0.38, "tier": "weak"},
    "Chicago": {"net": -2.1, "pace": 98.8, "home_pct": 0.48, "tier": "weak"},
    "Cleveland": {"net": 8.5, "pace": 97.2, "home_pct": 0.75, "tier": "elite"},
    "Dallas": {"net": 4.2, "pace": 99.0, "home_pct": 0.62, "tier": "good"},
    "Denver": {"net": 5.8, "pace": 98.5, "home_pct": 0.72, "tier": "good"},
    "Detroit": {"net": -8.2, "pace": 97.8, "home_pct": 0.32, "tier": "weak"},
    "Golden State": {"net": 2.5, "pace": 100.2, "home_pct": 0.58, "tier": "mid"},
    "Houston": {"net": -1.5, "pace": 99.5, "home_pct": 0.55, "tier": "mid"},
    "Indiana": {"net": 3.8, "pace": 102.5, "home_pct": 0.58, "tier": "good"},
    "LA Clippers": {"net": 1.2, "pace": 97.8, "home_pct": 0.52, "tier": "mid"},
    "LA Lakers": {"net": 2.8, "pace": 98.5, "home_pct": 0.62, "tier": "mid"},
    "Memphis": {"net": 1.5, "pace": 99.8, "home_pct": 0.55, "tier": "mid"},
    "Miami": {"net": 0.5, "pace": 97.2, "home_pct": 0.58, "tier": "mid"},
    "Milwaukee": {"net": 4.5, "pace": 98.8, "home_pct": 0.65, "tier": "good"},
    "Minnesota": {"net": 5.2, "pace": 98.2, "home_pct": 0.68, "tier": "good"},
    "New Orleans": {"net": -2.8, "pace": 99.0, "home_pct": 0.48, "tier": "weak"},
    "New York": {"net": 6.8, "pace": 97.5, "home_pct": 0.72, "tier": "good"},
    "Oklahoma City": {"net": 9.5, "pace": 98.8, "home_pct": 0.78, "tier": "elite"},
    "Orlando": {"net": 2.2, "pace": 96.8, "home_pct": 0.58, "tier": "mid"},
    "Philadelphia": {"net": 1.8, "pace": 97.5, "home_pct": 0.55, "tier": "mid"},
    "Phoenix": {"net": 0.8, "pace": 98.2, "home_pct": 0.52, "tier": "mid"},
    "Portland": {"net": -5.5, "pace": 98.8, "home_pct": 0.42, "tier": "weak"},
    "Sacramento": {"net": -1.2, "pace": 100.5, "home_pct": 0.52, "tier": "mid"},
    "San Antonio": {"net": -8.5, "pace": 99.2, "home_pct": 0.35, "tier": "weak"},
    "Toronto": {"net": -3.8, "pace": 97.8, "home_pct": 0.45, "tier": "weak"},
    "Utah": {"net": -6.2, "pace": 98.5, "home_pct": 0.38, "tier": "weak"},
    "Washington": {"net": -9.5, "pace": 100.8, "home_pct": 0.28, "tier": "weak"}
}

STAR_PLAYERS = {
    "Boston": ["Jayson Tatum", "Jaylen Brown", "Derrick White"],
    "Cleveland": ["Donovan Mitchell", "Darius Garland", "Evan Mobley"],
    "Oklahoma City": ["Shai Gilgeous-Alexander", "Chet Holmgren", "Jalen Williams"],
    "New York": ["Jalen Brunson", "Karl-Anthony Towns", "Mikal Bridges"],
    "Milwaukee": ["Giannis Antetokounmpo", "Damian Lillard"],
    "Minnesota": ["Anthony Edwards", "Rudy Gobert"],
    "Dallas": ["Luka Doncic", "Kyrie Irving"],
    "LA Lakers": ["LeBron James", "Anthony Davis"],
    "Miami": ["Jimmy Butler", "Bam Adebayo"],
    "Philadelphia": ["Joel Embiid", "Tyrese Maxey"],
    "Memphis": ["Ja Morant", "Jaren Jackson Jr"],
    "Sacramento": ["De'Aaron Fox", "Domantas Sabonis"],
    "Indiana": ["Tyrese Haliburton", "Pascal Siakam"],
    "Houston": ["Jalen Green", "Alperen Sengun"],
    "Atlanta": ["Trae Young", "Dejounte Murray"],
    "Charlotte": ["LaMelo Ball", "Brandon Miller"],
    "Detroit": ["Cade Cunningham", "Jaden Ivey"],
    "Toronto": ["Scottie Barnes", "RJ Barrett"],
    "Brooklyn": ["Mikal Bridges", "Cameron Johnson"],
    "San Antonio": ["Victor Wembanyama", "Devin Vassell"],
    "Utah": ["Lauri Markkanen", "Collin Sexton"],
    "Portland": ["Anfernee Simons", "Scoot Henderson"],
    "Washington": ["Jordan Poole", "Kyle Kuzma"],
    "Denver": ["Nikola Jokic", "Jamal Murray"],
    "Phoenix": ["Kevin Durant", "Devin Booker"],
    "Golden State": ["Stephen Curry", "Draymond Green"],
    "LA Clippers": ["Kawhi Leonard", "Paul George"],
    "Orlando": ["Paolo Banchero", "Franz Wagner"],
    "Chicago": ["Zach LaVine", "Coby White"],
    "New Orleans": ["Zion Williamson", "Brandon Ingram"]
}

STAR_TIERS = {
    "Nikola Jokic": 3, "Shai Gilgeous-Alexander": 3, "Giannis Antetokounmpo": 3,
    "Luka Doncic": 3, "Joel Embiid": 3, "Jayson Tatum": 3, "LeBron James": 3,
    "Stephen Curry": 3, "Kevin Durant": 3, "Anthony Edwards": 3,
    "Donovan Mitchell": 2, "Jaylen Brown": 2, "Damian Lillard": 2, "Jimmy Butler": 2,
    "Anthony Davis": 2, "Kyrie Irving": 2, "Devin Booker": 2, "Ja Morant": 2,
    "Trae Young": 2, "Zion Williamson": 2, "Tyrese Haliburton": 2, "De'Aaron Fox": 2,
    "Jalen Brunson": 2, "Chet Holmgren": 2, "Paolo Banchero": 2, "Franz Wagner": 2,
    "Victor Wembanyama": 2, "Evan Mobley": 2, "LaMelo Ball": 2, "Cade Cunningham": 2,
    "Tyrese Maxey": 2, "Bam Adebayo": 2, "Karl-Anthony Towns": 2
}

@st.cache_data(ttl=60)
def fetch_all():
    today = now.strftime('%Y%m%d')
    games = requests.get(f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={today}").json()
    
    injury_map = {}
    try:
        injuries = requests.get("https://site.api.espn.com/apis/site/v2/sports/basketball/nba/injuries").json()
        for team in injuries.get("injuries", []):
            team_name = team.get("team", {}).get("displayName", "")
            short = TEAM_ABBREVS.get(team_name, team_name)
            injury_map[short] = [{"name": i.get("athlete", {}).get("displayName", ""), "status": i.get("status", "")} for i in team.get("injuries", [])]
    except:
        pass
    
    yesterday = (now - timedelta(days=1)).strftime('%Y%m%d')
    b2b_teams = set()
    try:
        b2b_resp = requests.get(f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={yesterday}").json()
        for event in b2b_resp.get("events", []):
            for comp in event.get("competitions", []):
                for team in comp.get("competitors", []):
                    team_name = team.get("team", {}).get("displayName", "")
                    short = TEAM_ABBREVS.get(team_name, team_name)
                    b2b_teams.add(short)
    except:
        pass
    
    return games, injury_map, b2b_teams

games, injuries, b2b_teams = fetch_all()

def get_ml_link(away, home):
    a = KALSHI_CODES.get(away, "XXX").lower()
    h = KALSHI_CODES.get(home, "XXX").lower()
    date = now.strftime('%y%b%d').lower()
    return f"https://kalshi.com/markets/kxnbagame/professional-basketball-game/kxnbagame-{date}{a}{h}"

def get_totals_link(away, home):
    a = KALSHI_CODES.get(away, "XXX").lower()
    h = KALSHI_CODES.get(home, "XXX").lower()
    date = now.strftime('%y%b%d').lower()
    return f"https://kalshi.com/markets/kxnbatotal/pro-basketball-total-points/kxnbatotal-{date}{a}{h}"

def get_spread_link(away, home, line=1.5):
    a = KALSHI_CODES.get(away, "XXX").lower()
    h = KALSHI_CODES.get(home, "XXX").lower()
    date = now.strftime('%y%b%d').lower()
    if line > 0:
        return f"https://kalshi.com/markets/kxnbasprd/pro-basketball-spread/kxnbasprd-{date}{h}{a}ovr{abs(line)}"
    else:
        return f"https://kalshi.com/markets/kxnbasprd/pro-basketball-spread/kxnbasprd-{date}{a}{h}ovr{abs(line)}"

def calc_edge(away, home):
    base = 50
    
    # B2B adjustment
    if away in b2b_teams:
        base += 3
    if home in b2b_teams:
        base -= 2
    
    # Injury adjustment
    home_stars = STAR_PLAYERS.get(home, [])
    for s in home_stars:
        for inj in injuries.get(home, []):
            if s.lower() in inj.get("name", "").lower():
                status = inj.get("status", "").upper()
                if "OUT" in status or "DOUBT" in status:
                    base -= STAR_TIERS.get(s, 1) * 2
    
    away_stars = STAR_PLAYERS.get(away, [])
    for s in away_stars:
        for inj in injuries.get(away, []):
            if s.lower() in inj.get("name", "").lower():
                status = inj.get("status", "").upper()
                if "OUT" in status or "DOUBT" in status:
                    base += STAR_TIERS.get(s, 1) * 2
    
    # Net rating + home court
    home_net = TEAM_STATS.get(home, {}).get("net", 0)
    away_net = TEAM_STATS.get(away, {}).get("net", 0)
    base += (home_net - away_net) + 2.5
    
    pick = home if base > 50 else away
    score = round(base)
    conf = min(100, max(50, int(50 + abs(base - 50) * 1.5)))
    edge_cents = max(1, abs(base - 50) * 0.3)
    
    return pick, score, conf, round(edge_cents, 1)

# --- UI ---
st.title("🏀 Edge Finder")
st.caption(f"v{VERSION} • {now.strftime('%I:%M %p')} ET")

games_live = []
games_sched = []

for event in games.get("events", []):
    comps = event.get("competitions", [])
    if not comps:
        continue
    comp = comps[0]
    competitors = comp.get("competitors", [])
    if len(competitors) < 2:
        continue
    
    away_team = None
    home_team = None
    for team in competitors:
        if team.get("homeAway") == "away":
            away_team = team.get("team", {}).get("displayName", "")
        else:
            home_team = team.get("team", {}).get("displayName", "")
    
    if not away_team or not home_team:
        continue
    
    a = TEAM_ABBREVS.get(away_team)
    h = TEAM_ABBREVS.get(home_team)
    if not a or not h:
        continue
    
    status = comp.get("status", {}).get("type", {}).get("name", "")
    if status == "STATUS_SCHEDULED":
        games_sched.append((a, h))
    elif status in ["STATUS_IN_PROGRESS", "STATUS_HALFTIME"]:
        games_live.append((a, h))

if games_live:
    st.subheader("🔴 LIVE GAMES")
    for a, h in games_live:
        pick, score, conf, cents = calc_edge(a, h)
        col = "🟢" if score >= 70 else "🟡" if score >= 60 else "⚪"
        st.markdown(f"### {col} BUY: {pick} to win | {score}/100")
        st.caption(f"Confidence: {conf}% • Edge: {cents}¢")
        cols = st.columns(5)
        cols[0].link_button("ML", get_ml_link(a, h))
        cols[1].link_button("+1.5", get_spread_link(a, h, 1.5))
        cols[2].link_button("-1.5", get_spread_link(a, h, -1.5))
        cols[3].link_button("Over", get_totals_link(a, h))
        cols[4].link_button("Under", get_totals_link(a, h))

if games_sched:
    st.subheader("🎯 BEST EDGE")
    top = max(games_sched, key=lambda g: calc_edge(g[0], g[1])[1])
    a, h = top
    pick, score, conf, cents = calc_edge(a, h)
    st.markdown(f"### 🟢 BUY: {pick} to win | {score}/100")
    st.caption(f"Confidence: {conf}% • Edge: {cents}¢")
    cols = st.columns(5)
    cols[0].link_button("ML", get_ml_link(a, h))
    cols[1].link_button("+1.5", get_spread_link(a, h, 1.5))
    cols[2].link_button("-1.5", get_spread_link(a, h, -1.5))
    cols[3].link_button("Over", get_totals_link(a, h))
    cols[4].link_button("Under", get_totals_link(a, h))
    
    st.divider()
    st.subheader("📋 ALL GAMES")
    for a, h in games_sched:
        pick, score, conf, cents = calc_edge(a, h)
        col = "🟢" if score >= 70 else "🟡" if score >= 60 else "⚪"
        with st.expander(f"{col} {a} @ {h} — {pick} ({score}/100)"):
            st.caption(f"Confidence: {conf}% • Edge: {cents}¢")
            cols = st.columns(5)
            cols[0].link_button("ML", get_ml_link(a, h))
            cols[1].link_button("+1.5", get_spread_link(a, h, 1.5))
            cols[2].link_button("-1.5", get_spread_link(a, h, -1.5))
            cols[3].link_button("Over", get_totals_link(a, h))
            cols[4].link_button("Under", get_totals_link(a, h))

if not games_live and not games_sched:
    st.info("No NBA games scheduled today.")

st.divider()
st.caption("Stay small. Stay quiet. Win.")
