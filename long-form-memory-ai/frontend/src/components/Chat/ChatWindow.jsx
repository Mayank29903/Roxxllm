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
  const [pendingDeleteConversation, setPendingDeleteConversation] = useState(null)
  const [isDeletingConversation, setIsDeletingConversation] = useState(false)

  useEffect(() => {
    let isCancelled = false

    const restoreConversation = async () => {
      const loadedConversations = await loadConversations()
      if (isCancelled || !loadedConversations?.length) return

      const savedConversationId = localStorage.getItem('activeConversationId')
      const restoredConversation =
        loadedConversations.find((conv) => conv.id === savedConversationId) ||
        loadedConversations[0]

      if (restoredConversation) {
        await selectConversation(restoredConversation)
      }
    }

    restoreConversation()

    return () => {
      isCancelled = true
    }
  }, [loadConversations, selectConversation])

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

  const handleRequestDeleteConversation = (conversation) => {
    setPendingDeleteConversation(conversation)
  }

  const closeDeleteConversationDialog = () => {
    if (isDeletingConversation) return
    setPendingDeleteConversation(null)
  }

  const confirmDeleteConversation = async () => {
    if (!pendingDeleteConversation || isDeletingConversation) return
    try {
      setIsDeletingConversation(true)
      await deleteConversation(pendingDeleteConversation.id)
      setPendingDeleteConversation(null)
    } finally {
      setIsDeletingConversation(false)
    }
  }

  useEffect(() => {
    if (!pendingDeleteConversation) return undefined

    const onKeyDown = (event) => {
      if (event.key === 'Escape') {
        closeDeleteConversationDialog()
      }
    }

    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [pendingDeleteConversation, isDeletingConversation])

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
        onRequestDeleteConversation={handleRequestDeleteConversation}
        onCloseMobile={() => setIsSidebarOpen(false)}
        onToggleCollapse={handleToggleSidebar}
        collapsed={isSidebarCollapsed}
        user={user}
        className={`fixed inset-y-0 left-0 z-50 overflow-hidden transition-[transform,width] duration-[380ms] ease-[cubic-bezier(0.22,1,0.36,1)] lg:static lg:translate-x-0 ${
          isSidebarOpen ? 'translate-x-0' : '-translate-x-full'
        } ${isSidebarCollapsed ? 'lg:w-[92px]' : 'lg:w-[320px]'} w-[292px]`}
      />

      <section className="chat-main-surface relative flex-1 min-w-0 flex flex-col h-full">
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
              <span className="hidden md:inline-flex items-center gap-1.5 px-3 py-1 rounded-full status-pill text-xs font-medium">
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

        {pendingDeleteConversation && (
          <div className="absolute inset-0 z-[70] flex items-center justify-center p-4 sm:p-6">
            <button
              type="button"
              className="absolute inset-0 bg-[var(--overlay)]"
              onClick={closeDeleteConversationDialog}
              aria-label="Close delete confirmation"
            />

            <div
              role="dialog"
              aria-modal="true"
              aria-labelledby="delete-chat-title"
              className="relative w-full max-w-2xl surface-panel rounded-3xl p-6 sm:p-8"
            >
              <h3 id="delete-chat-title" className="text-2xl sm:text-3xl font-semibold">
                Delete This Conversation?
              </h3>
              <p className="mt-3 text-base sm:text-lg text-secondary leading-7">
                You are about to permanently delete{' '}
                <span className="font-semibold text-[var(--text-primary)]">
                  "{pendingDeleteConversation.title}"
                </span>
                . This will also remove all memories extracted from this chat.
              </p>

              <div className="mt-7 flex items-center justify-end gap-3">
                <button
                  type="button"
                  onClick={closeDeleteConversationDialog}
                  disabled={isDeletingConversation}
                  className="neutral-button px-5 py-2.5"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={confirmDeleteConversation}
                  disabled={isDeletingConversation}
                  className="danger-button delete-conversation-btn rounded-xl px-5 py-2.5 disabled:opacity-60"
                >
                  {isDeletingConversation ? 'Deleting...' : 'Delete Conversation'}
                </button>
              </div>
            </div>
          </div>
        )}
      </section>
    </div>
  )
}

export default ChatWindow
