"""
🔬 MATCH ANALYZER v30
Win Probability Engine + Kalshi Edge Finder + One-Click Trading
BigSnapshot.com
"""
import streamlit as st
import requests
import math
import time
import base64
import json
from datetime import datetime
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend

st.set_page_config(page_title="Match Analyzer", page_icon="🔬", layout="wide")

# ============================================================
# OWNER-ONLY ACCESS — bookmark: yoursite.com/MatchAnalyzer?key=shark
# ============================================================
if st.query_params.get("key") != "shark":
    st.error("🔒 Access denied")
    st.stop()

# ============================================================
# KALSHI AUTH
# ============================================================
API_KEY = st.secrets.get("KALSHI_API_KEY", "")
PRIVATE_KEY = st.secrets.get("KALSHI_PRIVATE_KEY", "")
KALSHI_BASE = "https://api.elections.kalshi.com"


def create_kalshi_signature(timestamp, method, path):
    try:
        message = (str(timestamp) + method + path).encode('utf-8')
        pk = serialization.load_pem_private_key(
            PRIVATE_KEY.encode(), password=None, backend=default_backend()
        )
        sig = pk.sign(
            message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.DIGEST_LENGTH
            ),
            hashes.SHA256()
        )
        return base64.b64encode(sig).decode()
    except Exception:
        return None


def kalshi_headers(method, path):
    ts = str(int(time.time() * 1000))
    sig = create_kalshi_signature(ts, method, path)
    if not sig:
        return None
    return {
        "KALSHI-ACCESS-KEY": API_KEY,
        "KALSHI-ACCESS-SIGNATURE": sig,
        "KALSHI-ACCESS-TIMESTAMP": ts,
        "Content-Type": "application/json"
    }


def get_kalshi_balance():
    path = "/trade-api/v2/portfolio/balance"
    h = kalshi_headers("GET", path)
    if not h:
        return None
    try:
        r = requests.get(KALSHI_BASE + path, headers=h, timeout=10)
        if r.status_code == 200:
            return r.json().get("balance", 0) / 100
        return None
    except Exception:
        return None


def place_kalshi_order(ticker, side, price_cents, count):
    path = "/trade-api/v2/portfolio/orders"
    h = kalshi_headers("POST", path)
    if not h:
        return False, "Auth failed", ""
    body = {
        "ticker": ticker,
        "action": "buy",
        "side": side,
        "count": count,
        "type": "limit",
    }
    if side == "yes":
        body["yes_price"] = price_cents
    else:
        body["no_price"] = price_cents
    try:
        r = requests.post(KALSHI_BASE + path, headers=h, json=body, timeout=10)
        d = r.json()
        if r.status_code in [200, 201]:
            oid = d.get("order", {}).get("order_id", d.get("order_id", ""))
            return True, "Order placed", oid
        msg = d.get("message", d.get("error", "HTTP " + str(r.status_code)))
        return False, msg, ""
    except Exception as e:
        return False, str(e), ""


# ============================================================
# LEAGUE CONFIG
# ============================================================
LEAGUES = {
    "NBA": {"pace": 0.034, "minutes": 48, "periods": 4, "pmin": 12,
            "label": "NBA", "espn": "basketball/nba", "kalshi": "KXNBAGAME", "plbl": "Q"},
    "NCAAM": {"pace": 0.028, "minutes": 40, "periods": 2, "pmin": 20,
              "label": "NCAA Men", "espn": "basketball/mens-college-basketball",
              "kalshi": "KXNCAAMBGAME", "plbl": "H"},
    "NCAAW": {"pace": 0.022, "minutes": 40, "periods": 4, "pmin": 10,
              "label": "NCAA Women", "espn": "basketball/womens-college-basketball",
              "kalshi": "KXNCAAWBGAME", "plbl": "Q"},
    "NHL": {"pace": 0.025, "minutes": 60, "periods": 3, "pmin": 20,
            "label": "NHL", "espn": "hockey/nhl", "kalshi": "KXNHLGAME", "plbl": "P"},
    "NFL": {"pace": 0.018, "minutes": 60, "periods": 4, "pmin": 15,
            "label": "NFL", "espn": "football/nfl", "kalshi": "KXNFLGAME", "plbl": "Q"},
}

FACTORS = [
    {"id": "offEff", "label": "Off/Def Efficiency", "lo": -10.0, "hi": 10.0, "step": 0.5},
    {"id": "form", "label": "Recent Form (L10)", "lo": -5.0, "hi": 5.0, "step": 0.5},
    {"id": "h2h", "label": "Head-to-Head", "lo": -3.0, "hi": 3.0, "step": 0.5},
    {"id": "homeSplit", "label": "Home/Away Splits", "lo": -4.0, "hi": 4.0, "step": 0.5},
    {"id": "injuries", "label": "Key Injuries", "lo": -8.0, "hi": 8.0, "step": 1.0},
    {"id": "tempo", "label": "Pace & Tempo", "lo": -3.0, "hi": 3.0, "step": 0.5},
    {"id": "vegas", "label": "Vegas/Line Edge", "lo": -10.0, "hi": 10.0, "step": 0.5},
]


# ============================================================
# ESPN FETCH
# ============================================================
@st.cache_data(ttl=30)
def fetch_espn_games(league_key):
    cfg = LEAGUES.get(league_key)
    if not cfg:
        return []
    url = "https://site.api.espn.com/apis/site/v2/sports/" + cfg["espn"] + "/scoreboard"
    try:
        r = requests.get(url, timeout=10)
        d = r.json()
    except Exception:
        return []
    games = []
    for ev in d.get("events", []):
        comp = ev.get("competitions", [{}])[0]
        teams = comp.get("competitors", [])
        ht = None
        at = None
        for t in teams:
            if t.get("homeAway") == "home":
                ht = t
            else:
                at = t
        if not ht and len(teams) > 0:
            ht = teams[0]
        if not at and len(teams) > 1:
            at = teams[1]
        if not ht:
            ht = {}
        if not at:
            at = {}
        si = ev.get("status", {})
        tp = si.get("type", {})
        state = tp.get("state", "pre")
        per = si.get("period", 0)
        clk = si.get("displayClock", "0:00")
        h_score = int(ht.get("score", 0) or 0)
        a_score = int(at.get("score", 0) or 0)
        h_tm = ht.get("team", {})
        a_tm = at.get("team", {})
        h_name = h_tm.get("shortDisplayName", h_tm.get("displayName", "Home"))
        a_name = a_tm.get("shortDisplayName", a_tm.get("displayName", "Away"))
        h_abbr = h_tm.get("abbreviation", "")
        a_abbr = a_tm.get("abbreviation", "")
        h_rec = ""
        a_rec = ""
        hr = ht.get("records", [])
        ar = at.get("records", [])
        if hr:
            h_rec = hr[0].get("summary", "")
        if ar:
            a_rec = ar[0].get("summary", "")
        stxt = ""
        if state == "in":
            stxt = cfg["plbl"] + str(per) + " " + clk
        elif state == "post":
            stxt = "FINAL"
        else:
            try:
                dt = datetime.fromisoformat(ev.get("date", "").replace("Z", "+00:00"))
                stxt = dt.strftime("%-I:%M %p")
            except Exception:
                stxt = "TBD"
        odds = {}
        co = comp.get("odds", [])
        if co:
            odds = co[0]
        games.append({
            "id": ev.get("id", ""),
            "home": h_name, "away": a_name,
            "hAbbr": h_abbr, "aAbbr": a_abbr,
            "hScore": h_score, "aScore": a_score,
            "hRec": h_rec, "aRec": a_rec,
            "state": state, "period": per, "clock": clk,
            "statusText": stxt,
            "margin": h_score - a_score,
            "spread": odds.get("details", ""),
            "ou": odds.get("overUnder", ""),
        })
    return games


# ============================================================
# WIN PROBABILITY MODEL
# ============================================================
def calc_wp(mg, tf, pace):
    if tf <= 0:
        if mg > 0:
            return 99.9
        elif mg < 0:
            return 0.1
        return 50.0
    k = pace / math.sqrt(tf)
    return 100.0 / (1.0 + math.exp(-k * mg))


def parse_clock(s):
    if not s:
        return 0
    p = s.split(":")
    mn = int(p[0]) if len(p) > 0 and p[0].isdigit() else 0
    sc = int(p[1]) if len(p) > 1 and p[1].isdigit() else 0
    return mn * 60 + sc


def get_time_frac(per, clk, cfg):
    cs = parse_clock(clk)
    pm = cfg["pmin"]
    elapsed = ((per - 1) * pm * 60) + (pm * 60 - cs)
    total = cfg["minutes"] * 60
    return max(0, (total - elapsed) / total), total


# ============================================================
# KALSHI MARKET FETCH
# ============================================================
@st.cache_data(ttl=30)
def fetch_kalshi_markets(series_ticker):
    url = KALSHI_BASE + "/trade-api/v2/markets"
    try:
        r = requests.get(url, params={"series_ticker": series_ticker, "status": "open", "limit": 200}, timeout=10)
        d = r.json()
    except Exception:
        return {}
    prices = {}
    for m in d.get("markets", []):
        tk = m.get("ticker", "")
        prices[tk] = {
            "yes_price": m.get("yes_price", m.get("last_price", 0)),
            "title": m.get("title", ""),
            "subtitle": m.get("subtitle", ""),
        }
    return prices


def find_kalshi_price(game, lk):
    cfg = LEAGUES.get(lk, {})
    series = cfg.get("kalshi", "")
    if not series:
        return None, None
    prices = fetch_kalshi_markets(series)
    if not prices:
        return None, None
    hw = game.get("home", "").lower().split()
    aw = game.get("away", "").lower().split()
    ha = game.get("hAbbr", "").upper()
    aa = game.get("aAbbr", "").upper()
    for tk, info in prices.items():
        combo = (info.get("title", "") + " " + info.get("subtitle", "")).lower()
        tup = tk.upper()
        mh = any(w for w in hw if len(w) > 3 and w in combo) or (ha and ha in tup)
        ma = any(w for w in aw if len(w) > 3 and w in combo) or (aa and aa in tup)
        if mh and ma:
            return info.get("yes_price", 0), tk
    return None, None


# ============================================================
# SVG CHART BUILDER
# ============================================================
def build_chart(data, xl, yl, xdom, dx=None, dy=None, kl=None):
    W = 500
    H = 240
    pl = 50
    pt = 18
    pr = 25
    pb = 46
    cw = W - pl - pr
    ch = H - pt - pb
    xmn = xdom[0]
    xmx = xdom[1]

    def sx(v):
        return pl + ((v - xmn) / (xmx - xmn)) * cw

    def sy(v):
        return pt + ch - (v / 100) * ch

    s = ""
    s += '<svg viewBox="0 0 500 240" style="width:100%;display:block;background:#0a0a1a;border-radius:10px">'
    s += '<rect x="50" y="18" width="' + str(cw) + '" height="' + str(ch) + '" fill="#0f172a" rx="4"/>'
    for yv in [0, 25, 50, 75, 100]:
        yp = sy(yv)
        s += '<line x1="50" x2="' + str(pl + cw) + '" y1="' + str(round(yp, 1)) + '" y2="' + str(round(yp, 1)) + '" stroke="#1e293b" stroke-width="0.5"/>'
        s += '<text x="44" y="' + str(round(yp + 4, 1)) + '" fill="#64748b" font-size="10" text-anchor="end">' + str(yv) + '%</text>'
    pd = ""
    for i, pt_d in enumerate(data):
        xp = sx(pt_d[0])
        yp = sy(pt_d[1])
        pd += ("M" if i == 0 else "L") + str(round(xp, 1)) + "," + str(round(yp, 1))
    s += '<path d="' + pd + '" fill="none" stroke="#10b981" stroke-width="2.5"/>'
    mid = sy(50)
    s += '<line x1="50" x2="' + str(pl + cw) + '" y1="' + str(round(mid, 1)) + '" y2="' + str(round(mid, 1)) + '" stroke="#f59e0b" stroke-width="0.7" stroke-dasharray="4,4"/>'
    hk = kl is not None and kl > 0 and dy is not None
    if hk and dx is not None:
        ed = dy - kl
        kc = "#10b981" if ed > 5 else "#ef4444" if ed < -5 else "#f59e0b"
        dxp = sx(dx)
        dyp = sy(dy)
        kyp = sy(kl)
        sgn = "+" if ed > 0 else ""
        s += '<line x1="' + str(round(dxp, 1)) + '" x2="' + str(round(dxp, 1)) + '" y1="' + str(round(dyp, 1)) + '" y2="' + str(round(kyp, 1)) + '" stroke="' + kc + '" stroke-width="1.5" stroke-dasharray="3,2" opacity="0.6"/>'
        mc = (dyp + kyp) / 2
        s += '<text x="' + str(round(dxp + 10, 1)) + '" y="' + str(round(mc + 4, 1)) + '" fill="' + kc + '" font-size="10" font-weight="bold">' + sgn + str(round(ed)) + '¢</text>'
        s += '<circle cx="' + str(round(dxp, 1)) + '" cy="' + str(round(kyp, 1)) + '" r="6" fill="' + kc + '" stroke="#000" stroke-width="1.5"/>'
        s += '<text x="' + str(round(dxp + 10, 1)) + '" y="' + str(round(kyp + 4, 1)) + '" fill="' + kc + '" font-size="9">Kalshi ' + str(kl) + '¢</text>'
    if dx is not None and dy is not None:
        dxp = sx(dx)
        dyp = sy(dy)
        s += '<circle cx="' + str(round(dxp, 1)) + '" cy="' + str(round(dyp, 1)) + '" r="5" fill="#f59e0b" stroke="#000" stroke-width="1.5"/>'
    s += '<text x="250" y="238" fill="#94a3b8" font-size="11" text-anchor="middle">' + xl + '</text>'
    s += '<text x="12" y="120" fill="#94a3b8" font-size="11" text-anchor="middle" transform="rotate(-90,12,120)">' + yl + '</text>'
    s += '</svg>'
    return s


# ============================================================
# SESSION STATE
# ============================================================
if "order_log" not in st.session_state:
    st.session_state.order_log = []
if "sel_game_id" not in st.session_state:
    st.session_state.sel_game_id = None
if "sel_league" not in st.session_state:
    st.session_state.sel_league = "NBA"

# ============================================================
# HEADER
# ============================================================
st.markdown('<div style="text-align:center;padding:8px 0"><span style="font-size:24px;color:#f0c040;font-weight:800">🔬 MATCH ANALYZER</span><br><span style="color:#64748b;font-size:13px">Win Probability Engine + Kalshi Edge Finder + One-Click Trading</span></div>', unsafe_allow_html=True)

# API STATUS
bal = get_kalshi_balance()
api_ok = bal is not None
if api_ok:
    st.success("🟢 Kalshi API Connected — Balance: $" + str(round(bal, 2)))
else:
    st.warning("🔴 Kalshi API not connected — add KALSHI_API_KEY + KALSHI_PRIVATE_KEY to secrets")

# LEAGUE TABS
lkeys = list(LEAGUES.keys())
cols = st.columns(len(lkeys))
for i, lk in enumerate(lkeys):
    cnt = len(fetch_espn_games(lk))
    lab = LEAGUES[lk]["label"] + " (" + str(cnt) + ")"
    with cols[i]:
        btype = "primary" if st.session_state.sel_league == lk else "secondary"
        if st.button(lab, key="lg_" + lk, use_container_width=True, type=btype):
            st.session_state.sel_league = lk
            st.session_state.sel_game_id = None
            st.rerun()

sel_league = st.session_state.sel_league
cfg = LEAGUES[sel_league]

# GAME LIST
all_games = fetch_espn_games(sel_league)
live_g = [g for g in all_games if g["state"] == "in"]
pre_g = [g for g in all_games if g["state"] == "pre"]
fin_g = [g for g in all_games if g["state"] == "post"]

st.markdown("---")

def game_btn(g, pfx):
    is_sel = st.session_state.sel_game_id == g["id"]
    lab = ""
    if g["state"] != "pre":
        lab = g["aAbbr"] + " " + str(g["aScore"]) + " @ " + g["hAbbr"] + " " + str(g["hScore"])
    else:
        lab = g["aAbbr"] + " @ " + g["hAbbr"]
    kp, _ = find_kalshi_price(g, sel_league)
    if kp:
        lab += " | " + str(kp) + "¢"
    if g["spread"]:
        lab += " | " + g["spread"]
    lab += " — " + g["statusText"]
    if g["state"] == "in":
        lab = "🔴 " + lab
    bt = "primary" if is_sel else "secondary"
    if st.button(lab, key=pfx + "_" + g["id"], use_container_width=True, type=bt):
        st.session_state.sel_game_id = g["id"]
        st.rerun()

if live_g:
    st.markdown("**🔴 LIVE (" + str(len(live_g)) + ")**")
    for g in live_g:
        game_btn(g, "lv")
if pre_g:
    st.markdown("**🕐 UPCOMING (" + str(len(pre_g)) + ")**")
    for g in pre_g:
        game_btn(g, "pr")
if fin_g:
    st.markdown("**✅ FINAL (" + str(len(fin_g)) + ")**")
    for g in fin_g:
        game_btn(g, "fn")
if not all_games:
    st.info("No " + cfg["label"] + " games today")

st.markdown("---")

# SELECTED GAME
sel_game = None
for g in all_games:
    if g["id"] == st.session_state.sel_game_id:
        sel_game = g
        break

home_team = sel_game["home"] if sel_game else "Home"
away_team = sel_game["away"] if sel_game else "Away"
g_margin = sel_game["margin"] if sel_game else 0
g_period = sel_game.get("period", 1) if sel_game else 1
g_clock = sel_game.get("clock", "0:00") if sel_game else "0:00"
is_live = sel_game and sel_game["state"] == "in"
is_pre = sel_game and sel_game["state"] == "pre"
mode = "pregame" if is_pre else "ingame"

k_price, k_ticker = (None, None)
if sel_game:
    k_price, k_ticker = find_kalshi_price(sel_game, sel_league)

# SCOREBOARD
if sel_game:
    sc = "#10b981" if sel_game["state"] == "in" else "#64748b" if sel_game["state"] == "post" else "#38bdf8"
    badge = ""
    if sel_game["state"] == "in":
        badge = '<span style="background:#ef4444;color:#fff;padding:2px 10px;border-radius:10px;font-size:11px;font-weight:700">● LIVE — ' + cfg["plbl"] + str(sel_game["period"]) + " " + sel_game["clock"] + '</span>'
    elif sel_game["state"] == "post":
        badge = '<span style="background:#334155;color:#94a3b8;padding:2px 10px;border-radius:10px;font-size:11px;font-weight:700">FINAL</span>'
    else:
        badge = '<span style="background:#1e3a5f;color:#38bdf8;padding:2px 10px;border-radius:10px;font-size:11px;font-weight:700">' + sel_game["statusText"] + '</span>'
    ac = "#10b981" if sel_game["aScore"] > sel_game["hScore"] else "#94a3b8"
    hc = "#10b981" if sel_game["hScore"] > sel_game["aScore"] else "#94a3b8"
    html = '<div style="background:linear-gradient(135deg,#0f172a,#1a1a2e);border-radius:10px;padding:14px;border:2px solid ' + sc + ';text-align:center;margin-bottom:14px">'
    html += '<div style="margin-bottom:6px">' + badge + '</div>'
    html += '<div style="display:flex;justify-content:center;align-items:center;gap:20px">'
    html += '<div style="text-align:center;min-width:100px"><div style="color:' + ac + ';font-size:11px;font-weight:600">' + away_team + '</div>'
    html += '<div style="color:' + ac + ';font-size:36px;font-weight:800;font-family:monospace">' + str(sel_game["aScore"]) + '</div>'
    if sel_game["aRec"]:
        html += '<div style="color:#475569;font-size:10px">' + sel_game["aRec"] + '</div>'
    html += '</div>'
    html += '<div style="color:#475569;font-size:22px;font-weight:300">—</div>'
    html += '<div style="text-align:center;min-width:100px"><div style="color:' + hc + ';font-size:11px;font-weight:600">' + home_team + '</div>'
    html += '<div style="color:' + hc + ';font-size:36px;font-weight:800;font-family:monospace">' + str(sel_game["hScore"]) + '</div>'
    if sel_game["hRec"]:
        html += '<div style="color:#475569;font-size:10px">' + sel_game["hRec"] + '</div>'
    html += '</div></div>'
    if sel_game["spread"] or sel_game["ou"]:
        html += '<div style="margin-top:6px;color:#64748b;font-size:11px">'
        if sel_game["spread"]:
            html += '<span style="margin-right:12px">Line: ' + sel_game["spread"] + '</span>'
        if sel_game["ou"]:
            html += '<span>O/U: ' + str(sel_game["ou"]) + '</span>'
        html += '</div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

# CONTROLS
c1, c2, c3 = st.columns([2, 1, 1])
with c1:
    margin = st.slider("Margin (Home-Away)", -40, 40, g_margin, key="msl")
with c2:
    mxp = cfg["periods"] + 1
    period = st.selectbox("Period", range(1, mxp + 1), index=min(g_period - 1, mxp - 1), key="psl")
with c3:
    clock_val = st.text_input("Clock", value=g_clock, key="cin")

# FACTORS
with st.expander("⚙️ Factor Adjustments"):
    fvals = {}
    fc = st.columns(2)
    for i, f in enumerate(FACTORS):
        with fc[i % 2]:
            v = st.slider(f["label"], f["lo"], f["hi"], 0.0, step=f["step"], key="f_" + f["id"])
            fvals[f["id"]] = v

# WP CALC
pe = sum(fvals.values())
tf, tsec = get_time_frac(period, clock_val, cfg)
if mode == "pregame":
    em = pe
    tf_use = 1.0
else:
    em = margin + pe * tf
    tf_use = tf
wp = calc_wp(em, tf_use, cfg["pace"])
kv = cfg["pace"] / math.sqrt(max(tf_use, 0.001))

wpc = "#10b981" if wp >= 65 else "#f59e0b" if wp >= 55 else "#ef4444" if wp <= 35 else "#f59e0b" if wp <= 45 else "#94a3b8"
wpl = "STRONG" if wp >= 70 else "LEAN" if wp >= 60 else "SLIGHT" if wp >= 55 else "STRONG (Away)" if wp <= 30 else "LEAN (Away)" if wp <= 40 else "SLIGHT (Away)" if wp <= 45 else "TOSS-UP"

html = '<div style="background:linear-gradient(135deg,#0f172a,#020617);border-radius:12px;padding:16px;border:2px solid ' + wpc + ';text-align:center;margin-bottom:14px">'
html += '<div style="font-size:12px;color:#94a3b8">' + home_team + ' Win Probability</div>'
html += '<div style="font-size:48px;font-weight:800;color:' + wpc + ';font-family:monospace">' + str(round(wp, 1)) + '%</div>'
html += '<div style="font-size:14px;color:' + wpc + ';font-weight:700">' + wpl + '</div>'
if mode == "ingame":
    sgn = "+" if em > 0 else ""
    html += '<div style="font-size:11px;color:#64748b;margin-top:6px">Margin: ' + sgn + str(round(em, 1)) + ' | Time: ' + str(round(tf * 100, 1)) + '% | k = ' + str(round(kv, 4)) + '</div>'
awp = 100 - wp
awc = "#ef4444" if wp < 50 else "#64748b"
hwc = "#10b981" if wp > 50 else "#64748b"
html += '<div style="display:flex;justify-content:center;gap:30px;margin-top:10px">'
html += '<div><div style="color:#64748b;font-size:11px">' + away_team + '</div><div style="font-size:22px;font-weight:700;color:' + awc + '">' + str(round(awp, 1)) + '%</div></div>'
html += '<div><div style="color:#64748b;font-size:11px">' + home_team + '</div><div style="font-size:22px;font-weight:700;color:' + hwc + '">' + str(round(wp, 1)) + '%</div></div>'
html += '</div></div>'
st.markdown(html, unsafe_allow_html=True)

# EDGE FINDER
st.markdown('<div style="text-align:center;color:#f0c040;font-weight:700;font-size:16px;margin:10px 0">💰 KALSHI EDGE FINDER</div>', unsafe_allow_html=True)
kpv = int(k_price) if k_price else 0
kpo = st.number_input("Home ML Price (¢)", min_value=0, max_value=99, value=kpv, key="kpi", help="Auto-filled. Override if needed.")
if kpo > 0:
    kpv = kpo

contracts = st.slider("Contracts", 1, 100, 10, key="csl")

if kpv > 0 and kpv <= 100:
    he = wp - kpv
    ae = abs(he)
    bs = "home" if he >= 0 else "away"
    bside = "yes" if bs == "home" else "no"
    bp = kpv if bs == "home" else 100 - kpv
    wpr = wp if bs == "home" else 100 - wp
    sn = home_team if bs == "home" else away_team
    if he > 10:
        sig = "🔒 STRONG BUY HOME"
    elif he > 5:
        sig = "🔵 BUY HOME"
    elif he > 2:
        sig = "🟡 LEAN HOME"
    elif he < -10:
        sig = "🔒 STRONG BUY AWAY"
    elif he < -5:
        sig = "🔵 BUY AWAY"
    elif he < -2:
        sig = "🟡 LEAN AWAY"
    else:
        sig = "⚪ NO EDGE"
    ec = "#10b981" if he > 8 else "#f59e0b" if he > 3 else "#ef4444" if he < -8 else "#f59e0b" if he < -3 else "#64748b"
    esgn = "+" if he > 0 else ""
    html = '<div style="display:flex;justify-content:center;gap:20px;margin:8px 0">'
    html += '<div style="text-align:center"><div style="color:#64748b;font-size:10px">Model</div><div style="color:' + wpc + ';font-size:20px;font-weight:800">' + str(round(wp, 1)) + '%</div></div>'
    html += '<div style="text-align:center"><div style="color:#64748b;font-size:10px">vs</div><div style="color:#64748b;font-size:20px">→</div></div>'
    html += '<div style="text-align:center"><div style="color:#64748b;font-size:10px">Kalshi</div><div style="color:#38bdf8;font-size:20px;font-weight:800">' + str(kpv) + '¢</div></div>'
    html += '<div style="text-align:center"><div style="color:#64748b;font-size:10px">=</div><div style="color:#64748b;font-size:20px">=</div></div>'
    html += '<div style="text-align:center"><div style="color:#64748b;font-size:10px">Edge</div><div style="color:' + ec + ';font-size:20px;font-weight:800">' + esgn + str(round(he, 1)) + '¢</div></div>'
    html += '</div>'
    html += '<div style="text-align:center;padding:8px;border-radius:8px;background:#020617;border:1px solid ' + ec + ';margin-bottom:10px">'
    html += '<div style="color:' + ec + ';font-size:16px;font-weight:800">' + sig + '</div></div>'
    st.markdown(html, unsafe_allow_html=True)

    # PROFIT
    cost = (bp / 100) * contracts
    pw = ((100 - bp) / 100) * contracts
    ll = cost
    ev = (wpr / 100) * pw - ((100 - wpr) / 100) * ll
    roi = (ev / cost * 100) if cost > 0 else 0
    rr = (ll / pw) if pw > 0 else 99
    evc = "#10b981" if ev > 0 else "#ef4444"
    evs = "+" if ev > 0 else ""
    ros = "+" if roi > 0 else ""
    html = '<div style="display:flex;justify-content:center;gap:6px;flex-wrap:wrap;margin:8px 0">'
    html += '<div style="background:#0f172a;border-radius:6px;padding:6px 12px;text-align:center;min-width:80px;border:1px solid #1e293b"><div style="color:#64748b;font-size:9px">BEST SIDE</div><div style="color:#f0c040;font-size:13px;font-weight:700">' + sn + '</div><div style="color:#64748b;font-size:10px">@ ' + str(bp) + '¢ ' + bside.upper() + '</div></div>'
    html += '<div style="background:#0f172a;border-radius:6px;padding:6px 12px;text-align:center;min-width:80px;border:1px solid #1e293b"><div style="color:#64748b;font-size:9px">COST</div><div style="color:#e2e8f0;font-size:13px;font-weight:700">$' + str(round(cost, 2)) + '</div></div>'
    html += '<div style="background:#0f172a;border-radius:6px;padding:6px 12px;text-align:center;min-width:80px;border:1px solid #1e293b"><div style="color:#64748b;font-size:9px">IF WIN</div><div style="color:#10b981;font-size:13px;font-weight:700">+$' + str(round(pw, 2)) + '</div></div>'
    html += '<div style="background:#0f172a;border-radius:6px;padding:6px 12px;text-align:center;min-width:80px;border:1px solid #1e293b"><div style="color:#64748b;font-size:9px">IF LOSE</div><div style="color:#ef4444;font-size:13px;font-weight:700">-$' + str(round(ll, 2)) + '</div></div>'
    html += '</div>'
    html += '<div style="display:flex;justify-content:center;gap:6px;flex-wrap:wrap;margin:8px 0">'
    html += '<div style="background:#0f172a;border-radius:6px;padding:6px 12px;text-align:center;min-width:90px;border:1px solid ' + evc + '"><div style="color:#64748b;font-size:9px">EV</div><div style="color:' + evc + ';font-size:15px;font-weight:800">' + evs + '$' + str(round(ev, 2)) + '</div></div>'
    html += '<div style="background:#0f172a;border-radius:6px;padding:6px 12px;text-align:center;min-width:90px;border:1px solid #1e293b"><div style="color:#64748b;font-size:9px">ROI</div><div style="color:' + evc + ';font-size:15px;font-weight:800">' + ros + str(round(roi, 1)) + '%</div></div>'
    html += '<div style="background:#0f172a;border-radius:6px;padding:6px 12px;text-align:center;min-width:90px;border:1px solid #1e293b"><div style="color:#64748b;font-size:9px">BREAKEVEN</div><div style="color:#94a3b8;font-size:15px;font-weight:800">' + str(bp) + '%</div></div>'
    html += '<div style="background:#0f172a;border-radius:6px;padding:6px 12px;text-align:center;min-width:90px;border:1px solid #1e293b"><div style="color:#64748b;font-size:9px">RISK:REWARD</div><div style="color:#94a3b8;font-size:15px;font-weight:800">' + str(round(rr, 1)) + ':1</div></div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

    # BUY BUTTON
    if api_ok and k_ticker and ae >= 2:
        blab = "🚀 BUY " + str(contracts) + "x " + sn + " " + bside.upper() + " @ " + str(int(bp)) + "¢"
        if st.button(blab, key="buy", use_container_width=True, type="primary"):
            ok, msg, oid = place_kalshi_order(k_ticker, bside, int(bp), contracts)
            if ok:
                st.success("✅ Order placed! " + str(contracts) + "x " + sn + " " + bside.upper() + " @ " + str(bp) + "¢ — ID: " + oid)
            else:
                st.error("❌ Order failed: " + msg)
            st.session_state.order_log.append({
                "time": datetime.now().strftime("%H:%M:%S"),
                "ticker": k_ticker, "side": bside.upper(),
                "team": sn, "contracts": contracts,
                "price": int(bp), "ok": ok, "msg": msg,
            })
    elif not api_ok:
        st.info("Connect Kalshi API to enable one-click trading")
    elif not k_ticker:
        st.warning("⚠️ Could not match Kalshi ticker")

    # CHECKLIST
    checks = []
    checks.append({"l": "Game Selected", "p": sel_game is not None})
    checks.append({"l": "Edge >= 5¢ (" + str(round(ae, 1)) + "¢)", "p": ae >= 5})
    checks.append({"l": "EV +EV ($" + str(round(ev, 2)) + ")", "p": ev > 0})
    checks.append({"l": "Breakeven < 80% (" + str(bp) + "%)", "p": bp < 80})
    checks.append({"l": "Risk:Reward < 4:1 (" + str(round(rr, 1)) + ":1)", "p": rr < 4})
    checks.append({"l": "Not blowout (margin " + str(abs(margin)) + ")", "p": abs(margin) < 25})
    pc = sum(1 for c in checks if c["p"])
    tc = len(checks)
    vc = "#10b981" if pc == tc else "#f59e0b" if pc >= 4 else "#ef4444"
    vt = "🟢 ALL CLEAR — PLACE TRADE" if pc == tc else "🟡 PROCEED WITH CAUTION" if pc >= 4 else "🔴 DO NOT TRADE"
    st.markdown('<div style="text-align:center;color:#f0c040;font-weight:700;font-size:13px;margin:10px 0">📋 PRE-TRADE CHECKLIST</div>', unsafe_allow_html=True)
    for c in checks:
        ic = "✅" if c["p"] else "❌"
        cl = "#10b981" if c["p"] else "#ef4444"
        bg = "#0a1f0a" if c["p"] else "#1f0a0a"
        st.markdown('<div style="display:flex;align-items:center;gap:8px;padding:4px 8px;border-radius:4px;background:' + bg + ';margin-bottom:2px"><span style="font-size:14px">' + ic + '</span><span style="color:' + cl + ';font-size:12px;font-weight:600">' + c["l"] + '</span></div>', unsafe_allow_html=True)
    st.markdown('<div style="text-align:center;padding:10px;border-radius:8px;background:#020617;border:2px solid ' + vc + ';margin:10px 0"><div style="font-size:18px;font-weight:800;color:' + vc + '">' + vt + '</div></div>', unsafe_allow_html=True)
else:
    st.info("Select a game — Kalshi price auto-fills")

# CHARTS
st.markdown("---")
md = []
for i in range(81):
    m = i - 40
    md.append((m, calc_wp(m, tf_use, cfg["pace"])))
td = []
for i in range(101):
    s = (i / 100) * tsec
    tfr = max(0, (tsec - s) / tsec)
    mv = pe if mode == "pregame" else margin
    td.append((s, calc_wp(mv, tfr, cfg["pace"])))
kl_chart = kpv if kpv > 0 else None
ch1, ch2 = st.columns(2)
with ch1:
    sv1 = build_chart(md, "Score Margin", "Win Prob", [-40, 40], dx=em, dy=wp, kl=kl_chart)
    st.markdown(sv1, unsafe_allow_html=True)
    st.caption("Yellow above green = BUY")
with ch2:
    dtx = tf_use * tsec
    sv2 = build_chart(td, "Seconds Remaining (" + str(tsec) + ")", "Win Prob", [0, tsec], dx=dtx, dy=wp, kl=kl_chart)
    st.markdown(sv2, unsafe_allow_html=True)
    st.caption("Dot pulling away = edge growing")

# ORDER LOG
if st.session_state.order_log:
    st.markdown("---")
    st.markdown("**📋 ORDER LOG (" + str(len(st.session_state.order_log)) + ")**")
    for o in st.session_state.order_log:
        ic = "✅" if o["ok"] else "❌"
        cl = "#10b981" if o["ok"] else "#ef4444"
        bg = "#0a1f0a" if o["ok"] else "#1f0a0a"
        st.markdown('<div style="display:flex;justify-content:space-between;padding:4px 8px;border-radius:4px;background:' + bg + ';margin-bottom:2px"><span style="color:#94a3b8;font-size:11px">' + o["time"] + '</span><span style="color:#e2e8f0;font-size:11px;font-weight:600">' + str(o["contracts"]) + 'x ' + o["team"] + ' ' + o["side"] + ' @ ' + str(o["price"]) + '¢</span><span style="color:' + cl + ';font-size:11px;font-weight:700">' + ic + ' ' + o["msg"] + '</span></div>', unsafe_allow_html=True)

# AUTO REFRESH
st.markdown("---")
auto = st.checkbox("🔄 Auto-refresh (30s)", value=True, key="aref")
if auto:
    time.sleep(30)
    st.rerun()

st.caption("⚠️ Educational only. Not financial advice. v30")
