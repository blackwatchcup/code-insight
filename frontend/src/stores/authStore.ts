import { create } from 'zustand'
import { api } from '../services/api'

interface User {
  id: string
  username: string
  email: string
  role: string
  is_active: boolean
}

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  
  login: (username: string, password: string) => Promise<void>
  register: (username: string, email: string, password: string) => Promise<void>
  logout: () => void
  fetchUser: () => Promise<void>
  setToken: (token: string) => void
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  token: localStorage.getItem('token'),
  isAuthenticated: !!localStorage.getItem('token'),
  isLoading: false,
  
  setToken: (token: string) => {
    localStorage.setItem('token', token)
    api.defaults.headers.common['Authorization'] = `Bearer ${token}`
    set({ token, isAuthenticated: true })
  },
  
  login: async (username: string, password: string) => {
    set({ isLoading: true })
    try {
      const formData = new FormData()
      formData.append('username', username)
      formData.append('password', password)
      
      const res = await api.post('/auth/login', formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      })
      
      const { access_token, user } = res.data
      localStorage.setItem('token', access_token)
      api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
      
      set({ 
        user, 
        token: access_token, 
        isAuthenticated: true, 
        isLoading: false 
      })
    } catch (err: any) {
      set({ isLoading: false })
      throw err
    }
  },
  
  register: async (username: string, email: string, password: string) => {
    set({ isLoading: true })
    try {
      const res = await api.post('/auth/register', {
        username,
        email,
        password
      })
      
      const { access_token, user } = res.data
      localStorage.setItem('token', access_token)
      api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
      
      set({ 
        user, 
        token: access_token, 
        isAuthenticated: true, 
        isLoading: false 
      })
    } catch (err: any) {
      set({ isLoading: false })
      throw err
    }
  },
  
  logout: () => {
    localStorage.removeItem('token')
    delete api.defaults.headers.common['Authorization']
    set({ 
      user: null, 
      token: null, 
      isAuthenticated: false 
    })
  },
  
  fetchUser: async () => {
    const token = get().token
    if (!token) return
    
    try {
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`
      const res = await api.get('/auth/me')
      set({ user: res.data, isAuthenticated: true })
    } catch (err) {
      localStorage.removeItem('token')
      set({ user: null, token: null, isAuthenticated: false })
    }
  }
}))

// Initialize auth on load
const token = localStorage.getItem('token')
if (token) {
  api.defaults.headers.common['Authorization'] = `Bearer ${token}`
}
