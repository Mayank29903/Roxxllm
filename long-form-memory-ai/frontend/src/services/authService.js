import api from './api'

export const authService = {
  login: async (email, password) => {
    const formData = new FormData()
    formData.append('username', email)
    formData.append('password', password)
    
    const response = await api.post('/auth/login', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return response.data
  },

  register: async (email, username, password) => {
    const response = await api.post('/auth/register', {
      email,
      username,
      password
    })
    return response.data
  },

  loginWithGoogle: async (googleData) => {
    const response = await api.post('/auth/google', googleData)
    return response.data
  },

  getMe: async () => {
    const response = await api.get('/auth/me')
    return response.data
  },

  refreshToken: async (refreshToken) => {
    const response = await api.post('/auth/refresh', {
      refresh_token: refreshToken
    })
    return response.data
  },

  deleteAccount: async () => {
    return api.delete('/user/delete')
  }
}