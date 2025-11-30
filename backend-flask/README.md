# Talaqqi Flask Backend - Unified with SQLAlchemy ORM & ML

## Overview

Unified Flask backend combining user management, real-time communication, and AI-powered Tajweed analysis. Migrated from raw SQL to SQLAlchemy ORM following SOLID principles.

## Features

✅ **User Authentication**: Teachers and students registration/login  
✅ **Real-time Chat**: WebSocket messaging via Flask-SocketIO  
✅ **Video Calling**: WebRTC peer-to-peer video sessions  
✅ **AI Tajweed Analysis**: Upload audio for ML-powered recitation feedback  
✅ **Real-time Analysis**: Stream audio during video calls for instant Tajweed feedback  
✅ **Progress Tracking**: Monitor student improvement on specific Tajweed rules  
✅ **Review System**: Teachers can review student performance

## Tech Stack

- **Framework**: Flask 3.0.0
- **ORM**: SQLAlchemy (Flask-SQLAlchemy 3.1.1)
- **Real-time**: Flask-SocketIO 5.3.5 (WebSocket)
- **Database**: SQLite
- **ML Framework**: TensorFlow 2.15.0
- **Audio Processing**: librosa 0.10.1

## Architecture

### SOLID Principles Applied

**Single Responsibility**
- `UserRepository`: Only user database operations
- `MessageRepository`: Only message operations
- `TajweedAnalysisService`: Only Tajweed analysis orchestration

**Open/Closed**
- `BaseService`: Abstract class for service extension
- Repository pattern: Easy to swap ORM implementations

**Liskov Substitution**
- All Repository classes interchangeable via common interface patterns

**Interface Segregation**
- Separate service classes for distinct functionality

**Dependency Inversion**
- Services depend on Repository abstractions
- TajweedAnalysisService depends on ML facades

### Design Patterns

- **Repository Pattern**: Data access layer (with SQLAlchemy)
- **Service Layer**: Business logic separation
- **Facade Pattern**: `TajweedAnalyzer` simplifies ML pipeline
- **Factory Pattern**: `TajweedRuleDetectorFactory` creates rule detectors
- **Singleton Pattern**: `ModelLoader` caches ML models

## Project Structure

```
backend-flask/
├── app.py                      # Main Flask application (578 lines)
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

## Database Schema (SQLAlchemy Models)

### Core Models
- **User**: `id`, `username`, `password`, `user_type`, `created_at`
- **Message**: `id`, `sender_id`, `receiver_id`, `message`, `timestamp`
- **Review**: `id`, `teacher_id`, `student_id`, `review`, `rating`, `created_at`
- **VideoCall**: `id`, `teacher_id`, `student_id`, `room_id`, `status`, `created_at`

### ML/AI Models
- **RecitationAnalysis**: `id`, `student_id`, `session_id`, `audio_file_path`, `overall_score`, `timestamp`
- **TajweedError**: `id`, `analysis_id`, `rule_type`, `timestamp_in_audio`, `error_description`, `correction_suggestion`, `confidence_score`
- **StudentProgress**: `id`, `student_id`, `surah_name`, `ayah_number`, `tajweed_rule`, `mastery_level`, `practice_count`

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

### AI Tajweed Analysis (NEW)
- `POST /api/analysis/upload` - Upload audio for analysis
- `GET /api/analysis/<analysis_id>` - Get analysis results
- `GET /api/analysis/history` - Get student analysis history
- `GET /api/progress` - Get student Tajweed progress

## WebSocket Events

### Video Calling
- `connect/disconnect` - Connection management
- `join_room` - Join video room
- `webrtc_offer/answer` - WebRTC signaling
- `ice_candidate` - ICE candidate exchange
- `toggle_video/audio` - Media controls
- `end_call` - End video session

### Tajweed Analysis (NEW)
- `analyze_audio_stream` - Send audio chunk for real-time analysis
- `tajweed_feedback` - Receive Tajweed analysis results
- `tajweed_error` - Error notification

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
const socket = io('http://localhost:5000');

socket.emit('analyze_audio_stream', {
    audio_chunk: base64AudioData,
    room_id: roomId,
    student_id: studentId
});

socket.on('tajweed_feedback', (data) => {
    console.log('Score:', data.score);
    console.log('Feedback:', data.feedback);
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

- ML features require trained TensorFlow model
- WebSocket requires Socket.IO client library
- Audio files stored in `audio_files/` directory
- Maximum file size: 50MB (configurable)

## License

Educational project for Software Design and Analysis course.
