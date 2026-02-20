import { create } from 'zustand'
import { api } from '../services/api'
import type { Project, ImportData } from '../types'

interface ProjectStore {
  projects: Project[]
  isLoading: boolean
  error: string | null
  isImporting: boolean
  
  fetchProjects: () => Promise<void>
  importProject: (data: ImportData) => Promise<void>
  deleteProject: (id: string) => Promise<void>
}

export const useProjectStore = create<ProjectStore>((set) => ({
  projects: [],
  isLoading: false,
  error: null,
  isImporting: false,
  
  fetchProjects: async () => {
    set({ isLoading: true, error: null })
    try {
      const res = await api.get('/projects')
      set({ projects: res.data.data.items, isLoading: false })
    } catch (err: any) {
      set({ error: err.message, isLoading: false })
    }
  },
  
  importProject: async (data: ImportData) => {
    set({ isImporting: true, error: null })
    try {
      if (data.source_type === 'local') {
        await api.post('/projects', {
          name: data.name,
          source_type: 'local',
          local_path: data.url,
        })
      } else {
        await api.post('/projects/import', {
          type: data.source_type,
          url: data.url,
          name: data.name,
          branch: data.branch,
          token: data.token,
        })
      }
      set({ isImporting: false })
    } catch (err: any) {
      set({ error: err.message, isImporting: false })
      throw err
    }
  },
  
  deleteProject: async (id: string) => {
    try {
      await api.delete(`/projects/${id}`)
      set((state) => ({
        projects: state.projects.filter((p) => p.id !== id)
      }))
    } catch (err: any) {
      set({ error: err.message })
    }
  },
}))
