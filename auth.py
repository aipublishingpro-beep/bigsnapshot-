import streamlit as st
import os
import json
from datetime import datetime
import pytz

EMAIL_LOG_FILE = "email_signups.json"

def load_emails():
    """Load existing emails from file"""
    try:
        if os.path.exists(EMAIL_LOG_FILE):
            with open(EMAIL_LOG_FILE, 'r') as f:
                return json.load(f)
    except:
        pass
    return []

def save_email(email):
    """Save new email to file"""
    try:
        emails = load_emails()
        eastern = pytz.timezone('US/Eastern')
        now = datetime.now(eastern)
        
        # Check if email already exists
        existing = [e for e in emails if e.get('email', '').lower() == email.lower()]
        if not existing:
            emails.append({
                "email": email,
                "timestamp": now.strftime("%Y-%m-%d %H:%M:%S ET"),
                "source": "bigsnapshot"
            })
            with open(EMAIL_LOG_FILE, 'w') as f:
                json.dump(emails, f, indent=2)
        return True
    except:
        return False

def is_valid_email(email):
    """Basic email validation"""
    if not email:
        return False
    email = email.strip()
    if "@" not in email or "." not in email:
        return False
    if len(email) < 5:
        return False
    return True

def require_auth():
    """
    Email gate for free access.
    Users must enter email once to access all tools.
    """
    # Check if already authenticated this session
    if st.session_state.get("authenticated"):
        return
    
    # Check localStorage for returning users
    if "auth_checked" not in st.session_state:
        st.session_state.auth_checked = False
    
    # Show email gate
    st.markdown("""
    <div style="text-align: center; padding: 40px 20px;">
        <div style="font-size: 50px; margin-bottom: 15px;">🎯</div>
        <h2 style="color: #fff; margin-bottom: 10px;">Free Access</h2>
        <p style="color: #4ade80; font-size: 16px; font-weight: 600; margin-bottom: 8px;">✓ No credit card required</p>
        <p style="color: #ccc; font-size: 14px;">✓ No payment info &nbsp;•&nbsp; ✓ No spam &nbsp;•&nbsp; ✓ Instant access</p>
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
            We'll only email you for major updates.<br>
            Questions? <a href="mailto:aipublishingpro@gmail.com" style="color: #4ade80;">aipublishingpro@gmail.com</a>
        </p>
        """, unsafe_allow_html=True)
    
    st.stop()
