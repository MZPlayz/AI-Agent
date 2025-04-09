from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from cryptography.fernet import Fernet
import os
from datetime import datetime

db = SQLAlchemy()

class VideoTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    template_data = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Social Media Credentials (Encrypted)
    facebook_email = db.Column(db.String(120))
    facebook_password_hash = db.Column(db.String(256))
    facebook_access_token = db.Column(db.String(200))
    facebook_page_id = db.Column(db.String(120))
    
    instagram_email = db.Column(db.String(120))
    instagram_password_hash = db.Column(db.String(256))
    instagram_access_token = db.Column(db.String(200))
    
    twitter_email = db.Column(db.String(120))
    twitter_password_hash = db.Column(db.String(256))
    twitter_access_token = db.Column(db.String(200))
    
    json2video_token = db.Column(db.String(200))
    
    # AI Agent related fields
    agents = db.relationship('Agent', backref='user', lazy=True)
    tasks = db.relationship('Task', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def encrypt_credentials(self, platform, email, password):
        """Encrypt social media credentials"""
        key = os.getenv('ENCRYPTION_KEY')
        if not key:
            raise ValueError("ENCRYPTION_KEY not set in environment variables")
            
        f = Fernet(key.encode())
        encrypted_password = f.encrypt(password.encode()).decode()
        
        if platform == 'facebook':
            self.facebook_email = email
            self.facebook_password_hash = encrypted_password
        elif platform == 'instagram':
            self.instagram_email = email
            self.instagram_password_hash = encrypted_password
        elif platform == 'twitter':
            self.twitter_email = email
            self.twitter_password_hash = encrypted_password
            
    def get_credentials(self, platform):
        """Get decrypted social media credentials"""
        key = os.getenv('ENCRYPTION_KEY')
        if not key:
            raise ValueError("ENCRYPTION_KEY not set in environment variables")
            
        f = Fernet(key.encode())
        
        if platform == 'facebook':
            if self.facebook_password_hash:
                return {
                    'email': self.facebook_email,
                    'password': f.decrypt(self.facebook_password_hash.encode()).decode(),
                    'page_id': self.facebook_page_id
                }
        elif platform == 'instagram':
            if self.instagram_password_hash:
                return {
                    'email': self.instagram_email,
                    'password': f.decrypt(self.instagram_password_hash.encode()).decode()
                }
        elif platform == 'twitter':
            if self.twitter_password_hash:
                return {
                    'email': self.twitter_email,
                    'password': f.decrypt(self.twitter_password_hash.encode()).decode()
                }
        return None

class Agent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    agent_type = db.Column(db.String(50), nullable=False)  # e.g., 'research', 'automation', 'analysis'
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='inactive')  # inactive, active, busy
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_active = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Agent capabilities and configuration
    capabilities = db.Column(db.JSON)  # Store agent capabilities as JSON
    configuration = db.Column(db.JSON)  # Store agent configuration as JSON
    
    # Relationship with tasks
    tasks = db.relationship('Task', backref='agent', lazy=True)
    
    def __repr__(self):
        return f'<Agent {self.name}>'

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # pending, active, completed, failed
    priority = db.Column(db.Integer, default=1)  # 1-5, 5 being highest
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    agent_id = db.Column(db.Integer, db.ForeignKey('agent.id'))
    
    # Task parameters and results
    parameters = db.Column(db.JSON)  # Store task parameters as JSON
    results = db.Column(db.JSON)  # Store task results as JSON
    error_message = db.Column(db.Text)  # Store error message if task failed
    
    def __repr__(self):
        return f'<Task {self.title}>'