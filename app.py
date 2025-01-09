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

# Rest of your app.py code...

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

# Add implementation for each page function...

if __name__ == "__main__":
    init_db()
    main() 