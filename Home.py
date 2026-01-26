import streamlit as st

st.set_page_config(page_title="BigSnapshot", page_icon="🎯", layout="wide")

import streamlit.components.v1 as components
components.html("""
<script async src="https://www.googletagmanager.com/gtag/js?id=G-1T35YHHYBC"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-1T35YHHYBC', { send_page_view: true });
</script>
""", height=0)

import os
import json
from datetime import datetime
import pytz

EMAIL_LOG_FILE = "email_signups.json"

def load_emails():
    try:
        if os.path.exists(EMAIL_LOG_FILE):
            with open(EMAIL_LOG_FILE, 'r') as f:
                return json.load(f)
    except:
        pass
    return []

def save_email(email):
    try:
        emails = load_emails()
        eastern = pytz.timezone('US/Eastern')
        now = datetime.now(eastern)
        existing = [e for e in emails if e.get('email', '').lower() == email.lower()]
        if not existing:
            emails.append({
                "email": email,
                "timestamp": now.strftime("%Y-%m-%d %H:%M:%S ET"),
                "source": "bigsnapshot_home"
            })
            with open(EMAIL_LOG_FILE, 'w') as f:
                json.dump(emails, f, indent=2)
        return True
    except:
        return False

def is_valid_email(email):
    if not email:
        return False
    email = email.strip()
    if "@" not in email or "." not in email:
        return False
    if len(email) < 5:
        return False
    return True

# ============================================================
# MOBILE CSS
# ============================================================
st.markdown("""
<style>
@media (max-width: 768px) {
    .stColumns > div { flex: 1 1 100% !important; min-width: 100% !important; }
    [data-testid="stMetricValue"] { font-size: 1.2rem !important; }
    [data-testid="stMetricLabel"] { font-size: 0.8rem !important; }
    h1 { font-size: 1.5rem !important; }
    h2 { font-size: 1.2rem !important; }
    h3 { font-size: 1rem !important; }
    button { padding: 8px 12px !important; font-size: 0.85em !important; }
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# CHECK AUTH STATE
# ============================================================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# ============================================================
# NOT AUTHENTICATED - SHOW EMAIL GATE
# ============================================================
if not st.session_state.authenticated:
    
    # HERO
    st.markdown("""
    <div style="text-align: center; padding: 40px 20px 20px 20px;">
        <div style="font-size: 70px; margin-bottom: 15px;">🎯</div>
        <h1 style="font-size: 52px; font-weight: 800; color: #fff; margin-bottom: 10px;">BigSnapshot</h1>
        <p style="color: #888; font-size: 20px; margin-bottom: 10px;">Prediction Market Edge Finder</p>
        <p style="color: #555; font-size: 14px;">Structural analysis for Kalshi markets</p>
    </div>
    """, unsafe_allow_html=True)
    
    # FREE BANNER
    st.markdown("""
    <div style="text-align: center; padding: 20px; margin: 20px auto; max-width: 800px; background: linear-gradient(135deg, #1a3a1a 0%, #2a4a2a 100%); border-radius: 16px; border: 2px solid #22c55e;">
        <h2 style="color: #4ade80; margin-bottom: 10px;">🎉 FREE FOR 2025-26 SEASON</h2>
        <p style="color: #ccc; font-size: 16px; margin-bottom: 10px;">
            All tools are <strong>100% free</strong> while we build proof and refine our edge-finding systems.
        </p>
        <p style="color: #f97316; font-size: 13px;">
            ⚠️ We reserve the right to implement paid subscriptions at any time.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # TOOL CARDS PREVIEW
    st.markdown("### 🔥 What You Get — Free")
    st.markdown("""
    <div style="display: flex; justify-content: center; gap: 12px; flex-wrap: wrap; padding: 15px;">
        <div style="background: linear-gradient(135deg, #1a3a1a 0%, #2a4a2a 100%); border-radius: 12px; padding: 15px; width: 100px; text-align: center; border: 1px solid #22c55e;">
            <div style="font-size: 30px;">🏀</div>
            <p style="color: #4ade80; margin: 5px 0 0 0; font-size: 12px;">NBA</p>
        </div>
        <div style="background: linear-gradient(135deg, #1a3a1a 0%, #2a4a2a 100%); border-radius: 12px; padding: 15px; width: 100px; text-align: center; border: 1px solid #22c55e;">
            <div style="font-size: 30px;">🏈</div>
            <p style="color: #4ade80; margin: 5px 0 0 0; font-size: 12px;">NFL</p>
        </div>
        <div style="background: linear-gradient(135deg, #1a3a1a 0%, #2a4a2a 100%); border-radius: 12px; padding: 15px; width: 100px; text-align: center; border: 1px solid #22c55e;">
            <div style="font-size: 30px;">🏒</div>
            <p style="color: #4ade80; margin: 5px 0 0 0; font-size: 12px;">NHL</p>
        </div>
        <div style="background: linear-gradient(135deg, #1a3a1a 0%, #2a4a2a 100%); border-radius: 12px; padding: 15px; width: 100px; text-align: center; border: 1px solid #22c55e;">
            <div style="font-size: 30px;">🎓</div>
            <p style="color: #4ade80; margin: 5px 0 0 0; font-size: 12px;">NCAA</p>
        </div>
        <div style="background: linear-gradient(135deg, #1a3a1a 0%, #2a4a2a 100%); border-radius: 12px; padding: 15px; width: 100px; text-align: center; border: 1px solid #22c55e;">
            <div style="font-size: 30px;">⚽</div>
            <p style="color: #4ade80; margin: 5px 0 0 0; font-size: 12px;">Soccer</p>
        </div>
        <div style="background: linear-gradient(135deg, #1a3a1a 0%, #2a4a2a 100%); border-radius: 12px; padding: 15px; width: 100px; text-align: center; border: 1px solid #22c55e;">
            <div style="font-size: 30px;">🌡️</div>
            <p style="color: #4ade80; margin: 5px 0 0 0; font-size: 12px;">Temp</p>
        </div>
        <div style="background: linear-gradient(135deg, #1a3a1a 0%, #2a4a2a 100%); border-radius: 12px; padding: 15px; width: 100px; text-align: center; border: 1px solid #22c55e;">
            <div style="font-size: 30px;">📊</div>
            <p style="color: #4ade80; margin: 5px 0 0 0; font-size: 12px;">Econ</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # EMAIL GATE - CLEAN INPUT
    st.markdown("""
    <div style="text-align: center; padding: 20px;">
        <h2 style="color: #fff; margin-bottom: 10px;">🔓 Enter Email to Unlock</h2>
        <p style="color: #4ade80; font-size: 16px; font-weight: 600; margin-bottom: 8px;">✓ No credit card required</p>
        <p style="color: #ccc; font-size: 14px;">✓ No payment info • ✓ No spam • ✓ Instant access</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        email = st.text_input("Your Email", placeholder="you@example.com", label_visibility="collapsed")
        
        if st.button("🔓 UNLOCK FREE ACCESS", use_container_width=True, type="primary"):
            if is_valid_email(email):
                save_email(email)
                st.session_state.authenticated = True
                st.session_state.user_email = email
                st.session_state.user_type = "Free User"
                st.rerun()
            else:
                st.error("Please enter a valid email address")
        
        st.markdown("""
        <p style="color: #666; font-size: 11px; text-align: center; margin-top: 15px;">
            Questions? <a href="mailto:aipublishingpro@gmail.com" style="color: #4ade80;">aipublishingpro@gmail.com</a>
        </p>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # VALUE PROP
    st.markdown("""
    <div style="text-align: center; padding: 20px; max-width: 700px; margin: 0 auto;">
        <h3 style="color: #fff; margin-bottom: 15px;">Why BigSnapshot?</h3>
        <p style="color: #888; font-size: 16px; line-height: 1.6;">
            Stop switching tabs. We pull live ESPN data, Vegas odds, and Kalshi prices into one screen — so you spend less time hunting and more time deciding.
        </p>
        <p style="color: #4ade80; font-size: 14px; margin-top: 15px;">
            Fewer bad decisions = Fewer bad trades. That's the edge.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # FOOTER
    st.markdown("""
    <div style="text-align: center; padding: 30px 20px;">
        <p style="color: #555; font-size: 12px;">
            ⚠️ For entertainment and educational purposes only. Not financial advice.
        </p>
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# AUTHENTICATED - SHOW FULL APP
# ============================================================
else:
    st.markdown("""
    <div style="text-align: center; padding: 30px 20px 15px 20px;">
        <div style="font-size: 50px; margin-bottom: 10px;">🎯</div>
        <h1 style="font-size: 42px; font-weight: 800; color: #fff; margin-bottom: 5px;">BigSnapshot</h1>
        <p style="color: #888; font-size: 16px;">Prediction Market Edge Finder</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Free banner
    st.markdown("""
    <div style="text-align: center; padding: 15px; margin: 10px auto 20px auto; max-width: 700px; background: linear-gradient(135deg, #1a3a1a 0%, #2a4a2a 100%); border-radius: 12px; border: 1px solid #22c55e;">
        <p style="color: #4ade80; font-size: 14px; margin: 0;">
            🎉 <strong>FREE FOR 2025-26 SEASON</strong> — All tools unlocked
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 🔥 Live Tools — All Free")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("🏀 NBA Edge", use_container_width=True, type="primary"):
            st.switch_page("pages/2_NBA.py")
        if st.button("🏈 NFL Edge", use_container_width=True, type="primary"):
            st.switch_page("pages/1_NFL.py")
    with col2:
        if st.button("🏒 NHL Edge", use_container_width=True, type="primary"):
            st.switch_page("pages/3_NHL.py")
        if st.button("⚽ Soccer Edge", use_container_width=True, type="primary"):
            st.switch_page("pages/8_Soccer.py")
    with col3:
        if st.button("🎓 NCAA Edge", use_container_width=True, type="primary"):
            st.switch_page("pages/7_NCAA.py")
        if st.button("🌡️ Temp Edge", use_container_width=True, type="primary"):
            st.switch_page("pages/5_Temp.py")
    with col4:
        if st.button("📊 Economics", use_container_width=True, type="primary"):
            st.switch_page("pages/9_Economics.py")
    
    # Dev notice
    st.markdown("""
    <div style="text-align: center; padding: 12px; margin: 20px auto; max-width: 600px; background: #1a1a2a; border-radius: 10px; border: 1px solid #3b82f6;">
        <p style="color: #60a5fa; font-size: 13px; margin: 0;">
            🔧 NHL, Soccer, Economics in continued development
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Coming Soon
    st.markdown("### 🚧 Coming Soon")
    st.markdown("⚾ MLB • 🏛️ Politics • 🎬 Entertainment")
    
    st.markdown("---")
    
    # Footer
    st.markdown("""
    <div style="text-align: center; padding: 20px;">
        <p style="color: #f97316; font-size: 12px; margin-bottom: 10px;">
            ⚠️ Free during beta. We reserve the right to implement paid subscriptions at any time.
        </p>
        <p style="color: #555; font-size: 11px;">
            ⚠️ For entertainment and educational purposes only. Not financial advice.
        </p>
    </div>
    """, unsafe_allow_html=True)
