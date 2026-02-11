import React, { useEffect, useRef, useState } from 'react'
import {
  ArrowRightOnRectangleIcon,
  MoonIcon,
  SunIcon,
  BoltIcon,
  ChevronDoubleRightIcon
} from '@heroicons/react/24/outline'
import useChat from '../../hooks/useChat'
import useAuth from '../../hooks/useAuth'
import useTheme from '../../hooks/useTheme'
import Sidebar from '../Common/Sidebar'
import MessageList from './MessageList'
import MessageInput from './MessageInput'

const DESKTOP_BREAKPOINT = 1024
const AUTO_SCROLL_THRESHOLD = 170

const ChatWindow = () => {
  const {
    conversations,
    currentConversation,
    messages,
    isLoading,
    streamingMessage,
    loadConversations,
    createConversation,
    selectConversation,
    deleteConversation,
    sendMessage,
    setConversations // only used if available in your hook
  } = useChat()

  const { user, logout } = useAuth()
  const { isDark, toggleTheme } = useTheme()

  const scrollContainerRef = useRef(null)
  const shouldAutoScrollRef = useRef(true)
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false)

  useEffect(() => {
    loadConversations()
  }, [loadConversations])

  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth >= DESKTOP_BREAKPOINT) {
        setIsSidebarOpen(false)
      }
    }
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  const scrollToBottom = (behavior = 'auto') => {
    const el = scrollContainerRef.current
    if (!el) return
    el.scrollTo({ top: el.scrollHeight, behavior })
  }

  useEffect(() => {
    const el = scrollContainerRef.current
    if (!el) return undefined

    const updateAutoScroll = () => {
      const distanceFromBottom =
        el.scrollHeight - el.scrollTop - el.clientHeight
      shouldAutoScrollRef.current =
        distanceFromBottom < AUTO_SCROLL_THRESHOLD
    }

    updateAutoScroll()
    el.addEventListener('scroll', updateAutoScroll, { passive: true })
    return () => el.removeEventListener('scroll', updateAutoScroll)
  }, [currentConversation?.id])

  useEffect(() => {
    if (shouldAutoScrollRef.current) {
      requestAnimationFrame(() => scrollToBottom('auto'))
    }
  }, [messages.length])

  useEffect(() => {
    if (shouldAutoScrollRef.current) {
      requestAnimationFrame(() => scrollToBottom('auto'))
    }
  }, [streamingMessage])

  useEffect(() => {
    shouldAutoScrollRef.current = true
    requestAnimationFrame(() => scrollToBottom('auto'))
  }, [currentConversation?.id])

  const handleToggleSidebar = () => {
    if (window.innerWidth >= DESKTOP_BREAKPOINT) {
      setIsSidebarCollapsed(prev => !prev)
    } else {
      setIsSidebarOpen(prev => !prev)
    }
  }

  const handleNewChat = async () => {
    await createConversation()
    if (window.innerWidth < DESKTOP_BREAKPOINT) {
      setIsSidebarOpen(false)
    }
  }

  const handleSendMessage = async (content) => {
    shouldAutoScrollRef.current = true
    requestAnimationFrame(() => scrollToBottom('auto'))

    await sendMessage(content, true)

    // SAFE optional sidebar timestamp refresh
    if (currentConversation && typeof setConversations === 'function') {
      setConversations(prev =>
        prev.map(c =>
          c.id === currentConversation.id
            ? { ...c, updated_at: new Date().toISOString() }
            : c
        )
      )
    }
  }

  const displayName = user?.username ? `@${user.username}` : '@user'
  const userInitial =
    (user?.username?.trim()?.charAt(0) || 'U').toUpperCase()

  return (
    <div className="flex h-screen overflow-hidden text-[var(--text-primary)]">
      {isSidebarOpen && (
        <button
          className="fixed inset-0 bg-[var(--overlay)] z-40 lg:hidden"
          onClick={() => setIsSidebarOpen(false)}
          aria-label="Close sidebar overlay"
        />
      )}

      <Sidebar
        conversations={conversations}
        currentConversation={currentConversation}
        onSelectConversation={(conv) => {
          selectConversation(conv)
          setIsSidebarOpen(false)
        }}
        onNewChat={handleNewChat}
        onDeleteConversation={deleteConversation}
        onCloseMobile={() => setIsSidebarOpen(false)}
        onToggleCollapse={handleToggleSidebar}
        collapsed={isSidebarCollapsed}
        user={user}
        className={`fixed inset-y-0 left-0 z-50 transition-transform duration-200 lg:static lg:translate-x-0 ${
          isSidebarOpen ? 'translate-x-0' : '-translate-x-full'
        } ${isSidebarCollapsed ? 'lg:w-[92px]' : 'lg:w-[320px]'} w-[292px]`}
      />

      <section className="flex-1 min-w-0 flex flex-col h-full">
        <header className="surface-panel rounded-none border-x-0 border-t-0 px-4 sm:px-6 py-3">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-3 min-w-0">
              {!isSidebarOpen && (
                <button
                  className="neutral-button p-2 lg:hidden"
                  onClick={() => setIsSidebarOpen(true)}
                  aria-label="Open sidebar"
                >
                  <ChevronDoubleRightIcon className="h-4 w-4" />
                </button>
              )}
              <div className="h-9 w-9 rounded-xl surface-strong glow-ring hidden sm:flex items-center justify-center">
                <BoltIcon className="h-4 w-4 text-[var(--accent)]" />
              </div>
              <div className="min-w-0">
                <h1 className="text-lg sm:text-xl font-semibold truncate">
                  MemoryAI
                </h1>
                <p className="text-xs sm:text-sm text-muted truncate">
                  {currentConversation
                    ? currentConversation.title
                    : 'Start a conversation and keep context across sessions.'}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2 sm:gap-3">
              <span className="hidden md:inline-flex items-center gap-1.5 px-3 py-1 rounded-full surface-strong text-xs font-medium">
                <span className="inline-block h-2 w-2 rounded-full bg-[var(--success)]" />
                Active
              </span>
              <button
                onClick={toggleTheme}
                className="neutral-button p-2"
                aria-label="Toggle theme"
                title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
              >
                {isDark ? (
                  <SunIcon className="h-5 w-5" />
                ) : (
                  <MoonIcon className="h-5 w-5" />
                )}
              </button>
              <span className="text-sm font-medium hidden sm:block">
                {displayName}
              </span>
              <button
                onClick={logout}
                className="neutral-button p-2"
                title="Logout"
                aria-label="Logout"
              >
                <ArrowRightOnRectangleIcon className="h-5 w-5" />
              </button>
            </div>
          </div>
        </header>

        <MessageList
          messages={messages}
          streamingMessage={streamingMessage}
          isLoading={isLoading}
          scrollContainerRef={scrollContainerRef}
          userInitial={userInitial}
        />

        <MessageInput
          onSend={handleSendMessage}
          isLoading={isLoading}
        />
      </section>
    </div>
  )
}

export default ChatWindow
