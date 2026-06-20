import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Search, 
  Calendar, 
  Users,
  FileText,
  Trash2,
  Eye,
  Download,
  AlertCircle
} from 'lucide-react';
import { meetingAPI } from '../services/api';
import { format } from 'date-fns';
import './MeetingHistory.css';

const MeetingHistory = () => {
  const navigate = useNavigate();
  const [meetings, setMeetings] = useState([]);
  const [filteredMeetings, setFilteredMeetings] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [deleteConfirm, setDeleteConfirm] = useState(null);

  useEffect(() => {
    loadMeetings();
  }, []);

  useEffect(() => {
    filterMeetings();
  }, [searchQuery, meetings]);

  const loadMeetings = async () => {
    try {
      setLoading(true);
      setError('');
      const data = await meetingAPI.getAllMeetings();
      setMeetings(data.meetings || []);
    } catch (error) {
      setError('Failed to load meetings');
      console.error('Error loading meetings:', error);
    } finally {
      setLoading(false);
    }
  };

  const filterMeetings = () => {
    if (!searchQuery.trim()) {
      setFilteredMeetings(meetings);
      return;
    }

    const query = searchQuery.toLowerCase();
    const filtered = meetings.filter(meeting => 
      meeting.title?.toLowerCase().includes(query) ||
      meeting.participants?.some(p => p.toLowerCase().includes(query)) ||
      meeting.meeting_id?.toLowerCase().includes(query)
    );
    setFilteredMeetings(filtered);
  };

  const handleView = (meetingId) => {
    navigate(`/meeting/${meetingId}`);
  };

  const handleDelete = async (meetingId) => {
    try {
      await meetingAPI.deleteMeeting(meetingId);
      setMeetings(meetings.filter(m => m.meeting_id !== meetingId));
      setDeleteConfirm(null);
    } catch (error) {
      alert('Failed to delete meeting');
    }
  };

  const handleExport = async (meetingId) => {
    try {
      const blob = await meetingAPI.exportMeeting(meetingId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `meeting_${meetingId}.txt`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      alert('Failed to export meeting');
    }
  };

  const formatDate = (dateString) => {
    try {
      return format(new Date(dateString), 'MMM dd, yyyy HH:mm');
    } catch {
      return dateString;
    }
  };

  if (loading) {
    return (
      <div className="meeting-history">
        <div className="page-header">
          <h1>Meeting History</h1>
        </div>
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Loading meetings...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="meeting-history">
      <div className="page-header">
        <div>
          <h1>Meeting History</h1>
          <p className="page-subtitle">Browse and manage past meetings</p>
        </div>
      </div>

      {error && (
        <div className="alert alert-error">
          <AlertCircle size={20} />
          <span>{error}</span>
        </div>
      )}

      {/* Search Bar */}
      <div className="search-bar">
        <Search size={20} className="search-icon" />
        <input
          type="text"
          className="search-input"
          placeholder="Search by title, participant, or meeting ID..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
        {searchQuery && (
          <button 
            className="clear-search-btn"
            onClick={() => setSearchQuery('')}
          >
            Clear
          </button>
        )}
      </div>

      {/* Stats */}
      <div className="history-stats">
        <div className="stat-item">
          <FileText size={20} />
          <div>
            <div className="stat-value">{meetings.length}</div>
            <div className="stat-label">Total Meetings</div>
          </div>
        </div>
        <div className="stat-item">
          <Search size={20} />
          <div>
            <div className="stat-value">{filteredMeetings.length}</div>
            <div className="stat-label">Search Results</div>
          </div>
        </div>
      </div>

      {/* Meetings List */}
      {filteredMeetings.length === 0 ? (
        <div className="empty-state">
          {searchQuery ? (
            <>
              <Search size={48} className="empty-icon" />
              <p>No meetings found matching "{searchQuery}"</p>
              <button className="btn btn-primary" onClick={() => setSearchQuery('')}>
                Clear Search
              </button>
            </>
          ) : (
            <>
              <FileText size={48} className="empty-icon" />
              <p>No meetings yet</p>
              <p className="empty-hint">Start a meeting or upload audio to get started</p>
              <div className="empty-actions">
                <button className="btn btn-primary" onClick={() => navigate('/live')}>
                  Start Live Meeting
                </button>
                <button className="btn btn-secondary" onClick={() => navigate('/upload')}>
                  Upload Audio
                </button>
              </div>
            </>
          )}
        </div>
      ) : (
        <div className="meetings-grid">
          {filteredMeetings.map((meeting) => (
            <div key={meeting.meeting_id} className="meeting-card">
              <div className="meeting-header">
                <h3 className="meeting-title">{meeting.title || 'Untitled Meeting'}</h3>
                <span className="meeting-id">ID: {meeting.meeting_id?.slice(0, 8)}</span>
              </div>

              <div className="meeting-meta">
                <div className="meta-item">
                  <Calendar size={16} />
                  <span>{formatDate(meeting.date)}</span>
                </div>
                {meeting.participants && meeting.participants.length > 0 && (
                  <div className="meta-item">
                    <Users size={16} />
                    <span>{meeting.participants.slice(0, 2).join(', ')}
                      {meeting.participants.length > 2 && ` +${meeting.participants.length - 2}`}
                    </span>
                  </div>
                )}
              </div>

              <div className="meeting-stats">
                {meeting.summary && (
                  <div className="stat-badge">
                    <FileText size={14} />
                    <span>Summary</span>
                  </div>
                )}
                {meeting.key_decisions && meeting.key_decisions.length > 0 && (
                  <div className="stat-badge">
                    <span>{meeting.key_decisions.length} Decisions</span>
                  </div>
                )}
                {meeting.action_items && meeting.action_items.length > 0 && (
                  <div className="stat-badge">
                    <span>{meeting.action_items.length} Actions</span>
                  </div>
                )}
              </div>

              <div className="meeting-actions">
                <button
                  className="action-btn action-btn-primary"
                  onClick={() => handleView(meeting.meeting_id)}
                  title="View Details"
                >
                  <Eye size={16} />
                  View
                </button>
                <button
                  className="action-btn action-btn-secondary"
                  onClick={() => handleExport(meeting.meeting_id)}
                  title="Export as TXT"
                >
                  <Download size={16} />
                  Export
                </button>
                <button
                  className="action-btn action-btn-danger"
                  onClick={() => setDeleteConfirm(meeting.meeting_id)}
                  title="Delete Meeting"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deleteConfirm && (
        <div className="modal-overlay" onClick={() => setDeleteConfirm(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Delete Meeting?</h3>
            </div>
            <div className="modal-body">
              <p>Are you sure you want to delete this meeting? This action cannot be undone.</p>
            </div>
            <div className="modal-actions">
              <button
                className="btn btn-secondary"
                onClick={() => setDeleteConfirm(null)}
              >
                Cancel
              </button>
              <button
                className="btn btn-danger"
                onClick={() => handleDelete(deleteConfirm)}
              >
                <Trash2 size={16} />
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MeetingHistory;
