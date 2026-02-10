import streamlit as st
import yfinance as yf
from datetime import datetime, timedelta
import math

st.set_page_config(page_title="Fibo Playground", page_icon="📐", layout="wide")

# ============================================================
# MARKET CONFIGS
# ============================================================
MARKETS = {
    "S&P 500": {
        "ticker": "^GSPC",
        "kalshi_series": "kxinxu",
        "kalshi_slug": "sp-500-abovebelow",
        "kalshi_url": "https://kalshi.com/markets/kxinxu/sp-500-abovebelow",
        "bracket_step": 25,
        "bracket_min": 5000,
        "bracket_max": 8000,
        "icon": "📊",
        "category": "🟢 Equity Index",
    },
    "Nasdaq 100": {
        "ticker": "^NDX",
        "kalshi_series": "kxnasdaq100u",
        "kalshi_slug": "nasdaq-abovebelow",
        "kalshi_url": "https://kalshi.com/markets/kxnasdaq100u/nasdaq-abovebelow",
        "bracket_step": 50,
        "bracket_min": 15000,
        "bracket_max": 25000,
        "icon": "💻",
        "category": "🟢 Equity Index",
    },
    "Dow Jones": {
        "ticker": "^DJI",
        "kalshi_series": "kxdjiu",
        "kalshi_slug": "dow-jones-abovebelow",
        "kalshi_url": "https://kalshi.com/category/financials",
        "bracket_step": 100,
        "bracket_min": 35000,
        "bracket_max": 55000,
        "icon": "🏛️",
        "category": "🟢 Equity Index",
    },
    "Russell 2000": {
        "ticker": "^RUT",
        "kalshi_series": "kxrutu",
        "kalshi_slug": "russell-2000-abovebelow",
        "kalshi_url": "https://kalshi.com/category/financials",
        "bracket_step": 10,
        "bracket_min": 1500,
        "bracket_max": 3000,
        "icon": "📈",
        "category": "🟢 Equity Index",
    },
    "Gold": {
        "ticker": "GC=F",
        "kalshi_series": "kxgoldu",
        "kalshi_slug": "gold-abovebelow",
        "kalshi_url": "https://kalshi.com/category/financials",
        "bracket_step": 25,
        "bracket_min": 1500,
        "bracket_max": 5000,
        "icon": "🥇",
        "category": "🟢 Commodity",
    },
    "Silver": {
        "ticker": "SI=F",
        "kalshi_series": "kxsilveru",
        "kalshi_slug": "silver-abovebelow",
        "kalshi_url": "https://kalshi.com/category/financials",
        "bracket_step": 0.5,
        "bracket_min": 20,
        "bracket_max": 70,
        "icon": "🥈",
        "category": "🟢 Commodity",
    },
    "Oil (WTI)": {
        "ticker": "CL=F",
        "kalshi_series": "wti",
        "kalshi_slug": "wti-oil-daily-range",
        "kalshi_url": "https://kalshi.com/markets/wti/wti-oil-daily-range",
        "bracket_step": 1,
        "bracket_min": 40,
        "bracket_max": 120,
        "icon": "🛢️",
        "category": "🟢 Commodity",
    },
    "Natural Gas": {
        "ticker": "NG=F",
        "kalshi_series": "kxngu",
        "kalshi_slug": "natural-gas-abovebelow",
        "kalshi_url": "https://kalshi.com/category/financials",
        "bracket_step": 0.25,
        "bracket_min": 1,
        "bracket_max": 10,
        "icon": "🔥",
        "category": "🟡 Commodity",
    },
    "Bitcoin": {
        "ticker": "BTC-USD",
        "kalshi_series": "kxbtcu",
        "kalshi_slug": "bitcoin-abovebelow",
        "kalshi_url": "https://kalshi.com/category/crypto",
        "bracket_step": 500,
        "bracket_min": 30000,
        "bracket_max": 200000,
        "icon": "₿",
        "category": "🟡 Crypto",
    },
    "Ethereum": {
        "ticker": "ETH-USD",
        "kalshi_series": "kxethu",
        "kalshi_slug": "ethereum-abovebelow",
        "kalshi_url": "https://kalshi.com/category/crypto",
        "bracket_step": 50,
        "bracket_min": 500,
        "bracket_max": 8000,
        "icon": "⟠",
        "category": "🟡 Crypto",
    },
    "EUR/USD": {
        "ticker": "EURUSD=X",
        "kalshi_series": "kxeuru",
        "kalshi_slug": "eurusd-abovebelow",
        "kalshi_url": "https://kalshi.com/category/financials",
        "bracket_step": 0.005,
        "bracket_min": 0.9,
        "bracket_max": 1.3,
        "icon": "💶",
        "category": "🟡 FX",
    },
    "USD/JPY": {
        "ticker": "JPY=X",
        "kalshi_series": "kxjpyu",
        "kalshi_slug": "usdjpy-abovebelow",
        "kalshi_url": "https://kalshi.com/category/financials",
        "bracket_step": 0.5,
        "bracket_min": 120,
        "bracket_max": 170,
        "icon": "💴",
        "category": "🟡 FX",
    },
}

FIBO_LEVELS = [
    (0.0, "0% (Swing Low)"),
    (0.236, "23.6%"),
    (0.382, "38.2%"),
    (0.5, "50.0%"),
    (0.618, "61.8% ★ GOLDEN"),
    (0.786, "78.6%"),
    (1.0, "100% (Swing High)"),
]

# ============================================================
# HELPERS
# ============================================================
def make_brackets(cfg):
    step = cfg["bracket_step"]
    lo = cfg["bracket_min"]
    hi = cfg["bracket_max"]
    brackets = []
    v = lo
    while v <= hi:
        brackets.append(round(v, 4))
        v += step
    return brackets

def nearest_bracket_below(val, brackets):
    best = brackets[0]
    for b in brackets:
        if b <= val:
            best = b
    return best

def next_trading_day():
    d = datetime.now() + timedelta(days=1)
    while d.weekday() >= 5:
        d += timedelta(days=1)
    return d

def ticker_date(d):
    months = ["jan","feb","mar","apr","may","jun","jul","aug","sep","oct","nov","dec"]
    return f"{str(d.year)[2:]}{months[d.month-1]}{d.day:02d}"

def kalshi_url(cfg, d):
    # Use confirmed direct URL if available, otherwise construct it
    base = cfg.get("kalshi_url", "")
    td = ticker_date(d)
    constructed = f"https://kalshi.com/markets/{cfg['kalshi_series']}/{cfg['kalshi_slug']}/{cfg['kalshi_series']}-{td}h1600"
    return constructed, base

def fmt_price(val, cfg):
    step = cfg["bracket_step"]
    if step >= 1:
        if step >= 100:
            return f"{val:,.0f}"
        elif step >= 10:
            return f"{val:,.0f}"
        else:
            return f"{val:,.0f}"
    elif step >= 0.01:
        return f"{val:,.2f}"
    else:
        return f"{val:,.4f}"

@st.cache_data(ttl=300)
def fetch_data(ticker, days):
    end = datetime.now()
    start = end - timedelta(days=days * 2 + 5)
    df = yf.download(ticker, start=start.strftime("%Y-%m-%d"), end=end.strftime("%Y-%m-%d"), progress=False)
    if df.empty:
        return None, None, None
    df = df.tail(days)
    high = float(df["High"].max())
    low = float(df["Low"].min())
    close = float(df["Close"].iloc[-1])
    return round(high, 4), round(low, 4), round(close, 4)

# ============================================================
# STYLING
# ============================================================
st.markdown("""
<style>
    .stApp {background-color: #0d1117}
    .block-container {max-width: 900px}
    h1, h2, h3 {font-family: 'Courier New', monospace !important}
    .big-pick {
        background: linear-gradient(135deg, #1a1a0e, #2a2a0e);
        border: 2px solid #f0b90b;
        border-radius: 12px;
        padding: 24px;
        text-align: center;
        margin: 16px 0;
    }
    .pick-title {color: #f0b90b; font-size: 14px; text-transform: uppercase; letter-spacing: 2px}
    .pick-main {color: #ffffff; font-size: 32px; font-weight: bold; font-family: 'Courier New', monospace}
    .pick-sub {color: #8b949e; font-size: 14px}
    .cushion-num {color: #3fb950; font-size: 28px; font-weight: bold; font-family: 'Courier New', monospace}
    .cushion-label {color: #8b949e; font-size: 12px}
    .metric-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 12px;
        text-align: center;
    }
    .metric-label {color: #8b949e; font-size: 11px; text-transform: uppercase}
    .metric-val {font-size: 22px; font-weight: bold; font-family: 'Courier New', monospace}
    .market-btn {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 10px;
        text-align: center;
        cursor: pointer;
    }
    .market-btn:hover {border-color: #f0b90b}
    .green {color: #3fb950}
    .red {color: #f85149}
    .gold {color: #f0b90b}
</style>
""", unsafe_allow_html=True)

# ============================================================
# HEADER
# ============================================================
st.markdown("<h1 style='text-align:center; color:#f0b90b; border-bottom:2px solid #f0b90b; padding-bottom:10px'>📐 FIBONACCI PLAYGROUND</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#8b949e; font-family:monospace'>Golden Ratio Edge — All Markets</p>", unsafe_allow_html=True)

# ============================================================
# MARKET SELECTOR
# ============================================================
st.markdown("---")

col_market, col_lookback = st.columns([3, 1])

with col_market:
    categories = {}
    for name, cfg in MARKETS.items():
        cat = cfg["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(name)

    market_options = []
    for cat in sorted(categories.keys()):
        for name in categories[cat]:
            market_options.append(f"{MARKETS[name]['icon']} {name}")

    selected_display = st.selectbox("Select Market", market_options, index=0)
    selected_name = selected_display.split(" ", 1)[1]
    cfg = MARKETS[selected_name]

with col_lookback:
    lookback = st.selectbox("Lookback", [3, 5, 10, 20], index=1, format_func=lambda x: f"{x} days")

# ============================================================
# FETCH DATA
# ============================================================
with st.spinner(f"🔄 Fetching {selected_name} data..."):
    high, low, close = fetch_data(cfg["ticker"], lookback)

if high is None:
    st.error(f"❌ Failed to fetch {selected_name} data. Ticker: {cfg['ticker']}")
    st.stop()

st.success(f"✅ {selected_name} data loaded — {lookback}-day window | Source: Yahoo Finance ({cfg['ticker']})")

# ============================================================
# CALCULATIONS
# ============================================================
brackets = make_brackets(cfg)
rng = round(high - low, 4)

levels = []
for pct, label in FIBO_LEVELS:
    price = low + rng * pct
    bracket = nearest_bracket_below(price, brackets)
    dist = close - bracket
    dist_pct = round((dist / close) * 100, 2) if close != 0 else 0
    levels.append({
        "pct": pct,
        "label": label,
        "price": round(price, 4),
        "bracket": bracket,
        "dist": round(dist, 2),
        "dist_pct": dist_pct
    })

golden = [l for l in levels if l["pct"] == 0.618][0]
pick = golden["bracket"]
cushion = round(close - pick, 4)
cushion_pct = round((cushion / close) * 100, 2) if close != 0 else 0
nd = next_trading_day()
kurl_direct, kurl_browse = kalshi_url(cfg, nd)

# ============================================================
# MARKET DATA BAR
# ============================================================
c1, c2, c3, c4 = st.columns(4)
fp = lambda v: fmt_price(v, cfg)

with c1:
    st.markdown(f'<div class="metric-card"><div class="metric-label">Last Close</div><div class="metric-val" style="color:#e6edf3">{fp(close)}</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="metric-card"><div class="metric-label">{lookback}D High</div><div class="metric-val green">{fp(high)}</div></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="metric-card"><div class="metric-label">{lookback}D Low</div><div class="metric-val red">{fp(low)}</div></div>', unsafe_allow_html=True)
with c4:
    st.markdown(f'<div class="metric-card"><div class="metric-label">Range</div><div class="metric-val" style="color:#e6edf3">{fp(rng)}</div></div>', unsafe_allow_html=True)

# ============================================================
# THE PICK
# ============================================================
st.markdown(f"""
<div class="big-pick">
    <div class="pick-title">★ {cfg['icon']} {selected_name} — Golden Ratio Pick ★</div>
    <div class="pick-main">BUY YES — {fp(pick)} or above</div>
    <div class="pick-sub">61.8% Fibo = {fp(golden['price'])} → Nearest bracket: {fp(pick)}</div>
    <br>
    <div style="display:flex; justify-content:center; gap:40px">
        <div><div class="cushion-num">{fp(cushion)} pts</div><div class="cushion-label">Cushion from close</div></div>
        <div><div class="cushion-num">{cushion_pct}%</div><div class="cushion-label">Drop needed to lose</div></div>
    </div>
    <br>
    <div style="color:#8b949e; font-size:13px">Market: {nd.strftime('%A %b %d, %Y')} at 4pm EST</div>
    <br>
    <a href="{kurl_direct}" target="_blank" style="display:inline-block; background:#f0b90b; color:#000; padding:12px 32px; border-radius:8px; font-weight:bold; font-size:16px; text-decoration:none; font-family:monospace">🎯 OPEN ON KALSHI →</a>
    <div style="color:#484f58; font-size:10px; margin-top:6px">{kurl_direct}</div>
    <div style="margin-top:8px"><a href="{kurl_browse}" target="_blank" style="color:#58a6ff; font-size:12px; text-decoration:none">📂 Browse all {selected_name} brackets →</a></div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# ALL MARKETS QUICK SCAN
# ============================================================
st.markdown("---")
st.markdown("### 🔍 All Markets Quick Scan")
st.markdown("<p style='color:#8b949e; font-size:12px'>Golden ratio picks across all markets at a glance</p>", unsafe_allow_html=True)

scan_cols = st.columns(3)
col_idx = 0

for mname, mcfg in MARKETS.items():
    try:
        mh, ml, mc = fetch_data(mcfg["ticker"], lookback)
        if mh is None or ml is None or mc is None:
            continue
        mb = make_brackets(mcfg)
        mrng = mh - ml
        gprice = ml + mrng * 0.618
        gpick = nearest_bracket_below(gprice, mb)
        mcush = mc - gpick
        mcush_pct = round((mcush / mc) * 100, 2) if mc != 0 else 0
        mfp = lambda v, c=mcfg: fmt_price(v, c)
        color = "#3fb950" if mcush >= 0 else "#f85149"

        with scan_cols[col_idx % 3]:
            st.markdown(f"""
            <div style="background:#161b22; border:1px solid #30363d; border-radius:8px; padding:12px; margin-bottom:10px">
                <div style="color:#f0b90b; font-size:13px; font-weight:bold">{mcfg['icon']} {mname}</div>
                <div style="color:#e6edf3; font-size:11px">Close: {mfp(mc)} | Pick: <span style="color:#f0b90b; font-weight:bold">{mfp(gpick)}</span></div>
                <div style="color:{color}; font-size:11px">Cushion: {mfp(mcush)} ({mcush_pct}%)</div>
            </div>
            """, unsafe_allow_html=True)
        col_idx += 1
    except:
        continue

# ============================================================
# FIBO TABLE
# ============================================================
st.markdown("---")
st.markdown(f"### {cfg['icon']} {selected_name} — All Fibonacci Levels")

header = "| Level | Price | Bracket | Cushion | Trade |"
sep = "|:------|------:|--------:|--------:|:-----:|"
rows = [header, sep]
for l in levels:
    g = "**" if l["pct"] == 0.618 else ""
    dc = "🟢" if l["dist"] >= 0 else "🔴"
    link = f"[Open →]({kurl_browse})"
    rows.append(f"| {g}{l['label']}{g} | {fp(l['price'])} | {g}{fp(l['bracket'])}{g} | {dc} {fp(l['dist'])} ({l['dist_pct']}%) | {link} |")
st.markdown("\n".join(rows))

# ============================================================
# FORMULA
# ============================================================
st.markdown(f"### 📐 The Formula — {selected_name}")
st.markdown(f"""
1. Get {lookback}-day swing high & low for **{selected_name}** ({cfg['ticker']})
2. Range = {fp(high)} − {fp(low)} = **{fp(rng)}**
3. Golden = Low + (Range × 0.618) = {fp(low)} + ({fp(rng)} × 0.618) = **{fp(golden['price'])}**
4. Nearest bracket ≤ golden = **{fp(pick)}**
5. **BUY YES on "{fp(pick)} or above"**
""")

# ============================================================
# MARKET NOTES
# ============================================================
st.markdown("---")
st.markdown("### 📋 Market Fit Guide")
st.markdown("""
| Rating | Markets | Notes |
|:-------|:--------|:------|
| 🟢 **Best** | S&P 500, Nasdaq, Dow, Russell, Gold, Oil | Clear swing levels, mean-reversion, well-defined brackets |
| 🟡 **Good** | Natural Gas, Bitcoin, Ethereum, EUR/USD, USD/JPY | More volatile, use shorter lookback, expect false breaks |
| 🔴 **Skip** | Temperature, Weather | Not price-driven, use SHARK instead |
""")

st.markdown("---")
st.markdown("""
<div style="background:#161b22; border:1px solid #30363d; border-radius:8px; padding:16px; margin-top:16px">
<p style="color:#f0b90b; font-size:13px; font-weight:bold; margin-bottom:8px">⚠️ DISCLAIMER</p>
<p style="color:#8b949e; font-size:11px; line-height:1.7">
This tool is for <strong>research and educational purposes only</strong>. It is NOT financial advice. 
Fibonacci retracement levels are technical analysis indicators based on historical price patterns — they do NOT predict future price movements. 
Past performance does not guarantee future results. All trading involves risk and you can lose your entire investment. 
The golden ratio pick is a mathematical calculation, not a recommendation to buy or sell. 
Always do your own research and never trade more than you can afford to lose. 
This tool has no affiliation with Kalshi, Yahoo Finance, or any exchange.
</p>
</div>
""", unsafe_allow_html=True)
st.markdown(f"<p style='color:#484f58; font-size:11px; text-align:center; margin-top:12px'>Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Data: Yahoo Finance | Auto-refreshes every 5 min</p>", unsafe_allow_html=True)
