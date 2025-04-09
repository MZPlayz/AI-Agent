from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
from dotenv import load_dotenv
import tweepy
import facebook
import instagram_private_api
import requests
import json

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///social_media.db'
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Load environment variables
load_dotenv()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    twitter_token = db.Column(db.String(200))
    facebook_token = db.Column(db.String(200))
    instagram_token = db.Column(db.String(200))
    json2video_token = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SocialMediaPage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    platform = db.Column(db.String(20), nullable=False)
    page_id = db.Column(db.String(100), nullable=False)
    page_name = db.Column(db.String(100), nullable=False)
    access_token = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    json_data = db.Column(db.Text, nullable=False)
    video_url = db.Column(db.String(200))
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        pages = SocialMediaPage.query.filter_by(user_id=user.id).all()
        return render_template('dashboard.html', user=user, pages=pages)
    return render_template('index.html')

@app.route('/connect/twitter')
def connect_twitter():
    auth = tweepy.OAuthHandler(
        os.getenv('TWITTER_API_KEY'),
        os.getenv('TWITTER_API_SECRET'),
        url_for('twitter_callback', _external=True)
    )
    return redirect(auth.get_authorization_url())

@app.route('/connect/facebook')
def connect_facebook():
    # Meta OAuth URL for Facebook
    auth_url = f"https://www.facebook.com/v18.0/dialog/oauth?client_id={os.getenv('FACEBOOK_APP_ID')}&redirect_uri={url_for('facebook_callback', _external=True)}&scope=pages_manage_posts,pages_read_engagement,pages_show_list"
    return redirect(auth_url)

@app.route('/connect/instagram')
def connect_instagram():
    # Meta OAuth URL for Instagram
    auth_url = f"https://www.facebook.com/v18.0/dialog/oauth?client_id={os.getenv('INSTAGRAM_CLIENT_ID')}&redirect_uri={url_for('instagram_callback', _external=True)}&scope=instagram_basic,instagram_content_publish,pages_show_list"
    return redirect(auth_url)

@app.route('/twitter/callback')
def twitter_callback():
    auth = tweepy.OAuthHandler(
        os.getenv('TWITTER_API_KEY'),
        os.getenv('TWITTER_API_SECRET')
    )
    verifier = request.args.get('oauth_verifier')
    auth.get_access_token(verifier)
    
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        user.twitter_token = auth.access_token
        db.session.commit()
    
    return redirect(url_for('index'))

@app.route('/facebook/callback')
def facebook_callback():
    code = request.args.get('code')
    if not code:
        return redirect(url_for('index'))
    
    # Exchange code for access token
    token_url = "https://graph.facebook.com/v18.0/oauth/access_token"
    params = {
        'client_id': os.getenv('FACEBOOK_APP_ID'),
        'client_secret': os.getenv('FACEBOOK_APP_SECRET'),
        'redirect_uri': url_for('facebook_callback', _external=True),
        'code': code
    }
    
    response = requests.get(token_url, params=params)
    data = response.json()
    access_token = data.get('access_token')
    
    if access_token and 'user_id' in session:
        user = User.query.get(session['user_id'])
        user.facebook_token = access_token
        
        # Get user's pages
        pages_url = "https://graph.facebook.com/v18.0/me/accounts"
        pages_response = requests.get(pages_url, params={'access_token': access_token})
        pages_data = pages_response.json()
        
        if 'data' in pages_data:
            for page in pages_data['data']:
                existing_page = SocialMediaPage.query.filter_by(
                    user_id=user.id,
                    platform='facebook',
                    page_id=page['id']
                ).first()
                
                if not existing_page:
                    new_page = SocialMediaPage(
                        user_id=user.id,
                        platform='facebook',
                        page_id=page['id'],
                        page_name=page['name'],
                        access_token=page['access_token']
                    )
                    db.session.add(new_page)
        
        db.session.commit()
    
    return redirect(url_for('index'))

@app.route('/instagram/callback')
def instagram_callback():
    code = request.args.get('code')
    if not code:
        return redirect(url_for('index'))
    
    # Exchange code for access token
    token_url = "https://graph.facebook.com/v18.0/oauth/access_token"
    params = {
        'client_id': os.getenv('INSTAGRAM_CLIENT_ID'),
        'client_secret': os.getenv('INSTAGRAM_CLIENT_SECRET'),
        'redirect_uri': url_for('instagram_callback', _external=True),
        'code': code
    }
    
    response = requests.get(token_url, params=params)
    data = response.json()
    access_token = data.get('access_token')
    
    if access_token and 'user_id' in session:
        user = User.query.get(session['user_id'])
        user.instagram_token = access_token
        
        # Get user's Instagram Business accounts
        accounts_url = "https://graph.facebook.com/v18.0/me/accounts"
        accounts_response = requests.get(accounts_url, params={'access_token': access_token})
        accounts_data = accounts_response.json()
        
        if 'data' in accounts_data:
            for account in accounts_data['data']:
                # Get Instagram Business account ID
                instagram_url = f"https://graph.facebook.com/v18.0/{account['id']}?fields=instagram_business_account&access_token={access_token}"
                instagram_response = requests.get(instagram_url)
                instagram_data = instagram_response.json()
                
                if 'instagram_business_account' in instagram_data:
                    instagram_id = instagram_data['instagram_business_account']['id']
                    
                    existing_page = SocialMediaPage.query.filter_by(
                        user_id=user.id,
                        platform='instagram',
                        page_id=instagram_id
                    ).first()
                    
                    if not existing_page:
                        new_page = SocialMediaPage(
                            user_id=user.id,
                            platform='instagram',
                            page_id=instagram_id,
                            page_name=account['name'],
                            access_token=access_token
                        )
                        db.session.add(new_page)
        
        db.session.commit()
    
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        username = request.form.get('username')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('register'))
        
        user = User(
            email=email,
            password_hash=generate_password_hash(password),
            username=username
        )
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        return redirect(url_for('dashboard'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/create_video', methods=['GET', 'POST'])
@login_required
def create_video():
    if request.method == 'POST':
        title = request.form.get('title')
        template_data = request.form.get('template_data')
        
        # Create video using JSON2Video API
        headers = {
            'Authorization': f'Bearer {current_user.json2video_token}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'title': title,
            'template': json.loads(template_data)
        }
        
        response = requests.post(
            'https://api.json2video.com/v1/videos',
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            video_data = response.json()
            video = Video(
                user_id=current_user.id,
                title=title,
                json_data=template_data,
                video_url=video_data.get('url'),
                status='processing'
            )
            db.session.add(video)
            db.session.commit()
            flash('Video creation started')
        else:
            flash('Error creating video')
        
        return redirect(url_for('dashboard'))
    
    return render_template('create_video.html')

@app.route('/videos')
@login_required
def videos():
    user_videos = Video.query.filter_by(user_id=current_user.id).order_by(Video.created_at.desc()).all()
    return render_template('videos.html', videos=user_videos)

@app.route('/check_video_status/<int:video_id>')
@login_required
def check_video_status(video_id):
    video = Video.query.get_or_404(video_id)
    if video.user_id != current_user.id:
        return {'error': 'Unauthorized'}, 403
    
    headers = {
        'Authorization': f'Bearer {current_user.json2video_token}'
    }
    
    response = requests.get(
        f'https://api.json2video.com/v1/videos/{video.video_url}',
        headers=headers
    )
    
    if response.status_code == 200:
        status_data = response.json()
        video.status = status_data.get('status', 'unknown')
        db.session.commit()
        return {'status': video.status}
    
    return {'error': 'Failed to check status'}, 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 