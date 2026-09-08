import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: API_BASE,
})

export const authAPI = {
  register: (name, email) =>
    api.post('/auth/register', { name, email }),

  enroll: (userId, audioBlob) => {
    const formData = new FormData()
    formData.append('user_id', userId)
    formData.append('audio', audioBlob, 'enrollment.wav')
    return api.post('/auth/enroll', formData)
  },

  getChallenge: (userId) =>
    api.get(`/auth/challenge?user_id=${userId}`),

  verify: (userId, token, audioBlob) => {
    const formData = new FormData()
    formData.append('user_id', userId)
    formData.append('token', token)
    formData.append('audio', audioBlob, 'verify.wav')
    return api.post('/auth/verify', formData)
  },

  getVoiceprintHistory: (userId) =>
    api.get(`/users/${userId}/voiceprint-history`),
}
