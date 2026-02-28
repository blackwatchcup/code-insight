import { useState, useEffect } from 'react'
import { useFeatureStore } from '../stores/featureStore'
import type { FeatureNode, APIEndpoint, DataModel } from '../types'

interface FeatureAnalysisProps {
  projectId: string
  project?: any
}

export default function FeatureAnalysis({ projectId, project }: FeatureAnalysisProps) {
  const [activeTab, setActiveTab] = useState('tree')
  const [featureTree, setFeatureTree] = useState<FeatureNode | null>(null)
  const [frontendFeatures, setFrontendFeatures] = useState<FeatureNode[]>([])
  const [backendFeatures, setBackendFeatures] = useState<FeatureNode[]>([])
  const [apiEndpoints, setApiEndpoints] = useState<APIEndpoint[]>([])
  const [dataModels, setDataModels] = useState<DataModel[]>([])
  
  const { getFeatureTree, getFrontendFeatures, getBackendFeatures, getApiEndpoints, getDataModels, isLoading, error } = useFeatureStore()

  const formatFilePath = (filePath: string) => {
    // 移除路径前缀，只显示相对路径，并使用项目名称作为根目录
    let displayPath = filePath
    
    // 移除 data/projects/xxx/ 前缀（处理不同的路径分隔符）
    displayPath = displayPath.replace(/^.*data[\\/\\]projects[\\/\\][^\\/\\]+[\\/\\]/, '')
    
    // 使用项目名称作为根目录
    if (project?.name) {
      displayPath = `${project.name}\\${displayPath}`
    }
    
    return displayPath
  }

  useEffect(() => {
    loadFeatures()
  }, [projectId])

  const loadFeatures = async () => {
    try {
      const tree = await getFeatureTree(projectId)
      // 处理后端返回的数据结构
      if (tree) {
        // 创建一个根节点，包含前端和后端功能
        const rootNode = {
          id: 'root',
          name: '项目功能',
          type: 'component' as const,
          category: 'frontend' as const,
          description: '项目功能树',
          file_path: '',
          line_start: 0,
          line_end: 0,
          children: [
            tree.frontend,
            tree.backend
          ],
          metadata: {}
        }
        setFeatureTree(rootNode)
      } else {
        setFeatureTree(null)
      }

      const [frontendData, backendData, apis, models] = await Promise.all([
        getFrontendFeatures(projectId).catch(() => null),
        getBackendFeatures(projectId).catch(() => null),
        getApiEndpoints(projectId).catch(() => []),
        getDataModels(projectId).catch(() => []),
      ])

      // 处理前端功能数据
      if (frontendData && typeof frontendData === 'object' && !Array.isArray(frontendData)) {
        const frontendFeaturesList: any[] = []
        const typedFrontendData = frontendData as any
        if (typedFrontendData.routes) frontendFeaturesList.push(...typedFrontendData.routes)
        if (typedFrontendData.page_functions) {
          Object.values(typedFrontendData.page_functions).forEach((functions: any) => {
            if (Array.isArray(functions)) {
              frontendFeaturesList.push(...functions)
            }
          })
        }
        if (typedFrontendData.api_calls) {
          Object.values(typedFrontendData.api_calls).forEach((calls: any) => {
            if (Array.isArray(calls)) {
              frontendFeaturesList.push(...calls)
            }
          })
        }
        setFrontendFeatures(frontendFeaturesList)
      } else {
        setFrontendFeatures([])
      }

      // 处理后端功能数据
      if (backendData && typeof backendData === 'object' && !Array.isArray(backendData)) {
        const backendFeaturesList: any[] = []
        const typedBackendData = backendData as any
        if (typedBackendData.apis) backendFeaturesList.push(...typedBackendData.apis)
        if (typedBackendData.system_features) backendFeaturesList.push(...typedBackendData.system_features)
        if (typedBackendData.models) backendFeaturesList.push(...typedBackendData.models)
        setBackendFeatures(backendFeaturesList)
      } else {
        setBackendFeatures([])
      }

      setApiEndpoints(apis || [])
      setDataModels(models || [])
    } catch (err) {
      console.error('Failed to load features:', err)
    }
  }

  const renderFeatureTree = (node: FeatureNode, level: number = 0) => {
    const paddingLeft = level * 24
    return (
      <div key={node.id} className="py-2">
        <div 
          className="flex items-center gap-2 py-1 px-2 rounded-lg hover:bg-gray-50 transition-colors cursor-pointer"
          style={{ paddingLeft: `${paddingLeft}px` }}
        >
          <svg className="w-4 h-4 text-blue-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          <span className="text-sm text-gray-900 truncate">{node.name}</span>
          <span className="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full">{node.type}</span>
        </div>
        {node.children && node.children.map((child) => renderFeatureTree(child, level + 1))}
      </div>
    )
  }

  const tabs = [
    { id: 'tree', label: '功能树', icon: '🌳' },
    { id: 'frontend', label: '前端功能', icon: '🎨' },
    { id: 'backend', label: '后端功能', icon: '⚙️' },
    { id: 'apis', label: 'API端点', icon: '🔗' },
    { id: 'models', label: '数据模型', icon: '📊' },
  ]

  if (isLoading && !featureTree) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-200 rounded-full animate-spin border-t-blue-600 mx-auto"></div>
          <p className="mt-3 text-gray-500 text-sm">加载功能分析中...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-6 py-4 rounded-xl">
        {error}
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 border-b border-gray-200/50">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors border-b-2 -mb-px ${
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

      <div className="bg-white/80 backdrop-blur-sm rounded-2xl border border-gray-200/50 p-6">
        {activeTab === 'tree' && (
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">功能树结构</h3>
            {featureTree ? (
              <div className="bg-gray-50 rounded-xl p-4 overflow-auto max-h-96">
                {renderFeatureTree(featureTree)}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">暂无功能树数据</div>
            )}
          </div>
        )}

        {activeTab === 'frontend' && (
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">前端功能 ({frontendFeatures?.length || 0})</h3>
            {frontendFeatures && frontendFeatures.length > 0 ? (
              <div className="space-y-3">
                {(frontendFeatures || []).map((feature) => (
                  <div
                    key={feature.id}
                    className="flex items-center gap-3 p-3 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors"
                  >
                    <svg className="w-5 h-5 text-blue-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z" />
                    </svg>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium text-gray-900">{feature.name}</div>
                      <div className="text-xs text-gray-500">{formatFilePath(feature.file_path)}</div>
                    </div>
                    <span className="text-xs text-blue-600 bg-blue-50 px-2 py-1 rounded-full">{feature.type}</span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">暂无前端功能数据</div>
            )}
          </div>
        )}

        {activeTab === 'backend' && (
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">后端功能 ({backendFeatures?.length || 0})</h3>
            {backendFeatures && backendFeatures.length > 0 ? (
              <div className="space-y-3">
                {(backendFeatures || []).map((feature) => (
                  <div
                    key={feature.id}
                    className="flex items-center gap-3 p-3 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors"
                  >
                    <svg className="w-5 h-5 text-indigo-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                    </svg>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium text-gray-900">{feature.name}</div>
                      <div className="text-xs text-gray-500">{formatFilePath(feature.file_path)}</div>
                    </div>
                    <span className="text-xs text-indigo-600 bg-indigo-50 px-2 py-1 rounded-full">{feature.type}</span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">暂无后端功能数据</div>
            )}
          </div>
        )}

        {activeTab === 'apis' && (
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">API端点 ({apiEndpoints?.length || 0})</h3>
            {apiEndpoints && apiEndpoints.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">方法</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">路径</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">文件</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(apiEndpoints || []).map((api, idx) => (
                      <tr key={idx} className="border-b border-gray-100 hover:bg-gray-50">
                        <td className="px-4 py-3">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            api.method === 'GET' ? 'bg-green-100 text-green-800' :
                            api.method === 'POST' ? 'bg-blue-100 text-blue-800' :
                            api.method === 'PUT' ? 'bg-yellow-100 text-yellow-800' :
                            api.method === 'DELETE' ? 'bg-red-100 text-red-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {api.method}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-900 font-mono">{api.path}</td>
                        <td className="px-4 py-3 text-sm text-gray-500">{formatFilePath(api.file_path)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">暂无API端点数据</div>
            )}
          </div>
        )}

        {activeTab === 'models' && (
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">数据模型 ({dataModels?.length || 0})</h3>
            {dataModels && dataModels.length > 0 ? (
              <div className="grid gap-4">
                {(dataModels || []).map((model, idx) => (
                  <div key={idx} className="p-4 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors">
                    <div className="flex items-center gap-2 mb-2">
                      <svg className="w-5 h-5 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
                      </svg>
                      <span className="text-sm font-semibold text-gray-900">{model.name}</span>
                      <span className="text-xs text-gray-500 ml-auto">{formatFilePath(model.file_path)}</span>
                    </div>
                    <div className="space-y-1">
                      {(model.fields || []).map((field, fieldIdx) => (
                        <div key={fieldIdx} className="flex items-center gap-2 text-sm pl-7">
                          <span className="text-gray-900">{field.name}</span>
                          <span className="text-blue-600 text-xs">{field.type}</span>
                          {field.optional && (
                            <span className="text-gray-400 text-xs">(可选)</span>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">暂无数据模型</div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
