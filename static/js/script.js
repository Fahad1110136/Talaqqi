// Socket.io connection
const socket = io();

// Chat functionality
function sendMessage(receiverId) {
    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value.trim();
    
    if (message) {
        fetch('/send_message', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                receiver_id: receiverId,
                message: message
            })
        }).then(response => response.json())
          .then(data => {
              if (data.success) {
                  messageInput.value = '';
                  scrollToBottom();
              }
          });
    }
}

// Socket event for receiving messages
socket.on('new_message', function(data) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${data.sender_id === parseInt('{{ session.user_id }}') ? 'message-sent' : 'message-received'}`;
    
    messageDiv.innerHTML = `
        <div class="message-header">
            <strong>${data.sender_name}</strong>
            <small>${new Date().toLocaleString()}</small>
        </div>
        <p>${data.message}</p>
    `;
    
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
});

function scrollToBottom() {
    const chatMessages = document.getElementById('chatMessages');
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Review modal functionality
function openReviewModal(studentId) {
    document.getElementById('reviewStudentId').value = studentId;
    document.getElementById('reviewModal').style.display = 'block';
}

function closeReviewModal() {
    document.getElementById('reviewModal').style.display = 'none';
}

document.getElementById('reviewForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const studentId = document.getElementById('reviewStudentId').value;
    const review = document.getElementById('reviewText').value;
    const rating = document.getElementById('reviewRating').value;
    
    fetch('/add_review', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            student_id: studentId,
            review: review,
            rating: rating
        })
    }).then(response => response.json())
      .then(data => {
          if (data.success) {
              closeReviewModal();
              location.reload();
          }
      });
});

// Close modal when clicking X
document.querySelector('.close').addEventListener('click', closeReviewModal);

// Close modal when clicking outside
window.addEventListener('click', function(e) {
    const modal = document.getElementById('reviewModal');
    if (e.target === modal) {
        closeReviewModal();
    }
});

// Video call simulation
document.addEventListener('DOMContentLoaded', function() {
    const startCallBtn = document.getElementById('startCall');
    const endCallBtn = document.getElementById('endCall');
    const localVideo = document.getElementById('localVideo');
    const remoteVideo = document.getElementById('remoteVideo');
    
    if (startCallBtn) {
        startCallBtn.addEventListener('click', function() {
            // Simulate starting a call
            startCallBtn.disabled = true;
            endCallBtn.disabled = false;
            
            // In a real implementation, you would set up WebRTC here
            // This is just a simulation
            localVideo.srcObject = getLocalStream();
            
            // Simulate remote video after 2 seconds
            setTimeout(() => {
                remoteVideo.srcObject = getRemoteStream();
            }, 2000);
        });
    }
    
    if (endCallBtn) {
        endCallBtn.addEventListener('click', function() {
            // Simulate ending a call
            startCallBtn.disabled = false;
            endCallBtn.disabled = true;
            
            if (localVideo.srcObject) {
                localVideo.srcObject.getTracks().forEach(track => track.stop());
                localVideo.srcObject = null;
            }
            if (remoteVideo.srcObject) {
                remoteVideo.srcObject.getTracks().forEach(track => track.stop());
                remoteVideo.srcObject = null;
            }
        });
    }
});

// Mock functions for video streams (in real app, use getUserMedia and WebRTC)
function getLocalStream() {
    // This would normally use navigator.mediaDevices.getUserMedia
    // For simulation, we'll create a blank video
    return null;
}

function getRemoteStream() {
    // This would be the remote stream from WebRTC
    // For simulation, we'll create a blank video
    return null;
}

// Handle Enter key in chat
document.addEventListener('DOMContentLoaded', function() {
    const messageInput = document.getElementById('messageInput');
    if (messageInput) {
        messageInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage(otherUserId);
            }
        });
    }
});