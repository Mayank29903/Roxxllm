import React from 'react'
import { PlusIcon, ChatBubbleLeftIcon, TrashIcon, XMarkIcon } from '@heroicons/react/24/outline'

const Sidebar = ({ conversations, currentConversation, onSelectConversation, onNewChat, onDeleteConversation }) => {
  return (
    <div className="w-64 bg-gray-900 text-white flex flex-col h-full">
      <div className="p-4">
        <button
          onClick={onNewChat}
          className="w-full flex items-center justify-center space-x-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg px-4 py-3 transition-colors"
        >
          <PlusIcon className="h-5 w-5" />
          <span>New Chat</span>
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-3 space-y-1">
        <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2 px-3">
          Recent Conversations
        </div>
        {conversations.map((conv) => (
          <div
            key={conv.id}
            className={`w-full flex items-center space-x-3 px-3 py-3 rounded-lg transition-colors group ${
              currentConversation?.id === conv.id
                ? 'bg-gray-800 text-white'
                : 'text-gray-300 hover:bg-gray-800'
            }`}
          >
            <button
              onClick={() => onSelectConversation(conv)}
              className="flex items-center space-x-3 flex-1 min-w-0"
            >
              <ChatBubbleLeftIcon className="h-5 w-5 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">
                  {conv.title}
                </p>
                <p className="text-xs text-gray-500">
                  {conv.turn_count || 0} turns
                </p>
              </div>
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation()
                if (window.confirm('Delete this conversation and all its memories?')) {
                  onDeleteConversation(conv.id)
                }
              }}
              className="opacity-0 group-hover:opacity-100 p-1 hover:bg-red-600 rounded transition-all"
              title="Delete conversation and all memories"
            >
              <TrashIcon className="h-4 w-4" />
            </button>
          </div>
        ))}
      </div>

      <div className="p-4 border-t border-gray-800">
        <div className="text-xs text-gray-400">
          <p>Long-Form Memory System</p>
          <p>Retains context across 1000+ turns</p>
        </div>
      </div>
    </div>
  )
}

export default Sidebar