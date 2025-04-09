from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
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
from models import db, User, Agent, Task

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///social_media.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Load environment variables
load_dotenv()

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
    # Get user's agents
    agents = Agent.query.filter_by(user_id=current_user.id).all()
    
    # Get active tasks
    active_tasks = Task.query.filter_by(user_id=current_user.id, status='active').all()
    
    # Get task statistics
    total_tasks = Task.query.filter_by(user_id=current_user.id).count()
    completed_tasks = Task.query.filter_by(user_id=current_user.id, status='completed').count()
    failed_tasks = Task.query.filter_by(user_id=current_user.id, status='failed').count()
    
    return render_template('dashboard.html',
                         agents=agents,
                         active_tasks=active_tasks,
                         total_tasks=total_tasks,
                         completed_tasks=completed_tasks,
                         failed_tasks=failed_tasks)

@app.route('/agents')
@login_required
def agents():
    user_agents = Agent.query.filter_by(user_id=current_user.id).all()
    return render_template('agents.html', agents=user_agents)

@app.route('/agents/create', methods=['GET', 'POST'])
@login_required
def create_agent():
    if request.method == 'POST':
        name = request.form.get('name')
        agent_type = request.form.get('type')
        description = request.form.get('description')
        
        new_agent = Agent(
            name=name,
            agent_type=agent_type,
            description=description,
            user_id=current_user.id
        )
        
        try:
            db.session.add(new_agent)
            db.session.commit()
            flash('Agent created successfully!', 'success')
            return redirect(url_for('agents'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating agent: {str(e)}', 'danger')
    
    return render_template('create_agent.html')

@app.route('/tasks')
@login_required
def tasks():
    user_tasks = Task.query.filter_by(user_id=current_user.id).order_by(Task.created_at.desc()).all()
    return render_template('tasks.html', tasks=user_tasks)

@app.route('/tasks/create', methods=['GET', 'POST'])
@login_required
def create_task():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        agent_id = request.form.get('agent_id')
        
        new_task = Task(
            title=title,
            description=description,
            agent_id=agent_id,
            user_id=current_user.id,
            status='pending'
        )
        
        try:
            db.session.add(new_task)
            db.session.commit()
            flash('Task created successfully!', 'success')
            return redirect(url_for('tasks'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating task: {str(e)}', 'danger')
    
    agents = Agent.query.filter_by(user_id=current_user.id).all()
    return render_template('create_task.html', agents=agents)

@app.route('/task/<int:task_id>', methods=['GET', 'POST'])
@login_required
def task_detail(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('tasks'))
    
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'start':
            task.status = 'active'
            task.started_at = datetime.utcnow()
        elif action == 'complete':
            task.status = 'completed'
            task.completed_at = datetime.utcnow()
        elif action == 'fail':
            task.status = 'failed'
            task.completed_at = datetime.utcnow()
        
        try:
            db.session.commit()
            flash(f'Task {action}ed successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating task: {str(e)}', 'danger')
    
    return render_template('task_detail.html', task=task)

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
            flash('All fields are required', 'error')
            return redirect(url_for('register'))
            
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('register'))
            
        if len(password) < 6:
            flash('Password must be at least 6 characters long', 'error')
            return redirect(url_for('register'))
            
        if len(username) < 3:
            flash('Username must be at least 3 characters long', 'error')
            return redirect(url_for('register'))
        
        # Check if email or username already exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('register'))
            
        if User.query.filter_by(username=username).first():
            flash('Username already taken', 'error')
            return redirect(url_for('register'))
        
        try:
            user = User(
                email=email,
                username=username
            )
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            
            login_user(user)
            flash('Registration successful!', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration. Please try again.', 'error')
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
            flash('Please fill in all fields', 'error')
            return redirect(url_for('login'))
        
        try:
            user = User.query.filter_by(email=email).first()
            if user and user.check_password(password):
                login_user(user)
                next_page = request.args.get('next')
                if next_page and url_for('static', filename='') not in next_page:
                    return redirect(next_page)
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid email or password', 'error')
        except Exception as e:
            flash('An error occurred during login. Please try again.', 'error')
        
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
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        page_id = request.form.get('page_id')
        
        try:
            # Initialize Facebook SDK
            graph = facebook.GraphAPI(version="3.1")
            
            # Attempt to login and get access token
            response = requests.post(
                "https://graph.facebook.com/v18.0/oauth/access_token",
                params={
                    "grant_type": "password",
                    "client_id": os.getenv('FACEBOOK_APP_ID'),
                    "client_secret": os.getenv('FACEBOOK_APP_SECRET'),
                    "username": email,
                    "password": password
                }
            )
            
            if response.status_code == 200:
                # Store encrypted credentials
                current_user.encrypt_credentials('facebook', email, password)
                if page_id:
                    current_user.facebook_page_id = page_id
                db.session.commit()
                flash('Facebook account connected successfully!')
            else:
                flash('Failed to connect Facebook account. Please check your credentials.')
                
        except Exception as e:
            flash(f'Error connecting Facebook account: {str(e)}')
        
        return redirect(url_for('dashboard'))
        
    return render_template('connect_facebook.html')

@app.route('/connect/instagram', methods=['GET', 'POST'])
@login_required
def connect_instagram():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        try:
            # Initialize Instagram Private API
            api = instagram_private_api.Client(
                username=email,
                password=password,
                auto_patch=True,
                drop_incompat_keys=False
            )
            
            # If we get here, authentication was successful
            current_user.encrypt_credentials('instagram', email, password)
            db.session.commit()
            flash('Instagram account connected successfully!')
            
        except Exception as e:
            flash(f'Error connecting Instagram account: {str(e)}')
        
        return redirect(url_for('dashboard'))
        
    return render_template('connect_instagram.html')

@app.route('/connect/twitter', methods=['GET', 'POST'])
@login_required
def connect_twitter():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        try:
            # Initialize Tweepy client
            auth = tweepy.OAuthHandler(
                os.getenv('TWITTER_API_KEY'),
                os.getenv('TWITTER_API_SECRET')
            )
            
            # Use email/password to get access token
            auth_url = auth.get_authorization_url()
            session['request_token'] = auth.request_token
            
            # Store encrypted credentials
            current_user.encrypt_credentials('twitter', email, password)
            db.session.commit()
            flash('Twitter account connected successfully!')
            
        except Exception as e:
            flash(f'Error connecting Twitter account: {str(e)}')
        
        return redirect(url_for('dashboard'))
        
    return render_template('connect_twitter.html')

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

@app.route('/video/<int:video_id>', methods=['DELETE'])
@login_required
def delete_video(video_id):
    video = Video.query.get_or_404(video_id)
    if video.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        db.session.delete(video)
        db.session.commit()
        return jsonify({'message': 'Video deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/manage/facebook')
@login_required
def manage_facebook():
    if not current_user.facebook_email or not current_user.facebook_password_hash:
        flash('Please connect your Facebook account first', 'error')
        return redirect(url_for('connect_facebook'))
    return render_template('manage_facebook.html')

@app.route('/manage/instagram')
@login_required
def manage_instagram():
    if not current_user.instagram_email or not current_user.instagram_password_hash:
        flash('Please connect your Instagram account first', 'error')
        return redirect(url_for('connect_instagram'))
    return render_template('manage_instagram.html')

@app.route('/manage/twitter')
@login_required
def manage_twitter():
    if not current_user.twitter_email or not current_user.twitter_password_hash:
        flash('Please connect your Twitter account first', 'error')
        return redirect(url_for('connect_twitter'))
    return render_template('manage_twitter.html')

@app.route('/schedule')
@login_required
def schedule():
    return render_template('schedule.html')

@app.route('/analytics')
@login_required
def analytics():
    # Get task completion statistics
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    total_tasks = len(tasks)
    completed_tasks = sum(1 for t in tasks if t.status == 'completed')
    failed_tasks = sum(1 for t in tasks if t.status == 'failed')
    success_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    # Get agent performance statistics
    agents = Agent.query.filter_by(user_id=current_user.id).all()
    agent_stats = []
    for agent in agents:
        agent_tasks = Task.query.filter_by(agent_id=agent.id).all()
        agent_total = len(agent_tasks)
        agent_completed = sum(1 for t in agent_tasks if t.status == 'completed')
        agent_success_rate = (agent_completed / agent_total * 100) if agent_total > 0 else 0
        agent_stats.append({
            'agent': agent,
            'total_tasks': agent_total,
            'completed_tasks': agent_completed,
            'success_rate': agent_success_rate
        })
    
    return render_template('analytics.html',
                         total_tasks=total_tasks,
                         completed_tasks=completed_tasks,
                         failed_tasks=failed_tasks,
                         success_rate=success_rate,
                         agent_stats=agent_stats)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 