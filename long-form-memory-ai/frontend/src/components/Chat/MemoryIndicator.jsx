import React from 'react'
import { LightBulbIcon } from '@heroicons/react/24/outline'

const MemoryIndicator = ({ count, memories }) => {
  if (!count || count === 0) return null

  return (
    <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 mb-4">
      <div className="flex items-center space-x-2 mb-2">
        <LightBulbIcon className="h-5 w-5 text-amber-600" />
        <span className="text-sm font-medium text-amber-800">
          Active Memories ({count})
        </span>
      </div>
      <div className="space-y-1">
        {memories?.map((mem, idx) => (
          <div key={idx} className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800 border border-amber-200 mr-2">
            {mem.type}: {mem.content}
          </div>
        ))}
      </div>
    </div>
  )
}

export default MemoryIndicator