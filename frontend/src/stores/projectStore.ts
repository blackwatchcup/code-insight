import { create } from 'zustand'
import { api } from '../services/api'
import type { Project, ImportData } from '../types'

interface ProjectStore {
  projects: Project[]
  isLoading: boolean
  error: string | null
  isImporting: boolean
  
  fetchProjects: () => Promise<void>
  fetchProject: (id: string) => Promise<Project>
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
      // Handle both response formats: {items: [...]} or {code: 200, data: {items: [...]}}
      const items = res.data.items || res.data.data?.items || []
      set({ projects: items, isLoading: false })
    } catch (err: any) {
      set({ error: err.message, isLoading: false })
    }
  },
  
  fetchProject: async (id: string) => {
    try {
      const res = await api.get(`/projects/${id}`)
      return res.data.data || res.data
    } catch (err: any) {
      set({ error: err.message })
      throw err
    }
  },
  
  importProject: async (data: ImportData) => {
    set({ isImporting: true, error: null })
    try {
      let projectData
      if (data.source_type === 'local') {
        const res = await api.post('/projects', {
          name: data.name,
          source_type: 'local',
          local_path: data.url,
        })
        projectData = res.data.data || res.data
        console.log('本地项目创建成功:', projectData)
      } else {
        const res = await api.post('/projects/import', {
          type: data.source_type,
          url: data.url,
          name: data.name,
          branch: data.branch,
          token: data.token,
        })
        projectData = res.data.data || res.data
        console.log('导入项目成功:', projectData)
      }
      
      set({ isImporting: false })
      
      // Refresh project list after import
      const res = await api.get('/projects')
      console.log('刷新项目列表响应:', res.data)
      const items = res.data.items || res.data.data?.items || []
      console.log('项目列表:', items)
      set({ projects: items })
    } catch (err: any) {
      console.error('导入项目失败:', err)
      console.error('错误详情:', err.response?.data)
      set({ error: err.message, isImporting: false })
      throw err
    }
  },
  
  deleteProject: async (id: string) => {
    try {
      await api.delete(`/projects/${id}`)
      // Refresh project list after deletion
      const res = await api.get('/projects')
      const items = res.data.items || res.data.data?.items || []
      set({ projects: items })
    } catch (err: any) {
      set({ error: err.message })
    }
  },
}))
