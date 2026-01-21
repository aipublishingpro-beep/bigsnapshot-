import streamlit as st

st.set_page_config(
    page_title="Politics Edge Finder | BigSnapshot",
    page_icon="🗳️",
    layout="wide"
)

# ============================================================
# AUTH CHECK
# ============================================================
if 'authenticated' not in st.session_state or not st.session_state.authenticated:
    st.warning("⚠️ Please log in from the Home page first.")
    st.page_link("Home.py", label="🏠 Go to Home", use_container_width=True)
    st.stop()

# ============================================================
# CUSTOM CSS
# ============================================================
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stApp {
        background: linear-gradient(180deg, #0a0a0f 0%, #1a1a2e 100%);
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# COMING SOON PAGE
# ============================================================
st.markdown("""
<div style="text-align: center; padding: 80px 20px;">
    <div style="font-size: 80px; margin-bottom: 20px;">🗳️</div>
    <h1 style="font-size: 48px; font-weight: 800; color: #fff; margin-bottom: 15px;">
        Politics Edge Finder
    </h1>
    <p style="color: #888; font-size: 22px; margin-bottom: 40px;">
        Coming Soon — 2026 Midterms
    </p>
    <div style="background: linear-gradient(135deg, #1e1e2e 0%, #2a2a3e 100%); 
                border-radius: 16px; padding: 40px; max-width: 600px; margin: 0 auto;
                border: 1px solid #333;">
        <p style="color: #4dabf7; font-size: 18px; font-weight: 600; margin-bottom: 20px;">
            📅 November 3, 2026
        </p>
        <p style="color: #ccc; font-size: 16px; line-height: 1.7; margin-bottom: 25px;">
            Political prediction markets are seasonal. This tool will activate when 
            Kalshi has meaningful political markets — primaries, Senate races, 
            House control odds, and more.
        </p>
        <div style="background: #1a1a2e; border-radius: 12px; padding: 20px; text-align: left;">
            <p style="color: #888; font-size: 13px; margin-bottom: 10px;">EXPECTED TIMELINE</p>
            <p style="color: #666; font-size: 14px; margin: 8px 0;">⬜ Jan - Mar 2026: Candidate announcements</p>
            <p style="color: #666; font-size: 14px; margin: 8px 0;">⬜ Apr - Aug 2026: Primary season</p>
            <p style="color: #00c853; font-size: 14px; margin: 8px 0;">🟢 Sep - Nov 2026: Full markets active</p>
        </div>
    </div>
    <p style="color: #555; font-size: 14px; margin-top: 50px;">
        BigSnapshot © 2026 | Check back in Summer 2026
    </p>
</div>
""", unsafe_allow_html=True)
