import { useState, useEffect } from 'react'
import { MermaidChart } from '@/components/mermaid/MermaidChart'
import { api } from '@/services/api'

interface Props {
  projectId: string
}

interface FileNode {
  path: string
  name: string
}

export function FlowChart({ projectId }: Props) {
  const [flowData, setFlowData] = useState('')
  const [loading, setLoading] = useState(false)
  const [selectedFile, setSelectedFile] = useState('')
  const [files, setFiles] = useState<FileNode[]>([])
  const [error, setError] = useState('')

  useEffect(() => {
    fetchFiles()
  }, [projectId])

  const fetchFiles = async () => {
    try {
      const res = await api.get(`/projects/${projectId}/files`)
      const fileData = res.data.data
      // 提取Python和JavaScript文件
      const codeFiles = fileData.filter((f: any) =>
        f.path?.endsWith('.py') || f.path?.endsWith('.js') || f.path?.endsWith('.ts') || f.path?.endsWith('.tsx')
      )
      setFiles(codeFiles)
    } catch (err) {
      console.error('Failed to fetch files:', err)
    }
  }

  const generateFlow = async () => {
    if (!selectedFile) return

    setLoading(true)
    setError('')

    try {
      const res = await api.get(`/graph/${projectId}/flow`, {
        params: { file_path: selectedFile }
      })
      setFlowData(res.data.data.content)
    } catch (err: any) {
      console.error('Failed to generate flowchart:', err)
      setError(err.response?.data?.detail || '生成流程图失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold mb-4">流程图生成</h2>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              选择文件
            </label>
            <select
              value={selectedFile}
              onChange={e => setSelectedFile(e.target.value)}
              className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              disabled={files.length === 0}
            >
              <option value="">请选择文件...</option>
              {files.map(file => (
                <option key={file.path} value={file.path}>
                  {file.path}
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={generateFlow}
            disabled={!selectedFile || loading}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? '生成中...' : '生成流程图'}
          </button>

          {error && (
            <div className="text-red-600 bg-red-50 p-3 rounded-lg border border-red-200">
              {error}
            </div>
          )}
        </div>
      </div>

      {flowData && (
        <div className="border border-gray-200 rounded-lg p-4 bg-white">
          <h3 className="text-lg font-semibold mb-3">流程图</h3>
          <MermaidChart code={flowData} className="w-full" />
        </div>
      )}
    </div>
  )
}
