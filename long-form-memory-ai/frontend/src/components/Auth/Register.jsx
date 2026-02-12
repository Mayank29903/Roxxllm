import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { MoonIcon, SunIcon, SparklesIcon } from '@heroicons/react/24/outline'
import useAuth from '../../hooks/useAuth'
import useTheme from '../../hooks/useTheme'

const Register = () => {
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    password: '',
    confirmPassword: ''
  })
  const [validationError, setValidationError] = useState('')
  const [isGoogleLoading, setIsGoogleLoading] = useState(false)
  const { register, loginWithGoogle, error } = useAuth()
  const { isDark, toggleTheme } = useTheme()
  const navigate = useNavigate()

  const handleChange = (e) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setValidationError('')

    if (formData.password !== formData.confirmPassword) {
      setValidationError('Passwords do not match')
      return
    }

    if (formData.password.length < 6) {
      setValidationError('Password must be at least 6 characters')
      return
    }

    try {
      await register(formData.email, formData.username, formData.password)
      navigate('/chat')
    } catch {
      // Error handled in context
    }
  }

  const handleGoogleSignIn = async (useRedirect = false) => {
    try {
      setIsGoogleLoading(true)
      await loginWithGoogle(useRedirect)
      navigate('/chat')
    } catch {
      // Error handled in context
    } finally {
      setIsGoogleLoading(false)
    }
  }

  return (
    <div className="h-[100dvh] overflow-hidden px-4 py-2 sm:py-3">
      <div className="relative max-w-6xl mx-auto h-full">
        <div className="absolute top-0 right-0 z-10">
          <button
            onClick={toggleTheme}
            className="neutral-button p-2 cursor-pointer"
            aria-label="Toggle theme"
            title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
          >
            {isDark ? <SunIcon className="h-5 w-5" /> : <MoonIcon className="h-5 w-5" />}
          </button>
        </div>

        <div className="h-full flex items-center justify-center">
          <div className="max-w-lg w-full mx-auto surface-panel rounded-3xl p-5 sm:p-6">
            <div className="text-center">
              <div className="h-12 w-12 mx-auto rounded-xl surface-strong flex items-center justify-center glow-ring">
                <SparklesIcon className="h-6 w-6 text-[var(--accent)]" />
              </div>
              <h2 className="mt-3 text-3xl font-semibold">Create Account</h2>
              <p className="mt-1 text-secondary">Join MemoryAI and keep context across chats</p>
            </div>

            <form className="mt-4 space-y-2.5" onSubmit={handleSubmit}>
              {(error || validationError) && (
                <div className="auth-error rounded-xl px-4 py-2 text-sm">
                  {validationError || error}
                </div>
              )}

              <div>
                <label htmlFor="email" className="block text-sm font-medium mb-1">
                  Email address
                </label>
                <input
                  id="email"
                  name="email"
                  type="email"
                  required
                  className="input-field px-4 py-2"
                  placeholder="Enter your email"
                  value={formData.email}
                  onChange={handleChange}
                />
              </div>

              <div>
                <label htmlFor="username" className="block text-sm font-medium mb-1">
                  Username
                </label>
                <input
                  id="username"
                  name="username"
                  type="text"
                  required
                  className="input-field px-4 py-2"
                  placeholder="Choose a username"
                  value={formData.username}
                  onChange={handleChange}
                />
              </div>

              <div>
                <label htmlFor="password" className="block text-sm font-medium mb-1">
                  Password
                </label>
                <input
                  id="password"
                  name="password"
                  type="password"
                  required
                  className="input-field px-4 py-2"
                  placeholder="Create a password"
                  value={formData.password}
                  onChange={handleChange}
                />
              </div>

              <div>
                <label htmlFor="confirmPassword" className="block text-sm font-medium mb-1">
                  Confirm Password
                </label>
                <input
                  id="confirmPassword"
                  name="confirmPassword"
                  type="password"
                  required
                  className="input-field px-4 py-2"
                  placeholder="Confirm your password"
                  value={formData.confirmPassword}
                  onChange={handleChange}
                />
              </div>

              <button type="submit" className="accent-button w-full py-1.5 font-semibold cursor-pointer">
                Create account
              </button>
            </form>

            {/* Divider */}
            <div className="relative my-3">
              <div className="absolute inset-0 flex items-center">
                <div className="auth-divider-line w-full border-t"></div>
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 surface-panel text-secondary">Or continue with</span>
              </div>
            </div>

            {/* Google Sign-In */}
            <button
              type="button"
              onClick={() => handleGoogleSignIn(false)}
              disabled={isGoogleLoading}
              className="google-auth-btn w-full flex items-center justify-center gap-3 rounded-xl px-4 py-2 text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
            >
              {isGoogleLoading ? (
                <>
                  <div className="h-5 w-5 animate-spin rounded-full border-2 border-[var(--border-soft)] border-t-[var(--accent)]"></div>
                  Signing up...
                </>
              ) : (
                <>
                  <svg className="h-5 w-5" viewBox="0 0 24 24">
                    <path 
                      fill="#4285F4" 
                      d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                    />
                    <path 
                      fill="#34A853" 
                      d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                    />
                    <path 
                      fill="#FBBC05" 
                      d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                    />
                    <path 
                      fill="#EA4335" 
                      d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l2.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                    />
                  </svg>
                  Continue with Google
                </>
              )}
            </button>

            <p className="text-center mt-3 text-sm text-secondary">
              Already have an account?{' '}
              <Link to="/login" className="font-semibold text-[var(--accent)] hover:underline">
                Sign in here
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Register
