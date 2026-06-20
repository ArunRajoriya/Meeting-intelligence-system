# Meeting Intelligence System - Frontend

Modern React frontend for the Meeting Intelligence System with real-time meeting capture, audio upload, and intelligent note generation.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
npm install
```

### 2. Start Development Server
```bash
npm run dev
```

Frontend runs on: **http://localhost:3000**

### 3. Ensure Backend is Running
The frontend requires the backend API to be running:
```bash
# In project root directory
python main.py
```

Backend runs on: **http://localhost:8000**

---

## 📁 Project Structure

```
src/
├── components/          # Reusable UI components
│   ├── Sidebar.jsx     # Navigation sidebar
│   └── Sidebar.css
│
├── pages/              # Route pages
│   ├── Dashboard.jsx   # Main dashboard with stats
│   ├── LiveMeeting.jsx # Start/stop live meetings
│   ├── UploadAudio.jsx # Upload and process audio files
│   ├── MeetingHistory.jsx # Browse past meetings
│   ├── MeetingDetail.jsx  # View meeting details
│   └── *.css           # Page-specific styles
│
├── services/
│   └── api.js          # API client (axios)
│
├── App.jsx             # Main app with routing
├── main.jsx            # React entry point
└── index.css           # Global styles
```

---

## 🎨 Features

### Dashboard
- System stats (meetings, AI status, transcription)
- Quick actions (Start meeting, Upload, History)
- Active meeting indicator
- System features overview

### Live Meeting
- Start/stop recording interface
- Meeting details form
- Real-time status display
- Live transcript viewer (ready for WebSocket)

### Upload Audio
- Drag & drop file upload
- File validation (MP3, WAV, M4A, OGG, FLAC, max 25MB)
- Progress tracking
- Automatic meeting note generation

### Meeting History
- Search and filter meetings
- Grid/card layout
- View, export, delete actions
- Empty states and loading indicators

### Meeting Detail
- Full meeting notes display
- Summary, decisions, action items
- Export to TXT
- Copy to clipboard
- Raw JSON viewer

---

## 🔌 API Integration

The frontend communicates with the FastAPI backend via `/api` proxy:

```javascript
// Example API calls
import { meetingAPI } from './services/api';

// Start meeting
const meeting = await meetingAPI.startMeeting(title, participants);

// Upload audio
await meetingAPI.addAudio(audioFile);

// Get all meetings
const meetings = await meetingAPI.getAllMeetings();

// Get meeting by ID
const notes = await meetingAPI.getMeeting(meetingId);
```

### Proxy Configuration
Requests to `/api/*` are proxied to `http://localhost:8000`:
```javascript
// vite.config.js
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true,
    rewrite: (path) => path.replace(/^\/api/, '')
  }
}
```

---

## 🎯 Available Scripts

### Development
```bash
npm run dev        # Start dev server (port 3000)
```

### Production
```bash
npm run build      # Build for production
npm run preview    # Preview production build
```

### Linting
```bash
npm run lint       # Run ESLint
```

---

## 🎨 Tech Stack

- **React 18** - UI library
- **Vite** - Build tool (fast HMR, optimized builds)
- **React Router** - Client-side routing
- **Axios** - HTTP client
- **Lucide React** - Icon library
- **date-fns** - Date formatting
- **CSS3** - Custom styling (no framework)

---

## 🌈 Design System

### Colors
```css
--primary: #3b82f6      /* Blue - Primary actions */
--success: #10b981      /* Green - Success states */
--warning: #f59e0b      /* Orange - Warnings */
--danger: #ef4444       /* Red - Errors, delete */
--secondary: #8b5cf6    /* Purple - Secondary */
--dark: #1f2937         /* Text */
--gray: #6b7280         /* Secondary text */
--light-gray: #f3f4f6   /* Backgrounds */
```

### Typography
- Font Family: System fonts (-apple-system, Segoe UI, Roboto)
- Base Size: 16px
- Line Height: 1.6

### Spacing
```css
--spacing-xs: 0.25rem   /* 4px */
--spacing-sm: 0.5rem    /* 8px */
--spacing-md: 1rem      /* 16px */
--spacing-lg: 1.5rem    /* 24px */
--spacing-xl: 2rem      /* 32px */
```

---

## 📱 Responsive Design

- **Desktop:** 1024px+ (full sidebar, multi-column)
- **Tablet:** 768px - 1023px (collapsible sidebar)
- **Mobile:** < 768px (hamburger menu, single column)

---

## 🔧 Configuration

### Environment Variables
Create `.env` file in frontend directory if needed:
```env
VITE_API_URL=http://localhost:8000
```

### Vite Config
`vite.config.js` handles:
- React plugin
- Dev server (port 3000)
- API proxy to backend
- Build optimization

---

## 📦 Dependencies

### Core
- react, react-dom - UI library
- react-router-dom - Routing
- axios - HTTP client

### UI
- lucide-react - Icons
- date-fns - Date formatting

### Dev
- vite - Build tool
- @vitejs/plugin-react - React support
- eslint - Linting

---

## 🚀 Production Deployment

### 1. Build Frontend
```bash
npm run build
```

Creates `dist/` folder with optimized files.

### 2. Serve from Backend
Add to FastAPI `main.py`:
```python
from fastapi.staticfiles import StaticFiles

# After all API routes
app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="frontend")
```

### 3. Deploy
Deploy as single application with both frontend and backend!

---

## 🐛 Troubleshooting

### Dev Server Won't Start
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### API Calls Failing
1. Check backend is running on port 8000
2. Check CORS is enabled in `main.py`
3. Check proxy config in `vite.config.js`

### Build Errors
```bash
# Clear Vite cache
rm -rf dist node_modules/.vite
npm install
npm run build
```

---

## 📚 Documentation

- [Full Stack Guide](../FULLSTACK_GUIDE.md)
- [Frontend Setup](../FRONTEND_SETUP.md)
- [Frontend Complete](../FRONTEND_COMPLETE.md)
- [Main README](../README.md)

---

## ✅ Features Checklist

- [x] Dashboard with stats
- [x] Live meeting interface
- [x] Audio file upload
- [x] Meeting history browser
- [x] Meeting detail viewer
- [x] Search and filter
- [x] Export functionality
- [x] Responsive design
- [x] Error handling
- [x] Loading states
- [x] Empty states
- [x] Form validation

---

## 🎉 Ready!

Your frontend is complete and ready to use!

```bash
# Start everything
cd ..
start_fullstack.bat

# Or manually
python main.py          # Terminal 1
cd frontend && npm run dev  # Terminal 2
```

Open: **http://localhost:3000**

Enjoy your fullstack Meeting Intelligence System! 🚀
