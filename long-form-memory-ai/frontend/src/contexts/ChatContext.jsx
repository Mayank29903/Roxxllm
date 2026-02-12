/* eslint-disable react-refresh/only-export-components */
import React, { createContext, useState, useCallback } from 'react'
import { chatService } from '../services/chatService'

export const ChatContext = createContext(null)
const ACTIVE_CONVERSATION_STORAGE_KEY = 'activeConversationId'
const CONVERSATION_TITLE_CACHE_KEY = 'conversationTitleCache'

const isPlaceholderConversationTitle = (title) =>
  !title || title.trim() === '' || title === 'New Conversation'

const readConversationTitleCache = () => {
  try {
    const raw = localStorage.getItem(CONVERSATION_TITLE_CACHE_KEY)
    const parsed = raw ? JSON.parse(raw) : {}
    return parsed && typeof parsed === 'object' ? parsed : {}
  } catch {
    return {}
  }
}

const writeConversationTitleCache = (cache) => {
  try {
    localStorage.setItem(CONVERSATION_TITLE_CACHE_KEY, JSON.stringify(cache))
  } catch {
    // Ignore storage write failures
  }
}

const cacheConversationTitle = (conversationId, title) => {
  if (!conversationId || isPlaceholderConversationTitle(title)) return
  const cache = readConversationTitleCache()
  if (cache[conversationId] === title) return
  cache[conversationId] = title
  writeConversationTitleCache(cache)
}

const removeConversationTitleFromCache = (conversationId) => {
  if (!conversationId) return
  const cache = readConversationTitleCache()
  if (!(conversationId in cache)) return
  delete cache[conversationId]
  writeConversationTitleCache(cache)
}

const applyCachedConversationTitles = (conversations = []) => {
  const cache = readConversationTitleCache()
  let cacheChanged = false

  const merged = conversations.map((conv) => {
    if (!conv?.id) return conv

    if (isPlaceholderConversationTitle(conv.title) && cache[conv.id]) {
      return { ...conv, title: cache[conv.id] }
    }

    if (!isPlaceholderConversationTitle(conv.title) && cache[conv.id] !== conv.title) {
      cache[conv.id] = conv.title
      cacheChanged = true
    }

    return conv
  })

  if (cacheChanged) {
    writeConversationTitleCache(cache)
  }

  return merged
}

const deriveConversationTitle = (content) => {
  const cleaned = (content || '').trim().replace(/\s+/g, ' ')
  if (!cleaned) return 'New Conversation'

  const maxLength = 60
  if (cleaned.length <= maxLength) return cleaned

  const truncated = cleaned.slice(0, maxLength)
  const lastSpace = truncated.lastIndexOf(' ')
  const readable = lastSpace > 0 ? truncated.slice(0, lastSpace) : truncated
  return `${readable}...`
}

export const ChatProvider = ({ children }) => {
  const [conversations, setConversations] = useState([])
  const [currentConversation, setCurrentConversation] = useState(null)
  const [messages, setMessages] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [streamingMessage, setStreamingMessage] = useState('')

  const loadConversations = useCallback(async () => {
    try {
      const data = await chatService.getConversations()
      const hydrated = applyCachedConversationTitles(data)
      setConversations(hydrated)
      return hydrated
    } catch (err) {
      console.error('Failed to load conversations:', err)
      return []
    }
  }, [])

  const createConversation = useCallback(async (title = null) => {
    try {
      const data = await chatService.createConversation(title)
      if (data?.id && !isPlaceholderConversationTitle(data.title)) {
        cacheConversationTitle(data.id, data.title)
      }
      setConversations(prev => [data, ...prev])
      setCurrentConversation(data)
      setMessages([])
      localStorage.setItem(ACTIVE_CONVERSATION_STORAGE_KEY, data.id)
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
    localStorage.setItem(ACTIVE_CONVERSATION_STORAGE_KEY, conversation.id)
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

      if (localStorage.getItem(ACTIVE_CONVERSATION_STORAGE_KEY) === conversationId) {
        localStorage.removeItem(ACTIVE_CONVERSATION_STORAGE_KEY)
      }

      removeConversationTitleFromCache(conversationId)
      
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
    const defaultFirstTitle = deriveConversationTitle(content)
    let resolvedConversationTitle = activeConversation.title

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
        setStreamingMessage('')
        const returnedTitle = response?.conversation?.title
        const nextConversationTitle =
          returnedTitle ||
          ((activeConversation.turn_count || 0) === 0
            ? defaultFirstTitle
            : activeConversation.title)
        resolvedConversationTitle = nextConversationTitle
        setMessages(prev => [...prev, {
          id: Date.now() + 1,
          role: 'assistant',
          content: response.message.content,
          turn_number: response.message.turn_number,
          created_at: assistantCreatedAt,
          active_memories: response.memory_metadata?.active_memories || []
        }])

        setCurrentConversation(prev => {
          if (!prev || prev.id !== conversationId) return prev
          return { ...prev, title: nextConversationTitle }
        })
      } else {
        // Non-streaming response
        const response = await chatService.sendMessage(conversationId, content)
        const assistantCreatedAt = response?.message?.created_at || new Date().toISOString()
        const returnedTitle = response?.conversation?.title
        const nextConversationTitle =
          returnedTitle ||
          ((activeConversation.turn_count || 0) === 0
            ? defaultFirstTitle
            : activeConversation.title)
        resolvedConversationTitle = nextConversationTitle
        setMessages(prev => [...prev, {
          id: response.message.id,
          role: 'assistant',
          content: response.message.content,
          turn_number: response.message.turn_number,
          created_at: assistantCreatedAt,
          active_memories: response.memory_metadata?.active_memories || []
        }])

        setCurrentConversation(prev => {
          if (!prev || prev.id !== conversationId) return prev
          return { ...prev, title: nextConversationTitle }
        })
      }

      if (!isPlaceholderConversationTitle(resolvedConversationTitle)) {
        cacheConversationTitle(conversationId, resolvedConversationTitle)
      }

      // Update conversation turn count
      setCurrentConversation(prev => {
        if (!prev || prev.id !== conversationId) return prev
        const nowIso = new Date().toISOString()
        const shouldSetTitle =
          (prev.turn_count || 0) === 0 &&
          (!prev.title || prev.title === 'New Conversation')
        return {
          ...prev,
          title: shouldSetTitle
            ? defaultFirstTitle
            : (resolvedConversationTitle || prev.title),
          turn_count: (prev.turn_count || 0) + 1,
          updated_at: nowIso
        }
      })

      // Update conversation in the list
      setConversations(prev => {
        const nowIso = new Date().toISOString()
        const exists = prev.some(conv => conv.id === conversationId)
        const preferredTitle = !isPlaceholderConversationTitle(resolvedConversationTitle)
          ? resolvedConversationTitle
          : defaultFirstTitle
        if (!exists) {
          return [{ ...activeConversation, title: preferredTitle, turn_count: 1, updated_at: nowIso }, ...prev]
        }

        return prev.map(conv =>
          conv.id === conversationId
            ? {
                ...conv,
                title: !isPlaceholderConversationTitle(resolvedConversationTitle)
                  ? resolvedConversationTitle
                  : (
                    (conv.turn_count || 0) === 0 && isPlaceholderConversationTitle(conv.title)
                      ? defaultFirstTitle
                      : conv.title
                  ),
                turn_count: (conv.turn_count || 0) + 1,
                updated_at: nowIso
              }
            : conv
        )
      })

    } catch (err) {
      console.error('Failed to send message:', err)
      setStreamingMessage('')
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
