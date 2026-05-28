// Enhanced debugging
console.log('=== VIDEO CALL DEBUG INFO ===');
console.log('Room ID:', roomId);
console.log('User ID:', userId);
console.log('User Type:', "{{ user_type }}");
console.log('=============================');

let localStream;
let remoteStream;
let peerConnection;
let isVideoEnabled = true;
let isAudioEnabled = true;
let isCaller = false;
let hasRemoteDescription = false;

// WebRTC configuration
const configuration = {
    iceServers: [
        { urls: 'stun:stun.l.google.com:19302' },
        { urls: 'stun:stun1.l.google.com:19302' }
    ],
    iceCandidatePoolSize: 10
};

// Socket.io connection for video calls
const socket = io();

// Initialize video call
async function initializeVideoCall() {
    try {
        console.log('Initializing video call...');
        updateConnectionStatus('Requesting camera and microphone access...');
        
        // Get local media stream
        localStream = await navigator.mediaDevices.getUserMedia({
            video: {
                width: { ideal: 1280 },
                height: { ideal: 720 },
                frameRate: { ideal: 30 }
            },
            audio: {
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true
            }
        });
        
        console.log('✅ Local stream obtained successfully');
        document.getElementById('localVideo').srcObject = localStream;
        document.getElementById('localVideoStatus').textContent = 'Camera On';
        updateConnectionStatus('Camera and microphone ready');
        
        // Create peer connection
        createPeerConnection();
        
        // Add local stream to peer connection
        localStream.getTracks().forEach(track => {
            console.log('➕ Adding track:', track.kind);
            peerConnection.addTrack(track, localStream);
        });
        
        // Join the room
        socket.emit('join_room', { 
            room_id: roomId,
            user_id: userId,
            user_type: "{{ user_type }}"
        });
        console.log('✅ Joined room:', roomId);
        
        // Wait a bit before starting call setup to ensure both users are connected
        setTimeout(() => {
            startCallSetup();
        }, 2000);
        
    } catch (error) {
        console.error('❌ Error accessing media devices:', error);
        updateConnectionStatus('Error: ' + error.message);
        
        let errorMessage = 'Cannot access camera/microphone. ';
        if (error.name === 'NotAllowedError') {
            errorMessage += 'Please allow camera and microphone permissions and refresh the page.';
        } else if (error.name === 'NotFoundError') {
            errorMessage += 'No camera/microphone found. Please check your device.';
        } else {
            errorMessage += 'Please check your device permissions and try again.';
        }
        
        alert(errorMessage);
    }
}

function startCallSetup() {
    // Simple logic: Teacher initiates the call, student waits
    if ("{{ user_type }}" === 'teacher') {
        console.log('🎯 Teacher: Initiating call as caller');
        isCaller = true;
        createOffer();
    } else {
        console.log('🎯 Student: Waiting for call from teacher');
        updateConnectionStatus('Waiting for teacher to start call...');
    }
}

async function createOffer() {
    try {
        console.log('📞 Creating offer...');
        updateConnectionStatus('Setting up call...');
        
        const offer = await peerConnection.createOffer({
            offerToReceiveAudio: true,
            offerToReceiveVideo: true
        });
        console.log('✅ Offer created');
        
        await peerConnection.setLocalDescription(offer);
        console.log('✅ Local description set');
        
        socket.emit('webrtc_offer', {
            room_id: roomId,
            offer: offer,
            sender_id: userId
        });
        
        updateConnectionStatus('Call initiated, waiting for answer...');
        console.log('📤 Offer sent to room');
        
    } catch (error) {
        console.error('❌ Error creating offer:', error);
        updateConnectionStatus('Error setting up call');
    }
}

function createPeerConnection() {
    try {
        peerConnection = new RTCPeerConnection(configuration);
        console.log('✅ Peer connection created');
        
        // Handle incoming remote stream
        peerConnection.ontrack = (event) => {
            console.log('📹 Received remote track:', event.track.kind);
            if (event.streams && event.streams[0]) {
                remoteStream = event.streams[0];
                document.getElementById('remoteVideo').srcObject = remoteStream;
                document.getElementById('remoteVideoStatus').textContent = 'Connected';
                updateConnectionStatus('✅ Call connected successfully!');
                console.log('🎉 Remote video stream connected and playing');
            }
        };
        
        // Handle ICE candidates
        peerConnection.onicecandidate = (event) => {
            if (event.candidate) {
                console.log('🧊 Sending ICE candidate');
                socket.emit('ice_candidate', {
                    room_id: roomId,
                    candidate: event.candidate,
                    sender_id: userId
                });
            } else {
                console.log('✅ All ICE candidates sent');
            }
        };
        
        // Handle connection state changes
        peerConnection.onconnectionstatechange = () => {
            const state = peerConnection.connectionState;
            console.log('🔗 Connection state:', state);
            updateConnectionStatus(`Connection: ${state}`);
            
            if (state === 'connected') {
                console.log('🎉 Peers connected successfully!');
            } else if (state === 'failed') {
                console.error('❌ Connection failed');
                updateConnectionStatus('Connection failed. Please try again.');
            }
        };
        
        // Handle ICE connection state
        peerConnection.oniceconnectionstatechange = () => {
            const iceState = peerConnection.iceConnectionState;
            console.log('🌐 ICE connection state:', iceState);
        };
        
    } catch (error) {
        console.error('❌ Error creating peer connection:', error);
        updateConnectionStatus('Error setting up call connection');
    }
}

// Socket event handlers
socket.on('connect', () => {
    console.log('✅ Socket connected to server');
    updateConnectionStatus('Connected to server');
});

socket.on('user_joined', (data) => {
    console.log('👤 User joined room:', data);
    updateConnectionStatus('Other user is in the call');
    
    // If teacher and student joins, teacher should initiate call
    if ("{{ user_type }}" === 'teacher' && !isCaller) {
        console.log('🎯 Teacher detected student joined, initiating call');
        setTimeout(() => {
            isCaller = true;
            createOffer();
        }, 1000);
    }
});

socket.on('webrtc_offer', async (data) => {
    console.log('📨 Received WebRTC offer from:', data.sender_id);
    
    if (data.sender_id !== userId) {
        try {
            console.log('🔄 Setting remote description from offer');
            await peerConnection.setRemoteDescription(data.offer);
            hasRemoteDescription = true;
            
            console.log('📝 Creating answer...');
            const answer = await peerConnection.createAnswer();
            await peerConnection.setLocalDescription(answer);
            console.log('✅ Answer created and set');
            
            socket.emit('webrtc_answer', {
                room_id: roomId,
                answer: answer,
                sender_id: userId
            });
            
            updateConnectionStatus('Call answered, connecting...');
            console.log('📤 Answer sent to room');
            
        } catch (error) {
            console.error('❌ Error handling offer:', error);
            updateConnectionStatus('Error accepting call');
        }
    }
});

socket.on('webrtc_answer', async (data) => {
    console.log('📨 Received WebRTC answer from:', data.sender_id);
    
    if (data.sender_id !== userId) {
        try {
            console.log('🔄 Setting remote description from answer');
            await peerConnection.setRemoteDescription(data.answer);
            hasRemoteDescription = true;
            console.log('✅ Remote description set from answer');
            updateConnectionStatus('Finalizing connection...');
        } catch (error) {
            console.error('❌ Error handling answer:', error);
            updateConnectionStatus('Error finalizing call connection');
        }
    }
});

socket.on('ice_candidate', async (data) => {
    console.log('🧊 Received ICE candidate from:', data.sender_id);
    
    if (data.sender_id !== userId && data.candidate) {
        try {
            await peerConnection.addIceCandidate(data.candidate);
            console.log('✅ Added remote ICE candidate');
        } catch (error) {
            console.error('❌ Error adding ICE candidate:', error);
        }
    }
});

socket.on('call_ended', () => {
    console.log('📞 Call ended by other user');
    updateConnectionStatus('Call ended by other user');
    setTimeout(() => {
        alert('The other user ended the call.');
        window.location.href = '/dashboard';
    }, 1000);
});

socket.on('video_toggled', (data) => {
    if (data.sender_id !== userId) {
        const status = data.video_enabled ? 'Camera On' : 'Camera Off';
        document.getElementById('remoteVideoStatus').textContent = status;
        console.log('📹 Remote user toggled video:', status);
    }
});

socket.on('audio_toggled', (data) => {
    if (data.sender_id !== userId) {
        console.log('🎤 Remote user toggled audio:', data.audio_enabled ? 'On' : 'Off');
    }
});

// Control functions
function toggleVideo() {
    if (!localStream) {
        alert('No camera access available');
        return;
    }
    
    const videoTrack = localStream.getVideoTracks()[0];
    if (videoTrack) {
        isVideoEnabled = !isVideoEnabled;
        videoTrack.enabled = isVideoEnabled;
        
        const toggleBtn = document.getElementById('toggleVideo');
        if (isVideoEnabled) {
            toggleBtn.classList.add('video-active');
            toggleBtn.classList.remove('video-inactive');
            toggleBtn.innerHTML = '<span>🎥</span><span>Video On</span>';
            document.getElementById('localVideoStatus').textContent = 'Camera On';
        } else {
            toggleBtn.classList.add('video-inactive');
            toggleBtn.classList.remove('video-active');
            toggleBtn.innerHTML = '<span>🚫</span><span>Video Off</span>';
            document.getElementById('localVideoStatus').textContent = 'Camera Off';
        }
        
        socket.emit('toggle_video', {
            room_id: roomId,
            video_enabled: isVideoEnabled,
            sender_id: userId
        });
        
        console.log('📹 Video toggled:', isVideoEnabled ? 'On' : 'Off');
    }
}

function toggleAudio() {
    if (!localStream) {
        alert('No microphone access available');
        return;
    }
    
    const audioTrack = localStream.getAudioTracks()[0];
    if (audioTrack) {
        isAudioEnabled = !isAudioEnabled;
        audioTrack.enabled = isAudioEnabled;
        
        const toggleBtn = document.getElementById('toggleAudio');
        if (isAudioEnabled) {
            toggleBtn.classList.add('audio-active');
            toggleBtn.classList.remove('audio-inactive');
            toggleBtn.innerHTML = '<span>🎤</span><span>Audio On</span>';
        } else {
            toggleBtn.classList.add('audio-inactive');
            toggleBtn.classList.remove('audio-active');
            toggleBtn.innerHTML = '<span>🔇</span><span>Audio Off</span>';
        }
        
        socket.emit('toggle_audio', {
            room_id: roomId,
            audio_enabled: isAudioEnabled,
            sender_id: userId
        });
        
        console.log('🎤 Audio toggled:', isAudioEnabled ? 'On' : 'Off');
    }
}

function endCall() {
    console.log('📞 Ending call...');
    updateConnectionStatus('Ending call...');
    
    // Send end call signal
    socket.emit('end_call', { room_id: roomId });
    
    // Close peer connection
    if (peerConnection) {
        peerConnection.close();
        peerConnection = null;
        console.log('✅ Peer connection closed');
    }
    
    // Stop local stream
    if (localStream) {
        localStream.getTracks().forEach(track => {
            track.stop();
            console.log('⏹️ Stopped track:', track.kind);
        });
        localStream = null;
    }
    
    // Redirect to dashboard
    setTimeout(() => {
        window.location.href = '/dashboard';
    }, 500);
}

function updateConnectionStatus(status) {
    console.log('📢 Status:', status);
    const statusElement = document.getElementById('connectionStatus');
    if (statusElement) {
        statusElement.textContent = status;
        
        // Add color coding for status
        if (status.includes('✅') || status.includes('connected') || status.includes('success')) {
            statusElement.style.color = '#27ae60';
            statusElement.style.fontWeight = 'bold';
        } else if (status.includes('❌') || status.includes('Error') || status.includes('failed')) {
            statusElement.style.color = '#e74c3c';
            statusElement.style.fontWeight = 'bold';
        } else if (status.includes('waiting') || status.includes('Waiting')) {
            statusElement.style.color = '#f39c12';
        } else {
            statusElement.style.color = '#3498db';
        }
    }
}

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Video call page loaded completely');
    
    // Check if browser supports WebRTC
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        const errorMsg = '❌ Your browser does not support video calling. Please use Chrome, Firefox, or Edge.';
        alert(errorMsg);
        updateConnectionStatus(errorMsg);
        return;
    }
    
    // Check if required variables are available
    if (!roomId || !userId) {
        const errorMsg = '❌ Missing room or user information. Please go back and try again.';
        alert(errorMsg);
        updateConnectionStatus(errorMsg);
        return;
    }
    
    console.log('🎬 Starting video call initialization...');
    
    // Initialize call when page loads
    setTimeout(() => {
        initializeVideoCall();
    }, 500);
    
    // Add event listeners to control buttons
    document.getElementById('toggleVideo').addEventListener('click', toggleVideo);
    document.getElementById('toggleAudio').addEventListener('click', toggleAudio);
    document.getElementById('endCall').addEventListener('click', endCall);
    
    // Handle page refresh/close
    window.addEventListener('beforeunload', endCall);
});

// Manual call restart function (for debugging)
function restartCall() {
    console.log('🔄 Manually restarting call...');
    if (peerConnection) {
        peerConnection.close();
        peerConnection = null;
    }
    initializeVideoCall();
}

// Add restart button for debugging (remove in production)
document.addEventListener('DOMContentLoaded', function() {
    const debugDiv = document.createElement('div');
    debugDiv.style.position = 'fixed';
    debugDiv.style.top = '10px';
    debugDiv.style.right = '10px';
    debugDiv.style.zIndex = '1000';
    debugDiv.innerHTML = `
        <button onclick="restartCall()" style="background: #e74c3c; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer;">
            🔄 Restart Call
        </button>
    `;
    document.body.appendChild(debugDiv);
});