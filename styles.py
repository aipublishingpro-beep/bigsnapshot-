import streamlit as st

def apply_styles():
    st.markdown("""
    <style>
    .stLinkButton > a {background-color: #00aa00 !important;border-color: #00aa00 !important;color: white !important;}
    .stLinkButton > a:hover {background-color: #00cc00 !important;border-color: #00cc00 !important;}
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
        overflow-x: hidden !important;
        max-width: 100vw !important;
    }
    div[data-testid="stMarkdownContainer"] > div {
        overflow-x: auto !important;
        max-width: 100% !important;
    }
    </style>
    """, unsafe_allow_html=True)
