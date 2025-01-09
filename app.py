import streamlit as st
from datetime import datetime
import pandas as pd
from PIL import Image
import os
import bcrypt
from streamlit_option_menu import option_menu
from database import init_db, create_user, authenticate_user, check_username_exists

# Import only essential functions first
from pages import (
    show_home_page,
    show_messages_page,
    show_profile_page
)

# Configure Streamlit page
st.set_page_config(
    page_title="DareMe",
    page_icon="🎯",
    layout="wide"
)

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
        
        if st.button("Register"):
            if new_password != confirm_password:
                st.error("Passwords don't match!")
            elif create_user(new_username, email, new_password):
                st.success("Registration successful! Please login.")
            else:
                st.error("Username or email already exists!")

def show_main_app():
    # Simplified menu first
    selected = option_menu(
        menu_title=None,
        options=["Home", "Messages", "Profile"],
        icons=["house", "chat", "person"],
        orientation="horizontal",
    )
    
    if selected == "Home":
        show_home_page()
    elif selected == "Messages":
        show_messages_page()
    elif selected == "Profile":
        show_profile_page()

if __name__ == "__main__":
    init_db()
    main() 