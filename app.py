import streamlit as st
from datetime import datetime
import pandas as pd
from PIL import Image
import os
import bcrypt
from streamlit_option_menu import option_menu
from streamlit_lottie import st_lottie
import requests
import json
from database import init_db, create_user, authenticate_user
from pages import show_home_page, show_search_page, show_add_post, show_stream_page, show_profile_page
from google.oauth2 import id_token
from google.auth.transport import requests
from google_auth_oauthlib.flow import Flow

# Configure Streamlit page
st.set_page_config(
    page_title="DareMe",
    page_icon="🎯",
    layout="wide"
)

# Add custom CSS
st.markdown("""
<style>
    /* Mobile-friendly styles */
    @media screen and (max-width: 768px) {
        .main {
            padding: 1rem;
        }
        
        .stButton>button {
            padding: 0.5rem;
            font-size: 14px;
        }
        
        /* Make images and videos responsive */
        img, video {
            width: 100% !important;
            height: auto !important;
        }
        
        /* Adjust column layouts for mobile */
        .row-widget.stHorizontal {
            flex-direction: column;
        }
        
        /* Make menu more touch-friendly */
        .stSelectbox, .stTextInput {
            min-height: 44px;
        }
    }

    /* Existing styles */
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
        background-color: #FF4B4B;
        color: white;
    }
    .dare-card {
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid #ddd;
        margin: 1rem 0;
    }
    .points-badge {
        background-color: #FF4B4B;
        color: white;
        padding: 0.5rem;
        border-radius: 20px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Security Functions
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

# Comment out or remove Google OAuth code
# GOOGLE_CLIENT_ID = st.secrets["GOOGLE_CLIENT_ID"]
# GOOGLE_CLIENT_SECRET = st.secrets["GOOGLE_CLIENT_SECRET"]

def init_google_auth():
    flow = Flow.from_client_secrets_file(
        'client_secrets.json',
        scopes=['openid', 'email', 'profile'],
        redirect_uri=st.secrets["OAUTH_REDIRECT_URI"]
    )
    return flow

def verify_google_token(token):
    try:
        idinfo = id_token.verify_oauth2_token(
            token, requests.Request(), GOOGLE_CLIENT_ID)
        return idinfo
    except ValueError:
        return None

# Main App with Enhanced UI
def main():
    if not os.path.exists("uploads"):
        os.makedirs("uploads")
    if 'user_id' not in st.session_state:
        show_login_page()
    else:
        show_main_app()

def show_login_page():
    st.title("🎯 DareMe")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        username = st.text_input("Username or Email", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login"):
            user_id = authenticate_user(username, password)
            if user_id:
                st.session_state.user_id = user_id
                st.session_state.username = username
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid credentials!")
    
    with tab2:
        new_username = st.text_input("Choose Username", key="reg_username")
        email = st.text_input("Email", key="reg_email")
        new_password = st.text_input("Choose Password", type="password", key="reg_password")
        confirm_password = st.text_input("Confirm Password", type="password")
        bio = st.text_area("Bio (optional)")
        
        if st.button("Register"):
            if new_password != confirm_password:
                st.error("Passwords don't match!")
            elif create_user(new_username, email, new_password, bio):
                st.success("Registration successful! Please login.")
            else:
                st.error("Username or email already exists!")

def show_main_app():
    # Add logout button in sidebar
    if st.sidebar.button("Logout"):
        # Clear session state
        for key in st.session_state.keys():
            del st.session_state[key]
        st.rerun()
        
    # Horizontal menu
    selected = option_menu(
        menu_title=None,
        options=["Home", "Search", "Add Post", "Stream", "Profile"],
        icons=["house", "search", "plus-circle", "collection-play", "person"],
        orientation="horizontal",
    )
    
    if selected == "Home":
        show_home_page()
    elif selected == "Search":
        show_search_page()
    elif selected == "Add Post":
        show_add_post()
    elif selected == "Stream":
        show_stream_page()
    elif selected == "Profile":
        show_profile_page()

# Add implementation for each page function...

if __name__ == "__main__":
    init_db()
    main() 