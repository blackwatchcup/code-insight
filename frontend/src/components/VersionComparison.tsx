import { useState, useEffect } from 'react'
import { api } from '../services/api'

interface Version {
  id: string
  project_id: string
  version_number: string
  description: string | null
  commit_hash: string | null
  created_at: string
  created_by: string | null
  file_count: number
  line_count: number
}

interface VersionDiff {
  version_1: Version
  version_2: Version
  file_count_diff: number
  line_count_diff: number
  changes: Array<{
    type: string
    count: number
    description: string
  }>
}

interface VersionComparisonProps {
  projectId: string
}

export default function VersionComparison({ projectId }: VersionComparisonProps) {
  const [versions, setVersions] = useState<Version[]>([])
  const [selectedVersion1, setSelectedVersion1] = useState<string>('')
  const [selectedVersion2, setSelectedVersion2] = useState<string>('')
  const [diff, setDiff] = useState<VersionDiff | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isCreating, setIsCreating] = useState(false)
  const [newVersionNumber, setNewVersionNumber] = useState('')
  const [newVersionDescription, setNewVersionDescription] = useState('')

  useEffect(() => {
    loadVersions()
  }, [projectId])

  const loadVersions = async () => {
    try {
      const res = await api.get(`/projects/${projectId}/versions`)
      setVersions(res.data.data || [])
    } catch (err) {
      console.error('Failed to load versions:', err)
    }
  }

  const handleCreateVersion = async () => {
    if (!newVersionNumber.trim()) {
      alert('请输入版本号')
      return
    }

    setIsCreating(true)
    try {
      await api.post(`/projects/${projectId}/versions`, {
        version_number: newVersionNumber,
        description: newVersionDescription || null,
      })
      setNewVersionNumber('')
      setNewVersionDescription('')
      loadVersions()
      alert('版本创建成功')
    } catch (err: any) {
      console.error('Failed to create version:', err)
      alert('创建版本失败: ' + (err.response?.data?.detail || err.message))
    } finally {
      setIsCreating(false)
    }
  }

  const handleCompare = async () => {
    if (!selectedVersion1 || !selectedVersion2) {
      alert('请选择两个版本进行比较')
      return
    }

    if (selectedVersion1 === selectedVersion2) {
      alert('请选择不同的版本进行比较')
      return
    }

    setIsLoading(true)
    try {
      const res = await api.post(`/projects/${projectId}/versions/compare`, {
        version_id_1: selectedVersion1,
        version_id_2: selectedVersion2,
      })
      setDiff(res.data.data)
    } catch (err: any) {
      console.error('Failed to compare versions:', err)
      alert('版本比较失败: ' + (err.response?.data?.detail || err.message))
    } finally {
      setIsLoading(false)
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('zh-CN')
  }

  return (
    <div className="space-y-6">
      {/* Create Version Section */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">创建新版本</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <input
            type="text"
            placeholder="版本号 (例如: 1.0.0)"
            value={newVersionNumber}
            onChange={(e) => setNewVersionNumber(e.target.value)}
            className="px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <input
            type="text"
            placeholder="版本描述 (可选)"
            value={newVersionDescription}
            onChange={(e) => setNewVersionDescription(e.target.value)}
            className="px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            onClick={handleCreateVersion}
            disabled={isCreating}
            className="px-6 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-lg font-medium hover:from-blue-700 hover:to-indigo-700 transition-all disabled:opacity-50"
          >
            {isCreating ? '创建中...' : '创建版本'}
          </button>
        </div>
      </div>

      {/* Version List */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">版本列表 ({versions.length})</h3>
        {versions.length === 0 ? (
          <div className="text-center py-8 text-gray-500">暂无版本记录</div>
        ) : (
          <div className="space-y-3">
            {versions.map((version) => (
              <div
                key={version.id}
                className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-1">
                    <span className="text-sm font-semibold text-gray-900">{version.version_number}</span>
                    {version.commit_hash && (
                      <span className="text-xs text-gray-500 font-mono bg-gray-200 px-2 py-0.5 rounded">
                        {version.commit_hash.substring(0, 7)}
                      </span>
                    )}
                  </div>
                  {version.description && (
                    <div className="text-sm text-gray-600 mb-1">{version.description}</div>
                  )}
                  <div className="flex items-center gap-4 text-xs text-gray-500">
                    <span>{formatDate(version.created_at)}</span>
                    <span>{version.file_count} 文件</span>
                    <span>{version.line_count.toLocaleString()} 行代码</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Compare Versions */}
      {versions.length >= 2 && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">版本对比</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <select
              value={selectedVersion1}
              onChange={(e) => setSelectedVersion1(e.target.value)}
              className="px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">选择版本 1</option>
              {versions.map((v) => (
                <option key={v.id} value={v.id}>
                  {v.version_number}
                </option>
              ))}
            </select>
            <select
              value={selectedVersion2}
              onChange={(e) => setSelectedVersion2(e.target.value)}
              className="px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">选择版本 2</option>
              {versions.map((v) => (
                <option key={v.id} value={v.id}>
                  {v.version_number}
                </option>
              ))}
            </select>
            <button
              onClick={handleCompare}
              disabled={isLoading}
              className="px-6 py-2 bg-gradient-to-r from-green-600 to-teal-600 text-white rounded-lg font-medium hover:from-green-700 hover:to-teal-700 transition-all disabled:opacity-50"
            >
              {isLoading ? '比较中...' : '开始比较'}
            </button>
          </div>

          {/* Diff Results */}
          {diff && (
            <div className="mt-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 bg-red-50 rounded-lg border border-red-200">
                  <h4 className="text-sm font-semibold text-red-900 mb-2">版本 1: {diff.version_1.version_number}</h4>
                  <div className="text-xs text-red-700 space-y-1">
                    <div>文件数: {diff.version_1.file_count}</div>
                    <div>代码行数: {diff.version_1.line_count.toLocaleString()}</div>
                    <div>创建时间: {formatDate(diff.version_1.created_at)}</div>
                  </div>
                </div>
                <div className="p-4 bg-green-50 rounded-lg border border-green-200">
                  <h4 className="text-sm font-semibold text-green-900 mb-2">版本 2: {diff.version_2.version_number}</h4>
                  <div className="text-xs text-green-700 space-y-1">
                    <div>文件数: {diff.version_2.file_count}</div>
                    <div>代码行数: {diff.version_2.line_count.toLocaleString()}</div>
                    <div>创建时间: {formatDate(diff.version_2.created_at)}</div>
                  </div>
                </div>
              </div>

              <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                <h4 className="text-sm font-semibold text-blue-900 mb-3">变更摘要</h4>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div className="flex items-center justify-between">
                    <span className="text-blue-700">文件数变化:</span>
                    <span className={`font-semibold ${diff.file_count_diff >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {diff.file_count_diff >= 0 ? '+' : ''}{diff.file_count_diff}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-blue-700">代码行数变化:</span>
                    <span className={`font-semibold ${diff.line_count_diff >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {diff.line_count_diff >= 0 ? '+' : ''}{diff.line_count_diff.toLocaleString()}
                    </span>
                  </div>
                </div>
              </div>

              {diff.changes.length > 0 && (
                <div className="space-y-2">
                  <h4 className="text-sm font-semibold text-gray-900">详细变更</h4>
                  {diff.changes.map((change, idx) => (
                    <div
                      key={idx}
                      className={`p-3 rounded-lg text-sm ${
                        change.type === 'files_added'
                          ? 'bg-green-50 text-green-800 border border-green-200'
                          : 'bg-red-50 text-red-800 border border-red-200'
                      }`}
                    >
                      {change.description}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
