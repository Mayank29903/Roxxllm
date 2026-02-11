/* eslint-disable react-refresh/only-export-components */
import React, { createContext, useState, useCallback } from 'react'
import { chatService } from '../services/chatService'

export const ChatContext = createContext(null)

export const ChatProvider = ({ children }) => {
  const [conversations, setConversations] = useState([])
  const [currentConversation, setCurrentConversation] = useState(null)
  const [messages, setMessages] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [streamingMessage, setStreamingMessage] = useState('')

  const loadConversations = useCallback(async () => {
    try {
      const data = await chatService.getConversations()
      setConversations(data)
    } catch (err) {
      console.error('Failed to load conversations:', err)
    }
  }, [])

  const createConversation = useCallback(async (title = null) => {
    try {
      const data = await chatService.createConversation(title)
      setConversations(prev => [data, ...prev])
      setCurrentConversation(data)
      setMessages([])
      return data
    } catch (err) {
      console.error('Failed to create conversation:', err)
      throw err
    }
  }, [])

  const loadMessages = useCallback(async (conversationId) => {
    try {
      const data = await chatService.getMessages(conversationId)
      setMessages(data)
      return data
    } catch (err) {
      console.error('Failed to load messages:', err)
      throw err
    }
  }, [])

  const selectConversation = useCallback(async (conversation) => {
    setCurrentConversation(conversation)
    await loadMessages(conversation.id)
  }, [loadMessages])

  const deleteConversation = useCallback(async (conversationId) => {
    try {
      await chatService.deleteConversation(conversationId)
      
      // Remove from list
      setConversations(prev => prev.filter(conv => conv.id !== conversationId))
      
      // If it was the current conversation, clear it
      if (currentConversation?.id === conversationId) {
        setCurrentConversation(null)
        setMessages([])
      }
      
      console.log('✅ Conversation and all memories deleted')
    } catch (err) {
      console.error('Failed to delete conversation:', err)
      throw err
    }
  }, [currentConversation])

  const sendMessage = useCallback(async (content, stream = true) => {
    let activeConversation = currentConversation
    if (!activeConversation) {
      activeConversation = await createConversation()
    }

    const conversationId = activeConversation.id
    const nextTurnNumber = (activeConversation.turn_count || 0) + 1

    setIsLoading(true)
    setStreamingMessage('')

    // Optimistically add user message
    const tempUserMessage = {
      id: Date.now(),
      role: 'user',
      content,
      turn_number: nextTurnNumber,
      created_at: new Date().toISOString()
    }
    setMessages(prev => [...prev, tempUserMessage])

    try {
      if (stream) {
        let chunkBuffer = ''
        let flushTimer = null

        const flushChunks = () => {
          if (chunkBuffer) {
            const buffered = chunkBuffer
            chunkBuffer = ''
            setStreamingMessage(prev => prev + buffered)
          }
        }

        const scheduleFlush = () => {
          if (flushTimer) return
          flushTimer = window.setTimeout(() => {
            flushTimer = null
            flushChunks()
          }, 26)
        }

        // Streaming response
        const response = await chatService.sendMessageStream(
          conversationId,
          content,
          (chunk) => {
            chunkBuffer += chunk
            scheduleFlush()
          }
        )
        if (flushTimer) {
          window.clearTimeout(flushTimer)
          flushTimer = null
        }
        flushChunks()

        // Add final assistant message
        const assistantCreatedAt = response?.message?.created_at || new Date().toISOString()
        setMessages(prev => [...prev, {
          id: Date.now() + 1,
          role: 'assistant',
          content: response.message.content,
          turn_number: response.message.turn_number,
          created_at: assistantCreatedAt,
          active_memories: response.memory_metadata?.active_memories || []
        }])
        
        setStreamingMessage('')
      } else {
        // Non-streaming response
        const response = await chatService.sendMessage(conversationId, content)
        const assistantCreatedAt = response?.message?.created_at || new Date().toISOString()
        setMessages(prev => [...prev, {
          id: response.message.id,
          role: 'assistant',
          content: response.message.content,
          turn_number: response.message.turn_number,
          created_at: assistantCreatedAt,
          active_memories: response.memory_metadata?.active_memories || []
        }])
      }

      // Update conversation turn count
      setCurrentConversation(prev => {
        if (!prev || prev.id !== conversationId) return prev
        const nowIso = new Date().toISOString()
        return {
          ...prev,
          turn_count: (prev.turn_count || 0) + 1,
          updated_at: nowIso
        }
      })

      // Update conversation in the list
      setConversations(prev => {
        const nowIso = new Date().toISOString()
        const exists = prev.some(conv => conv.id === conversationId)
        if (!exists) {
          return [{ ...activeConversation, turn_count: 1, updated_at: nowIso }, ...prev]
        }

        return prev.map(conv =>
          conv.id === conversationId
            ? { ...conv, turn_count: (conv.turn_count || 0) + 1, updated_at: nowIso }
            : conv
        )
      })

    } catch (err) {
      console.error('Failed to send message:', err)
      // Remove optimistic message on error
      setMessages(prev => prev.filter(m => m.id !== tempUserMessage.id))
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [currentConversation, createConversation])

  const value = {
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
    loadMessages
  }

  return (
    <ChatContext.Provider value={value}>
      {children}
    </ChatContext.Provider>
  )
}
