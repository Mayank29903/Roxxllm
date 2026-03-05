import api from './api'

export const memoryService = {
  /**
   * Fetch all memories for the current user
   * @param {string|null} memoryType - Optional filter by type (e.g., 'fact', 'preference')
   */
  getMemories: async (memoryType = null) => {
    const params = {}
    if (memoryType) {
      params.memory_type = memoryType
    }

    try {
      const response = await api.get('/memory/', { params })
      return Array.isArray(response.data) ? response.data : (response.data.memories || [])
    } catch (error) {
      if (error?.response?.status === 404) {
        const fallback = await api.get('/memory/memory/', { params })
        return Array.isArray(fallback.data) ? fallback.data : (fallback.data.memories || [])
      }
      console.error('Error fetching memories:', error)
      throw error
    }
  },

  /**
   * Delete a specific memory
   * @param {string} memoryId 
   */
  deleteMemory: async (memoryId) => {
    try {
      await api.delete(`/memory/${memoryId}`)
      return true
    } catch (error) {
      console.error('Error deleting memory:', error)
      throw error
    }
  }
}
