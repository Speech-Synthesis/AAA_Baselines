import axios from 'axios';

// API base URL (Backend FastAPI server)
const API_BASE = 'http://localhost:8000';

// Configure Axios client with timeout (60s for model loading on first request)
const client = axios.create({
  baseURL: API_BASE,
  timeout: 60000,
});

// Check if live backend is reachable
export const checkServerHealth = async () => {
  try {
    const res = await client.get('/');
    return res.data && res.data.status === 'running';
  } catch (err) {
    return false;
  }
};

// Get all registered users
export const getAllUsers = async () => {
  try {
    const res = await client.get('/users');
    return res.data;
  } catch (err) {
    console.error('Get users error:', err);
    return [];
  }
};

// 1. Register User
export const registerUser = async (name, email) => {
  try {
    const res = await client.post('/auth/register', { name, email });
    return res.data;
  } catch (err) {
    console.error('Register API error:', err);
    if (err.response?.data?.detail) throw new Error(err.response.data.detail);
    throw new Error(err.message || 'Backend connection failed');
  }
};

// 2. Enroll Voice Sample
export const enrollVoice = async (userId, audioBlob) => {
  const formData = new FormData();
  formData.append('user_id', userId);
  formData.append('audio', audioBlob, 'enrollment.wav');

  try {
    const res = await client.post('/auth/enroll', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return res.data;
  } catch (err) {
    console.error('Enroll API error:', err);
    if (err.response?.data?.detail) throw new Error(err.response.data.detail);
    throw new Error(err.message || 'Backend connection failed');
  }
};

// 3. Get Dynamic Challenge
export const getChallenge = async (userId) => {
  try {
    const res = await client.get(`/auth/challenge?user_id=${userId}`);
    return res.data;
  } catch (err) {
    console.error('Challenge API error:', err);
    if (err.response?.data?.detail) throw new Error(err.response.data.detail);
    throw new Error(err.message || 'Backend connection failed');
  }
};

// 4. Verify Voice Response
export const verifyVoice = async (userId, token, audioBlob) => {
  const formData = new FormData();
  formData.append('user_id', userId);
  formData.append('token', token);
  formData.append('audio', audioBlob, 'verify.wav');

  try {
    const res = await client.post('/auth/verify', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return res.data;
  } catch (err) {
    console.error('Verify API error:', err);
    if (err.response?.data?.detail) throw new Error(err.response.data.detail);
    throw new Error(err.message || 'Backend connection failed');
  }
};

// 5. Get Voiceprint History
export const getVoiceprintHistory = async (userId) => {
  try {
    const res = await client.get(`/users/${userId}/voiceprint-history`);
    return res.data;
  } catch (err) {
    console.error('Voiceprint history error:', err);
    return [];
  }
};

// 6. Get Auth Logs
export const getAuthLogs = async (userId) => {
  try {
    const res = await client.get(`/users/${userId}/auth-logs`);
    return res.data;
  } catch (err) {
    console.error('Auth logs error:', err);
    return [];
  }
};
