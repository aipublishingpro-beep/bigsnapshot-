import streamlit as st

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="BigSnapshot | Prediction Market Edge Finder",
    page_icon="📊",
    layout="wide"
)

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
    
    .app-card {
        background: linear-gradient(135deg, #1e1e2e 0%, #2a2a3e 100%);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 15px;
        border: 1px solid #333;
        transition: transform 0.2s, border-color 0.2s;
    }
    
    .app-card:hover {
        transform: translateY(-2px);
        border-color: #4dabf7;
    }
    
    .status-live {
        background: #00c853;
        color: #000;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: 700;
    }
    
    .status-soon {
        background: #555;
        color: #fff;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# HEADER
# ============================================================
st.markdown("""
<div style="text-align: center; padding: 60px 20px 40px 20px;">
    <div style="font-size: 70px; margin-bottom: 15px;">📊</div>
    <h1 style="font-size: 52px; font-weight: 800; color: #fff; margin-bottom: 10px;">
        BigSnapshot
    </h1>
    <p style="color: #888; font-size: 20px; margin-bottom: 10px;">
        Prediction Market Edge Finder
    </p>
    <p style="color: #555; font-size: 14px;">
        Structural analysis for Kalshi markets
    </p>
</div>
""", unsafe_allow_html=True)

# ============================================================
# APP GRID
# ============================================================
st.markdown("""
<div style="max-width: 900px; margin: 0 auto; padding: 0 20px;">
    <p style="color: #888; font-size: 13px; margin-bottom: 20px; text-align: center;">
        SELECT A MARKET CATEGORY
    </p>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    # NFL
    st.markdown("""
    <div class="app-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span style="font-size: 28px;">🏈</span>
                <span style="font-size: 20px; font-weight: 700; color: #fff; margin-left: 12px;">NFL Edge Finder</span>
            </div>
            <span class="status-live">LIVE</span>
        </div>
        <p style="color: #888; font-size: 14px; margin-top: 12px;">Game spreads, totals, player props</p>
    </div>
    """, unsafe_allow_html=True)
    
    # NHL
    st.markdown("""
    <div class="app-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span style="font-size: 28px;">🏒</span>
                <span style="font-size: 20px; font-weight: 700; color: #fff; margin-left: 12px;">NHL Edge Finder</span>
            </div>
            <span class="status-live">LIVE</span>
        </div>
        <p style="color: #888; font-size: 14px; margin-top: 12px;">Game spreads, totals, player props</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Temp
    st.markdown("""
    <div class="app-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span style="font-size: 28px;">🌡️</span>
                <span style="font-size: 20px; font-weight: 700; color: #fff; margin-left: 12px;">Temp Edge Finder</span>
            </div>
            <span class="status-live">LIVE</span>
        </div>
        <p style="color: #888; font-size: 14px; margin-top: 12px;">Daily temperature forecasts vs markets</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    # NBA
    st.markdown("""
    <div class="app-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span style="font-size: 28px;">🏀</span>
                <span style="font-size: 20px; font-weight: 700; color: #fff; margin-left: 12px;">NBA Edge Finder</span>
            </div>
            <span class="status-live">LIVE</span>
        </div>
        <p style="color: #888; font-size: 14px; margin-top: 12px;">12-factor scoring model, live odds</p>
    </div>
    """, unsafe_allow_html=True)
    
    # MLB
    st.markdown("""
    <div class="app-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span style="font-size: 28px;">⚾</span>
                <span style="font-size: 20px; font-weight: 700; color: #fff; margin-left: 12px;">MLB Edge Finder</span>
            </div>
            <span class="status-soon">COMING SOON</span>
        </div>
        <p style="color: #888; font-size: 14px; margin-top: 12px;">Launching for 2026 season</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Politics
    st.markdown("""
    <div class="app-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span style="font-size: 28px;">🗳️</span>
                <span style="font-size: 20px; font-weight: 700; color: #fff; margin-left: 12px;">Politics Edge Finder</span>
            </div>
            <span class="status-soon">COMING SOON</span>
        </div>
        <p style="color: #888; font-size: 14px; margin-top: 12px;">2026 Midterms — launching Summer 2026</p>
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# HOW IT WORKS
# ============================================================
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("""
<div style="max-width: 800px; margin: 40px auto; padding: 30px; 
            background: linear-gradient(135deg, #1a2a3a 0%, #2a3a4a 100%);
            border-radius: 16px; border: 1px solid #3a4a5a;">
    <h3 style="color: #fff; font-size: 18px; margin-bottom: 20px; text-align: center;">
        ⚡ How BigSnapshot Works
    </h3>
    <div style="display: flex; gap: 30px; flex-wrap: wrap; justify-content: center;">
        <div style="flex: 1; min-width: 200px; text-align: center;">
            <p style="color: #4dabf7; font-size: 24px; margin-bottom: 8px;">1</p>
            <p style="color: #ccc; font-size: 14px;">Pull live odds from Kalshi prediction markets</p>
        </div>
        <div style="flex: 1; min-width: 200px; text-align: center;">
            <p style="color: #4dabf7; font-size: 24px; margin-bottom: 8px;">2</p>
            <p style="color: #ccc; font-size: 14px;">Run structural analysis to find mispricings</p>
        </div>
        <div style="flex: 1; min-width: 200px; text-align: center;">
            <p style="color: #4dabf7; font-size: 24px; margin-bottom: 8px;">3</p>
            <p style="color: #ccc; font-size: 14px;">Surface edge opportunities before markets adjust</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# FOOTER
# ============================================================
st.markdown("""
<div style="text-align: center; padding: 40px 20px; color: #555;">
    <p style="font-size: 12px; margin-bottom: 8px;">
        ⚠️ For entertainment and analysis only. Not financial advice.
    </p>
    <p style="font-size: 11px;">
        BigSnapshot © 2026 | bigsnapshot.com
    </p>
</div>
""", unsafe_allow_html=True)
