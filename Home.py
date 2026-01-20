import streamlit as st

st.set_page_config(
    page_title="BigSnapshot | Prediction Market Edge Finder",
    page_icon="📊",
    layout="wide"
)

# ============================================================
# GA4 TRACKING
# ============================================================
st.markdown("""
<script async src="https://www.googletagmanager.com/gtag/js?id=G-NQKY5VQ376"></script>
<script>window.dataLayer = window.dataLayer || [];function gtag(){dataLayer.push(arguments);}gtag('js', new Date());gtag('config', 'G-NQKY5VQ376');</script>
""", unsafe_allow_html=True)

# ============================================================
# SESSION STATE
# ============================================================
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

# ============================================================
# PASSWORD CONFIG
# ============================================================
VALID_PASSWORDS = {
    "WILLIE1228": "Owner",
    "BETAUSER": "Beta Tester",
}

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
    
    .card-link {
        text-decoration: none !important;
        display: block;
    }
    
    .card {
        padding: 30px;
        border-radius: 20px;
        text-align: center;
        min-height: 220px;
        transition: transform 0.2s, box-shadow 0.2s;
        cursor: pointer;
    }
    
    .card:hover {
        transform: translateY(-5px);
    }
    
    .card-nfl {
        background: linear-gradient(135deg, #1a1a2e, #0a0a1e);
        border: 2px solid #00aa00;
    }
    .card-nfl:hover { box-shadow: 0 10px 30px rgba(0, 170, 0, 0.3); }
    
    .card-nba {
        background: linear-gradient(135deg, #1a2e1a, #0a1e0a);
        border: 2px solid #ff6600;
    }
    .card-nba:hover { box-shadow: 0 10px 30px rgba(255, 102, 0, 0.3); }
    
    .card-nhl {
        background: linear-gradient(135deg, #1a1a2e, #0a0a1e);
        border: 2px solid #4dabf7;
    }
    .card-nhl:hover { box-shadow: 0 10px 30px rgba(77, 171, 247, 0.3); }
    
    .card-temp {
        background: linear-gradient(135deg, #2e1a2e, #1e0a1e);
        border: 2px solid #e040fb;
    }
    .card-temp:hover { box-shadow: 0 10px 30px rgba(224, 64, 251, 0.3); }
    
    .card-disabled {
        background: linear-gradient(135deg, #2e2e1a, #1e1e0a);
        border: 2px solid #555;
        opacity: 0.6;
    }
    
    .card-icon { font-size: 3.5em; }
    .card-title { font-size: 1.5em; font-weight: bold; margin-top: 15px; }
    .card-subtitle { color: #888; margin-top: 10px; font-size: 0.9em; }
    
    .badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.75em;
        font-weight: 700;
        margin-top: 15px;
    }
    .badge-live { background: #00c853; color: #000; }
    .badge-soon { background: #555; color: #fff; }
    
    .title-nfl { color: #00aa00; }
    .title-nba { color: #ff6600; }
    .title-nhl { color: #4dabf7; }
    .title-temp { color: #e040fb; }
    .title-disabled { color: #888; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# LOGIN PAGE
# ============================================================
if not st.session_state.authenticated:
    st.markdown("""
    <div style="text-align: center; padding: 60px 20px 30px 20px;">
        <div style="font-size: 70px; margin-bottom: 15px;">📊</div>
        <h1 style="font-size: 52px; font-weight: 800; color: #fff; margin-bottom: 10px;">BigSnapshot</h1>
        <p style="color: #888; font-size: 20px; margin-bottom: 10px;">Prediction Market Edge Finder</p>
        <p style="color: #555; font-size: 14px;">Structural analysis for Kalshi markets</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="max-width: 500px; margin: 30px auto; padding: 30px;
                background: linear-gradient(135deg, #1a3a2a 0%, #2a4a3a 100%);
                border-radius: 16px; border: 1px solid #3a5a4a; text-align: center;">
        <p style="color: #00c853; font-size: 18px; font-weight: 700; margin-bottom: 10px;">🚀 NOW IN PRIVATE BETA</p>
        <p style="color: #ccc; font-size: 14px; margin-bottom: 20px;">Want access? Email us to request a beta invite.</p>
        <a href="mailto:aipublishingpro@gmail.com?subject=BigSnapshot%20Beta%20Request&body=I%20would%20like%20to%20join%20the%20BigSnapshot%20beta%20program."
           style="display: inline-block; background: #00c853; color: #000; padding: 12px 30px;
                  border-radius: 8px; font-weight: 700; text-decoration: none; font-size: 14px;">
            📧 REQUEST BETA ACCESS
        </a>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<p style="text-align:center; color:#888; margin-top:30px;">Already a beta tester? Enter your password:</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        password_input = st.text_input("Password", type="password", label_visibility="collapsed", placeholder="Enter password")
        if st.button("🔓 UNLOCK", use_container_width=True, type="primary"):
            if password_input.upper() in VALID_PASSWORDS:
                st.session_state.authenticated = True
                st.session_state.user_type = VALID_PASSWORDS[password_input.upper()]
                st.rerun()
            else:
                st.error("❌ Invalid password")
        st.markdown('<p style="text-align:center; color:#555; font-size:11px; margin-top:20px;">Contact aipublishingpro@gmail.com for access</p>', unsafe_allow_html=True)
    
    st.stop()

# ============================================================
# AUTHENTICATED - APP HUB
# ============================================================
st.markdown("""
<div style="text-align: center; padding: 40px 20px 20px 20px;">
    <div style="font-size: 60px; margin-bottom: 10px;">📊</div>
    <h1 style="font-size: 48px; font-weight: 800; color: #fff; margin-bottom: 5px;">BigSnapshot</h1>
    <p style="color: #888; font-size: 18px;">Prediction Market Edge Finder</p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ============================================================
# CLICKABLE CARDS - ROW 1
# ============================================================
st.markdown("""
<div style="display: flex; gap: 20px; flex-wrap: wrap; justify-content: center; padding: 0 20px;">
    <a href="/NFL" target="_self" class="card-link" style="flex: 1; min-width: 280px; max-width: 350px;">
        <div class="card card-nfl">
            <div class="card-icon">🏈</div>
            <div class="card-title title-nfl">NFL Edge Finder</div>
            <div class="card-subtitle">10-Factor Model</div>
            <div><span class="badge badge-live">LIVE</span></div>
        </div>
    </a>
    <a href="/NBA" target="_self" class="card-link" style="flex: 1; min-width: 280px; max-width: 350px;">
        <div class="card card-nba">
            <div class="card-icon">🏀</div>
            <div class="card-title title-nba">NBA Edge Finder</div>
            <div class="card-subtitle">12-Factor Model</div>
            <div><span class="badge badge-live">LIVE</span></div>
        </div>
    </a>
    <a href="/NHL" target="_self" class="card-link" style="flex: 1; min-width: 280px; max-width: 350px;">
        <div class="card card-nhl">
            <div class="card-icon">🏒</div>
            <div class="card-title title-nhl">NHL Edge Finder</div>
            <div class="card-subtitle">10-Factor Model</div>
            <div><span class="badge badge-live">LIVE</span></div>
        </div>
    </a>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ============================================================
# CLICKABLE CARDS - ROW 2
# ============================================================
st.markdown("""
<div style="display: flex; gap: 20px; flex-wrap: wrap; justify-content: center; padding: 0 20px;">
    <a href="/Temp" target="_self" class="card-link" style="flex: 1; min-width: 280px; max-width: 350px;">
        <div class="card card-temp">
            <div class="card-icon">🌡️</div>
            <div class="card-title title-temp">Temp Edge Finder</div>
            <div class="card-subtitle">NWS vs Kalshi</div>
            <div><span class="badge badge-live">LIVE</span></div>
        </div>
    </a>
    <div style="flex: 1; min-width: 280px; max-width: 350px;">
        <div class="card card-disabled">
            <div class="card-icon">⚾</div>
            <div class="card-title title-disabled">MLB Edge Finder</div>
            <div class="card-subtitle">Coming Soon</div>
            <div><span class="badge badge-soon">SOON</span></div>
        </div>
    </div>
    <div style="flex: 1; min-width: 280px; max-width: 350px;">
        <div class="card card-disabled">
            <div class="card-icon">🗳️</div>
            <div class="card-title title-disabled">Politics Edge Finder</div>
            <div class="card-subtitle">Coming Summer 2026</div>
            <div><span class="badge badge-soon">SOON</span></div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ============================================================
# HOW IT WORKS
# ============================================================
st.markdown("""
<div style="max-width: 800px; margin: 40px auto; padding: 30px; 
            background: linear-gradient(135deg, #1a2a3a 0%, #2a3a4a 100%);
            border-radius: 16px; border: 1px solid #3a4a5a;">
    <h3 style="color: #fff; font-size: 18px; margin-bottom: 20px; text-align: center;">⚡ How BigSnapshot Works</h3>
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
    <p style="font-size: 12px; margin-bottom: 8px;">⚠️ For entertainment and analysis only. Not financial advice.</p>
    <p style="font-size: 11px;">📧 aipublishingpro@gmail.com | bigsnapshot.com</p>
</div>
""", unsafe_allow_html=True)
