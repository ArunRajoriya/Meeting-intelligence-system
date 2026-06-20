import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, 
  Calendar, 
  Users,
  FileText,
  CheckCircle,
  Download,
  Copy,
  AlertCircle
} from 'lucide-react';
import { meetingAPI } from '../services/api';
import { format } from 'date-fns';
import './MeetingDetail.css';

const MeetingDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  
  const [meeting, setMeeting] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    loadMeeting();
  }, [id]);

  const loadMeeting = async () => {
    try {
      setLoading(true);
      setError('');
      const data = await meetingAPI.getMeeting(id);
      setMeeting(data);
    } catch (error) {
      setError(error.response?.data?.detail || 'Failed to load meeting');
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    try {
      const blob = await meetingAPI.exportMeeting(id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `meeting_${id}.txt`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      alert('Failed to export meeting');
    }
  };

  const handleCopy = () => {
    const text = `
Meeting: ${meeting.title}
Date: ${meeting.date}
Participants: ${meeting.participants?.join(', ')}

SUMMARY:
${meeting.summary}

KEY DECISIONS:
${meeting.key_decisions?.map((d, i) => `${i + 1}. ${d}`).join('\n')}

ACTION ITEMS:
${meeting.action_items?.map((a, i) => `${i + 1}. ${a.task}\n   Owner: ${a.owner || 'Unassigned'}\n   Deadline: ${a.deadline || 'No deadline'}`).join('\n\n')}
    `.trim();

    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const formatDate = (dateString) => {
    try {
      return format(new Date(dateString), 'MMMM dd, yyyy • HH:mm');
    } catch {
      return dateString;
    }
  };

  if (loading) {
    return (
      <div className="meeting-detail">
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Loading meeting...</p>
        </div>
      </div>
    );
  }

  if (error || !meeting) {
    return (
      <div className="meeting-detail">
        <div className="error-state">
          <AlertCircle size={48} className="error-icon" />
          <h2>Meeting Not Found</h2>
          <p>{error || 'The requested meeting could not be found.'}</p>
          <button className="btn btn-primary" onClick={() => navigate('/history')}>
            <ArrowLeft size={16} />
            Back to History
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="meeting-detail">
      {/* Header */}
      <div className="detail-header">
        <button className="back-btn" onClick={() => navigate('/history')}>
          <ArrowLeft size={20} />
          Back to History
        </button>

        <div className="header-actions">
          <button className="btn btn-secondary" onClick={handleCopy}>
            <Copy size={16} />
            {copied ? 'Copied!' : 'Copy All'}
          </button>
          <button className="btn btn-primary" onClick={handleExport}>
            <Download size={16} />
            Export TXT
          </button>
        </div>
      </div>

      {/* Meeting Info */}
      <div className="meeting-info-card">
        <h1 className="meeting-title">{meeting.title}</h1>
        
        <div className="meeting-metadata">
          <div className="metadata-item">
            <Calendar size={18} />
            <span>{formatDate(meeting.date)}</span>
          </div>
          
          {meeting.participants && meeting.participants.length > 0 && (
            <div className="metadata-item">
              <Users size={18} />
              <span>{meeting.participants.join(', ')}</span>
            </div>
          )}

          <div className="metadata-item">
            <FileText size={18} />
            <span>ID: {meeting.meeting_id}</span>
          </div>
        </div>
      </div>

      {/* Summary Section */}
      <div className="content-section">
        <div className="section-header">
          <FileText size={20} />
          <h2>Summary</h2>
        </div>
        <div className="section-content">
          <p className="summary-text">{meeting.summary || 'No summary available'}</p>
        </div>
      </div>

      {/* Key Decisions Section */}
      <div className="content-section">
        <div className="section-header">
          <CheckCircle size={20} />
          <h2>Key Decisions</h2>
          {meeting.key_decisions && meeting.key_decisions.length > 0 && (
            <span className="count-badge">{meeting.key_decisions.length}</span>
          )}
        </div>
        <div className="section-content">
          {meeting.key_decisions && meeting.key_decisions.length > 0 ? (
            <ul className="decisions-list">
              {meeting.key_decisions.map((decision, index) => (
                <li key={index} className="decision-item">
                  <span className="decision-number">{index + 1}</span>
                  <span className="decision-text">{decision}</span>
                </li>
              ))}
            </ul>
          ) : (
            <div className="empty-section">
              <p>No key decisions recorded</p>
            </div>
          )}
        </div>
      </div>

      {/* Action Items Section */}
      <div className="content-section">
        <div className="section-header">
          <CheckCircle size={20} />
          <h2>Action Items</h2>
          {meeting.action_items && meeting.action_items.length > 0 && (
            <span className="count-badge">{meeting.action_items.length}</span>
          )}
        </div>
        <div className="section-content">
          {meeting.action_items && meeting.action_items.length > 0 ? (
            <div className="action-items-grid">
              {meeting.action_items.map((item, index) => (
                <div key={index} className="action-item-card">
                  <div className="action-item-number">{index + 1}</div>
                  <div className="action-item-content">
                    <div className="action-task">{item.task}</div>
                    <div className="action-meta">
                      <div className="action-meta-item">
                        <Users size={14} />
                        <span>{item.owner || 'Unassigned'}</span>
                      </div>
                      <div className="action-meta-item">
                        <Calendar size={14} />
                        <span>{item.deadline || 'No deadline'}</span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-section">
              <p>No action items identified</p>
            </div>
          )}
        </div>
      </div>

      {/* JSON Preview (Optional) */}
      <div className="content-section">
        <div className="section-header">
          <FileText size={20} />
          <h2>Raw Data (JSON)</h2>
        </div>
        <div className="section-content">
          <pre className="json-preview">
            {JSON.stringify(meeting, null, 2)}
          </pre>
        </div>
      </div>
    </div>
  );
};

export default MeetingDetail;
