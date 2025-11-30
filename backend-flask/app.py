"""
Talaqqi Flask Backend - Unified with SQLAlchemy ORM and ML Integration.
Demonstrates: SOLID Principles, Repository Pattern with ORM, Service Layer, WebSocket.
"""
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import logging
import base64
import numpy as np

# Import configuration and models
from config import Config
from models import db, init_db, User, Message, Review, VideoCall, RecitationAnalysis, TajweedError, StudentProgress

# Import services
from services.tajweed_service import TajweedAnalysisService

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize database
init_db(app)

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins=app.config['SOCKETIO_CORS_ALLOWED_ORIGINS'])

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize Tajweed service
tajweed_service = TajweedAnalysisService()

# ===== REPOSITORY LAYER (SQLAlchemy ORM) =====

class UserRepository:
    """User repository using SQLAlchemy ORM - replaced raw SQL"""
    
    @staticmethod
    def create_user(username: str, password: str, user_type: str) -> bool:
        try:
            user = User(username=username, password=password, user_type=user_type)
            db.session.add(user)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"Create user failed: {e}")
            return False
    
    @staticmethod
    def get_user_by_credentials(username: str, password: str) -> Optional[User]:
        return User.query.filter_by(username=username, password=password).first()
    
    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[User]:
        return User.query.get(user_id)
    
    @staticmethod
    def get_users_by_type(user_type: str) -> List[User]:
        return User.query.filter_by(user_type=user_type).all()


class MessageRepository:
    """Message repository using SQLAlchemy ORM"""
    
    @staticmethod
    def create_message(sender_id: int, receiver_id: int, message: str) -> bool:
        try:
            msg = Message(sender_id=sender_id, receiver_id=receiver_id, message=message)
            db.session.add(msg)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"Create message failed: {e}")
            return False
    
    @staticmethod
    def get_conversation(user1_id: int, user2_id: int) -> List[Message]:
        return Message.query.filter(
            ((Message.sender_id == user1_id) & (Message.receiver_id == user2_id)) |
            ((Message.sender_id == user2_id) & (Message.receiver_id == user1_id))
        ).order_by(Message.timestamp).all()


class ReviewRepository:
    """Review repository using SQLAlchemy ORM"""
    
    @staticmethod
    def create_review(teacher_id: int, student_id: int, review: str, rating: int) -> bool:
        try:
            rev = Review(teacher_id=teacher_id, student_id=student_id, review=review, rating=rating)
            db.session.add(rev)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"Create review failed: {e}")
            return False
    
    @staticmethod
    def get_reviews_by_teacher(teacher_id: int) -> List[Review]:
        return Review.query.filter_by(teacher_id=teacher_id).all()
    
    @staticmethod
    def get_reviews_by_student(student_id: int) -> List[Review]:
        return Review.query.filter_by(student_id=student_id).all()


class VideoCallRepository:
    """Video call repository using SQLAlchemy ORM"""
    
    @staticmethod
    def create_video_call(teacher_id: int, student_id: int, room_id: str) -> bool:
        try:
            call = VideoCall(teacher_id=teacher_id, student_id=student_id, room_id=room_id)
            db.session.add(call)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"Create video call failed: {e}")
            return False
    
    @staticmethod
    def get_active_call(teacher_id: int, student_id: int) -> Optional[VideoCall]:
        return VideoCall.query.filter_by(
            teacher_id=teacher_id,
            student_id=student_id,
            status='active'
        ).first()
    
    @staticmethod
    def get_call_by_room_id(room_id: str) -> Optional[VideoCall]:
        return VideoCall.query.filter_by(room_id=room_id).first()
    
    @staticmethod
    def end_call(room_id: str) -> bool:
        try:
            call = VideoCall.query.filter_by(room_id=room_id).first()
            if call:
                call.status = 'ended'
                db.session.commit()
                return True
            return False
        except Exception as e:
            db.session.rollback()
            logger.error(f"End call failed: {e}")
            return False


# ===== SERVICE LAYER (Open/Closed Principle) =====

class BaseService(ABC):
    """Abstract base class for services - OCP"""
    @abstractmethod
    def validate_input(self, *args, **kwargs) -> bool:
        pass


class UserService(BaseService):
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
    
    def validate_input(self, username: str, password: str, user_type: str) -> bool:
        return bool(username and password and user_type in ['teacher', 'student'])
    
    def register_user(self, username: str, password: str, user_type: str) -> tuple:
        if not self.validate_input(username, password, user_type):
            return False, "Invalid input data"
        
        success = self.user_repo.create_user(username, password, user_type)
        if success:
            return True, "Registration successful"
        return False, "Username already exists"
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        return self.user_repo.get_user_by_credentials(username, password)
    
    def get_users_by_type(self, user_type: str) -> List[User]:
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
    
    def get_conversation(self, user1_id: int, user2_id: int) -> List[Message]:
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
    
    def get_teacher_reviews(self, teacher_id: int) -> List[Review]:
        return self.review_repo.get_reviews_by_teacher(teacher_id)
    
    def get_student_reviews(self, student_id: int) -> List[Review]:
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
            return existing_call.room_id
        
        room_id = str(uuid.uuid4())
        success = self.video_call_repo.create_video_call(teacher_id, student_id, room_id)
        return room_id if success else None
    
    def get_room_details(self, room_id: str) -> Optional[VideoCall]:
        return self.video_call_repo.get_call_by_room_id(room_id)
    
    def can_user_access_room(self, room_id: str, user_id: int) -> bool:
        room_details = self.get_room_details(room_id)
        if not room_details:
            return False
        return user_id in [room_details.teacher_id, room_details.student_id]
    
    def end_call(self, room_id: str) -> bool:
        return self.video_call_repo.end_call(room_id)


# ===== APPLICATION SETUP =====
# Initialize repositories
user_repo = UserRepository()
message_repo = MessageRepository()
review_repo = ReviewRepository()
video_call_repo = VideoCallRepository()

# Initialize services
user_service = UserService(user_repo)
message_service = MessageService(message_repo)
review_service = ReviewService(review_repo)
video_call_service = VideoCallService(video_call_repo, user_repo)

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
            session['user_id'] = user.id
            session['username'] = user.username
            session['user_type'] = user.user_type
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
                         students=[s.to_dict() for s in students] if students else None,
                         teachers=[t.to_dict() for t in teachers] if teachers else None,
                         reviews=[r.to_dict() for r in reviews])


@app.route('/mushaf')
def mushaf():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('mushaf.html')


@app.route('/chat/<int:user_id>')
def chat(user_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    other_user = user_repo.get_user_by_id(user_id)
    if not other_user:
        return "User not found"
    
    messages = message_service.get_conversation(session['user_id'], user_id)
    
    return render_template('chat.html', 
                         other_user=other_user.to_dict(), 
                         messages=[m.to_dict() for m in messages])


@app.route('/send_message', methods=['POST'])
def send_message():
    if 'user_id' not in session:
        return jsonify({'success': False}), 401
    
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
        return jsonify({'success': False}), 401
    
    student_id = request.json['student_id']
    review_text = request.json['review']
    rating = request.json['rating']
    
    success = review_service.add_review(session['user_id'], student_id, review_text, rating)
    return jsonify({'success': success})


# ===== VIDEO CALL ROUTES =====

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
    
    other_user_name = (call_data.teacher.username if session['user_type'] == 'student' 
                      else call_data.student.username)
    
    return render_template('video_call.html', 
                         room_id=room_id, 
                         other_user_name=other_user_name,
                         user_type=session['user_type'])


# ===== AI/ML TAJWEED ANALYSIS ROUTES =====

@app.route('/api/analysis/upload', methods=['POST'])
def upload_audio():
    """Upload audio file for Tajweed analysis"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    if 'audio' not in request.files:
        return jsonify({'success': False, 'error': 'No audio file'}), 400
    
    audio_file = request.files['audio']
    
    # Validate file
    if audio_file.filename == '':
        return jsonify({'success': False, 'error': 'Empty filename'}), 400
    
    # Save file
    filename = secure_filename(f"{session['user_id']}_{datetime.utcnow().timestamp()}.wav")
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    audio_file.save(filepath)
    
    try:
        # Analyze audio
        result = tajweed_service.analyze_audio_file(filepath, session['user_id'])
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/analysis/<int:analysis_id>')
def get_analysis(analysis_id):
    """Retrieve analysis results by ID"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    result = tajweed_service.get_analysis_by_id(analysis_id, session['user_id'])
    
    if not result:
        return jsonify({'error': 'Analysis not found'}), 404
    
    return jsonify(result)


@app.route('/api/analysis/history')
def get_analysis_history():
    """Get student's analysis history"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    limit = request.args.get('limit', 10, type=int)
    history = tajweed_service.get_student_history(session['user_id'], limit)
    
    return jsonify({'history': history})


@app.route('/api/progress')
def get_progress():
    """Get student's Tajweed progress"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    progress = tajweed_service.get_student_progress(session['user_id'])
    
    return jsonify({'progress': progress})


# ===== SOCKET.IO HANDLERS =====

@socketio.on('connect')
def handle_connect():
    logger.info('Client connected')


@socketio.on('disconnect')
def handle_disconnect():
    logger.info('Client disconnected')


@socketio.on('join_room')
def handle_join_room(data):
    room_id = data['room_id']
    user_id = data.get('user_id')
    user_type = data.get('user_type')
    
    join_room(room_id)
    logger.info(f'User {user_id} ({user_type}) joined room {room_id}')
    
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


# ===== REAL-TIME TAJWEED ANALYSIS (WebSocket) =====

@socketio.on('analyze_audio_stream')
def handle_audio_stream(data):
    """Real-time audio analysis during video call"""
    try:
        audio_chunk_b64 = data['audio_chunk']
        room_id = data['room_id']
        student_id = data.get('student_id', session.get('user_id'))
        
        # Decode base64 audio
        audio_bytes = base64.b64decode(audio_chunk_b64)
        audio_array = np.frombuffer(audio_bytes, dtype=np.float32)
        
        # Analyze chunk
        result = tajweed_service.analyze_audio_stream(audio_array, student_id, room_id)
        
        # Emit results to room
        emit('tajweed_feedback', {
            'score': result.get('overall_score', 0),
            'detections': result.get('detections', []),
            'feedback': result.get('feedback', [])
        }, room=room_id)
        
    except Exception as e:
        logger.error(f"Stream analysis failed: {str(e)}")
        emit('tajweed_error', {'error': str(e)}, room=data.get('room_id'))


if __name__ == '__main__':
    socketio.run(app, debug=app.config['DEBUG'], host='0.0.0.0', port=5000)