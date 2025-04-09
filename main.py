from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import requests
import json
from dotenv import load_dotenv
import facebook
import instagram_private_api
import tweepy

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
    json2video_token = db.Column(db.String(200))
    # Social Media Credentials
    facebook_email = db.Column(db.String(120))
    facebook_password_hash = db.Column(db.String(200))
    facebook_access_token = db.Column(db.String(200))
    
    instagram_email = db.Column(db.String(120))
    instagram_password_hash = db.Column(db.String(200))
    instagram_access_token = db.Column(db.String(200))
    
    twitter_email = db.Column(db.String(120))
    twitter_password_hash = db.Column(db.String(200))
    twitter_access_token = db.Column(db.String(200))
    
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
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/dashboard')
@login_required
def dashboard():
    user_videos = Video.query.filter_by(user_id=current_user.id).order_by(Video.created_at.desc()).all()
    return render_template('dashboard.html', videos=user_videos)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        username = request.form.get('username')
        
        # Validate input
        if not all([email, password, confirm_password, username]):
            flash('All fields are required')
            return redirect(url_for('register'))
            
        if password != confirm_password:
            flash('Passwords do not match')
            return redirect(url_for('register'))
            
        if len(password) < 6:
            flash('Password must be at least 6 characters long')
            return redirect(url_for('register'))
            
        if len(username) < 3:
            flash('Username must be at least 3 characters long')
            return redirect(url_for('register'))
        
        # Check if email or username already exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('register'))
            
        if User.query.filter_by(username=username).first():
            flash('Username already taken')
            return redirect(url_for('register'))
        
        try:
            user = User(
                email=email,
                password_hash=generate_password_hash(password),
                username=username
            )
            db.session.add(user)
            db.session.commit()
            
            login_user(user)
            flash('Registration successful!', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration. Please try again.')
            return redirect(url_for('register'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not all([email, password]):
            flash('Please fill in all fields')
            return redirect(url_for('login'))
        
        try:
            user = User.query.filter_by(email=email).first()
            if user and check_password_hash(user.password_hash, password):
                login_user(user)
                next_page = request.args.get('next')
                if next_page and url_for('static', filename='') not in next_page:
                    return redirect(next_page)
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid email or password')
        except Exception as e:
            flash('An error occurred during login. Please try again.')
        
        return redirect(url_for('login'))
    
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

@app.route('/connect/facebook', methods=['GET', 'POST'])
@login_required
def connect_facebook():
    if request.method == 'GET':
        # Generate OAuth URL for Facebook login
        oauth_url = f"https://www.facebook.com/v18.0/dialog/oauth?" + \
                   f"client_id={os.getenv('FACEBOOK_APP_ID')}&" + \
                   f"redirect_uri={url_for('facebook_callback', _external=True)}&" + \
                   "scope=pages_show_list,pages_read_engagement,pages_manage_posts"
        return redirect(oauth_url)
    
    return render_template('connect_facebook.html')

@app.route('/facebook/callback')
@login_required
def facebook_callback():
    code = request.args.get('code')
    if not code:
        flash('Failed to connect Facebook account.')
        return redirect(url_for('dashboard'))

    try:
        # Exchange code for access token
        token_url = "https://graph.facebook.com/v18.0/oauth/access_token"
        response = requests.get(token_url, params={
            'client_id': os.getenv('FACEBOOK_APP_ID'),
            'client_secret': os.getenv('FACEBOOK_APP_SECRET'),
            'redirect_uri': url_for('facebook_callback', _external=True),
            'code': code
        })
        
        if response.status_code == 200:
            data = response.json()
            access_token = data.get('access_token')
            
            # Get user info
            graph = facebook.GraphAPI(access_token=access_token)
            user_info = graph.get_object('me', fields='id,name,email')
            
            # Store the credentials
            current_user.facebook_access_token = access_token
            current_user.facebook_email = user_info.get('email')
            db.session.commit()
            
            flash('Facebook account connected successfully!')
        else:
            flash('Failed to get Facebook access token.')
            
    except Exception as e:
        flash(f'Error connecting Facebook account: {str(e)}')
    
    return redirect(url_for('dashboard'))

@app.route('/connect/instagram', methods=['GET', 'POST'])
@login_required
def connect_instagram():
    if request.method == 'GET':
        # Generate OAuth URL for Instagram login
        oauth_url = f"https://api.instagram.com/oauth/authorize?" + \
                   f"client_id={os.getenv('INSTAGRAM_APP_ID')}&" + \
                   f"redirect_uri={url_for('instagram_callback', _external=True)}&" + \
                   "scope=basic+public_content&response_type=code"
        return redirect(oauth_url)
    
    return render_template('connect_instagram.html')

@app.route('/instagram/callback')
@login_required
def instagram_callback():
    code = request.args.get('code')
    if not code:
        flash('Failed to connect Instagram account.')
        return redirect(url_for('dashboard'))

    try:
        # Exchange code for access token
        token_url = "https://api.instagram.com/oauth/access_token"
        response = requests.post(token_url, data={
            'client_id': os.getenv('INSTAGRAM_APP_ID'),
            'client_secret': os.getenv('INSTAGRAM_APP_SECRET'),
            'grant_type': 'authorization_code',
            'redirect_uri': url_for('instagram_callback', _external=True),
            'code': code
        })
        
        if response.status_code == 200:
            data = response.json()
            access_token = data.get('access_token')
            user_id = data.get('user_id')
            
            # Get user info
            user_info_url = f"https://graph.instagram.com/v12.0/{user_id}"
            user_response = requests.get(user_info_url, params={
                'fields': 'id,username',
                'access_token': access_token
            })
            
            if user_response.status_code == 200:
                user_data = user_response.json()
                current_user.instagram_access_token = access_token
                current_user.instagram_email = user_data.get('username')
                db.session.commit()
                flash('Instagram account connected successfully!')
            else:
                flash('Failed to get Instagram user info.')
        else:
            flash('Failed to get Instagram access token.')
            
    except Exception as e:
        flash(f'Error connecting Instagram account: {str(e)}')
    
    return redirect(url_for('dashboard'))

@app.route('/connect/twitter', methods=['GET', 'POST'])
@login_required
def connect_twitter():
    if request.method == 'GET':
        # Initialize Tweepy OAuth2 client
        client = tweepy.OAuth2UserHandler(
            client_id=os.getenv('TWITTER_CLIENT_ID'),
            client_secret=os.getenv('TWITTER_CLIENT_SECRET'),
            redirect_uri=url_for('twitter_callback', _external=True),
            scope=['tweet.read', 'tweet.write', 'users.read']
        )
        
        # Get authorization URL
        auth_url = client.get_authorization_url()
        session['twitter_oauth_state'] = client.state
        return redirect(auth_url)
    
    return render_template('connect_twitter.html')

@app.route('/twitter/callback')
@login_required
def twitter_callback():
    code = request.args.get('code')
    state = request.args.get('state')
    
    if not code or not state or state != session.get('twitter_oauth_state'):
        flash('Failed to connect Twitter account.')
        return redirect(url_for('dashboard'))

    try:
        # Initialize OAuth2 handler
        client = tweepy.OAuth2UserHandler(
            client_id=os.getenv('TWITTER_CLIENT_ID'),
            client_secret=os.getenv('TWITTER_CLIENT_SECRET'),
            redirect_uri=url_for('twitter_callback', _external=True),
            scope=['tweet.read', 'tweet.write', 'users.read']
        )
        
        # Get access token
        access_token = client.fetch_token(code)
        
        # Initialize API v2 client
        twitter_client = tweepy.Client(
            bearer_token=access_token['access_token']
        )
        
        # Get user info
        user = twitter_client.get_me()
        
        if user.data:
            current_user.twitter_access_token = access_token['access_token']
            current_user.twitter_email = user.data.username
            db.session.commit()
            flash('Twitter account connected successfully!')
        else:
            flash('Failed to get Twitter user info.')
            
    except Exception as e:
        flash(f'Error connecting Twitter account: {str(e)}')
    
    return redirect(url_for('dashboard'))

@app.route('/disconnect/<platform>')
@login_required
def disconnect_platform(platform):
    if platform == 'facebook':
        current_user.facebook_email = None
        current_user.facebook_password_hash = None
        current_user.facebook_access_token = None
    elif platform == 'instagram':
        current_user.instagram_email = None
        current_user.instagram_password_hash = None
        current_user.instagram_access_token = None
    elif platform == 'twitter':
        current_user.twitter_email = None
        current_user.twitter_password_hash = None
        current_user.twitter_access_token = None
        
    db.session.commit()
    flash(f'{platform.title()} account disconnected successfully!')
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 