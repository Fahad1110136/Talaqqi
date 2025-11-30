# Talaqqi - Quran Recitation Learning Platform

A comprehensive platform for learning Quran recitation with AI-powered Tajweed analysis, live classes, and interactive features.

## Project Structure

```
Talaqqi/
├── backend-flask/          # Flask backend (User management, chat, video calls)
├── backend-fastapi/        # FastAPI backend (AI/ML Tajweed analysis)
├── Frontend/               # Frontend application
├── docs/                   # Documentation and deliverables
└── README.md              # This file
```

## Components

### Backend - Flask (`backend-flask/`)
Legacy Flask application handling:
- User authentication (teachers/students)
- Real-time chat messaging
- Video calling (WebRTC)
- Student dashboards
- Teacher dashboards
- Mushaf (Quran) viewer

**Tech Stack**: Flask, Flask-SocketIO, SQLite  
**Port**: 5000  
**Documentation**: See `backend-flask/README.md`

### Backend - FastAPI (`backend-fastapi/`)
New AI/ML backend for Tajweed analysis:
- Audio recitation analysis
- Tajweed rule detection (Al-Madd, Ghunnah, Ikhfāʾ)
- ML model inference
- Student progress tracking  

**Tech Stack**: FastAPI, TensorFlow/Keras, SQLAlchemy  
**Port**: 8000  
**Documentation**: See `backend-fastapi/README.md`

### Frontend (`Frontend/`)
User interface files organized by purpose:
- `dashboards/` - Admin, student, and teacher dashboards
- `pages/` - Home, live class, registration pages
- `css/` - Stylesheets
- `assets/` - Static assets (colors, images)
- `video-call/` - Video calling module (Vite/WebRTC)
- `authentication.html` - Login/registration page

### Documentation (`docs/`)
- `deliverables/` - Course deliverables (PDFs)
- `guides/` - User guides and tutorials

## Quick Start

### Running Flask Backend
```bash
cd backend-flask
pip install -r requirements.txt
python app.py
# Visit: http://localhost:5000
```

### Running FastAPI Backend
```bash
cd backend-fastapi
pip install -r requirements.txt
python main.py
# Visit: http://localhost:8000
# API Docs: http://localhost:8000/api/v1/docs
```

### Frontend
Open frontend HTML files directly in your browser, or serve them using a local server.

## Development

- **Backend (Flask)**: Handles user sessions, real-time messaging with WebSocket (SocketIO), video calls
- **Backend (FastAPI)**: Processes audio recitations, performs Tajweed analysis using ML models
- **Frontend**: Static HTML/CSS/JS files, can be served independently or integrated with backends

## Architecture Patterns

Both backends follow software design best practices:
- **SOLID Principles**: Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion
- **Design Patterns**: Singleton, Factory, Strategy, Facade, Repository Pattern, Chain of Responsibility
- **Clean Code**: Type hints, comprehensive logging, error handling

## Course Information

This project is developed for the Software Design and Analysis (SDA) course, demonstrating:
- Object-Oriented Programming (OOP)
- Design Patterns
- SOLID Principles
- Clean Architecture
- RESTful API Design
- Real-time Communication

## License

Educational project for academic purposes.
