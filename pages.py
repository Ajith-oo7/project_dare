import streamlit as st
import sqlite3
import pandas as pd
from database import (
    create_post, add_comment, get_db_path, send_message,
    mark_messages_as_read
)
import os
from datetime import datetime

def show_home_page():
    st.title("Home")
    # Basic home page implementation
    pass

def show_messages_page():
    st.title("Messages")
    # Basic messages implementation
    pass

def show_profile_page():
    st.title("Profile")
    # Basic profile implementation
    pass 