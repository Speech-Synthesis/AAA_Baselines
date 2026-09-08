import axios from 'axios';

// API base URL (Backend FastAPI server)
const API_BASE = 'http://localhost:8000';

// Configure Axios client with timeout
const client = axios.create({
  baseURL: API_BASE,
  timeout: 8000,
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

// 2. Enroll Voice Sample
export const enrollVoice = async (userId, audioBlob) => {
  try {
    const formData = new FormData();
    formData.append('user_id', userId);
    formData.append('audio', audioBlob, 'enrollment.wav');

    const res = await client.post('/auth/enroll', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return res.data;
  } catch (err) {
    if (err.response?.data?.detail) throw new Error(err.response.data.detail);
    
    // Fallback Mock Execution
    console.warn('Backend unreachable. Executing enroll in Mock Mode.');
    const current = mockStore.voiceprints[userId] || { sample_count: 0 };
    const updated = {
      sample_count: current.sample_count + 1,
      updated_at: new Date().toISOString()
    };
    mockStore.voiceprints[userId] = updated;
    return { status: 'enrolled', sample_count: updated.sample_count, is_mock: true };
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

// 4. Verify Voice Response
export const verifyVoice = async (userId, token, audioBlob, forceSpoof = false) => {
  try {
    const formData = new FormData();
    formData.append('user_id', userId);
    formData.append('token', token);
    formData.append('audio', audioBlob, 'verify.wav');

    const res = await client.post('/auth/verify', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return res.data;
  } catch (err) {
    if (err.response?.data?.detail) throw new Error(err.response.data.detail);
    
    // Fallback Mock Execution
    console.warn('Backend unreachable. Executing verifyVoice in Mock Mode.');
    const sessionId = `sess-${Math.random().toString(36).substring(2, 10)}`;
    const isSuccess = !forceSpoof && Math.random() > 0.15; // 85% accept rate unless forced

    const mockResponse = isSuccess
      ? {
          result: 'ACCEPT',
          confidence: 0.958,
          layer_blocked: null,
          session_id: sessionId,
          reason: 'Authentication successful (Voice & Challenge verified)',
          l2_label: 'bonafide',
          l2_confidence: 0.991,
          l1_score: 0.958
        }
      : {
          result: 'REJECT',
          confidence: forceSpoof ? 0.965 : 0.421,
          layer_blocked: forceSpoof ? 2 : 1,
          session_id: sessionId,
          reason: forceSpoof ? 'Deepfake/spoof detected at Layer 2' : 'Speaker verification failed at Layer 1',
          l2_label: forceSpoof ? 'spoof' : 'bonafide',
          l2_confidence: forceSpoof ? 0.965 : 0.920,
          l1_score: forceSpoof ? 0.0 : 0.421
        };

    // Update mock logs & voiceprint
    mockStore.logs.unshift({
      id: `log-${Date.now()}`,
      user_id: userId,
      ...mockResponse,
      created_at: new Date().toISOString()
    });

    if (isSuccess && mockStore.voiceprints[userId]) {
      mockStore.voiceprints[userId].sample_count += 1;
      mockStore.voiceprints[userId].updated_at = new Date().toISOString();
    }

    return { ...mockResponse, is_mock: true };
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
