import streamlit as st
import requests
from datetime import datetime, timedelta
import pytz

# ============================================================
# TEMP TIME EDGE - PRIVATE TEST APP
# Tomorrow's NWS vs Today's NWS Comparison
# ============================================================

st.set_page_config(page_title="Time Edge Test", page_icon="⏳", layout="wide")

# ============================================================
# AUTH CHECK - OWNER ONLY
# ============================================================
if 'authenticated' not in st.session_state or not st.session_state.authenticated:
    st.warning("⚠️ Please log in from the Home page first.")
    st.page_link("Home.py", label="🏠 Go to Home", use_container_width=True)
    st.stop()

# Owner-only access
if st.session_state.get('user_type') != "Owner":
    st.error("🔒 This is a private test feature. Owner access only.")
    st.stop()

VERSION = "0.1-TEST"
eastern = pytz.timezone("US/Eastern")
now_et = datetime.now(eastern)

st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ============================================================
# NWS API
# ============================================================
@st.cache_data(ttl=300)
def fetch_nws_forecast(gridpoint):
    url = f"https://api.weather.gov/gridpoints/{gridpoint}/forecast"
    headers = {"User-Agent": "TimeEdgeTest/0.1"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        return {"success": True, "data": resp.json()}
    except Exception as e:
        return {"success": False, "error": str(e)}

def extract_temps_for_date(forecast_data, target_date):
    periods = forecast_data.get("properties", {}).get("periods", [])
    high = None
    low = None
    for period in periods:
        name = period.get("name", "").lower()
        temp = period.get("temperature")
        start_time = period.get("startTime", "")
        if target_date.strftime("%Y-%m-%d") in start_time:
            if "night" in name or "tonight" in name:
                low = temp
            elif temp:
                if high is None or temp > high:
                    high = temp
    return {"high": high, "low": low}

# ============================================================
# MAIN APP
# ============================================================
st.title("⏳ Time Edge Test Lab")
st.caption(f"PRIVATE | {now_et.strftime('%I:%M %p ET')} | v{VERSION}")

st.markdown("""
<div style="background: #1a1a2e; padding: 15px; border-radius: 8px; border-left: 4px solid #ff6b6b; margin-bottom: 20px;">
    <strong style="color: #ff6b6b;">🔒 OWNER ONLY TEST APP</strong><br>
    <span style="color: #888;">Testing tomorrow's NWS forecast for Time Edge positioning</span>
</div>
""", unsafe_allow_html=True)

# NYC Only for testing
gridpoint = "OKX/33,37"
city_name = "New York City"

today = now_et.date()
tomorrow = today + timedelta(days=1)

st.markdown("---")

# Fetch forecast once
nws_result = fetch_nws_forecast(gridpoint)

if nws_result["success"]:
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("## 📅 TODAY")
        st.caption(f"{today.strftime('%A, %B %d')}")
        
        today_temps = extract_temps_for_date(nws_result["data"], today)
        
        if today_temps["high"]:
            st.metric("NWS High", f"{today_temps['high']}°F")
        else:
            st.warning("No high temp data")
            
        if today_temps["low"]:
            st.metric("NWS Low", f"{today_temps['low']}°F")
        else:
            st.warning("No low temp data")
    
    with col2:
        st.markdown("## ⏳ TOMORROW")
        st.caption(f"{tomorrow.strftime('%A, %B %d')}")
        
        tomorrow_temps = extract_temps_for_date(nws_result["data"], tomorrow)
        
        if tomorrow_temps["high"]:
            st.metric("NWS High", f"{tomorrow_temps['high']}°F")
        else:
            st.warning("No high temp data")
            
        if tomorrow_temps["low"]:
            st.metric("NWS Low", f"{tomorrow_temps['low']}°F")
        else:
            st.warning("No low temp data")
    
    # Comparison
    st.markdown("---")
    st.markdown("## 📊 TIME EDGE ANALYSIS")
    
    if today_temps["high"] and tomorrow_temps["high"]:
        high_change = tomorrow_temps["high"] - today_temps["high"]
        st.markdown(f"**High Temp Change:** {high_change:+}°F")
        
        if abs(high_change) >= 5:
            st.success(f"🔥 SIGNIFICANT SHIFT — {abs(high_change)}° swing detected")
        elif abs(high_change) >= 3:
            st.info(f"📈 MODERATE SHIFT — {abs(high_change)}° change")
        else:
            st.caption("No major swing — stable forecast")
    
    if today_temps["low"] and tomorrow_temps["low"]:
        low_change = tomorrow_temps["low"] - today_temps["low"]
        st.markdown(f"**Low Temp Change:** {low_change:+}°F")
        
        if abs(low_change) >= 5:
            st.success(f"❄️ SIGNIFICANT SHIFT — {abs(low_change)}° swing detected")
        elif abs(low_change) >= 3:
            st.info(f"📈 MODERATE SHIFT — {abs(low_change)}° change")
        else:
            st.caption("No major swing — stable forecast")
    
    st.markdown("---")
    st.markdown("### 💡 Time Edge Strategy")
    st.markdown("""
    **If tomorrow shows significant shift from today:**
    1. Check if Kalshi tomorrow markets are open yet
    2. If YES → Position based on NWS forecast
    3. If NO → Set reminder to check at 8 AM when markets open
    4. Early positioning = buying before crowd sees the swing
    
    **Key insight:** NWS updates overnight. You see the forecast before morning traders.
    """)

else:
    st.error(f"NWS API Error: {nws_result.get('error', 'Unknown')}")

st.markdown("---")
st.caption("⚠️ Private test app — not for production")
