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
import tempfile
from datetime import datetime
from config import Config
from xmpp_handler import XMPPManager

# Initialize XMPP manager
xmpp_manager = XMPPManager()

# Implementation of individual pages
def show_home_page():
    st.title("Home")
    
    # Show active stories
    conn = sqlite3.connect(get_db_path())
    stories = pd.read_sql_query("""
        SELECT s.*, u.username
        FROM stories s
        JOIN users u ON s.user_id = u.user_id
        WHERE s.created_date >= datetime('now', '-24 hours')
        ORDER BY s.created_date DESC
    """, conn)
    
    if not stories.empty:
        st.subheader("Stories")
        story_cols = st.columns(min(4, len(stories)))
        for idx, (_, story) in enumerate(stories.iterrows()):
            with story_cols[idx % 4]:
                if os.path.exists(story['media_path']):
                    if st.button(story['username'], key=f"story_{story['story_id']}"):
                        show_story(story)
    
    st.divider()
    
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
                try:
                    if post['media_type'] == 'image':
                        if os.path.exists(post['video_path']):
                            with open(post['video_path'], 'rb') as f:
                                image_bytes = f.read()
                            st.image(image_bytes, width=300)
                        else:
                            st.warning("Image not available")
                    else:
                        if os.path.exists(post['video_path']):
                            st.video(post['video_path'])
                        else:
                            st.warning("Video not available")
                except Exception as e:
                    st.error(f"Error displaying media: {str(e)}")
                    
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
    search_term = st.text_input("Search users or hashtags...")
    
    if search_term:
        conn = sqlite3.connect(get_db_path())
        users = pd.read_sql_query("""
            SELECT u.user_id, u.username, u.bio, u.profile_pic,
                   COUNT(p.post_id) as post_count
            FROM users u
            LEFT JOIN posts p ON u.user_id = p.user_id
            WHERE u.username LIKE ? OR u.bio LIKE ?
            GROUP BY u.user_id
        """, conn, params=(f"%{search_term}%", f"%{search_term}%"))
        
        for _, user in users.iterrows():
            with st.container():
                col1, col2 = st.columns([1, 4])
                with col1:
                    if user['profile_pic']:
                        st.image(user['profile_pic'], width=50)
                    else:
                        st.markdown("👤")
                with col2:
                    if st.button(f"@{user['username']}", key=f"user_{user['user_id']}"):
                        show_user_profile(user['user_id'])

def show_user_profile(user_id):
    conn = sqlite3.connect(get_db_path())
    user = pd.read_sql_query("SELECT * FROM users WHERE user_id = ?", 
                            conn, params=(user_id,)).iloc[0]
    
    st.title(f"@{user['username']}")
    st.write(user['bio'])
    
    posts = pd.read_sql_query("""
        SELECT * FROM posts 
        WHERE user_id = ? AND is_archived = 0
        ORDER BY created_date DESC
    """, conn, params=(user_id,))
    
    for _, post in posts.iterrows():
        show_post(post)

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
            # Use Config paths
            upload_dir = Config.UPLOAD_PATHS['posts']
            os.makedirs(upload_dir, exist_ok=True)
            
            # Generate unique filename with username prefix
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            username = st.session_state.username
            file_extension = os.path.splitext(uploaded_file.name)[1]
            unique_filename = f"{username}_{timestamp}{file_extension}"
            
            # Create full file path
            file_path = os.path.join(upload_dir, unique_filename)
            
            # Save file
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
            
        except OSError as e:
            st.error(f"Error saving file: {str(e)}")
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

def show_messages_page():
    st.title("Messages")
    
    # Initialize chat state if not exists
    if 'active_chat' not in st.session_state:
        st.session_state.active_chat = None
        st.session_state.chat_username = None
        st.session_state.messages = []

    # Add search bar for users
    search_user = st.text_input("Search users to message", key="message_search")
    
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

    # Chat interface
    chat_area, message_area = st.container(), st.container()

    # Show conversations in sidebar-like layout
    with st.sidebar:
        st.subheader("Conversations")
        for _, conv in conversations.iterrows():
            col1, col2 = st.columns([1, 4])
            with col1:
                st.markdown("👤")
            with col2:
                if st.button(
                    f"{conv['username']} {'🔴' if conv['unread_count'] > 0 else ''}", 
                    key=f"chat_{conv['other_user_id']}"
                ):
                    st.session_state.active_chat = conv['other_user_id']
                    st.session_state.chat_username = conv['username']
                    mark_messages_as_read(st.session_state.user_id, conv['other_user_id'])
                    st.rerun()

    # Show active chat
    if st.session_state.active_chat:
        with chat_area:
            st.subheader(f"Chat with {st.session_state.chat_username}")
            
            # Get messages
            messages = pd.read_sql_query("""
                SELECT m.*, u.username 
                FROM messages m
                JOIN users u ON m.sender_id = u.user_id
                WHERE (sender_id = ? AND receiver_id = ?)
                OR (sender_id = ? AND receiver_id = ?)
                ORDER BY m.created_date DESC
                LIMIT 50
            """, conn, params=(st.session_state.user_id, st.session_state.active_chat,
                             st.session_state.active_chat, st.session_state.user_id))
            
            # Show messages
            for _, msg in messages.iloc[::-1].iterrows():
                is_me = msg['sender_id'] == st.session_state.user_id
                st.markdown(
                    f"""<div style='text-align: {'right' if is_me else 'left'}'>
                        <small>{msg['username']}</small><br>
                        <div style='background: {'#DCF8C6' if is_me else '#E8E8E8'}; 
                                    display: inline-block; padding: 10px; 
                                    border-radius: 10px; margin: 5px;
                                    max-width: 70%;'>
                            {msg['content']}
                        </div>
                    </div>""", 
                    unsafe_allow_html=True
                )

        # Message input at bottom
        with message_area:
            col1, col2 = st.columns([4, 1])
            with col1:
                message = st.text_input("Message", key="message_input")
            with col2:
                if st.button("Send", key="send_button"):
                    if message.strip():
                        send_message(st.session_state.user_id, st.session_state.active_chat, message)
                        st.rerun()

    conn.close()

    # Auto-refresh
    if st.session_state.active_chat:
        time.sleep(1)
        st.rerun()

def show_stories_page():
    st.title("Stories")
    
    # Show user's active stories
    conn = sqlite3.connect(get_db_path())
    my_stories = pd.read_sql_query("""
        SELECT * FROM stories
        WHERE user_id = ?
        AND created_date >= datetime('now', '-24 hours')
        ORDER BY created_date DESC
    """, conn, params=(st.session_state.user_id,))
    
    if not my_stories.empty:
        st.subheader("Your Active Stories")
        for _, story in my_stories.iterrows():
            if os.path.exists(story['media_path']):
                st.image(story['media_path'], caption=story['caption'])
    
    st.divider()
    # Upload new story
    st.subheader("Create New Story")
    uploaded_file = st.file_uploader("Upload Story", 
                                   type=['png', 'jpg', 'jpeg', 'gif', 'mp4'])
    caption = st.text_input("Add caption (optional)")
    
    if uploaded_file and st.button("Share Story"):
        try:
            # Use Config paths
            upload_dir = Config.UPLOAD_PATHS['stories']
            os.makedirs(upload_dir, exist_ok=True)
            
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            username = st.session_state.username
            file_extension = os.path.splitext(uploaded_file.name)[1]
            unique_filename = f"{username}_{timestamp}{file_extension}"
            
            file_path = os.path.join(upload_dir, unique_filename)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            create_story(st.session_state.user_id, file_path, caption)
            st.success("Story shared!")
            st.rerun()
        except Exception as e:
            st.error(f"Error sharing story: {str(e)}")

def show_challenges_page():
    st.title("Challenges")
    
    # Create new challenge
    with st.expander("Create New Challenge"):
        title = st.text_input("Challenge Title")
        description = st.text_area("Challenge Description")
        reward_points = st.number_input("Reward Points", min_value=1, value=10)
        duration = st.number_input("Duration (days)", min_value=1, value=7)
        
        if st.button("Create Challenge"):
            create_challenge(st.session_state.user_id, title, description, 
                           reward_points, duration)
            st.success("Challenge created!")
    
    # Show active challenges
    st.subheader("Active Challenges")
    conn = sqlite3.connect(get_db_path())
    challenges = pd.read_sql_query("""
        SELECT c.*, u.username, 
               COUNT(s.submission_id) as submission_count
        FROM challenges c
        JOIN users u ON c.creator_id = u.user_id
        LEFT JOIN challenge_submissions s ON c.challenge_id = s.challenge_id
        WHERE c.status = 'active'
        GROUP BY c.challenge_id
        ORDER BY c.created_date DESC
    """, conn)
    
    for _, challenge in challenges.iterrows():
        with st.container():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**{challenge['title']}**")
                st.write(challenge['description'])
                st.write(f"Created by: {challenge['username']}")
                st.write(f"Reward: {challenge['reward_points']} points")
            with col2:
                if st.button("Submit", key=f"submit_{challenge['challenge_id']}"):
                    st.session_state.active_challenge = challenge['challenge_id']
                    st.rerun()

def show_post(post, show_actions=True):
    with st.container():
        # ... existing post display code ...
        
        if show_actions:
            col1, col2, col3 = st.columns([1, 1, 1])
            with col3:
                if st.button("⚠️ Report", key=f"report_{post['post_id']}"):
                    reason = st.text_area("Why are you reporting this post?")
                    if st.button("Submit Report"):
                        report_content(st.session_state.user_id, 
                                    'post', 
                                    post['post_id'], 
                                    reason)
                        st.success("Report submitted")

def show_story(story):
    story_container = st.empty()
    with story_container.container():
        if os.path.exists(story['media_path']):
            st.image(story['media_path'], caption=story['caption'])
    time.sleep(5)  # Show for 5 seconds
    story_container.empty()

# Implement other page functions similarly... 