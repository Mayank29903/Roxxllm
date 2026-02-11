import React, { memo, useEffect, useMemo, useRef, useState } from 'react'
import { SparklesIcon } from '@heroicons/react/24/solid'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { formatISTDateTime, formatNowISTDateTime } from '../../utils/time'

const WELCOME_HEADLINE = 'Memory Workspace'
const WELCOME_TITLE = 'Start a High-Context Session'
const WELCOME_SUBTITLE = 'Share once and chat naturally. We remember important details across your conversations.'
const STREAM_TYPE_INTERVAL_MS = 18

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

const MessageCard = memo(({ message, userInitial }) => {
  const isUser = message.role === 'user'

  return (
    <article className={`chat-row ${isUser ? 'chat-row-user' : 'chat-row-assistant'}`}>
      <div className={`flex items-start gap-3 ${isUser ? 'flex-row-reverse' : ''}`}>
        <InitialBadge label={isUser ? userInitial : 'A'} />
        <div className="min-w-0 flex-1">
          <div className={`flex items-center mb-2 ${isUser ? 'justify-end' : 'justify-start'}`}>
            <span className="text-xs text-muted">{formatISTDateTime(message.created_at)}</span>
          </div>
          <div
            className={`prose prose-sm sm:prose-base max-w-none leading-7 text-[var(--text-primary)] prose-headings:text-[var(--text-primary)] prose-strong:text-[var(--text-primary)] prose-p:text-[var(--text-primary)] prose-li:text-[var(--text-primary)] prose-code:text-[var(--text-primary)] ${
              isUser ? 'text-right' : 'text-left'
            }`}
          >
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {message.content}
            </ReactMarkdown>
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
        window.clearTimeout(streamTimerRef.current)
        streamTimerRef.current = null
      }
      displayedLengthRef.current = 0
      setAnimatedStreamingMessage('')
      return undefined
    }

    const tick = () => {
      const target = streamTargetRef.current
      if (!target) {
        streamTimerRef.current = null
        return
      }

      const currentLength = displayedLengthRef.current
      if (currentLength >= target.length) {
        streamTimerRef.current = null
        return
      }

      const remaining = target.length - currentLength
      const step =
        remaining > 120 ? 14
          : remaining > 80 ? 10
            : remaining > 40 ? 6
              : remaining > 20 ? 4
                : 2

      const nextLength = Math.min(target.length, currentLength + step)
      const nextText = target.slice(0, nextLength)

      displayedLengthRef.current = nextLength
      setAnimatedStreamingMessage(nextText)
      streamTimerRef.current = window.setTimeout(tick, STREAM_TYPE_INTERVAL_MS)
    }

    if (!streamTimerRef.current) {
      tick()
    }
  }, [streamingMessage])

  useEffect(() => () => {
    if (streamTimerRef.current) {
      window.clearTimeout(streamTimerRef.current)
      streamTimerRef.current = null
    }
  }, [])

  const renderedMessages = useMemo(
    () => messages.map((message, index) => (
      <MessageCard key={message.id || index} message={message} userInitial={userInitial} />
    )),
    [messages, userInitial]
  )

  const liveStreamingText = animatedStreamingMessage || streamingMessage

  return (
    <div ref={scrollContainerRef} className="flex-1 overflow-y-auto soft-scroll px-3 sm:px-5 py-5">
      {messages.length === 0 && !streamingMessage && <EmptyState typing={typing} />}

      <div className="max-w-5xl mx-auto space-y-4">
        {renderedMessages}

        {liveStreamingText && (
          <article className="chat-row chat-row-assistant">
            <div className="flex items-start gap-3">
              <InitialBadge label="A" />
              <div className="min-w-0 flex-1">
                <div className="flex items-center justify-start mb-2">
                  <span className="text-xs text-muted">{formatNowISTDateTime()}</span>
                </div>
                <div className="whitespace-pre-wrap leading-7 text-[var(--text-primary)]">
                  {liveStreamingText}
                  <span className="inline-block h-5 w-2 ml-1 align-middle bg-[var(--accent)] animate-pulse rounded-sm" />
                </div>
              </div>
            </div>
          </article>
        )}

        {isLoading && !streamingMessage && (
          <div className="py-8 flex items-center justify-center">
            <div className="h-8 w-8 rounded-full border-2 border-[var(--border-soft)] border-t-[var(--accent)] animate-spin" />
          </div>
        )}
      </div>
    </div>
  )
}

export default MessageList
