import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database
    DB_PATH = os.getenv('DB_PATH', 'app_collected_data.db')
    UPLOAD_PATH = os.getenv('UPLOAD_PATH', 'uploads')
    
    # Security
    SECRET_KEY = os.getenv('SECRET_KEY')
    
    # Storage
    CLOUD_STORAGE_BUCKET = os.getenv('CLOUD_STORAGE_BUCKET')
    
    # Features
    MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5MB
    ALLOWED_IMAGE_TYPES = ['png', 'jpg', 'jpeg', 'gif']
    ALLOWED_VIDEO_TYPES = ['mp4', 'mov', 'avi'] 
    
    # Update paths
    UPLOAD_PATHS = {
        'posts': 'uploads/posts',
        'stories': 'uploads/stories',
        'challenges': 'uploads/challenges'
    } 
    
    # XMPP Configuration
    XMPP_SERVER = os.getenv('XMPP_SERVER', 'localhost')
    XMPP_PORT = int(os.getenv('XMPP_PORT', 5222)) 