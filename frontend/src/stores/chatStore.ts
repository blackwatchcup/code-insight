import { create } from 'zustand'
import { api } from '../services/api'
import type { ChatSession } from '../types'

interface UserSettings {
  apiKey: string
  model: string
  customModel: string
  baseUrl: string
  temperature: number
  maxTokens: number
}

const DEFAULT_SETTINGS: UserSettings = {
  apiKey: '',
  model: 'deepseek-chat',
  customModel: '',
  baseUrl: 'https://api.deepseek.com',
  temperature: 0.7,
  maxTokens: 2000,
}

export const getUserSettings = (): UserSettings => {
  const savedSettings = localStorage.getItem('user_settings')
  if (savedSettings) {
    try {
      return { ...DEFAULT_SETTINGS, ...JSON.parse(savedSettings) }
    } catch (e) {
      console.error('Failed to parse settings:', e)
    }
  }
  return DEFAULT_SETTINGS
}

export const getLLMConfig = () => {
  const settings = getUserSettings()
  const model = settings.model === 'custom' ? settings.customModel : settings.model
  const baseUrl = settings.model === 'custom' ? settings.baseUrl : undefined
  
  if (!settings.apiKey && !baseUrl) {
    return null
  }
  
  return {
    model,
    api_key: settings.apiKey,
    base_url: baseUrl,
  }
}

interface ChatStore {
  isLoading: boolean
  error: string | null
  
  ask: (question: string, projectId?: string, sessionId?: string, qaType?: string, topK?: number, chatMode?: string) => Promise<any>
  askStream: (question: string, projectId?: string, sessionId?: string, qaType?: string, topK?: number, chatMode?: string, onChunk?: (chunk: string) => void, onError?: (error: string) => void) => Promise<void>
  search: (query: string, projectId?: string, topK?: number, threshold?: number) => Promise<any[]>
  indexProject: (projectId: string, projectPath: string, fileExtensions?: string[]) => Promise<any>
  deleteProjectIndex: (projectId: string) => Promise<any>
  getChatHistory: (sessionId: string, limit?: number) => Promise<any[]>
  clearChatHistory: (sessionId: string) => Promise<void>
  listSessions: (projectId?: string, limit?: number, offset?: number) => Promise<ChatSession[]>
  deleteSession: (sessionId: string) => Promise<boolean>
  getStats: () => Promise<any>
  getProjectSummary: (projectId: string, topK?: number) => Promise<any>
}

export const useChatStore = create<ChatStore>((set) => ({
  isLoading: false,
  error: null,
  
  ask: async (question: string, projectId?: string, sessionId?: string, qaType?: string, topK: number = 5, chatMode: string = 'project') => {
    set({ isLoading: true, error: null })
    try {
      const llmConfig = getLLMConfig()
      
      const res = await api.post('/chat/ask', {
        question,
        project_id: projectId,
        session_id: sessionId,
        qa_type: qaType,
        top_k: topK,
        chat_mode: chatMode,
        ...llmConfig,
      })
      set({ isLoading: false })
      return res.data.data
    } catch (err: unknown) {
      const errorObj = err as { response?: { data?: { detail?: string; message?: string } }; message?: string }
      const errorMessage = errorObj.response?.data?.detail || 
                           errorObj.response?.data?.message || 
                           errorObj.message || 
                           'Failed to get response'
      console.error('Chat error:', err)
      set({ error: errorMessage, isLoading: false })
      throw new Error(errorMessage)
    }
  },
  
  askStream: async (
    question: string,
    projectId?: string,
    sessionId?: string,
    qaType?: string,
    topK: number = 5,
    chatMode: string = 'project',
    onChunk?: (chunk: string) => void,
    onError?: (error: string) => void
  ) => {
    set({ isLoading: true, error: null })
    try {
      const llmConfig = getLLMConfig()
      
      const response = await fetch(`${api.defaults.baseURL}/chat/ask/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': api.defaults.headers.common['Authorization'] as string,
        },
        body: JSON.stringify({
          question,
          project_id: projectId,
          session_id: sessionId,
          qa_type: qaType,
          top_k: topK,
          chat_mode: chatMode,
          ...llmConfig,
        }),
      })
      
      const reader = response.body?.getReader()
      const decoder = new TextDecoder()
      
      if (!reader) {
        throw new Error('No response body')
      }
      
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        
        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6)
            if (data === '[DONE]') {
              set({ isLoading: false })
              return
            }
            try {
              const parsed = JSON.parse(data)
              if (parsed.content) {
                onChunk?.(parsed.content)
              }
            } catch {
              onChunk?.(data)
            }
          }
        }
      }
      
      set({ isLoading: false })
    } catch (err: unknown) {
      const errorObj = err as { message?: string }
      const errorMessage = errorObj.message || 'Stream error'
      console.error('Chat stream error:', err)
      set({ error: errorMessage, isLoading: false })
      onError?.(errorMessage)
    }
  },
  
  search: async (query: string, projectId?: string, topK: number = 5, threshold: number = 0.5) => {
    try {
      const res = await api.post('/chat/search', {
        query,
        project_id: projectId,
        top_k: topK,
        threshold,
      })
      return res.data.data.results || []
    } catch (err) {
      console.error('Search error:', err)
      return []
    }
  },
  
  indexProject: async (projectId: string, projectPath: string, fileExtensions?: string[]) => {
    try {
      const res = await api.post('/chat/index', {
        project_id: projectId,
        project_path: projectPath,
        file_extensions: fileExtensions,
      })
      return res.data.data
    } catch (err) {
      console.error('Index error:', err)
      throw err
    }
  },
  
  deleteProjectIndex: async (projectId: string) => {
    try {
      const res = await api.delete(`/chat/index/${projectId}`)
      return res.data.data
    } catch (err) {
      console.error('Delete index error:', err)
      throw err
    }
  },
  
  getChatHistory: async (sessionId: string, limit: number = 50) => {
    try {
      const res = await api.get(`/chat/history/${sessionId}`, {
        params: { limit },
      })
      return res.data.data || []
    } catch (err) {
      console.error('Get history error:', err)
      return []
    }
  },
  
  clearChatHistory: async (sessionId: string) => {
    try {
      await api.delete(`/chat/history/${sessionId}`)
    } catch (err) {
      console.error('Clear history error:', err)
    }
  },
  
  listSessions: async (projectId?: string, limit: number = 50, offset: number = 0) => {
    try {
      const res = await api.get('/chat/sessions', {
        params: { project_id: projectId, limit, offset },
      })
      return res.data.data || []
    } catch (err) {
      console.error('List sessions error:', err)
      return []
    }
  },
  
  deleteSession: async (sessionId: string) => {
    try {
      await api.delete(`/chat/history/${sessionId}`)
      return true
    } catch (err) {
      console.error('Delete session error:', err)
      return false
    }
  },
  
  getStats: async () => {
    try {
      const res = await api.get('/chat/stats')
      return res.data.data
    } catch (err) {
      console.error('Get stats error:', err)
      return null
    }
  },
  
  getProjectSummary: async (projectId: string, topK: number = 20) => {
    set({ isLoading: true, error: null })
    try {
      const res = await api.get(`/chat/project-summary/${projectId}`, {
        params: { top_k: topK },
      })
      set({ isLoading: false })
      return res.data.data
    } catch (err: unknown) {
      const errorObj = err as { response?: { data?: { detail?: string } }; message?: string }
      const errorMessage = errorObj.response?.data?.detail || errorObj.message || 'Failed to generate project summary'
      console.error('Get project summary error:', err)
      set({ error: errorMessage, isLoading: false })
      throw new Error(errorMessage)
    }
  },
}))
