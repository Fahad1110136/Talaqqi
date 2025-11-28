from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
import sqlite3
import os
import uuid
from datetime import datetime


app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
socketio = SocketIO(app, cors_allowed_origins="*")

# Database initialization
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL,
                  user_type TEXT NOT NULL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Messages table
    c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  sender_id INTEGER NOT NULL,
                  receiver_id INTEGER NOT NULL,
                  message TEXT NOT NULL,
                  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (sender_id) REFERENCES users (id),
                  FOREIGN KEY (receiver_id) REFERENCES users (id))''')
    
    # Reviews table
    c.execute('''CREATE TABLE IF NOT EXISTS reviews
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  teacher_id INTEGER NOT NULL,
                  student_id INTEGER NOT NULL,
                  review TEXT NOT NULL,
                  rating INTEGER NOT NULL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (teacher_id) REFERENCES users (id),
                  FOREIGN KEY (student_id) REFERENCES users (id))''')
    
    # Video calls table
    c.execute('''CREATE TABLE IF NOT EXISTS video_calls
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  teacher_id INTEGER NOT NULL,
                  student_id INTEGER NOT NULL,
                  room_id TEXT UNIQUE NOT NULL,
                  status TEXT DEFAULT 'active',
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (teacher_id) REFERENCES users (id),
                  FOREIGN KEY (student_id) REFERENCES users (id))''')
    
    conn.commit()
    conn.close()

init_db()

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# Routes
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
        
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (username, password, user_type) VALUES (?, ?, ?)',
                        (username, password, user_type))
            conn.commit()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return "Username already exists"
        finally:
            conn.close()
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?',
                           (username, password)).fetchone()
        conn.close()
        
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
    
    conn = get_db_connection()
    
    if session['user_type'] == 'teacher':
        # Get all students for teacher
        students = conn.execute('''
            SELECT DISTINCT u.id, u.username 
            FROM users u 
            WHERE u.user_type = 'student'
        ''').fetchall()
        
        # Get reviews given by this teacher
        reviews = conn.execute('''
            SELECT r.*, u.username as student_name 
            FROM reviews r 
            JOIN users u ON r.student_id = u.id 
            WHERE r.teacher_id = ?
        ''', (session['user_id'],)).fetchall()
        
    else:  # student
        # Get all teachers for student
        teachers = conn.execute('''
            SELECT DISTINCT u.id, u.username 
            FROM users u 
            WHERE u.user_type = 'teacher'
        ''').fetchall()
        
        # Get reviews received by this student
        reviews = conn.execute('''
            SELECT r.*, u.username as teacher_name 
            FROM reviews r 
            JOIN users u ON r.teacher_id = u.id 
            WHERE r.student_id = ?
        ''', (session['user_id'],)).fetchall()
    
    conn.close()
    
    return render_template('dashboard.html', 
                         user_type=session['user_type'],
                         students=students if session['user_type'] == 'teacher' else None,
                         teachers=teachers if session['user_type'] == 'student' else None,
                         reviews=reviews)

@app.route('/mushaf')
def mushaf():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('mushaf.html')

@app.route('/chat/<int:user_id>')
def chat(user_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    other_user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    
    # Get message history
    messages = conn.execute('''
        SELECT m.*, u.username as sender_name 
        FROM messages m 
        JOIN users u ON m.sender_id = u.id 
        WHERE (m.sender_id = ? AND m.receiver_id = ?) 
           OR (m.sender_id = ? AND m.receiver_id = ?) 
        ORDER BY m.timestamp
    ''', (session['user_id'], user_id, user_id, session['user_id'])).fetchall()
    
    conn.close()
    
    return render_template('chat.html', other_user=other_user, messages=messages)

@app.route('/send_message', methods=['POST'])
def send_message():
    if 'user_id' not in session:
        return jsonify({'success': False})
    
    receiver_id = request.json['receiver_id']
    message = request.json['message']
    
    conn = get_db_connection()
    conn.execute('INSERT INTO messages (sender_id, receiver_id, message) VALUES (?, ?, ?)',
                (session['user_id'], receiver_id, message))
    conn.commit()
    conn.close()
    
    # Emit socket event for real-time messaging
    socketio.emit('new_message', {
        'sender_id': session['user_id'],
        'receiver_id': receiver_id,
        'message': message,
        'sender_name': session['username']
    })
    
    return jsonify({'success': True})

@app.route('/add_review', methods=['POST'])
def add_review():
    if 'user_id' not in session or session['user_type'] != 'teacher':
        return jsonify({'success': False})
    
    student_id = request.json['student_id']
    review = request.json['review']
    rating = request.json['rating']
    
    conn = get_db_connection()
    conn.execute('INSERT INTO reviews (teacher_id, student_id, review, rating) VALUES (?, ?, ?, ?)',
                (session['user_id'], student_id, review, rating))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

# Video Call Routes
@app.route('/create_video_room/<int:other_user_id>')
def create_video_room(other_user_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    # Check if there's already an active call between these users
    if session['user_type'] == 'teacher':
        existing_call = conn.execute('''
            SELECT room_id FROM video_calls 
            WHERE teacher_id = ? AND student_id = ? AND status = 'active'
        ''', (session['user_id'], other_user_id)).fetchone()
    else:
        existing_call = conn.execute('''
            SELECT room_id FROM video_calls 
            WHERE teacher_id = ? AND student_id = ? AND status = 'active'
        ''', (other_user_id, session['user_id'])).fetchone()
    
    if existing_call:
        # Use existing room
        room_id = existing_call['room_id']
        print(f"Using existing room: {room_id}")
    else:
        # Generate unique room ID
        room_id = str(uuid.uuid4())
        
        # Determine who is teacher and who is student
        if session['user_type'] == 'teacher':
            teacher_id = session['user_id']
            student_id = other_user_id
        else:
            teacher_id = other_user_id
            student_id = session['user_id']
        
        # Create video call room
        conn.execute('INSERT INTO video_calls (teacher_id, student_id, room_id) VALUES (?, ?, ?)',
                    (teacher_id, student_id, room_id))
        conn.commit()
        print(f"Created new room: {room_id}")
    
    conn.close()
    
    return redirect(url_for('video_call', room_id=room_id))

@app.route('/join_video_room/<int:other_user_id>')
def join_video_room(other_user_id):
    """Alternative route for students to join existing teacher calls"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    # Find active call with this user
    if session['user_type'] == 'teacher':
        existing_call = conn.execute('''
            SELECT room_id FROM video_calls 
            WHERE teacher_id = ? AND student_id = ? AND status = 'active'
        ''', (session['user_id'], other_user_id)).fetchone()
    else:
        existing_call = conn.execute('''
            SELECT room_id FROM video_calls 
            WHERE teacher_id = ? AND student_id = ? AND status = 'active'
        ''', (other_user_id, session['user_id'])).fetchone()
    
    if existing_call:
        room_id = existing_call['room_id']
        conn.close()
        return redirect(url_for('video_call', room_id=room_id))
    else:
        conn.close()
        return "No active call found. Please ask the teacher to start a call first."

@app.route('/video_call/<room_id>')
def video_call(room_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    call_data = conn.execute('''
        SELECT vc.*, t.username as teacher_name, s.username as student_name 
        FROM video_calls vc
        JOIN users t ON vc.teacher_id = t.id
        JOIN users s ON vc.student_id = s.id
        WHERE vc.room_id = ?
    ''', (room_id,)).fetchone()
    
    conn.close()
    
    if not call_data:
        return "Room not found"
    
    # Check if user is part of this call
    if session['user_id'] not in [call_data['teacher_id'], call_data['student_id']]:
        return "Access denied"
    
    other_user_name = call_data['teacher_name'] if session['user_type'] == 'student' else call_data['student_name']
    
    return render_template('video_call.html', 
                         room_id=room_id, 
                         other_user_name=other_user_name,
                         user_type=session['user_type'])

# Socket.IO Handlers
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
    
    # Notify other users in the room
    emit('user_joined', {
        'user_id': user_id,
        'user_type': user_type,
        'message': f'User {user_id} joined room {room_id}'
    }, room=room_id, include_self=False)

@socketio.on('webrtc_offer')
def handle_webrtc_offer(data):
    room_id = data['room_id']
    print(f'WebRTC offer in room {room_id}')
    emit('webrtc_offer', {
        'offer': data['offer'],
        'sender_id': data['sender_id']
    }, room=room_id, include_self=False)

@socketio.on('webrtc_answer')
def handle_webrtc_answer(data):
    room_id = data['room_id']
    print(f'WebRTC answer in room {room_id}')
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
    print(f'Ending call in room {room_id}')
    emit('call_ended', {'message': 'Call ended by other user'}, room=room_id)
    
    # Update call status in database
    conn = get_db_connection()
    conn.execute('UPDATE video_calls SET status = "ended" WHERE room_id = ?', (room_id,))
    conn.commit()
    conn.close()

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