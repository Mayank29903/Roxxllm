import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import { ChatProvider } from './contexts/ChatContext'
import Login from './components/Auth/Login'
import Register from './components/Auth/Register'
import ChatWindow from './components/Chat/ChatWindow'
import Header from './components/Common/Header'
import useAuth from './hooks/useAuth'

const PrivateRoute = ({ children }) => {
  const { user, loading } = useAuth()
  
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }
  
  return user ? children : <Navigate to="/login" />
}

function AppContent() {
  const { user } = useAuth()

  return (
    <div className="min-h-screen bg-gray-50">
      {user && <Header />}
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route 
          path="/chat" 
          element={
            <PrivateRoute>
              <ChatProvider>
                <ChatWindow />
              </ChatProvider>
            </PrivateRoute>
          } 
        />
        <Route path="/" element={<Navigate to="/chat" />} />
      </Routes>
    </div>
  )
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  )
}

export default App