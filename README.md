# Talaqqi - Quran Recitation Learning Platform

A comprehensive platform for learning Quran recitation with AI-powered Tajweed analysis, live classes, and interactive features.

## Project Structure

```
Talaqqi/
├── backend-flask/          # Unified Flask backend (SQLAlchemy + ML)
├── backend-fastapi/        # (Legacy - ML components migrated to Flask)
├── Frontend/               # Frontend application
├── docs/                   # Documentation and deliverables
└── README.md              # This file
```

## Main Backend (Flask)

**Unified Flask backend** handling all functionality:
- User authentication (teachers/students)
- Real-time chat messaging (WebSocket)
- Video calling (WebRTC + SocketIO)
- **AI Tajweed analysis** (ML-powered recitation feedback)
- Student progress tracking
- Review system

**Tech Stack**: Flask, SQLAlchemy ORM, Flask-SocketIO, TensorFlow/Keras  
**Port**: 5000  
**Documentation**: See `backend-flask/README.md`

## Frontend

User interface files organized by purpose:
- `dashboards/` - Admin, student, and teacher dashboards
- `pages/` - Home, live class, registration pages
- `css/` - Stylesheets
- `assets/` - Static assets (colors, images)
- `video-call/` - Video calling module (Vite/WebRTC)
- `authentication.html` - Login/registration page

## Quick Start

### Running Backend (Flask)
```bash
cd backend-flask
pip install -r requirements.txt

# Initialize database
python
>>> from app import app, db
>>> with app.app_context():
...     db.create_all()
>>> exit()

# Run server
python app.py
# Visit: http://localhost:5000
```

### Frontend
Open frontend HTML files directly in your browser, or serve them using a local server.

## Key Features

### Implemented ✅
- User authentication (teachers & students)
- Real-time chat with WebSocket
- WebRTC video calling
- Teacher dashboards & student dashboards  
- Review system
- **SQLAlchemy ORM** (migrated from raw SQL)
- **ML Infrastructure** (TajweedAnalyzer, detectors, factories)
- **Tajweed Analysis API** (upload audio, get results, history)
- **Real-time Tajweed Feedback** (WebSocket streaming)
- **Student Progress Tracking** (mastery levels by rule)

### In Development 🚧
- ML model training (QDAT dataset)
- Frontend integration with ML endpoints
- Comprehensive testing suite

## Architecture

### Backend Design Patterns
- **Repository Pattern**: Data access with SQLAlchemy ORM
- **Service Layer**: Business logic separation
- **Facade Pattern**: `TajweedAnalyzer` simplifies ML pipeline
- **Factory Pattern**: `TajweedRuleDetectorFactory` creates detectors
- **Singleton Pattern**: `ModelLoader` caches ML models

### SOLID Principles
✅ **Single Responsibility**: Each class has one clear purpose  
✅ **Open/Closed**: Extensible via inheritance (BaseService, detectors)  
✅ **Liskov Substitution**: Interchangeable implementations  
✅ **Interface Segregation**: Separate interfaces for distinct functionality  
✅ **Dependency Inversion**: Services depend on abstractions

## Database Schema (SQLAlchemy Models)

**Core Tables**:
- `users` - User accounts (teachers/students)
- `messages` - Chat messages
- `reviews` - Teacher reviews
- `video_calls` - Video call sessions

**ML/AI Tables**:
- `recitation_analyses` - Audio analysis results
- `tajweed_errors` - Detected Tajweed rule violations
- `student_progress` - Progress tracking per rule/verse

## API Endpoints

### Authentication
- `POST /register` - User registration
- `POST /login` - User login

### Communication
- `GET /chat/<user_id>` - Chat interface
- `POST /send_message` - Send message

### Video Calling
- `GET /create_video_room/<user_id>` - Create/join room
- `GET /video_call/<room_id>` - Video interface

### AI Tajweed Analysis
- `POST /api/analysis/upload` - Upload audio
- `GET /api/analysis/<id>` - Get results
- `GET /api/analysis/history` - Student history
- `GET /api/progress` - Progress tracking

### WebSocket Events
- `analyze_audio_stream` - Stream audio for real-time analysis
- `tajweed_feedback` - Receive Tajweed feedback
- WebRTC signaling (offer, answer, ICE)

## Course Information

This project demonstrates:
- **Object-Oriented Programming (OOP)**: Classes, inheritance, encapsulation
- **Design Patterns**: Repository, Service Layer, Facade, Factory, Singleton
- **SOLID Principles**: All 5 principles applied throughout
- **Clean Architecture**: Separation of concerns
- **RESTful API Design**: Well-structured endpoints
- **Real-time Communication**: WebSocket for chat and live feedback

Developed for **Software Design and Analysis (SDA)** course.

## Technologies

- **Backend**: Flask 3.0.0, SQLAlchemy 3.1.1, Flask-SocketIO 5.3.5
- **ML/AI**: TensorFlow 2.15.0, librosa 0.10.1
- **Database**: SQLite (dev), PostgreSQL-ready
- **Real-time**: WebSocket (SocketIO)
- **Video**: WebRTC
- **Frontend**: HTML, CSS, JavaScript

## Development Status

**Phase 1**: ✅ Backend Infrastructure (Complete)  
**Phase 2**: ✅ SQLAlchemy Migration (Complete)  
**Phase 3**: ✅ ML Integration (Complete)  
**Phase 4**: 🚧 Model Training (In Progress)  
**Phase 5**: 🚧 Frontend Integration (Next)

## License

Educational project for academic purposes.
