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
      return res.data.data || res.data
    } catch (err: any) {
      set({ error: err.message, isLoading: false })
      throw err
    }
  },
  
  getFeatureSummary: async (projectId: string) => {
    set({ isLoading: true, error: null })
    try {
      const res = await api.get(`/features/${projectId}/summary`)
      set({ isLoading: false })
      return res.data.data || res.data
    } catch (err: any) {
      set({ error: err.message, isLoading: false })
      throw err
    }
  },
  
  getFrontendFeatures: async (projectId: string) => {
    set({ isLoading: true, error: null })
    try {
      const res = await api.get(`/features/${projectId}/frontend`)
      set({ isLoading: false })
      return res.data.data || res.data
    } catch (err: any) {
      set({ error: err.message, isLoading: false })
      throw err
    }
  },
  
  getBackendFeatures: async (projectId: string) => {
    set({ isLoading: true, error: null })
    try {
      const res = await api.get(`/features/${projectId}/backend`)
      set({ isLoading: false })
      return res.data.data || res.data
    } catch (err: any) {
      set({ error: err.message, isLoading: false })
      throw err
    }
  },
  
  getApiEndpoints: async (projectId: string) => {
    set({ isLoading: true, error: null })
    try {
      const res = await api.get(`/features/${projectId}/apis`)
      set({ isLoading: false })
      return res.data.data || res.data
    } catch (err: any) {
      set({ error: err.message, isLoading: false })
      throw err
    }
  },
  
  getDataModels: async (projectId: string) => {
    set({ isLoading: true, error: null })
    try {
      const res = await api.get(`/features/${projectId}/models`)
      set({ isLoading: false })
      return res.data.data || res.data
    } catch (err: any) {
      set({ error: err.message, isLoading: false })
      throw err
    }
  },
  
  getSystemFeatures: async (projectId: string) => {
    set({ isLoading: true, error: null })
    try {
      const res = await api.get(`/features/${projectId}/system`)
      set({ isLoading: false })
      return res.data.data || res.data
    } catch (err: any) {
      set({ error: err.message, isLoading: false })
      throw err
    }
  },
}))
