import axios from 'axios';

const API_BASE_URL =
"https://ai-powered-meeting-intelligence-platform.onrender.com";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Meeting API
export const meetingAPI = {
  // Start a new meeting
  startMeeting: async (title, participants) => {
    const response = await api.post('/meeting/start', {
      title,
      participants: participants.split(',').map(p => p.trim()),
    });
    return response.data;
  },

  // Stop active meeting
  stopMeeting: async () => {
    const response = await api.post('/meeting/stop');
    return response.data;
  },

  // Get meeting status
  getStatus: async () => {
    const response = await api.get('/meeting/status');
    return response.data;
  },

  // Add text input to meeting
  addInput: async (text) => {
    const response = await api.post('/meeting/input', { text });
    return response.data;
  },

  // Add audio input to meeting
  addAudio: async (audioFile) => {
    const formData = new FormData();
    formData.append('audio', audioFile);
    const response = await api.post('/meeting/input/audio', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // Get meeting by ID
  getMeeting: async (meetingId) => {
    const response = await api.get(`/meeting/${meetingId}`);
    return response.data;
  },

  // Get all meetings
  getAllMeetings: async () => {
    const response = await api.get('/meetings');
    return response.data;
  },

  // Delete meeting
  deleteMeeting: async (meetingId) => {
    const response = await api.delete(`/meeting/${meetingId}`);
    return response.data;
  },

  // Export meeting as TXT
  exportMeeting: async (meetingId) => {
    const response = await api.get(`/meeting/${meetingId}/export`, {
      responseType: 'blob',
    });
    return response.data;
  },
};

// Transcription API
export const transcriptionAPI = {
  // Transcribe audio file
  transcribeFile: async (audioFile) => {
    const formData = new FormData();
    formData.append('audio', audioFile);
    const response = await api.post('/transcribe/file', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
};

// Health check
export const healthCheck = async () => {
  const response = await api.get('/health');
  return response.data;
};

// Get system status
export const getSystemStatus = async () => {
  const response = await api.get('/');
  return response.data;
};

export default api;
