import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useProjectStore } from '../stores/projectStore'
import { useChatStore } from '../stores/chatStore'
import FeatureAnalysis from '../components/FeatureAnalysis'
import ParserAnalysis from '../components/ParserAnalysis'
import VersionComparison from '../components/VersionComparison'
import Chat from './Chat'
import { api } from '../services/api'
import ReactMarkdown from 'react-markdown'

export default function ProjectDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { fetchProject, deleteProject, isLoading } = useProjectStore()
  const { indexProject, deleteProjectIndex } = useChatStore()
  
  const [activeTab, setActiveTab] = useState('overview')
  const [project, setProject] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)
  const [projectInfo, setProjectInfo] = useState<{ description: string; architecture: string } | null>(null)
  const [isLoadingInfo, setIsLoadingInfo] = useState(false)

  useEffect(() => {
    loadProject()
  }, [id])

  useEffect(() => {
    if (project) {
      loadProjectInfo()
    }
  }, [project])

  const loadProject = async () => {
    if (!id) return
    try {
      const data = await fetchProject(id)
      setProject(data)
    } catch (err: any) {
      setError(err.message || 'Failed to load project')
    }
  }

  const loadProjectInfo = async () => {
    if (!id) return
    setIsLoadingInfo(true)
    try {
      const response = await api.get(`/projects/${id}/info`)
      setProjectInfo(response.data.data)
    } catch (err: any) {
      console.error('Failed to load project info:', err)
      // 失败时使用默认描述
      setProjectInfo({
        description: project?.description || '本地代码仓库智能分析和知识问答系统。CodeInsight 是一个强大的代码分析工具，能够智能分析本地代码仓库，提供代码结构可视化、依赖关系分析、功能提取等功能，并支持基于代码的智能问答。',
        architecture: '系统采用前后端分离架构，前端使用React + TypeScript + TailwindCSS，后端使用FastAPI + Python，数据库使用SQLite。系统支持代码解析、依赖分析、功能提取、智能问答等核心功能。'
      })
    } finally {
      setIsLoadingInfo(false)
    }
  }

  const handleReindex = async () => {
    if (!project) return
    try {
      const confirmDelete = window.confirm('确定要删除现有索引并重新开始吗？')
      if (!confirmDelete) return

      alert('开始删除旧索引...')
      await deleteProjectIndex(project.id)
      
      alert('开始重新索引，这可能需要几分钟时间...')
      const result = await indexProject(project.id, project.local_path)
      
      if (result?.success) {
        alert('索引完成！')
        loadProject()
      } else {
        alert('索引完成，但可能存在问题: ' + (result?.error || '未知错误'))
        loadProject()
      }
    } catch (err: any) {
      console.error('索引错误:', err)
      const errorMsg = err.response?.data?.detail || err.message || '未知错误'
      alert('索引失败: ' + errorMsg)
    }
  }

  const handleDelete = async () => {
    if (!id) return
    if (window.confirm('确定要删除这个项目吗？此操作无法撤销。')) {
      try {
        await deleteProject(id)
        navigate('/')
      } catch (err: any) {
        alert('删除失败: ' + err.message)
      }
    }
  }

  const tabs = [
    { id: 'overview', label: '项目概览', icon: '📊' },
    { id: 'parser', label: '代码结构', icon: '🔍' },
    { id: 'features', label: '功能分析', icon: '🎯' },
    { id: 'versions', label: '版本对比', icon: '🔄' },
    { id: 'chat', label: '智能问答', icon: '💬' },
  ]

  if (isLoading && !project) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-200 rounded-full animate-spin border-t-blue-600 mx-auto"></div>
          <p className="mt-3 text-gray-500 text-sm">加载项目中...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 text-red-700 px-6 py-4 rounded-xl flex items-center gap-3">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          {error}
        </div>
      </div>
    )
  }

  if (!project) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center text-gray-500">项目不存在</div>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <button
            onClick={() => navigate('/')}
            className="text-sm text-gray-500 hover:text-gray-700 mb-2 flex items-center gap-1 transition-colors"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            返回项目列表
          </button>
          <h1 className="text-2xl font-bold text-gray-900">{project?.name ?? '未命名项目'}</h1>
          <p className="text-gray-500 text-sm mt-1">{project?.source_type === 'local' ? '本地目录' : project?.source_type?.toUpperCase() ?? '未知来源'}</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleReindex}
            className="px-4 py-2 bg-white border border-gray-200 text-gray-700 rounded-xl hover:bg-gray-50 transition-colors flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            重新索引
          </button>
          <button
            onClick={handleDelete}
            className="px-4 py-2 bg-red-50 border border-red-200 text-red-600 rounded-xl hover:bg-red-100 transition-colors flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
            删除
          </button>
        </div>
      </div>

      {activeTab === 'overview' && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl p-5">
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 bg-white rounded-lg shadow-sm">
                <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <span className="text-sm text-blue-600 font-medium">文件数</span>
            </div>
            <div className="text-2xl font-bold text-blue-900">{(project?.file_count ?? 0).toLocaleString()}</div>
          </div>

          <div className="bg-gradient-to-br from-indigo-50 to-indigo-100 rounded-xl p-5">
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 bg-white rounded-lg shadow-sm">
                <svg className="w-5 h-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
                </svg>
              </div>
              <span className="text-sm text-indigo-600 font-medium">代码行数</span>
            </div>
            <div className="text-2xl font-bold text-indigo-900">{(project?.line_count ?? 0).toLocaleString()}</div>
          </div>

          <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl p-5">
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 bg-white rounded-lg shadow-sm">
                <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <span className="text-sm text-purple-600 font-medium">状态</span>
            </div>
            <div className="text-lg font-bold text-purple-900">
              {project?.status === 'ready' ? '就绪' : project?.status === 'error' ? '错误' : project?.status === 'indexing' ? '索引中' : '未知'}
            </div>
          </div>

          <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl p-5">
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 bg-white rounded-lg shadow-sm">
                <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </div>
              <span className="text-sm text-gray-600 font-medium">创建时间</span>
            </div>
            <div className="text-sm font-semibold text-gray-900">
              {project?.created_at ? new Date(project.created_at).toLocaleDateString('zh-CN') : '未知'}
            </div>
          </div>
        </div>
      )}

      <div className="bg-white/80 backdrop-blur-sm rounded-2xl border border-gray-200/50 overflow-hidden">
        <div className="flex items-center gap-2 border-b border-gray-200/50 px-6">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-4 text-sm font-medium transition-colors border-b-2 -mb-px ${
                activeTab === tab.id
                  ? 'text-blue-600 border-blue-600'
                  : 'text-gray-500 border-transparent hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <span>{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </div>

        <div className="p-6 overflow-y-auto">
          {activeTab === 'overview' && (
            <div className="space-y-4">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">项目信息</h3>
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                  <div className="bg-gray-50 rounded-xl p-4">
                    <div className="text-sm text-gray-600 mb-1">项目名称</div>
                    <div className="text-lg font-semibold text-gray-900">{project?.name || '未命名项目'}</div>
                  </div>
                  <div className="bg-gray-50 rounded-xl p-4">
                    <div className="text-sm text-gray-600 mb-1">项目类型</div>
                    <div className="text-lg font-semibold text-gray-900">
                      {project?.source_type === 'local' ? '本地目录' : project?.source_type?.toUpperCase() || '未知类型'}
                    </div>
                  </div>
                  <div className="bg-gray-50 rounded-xl p-4">
                    <div className="text-sm text-gray-600 mb-1">创建时间</div>
                    <div className="text-lg font-semibold text-gray-900">
                      {project?.created_at ? new Date(project.created_at).toLocaleDateString('zh-CN') : '未知'}
                    </div>
                  </div>
                  <div className="bg-gray-50 rounded-xl p-4">
                    <div className="text-sm text-gray-600 mb-1">状态</div>
                    <div className="text-lg font-semibold text-gray-900">
                      {project?.status === 'ready' ? '就绪' : project?.status === 'error' ? '错误' : project?.status === 'indexing' ? '索引中' : '未知'}
                    </div>
                  </div>
                </div>
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">项目描述</h3>
                <div className="bg-gray-50 rounded-xl p-4">
                  {isLoadingInfo ? (
                    <div className="flex items-center justify-center h-24">
                      <div className="w-8 h-8 border-4 border-blue-200 rounded-full animate-spin border-t-blue-600"></div>
                    </div>
                  ) : (
                    <div className="text-gray-700 max-h-96 overflow-auto">
                      <div className="prose min-w-full">
                        <ReactMarkdown>
                          {projectInfo?.description || project?.description || '本地代码仓库智能分析和知识问答系统。CodeInsight 是一个强大的代码分析工具，能够智能分析本地代码仓库，提供代码结构可视化、依赖关系分析、功能提取等功能，并支持基于代码的智能问答。'}
                        </ReactMarkdown>
                      </div>
                    </div>
                  )}
                </div>
              </div>
              {project.source_url && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">源代码地址</h3>
                  <a
                    href={project.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:text-blue-700 flex items-center gap-2"
                  >
                    {project.source_url}
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                    </svg>
                  </a>
                </div>
              )}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">项目架构</h3>
                <div className="bg-gray-50 rounded-xl p-4">
                  <div className="grid gap-4">
                    <div className="grid gap-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600">文件总数</span>
                        <span className="font-semibold text-gray-900">{project?.file_count || 0}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">代码行数</span>
                        <span className="font-semibold text-gray-900">{project?.line_count || 0}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">分支</span>
                        <span className="font-semibold text-gray-900">{project?.branch || 'main'}</span>
                      </div>
                    </div>
                    <div className="pt-4 border-t border-gray-200">
                      <h4 className="text-sm font-semibold text-gray-900 mb-3">架构图</h4>
                      <div className="bg-white rounded-lg p-4 border border-gray-200">
                        {isLoadingInfo ? (
                          <div className="flex items-center justify-center h-24">
                            <div className="w-8 h-8 border-4 border-blue-200 rounded-full animate-spin border-t-blue-600"></div>
                          </div>
                        ) : (
                          <div className="text-gray-700 max-h-96 overflow-auto">
                            <div className="prose min-w-full">
                              <ReactMarkdown>
                                {projectInfo?.architecture || '系统采用前后端分离架构，前端使用React + TypeScript + TailwindCSS，后端使用FastAPI + Python，数据库使用SQLite。系统支持代码解析、依赖分析、功能提取、智能问答等核心功能。'}
                              </ReactMarkdown>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'parser' && <ParserAnalysis projectId={id!} project={project} />}
          
          {activeTab === 'features' && <FeatureAnalysis projectId={id!} project={project} />}
          
          {activeTab === 'versions' && <VersionComparison projectId={id!} />}
          
          {activeTab === 'chat' && (
            <div className="h-full">
              <Chat />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
