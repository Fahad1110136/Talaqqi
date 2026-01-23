# Talaqqi - Quran Learning Platform

A comprehensive web platform for Quran study and recitation learning with real-time communication features, interactive Mushaf viewer, and progress tracking.

## 🎯 Project Overview

**Talaqqi** is an educational platform connecting Quran teachers and students through:

- **Interactive Mushaf**: Digital Quran with personal annotations and highlighting
- **Live Communication**: Real-time chat and video calling for remote learning
- **Progress Tracking**: Monitor reading habits and study activities
- **Teacher-Student System**: Review system and structured learning environment

**Developed for**: Software Design and Analysis (SDA) Course  
**Academic Purpose**: Demonstrating OOP principles, design patterns, and clean architecture

## 📁 Project Structure

```
Talaqqi/
├── backend-flask/          # Flask backend with Repository & Service patterns
│   ├── app.py             # Main application (901 lines)
│   ├── models.py          # SQLAlchemy models (prepared for future migration)
│   ├── templates/         # HTML templates (11 files)
│   ├── static/            # CSS and JavaScript
│   ├── ml/                # ML components (prepared for AI features)
│   └── services/          # Business logic layer
├── video-call/            # Standalone WebRTC video module (Vite + Firebase)
├── ml_training/           # ML model training notebooks (Kaggle TPU)
├── docs/                  # Documentation and course deliverables
│   ├── deliverables/     # Project deliverables (PDFs)
│   └── guides/           # Setup guides
└── README.md
```

## ✨ Implemented Features

### 🔐 User Authentication

- Separate registration/login for **teachers** and **students**
- Session-based authentication
- Role-based access control

### 📖 Interactive Mushaf Viewer

- Full Quran display with Arabic text
- **Personal annotations**: Add colored notes to any verse
- **Verse annotations**: Track insights and learning notes
- Annotation management (create, read, update, delete)
- Dedicated "My Annotations" page

### 💬 Real-Time Chat

- Direct messaging between teachers and students
- WebSocket-powered instant delivery
- Chat history persistence
- User-to-user conversation threads

### 📹 Video Calling

- WebRTC peer-to-peer video sessions
- Room-based video calls
- Support for teacher-student live classes
- WebSocket signaling for connection setup

### ⭐ Review System

- Teachers can review student performance
- 5-star rating system
- Written feedback and comments

### 📊 Progress Tracking

- Track verses read, listening time, and study activities
- Weekly activity summaries
- Annotation statistics
- Action-based tracking (read, listened, studied)

### 🎨 User Dashboard

- Personalized dashboard for teachers and students
- Progress summaries and statistics
- Quick access to all features

## 🏗️ Architecture & Design Patterns

### Design Patterns Implemented

#### 1. **Repository Pattern**

Separates data access logic from business logic:

```python
class UserRepository:
    def get_user_by_credentials(username, password)
    def create_user(username, password, user_type)
    # ... more data access methods
```

#### 2. **Service Layer Pattern**

Encapsulates business logic and validation:

```python
class UserService(BaseService):
    def register_user(username, password, user_type)
    def authenticate_user(username, password)
    # ... business logic methods
```

#### 3. **Context Manager Pattern**

Manages database connections safely:

```python
class DatabaseConnection:
    def __enter__(self)  # Acquire connection
    def __exit__(self)   # Release connection
```

#### 4. **Abstract Base Class**

Enforces service contracts:

```python
class BaseService(ABC):
    @abstractmethod
    def validate_input(*args, **kwargs)
```

### SOLID Principles

✅ **Single Responsibility**: Each class has one clear purpose (UserRepository for user data, MessageService for messaging logic)  
✅ **Open/Closed**: Services extended via inheritance (BaseService → UserService, MessageService)  
✅ **Liskov Substitution**: All services interchangeable via BaseService interface  
✅ **Interface Segregation**: Separate repositories for distinct concerns (User, Message, Review, VideoCall)  
✅ **Dependency Inversion**: Services depend on Repository abstractions, not concrete implementations

## 🗄️ Database Schema

### Current Implementation (SQLite with Raw SQL)

**Core Tables**:

- `users` - User accounts (id, username, password, user_type, created_at)
- `messages` - Chat messages with sender/receiver relationships
- `reviews` - Teacher reviews for students (rating, review text)
- `video_calls` - Video session management (room_id, status)

**Feature Tables**:

- `annotations` - Verse annotations (user_id, surah, ayah, text, color)
- `progress` - User activity tracking (action_type, duration, timestamp)

### Prepared for Future: SQLAlchemy Models

The `models.py` file contains complete SQLAlchemy ORM models with:

- Relationships and foreign keys
- Type safety with model classes
- Additional ML-ready tables (recitation_analyses, tajweed_errors, student_progress)

**Note**: Migration to SQLAlchemy ORM is planned but **not yet active** in the running application.

## 🔌 API Endpoints

### Authentication & User Management

- `POST /register` - User registration
- `POST /login` - User authentication
- `GET /logout` - End session
- `GET /dashboard` - User dashboard with statistics

### Mushaf & Annotations

- `GET /mushaf` - Interactive Quran viewer
- `POST /add_annotation` - Create verse annotation
- `GET /get_verse_annotations` - Get annotations for specific verse
- `POST /update_annotation` - Modify existing annotation
- `POST /delete_annotation` - Remove annotation
- `GET /my_annotations` - View all user annotations

### Progress Tracking

- `POST /record_progress` - Log user activity
- `GET /progress_report` - Detailed progress analytics

### Communication

- `GET /chat/<user_id>` - Chat interface
- `POST /send_message` - Send message (REST + WebSocket)
- `POST /add_review` - Teacher adds student review

### Video Calling

- `GET /create_video_room/<user_id>` - Create/join video room
- `GET /join_video_room/<user_id>` - Join existing room
- `GET /video_call/<room_id>` - Video call interface

### WebSocket Events

**Chat**: `new_message`  
**Video**: `join_room`, `webrtc_offer`, `webrtc_answer`, `ice_candidate`, `toggle_video`, `toggle_audio`, `end_call`

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- pip (Python package manager)

### Installation & Setup

```bash
# 1. Navigate to backend
cd backend-flask

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the application
python app.py

# 4. Access the application
# Open browser: http://localhost:5000
```

The database will be automatically created on first run with all required tables.

### First Steps

1. **Register**: Create teacher or student account at `/register`
2. **Login**: Access dashboard at `/login`
3. **Explore Mushaf**: Browse Quran and add annotations at `/mushaf`
4. **Start Learning**: Connect with teachers/students via chat or video

## 🛠️ Technology Stack

### Backend

- **Framework**: Flask 3.0.0
- **Real-time**: Flask-SocketIO 5.3.5 (WebSocket)
- **Database**: SQLite (development)
- **ORM (Prepared)**: Flask-SQLAlchemy 3.1.1
- **Session Management**: Flask sessions with secret key

### Frontend

- **Templates**: Jinja2 (Flask templating)
- **Styling**: Custom CSS
- **JavaScript**: Vanilla JS for interactivity
- **WebSocket**: Socket.IO client

### Video Module (Standalone)

- **Build Tool**: Vite
- **WebRTC**: Peer-to-peer video
- **Signaling**: Firebase Firestore (optional backend)

### ML Preparation

- **Framework**: TensorFlow 2.x
- **Audio**: librosa 0.10.1
- **Models**: Wav2Vec2 for Tajweed analysis (training notebooks ready)

## 📋 Development Roadmap

### ✅ Phase 1: Core Features (Complete)

- User authentication system
- Chat messaging with WebSocket
- Video calling infrastructure
- Repository and Service patterns
- Database schema design

### ✅ Phase 2: Mushaf Features (Complete)

- Interactive Quran viewer
- Annotation system (CRUD operations)
- Progress tracking
- Dashboard analytics

### 🚧 Phase 3: ML Integration (In Progress)

- [ ] Migrate to SQLAlchemy ORM (models ready)
- [ ] Train Tajweed classifier model (notebooks prepared)
- [ ] Integrate ML endpoints into app.py
- [ ] Real-time Tajweed feedback via WebSocket

### 📅 Phase 4: Enhancement (Planned)

- [ ] Frontend polish and responsive design
- [ ] Comprehensive testing suite
- [ ] Docker containerization
- [ ] Production deployment guide
- [ ] PostgreSQL migration for production

## 🧪 Testing

**Current Status**: Manual testing completed for all features

**Planned**:

```bash
# Unit tests
pytest tests/test_repositories.py
pytest tests/test_services.py

# Integration tests
pytest tests/test_api.py
pytest tests/test_websocket.py
```

## 🎓 Academic Learning Outcomes

This project demonstrates proficiency in:

1. **Object-Oriented Programming**
   - Classes and objects
   - Inheritance (BaseService)
   - Encapsulation (Repository pattern)
   - Polymorphism (Service implementations)

2. **Software Design**
   - Repository Pattern
   - Service Layer Pattern
   - MVC architecture
   - Separation of concerns

3. **SOLID Principles**
   - All 5 principles applied throughout codebase
   - Clean, maintainable architecture

4. **Real-World Skills**
   - RESTful API design
   - WebSocket real-time communication
   - Database design and relationships
   - Session management and authentication
   - WebRTC video technology

## 📝 Documentation

- **Main README**: `README.md` (this file)
- **Backend Details**: `backend-flask/README.md`
- **ML Training**: `ml_training/README.md`
- **Video Module**: `video-call/README.md`
- **Implementation Walkthrough**: `walkthrough.md`

## 🤝 Contributing

This is an academic project. For educational purposes only.

## 📄 License

Educational project for Software Design and Analysis course.

---

**Note**: This project emphasizes **software architecture and design principles** over production-level polish. The focus is on demonstrating clean code, design patterns, and SOLID principles in a real-world application context.
