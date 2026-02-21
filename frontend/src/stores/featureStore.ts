import { create } from 'zustand'
import { api } from '../services/api'

interface FeatureStore {
  isLoading: boolean
  error: string | null
  
  getFeatureTree: (projectId: string) => Promise<any>
  getFeatureSummary: (projectId: string) => Promise<any>
  getFrontendFeatures: (projectId: string) => Promise<any[]>
  getBackendFeatures: (projectId: string) => Promise<any[]>
  getApiEndpoints: (projectId: string) => Promise<any[]>
  getDataModels: (projectId: string) => Promise<any[]>
  getSystemFeatures: (projectId: string) => Promise<any[]>
}

export const useFeatureStore = create<FeatureStore>((set) => ({
  isLoading: false,
  error: null,
  
  getFeatureTree: async (projectId: string) => {
    set({ isLoading: true, error: null })
    try {
      const res = await api.get(`/features/${projectId}`)
      set({ isLoading: false })
      return res.data?.data || res.data
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to load features'
      set({ error: errorMsg, isLoading: false })
      throw new Error(errorMsg)
    }
  },
  
  getFeatureSummary: async (projectId: string) => {
    set({ isLoading: true, error: null })
    try {
      const res = await api.get(`/features/${projectId}/summary`)
      set({ isLoading: false })
      return res.data?.data || res.data
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to load summary'
      set({ error: errorMsg, isLoading: false })
      throw new Error(errorMsg)
    }
  },
  
  getFrontendFeatures: async (projectId: string) => {
    set({ isLoading: true, error: null })
    try {
      const res = await api.get(`/features/${projectId}/frontend`)
      set({ isLoading: false })
      return res.data?.data || res.data
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to load frontend features'
      set({ error: errorMsg, isLoading: false })
      throw new Error(errorMsg)
    }
  },
  
  getBackendFeatures: async (projectId: string) => {
    set({ isLoading: true, error: null })
    try {
      const res = await api.get(`/features/${projectId}/backend`)
      set({ isLoading: false })
      return res.data?.data || res.data
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to load backend features'
      set({ error: errorMsg, isLoading: false })
      throw new Error(errorMsg)
    }
  },
  
  getApiEndpoints: async (projectId: string) => {
    set({ isLoading: true, error: null })
    try {
      const res = await api.get(`/features/${projectId}/apis`)
      set({ isLoading: false })
      return res.data?.data || res.data
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to load API endpoints'
      set({ error: errorMsg, isLoading: false })
      throw new Error(errorMsg)
    }
  },
  
  getDataModels: async (projectId: string) => {
    set({ isLoading: true, error: null })
    try {
      const res = await api.get(`/features/${projectId}/models`)
      set({ isLoading: false })
      return res.data?.data || res.data
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to load data models'
      set({ error: errorMsg, isLoading: false })
      throw new Error(errorMsg)
    }
  },
  
  getSystemFeatures: async (projectId: string) => {
    set({ isLoading: true, error: null })
    try {
      const res = await api.get(`/features/${projectId}/system`)
      set({ isLoading: false })
      return res.data?.data || res.data
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to load system features'
      set({ error: errorMsg, isLoading: false })
      throw new Error(errorMsg)
    }
  },
}))
