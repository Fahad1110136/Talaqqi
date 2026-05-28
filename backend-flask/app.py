from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
import sqlite3
import os
import uuid
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import json

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
socketio = SocketIO(app, cors_allowed_origins="*")

# ===== DATABASE LAYER =====
class DatabaseConnection:
    def __init__(self, db_path: str = 'database.db'):
        self.db_path = db_path
    
    def __enter__(self):
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        return self.conn
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()

class UserRepository:
    def create_table(self):
        with DatabaseConnection() as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS users
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                          username TEXT UNIQUE NOT NULL,
                          password TEXT NOT NULL,
                          user_type TEXT NOT NULL,
                          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    def create_user(self, username: str, password: str, user_type: str) -> bool:
        try:
            with DatabaseConnection() as conn:
                conn.execute('INSERT INTO users (username, password, user_type) VALUES (?, ?, ?)',
                            (username, password, user_type))
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False
    
    def get_user_by_credentials(self, username: str, password: str) -> Optional[Dict]:
        with DatabaseConnection() as conn:
            user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?',
                              (username, password)).fetchone()
            return dict(user) if user else None
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        with DatabaseConnection() as conn:
            user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
            return dict(user) if user else None
    
    def get_users_by_type(self, user_type: str) -> List[Dict]:
        with DatabaseConnection() as conn:
            users = conn.execute('SELECT id, username FROM users WHERE user_type = ?', 
                               (user_type,)).fetchall()
            return [dict(user) for user in users]

class MessageRepository:
    def create_table(self):
        with DatabaseConnection() as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS messages
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                          sender_id INTEGER NOT NULL,
                          receiver_id INTEGER NOT NULL,
                          message TEXT NOT NULL,
                          timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                          FOREIGN KEY (sender_id) REFERENCES users (id),
                          FOREIGN KEY (receiver_id) REFERENCES users (id))''')
    
    def create_message(self, sender_id: int, receiver_id: int, message: str) -> bool:
        with DatabaseConnection() as conn:
            conn.execute('INSERT INTO messages (sender_id, receiver_id, message) VALUES (?, ?, ?)',
                        (sender_id, receiver_id, message))
            conn.commit()
            return True
    
    def get_conversation(self, user1_id: int, user2_id: int) -> List[Dict]:
        with DatabaseConnection() as conn:
            messages = conn.execute('''
                SELECT m.*, u.username as sender_name 
                FROM messages m 
                JOIN users u ON m.sender_id = u.id 
                WHERE (m.sender_id = ? AND m.receiver_id = ?) 
                   OR (m.sender_id = ? AND m.receiver_id = ?) 
                ORDER BY m.timestamp
            ''', (user1_id, user2_id, user2_id, user1_id)).fetchall()
            return [dict(msg) for msg in messages]

class ReviewRepository:
    def create_table(self):
        with DatabaseConnection() as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS reviews
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                          teacher_id INTEGER NOT NULL,
                          student_id INTEGER NOT NULL,
                          review TEXT NOT NULL,
                          rating INTEGER NOT NULL,
                          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                          FOREIGN KEY (teacher_id) REFERENCES users (id),
                          FOREIGN KEY (student_id) REFERENCES users (id))''')
    
    def create_review(self, teacher_id: int, student_id: int, review: str, rating: int) -> bool:
        with DatabaseConnection() as conn:
            conn.execute('INSERT INTO reviews (teacher_id, student_id, review, rating) VALUES (?, ?, ?, ?)',
                        (teacher_id, student_id, review, rating))
            conn.commit()
            return True
    
    def get_reviews_by_teacher(self, teacher_id: int) -> List[Dict]:
        with DatabaseConnection() as conn:
            reviews = conn.execute('''
                SELECT r.*, u.username as student_name 
                FROM reviews r 
                JOIN users u ON r.student_id = u.id 
                WHERE r.teacher_id = ?
            ''', (teacher_id,)).fetchall()
            return [dict(review) for review in reviews]
    
    def get_reviews_by_student(self, student_id: int) -> List[Dict]:
        with DatabaseConnection() as conn:
            reviews = conn.execute('''
                SELECT r.*, u.username as teacher_name 
                FROM reviews r 
                JOIN users u ON r.teacher_id = u.id 
                WHERE r.student_id = ?
            ''', (student_id,)).fetchall()
            return [dict(review) for review in reviews]

class VideoCallRepository:
    def create_table(self):
        with DatabaseConnection() as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS video_calls
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                          teacher_id INTEGER NOT NULL,
                          student_id INTEGER NOT NULL,
                          room_id TEXT UNIQUE NOT NULL,
                          status TEXT DEFAULT 'active',
                          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                          FOREIGN KEY (teacher_id) REFERENCES users (id),
                          FOREIGN KEY (student_id) REFERENCES users (id))''')
    
    def create_video_call(self, teacher_id: int, student_id: int, room_id: str) -> bool:
        with DatabaseConnection() as conn:
            conn.execute('INSERT INTO video_calls (teacher_id, student_id, room_id) VALUES (?, ?, ?)',
                        (teacher_id, student_id, room_id))
            conn.commit()
            return True
    
    def get_active_call(self, teacher_id: int, student_id: int) -> Optional[Dict]:
        with DatabaseConnection() as conn:
            call = conn.execute('''
                SELECT room_id FROM video_calls 
                WHERE teacher_id = ? AND student_id = ? AND status = 'active'
            ''', (teacher_id, student_id)).fetchone()
            return dict(call) if call else None
    
    def get_call_by_room_id(self, room_id: str) -> Optional[Dict]:
        with DatabaseConnection() as conn:
            call = conn.execute('''
                SELECT vc.*, t.username as teacher_name, s.username as student_name 
                FROM video_calls vc
                JOIN users t ON vc.teacher_id = t.id
                JOIN users s ON vc.student_id = s.id
                WHERE vc.room_id = ?
            ''', (room_id,)).fetchone()
            return dict(call) if call else None
    
    def end_call(self, room_id: str) -> bool:
        with DatabaseConnection() as conn:
            conn.execute('UPDATE video_calls SET status = "ended" WHERE room_id = ?', (room_id,))
            conn.commit()
            return True

# ===== NEW: ANNOTATION & PROGRESS DATABASE =====
class AnnotationRepository:
    def create_table(self):
        with DatabaseConnection() as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS annotations
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                          user_id INTEGER NOT NULL,
                          surah_number INTEGER NOT NULL,
                          verse_number INTEGER NOT NULL,
                          text TEXT NOT NULL,
                          color TEXT DEFAULT '#FFEB3B',
                          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                          updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                          FOREIGN KEY (user_id) REFERENCES users (id))''')
    
    def create_annotation(self, user_id: int, surah_number: int, verse_number: int, 
                         text: str, color: str = '#FFEB3B') -> bool:
        try:
            with DatabaseConnection() as conn:
                conn.execute('''INSERT INTO annotations 
                              (user_id, surah_number, verse_number, text, color) 
                              VALUES (?, ?, ?, ?, ?)''',
                           (user_id, surah_number, verse_number, text, color))
                conn.commit()
                return True
        except:
            return False
    
    def get_annotations_by_user(self, user_id: int) -> List[Dict]:
        with DatabaseConnection() as conn:
            annotations = conn.execute('''
                SELECT * FROM annotations 
                WHERE user_id = ? 
                ORDER BY surah_number, verse_number
            ''', (user_id,)).fetchall()
            return [dict(ann) for ann in annotations]
    
    def get_annotations_by_verse(self, user_id: int, surah_number: int, 
                                verse_number: int) -> List[Dict]:
        with DatabaseConnection() as conn:
            annotations = conn.execute('''
                SELECT * FROM annotations 
                WHERE user_id = ? AND surah_number = ? AND verse_number = ?
            ''', (user_id, surah_number, verse_number)).fetchall()
            return [dict(ann) for ann in annotations]
    
    def update_annotation(self, annotation_id: int, user_id: int, 
                         text: str, color: str) -> bool:
        with DatabaseConnection() as conn:
            conn.execute('''UPDATE annotations 
                          SET text = ?, color = ?, updated_at = CURRENT_TIMESTAMP 
                          WHERE id = ? AND user_id = ?''',
                       (text, color, annotation_id, user_id))
            conn.commit()
            return conn.total_changes > 0
    
    def delete_annotation(self, annotation_id: int, user_id: int) -> bool:
        with DatabaseConnection() as conn:
            conn.execute('DELETE FROM annotations WHERE id = ? AND user_id = ?',
                        (annotation_id, user_id))
            conn.commit()
            return conn.total_changes > 0

class ProgressRepository:
    def create_table(self):
        with DatabaseConnection() as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS progress
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                          user_id INTEGER NOT NULL,
                          surah_number INTEGER NOT NULL,
                          verse_number INTEGER NOT NULL,
                          action_type TEXT NOT NULL,
                          duration INTEGER DEFAULT 0,
                          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                          FOREIGN KEY (user_id) REFERENCES users (id))''')
    
    def record_progress(self, user_id: int, surah_number: int, verse_number: int,
                       action_type: str, duration: int = 0) -> bool:
        try:
            with DatabaseConnection() as conn:
                conn.execute('''INSERT INTO progress 
                              (user_id, surah_number, verse_number, action_type, duration) 
                              VALUES (?, ?, ?, ?, ?)''',
                           (user_id, surah_number, verse_number, action_type, duration))
                conn.commit()
                return True
        except:
            return False
    
    def get_user_progress(self, user_id: int) -> List[Dict]:
        with DatabaseConnection() as conn:
            progress = conn.execute('''
                SELECT surah_number, verse_number, action_type, 
                       COUNT(*) as count, SUM(duration) as total_duration,
                       MAX(created_at) as last_activity
                FROM progress 
                WHERE user_id = ?
                GROUP BY surah_number, verse_number, action_type
                ORDER BY surah_number, verse_number
            ''', (user_id,)).fetchall()
            return [dict(p) for p in progress]
    
    def get_progress_summary(self, user_id: int) -> Dict:
        with DatabaseConnection() as conn:
            # Get total verses read
            verses_read = conn.execute('''
                SELECT COUNT(DISTINCT surah_number || '-' || verse_number) as total 
                FROM progress WHERE user_id = ? AND action_type = 'read'
            ''', (user_id,)).fetchone()
            
            # Get total listening time
            listen_time = conn.execute('''
                SELECT SUM(duration) as total 
                FROM progress WHERE user_id = ? AND action_type = 'listened'
            ''', (user_id,)).fetchone()
            
            # Get total annotations
            annotation_count = conn.execute('''
                SELECT COUNT(*) as total FROM annotations WHERE user_id = ?
            ''', (user_id,)).fetchone()
            
            # Get last 7 days activity
            week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
            weekly_activity = conn.execute('''
                SELECT DATE(created_at) as date, COUNT(*) as count
                FROM progress 
                WHERE user_id = ? AND created_at > ?
                GROUP BY DATE(created_at)
                ORDER BY date DESC
            ''', (user_id, week_ago)).fetchall()
            
            return {
                'verses_read': verses_read['total'] if verses_read['total'] else 0,
                'listen_time': listen_time['total'] if listen_time['total'] else 0,
                'annotation_count': annotation_count['total'] if annotation_count['total'] else 0,
                'weekly_activity': [dict(a) for a in weekly_activity]
            }

# ===== SERVICE LAYER =====
class BaseService(ABC):
    @abstractmethod
    def validate_input(self, *args, **kwargs) -> bool:
        pass

class UserService(BaseService):
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
    
    def validate_input(self, username: str, password: str, user_type: str) -> bool:
        return bool(username and password and user_type in ['teacher', 'student'])
    
    def register_user(self, username: str, password: str, user_type: str) -> tuple[bool, str]:
        if not self.validate_input(username, password, user_type):
            return False, "Invalid input data"
        
        success = self.user_repo.create_user(username, password, user_type)
        if success:
            return True, "Registration successful"
        return False, "Username already exists"
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        return self.user_repo.get_user_by_credentials(username, password)
    
    def get_users_by_type(self, user_type: str) -> List[Dict]:
        return self.user_repo.get_users_by_type(user_type)

class MessageService(BaseService):
    def __init__(self, message_repo: MessageRepository):
        self.message_repo = message_repo
    
    def validate_input(self, sender_id: int, receiver_id: int, message: str) -> bool:
        return bool(sender_id and receiver_id and message.strip())
    
    def send_message(self, sender_id: int, receiver_id: int, message: str) -> bool:
        if not self.validate_input(sender_id, receiver_id, message):
            return False
        return self.message_repo.create_message(sender_id, receiver_id, message)
    
    def get_conversation(self, user1_id: int, user2_id: int) -> List[Dict]:
        return self.message_repo.get_conversation(user1_id, user2_id)

class ReviewService(BaseService):
    def __init__(self, review_repo: ReviewRepository):
        self.review_repo = review_repo
    
    def validate_input(self, teacher_id: int, student_id: int, review: str, rating: int) -> bool:
        return bool(teacher_id and student_id and review.strip() and 1 <= rating <= 5)
    
    def add_review(self, teacher_id: int, student_id: int, review: str, rating: int) -> bool:
        if not self.validate_input(teacher_id, student_id, review, rating):
            return False
        return self.review_repo.create_review(teacher_id, student_id, review, rating)
    
    def get_teacher_reviews(self, teacher_id: int) -> List[Dict]:
        return self.review_repo.get_reviews_by_teacher(teacher_id)
    
    def get_student_reviews(self, student_id: int) -> List[Dict]:
        return self.review_repo.get_reviews_by_student(student_id)

class VideoCallService(BaseService):
    def __init__(self, video_call_repo: VideoCallRepository, user_repo: UserRepository):
        self.video_call_repo = video_call_repo
        self.user_repo = user_repo
    
    def validate_input(self, current_user_id: int, other_user_id: int) -> bool:
        return bool(current_user_id and other_user_id)
    
    def create_or_get_room(self, current_user_id: int, current_user_type: str, other_user_id: int) -> Optional[str]:
        if not self.validate_input(current_user_id, other_user_id):
            return None
        
        if current_user_type == 'teacher':
            teacher_id, student_id = current_user_id, other_user_id
        else:
            teacher_id, student_id = other_user_id, current_user_id
        
        existing_call = self.video_call_repo.get_active_call(teacher_id, student_id)
        if existing_call:
            return existing_call['room_id']
        
        room_id = str(uuid.uuid4())
        success = self.video_call_repo.create_video_call(teacher_id, student_id, room_id)
        return room_id if success else None
    
    def get_room_details(self, room_id: str) -> Optional[Dict]:
        return self.video_call_repo.get_call_by_room_id(room_id)
    
    def can_user_access_room(self, room_id: str, user_id: int) -> bool:
        room_details = self.get_room_details(room_id)
        if not room_details:
            return False
        return user_id in [room_details['teacher_id'], room_details['student_id']]
    
    def end_call(self, room_id: str) -> bool:
        return self.video_call_repo.end_call(room_id)

# ===== NEW: ANNOTATION & PROGRESS SERVICES =====
class AnnotationService(BaseService):
    def __init__(self, annotation_repo: AnnotationRepository):
        self.annotation_repo = annotation_repo
    
    def validate_input(self, user_id: int, surah_number: int, verse_number: int, 
                      text: str, color: str) -> bool:
        return bool(user_id and surah_number > 0 and verse_number > 0 and text.strip())
    
    def add_annotation(self, user_id: int, surah_number: int, verse_number: int,
                      text: str, color: str = '#FFEB3B') -> tuple[bool, str]:
        if not self.validate_input(user_id, surah_number, verse_number, text, color):
            return False, "Invalid input data"
        
        success = self.annotation_repo.create_annotation(user_id, surah_number, verse_number, text, color)
        return success, "Annotation added successfully" if success else "Failed to add annotation"
    
    def get_user_annotations(self, user_id: int) -> List[Dict]:
        return self.annotation_repo.get_annotations_by_user(user_id)
    
    def get_verse_annotations(self, user_id: int, surah_number: int, verse_number: int) -> List[Dict]:
        return self.annotation_repo.get_annotations_by_verse(user_id, surah_number, verse_number)
    
    def update_annotation(self, annotation_id: int, user_id: int, text: str, color: str) -> tuple[bool, str]:
        if not text.strip():
            return False, "Annotation text cannot be empty"
        
        success = self.annotation_repo.update_annotation(annotation_id, user_id, text, color)
        return success, "Annotation updated successfully" if success else "Failed to update annotation"
    
    def delete_annotation(self, annotation_id: int, user_id: int) -> tuple[bool, str]:
        success = self.annotation_repo.delete_annotation(annotation_id, user_id)
        return success, "Annotation deleted successfully" if success else "Failed to delete annotation"

class ProgressService(BaseService):
    def __init__(self, progress_repo: ProgressRepository):
        self.progress_repo = progress_repo
    
    def validate_input(self, user_id: int, surah_number: int, verse_number: int,
                      action_type: str, duration: int) -> bool:
        return bool(user_id and surah_number > 0 and verse_number > 0 and action_type)
    
    def record_activity(self, user_id: int, surah_number: int, verse_number: int,
                       action_type: str, duration: int = 0) -> bool:
        if not self.validate_input(user_id, surah_number, verse_number, action_type, duration):
            return False
        return self.progress_repo.record_progress(user_id, surah_number, verse_number, action_type, duration)
    
    def get_user_progress(self, user_id: int) -> List[Dict]:
        return self.progress_repo.get_user_progress(user_id)
    
    def get_progress_summary(self, user_id: int) -> Dict:
        return self.progress_repo.get_progress_summary(user_id)

# ===== APPLICATION SETUP =====
# Initialize repositories
user_repo = UserRepository()
message_repo = MessageRepository()
review_repo = ReviewRepository()
video_call_repo = VideoCallRepository()
annotation_repo = AnnotationRepository()
progress_repo = ProgressRepository()

# Initialize services
user_service = UserService(user_repo)
message_service = MessageService(message_repo)
review_service = ReviewService(review_repo)
video_call_service = VideoCallService(video_call_repo, user_repo)
annotation_service = AnnotationService(annotation_repo)
progress_service = ProgressService(progress_repo)

# Database initialization
def init_db():
    user_repo.create_table()
    message_repo.create_table()
    review_repo.create_table()
    video_call_repo.create_table()
    annotation_repo.create_table()
    progress_repo.create_table()

init_db()

# ===== ROUTES =====
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user_type = request.form['user_type']
        
        success, message = user_service.register_user(username, password, user_type)
        if success:
            return redirect(url_for('login'))
        else:
            return message
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = user_service.authenticate_user(username, password)
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['user_type'] = user['user_type']
            return redirect(url_for('dashboard'))
        else:
            return "Invalid credentials"
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_type = session['user_type']
    user_id = session['user_id']
    
    # Get progress summary for dashboard
    progress_summary = progress_service.get_progress_summary(user_id)
    
    if user_type == 'teacher':
        students = user_service.get_users_by_type('student')
        reviews = review_service.get_teacher_reviews(user_id)
        teachers = None
    else:
        teachers = user_service.get_users_by_type('teacher')
        reviews = review_service.get_student_reviews(user_id)
        students = None
    
    return render_template('dashboard.html', 
                         user_type=user_type,
                         students=students,
                         teachers=teachers,
                         reviews=reviews,
                         progress_summary=progress_summary)

@app.route('/mushaf')
def mushaf():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get user's annotations for the mushaf
    user_id = session['user_id']
    annotations = annotation_service.get_user_annotations(user_id)
    
    return render_template('mushaf.html', annotations=annotations)

# ===== NEW: ANNOTATION ROUTES =====
@app.route('/add_annotation', methods=['POST'])
def add_annotation():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    try:
        data = request.json
        user_id = session['user_id']
        surah_number = int(data['surah_number'])
        verse_number = int(data['verse_number'])
        text = data['text']
        color = data.get('color', '#FFEB3B')
        
        success, message = annotation_service.add_annotation(
            user_id, surah_number, verse_number, text, color
        )
        
        return jsonify({'success': success, 'message': message})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/get_verse_annotations', methods=['GET'])
def get_verse_annotations():
    if 'user_id' not in session:
        return jsonify({'success': False, 'annotations': []})
    
    try:
        surah_number = int(request.args.get('surah_number'))
        verse_number = int(request.args.get('verse_number'))
        user_id = session['user_id']
        
        annotations = annotation_service.get_verse_annotations(
            user_id, surah_number, verse_number
        )
        
        return jsonify({'success': True, 'annotations': annotations})
    
    except Exception as e:
        return jsonify({'success': False, 'annotations': []})

@app.route('/update_annotation', methods=['POST'])
def update_annotation():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    try:
        data = request.json
        annotation_id = int(data['annotation_id'])
        user_id = session['user_id']
        text = data['text']
        color = data.get('color', '#FFEB3B')
        
        success, message = annotation_service.update_annotation(
            annotation_id, user_id, text, color
        )
        
        return jsonify({'success': success, 'message': message})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/delete_annotation', methods=['POST'])
def delete_annotation():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    try:
        data = request.json
        annotation_id = int(data['annotation_id'])
        user_id = session['user_id']
        
        success, message = annotation_service.delete_annotation(annotation_id, user_id)
        
        return jsonify({'success': success, 'message': message})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/my_annotations')
def my_annotations():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    annotations = annotation_service.get_user_annotations(user_id)
    
    return render_template('my_annotations.html', annotations=annotations)

# ===== NEW: PROGRESS TRACKING ROUTES =====
@app.route('/record_progress', methods=['POST'])
def record_progress():
    if 'user_id' not in session:
        return jsonify({'success': False})
    
    try:
        data = request.json
        user_id = session['user_id']
        surah_number = int(data['surah_number'])
        verse_number = int(data['verse_number'])
        action_type = data['action_type']
        duration = int(data.get('duration', 0))
        
        success = progress_service.record_activity(
            user_id, surah_number, verse_number, action_type, duration
        )
        
        return jsonify({'success': success})
    
    except Exception as e:
        return jsonify({'success': False})

@app.route('/progress_report')
def progress_report():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    progress_data = progress_service.get_user_progress(user_id)
    progress_summary = progress_service.get_progress_summary(user_id)
    
    return render_template('progress_report.html', 
                         progress_data=progress_data,
                         progress_summary=progress_summary)

# ===== EXISTING ROUTES (unchanged) =====
@app.route('/chat/<int:user_id>')
def chat(user_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    other_user = user_repo.get_user_by_id(user_id)
    if not other_user:
        return "User not found"
    
    messages = message_service.get_conversation(session['user_id'], user_id)
    
    return render_template('chat.html', other_user=other_user, messages=messages)

@app.route('/send_message', methods=['POST'])
def send_message():
    if 'user_id' not in session:
        return jsonify({'success': False})
    
    receiver_id = request.json['receiver_id']
    message_text = request.json['message']
    
    success = message_service.send_message(session['user_id'], receiver_id, message_text)
    
    if success:
        socketio.emit('new_message', {
            'sender_id': session['user_id'],
            'receiver_id': receiver_id,
            'message': message_text,
            'sender_name': session['username']
        })
    
    return jsonify({'success': success})

@app.route('/add_review', methods=['POST'])
def add_review():
    if 'user_id' not in session or session['user_type'] != 'teacher':
        return jsonify({'success': False})
    
    student_id = request.json['student_id']
    review_text = request.json['review']
    rating = request.json['rating']
    
    success = review_service.add_review(session['user_id'], student_id, review_text, rating)
    return jsonify({'success': success})

@app.route('/create_video_room/<int:other_user_id>')
def create_video_room(other_user_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    room_id = video_call_service.create_or_get_room(
        session['user_id'], 
        session['user_type'], 
        other_user_id
    )
    
    if not room_id:
        return "Failed to create video room"
    
    return redirect(url_for('video_call', room_id=room_id))


    # ===== NEW: TAJWEED ANALYSIS ROUTE =====
@app.route('/tajweed_analysis')
def tajweed_analysis():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Record progress for accessing tajweed analysis
    user_id = session['user_id']
    progress_service.record_activity(user_id, 0, 0, 'tajweed_analysis', 0)
    
    return render_template('tajweed_analysis.html', user_type=session['user_type'])

@app.route('/redirect_to_tarteel')
def redirect_to_tarteel():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Record that user used the tarteel redirect
    user_id = session['user_id']
    progress_service.record_activity(user_id, 0, 0, 'tarteel_redirect', 0)
    
    # Redirect to Tarteel.ai
    return redirect('https://www.tarteel.ai/')

@app.route('/join_video_room/<int:other_user_id>')
def join_video_room(other_user_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    room_id = video_call_service.create_or_get_room(
        session['user_id'], 
        session['user_type'], 
        other_user_id
    )
    
    if not room_id:
        return "No active call found. Please ask the teacher to start a call first."
    
    return redirect(url_for('video_call', room_id=room_id))

@app.route('/video_call/<room_id>')
def video_call(room_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if not video_call_service.can_user_access_room(room_id, session['user_id']):
        return "Access denied"
    
    call_data = video_call_service.get_room_details(room_id)
    if not call_data:
        return "Room not found"
    
    other_user_name = (call_data['teacher_name'] if session['user_type'] == 'student' 
                      else call_data['student_name'])
    
    return render_template('video_call.html', 
                         room_id=room_id, 
                         other_user_name=other_user_name,
                         user_type=session['user_type'])

# ===== SOCKET.IO HANDLERS =====
@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('join_room')
def handle_join_room(data):
    room_id = data['room_id']
    user_id = data.get('user_id')
    user_type = data.get('user_type')
    
    join_room(room_id)
    print(f'User {user_id} ({user_type}) joined room {room_id}')
    
    emit('user_joined', {
        'user_id': user_id,
        'user_type': user_type,
        'message': f'User {user_id} joined room {room_id}'
    }, room=room_id, include_self=False)

@socketio.on('webrtc_offer')
def handle_webrtc_offer(data):
    room_id = data['room_id']
    emit('webrtc_offer', {
        'offer': data['offer'],
        'sender_id': data['sender_id']
    }, room=room_id, include_self=False)

@socketio.on('webrtc_answer')
def handle_webrtc_answer(data):
    room_id = data['room_id']
    emit('webrtc_answer', {
        'answer': data['answer'],
        'sender_id': data['sender_id']
    }, room=room_id, include_self=False)

@socketio.on('ice_candidate')
def handle_ice_candidate(data):
    room_id = data['room_id']
    emit('ice_candidate', {
        'candidate': data['candidate'],
        'sender_id': data['sender_id']
    }, room=room_id, include_self=False)

@socketio.on('end_call')
def handle_end_call(data):
    room_id = data['room_id']
    emit('call_ended', {'message': 'Call ended by other user'}, room=room_id)
    video_call_service.end_call(room_id)

@socketio.on('toggle_video')
def handle_toggle_video(data):
    room_id = data['room_id']
    emit('video_toggled', {
        'video_enabled': data['video_enabled'],
        'sender_id': data['sender_id']
    }, room=room_id)

@socketio.on('toggle_audio')
def handle_toggle_audio(data):
    room_id = data['room_id']
    emit('audio_toggled', {
        'audio_enabled': data['audio_enabled'],
        'sender_id': data['sender_id']
    }, room=room_id)

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)