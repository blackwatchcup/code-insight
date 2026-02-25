import { create } from 'zustand'
import { api } from '../services/api'
import type { ChatSession } from '../types'

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
}

export const useChatStore = create<ChatStore>((set) => ({
  isLoading: false,
  error: null,
  
  ask: async (question: string, projectId?: string, sessionId?: string, qaType?: string, topK: number = 5, chatMode: string = 'project') => {
    set({ isLoading: true, error: null })
    try {
      const res = await api.post('/chat/ask', {
        question,
        project_id: projectId,
        session_id: sessionId,
        qa_type: qaType,
        top_k: topK,
        chat_mode: chatMode,
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
            const data = JSON.parse(line.slice(6))
            if (data.chunk) {
              onChunk?.(data.chunk)
            } else if (data.error) {
              onError?.(data.error)
              set({ error: data.error, isLoading: false })
              return
            } else if (data.done) {
              set({ isLoading: false })
              return
            }
          }
        }
      }
    } catch (err: unknown) {
      const errorObj = err as { message?: string }
      set({ error: errorObj.message || 'Unknown error', isLoading: false })
      onError?.(errorObj.message || 'Unknown error')
    }
  },
  
  search: async (query: string, projectId?: string, topK: number = 5, threshold?: number) => {
    set({ isLoading: true, error: null })
    try {
      const res = await api.post('/chat/search', {
        query,
        project_id: projectId,
        top_k: topK,
        threshold,
      })
      set({ isLoading: false })
      return res.data.data
    } catch (err: unknown) {
      const errorObj = err as { message?: string }
      set({ error: errorObj.message || 'Unknown error', isLoading: false })
      throw err
    }
  },
  
  indexProject: async (projectId: string, projectPath: string, fileExtensions?: string[]) => {
    set({ isLoading: true, error: null })
    try {
      const res = await api.post('/chat/index', {
        project_id: projectId,
        project_path: projectPath,
        file_extensions: fileExtensions,
      })
      set({ isLoading: false })
      return res.data.data
    } catch (err: unknown) {
      const errorObj = err as { message?: string }
      set({ error: errorObj.message || 'Unknown error', isLoading: false })
      throw err
    }
  },
  
  deleteProjectIndex: async (projectId: string) => {
    set({ isLoading: true, error: null })
    try {
      const res = await api.delete(`/chat/index/${projectId}`)
      set({ isLoading: false })
      return res.data.data
    } catch (err: unknown) {
      const errorObj = err as { message?: string }
      set({ error: errorObj.message || 'Unknown error', isLoading: false })
      throw err
    }
  },
  
  getChatHistory: async (sessionId: string, limit?: number) => {
    set({ isLoading: true, error: null })
    try {
      const params = limit ? { limit } : {}
      const res = await api.get(`/chat/history/${sessionId}`, { params })
      set({ isLoading: false })
      return res.data.data
    } catch (err: unknown) {
      const errorObj = err as { message?: string }
      set({ error: errorObj.message || 'Unknown error', isLoading: false })
      throw err
    }
  },
  
  clearChatHistory: async (sessionId: string) => {
    set({ isLoading: true, error: null })
    try {
      await api.delete(`/chat/history/${sessionId}`)
      set({ isLoading: false })
    } catch (err: unknown) {
      const errorObj = err as { message?: string }
      set({ error: errorObj.message || 'Unknown error', isLoading: false })
      throw err
    }
  },

  listSessions: async (projectId?: string, limit: number = 50, offset: number = 0) => {
    set({ isLoading: true, error: null })
    try {
      const params: Record<string, string | number> = { limit, offset }
      if (projectId) {
        params.project_id = projectId
      }
      const res = await api.get('/chat/sessions', { params })
      set({ isLoading: false })
      return res.data.data as ChatSession[]
    } catch (err: unknown) {
      const errorObj = err as { message?: string }
      set({ error: errorObj.message || 'Unknown error', isLoading: false })
      throw err
    }
  },

  deleteSession: async (sessionId: string) => {
    set({ isLoading: true, error: null })
    try {
      const res = await api.delete(`/chat/sessions/${sessionId}`)
      set({ isLoading: false })
      return res.data.code === 200
    } catch (err: unknown) {
      const errorObj = err as { message?: string }
      set({ error: errorObj.message || 'Unknown error', isLoading: false })
      return false
    }
  },
  
  getStats: async () => {
    set({ isLoading: true, error: null })
    try {
      const res = await api.get('/chat/stats')
      set({ isLoading: false })
      return res.data.data
    } catch (err: unknown) {
      const errorObj = err as { message?: string }
      set({ error: errorObj.message || 'Unknown error', isLoading: false })
      throw err
    }
  },
}))
