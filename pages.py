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
    st.title("Messages")
    
    # Initialize chat state
    if 'active_chat' not in st.session_state:
        st.session_state.active_chat = None
        st.session_state.chat_username = None

    # Add custom CSS for iOS-style messages
    st.markdown("""
        <style>
        .message-right {
            background-color: #007AFF;
            color: white;
            padding: 10px;
            border-radius: 15px;
            margin: 5px;
            text-align: right;
        }
        .message-left {
            background-color: #E9E9EB;
            color: black;
            padding: 10px;
            border-radius: 15px;
            margin: 5px;
            text-align: left;
        }
        </style>
    """, unsafe_allow_html=True)

    # Get conversations
    conn = sqlite3.connect(get_db_path())
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

    # Show conversations list in sidebar
    with st.sidebar:
        st.subheader("Chats")
        for _, conv in conversations.iterrows():
            if st.button(
                f"{conv['username']} {'🔵' if conv['unread_count'] > 0 else ''}", 
                key=f"chat_{conv['other_user_id']}"
            ):
                st.session_state.active_chat = conv['other_user_id']
                st.session_state.chat_username = conv['username']
                mark_messages_as_read(st.session_state.user_id, conv['other_user_id'])
                st.rerun()

    # Show active chat
    if st.session_state.active_chat:
        st.subheader(f"Chat with {st.session_state.chat_username}")
        
        # Get messages
        messages = pd.read_sql_query("""
            SELECT m.*, u.username 
            FROM messages m
            JOIN users u ON m.sender_id = u.user_id
            WHERE (sender_id = ? AND receiver_id = ?)
            OR (sender_id = ? AND receiver_id = ?)
            ORDER BY m.created_date
        """, conn, params=(st.session_state.user_id, st.session_state.active_chat,
                         st.session_state.active_chat, st.session_state.user_id))
        
        # Show messages
        for _, msg in messages.iterrows():
            is_me = msg['sender_id'] == st.session_state.user_id
            st.markdown(
                f"""<div class='message-{'right' if is_me else 'left'}'>
                    {msg['content']}
                </div>""", 
                unsafe_allow_html=True
            )

        # Message input
        col1, col2 = st.columns([4, 1])
        with col1:
            message = st.text_input("", placeholder="iMessage", key="message_input")
        with col2:
            if st.button("Send", key="send_button"):
                if message.strip():
                    send_message(st.session_state.user_id, st.session_state.active_chat, message)
                    st.rerun()

    conn.close() 