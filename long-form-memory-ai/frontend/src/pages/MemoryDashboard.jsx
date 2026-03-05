import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { FaBrain, FaSync, FaArrowLeft, FaExclamationCircle } from 'react-icons/fa'
import { formatISTDateTime } from '../utils/time'
import { memoryService } from '../services/memoryService'

// Styling maps for memory types
const TYPE_STYLES = {
  preference: 'bg-emerald-500/10 text-emerald-600 border-emerald-500/20',
  fact: 'bg-sky-500/10 text-sky-600 border-sky-500/20',
  commitment: 'bg-amber-500/10 text-amber-600 border-amber-500/20',
  instruction: 'bg-violet-500/10 text-violet-600 border-violet-500/20',
  entity: 'bg-rose-500/10 text-rose-600 border-rose-500/20',
  default: 'bg-gray-500/10 text-gray-600 border-gray-500/20'
}

const normalizeText = (value) => String(value || '').trim().toLowerCase().replace(/\s+/g, ' ')

const isUsefulMemory = (memory) => {
  const type = normalizeText(memory.type || memory.memory_type)
  const key = normalizeText(memory.key || '')
  const value = normalizeText(memory.value || memory.content || '')
  const confidence = Number(memory.confidence ?? 0)
  const importance = Number(memory.importance ?? memory.importance_score ?? 0)

  if (!type || !key || !value) return false
  if (confidence < 0.6 || importance < 0.55) return false

  const noisyTypes = new Set(['temporary_state'])
  if (noisyTypes.has(type)) return false

  const taskMarkers = [
    'main function',
    'full code',
    'single file',
    'response format',
    'output format',
    'this task',
    'this question',
    'factorial',
    'c++',
    'cpp',
    'python code'
  ]
  const blob = `${type} ${key} ${value}`
  if (taskMarkers.some((marker) => blob.includes(marker))) return false

  return true
}

const MemoryDashboard = () => {
  const [memories, setMemories] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  const loadMemories = useCallback(async () => {
    setIsLoading(true)
    setError('')
    try {
      const data = await memoryService.getMemories()
      setMemories(Array.isArray(data) ? data : [])
    } catch (err) {
      console.error('Failed to load memories:', err)
      const errorMessage = err?.response?.data?.detail || 'Failed to connect to memory service'
      setError(errorMessage)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    loadMemories()
  }, [loadMemories])

  const visibleMemories = useMemo(() => {
    const filtered = memories.filter(isUsefulMemory)
    const deduped = new Map()

    filtered.forEach((memory) => {
      const type = normalizeText(memory.type || memory.memory_type)
      const value = normalizeText(memory.value || memory.content || '')
      const signature = `${type}|${value}`
      const existing = deduped.get(signature)
      const score = Number(memory.importance ?? memory.importance_score ?? 0) + Number(memory.confidence ?? 0)

      if (!existing) {
        deduped.set(signature, memory)
        return
      }

      const existingScore = Number(existing.importance ?? existing.importance_score ?? 0) + Number(existing.confidence ?? 0)
      if (score > existingScore) {
        deduped.set(signature, memory)
      }
    })

    return [...deduped.values()].sort(
      (a, b) => new Date(b.created_at || b.createdAt || 0).getTime() - new Date(a.created_at || a.createdAt || 0).getTime()
    )
  }, [memories])

  // Helper to safely get type
  const getMemoryType = (memory) => {
    return (memory.type || memory.memory_type || 'default').toLowerCase()
  }

  // Helper to safely get content
  const getMemoryContent = (memory) => {
    return memory.value || memory.content || memory.text || 'No content available'
  }

  // Helper to safely get key/summary
  const getMemoryKey = (memory) => {
    return memory.key || memory.summary || memory.topic || 'Memory Detail'
  }

  return (
    <div className="min-h-screen app-shell p-4 sm:p-6 lg:p-8 transition-colors duration-300">
      <div className="max-w-7xl mx-auto">
        
        {/* Header Section */}
        <div className="surface-panel rounded-2xl p-5 sm:p-6 mb-6 shadow-sm border border-[var(--border-soft)]">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="flex items-center gap-4 min-w-0">
              <div className="h-12 w-12 rounded-xl bg-[var(--accent)]/10 flex items-center justify-center shrink-0">
                <FaBrain className="h-6 w-6 text-[var(--accent)]" />
              </div>
              <div className="min-w-0">
                <h1 className="text-2xl sm:text-3xl font-bold text-[var(--text-primary)] truncate">
                  Memory Dashboard
                </h1>
                <p className="text-sm text-[var(--text-secondary)] mt-1">
                  {isLoading ? 'Loading...' : `${visibleMemories.length} useful memories`}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2 w-full sm:w-auto">
              <button
                type="button"
                onClick={loadMemories}
                disabled={isLoading}
                className="flex-1 sm:flex-none neutral-button inline-flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-medium transition-all hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <FaSync className={isLoading ? 'animate-spin' : ''} />
                Refresh
              </button>
              <Link
                to="/chat"
                className="flex-1 sm:flex-none neutral-button inline-flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-medium transition-all hover:scale-105"
              >
                <FaArrowLeft />
                Back to Chat
              </Link>
            </div>
          </div>
        </div>

        {/* Loading State */}
        {isLoading && (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="surface-panel rounded-2xl p-6 animate-pulse">
                <div className="h-4 bg-[var(--border-soft)] rounded w-1/3 mb-4"></div>
                <div className="h-6 bg-[var(--border-soft)] rounded w-3/4 mb-2"></div>
                <div className="h-4 bg-[var(--border-soft)] rounded w-full mb-2"></div>
                <div className="h-4 bg-[var(--border-soft)] rounded w-2/3"></div>
              </div>
            ))}
          </div>
        )}

        {/* Error State */}
        {!isLoading && error && (
          <div className="surface-panel rounded-2xl p-8 border border-red-500/20 bg-red-500/5">
            <div className="flex items-center gap-3 text-red-600 mb-2">
              <FaExclamationCircle className="text-xl" />
              <h3 className="font-semibold">Failed to Load Memories</h3>
            </div>
            <p className="text-sm text-red-500/80 mb-4">{error}</p>
            <button 
              onClick={loadMemories}
              className="text-sm font-medium text-red-600 hover:text-red-700 underline"
            >
              Try Again
            </button>
          </div>
        )}

        {/* Empty State */}
        {!isLoading && !error && visibleMemories.length === 0 && (
          <div className="surface-panel rounded-2xl p-12 text-center">
            <div className="inline-flex items-center justify-center h-20 w-20 rounded-full bg-[var(--bg-secondary)] mb-6">
              <FaBrain className="h-10 w-10 text-[var(--text-secondary)] opacity-50" />
            </div>
            <h3 className="text-xl font-semibold text-[var(--text-primary)] mb-2">
              No Memories Yet
            </h3>
            <p className="text-[var(--text-secondary)] max-w-md mx-auto mb-6">
              Memories are automatically extracted from your conversations. 
              Start chatting with the assistant to build your long-term memory bank.
            </p>
            <Link
              to="/chat"
              className="primary-button inline-flex items-center gap-2 px-6 py-3 rounded-xl font-medium"
            >
              Start Chatting
            </Link>
          </div>
        )}

        {/* Memories Grid */}
        {!isLoading && !error && visibleMemories.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {visibleMemories.map((memory) => {
              const type = getMemoryType(memory)
              const style = TYPE_STYLES[type] || TYPE_STYLES.default

              return (
                <article 
                  key={memory.id || memory.memory_id} 
                  className="surface-panel rounded-2xl p-5 hover:shadow-md transition-all duration-300 border border-[var(--border-soft)] group"
                >
                  <div className="flex items-start justify-between gap-3 mb-3">
                    <span className={`text-xs font-bold px-3 py-1 rounded-full border ${style} uppercase tracking-wider`}>
                      {type}
                    </span>
                    {memory.importance != null && (
                      <span className="text-xs font-medium text-[var(--text-secondary)] bg-[var(--bg-secondary)] px-2 py-1 rounded">
                        {Math.round(Number(memory.importance) * 100)}% Confidence
                      </span>
                    )}
                  </div>

                  <h3 className="text-sm font-bold text-[var(--text-primary)] mb-2 line-clamp-1">
                    {getMemoryKey(memory)}
                  </h3>
                  
                  <p className="text-sm text-[var(--text-secondary)] leading-relaxed line-clamp-3 mb-4">
                    {getMemoryContent(memory)}
                  </p>

                  <div className="pt-4 border-t border-[var(--border-soft)] flex items-center justify-between text-xs text-[var(--text-secondary)]">
                    <span>
                      {memory.created_at ? formatISTDateTime(memory.created_at) : 'Recently'}
                    </span>
                    {/* Optional: Add delete button here if needed */}
                  </div>
                </article>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}

export default MemoryDashboard
