"""
SQLAlchemy ORM Models for Talaqqi Flask Backend.
Demonstrates: OOP, Encapsulation, Relationships.
"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from typing import List

db = SQLAlchemy()


class User(db.Model):
    """
    User model - represents teachers and students.
    Replaces UserRepository raw SQL with ORM.
    """
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password = db.Column(db.String(200), nullable=False)
    user_type = db.Column(db.String(20), nullable=False)  # 'teacher' or 'student'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    sent_messages = db.relationship('Message', foreign_keys='Message.sender_id', backref='sender', lazy='dynamic')
    received_messages = db.relationship('Message', foreign_keys='Message.receiver_id', backref='receiver', lazy='dynamic')
    given_reviews = db.relationship('Review', foreign_keys='Review.teacher_id', backref='teacher', lazy='dynamic')
    received_reviews = db.relationship('Review', foreign_keys='Review.student_id', backref='student', lazy='dynamic')
    
    # ML relationships
    recitation_analyses = db.relationship('RecitationAnalysis', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    progress_records = db.relationship('StudentProgress', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.username} ({self.user_type})>'
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'username': self.username,
            'user_type': self.user_type,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Message(db.Model):
    """Chat message model."""
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<Message from {self.sender_id} to {self.receiver_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'sender_id': self.sender_id,
            'receiver_id': self.receiver_id,
            'message': self.message,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'sender_name': self.sender.username if self.sender else None
        }


class Review(db.Model):
    """Teacher reviews for students."""
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    review = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Review by teacher {self.teacher_id} for student {self.student_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'teacher_id': self.teacher_id,
            'student_id': self.student_id,
            'review': self.review,
            'rating': self.rating,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'teacher_name': self.teacher.username if self.teacher else None,
            'student_name': self.student.username if self.student else None
        }


class VideoCall(db.Model):
    """Video call sessions."""
    __tablename__ = 'video_calls'
    
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    room_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    status = db.Column(db.String(20), default='active')  # active, ended
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    teacher = db.relationship('User', foreign_keys=[teacher_id])
    student = db.relationship('User', foreign_keys=[student_id])
    
    def __repr__(self):
        return f'<VideoCall room={self.room_id} status={self.status}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'room_id': self.room_id,
            'status': self.status,
            'teacher_id': self.teacher_id,
            'student_id': self.student_id,
            'teacher_name': self.teacher.username if self.teacher else None,
            'student_name': self.student.username if self.student else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# ===== ML/AI MODELS =====

class RecitationAnalysis(db.Model):
    """
    Recitation analysis results from AI Tajweed system.
    Stores overall analysis metadata.
    """
    __tablename__ = 'recitation_analyses'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, nullable=True)  # Optional link to video call session
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    audio_file_path = db.Column(db.String(500), nullable=False)
    transcription = db.Column(db.Text)  # Optional: Arabic text transcription
    overall_score = db.Column(db.Float)  # 0-100 score
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    tajweed_errors = db.relationship('TajweedError', backref='analysis', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<RecitationAnalysis id={self.id} student={self.student_id} score={self.overall_score}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'audio_file_path': self.audio_file_path,
            'overall_score': self.overall_score,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'errors': [error.to_dict() for error in self.tajweed_errors]
        }


class TajweedError(db.Model):
    """
    Individual Tajweed rule violations detected in recitation.
    Linked to RecitationAnalysis.
    """
    __tablename__ = 'tajweed_errors'
    
    id = db.Column(db.Integer, primary_key=True)
    analysis_id = db.Column(db.Integer, db.ForeignKey('recitation_analyses.id'), nullable=False, index=True)
    rule_type = db.Column(db.String(50), nullable=False)  # madd, ghunnah, ikhfa
    timestamp_in_audio = db.Column(db.Float, nullable=False)  # seconds
    ayah_reference = db.Column(db.String(100))  # e.g., "Al-Ma'idah:109"
    error_description = db.Column(db.Text, nullable=False)
    correction_suggestion = db.Column(db.Text)
    confidence_score = db.Column(db.Float, nullable=False)  # 0-1
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<TajweedError {self.rule_type} at {self.timestamp_in_audio}s>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'rule_type': self.rule_type,
            'timestamp': self.timestamp_in_audio,
            'description': self.error_description,
            'suggestion': self.correction_suggestion,
            'confidence': self.confidence_score
        }


class StudentProgress(db.Model):
    """
    Track student progress on specific Tajweed rules and verses.
    Used for personalized learning recommendations.
    """
    __tablename__ = 'student_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    surah_name = db.Column(db.String(100), nullable=False)  # e.g., "Al-Ma'idah"
    ayah_number = db.Column(db.Integer, nullable=False)  # e.g., 109
    tajweed_rule = db.Column(db.String(50), nullable=False)  # madd, ghunnah, ikhfa
    mastery_level = db.Column(db.Float, default=0.0)  # 0-100
    practice_count = db.Column(db.Integer, default=0)
    last_practiced_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Composite index for efficient querying
    __table_args__ = (
        db.Index('idx_student_surah_ayah', 'student_id', 'surah_name', 'ayah_number', 'tajweed_rule'),
    )
    
    def __repr__(self):
        return f'<StudentProgress student={self.student_id} {self.surah_name}:{self.ayah_number} {self.tajweed_rule} mastery={self.mastery_level}%>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'surah_name': self.surah_name,
            'ayah_number': self.ayah_number,
            'tajweed_rule': self.tajweed_rule,
            'mastery_level': self.mastery_level,
            'practice_count': self.practice_count,
            'last_practiced': self.last_practiced_at.isoformat() if self.last_practiced_at else None
        }


# ===== UTILITY FUNCTIONS =====

def init_db(app):
    """Initialize database with app context."""
    db.init_app(app)
    with app.app_context():
        db.create_all()
        print("✅ Database tables created successfully")
