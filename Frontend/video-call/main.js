import './style.css';



// With compat imports:
import firebase from 'firebase/compat/app';
import 'firebase/compat/firestore';

const firebaseConfig = {
  apiKey: "AIzaSyA1kemjxzzt5DkyFII8vJP8be7g6_meylc",
  authDomain: "talaqi-22248.firebaseapp.com",
  databaseURL: "https://talaqi-22248-default-rtdb.asia-southeast1.firebasedatabase.app",
  projectId: "talaqi-22248",
  storageBucket: "talaqi-22248.firebasestorage.app",
  messagingSenderId: "649776797586",
  appId: "1:649776797586:web:461f483374194dec4b134b",
  measurementId: "G-9S0R8VP60J"
};
if (!firebase.apps.length) {
  firebase.initializeApp(firebaseConfig);
}
// expose for debugging
window.firebase = firebase;
const firestore = firebase.firestore();
window.firestore = firestore;
console.log('Firestore initialized for project:', firebaseConfig.projectId);

const servers = {
  iceServers: [
    { urls: ['stun:stun1.l.google.com:19302', 'stun:stun2.l.google.com:19302'] },
  ],
  iceCandidatePoolSize: 10,
};

let pc = null;
let localStream = null;
let remoteStream = null;
let callSnapshotUnsub = null;
let offerCandidatesUnsub = null;
let answerCandidatesUnsub = null;
let currentCallDoc = null;

function detachSnapshotListeners() {
  callSnapshotUnsub?.();
  callSnapshotUnsub = null;
  offerCandidatesUnsub?.();
  offerCandidatesUnsub = null;
  answerCandidatesUnsub?.();
  answerCandidatesUnsub = null;
}

async function deleteCollection(collectionRef) {
  const snapshot = await collectionRef.get();
  await Promise.all(snapshot.docs.map((doc) => doc.ref.delete()));
}

async function cleanupCallDocs() {
  if (!currentCallDoc) return;
  try {
    await deleteCollection(currentCallDoc.collection('offerCandidates'));
    await deleteCollection(currentCallDoc.collection('answerCandidates'));
    await currentCallDoc.delete();
  } catch (err) {
    console.warn('Failed to clean call docs', err);
  } finally {
    currentCallDoc = null;
  }
}

function setupPeerConnection() {
  if (pc) {
    pc.onicecandidate = null;
    pc.ontrack = null;
    try { pc.close(); } catch (err) { console.warn(err); }
  }
  pc = new RTCPeerConnection(servers);
  pc.ontrack = (event) => {
    event.streams[0].getTracks().forEach((track) => {
      remoteStream?.addTrack(track);
    });
  };
  localStream?.getTracks().forEach((track) => pc.addTrack(track, localStream));
}

async function hangUp() {
  detachSnapshotListeners();

  if (pc) {
    pc.onicecandidate = null;
    try { pc.close(); } catch (err) { console.warn(err); }
    pc = null;
  }

  await cleanupCallDocs();

  localStream?.getTracks().forEach((track) => track.stop());
  remoteStream?.getTracks().forEach((track) => track.stop());
  localStream = null;
  remoteStream = null;
  webcamVideo.srcObject = null;
  remoteVideo.srcObject = null;

  callInput.value = '';
  hangupButton.disabled = true;
  callButton.disabled = true;
  answerButton.disabled = true;
  webcamButton.disabled = false;
}

// HTML elements
const webcamButton = document.getElementById('webcamButton');
const webcamVideo = document.getElementById('webcamVideo');
const callButton = document.getElementById('callButton');
const callInput = document.getElementById('callInput');
const answerButton = document.getElementById('answerButton');
const remoteVideo = document.getElementById('remoteVideo');
const hangupButton = document.getElementById('hangupButton');

// 1. Setup media sources

webcamButton.onclick = async () => {
  try {
    if (!('mediaDevices' in navigator) || !navigator.mediaDevices.getUserMedia) {
      alert('This browser does not allow camera access here. Use HTTPS or localhost.');
      return;
    }

    localStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
    remoteStream = new MediaStream();

    webcamVideo.srcObject = localStream;
    remoteVideo.srcObject = remoteStream;

    setupPeerConnection();

    callButton.disabled = false;
    answerButton.disabled = false;
    webcamButton.disabled = true;
  } catch (err) {
    console.error('Failed to start webcam:', err);
    alert('Cannot access camera/mic: ' + (err.message || err));
  }
};

// 2. Create an offer
callButton.onclick = async () => {
  if (!localStream || !pc) {
    alert('Start the webcam first.');
    return;
  }
  try {
    const callDoc = firestore.collection('calls').doc();
    currentCallDoc = callDoc;
    const offerCandidates = callDoc.collection('offerCandidates');
    const answerCandidates = callDoc.collection('answerCandidates');

    callInput.value = callDoc.id;
    pc.onicecandidate = (event) => {
      if (event.candidate) {
        offerCandidates.add(event.candidate.toJSON()).catch((err) => console.error('offer ICE add failed', err));
      }
    };

    const offerDescription = await pc.createOffer();
    await pc.setLocalDescription(offerDescription);
    await callDoc.set({ offer: { sdp: offerDescription.sdp, type: offerDescription.type } });

    callSnapshotUnsub = callDoc.onSnapshot((snapshot) => {
      const data = snapshot.data();
      if (data?.answer && !pc.currentRemoteDescription) {
        pc.setRemoteDescription(new RTCSessionDescription(data.answer)).catch((err) => console.error('setRemoteDescription failed', err));
      }
    });

    answerCandidatesUnsub = answerCandidates.onSnapshot((snapshot) => {
      snapshot.docChanges().forEach((change) => {
        if (change.type === 'added') {
          pc.addIceCandidate(new RTCIceCandidate(change.doc.data())).catch((err) => console.error('addIceCandidate failed', err));
        }
      });
    });

    hangupButton.disabled = false;
    callButton.disabled = true;
    answerButton.disabled = true;
  } catch (err) {
    console.error('Failed to create call:', err);
    alert('Create call failed: ' + (err.message || err));
  }
};

// 3. Answer the call with the unique ID
answerButton.onclick = async () => {
  if (!localStream || !pc) {
    alert('Start the webcam first.');
    return;
  }
  const callId = callInput.value.trim();
  if (!callId) {
    alert('Enter a call ID.');
    return;
  }
  try {
    const callDoc = firestore.collection('calls').doc(callId);
    const callSnap = await callDoc.get();
    if (!callSnap.exists) {
      alert(`Call not found (${callId})`);
      return;
    }
    const callData = callSnap.data();
    if (!callData?.offer) {
      alert('Call has no offer yet.');
      return;
    }

    currentCallDoc = callDoc;
    const answerCandidates = callDoc.collection('answerCandidates');
    const offerCandidates = callDoc.collection('offerCandidates');

    pc.onicecandidate = (event) => {
      if (event.candidate) {
        answerCandidates.add(event.candidate.toJSON()).catch((err) => console.error('answer ICE add failed', err));
      }
    };

    await pc.setRemoteDescription(new RTCSessionDescription(callData.offer));
    const answerDescription = await pc.createAnswer();
    await pc.setLocalDescription(answerDescription);
    await callDoc.update({ answer: { type: answerDescription.type, sdp: answerDescription.sdp } });

    offerCandidatesUnsub = offerCandidates.onSnapshot((snapshot) => {
      snapshot.docChanges().forEach((change) => {
        if (change.type === 'added') {
          pc.addIceCandidate(new RTCIceCandidate(change.doc.data())).catch((err) => console.error('addIceCandidate failed', err));
        }
      });
    });

    hangupButton.disabled = false;
    callButton.disabled = true;
    answerButton.disabled = true;
  } catch (err) {
    console.error('Error answering call:', err);
    alert('Answer failed: ' + (err.message || err));
  }
};

hangupButton.onclick = hangUp;
window.addEventListener('beforeunload', hangUp);
