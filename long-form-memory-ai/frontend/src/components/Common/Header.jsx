import React from 'react'
import { Link } from 'react-router-dom'
import { UserCircleIcon, ArrowRightOnRectangleIcon } from '@heroicons/react/24/outline'
import useAuth from '../../hooks/useAuth'

const Header = () => {
  const { user, logout } = useAuth()

  return (
    <header className="sticky top-0 z-50 border-b border-neutral-800 bg-neutral-900/95">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center">
            <Link to="/chat" className="flex items-center space-x-2">
              <div className="w-9 h-9 rounded-md flex items-center justify-center bg-neutral-800 border border-neutral-700">
                <span className="text-neutral-100 font-bold text-lg">M</span>
              </div>
              <span className="text-xl font-bold text-neutral-100">MemoryAI</span>
            </Link>
          </div>

          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2 text-sm text-neutral-300">
              <UserCircleIcon className="h-5 w-5" />
              <span>{user?.username}</span>
            </div>
            <button
              onClick={logout}
              className="p-2 text-neutral-400 hover:text-neutral-200 hover:bg-neutral-800 rounded-md transition-colors cursor-pointer"
              title="Logout"
            >
              <ArrowRightOnRectangleIcon className="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>
    </header>
  )
}

export default Header
