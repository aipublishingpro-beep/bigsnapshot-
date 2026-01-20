# Add these imports at the TOP of the file (with other imports)
import requests
import uuid

# Add this block RIGHT AFTER st.set_page_config(...)

# ============================================================
# GA4 TRACKING
# ============================================================
GA4_MEASUREMENT_ID = "G-NQKY5VQ376"
GA4_API_SECRET = "n4oBJjH7RXi3dA7aQo2CZA"

if "sid" not in st.session_state:
    st.session_state["sid"] = str(uuid.uuid4())

def track_ga4_event(event_name, params=None):
    """Send event to GA4 via Measurement Protocol"""
    try:
        url = f"https://www.google-analytics.com/mp/collect?measurement_id={GA4_MEASUREMENT_ID}&api_secret={GA4_API_SECRET}"
        payload = {
            "client_id": st.session_state.get("sid", str(uuid.uuid4())),
            "events": [{"name": event_name, "params": params or {}}]
        }
        requests.post(url, json=payload, timeout=2)
    except:
        pass

# Track page view on load
if "nhl_tracked" not in st.session_state:
    track_ga4_event("page_view", {"page_title": "NHL Edge Finder", "page_location": "https://bigsnapshot.streamlit.app/NHL"})
    st.session_state.nhl_tracked = True
