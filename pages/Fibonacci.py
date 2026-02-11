import streamlit as st
import yfinance as yf
import numpy as np
from datetime import datetime, timedelta
import math
import time
import base64
import requests
from cryptography.hazmat.primitives.asymmetric import padding as asym_padding
from cryptography.hazmat.primitives import hashes, serialization

st.set_page_config(page_title="Fibo Reaction Engine", page_icon="📐", layout="wide")

# ============================================================
# KALSHI AUTH
# ============================================================
API_KEY = st.secrets.get("KALSHI_API_KEY", "")
PRIVATE_KEY = st.secrets.get("KALSHI_PRIVATE_KEY", "")
KALSHI_BASE = "https://api.elections.kalshi.com"

def create_kalshi_signature(method, path, timestamp_str):
    key_data = PRIVATE_KEY.strip()
    if "BEGIN" not in key_data:
        key_data = "-----BEGIN RSA PRIVATE KEY-----\n" + key_data + "\n-----END RSA PRIVATE KEY-----"
    priv = serialization.load_pem_private_key(key_data.encode(), password=None)
    msg = (timestamp_str + method + path).encode()
    sig = priv.sign(
        msg,
        asym_padding.PSS(
            mgf=asym_padding.MGF1(hashes.SHA256()),
            salt_length=asym_padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    return base64.b64encode(sig).decode()

def kalshi_headers(method, path):
    ts = str(int(time.time()))
    sig = create_kalshi_signature(method, path, ts)
    return {
        "Content-Type": "application/json",
        "KALSHI-ACCESS-KEY": API_KEY,
        "KALSHI-ACCESS-SIGNATURE": sig,
        "KALSHI-ACCESS-TIMESTAMP": ts,
    }

# ============================================================
# SCORE WEIGHTS & FIBO LEVELS
# ============================================================
SCORE_WEIGHTS = {
    "location": 0.20,
    "volatility": 0.20,
    "momentum": 0.20,
    "flow": 0.15,
    "mispricing": 0.25,
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

# ============================================================
# CSS
# ============================================================
st.markdown("""
<style>
    .stApp {background-color: #0d1117}
    .block-container {max-width: 960px}
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
    .score-gauge {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        margin: 12px 0;
    }
    .score-big {font-size: 64px; font-weight: bold; font-family: 'Courier New', monospace}
    .regime-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 16px;
        font-size: 12px;
        font-weight: bold;
        font-family: 'Courier New', monospace;
    }
    .green {color: #3fb950}
    .red {color: #f85149}
    .gold {color: #f0b90b}
    .yellow {color: #d29922}
</style>
""", unsafe_allow_html=True)
# ============================================================
# DATA FETCHING
# ============================================================
@st.cache_data(ttl=300)
def fetch_full_data(ticker, days):
    """Returns full DataFrame with OHLCV for technical analysis."""
    end = datetime.now()
    start = end - timedelta(days=days * 2 + 10)
    df = yf.download(ticker, start=start.strftime("%Y-%m-%d"), end=end.strftime("%Y-%m-%d"), progress=False)
    if df.empty:
        return None
    if hasattr(df.columns, 'levels'):
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
    return df.tail(days + 20)

def extract_hlc(df, days):
    """Extract high, low, close from last N days of DataFrame."""
    if df is None or len(df) < 1:
        return None, None, None
    recent = df.tail(days)
    high = float(recent["High"].max())
    low = float(recent["Low"].min())
    close = float(df["Close"].iloc[-1])
    return round(high, 4), round(low, 4), round(close, 4)

# ============================================================
# BRACKET HELPERS
# ============================================================
def make_brackets(cfg):
    step = cfg.get("bracket_step", 1)
    lo = cfg.get("bracket_min", 0)
    hi = cfg.get("bracket_max", 10000)
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
    """Returns (direct_url, browse_url).
    Kalshi web URLs don't support deep-linking to specific event tickers,
    so direct_url points to the series browse page.
    The API event ticker is only used for API calls, not web URLs."""
    base = cfg.get("kalshi_url", "")
    series = cfg.get("kalshi_series", "")
    slug = cfg.get("kalshi_slug", "")
    # Best working URL: series browse page
    browse = "https://kalshi.com/markets/" + series + "/" + slug if series and slug else base
    return browse, base

def fmt_price(val, cfg):
    step = cfg.get("bracket_step", 1)
    if step >= 1:
        return f"{val:,.0f}"
    elif step >= 0.01:
        return f"{val:,.2f}"
    else:
        return f"{val:,.4f}"

# ============================================================
# KALSHI LIVE DATA
# ============================================================
@st.cache_data(ttl=120)
def fetch_kalshi_event_markets(series, slug, date_obj):
    """Fetch live Kalshi bracket prices for an event."""
    td = ticker_date(date_obj)
    event_ticker = series + "-" + td + "h1600"
    path = "/trade-api/v2/events/" + event_ticker
    try:
        r = requests.get(
            KALSHI_BASE + path,
            headers=kalshi_headers("GET", path),
            timeout=10
        )
        if r.status_code != 200:
            return {}
        data = r.json()
        markets = data.get("markets", [])
        if not markets:
            event_data = data.get("event", {})
            markets = event_data.get("markets", [])
        result = {}
        for m in markets:
            ticker = m.get("ticker", "")
            subtitle = m.get("subtitle", m.get("title", ""))
            yes_bid = m.get("yes_bid", 0)
            yes_ask = m.get("yes_ask", 0)
            no_bid = m.get("no_bid", 0)
            volume = m.get("volume", 0)
            result[ticker] = {
                "subtitle": subtitle,
                "yes_bid": yes_bid,
                "yes_ask": yes_ask,
                "no_bid": no_bid,
                "volume": volume,
                "implied_prob": yes_bid,
            }
        return result
    except Exception:
        return {}

@st.cache_data(ttl=120)
def fetch_kalshi_series_markets(series):
    """Fetch all active markets in a Kalshi series."""
    path = "/trade-api/v2/markets"
    params = "?series_ticker=" + series + "&status=open&limit=50"
    full_path = path + params
    try:
        r = requests.get(
            KALSHI_BASE + full_path,
            headers=kalshi_headers("GET", full_path),
            timeout=10
        )
        if r.status_code != 200:
            return {}
        data = r.json()
        markets = data.get("markets", [])
        result = {}
        for m in markets:
            ticker = m.get("ticker", "")
            subtitle = m.get("subtitle", m.get("title", ""))
            yes_bid = m.get("yes_bid", 0)
            yes_ask = m.get("yes_ask", 0)
            floor = m.get("floor_strike", None)
            cap = m.get("cap_strike", None)
            result[ticker] = {
                "subtitle": subtitle,
                "yes_bid": yes_bid,
                "yes_ask": yes_ask,
                "floor": floor,
                "cap": cap,
                "implied_prob": yes_bid,
            }
        return result
    except Exception:
        return {}

def get_kalshi_balance():
    path = "/trade-api/v2/portfolio/balance"
    try:
        r = requests.get(
            KALSHI_BASE + path,
            headers=kalshi_headers("GET", path),
            timeout=10
        )
        d = r.json()
        return d.get("balance", 0) / 100.0
    except Exception:
        return 0.0
        # ============================================================
# LAYER 1: LOCATION SCORE (0-10)
# ============================================================
def score_location(close, golden_price, rng):
    """Score based on distance from price to 61.8% fib level."""
    if rng == 0:
        return 5.0
    dist = abs(close - golden_price)
    dist_ratio = dist / rng
    raw = max(0, 10 - (dist_ratio * 20))
    return round(min(10, raw), 1)

# ============================================================
# LAYER 2: VOLATILITY REGIME (0-10)
# ============================================================
def compute_atr(df, period):
    """Average True Range for N periods."""
    if len(df) < period + 1:
        return 0.0
    highs = df["High"].values
    lows = df["Low"].values
    closes = df["Close"].values
    trs = []
    for i in range(1, len(df)):
        h = float(highs[i])
        l = float(lows[i])
        cp = float(closes[i - 1])
        tr = max(h - l, abs(h - cp), abs(l - cp))
        trs.append(tr)
    if len(trs) < period:
        return sum(trs) / max(len(trs), 1)
    return sum(trs[-period:]) / period

def compute_bollinger_width_percentile(df, period=20, lookback=30):
    """Bollinger Band width percentile over lookback days."""
    closes = df["Close"].values
    if len(closes) < period + lookback:
        return 50.0
    widths = []
    for i in range(period, len(closes)):
        window = closes[i - period:i]
        mean_val = float(np.mean(window))
        std_val = float(np.std(window))
        if mean_val == 0:
            widths.append(0)
        else:
            widths.append((std_val * 2) / mean_val)
    if len(widths) < 2:
        return 50.0
    current = widths[-1]
    recent = widths[-lookback:] if len(widths) >= lookback else widths
    rank = sum(1 for w in recent if w <= current)
    pct = (rank / len(recent)) * 100
    return round(pct, 1)

def score_volatility(df):
    """Volatility regime score. Compression = higher score.
    Returns (score 0-10, regime_label, atr_ratio, bb_percentile).
    ALL RETURN VALUES ARE PLAIN PYTHON TYPES (float, str)."""
    atr5 = compute_atr(df, 5)
    atr20 = compute_atr(df, 20)
    if atr20 == 0:
        ratio = 1.0
    else:
        ratio = atr5 / atr20
    bb_pct = compute_bollinger_width_percentile(df)
    if ratio < 0.6:
        ratio_score = 10
    elif ratio < 0.8:
        ratio_score = 8
    elif ratio < 1.0:
        ratio_score = 6
    elif ratio < 1.2:
        ratio_score = 4
    else:
        ratio_score = 2
    if bb_pct < 20:
        bb_score = 10
    elif bb_pct < 40:
        bb_score = 7
    elif bb_pct < 60:
        bb_score = 5
    elif bb_pct < 80:
        bb_score = 3
    else:
        bb_score = 1
    combined = (ratio_score * 0.5) + (bb_score * 0.5)
    if ratio < 0.8:
        regime = "COMPRESSION"
    elif ratio > 1.2:
        regime = "EXPANSION"
    else:
        regime = "NORMAL"
    return round(float(combined), 1), str(regime), round(float(ratio), 3), round(float(bb_pct), 1)

# ============================================================
# LAYER 3: MOMENTUM EXHAUSTION (0-10)
# ============================================================
def compute_rsi(df, period=14):
    """RSI calculation."""
    closes = df["Close"].values
    if len(closes) < period + 1:
        return 50.0
    deltas = []
    for i in range(1, len(closes)):
        deltas.append(float(closes[i]) - float(closes[i - 1]))
    gains = [d if d > 0 else 0 for d in deltas]
    losses = [-d if d < 0 else 0 for d in deltas]
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return round(rsi, 1)

def compute_macd_hist_slope(df):
    """MACD histogram slope (last 3 bars)."""
    closes = df["Close"].values.astype(float)
    if len(closes) < 26:
        return 0.0
    def ema(data, period):
        result = [data[0]]
        mult = 2.0 / (period + 1)
        for i in range(1, len(data)):
            result.append((data[i] - result[-1]) * mult + result[-1])
        return result
    ema12 = ema(list(closes), 12)
    ema26 = ema(list(closes), 26)
    macd_line = [ema12[i] - ema26[i] for i in range(len(closes))]
    signal = ema(macd_line, 9)
    hist = [macd_line[i] - signal[i] for i in range(len(closes))]
    if len(hist) < 3:
        return 0.0
    slope = hist[-1] - hist[-3]
    return round(slope, 4)

def compute_roc(df, period=3):
    """Rate of Change over N periods."""
    closes = df["Close"].values
    if len(closes) < period + 1:
        return 0.0
    current = float(closes[-1])
    past = float(closes[-period - 1])
    if past == 0:
        return 0.0
    return round(((current - past) / past) * 100, 2)

def score_momentum(df):
    """Momentum exhaustion score.
    Returns (score 0-10, rsi, macd_slope, roc)."""
    rsi = compute_rsi(df)
    macd_slope = compute_macd_hist_slope(df)
    roc = compute_roc(df)
    if rsi < 30 or rsi > 70:
        rsi_score = 9
    elif rsi < 35 or rsi > 65:
        rsi_score = 7
    elif rsi < 40 or rsi > 60:
        rsi_score = 5
    else:
        rsi_score = 3
    if macd_slope < -0.5:
        macd_score = 9
    elif macd_slope < -0.1:
        macd_score = 7
    elif macd_slope < 0.1:
        macd_score = 5
    else:
        macd_score = 3
    abs_roc = abs(roc)
    if abs_roc < 0.5:
        roc_score = 9
    elif abs_roc < 1.0:
        roc_score = 7
    elif abs_roc < 2.0:
        roc_score = 5
    else:
        roc_score = 3
    combined = (rsi_score * 0.4) + (macd_score * 0.35) + (roc_score * 0.25)
    return round(combined, 1), rsi, macd_slope, roc
    # ============================================================
# LAYER 4: ORDER FLOW PROXY (0-10)
# ============================================================
def score_flow(df):
    """Order flow proxy using volume ratio and VWAP distance.
    Returns (score 0-10, vol_ratio, vwap_dist_pct)."""
    if "Volume" not in df.columns or len(df) < 21:
        return 5.0, 1.0, 0.0
    volumes = df["Volume"].values
    closes = df["Close"].values
    highs = df["High"].values
    lows = df["Low"].values
    current_vol = float(volumes[-1])
    avg_vol_20 = float(np.mean(volumes[-21:-1])) if len(volumes) >= 21 else float(np.mean(volumes[:-1]))
    if avg_vol_20 == 0:
        vol_ratio = 1.0
    else:
        vol_ratio = current_vol / avg_vol_20
    # VWAP approximation using typical price * volume
    typical = [(float(highs[i]) + float(lows[i]) + float(closes[i])) / 3.0 for i in range(len(df))]
    vols = [float(volumes[i]) for i in range(len(df))]
    cum_tv = 0.0
    cum_v = 0.0
    for i in range(len(df)):
        cum_tv += typical[i] * vols[i]
        cum_v += vols[i]
    vwap = cum_tv / cum_v if cum_v > 0 else float(closes[-1])
    current_close = float(closes[-1])
    vwap_dist = round(((current_close - vwap) / vwap) * 100, 2) if vwap != 0 else 0.0
    # Score volume ratio
    if vol_ratio > 2.0:
        vol_score = 9
    elif vol_ratio > 1.5:
        vol_score = 7
    elif vol_ratio > 1.0:
        vol_score = 5
    elif vol_ratio > 0.5:
        vol_score = 3
    else:
        vol_score = 1
    # Score VWAP distance (closer to VWAP = better for mean reversion)
    abs_vwap = abs(vwap_dist)
    if abs_vwap < 0.3:
        vwap_score = 9
    elif abs_vwap < 0.7:
        vwap_score = 7
    elif abs_vwap < 1.5:
        vwap_score = 5
    elif abs_vwap < 3.0:
        vwap_score = 3
    else:
        vwap_score = 1
    combined = (vol_score * 0.5) + (vwap_score * 0.5)
    return round(float(combined), 1), round(float(vol_ratio), 2), round(float(vwap_dist), 2)

# ============================================================
# LAYER 5: MISPRICING SCORE (0-10)
# ============================================================
def score_mispricing(df, pick_bracket, kalshi_data):
    """Mispricing score using empirical probability (last 60 returns) vs market implied.
    Returns (score 0-10, model_prob, market_prob_or_None, edge_pct)."""
    closes = df["Close"].values
    current = float(closes[-1])
    # Empirical probability: what % of last 60 daily returns would keep price above pick?
    n_returns = min(60, len(closes) - 1)
    if n_returns < 5:
        return 5.0, 50.0, None, 0.0
    returns = []
    for i in range(len(closes) - n_returns, len(closes)):
        if i > 0:
            prev = float(closes[i - 1])
            curr = float(closes[i])
            if prev != 0:
                returns.append((curr - prev) / prev)
    if len(returns) < 5:
        return 5.0, 50.0, None, 0.0
    # Project: how many of these returns would land above pick_bracket?
    above_count = 0
    for r in returns:
        projected = current * (1 + r)
        if projected >= pick_bracket:
            above_count += 1
    model_prob = round((above_count / len(returns)) * 100, 1)
    # Find market implied from Kalshi data
    market_prob = None
    if kalshi_data:
        best_match = None
        for ticker, mdata in kalshi_data.items():
            subtitle = str(mdata.get("subtitle", "")).lower()
            floor = mdata.get("floor", None)
            # Try to match by floor strike
            if floor is not None:
                try:
                    if abs(float(floor) - pick_bracket) < 0.01:
                        best_match = mdata
                        break
                except (ValueError, TypeError):
                    pass
            # Try subtitle match
            pick_str = str(int(pick_bracket)) if pick_bracket == int(pick_bracket) else str(pick_bracket)
            if pick_str in subtitle:
                best_match = mdata
                break
        if best_match:
            yb = best_match.get("yes_bid", 0)
            if yb and yb > 0:
                market_prob = round(float(yb), 1)
    # Compute edge
    if market_prob is not None and market_prob > 0:
        edge_pct = round(model_prob - market_prob, 1)
    else:
        edge_pct = 0.0
    # Score
    abs_edge = abs(edge_pct)
    if market_prob is not None:
        if abs_edge > 15:
            score = 10
        elif abs_edge > 10:
            score = 8
        elif abs_edge > 6:
            score = 7
        elif abs_edge > 3:
            score = 5
        else:
            score = 3
        # Bonus if edge is positive (model says underpriced)
        if edge_pct > 6:
            score = min(10, score + 1)
    else:
        score = 5.0  # neutral when no market data
    return round(float(score), 1), round(float(model_prob), 1), market_prob, round(float(edge_pct), 1)

# ============================================================
# COMPOSITE SCORE & TRADE SUGGESTION
# ============================================================
def compute_composite(scores, regime, vol_ratio):
    """Weighted composite score 0-100 with regime adjustment."""
    raw = 0.0
    for key, weight in SCORE_WEIGHTS.items():
        raw += scores.get(key, 5.0) * weight
    # Scale to 0-100
    base = round(raw * 10, 1)
    # Regime bonus/penalty
    if regime == "COMPRESSION":
        base = min(100, base + 5)
    elif regime == "EXPANSION":
        base = max(0, base - 5)
    return round(float(base), 1)

def trade_suggestion(composite, edge_pct):
    """Trade suggestion based on composite score.
    Returns (suggestion_text, color)."""
    if composite >= 80:
        return "🟢 AGGRESSIVE SIZE", "#3fb950"
    elif composite >= 65:
        return "🟡 MEDIUM SIZE", "#d29922"
    elif composite >= 50:
        if edge_pct > 0:
            return "🟠 SMALL SIZE", "#f09000"
        else:
            return "🔴 NO TRADE — Negative Edge", "#f85149"
    else:
        return "🔴 NO TRADE", "#f85149"
        # ============================================================
# HEADER
# ============================================================
st.markdown("<h1 style='text-align:center; color:#f0b90b; border-bottom:2px solid #f0b90b; padding-bottom:10px'>📐 FIBONACCI REACTION ENGINE</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#8b949e; font-family:monospace'>Location + Volatility + Momentum + Flow + Mispricing = Edge</p>", unsafe_allow_html=True)

# ============================================================
# MARKET SELECTOR
# ============================================================
st.markdown("---")
col_market, col_lookback = st.columns([3, 1])

with col_market:
    categories = {}
    for name, mcfg in MARKETS.items():
        cat = mcfg.get("category", "Other")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(name)
    market_options = []
    for cat in sorted(categories.keys()):
        for name in categories[cat]:
            icon = MARKETS[name].get("icon", "")
            market_options.append(icon + " " + name)
    selected_display = st.selectbox("Select Market", market_options, index=0)
    selected_name = selected_display.split(" ", 1)[1]
    cfg = MARKETS[selected_name]

with col_lookback:
    lookback = st.selectbox("Lookback", [3, 5, 10, 20], index=1, format_func=lambda x: str(x) + " days")

# ============================================================
# FETCH DATA
# ============================================================
with st.spinner("Loading " + selected_name + " data..."):
    df = fetch_full_data(cfg.get("ticker", ""), lookback)

if df is None or len(df) < 2:
    st.error("Failed to fetch " + selected_name + " data.")
    st.stop()

high, low, close = extract_hlc(df, lookback)
if high is None:
    st.error("No price data for " + selected_name)
    st.stop()

rng = round(high - low, 4)
brackets = make_brackets(cfg)

# Compute fib levels
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
        "dist_pct": dist_pct,
    })

golden = [l for l in levels if l["pct"] == 0.618][0]
pick = golden["bracket"]
cushion = round(close - pick, 4)
cushion_pct = round((cushion / close) * 100, 2) if close != 0 else 0
nd = next_trading_day()
kurl_direct, kurl_browse = kalshi_url(cfg, nd)

# ============================================================
# FETCH KALSHI LIVE PRICES
# ============================================================
kalshi_data = {}
if API_KEY and PRIVATE_KEY:
    series = cfg.get("kalshi_series", "")
    slug = cfg.get("kalshi_slug", "")
    kalshi_data = fetch_kalshi_event_markets(series, slug, nd)
    if not kalshi_data:
        kalshi_data = fetch_kalshi_series_markets(series)

# ============================================================
# COMPUTE ALL 5 SCORES
# ALL values cast to plain Python float/str to prevent numpy TypeErrors
# ============================================================
loc_score = float(score_location(close, golden["price"], rng))
vol_score, vol_regime, vol_ratio, bb_pct = score_volatility(df)
vol_score = float(vol_score)
vol_regime = str(vol_regime)
vol_ratio = float(vol_ratio)
bb_pct = float(bb_pct)
mom_score, rsi_val, macd_slope, roc_val = score_momentum(df)
mom_score = float(mom_score)
rsi_val = float(rsi_val)
macd_slope = float(macd_slope)
roc_val = float(roc_val)
flow_score_val, vol_ratio_flow, vwap_dist = score_flow(df)
flow_score_val = float(flow_score_val)
vol_ratio_flow = float(vol_ratio_flow)
vwap_dist = float(vwap_dist)
mis_score, model_prob, market_prob, edge_pct = score_mispricing(df, pick, kalshi_data)
mis_score = float(mis_score)
model_prob = float(model_prob)
# market_prob can be None — do NOT cast if None
if market_prob is not None:
    market_prob = float(market_prob)
edge_pct = float(edge_pct)

scores = {
    "location": loc_score,
    "volatility": vol_score,
    "momentum": mom_score,
    "flow": flow_score_val,
    "mispricing": mis_score,
}
composite = compute_composite(scores, vol_regime, vol_ratio)
suggestion, suggestion_color = trade_suggestion(composite, edge_pct)

# ============================================================
# MARKET DATA BAR
# ============================================================
fp = lambda v: fmt_price(v, cfg)
c1, c2, c3, c4 = st.columns(4)
with c1:
    html = '<div class="metric-card">'
    html += '<div class="metric-label">Last Close</div>'
    html += '<div class="metric-val" style="color:#e6edf3">' + fp(close) + '</div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)
with c2:
    html = '<div class="metric-card">'
    html += '<div class="metric-label">' + str(lookback) + 'D High</div>'
    html += '<div class="metric-val green">' + fp(high) + '</div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)
with c3:
    html = '<div class="metric-card">'
    html += '<div class="metric-label">' + str(lookback) + 'D Low</div>'
    html += '<div class="metric-val red">' + fp(low) + '</div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)
with c4:
    html = '<div class="metric-card">'
    html += '<div class="metric-label">Range</div>'
    html += '<div class="metric-val" style="color:#e6edf3">' + fp(rng) + '</div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

# ============================================================
# COMPOSITE HEAT METER
# ============================================================
st.markdown("---")
gauge_color = suggestion_color
html = '<div class="score-gauge">'
html += '<div style="color:#8b949e; font-size:12px; text-transform:uppercase; letter-spacing:2px">Fibonacci Reaction Score</div>'
html += '<div class="score-big" style="color:' + gauge_color + '">' + str(composite) + '</div>'
html += '<div style="color:' + gauge_color + '; font-size:20px; font-weight:bold">' + suggestion + '</div>'
if vol_regime == "COMPRESSION":
    badge_bg = "#1a3a1a"
    badge_border = "#3fb950"
    badge_color = "#3fb950"
elif vol_regime == "EXPANSION":
    badge_bg = "#3a1a1a"
    badge_border = "#f85149"
    badge_color = "#f85149"
else:
    badge_bg = "#2a2a1a"
    badge_border = "#d29922"
    badge_color = "#d29922"
html += '<div style="margin-top:12px">'
html += '<span class="regime-badge" style="background:' + badge_bg + '; border:1px solid ' + badge_border + '; color:' + badge_color + '">'
html += 'VOL: ' + vol_regime
html += '</span>'
html += '</div>'
html += '</div>'
st.markdown(html, unsafe_allow_html=True)
# ============================================================
# SCORE BREAKDOWN
# ============================================================
st.markdown("### 🎯 Score Breakdown")

sc1, sc2, sc3, sc4, sc5 = st.columns(5)

with sc1:
    lc = "#3fb950" if loc_score >= 7 else "#d29922" if loc_score >= 4 else "#f85149"
    html = '<div class="metric-card">'
    html += '<div class="metric-label">Location</div>'
    html += '<div class="metric-val" style="color:' + lc + '">' + str(loc_score) + '</div>'
    html += '<div style="color:#484f58; font-size:10px">Weight: 20%</div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

with sc2:
    vc = "#3fb950" if vol_score >= 7 else "#d29922" if vol_score >= 4 else "#f85149"
    html = '<div class="metric-card">'
    html += '<div class="metric-label">Volatility</div>'
    html += '<div class="metric-val" style="color:' + vc + '">' + str(vol_score) + '</div>'
    html += '<div style="color:#484f58; font-size:10px">Weight: 20%</div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

with sc3:
    mc = "#3fb950" if mom_score >= 7 else "#d29922" if mom_score >= 4 else "#f85149"
    html = '<div class="metric-card">'
    html += '<div class="metric-label">Momentum</div>'
    html += '<div class="metric-val" style="color:' + mc + '">' + str(mom_score) + '</div>'
    html += '<div style="color:#484f58; font-size:10px">Weight: 20%</div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

with sc4:
    fc = "#3fb950" if flow_score_val >= 7 else "#d29922" if flow_score_val >= 4 else "#f85149"
    html = '<div class="metric-card">'
    html += '<div class="metric-label">Flow</div>'
    html += '<div class="metric-val" style="color:' + fc + '">' + str(flow_score_val) + '</div>'
    html += '<div style="color:#484f58; font-size:10px">Weight: 15%</div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

with sc5:
    ec = "#3fb950" if mis_score >= 7 else "#d29922" if mis_score >= 4 else "#f85149"
    html = '<div class="metric-card">'
    html += '<div class="metric-label">Mispricing</div>'
    html += '<div class="metric-val" style="color:' + ec + '">' + str(mis_score) + '</div>'
    html += '<div style="color:#484f58; font-size:10px">Weight: 25%</div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

# ============================================================
# INDICATOR DETAILS (expandable)
# ============================================================
with st.expander("📊 Indicator Details"):
    d1, d2 = st.columns(2)
    with d1:
        st.markdown("**Volatility Regime**")
        st.markdown("ATR5/ATR20 Ratio: **" + str(vol_ratio) + "**")
        st.markdown("Bollinger Width %ile: **" + str(bb_pct) + "%**")
        st.markdown("Regime: **" + vol_regime + "**")
        st.markdown("---")
        st.markdown("**Momentum**")
        st.markdown("RSI(14): **" + str(rsi_val) + "**")
        st.markdown("MACD Hist Slope: **" + str(macd_slope) + "**")
        st.markdown("ROC(3): **" + str(roc_val) + "%**")
    with d2:
        st.markdown("**Order Flow Proxy**")
        st.markdown("Volume Ratio (vs 20d avg): **" + str(vol_ratio_flow) + "x**")
        st.markdown("VWAP Distance: **" + str(vwap_dist) + "%**")
        st.markdown("---")
        st.markdown("**Mispricing**")
        st.markdown("Model Probability: **" + str(model_prob) + "%**")
        mp_display = str(market_prob) + "%" if market_prob is not None else "N/A"
        st.markdown("Market Implied: **" + mp_display + "**")
        if market_prob is not None:
            edge_color = "green" if edge_pct > 0 else "red"
            edge_sign = "+" if edge_pct > 0 else ""
            st.markdown("Edge: **:" + edge_color + "[" + edge_sign + str(edge_pct) + "%]**")
            tradeable = "YES ✅" if edge_pct > 6 else "MARGINAL ⚠️" if edge_pct > 3 else "NO ❌"
            st.markdown("Tradeable Edge: **" + tradeable + "**")
        else:
            st.markdown("Edge: **N/A** (no market data)")
            st.markdown("Tradeable Edge: **N/A**")

# ============================================================
# THE PICK
# ============================================================
st.markdown("---")

html = '<div class="big-pick">'
html += '<div class="pick-title">★ ' + cfg.get("icon", "") + ' ' + selected_name + ' — Reaction Engine Pick ★</div>'
html += '<div class="pick-main">BUY YES — ' + fp(pick) + ' or above</div>'
html += '<div class="pick-sub">61.8% Fibo = ' + fp(golden["price"]) + ' → Nearest bracket: ' + fp(pick) + '</div>'
html += '<br>'
html += '<div style="display:flex; justify-content:center; gap:40px">'
html += '<div><div class="cushion-num">' + fp(cushion) + ' pts</div><div class="cushion-label">Cushion from close</div></div>'
html += '<div><div class="cushion-num">' + str(cushion_pct) + '%</div><div class="cushion-label">Drop needed to lose</div></div>'
html += '</div>'
html += '<br>'
# Model vs Market — handles None market_prob
mp_color = "#d29922"
if market_prob is not None:
    mp_color = "#3fb950" if edge_pct > 3 else "#f85149" if edge_pct < -3 else "#d29922"
mp_display = str(market_prob) + "%" if market_prob is not None else "N/A"
edge_display = ("+" if edge_pct > 0 else "") + str(edge_pct) + "%" if market_prob is not None else "N/A"
html += '<div style="display:flex; justify-content:center; gap:30px; margin-bottom:12px">'
html += '<div style="text-align:center"><div style="color:#58a6ff; font-size:24px; font-weight:bold">' + str(model_prob) + '%</div><div style="color:#8b949e; font-size:11px">Model Prob</div></div>'
html += '<div style="text-align:center; color:#484f58; font-size:20px; padding-top:4px">vs</div>'
html += '<div style="text-align:center"><div style="color:#f0b90b; font-size:24px; font-weight:bold">' + mp_display + '</div><div style="color:#8b949e; font-size:11px">Market Implied</div></div>'
html += '<div style="text-align:center"><div style="color:' + mp_color + '; font-size:24px; font-weight:bold">'
html += edge_display + '</div><div style="color:#8b949e; font-size:11px">Edge</div></div>'
html += '</div>'
# Trade suggestion
html += '<div style="color:' + suggestion_color + '; font-size:18px; font-weight:bold; margin-bottom:12px">' + suggestion + '</div>'
# Kelly — capped 15%, hidden below composite 65
if edge_pct > 0 and market_prob is not None and market_prob > 0 and market_prob < 100 and composite >= 65:
    mp_dec = market_prob / 100.0
    odds = (1.0 / mp_dec) - 1.0 if mp_dec > 0 else 0
    model_dec = model_prob / 100.0
    kelly = 0.0
    if odds > 0:
        kelly = ((model_dec * odds) - (1 - model_dec)) / odds
        kelly = max(0, min(0.15, kelly))
    kelly_pct = round(kelly * 100, 1)
    html += '<div style="color:#8b949e; font-size:12px">Kelly Fraction: ' + str(kelly_pct) + '% of bankroll</div>'
html += '<br>'
html += '<div style="color:#8b949e; font-size:13px">Market: ' + nd.strftime("%A %b %d, %Y") + ' at 4pm EST</div>'
html += '<br>'
html += '<a href="' + kurl_direct + '" target="_blank" style="display:inline-block; background:#f0b90b; color:#000; padding:12px 32px; border-radius:8px; font-weight:bold; font-size:16px; text-decoration:none; font-family:monospace">🎯 OPEN ON KALSHI →</a>'
html += '<div style="color:#484f58; font-size:10px; margin-top:6px">' + kurl_direct + '</div>'
html += '<div style="margin-top:8px"><a href="' + kurl_browse + '" target="_blank" style="color:#58a6ff; font-size:12px; text-decoration:none">📂 Browse all ' + selected_name + ' brackets →</a></div>'
html += '</div>'
st.markdown(html, unsafe_allow_html=True)
# ============================================================
# ALL MARKETS SCORED SCAN
# ============================================================
st.markdown("---")
st.markdown("### 🔍 All Markets — Reaction Scores")
st.markdown("<p style='color:#8b949e; font-size:12px'>Composite scores across all 12 markets</p>", unsafe_allow_html=True)

scan_results = []
for mname, mcfg in MARKETS.items():
    try:
        mdf = fetch_full_data(mcfg.get("ticker", ""), lookback)
        if mdf is None or len(mdf) < 2:
            continue
        mh, ml, mc = extract_hlc(mdf, lookback)
        if mh is None:
            continue
        mrng = mh - ml
        mb = make_brackets(mcfg)
        gprice = ml + mrng * 0.618
        gpick = nearest_bracket_below(gprice, mb)
        mcush = mc - gpick
        mcush_pct = round((mcush / mc) * 100, 2) if mc != 0 else 0
        m_loc = float(score_location(mc, gprice, mrng))
        m_vol, m_regime, m_vratio, _ = score_volatility(mdf)
        m_vol = float(m_vol)
        m_regime = str(m_regime)
        m_vratio = float(m_vratio)
        m_mom, _, _, _ = score_momentum(mdf)
        m_mom = float(m_mom)
        m_flow, _, _ = score_flow(mdf)
        m_flow = float(m_flow)
        m_mis = 5.0
        m_scores = {"location": m_loc, "volatility": m_vol, "momentum": m_mom, "flow": m_flow, "mispricing": m_mis}
        m_comp = compute_composite(m_scores, m_regime, m_vratio)
        m_sug, m_sug_color = trade_suggestion(m_comp, 0.0)
        scan_results.append({
            "name": mname,
            "icon": mcfg.get("icon", ""),
            "close": mc,
            "pick": gpick,
            "cushion_pct": mcush_pct,
            "composite": m_comp,
            "suggestion": m_sug,
            "color": m_sug_color,
            "regime": m_regime,
            "cfg": mcfg,
        })
    except Exception:
        continue

scan_results.sort(key=lambda x: x.get("composite", 0), reverse=True)

if scan_results:
    header = "| Market | Close | Pick | Cushion | Score | Signal | Regime |"
    sep = "|:-------|------:|-----:|--------:|------:|:------:|:------:|"
    rows = [header, sep]
    for sr in scan_results:
        mfp = lambda v, c=sr["cfg"]: fmt_price(v, c)
        cush_str = str(sr.get("cushion_pct", 0)) + "%"
        cush_icon = "🟢" if sr.get("cushion_pct", 0) >= 0 else "🔴"
        score_str = str(sr.get("composite", 0))
        row = "| " + sr.get("icon", "") + " " + sr.get("name", "")
        row += " | " + mfp(sr.get("close", 0))
        row += " | " + mfp(sr.get("pick", 0))
        row += " | " + cush_icon + " " + cush_str
        row += " | **" + score_str + "**"
        row += " | " + sr.get("suggestion", "")
        row += " | " + sr.get("regime", "")
        row += " |"
        rows.append(row)
    st.markdown("\n".join(rows))
else:
    st.warning("No market data available for scan.")

# ============================================================
# FIBO TABLE
# ============================================================
st.markdown("---")
st.markdown("### " + cfg.get("icon", "") + " " + selected_name + " — All Fibonacci Levels")

header = "| Level | Price | Bracket | Cushion | Trade |"
sep = "|:------|------:|--------:|--------:|:-----:|"
rows = [header, sep]
for l in levels:
    g = "**" if l.get("pct", 0) == 0.618 else ""
    dc = "🟢" if l.get("dist", 0) >= 0 else "🔴"
    link = "[Open →](" + kurl_browse + ")"
    row = "| " + g + l.get("label", "") + g
    row += " | " + fp(l.get("price", 0))
    row += " | " + g + fp(l.get("bracket", 0)) + g
    row += " | " + dc + " " + fp(l.get("dist", 0)) + " (" + str(l.get("dist_pct", 0)) + "%)"
    row += " | " + link + " |"
    rows.append(row)
st.markdown("\n".join(rows))

# ============================================================
# FORMULA
# ============================================================
st.markdown("### 📐 The Formula — " + selected_name)
st.markdown("1. Get " + str(lookback) + "-day swing high & low for **" + selected_name + "** (" + cfg.get("ticker", "") + ")")
st.markdown("2. Range = " + fp(high) + " − " + fp(low) + " =
