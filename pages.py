import streamlit as st
import sqlite3
import pandas as pd
from database import create_post, add_comment, update_privacy, delete_post, toggle_archive_post, add_trend, has_user_trended
import os
import time
import tempfile

# Implementation of individual pages
def show_home_page():
    st.title("Home")
    
    conn = sqlite3.connect('app_collected_data.db')
    # Get posts with comments
    posts = pd.read_sql_query("""
        SELECT p.*, u.username, u.is_private,
               COUNT(DISTINCT t.user_id) as trend_count
        FROM posts p
        JOIN users u ON p.user_id = u.user_id
        LEFT JOIN trends t ON p.post_id = t.post_id
        WHERE u.is_private = 0 AND p.is_archived = 0
        GROUP BY p.post_id
        ORDER BY p.created_date DESC
    """, conn)
    
    for _, post in posts.iterrows():
        with st.container():
            col1, col2 = st.columns([3, 1])
            with col1:
                # Display media based on type
                if post['media_type'] == 'image':
                    st.image(post['video_path'], width=300)  # Smaller image size
                else:
                    st.video(post['video_path'])
                    
                st.write(f"Posted by: {post['username']}")
                st.write(post['caption'])
                
                # Trend buttons
                trend_col1, trend_col2 = st.columns(2)
                with trend_col1:
                    if not has_user_trended(post['post_id'], st.session_state.user_id):
                        if st.button("⬆️ Uptrend", key=f"up_{post['post_id']}"):
                            add_trend(post['post_id'], st.session_state.user_id, True)
                            st.rerun()
                with trend_col2:
                    if not has_user_trended(post['post_id'], st.session_state.user_id):
                        if st.button("⬇️ Lowtrend", key=f"down_{post['post_id']}"):
                            add_trend(post['post_id'], st.session_state.user_id, False)
                            st.rerun()
                
                # Show trend count
                st.write(f"Trend Level: {post['trend_level']}/10 ({post['trend_count']} votes)")
                
                # Show comments
                comments = pd.read_sql_query("""
                    SELECT c.*, u.username 
                    FROM comments c
                    JOIN users u ON c.user_id = u.user_id
                    WHERE c.post_id = ?
                    ORDER BY c.created_date DESC
                """, conn, params=(post['post_id'],))
                
                st.write("---")
                st.write("Comments:")
                for _, comment in comments.iterrows():
                    st.write(f"**{comment['username']}**: {comment['comment']}")
            
            with col2:
                # Add comment section
                comment = st.text_input("Add comment", key=f"comment_{post['post_id']}")
                if st.button("Post", key=f"post_{post['post_id']}"):
                    add_comment(post['post_id'], st.session_state.user_id, comment)
                    st.rerun()

def show_search_page():
    st.title("Search")
    search_term = st.text_input("Search users or captions...")
    
    if search_term:
        conn = sqlite3.connect('app_collected_data.db')
        results = pd.read_sql_query("""
            SELECT username, bio FROM users 
            WHERE username LIKE ? OR bio LIKE ?
            UNION
            SELECT p.caption, u.username 
            FROM posts p
            JOIN users u ON p.user_id = u.user_id
            WHERE p.caption LIKE ?
        """, conn, params=(f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"))
        
        st.write("Search Results:")
        st.dataframe(results)

def show_add_post():
    st.title("Create New Post")
    
    # Add tabs for different media types
    media_type = st.radio("Select media type:", ["Image", "Video"])
    
    if media_type == "Image":
        uploaded_file = st.file_uploader("Upload Image", 
                                       type=['png', 'jpg', 'jpeg', 'gif'])
        if uploaded_file:
            # Smaller preview
            st.image(uploaded_file, caption="Preview", width=200)
        
        caption = st.text_area("Caption")
        
    else:  # Video
        uploaded_file = st.file_uploader("Upload Video", 
                                       type=['mp4', 'mov', 'avi'])
        if uploaded_file:
            st.video(uploaded_file)
        caption = st.text_area("Caption")
    
    # Add hashtags and location
    hashtags = st.text_input("Add hashtags (separate with spaces)", "")
    location = st.text_input("Add location (optional)")
    
    # Submit button with styling
    submit_button = st.button("Submit Post", 
                            type="primary",
                            use_container_width=True)
    
    if uploaded_file and submit_button:
        try:
            # Create uploads directory if it doesn't exist
            os.makedirs("uploads", exist_ok=True)
            
            # Save file
            file_path = f"uploads/{uploaded_file.name}"
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Prepare caption with hashtags and location
            full_caption = caption
            if hashtags:
                full_caption += f"\n\nHashtags: {hashtags}"
            if location:
                full_caption += f"\nLocation: {location}"
            
            # Create post
            create_post(st.session_state.user_id, file_path, full_caption)
            st.success("Post created successfully!")
            
            # Wait 2 seconds to show success message
            time.sleep(2)
            
            # Redirect to home
            st.session_state.redirect_to_home = True
            st.rerun()
            
        except Exception as e:
            st.error(f"Error creating post: {str(e)}")

    # Handle redirect
    if 'redirect_to_home' in st.session_state and st.session_state.redirect_to_home:
        st.session_state.redirect_to_home = False
        show_home_page()

def show_stream_page():
    st.title("Discover")
    
    conn = sqlite3.connect('app_collected_data.db')
    random_posts = pd.read_sql_query("""
        SELECT p.*, u.username 
        FROM posts p
        JOIN users u ON p.user_id = u.user_id
        WHERE u.is_private = 0
        ORDER BY RANDOM()
        LIMIT 5
    """, conn)
    
    for _, post in random_posts.iterrows():
        # Display media based on type
        if post['media_type'] == 'image':
            st.image(post['video_path'], width=300)  # Smaller image size
        else:
            st.video(post['video_path'])
            
        st.write(f"By: {post['username']}")
        st.write(post['caption'])
        st.write(f"Trend Level: {post['trend_level']}/10")
        st.write("---")  # Add separator between posts

def show_profile_page():
    st.title("Profile")
    
    # Get user data
    conn = sqlite3.connect('app_collected_data.db')
    user_data = pd.read_sql_query("""
        SELECT * FROM users WHERE user_id = ?
    """, conn, params=(st.session_state.user_id,))
    
    # Profile header
    col1, col2 = st.columns([1, 3])
    with col1:
        st.markdown("<h1 style='font-size: 48px; text-align: center;'>👤</h1>", unsafe_allow_html=True)
    
    with col2:
        st.write(f"Username: {user_data.iloc[0]['username']}")
        st.write(f"Bio: {user_data.iloc[0]['bio']}")
    
    # Settings
    with st.expander("Settings"):
        is_private = st.toggle("Private Account", 
                             value=user_data.iloc[0]['is_private'])
        if st.button("Save Settings"):
            update_privacy(st.session_state.user_id, is_private)
            st.success("Settings updated!")
    
    # Add tabs for normal and archived posts
    tab1, tab2 = st.tabs(["Posts", "Archived"])
    
    with tab1:
        st.subheader("Your Posts")
        posts = pd.read_sql_query("""
            SELECT * FROM posts 
            WHERE user_id = ? AND is_archived = 0
            ORDER BY created_date DESC
        """, conn, params=(st.session_state.user_id,))
        
        show_posts(posts, archived=False)
    
    with tab2:
        st.subheader("Archived Posts")
        archived_posts = pd.read_sql_query("""
            SELECT * FROM posts 
            WHERE user_id = ? AND is_archived = 1
            ORDER BY created_date DESC
        """, conn, params=(st.session_state.user_id,))
        
        show_posts(archived_posts, archived=True)

def show_posts(posts, archived=False):
    for _, post in posts.iterrows():
        with st.container():
            col1, col2 = st.columns([4, 1])
            with col1:
                if post['media_type'] == 'image':
                    if os.path.exists(post['video_path']):
                        st.image(post['video_path'])
                    else:
                        st.warning("Image not available")
                else:
                    if os.path.exists(post['video_path']):
                        st.video(post['video_path'])
                    else:
                        st.warning("Video not available")
                st.write(post['caption'])
                st.write(f"Trend Level: {post['trend_level']}/10")
            
            with col2:
                # Archive/Unarchive button
                if archived:
                    if st.button("Unarchive", key=f"unarchive_{post['post_id']}"):
                        toggle_archive_post(post['post_id'], False)
                        st.success("Post unarchived!")
                        st.rerun()
                else:
                    if st.button("Archive", key=f"archive_{post['post_id']}"):
                        toggle_archive_post(post['post_id'], True)
                        st.success("Post archived!")
                        st.rerun()
                
                # Delete button
                if st.button("Delete", key=f"delete_{post['post_id']}"):
                    delete_post(post['post_id'])
                    st.success("Post deleted!")
                    st.rerun()

def get_upload_path():
    return tempfile.gettempdir()

# Implement other page functions similarly... 