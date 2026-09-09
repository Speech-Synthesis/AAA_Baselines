import axios from 'axios';

// API base URL (Backend FastAPI server)
const API_BASE = 'http://localhost:8000';

// Configure Axios client with timeout (60s for model loading on first request)
const client = axios.create({
  baseURL: API_BASE,
  timeout: 60000,
});

// Local in-memory mock store for offline/demo mode
const mockStore = {
  users: [
    { id: 'usr-90a1b2c3-4567-8901-2345-6789abcdef01', name: 'Dr. Aditya Sharma', email: 'aditya@aaaengine.io' },
    { id: 'usr-11b2c3d4-5678-9012-3456-789abcdef02', name: 'Navadeep Kumar', email: 'navadeep@aaaengine.io' }
  ],
  voiceprints: {
    'usr-90a1b2c3-4567-8901-2345-6789abcdef01': { sample_count: 3, updated_at: new Date().toISOString() }
  },
  challenges: {},
  logs: [
    {
      id: 'log-001',
      user_id: 'usr-90a1b2c3-4567-8901-2345-6789abcdef01',
      result: 'ACCEPT',
      confidence: 0.942,
      layer_blocked: null,
      reason: 'Authentication successful',
      l2_label: 'bonafide',
      l2_confidence: 0.985,
      l1_score: 0.942,
      created_at: new Date(Date.now() - 3600000).toISOString()
    },
    {
      id: 'log-002',
      user_id: 'usr-90a1b2c3-4567-8901-2345-6789abcdef01',
      result: 'REJECT',
      confidence: 0.961,
      layer_blocked: 2,
      reason: 'Deepfake/spoof detected',
      l2_label: 'spoof',
      l2_confidence: 0.961,
      l1_score: 0.0,
      created_at: new Date(Date.now() - 7200000).toISOString()
    }
  ]
};

// Check if live backend is reachable
export const checkServerHealth = async () => {
  try {
    const res = await client.get('/');
    return res.data && res.data.status === 'running';
  } catch (err) {
    return false;
  }
};

// 1. Register User
export const registerUser = async (name, email) => {
  try {
    const res = await client.post('/auth/register', { name, email });
    return res.data;
  } catch (err) {
    if (err.response?.data?.detail) throw new Error(err.response.data.detail);
    
    // Fallback Mock Execution
    console.warn('Backend unreachable. Executing register in Mock Mode.');
    const newId = `usr-${Math.random().toString(36).substring(2, 10)}-${Date.now()}`;
    const newUser = { id: newId, name, email };
    mockStore.users.push(newUser);
    return { user_id: newId, is_mock: true };
  }
};

// 2. Enroll Voice Sample (NO MOCK - always use real backend)
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
    throw new Error(err.message || 'Backend connection failed - check if server is running');
  }
};

// 3. Get Dynamic Challenge
export const getChallenge = async (userId) => {
  try {
    const res = await client.get(`/auth/challenge?user_id=${userId}`);
    return res.data;
  } catch (err) {
    if (err.response?.data?.detail) throw new Error(err.response.data.detail);
    
    // Fallback Mock Execution
    console.warn('Backend unreachable. Executing getChallenge in Mock Mode.');
    const phrases = [
      'Say: four crimson falcon nine',
      'Say: seven emerald panther three',
      'The quick brown fox jumps over the lazy dog',
      'My voice is my secure biometric key',
      'Say: eight amber sapphire two'
    ];
    const phrase = phrases[Math.floor(Math.random() * phrases.length)];
    const expiresAt = new Date(Date.now() + 90000).toISOString(); // 90s TTL
    const token = `mock-token-${Math.random().toString(36).substring(2, 10)}`;

    mockStore.challenges[token] = { userId, phrase, expiresAt };

    return {
      phrase,
      token,
      expires_at: expiresAt,
      is_mock: true
    };
  }
};

// 4. Verify Voice Response (NO MOCK - always use real backend)
export const verifyVoice = async (userId, token, audioBlob, forceSpoof = false) => {
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
    throw new Error(err.message || 'Backend connection failed - check if server is running');
  }
};

// 5. Get Voiceprint History / Logs
export const getVoiceprintHistory = async (userId) => {
  try {
    const res = await client.get(`/users/${userId}/voiceprint-history`);
    return res.data;
  } catch (err) {
    const vp = mockStore.voiceprints[userId];
    if (vp) {
      return [{ updated_at: vp.updated_at, sample_count: vp.sample_count }];
    }
    return [{ updated_at: new Date().toISOString(), sample_count: 3 }];
  }
};

export const getMockStore = () => mockStore;
