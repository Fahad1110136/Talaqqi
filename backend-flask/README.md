# Talaqqi Flask Backend

## Overview

Flask backend for the Talaqqi Quran learning platform, implementing user management, real-time communication, interactive Mushaf viewer, and progress tracking using Repository and Service Layer patterns.

## Features

✅ **User Authentication**: Teachers and students registration/login  
✅ **Real-time Chat**: WebSocket messaging via Flask-SocketIO  
✅ **Video Calling**: WebRTC peer-to-peer video sessions  
✅ **Interactive Mushaf**: Digital Quran viewer with verse annotations  
✅ **Annotation System**: Personal notes with color coding (CRUD operations)  
✅ **Progress Tracking**: Monitor verses read, listening time, and study activities  
✅ **Review System**: Teachers can review student performance

## Tech Stack

- **Framework**: Flask 3.0.0
- **Real-time**: Flask-SocketIO 5.3.5 (WebSocket)
- **Database**: SQLite with raw SQL (sqlite3)
- **ORM (Prepared)**: SQLAlchemy models ready for future migration
- **ML Components (Prepared)**: TensorFlow, librosa infrastructure (not yet integrated)

## Architecture

### SOLID Principles Applied

**Single Responsibility**

- `UserRepository`: Only user database operations
- `MessageRepository`: Only message operations
- `AnnotationRepository`: Only annotation data access

**Open/Closed**

- `BaseService`: Abstract class for service extension
- Repository pattern: Easy to swap ORM implementations

**Liskov Substitution**

- All Repository classes interchangeable via common interface patterns

**Interface Segregation**

- Separate service classes for distinct functionality

**Dependency Inversion**

- Services depend on Repository abstractions
- High-level modules independent of low-level database details

### Design Patterns Implemented

- **Repository Pattern**: Data access layer (raw SQL with context managers)
- **Service Layer**: Business logic separation and validation
- **Context Manager Pattern**: Safe database connection handling
- **Abstract Base Class**: Service interface enforcement

### Design Patterns Prepared (ML components)

- **Facade Pattern**: `TajweedAnalyzer` (in ml/ directory, not yet integrated)
- **Factory Pattern**: `TajweedRuleDetectorFactory` (prepared for future use)
- **Singleton Pattern**: `ModelLoader` (prepared for model caching)

## Project Structure

```
backend-flask/
├── app.py                      # Main Flask application (901 lines)
├── models.py                   # SQLAlchemy ORM models
├── config.py                   # Configuration settings
├── requirements.txt            # Dependencies
├── .env.example               # Environment variables template
│
├── ml/                         # ML components (from FastAPI)
│   ├── interfaces/            # Abstract base classes
│   ├── implementations/       # AudioProcessor, TajweedClassifier, ModelLoader
│   ├── detectors/             # MaddDetector, GhunnahDetector, IkhfaDetector
│   ├── factories/             # TajweedRuleDetectorFactory
│   └── facades/               # TajweedAnalyzer
│
├── services/                   # Business logic services
│   └── tajweed_service.py    # TajweedAnalysisService
│
├── utils/                      # Utilities
│   ├── exceptions.py          # Custom exceptions
│   ├── audio_utils.py         # Audio validation
│   └── response_helpers.py   # Response formatting
│
├── audio_files/                # Uploaded audio storage
├── static/                     # CSS, JS, images
└── templates/                  # HTML templates
```

## Database Schema

### Current Implementation (SQLite + Raw SQL)

**Core Tables**:

- **users**: `id`, `username`, `password`, `user_type`, `created_at`
- **messages**: `id`, `sender_id`, `receiver_id`, `message`, `timestamp`
- **reviews**: `id`, `teacher_id`, `student_id`, `review`, `rating`, `created_at`
- **video_calls**: `id`, `teacher_id`, `student_id`, `room_id`, `status`, `created_at`

**Feature Tables**:

- **annotations**: `id`, `user_id`, `surah_number`, `verse_number`, `text`, `color`, `created_at`, `updated_at`
- **progress**: `id`, `user_id`, `surah_number`, `verse_number`, `action_type`, `duration`, `created_at`

### Prepared: SQLAlchemy Models (models.py)

The `models.py` file contains ORM models for future migration:

- All core tables with relationships and foreign keys
- Additional ML tables: `RecitationAnalysis`, `TajweedError`, `StudentProgress` (ready for AI features)
- Type safety with model classes and `.to_dict()` methods

**Status**: Models defined but **not yet used** in app.py

## API Endpoints

### Authentication & User Management

- `GET /` - Home page
- `POST /register` - User registration
- `POST /login` - User login
- `GET /logout` - Logout
- `GET /dashboard` - User dashboard

### Communication

- `GET /chat/<user_id>` - Chat interface
- `POST /send_message` - Send message
- `POST /add_review` - Add student review

### Video Calling

- `GET /create_video_room/<user_id>` - Create video room
- `GET /join_video_room/<user_id>` - Join existing room
- `GET /video_call/<room_id>` - Video call interface

### Mushaf & Annotations

- `GET /mushaf` - Interactive Quran viewer
- `POST /add_annotation` - Create verse annotation
- `GET /get_verse_annotations` - Get annotations for specific verse
- `POST /update_annotation` - Modify annotation
- `POST /delete_annotation` - Remove annotation
- `GET /my_annotations` - View all user annotations

### Progress Tracking

- `POST /record_progress` - Log user activity (read, listened, studied)
- `GET /progress_report` - Progress analytics dashboard
- `GET /tajweed_analysis` - Tajweed analysis page (redirects to external tool)
- `GET /redirect_to_tarteel` - External Tajweed analysis via Tarteel.ai

## WebSocket Events

### Video Calling

- `connect/disconnect` - Connection management
- `join_room` - Join video room
- `webrtc_offer/answer` - WebRTC signaling
- `ice_candidate` - ICE candidate exchange
- `toggle_video/audio` - Media controls
- `end_call` - End video session

### Chat & Messaging

- `new_message` - Real-time message delivery to recipient

## Setup & Installation

### 1. Install Dependencies

```bash
cd backend-flask
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings
```

### 3. Initialize Database

```bash
python
>>> from app import app, db
>>> with app.app_context():
...     db.create_all()
>>> exit()
```

### 4. Run Application

```bash
python app.py
# Visit: http://localhost:5000
```

## ML Model Setup (Optional - for full functionality)

1. Download QDAT dataset from Kaggle
2. Train CNN/LSTM model on Al-Ma'idah verse 109
3. Save model as `models/tajweed_classifier.keras`
4. Update `MODEL_PATH` in `.env`

Without trained model, ML endpoints will return graceful errors.

## Usage Examples

### Upload Audio for Analysis

```python
import requests

files = {'audio': open('recitation.wav', 'rb')}
response = requests.post(
    'http://localhost:5000/api/analysis/upload',
    files=files,
    cookies={'session': session_cookie}
)
result = response.json()
print(f"Score: {result['result']['overall_score']}")
```

### Real-time Analysis (WebSocket)

```javascript
const socket = io("http://localhost:5000");

socket.emit("analyze_audio_stream", {
  audio_chunk: base64AudioData,
  room_id: roomId,
  student_id: studentId,
});

socket.on("tajweed_feedback", (data) => {
  console.log("Score:", data.score);
  console.log("Feedback:", data.feedback);
});
```

## Migration from Raw SQL to SQLAlchemy

**Before** (Raw SQL):

```python
with DatabaseConnection() as conn:
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
```

**After** (SQLAlchemy ORM):

```python
user = User.query.filter_by(username=username).first()
```

### Benefits

- Type safety with model classes
- Automatic relationship loading
- Query builder for complex queries
- Built-in connection pooling
- Easier testing with mocking

## Development

- **Port**: 5000
- **Debug Mode**: Enabled by default (set `DEBUG=False` in production)
- **Database**: SQLite (`database.db`)
- **Logs**: Console output with structured logging

## Testing

```bash
# Unit tests (to be added)
pytest tests/test_services.py
pytest tests/test_models.py

# Integration tests
pytest tests/test_api.py
```

## Production Deployment

1. Set `DEBUG=False` in `.env`
2. Change `SECRET_KEY` to secure random value
3. Use PostgreSQL instead of SQLite
4. Deploy with Gunicorn + Nginx
5. Use Redis for session storage
6. Enable HTTPS

## Notes

- **ML Infrastructure**: ML components exist in `ml/` directory but are not yet integrated into app.py
- **SQLAlchemy Models**: Complete ORM models exist in `models.py` for future migration
- **Current Database**: Using SQLite with raw SQL via context managers
- **WebSocket**: Socket.IO client required for real-time features
- **Annotations**: Stored in SQLite, support personal study notes

## License

Educational project for Software Design and Analysis course.
