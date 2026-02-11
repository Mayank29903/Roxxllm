import React from 'react'
import {
  PlusIcon,
  ChatBubbleLeftRightIcon,
  TrashIcon,
  ChevronDoubleLeftIcon,
  ChevronDoubleRightIcon,
  SparklesIcon,
  UserCircleIcon
} from '@heroicons/react/24/outline'
import { formatSidebarIST } from '../../utils/time'

const Sidebar = ({
  conversations,
  currentConversation,
  onSelectConversation,
  onNewChat,
  onDeleteConversation,
  onCloseMobile,
  onToggleCollapse,
  collapsed = false,
  className = '',
  user
}) => {
  const username = user?.username || 'Guest'

  return (
    <aside className={`flex flex-col h-full surface-panel ${className}`}>
      <div className="p-3 md:p-4 flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <div className="h-10 w-10 rounded-xl surface-strong flex items-center justify-center">
            <SparklesIcon className="h-5 w-5 text-[var(--accent)]" />
          </div>
          {!collapsed && (
            <div className="min-w-0">
              <p className="text-xs text-muted uppercase tracking-wider">
                Conversations
              </p>
            </div>
          )}
        </div>

        <button
          onClick={() => {
            onToggleCollapse()
            onCloseMobile()
          }}
          className="neutral-button p-2"
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? (
            <ChevronDoubleRightIcon className="h-4 w-4" />
          ) : (
            <ChevronDoubleLeftIcon className="h-4 w-4" />
          )}
        </button>
      </div>

      <div className="px-3 md:px-4 pb-3 md:pb-4">
        <button
          onClick={onNewChat}
          className="accent-button w-full flex items-center justify-center gap-2 px-4 py-3"
          title="Start a new conversation"
        >
          <PlusIcon className="h-5 w-5" />
          {!collapsed && <span className="font-medium">New Chat</span>}
        </button>
      </div>

      <div className="flex-1 overflow-y-auto soft-scroll px-2 md:px-3 space-y-1.5">
        {!collapsed && (
          <div className="px-2 py-1 text-xs font-semibold text-muted uppercase tracking-[0.16em]">
            Your Chats
          </div>
        )}

        {conversations.map((conv) => (
          <div
            key={conv.id}
            className={`sidebar-item group p-2 ${
              currentConversation?.id === conv.id
                ? 'sidebar-item-active'
                : ''
            }`}
            title={collapsed ? conv.title : undefined}
          >
            <div className="w-full flex items-center gap-2 min-w-0">
              <button
                onClick={() => onSelectConversation(conv)}
                className="w-full flex items-center gap-2 min-w-0"
              >
                <div className="h-9 w-9 rounded-lg surface-strong flex items-center justify-center shrink-0">
                  <ChatBubbleLeftRightIcon className="h-4 w-4 text-[var(--accent)]" />
                </div>

                {!collapsed && (
                  <div className="flex-1 min-w-0 text-left">
                    <p className="text-sm font-medium truncate">
                      {conv.title}
                    </p>
                    <p className="text-xs text-muted">
                      {formatSidebarIST(conv.created_at)}
                    </p>
                  </div>
                )}
              </button>

              {!collapsed && (
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    if (
                      window.confirm(
                        'Delete this conversation and all its memories?'
                      )
                    ) {
                      onDeleteConversation(conv.id)
                    }
                  }}
                  className="opacity-0 group-hover:opacity-100 transition-opacity p-2 text-muted hover:text-red-400"
                  title="Delete conversation and all memories"
                >
                  <TrashIcon className="h-4 w-4" />
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="p-3 md:p-4 border-t">
        <div
          className={`surface-strong rounded-xl p-3 flex items-center gap-2 ${
            collapsed ? 'justify-center' : ''
          }`}
        >
          <UserCircleIcon className="h-6 w-6 text-[var(--accent)] shrink-0" />
          {!collapsed && (
            <div className="min-w-0">
              <p className="text-sm font-semibold truncate">{username}</p>
              <p className="text-xs text-muted">Signed in</p>
            </div>
          )}
          {collapsed && (
            <span className="text-xs font-semibold truncate max-w-10">
              {username}
            </span>
          )}
        </div>
      </div>
    </aside>
  )
}

export default Sidebar
