import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import LiveMeeting from './pages/LiveMeeting';
import UploadAudio from './pages/UploadAudio';
import MeetingHistory from './pages/MeetingHistory';
import MeetingDetail from './pages/MeetingDetail';
import './App.css';

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true);

  return (
    <Router>
      <div className="app">
        <Sidebar isOpen={sidebarOpen} onToggle={() => setSidebarOpen(!sidebarOpen)} />
        <main className={`main-content ${sidebarOpen ? 'sidebar-open' : 'sidebar-closed'}`}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/live" element={<LiveMeeting />} />
            <Route path="/upload" element={<UploadAudio />} />
            <Route path="/history" element={<MeetingHistory />} />
            <Route path="/meeting/:id" element={<MeetingDetail />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
