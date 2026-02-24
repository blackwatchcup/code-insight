import { useState, useEffect, useRef } from 'react'
import { useParams } from 'react-router-dom'
import { useChatStore } from '../stores/chatStore'
import { useProjectStore } from '../stores/projectStore'
import type { ChatMessage } from '../types'

export default function Chat() {
  const { projectId } = useParams()
  const { projects, fetchProjects } = useProjectStore()
  const { ask, getChatHistory, error: chatError } = useChatStore()
  
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [selectedProjectId, setSelectedProjectId] = useState<string>(projectId || '')
  const [sessionId] = useState<string>(() => {
    const existing = sessionStorage.getItem('chat_session_id')
    if (existing) return existing
    const newId = Date.now().toString()
    sessionStorage.setItem('chat_session_id', newId)
    return newId
  })
  const [isStreaming, setIsStreaming] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    fetchProjects()
    if (projectId) {
      setSelectedProjectId(projectId)
    }
    
    const loadHistory = async () => {
      try {
        const history = await getChatHistory(sessionId, 20)
        if (history && history.length > 0) {
          const formattedMessages: ChatMessage[] = history.map((msg: any) => ({
            id: msg.id || Date.now().toString() + Math.random(),
            role: msg.role,
            content: msg.content || msg.question || msg.answer || '',
            timestamp: msg.timestamp || new Date().toISOString(),
            sources: msg.sources,
          }))
          setMessages(formattedMessages)
        }
      } catch (err) {
        console.log('No history found or failed to load')
      }
    }
    
    loadHistory()
  }, [fetchProjects, projectId, sessionId, getChatHistory])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

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
        sources: response.sources,
      }

      setMessages((prev) => [...prev, assistantMessage])
    } catch (err: any) {
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

  return (
    <div className="flex flex-col h-full">
      <div className="p-6 border-b border-gray-200/50 bg-white/80 backdrop-blur-sm">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">智能问答</h2>
            <p className="text-gray-500 mt-1 text-sm">与您的代码库进行对话</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <label className="text-sm text-gray-600 font-medium">选择项目:</label>
          <select
            value={selectedProjectId}
            onChange={(e) => setSelectedProjectId(e.target.value)}
            className="flex-1 max-w-md px-3 py-2 bg-white border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-shadow"
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

      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.length === 0 && (
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
        )}

        {messages.map((message) => (
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
              <div className="whitespace-pre-wrap text-sm break-words">{message.content}</div>
              {message.sources && message.sources.length > 0 && !message.content.startsWith('Error:') && (
                <div className="mt-3 pt-3 border-t border-red-100/20">
                  <div className="text-xs text-red-900/70 mb-2">参考来源:</div>
                  {message.sources.map((source, idx) => (
                    <div key={idx} className="text-xs text-red-900/80 font-mono">
                      {source.file_path}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

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

      <div className="p-6 border-t border-gray-200/50 bg-white/80 backdrop-blur-sm">
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
  )
}
