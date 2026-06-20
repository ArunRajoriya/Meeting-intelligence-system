import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Upload, 
  File, 
  X, 
  CheckCircle,
  AlertCircle,
  Loader
} from 'lucide-react';
import { meetingAPI } from '../services/api';
import './UploadAudio.css';

const UploadAudio = () => {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);
  
  const [title, setTitle] = useState('');
  const [participants, setParticipants] = useState('');
  const [file, setFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [meetingId, setMeetingId] = useState(null);

  const MAX_FILE_SIZE = 25 * 1024 * 1024; // 25MB
  const ALLOWED_TYPES = ['audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/m4a', 'audio/x-m4a', 'audio/ogg', 'audio/flac'];

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleFileInput = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelect(e.target.files[0]);
    }
  };

  const handleFileSelect = (selectedFile) => {
    setError('');
    setSuccess(false);

    // Check file type
    if (!ALLOWED_TYPES.includes(selectedFile.type) && !selectedFile.name.match(/\.(mp3|wav|m4a|ogg|flac)$/i)) {
      setError('Invalid file type. Please upload MP3, WAV, M4A, OGG, or FLAC');
      return;
    }

    // Check file size
    if (selectedFile.size > MAX_FILE_SIZE) {
      setError(`File too large. Maximum size is ${MAX_FILE_SIZE / 1024 / 1024}MB`);
      return;
    }

    setFile(selectedFile);
  };

  const removeFile = () => {
    setFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!title.trim()) {
      setError('Please enter a meeting title');
      return;
    }

    if (!participants.trim()) {
      setError('Please enter at least one participant');
      return;
    }

    if (!file) {
      setError('Please select an audio file');
      return;
    }

    setUploading(true);
    setError('');
    setProgress(0);

    try {
      // Step 1: Start meeting
      setProgress(10);
      const startResponse = await meetingAPI.startMeeting(title, participants);
      const newMeetingId = startResponse.meeting_id;

      // Step 2: Upload audio file
      setProgress(30);
      await meetingAPI.addAudio(file);

      // Step 3: Stop meeting and generate notes
      setProgress(70);
      const notes = await meetingAPI.stopMeeting();
      
      setProgress(100);
      setSuccess(true);
      setMeetingId(notes.meeting_id);

      // Navigate to meeting detail after 2 seconds
      setTimeout(() => {
        navigate(`/meeting/${notes.meeting_id}`);
      }, 2000);

    } catch (error) {
      setError(error.response?.data?.detail || 'Failed to process audio file');
      setUploading(false);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  return (
    <div className="upload-audio">
      <div className="page-header">
        <div>
          <h1>Upload Audio</h1>
          <p className="page-subtitle">Process recorded meeting audio files</p>
        </div>
      </div>

      {error && (
        <div className="alert alert-error">
          <AlertCircle size={20} />
          <span>{error}</span>
        </div>
      )}

      {success && (
        <div className="alert alert-success">
          <CheckCircle size={20} />
          <span>Meeting processed successfully! Redirecting...</span>
        </div>
      )}

      <div className="upload-container">
        <div className="upload-card">
          <form onSubmit={handleSubmit}>
            {/* Meeting Details */}
            <div className="form-section">
              <h3>Meeting Details</h3>
              
              <div className="form-group">
                <label>Meeting Title *</label>
                <input
                  type="text"
                  className="input"
                  placeholder="e.g., Team Standup"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  disabled={uploading}
                  required
                />
              </div>

              <div className="form-group">
                <label>Participants *</label>
                <input
                  type="text"
                  className="input"
                  placeholder="e.g., Alice, Bob, Charlie"
                  value={participants}
                  onChange={(e) => setParticipants(e.target.value)}
                  disabled={uploading}
                  required
                />
                <small className="input-hint">Comma-separated names</small>
              </div>
            </div>

            {/* File Upload */}
            <div className="form-section">
              <h3>Audio File</h3>
              
              {!file ? (
                <div
                  className={`upload-dropzone ${dragActive ? 'drag-active' : ''}`}
                  onDragEnter={handleDrag}
                  onDragLeave={handleDrag}
                  onDragOver={handleDrag}
                  onDrop={handleDrop}
                  onClick={() => !uploading && fileInputRef.current?.click()}
                >
                  <Upload size={48} className="upload-icon" />
                  <p className="upload-text">
                    Drag & drop audio file here, or click to browse
                  </p>
                  <p className="upload-hint">
                    Supported: MP3, WAV, M4A, OGG, FLAC (max 25MB)
                  </p>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="audio/*,.mp3,.wav,.m4a,.ogg,.flac"
                    onChange={handleFileInput}
                    style={{ display: 'none' }}
                    disabled={uploading}
                  />
                </div>
              ) : (
                <div className="file-preview">
                  <div className="file-info">
                    <File size={40} className="file-icon" />
                    <div className="file-details">
                      <div className="file-name">{file.name}</div>
                      <div className="file-size">{formatFileSize(file.size)}</div>
                    </div>
                  </div>
                  {!uploading && (
                    <button
                      type="button"
                      className="remove-file-btn"
                      onClick={removeFile}
                    >
                      <X size={20} />
                    </button>
                  )}
                </div>
              )}
            </div>

            {/* Progress Bar */}
            {uploading && (
              <div className="progress-section">
                <div className="progress-bar-container">
                  <div className="progress-bar" style={{ width: `${progress}%` }} />
                </div>
                <div className="progress-text">
                  {progress < 30 ? 'Starting meeting...' :
                   progress < 70 ? 'Processing audio...' :
                   progress < 100 ? 'Generating notes...' :
                   'Complete!'}
                </div>
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              className="btn btn-primary btn-block btn-large"
              disabled={!file || uploading}
            >
              {uploading ? (
                <>
                  <Loader size={20} className="spin" />
                  Processing...
                </>
              ) : (
                <>
                  <Upload size={20} />
                  Process Audio File
                </>
              )}
            </button>
          </form>
        </div>

        {/* Info Panel */}
        <div className="info-panel">
          <div className="card">
            <div className="card-header">
              <AlertCircle size={20} />
              <span>How it works</span>
            </div>
            <div className="card-body">
              <ol className="steps-list">
                <li>
                  <strong>Upload audio file</strong>
                  <p>Drag & drop or browse for your recording</p>
                </li>
                <li>
                  <strong>Add meeting details</strong>
                  <p>Enter title and participant names</p>
                </li>
                <li>
                  <strong>Process</strong>
                  <p>AI transcribes and analyzes the content</p>
                </li>
                <li>
                  <strong>Get notes</strong>
                  <p>Summary, decisions, and action items generated</p>
                </li>
              </ol>
            </div>
          </div>

          <div className="card">
            <div className="card-header">
              <CheckCircle size={20} />
              <span>File Requirements</span>
            </div>
            <div className="card-body">
              <ul className="requirements-list">
                <li>
                  <CheckCircle size={16} className="check-icon" />
                  <span>Format: MP3, WAV, M4A, OGG, FLAC</span>
                </li>
                <li>
                  <CheckCircle size={16} className="check-icon" />
                  <span>Max size: 25MB</span>
                </li>
                <li>
                  <CheckCircle size={16} className="check-icon" />
                  <span>Duration: Up to 2 hours</span>
                </li>
                <li>
                  <CheckCircle size={16} className="check-icon" />
                  <span>Quality: Clear audio recommended</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UploadAudio;
