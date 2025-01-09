import streamlit as st
import pandas as pd
from database import get_db_path
import sqlite3
import plotly.express as px

def show_admin_dashboard():
    st.title("Admin Dashboard")
    
    tab1, tab2, tab3 = st.tabs(["User Management", "Content Moderation", "Analytics"])
    
    with tab1:
        show_user_management()
    
    with tab2:
        show_content_moderation()
        
    with tab3:
        show_analytics()

def show_user_management():
    conn = sqlite3.connect(get_db_path())
    users = pd.read_sql_query("SELECT * FROM users", conn)
    
    st.subheader("User Management")
    for _, user in users.iterrows():
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"Username: {user['username']}")
            st.write(f"Email: {user['email']}")
        with col2:
            if st.button("Suspend", key=f"suspend_{user['user_id']}"):
                # Add suspension logic
                st.success(f"User {user['username']} suspended")

def show_content_moderation():
    conn = sqlite3.connect(get_db_path())
    posts = pd.read_sql_query("""
        SELECT p.*, u.username
        FROM posts p
        JOIN users u ON p.user_id = u.user_id
        ORDER BY p.created_date DESC
    """, conn)
    
    st.subheader("Content Moderation")
    for _, post in posts.iterrows():
        with st.container():
            st.write(f"Posted by: {post['username']}")
            if post['media_type'] == 'image':
                st.image(post['video_path'])
            else:
                st.video(post['video_path'])
            if st.button("Remove", key=f"remove_{post['post_id']}"):
                # Add removal logic
                st.success("Post removed")

def show_analytics():
    conn = sqlite3.connect(get_db_path())
    
    # User growth
    users = pd.read_sql_query("""
        SELECT DATE(join_date) as date, COUNT(*) as count
        FROM users
        GROUP BY DATE(join_date)
    """, conn)
    
    st.subheader("User Growth")
    fig = px.line(users, x='date', y='count', title='Daily User Signups')
    st.plotly_chart(fig)
    
    # Engagement metrics
    engagement = pd.read_sql_query("""
        SELECT DATE(created_date) as date,
               COUNT(*) as posts,
               COUNT(DISTINCT user_id) as active_users
        FROM posts
        GROUP BY DATE(created_date)
    """, conn)
    
    st.subheader("Engagement Metrics")
    fig2 = px.line(engagement, x='date', y=['posts', 'active_users'], 
                   title='Daily Posts and Active Users')
    st.plotly_chart(fig2) 