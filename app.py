from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import mongoengine
from werkzeug.security import generate_password_hash, check_password_hash
import os
import json
from datetime import datetime, timedelta
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from functools import wraps
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['MAIL_SUBJECT_PREFIX'] = '[SEMI]'
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here-change-in-production')

# MongoDB Configuration
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/semi_db')
MONGODB_DB = os.getenv('MONGODB_DB', 'semi_db')

# MongoDB Connection with SSL/TLS support
try:
    if 'mongodb.net' in MONGODB_URI or 'mongodb+srv' in MONGODB_URI:
        # MongoDB Atlas connection with SSL
        mongoengine.connect(
            db=MONGODB_DB,
            host=MONGODB_URI,
            tls=True,
            tlsAllowInvalidCertificates=True,  # For development only
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000
        )
    else:
        # Local MongoDB connection
        mongoengine.connect(db=MONGODB_DB, host=MONGODB_URI)
    print(f"✅ MongoDB connected successfully to: {MONGODB_DB}")
except Exception as e:
    print(f"⚠️ MongoDB connection warning: {e}")
    print("📝 App will continue but database operations may fail.")

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Admin configuration
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'mezmure048@gmail.com')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')

# Email configuration
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USER = os.getenv('EMAIL_USER', 'mezmure048@gmail.com')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', 'your-app-password')
ENABLE_EMAIL_VERIFICATION = os.getenv('ENABLE_EMAIL_VERIFICATION', 'False').lower() == 'true'

# Ensure data directory exists
os.makedirs('data', exist_ok=True)

# File Upload Configuration
UPLOAD_FOLDER = os.path.join('static', 'uploads', 'lessons')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'pdf', 'mp3', 'webp'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Admin decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

import random

# Email verification functions
def generate_otp():
    return str(random.randint(100000, 999999))

def send_otp_email(email, otp):
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = f"SEMI <{EMAIL_USER}>"
        msg['To'] = email
        msg['Subject'] = 'Verify Your SEMI Identity'
        
        # Premium HTML Template
        html_body = f"""
        <html>
        <head>
            <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;700&display=swap" rel="stylesheet">
            <style>
                body {{ font-family: 'Outfit', sans-serif; background-color: #050a10; color: #ffffff; padding: 40px; }}
                .container {{ max-width: 500px; margin: 0 auto; background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 20px; padding: 40px; backdrop-filter: blur(10px); }}
                .header {{ text-align: center; margin-bottom: 30px; }}
                .otp-box {{ background: linear-gradient(135deg, #00f2fe, #4facfe); color: #020617; font-size: 42px; font-weight: 800; text-align: center; padding: 20px; border-radius: 12px; letter-spacing: 8px; margin: 30px 0; }}
                .footer {{ font-size: 12px; color: #64748b; text-align: center; margin-top: 40px; }}
                p {{ line-height: 1.6; color: #94a3b8; }}
                strong {{ color: #ffffff; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="color: #ffffff; margin: 0;">SEMI</h1>
                    <p style="margin-top: 5px;">Secure Ecosystem for Multi-Intelligence</p>
                </div>
                <p>Hello,</p>
                <p>Use the Following verification packet to synchronize your new student account with our learning neural network.</p>
                <div class="otp-box">{otp}</div>
                <p>This synchronization code remains valid for <strong>5 minutes</strong>. If you did not initiate this request, please ignore this transmission.</p>
                <div class="footer">
                    &copy; 2025 SEMI Platform. All rights reserved.<br>
                    Global ASL Learning Hub
                </div>
            </div>
        </body>
        </html>
        """
        
        plain_text_body = f"Welcome to SEMI! Your verification code is: {otp}. It expires in 5 minutes."
        
        msg.attach(MIMEText(plain_text_body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))
        
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL_USER, email, text)
        server.quit()
        return True
    except Exception as e:
        import traceback
        print(f"CRITICAL: Failed to transmit OTP to {email}")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Error Detail: {str(e)}")
        return False

def send_admin_notification(subject, message):
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = f"SEMI Admin <{EMAIL_USER}>"
        msg['To'] = ADMIN_EMAIL
        msg['Subject'] = f'SEMI Admin: {subject}'
        
        html_content = f"""
        <html>
        <body style="font-family: sans-serif; background-color: #050a10; color: #ffffff; padding: 20px;">
            <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 25px;">
                <h2 style="color: #4facfe; margin-top: 0;">System Intelligence Report</h2>
                <p style="color: #94a3b8; line-height: 1.6;">{message.replace('\\n', '<br>')}</p>
                <hr style="border: none; border-top: 1px solid rgba(255,255,255,0.1); margin: 20px 0;">
                <p style="font-size: 12px; color: #64748b;">Automated Admin Transmission • SEMI Protocol</p>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(message, 'plain'))
        msg.attach(MIMEText(html_content, 'html'))
        
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL_USER, ADMIN_EMAIL, text)
        server.quit()
        return True
    except Exception as e:
        print(f"Admin notification error: {e}")
        return False



# Database Models
class User(UserMixin, mongoengine.Document):
    meta = {'collection': 'users'}
    id = mongoengine.StringField(primary_key=True, default=lambda: str(uuid.uuid4()))
    username = mongoengine.StringField(unique=True, required=True)
    email = mongoengine.StringField(unique=True, required=True)
    password_hash = mongoengine.StringField()
    first_name = mongoengine.StringField()
    last_name = mongoengine.StringField()
    avatar_url = mongoengine.StringField()
    learning_goal = mongoengine.StringField()
    motivation = mongoengine.StringField()
    created_at = mongoengine.DateTimeField(default=datetime.utcnow)
    last_login = mongoengine.DateTimeField()
    is_active_user = mongoengine.BooleanField(default=True)
    is_verified = mongoengine.BooleanField(default=False)
    is_admin = mongoengine.BooleanField(default=False)
    otp = mongoengine.StringField()
    otp_expiry = mongoengine.DateTimeField()
    status = mongoengine.StringField(default='pending') # pending, approved, rejected

    def get_id(self):
        return str(self.id)
    
    @property
    def is_active(self):
        return self.is_active_user

class CourseCategory(mongoengine.Document):
    meta = {'collection': 'course_categories'}
    id = mongoengine.StringField(primary_key=True, default=lambda: str(uuid.uuid4()))
    name = mongoengine.StringField(required=True)
    description = mongoengine.StringField()
    icon = mongoengine.StringField(default='📚')
    order = mongoengine.IntField(default=0)
    is_active = mongoengine.BooleanField(default=True)
    created_at = mongoengine.DateTimeField(default=datetime.utcnow)

class Course(mongoengine.Document):
    meta = {'collection': 'courses'}
    id = mongoengine.StringField(primary_key=True, default=lambda: str(uuid.uuid4()))
    title = mongoengine.StringField(required=True)
    description = mongoengine.StringField()
    category = mongoengine.StringField()  # Legacy string category
    category_id = mongoengine.StringField()  # Subject Category Reference
    difficulty = mongoengine.StringField()
    duration_weeks = mongoengine.IntField()
    lessons_count = mongoengine.IntField()
    is_featured = mongoengine.BooleanField(default=True)
    created_at = mongoengine.DateTimeField(default=datetime.utcnow)
    is_active = mongoengine.BooleanField(default=True)

class Translation(mongoengine.Document):
    meta = {'collection': 'translations'}
    id = mongoengine.StringField(primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = mongoengine.StringField(required=True)
    original_text = mongoengine.StringField(required=True)
    translated_text = mongoengine.StringField()
    translation_type = mongoengine.StringField(default='text')
    created_at = mongoengine.DateTimeField(default=datetime.utcnow)
    is_favorite = mongoengine.BooleanField(default=False)

class Progress(mongoengine.Document):
    meta = {'collection': 'progress'}
    user_id = mongoengine.StringField(unique=True, required=True)
    category = mongoengine.StringField()
    level = mongoengine.IntField(default=1)
    experience_points = mongoengine.IntField(default=0)
    lessons_completed = mongoengine.IntField(default=0)
    quizzes_passed = mongoengine.IntField(default=0)
    streak_count = mongoengine.IntField(default=0)
    max_streak = mongoengine.IntField(default=0)
    last_activity_date = mongoengine.DateTimeField()
    last_updated = mongoengine.DateTimeField(default=datetime.utcnow)

class DailyActivity(mongoengine.Document):
    meta = {'collection': 'daily_activity', 'indexes': ['user_id', 'date']}
    user_id = mongoengine.StringField(required=True)
    date = mongoengine.StringField(required=True) # YYYY-MM-DD
    count = mongoengine.IntField(default=1)

class QuizAttempt(mongoengine.Document):
    meta = {'collection': 'quiz_attempts'}
    id = mongoengine.StringField(primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = mongoengine.StringField(required=True)
    difficulty = mongoengine.StringField(required=True)  # beginner, intermediate, advanced
    total_questions = mongoengine.IntField(required=True)
    correct_answers = mongoengine.IntField(default=0)
    incorrect_answers = mongoengine.IntField(default=0)
    score_percentage = mongoengine.FloatField(default=0.0)
    time_taken_seconds = mongoengine.IntField(default=0)
    max_streak = mongoengine.IntField(default=0)
    answers = mongoengine.ListField()  # List of answer objects
    created_at = mongoengine.DateTimeField(default=datetime.utcnow)
    completed = mongoengine.BooleanField(default=False)

class QuizQuestion(mongoengine.Document):
    meta = {'collection': 'quiz_questions'}
    id = mongoengine.StringField(primary_key=True, default=lambda: str(uuid.uuid4()))
    question_text = mongoengine.StringField(required=True)
    sign_url = mongoengine.StringField(required=True)  # Path to GIF/image (Legacy single URL)
    media_urls = mongoengine.ListField(mongoengine.StringField())  # List of paths for sequence support
    options = mongoengine.ListField(required=True)  # List of 4 options
    correct_answer_index = mongoengine.IntField(required=True)  # 0-3
    difficulty = mongoengine.StringField(required=True)  # beginner, intermediate, advanced
    category = mongoengine.StringField(default='words')  # words, phrases, alphabet
    times_shown = mongoengine.IntField(default=0)
    times_correct = mongoengine.IntField(default=0)
    created_at = mongoengine.DateTimeField(default=datetime.utcnow)
    is_active = mongoengine.BooleanField(default=True)

class Achievement(mongoengine.Document):
    meta = {'collection': 'achievements'}
    id = mongoengine.StringField(primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = mongoengine.StringField(required=True)
    achievement_type = mongoengine.StringField(required=True)  # first_quiz, perfect_score, streak_master, etc.
    title = mongoengine.StringField(required=True)
    description = mongoengine.StringField()
    icon = mongoengine.StringField(default='🏆')
    earned_at = mongoengine.DateTimeField(default=datetime.utcnow)
    metadata = mongoengine.DictField()  # Additional data like score, streak, etc.

class Feedback(mongoengine.Document):
    meta = {'collection': 'feedback'}
    id = mongoengine.StringField(primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = mongoengine.StringField(required=True)
    username = mongoengine.StringField()
    category = mongoengine.StringField(required=True)  # Experience, Technical, Content, Other
    rating = mongoengine.IntField(min_value=1, max_value=5)
    subject = mongoengine.StringField(required=True)
    message = mongoengine.StringField(required=True)
    created_at = mongoengine.DateTimeField(default=datetime.utcnow)
    is_read = mongoengine.BooleanField(default=False)
    admin_note = mongoengine.StringField()


# Gamification Logic
def update_user_activity(user_id):
    """Update user streak and daily activity"""
    now = datetime.utcnow()
    today_str = now.strftime('%Y-%m-%d')
    
    # 1. Update Daily Activity
    activity = DailyActivity.objects(user_id=user_id, date=today_str).first()
    if activity:
        activity.count += 1
        activity.save()
    else:
        DailyActivity(user_id=user_id, date=today_str, count=1).save()
    
    # 2. Update Streak
    progress = Progress.objects(user_id=user_id).first()
    if not progress:
        progress = Progress(user_id=user_id)
    
    last_active = progress.last_activity_date
    if last_active:
        yesterday = (now - timedelta(days=1)).strftime('%Y-%m-%d')
        last_active_str = last_active.strftime('%Y-%m-%d')
        
        if last_active_str == today_str:
            # Already active today, streak stays the same
            pass
        elif last_active_str == yesterday:
            # Consecutive day!
            progress.streak_count += 1
        else:
            # Streak broken
            progress.streak_count = 1
    else:
        # First activity ever
        progress.streak_count = 1
    
    if progress.streak_count > progress.max_streak:
        progress.max_streak = progress.streak_count
        
    progress.last_activity_date = now
    progress.save()
    
    # 3. Check for Streak Achievements
    check_streak_achievements(user_id, progress.streak_count)
    return progress

def check_streak_achievements(user_id, streak):
    milestones = [
        (3, 'Daily Learner', '3-day learning streak!', '🔥'),
        (7, 'Weekly Warrior', '7-day learning streak!', '🛡️'),
        (30, 'Hand-Talker Hero', '30-day learning streak!', '🦸'),
        (100, 'Master Interpreter', '100-day learning streak!', '👑')
    ]
    
    for count, title, desc, icon in milestones:
        if streak == count:
            if not Achievement.objects(user_id=user_id, title=title).first():
                Achievement(
                    user_id=user_id,
                    achievement_type='streak_milestone',
                    title=title,
                    description=desc,
                    icon=icon,
                    metadata={'streak': streak}
                ).save()

@app.route('/api/user/heatmap')
@login_required
def get_heatmap_data():
    # Get last 365 days of activity
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=365)
    
    activities = DailyActivity.objects(
        user_id=current_user.id,
        date__gte=start_date.strftime('%Y-%m-%d')
    )
    
    heatmap = {a.date: a.count for a in activities}
    return jsonify({'success': True, 'heatmap': heatmap})

class LessonCategory(mongoengine.Document):
    meta = {'collection': 'lesson_categories'}
    id = mongoengine.StringField(primary_key=True, default=lambda: str(uuid.uuid4()))
    name = mongoengine.StringField(required=True)
    description = mongoengine.StringField()
    icon = mongoengine.StringField(default='📚')
    difficulty_level = mongoengine.StringField(default='beginner')  # beginner, intermediate, advanced
    course_id = mongoengine.StringField()  # Parent course ID
    order = mongoengine.IntField(default=0)
    is_active = mongoengine.BooleanField(default=True)
    created_at = mongoengine.DateTimeField(default=datetime.utcnow)

class Lesson(mongoengine.Document):
    meta = {'collection': 'lessons'}
    id = mongoengine.StringField(primary_key=True, default=lambda: str(uuid.uuid4()))
    category_id = mongoengine.StringField(required=True)
    title = mongoengine.StringField(required=True)
    description = mongoengine.StringField()
    duration_minutes = mongoengine.IntField(default=15)
    difficulty_level = mongoengine.StringField(default='beginner')
    order = mongoengine.IntField(default=0)
    is_active = mongoengine.BooleanField(default=True)
    created_at = mongoengine.DateTimeField(default=datetime.utcnow)
    updated_at = mongoengine.DateTimeField(default=datetime.utcnow)

class LessonStep(mongoengine.Document):
    meta = {'collection': 'lesson_steps'}
    id = mongoengine.StringField(primary_key=True, default=lambda: str(uuid.uuid4()))
    lesson_id = mongoengine.StringField(required=True)
    title = mongoengine.StringField(required=True)
    description = mongoengine.StringField()
    content_type = mongoengine.StringField(default='video')  # video, gif, text, image
    content_url = mongoengine.StringField()  # Path to video/GIF file
    transcript = mongoengine.StringField()  # Translation or transcript text
    order = mongoengine.IntField(default=0)
    created_at = mongoengine.DateTimeField(default=datetime.utcnow)



def init_db():
    # MongoDB creates collections automatically on first document insertion
    # Create admin user if it doesn't exist
    admin = User.objects(is_admin=True).first()
    if not admin:
        admin = User(
            username='admin',
            email=ADMIN_EMAIL,
            password_hash=generate_password_hash(ADMIN_PASSWORD),
            first_name='Admin',
            last_name='User',
            is_active_user=True,
            is_verified=True,
            is_admin=True,
            status='approved'
        )
        admin.save()
        print("Admin user created.")

    # SignLearn Course Catalog Seeding
    if not CourseCategory.objects().first():
        subjects = [
            CourseCategory(name='Literature', description='Master reading and writing through ASL-narrated analysis.', icon='📖', order=1),
            CourseCategory(name='Sciences', description='Biology, Physics & Chemistry with visual demonstrations.', icon='🔬', order=2),
            CourseCategory(name='Mathematics', description='Step-by-step algebra and geometry from root concepts.', icon='🧮', order=3)
        ]
        for s in subjects: s.save()
        print("Seeded course categories.")

    lit_cat = CourseCategory.objects(name='Literature').first()
    
    if not Course.objects().first():
        Course(
            title="Basic ASL", 
            description="Learn the fundamentals of American Sign Language, including the alphabet and basic greetings.",
            category="beginner", 
            category_id=str(lit_cat.id) if lit_cat else None,
            difficulty="Beginner", 
            duration_weeks=4, 
            lessons_count=8,
            is_featured=True
        ).save()
        
        Course(
            title="Intermediate ASL", 
            description="Expand your vocabulary and learn common conversational phrases and sentence structures.",
            category="intermediate", 
            category_id=str(lit_cat.id) if lit_cat else None,
            difficulty="Intermediate", 
            duration_weeks=6, 
            lessons_count=12,
            is_featured=True
        ).save()
        
        Course(
            title="Advanced ASL", 
            description="Master complex signs, non-manual markers, and advanced storytelling in ASL.",
            category="advanced", 
            category_id=str(lit_cat.id) if lit_cat else None,
            difficulty="Advanced", 
            duration_weeks=8, 
            lessons_count=16,
            is_featured=True
        ).save()
        print("Sample courses seeded.")
    else:
        if lit_cat:
            Course.objects(category_id=None).update(set__category_id=str(lit_cat.id), set__is_featured=True)
    
    # Seed quiz questions if none exist or are low in count
    expected_beginner = 10
    expected_intermediate = 10
    expected_advanced = 10
    
    current_count = QuizQuestion.objects().count()
    if current_count < (expected_beginner + expected_intermediate + expected_advanced):
        # We'll use a dictionary to avoid duplicates during seeding
        new_questions = [
            # Beginner (10)
            {"text": "What word does this sign represent?", "url": "/static/sign/words/hello.gif", "opts": ["Hello", "Goodbye", "Please", "Thank you"], "correct": 0, "diff": "beginner"},
            {"text": "What word does this sign represent?", "url": "/static/sign/words/family.gif", "opts": ["Friends", "People", "Family", "Community"], "correct": 2, "diff": "beginner"},
            {"text": "What word does this sign represent?", "url": "/static/sign/words/bread.gif", "opts": ["Cake", "Bread", "Cheese", "Meat"], "correct": 1, "diff": "beginner"},
            {"text": "What word does this sign represent?", "url": "/static/sign/words/water.gif", "opts": ["Juice", "Water", "Milk", "Tea"], "correct": 1, "diff": "beginner"},
            {"text": "What word does this sign represent?", "url": "/static/sign/words/happy.gif", "opts": ["Sad", "Brave", "Happy", "Excited"], "correct": 2, "diff": "beginner"},
            {"text": "What word does this sign represent?", "url": "/static/sign/words/apple.gif", "opts": ["Orange", "Apple", "Grape", "Peach"], "correct": 1, "diff": "beginner"},
            {"text": "What word does this sign represent?", "url": "/static/sign/words/banana.gif", "opts": ["Banana", "Apple", "Lemon", "Mango"], "correct": 0, "diff": "beginner"},
            {"text": "What word does this sign represent?", "url": "/static/sign/words/ball.gif", "opts": ["Box", "Square", "Ball", "Circle"], "correct": 2, "diff": "beginner"},
            {"text": "What word does this sign represent?", "url": "/static/sign/words/hat.gif", "opts": ["Shirt", "Shoes", "Hat", "Gloves"], "correct": 2, "diff": "beginner"},
            {"text": "What word does this sign represent?", "url": "/static/sign/words/shoes.gif", "opts": ["Pants", "Socks", "Shoes", "Hat"], "correct": 2, "diff": "beginner"},

            # Intermediate (10)
            {"text": "What word does this sign represent?", "url": "/static/sign/words/birthday.gif", "opts": ["Holiday", "Birthday", "Party", "Celebration"], "correct": 1, "diff": "intermediate"},
            {"text": "What word does this sign represent?", "url": "/static/sign/words/doctor.gif", "opts": ["Teacher", "Police", "Doctor", "Nurse"], "correct": 2, "diff": "intermediate"},
            {"text": "What word does this sign represent?", "url": "/static/sign/words/weather.gif", "opts": ["Sky", "Weather", "Nature", "Rain"], "correct": 1, "diff": "intermediate"},
            {"text": "What word does this sign represent?", "url": "/static/sign/words/morning.gif", "opts": ["Night", "Noon", "Morning", "Evening"], "correct": 2, "diff": "intermediate"},
            {"text": "What word does this sign represent?", "url": "/static/sign/words/afternoon.gif", "opts": ["Afternoon", "Morning", "Evening", "Night"], "correct": 0, "diff": "intermediate"},
            {"text": "What word does this sign represent?", "url": "/static/sign/words/evening.gif", "opts": ["Sunset", "Evening", "Midnight", "Morning"], "correct": 1, "diff": "intermediate"},
            {"text": "What word does this sign represent?", "url": "/static/sign/words/good night.gif", "opts": ["Goodbye", "Good night", "Sleepy", "Bedtime"], "correct": 1, "diff": "intermediate"},
            {"text": "What word does this sign represent?", "url": "/static/sign/words/today.gif", "opts": ["Tomorrow", "Yesterday", "Daily", "Today"], "correct": 3, "diff": "intermediate"},
            {"text": "What word does this sign represent?", "url": "/static/sign/words/tomorrow.gif", "opts": ["Today", "Yesterday", "Future", "Tomorrow"], "correct": 3, "diff": "intermediate"},
            {"text": "What word does this sign represent?", "url": "/static/sign/words/weekend.gif", "opts": ["Weekday", "Holiday", "Weekend", "Vacation"], "correct": 2, "diff": "intermediate"},

            # Advanced (10)
            {"text": "What word does this sign represent?", "url": "/static/sign/words/annually.gif", "opts": ["Monthly", "Weekly", "Daily", "Annually"], "correct": 3, "diff": "advanced"},
            {"text": "What word does this sign represent?", "url": "/static/sign/words/blizzard.gif", "opts": ["Snowfall", "Storm", "Blizzard", "Hail"], "correct": 2, "diff": "advanced"},
            {"text": "What word does this sign represent?", "url": "/static/sign/words/emergency.gif", "opts": ["Accident", "Emergency", "Crisis", "Urgent"], "correct": 1, "diff": "advanced"},
            {"text": "What word does this sign represent?", "url": "/static/sign/words/midnight.gif", "opts": ["Twilight", "Noon", "Midnight", "Darkness"], "correct": 2, "diff": "advanced"},
            {"text": "What word does this sign represent?", "url": "/static/sign/words/sunrise.gif", "opts": ["Dawn", "Sunrise", "Morning", "Horizon"], "correct": 1, "diff": "advanced"},
            {"text": "What word does this sign represent?", "url": "/static/sign/words/sunset.gif", "opts": ["Dusk", "Sunset", "Evening", "Afterglow"], "correct": 1, "diff": "advanced"},
            {"text": "What word does this sign represent?", "url": "/static/sign/words/exhausted.gif", "opts": ["Tired", "Sleepy", "Exhausted", "Weak"], "correct": 2, "diff": "advanced"},
            {"text": "What word does this sign represent?", "url": "/static/sign/words/inspired.gif", "opts": ["Creative", "Inspired", "Motivated", "Excited"], "correct": 1, "diff": "advanced"},
            {"text": "What word does this sign represent?", "url": "/static/sign/words/awesome.gif", "opts": ["Great", "Wonderful", "Awesome", "Fantastic"], "correct": 2, "diff": "advanced"},
            {"text": "What word does this sign represent?", "url": "/static/sign/words/everything.gif", "opts": ["Something", "Anything", "Nothing", "Everything"], "correct": 3, "diff": "advanced"},
        ]

        added_count = 0
        for q_data in new_questions:
            # Check if this specific sign is already in this difficulty to avoid exact dups
            if not QuizQuestion.objects(sign_url=q_data["url"], difficulty=q_data["diff"]).first():
                QuizQuestion(
                    question_text=q_data["text"],
                    sign_url=q_data["url"],
                    options=q_data["opts"],
                    correct_answer_index=q_data["correct"],
                    difficulty=q_data["diff"],
                    category="words",
                    is_active=True
                ).save()
                added_count += 1
        
        if added_count > 0:
            print(f"Seeded {added_count} new quiz questions.")
    
    # Seed lesson categories and lessons if none exist
    if not LessonCategory.objects().first():
        # Get basic_course for linking
        basic_course = Course.objects(title="Basic ASL").first()
        intermediate_course = Course.objects(title="Intermediate ASL").first()
        
        # Create categories
        greetings_cat = LessonCategory(
            name="Greetings & Basics",
            description="Learn to introduce yourself and handle basic greetings.",
            icon="👋",
            difficulty_level="beginner",
            course_id=str(basic_course.id) if basic_course else None,
            order=1
        )
        greetings_cat.save()
        
        family_cat = LessonCategory(
            name="Family Circle",
            description="Master signs for siblings, parents, and extended family.",
            icon="👨‍👩‍👧‍👦",
            difficulty_level="beginner",
            course_id=str(intermediate_course.id) if intermediate_course else None,
            order=2
        )
        family_cat.save()
        
        # Create lessons for Greetings & Basics
        greetings_lesson = Lesson(
            category_id=str(greetings_cat.id),
            title="Essential Greetings",
            description="Learn the most common greetings in ASL",
            duration_minutes=15,
            difficulty_level="beginner",
            order=1
        )
        greetings_lesson.save()
        
        # Create steps for greetings lesson
        LessonStep(
            lesson_id=str(greetings_lesson.id),
            title="Wave Hello",
            description="The most universal sign. A simple wave of the open hand.",
            content_type="video",
            content_url="/static/sign/words/hello.gif",
            order=1
        ).save()
        
        LessonStep(
            lesson_id=str(greetings_lesson.id),
            title="Say Goodbye",
            description="A friendly farewell gesture.",
            content_type="video",
            content_url="/static/sign/words/goodbye.gif",
            order=2
        ).save()
        
        # Create lessons for Family Circle
        family_lesson = Lesson(
            category_id=str(family_cat.id),
            title="Family Members",
            description="Learn signs for immediate family members",
            duration_minutes=20,
            difficulty_level="beginner",
            order=1
        )
        family_lesson.save()
        
        LessonStep(
            lesson_id=str(family_lesson.id),
            title="Family Sign",
            description="The general sign for family - bringing hands together.",
            content_type="video",
            content_url="/static/sign/words/family.gif",
            order=1
        ).save()
        
        print("Seeded lesson categories, lessons, and steps.")

    # --- Sign Lab Foundations (course_id=None) ---
    asl_foundations = LessonCategory.objects(name="ASL Foundations", course_id=None).first()
    if not asl_foundations:
        asl_foundations = LessonCategory(
            name="ASL Foundations",
            description="Master the foundational building blocks of American Sign Language.",
            icon="🧠",
            difficulty_level="beginner",
            course_id=None,
            order=1
        ).save()

    # (A) Complete ASL Alphabet
    asl_alphabet = Lesson.objects(category_id=str(asl_foundations.id), title="Complete ASL Alphabet (A-Z)").first()
    if not asl_alphabet:
        asl_alphabet = Lesson(
            category_id=str(asl_foundations.id),
            title="Complete ASL Alphabet (A-Z)",
            description="Learn the foundational shapes recognized by SEMI's Neural Engine.",
            duration_minutes=10,
            difficulty_level="beginner",
            order=1
        ).save()
        
        letters = "abcdefghijklmnopqrstuvwxyz"
        for i, char in enumerate(letters):
            LessonStep(
                lesson_id=str(asl_alphabet.id),
                title=f"Letter {char.upper()}",
                description=f"Form the letter '{char.upper()}' in ASL.",
                content_type="image",
                content_url=f"/static/sign/letters/{char}.jpg",
                order=i+1
            ).save()

    # (B) Essential ASL Greetings
    asl_greetings = Lesson.objects(category_id=str(asl_foundations.id), title="Essential AI Greetings").first()
    if not asl_greetings:
        asl_greetings = Lesson(
            category_id=str(asl_foundations.id),
            title="Essential AI Greetings",
            description="Master the basic signals for 'Hello', 'Yes', and 'No'.",
            duration_minutes=5,
            difficulty_level="beginner",
            order=2
        ).save()
        
        greetings = [
            ("Hello", "A simple wave to start a conversation.", "/static/sign/words/hello.gif"),
            ("Yes", "A nodding-like fist movement.", "/static/sign/words/yes.gif"),
            ("No", "A quick pinching motion with index, middle, and thumb.", "/static/sign/words/no.gif")
        ]
        for i, (title, desc, url) in enumerate(greetings):
            LessonStep(
                lesson_id=str(asl_greetings.id),
                title=title,
                description=desc,
                content_type="video",
                content_url=url,
                order=i+1
            ).save()

    # --- Amharic Foundations (course_id=None) ---
    amharic_foundations = LessonCategory.objects(name="Amharic Foundations", course_id=None).first()
    if not amharic_foundations:
        amharic_foundations = LessonCategory(
            name="Amharic Foundations",
            description="Explore the rich 231-character system of Ethiopian Sign Language.",
            icon="🇪🇹",
            difficulty_level="beginner",
            course_id=None,
            order=2
        ).save()

    # (C) Amharic Alphabet Families (Family-by-Family Training)
    try:
        amharic_data_path = 'data/amharic_signs.json'
        if os.path.exists(amharic_data_path):
            with open(amharic_data_path, 'r', encoding='utf-8') as f:
                amharic_data = json.load(f)
                letters = amharic_data.get('letters', [])
            
            # Clean up old massive lesson if it exists
            old_amharic_lesson = Lesson.objects(category_id=str(amharic_foundations.id), title="Ethiopian Alphabet (231 Signs)").first()
            if old_amharic_lesson:
                LessonStep.objects(lesson_id=str(old_amharic_lesson.id)).delete()
                old_amharic_lesson.delete()

            # Group into families of 7
            for i in range(0, len(letters), 7):
                family_chars = letters[i:i+7]
                if not family_chars: continue
                
                base_char = family_chars[0]
                lesson_title = f"The '{base_char}' Character Family"
                
                # Check if lesson already exists
                family_lesson = Lesson.objects(category_id=str(amharic_foundations.id), title=lesson_title).first()
                if not family_lesson:
                    family_lesson = Lesson(
                        category_id=str(amharic_foundations.id),
                        title=lesson_title,
                        description=f"Master the '{base_char}' family: {' '.join(family_chars)}",
                        duration_minutes=5,
                        difficulty_level="beginner",
                        order=(i // 7) + 1
                    ).save()
                    
                    for j, char in enumerate(family_chars):
                        LessonStep(
                            lesson_id=str(family_lesson.id),
                            title=f"Character {char}",
                            description=f"Sign the Amharic character '{char}'",
                            content_type="image",
                            content_url=f"/static/sign/Amharic/letters/{char}.jpg",
                            order=j+1
                        ).save()
            print(f"Seeded {len(letters)//7} Amharic alphabet family modules.")
    except Exception as e:
        print(f"Error seeding Amharic families: {e}")

# Initialize database
try:
    init_db()
except Exception as e:
    print(f"⚠️ Database initialization skipped: {e}")
    print("📝 App will start but admin user and seed data may not be available.")

@login_manager.user_loader
def load_user(user_id):
    return User.objects(id=user_id).first()

# Routes
@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('home.html')

# PWA Routes
@app.route('/offline')
def offline():
    """Offline fallback page for PWA"""
    return render_template('offline.html')

@app.route('/ping', methods=['HEAD', 'GET'])
def ping():
    """Health check endpoint for PWA connection testing"""
    return '', 200

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        user = User.objects(email=email).first()
        
        if user and check_password_hash(user.password_hash, password):
            if ENABLE_EMAIL_VERIFICATION and not user.is_verified:
                # Generate new OTP for login attempt if unverified
                otp = generate_otp()
                user.otp = otp
                from datetime import timedelta
                user.otp_expiry = datetime.utcnow() + timedelta(minutes=10)
                user.save()
                send_otp_email(user.email, otp)
                session['verifying_email'] = user.email
                return jsonify({'success': True, 'redirect': url_for('verify_otp'), 'message': 'Account not verified. New OTP sent.'})
            
            if user.status != 'approved':
                if user.status == 'pending':
                    return jsonify({'success': False, 'message': 'Your account is pending admin approval.'})
                elif user.status == 'rejected':
                    return jsonify({'success': False, 'message': 'Your account has been rejected.'})
            
            user.last_login = datetime.utcnow()
            user.save()
            login_user(user)
            
            if user.is_admin:
                session['admin_mode'] = True
            
            redirect_url = url_for('admin_dashboard') if user.is_admin else url_for('dashboard')
            return jsonify({'success': True, 'redirect': redirect_url})
        else:
            return jsonify({'success': False, 'message': 'Invalid email or password'})
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        first_name = data.get('first_name')
        last_name = data.get('last_name')

        # Backend Password Strength Validation
        import re
        errors = []
        if len(password) < 8:
            errors.append('Password must be at least 8 characters long')
        if not re.search(r"[A-Z]", password):
            errors.append('Password must contain at least one uppercase letter')
        if not re.search(r"[0-9]", password):
            errors.append('Password must contain at least one digit')
        if not re.search(r"[@$!%*?&]", password):
            errors.append('Password must contain at least one special character (@$!%*?&)')
        
        if errors:
            return jsonify({'success': False, 'message': errors[0]})
        
        password = password.strip() if password else ""
        confirm_password = data.get('confirm_password', '').strip()

        if password != confirm_password:
            return jsonify({'success': False, 'message': 'Passwords do not match. Please ensure no leading/trailing spaces.'})

        if User.objects(email=email).first():
            return jsonify({'success': False, 'message': 'Email already registered'})
        
        user_id = str(uuid.uuid4())
        otp = generate_otp() if ENABLE_EMAIL_VERIFICATION else None
        
        from datetime import timedelta
        new_user = User(
            id=user_id,
            username=email.split('@')[0], # Fallback username
            email=email,
            password_hash=generate_password_hash(password),
            first_name=first_name,
            last_name=last_name,
            is_active_user=True,
            is_verified=not ENABLE_EMAIL_VERIFICATION,
            is_admin=False,
            otp=otp,
            otp_expiry=datetime.utcnow() + timedelta(minutes=5) if otp else None,
            status='approved' if not ENABLE_EMAIL_VERIFICATION else 'pending'
        )
        new_user.save()
        
        if ENABLE_EMAIL_VERIFICATION:
            if send_otp_email(email, otp):
                session['verifying_email'] = email
                return jsonify({'success': True, 'redirect': url_for('verify_otp'), 'message': 'OTP sent to your email.'})
            else:
                new_user.delete()
                return jsonify({'success': False, 'message': 'Failed to send OTP.'})
        else:
            # Create progress record for non-verification flow
            Progress(user_id=user_id, category='basic', level=1).save()
            return jsonify({'success': True, 'message': 'Registration successful!'})
    
    return render_template('register.html')

@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    email = session.get('verifying_email')
    if not email:
        return redirect(url_for('register'))
    
    if request.method == 'POST':
        data = request.get_json()
        otp_input = data.get('otp')
        
        user = User.objects(email=email).first()
        if not user:
            return jsonify({'success': False, 'message': 'User not found.'})
        
        if user.otp == otp_input and user.otp_expiry > datetime.utcnow():
            user.is_verified = True
            user.otp = None
            user.otp_expiry = None
            user.save()
            
            # Create progress record now that they're verified
            if not Progress.objects(user_id=user.id).first():
                Progress(user_id=user.id, category='basic', level=1).save()
            
            session.pop('verifying_email', None)
            return jsonify({'success': True, 'redirect': url_for('login'), 'message': 'Email verified! Please wait for admin approval.'})
        else:
            return jsonify({'success': False, 'message': 'Invalid or expired OTP.'})
            
    return render_template('verify_otp.html', email=email)

@app.route('/resend_otp', methods=['POST'])
def resend_otp():
    email = session.get('verifying_email')
    if not email:
        return jsonify({'success': False, 'message': 'Session expired. Please register again.'})
    
    user = User.objects(email=email).first()
    if not user:
        return jsonify({'success': False, 'message': 'User not found.'})
    
    otp = generate_otp()
    user.otp = otp
    user.otp_expiry = datetime.utcnow() + timedelta(minutes=5)
    user.save()
    
    if send_otp_email(email, otp):
        return jsonify({'success': True, 'message': 'A new verification code has been transmitted.'})
    else:
        return jsonify({'success': False, 'message': 'Failed to transmit verification packet.'})

@app.route('/logout')
@login_required
def logout():
    session.pop('admin_mode', None)
    logout_user()
    return redirect(url_for('home'))

@app.route('/switch_mode')
@login_required
def switch_mode():
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))
    
    current_mode = session.get('admin_mode', True)
    session['admin_mode'] = not current_mode
    
    target = 'admin_dashboard' if session['admin_mode'] else 'dashboard'
    return redirect(url_for(target))

@app.route('/dashboard')
@login_required
def dashboard():
    # Get user statistics
    user_translations = Translation.objects(user_id=current_user.id)
    user_favorites = Translation.objects(user_id=current_user.id, is_favorite=True)
    user_progress = Progress.objects(user_id=current_user.id).first()
    user_achievements = Achievement.objects(user_id=current_user.id).order_by('-earned_at').limit(4)
    
    total_translations = user_translations.count()
    total_favorites = user_favorites.count()
    recent_translations = Translation.objects(user_id=current_user.id).order_by('-created_at').limit(5)
    
    return render_template('dashboard.html', 
                         total_translations=total_translations,
                         total_favorites=total_favorites,
                         recent_translations=recent_translations,
                         progress=user_progress,
                         achievements=user_achievements)

@app.route('/translator')
@login_required
def translator():
    return render_template('translator.html')

@app.route('/translate', methods=['POST'])
@login_required
def translate():
    data = request.get_json()
    text = data.get('text', '').strip()
    language = data.get('language', 'english').lower()  # 'english' or 'amharic'
    
    if not text:
        return jsonify({'success': False, 'message': 'Please enter text to translate'})
    
    # Auto-detect Language if not specified
    if language == 'auto':
        # Check if text contains Amharic characters
        amharic_chars = set('ሀሁሂሃሄህሆለሉሊላሌልሎሐሑሒሓሔሕሖመሙሚማሜምሞሠሡሢሣሤሥሦረሩሪራሬርሮሰሱሲሳሴስሶሸሹሺሻሼሽሾቀቁቂቃቄቅቆበቡቢባቤብቦተቱቲታቴትቶቸቹቺቻቼችቾነኑኒናኔንኖኘኙኚኛኜኝኞአኡኢኣኤእኦከኩኪካኬክኮኸኹኺኻኼኽኾወዉዊዋዌውዎዐዑዒዓዔዕዖዘዙዚዛዜዝዞዠዡዢዣዤዥዦየዩዪያዬይዮደዱዲዳዴድዶጀጁጂጃጄጅጆገጉጊጋጌግጎጠጡጢጣጤጥጦጨጩጪጫጬጭጮጰጱጲጳጴጵጶፀፁፂፃፄፅፆፈፉፊፋፌፍፎፐፑፒፓፔፕፖ')
        has_amharic = any(char in amharic_chars for char in text)
        language = 'amharic' if has_amharic else 'english'
    
    sign_assets = []
    
    if language == 'amharic':
        # Amharic to Ethiopian Sign Language
        WORDS_DIR = 'static/sign/Amharic/words'
        LETTERS_DIR = 'static/sign/Amharic/letters'
        
        # Load Amharic sign mappings
        amharic_data_path = 'data/amharic_signs.json'
        amharic_words = {}
        if os.path.exists(amharic_data_path):
            with open(amharic_data_path, 'r', encoding='utf-8') as f:
                amharic_data = json.load(f)
                amharic_words = amharic_data.get('words', {})
        
        # Split text into words
        words = text.split()
        
        for word in words:
            word_found = False
            
            # Try to find word sign
            word_file = f"{word}.gif"
            word_path = os.path.join(WORDS_DIR, word_file)
            if os.path.exists(word_path):
                sign_assets.append({
                    'type': 'word',
                    'word': word,
                    'url': f'/static/sign/Amharic/words/{word_file}'
                })
                word_found = True
            
            # If word not found, fingerspell each character
            if not word_found:
                for char in word:
                    char_file = f"{char}.jpg"
                    char_path = os.path.join(LETTERS_DIR, char_file)
                    if os.path.exists(char_path):
                        sign_assets.append({
                            'type': 'letter',
                            'char': char,
                            'url': f'/static/sign/Amharic/letters/{char_file}'
                        })
                sign_assets.append({'type': 'break'})
        
        # Remove trailing break
        if sign_assets and sign_assets[-1]['type'] == 'break':
            sign_assets.pop()
        
        normalized_text = text  # Keep Amharic as-is
        
    else:
        # English to ASL (existing logic)
        LOCATION_DATABASE = {
            'addis', 'ethiopia', 'school', 'church', 'home', 'office', 
            'hospital', 'park', 'store', 'restaurant', 'city', 'town',
            'building', 'room', 'class', 'library', 'gym', 'cafe',
            'street', 'road', 'house', 'apartment', 'hotel', 'airport'
        }
        
        # Semantic Pattern Detection
        text_lower = text.lower()
        words_list = text.split()
        implied_words = []
        
        # Pattern: "welcome to [PLACE]"
        if 'welcome' in text_lower and 'to' in text_lower:
            try:
                to_index = [w.lower() for w in words_list].index('to')
                if to_index + 1 < len(words_list):
                    next_word = words_list[to_index + 1].lower()
                    if next_word in LOCATION_DATABASE:
                        implied_words.append('ARRIVE')
            except ValueError:
                pass
        
        # ASL Grammar Normalization
        asl_stop_words = {'is', 'am', 'are', 'the', 'a', 'an', 'was', 'were', 'be', 'been', 'being'}
        
        if not implied_words:
            asl_stop_words.add('to')
        
        original_words = text.split()
        words = [word for word in original_words if word.lower() not in asl_stop_words]
        
        # Inject implied words
        if implied_words:
            if 'welcome' in text_lower and 'to' in text_lower:
                try:
                    welcome_idx = [w.lower() for w in words].index('welcome')
                    to_idx = [w.lower() for w in words].index('to')
                    if to_idx + 1 < len(words):
                        place_word = words[to_idx + 1]
                        words = [place_word, 'YOU'] + implied_words + ['WELCOME']
                except (ValueError, IndexError):
                    pass
        
        normalized_text = " ".join(words)
        
        # Generate sign assets for English
        WORDS_DIR = 'static/sign/words'
        LETTERS_DIR = 'static/sign/letters'
        
        for word in words:
            word_found = False
            potential_word_files = [f for f in os.listdir(WORDS_DIR) if f.lower() == f"{word.lower()}.gif"]
            if potential_word_files:
                sign_assets.append({'type': 'word', 'word': word, 'url': f'/static/sign/words/{potential_word_files[0]}'})
                word_found = True
            if not word_found:
                for char in word.lower():
                    if char.isalnum():
                        num_map = {'1':'one','2':'two','3':'three','4':'four','5':'five','6':'six','7':'seven','8':'eight','9':'nine','0':'ten'}
                        char_filename = num_map.get(char, char) + '.jpg'
                        if os.path.exists(os.path.join(LETTERS_DIR, char_filename)):
                            sign_assets.append({'type': 'letter', 'char': char, 'url': f'/static/sign/letters/{char_filename}'})
                sign_assets.append({'type': 'break'})
        
        if sign_assets and sign_assets[-1]['type'] == 'break':
            sign_assets.pop()

    # Save translation to database
    new_translation = Translation(
        user_id=str(current_user.id),
        original_text=text,
        translated_text=normalized_text.upper() if language == 'english' else normalized_text,
        translation_type=f'{language}_text',
        is_favorite=False
    )
    new_translation.save()
    
    return jsonify({
        'success': True,
        'original': text,
        'language': language,
        'sign_assets': sign_assets,
        'translation_id': str(new_translation.id)
    })

@app.route('/favorite/<translation_id>', methods=['POST'])
@login_required
def toggle_favorite(translation_id):
    translation = Translation.objects(id=translation_id).first()
    if not translation or str(translation.user_id) != str(current_user.id):
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    translation.is_favorite = not translation.is_favorite
    translation.save()
    
    action = 'added' if translation.is_favorite else 'removed'
    return jsonify({
        'success': True, 
        'action': action,
        'is_favorite': translation.is_favorite
    })

@app.route('/history')
@login_required
def history():
    user_translations = Translation.objects(user_id=str(current_user.id)).order_by('-created_at')
    return render_template('history.html', translations=user_translations)

@app.route('/courses')
@login_required
def courses():
    category_id = request.args.get('category_id')
    search_query = request.args.get('search')
    categories = list(CourseCategory.objects(is_active=True).order_by('order'))
    
    current_category = None
    courses_query = Course.objects(is_active=True)
    
    if category_id:
        current_category = CourseCategory.objects(id=category_id).first()
        courses_query = courses_query.filter(category_id=category_id)
    
    if search_query:
        from mongoengine.queryset.visitor import Q
        courses_query = courses_query.filter(Q(title__icontains=search_query) | Q(description__icontains=search_query))
    
    if not category_id and not search_query:
        # Default view: show featured courses
        courses_query = courses_query.filter(is_featured=True)
        
    courses_list = list(courses_query.order_by('-created_at'))
    
    # Calculate dynamic lesson counts for display
    from app import LessonCategory
    for course in courses_list:
        course.lessons_count = LessonCategory.objects(course_id=str(course.id)).count()
    
    # Enrich categories with course counts
    enhanced_categories = []
    for cat in categories:
        count = Course.objects(category_id=str(cat.id), is_active=True).count()
        enhanced_categories.append({
            'id': str(cat.id),
            'name': cat.name,
            'description': cat.description,
            'icon': cat.icon,
            'course_count': count
        })
        
    return render_template('courses.html', 
                         categories=enhanced_categories, 
                         courses=courses_list, 
                         current_category=current_category)

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@app.route('/feedback')
@login_required
def feedback():
    return render_template('feedback.html', success=False)

@app.route('/submit_feedback', methods=['POST'])
@login_required
def submit_feedback():
    rating = request.form.get('rating')
    category = request.form.get('category')
    subject = request.form.get('subject')
    message = request.form.get('message')
    
    if not all([rating, category, subject, message]):
        flash('All fields are required.', 'error')
        return redirect(url_for('feedback'))
    
    try:
        new_feedback = Feedback(
            user_id=str(current_user.id),
            username=current_user.username,
            category=category,
            rating=int(rating),
            subject=subject,
            message=message
        )
        new_feedback.save()
        
        # Notify admin of new feedback
        admin_subject = f"New Feedback: {category} - {subject}"
        admin_msg = f"User: {current_user.username}\nRating: {rating} Stars\nCategory: {category}\nSubject: {subject}\n\nMessage:\n{message}"
        send_admin_notification(admin_subject, admin_msg)
        
        return render_template('feedback.html', success=True)
    except Exception as e:
        flash(f'System interference: {str(e)}', 'error')
        return redirect(url_for('feedback'))

@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    data = request.get_json()
    
    current_user.first_name = data.get('first_name', current_user.first_name)
    current_user.last_name = data.get('last_name', current_user.last_name)
    # Email updates typically require verification, skipping safe update for now
    # current_user.email = data.get('email', current_user.email)
    
    current_user.learning_goal = data.get('learning_goal', current_user.learning_goal)
    current_user.motivation = data.get('motivation', current_user.motivation)
    
    current_user.save()
    return jsonify({'success': True, 'message': 'Profile updated successfully'})

@app.route('/api/upload_avatar', methods=['POST'])
@login_required
def upload_avatar():
    if 'avatar' not in request.files:
        return jsonify({'success': False, 'message': 'No file part'})
    
    file = request.files['avatar']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No selected file'})
        
    if file and allowed_file(file.filename):
        # Create avatars directory if not exists
        avatar_dir = os.path.join('static', 'uploads', 'avatars')
        os.makedirs(avatar_dir, exist_ok=True)
        
        # Secure filename and save
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"avatar_{current_user.id}_{int(datetime.utcnow().timestamp())}.{ext}"
        filepath = os.path.join(avatar_dir, filename)
        file.save(filepath)
        
        # Update user avatar_url
        # Store relative path for frontend usage
        relative_path = f"/static/uploads/avatars/{filename}"
        current_user.avatar_url = relative_path
        current_user.save()
        
        return jsonify({'success': True, 'avatar_url': relative_path, 'message': 'Avatar updated!'})
        
    return jsonify({'success': False, 'message': 'Invalid file type'})

@app.route('/change_password', methods=['POST'])
@login_required
def change_password():
    data = request.get_json()
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    
    if check_password_hash(current_user.password_hash, current_password):
        current_user.password_hash = generate_password_hash(new_password)
        current_user.save()
        return jsonify({'success': True, 'message': 'Password changed successfully'})
    
    return jsonify({'success': False, 'message': 'Current password is incorrect'})

# API endpoints for AJAX requests
@app.route('/api/user_stats')
@login_required
def user_stats():
    total_translations = Translation.objects(user_id=str(current_user.id)).count()
    total_favorites = Translation.objects(user_id=str(current_user.id), is_favorite=True).count()
    
    from datetime import timedelta
    week_ago = datetime.utcnow() - timedelta(days=7)
    weekly_translations = Translation.objects(
        user_id=str(current_user.id),
        created_at__gte=week_ago
    ).count()
    
    return jsonify({
        'total_translations': total_translations,
        'total_favorites': total_favorites,
        'weekly_translations': weekly_translations
    })

@app.route('/api/recent_translations')
@login_required
def recent_translations():
    recent = Translation.objects(user_id=str(current_user.id)).order_by('-created_at').limit(10)
    
    result = []
    for t in recent:
        result.append({
            'id': str(t.id),
            'text': t.original_text,
            'date': t.created_at.strftime('%Y-%m-%d %H:%M'),
            'is_favorite': t.is_favorite
        })
    
    return jsonify(result)


# Admin routes
@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    # Filter out admin users for regular user stats
    regular_users_count = User.objects(is_admin=False).count()
    pending_users_count = User.objects(status='pending', is_admin=False).count()
    total_courses = Course.objects().count()
    total_translations = Translation.objects().count()
    unread_feedback = Feedback.objects(is_read=False).count()
    
    return render_template('admin/dashboard.html',
                         total_users=regular_users_count,
                         pending_users=pending_users_count,
                         total_courses=total_courses,
                         total_translations=total_translations,
                         unread_feedback=unread_feedback)

@app.route('/admin/feedback')
@login_required
@admin_required
def admin_feedback():
    all_feedback = Feedback.objects().order_by('-created_at')
    return render_template('admin/feedback.html', feedbacks=all_feedback)

@app.route('/admin/feedback/read/<feedback_id>', methods=['POST'])
@login_required
@admin_required
def mark_feedback_read(feedback_id):
    feedback = Feedback.objects(id=feedback_id).first()
    if feedback:
        feedback.is_read = True
        feedback.save()
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Feedback not found'})

@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    regular_users = User.objects(is_admin=False)
    return render_template('admin/users.html', users=regular_users)

@app.route('/admin/approve_user/<user_id>', methods=['POST'])
@login_required
@admin_required
def approve_user(user_id):
    user = User.objects(id=user_id).first()
    
    if user:
        user.status = 'approved'
        user.is_active_user = True
        user.save()
        
        # Create initial progress record if it doesn't exist
        if not Progress.objects(user_id=user_id).first():
            progress = Progress(user_id=user_id, category='basic', level=1)
            progress.save()
        
        # Send premium approval email
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = f"SEMI Admin <{EMAIL_USER}>"
            msg['To'] = user.email
            msg['Subject'] = 'SEMI • Account Approved!'
            
            html_body = f"""
            <html>
            <body style="font-family: sans-serif; background-color: #050a10; color: #ffffff; padding: 40px;">
                <div style="max-width: 500px; margin: 0 auto; background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 20px; padding: 40px;">
                    <h1 style="color: #4facfe; text-align: center;">Welcome Aboard!</h1>
                    <p style="color: #94a3b8; line-height: 1.6;">Hello {user.first_name},</p>
                    <p style="color: #94a3b8; line-height: 1.6;">Your registration for the SEMI platform has been <strong>approved</strong>. Your digital learning environment is now synchronized and ready for use.</p>
                    <div style="text-align: center; margin: 40px 0;">
                        <a href="{url_for('login', _external=True)}" style="background: linear-gradient(135deg, #00f2fe, #4facfe); color: #020617; padding: 15px 35px; border-radius: 12px; text-decoration: none; font-weight: bold;">Launch SEMI Protocol</a>
                    </div>
                    <hr style="border: none; border-top: 1px solid rgba(255,255,255,0.1); margin: 30px 0;">
                    <p style="font-size: 12px; color: #64748b; text-align: center;">Security Ecosystem for Multi-Intelligence</p>
                </div>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(f"Your account has been approved. Login at: {url_for('login', _external=True)}", 'plain'))
            msg.attach(MIMEText(html_body, 'html'))
            
            server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_USER, user.email, msg.as_string())
            server.quit()
        except Exception as e:
            print(f"Approval email error: {e}")
        
        return jsonify({'success': True, 'message': 'User approved and notified.'})
    
    return jsonify({'success': False, 'message': 'Identity not found in records.'})

@app.route('/admin/reject_user/<user_id>', methods=['POST'])
@login_required
@admin_required
def reject_user(user_id):
    user = User.objects(id=user_id).first()
    
    if user:
        user.status = 'rejected'
        user.is_active_user = False
        user.save()
        
        # Send premium rejection email
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = f"SEMI Admin <{EMAIL_USER}>"
            msg['To'] = user.email
            msg['Subject'] = 'SEMI • Account Status Update'
            
            html_body = f"""
            <html>
            <body style="font-family: sans-serif; background-color: #050a10; color: #ffffff; padding: 40px;">
                <div style="max-width: 500px; margin: 0 auto; background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 20px; padding: 40px;">
                    <h1 style="color: #ef4444; text-align: center;">Status Update</h1>
                    <p style="color: #94a3b8; line-height: 1.6;">Dear {user.first_name},</p>
                    <p style="color: #94a3b8; line-height: 1.6;">We have completed the review of your registration. Unfortunately, we cannot approve your account at this time.</p>
                    <p style="color: #94a3b8; line-height: 1.6;">If you believe this is an error, please contact our support team for a manual audit.</p>
                    <hr style="border: none; border-top: 1px solid rgba(255,255,255,0.1); margin: 30px 0;">
                    <p style="font-size: 12px; color: #64748b; text-align: center;">Security Ecosystem for Multi-Intelligence</p>
                </div>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(f"Your registration status has been updated to rejected. Please contact support if you have questions.", 'plain'))
            msg.attach(MIMEText(html_body, 'html'))
            
            server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_USER, user.email, msg.as_string())
            server.quit()
        except Exception as e:
            print(f"Rejection email error: {e}")
        
        return jsonify({'success': True, 'message': 'Status updated to rejected.'})
    
    return jsonify({'success': False, 'message': 'Identity not found.'})

@app.route('/admin/delete_user/<user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.objects(id=user_id).first()
    if user:
        if user.is_admin:
            return jsonify({'success': False, 'message': 'Administrative protocols prevent self-deletion.'})
        
        # Cleanup related records
        Progress.objects(user_id=user_id).delete()
        Translation.objects(user_id=user_id).delete()
        user.delete()
        
        return jsonify({'success': True, 'message': 'Identity purged from system.'})
    return jsonify({'success': False, 'message': 'Target record not found.'})

@app.route('/admin/courses')
@login_required
@admin_required
def admin_courses():
    raw_courses = Course.objects().order_by('-created_at')
    categories = CourseCategory.objects(is_active=True).order_by('order')
    
    courses_list = []
    for c in raw_courses:
        # Convert to dict and ensure ID is a string for JSON serialization
        course_dict = c.to_mongo().to_dict()
        course_dict['id'] = str(c.id)
        if '_id' in course_dict:
            del course_dict['_id']
        if 'created_at' in course_dict:
            del course_dict['created_at']
            
        # Calculate real lesson count
        linked_categories = LessonCategory.objects(course_id=str(c.id))
        category_ids = [str(cat.id) for cat in linked_categories]
        real_lessons_count = Lesson.objects(category_id__in=category_ids).count()
        
        course_dict['lessons_count'] = real_lessons_count
        courses_list.append(course_dict)
        
    categories_dict = [
        {
            'id': str(cat.id),
            'name': cat.name,
            'description': cat.description,
            'icon': cat.icon,
            'order': cat.order
        } for cat in categories
    ]
        
    return render_template('admin/courses.html', courses=courses_list, categories=categories_dict)

@app.route('/admin/add_course', methods=['POST'])
@login_required
@admin_required
def add_course():
    data = request.get_json()
    
    category_id = data.get('category_id')
    new_cat_name = data.get('new_category_name')
    new_cat_icon = data.get('new_category_icon', '📚')
    
    # Check for dynamic category creation
    if category_id == 'NEW_CATEGORY' and new_cat_name:
        # Create new category
        new_vibrant_cat = CourseCategory(
            name=new_cat_name,
            icon=new_cat_icon,
            description=f"New dynamic subject: {new_cat_name}"
        )
        new_vibrant_cat.save()
        category_id = str(new_vibrant_cat.id)
        send_admin_notification("Ecosystem Expansion", f"New Subject Category created: {new_cat_name}")

    new_course = Course(
        title=data.get('title'),
        description=data.get('description'),
        category_id=category_id,
        difficulty=data.get('difficulty'),
        duration_weeks=int(data.get('duration_weeks', 4)),
        is_featured=data.get('is_featured', False),
        is_active=True
    )
    new_course.save()
    return jsonify({'success': True, 'message': 'Course added successfully'})

@app.route('/admin/edit_course/<course_id>', methods=['POST'])
@login_required
@admin_required
def edit_course(course_id):
    data = request.get_json()
    course = Course.objects(id=course_id).first()
    if course:
        category_id = data.get('category_id')
        new_cat_name = data.get('new_category_name')
        new_cat_icon = data.get('new_category_icon', '📚')
        
        # Check for dynamic category creation
        if category_id == 'NEW_CATEGORY' and new_cat_name:
            new_vibrant_cat = CourseCategory(
                name=new_cat_name,
                icon=new_cat_icon,
                description=f"New dynamic subject: {new_cat_name}"
            )
            new_vibrant_cat.save()
            category_id = str(new_vibrant_cat.id)
            send_admin_notification("Ecosystem Expansion", f"Subject Category refined/added: {new_cat_name}")

        course.title = data.get('title', course.title)
        course.description = data.get('description', course.description)
        course.category_id = category_id if category_id else course.category_id
        course.difficulty = data.get('difficulty', course.difficulty)
        course.duration_weeks = int(data.get('duration_weeks', course.duration_weeks))
        course.is_featured = data.get('is_featured', course.is_featured)
        course.save()
        return jsonify({'success': True, 'message': 'Course updated successfully'})
    return jsonify({'success': False, 'message': 'Course not found'})

@app.route('/admin/add_course_category', methods=['POST'])
@login_required
@admin_required
def add_course_category():
    data = request.get_json()
    cat = CourseCategory(
        name=data.get('name'),
        description=data.get('description'),
        icon=data.get('icon', '📚'),
        order=CourseCategory.objects().count() + 1
    )
    cat.save()
    return jsonify({'success': True, 'message': 'Subject category added'})

@app.route('/admin/edit_course_category/<cat_id>', methods=['POST'])
@login_required
@admin_required
def edit_course_category(cat_id):
    data = request.get_json()
    cat = CourseCategory.objects(id=cat_id).first()
    if cat:
        cat.name = data.get('name', cat.name)
        cat.description = data.get('description', cat.description)
        cat.icon = data.get('icon', cat.icon)
        cat.save()
        return jsonify({'success': True, 'message': 'Subject category updated'})
    return jsonify({'success': False, 'message': 'Category not found'})

@app.route('/admin/delete_course_category/<cat_id>', methods=['POST'])
@login_required
@admin_required
def delete_course_category(cat_id):
    cat = CourseCategory.objects(id=cat_id).first()
    if cat:
        # Unlink courses
        Course.objects(category_id=cat_id).update(set__category_id=None)
        cat.delete()
        return jsonify({'success': True, 'message': 'Category removed'})
    return jsonify({'success': False, 'message': 'Category not found'})

@app.route('/admin/delete_course/<course_id>', methods=['POST'])
@login_required
@admin_required
def delete_course(course_id):
    course = Course.objects(id=course_id).first()
    if course:
        course.delete()
        return jsonify({'success': True, 'message': 'Course deleted successfully'})
    return jsonify({'success': False, 'message': 'Course not found'})

# Public Lesson API
@app.route('/api/lesson/<lesson_id>/steps')
@login_required
def get_public_lesson_steps(lesson_id):
    steps = LessonStep.objects(lesson_id=lesson_id).order_by('order')
    return jsonify({
        'success': True,
        'steps': [
            {
                'title': s.title,
                'description': s.description,
                'content_url': s.content_url,
                'content_type': s.content_type,
                'transcript': s.transcript
            } for s in steps
        ]
    })

@app.route('/api/lesson/complete', methods=['POST'])
@login_required
def complete_lesson():
    data = request.get_json()
    lesson_id = data.get('lesson_id')
    
    # Update user progress
    progress = Progress.objects(user_id=current_user.id).first()
    if not progress:
        progress = Progress(user_id=current_user.id)
    
    progress.lessons_completed += 1
    progress.experience_points += 50
    progress.last_updated = datetime.utcnow()
    progress.save()
    
    # Update Gamification
    update_user_activity(current_user.id)
    
    return jsonify({'success': True, 'new_xp': progress.experience_points})

@app.route('/sign-lab')
@login_required
def sign_lab_page():
    # Only fetch categories that are foundational (no course_id assigned)
    categories_obj = LessonCategory.objects(course_id=None, is_active=True).order_by('order')
    
    curriculum = []
    for cat in categories_obj:
        cat_lessons = Lesson.objects(category_id=str(cat.id), is_active=True).order_by('order')
        module_lessons = []
        for lesson in cat_lessons:
            module_lessons.append({
                'id': str(lesson.id),
                'title': lesson.title,
                'description': lesson.description,
                'duration': lesson.duration_minutes,
                'difficulty': lesson.difficulty_level,
                'category_name': cat.name,
                'category_icon': cat.icon,
                'category_id': str(cat.id)
            })
        
        curriculum.append({
            'module': cat,
            'lessons': module_lessons
        })
            
    return render_template('sign_lab.html', curriculum=curriculum)

@app.route('/course/classroom/<course_id>')
@login_required
def classroom_page(course_id):
    current_course = Course.objects(id=course_id).first()
    if not current_course:
        return redirect(url_for('courses'))
        
    categories_obj = LessonCategory.objects(course_id=course_id, is_active=True).order_by('order')
    
    curriculum = []
    for cat in categories_obj:
        cat_lessons = Lesson.objects(category_id=str(cat.id), is_active=True).order_by('order')
        module_lessons = []
        for lesson in cat_lessons:
            module_lessons.append({
                'id': str(lesson.id),
                'title': lesson.title,
                'description': lesson.description,
                'duration': lesson.duration_minutes,
                'difficulty': lesson.difficulty_level,
                'category_name': cat.name,
                'category_icon': cat.icon,
                'category_id': str(cat.id)
            })
        
        curriculum.append({
            'module': cat,
            'lessons': module_lessons
        })
            
    return render_template('classroom.html', 
                         curriculum=curriculum, 
                         current_course=current_course)

# Legacy redirect for compatibility
@app.route('/lessons')
def lessons_redirect():
    return redirect(url_for('sign_lab_page'))

# Admin Lesson Management Routes
@app.route('/api/admin/curriculum/<course_id>')
@login_required
@admin_required
def get_admin_curriculum(course_id):
    chapters = LessonCategory.objects(course_id=course_id, is_active=True).order_by('order')
    curriculum = []
    for cat in chapters:
        lessons = Lesson.objects(category_id=str(cat.id), is_active=True).order_by('order')
        curriculum.append({
            'chapter': {
                'id': str(cat.id),
                'name': cat.name,
                'description': cat.description,
                'icon': cat.icon,
                'difficulty': cat.difficulty_level
            },
            'lessons': [
                {
                    'id': str(l.id),
                    'title': l.title,
                    'description': l.description,
                    'duration': l.duration_minutes,
                    'difficulty': l.difficulty_level,
                    'order': l.order
                } for l in lessons
            ]
        })
    return jsonify({'success': True, 'curriculum': curriculum})

@app.route('/admin/lessons')
@login_required
@admin_required
def admin_lessons():
    categories = list(LessonCategory.objects(is_active=True).order_by('order'))
    lessons = list(Lesson.objects(is_active=True).order_by('order'))
    courses = list(Course.objects(is_active=True))
    
    # Convert to dict for template
    categories_dict = [
        {
            'id': str(cat.id),
            'name': cat.name,
            'description': cat.description,
            'icon': cat.icon,
            'difficulty_level': cat.difficulty_level,
            'course_id': cat.course_id,
            'order': cat.order
        }
        for cat in categories
    ]
    
    courses_dict = [
        {'id': str(c.id), 'title': c.title}
        for c in courses
    ]
    
    lessons_dict = [
        {
            'id': str(lesson.id),
            'category_id': lesson.category_id,
            'title': lesson.title,
            'description': lesson.description,
            'duration_minutes': lesson.duration_minutes,
            'difficulty_level': lesson.difficulty_level,
            'order': lesson.order
        }
        for lesson in lessons
    ]
    
    return render_template('admin/lessons.html', categories=categories_dict, lessons=lessons_dict, courses=courses_dict)
@app.route('/admin/upload_content', methods=['POST'])
@login_required
@admin_required
def upload_content():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file part'})
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No selected file'})
    if file and allowed_file(file.filename):
        from werkzeug.utils import secure_filename
        filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
        file.save(os.path.join(UPLOAD_FOLDER, filename))
        url = url_for('static', filename=f'uploads/lessons/{filename}')
        return jsonify({'success': True, 'url': url})
    return jsonify({'success': False, 'message': 'File type not allowed'})

@app.route('/admin/add_lesson_category', methods=['POST'])
@login_required
@admin_required
def add_lesson_category():
    data = request.get_json()
    category = LessonCategory(
        name=data.get('name'),
        description=data.get('description'),
        icon=data.get('icon', '📚'),
        difficulty_level=data.get('difficulty_level', 'beginner'),
        course_id=data.get('course_id'),
        order=LessonCategory.objects().count() + 1
    )
    category.save()
    return jsonify({'success': True, 'message': 'Category added successfully'})

@app.route('/admin/edit_lesson_category/<category_id>', methods=['POST'])
@login_required
@admin_required
def edit_lesson_category(category_id):
    category = LessonCategory.objects(id=category_id).first()
    if category:
        data = request.get_json()
        category.name = data.get('name', category.name)
        category.description = data.get('description', category.description)
        category.icon = data.get('icon', category.icon)
        category.difficulty_level = data.get('difficulty_level', category.difficulty_level)
        category.course_id = data.get('course_id', category.course_id)
        category.save()
        return jsonify({'success': True, 'message': 'Category updated successfully'})
    return jsonify({'success': False, 'message': 'Category not found'})

@app.route('/admin/delete_lesson_category/<category_id>', methods=['POST'])
@login_required
@admin_required
def delete_lesson_category(category_id):
    category = LessonCategory.objects(id=category_id).first()
    if category:
        # Delete all lessons in this category
        Lesson.objects(category_id=category_id).delete()
        category.delete()
        return jsonify({'success': True, 'message': 'Category deleted successfully'})
    return jsonify({'success': False, 'message': 'Category not found'})

@app.route('/admin/add_lesson', methods=['POST'])
@login_required
@admin_required
def add_lesson():
    data = request.get_json()
    lesson = Lesson(
        category_id=data.get('category_id'),
        title=data.get('title'),
        description=data.get('description'),
        duration_minutes=int(data.get('duration_minutes', 15)),
        difficulty_level=data.get('difficulty_level', 'beginner'),
        order=Lesson.objects(category_id=data.get('category_id')).count() + 1
    )
    lesson.save()
    return jsonify({'success': True, 'message': 'Lesson added successfully'})

@app.route('/admin/edit_lesson/<lesson_id>', methods=['POST'])
@login_required
@admin_required
def edit_lesson(lesson_id):
    lesson = Lesson.objects(id=lesson_id).first()
    if lesson:
        data = request.get_json()
        lesson.title = data.get('title', lesson.title)
        lesson.description = data.get('description', lesson.description)
        lesson.duration_minutes = int(data.get('duration_minutes', lesson.duration_minutes))
        lesson.difficulty_level = data.get('difficulty_level', lesson.difficulty_level)
        lesson.updated_at = datetime.utcnow()
        lesson.save()
        return jsonify({'success': True, 'message': 'Lesson updated successfully'})
    return jsonify({'success': False, 'message': 'Lesson not found'})

@app.route('/admin/delete_lesson/<lesson_id>', methods=['POST'])
@login_required
@admin_required
def delete_lesson(lesson_id):
    lesson = Lesson.objects(id=lesson_id).first()
    if lesson:
        # Delete all steps in this lesson
        LessonStep.objects(lesson_id=lesson_id).delete()
        lesson.delete()
        return jsonify({'success': True, 'message': 'Lesson deleted successfully'})
    return jsonify({'success': False, 'message': 'Lesson not found'})

@app.route('/admin/get_lesson_steps/<lesson_id>', methods=['GET'])
@login_required
@admin_required
def get_lesson_steps(lesson_id):
    steps = list(LessonStep.objects(lesson_id=lesson_id).order_by('order'))
    steps_dict = [
        {
            'id': str(step.id),
            'lesson_id': step.lesson_id,
            'title': step.title,
            'description': step.description,
            'content_type': step.content_type,
            'content_url': step.content_url,
            'transcript': step.transcript,
            'order': step.order
        }
        for step in steps
    ]
    return jsonify({'success': True, 'steps': steps_dict})

@app.route('/admin/add_lesson_step', methods=['POST'])
@login_required
@admin_required
def add_lesson_step():
    data = request.get_json()
    step = LessonStep(
        lesson_id=data.get('lesson_id'),
        title=data.get('title'),
        description=data.get('description'),
        content_type=data.get('content_type', 'video'),
        content_url=data.get('content_url'),
        transcript=data.get('transcript'),
        order=LessonStep.objects(lesson_id=data.get('lesson_id')).count() + 1
    )
    step.save()
    return jsonify({'success': True, 'message': 'Step added successfully'})

@app.route('/admin/edit_lesson_step/<step_id>', methods=['POST'])
@login_required
@admin_required
def edit_lesson_step(step_id):
    step = LessonStep.objects(id=step_id).first()
    if step:
        data = request.get_json()
        step.title = data.get('title', step.title)
        step.description = data.get('description', step.description)
        step.content_type = data.get('content_type', step.content_type)
        step.content_url = data.get('content_url', step.content_url)
        step.transcript = data.get('transcript', step.transcript)
        step.save()
        return jsonify({'success': True, 'message': 'Step updated successfully'})
    return jsonify({'success': False, 'message': 'Step not found'})

@app.route('/admin/delete_lesson_step/<step_id>', methods=['POST'])
@login_required
@admin_required
def delete_lesson_step(step_id):
    step = LessonStep.objects(id=step_id).first()
    if step:
        step.delete()
        return jsonify({'success': True, 'message': 'Step deleted successfully'})
    return jsonify({'success': False, 'message': 'Step not found'})


# Quiz and Lessons routes
@app.route('/quiz')
@login_required
def quiz_page():
    return render_template('quiz.html')

# Quiz API Endpoints
@app.route('/api/quiz/start', methods=['POST'])
@login_required
def start_quiz():
    """Initialize a new quiz attempt"""
    data = request.get_json()
    difficulty = data.get('difficulty', 'beginner')
    
    # Get questions for this difficulty
    questions = list(QuizQuestion.objects(difficulty=difficulty, is_active=True))
    
    if not questions:
        return jsonify({'success': False, 'message': 'No questions available for this difficulty'})
    
    # Randomize questions
    import random
    random.shuffle(questions)
    
    # Limit number of questions based on difficulty
    question_limits = {'beginner': 5, 'intermediate': 7, 'advanced': 8}
    max_questions = question_limits.get(difficulty, 5)
    
    # Check if we have enough questions
    if len(questions) < max_questions:
        # If not enough specific difficulty questions, maybe add some from lower difficulties?
        # For now, just use what we have.
        print(f"Warning: Only {len(questions)} questions found for difficulty {difficulty}, requested {max_questions}.")
        
    questions = questions[:max_questions]
    
    # Create quiz attempt
    attempt = QuizAttempt(
        user_id=str(current_user.id),
        difficulty=difficulty,
        total_questions=len(questions),
        completed=False
    )
    attempt.save()
    
    # Return question IDs for this attempt
    question_ids = [str(q.id) for q in questions]
    
    return jsonify({
        'success': True,
        'attempt_id': str(attempt.id),
        'question_ids': question_ids,
        'total_questions': len(questions)
    })

@app.route('/api/quiz/question/<question_id>', methods=['GET'])
@login_required
def get_question(question_id):
    """Get a specific question"""
    question = QuizQuestion.objects(id=question_id).first()
    
    if not question:
        return jsonify({'success': False, 'message': 'Question not found'})
    
    # Increment times shown
    question.times_shown += 1
    question.save()
    
    return jsonify({
        'success': True,
        'question': {
            'id': str(question.id),
            'text': question.question_text,
            'sign_url': question.sign_url,
            'options': question.options,
            'difficulty': question.difficulty
        }
    })

@app.route('/api/quiz/submit', methods=['POST'])
@login_required
def submit_answer():
    """Submit an answer for a question"""
    data = request.get_json()
    attempt_id = data.get('attempt_id')
    question_id = data.get('question_id')
    selected_index = data.get('selected_index')
    time_taken = data.get('time_taken', 0)
    
    attempt = QuizAttempt.objects(id=attempt_id).first()
    question = QuizQuestion.objects(id=question_id).first()
    
    if not attempt or not question:
        return jsonify({'success': False, 'message': 'Invalid attempt or question'})
    
    is_correct = selected_index == question.correct_answer_index
    
    # Update question statistics
    if is_correct:
        question.times_correct += 1
    question.save()
    
    # Store answer
    answer_data = {
        'question_id': question_id,
        'selected_index': selected_index,
        'correct_index': question.correct_answer_index,
        'is_correct': is_correct,
        'time_taken': time_taken
    }
    
    attempt.answers.append(answer_data)
    
    if is_correct:
        attempt.correct_answers += 1
    else:
        attempt.incorrect_answers += 1
    
    attempt.save()
    
    return jsonify({
        'success': True,
        'is_correct': is_correct,
        'correct_index': question.correct_answer_index
    })

@app.route('/api/quiz/complete', methods=['POST'])
@login_required
def complete_quiz():
    """Complete a quiz attempt and calculate final score"""
    data = request.get_json()
    attempt_id = data.get('attempt_id')
    max_streak = data.get('max_streak', 0)
    total_time = data.get('total_time', 0)
    
    attempt = QuizAttempt.objects(id=attempt_id).first()
    
    if not attempt:
        return jsonify({'success': False, 'message': 'Attempt not found'})
    
    # Calculate score
    score_percentage = (attempt.correct_answers / attempt.total_questions) * 100 if attempt.total_questions > 0 else 0
    
    attempt.score_percentage = score_percentage
    attempt.max_streak = max_streak
    attempt.time_taken_seconds = total_time
    attempt.completed = True
    attempt.save()
    
    # Update user progress
    progress = Progress.objects(user_id=str(current_user.id)).first()
    if progress:
        progress.quizzes_passed += 1
        progress.experience_points += int(score_percentage)  # Award XP based on score
        progress.last_updated = datetime.utcnow()
        progress.save()
        
        # Update Gamification
        update_user_activity(str(current_user.id))
    
    # Check for achievements
    achievements_earned = []
    
    # First quiz achievement
    if QuizAttempt.objects(user_id=str(current_user.id), completed=True).count() == 1:
        achievement = Achievement(
            user_id=str(current_user.id),
            achievement_type='first_quiz',
            title='Quiz Novice',
            description='Completed your first quiz!',
            icon='🎯',
            metadata={'score': score_percentage}
        )
        achievement.save()
        achievements_earned.append({
            'title': achievement.title,
            'description': achievement.description,
            'icon': achievement.icon
        })
    
    # Perfect score achievement
    if score_percentage == 100:
        achievement = Achievement(
            user_id=str(current_user.id),
            achievement_type='perfect_score',
            title='Perfect Score!',
            description='Achieved 100% on a quiz!',
            icon='🏆',
            metadata={'difficulty': attempt.difficulty}
        )
        achievement.save()
        achievements_earned.append({
            'title': achievement.title,
            'description': achievement.description,
            'icon': achievement.icon
        })
    
    # Streak master achievement
    if max_streak >= 5:
        achievement = Achievement(
            user_id=str(current_user.id),
            achievement_type='streak_master',
            title='Streak Master',
            description=f'Achieved a {max_streak} answer streak!',
            icon='🔥',
            metadata={'streak': max_streak}
        )
        achievement.save()
        achievements_earned.append({
            'title': achievement.title,
            'description': achievement.description,
            'icon': achievement.icon
        })
    
    return jsonify({
        'success': True,
        'score_percentage': score_percentage,
        'correct_answers': attempt.correct_answers,
        'incorrect_answers': attempt.incorrect_answers,
        'max_streak': max_streak,
        'achievements': achievements_earned
    })

@app.route('/api/quiz/history', methods=['GET'])
@login_required
def quiz_history():
    """Get user's quiz history"""
    attempts = QuizAttempt.objects(user_id=str(current_user.id), completed=True).order_by('-created_at').limit(20)
    
    history = []
    for attempt in attempts:
        history.append({
            'id': str(attempt.id),
            'difficulty': attempt.difficulty,
            'score_percentage': attempt.score_percentage,
            'correct_answers': attempt.correct_answers,
            'total_questions': attempt.total_questions,
            'max_streak': attempt.max_streak,
            'time_taken': attempt.time_taken_seconds,
            'date': attempt.created_at.strftime('%Y-%m-%d %H:%M')
        })
    
    return jsonify({
        'success': True,
        'history': history
    })

@app.route('/api/quiz/stats', methods=['GET'])
@login_required
def quiz_stats():
    """Get user's overall quiz statistics"""
    attempts = QuizAttempt.objects(user_id=str(current_user.id), completed=True)
    
    if not attempts:
        return jsonify({
            'success': True,
            'stats': {
                'total_quizzes': 0,
                'average_score': 0,
                'best_score': 0,
                'total_questions_answered': 0,
                'accuracy_rate': 0
            }
        })
    
    total_quizzes = attempts.count()
    total_score = sum(a.score_percentage for a in attempts)
    average_score = total_score / total_quizzes if total_quizzes > 0 else 0
    best_score = max(a.score_percentage for a in attempts)
    total_questions = sum(a.total_questions for a in attempts)
    total_correct = sum(a.correct_answers for a in attempts)
    accuracy_rate = (total_correct / total_questions * 100) if total_questions > 0 else 0
    
    achievements = Achievement.objects(user_id=str(current_user.id)).count()
    
    return jsonify({
        'success': True,
        'stats': {
            'total_quizzes': total_quizzes,
            'average_score': round(average_score, 1),
            'best_score': round(best_score, 1),
            'total_questions_answered': total_questions,
            'accuracy_rate': round(accuracy_rate, 1),
            'achievements_earned': achievements
        }
    })



# --- Admin Quiz Management ---
@app.route('/admin/quizzes')
@login_required
@admin_required
def admin_quizzes():
    questions = list(QuizQuestion.objects(is_active=True).order_by('-created_at'))
    
    # Convert to dict for template
    questions_dict = []
    for q in questions:
        q_dict = {
            'id': str(q.id),
            'question_text': q.question_text,
            'sign_url': q.sign_url,
            'options': q.options,
            'correct_answer_index': q.correct_answer_index,
            'difficulty': q.difficulty,
            'category': q.category,
            'times_shown': q.times_shown,
            'times_correct': q.times_correct
        }
        questions_dict.append(q_dict)
    
    return render_template('admin/quizzes.html', questions=questions_dict)

@app.route('/admin/add_quiz_question', methods=['POST'])
@login_required
@admin_required
def add_quiz_question():
    try:
        data = request.json
        media_list = data.get('media_urls', [])
        # Support legacy single sign_url if media_urls is empty
        if not media_list and data.get('sign_url'):
            media_list = [data.get('sign_url')]
            
        question = QuizQuestion(
            question_text=data.get('question_text'),
            sign_url=media_list[0] if media_list else data.get('sign_url'),
            media_urls=media_list,
            options=data.get('options'),
            correct_answer_index=int(data.get('correct_answer_index')),
            difficulty=data.get('difficulty'),
            category=data.get('category', 'words')
        )
        question.save()
        return jsonify({'success': True, 'message': 'Question integrated successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/edit_quiz_question/<qid>', methods=['POST'])
@login_required
@admin_required
def edit_quiz_question(qid):
    try:
        data = request.json
        question = QuizQuestion.objects(id=qid).first()
        if not question:
            return jsonify({'success': False, 'message': 'Question not found'})
            
        media_list = data.get('media_urls', [])
        if not media_list and data.get('sign_url'):
            media_list = [data.get('sign_url')]

        question.question_text = data.get('question_text')
        question.media_urls = media_list
        question.sign_url = media_list[0] if media_list else data.get('sign_url')
        question.options = data.get('options')
        question.correct_answer_index = int(data.get('correct_answer_index'))
        question.difficulty = data.get('difficulty')
        question.category = data.get('category', 'words')
        question.save()
        
        return jsonify({'success': True, 'message': 'Question synchronized'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/delete_quiz_question/<qid>', methods=['POST'])
@login_required
@admin_required
def delete_quiz_question(qid):
    try:
        question = QuizQuestion.objects(id=qid).first()
        if not question:
            return jsonify({'success': False, 'message': 'Question not found'})
            
        question.is_active = False # Soft delete
        question.save()
        return jsonify({'success': True, 'message': 'Question purged'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True)
