import React, { memo, useEffect, useMemo, useRef, useState } from 'react'
import { SparklesIcon } from '@heroicons/react/24/solid'
import { CheckIcon, ClipboardDocumentIcon } from '@heroicons/react/24/outline'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { formatISTDateTime, formatNowISTDateTime } from '../../utils/time'

const WELCOME_HEADLINE = 'Memory Workspace'
const WELCOME_TITLE = 'Start a High-Context Session'
const WELCOME_SUBTITLE = 'Share once and chat naturally. We remember important details across your conversations.'
const STREAM_TYPE_INTERVAL_MS = 18

const copyToClipboard = async (text) => {
  if (!text) return false

  try {
    if (navigator?.clipboard?.writeText) {
      await navigator.clipboard.writeText(text)
      return true
    }
  } catch {
    // Fallback path handled below.
  }

  try {
    const textarea = document.createElement('textarea')
    textarea.value = text
    textarea.style.position = 'fixed'
    textarea.style.opacity = '0'
    document.body.appendChild(textarea)
    textarea.focus()
    textarea.select()
    const ok = document.execCommand('copy')
    document.body.removeChild(textarea)
    return ok
  } catch {
    return false
  }
}

const EmptyState = ({ typing }) => (
  <div className="h-full flex items-center justify-center px-4">
    <div className="inline-block max-w-[min(92%,58rem)] surface-panel rounded-3xl p-8 sm:p-12 border border-[var(--border-soft)]">
      <div className="flex items-center gap-3">
        <div className="h-14 w-14 rounded-2xl surface-strong flex items-center justify-center glow-ring">
          <SparklesIcon className="h-7 w-7 text-[var(--accent)]" />
        </div>
        <div>
          <p className="text-xs uppercase tracking-[0.22em] text-muted min-h-4">{typing.headline}</p>
          <h2 className="text-3xl sm:text-4xl font-semibold mt-1 min-h-12">{typing.title}</h2>
        </div>
      </div>

      <p className="mt-7 text-base sm:text-lg text-secondary leading-8 min-h-12">
        {typing.subtitle}
        {typing.isTyping && (
          <span className="inline-block h-5 w-1.5 ml-1 align-middle bg-[var(--accent)] animate-pulse rounded-sm" />
        )}
      </p>

      <div className="mt-8 flex flex-wrap gap-2">
        <span className="surface-strong rounded-full px-4 py-2 text-sm">Plan my day</span>
        <span className="surface-strong rounded-full px-4 py-2 text-sm">Summarize my last task</span>
        <span className="surface-strong rounded-full px-4 py-2 text-sm">Remember my preferences</span>
      </div>
    </div>
  </div>
)

const InitialBadge = ({ label }) => (
  <div className="h-8 w-8 rounded-full surface-strong flex items-center justify-center text-xs font-semibold text-[var(--accent)] shrink-0">
    {label}
  </div>
)

const ThinkingIndicator = () => (
  <article className="chat-row chat-row-assistant">
    <div className="flex items-start gap-3">
      <InitialBadge label="A" />
      <div className="min-w-0 flex-1">
        <div className="flex items-center justify-start mb-2">
          <span className="text-xs text-muted">{formatNowISTDateTime()}</span>
        </div>
        <div className="inline-flex items-center gap-2 rounded-2xl surface-panel px-4 py-2.5">
          <span className="text-sm font-medium text-secondary animate-pulse">Thinking</span>
          <span className="inline-flex items-center gap-1" aria-hidden="true">
            <span className="h-1.5 w-1.5 rounded-full bg-[var(--accent)] animate-pulse [animation-delay:0ms]" />
            <span className="h-1.5 w-1.5 rounded-full bg-[var(--accent)] animate-pulse [animation-delay:180ms]" />
            <span className="h-1.5 w-1.5 rounded-full bg-[var(--accent)] animate-pulse [animation-delay:360ms]" />
          </span>
        </div>
      </div>
    </div>
  </article>
)

const MessageCard = memo(({ message, userInitial }) => {
  const isUser = message.role === 'user'
  const [isCopied, setIsCopied] = useState(false)
  const copiedTimerRef = useRef(null)

  useEffect(() => () => {
    if (copiedTimerRef.current) {
      window.clearTimeout(copiedTimerRef.current)
      copiedTimerRef.current = null
    }
  }, [])

  const handleCopy = async () => {
    const copied = await copyToClipboard(message.content)
    if (!copied) return

    setIsCopied(true)
    if (copiedTimerRef.current) {
      window.clearTimeout(copiedTimerRef.current)
    }
    copiedTimerRef.current = window.setTimeout(() => {
      setIsCopied(false)
      copiedTimerRef.current = null
    }, 1200)
  }

  return (
    <article className={`chat-row ${isUser ? 'chat-row-user' : 'chat-row-assistant'}`}>
      <div className={`flex items-start gap-3 ${isUser ? 'flex-row-reverse' : ''}`}>
        <InitialBadge label={isUser ? userInitial : 'A'} />
        <div className="min-w-0 flex-1">
          <div className={`flex items-center gap-2 mb-2 ${isUser ? 'justify-end' : 'justify-start'}`}>
            <span className="text-xs text-muted">{formatISTDateTime(message.created_at)}</span>
          </div>

          <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
            <div className={`message-bubble-wrap ${isUser ? 'message-bubble-wrap-user' : 'message-bubble-wrap-ai'}`}>
              <div className={`message-bubble ${isUser ? 'message-bubble-user' : 'message-bubble-ai'}`}>
                <div
                  className={`message-markdown prose prose-sm sm:prose-base max-w-none leading-7 text-[var(--text-primary)] prose-headings:text-[var(--text-primary)] prose-strong:text-[var(--text-primary)] prose-p:text-[var(--text-primary)] prose-li:text-[var(--text-primary)] prose-code:text-[var(--text-primary)] ${
                    isUser ? 'text-right' : 'text-left'
                  }`}
                >
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {message.content}
                  </ReactMarkdown>
                </div>
              </div>

              <button
                type="button"
                onClick={handleCopy}
                className={`bubble-copy-btn bubble-copy-btn-anchored ${isUser ? 'bubble-copy-btn-user' : 'bubble-copy-btn-ai'}`}
                data-copied={isCopied ? 'true' : 'false'}
                title={isCopied ? 'Copied' : 'Copy message'}
                aria-label={isCopied ? 'Copied' : 'Copy message'}
              >
                {isCopied ? (
                  <CheckIcon className="h-3.5 w-3.5" />
                ) : (
                  <ClipboardDocumentIcon className="h-3.5 w-3.5" />
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    </article>
  )
})

const MessageList = ({ messages, streamingMessage, isLoading, scrollContainerRef, userInitial = 'U' }) => {
  const [typing, setTyping] = useState({
    headline: '',
    title: '',
    subtitle: '',
    isTyping: false
  })
  const [animatedStreamingMessage, setAnimatedStreamingMessage] = useState('')
  const streamTargetRef = useRef('')
  const streamTimerRef = useRef(null)
  const displayedLengthRef = useRef(0)

  useEffect(() => {
    if (messages.length > 0 || streamingMessage) {
      return undefined
    }

    const steps = [
      { key: 'headline', text: WELCOME_HEADLINE, delay: 28 },
      { key: 'title', text: WELCOME_TITLE, delay: 20 },
      { key: 'subtitle', text: WELCOME_SUBTITLE, delay: 18 }
    ]

    const reset = { headline: '', title: '', subtitle: '', isTyping: true }
    let timeoutId = null
    let stepIndex = 0
    let charIndex = 0

    const tick = () => {
      if (stepIndex >= steps.length) {
        setTyping((prev) => ({ ...prev, isTyping: false }))
        return
      }

      const current = steps[stepIndex]
      const activeText = current.text.slice(0, charIndex + 1)
      setTyping((prev) => ({ ...prev, [current.key]: activeText, isTyping: true }))
      charIndex += 1

      if (charIndex >= current.text.length) {
        stepIndex += 1
        charIndex = 0
        timeoutId = window.setTimeout(tick, 160)
        return
      }

      timeoutId = window.setTimeout(tick, current.delay)
    }

    timeoutId = window.setTimeout(() => {
      setTyping(reset)
      tick()
    }, 180)

    return () => {
      if (timeoutId) {
        window.clearTimeout(timeoutId)
      }
    }
  }, [messages.length, streamingMessage])

  useEffect(() => {
    streamTargetRef.current = streamingMessage || ''

    if (!streamTargetRef.current) {
      if (streamTimerRef.current) {
        window.clearInterval(streamTimerRef.current)
        streamTimerRef.current = null
      }
      displayedLengthRef.current = 0
      setAnimatedStreamingMessage('')
      return undefined
    }

    if (displayedLengthRef.current > streamTargetRef.current.length) {
      displayedLengthRef.current = streamTargetRef.current.length
      setAnimatedStreamingMessage(
        streamTargetRef.current.slice(0, displayedLengthRef.current)
      )
    }

    const tick = () => {
      const target = streamTargetRef.current
      if (!target) return
      if (displayedLengthRef.current >= target.length) return

      displayedLengthRef.current += 1
      setAnimatedStreamingMessage(target.slice(0, displayedLengthRef.current))
    }

    if (!streamTimerRef.current) {
      tick()
      streamTimerRef.current = window.setInterval(tick, STREAM_TYPE_INTERVAL_MS)
    }

    return undefined
  }, [streamingMessage])

  useEffect(() => () => {
    if (streamTimerRef.current) {
      window.clearInterval(streamTimerRef.current)
      streamTimerRef.current = null
    }
  }, [])

  const renderedMessages = useMemo(
    () => messages.map((message, index) => (
      <MessageCard key={message.id || index} message={message} userInitial={userInitial} />
    )),
    [messages, userInitial]
  )

  const liveStreamingText = animatedStreamingMessage

  return (
    <div ref={scrollContainerRef} className="chat-message-area flex-1 overflow-y-auto soft-scroll px-3 sm:px-5 py-5">
      {messages.length === 0 && !streamingMessage && <EmptyState typing={typing} />}

      <div className="max-w-5xl mx-auto space-y-4">
        {renderedMessages}

        {isLoading && liveStreamingText && (
          <article className="chat-row chat-row-assistant">
            <div className="flex items-start gap-3">
              <InitialBadge label="A" />
              <div className="min-w-0 flex-1">
                <div className="flex items-center justify-start mb-2">
                  <span className="text-xs text-muted">{formatNowISTDateTime()}</span>
                </div>
                <div className="flex justify-start">
                  <div className="message-bubble message-bubble-ai">
                    <div className="whitespace-pre-wrap leading-7 text-[var(--text-primary)]">
                      {liveStreamingText}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </article>
        )}

        {isLoading && !streamingMessage && <ThinkingIndicator />}
      </div>
    </div>
  )
}

export default MessageList
