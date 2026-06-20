import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Mic, 
  Upload, 
  History, 
  Menu,
  X 
} from 'lucide-react';
import './Sidebar.css';

const Sidebar = ({ isOpen, onToggle }) => {
  const location = useLocation();

  const menuItems = [
    { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
    { path: '/live', icon: Mic, label: 'Live Meeting' },
    { path: '/upload', icon: Upload, label: 'Upload Audio' },
    { path: '/history', icon: History, label: 'History' },
  ];

  const isActive = (path) => location.pathname === path;

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div className="sidebar-overlay" onClick={onToggle} />
      )}

      <aside className={`sidebar ${isOpen ? 'open' : 'closed'}`}>
        <div className="sidebar-header">
          <div className="sidebar-logo">
            <Mic className="logo-icon" />
            {isOpen && <span className="logo-text">Meeting AI</span>}
          </div>
          <button className="toggle-btn" onClick={onToggle}>
            {isOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>

        <nav className="sidebar-nav">
          {menuItems.map((item) => {
            const Icon = item.icon;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`nav-item ${isActive(item.path) ? 'active' : ''}`}
                title={!isOpen ? item.label : ''}
              >
                <Icon size={20} className="nav-icon" />
                {isOpen && <span className="nav-label">{item.label}</span>}
              </Link>
            );
          })}
        </nav>

        <div className="sidebar-footer">
          <div className="version-info">
            {isOpen && <span>v1.0.0</span>}
          </div>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;
