console.log('=== SIMPLE VIDEO CALL STARTING ===');
console.log('Room:', roomId);
console.log('User:', userId);
console.log('User Type:', "{{ user_type }}");

let localStream;
let peerConnection;
let isCaller = "{{ user_type }}" === 'teacher';

// Socket.io
const socket = io();

// Initialize call
async function startCall() {
    try {
        console.log('1. Getting media devices...');
        localStream = await navigator.mediaDevices.getUserMedia({ 
            video: true, 
            audio: true 
        });
        
        document.getElementById('localVideo').srcObject = localStream;
        document.getElementById('localVideoStatus').textContent = 'Ready';
        updateStatus('Camera ready');
        
        console.log('2. Creating peer connection...');
        createPeerConnection();
        
        console.log('3. Joining room...');
        socket.emit('join_room', { room_id: roomId, user_id: userId });
        
        // Add tracks to connection
        localStream.getTracks().forEach(track => {
            peerConnection.addTrack(track, localStream);
        });
        
        if (isCaller) {
            console.log('4. Teacher: Creating offer...');
            await createOffer();
        } else {
            console.log('4. Student: Waiting for offer...');
            updateStatus('Waiting for teacher...');
        }
        
    } catch (error) {
        console.error('Start call error:', error);
        updateStatus('Error: ' + error.message);
        alert('Camera/microphone access required!');
    }
}

function createPeerConnection() {
    peerConnection = new RTCPeerConnection({
        iceServers: [{ urls: 'stun:stun.l.google.com:19302' }]
    });
    
    // Handle incoming stream
    peerConnection.ontrack = (event) => {
        console.log('Received remote stream!');
        const remoteVideo = document.getElementById('remoteVideo');
        remoteVideo.srcObject = event.streams[0];
        document.getElementById('remoteVideoStatus').textContent = 'Connected';
        updateStatus('Call connected! ✅');
    };
    
    // Handle ICE candidates
    peerConnection.onicecandidate = (event) => {
        if (event.candidate) {
            socket.emit('ice_candidate', {
                room_id: roomId,
                candidate: event.candidate
            });
        }
    };
}

async function createOffer() {
    try {
        updateStatus('Starting call...');
        const offer = await peerConnection.createOffer();
        await peerConnection.setLocalDescription(offer);
        
        socket.emit('webrtc_offer', {
            room_id: roomId,
            offer: offer
        });
        
        updateStatus('Calling...');
        
    } catch (error) {
        console.error('Offer error:', error);
        updateStatus('Call failed');
    }
}

// Socket events
socket.on('webrtc_offer', async (data) => {
    if (!isCaller) {
        console.log('Received offer, creating answer...');
        await peerConnection.setRemoteDescription(data.offer);
        
        const answer = await peerConnection.createAnswer();
        await peerConnection.setLocalDescription(answer);
        
        socket.emit('webrtc_answer', {
            room_id: roomId,
            answer: answer
        });
        
        updateStatus('Answering call...');
    }
});

socket.on('webrtc_answer', async (data) => {
    if (isCaller) {
        console.log('Received answer, finalizing...');
        await peerConnection.setRemoteDescription(data.answer);
        updateStatus('Call connected! ✅');
    }
});

socket.on('ice_candidate', async (data) => {
    if (data.candidate) {
        await peerConnection.addIceCandidate(data.candidate);
    }
});

socket.on('user_joined', (data) => {
    console.log('Other user joined:', data);
    updateStatus('Other user joined');
});

// Control functions
function toggleVideo() {
    if (localStream) {
        const videoTrack = localStream.getVideoTracks()[0];
        if (videoTrack) {
            videoTrack.enabled = !videoTrack.enabled;
            const btn = document.getElementById('toggleVideo');
            if (videoTrack.enabled) {
                btn.innerHTML = '<span>🎥</span><span>Video On</span>';
                btn.className = 'btn btn-control video-active';
            } else {
                btn.innerHTML = '<span>🚫</span><span>Video Off</span>';
                btn.className = 'btn btn-control video-inactive';
            }
        }
    }
}

function toggleAudio() {
    if (localStream) {
        const audioTrack = localStream.getAudioTracks()[0];
        if (audioTrack) {
            audioTrack.enabled = !audioTrack.enabled;
            const btn = document.getElementById('toggleAudio');
            if (audioTrack.enabled) {
                btn.innerHTML = '<span>🎤</span><span>Audio On</span>';
                btn.className = 'btn btn-control audio-active';
            } else {
                btn.innerHTML = '<span>🔇</span><span>Audio Off</span>';
                btn.className = 'btn btn-control audio-inactive';
            }
        }
    }
}

function endCall() {
    if (peerConnection) peerConnection.close();
    if (localStream) localStream.getTracks().forEach(track => track.stop());
    window.location.href = '/dashboard';
}

function updateStatus(message) {
    document.getElementById('connectionStatus').textContent = message;
    console.log('Status:', message);
}

// Start everything
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, starting call...');
    setTimeout(startCall, 1000);
    
    // Add event listeners
    document.getElementById('toggleVideo').addEventListener('click', toggleVideo);
    document.getElementById('toggleAudio').addEventListener('click', toggleAudio);
    document.getElementById('endCall').addEventListener('click', endCall);
});