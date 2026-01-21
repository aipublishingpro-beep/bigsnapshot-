# FILE: fred_data.py
# FRED API Integration for BigSnapshot Economics Page
# Place this file in your repository root (same level as Home.py)

import requests
import streamlit as st

# ============================================================
# CONFIGURATION
# ============================================================
# Add your FRED API key to Streamlit secrets:
# In Streamlit Cloud: Settings > Secrets > Add:
# FRED_API_KEY = "your_key_here"
#
# Get free API key at: https://fred.stlouisfed.org/docs/api/api_key.html

FRED_BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

# Key economic series IDs
SERIES = {
    "fed_rate_upper": "DFEDTARU",
    "fed_rate_lower": "DFEDTARL",
    "cpi": "CPIAUCSL",
    "core_cpi": "CPILFESL",
    "unemployment": "UNRATE",
    "gdp_growth": "A191RL1Q225SBEA",
    "treasury_10y": "DGS10",
    "treasury_2y": "DGS2",
    "jobless_claims": "ICSA",
}

# Fallback values if API fails
FALLBACKS = {
    "fed_rate": "3.50% - 3.75%",
    "unemployment": "4.2%",
    "gdp_growth": "2.5%",
    "cpi_yoy": "2.7%",
}

# ============================================================
# API FUNCTIONS
# ============================================================
def get_api_key():
    """Get FRED API key from secrets or use hardcoded key"""
    try:
        return st.secrets["FRED_API_KEY"]
    except:
        return "YOUR_KEY_HERE"  # Replace YOUR_KEY_HERE with your actual FRED API key

@st.cache_data(ttl=3600)
def fetch_fred_series(series_id, limit=1):
    """
    Fetch latest observation(s) from FRED API
    
    Args:
        series_id: FRED series identifier
        limit: Number of observations to fetch
        
    Returns:
        dict with 'value' and 'date', or None on error
    """
    try:
        params = {
            "series_id": series_id,
            "api_key": get_api_key(),
            "file_type": "json",
            "sort_order": "desc",
            "limit": limit
        }
        response = requests.get(FRED_BASE_URL, params=params, timeout=10)
        
        if response.status_code == 429:
            return None
            
        if response.status_code == 200:
            data = response.json()
            if 'observations' in data and len(data['observations']) > 0:
                obs = data['observations'][0]
                value = obs.get('value', 'N/A')
                if value == '.':
                    return None
                return {
                    "value": value,
                    "date": obs.get('date', 'N/A')
                }
        return None
    except Exception:
        return None

@st.cache_data(ttl=3600)
def fetch_fred_series_multiple(series_id, limit=13):
    """
    Fetch multiple observations for YoY calculations
    
    Args:
        series_id: FRED series identifier
        limit: Number of observations (13 for monthly YoY)
        
    Returns:
        list of observations or None
    """
    try:
        params = {
            "series_id": series_id,
            "api_key": get_api_key(),
            "file_type": "json",
            "sort_order": "desc",
            "limit": limit
        }
        response = requests.get(FRED_BASE_URL, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'observations' in data and len(data['observations']) > 0:
                return data['observations']
        return None
    except Exception:
        return None

# ============================================================
# DATA GETTER FUNCTIONS
# ============================================================
def get_fed_rate():
    """Get current Fed Funds target range"""
    upper = fetch_fred_series(SERIES["fed_rate_upper"])
    lower = fetch_fred_series(SERIES["fed_rate_lower"])
    
    if upper and lower:
        try:
            u = float(upper['value'])
            l = float(lower['value'])
            return {
                "value": f"{l:.2f}%-{u:.2f}%",
                "upper": u,
                "lower": l,
                "date": upper['date']
            }
        except:
            pass
    return {"value": FALLBACKS["fed_rate"], "upper": 3.75, "lower": 3.50, "date": "N/A"}

def get_unemployment():
    """Get latest unemployment rate"""
    data = fetch_fred_series(SERIES["unemployment"])
    if data:
        try:
            return {
                "value": f"{float(data['value']):.1f}%",
                "raw": float(data['value']),
                "date": data['date']
            }
        except:
            pass
    return {"value": FALLBACKS["unemployment"], "raw": 4.2, "date": "N/A"}

def get_gdp_growth():
    """Get latest GDP growth rate (annualized)"""
    data = fetch_fred_series(SERIES["gdp_growth"])
    if data:
        try:
            return {
                "value": f"{float(data['value']):.1f}%",
                "raw": float(data['value']),
                "date": data['date']
            }
        except:
            pass
    return {"value": FALLBACKS["gdp_growth"], "raw": 2.5, "date": "N/A"}

def get_cpi_yoy():
    """
    Calculate CPI Year-over-Year percentage change
    Requires 13 months of data to compare current vs 12 months ago
    """
    observations = fetch_fred_series_multiple(SERIES["cpi"], limit=13)
    if observations and len(observations) >= 13:
        try:
            current = float(observations[0]['value'])
            year_ago = float(observations[12]['value'])
            yoy_change = ((current - year_ago) / year_ago) * 100
            return {
                "value": f"{yoy_change:.1f}%",
                "raw": yoy_change,
                "date": observations[0]['date'],
                "current_cpi": current,
                "year_ago_cpi": year_ago
            }
        except:
            pass
    return {"value": FALLBACKS["cpi_yoy"], "raw": 2.7, "date": "N/A"}

def get_treasury_spread():
    """
    Get 10Y-2Y Treasury spread (yield curve indicator)
    Negative spread = inverted yield curve (recession signal)
    """
    t10 = fetch_fred_series(SERIES["treasury_10y"])
    t2 = fetch_fred_series(SERIES["treasury_2y"])
    
    if t10 and t2:
        try:
            t10_val = float(t10['value'])
            t2_val = float(t2['value'])
            spread = t10_val - t2_val
            return {
                "spread": f"{spread:.2f}%",
                "raw": spread,
                "inverted": spread < 0,
                "t10": t10_val,
                "t2": t2_val,
                "date": t10['date']
            }
        except:
            pass
    return None

def get_jobless_claims():
    """Get latest initial jobless claims"""
    data = fetch_fred_series(SERIES["jobless_claims"])
    if data:
        try:
            claims = int(float(data['value']))
            return {
                "value": f"{claims:,}",
                "raw": claims,
                "date": data['date']
            }
        except:
            pass
    return None

# ============================================================
# AGGREGATE FUNCTION
# ============================================================
def get_all_indicators():
    """
    Fetch all key economic indicators at once
    Returns dict with all indicator data
    """
    return {
        "fed_rate": get_fed_rate(),
        "unemployment": get_unemployment(),
        "gdp_growth": get_gdp_growth(),
        "cpi_yoy": get_cpi_yoy(),
        "treasury_spread": get_treasury_spread(),
        "jobless_claims": get_jobless_claims(),
    }

# ============================================================
# DISPLAY HELPERS
# ============================================================
def get_indicator_color(indicator, value):
    """
    Return color based on indicator value
    Green = good, Yellow = caution, Red = concern
    """
    if indicator == "unemployment":
        if value < 4.0:
            return "#4ade80"
        elif value < 5.0:
            return "#ffcc00"
        else:
            return "#ff6b6b"
    elif indicator == "cpi_yoy":
        if value < 2.5:
            return "#4ade80"
        elif value < 3.5:
            return "#ffcc00"
        else:
            return "#ff6b6b"
    elif indicator == "gdp_growth":
        if value > 2.0:
            return "#4ade80"
        elif value > 0:
            return "#ffcc00"
        else:
            return "#ff6b6b"
    return "#4a9eff"
