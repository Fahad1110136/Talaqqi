# Talaqqi Flask Backend

Legacy Flask application for the Talaqqi platform, handling user management, messaging, and video calling.

## Features

- **User Authentication**: Registration and login for teachers and students
- **Real-time Chat**: WebSocket-based messaging between users
- **Video Calling**: WebRTC-based video calls between teachers and students
- **Dashboards**: Separate dashboards for teachers and students
- **Reviews System**: Teachers can review student performance
- **Mushaf Viewer**: Interactive Quran viewer

## Architecture

This backend follows SOLID principles and design patterns:

- **Repository Pattern**: Separate repositories for users, messages, reviews, and video calls
- **Service Layer**: Business logic separated from data access
- **Single Responsibility**: Each class has one clear purpose
- **Dependency Injection**: Services receive their dependencies

## Structure

```
backend-flask/
├── app.py              # Main Flask application
├── database.db         # SQLite database
├── requirements.txt    # Python dependencies
├── static/             # Static files (CSS, JS)
│   ├── css/
│   └── js/
└── templates/          # HTML templates
```

## Database Schema

- **users**: User accounts (teachers/students)
- **messages**: Chat messages between users
- **reviews**: Teacher reviews of students
- **video_calls**: Video calling sessions

## Running the Application

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
python app.py

# Visit http://localhost:5000
```

## API Endpoints

- `GET /` - Home page
- `GET /register` - Registration page
- `GET /login` - Login page
- `GET /dashboard` - User dashboard
- `GET /chat/<user_id>` - Chat with specific user
- `GET /mushaf` - Quran viewer
- `POST /send_message` - Send chat message
- `POST /add_review` - Add student review
- `GET /create_video_room/<user_id>` - Create video call
- `GET /video_call/<room_id>` - Join video call

## WebSocket Events

- `connect` - Client connected
- `disconnect` - Client disconnected
- `join_room` - User joined video room
- `webrtc_offer` - WebRTC offer
- `webrtc_answer` - WebRTC answer
- `ice_candidate` - ICE candidate exchange
- `end_call` - Call ended
- `toggle_video` - Video toggled
- `toggle_audio` - Audio toggled

## Dependencies

- Flask: Web framework
- Flask-SocketIO: WebSocket support
- SQLite3: Database

## Tech Stack

- **Backend**: Flask, Flask-SocketIO
- **Database**: SQLite
- **Real-time**: WebSocket (SocketIO)
- **Video**: WebRTC

## Notes

- Default port: 5000
- Secret key should be changed in production
- Database file is created automatically on first run
