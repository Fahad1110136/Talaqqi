"""
Database models for Talaqqi application.
Demonstrates: OOP, Encapsulation, Single Responsibility Principle.
"""
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from enum import Enum
from config import settings

# Create database engine
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all models
Base = declarative_base()


# Enums for type safety
class UserRole(str, Enum):
    """User roles in the system."""
    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"


class SessionStatus(str, Enum):
    """Live class session statuses."""
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TajweedRule(str, Enum):
    """Supported Tajweed rules."""
    MADD = "madd"
    GHUNNAH = "ghunnah"
    IKHFA = "ikhfa"


# Database Models (following Single Responsibility Principle)

class User(Base):
    """
    User model - represents students, teachers, and admins.
    Demonstrates: Encapsulation, clear data layer.
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    teaching_sessions = relationship("Session", foreign_keys="Session.teacher_id", back_populates="teacher")
    student_sessions = relationship("Session", foreign_keys="Session.student_id", back_populates="student")
    recitation_analyses = relationship("RecitationAnalysis", back_populates="student")
    progress_records = relationship("StudentProgress", back_populates="student")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"


class Session(Base):
    """
    Live class session model.
    Tracks teacher-student recitation sessions.
    """
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    status = Column(SQLEnum(SessionStatus), default=SessionStatus.SCHEDULED)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    teacher = relationship("User", foreign_keys=[teacher_id], back_populates="teaching_sessions")
    student = relationship("User", foreign_keys=[student_id], back_populates="student_sessions")
    recitation_analyses = relationship("RecitationAnalysis", back_populates="session")
    
    def __repr__(self):
        return f"<Session(id={self.id}, status='{self.status}')>"


class RecitationAnalysis(Base):
    """
    Recitation analysis result model.
    Stores AI analysis results for student recitations.
    """
    __tablename__ = "recitation_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    audio_file_path = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Analysis results
    transcription = Column(String)  # Optional: transcribed text
    tajweed_errors = Column(JSON)  # List of detected errors
    overall_score = Column(Float)  # 0-100 score
    
    # Relationships
    session = relationship("Session", back_populates="recitation_analyses")
    student = relationship("User", back_populates="recitation_analyses")
    errors = relationship("TajweedError", back_populates="analysis")
    
    def __repr__(self):
        return f"<RecitationAnalysis(id={self.id}, score={self.overall_score})>"


class TajweedError(Base):
    """
    Individual Tajweed error detected in a recitation.
    Granular error tracking for detailed feedback.
    """
    __tablename__ = "tajweed_errors"
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("recitation_analyses.id"), nullable=False)
    rule_type = Column(SQLEnum(TajweedRule), nullable=False)
    timestamp_in_audio = Column(Float, nullable=False)  # seconds
    ayah_reference = Column(String)  # e.g., "Al-Ma'idah:109"
    error_description = Column(String, nullable=False)
    correction_suggestion = Column(String)
    confidence_score = Column(Float, nullable=False)  # 0-1
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    analysis = relationship("RecitationAnalysis", back_populates="errors")
    
    def __repr__(self):
        return f"<TajweedError(id={self.id}, rule='{self.rule_type}', confidence={self.confidence_score})>"


class StudentProgress(Base):
    """
    Student progress tracking model.
    Monitors improvement in specific Tajweed rules and verses.
    """
    __tablename__ = "student_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    surah_name = Column(String, nullable=False)  # e.g., "Al-Ma'idah"
    ayah_number = Column(Integer, nullable=False)  # e.g., 109
    tajweed_rule = Column(SQLEnum(TajweedRule), nullable=False)
    mastery_level = Column(Float, default=0.0)  # 0-100
    practice_count = Column(Integer, default=0)
    last_practiced_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    student = relationship("User", back_populates="progress_records")
    
    def __repr__(self):
        return f"<StudentProgress(student={self.student_id}, rule='{self.tajweed_rule}', mastery={self.mastery_level})>"


# Database initialization
def init_db():
    """
    Initialize database tables.
    Creates all tables defined in Base.
    """
    Base.metadata.create_all(bind=engine)


def get_db():
    """
    Dependency injection for database sessions.
    Yields a database session and ensures cleanup.
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
