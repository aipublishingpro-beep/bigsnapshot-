import streamlit as st
import requests

st.set_page_config(page_title="BigSnapshot", page_icon="📊", layout="wide")

WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbzXhJVMpddiC63nLx2NDdwBAz8zTAktK0RvfcUVFs0yWDGeWJX-VbM3rfXZWyoBZYDcVQ/exec"

def check_auth():
    return st.session_state.get("authenticated", False)

def set_auth():
    st.session_state["authenticated"] = True

# Email gate
if not check_auth():
    st.title("📊 Welcome to BigSnapshot")
    st.subheader("Free Prediction Market Edge Finders")
    st.write("Enter your email to access all tools:")
    
    email = st.text_input("Your Email", placeholder="you@example.com")
    
    if st.button("Access Free Tools", type="primary"):
        if email and "@" in email:
            try:
                requests.post(WEBHOOK_URL, json={"email": email}, timeout=10)
            except:
                pass  # Still let them in even if webhook fails
            set_auth()
            st.rerun()
        else:
            st.error("Please enter a valid email address.")
    
    st.stop()

# Main content (only shows after email entry)
st.title("📊 BigSnapshot Edge Finders")
st.success("Welcome! Choose a tool from the sidebar.")

st.markdown("### Available Tools")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("#### 🏀 NBA")
    st.write("Player props & game predictions")
    
with col2:
    st.markdown("#### 🏈 NFL")
    st.write("Game spreads & totals analysis")
    
with col3:
    st.markdown("#### 🏒 NHL")
    st.write("Puck line & goal predictions")

st.markdown("---")
st.caption("© 2026 BigSnapshot. All rights reserved.")
