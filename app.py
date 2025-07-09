from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy.orm import DeclarativeBase
import os
import json
import zipfile
from datetime import datetime
import shutil
import threading
import time
from content_generator import ContentGenerator
from seo_optimizer import SEOOptimizer

class Base(DeclarativeBase):
    pass

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'sakmpar-secret-key-2025')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize extensions
db = SQLAlchemy(app, model_class=Base)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# Create upload directory
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize content generator and SEO optimizer
content_gen = ContentGenerator()
seo_optimizer = SEOOptimizer()

# Global variables for scheduler
scheduler_running = False
scheduler_thread = None
scheduler_interval = 1800  # Default 30 minutes for unlimited generation

# Define models directly in app.py to avoid circular imports
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    bio = db.Column(db.Text)
    profile_image = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    
    # Relationships
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    likes = db.relationship('Like', backref='user', lazy='dynamic')
    comments = db.relationship('Comment', backref='author', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    description = db.Column(db.String(500))
    image_url = db.Column(db.String(500))
    tags = db.Column(db.String(200))
    category = db.Column(db.String(100))
    status = db.Column(db.String(20), default='published')
    is_featured = db.Column(db.Boolean, default=False)
    is_auto_generated = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    likes = db.relationship('Like', backref='post', lazy='dynamic', cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='post', lazy='dynamic', cascade='all, delete-orphan')
    shares = db.relationship('Share', backref='post', lazy='dynamic', cascade='all, delete-orphan')
    
    @property
    def likes_count(self):
        return self.likes.count()
    
    @property
    def comments_count(self):
        return self.comments.count()
    
    @property
    def shares_count(self):
        return self.shares.count()
    
    def __repr__(self):
        return f'<Post {self.title}>'

class Like(db.Model):
    __tablename__ = 'likes'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Unique constraint to prevent double-liking
    __table_args__ = (db.UniqueConstraint('user_id', 'post_id', name='unique_user_post_like'),)

class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comments.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Self-referential relationship for replies
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')
    
    def __repr__(self):
        return f'<Comment {self.id}>'

class Share(db.Model):
    __tablename__ = 'shares'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    platform = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Share {self.id}>'

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Category {self.name}>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create database tables
with app.app_context():
    db.create_all()
    
    # Create admin user if not exists
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@sakmpar.co.in',
            full_name='SAKMPAR Admin',
            bio='SAKMPAR News Administrator',
            is_admin=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("✅ Admin user created: admin/admin123")
    
    # Import a few existing posts into database (not all to avoid memory issues)
    generated_dir = 'generated'
    if os.path.exists(generated_dir) and Post.query.count() == 0:
        print("📝 Importing sample blog posts to database...")
        imported_count = 0
        max_import = 5  # Limit to 5 posts to avoid memory issues
        
        html_files = [f for f in os.listdir(generated_dir) if f.endswith('.html') and f != 'index.html' and 'facebook' not in f]
        
        for filename in html_files[:max_import]:
            filepath = os.path.join(generated_dir, filename)
            try:
                # Extract title from filename
                title = filename.replace('.html', '').replace('-', ' ')
                if '20250709' in title:
                    title = title.replace('20250709', '').strip()
                title = title.title()[:200]
                
                # Determine category and language  
                category = 'News'
                if any(hindi_word in filename for hindi_word in ['bihar', 'pithoragarh', 'vadodara']):
                    category = 'हिंदी समाचार'
                
                # Create minimal database post (without full HTML content to save memory)
                db_post = Post(
                    title=title,
                    content=f"Auto-generated trending content about {title}. This is a sample post imported from generated files.",
                    description=f"Trending news and updates about {title}",
                    image_url='https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=800',
                    category=category,
                    tags='trending,news,auto',
                    user_id=admin.id,
                    is_auto_generated=True
                )
                
                db.session.add(db_post)
                imported_count += 1
                
            except Exception as e:
                print(f"❌ Error importing {filename}: {e}")
        
        db.session.commit()
        print(f"✅ Imported {imported_count} sample posts to database")

# Authentication Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        username = data.get('username')
        password = data.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            if request.is_json:
                return jsonify({'success': True, 'message': 'Login successful'})
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            if request.is_json:
                return jsonify({'success': False, 'message': 'Invalid username or password'})
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        full_name = data.get('full_name')
        bio = data.get('bio', '')
        
        # Validation
        if User.query.filter_by(username=username).first():
            if request.is_json:
                return jsonify({'success': False, 'message': 'Username already exists'})
            flash('Username already exists', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            if request.is_json:
                return jsonify({'success': False, 'message': 'Email already registered'})
            flash('Email already registered', 'error')
            return render_template('register.html')
        
        # Create new user
        user = User(
            username=username,
            email=email,
            full_name=full_name,
            bio=bio
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        
        if request.is_json:
            return jsonify({'success': True, 'message': 'Registration successful'})
        flash('Registration successful!', 'success')
        return redirect(url_for('index'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# Main Routes
@app.route('/')
def index():
    """Main Facebook-style interface"""
    return render_template('facebook_social.html')

@app.route('/admin')
@login_required
def admin_panel():
    """Admin control panel for blog management"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    
    from flask import make_response
    response = render_template('admin_panel.html', scheduler_running=scheduler_running, scheduler_interval=scheduler_interval)
    resp = make_response(response)
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp

@app.route('/public')
def public_blog():
    """Public blog interface with Facebook-style infinite scroll"""
    from flask import make_response
    response = render_template('facebook_social.html')
    resp = make_response(response)
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp

# User Post Creation
@app.route('/create-post', methods=['POST'])
@login_required
def create_post():
    """Create a new user post"""
    try:
        data = request.get_json() if request.is_json else request.form
        
        title = data.get('title')
        content = data.get('content')
        description = data.get('description', '')
        tags = data.get('tags', '')
        category = data.get('category', 'General')
        image_url = data.get('image_url', '')
        
        if not title or not content:
            return jsonify({'success': False, 'message': 'Title and content are required'})
        
        # Create new post
        post = Post(
            title=title,
            content=content,
            description=description,
            tags=tags,
            category=category,
            image_url=image_url,
            user_id=current_user.id,
            is_auto_generated=False
        )
        
        db.session.add(post)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Post created successfully',
            'post_id': post.id
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error creating post: {str(e)}'})

# Social Interactions
@app.route('/like-post/<int:post_id>', methods=['POST'])
@login_required
def like_post(post_id):
    """Like or unlike a post"""
    try:
        post = Post.query.get_or_404(post_id)
        
        # Check if user already liked this post
        existing_like = Like.query.filter_by(user_id=current_user.id, post_id=post_id).first()
        
        if existing_like:
            # Unlike the post
            db.session.delete(existing_like)
            liked = False
        else:
            # Like the post
            like = Like(user_id=current_user.id, post_id=post_id)
            db.session.add(like)
            liked = True
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'liked': liked,
            'likes_count': post.likes_count
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/comment-post/<int:post_id>', methods=['POST'])
@login_required
def comment_post(post_id):
    """Add a comment to a post"""
    try:
        data = request.get_json()
        content = data.get('content', '').strip()
        
        if not content:
            return jsonify({'success': False, 'message': 'Comment content is required'})
        
        post = Post.query.get_or_404(post_id)
        
        comment = Comment(
            content=content,
            user_id=current_user.id,
            post_id=post_id
        )
        
        db.session.add(comment)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Comment added successfully',
            'comment': {
                'id': comment.id,
                'content': comment.content,
                'author': current_user.full_name,
                'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M')
            },
            'comments_count': post.comments_count
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/share-post/<int:post_id>', methods=['POST'])
@login_required
def share_post(post_id):
    """Share a post"""
    try:
        data = request.get_json()
        platform = data.get('platform', 'general')
        
        post = Post.query.get_or_404(post_id)
        
        # Check if user already shared this post on this platform
        existing_share = Share.query.filter_by(
            user_id=current_user.id, 
            post_id=post_id, 
            platform=platform
        ).first()
        
        if not existing_share:
            share = Share(
                user_id=current_user.id,
                post_id=post_id,
                platform=platform
            )
            db.session.add(share)
            db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Post shared successfully',
            'shares_count': post.shares_count
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

# API Endpoints
@app.route('/api/posts')
def api_posts():
    """API endpoint to get all posts for social interface"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Get posts with user data, likes, comments, shares
        posts_query = Post.query.filter_by(status='published').order_by(Post.created_at.desc())
        posts_paginated = posts_query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        posts_data = []
        for post in posts_paginated.items:
            # Check if current user liked this post
            user_liked = False
            if current_user.is_authenticated:
                user_liked = Like.query.filter_by(
                    user_id=current_user.id, 
                    post_id=post.id
                ).first() is not None
            
            # Get recent comments
            recent_comments = Comment.query.filter_by(post_id=post.id)\
                .order_by(Comment.created_at.desc()).limit(3).all()
            
            comments_data = []
            for comment in recent_comments:
                comments_data.append({
                    'id': comment.id,
                    'content': comment.content,
                    'author': comment.author.full_name,
                    'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M')
                })
            
            posts_data.append({
                'id': post.id,
                'title': post.title,
                'content': post.content[:500] + '...' if len(post.content) > 500 else post.content,
                'description': post.description,
                'image_url': post.image_url,
                'category': post.category,
                'tags': post.tags.split(',') if post.tags else [],
                'author': {
                    'id': post.author.id,
                    'username': post.author.username,
                    'full_name': post.author.full_name,
                    'profile_image': post.author.profile_image
                },
                'created_at': post.created_at.isoformat(),
                'likes_count': post.likes_count,
                'comments_count': post.comments_count,
                'shares_count': post.shares_count,
                'user_liked': user_liked,
                'recent_comments': comments_data,
                'is_auto_generated': post.is_auto_generated
            })
        
        return jsonify({
            'success': True,
            'posts': posts_data,
            'has_next': posts_paginated.has_next,
            'page': page,
            'total': posts_paginated.total
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/api/user-profile')
@login_required
def api_user_profile():
    """Get current user profile"""
    return jsonify({
        'success': True,
        'user': {
            'id': current_user.id,
            'username': current_user.username,
            'full_name': current_user.full_name,
            'email': current_user.email,
            'bio': current_user.bio,
            'profile_image': current_user.profile_image,
            'is_admin': current_user.is_admin,
            'posts_count': current_user.posts.count()
        }
    })

# Auto Content Generation (existing functionality)
@app.route('/generate-content', methods=['POST'])
@login_required
def generate_content():
    """Generate blog content from trending topics"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Admin privileges required'})
    
    try:
        data = request.get_json()
        language = data.get('language', 'english')
        count = int(data.get('count', 5))
        
        # Generate content using existing system
        results = content_gen.generate_blog_posts(count=count, language=language)
        
        if results['success']:
            # Create posts in database from generated content
            admin_user = User.query.filter_by(username='admin').first()
            
            for generated_post in results['posts']:
                # Extract title from filename
                title = generated_post['title']
                
                # Read generated HTML content
                html_path = os.path.join('generated', generated_post['filename'])
                if os.path.exists(html_path):
                    with open(html_path, 'r', encoding='utf-8') as f:
                        html_content = f.read()
                    
                    # Extract image URL from HTML
                    image_url = None
                    img_start = html_content.find('src="https://images.unsplash.com')
                    if img_start > -1:
                        img_end = html_content.find('"', img_start + 5)
                        if img_end > img_start:
                            image_url = html_content[img_start + 5:img_end]
                    
                    # Create database post
                    db_post = Post(
                        title=title,
                        content=html_content,
                        description=f"Auto-generated content about {title}",
                        image_url=image_url or '',
                        category='Auto Generated',
                        tags='trending,news,auto',
                        user_id=admin_user.id,
                        is_auto_generated=True
                    )
                    
                    db.session.add(db_post)
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Successfully generated {len(results["posts"])} blog posts',
                'posts': results['posts']
            })
        else:
            return jsonify({
                'success': False,
                'message': results['message']
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error generating content: {str(e)}'
        })

# Scheduler functionality (existing)
@app.route('/start-scheduler', methods=['POST'])
@login_required
def start_scheduler():
    """Start automated content generation scheduler"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Admin privileges required'})
    
    global scheduler_running, scheduler_thread, scheduler_interval
    
    try:
        data = request.get_json()
        interval_hours = float(data.get('interval', 0.5))
        posts_count = int(data.get('posts', 20))
        
        scheduler_interval = int(interval_hours * 3600)
        
        if not scheduler_running:
            scheduler_running = True
            scheduler_thread = threading.Thread(target=content_scheduler)
            scheduler_thread.daemon = True
            scheduler_thread.start()
            
            return jsonify({
                'success': True,
                'message': f'Scheduler started with {interval_hours}h interval'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Scheduler is already running'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error starting scheduler: {str(e)}'
        })

@app.route('/stop-scheduler', methods=['POST'])
@login_required
def stop_scheduler():
    """Stop automated content generation scheduler"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Admin privileges required'})
    
    global scheduler_running
    
    try:
        scheduler_running = False
        return jsonify({
            'success': True,
            'message': 'Scheduler stopped successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error stopping scheduler: {str(e)}'
        })

def content_scheduler():
    """Background scheduler for automated unlimited content generation"""
    global scheduler_running, scheduler_interval
    import random
    
    admin_user = User.query.filter_by(username='admin').first()
    
    while scheduler_running:
        try:
            print(f"🚀 AUTO CONTENT GENERATOR: Starting at {datetime.now()}")
            
            # Generate different types of content in rotation
            languages = ['english', 'hindi', 'global']
            current_language = languages[int(time.time() // scheduler_interval) % len(languages)]
            
            # Generate unlimited amounts: 15-25 posts per cycle
            post_count = random.randint(15, 25)
            
            print(f"📝 Generating {post_count} posts in {current_language}")
            results = content_gen.generate_blog_posts(count=post_count, language=current_language)
            
            if results['success']:
                # Add generated posts to database
                with app.app_context():
                    for generated_post in results['posts']:
                        title = generated_post['title']
                        
                        # Read generated HTML content
                        html_path = os.path.join('generated', generated_post['filename'])
                        if os.path.exists(html_path):
                            with open(html_path, 'r', encoding='utf-8') as f:
                                html_content = f.read()
                            
                            # Extract image URL
                            image_url = None
                            img_start = html_content.find('src="https://images.unsplash.com')
                            if img_start > -1:
                                img_end = html_content.find('"', img_start + 5)
                                if img_end > img_start:
                                    image_url = html_content[img_start + 5:img_end]
                            
                            # Create database post
                            db_post = Post(
                                title=title,
                                content=html_content,
                                description=f"Auto-generated trending content about {title}",
                                image_url=image_url or '',
                                category='Trending',
                                tags='trending,news,auto',
                                user_id=admin_user.id,
                                is_auto_generated=True
                            )
                            
                            db.session.add(db_post)
                    
                    db.session.commit()
                
                print(f"✅ Successfully generated {len(results['posts'])} posts")
            else:
                print(f"❌ Generation failed: {results['message']}")
                
        except Exception as e:
            print(f"❌ Scheduler error: {e}")
        
        print(f"⏱️ Next generation in {scheduler_interval//60} minutes...")
        time.sleep(scheduler_interval)

# Export functionality (existing)
@app.route('/export-site')
@login_required
def export_site():
    """Export the complete blog site as a ZIP file"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Admin privileges required'})
    
    try:
        generated_dir = 'generated'
        if not os.path.exists(generated_dir):
            return jsonify({
                'success': False,
                'message': 'No generated content found'
            })
        
        # Create ZIP file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        zip_filename = f'sakmpar_social_blog_{timestamp}.zip'
        zip_path = os.path.join('generated', zip_filename)
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(generated_dir):
                for file in files:
                    if file != zip_filename:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, generated_dir)
                        zipf.write(file_path, arcname)
        
        return send_file(zip_path, as_attachment=True, download_name=zip_filename)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error exporting site: {str(e)}'
        })

# Stats API
@app.route('/api/stats')
def api_stats():
    """API endpoint for blog statistics"""
    try:
        total_posts = Post.query.count()
        total_users = User.query.count()
        total_likes = Like.query.count()
        total_comments = Comment.query.count()
        auto_posts = Post.query.filter_by(is_auto_generated=True).count()
        user_posts = Post.query.filter_by(is_auto_generated=False).count()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_posts': total_posts,
                'total_users': total_users,
                'total_likes': total_likes,
                'total_comments': total_comments,
                'auto_generated_posts': auto_posts,
                'user_posts': user_posts
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/api/scheduler-status')
def api_scheduler_status():
    """API endpoint to check scheduler status"""
    return jsonify({
        'running': scheduler_running,
        'interval': scheduler_interval
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)