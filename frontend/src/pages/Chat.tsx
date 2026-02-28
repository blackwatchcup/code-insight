import { useState, useEffect, useRef } from 'react'
import { useParams } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import { useChatStore } from '../stores/chatStore'
import { useProjectStore } from '../stores/projectStore'
import type { ChatMessage, ChatSession } from '../types'

export default function Chat() {
  const { projectId } = useParams()
  const { projects, fetchProjects } = useProjectStore()
  const { ask, getChatHistory, listSessions, deleteSession, error: chatError } = useChatStore()
  
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [selectedProjectId, setSelectedProjectId] = useState<string>(projectId || '')
  const [sessionId, setSessionId] = useState<string>(() => {
    const existing = sessionStorage.getItem('chat_session_id')
    if (existing) return existing
    const newId = Date.now().toString()
    sessionStorage.setItem('chat_session_id', newId)
    return newId
  })
  const [sessions, setSessions] = useState<ChatSession[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [isLoadingHistory, setIsLoadingHistory] = useState(false)
  const [historyLoaded, setHistoryLoaded] = useState(false)
  const [showSidebar, setShowSidebar] = useState(true)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const [isAtBottom, setIsAtBottom] = useState(true)

  useEffect(() => {
    fetchProjects()
    if (projectId) {
      setSelectedProjectId(projectId)
    }
  }, [fetchProjects, projectId])

  useEffect(() => {
    loadSessions()
  }, [selectedProjectId])

  useEffect(() => {
    const loadHistory = async () => {
      if (!sessionId || historyLoaded) {
        return
      }
      
      setIsLoadingHistory(true)
      try {
        const history = await getChatHistory(sessionId, 100)
        
        if (history && Array.isArray(history) && history.length > 0) {
          const formattedMessages: ChatMessage[] = history.map((msg: any, index) => {
            return {
              id: msg.id || `${Date.now()}_${index}_${Math.random()}`,
              role: msg.role || 'assistant',
              content: msg.content || '',
              timestamp: msg.timestamp || new Date().toISOString(),
              sources: msg.sources || [],
            }
          })
          setMessages(formattedMessages)
        } else {
          setMessages([])
        }
        setHistoryLoaded(true)
      } catch (err: any) {
        console.error('Failed to load history:', err)
        setMessages([])
        setHistoryLoaded(true)
      } finally {
        setIsLoadingHistory(false)
      }
    }
    
    loadHistory()
  }, [sessionId, getChatHistory])

  const scrollToBottom = (behavior: ScrollBehavior = 'smooth') => {
    messagesEndRef.current?.scrollIntoView({ behavior })
  }

  const handleScroll = () => {
    if (containerRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = containerRef.current
      const atBottom = scrollHeight - scrollTop - clientHeight < 50
      setIsAtBottom(atBottom)
    }
  }

  useEffect(() => {
    if (isStreaming || isAtBottom) {
      scrollToBottom(isStreaming ? 'auto' : 'smooth')
    }
  }, [messages, isStreaming, isAtBottom])

  const loadSessions = async () => {
    try {
      const sessionList = await listSessions(selectedProjectId || undefined, 50, 0)
      setSessions(sessionList || [])
    } catch (err) {
      console.error('Failed to load sessions:', err)
    }
  }

  const handleSelectSession = (session: ChatSession) => {
    console.log('Selecting session:', session.id)
    sessionStorage.setItem('chat_session_id', session.id)
    setSessionId(session.id)
    setHistoryLoaded(false)
    setMessages([])
  }

  const handleNewChat = () => {
    const newSessionId = Date.now().toString()
    console.log('Creating new session:', newSessionId)
    sessionStorage.setItem('chat_session_id', newSessionId)
    setSessionId(newSessionId)
    setMessages([])
    setHistoryLoaded(false)
    setInput('')
    loadSessions()
  }

  const handleDeleteSession = async (e: React.MouseEvent, sessionIdToDelete: string) => {
    e.stopPropagation()
    if (!confirm('确定要删除这个会话吗？')) return
    
    try {
      await deleteSession(sessionIdToDelete)
      if (sessionIdToDelete === sessionId) {
        handleNewChat()
      } else {
        loadSessions()
      }
    } catch (err) {
      console.error('Failed to delete session:', err)
    }
  }

  const handleSend = async () => {
    if (!input.trim() || isStreaming) return

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date().toISOString(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setIsStreaming(true)

    try {
      const response = await ask(input, selectedProjectId, sessionId, undefined, 5)
      
      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.answer || '',
        timestamp: new Date().toISOString(),
        sources: response.sources || [],
      }

      setMessages((prev) => [...prev, assistantMessage])
      loadSessions()
    } catch (err: any) {
      console.error('Chat error:', err)
      const errorMsg = err.message || '未知错误'
      
      let helpText = ''
      if (errorMsg.includes('401') || errorMsg.includes('Unauthorized')) {
        helpText = '\n\n请检查登录状态'
      } else if (errorMsg.includes('403') || errorMsg.includes('Forbidden')) {
        helpText = '\n\n您没有权限访问此功能'
      } else if (errorMsg.includes('422') || errorMsg.includes('Validation')) {
        helpText = '\n\n请求参数错误'
      } else if (errorMsg.includes('API') || errorMsg.includes('key')) {
        helpText = '\n\nAPI配置错误，请联系管理员'
      }
      
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Error: ' + errorMsg + helpText,
        timestamp: new Date().toISOString(),
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsStreaming(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const formatTime = (timestamp: string) => {
    try {
      const date = new Date(timestamp)
      const now = new Date()
      const diffMs = now.getTime() - date.getTime()
      const diffMins = Math.floor(diffMs / 60000)
      const diffHours = Math.floor(diffMs / 3600000)
      const diffDays = Math.floor(diffMs / 86400000)

      if (diffMins < 1) return '刚刚'
      if (diffMins < 60) return `${diffMins}分钟前`
      if (diffHours < 24) return `${diffHours}小时前`
      if (diffDays < 7) return `${diffDays}天前`
      return date.toLocaleDateString('zh-CN')
    } catch {
      return ''
    }
  }

  return (
    <div className="flex h-screen">
      <div className={`${showSidebar ? 'w-72' : 'w-0'} flex-shrink-0 bg-gray-50 border-r border-gray-200 transition-all duration-300 overflow-hidden`}>
        <div className="w-72 h-full flex flex-col">
          <div className="p-4 border-b border-gray-200 flex-shrink-0">
            <button
              onClick={handleNewChat}
              className="w-full px-4 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl font-medium hover:from-blue-700 hover:to-indigo-700 transition-all shadow-lg shadow-blue-500/25 flex items-center justify-center gap-2"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              新建对话
            </button>
          </div>
          
          <div className="flex-1 overflow-y-auto">
            {sessions.length === 0 ? (
              <div className="p-4 text-center text-gray-500 text-sm">
                暂无会话记录
              </div>
            ) : (
              <div className="p-2">
                {sessions.map((session) => (
                  <div
                    key={session.id}
                    onClick={() => handleSelectSession(session)}
                    className={`group p-3 rounded-xl mb-1 cursor-pointer transition-all ${
                      session.id === sessionId
                        ? 'bg-blue-100 border border-blue-200'
                        : 'hover:bg-gray-100 border border-transparent'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-gray-900 text-sm truncate">
                          {session.title || '新对话'}
                        </div>
                        <div className="text-xs text-gray-500 mt-1">
                          {formatTime(session.updated_at)}
                        </div>
                      </div>
                      <button
                        onClick={(e) => handleDeleteSession(e, session.id)}
                        className="p-1 hover:bg-red-100 rounded-lg transition-all"
                      >
                        <svg className="w-4 h-4 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0112.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="flex-1 flex flex-col min-w-0">
        <div className="p-4 border-b border-gray-200/50 bg-white/80 backdrop-blur-sm flex-shrink-0 flex items-center gap-4">
          <button
            onClick={() => setShowSidebar(!showSidebar)}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
          
          <div className="flex-1 flex items-center gap-3">
            <label className="text-sm text-gray-600 font-medium whitespace-nowrap">项目:</label>
            <select
              value={selectedProjectId}
              onChange={(e) => setSelectedProjectId(e.target.value)}
              className="flex-1 max-w-md px-3 py-2 bg-white border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-shadow text-sm"
            >
              <option value="">所有项目</option>
              {(projects || []).map((project) => (
                <option key={project.id} value={project.id}>
                  {project.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div 
          ref={containerRef}
          onScroll={handleScroll}
          className="flex-1 overflow-y-auto p-6 space-y-4 min-h-0"
        >
          {isLoadingHistory ? (
            <div className="flex items-center justify-center h-full">
              <div className="flex flex-col items-center gap-3">
                <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                <span className="text-gray-500 text-sm">加载历史记录...</span>
              </div>
            </div>
          ) : messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <div className="w-20 h-20 bg-gradient-to-br from-blue-100 to-indigo-100 rounded-2xl flex items-center justify-center mb-5">
                <svg className="w-10 h-10 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">开始对话</h3>
              <p className="text-gray-500 text-sm max-w-md">
                询问关于代码库的任何问题，AI 将帮您找到答案并提供代码示例
              </p>
            </div>
          ) : (
            messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-3xl rounded-2xl px-5 py-3 ${
                    message.role === 'user'
                      ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white'
                      : message.content.startsWith('Error:')
                        ? 'bg-red-50 border border-red-200 text-red-900'
                        : 'bg-white border border-gray-200/50 text-gray-900'
                  }`}
                >
                  {message.role !== 'user' && !message.content.startsWith('Error:') ? (
                    <div className="prose prose-sm max-w-none prose-headings:font-semibold prose-headings:text-gray-900 prose-p:text-gray-700 prose-code:text-pink-600 prose-pre:bg-gray-50 prose-pre:border prose-pre:border-gray-200 prose-blockquote:border-l-4 prose-blockquote:border-gray-300 prose-blockquote:pl-4 prose-blockquote:italic prose-blockquote:text-gray-600 prose-ul:list-disc prose-ol:list-decimal prose-li:my-1 prose-a:text-blue-600 prose-a:no-underline hover:prose-a:underline">
                      <ReactMarkdown>{message.content}</ReactMarkdown>
                    </div>
                  ) : (
                    <div className="whitespace-pre-wrap text-sm break-words">{message.content}</div>
                  )}
                  {message.sources && message.sources.length > 0 && !message.content.startsWith('Error:') && (
                    <div className="mt-3 pt-3 border-t border-gray-200/50">
                      <div className="text-xs text-gray-600 mb-2">参考来源:</div>
                      {message.sources.map((source: any, idx) => (
                        <div key={idx} className="text-xs text-gray-700 font-mono">
                          {source.file_path}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))
          )}

          {isStreaming && (
            <div className="flex justify-start">
              <div className="bg-white border border-gray-200/50 rounded-2xl px-5 py-3">
                <div className="flex gap-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {chatError && (
          <div className="px-6 py-3 bg-red-50 border-t border-red-200">
            <div className="flex items-center gap-2 text-red-700 text-sm">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {chatError}
            </div>
          </div>
        )}

        <div className="p-6 border-t border-gray-200/50 bg-white/80 backdrop-blur-sm flex-shrink-0">
          <div className="flex gap-3">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="输入您的问题..."
              rows={1}
              className="flex-1 px-4 py-3 bg-white border border-gray-200 rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-shadow"
              disabled={isStreaming}
              style={{ minHeight: '48px', maxHeight: '200px' }}
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || isStreaming}
              className="px-6 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl font-medium hover:from-blue-700 hover:to-indigo-700 transition-all shadow-lg shadow-blue-500/25 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {isStreaming ? (
                <>
                  <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  发送中
                </>
              ) : (
                <>
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                  </svg>
                  发送
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
