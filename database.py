import sqlite3
from datetime import datetime, timedelta
import bcrypt
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()  # Load environment variables

def get_db_path():
    return os.getenv('DB_PATH', 'app_collected_data.db')

def init_db():
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY,
                  username TEXT UNIQUE,
                  email TEXT UNIQUE,
                  password_hash BLOB,
                  bio TEXT,
                  profile_pic TEXT,
                  is_private BOOLEAN DEFAULT 0,
                  join_date TEXT,
                  oauth_provider TEXT,
                  oauth_id TEXT)''')
                  
    c.execute('''CREATE TABLE IF NOT EXISTS posts
                 (post_id INTEGER PRIMARY KEY,
                  user_id INTEGER,
                  video_path TEXT,
                  caption TEXT,
                  created_date TEXT,
                  trend_level INTEGER DEFAULT 1,
                  views INTEGER DEFAULT 0,
                  media_type TEXT DEFAULT 'video',
                  is_archived BOOLEAN DEFAULT 0,
                  FOREIGN KEY (user_id) REFERENCES users(user_id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS comments
                 (comment_id INTEGER PRIMARY KEY,
                  post_id INTEGER,
                  user_id INTEGER,
                  comment TEXT,
                  created_date TEXT,
                  FOREIGN KEY (post_id) REFERENCES posts(post_id),
                  FOREIGN KEY (user_id) REFERENCES users(user_id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS trends
                 (trend_id INTEGER PRIMARY KEY,
                  post_id INTEGER,
                  user_id INTEGER,
                  is_uptrend BOOLEAN,
                  created_date TEXT,
                  FOREIGN KEY (post_id) REFERENCES posts(post_id),
                  FOREIGN KEY (user_id) REFERENCES users(user_id),
                  UNIQUE(post_id, user_id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS followers
                 (id INTEGER PRIMARY KEY,
                  user_id INTEGER,
                  follower_id INTEGER,
                  created_date TEXT,
                  FOREIGN KEY (user_id) REFERENCES users(user_id),
                  FOREIGN KEY (follower_id) REFERENCES users(user_id),
                  UNIQUE(user_id, follower_id))''')
                  
    c.execute('''CREATE TABLE IF NOT EXISTS notifications
                 (id INTEGER PRIMARY KEY,
                  user_id INTEGER,
                  type TEXT,
                  content TEXT,
                  is_read BOOLEAN DEFAULT 0,
                  created_date TEXT,
                  FOREIGN KEY (user_id) REFERENCES users(user_id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (message_id INTEGER PRIMARY KEY,
                  sender_id INTEGER,
                  receiver_id INTEGER,
                  content TEXT,
                  media_path TEXT,
                  is_read BOOLEAN DEFAULT 0,
                  created_date TEXT,
                  FOREIGN KEY (sender_id) REFERENCES users(user_id),
                  FOREIGN KEY (receiver_id) REFERENCES users(user_id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS stories
                 (story_id INTEGER PRIMARY KEY,
                  user_id INTEGER,
                  media_path TEXT,
                  caption TEXT,
                  created_date TEXT,
                  expires_date TEXT,
                  FOREIGN KEY (user_id) REFERENCES users(user_id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS story_views
                 (view_id INTEGER PRIMARY KEY,
                  story_id INTEGER,
                  viewer_id INTEGER,
                  view_date TEXT,
                  FOREIGN KEY (story_id) REFERENCES stories(story_id),
                  FOREIGN KEY (viewer_id) REFERENCES users(user_id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS saved_posts
                 (save_id INTEGER PRIMARY KEY,
                  user_id INTEGER,
                  post_id INTEGER,
                  created_date TEXT,
                  FOREIGN KEY (user_id) REFERENCES users(user_id),
                  FOREIGN KEY (post_id) REFERENCES posts(post_id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS challenges
                 (challenge_id INTEGER PRIMARY KEY,
                  creator_id INTEGER,
                  title TEXT,
                  description TEXT,
                  reward_points INTEGER,
                  created_date TEXT,
                  end_date TEXT,
                  status TEXT,
                  FOREIGN KEY (creator_id) REFERENCES users(user_id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS challenge_submissions
                 (submission_id INTEGER PRIMARY KEY,
                  challenge_id INTEGER,
                  user_id INTEGER,
                  media_path TEXT,
                  caption TEXT,
                  created_date TEXT,
                  votes INTEGER DEFAULT 0,
                  FOREIGN KEY (challenge_id) REFERENCES challenges(challenge_id),
                  FOREIGN KEY (user_id) REFERENCES users(user_id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS reports
                 (report_id INTEGER PRIMARY KEY,
                  reporter_id INTEGER,
                  content_type TEXT,
                  content_id INTEGER,
                  reason TEXT,
                  status TEXT,
                  created_date TEXT,
                  FOREIGN KEY (reporter_id) REFERENCES users(user_id))''')
    
    conn.commit()
    conn.close()

def update_privacy(user_id, is_private):
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    c.execute("UPDATE users SET is_private = ? WHERE user_id = ?", 
             (is_private, user_id))
    conn.commit()
    conn.close()

def create_post(user_id, media_path, caption):
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    
    # Determine media type from file extension
    media_type = 'image' if media_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')) else 'video'
    
    c.execute("""INSERT INTO posts 
                 (user_id, video_path, caption, created_date, media_type)
                 VALUES (?, ?, ?, ?, ?)""",
              (user_id, media_path, caption,
               datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
               media_type))
    conn.commit()
    conn.close()

def add_comment(post_id, user_id, comment):
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    c.execute("""INSERT INTO comments 
                 (post_id, user_id, comment, created_date)
                 VALUES (?, ?, ?, ?)""",
              (post_id, user_id, comment,
               datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def create_user(username, email, password=None, bio="", oauth_provider=None, oauth_id=None):
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    try:
        if password:
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        else:
            password_hash = None
            
        c.execute("""INSERT INTO users 
                    (username, email, password_hash, bio, is_private, join_date, 
                     oauth_provider, oauth_id) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                 (username, email, password_hash, bio, False, 
                  datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                  oauth_provider, oauth_id))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def authenticate_user(username, password):
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    c.execute("SELECT user_id, password_hash FROM users WHERE username = ?", (username,))
    result = c.fetchone()
    conn.close()
    
    if result and bcrypt.checkpw(password.encode('utf-8'), result[1]):
        return result[0]
    return None 

def delete_post(post_id):
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    
    try:
        # Get file path before deleting
        c.execute("SELECT video_path FROM posts WHERE post_id = ?", (post_id,))
        file_path = c.fetchone()[0]
        
        # Delete post
        c.execute("DELETE FROM posts WHERE post_id = ?", (post_id,))
        
        # Delete associated comments
        c.execute("DELETE FROM comments WHERE post_id = ?", (post_id,))
        
        conn.commit()
        
        # Delete file if it exists
        if os.path.exists(file_path):
            os.remove(file_path)
            
    except Exception as e:
        print(f"Error deleting post: {str(e)}")
    finally:
        conn.close()

def toggle_archive_post(post_id, archive=True):
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    c.execute("UPDATE posts SET is_archived = ? WHERE post_id = ?", 
             (archive, post_id))
    conn.commit()
    conn.close() 

def has_user_trended(post_id, user_id):
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    c.execute("""SELECT 1 FROM trends 
                 WHERE post_id = ? AND user_id = ?
                 AND created_date >= datetime('now', '-24 hours')""", 
             (post_id, user_id))
    result = c.fetchone() is not None
    conn.close()
    return result

def add_trend(post_id, user_id, is_uptrend):
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    try:
        # Add the trend vote
        c.execute("""INSERT INTO trends 
                     (post_id, user_id, is_uptrend, created_date)
                     VALUES (?, ?, ?, ?)""",
                 (post_id, user_id, is_uptrend,
                  datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        
        # Get trend counts
        c.execute("""SELECT 
                     COUNT(CASE WHEN is_uptrend THEN 1 END) as upvotes,
                     COUNT(*) as total_votes
                     FROM trends
                     WHERE post_id = ?""",
                 (post_id,))
        
        upvotes, total_votes = c.fetchone()
        # Calculate trend level (0-10 scale)
        trend_level = int((upvotes * 10.0) / total_votes) if total_votes > 0 else 1
        
        # Update post trend level
        c.execute("UPDATE posts SET trend_level = ? WHERE post_id = ?",
                 (trend_level, post_id))
        
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # User already voted
    finally:
        conn.close() 

def check_username_exists(username):
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    c.execute("SELECT 1 FROM users WHERE username = ?", (username,))
    exists = c.fetchone() is not None
    conn.close()
    return exists 

def add_follower(user_id, follower_id):
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    try:
        c.execute("""INSERT INTO followers 
                    (user_id, follower_id, created_date) 
                    VALUES (?, ?, ?)""",
                 (user_id, follower_id, 
                  datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_user_analytics(user_id):
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    
    # Get post stats
    c.execute("""SELECT 
                 COUNT(*) as post_count,
                 SUM(views) as total_views,
                 AVG(trend_level) as avg_trend
                 FROM posts 
                 WHERE user_id = ?""", (user_id,))
    stats = c.fetchone()
    
    # Get follower count
    c.execute("""SELECT COUNT(*) 
                 FROM followers 
                 WHERE user_id = ?""", (user_id,))
    followers = c.fetchone()[0]
    
    conn.close()
    return {
        'post_count': stats[0],
        'total_views': stats[1],
        'avg_trend': stats[2],
        'followers': followers
    } 

def send_message(sender_id, receiver_id, content, media_path=None):
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    try:
        c.execute("""INSERT INTO messages 
                     (sender_id, receiver_id, content, media_path, is_read, created_date)
                     VALUES (?, ?, ?, ?, ?, ?)""",
                  (sender_id, receiver_id, content, media_path, 0,
                   datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error sending message: {str(e)}")
        return False
    finally:
        conn.close()

def create_story(user_id, media_path, caption=None):
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    now = datetime.now()
    expires = now + timedelta(hours=24)
    
    c.execute("""INSERT INTO stories 
                 (user_id, media_path, caption, created_date, expires_date)
                 VALUES (?, ?, ?, ?, ?)""",
              (user_id, media_path, caption,
               now.strftime("%Y-%m-%d %H:%M:%S"),
               expires.strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def save_post(user_id, post_id):
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    try:
        c.execute("""INSERT INTO saved_posts 
                     (user_id, post_id, created_date)
                     VALUES (?, ?, ?)""",
                  (user_id, post_id,
                   datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close() 

def create_challenge(creator_id, title, description, reward_points, duration_days):
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    now = datetime.now()
    ends = now + timedelta(days=duration_days)
    
    c.execute("""INSERT INTO challenges 
                 (creator_id, title, description, reward_points, 
                  created_date, end_date, status)
                 VALUES (?, ?, ?, ?, ?, ?, ?)""",
              (creator_id, title, description, reward_points,
               now.strftime("%Y-%m-%d %H:%M:%S"),
               ends.strftime("%Y-%m-%d %H:%M:%S"),
               'active'))
    conn.commit()
    conn.close()

def submit_challenge(challenge_id, user_id, media_path, caption):
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    
    c.execute("""INSERT INTO challenge_submissions 
                 (challenge_id, user_id, media_path, caption, created_date)
                 VALUES (?, ?, ?, ?, ?)""",
              (challenge_id, user_id, media_path, caption,
               datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close() 

def report_content(reporter_id, content_type, content_id, reason):
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    
    c.execute("""INSERT INTO reports 
                 (reporter_id, content_type, content_id, reason, status, created_date)
                 VALUES (?, ?, ?, ?, ?, ?)""",
              (reporter_id, content_type, content_id, reason, 'pending',
               datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close() 

def mark_messages_as_read(user_id, sender_id):
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    c.execute("""UPDATE messages 
                 SET is_read = 1
                 WHERE sender_id = ? AND receiver_id = ? AND is_read = 0""",
              (sender_id, user_id))
    conn.commit()
    conn.close() 