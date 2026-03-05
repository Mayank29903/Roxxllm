import React from 'react'
import { Routes, Route, Navigate, Outlet } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import { ChatProvider } from './contexts/ChatContext'
import { ThemeProvider } from './contexts/ThemeContext'
import Login from './components/Auth/Login'
import Register from './components/Auth/Register'
import ChatWindow from './components/Chat/ChatWindow'
import MemoryDashboard from './pages/MemoryDashboard'
import useAuth from './hooks/useAuth'

// Protected Route Wrapper
const PrivateRoute = ({ children }) => {
  const { user, loading } = useAuth()
  
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--bg-primary)]">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-[var(--border-soft)] border-t-[var(--accent)]"></div>
      </div>
    )
  }
  
  return user ? children : <Navigate to="/login" replace />
}

// Layout for authenticated pages (includes ChatProvider)
const PrivateAppLayout = () => (
  <PrivateRoute>
    <ChatProvider>
      <Outlet />
    </ChatProvider>
  </PrivateRoute>
)

function AppContent() {
  return (
    <div className="min-h-screen app-shell bg-[var(--bg-primary)] text-[var(--text-primary)]">
      <Routes>
        {/* Public Routes */}
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        
        {/* Protected Routes */}
        <Route element={<PrivateAppLayout />}>
          <Route path="/chat" element={<ChatWindow />} />
          <Route path="/memory" element={<MemoryDashboard />} />
          
          {/* Default redirect to chat */}
          <Route path="/" element={<Navigate to="/chat" replace />} />
          
          {/* Catch all */}
          <Route path="*" element={<Navigate to="/chat" replace />} />
        </Route>
      </Routes>
    </div>
  )
}

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </ThemeProvider>
  )
}

export default App