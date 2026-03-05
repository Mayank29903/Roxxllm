import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { FaBrain } from 'react-icons/fa'
import { formatISTDateTime } from '../utils/time'
import { memoryService } from '../services/memoryService'

const TYPE_STYLES = {
  preference: 'bg-emerald-500/12 text-emerald-700',
  fact: 'bg-sky-500/12 text-sky-700',
  commitment: 'bg-amber-500/12 text-amber-700',
  instruction: 'bg-violet-500/12 text-violet-700',
  entity: 'bg-rose-500/12 text-rose-700'
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
      setError(err?.response?.data?.detail || 'Failed to load memories')
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    loadMemories()
  }, [loadMemories])

  const sortedMemories = useMemo(() => {
    return [...memories].sort(
      (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    )
  }, [memories])

  return (
    <div className="min-h-screen app-shell p-4 sm:p-6 lg:p-8">
      <div className="max-w-6xl mx-auto">
        <div className="surface-panel rounded-2xl p-5 sm:p-6">
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-3 min-w-0">
              <div className="h-11 w-11 rounded-xl surface-strong flex items-center justify-center">
                <FaBrain className="h-5 w-5 text-[var(--accent)]" />
              </div>
              <div className="min-w-0">
                <h1 className="text-2xl sm:text-3xl font-semibold truncate">Memory Dashboard</h1>
                <p className="text-sm text-secondary">
                  Saved memories: {sortedMemories.length}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={loadMemories}
                className="neutral-button px-4 py-2 text-sm"
              >
                Refresh
              </button>
              <Link
                to="/chat"
                className="neutral-button inline-flex items-center gap-2 px-4 py-2 text-sm"
              >
                Back to Chat
              </Link>
            </div>
          </div>
        </div>

        {isLoading && (
          <div className="mt-5 surface-panel rounded-2xl p-6">
            <p className="text-sm text-secondary">Loading memories...</p>
          </div>
        )}

        {!isLoading && error && (
          <div className="mt-5 surface-panel rounded-2xl p-6 border border-red-300/40">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        {!isLoading && !error && sortedMemories.length === 0 && (
          <div className="mt-5 surface-panel rounded-2xl p-6">
            <p className="text-sm text-secondary">
              No memories found yet. Chat for a bit and ask the assistant to remember key details.
            </p>
          </div>
        )}

        {!isLoading && !error && sortedMemories.length > 0 && (
          <div className="mt-5 grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {sortedMemories.map((memory) => (
              <article key={memory.id} className="surface-panel rounded-2xl p-5">
                <div className="flex items-center justify-between gap-2">
                  <span
                    className={`text-xs font-semibold px-2.5 py-1 rounded-full ${
                      TYPE_STYLES[memory.type] || 'bg-gray-500/10 text-gray-700'
                    }`}
                  >
                    {memory.type || 'memory'}
                  </span>
                  <span className="text-xs text-secondary">
                    {memory.importance != null
                      ? `${Math.round(Number(memory.importance) * 100)}%`
                      : 'N/A'}
                  </span>
                </div>

                <h3 className="mt-4 text-sm font-semibold text-secondary">
                  {memory.key || 'Detail'}
                </h3>
                <p className="mt-1 text-sm leading-6">{memory.value || memory.content || '-'}</p>

                <div className="mt-4 pt-3 border-t border-[var(--border-soft)]">
                  <p className="text-xs text-secondary">
                    Created: {memory.created_at ? formatISTDateTime(memory.created_at) : 'Unknown'}
                  </p>
                </div>
              </article>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default MemoryDashboard
