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
    "edge": 0.50,
    "volatility": 0.25,
    "momentum": 0.25,
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
        "bracket_step": 100,
        "bracket_min": 35000,
        "bracket_max": 55000,
        "icon": "🏛️",
        "category": "🟡 Equity Index",
    },
    "Russell 2000": {
        "ticker": "^RUT",
        "kalshi_series": "kxrutu",
        "kalshi_slug": "russell-2000-abovebelow",
        "bracket_step": 10,
        "bracket_min": 1500,
        "bracket_max": 3000,
        "icon": "📈",
        "category": "🟡 Equity Index",
    },
    "Gold": {
        "ticker": "GC=F",
        "kalshi_series": "kxgoldu",
        "kalshi_slug": "gold-abovebelow",
        "bracket_step": 25,
        "bracket_min": 1500,
        "bracket_max": 5000,
        "icon": "🥇",
        "category": "🟡 Commodity",
    },
    "Silver": {
        "ticker": "SI=F",
        "kalshi_series": "kxsilveru",
        "kalshi_slug": "silver-abovebelow",
        "bracket_step": 0.5,
        "bracket_min": 20,
        "bracket_max": 70,
        "icon": "🥈",
        "category": "🟡 Commodity",
    },
    "Oil (WTI)": {
        "ticker": "CL=F",
        "kalshi_series": "wti",
        "kalshi_slug": "wti-oil-daily-range",
        "bracket_step": 1,
        "bracket_min": 40,
        "bracket_max": 120,
        "icon": "🛢️",
        "category": "🟢 Commodity",
    },
    "Natural Gas": {
        "ticker": "NG=F",
        "kalshi_series": "",
        "kalshi_slug": "",
        "bracket_step": 0.25,
        "bracket_min": 1,
        "bracket_max": 10,
        "icon": "🔥",
        "category": "🔴 Commodity",
    },
    "Bitcoin": {
        "ticker": "BTC-USD",
        "kalshi_series": "kxbtcu",
        "kalshi_slug": "bitcoin-abovebelow",
        "bracket_step": 500,
        "bracket_min": 30000,
        "bracket_max": 200000,
        "icon": "₿",
        "category": "🟢 Crypto",
    },
    "Ethereum": {
        "ticker": "ETH-USD",
        "kalshi_series": "kxethu",
        "kalshi_slug": "ethereum-abovebelow",
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
        "bracket_step": 0.005,
        "bracket_min": 0.9,
        "bracket_max": 1.3,
        "icon": "💶",
        "category": "🟢 FX",
    },
    "USD/JPY": {
        "ticker": "JPY=X",
        "kalshi_series": "kxjpyu",
        "kalshi_slug": "usdjpy-abovebelow",
        "bracket_step": 0.5,
        "bracket_min": 120,
        "bracket_max": 170,
        "icon": "💴",
        "category": "🟢 FX",
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
    .runner-up {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
        margin: 8px 0;
    }
    .runner-title {color: #58a6ff; font-size: 12px; text-transform: uppercase; letter-spacing: 1px}
    .runner-main {color: #e6edf3; font-size: 22px; font-weight: bold; font-family: 'Courier New', monospace}
    .edge-pos {color: #3fb950; font-size: 20px; font-weight: bold; font-family: 'Courier New', monospace}
    .edge-neg {color: #f85149; font-size: 20px; font-weight: bold; font-family: 'Courier New', monospace}
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
    .no-data-box {
        background: #1a1a1a;
        border: 2px solid #484f58;
        border-radius: 12px;
        padding: 40px;
        text-align: center;
        margin: 16px 0;
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
    end = datetime.now()
    start = end - timedelta(days=days * 2 + 10)
    df = yf.download(ticker, start=start.strftime("%Y-%m-%d"), end=end.strftime("%Y-%m-%d"), progress=False)
    if df.empty:
        return None
    if hasattr(df.columns, 'levels'):
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
    return df.tail(days + 20)

def extract_hlc(df, days):
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

def fmt_price(val, cfg):
    step = cfg.get("bracket_step", 1)
    if step >= 1:
        return f"{val:,.0f}"
    elif step >= 0.01:
        return f"{val:,.2f}"
    else:
        return f"{val:,.4f}"

# ============================================================
# KALSHI LIVE DATA (API only — no web links)
# ============================================================
@st.cache_data(ttl=120)
def fetch_kalshi_event_markets(series, slug, date_obj):
    if not series:
        return {}
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
            floor_strike = m.get("floor_strike", None)
            cap_strike = m.get("cap_strike", None)
            result[ticker] = {
                "subtitle": subtitle,
                "yes_bid": yes_bid,
                "yes_ask": yes_ask,
                "no_bid": no_bid,
                "volume": volume,
                "floor": floor_strike,
                "cap": cap_strike,
                "implied_prob": yes_bid,
            }
        return result
    except Exception:
        return {}

@st.cache_data(ttl=120)
def fetch_kalshi_series_markets(series):
    if not series:
        return {}
    path = "/trade-api/v2/markets"
    params = "?series_ticker=" + series + "&status=open&limit=200"
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
# EDGE ENGINE: Model Probabilities for ALL brackets
# ============================================================
def compute_model_probs_all_brackets(df, kalshi_data):
    """
    For each Kalshi bracket, compute the model probability that
    the asset closes at or above the bracket's floor_strike.
    Uses historical daily returns to project next-day outcomes.
    Returns dict: {ticker: {floor, model_prob, market_prob, edge, subtitle, yes_bid, yes_ask}}
    """
    if not kalshi_data:
        return {}
    closes = df["Close"].values
    current = float(closes[-1])
    n_returns = min(60, len(closes) - 1)
    if n_returns < 5:
        return {}
    returns = []
    for i in range(len(closes) - n_returns, len(closes)):
        if i > 0:
            prev = float(closes[i - 1])
            curr = float(closes[i])
            if prev != 0:
                returns.append((curr - prev) / prev)
    if len(returns) < 5:
        return {}
    result = {}
    for ticker, mdata in kalshi_data.items():
        floor = mdata.get("floor", None)
        if floor is None:
            continue
        try:
            floor_val = float(floor)
        except (ValueError, TypeError):
            continue
        yes_bid = mdata.get("yes_bid", 0)
        yes_ask = mdata.get("yes_ask", 0)
        if not yes_bid or yes_bid <= 0:
            continue
        above_count = 0
        for r in returns:
            projected = current * (1 + r)
            if projected >= floor_val:
                above_count += 1
        model_prob = round((above_count / len(returns)) * 100, 1)
        market_prob = round(float(yes_bid), 1)
        edge = round(model_prob - market_prob, 1)
        result[ticker] = {
            "floor": floor_val,
            "model_prob": model_prob,
            "market_prob": market_prob,
            "edge": edge,
            "subtitle": mdata.get("subtitle", ""),
            "yes_bid": yes_bid,
            "yes_ask": yes_ask,
            "volume": mdata.get("volume", 0),
        }
    return result

def find_top_edges(bracket_probs, close, top_n=3):
    """
    From all brackets with model probs, find the top N with biggest positive edge.
    Also calculates cushion (how far price must fall to lose).
    Returns list of dicts sorted by edge descending, max top_n items.
    Only includes brackets with positive edge.
    """
    candidates = []
    for ticker, bp in bracket_probs.items():
        if bp.get("edge", 0) <= 0:
            continue
        floor_val = bp.get("floor", 0)
        cushion = round(close - floor_val, 4)
        cushion_pct = round((cushion / close) * 100, 2) if close != 0 else 0
        candidates.append({
            "ticker": ticker,
            "floor": floor_val,
            "model_prob": bp.get("model_prob", 0),
            "market_prob": bp.get("market_prob", 0),
            "edge": bp.get("edge", 0),
            "cushion": cushion,
            "cushion_pct": cushion_pct,
            "subtitle": bp.get("subtitle", ""),
            "yes_bid": bp.get("yes_bid", 0),
            "yes_ask": bp.get("yes_ask", 0),
            "volume": bp.get("volume", 0),
        })
    candidates.sort(key=lambda x: x.get("edge", 0), reverse=True)
    return candidates[:top_n]

def score_edge(top_edges):
    """
    Score 0-10 based on the best edge found.
    No edges found = 0. Edge > 20 = 10.
    """
    if not top_edges:
        return 0.0, 0.0
    best_edge = top_edges[0].get("edge", 0)
    if best_edge >= 25:
        score = 10
    elif best_edge >= 20:
        score = 9
    elif best_edge >= 15:
        score = 8
    elif best_edge >= 10:
        score = 7
    elif best_edge >= 7:
        score = 6
    elif best_edge >= 5:
        score = 5
    elif best_edge >= 3:
        score = 4
    elif best_edge >= 1:
        score = 3
    else:
        score = 2
    return round(float(score), 1), round(float(best_edge), 1)
    # ============================================================
# VOLATILITY REGIME (0-10)
# ============================================================
def compute_atr(df, period):
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
# MOMENTUM (0-10)
# ============================================================
def compute_rsi(df, period=14):
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
    closes = df["Close"].values
    if len(closes) < period + 1:
        return 0.0
    current = float(closes[-1])
    past = float(closes[-period - 1])
    if past == 0:
        return 0.0
    return round(((current - past) / past) * 100, 2)

def score_momentum(df):
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
# COMPOSITE SCORE & TRADE SUGGESTION
# ============================================================
def compute_composite(scores, regime):
    raw = 0.0
    for key, weight in SCORE_WEIGHTS.items():
        raw += scores.get(key, 0.0) * weight
    base = round(raw * 10, 1)
    if regime == "COMPRESSION":
        base = min(100, base + 5)
    elif regime == "EXPANSION":
        base = max(0, base - 5)
    return round(float(base), 1)

def trade_suggestion(composite, best_edge):
    if composite >= 75 and best_edge >= 10:
        return "🟢 AGGRESSIVE SIZE", "#3fb950"
    elif composite >= 60 and best_edge >= 5:
        return "🟡 MEDIUM SIZE", "#d29922"
    elif composite >= 45 and best_edge >= 3:
        return "🟠 SMALL SIZE", "#f09000"
    else:
        return "🔴 NO TRADE", "#f85149"
        # ============================================================
# HEADER
# ============================================================
st.markdown("<h1 style='text-align:center; color:#f0b90b; border-bottom:2px solid #f0b90b; padding-bottom:10px'>📐 FIBONACCI REACTION ENGINE v3</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#8b949e; font-family:monospace'>Edge Scanner — Find the most mispriced brackets across 12 markets</p>", unsafe_allow_html=True)

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
nd = next_trading_day()

# ============================================================
# FIBO LEVELS (reference only)
# ============================================================
fibo_levels = []
for pct, label in FIBO_LEVELS:
    price = low + rng * pct
    bracket = nearest_bracket_below(price, brackets)
    dist = close - bracket
    dist_pct = round((dist / close) * 100, 2) if close != 0 else 0
    fibo_levels.append({
        "pct": pct,
        "label": label,
        "price": round(price, 4),
        "bracket": bracket,
        "dist": round(dist, 2),
        "dist_pct": dist_pct,
    })

# ============================================================
# FETCH KALSHI LIVE PRICES (API only, no links)
# ============================================================
kalshi_data = {}
has_kalshi = False
if API_KEY and PRIVATE_KEY:
    series = cfg.get("kalshi_series", "")
    slug = cfg.get("kalshi_slug", "")
    if series:
        kalshi_data = fetch_kalshi_event_markets(series, slug, nd)
        if not kalshi_data:
            kalshi_data = fetch_kalshi_series_markets(series)
        if kalshi_data:
            has_kalshi = True
        # DEBUG — remove after testing
if not has_kalshi:
    series = cfg.get("kalshi_series", "")
    slug = cfg.get("kalshi_slug", "")
    td = ticker_date(nd)
    event_ticker = series + "-" + td + "h1600"
    st.warning(f"DEBUG: Tried event ticker: {event_ticker} | Series: {series} | Has API keys: {bool(API_KEY and PRIVATE_KEY)}")
# ============================================================
# COMPUTE EDGE (the core new logic)
# ============================================================
bracket_probs = {}
top_edges = []
edge_score_val = 0.0
best_edge = 0.0

if has_kalshi:
    bracket_probs = compute_model_probs_all_brackets(df, kalshi_data)
    top_edges = find_top_edges(bracket_probs, close, top_n=3)
    edge_score_val, best_edge = score_edge(top_edges)

# ============================================================
# COMPUTE VOLATILITY & MOMENTUM
# ============================================================
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

# ============================================================
# COMPOSITE
# ============================================================
scores = {
    "edge": edge_score_val,
    "volatility": vol_score,
    "momentum": mom_score,
}
composite = compute_composite(scores, vol_regime)
suggestion, suggestion_color = trade_suggestion(composite, best_edge)

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

if not has_kalshi:
    html = '<div class="no-data-box">'
    html += '<div style="font-size:48px; margin-bottom:12px">📡</div>'
    html += '<div style="color:#8b949e; font-size:18px; font-weight:bold">No Live Kalshi Data</div>'
    html += '<div style="color:#484f58; font-size:13px; margin-top:8px">Cannot scan brackets without live pricing. '
    html += 'This market may not have active daily brackets on Kalshi.</div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)
elif not top_edges:
    html = '<div class="no-data-box">'
    html += '<div style="font-size:48px; margin-bottom:12px">🔍</div>'
    html += '<div style="color:#8b949e; font-size:18px; font-weight:bold">No Positive Edge Found</div>'
    html += '<div style="color:#484f58; font-size:13px; margin-top:8px">All brackets are fairly priced or overpriced. No trade today.</div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)
else:
    gauge_color = suggestion_color
    html = '<div class="score-gauge">'
    html += '<div style="color:#8b949e; font-size:12px; text-transform:uppercase; letter-spacing:2px">Edge Reaction Score</div>'
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
# TOP 3 EDGE PICKS
# ============================================================
if has_kalshi and top_edges:
    st.markdown("### 🎯 Top Edge Brackets — " + cfg.get("icon", "") + " " + selected_name)
    st.markdown("<p style='color:#8b949e; font-size:12px'>Ranked by model edge (Model Prob - Market Implied)</p>", unsafe_allow_html=True)

    # === PICK #1 (the main pick) ===
    pick1 = top_edges[0]
    p1_floor = pick1.get("floor", 0)
    p1_model = pick1.get("model_prob", 0)
    p1_market = pick1.get("market_prob", 0)
    p1_edge = pick1.get("edge", 0)
    p1_cushion = pick1.get("cushion", 0)
    p1_cushion_pct = pick1.get("cushion_pct", 0)

    mp_color = "#3fb950" if p1_edge > 5 else "#d29922" if p1_edge > 0 else "#f85149"

    html = '<div class="big-pick">'
    html += '<div class="pick-title">★ #1 BEST EDGE ★</div>'
    html += '<div class="pick-main">BUY YES — ' + fp(p1_floor) + ' or above</div>'
    html += '<div class="pick-sub">' + str(pick1.get("subtitle", "")) + '</div>'
    html += '<br>'
    html += '<div style="display:flex; justify-content:center; gap:40px">'
    html += '<div><div class="cushion-num">' + fp(p1_cushion) + ' pts</div><div class="cushion-label">Cushion from close</div></div>'
    html += '<div><div class="cushion-num">' + str(p1_cushion_pct) + '%</div><div class="cushion-label">Drop needed to lose</div></div>'
    html += '</div>'
    html += '<br>'
    html += '<div style="display:flex; justify-content:center; gap:30px; margin-bottom:12px">'
    html += '<div style="text-align:center"><div style="color:#58a6ff; font-size:24px; font-weight:bold">' + str(p1_model) + '%</div><div style="color:#8b949e; font-size:11px">Model Prob</div></div>'
    html += '<div style="text-align:center; color:#484f58; font-size:20px; padding-top:4px">vs</div>'
    html += '<div style="text-align:center"><div style="color:#f0b90b; font-size:24px; font-weight:bold">' + str(p1_market) + '%</div><div style="color:#8b949e; font-size:11px">Market Implied</div></div>'
    html += '<div style="text-align:center"><div class="edge-pos">+' + str(p1_edge) + '%</div><div style="color:#8b949e; font-size:11px">Edge</div></div>'
    html += '</div>'
    html += '<div style="color:' + suggestion_color + '; font-size:18px; font-weight:bold; margin-bottom:12px">' + suggestion + '</div>'
    # Kelly fraction
    if p1_edge > 0 and p1_market > 0 and p1_market < 100 and composite >= 45:
        mp_dec = p1_market / 100.0
        odds = (1.0 / mp_dec) - 1.0 if mp_dec > 0 else 0
        model_dec = p1_model / 100.0
        kelly = 0.0
        if odds > 0:
            kelly = ((model_dec * odds) - (1 - model_dec)) / odds
            kelly = max(0, min(0.15, kelly))
        kelly_pct = round(kelly * 100, 1)
        html += '<div style="color:#8b949e; font-size:12px">Kelly Fraction: ' + str(kelly_pct) + '% of bankroll</div>'
    html += '<br>'
    html += '<div style="color:#8b949e; font-size:13px">Market: ' + nd.strftime("%A %b %d, %Y") + ' at 4pm EST</div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

    # === PICKS #2 and #3 (runners up) ===
    if len(top_edges) > 1:
        runner_cols = st.columns(min(len(top_edges) - 1, 2))
        for idx in range(1, min(len(top_edges), 3)):
            pick_n = top_edges[idx]
            pn_floor = pick_n.get("floor", 0)
            pn_model = pick_n.get("model_prob", 0)
            pn_market = pick_n.get("market_prob", 0)
            pn_edge = pick_n.get("edge", 0)
            pn_cushion = pick_n.get("cushion", 0)
            pn_cushion_pct = pick_n.get("cushion_pct", 0)
            with runner_cols[idx - 1]:
                html = '<div class="runner-up">'
                html += '<div class="runner-title">#' + str(idx + 1) + ' EDGE</div>'
                html += '<div class="runner-main">' + fp(pn_floor) + ' or above</div>'
                html += '<div style="color:#8b949e; font-size:11px; margin:4px 0">' + str(pick_n.get("subtitle", "")) + '</div>'
                html += '<div class="edge-pos">+' + str(pn_edge) + '% edge</div>'
                html += '<div style="color:#8b949e; font-size:11px; margin-top:4px">'
                html += 'Model: ' + str(pn_model) + '% vs Market: ' + str(pn_market) + '%'
                html += '</div>'
                html += '<div style="color:#8b949e; font-size:11px">'
                html += 'Cushion: ' + fp(pn_cushion) + ' pts (' + str(pn_cushion_pct) + '%)'
                html += '</div>'
                html += '</div>'
                st.markdown(html, unsafe_allow_html=True)

    # ============================================================
    # ALL BRACKETS TABLE (expandable)
    # ============================================================
    with st.expander("📋 All Scanned Brackets (" + str(len(bracket_probs)) + " total)"):
        sorted_brackets = sorted(bracket_probs.values(), key=lambda x: x.get("edge", 0), reverse=True)
        header = "| Bracket | Model % | Market % | Edge | Volume |"
        sep = "|--------:|--------:|---------:|-----:|-------:|"
        rows = [header, sep]
        for bp in sorted_brackets:
            edge_val = bp.get("edge", 0)
            edge_icon = "🟢" if edge_val > 3 else "🟡" if edge_val > 0 else "🔴"
            edge_str = ("+" if edge_val > 0 else "") + str(edge_val) + "%"
            row = "| " + fp(bp.get("floor", 0))
            row += " | " + str(bp.get("model_prob", 0)) + "%"
            row += " | " + str(bp.get("market_prob", 0)) + "%"
            row += " | " + edge_icon + " " + edge_str
            row += " | " + str(bp.get("volume", 0))
            row += " |"
            rows.append(row)
        st.markdown("\n".join(rows))

# ============================================================
# SCORE BREAKDOWN
# ============================================================
if has_kalshi and top_edges:
    st.markdown("---")
    st.markdown("### 📊 Score Breakdown")

    sc1, sc2, sc3 = st.columns(3)

    with sc1:
        ec = "#3fb950" if edge_score_val >= 7 else "#d29922" if edge_score_val >= 4 else "#f85149"
        html = '<div class="metric-card">'
        html += '<div class="metric-label">Edge</div>'
        html += '<div class="metric-val" style="color:' + ec + '">' + str(edge_score_val) + '</div>'
        html += '<div style="color:#484f58; font-size:10px">Weight: 50% | Best: +' + str(best_edge) + '%</div>'
        html += '</div>'
        st.markdown(html, unsafe_allow_html=True)

    with sc2:
        vc = "#3fb950" if vol_score >= 7 else "#d29922" if vol_score >= 4 else "#f85149"
        html = '<div class="metric-card">'
        html += '<div class="metric-label">Volatility</div>'
        html += '<div class="metric-val" style="color:' + vc + '">' + str(vol_score) + '</div>'
        html += '<div style="color:#484f58; font-size:10px">Weight: 25% | ' + vol_regime + '</div>'
        html += '</div>'
        st.markdown(html, unsafe_allow_html=True)

    with sc3:
        mc = "#3fb950" if mom_score >= 7 else "#d29922" if mom_score >= 4 else "#f85149"
        html = '<div class="metric-card">'
        html += '<div class="metric-label">Momentum</div>'
        html += '<div class="metric-val" style="color:' + mc + '">' + str(mom_score) + '</div>'
        html += '<div style="color:#484f58; font-size:10px">Weight: 25%</div>'
        html += '</div>'
        st.markdown(html, unsafe_allow_html=True)

    # ============================================================
    # INDICATOR DETAILS (expandable)
    # ============================================================
    with st.expander("🔬 Indicator Details"):
        d1, d2 = st.columns(2)
        with d1:
            st.markdown("**Volatility Regime**")
            st.markdown("ATR5/ATR20 Ratio: **" + str(vol_ratio) + "**")
            st.markdown("Bollinger Width %ile: **" + str(bb_pct) + "%**")
            st.markdown("Regime: **" + vol_regime + "**")
        with d2:
            st.markdown("**Momentum**")
            st.markdown("RSI(14): **" + str(rsi_val) + "**")
            st.markdown("MACD Hist Slope: **" + str(macd_slope) + "**")
            st.markdown("ROC(3): **" + str(roc_val) + "%**")

# ============================================================
# FIBO REFERENCE TABLE (always shown)
# ============================================================
st.markdown("---")
st.markdown("### 📐 " + cfg.get("icon", "") + " " + selected_name + " — Fibonacci Reference Levels")
st.markdown("<p style='color:#8b949e; font-size:12px'>For context only — the trade pick is driven by edge, not fibo</p>", unsafe_allow_html=True)

header = "| Level | Price | Nearest Bracket | Cushion |"
sep = "|:------|------:|----------------:|--------:|"
rows = [header, sep]
for l in fibo_levels:
    g = "**" if l.get("pct", 0) == 0.618 else ""
    dc = "🟢" if l.get("dist", 0) >= 0 else "🔴"
    row = "| " + g + l.get("label", "") + g
    row += " | " + fp(l.get("price", 0))
    row += " | " + g + fp(l.get("bracket", 0)) + g
    row += " | " + dc + " " + fp(l.get("dist", 0)) + " (" + str(l.get("dist_pct", 0)) + "%)"
    row += " |"
    rows.append(row)
st.markdown("\n".join(rows))
# ============================================================
# ALL MARKETS EDGE SCAN
# ============================================================
st.markdown("---")
st.markdown("### 🔍 All Markets — Edge Scan")
st.markdown("<p style='color:#8b949e; font-size:12px'>Scans all 12 markets for best edge brackets. Markets without live Kalshi data are skipped.</p>", unsafe_allow_html=True)

scan_results = []
for mname, mcfg in MARKETS.items():
    try:
        mseries = mcfg.get("kalshi_series", "")
        if not mseries:
            continue
        mdf = fetch_full_data(mcfg.get("ticker", ""), lookback)
        if mdf is None or len(mdf) < 2:
            continue
        mh, ml, mc = extract_hlc(mdf, lookback)
        if mh is None:
            continue
        # Fetch Kalshi data for this market
        mslug = mcfg.get("kalshi_slug", "")
        mk_data = fetch_kalshi_event_markets(mseries, mslug, nd)
        if not mk_data:
            mk_data = fetch_kalshi_series_markets(mseries)
        if not mk_data:
            continue
        # Compute edge
        m_bracket_probs = compute_model_probs_all_brackets(mdf, mk_data)
        m_top = find_top_edges(m_bracket_probs, mc, top_n=1)
        if not m_top:
            continue
        m_edge_score, m_best_edge = score_edge(m_top)
        m_vol, m_regime, m_vratio, _ = score_volatility(mdf)
        m_vol = float(m_vol)
        m_regime = str(m_regime)
        m_mom, _, _, _ = score_momentum(mdf)
        m_mom = float(m_mom)
        m_scores = {"edge": float(m_edge_score), "volatility": m_vol, "momentum": m_mom}
        m_comp = compute_composite(m_scores, m_regime)
        m_sug, m_sug_color = trade_suggestion(m_comp, float(m_best_edge))
        m_pick = m_top[0]
        scan_results.append({
            "name": mname,
            "icon": mcfg.get("icon", ""),
            "close": mc,
            "pick_floor": m_pick.get("floor", 0),
            "best_edge": m_best_edge,
            "model_prob": m_pick.get("model_prob", 0),
            "market_prob": m_pick.get("market_prob", 0),
            "cushion_pct": m_pick.get("cushion_pct", 0),
            "composite": m_comp,
            "suggestion": m_sug,
            "color": m_sug_color,
            "regime": m_regime,
            "cfg": mcfg,
        })
    except Exception:
        continue

scan_results.sort(key=lambda x: x.get("best_edge", 0), reverse=True)

if scan_results:
    header = "| Market | Close | Best Bracket | Edge | Model | Market | Cushion | Score | Signal |"
    sep = "|:-------|------:|-------------:|-----:|------:|-------:|--------:|------:|:------:|"
    rows = [header, sep]
    for sr in scan_results:
        mfp = lambda v, c=sr["cfg"]: fmt_price(v, c)
        edge_val = sr.get("best_edge", 0)
        edge_icon = "🟢" if edge_val > 5 else "🟡" if edge_val > 0 else "🔴"
        cush_val = sr.get("cushion_pct", 0)
        cush_icon = "🟢" if cush_val >= 0 else "🔴"
        row = "| " + sr.get("icon", "") + " " + sr.get("name", "")
        row += " | " + mfp(sr.get("close", 0))
        row += " | " + mfp(sr.get("pick_floor", 0))
        row += " | " + edge_icon + " +" + str(edge_val) + "%"
        row += " | " + str(sr.get("model_prob", 0)) + "%"
        row += " | " + str(sr.get("market_prob", 0)) + "%"
        row += " | " + cush_icon + " " + str(cush_val) + "%"
        row += " | **" + str(sr.get("composite", 0)) + "**"
        row += " | " + sr.get("suggestion", "")
        row += " |"
        rows.append(row)
    st.markdown("\n".join(rows))
else:
    st.warning("No markets with positive edge found. Try a different lookback period.")

# ============================================================
# FORMULA
# ============================================================
st.markdown("---")
st.markdown("### 📐 How the Edge Engine Works")
st.markdown("1. Fetch **all open Kalshi brackets** for " + selected_name + " (" + nd.strftime("%b %d") + " settlement)")
st.markdown("2. For each bracket, calculate **model probability** using " + str(min(60, len(df) - 1)) + " historical daily returns")
st.markdown("3. Compare model prob vs **market implied** (Kalshi yes_bid) for each bracket")
st.markdown("4. **Edge = Model Prob − Market Implied** for each bracket")
st.markdown("5. Rank all brackets by edge → pick the **top 3 with biggest positive edge**")
st.markdown("6. Score composite: **Edge (50%) + Volatility (25%) + Momentum (25%)** → " + str(composite) + "/100")
st.markdown("7. **" + suggestion + "**")

# ============================================================
# MARKET FIT GUIDE
# ============================================================
st.markdown("---")
st.markdown("### 📋 Market Fit Guide")
st.markdown("""
| Rating | Markets | Notes |
|:-------|:--------|:------|
| 🟢 **Best** | S&P 500, Nasdaq, Oil, Bitcoin, EUR/USD, USD/JPY | Confirmed daily Kalshi brackets, full edge scanning |
| 🟡 **Good** | Dow, Russell, Gold, Silver, Ethereum | Daily brackets may exist, edge scanning attempted |
| 🔴 **Skip** | Natural Gas | No daily above/below market on Kalshi, no edge scan possible |
""")

# ============================================================
# HOW TO USE THIS APP (collapsed)
# ============================================================
st.markdown("---")
with st.expander("🛠️ How to Use This App"):
    howto = '<div style="background:#161b22; border:1px solid #30363d; border-radius:8px; padding:20px; margin:12px 0">'
    howto += '<p style="color:#e6edf3; font-size:13px; line-height:1.8; margin:0">'
    howto += '<strong style="color:#f0b90b">1. Pick a market</strong> — Select any of the 12 markets from the dropdown. '
    howto += 'S&P 500, Nasdaq, Oil, Bitcoin, EUR/USD, and USD/JPY have confirmed daily Kalshi brackets.<br><br>'
    howto += '<strong style="color:#f0b90b">2. Set your lookback</strong> — 5 days is the default sweet spot. '
    howto += 'Use 3 days for fast-moving crypto/FX, 10-20 days for broader swing levels.<br><br>'
    howto += '<strong style="color:#f0b90b">3. Read the Edge Score</strong> — The big number (0-100) is your composite score '
    howto += 'across 3 layers: Edge (50%), Volatility (25%), and Momentum (25%). Higher = stronger setup.<br><br>'
    howto += '<strong style="color:#f0b90b">4. Check the top 3 brackets</strong> — The engine scans ALL live Kalshi brackets, '
    howto += 'calculates model probability for each using historical returns, and finds where the market is underpricing. '
    howto += 'The #1 pick has the fattest edge.<br><br>'
    howto += '<strong style="color:#f0b90b">5. Understand the edge</strong> — Edge = Model Prob minus Market Implied. '
    howto += 'If the model says 85% chance but Kalshi prices it at 70%, that is a +15% edge. Bigger = better.<br><br>'
    howto += '<strong style="color:#f0b90b">6. Check the cushion</strong> — How far price must drop before you lose. '
    howto += 'Bigger cushion = safer bet. Negative cushion = price already below the bracket (risky).<br><br>'
    howto += '<strong style="color:#f0b90b">7. Kelly Fraction</strong> — Optimal bet size based on your edge. '
    howto += 'This is the mathematically optimal percentage of your bankroll to risk. Capped at 15%.<br><br>'
    howto += '<strong style="color:#f0b90b">8. Scan all markets</strong> — Scroll down to the All Markets Edge Scan to find the '
    howto += 'highest-edge setups across all markets at once. Sorted by edge, best on top.<br><br>'
    howto += '<strong style="color:#f0b90b">9. Fibo reference</strong> — The Fibonacci levels table is shown for context. '
    howto += 'The 61.8% golden ratio is a classic support/resistance level, but the actual trade pick is driven purely by edge.<br><br>'
    howto += '<strong style="color:#f0b90b">10. Execute</strong> — Search for the market name on Kalshi and find the matching bracket. '
    howto += 'Buy YES on the pick bracket for the next trading day at 4pm EST settlement.'
    howto += '</p></div>'
    st.markdown(howto, unsafe_allow_html=True)

# ============================================================
# DISCLAIMER + FOOTER
# ============================================================
st.markdown("---")
disc = '<div style="background:#161b22; border:1px solid #30363d; border-radius:8px; padding:16px; margin-top:16px">'
disc += '<p style="color:#f0b90b; font-size:13px; font-weight:bold; margin-bottom:8px">⚠️ DISCLAIMER</p>'
disc += '<p style="color:#8b949e; font-size:11px; line-height:1.7">'
disc += 'This tool is for <strong>research and educational purposes only</strong>. It is NOT financial advice. '
disc += 'Model probabilities are based on historical return distributions and do NOT predict future price movements. '
disc += 'Past performance does not guarantee future results. All trading involves risk and you can lose your entire investment. '
disc += 'The composite score and edge calculations are mathematical models, not recommendations to buy or sell. '
disc += 'Always do your own research and never trade more than you can afford to lose. '
disc += 'This tool has no affiliation with Kalshi, Yahoo Finance, or any exchange.'
disc += '</p></div>'
st.markdown(disc, unsafe_allow_html=True)

now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
foot = '<p style="color:#484f58; font-size:11px; text-align:center; margin-top:12px">'
foot += 'Last updated: ' + now_str + ' | Data: Yahoo Finance + Kalshi API | Auto-refreshes every 5 min'
foot += '</p>'
st.markdown(foot, unsafe_allow_html=True)
