import streamlit as st
import requests
from datetime import datetime, timedelta

st.set_page_config(page_title="NYC Temp Edge Finder", page_icon="🌡️", layout="wide")

st.title("🌡️ NYC Temperature Edge Finder")
st.caption("Kalshi Weather Markets | BigSnapshot.com")

# --- CONFIG ---
# Ticker patterns from Kalshi URLs:
# HIGH: https://kalshi.com/markets/kxhighny/kxhighny-26jan20
# LOW:  https://kalshi.com/markets/kxlowtnyc/kxlowtnyc-26jan20
# Date format: YYmmmDD lowercase (26jan20 for Jan 20, 2026)

HIGH_SERIES = "kxhighny"
LOW_SERIES = "kxlowtnyc"  # Note the T!

def get_date_suffix(target_date):
    """Convert date to Kalshi format: 26jan20 (YYmmmDD lowercase)"""
    return target_date.strftime("%y%b%d").lower()

def fetch_markets(series_ticker, date_suffix):
    """Fetch markets from Kalshi API"""
    url = "https://api.elections.kalshi.com/trade-api/v2/markets"
    params = {"ticker": f"{series_ticker}-{date_suffix}"}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get("markets", []), None
        else:
            return [], f"API returned {response.status_code}"
    except Exception as e:
        return [], str(e)

def fetch_series_markets(series_ticker):
    """Fetch all markets in a series"""
    url = "https://api.elections.kalshi.com/trade-api/v2/markets"
    params = {"series_ticker": series_ticker, "limit": 100}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get("markets", []), None
        else:
            return [], f"API returned {response.status_code}"
    except Exception as e:
        return [], str(e)

# --- DATE SELECTION ---
st.subheader("Select Date")
col1, col2 = st.columns(2)

with col1:
    target_date = st.date_input(
        "Target Date",
        value=datetime.now().date(),
        min_value=datetime.now().date(),
        max_value=datetime.now().date() + timedelta(days=14)
    )

date_suffix = get_date_suffix(target_date)

with col2:
    st.info(f"**Date suffix:** {date_suffix}")
    st.caption(f"HIGH ticker: {HIGH_SERIES}-{date_suffix}")
    st.caption(f"LOW ticker: {LOW_SERIES}-{date_suffix}")

# --- DEBUG MODE ---
with st.expander("🔧 Debug Info", expanded=True):
    st.write("**Expected Tickers:**")
    st.code(f"{HIGH_SERIES}-{date_suffix}")
    st.code(f"{LOW_SERIES}-{date_suffix}")
    
    if st.button("🔍 Test API - Fetch Series Markets"):
        st.write("---")
        st.write("**HIGH Series Markets:**")
        high_markets, high_err = fetch_series_markets(HIGH_SERIES)
        if high_err:
            st.error(high_err)
        elif high_markets:
            for m in high_markets[:5]:
                st.write(f"- `{m.get('ticker')}` | {m.get('title', 'No title')}")
            if len(high_markets) > 5:
                st.caption(f"...and {len(high_markets)-5} more")
        else:
            st.warning("No HIGH markets returned")
        
        st.write("---")
        st.write("**LOW Series Markets:**")
        low_markets, low_err = fetch_series_markets(LOW_SERIES)
        if low_err:
            st.error(low_err)
        elif low_markets:
            for m in low_markets[:5]:
                st.write(f"- `{m.get('ticker')}` | {m.get('title', 'No title')}")
            if len(low_markets) > 5:
                st.caption(f"...and {len(low_markets)-5} more")
        else:
            st.warning("No LOW markets returned")

# --- FETCH MARKETS ---
st.subheader("Markets")

if st.button("🔄 Load Markets", type="primary"):
    with st.spinner("Fetching from Kalshi..."):
        # Fetch HIGH markets
        high_markets, high_err = fetch_markets(HIGH_SERIES, date_suffix)
        low_markets, low_err = fetch_markets(LOW_SERIES, date_suffix)
    
    col_high, col_low = st.columns(2)
    
    with col_high:
        st.write("### 🔥 HIGH Temp Markets")
        if high_err:
            st.error(f"Error: {high_err}")
        elif high_markets:
            for market in high_markets:
                ticker = market.get("ticker", "")
                title = market.get("title", "No title")
                yes_bid = market.get("yes_bid", 0)
                yes_ask = market.get("yes_ask", 0)
                
                if yes_bid and yes_ask:
                    mid = (yes_bid + yes_ask) / 2
                    st.metric(title[:50], f"{mid:.0f}¢")
                else:
                    st.write(f"**{title[:50]}**")
                st.caption(f"`{ticker}`")
        else:
            st.warning(f"No HIGH markets found for {HIGH_SERIES}-{date_suffix}")
    
    with col_low:
        st.write("### ❄️ LOW Temp Markets")
        if low_err:
            st.error(f"Error: {low_err}")
        elif low_markets:
            for market in low_markets:
                ticker = market.get("ticker", "")
                title = market.get("title", "No title")
                yes_bid = market.get("yes_bid", 0)
                yes_ask = market.get("yes_ask", 0)
                
                if yes_bid and yes_ask:
                    mid = (yes_bid + yes_ask) / 2
                    st.metric(title[:50], f"{mid:.0f}¢")
                else:
                    st.write(f"**{title[:50]}**")
                st.caption(f"`{ticker}`")
        else:
            st.warning(f"No LOW markets found for {LOW_SERIES}-{date_suffix}")

# --- FOOTER ---
st.divider()
st.caption("BigSnapshot.com | Weather Edge Finder v1.0")
