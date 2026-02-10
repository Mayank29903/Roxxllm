import api from './api'

export const chatService = {
  getConversations: async () => {
    const response = await api.get('/chat/conversations')
    return response.data
  },

  createConversation: async (title = null) => {
    const response = await api.post('/chat/conversations', { title })
    return response.data
  },

  getMessages: async (conversationId) => {
    const response = await api.get(`/chat/conversations/${conversationId}/messages`)
    return response.data
  },

  sendMessage: async (conversationId, content, stream = false) => {
    const response = await api.post('/chat/send', {
      conversation_id: conversationId,
      content,
      stream
    })
    return response.data
  },

  sendMessageStream: async (conversationId, content, onChunk) => {
    const response = await fetch('http://localhost:8000/chat/send', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify({
        conversation_id: conversationId,
        content,
        stream: true
      })
    })

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let fullMessage = ''
    let finalData = null

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const chunk = decoder.decode(value)
      const lines = chunk.split('\n')

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6)
          if (data === '[DONE]') continue
          
          try {
            const parsed = JSON.parse(data)
            if (parsed.type === 'chunk') {
              fullMessage += parsed.content
              onChunk(parsed.content)
            } else if (parsed.type === 'complete') {
              finalData = parsed
            }
          } catch (e) {
            console.error('Parse error:', e)
          }
        }
      }
    }

    return finalData || { message: { content: fullMessage } }
  },

  deleteConversation: async (conversationId) => {
    const response = await api.delete(`/chat/conversations/${conversationId}`)
    return response.data
  }
}