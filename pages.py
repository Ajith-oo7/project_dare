import streamlit as st
import sqlite3
import pandas as pd
from database import (
    create_post, add_comment, update_privacy, delete_post, 
    toggle_archive_post, add_trend, has_user_trended, create_story, 
    create_challenge, report_content, get_db_path, send_message,
    mark_messages_as_read
)
import os
import time
from datetime import datetime
from config import Config

# Add these imports if needed
import plotly.express as px
from PIL import Image
import io 

def show_messages_page():
    # ... existing styles ...

    # Use get_db_path() for database connections
    conn = sqlite3.connect(get_db_path())
    try:
        conversations = pd.read_sql_query("""
            SELECT DISTINCT 
                CASE 
                    WHEN m.sender_id = ? THEN m.receiver_id
                    ELSE m.sender_id 
                END as other_user_id,
                u.username,
                u.profile_pic,
                MAX(m.created_date) as last_message_date,
                SUM(CASE WHEN m.is_read = 0 AND m.receiver_id = ? THEN 1 ELSE 0 END) as unread_count
            FROM messages m
            JOIN users u ON u.user_id = 
                CASE 
                    WHEN m.sender_id = ? THEN m.receiver_id
                    ELSE m.sender_id 
                END
            WHERE m.sender_id = ? OR m.receiver_id = ?
            GROUP BY other_user_id
            ORDER BY last_message_date DESC
        """, conn, params=(st.session_state.user_id,)*5)
        
        # Rest of your code...
        
    finally:
        conn.close() 