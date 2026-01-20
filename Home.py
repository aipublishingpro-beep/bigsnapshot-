# ============================================================
# PASSWORD CONFIG - PAID ACCESS ONLY
# ============================================================
VALID_PASSWORDS = {
    "WILLIE1228": "Owner",
    # Add paid subscribers here after Stripe payment:
    # "PAID-001": "Subscriber Name",
}

# ============================================================
# STRIPE PAYMENT LINK
# ============================================================
STRIPE_LINK = "https://buy.stripe.com/14A00lcgHe9oaIodx65Rm00"

# ============================================================
# LOGIN PAGE (REPLACE YOUR EXISTING LOGIN SECTION)
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
    
    # ============ STRIPE PAYMENT SECTION ============
    st.markdown("""
    <div style="max-width: 500px; margin: 30px auto; padding: 30px;
                background: linear-gradient(135deg, #1a3a2a 0%, #2a4a3a 100%);
                border-radius: 16px; border: 1px solid #3a5a4a; text-align: center;">
        <p style="color: #00c853; font-size: 18px; font-weight: 700; margin-bottom: 10px;">🔓 Private Early Access</p>
        <p style="color: #ccc; font-size: 14px; margin-bottom: 20px;">
            Private early access. <strong>$49.99 one-time</strong>. Refund available if not a fit.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Stripe Button
    st.markdown(
        f"""
        <div style="text-align: center; margin: 20px 0;">
            <a href="{STRIPE_LINK}" target="_blank">
                <button style="
                    background-color:#22c55e;
                    color:black;
                    padding:14px 32px;
                    border:none;
                    border-radius:8px;
                    font-size:17px;
                    font-weight:700;
                    cursor:pointer;
                ">
                    Unlock Early Access – $49.99
                </button>
            </a>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    st.markdown("---")
    
    # ============ PASSWORD ENTRY FOR PAID USERS ============
    st.markdown("""
    <div style="max-width: 400px; margin: 30px auto; text-align: center;">
        <p style="color: #888; font-size: 14px; margin-bottom: 15px;">
            Already paid? Enter your password below:
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
            Questions? aipublishingpro@gmail.com
        </p>
        """, unsafe_allow_html=True)
    
    st.stop()
