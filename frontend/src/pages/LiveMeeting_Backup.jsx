import React, { useState, useEffect } from 'react';
import { 
  Mic, 
  Square, 
  Users, 
  FileText,
  Activity,
  AlertCircle,
  CheckCircle
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
  const mediaRecorderRef = React.useRef(null);
  const websocketRef = React.useRef(null);
  const audioContextRef = React.useRef(null);
  const analyserRef = React.useRef(null);

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
      setTitle(statusData.title);
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
    } catch (error) {
      setError(error.response?.data?.detail || 'Failed to start meeting');
    } finally {
      setLoading(false);
    }
  };

  const handleStop = async () => {
    if (!meetingId) return;

    setLoading(true);
    setError('');

    try {
      const notes = await meetingAPI.stopMeeting();
      setIsRecording(false);
      setStatus(null);
      
      // Show success and notes
      alert('Meeting stopped successfully! Notes generated.');
      
      // Optionally navigate to meeting detail
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
      setTranscript([...transcript, { text: textInput, timestamp: new Date() }]);
      setTextInput('');
      setError('');
    } catch (error) {
      setError(error.response?.data?.detail || 'Failed to add text');
    }
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
                    {loading ? 'Starting...' : 'Start Recording'}
                  </button>

                  <div className="info-box">
                    <AlertCircle size={16} />
                    <div>
                      <strong>Before you start:</strong>
                      <ul>
                        <li>Ensure microphone is working</li>
                        <li>Close unnecessary audio apps</li>
                        <li>Start your Zoom/Teams meeting</li>
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
                      <span className="info-label">Status:</span>
                      <span className="status-badge status-active">
                        <Activity size={14} />
                        Recording
                      </span>
                    </div>
                  </div>

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
                      <p>Add text or audio below to build transcript.</p>
                    </div>
                  </div>

                  {/* Text Input for Manual Transcript */}
                  <div className="text-input-section">
                    <label><strong>Add Text Input:</strong></label>
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
                    <small className="input-hint">
                      Use "Upload Audio" page for audio files, or add text manually here
                    </small>
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
                <li>Click "Start Recording"</li>
                <li><strong>Add Content:</strong>
                  <ul>
                    <li>Type text manually above</li>
                    <li>Upload audio via "Upload Audio" page</li>
                    <li>Use <code>streaming_meeting.py</code> for live capture</li>
                  </ul>
                </li>
                <li>Click "Stop Recording" when done</li>
                <li>Notes generated automatically</li>
              </ol>
              
              <div className="info-box" style={{marginTop: '1rem'}}>
                <AlertCircle size={14} />
                <small>
                  <strong>For Live Audio:</strong> Run <code>python streaming_meeting.py</code> 
                  from your terminal for real-time microphone capture.
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
                  <p>No transcript yet</p>
                  <small>Add text manually or upload audio files</small>
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

      {/* Note about Python backend */}
      <div className="note-box">
        <AlertCircle size={16} />
        <div>
          <strong>Live Audio Capture:</strong> This interface controls meeting sessions. 
          For live microphone/system audio capture, run <code>python streaming_meeting.py</code> from your terminal, 
          or use the "Upload Audio" page for pre-recorded files.
        </div>
      </div>
    </div>
  );
};

export default LiveMeeting;
