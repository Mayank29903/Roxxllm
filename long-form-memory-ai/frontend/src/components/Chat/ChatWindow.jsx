import React, { useEffect, useRef } from 'react'
import { PlusIcon } from '@heroicons/react/24/outline'
import useChat from '../../hooks/useChat'
import Sidebar from '../Common/Sidebar'
import MessageList from './MessageList'
import MessageInput from './MessageInput'

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
    sendMessage
  } = useChat()

  const messagesEndRef = useRef(null)

  useEffect(() => {
    loadConversations()
  }, [loadConversations])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamingMessage])

  const handleNewChat = async () => {
    await createConversation()
  }

  const handleSendMessage = async (content) => {
    await sendMessage(content, true)
  }

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <Sidebar
        conversations={conversations}
        currentConversation={currentConversation}
        onSelectConversation={selectConversation}
        onNewChat={handleNewChat}
        onDeleteConversation={deleteConversation}
      />

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col h-full">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold text-gray-900">
              {currentConversation?.title || 'New Conversation'}
            </h1>
            {currentConversation && (
              <p className="text-sm text-gray-500">
                Turn {currentConversation.turn_count || 0}
              </p>
            )}
          </div>
          <button
            onClick={handleNewChat}
            className="flex items-center space-x-2 bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-lg transition-colors"
          >
            <PlusIcon className="h-5 w-5" />
            <span>New Chat</span>
          </button>
        </div>

        {/* Messages */}
        <MessageList 
          messages={messages} 
          streamingMessage={streamingMessage}
          isLoading={isLoading}
        />

        {/* Input */}
        <MessageInput 
          onSend={handleSendMessage}
          isLoading={isLoading}
        />

        <div ref={messagesEndRef} />
      </div>
    </div>
  )
}

export default ChatWindow