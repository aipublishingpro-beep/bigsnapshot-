import streamlit as st
from streamlit_autorefresh import st_autorefresh
import streamlit.components.v1 as components

st.set_page_config(page_title="BigSnapshot Spread Edge Finder", page_icon="🎯", layout="wide")

from auth import require_auth
require_auth()

st_autorefresh(interval=30000, key="spreadrefresh")

import uuid
import requests as req_ga

def send_ga4_event(page_title, page_path):
    try:
        url = "https://www.google-analytics.com/mp/collect?measurement_id=G-NQKY5VQ376&api_secret=n4oBJjH7RXi0dA7aQo2CZA"
        payload = {"client_id": str(uuid.uuid4()), "events": [{"name": "page_view", "params": {"page_title": page_title, "page_location": "https://bigsnapshot.streamlit.app" + page_path}}]}
        req_ga.post(url, json=payload, timeout=2)
    except: pass

send_ga4_event("BigSnapshot Spread Edge Finder", "/Spreads")

import requests, re
from datetime import datetime, timedelta
import pytz

eastern = pytz.timezone("US/Eastern")
now = datetime.now(eastern)

VERSION = "1.0"
MIN_UNDERDOG_LEAD = 7
MIN_SPREAD_BRACKET = 10
MAX_NO_PRICE = 85
MIN_WP_EDGE = 8
LEAD_BY_QUARTER = {1: 7, 2: 8, 3: 10, 4: 13}

TEAM_ABBREVS = {"Atlanta Hawks": "Atlanta", "Boston Celtics": "Boston", "Brooklyn Nets": "Brooklyn", "Charlotte Hornets": "Charlotte", "Chicago Bulls": "Chicago", "Cleveland Cavaliers": "Cleveland", "Dallas Mavericks": "Dallas", "Denver Nuggets": "Denver", "Detroit Pistons": "Detroit", "Golden State Warriors": "Golden State", "Houston Rockets": "Houston", "Indiana Pacers": "Indiana", "LA Clippers": "LA Clippers", "Los Angeles Clippers": "LA Clippers", "LA Lakers": "LA Lakers", "Los Angeles Lakers": "LA Lakers", "Memphis Grizzlies": "Memphis", "Miami Heat": "Miami", "Milwaukee Bucks": "Milwaukee", "Minnesota Timberwolves": "Minnesota", "New Orleans Pelicans": "New Orleans", "New York Knicks": "New York", "Oklahoma City Thunder": "Oklahoma City", "Orlando Magic": "Orlando", "Philadelphia 76ers": "Philadelphia", "Phoenix Suns": "Phoenix", "Portland Trail Blazers": "Portland", "Sacramento Kings": "Sacramento", "San Antonio Spurs": "San Antonio", "Toronto Raptors": "Toronto", "Utah Jazz": "Utah", "Washington Wizards": "Washington"}

KALSHI_CODES = {"Atlanta": "ATL", "Boston": "BOS", "Brooklyn": "BKN", "Charlotte": "CHA", "Chicago": "CHI", "Cleveland": "CLE", "Dallas": "DAL", "Denver": "DEN", "Detroit": "DET", "Golden State": "GSW", "Houston": "HOU", "Indiana": "IND", "LA Clippers": "LAC", "LA Lakers": "LAL", "Memphis": "MEM", "Miami": "MIA", "Milwaukee": "MIL", "Minnesota": "MIN", "New Orleans": "NOP", "New York": "NYK", "Oklahoma City": "OKC", "Orlando": "ORL", "Philadelphia": "PHI", "Phoenix": "PHX", "Portland": "POR", "Sacramento": "SAC", "San Antonio": "SAS", "Toronto": "TOR", "Utah": "UTA", "Washington": "WAS"}

TEAM_COLORS = {"Atlanta": "#E03A3E", "Boston": "#007A33", "Brooklyn": "#000000", "Charlotte": "#1D1160", "Chicago": "#CE1141", "Cleveland": "#860038", "Dallas": "#00538C", "Denver": "#0E2240", "Detroit": "#C8102E", "Golden State": "#1D428A", "Houston": "#CE1141", "Indiana": "#002D62", "LA Clippers": "#C8102E", "LA Lakers": "#552583", "Memphis": "#5D76A9", "Miami": "#98002E", "Milwaukee": "#00471B", "Minnesota": "#0C2340", "New Orleans": "#0C2340", "New York": "#006BB6", "Oklahoma City": "#007AC1", "Orlando": "#0077C0", "Philadelphia": "#006BB6", "Phoenix": "#1D1160", "Portland": "#E03A3E", "Sacramento": "#5A2D81", "San Antonio": "#C4CED4", "Toronto": "#CE1141", "Utah": "#002B5C", "Washington": "#002B5C"}

ESPN_TEAM_IDS = {"Atlanta": "1", "Boston": "2", "Brooklyn": "17", "Charlotte": "30", "Chicago": "4", "Cleveland": "5", "Dallas": "6", "Denver": "7", "Detroit": "8", "Golden State": "9", "Houston": "10", "Indiana": "11", "LA Clippers": "12", "LA Lakers": "13", "Memphis": "29", "Miami": "14", "Milwaukee": "15", "Minnesota": "16", "New Orleans": "3", "New York": "18", "Oklahoma City": "25", "Orlando": "19", "Philadelphia": "20", "Phoenix": "21", "Portland": "22", "Sacramento": "23", "San Antonio": "24", "Toronto": "28", "Utah": "26", "Washington": "27"}

if 'sniper_alerts' not in st.session_state:
    st.session_state.sniper_alerts = []
if 'comeback_alerts' not in st.session_state:
    st.session_state.comeback_alerts = []
if 'comeback_tracking' not in st.session_state:
    st.session_state.comeback_tracking = {}
if 'alerted_games' not in st.session_state:
    st.session_state.alerted_games = set()
if 'comeback_alerted' not in st.session_state:
    st.session_state.comeback_alerted = set()

# ============================================================
# HELPERS
# ============================================================
def american_to_implied_prob(odds):
    if odds is None: return None
    if odds > 0: return 100 / (odds + 100)
    else: return abs(odds) / (abs(odds) + 100)

def parse_record(s):
    try:
        p = s.split("-")
        return int(p[0]), int(p[1])
    except:
        return 0, 0

def get_favorite_side(hr, ar, hml=0):
    if hml != 0:
        return "home" if hml < 0 else "away"
    hw, hl = parse_record(hr)
    aw, al = parse_record(ar)
    hp = hw / (hw + hl) if (hw + hl) > 0 else 0.5
    ap = aw / (aw + al) if (aw + al) > 0 else 0.5
    return "home" if hp >= ap else "away"

def get_kalshi_game_link(away_code, home_code):
    date_str = datetime.now(eastern).strftime('%y%b%d').lower()
    return "https://kalshi.com/markets/kxnbaspread/nba-spread/kxnbaspread-" + date_str + away_code.lower() + home_code.lower()

def get_kalshi_ml_link(away_code, home_code):
    date_str = datetime.now(eastern).strftime('%y%b%d').lower()
    return "https://kalshi.com/markets/kxnbagame/professional-basketball-game/kxnbagame-" + date_str + away_code.lower() + home_code.lower()

# ============================================================
# ESPN DATA
# ============================================================
@st.cache_data(ttl=30)
def fetch_espn_games():
    today = datetime.now(eastern).strftime('%Y%m%d')
    url = "https://site.web.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates=" + today
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        games = []
        for ev in data.get("events", []):
            try:
                comp = ev["competitions"][0]
                status = comp["status"]
                state = status.get("type", {}).get("state", "pre")
                period = status.get("period", 0)
                clock = status.get("displayClock", "0:00")
                detail = status.get("type", {}).get("shortDetail", "")
                teams = {}
                for t in comp["competitors"]:
                    ha = t.get("homeAway", "home")
                    rec = ""
                    if t.get("records") and len(t["records"]) > 0:
                        rec = t["records"][0].get("summary", "")
                    full_name = t["team"].get("displayName", "")
                    short_name = TEAM_ABBREVS.get(full_name, full_name)
                    teams[ha] = {
                        "id": t["team"]["id"],
                        "abbrev": t["team"].get("abbreviation", "???"),
                        "name": full_name,
                        "short_name": short_name,
                        "score": int(t.get("score", 0) or 0),
                        "record": rec
                    }
                home, away = teams.get("home", {}), teams.get("away", {})
                hml = 0
                odds = comp.get("odds", [])
                spread_val = None
                if odds:
                    for o in odds:
                        if "homeTeamOdds" in o:
                            hml = o["homeTeamOdds"].get("moneyLine", 0) or 0
                        if o.get("spread"):
                            try: spread_val = float(o["spread"])
                            except: pass
                        break
                games.append({
                    "id": ev["id"], "state": state, "period": period,
                    "clock": clock, "detail": detail,
                    "home": home, "away": away, "home_ml": hml,
                    "spread": spread_val
                })
            except: continue
        return games
    except Exception as e:
        st.error("ESPN fetch error: " + str(e))
        return []

@st.cache_data(ttl=20)
def fetch_espn_win_prob(game_id):
    try:
        url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary?event=" + str(game_id)
        r = requests.get(url, timeout=8)
        if r.status_code != 200: return None
        data = r.json()
        wp = data.get("winprobability", [])
        if wp:
            return wp[-1].get("homeWinPercentage", 0.5) * 100
        pred = data.get("predictor", {})
        if pred:
            return float(pred.get("homeTeam", {}).get("gameProjection", 50))
        return None
    except: return None

# ============================================================
# KALSHI DATA (public, no auth)
# ============================================================
@st.cache_data(ttl=60)
def fetch_kalshi_spreads():
    url = "https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXNBASPREAD&status=open&limit=200"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        markets = []
        for m in data.get("markets", []):
            ti = (m.get("title", "") or "").lower()
            sub = (m.get("subtitle", "") or "").lower()
            if "wins by" in ti or "spread" in ti or "margin" in ti:
                markets.append(m)
        return markets
    except: return []

@st.cache_data(ttl=60)
def fetch_kalshi_ml():
    url = "https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXNBAGAME&status=open&limit=200"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        mkts = {}
        for m in data.get("markets", []):
            tk = m.get("ticker", "")
            if "KXNBAGAME-" not in tk: continue
            ya = m.get("yes_ask", 0) or 0
            lp = m.get("last_price", 0) or 0
            yb = m.get("yes_bid", 0) or 0
            yp = ya or lp or yb
            if yp == 0: continue
            mkts[tk] = {"ticker": tk, "yes_price": yp, "yes_ask": ya, "yes_bid": yb, "title": m.get("title", "")}
        return mkts
    except: return {}

def find_spread_markets_for_game(ha, aa, hn, an):
    all_markets = fetch_kalshi_spreads()
    matches = []
    hab, aab = ha.lower(), aa.lower()
    hnl, anl = hn.lower(), an.lower()
    hc = hnl.split()[0] if hnl else ""
    ac = anl.split()[0] if anl else ""
    for m in all_markets:
        ti = (m.get("title", "") or "").lower()
        sub = (m.get("subtitle", "") or "").lower()
        comb = ti + " " + sub
        gm = False
        if (hab in comb or hnl in comb or hc in comb):
            if (aab in comb or anl in comb or ac in comb):
                gm = True
        if not gm:
            tk = (m.get("ticker", "") or "").lower()
            if hab in tk and aab in tk:
                gm = True
        if not gm: continue
        sv, sts = None, None
        if hab in ti or hnl in ti or hc in ti:
            if "wins by" in ti: sts = "home"
        if aab in ti or anl in ti or ac in ti:
            if "wins by" in ti: sts = "away"
        nums = re.findall(r'(?:over|more than|by)\s+([\d.]+)', ti)
        if nums:
            sv = float(nums[0])
        else:
            rm = re.findall(r'by\s+(\d+)\s*[-\u2013]\s*(\d+)', ti)
            if rm:
                sv = float(rm[0][0])
            else:
                an2 = re.findall(r'([\d.]+)', ti)
                for n in an2:
                    v = float(n)
                    if 1 <= v <= 50:
                        sv = v
                        break
        yp = m.get("yes_ask", 0) or m.get("last_price", 50)
        nb, na = m.get("no_bid", 0), m.get("no_ask", 0)
        np2 = na if na > 0 else (100 - yp) if yp else 0
        matches.append({
            "ticker": m.get("ticker", ""), "title": m.get("title", ""),
            "spread_val": sv, "spread_team_side": sts,
            "yes_price": yp, "yes_bid": m.get("yes_bid", 0),
            "no_price": np2, "no_bid": nb, "no_ask": na,
            "last_price": m.get("last_price", 0), "volume": m.get("volume", 0)
        })
    matches.sort(key=lambda x: x.get("spread_val") or 0, reverse=True)
    return matches

def find_ml_price_for_team(ha, aa, fs):
    mkts = fetch_kalshi_ml()
    hau, aau = ha.upper(), aa.upper()
    fc = hau if fs == "home" else aau
    for tk, m in mkts.items():
        t = tk.upper()
        if hau in t and aau in t:
            if t.endswith("-" + fc):
                return m["yes_price"], tk
            else:
                return 100 - m["yes_price"], tk
    return None, None

# ============================================================
# SNIPER LOGIC
# ============================================================
def check_spread_sniper(game):
    gid = game["id"]
    if gid in st.session_state.alerted_games: return None
    h, a = game["home"], game["away"]
    sd = h["score"] - a["score"]
    fs = get_favorite_side(h.get("record", ""), a.get("record", ""), game.get("home_ml", 0))
    ds = "away" if fs == "home" else "home"
    dl = sd if ds == "home" else -sd
    req = LEAD_BY_QUARTER.get(game["period"], MIN_UNDERDOG_LEAD)
    if dl < req: return None
    spreads = find_spread_markets_for_game(h["abbrev"], a["abbrev"], h["name"], a["name"])
    actionable = []
    for s in spreads:
        sv = s.get("spread_val")
        if sv is None or sv < MIN_SPREAD_BRACKET: continue
        if s["spread_team_side"] and s["spread_team_side"] != fs: continue
        np = s["no_price"]
        if np <= 0: np = 100 - s["yes_price"] if s["yes_price"] else 0
        if np >= MAX_NO_PRICE or np <= 0: continue
        actionable.append({**s, "swing_needed": dl + (sv or 0), "effective_no_price": np})
    actionable.sort(key=lambda x: x["effective_no_price"])
    st.session_state.alerted_games.add(gid)
    # Get ESPN win prob
    hwp = fetch_espn_win_prob(gid)
    fwp = None
    wpe = None
    if hwp is not None:
        fwp = hwp if fs == "home" else 100 - hwp
        fml_price, _ = find_ml_price_for_team(h["abbrev"], a["abbrev"], fs)
        if fml_price:
            wpe = round(fwp - fml_price, 1)
    return {
        "game": game, "dog_side": ds, "fav_side": fs, "dog_lead": dl,
        "spreads": actionable, "no_markets": len(spreads) == 0,
        "fav_wp": fwp, "wp_edge": wpe, "required": req
    }

def check_comeback(game):
    gid = game["id"]
    if game["state"] != "in": return None
    h, a = game["home"], game["away"]
    sd = h["score"] - a["score"]
    fs = get_favorite_side(h.get("record", ""), a.get("record", ""), game.get("home_ml", 0))
    fd = -sd if fs == "home" else sd
    COMEBACK_MIN_DEFICIT = 10
    COMEBACK_TRIGGER_WITHIN = 2
    # Track max deficit
    if fd >= COMEBACK_MIN_DEFICIT:
        if gid not in st.session_state.comeback_tracking:
            st.session_state.comeback_tracking[gid] = {"max_deficit": fd, "fav_side": fs}
        elif fd > st.session_state.comeback_tracking[gid]["max_deficit"]:
            st.session_state.comeback_tracking[gid]["max_deficit"] = fd
    # Check comeback trigger
    if gid in st.session_state.comeback_alerted or gid not in st.session_state.comeback_tracking:
        return None
    md = st.session_state.comeback_tracking[gid]["max_deficit"]
    fs = st.session_state.comeback_tracking[gid]["fav_side"]
    fm = sd if fs == "home" else -sd
    if fm < -COMEBACK_TRIGGER_WITHIN: return None
    ds = "away" if fs == "home" else "home"
    fp, mt = find_ml_price_for_team(h["abbrev"], a["abbrev"], fs)
    hwp = fetch_espn_win_prob(gid)
    fwp = None
    if hwp is not None:
        fwp = hwp if fs == "home" else 100 - hwp
    st.session_state.comeback_alerted.add(gid)
    return {
        "game": game, "fav_side": fs, "dog_side": ds,
        "max_deficit": md, "fav_margin": fm,
        "fav_price": fp, "ml_ticker": mt, "fav_wp": fwp
    }

# ============================================================
# MAIN UI
# ============================================================
games = fetch_espn_games()

live_games = [g for g in games if g['state'] == 'in']
pre_games = [g for g in games if g['state'] == 'pre']
post_games = [g for g in games if g['state'] == 'post']

st.title("BIGSNAPSHOT SPREAD EDGE FINDER")
st.caption("v" + VERSION + " | " + now.strftime('%b %d, %Y %I:%M %p ET') + " | Spread Sniper + Comeback Scanner")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Today's Games", len(games))
c2.metric("Live Now", len(live_games))
c3.metric("Pre-Game", len(pre_games))
c4.metric("Final", len(post_games))
st.divider()

# ============================================================
# STRATEGY EXPLAINER
# ============================================================
with st.expander("How Spread Sniping Works"):
    st.markdown(
        "**The Strategy:** When an underdog takes a big lead over the favorite, "
        "the market still prices the favorite's spread brackets as if they'll win big. "
        "We buy NO on high spread brackets (e.g., 'Favorite wins by 17.5+') at cheap prices.\n\n"
        "**Sniper Thresholds by Quarter:**\n\n"
        "| Quarter | Underdog Lead Needed |\n"
        "|---------|---------------------|\n"
        "| Q1 | 7+ points |\n"
        "| Q2 | 8+ points |\n"
        "| Q3 | 10+ points |\n"
        "| Q4 | 13+ points |\n\n"
        "**Comeback Scanner:** Tracks when favorites fall behind 10+ points, "
        "then alerts when they close within 2 points — the ML is often still cheap.\n\n"
        "**Rating System:**\n\n"
        "| Tag | NO Price | Meaning |\n"
        "|-----|----------|----------|\n"
        "| FIRE | ≤40c | Incredible value |\n"
        "| GOOD | 41-60c | Strong opportunity |\n"
        "| OK | 61-75c | Decent edge |\n"
        "| WARN | 76-85c | Thin margin |"
    )

# ============================================================
# LIVE SNIPER SCANNER
# ============================================================
st.subheader("SPREAD SNIPER — LIVE ALERTS")
st.caption("Fires when underdog lead hits threshold | BUY NO on favorite's spread brackets")

new_sniper_alerts = []
new_comeback_alerts = []

if live_games:
    for game in live_games:
        # Track comebacks
        gid = game["id"]
        h, a = game["home"], game["away"]
        sd = h["score"] - a["score"]
        fs = get_favorite_side(h.get("record", ""), a.get("record", ""), game.get("home_ml", 0))
        fd = -sd if fs == "home" else sd
        if fd >= 10:
            if gid not in st.session_state.comeback_tracking:
                st.session_state.comeback_tracking[gid] = {"max_deficit": fd, "fav_side": fs}
            elif fd > st.session_state.comeback_tracking[gid]["max_deficit"]:
                st.session_state.comeback_tracking[gid]["max_deficit"] = fd

        # Check sniper
        result = check_spread_sniper(game)
        if result:
            new_sniper_alerts.append(result)
            st.session_state.sniper_alerts.append(result)

        # Check comeback
        comeback = check_comeback(game)
        if comeback:
            new_comeback_alerts.append(comeback)
            st.session_state.comeback_alerts.append(comeback)

# Display ALL sniper alerts (current + previous)
all_sniper = st.session_state.sniper_alerts
all_comeback = st.session_state.comeback_alerts

if all_sniper:
    for result in all_sniper:
        game = result["game"]
        h, a = game["home"], game["away"]
        fav = game[result["fav_side"]]
        dog = game[result["dog_side"]]
        dl = result["dog_lead"]
        per = game["period"]
        clk = game["clock"]
        ps = "Q" + str(per) if per <= 4 else "OT" + str(per - 4)
        fav_code = KALSHI_CODES.get(TEAM_ABBREVS.get(fav["name"], fav.get("short_name", "")), fav["abbrev"])
        dog_code = KALSHI_CODES.get(TEAM_ABBREVS.get(dog["name"], dog.get("short_name", "")), dog["abbrev"])
        home_code = KALSHI_CODES.get(TEAM_ABBREVS.get(h["name"], h.get("short_name", "")), h["abbrev"])
        away_code = KALSHI_CODES.get(TEAM_ABBREVS.get(a["name"], a.get("short_name", "")), a["abbrev"])

        alert_html = "<div style='background:#1a1a2e;border-radius:10px;padding:16px;margin:10px 0;border-left:5px solid #ef4444'>"
        alert_html += "<div style='color:#ef4444;font-weight:bold;font-size:18px'>🎯 SPREAD SNIPER ALERT — " + ps + " " + clk + "</div>"
        alert_html += "<div style='color:#fff;font-size:16px;margin:8px 0'>" + a["abbrev"] + " " + str(a["score"]) + " @ " + h["abbrev"] + " " + str(h["score"]) + "</div>"
        alert_html += "<div style='color:#ffd700;font-size:14px'>UNDERDOG " + dog["abbrev"] + " (" + dog.get("record", "") + ") UP " + str(dl) + " pts over FAVORITE " + fav["abbrev"] + " (" + fav.get("record", "") + ")</div>"
        if result.get("fav_wp") is not None:
            wp_color = "#22c55e" if (result.get("wp_edge") or 0) >= MIN_WP_EDGE else "#eab308"
            alert_html += "<div style='color:" + wp_color + ";font-size:13px;margin-top:4px'>ESPN WP: " + fav["abbrev"] + " " + str(round(result["fav_wp"])) + "%"
            if result.get("wp_edge") is not None:
                if result["wp_edge"] >= MIN_WP_EDGE:
                    alert_html += " | CONFIRMED EDGE: +" + str(result["wp_edge"]) + "%"
                elif result["wp_edge"] > 0:
                    alert_html += " | Small edge: +" + str(result["wp_edge"]) + "%"
                else:
                    alert_html += " | No WP edge (" + str(result["wp_edge"]) + "%) — caution"
            alert_html += "</div>"
        alert_html += "</div>"
        st.markdown(alert_html, unsafe_allow_html=True)

        spreads = result.get("spreads", [])
        if result.get("no_markets"):
            st.warning("No spread markets found — check Kalshi manually. BUY NO on any bracket where " + fav["abbrev"] + " wins by 10+")
        elif not spreads:
            st.info("Spread markets found but none under " + str(MAX_NO_PRICE) + "c")
        else:
            st.markdown("**ACTIONABLE BRACKETS (" + str(len(spreads)) + "):**")
            for s in spreads:
                np2 = s["effective_no_price"]
                sw = s.get("swing_needed", "?")
                tk = s["ticker"]
                ts2 = s["title"][:50]
                if np2 <= 40: tag, tag_color = "FIRE", "#ef4444"
                elif np2 <= 60: tag, tag_color = "GOOD", "#22c55e"
                elif np2 <= 75: tag, tag_color = "OK", "#eab308"
                else: tag, tag_color = "WARN", "#f97316"
                row_html = "<div style='background:#0f172a;padding:10px;border-radius:6px;margin:4px 0;display:flex;justify-content:space-between;align-items:center'>"
                row_html += "<div><span style='color:" + tag_color + ";font-weight:bold'>[" + tag + "]</span> <span style='color:#fff'>" + ts2 + "</span></div>"
                row_html += "<div style='text-align:right'><span style='color:#fff;font-weight:bold'>" + str(np2) + "c NO</span> <span style='color:#888;margin-left:8px'>Swing: " + str(sw) + "pts</span></div>"
                row_html += "</div>"
                st.markdown(row_html, unsafe_allow_html=True)

            best = spreads[0]
            st.markdown("<div style='background:#0f2e0f;padding:12px;border-radius:8px;margin:8px 0;border:1px solid #22c55e'><span style='color:#22c55e;font-weight:bold'>BEST BET:</span> <span style='color:#fff'>BUY NO on \"" + best["title"][:50] + "\" @ " + str(best["effective_no_price"]) + "c — needs " + str(best["swing_needed"]) + "-pt swing</span></div>", unsafe_allow_html=True)

        spread_link = get_kalshi_game_link(away_code, home_code)
        st.link_button("Trade Spread on Kalshi", spread_link, use_container_width=True)
        st.markdown("---")
else:
    if not all_sniper:
        st.info("No spread sniper alerts yet. Scanning live games for underdog leads...")

st.divider()

# ============================================================
# COMEBACK SCANNER
# ============================================================
st.subheader("COMEBACK SCANNER")
st.caption("Tracks favorites falling behind 10+ pts | Alerts when they close within 2")

# Show tracking status
tracking = st.session_state.comeback_tracking
if tracking:
    st.markdown("**Currently Tracking:**")
    for gid, info in tracking.items():
        game = next((g for g in games if g["id"] == gid), None)
        if not game: continue
        h, a = game["home"], game["away"]
        fs = info["fav_side"]
        fav = game[fs]
        md = info["max_deficit"]
        sd = h["score"] - a["score"]
        fm = sd if fs == "home" else -sd
        if fm > 0: status_text = "NOW LEADS BY " + str(fm)
        elif fm == 0: status_text = "GAME TIED"
        else: status_text = "DOWN " + str(abs(fm))
        fired = gid in st.session_state.comeback_alerted
        badge = " ✅ FIRED" if fired else ""
        track_color = "#22c55e" if fm >= 0 else "#eab308"
        st.markdown("<div style='background:#1e1e2e;padding:10px;border-radius:6px;margin:4px 0'><span style='color:" + track_color + ";font-weight:bold'>" + fav["abbrev"] + "</span> <span style='color:#888'>was down " + str(md) + " — " + status_text + badge + "</span></div>", unsafe_allow_html=True)

if all_comeback:
    st.markdown("---")
    st.markdown("**COMEBACK ALERTS:**")
    for result in all_comeback:
        game = result["game"]
        h, a = game["home"], game["away"]
        fav = game[result["fav_side"]]
        dog = game[result["dog_side"]]
        md = result["max_deficit"]
        fm = result["fav_margin"]
        fp = result.get("fav_price")
        per = game["period"]
        clk = game["clock"]
        ps = "Q" + str(per) if per <= 4 else "OT" + str(per - 4)
        home_code = KALSHI_CODES.get(TEAM_ABBREVS.get(h["name"], h.get("short_name", "")), h["abbrev"])
        away_code = KALSHI_CODES.get(TEAM_ABBREVS.get(a["name"], a.get("short_name", "")), a["abbrev"])

        if fm > 0: sm = "NOW LEADS BY " + str(fm)
        elif fm == 0: sm = "GAME TIED"
        else: sm = "DOWN ONLY " + str(abs(fm)) + " — CLOSING IN"

        cb_html = "<div style='background:#1a1a2e;border-radius:10px;padding:16px;margin:10px 0;border-left:5px solid #22c55e'>"
        cb_html += "<div style='color:#22c55e;font-weight:bold;font-size:18px'>🔄 COMEBACK ALERT — " + ps + " " + clk + "</div>"
        cb_html += "<div style='color:#fff;font-size:16px;margin:8px 0'>" + a["abbrev"] + " " + str(a["score"]) + " @ " + h["abbrev"] + " " + str(h["score"]) + "</div>"
        cb_html += "<div style='color:#ffd700;font-size:14px'>" + fav["abbrev"] + " WAS DOWN " + str(md) + " — " + sm + "!</div>"
        if fp:
            price_color = "#ef4444" if fp <= 55 else "#eab308"
            cb_html += "<div style='color:" + price_color + ";font-size:13px;margin-top:4px'>Kalshi ML: " + fav["abbrev"] + " @ " + str(fp) + "c"
            if fp <= 55: cb_html += " — MARKET LAGGING!"
            elif fp <= 70: cb_html += " — Price catching up"
            cb_html += "</div>"
        if result.get("fav_wp") is not None:
            cb_html += "<div style='color:#3b82f6;font-size:13px'>ESPN WP: " + fav["abbrev"] + " " + str(round(result["fav_wp"])) + "%</div>"
        cb_html += "<div style='color:#fff;margin-top:8px'>BUY " + fav["abbrev"] + " ML if price hasn't caught up</div>"
        cb_html += "</div>"
        st.markdown(cb_html, unsafe_allow_html=True)

        ml_link = get_kalshi_ml_link(away_code, home_code)
        st.link_button("Trade ML on Kalshi", ml_link, use_container_width=True)
        st.markdown("---")
else:
    if not tracking:
        st.info("No favorites currently behind 10+ points. Monitoring...")
    else:
        st.info("Tracking favorites — waiting for comeback trigger (within 2 pts of lead)")

st.divider()

# ============================================================
# LIVE GAME DASHBOARD
# ============================================================
st.subheader("LIVE GAME MONITOR")

for game in games:
    h, a = game["home"], game["away"]
    gid = game["id"]
    state = game["state"]
    per = game["period"]
    clk = game["clock"]
    mu = a["abbrev"] + " " + str(a["score"]) + " @ " + h["abbrev"] + " " + str(h["score"])

    if state == "pre":
        fs = get_favorite_side(h.get("record", ""), a.get("record", ""), game.get("home_ml", 0))
        fav = game[fs]
        spread_text = ""
        if game.get("spread"):
            spread_text = " | Spread: " + str(game["spread"])
        st.markdown("<div style='background:#1e1e2e;padding:10px;border-radius:6px;margin:4px 0;border-left:3px solid #888'><span style='color:#888'>[PRE]</span> <span style='color:#fff'>" + mu + "</span> <span style='color:#888'>— Fav: " + fav["abbrev"] + " " + fav.get("record", "") + spread_text + "</span></div>", unsafe_allow_html=True)
        continue

    if state == "post":
        tags = ""
        if gid in st.session_state.alerted_games: tags += " 🎯"
        if gid in st.session_state.comeback_alerted: tags += " 🔄"
        st.markdown("<div style='background:#1e1e2e;padding:10px;border-radius:6px;margin:4px 0;border-left:3px solid #666'><span style='color:#666'>[FINAL]</span> <span style='color:#fff'>" + mu + tags + "</span></div>", unsafe_allow_html=True)
        continue

    # Live game
    ps = "Q" + str(per) if per <= 4 else "OT" + str(per - 4)
    fs = get_favorite_side(h.get("record", ""), a.get("record", ""), game.get("home_ml", 0))
    ds = "away" if fs == "home" else "home"
    dog, fav = game[ds], game[fs]
    sd = h["score"] - a["score"]
    dl = sd if ds == "home" else -sd
    req = LEAD_BY_QUARTER.get(per, MIN_UNDERDOG_LEAD)

    if gid in st.session_state.alerted_games and gid in st.session_state.comeback_alerted:
        border_color = "#a855f7"
        tag = "🎯🔄 BOTH FIRED"
    elif gid in st.session_state.alerted_games:
        border_color = "#ef4444"
        tag = "🎯 SNIPER FIRED"
    elif gid in st.session_state.comeback_alerted:
        border_color = "#22c55e"
        tag = "🔄 COMEBACK FIRED"
    elif dl >= req:
        border_color = "#ffd700"
        tag = "⚡ " + dog["abbrev"] + "(dog) +" + str(dl) + " THRESHOLD MET"
    elif dl >= MIN_UNDERDOG_LEAD:
        border_color = "#f97316"
        tag = "👀 " + dog["abbrev"] + "(dog) +" + str(dl) + " (need " + str(req) + ")"
    elif dl > 0:
        border_color = "#eab308"
        tag = dog["abbrev"] + "(dog) +" + str(dl)
    else:
        diff = abs(sd)
        leader = h["abbrev"] if h["score"] > a["score"] else a["abbrev"]
        fd_text = "up" if leader == fav["abbrev"] else "down"
        border_color = "#333"
        tag = fav["abbrev"] + "(fav) " + fd_text + " " + str(diff)

    st.markdown("<div style='background:#1e1e2e;padding:10px;border-radius:6px;margin:4px 0;border-left:3px solid " + border_color + "'><span style='color:" + border_color + ";font-weight:bold'>[" + ps + " " + clk + "]</span> <span style='color:#fff;font-weight:bold'>" + mu + "</span> <span style='color:" + border_color + "'> — " + tag + "</span></div>", unsafe_allow_html=True)

st.divider()

# ============================================================
# CONFIG DISPLAY
# ============================================================
with st.expander("Scanner Config"):
    st.markdown(
        "| Setting | Value |\n"
        "|---------|-------|\n"
        "| Min Spread Bracket | " + str(MIN_SPREAD_BRACKET) + " pts |\n"
        "| Max NO Price | " + str(MAX_NO_PRICE) + "c |\n"
        "| Min WP Edge | " + str(MIN_WP_EDGE) + "% |\n"
        "| Q1 Threshold | " + str(LEAD_BY_QUARTER[1]) + " pts |\n"
        "| Q2 Threshold | " + str(LEAD_BY_QUARTER[2]) + " pts |\n"
        "| Q3 Threshold | " + str(LEAD_BY_QUARTER[3]) + " pts |\n"
        "| Q4 Threshold | " + str(LEAD_BY_QUARTER[4]) + " pts |\n"
        "| Comeback Min Deficit | 10 pts |\n"
        "| Comeback Trigger | Within 2 pts |"
    )

st.divider()
st.caption("v" + VERSION + " | Educational only | Not financial advice")
st.caption("Stay small. Stay quiet. Win.")
