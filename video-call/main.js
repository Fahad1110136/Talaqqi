import './style.css';
import firebase from 'firebase/compat/app';
import 'firebase/compat/firestore';

// --- Firebase bootstrap ------------------------------------------------------
const firebaseConfig = {
  apiKey: 'AIzaSyA1kemjxzzt5DkyFII8vJP8be7g6_meylc',
  authDomain: 'talaqi-22248.firebaseapp.com',
  databaseURL: 'https://talaqi-22248-default-rtdb.asia-southeast1.firebasedatabase.app',
  projectId: 'talaqi-22248',
  storageBucket: 'talaqi-22248.firebasestorage.app',
  messagingSenderId: '649776797586',
  appId: '1:649776797586:web:461f483374194dec4b134b',
  measurementId: 'G-9S0R8VP60J',
};

if (!firebase.apps.length) {
  firebase.initializeApp(firebaseConfig);
}
const firestore = firebase.firestore();

// --- Core abstractions -------------------------------------------------------

class MediaManager {
  constructor(localVideoEl, remoteVideoEl) {
    this.localVideoEl = localVideoEl;
    this.remoteVideoEl = remoteVideoEl;
    this.localStream = null;
    this.remoteStream = null;
  }

  async start() {
    if (!navigator?.mediaDevices?.getUserMedia) {
      throw new Error('Camera requires HTTPS or localhost.');
    }
    this.localStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
    this.remoteStream = new MediaStream();

    this.localVideoEl.srcObject = this.localStream;
    this.remoteVideoEl.srcObject = this.remoteStream;
    return { localStream: this.localStream, remoteStream: this.remoteStream };
  }

  stop() {
    this.localStream?.getTracks().forEach((track) => track.stop());
    this.remoteStream?.getTracks().forEach((track) => track.stop());
    this.localVideoEl.srcObject = null;
    this.remoteVideoEl.srcObject = null;
    this.localStream = null;
    this.remoteStream = null;
  }
}

class PeerConnectionManager {
  constructor(iceServers) {
    this.iceServers = iceServers;
    this.pc = null;
  }

  create(localStream, remoteStream) {
    this.dispose();
    this.pc = new RTCPeerConnection(this.iceServers);

    localStream?.getTracks().forEach((track) => this.pc.addTrack(track, localStream));

    this.pc.ontrack = (event) => {
      event.streams[0].getTracks().forEach((track) => remoteStream?.addTrack(track));
    };

    return this.pc;
  }

  dispose() {
    if (!this.pc) return;
    this.pc.onicecandidate = null;
    this.pc.ontrack = null;
    try {
      this.pc.close();
    } catch (err) {
      console.warn('PeerConnection close failed:', err);
    }
    this.pc = null;
  }
}

class FirestoreSignalingService {
  constructor(db) {
    this.db = db;
  }

  createCallDocument() {
    return this.db.collection('calls').doc();
  }

  getCallDocument(id) {
    return this.db.collection('calls').doc(id);
  }

  async deleteAllCandidates(callDoc) {
    const clear = async (ref) => {
      const snap = await ref.get();
      await Promise.all(snap.docs.map((doc) => doc.ref.delete()));
    };
    await clear(callDoc.collection('offerCandidates'));
    await clear(callDoc.collection('answerCandidates'));
    await callDoc.delete();
  }
}

class CallController {
  constructor(options) {
    this.media = options.mediaManager;
    this.peer = options.peerManager;
    this.signaling = options.signalingService;

    this.ui = options.ui;
    this.currentCallDoc = null;
    this.unsubscribeCall = null;
    this.unsubscribeOfferCandidates = null;
    this.unsubscribeAnswerCandidates = null;
  }

  init() {
    this.ui.webcamButton.addEventListener('click', () => this.handleStartWebcam());
    this.ui.callButton.addEventListener('click', () => this.handleCreateCall());
    this.ui.answerButton.addEventListener('click', () => this.handleAnswerCall());
    this.ui.hangupButton.addEventListener('click', () => this.hangUp());
    window.addEventListener('beforeunload', () => this.hangUp());
  }

  async handleStartWebcam() {
    try {
      const { localStream, remoteStream } = await this.media.start();
      this.peer.create(localStream, remoteStream);

      this.toggleControls({ webcam: true, call: false, answer: false, hangup: true });
      this.ui.callButton.disabled = false;
      this.ui.answerButton.disabled = false;
    } catch (err) {
      alert(`Cannot access camera/mic: ${err.message || err}`);
    }
  }

  async handleCreateCall() {
    if (!this.peer.pc) {
      alert('Start the webcam first.');
      return;
    }

    try {
      const callDoc = this.signaling.createCallDocument();
      this.currentCallDoc = callDoc;

      const offerCandidatesRef = callDoc.collection('offerCandidates');
      const answerCandidatesRef = callDoc.collection('answerCandidates');

      this.peer.pc.onicecandidate = (event) => {
        if (event.candidate) {
          offerCandidatesRef.add(event.candidate.toJSON()).catch((err) => console.error('offer ICE add failed', err));
        }
      };

      const offerDescription = await this.peer.pc.createOffer();
      await this.peer.pc.setLocalDescription(offerDescription);
      await callDoc.set({ offer: { type: offerDescription.type, sdp: offerDescription.sdp } });

      this.ui.callInput.value = callDoc.id;
      this.subscribeToAnswer(callDoc);
      this.subscribeToAnswerCandidates(answerCandidatesRef);
      this.toggleControls({ call: true, answer: true, hangup: false });
    } catch (err) {
      alert(`Create call failed: ${err.message || err}`);
    }
  }

  async handleAnswerCall() {
    if (!this.peer.pc) {
      alert('Start the webcam first.');
      return;
    }
    const callId = this.ui.callInput.value.trim();
    if (!callId) {
      alert('Enter a call ID.');
      return;
    }

    try {
      const callDoc = this.signaling.getCallDocument(callId);
      const snapshot = await callDoc.get();
      if (!snapshot.exists) {
        alert(`Call not found (${callId})`);
        return;
      }

      const data = snapshot.data();
      if (!data?.offer) {
        alert('Call has no offer yet.');
        return;
      }

      this.currentCallDoc = callDoc;
      const answerCandidatesRef = callDoc.collection('answerCandidates');
      const offerCandidatesRef = callDoc.collection('offerCandidates');

      this.peer.pc.onicecandidate = (event) => {
        if (event.candidate) {
          answerCandidatesRef.add(event.candidate.toJSON()).catch((err) => console.error('answer ICE add failed', err));
        }
      };

      await this.peer.pc.setRemoteDescription(new RTCSessionDescription(data.offer));
      const answerDescription = await this.peer.pc.createAnswer();
      await this.peer.pc.setLocalDescription(answerDescription);

      await callDoc.update({
        answer: { type: answerDescription.type, sdp: answerDescription.sdp },
      });

      this.subscribeToOfferCandidates(offerCandidatesRef);
      this.toggleControls({ call: true, answer: true, hangup: false });
    } catch (err) {
      alert(`Answer failed: ${err.message || err}`);
    }
  }

  subscribeToAnswer(callDoc) {
    this.unsubscribeCall?.();
    this.unsubscribeCall = callDoc.onSnapshot((snapshot) => {
      const data = snapshot.data();
      if (!data?.answer || this.peer.pc?.currentRemoteDescription) return;
      this.peer.pc
        .setRemoteDescription(new RTCSessionDescription(data.answer))
        .catch((err) => console.error('Failed to set remote description', err));
    });
  }

  subscribeToOfferCandidates(ref) {
    this.unsubscribeOfferCandidates?.();
    this.unsubscribeOfferCandidates = ref.onSnapshot((snapshot) => {
      snapshot.docChanges().forEach((change) => {
        if (change.type !== 'added') return;
        const candidate = new RTCIceCandidate(change.doc.data());
        this.peer.pc
          ?.addIceCandidate(candidate)
          .catch((err) => console.error('addIceCandidate failed', err));
      });
    });
  }

  subscribeToAnswerCandidates(ref) {
    this.unsubscribeAnswerCandidates?.();
    this.unsubscribeAnswerCandidates = ref.onSnapshot((snapshot) => {
      snapshot.docChanges().forEach((change) => {
        if (change.type !== 'added') return;
        const candidate = new RTCIceCandidate(change.doc.data());
        this.peer.pc
          ?.addIceCandidate(candidate)
          .catch((err) => console.error('addIceCandidate failed', err));
      });
    });
  }

  async hangUp() {
    this.unsubscribeCall?.();
    this.unsubscribeOfferCandidates?.();
    this.unsubscribeAnswerCandidates?.();
    this.unsubscribeCall = this.unsubscribeOfferCandidates = this.unsubscribeAnswerCandidates = null;

    this.peer.dispose();
    this.media.stop();

    if (this.currentCallDoc) {
      try {
        await this.signaling.deleteAllCandidates(this.currentCallDoc);
      } catch (err) {
        console.warn('Cleanup failed:', err);
      }
      this.currentCallDoc = null;
    }

    this.ui.callInput.value = '';
    this.toggleControls({ webcam: false, call: true, answer: true, hangup: true });
  }

  toggleControls({ webcam = false, call = true, answer = true, hangup = true }) {
    this.ui.webcamButton.disabled = webcam;
    this.ui.callButton.disabled = call;
    this.ui.answerButton.disabled = answer;
    this.ui.hangupButton.disabled = hangup;
  }
}

// --- Bootstrap the controller ------------------------------------------------
const ui = {
  webcamButton: document.getElementById('webcamButton'),
  webcamVideo: document.getElementById('webcamVideo'),
  callButton: document.getElementById('callButton'),
  callInput: document.getElementById('callInput'),
  answerButton: document.getElementById('answerButton'),
  remoteVideo: document.getElementById('remoteVideo'),
  hangupButton: document.getElementById('hangupButton'),
};

const mediaManager = new MediaManager(ui.webcamVideo, ui.remoteVideo);
const peerManager = new PeerConnectionManager({
  iceServers: [
    { urls: ['stun:stun1.l.google.com:19302', 'stun:stun2.l.google.com:19302'] },
  ],
  iceCandidatePoolSize: 10,
});
const signalingService = new FirestoreSignalingService(firestore);

const callController = new CallController({
  mediaManager,
  peerManager,
  signalingService,
  ui,
});
callController.init();
