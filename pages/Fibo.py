import streamlit as st
import yfinance as yf
from datetime import datetime, timedelta
import math

st.set_page_config(page_title="Fibo Bracket Finder", page_icon="📐", layout="wide")

# ============================================================
# CONSTANTS
# ============================================================
BRACKETS = list(range(6200, 7500, 25))
FIBO_LEVELS = [
    (0.0, "0% (Swing Low)"),
    (0.236, "23.6%"),
    (0.382, "38.2%"),
    (0.5, "50.0%"),
    (0.618, "61.8% ★ GOLDEN"),
    (0.786, "78.6%"),
    (1.0, "100% (Swing High)"),
]

def nearest_bracket_below(val):
    best = BRACKETS[0]
    for b in BRACKETS:
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

def kalshi_url(d):
    return f"https://kalshi.com/markets/kxinxu/sp-500-abovebelow/kxinxu-{ticker_date(d)}h1600"

# ============================================================
# STYLING
# ============================================================
st.markdown("""
<style>
    .stApp {background-color: #0d1117}
    .block-container {max-width: 850px}
    h1, h2, h3 {font-family: 'Courier New', monospace !important}
    .gold {color: #f0b90b; font-weight: bold}
    .green {color: #3fb950}
    .red {color: #f85149}
    .big-pick {
        background: linear-gradient(135deg, #1a1a0e, #2a2a0e);
        border: 2px solid #f0b90b;
        border-radius: 12px;
        padding: 24px;
        text-align: center;
        margin: 16px 0;
    }
    .pick-title {color: #f0b90b; font-size: 14px; text-transform: uppercase; letter-spacing: 2px}
    .pick-main {color: #ffffff; font-size: 36px; font-weight: bold; font-family: 'Courier New', monospace}
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
    .metric-val {font-size: 24px; font-weight: bold; font-family: 'Courier New', monospace}
</style>
""", unsafe_allow_html=True)

# ============================================================
# HEADER
# ============================================================
st.markdown("<h1 style='text-align:center; color:#f0b90b; border-bottom:2px solid #f0b90b; padding-bottom:10px'>📐 FIBONACCI BRACKET FINDER</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#8b949e; font-family:monospace'>S&P 500 Daily Brackets — Golden Ratio Edge</p>", unsafe_allow_html=True)

# ============================================================
# CONTROLS
# ============================================================
col1, col2 = st.columns([1, 3])
with col1:
    lookback = st.selectbox("Lookback", [5, 10, 20], index=0, format_func=lambda x: f"{x} days")

# ============================================================
# FETCH DATA
# ============================================================
@st.cache_data(ttl=300)
def fetch_sp500(days):
    end = datetime.now()
    start = end - timedelta(days=days * 2)
    df = yf.download("^GSPC", start=start.strftime("%Y-%m-%d"), end=end.strftime("%Y-%m-%d"), progress=False)
    if df.empty:
        return None, None, None
    df = df.tail(days)
    high = float(df["High"].max())
    low = float(df["Low"].min())
    close = float(df["Close"].iloc[-1])
    return round(high, 2), round(low, 2), round(close, 2)

with st.spinner("🔄 Fetching S&P 500 data..."):
    high, low, close = fetch_sp500(lookback)

if high is None:
    st.error("❌ Failed to fetch data. Check your internet connection.")
    st.stop()

st.success(f"✅ Data loaded from Yahoo Finance — {lookback}-day window")

# ============================================================
# CALCULATIONS
# ============================================================
rng = round(high - low, 2)
levels = []
for pct, label in FIBO_LEVELS:
    price = low + rng * pct
    bracket = nearest_bracket_below(price)
    dist = close - bracket
    dist_pct = round((dist / close) * 100, 2)
    levels.append({"pct": pct, "label": label, "price": round(price, 2), "bracket": bracket, "dist": round(dist, 1), "dist_pct": dist_pct})

golden = [l for l in levels if l["pct"] == 0.618][0]
pick = golden["bracket"]
cushion = round(close - pick, 1)
cushion_pct = round((cushion / close) * 100, 2)
nd = next_trading_day()
kurl = kalshi_url(nd)

# ============================================================
# MARKET DATA BAR
# ============================================================
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f"""<div class="metric-card"><div class="metric-label">Last Close</div><div class="metric-val" style="color:#e6edf3">{close:,.2f}</div></div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""<div class="metric-card"><div class="metric-label">{lookback}D High</div><div class="metric-val green">{high:,.2f}</div></div>""", unsafe_allow_html=True)
with c3:
    st.markdown(f"""<div class="metric-card"><div class="metric-label">{lookback}D Low</div><div class="metric-val red">{low:,.2f}</div></div>""", unsafe_allow_html=True)
with c4:
    st.markdown(f"""<div class="metric-card"><div class="metric-label">Range</div><div class="metric-val" style="color:#e6edf3">{rng:,.2f}</div></div>""", unsafe_allow_html=True)

# ============================================================
# THE PICK
# ============================================================
st.markdown(f"""
<div class="big-pick">
    <div class="pick-title">★ Golden Ratio Pick ★</div>
    <div class="pick-main">BUY YES — {pick:,} or above</div>
    <div class="pick-sub">61.8% Fibo = {golden['price']:,.2f} → Nearest bracket: {pick:,}</div>
    <br>
    <div style="display:flex; justify-content:center; gap:40px">
        <div><div class="cushion-num">{cushion} pts</div><div class="cushion-label">Cushion from close</div></div>
        <div><div class="cushion-num">{cushion_pct}%</div><div class="cushion-label">Drop needed to lose</div></div>
    </div>
    <br>
    <div style="color:#8b949e; font-size:13px">Market: {nd.strftime('%A %b %d, %Y')} at 4pm EST</div>
    <br>
    <a href="{kurl}" target="_blank" style="display:inline-block; background:#f0b90b; color:#000; padding:12px 32px; border-radius:8px; font-weight:bold; font-size:16px; text-decoration:none; font-family:monospace">🎯 OPEN ON KALSHI →</a>
    <div style="color:#484f58; font-size:10px; margin-top:6px">{kurl}</div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# FIBO TABLE
# ============================================================
st.markdown("### All Fibonacci Levels")
header = "| Level | Price | Bracket | Cushion | Trade |"
sep = "|:------|------:|--------:|--------:|:-----:|"
rows = [header, sep]
for l in levels:
    g = "**" if l["pct"] == 0.618 else ""
    dc = "🟢" if l["dist"] >= 0 else "🔴"
    link = f"[Open →]({kurl})"
    rows.append(f"| {g}{l['label']}{g} | {l['price']:,.2f} | {g}{l['bracket']:,}{g} | {dc} {l['dist']} ({l['dist_pct']}%) | {link} |")
st.markdown("\n".join(rows))

# ============================================================
# FORMULA
# ============================================================
st.markdown("### 📐 The Formula")
st.markdown(f"""
1. Get {lookback}-day swing high & low  
2. Range = {high:,.2f} − {low:,.2f} = **{rng:,.2f}**  
3. Golden = Low + (Range × 0.618) = {low:,.2f} + ({rng:,.2f} × 0.618) = **{golden['price']:,.2f}**  
4. Nearest bracket ≤ golden = **{pick:,}**  
5. **BUY YES on "{pick:,} or above"**
""")

st.markdown("---")
st.markdown(f"<p style='color:#484f58; font-size:11px; text-align:center'>Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Data: Yahoo Finance | Auto-refreshes every 5 min</p>", unsafe_allow_html=True)
