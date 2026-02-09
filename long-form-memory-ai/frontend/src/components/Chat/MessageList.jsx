import React from 'react'
import { UserCircleIcon, CpuChipIcon } from '@heroicons/react/24/solid'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

const MessageList = ({ messages, streamingMessage, isLoading }) => {
  return (
    <div className="flex-1 overflow-y-auto bg-gray-50 p-4 space-y-4">
      {messages.length === 0 && !streamingMessage && (
        <div className="flex flex-col items-center justify-center h-full text-gray-400">
          <CpuChipIcon className="h-16 w-16 mb-4 text-primary-200" />
          <p className="text-lg font-medium">Start a conversation</p>
          <p className="text-sm">Your AI assistant remembers context across 1000+ turns</p>
        </div>
      )}

      {messages.map((message, index) => (
        <div
          key={message.id || index}
          className={`max-w-3xl mx-auto p-4 rounded-lg shadow-sm ${
            message.role === 'user' 
              ? 'bg-primary-50 border-l-4 border-primary-500' 
              : 'bg-white border-l-4 border-gray-300'
          }`}
        >
          <div className="flex items-start space-x-3">
            <div className="flex-shrink-0">
              {message.role === 'user' ? (
                <UserCircleIcon className="h-8 w-8 text-primary-600" />
              ) : (
                <CpuChipIcon className="h-8 w-8 text-gray-600" />
              )}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm font-medium text-gray-900 capitalize">
                  {message.role === 'user' ? 'You' : 'Assistant'}
                </span>
                <span className="text-xs text-gray-500">
                  Turn {message.turn_number}
                </span>
              </div>
              <div className="prose prose-sm max-w-none text-gray-800">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {message.content}
                </ReactMarkdown>
              </div>
              
              {/* Memory indicator */}
              {message.active_memories && message.active_memories.length > 0 && (
                <div className="mt-2 flex items-center space-x-2">
                  <span className="text-xs text-amber-600 font-medium bg-amber-100 px-2 py-1 rounded-full">
                    💡 Used {message.active_memories.length} memories
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
      ))}

      {/* Streaming message */}
      {streamingMessage && (
        <div className="max-w-3xl mx-auto p-4 bg-white border-l-4 border-gray-300 rounded-lg shadow-sm">
          <div className="flex items-start space-x-3">
            <CpuChipIcon className="h-8 w-8 text-gray-600 flex-shrink-0" />
            <div className="flex-1">
              <div className="prose prose-sm max-w-none text-gray-800">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {streamingMessage}
                </ReactMarkdown>
              </div>
              <span className="inline-block w-2 h-4 bg-primary-500 ml-1 animate-pulse"></span>
            </div>
          </div>
        </div>
      )}

      {isLoading && !streamingMessage && (
        <div className="flex items-center justify-center py-4">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        </div>
      )}
    </div>
  )
}

export default MessageList