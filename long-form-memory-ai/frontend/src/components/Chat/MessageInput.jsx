import React, { useState, useRef, useEffect } from 'react'
import { PaperAirplaneIcon } from '@heroicons/react/24/solid'

const MessageInput = ({ onSend, isLoading }) => {
  const [message, setMessage] = useState('')
  const textareaRef = useRef(null)

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`
    }
  }, [message])

  const handleSubmit = async (e) => {
    e.preventDefault()
    const trimmed = message.trim()
    if (!trimmed || isLoading) return

    setMessage('')
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }

    try {
      await onSend(trimmed)
    } catch (err) {
      setMessage(trimmed)
      console.error('Message send failed:', err)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  return (
    <footer className="px-3 sm:px-5 pb-4 sm:pb-5 pt-3">
      <form onSubmit={handleSubmit} className="max-w-5xl mx-auto">
        <div className="surface-panel rounded-3xl p-2 sm:p-3 flex items-end gap-2">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type your message..."
            className="input-field px-4 py-3 resize-none min-h-[50px] max-h-36 bg-transparent border-0 shadow-none focus:shadow-none"
            rows={1}
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={!message.trim() || isLoading}
            className="accent-button h-11 w-11 flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed shrink-0"
            aria-label="Send message"
          >
            <PaperAirplaneIcon className="h-5 w-5" />
          </button>
        </div>
      </form>
    </footer>
  )
}

export default MessageInput
