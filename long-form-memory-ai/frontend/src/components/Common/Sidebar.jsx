import React from 'react'
import {
  PlusIcon,
  ChatBubbleLeftRightIcon,
  TrashIcon,
  ChevronDoubleLeftIcon,
  ChevronDoubleRightIcon,
  SparklesIcon,
  UserCircleIcon,
  Cog6ToothIcon,
  ArrowRightOnRectangleIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline'
import { formatSidebarIST } from '../../utils/time'
import ConfirmDeleteModal from './ConfirmDeleteModal'
import useAuth from '../../hooks/useAuth'
import { authService } from '../../services/authService'

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
  const { logout } = useAuth();
  const username = user?.username || 'Guest';
  const [dropdownOpen, setDropdownOpen] = React.useState(false);
  const [deleteModalOpen, setDeleteModalOpen] = React.useState(false);
  const dropdownRef = React.useRef(null);

  React.useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setDropdownOpen(false);
      }
    }
    if (dropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    } else {
      document.removeEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [dropdownOpen]);

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
          className="neutral-button p-2 cursor-pointer"
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
          className="accent-button sidebar-new-chat w-full flex items-center justify-center gap-2 px-4 py-3 cursor-pointer"
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
                className="flex-1 flex items-center gap-2 min-w-0 cursor-pointer"
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
                className="sidebar-delete-btn p-2 ml-1 transition-opacity shrink-0 cursor-pointer"
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
          className={`surface-strong rounded-xl p-3 flex items-center gap-2 relative ${
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
          {/* Settings button and dropdown */}
          <div className="ml-auto relative" ref={dropdownRef}>
            <button
              onClick={() => setDropdownOpen((open) => !open)}
              className="p-2 rounded-md transition-colors hover:bg-neutral-800 group cursor-pointer"
              title="Settings"
            >
              <Cog6ToothIcon className="h-5 w-5 text-[var(--accent)] group-hover:text-white" />
            </button>
            {dropdownOpen && (
              <div className="absolute right-0 bottom-12 mb-2 w-48 bg-neutral-800 border border-neutral-700 rounded-md shadow-lg z-50">
                <button
                  onClick={logout}
                  className="flex items-center w-full px-4 py-2 text-neutral-200 hover:bg-neutral-700 transition-colors cursor-pointer"
                >
                  <ArrowRightOnRectangleIcon className="h-5 w-5 mr-2" /> Logout
                </button>
                <button
                  onClick={() => {
                    setDropdownOpen(false);
                    setDeleteModalOpen(true);
                  }}
                  className="flex items-center w-full px-4 py-2 mt-1 border-t border-neutral-700 text-red-400 hover:bg-red-900/30 transition-colors font-semibold justify-between cursor-pointer"
                >
                  <span className="flex items-center">
                    <ExclamationTriangleIcon className="h-5 w-5 mr-2" /> Delete Account
                  </span>
                  <span className="border border-red-400 rounded px-2 py-0.5 text-xs ml-2">Warning</span>
                </button>
              </div>
            )}
          </div>
        </div>
        <ConfirmDeleteModal
          open={deleteModalOpen}
          onClose={() => setDeleteModalOpen(false)}
          onConfirm={async () => {
            try {
              await authService.deleteAccount();
              setDeleteModalOpen(false);
              await logout();
            } catch (err) {
              alert('Failed to delete account. Please try again.');
            }
          }}
        />
      </div>
    </aside>
  )
}

export default Sidebar
