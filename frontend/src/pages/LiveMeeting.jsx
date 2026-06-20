import React, { useState, useEffect, useRef } from 'react';
import { 
  Mic, 
  MicOff,
  Square, 
  Users, 
  FileText,
  Activity,
  AlertCircle,
  CheckCircle,
  Radio
} from 'lucide-react';
import { meetingAPI } from '../services/api';
import './LiveMeeting.css';

const LiveMeeting = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [meetingId, setMeetingId] = useState(null);
  const [title, setTitle] = useState('');
  const [participants, setParticipants] = useState('');
  const [transcript, setTranscript] = useState([]);
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [textInput, setTextInput] = useState('');
  const [isCapturingAudio, setIsCapturingAudio] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  
  // Audio capture refs
  const mediaRecorderRef = useRef(null);
  const websocketRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const processIntervalRef = useRef(null);

  useEffect(() => {
    checkActiveMeeting();
    
    // Cleanup on unmount
    return () => {
      stopAudioCapture();
    };
  }, []);

  const checkActiveMeeting = async () => {
    try {
      const statusData = await meetingAPI.getStatus();
      setStatus(statusData);
      setIsRecording(true);
      setMeetingId(statusData.meeting_id);
      setTitle(statusData.title || '');
    } catch (error) {
      // No active meeting
      setIsRecording(false);
    }
  };

  const handleStart = async () => {
    if (!title.trim()) {
      setError('Please enter a meeting title');
      return;
    }

    if (!participants.trim()) {
      setError('Please enter at least one participant');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await meetingAPI.startMeeting(title, participants);
      setMeetingId(response.meeting_id);
      setIsRecording(true);
      setStatus(response);
      setTranscript([]);
      
      // Auto-start audio capture
      setTimeout(() => startAudioCapture(), 500);
    } catch (error) {
      setError(error.response?.data?.detail || 'Failed to start meeting');
    } finally {
      setLoading(false);
    }
  };

  const handleStop = async () => {
    if (!meetingId) return;

    // Stop audio capture first
    stopAudioCapture();

    setLoading(true);
    setError('');

    try {
      const notes = await meetingAPI.stopMeeting();
      setIsRecording(false);
      setStatus(null);
      
      // Show success and navigate to notes
      alert('Meeting stopped successfully! Viewing notes...');
      window.location.href = `/meeting/${notes.meeting_id}`;
    } catch (error) {
      setError(error.response?.data?.detail || 'Failed to stop meeting');
    } finally {
      setLoading(false);
    }
  };

  const handleAddText = async () => {
    if (!textInput.trim()) return;
    if (!meetingId) {
      setError('Please start a meeting first');
      return;
    }

    try {
      await meetingAPI.addInput(textInput);
      setTranscript(prev => [...prev, { 
        text: textInput, 
        time: new Date().toLocaleTimeString() 
      }]);
      setTextInput('');
      setError('');
    } catch (error) {
      setError(error.response?.data?.detail || 'Failed to add text');
    }
  };

  // ========== LIVE AUDIO CAPTURE ==========
  
  const startAudioCapture = async () => {
    try {
      setLoading(true);
      setError('');

      // Step 1: Request screen/tab sharing with audio (captures system audio)
      let systemStream = null;
      try {
        console.log('🖥️ Requesting screen/tab audio capture...');
        systemStream = await navigator.mediaDevices.getDisplayMedia({
          video: false,
          audio: {
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true,
            sampleRate: 16000
          }
        });
        console.log('✅ System audio access granted');
      } catch (err) {
        console.log('⚠️ System audio denied, will use microphone only');
      }

      // Step 2: Request microphone (captures your voice)
      let micStream = null;
      try {
        console.log('🎤 Requesting microphone access...');
        micStream = await navigator.mediaDevices.getUserMedia({ 
          audio: {
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true,
            sampleRate: 16000
          } 
        });
        console.log('✅ Microphone access granted');
      } catch (err) {
        console.error('❌ Microphone access denied');
        if (!systemStream) {
          throw new Error('Need at least microphone or system audio access');
        }
      }

      // Step 3: Mix both audio streams
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      audioContextRef.current = audioContext;
      
      const destination = audioContext.createMediaStreamDestination();
      
      // Add system audio if available
      if (systemStream && systemStream.getAudioTracks().length > 0) {
        try {
          const systemSource = audioContext.createMediaStreamSource(systemStream);
          const systemGain = audioContext.createGain();
          systemGain.gain.value = 1.0; // 100% system audio
          systemSource.connect(systemGain);
          systemGain.connect(destination);
          console.log('🔊 System audio connected');
        } catch (err) {
          console.warn('⚠️ System audio connection failed:', err);
        }
      }
      
      // Add microphone if available
      if (micStream && micStream.getAudioTracks().length > 0) {
        try {
          const micSource = audioContext.createMediaStreamSource(micStream);
          const micGain = audioContext.createGain();
          micGain.gain.value = 1.5; // 150% mic boost
          micSource.connect(micGain);
          micGain.connect(destination);
          console.log('🎤 Microphone connected');
        } catch (err) {
          console.warn('⚠️ Microphone connection failed:', err);
        }
      }

      // Check if we have any audio
      if (!systemStream && !micStream) {
        throw new Error('No audio sources available. Please grant at least microphone permission.');
      }

      // Setup analyzer for visualization
      analyserRef.current = audioContext.createAnalyser();
      
      // Connect analyzer to destination
      const analyzerSource = audioContext.createMediaStreamSource(destination.stream);
      analyzerSource.connect(analyserRef.current);
      
      monitorAudioLevel();

      // Get mixed stream
      const mixedStream = destination.stream;

      // Setup MediaRecorder with WAV format (no conversion needed!)
      let mediaRecorder;
      
      // Try to use WAV if supported, otherwise WebM
      const mimeTypes = [
        'audio/wav',
        'audio/webm;codecs=opus',
        'audio/webm',
        'audio/ogg;codecs=opus'
      ];
      
      let selectedMimeType = '';
      for (const mimeType of mimeTypes) {
        if (MediaRecorder.isTypeSupported(mimeType)) {
          selectedMimeType = mimeType;
          console.log(`✅ Using audio format: ${mimeType}`);
          break;
        }
      }
      
      mediaRecorderRef.current = new MediaRecorder(mixedStream, { 
        mimeType: selectedMimeType,
        audioBitsPerSecond: 128000
      });
      
      // Connect to WebSocket
      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${wsProtocol}//localhost:8000/ws/audio`;
      websocketRef.current = new WebSocket(wsUrl);
      
      websocketRef.current.onopen = () => {
        console.log('✅ WebSocket connected');
        setIsCapturingAudio(true);
        
        // Start recording
        mediaRecorderRef.current.start(1000); // Send chunks every 1 second
        
        // Process audio every 10 seconds
        processIntervalRef.current = setInterval(() => {
          if (websocketRef.current?.readyState === WebSocket.OPEN) {
            websocketRef.current.send(JSON.stringify({ type: 'process' }));
          }
        }, 10000);
      };
      
      websocketRef.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type === 'transcript') {
          // Add transcript to display
          setTranscript(prev => [...prev, { 
            text: data.text, 
            time: new Date().toLocaleTimeString() 
          }]);
          console.log('📝 Transcript:', data.text);
        } else if (data.type === 'error') {
          console.error('❌ Server error:', data.message);
          setError(data.message);
        } else if (data.type === 'ack') {
          console.log('✓ Audio buffer:', data.buffer_size, 'bytes');
        }
      };
      
      websocketRef.current.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
        setError('Failed to connect to audio server. Make sure backend is running.');
      };
      
      websocketRef.current.onclose = () => {
        console.log('🔌 WebSocket closed');
        setIsCapturingAudio(false);
      };
      
      // Send audio data to WebSocket
      mediaRecorderRef.current.ondataavailable = async (event) => {
        if (event.data.size > 0 && websocketRef.current?.readyState === WebSocket.OPEN) {
          try {
            const arrayBuffer = await event.data.arrayBuffer();
            websocketRef.current.send(arrayBuffer);
          } catch (err) {
            console.error('Failed to send audio:', err);
          }
        }
      };
      
      // Store streams for cleanup
      mediaRecorderRef.current.systemStream = systemStream;
      mediaRecorderRef.current.micStream = micStream;
      
      console.log('🎤 Dual audio capture started (System + Microphone)');
      
      // Show success message
      const sources = [];
      if (systemStream) sources.push('System Audio');
      if (micStream) sources.push('Microphone');
      setError(''); // Clear any previous errors
      
    } catch (error) {
      console.error('Audio capture error:', error);
      if (error.name === 'NotAllowedError') {
        setError('Permission denied. Please allow microphone/screen audio access and try again.');
      } else if (error.name === 'NotFoundError') {
        setError('No microphone found. Please connect a microphone and try again.');
      } else {
        setError('Failed to start audio capture: ' + error.message);
      }
    } finally {
      setLoading(false);
    }
  };

  const stopAudioCapture = () => {
    console.log('🛑 Stopping audio capture...');
    
    // Clear process interval
    if (processIntervalRef.current) {
      clearInterval(processIntervalRef.current);
      processIntervalRef.current = null;
    }
    
    // Stop media recorder and all tracks
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
      
      // Stop all tracks from both streams
      if (mediaRecorderRef.current.systemStream) {
        mediaRecorderRef.current.systemStream.getTracks().forEach(track => track.stop());
      }
      if (mediaRecorderRef.current.micStream) {
        mediaRecorderRef.current.micStream.getTracks().forEach(track => track.stop());
      }
      
      // Stop mixed stream tracks
      if (mediaRecorderRef.current.stream) {
        mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
      }
    }
    
    // Close WebSocket (process remaining audio first)
    if (websocketRef.current && websocketRef.current.readyState === WebSocket.OPEN) {
      websocketRef.current.send(JSON.stringify({ type: 'process' }));
      setTimeout(() => websocketRef.current?.close(), 500);
    }
    
    // Stop audio context
    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      audioContextRef.current.close();
    }
    
    setIsCapturingAudio(false);
    setAudioLevel(0);
  };

  const monitorAudioLevel = () => {
    if (!analyserRef.current) return;
    
    const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
    
    const checkLevel = () => {
      if (!analyserRef.current) return;
      
      analyserRef.current.getByteFrequencyData(dataArray);
      const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
      setAudioLevel(Math.min(100, average));
      
      if (isCapturingAudio || analyserRef.current) {
        requestAnimationFrame(checkLevel);
      }
    };
    
    checkLevel();
  };

  return (
    <div className="live-meeting">
      <div className="page-header">
        <div>
          <h1>Live Meeting</h1>
          <p className="page-subtitle">Real-time meeting capture and transcription</p>
        </div>
        {isRecording && (
          <div className="recording-badge">
            <Activity size={16} className="pulse" />
            <span>Recording</span>
            {isCapturingAudio && (
              <span className="audio-indicator">
                <Radio size={14} className="pulse" />
                Live Audio
              </span>
            )}
          </div>
        )}
      </div>

      {error && (
        <div className="alert alert-error">
          <AlertCircle size={20} />
          <span>{error}</span>
        </div>
      )}

      <div className="content-grid">
        {/* Left Column - Meeting Setup/Control */}
        <div className="control-panel">
          <div className="card">
            <div className="card-header">
              <Mic size={20} />
              <span>Meeting Control</span>
            </div>

            <div className="card-body">
              {!isRecording ? (
                <>
                  {/* Start Meeting Form */}
                  <div className="form-group">
                    <label>Meeting Title</label>
                    <input
                      type="text"
                      className="input"
                      placeholder="e.g., Team Standup"
                      value={title}
                      onChange={(e) => setTitle(e.target.value)}
                      disabled={loading}
                    />
                  </div>

                  <div className="form-group">
                    <label>Participants</label>
                    <input
                      type="text"
                      className="input"
                      placeholder="e.g., Alice, Bob, Charlie"
                      value={participants}
                      onChange={(e) => setParticipants(e.target.value)}
                      disabled={loading}
                    />
                    <small className="input-hint">Comma-separated names</small>
                  </div>

                  <button
                    className="btn btn-primary btn-block"
                    onClick={handleStart}
                    disabled={loading}
                  >
                    <Mic size={20} />
                    {loading ? 'Starting...' : 'Start Live Recording'}
                  </button>

                  <div className="info-box">
                    <AlertCircle size={16} />
                    <div>
                      <strong>🎤 Dual Audio Capture!</strong>
                      <ul>
                        <li><strong>Step 1:</strong> Share your browser tab/screen (for Zoom/Teams audio)</li>
                        <li><strong>Step 2:</strong> Allow microphone access (for your voice)</li>
                        <li>Both will be mixed and transcribed together!</li>
                      </ul>
                    </div>
                  </div>
                </>
              ) : (
                <>
                  {/* Active Meeting Info */}
                  <div className="meeting-info">
                    <div className="info-row">
                      <span className="info-label">Meeting ID:</span>
                      <span className="info-value">{meetingId}</span>
                    </div>
                    <div className="info-row">
                      <span className="info-label">Title:</span>
                      <span className="info-value">{title}</span>
                    </div>
                    <div className="info-row">
                      <span className="info-label">Audio Status:</span>
                      <span className={`status-badge ${isCapturingAudio ? 'status-active' : 'status-inactive'}`}>
                        {isCapturingAudio ? (
                          <><Mic size={14} /> Capturing</>
                        ) : (
                          <><MicOff size={14} /> Stopped</>
                        )}
                      </span>
                    </div>
                    {isCapturingAudio && (
                      <div className="info-row">
                        <span className="info-label">Audio Level:</span>
                        <div className="audio-level-bar">
                          <div 
                            className="audio-level-fill" 
                            style={{width: `${audioLevel}%`}}
                          />
                        </div>
                      </div>
                    )}
                  </div>

                  {!isCapturingAudio && isRecording && (
                    <button
                      className="btn btn-primary btn-block"
                      onClick={startAudioCapture}
                      disabled={loading}
                      style={{marginBottom: '1rem'}}
                    >
                      <Mic size={20} />
                      Start Audio Capture
                    </button>
                  )}

                  <button
                    className="btn btn-danger btn-block"
                    onClick={handleStop}
                    disabled={loading}
                  >
                    <Square size={20} />
                    {loading ? 'Stopping...' : 'Stop Recording'}
                  </button>

                  <div className="info-box info-box-success">
                    <CheckCircle size={16} />
                    <div>
                      <strong>Meeting Active</strong>
                      <p>{isCapturingAudio ? 'Listening to your microphone...' : 'Add text or start audio capture.'}</p>
                    </div>
                  </div>

                  {/* Text Input for Manual Transcript */}
                  <div className="text-input-section">
                    <label><strong>Or Add Text Manually:</strong></label>
                    <textarea
                      className="input"
                      rows="3"
                      placeholder="Type or paste meeting transcript here..."
                      value={textInput}
                      onChange={(e) => setTextInput(e.target.value)}
                    />
                    <button
                      className="btn btn-secondary btn-sm"
                      onClick={handleAddText}
                      disabled={!textInput.trim()}
                    >
                      Add to Transcript
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>

          {/* Instructions */}
          <div className="card">
            <div className="card-header">
              <FileText size={20} />
              <span>How It Works</span>
            </div>
            <div className="card-body">
              <ol className="instructions-list">
                <li>Enter meeting title and participants</li>
                <li>Click "Start Live Recording"</li>
                <li><strong>Share browser tab</strong> with audio (Zoom/Teams)</li>
                <li><strong>Allow microphone</strong> access (your voice)</li>
                <li>Speak normally - transcript appears every 10 seconds</li>
                <li>Watch audio level meter to verify capture</li>
                <li>Click "Stop Recording" to generate notes</li>
              </ol>
              
              <div className="info-box" style={{marginTop: '1rem'}}>
                <CheckCircle size={14} />
                <small>
                  <strong>✨ Dual Audio!</strong> Captures both system audio (Zoom/Teams) and microphone (you) simultaneously!
                </small>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column - Live Transcript */}
        <div className="transcript-panel">
          <div className="card card-full-height">
            <div className="card-header">
              <FileText size={20} />
              <span>Live Transcript</span>
              {transcript.length > 0 && (
                <span className="transcript-count">{transcript.length} segments</span>
              )}
            </div>

            <div className="card-body">
              {!isRecording ? (
                <div className="empty-state">
                  <Mic size={48} className="empty-icon" />
                  <p>Start a meeting to see live transcript</p>
                </div>
              ) : transcript.length === 0 ? (
                <div className="empty-state">
                  <Activity size={48} className="empty-icon pulse" />
                  <p>{isCapturingAudio ? 'Listening... speak now!' : 'Waiting for audio or text'}</p>
                  <small>{isCapturingAudio ? 'Transcription every 10 seconds' : 'Start audio capture or add text'}</small>
                </div>
              ) : (
                <div className="transcript-list">
                  {transcript.map((item, index) => (
                    <div key={index} className="transcript-item">
                      <span className="transcript-time">{item.time}</span>
                      <p className="transcript-text">{item.text}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Note about Live Audio */}
      <div className="note-box" style={{background: 'rgba(16, 185, 129, 0.05)', borderColor: 'rgba(16, 185, 129, 0.2)'}}>
        <CheckCircle size={16} style={{color: 'var(--success)'}} />
        <div>
          <strong>🎉 Dual Audio Capture!</strong> This system captures BOTH your microphone (your voice) AND system audio (Zoom/Teams - others' voices). 
          When you click "Start Live Recording", you'll be asked to share your browser tab/screen with audio, then allow microphone access.
        </div>
      </div>
    </div>
  );
};

export default LiveMeeting;
