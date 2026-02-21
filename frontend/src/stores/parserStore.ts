import { create } from 'zustand'
import { api } from '../services/api'

interface ParserStore {
  isLoading: boolean
  error: string | null
  
  getSupportedLanguages: () => Promise<any>
  getSupportedExtensions: () => Promise<any>
  parseFile: (filePath: string) => Promise<any>
  getProjectStructure: (projectId: string) => Promise<any>
  getCallGraph: (projectId: string) => Promise<any>
  getDependencies: (projectId: string) => Promise<any>
  getProjectSummary: (projectId: string) => Promise<any>
}

export const useParserStore = create<ParserStore>((set) => ({
  isLoading: false,
  error: null,
  
  getSupportedLanguages: async () => {
    set({ isLoading: true, error: null })
    try {
      const res = await api.get('/parser/languages')
      set({ isLoading: false })
      return res.data
    } catch (err: any) {
      set({ error: err.message, isLoading: false })
      throw err
    }
  },
  
  getSupportedExtensions: async () => {
    set({ isLoading: true, error: null })
    try {
      const res = await api.get('/parser/extensions')
      set({ isLoading: false })
      return res.data
    } catch (err: any) {
      set({ error: err.message, isLoading: false })
      throw err
    }
  },
  
  parseFile: async (filePath: string) => {
    set({ isLoading: true, error: null })
    try {
      const res = await api.post('/parser/file', { file_path: filePath })
      set({ isLoading: false })
      return res.data.data || res.data
    } catch (err: any) {
      set({ error: err.message, isLoading: false })
      throw err
    }
  },
  
  getProjectStructure: async (projectId: string) => {
    set({ isLoading: true, error: null })
    try {
      const res = await api.get(`/parser/project/${projectId}/structure`)
      set({ isLoading: false })
      return res.data?.data || res.data
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to load structure'
      set({ error: errorMsg, isLoading: false })
      throw new Error(errorMsg)
    }
  },
  
  getCallGraph: async (projectId: string) => {
    set({ isLoading: true, error: null })
    try {
      const res = await api.get(`/parser/project/${projectId}/call-graph`)
      set({ isLoading: false })
      return res.data?.data || res.data
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to load call graph'
      set({ error: errorMsg, isLoading: false })
      throw new Error(errorMsg)
    }
  },
  
  getDependencies: async (projectId: string) => {
    set({ isLoading: true, error: null })
    try {
      const res = await api.get(`/parser/project/${projectId}/dependencies`)
      set({ isLoading: false })
      return res.data?.data || res.data
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to load dependencies'
      set({ error: errorMsg, isLoading: false })
      throw new Error(errorMsg)
    }
  },
  
  getProjectSummary: async (projectId: string) => {
    set({ isLoading: true, error: null })
    try {
      const res = await api.get(`/parser/project/${projectId}/summary`)
      set({ isLoading: false })
      return res.data?.data || res.data
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to load summary'
      set({ error: errorMsg, isLoading: false })
      throw new Error(errorMsg)
    }
  },
}))
