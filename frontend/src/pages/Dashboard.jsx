import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Activity, 
  FileText, 
  CheckCircle, 
  Clock,
  Mic,
  Upload,
  TrendingUp
} from 'lucide-react';
import { getSystemStatus, meetingAPI } from '../services/api';
import './Dashboard.css';

const Dashboard = () => {
  const navigate = useNavigate();
  const [systemStatus, setSystemStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    totalMeetings: 0,
    activeMeeting: false,
    transcribedHours: 0,
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const status = await getSystemStatus();
      setSystemStatus(status);
      
      // Check if there's an active meeting
      try {
        await meetingAPI.getStatus();
        setStats(prev => ({ ...prev, activeMeeting: true }));
      } catch (error) {
        setStats(prev => ({ ...prev, activeMeeting: false }));
      }

      // Get meeting stats from storage
      if (status.storage) {
        setStats(prev => ({
          ...prev,
          totalMeetings: status.storage.total_meetings || 0,
        }));
      }
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const StatCard = ({ icon: Icon, title, value, color, subtitle }) => (
    <div className="stat-card">
      <div className="stat-icon" style={{ backgroundColor: `${color}20`, color }}>
        <Icon size={24} />
      </div>
      <div className="stat-content">
        <div className="stat-title">{title}</div>
        <div className="stat-value">{value}</div>
        {subtitle && <div className="stat-subtitle">{subtitle}</div>}
      </div>
    </div>
  );

  const QuickAction = ({ icon: Icon, title, description, onClick, color }) => (
    <button className="quick-action" onClick={onClick}>
      <div className="action-icon" style={{ backgroundColor: `${color}20`, color }}>
        <Icon size={20} />
      </div>
      <div className="action-content">
        <div className="action-title">{title}</div>
        <div className="action-description">{description}</div>
      </div>
    </button>
  );

  if (loading) {
    return (
      <div className="dashboard">
        <div className="dashboard-header">
          <h1>Dashboard</h1>
        </div>
        <div className="loading">Loading...</div>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <div>
          <h1>Dashboard</h1>
          <p className="dashboard-subtitle">Meeting Intelligence System</p>
        </div>
        {stats.activeMeeting && (
          <div className="active-meeting-badge">
            <Activity size={16} />
            <span>Meeting in Progress</span>
          </div>
        )}
      </div>

      {/* Stats Grid */}
      <div className="stats-grid">
        <StatCard
          icon={FileText}
          title="Total Meetings"
          value={stats.totalMeetings}
          color="#3b82f6"
          subtitle="All time"
        />
        <StatCard
          icon={Activity}
          title="Active Meeting"
          value={stats.activeMeeting ? 'Yes' : 'No'}
          color="#10b981"
          subtitle={stats.activeMeeting ? 'In progress' : 'Ready to start'}
        />
        <StatCard
          icon={CheckCircle}
          title="AI Status"
          value={systemStatus?.status === 'active' ? 'Online' : 'Offline'}
          color="#8b5cf6"
          subtitle="98%+ accuracy"
        />
        <StatCard
          icon={TrendingUp}
          title="Transcription"
          value="Multi-Provider"
          color="#f59e0b"
          subtitle="Groq • OpenAI • Local"
        />
      </div>

      {/* Quick Actions */}
      <div className="section">
        <h2 className="section-title">Quick Actions</h2>
        <div className="quick-actions-grid">
          <QuickAction
            icon={Mic}
            title="Start Live Meeting"
            description="Capture meeting in real-time"
            onClick={() => navigate('/live')}
            color="#3b82f6"
          />
          <QuickAction
            icon={Upload}
            title="Upload Recording"
            description="Process audio file"
            onClick={() => navigate('/upload')}
            color="#10b981"
          />
          <QuickAction
            icon={FileText}
            title="View History"
            description="Browse past meetings"
            onClick={() => navigate('/history')}
            color="#8b5cf6"
          />
          <QuickAction
            icon={Clock}
            title="Recent Meeting"
            description="Continue where you left off"
            onClick={() => navigate('/history')}
            color="#f59e0b"
          />
        </div>
      </div>

      {/* Features */}
      <div className="section">
        <h2 className="section-title">System Features</h2>
        <div className="features-grid">
          {systemStatus?.features?.map((feature, index) => (
            <div key={index} className="feature-item">
              <CheckCircle size={16} className="feature-icon" />
              <span>{feature}</span>
            </div>
          ))}
        </div>
      </div>

      {/* System Info */}
      {systemStatus && (
        <div className="system-info">
          <div className="info-item">
            <strong>Status:</strong> {systemStatus.status}
          </div>
          <div className="info-item">
            <strong>Version:</strong> 2.0.0
          </div>
          <div className="info-item">
            <strong>Backend:</strong> FastAPI + Python
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
