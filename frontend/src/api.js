import axios from 'axios';

// API base URL (Backend FastAPI server)
// In development: use empty string to leverage Vite proxy (avoids CORS issues)
// In production: use the deployed backend URL
const API_BASE = window.location.hostname === 'localhost'
  ? ''  // Empty = use Vite proxy, which handles CORS
  : 'https://aaa-backend.onrender.com';

// Configure Axios client with timeout (60s for model loading on first request)
const client = axios.create({
  baseURL: API_BASE,
  timeout: 60000,
  withCredentials: false,  // Don't send credentials to avoid CORS preflight complexity
});

// Backend availability status (updated by checkServerHealth)
let BACKEND_AVAILABLE = true;

// Check if live backend is reachable (uses /v1/health endpoint)
export const checkServerHealth = async () => {
  try {
    const res = await client.get('/v1/health', { timeout: 5000 });
    BACKEND_AVAILABLE = res.data && res.data.status === 'healthy';
    return BACKEND_AVAILABLE;
  } catch (err) {
    BACKEND_AVAILABLE = false;
    console.warn('[AAA Frontend] Backend unavailable:', err.message);
    return false;
  }
};

// Get detailed readiness status (includes model status)
export const checkServerReadiness = async () => {
  try {
    const res = await client.get('/v1/ready', { timeout: 10000 });
    return res.data;
  } catch (err) {
    console.warn('[AAA Frontend] Readiness check failed:', err.message);
    return { status: 'not_ready', error: err.message };
  }
};

// Get current backend availability status
export const isBackendAvailable = () => BACKEND_AVAILABLE;

// Get all registered users
export const getAllUsers = async () => {
  try {
    console.log('Fetching users from:', API_BASE + '/users');
    const res = await client.get('/users');
    console.log('Users fetched:', res.data);
    return res.data;
  } catch (err) {
    console.error('Get users error:', err.message, err.response?.status);
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

// 2. Enroll Voice Sample (v1 API)
export const enrollVoice = async (userId, audioBlob) => {
  const formData = new FormData();
  formData.append('user_id', userId);
  formData.append('audio', audioBlob, 'enrollment.wav');

  try {
    const res = await client.post('/v1/enroll', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return res.data;
  } catch (err) {
    console.error('Enroll API error:', err);
    if (err.response?.data?.detail) throw new Error(err.response.data.detail);
    throw new Error(err.message || 'Backend connection failed');
  }
};

// 3. Get Dynamic Challenge (v1 API - POST method)
export const getChallenge = async (userId) => {
  try {
    const res = await client.post('/v1/challenges', {
      user_id: userId,
      purpose: 'authentication'
    });
    return res.data;
  } catch (err) {
    console.error('Challenge API error:', err);
    if (err.response?.data?.detail) throw new Error(err.response.data.detail);
    throw new Error(err.message || 'Backend connection failed');
  }
};

// 4. Verify Voice Response (legacy endpoint for demo - shows raw scores for debugging)
// Note: Production apps use /v1/verify which hides internal scores per API specification
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
