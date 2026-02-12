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
  onRequestDeleteConversation,
  onCloseMobile,
  onToggleCollapse,
  collapsed = false,
  className = '',
  user
}) => {
  const username = user?.username || 'Guest'

  return (
    <aside className={`sidebar-shell flex flex-col h-full ${className}`}>
      <div className={`p-3 md:p-4 flex items-center gap-2 ${collapsed ? 'justify-center' : 'justify-between'}`}>
        {!collapsed && (
          <div className="flex items-center gap-2 min-w-0">
            <div className="h-10 w-10 rounded-xl surface-strong flex items-center justify-center">
              <SparklesIcon className="h-5 w-5 text-[var(--accent)]" />
            </div>
            <div className="min-w-0">
              <p className="text-xs text-secondary uppercase tracking-wider">
                Conversations
              </p>
            </div>
          </div>
        )}

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
          className="accent-button sidebar-new-chat w-full flex items-center justify-center gap-2 px-4 py-3"
          title="Start a new conversation"
        >
          <PlusIcon className="h-5 w-5" />
          {!collapsed && <span className="font-medium">New Chat</span>}
        </button>
      </div>

      <div className="flex-1 overflow-y-auto soft-scroll px-2 md:px-3 space-y-1.5">
        {!collapsed && (
          <div className="px-2 py-1 text-xs font-semibold text-secondary uppercase tracking-[0.16em]">
            Your Chats
          </div>
        )}

        {conversations.map((conv) => (
          <div
            key={conv.id}
            className={`sidebar-item group ${
              currentConversation?.id === conv.id
                ? 'sidebar-item-active'
                : ''
            }`}
            title={collapsed ? conv.title : undefined}
          >
            <div className="w-full flex items-center gap-2 min-w-0">
              <button
                onClick={() => onSelectConversation(conv)}
                className="flex-1 flex items-center gap-2 min-w-0"
              >
                <div className="h-9 w-9 rounded-lg surface-strong flex items-center justify-center shrink-0">
                  <ChatBubbleLeftRightIcon className="h-4 w-4 text-[var(--accent)]" />
                </div>

                {!collapsed && (
                  <div className="flex-1 min-w-0 text-left">
                    <p className="text-sm font-semibold truncate">
                      {conv.title}
                    </p>
                    <p className="text-xs text-secondary">
                      {formatSidebarIST(conv.created_at)}
                    </p>
                  </div>
                )}
              </button>

              <button
                onClick={(e) => {
                  e.stopPropagation()
                  onRequestDeleteConversation(conv)
                }}
                className="sidebar-delete-btn p-2 ml-1 transition-opacity shrink-0"
                title="Delete conversation and all memories"
                aria-label={`Delete ${conv.title}`}
              >
                <TrashIcon className="h-4 w-4" />
              </button>
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
              <p className="text-xs sidebar-profile-meta">Signed in</p>
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
