import { useState, useEffect } from 'react'
import { FeatureTree } from '@/components/features/FeatureTree'
import { MermaidChart } from '@/components/mermaid/MermaidChart'
import { api } from '@/services/api'

interface Props {
  projectId: string
}

interface FeatureNode {
  id: string
  name: string
  type: string
  category: string
  description: string
  file_path: string
  line_start: number
  line_end: number
  children: FeatureNode[]
  metadata: Record<string, any>
}

interface FeatureTreeData {
  project_id: string
  frontend: FeatureNode
  backend: FeatureNode
}

interface ArchitectureData {
  type: string
  format: 'mermaid' | 'markdown' | 'text'
  content: string
  source: string
}

export function Features({ projectId }: Props) {
  const [featureTree, setFeatureTree] = useState<FeatureTreeData | null>(null)
  const [selectedFeature, setSelectedFeature] = useState<FeatureNode | null>(null)
  const [activeTab, setActiveTab] = useState<'frontend' | 'backend'>('frontend')
  const [architectureData, setArchitectureData] = useState<ArchitectureData | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    fetchFeatures()
  }, [projectId, activeTab])

  const fetchFeatures = async () => {
    try {
      setLoading(true)
      const res = await api.get(`/features/${projectId}`)
      setFeatureTree(res.data.data)
    } catch (err) {
      console.error('Failed to fetch features:', err)
    } finally {
      setLoading(false)
    }
  }

  const generateArchitecture = async () => {
    try {
      setLoading(true)
      const res = await api.get(`/graph/${projectId}/architecture`)
      setArchitectureData(res.data.data)
    } catch (err) {
      console.error('Failed to generate architecture:', err)
    } finally {
      setLoading(false)
    }
  }

  const renderArchitecture = () => {
    if (!architectureData) return null

    if (architectureData.format === 'mermaid') {
      return (
        <div className="border border-gray-200 rounded-lg p-4 bg-white">
          <h3 className="text-lg font-semibold mb-3">架构图</h3>
          <p className="text-sm text-gray-500 mb-2">
            {architectureData.source === 'llm' ? '由AI生成的架构图' : '基于功能树生成的架构图'}
          </p>
          <MermaidChart code={architectureData.content} className="w-full" />
        </div>
      )
    }

    if (architectureData.format === 'markdown' || architectureData.format === 'text') {
      return (
        <div className="border border-gray-200 rounded-lg p-4 bg-white overflow-auto" style={{ maxHeight: '600px' }}>
          <h3 className="text-lg font-semibold mb-3">架构描述</h3>
          <p className="text-sm text-gray-500 mb-2">
            {architectureData.source === 'llm' ? '由AI生成的架构分析' : '架构信息'}
          </p>
          <div className="prose prose-sm max-w-none">
            <pre className="whitespace-pre-wrap text-sm bg-gray-50 p-4 rounded-lg">
              {architectureData.content}
            </pre>
          </div>
        </div>
      )
    }

    return null
  }

  const renderFeatureDetail = (feature: FeatureNode) => {
    return (
      <div className="space-y-4">
        <div>
          <h4 className="text-lg font-semibold mb-2">{feature.name}</h4>
          <p className="text-gray-600 mb-3">{feature.description}</p>

          {feature.file_path && (
            <div className="text-sm text-gray-500">
              <span>文件: </span>
              <code className="bg-gray-100 px-2 py-1 rounded">{feature.file_path}</code>
              {feature.line_start > 0 && <span>: 第 {feature.line_start} 行</span>}
            </div>
          )}

          {feature.metadata && Object.keys(feature.metadata).length > 0 && (
            <div className="mt-4 p-4 bg-gray-50 rounded-lg">
              <h5 className="font-medium mb-2">元数据</h5>
              <pre className="text-sm overflow-auto">
                {JSON.stringify(feature.metadata, null, 2)}
              </pre>
            </div>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold mb-4">功能分析</h2>

        <div className="mb-4">
          <div className="flex border-b mb-4">
            <button
              className={`flex-1 py-2 text-center transition-colors ${
                activeTab === 'frontend'
                  ? 'border-b-2 border-blue-600 text-blue-600 font-medium'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
              onClick={() => setActiveTab('frontend')}
            >
              前端
            </button>
            <button
              className={`flex-1 py-2 text-center transition-colors ${
                activeTab === 'backend'
                  ? 'border-b-2 border-blue-600 text-blue-600 font-medium'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
              onClick={() => setActiveTab('backend')}
            >
              后端
            </button>
          </div>
        </div>

        <div className="mb-4">
          <button
            onClick={generateArchitecture}
            disabled={loading}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? '生成中...' : '生成架构图'}
          </button>
        </div>
      </div>

      <div className="flex gap-6">
        {/* 左侧树形结构 */}
        <div className="w-96 flex-shrink-0 border border-gray-200 rounded-lg overflow-auto" style={{ maxHeight: '600px' }}>
          {loading ? (
            <div className="p-4 text-center text-gray-500">加载中...</div>
          ) : featureTree ? (
            <FeatureTree
              data={activeTab === 'frontend' ? featureTree.frontend : featureTree.backend}
              onSelect={setSelectedFeature}
            />
          ) : (
            <div className="p-4 text-center text-gray-500">暂无数据</div>
          )}
        </div>

        {/* 右侧详情 */}
        <div className="flex-1 overflow-auto" style={{ maxHeight: '600px' }}>
          {selectedFeature ? (
            <div className="p-4 border border-gray-200 rounded-lg">
              {renderFeatureDetail(selectedFeature)}
            </div>
          ) : architectureData ? (
            renderArchitecture()
          ) : (
            <div className="flex items-center justify-center h-full text-gray-500">
              选择一个功能查看详情，或点击"生成架构图"按钮查看项目架构
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
