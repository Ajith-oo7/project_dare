import streamlit as st
import sqlite3
import pandas as pd
from database import (
    create_post, add_comment, get_db_path, send_message,
    mark_messages_as_read, add_trend, has_user_trended,
    create_user, authenticate_user, check_username_exists,
    create_story, create_challenge, submit_challenge
)
import os
from datetime import datetime

def show_home_page():
    st.markdown("""
        <style>
        .main {
            background-color: #1a1c1f;
            color: white;
        }
        </style>
    """, unsafe_allow_html=True)
    
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
                    st.image(story['media_path'], 
                            caption=story['username'],
                            width=100)
    
    st.divider()
    
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
                # Display media
                try:
                    if post['media_type'] == 'image':
                        st.image(post['video_path'], width=300)
                    else:
                        st.video(post['video_path'])
                except Exception as e:
                    st.error("Media not available")
                
                st.write(f"Posted by: {post['username']}")
                st.write(post['caption'])
                
                # Trend buttons
                trend_col1, trend_col2 = st.columns(2)
                with trend_col1:
                    if st.button("🔥", key=f"trend_{post['post_id']}"):
                        if not has_user_trended(post['post_id'], st.session_state.user_id):
                            add_trend(post['post_id'], st.session_state.user_id, True)
                            st.rerun()
                with trend_col2:
                    st.write(f"{post['trend_count']} trends")
                
                # Comments
                comments = pd.read_sql_query("""
                    SELECT c.*, u.username
                    FROM comments c
                    JOIN users u ON c.user_id = u.user_id
                    WHERE c.post_id = ?
                    ORDER BY c.created_date DESC
                """, conn, params=(post['post_id'],))
                
                for _, comment in comments.iterrows():
                    st.text(f"{comment['username']}: {comment['comment']}")
                
                # Add comment
                new_comment = st.text_input("Add comment", key=f"comment_{post['post_id']}")
                if st.button("Comment", key=f"send_{post['post_id']}"):
                    if new_comment.strip():
                        add_comment(post['post_id'], st.session_state.user_id, new_comment)
                        st.rerun()
    
    conn.close()

def show_search_page():
    st.title("Search")
    
    search_term = st.text_input("Search users or posts...")
    
    if search_term:
        conn = sqlite3.connect(get_db_path())
        
        # Search users
        users = pd.read_sql_query("""
            SELECT user_id, username, profile_pic
            FROM users 
            WHERE username LIKE ? OR email LIKE ?
        """, conn, params=(f"%{search_term}%", f"%{search_term}%"))
        
        # Search posts
        posts = pd.read_sql_query("""
            SELECT p.*, u.username
            FROM posts p
            JOIN users u ON p.user_id = u.user_id
            WHERE caption LIKE ? OR username LIKE ?
            AND u.is_private = 0
        """, conn, params=(f"%{search_term}%", f"%{search_term}%"))
        
        # Show results
        if not users.empty:
            st.subheader("Users")
            for _, user in users.iterrows():
                col1, col2 = st.columns([1, 4])
                with col1:
                    st.markdown("👤")
                with col2:
                    st.write(user['username'])
        
        if not posts.empty:
            st.subheader("Posts")
            for _, post in posts.iterrows():
                with st.container():
                    try:
                        if post['media_type'] == 'image':
                            st.image(post['video_path'], width=300)
                        else:
                            st.video(post['video_path'])
                    except:
                        st.error("Media not available")
                    st.write(f"Posted by: {post['username']}")
                    st.write(post['caption'])
        
        conn.close()

def show_add_post():
    st.title("Add Post")
    
    media_type = st.radio("Select media type:", ["Image", "Video"])
    uploaded_file = st.file_uploader(
        f"Upload {media_type}", 
        type=['png', 'jpg', 'jpeg'] if media_type == "Image" else ['mp4', 'mov']
    )
    
    if uploaded_file:
        caption = st.text_area("Caption")
        if st.button("Post"):
            # Save file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_extension = os.path.splitext(uploaded_file.name)[1]
            filename = f"{st.session_state.username}_{timestamp}{file_extension}"
            file_path = os.path.join("uploads", "posts", filename)
            
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            create_post(st.session_state.user_id, file_path, caption, media_type.lower())
            st.success("Post created!")
            st.rerun()

def show_stories_page():
    st.title("Stories")
    
    # Add create story button
    if st.button("Create New Story"):
        uploaded_file = st.file_uploader("Upload Story", type=['png', 'jpg', 'jpeg', 'mp4'])
        if uploaded_file:
            caption = st.text_input("Caption (optional)")
            if st.button("Share Story"):
                # Create directory if not exists
                os.makedirs("uploads/stories", exist_ok=True)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_extension = os.path.splitext(uploaded_file.name)[1]
                filename = f"{st.session_state.username}_{timestamp}{file_extension}"
                file_path = os.path.join("uploads", "stories", filename)
                
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                create_story(st.session_state.user_id, file_path, caption)
                st.success("Story shared!")
                st.rerun()

def show_messages_page():
    st.title("Messages")

    # Add a search bar to start new conversations
    new_message = st.text_input("Search user to message...")
    if new_message:
        conn = sqlite3.connect(get_db_path())
        users = pd.read_sql_query("""
            SELECT user_id, username FROM users 
            WHERE username LIKE ? AND user_id != ?
        """, conn, params=(f"%{new_message}%", st.session_state.user_id))
        
        for _, user in users.iterrows():
            if st.button(f"Message {user['username']}", key=f"new_msg_{user['user_id']}"):
                st.session_state.active_chat = user['user_id']
                st.session_state.chat_username = user['username']
                st.rerun()
        conn.close()

    # Show existing conversations in sidebar
    with st.sidebar:
        st.subheader("Recent Chats")
        conn = sqlite3.connect(get_db_path())
        conversations = pd.read_sql_query("""
            SELECT DISTINCT 
                CASE WHEN m.sender_id = ? THEN m.receiver_id ELSE m.sender_id END as other_user_id,
                u.username,
                COUNT(CASE WHEN m.is_read = 0 AND m.receiver_id = ? THEN 1 END) as unread_count,
                MAX(m.created_date) as last_message
            FROM messages m
            JOIN users u ON u.user_id = 
                CASE WHEN m.sender_id = ? THEN m.receiver_id ELSE m.sender_id END
            WHERE m.sender_id = ? OR m.receiver_id = ?
            GROUP BY other_user_id
            ORDER BY last_message DESC
        """, conn, params=(st.session_state.user_id,)*5)

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
    if 'active_chat' in st.session_state and st.session_state.active_chat:
        st.subheader(f"Chat with {st.session_state.chat_username}")
        
        # Message history
        messages = pd.read_sql_query("""
            SELECT m.*, u.username 
            FROM messages m
            JOIN users u ON m.sender_id = u.user_id
            WHERE (sender_id = ? AND receiver_id = ?)
            OR (sender_id = ? AND receiver_id = ?)
            ORDER BY m.created_date
        """, conn, params=(st.session_state.user_id, st.session_state.active_chat,
                         st.session_state.active_chat, st.session_state.user_id))
        
        # Show messages in a container
        chat_container = st.container()
        with chat_container:
            for _, msg in messages.iterrows():
                is_me = msg['sender_id'] == st.session_state.user_id
                st.markdown(
                    f"""<div style='text-align: {'right' if is_me else 'left'}'>
                        <small>{'You' if is_me else msg['username']}</small><br>
                        <div style='background: {'#007AFF' if is_me else '#E9E9EB'}; 
                                    color: {'white' if is_me else 'black'};
                                    padding: 10px; 
                                    border-radius: 15px; 
                                    display: inline-block;
                                    margin: 5px;'>
                            {msg['content']}
                        </div>
                    </div>""", 
                    unsafe_allow_html=True
                )

        # Message input
        col1, col2 = st.columns([4, 1])
        with col1:
            message = st.text_input("", placeholder="Type a message...", key="message_input")
        with col2:
            if st.button("Send", key="send_button"):
                if message.strip():
                    send_message(st.session_state.user_id, st.session_state.active_chat, message)
                    st.rerun()

    conn.close()

def show_challenges_page():
    st.title("Challenges")
    
    # Add create challenge option
    if st.button("Create Challenge"):
        title = st.text_input("Challenge Title")
        description = st.text_area("Challenge Description")
        reward_points = st.number_input("Reward Points", min_value=1)
        duration = st.number_input("Duration (days)", min_value=1)
        
        if st.button("Create"):
            create_challenge(
                st.session_state.user_id,
                title,
                description,
                reward_points,
                duration
            )
            st.success("Challenge created!")
            st.rerun()
    
    # Show active challenges
    conn = sqlite3.connect(get_db_path())
    challenges = pd.read_sql_query("""
        SELECT c.*, u.username, COUNT(s.submission_id) as submissions
        FROM challenges c
        JOIN users u ON c.creator_id = u.user_id
        LEFT JOIN challenge_submissions s ON c.challenge_id = s.challenge_id
        WHERE c.end_date > datetime('now')
        GROUP BY c.challenge_id
        ORDER BY c.created_date DESC
    """, conn)
    
    for _, challenge in challenges.iterrows():
        with st.container():
            st.subheader(challenge['title'])
            st.write(f"By: {challenge['username']}")
            st.write(challenge['description'])
            st.write(f"Reward: {challenge['reward_points']} points")
            st.write(f"Submissions: {challenge['submissions']}")
            
            if st.button("Submit Entry", key=f"submit_{challenge['challenge_id']}"):
                uploaded_file = st.file_uploader("Upload your submission", 
                                              type=['png', 'jpg', 'jpeg', 'mp4'])
                if uploaded_file:
                    caption = st.text_input("Add caption")
                    if st.button("Submit"):
                        # Save submission
                        os.makedirs("uploads/challenges", exist_ok=True)
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        file_extension = os.path.splitext(uploaded_file.name)[1]
                        filename = f"challenge_{challenge['challenge_id']}_{timestamp}{file_extension}"
                        file_path = os.path.join("uploads", "challenges", filename)
                        
                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        
                        submit_challenge(challenge['challenge_id'], 
                                      st.session_state.user_id,
                                      file_path, caption)
                        st.success("Entry submitted!")
                        st.rerun()
    
    conn.close()

def show_profile_page():
    st.title("Profile")
    
    conn = sqlite3.connect(get_db_path())
    user = pd.read_sql_query("""
        SELECT u.*, 
               COUNT(DISTINCT f1.follower_id) as followers,
               COUNT(DISTINCT f2.user_id) as following,
               COUNT(DISTINCT p.post_id) as posts
        FROM users u
        LEFT JOIN followers f1 ON u.user_id = f1.user_id
        LEFT JOIN followers f2 ON u.user_id = f2.follower_id
        LEFT JOIN posts p ON u.user_id = p.user_id
        WHERE u.user_id = ?
        GROUP BY u.user_id
    """, conn, params=(st.session_state.user_id,)).iloc[0]
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Posts", user['posts'])
    with col2:
        st.metric("Followers", user['followers'])
    with col3:
        st.metric("Following", user['following'])
    
    # Add settings
    if st.button("Settings"):
        is_private = st.checkbox("Private Account", value=user['is_private'])
        bio = st.text_area("Bio", value=user['bio'] if user['bio'] else "")
        if st.button("Save Changes"):
            c = conn.cursor()
            c.execute("""UPDATE users 
                        SET is_private = ?, bio = ?
                        WHERE user_id = ?""",
                     (is_private, bio, st.session_state.user_id))
            conn.commit()
            st.success("Profile updated!")
            st.rerun()
    
    conn.close() 