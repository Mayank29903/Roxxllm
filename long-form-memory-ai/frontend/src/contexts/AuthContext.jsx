import React, { createContext, useState, useEffect, useCallback } from 'react'
import { authService } from '../services/authService'

export const AuthContext = createContext(null)

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (token) {
      fetchUser()
    } else {
      setLoading(false)
    }
  }, [])

  const fetchUser = async () => {
    try {
      const userData = await authService.getMe()
      setUser(userData)
    } catch (err) {
      localStorage.removeItem('token')
    } finally {
      setLoading(false)
    }
  }

  const login = async (email, password) => {
    try {
      setError(null)
      const data = await authService.login(email, password)
      localStorage.setItem('token', data.access_token)
      setUser(data.user)
      return data
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed')
      throw err
    }
  }

  const register = async (email, username, password) => {
    try {
      setError(null)
      const data = await authService.register(email, username, password)
      localStorage.setItem('token', data.access_token)
      setUser(data.user)
      return data
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed')
      throw err
    }
  }

  const logout = useCallback(() => {
    localStorage.removeItem('token')
    setUser(null)
  }, [])

  const value = {
    user,
    loading,
    error,
    login,
    register,
    logout,
    isAuthenticated: !!user
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}