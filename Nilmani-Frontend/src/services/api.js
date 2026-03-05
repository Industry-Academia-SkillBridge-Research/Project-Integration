import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8005';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const uploadJobDescription = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await axios.post(
    `${API_BASE_URL}/api/upload-jd`,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  );
  
  return response.data;
};

export const startInterview = async (sessionId) => {
  const response = await api.post('/api/start-interview', {
    session_id: sessionId,
  });
  return response.data;
};

export const submitAnswer = async (sessionId, answer) => {
  const response = await api.post('/api/next-question', {
    session_id: sessionId,
    user_answer: answer,
  });
  return response.data;
};

export const getSessionStatus = async (sessionId) => {
  const response = await api.get(`/api/session/${sessionId}`);
  return response.data;
};

export const endSession = async (sessionId) => {
  const response = await api.delete(`/api/session/${sessionId}`);
  return response.data;
};

export const healthCheck = async () => {
  const response = await api.get('/health');
  return response.data;
};

export default api;
