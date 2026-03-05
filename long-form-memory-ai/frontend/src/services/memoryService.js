import api from './api'

export const memoryService = {
  getMemories: async (memoryType = null) => {
    const params = {}
    if (memoryType) {
      params.memory_type = memoryType
    }

    const response = await api.get('/memory/', { params })
    return response.data
  }
}
