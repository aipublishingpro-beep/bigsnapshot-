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
    
    .app-card {
        display: block;
        background: linear-gradient(135deg, #1e1e2e 0%, #2a2a3e 100%);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 15px;
        border: 1px solid #333;
        transition: transform 0.2s, border-color 0.2s;
        text-decoration: none;
        cursor: pointer;
    }
    
    .app-card:hover {
        transform: translateY(-4px);
        border-color: #4dabf7;
        box-shadow: 0 8px 25px rgba(77, 171, 247, 0.2);
    }
    
    .app-card-disabled {
        display: block;
        background: linear-gradient(135deg, #1a1a24 0%, #22222e 100%);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 15px;
        border: 1px solid #2a2a2a;
        opacity: 0.6;
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
# LOGIN PAGE (if not authenticated)
# ============================================================
if not st.session_state.authenticated:
    st.markdown("""
    <div style="text-align: center; padding: 60px 20px 30px 20px;">
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
    
    # Beta signup callout
    st.markdown("""
    <div style="max-width: 500px; margin: 30px auto; padding: 30px;
                background: linear-gradient(135deg, #1a3a2a 0%, #2a4a3a 100%);
                border-radius: 16px; border: 1px solid #3a5a4a; text-align: center;">
        <p style="color: #00c853; font-size: 18px; font-weight: 700; margin-bottom: 10px;">
            🚀 NOW IN PRIVATE BETA
        </p>
        <p style="color: #ccc; font-size: 14px; margin-bottom: 20px;">
            Want access? Email us to request a beta invite.
        </p>
        <a href="mailto:aipublishingpro@gmail.com?subject=BigSnapshot%20Beta%20Request&body=I%20would%20like%20to%20join%20the%20BigSnapshot%20beta%20program."
           style="display: inline-block; background: #00c853; color: #000; padding: 12px 30px;
                  border-radius: 8px; font-weight: 700; text-decoration: none; font-size: 14px;">
            📧 REQUEST BETA ACCESS
        </a>
    </div>
    """, unsafe_allow_html=True)
    
    # Password entry
    st.markdown("""
    <div style="max-width: 400px; margin: 30px auto; text-align: center;">
        <p style="color: #888; font-size: 14px; margin-bottom: 15px;">
            Already a beta tester? Enter your password:
        </p>
    </div>
    """, unsafe_allow_html=True)
    
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
        
        st.markdown("""
        <p style="color: #555; font-size: 11px; margin-top: 20px; text-align: center;">
            Contact aipublishingpro@gmail.com for access
        </p>
        """, unsafe_allow_html=True)
    
    st.stop()

# ============================================================
# AUTHENTICATED - SHOW APP HUB
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
# CLICKABLE APP CARDS
# ============================================================
st.markdown("""
<div style="max-width: 900px; margin: 0 auto; padding: 0 20px;">
    <p style="color: #888; font-size: 13px; margin-bottom: 20px; text-align: center;">
        CLICK A CARD TO OPEN
    </p>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    # NFL
    if st.button("🏈  NFL Edge Finder  •  LIVE", use_container_width=True, key="nfl_btn"):
        st.switch_page("pages/1_NFL.py")
    
    # NHL
    if st.button("🏒  NHL Edge Finder  •  LIVE", use_container_width=True, key="nhl_btn"):
        st.switch_page("pages/3_NHL.py")
    
    # Temp
    if st.button("🌡️  Temp Edge Finder  •  LIVE", use_container_width=True, key="temp_btn"):
        st.switch_page("pages/5_Temp.py")

with col2:
    # NBA
    if st.button("🏀  NBA Edge Finder  •  LIVE", use_container_width=True, key="nba_btn"):
        st.switch_page("pages/2_NBA.py")
    
    # MLB - disabled
    st.button("⚾  MLB Edge Finder  •  COMING SOON", use_container_width=True, key="mlb_btn", disabled=True)
    
    # Politics - disabled
    st.button("🗳️  Politics Edge Finder  •  COMING SOON", use_container_width=True, key="pol_btn", disabled=True)

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
