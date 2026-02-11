import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { MoonIcon, SunIcon, SparklesIcon } from '@heroicons/react/24/outline'
import useAuth from '../../hooks/useAuth'
import useTheme from '../../hooks/useTheme'

const Login = () => {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isGoogleLoading, setIsGoogleLoading] = useState(false)
  const { login, loginWithGoogle, error } = useAuth()
  const { isDark, toggleTheme } = useTheme()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      await login(email, password)
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
    <div className="min-h-screen px-4 py-8 sm:py-12">
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-end mb-6">
          <button
            onClick={toggleTheme}
            className="neutral-button p-2"
            aria-label="Toggle theme"
            title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
          >
            {isDark ? <SunIcon className="h-5 w-5" /> : <MoonIcon className="h-5 w-5" />}
          </button>
        </div>

        <div className="max-w-md mx-auto surface-panel rounded-3xl p-7 sm:p-9">
          <div className="text-center">
            <div className="h-14 w-14 mx-auto rounded-2xl surface-strong flex items-center justify-center glow-ring">
              <SparklesIcon className="h-7 w-7 text-[var(--accent)]" />
            </div>
            <h2 className="mt-5 text-3xl font-semibold">Welcome Back</h2>
            <p className="mt-2 text-secondary">Sign in to continue with MemoryAI</p>
          </div>

          <form className="mt-8 space-y-4" onSubmit={handleSubmit}>
            {error && (
              <div className="rounded-xl border border-red-400/40 bg-red-500/10 text-red-300 px-4 py-3 text-sm">
                {error}
              </div>
            )}

            <div>
              <label htmlFor="email" className="block text-sm font-medium mb-1.5">
                Email address
              </label>
              <input
                id="email"
                name="email"
                type="email"
                required
                className="input-field px-4 py-2.5"
                placeholder="Enter your email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium mb-1.5">
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                required
                className="input-field px-4 py-2.5"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>

            <button type="submit" className="accent-button w-full py-2.5 font-semibold">
              Sign in
            </button>
          </form>

          {/* Divider */}
          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-300 dark:border-gray-600"></div>
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
            className="w-full flex items-center justify-center gap-3 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-4 py-2.5 text-sm font-medium text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isGoogleLoading ? (
              <>
                <div className="h-5 w-5 animate-spin rounded-full border-2 border-gray-300 border-t-blue-600"></div>
                Signing in...
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

          <p className="text-center mt-6 text-sm text-secondary">
            Don&apos;t have an account?{' '}
            <Link to="/register" className="font-semibold text-[var(--accent)] hover:underline">
              Register here
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}

export default Login
