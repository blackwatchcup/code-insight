import { useState, useEffect } from 'react'
import { api } from '../services/api'

interface GitCommit {
  hash: string
  message: string
  author: string
  date: string
}

interface VersionSwitcherProps {
  projectId: string
  isGitRepo?: boolean
  onVersionChanged?: (commitHash: string) => void
}

export const VersionSwitcher: React.FC<VersionSwitcherProps> = ({ projectId, isGitRepo = false, onVersionChanged }) => {
  const [commits, setCommits] = useState<GitCommit[]>([])
  const [selectedCommit, setSelectedCommit] = useState<string>('')
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    if (isGitRepo) {
      loadGitCommits()
    }
  }, [isGitRepo, projectId])

  const loadGitCommits = async () => {
    try {
      const response = await api.get(`/projects/${projectId}/git/commits?limit=100`)
      if (response.data.code === 200) {
        setCommits(response.data.data.commits || [])
      }
    } catch (err) {
      console.error('Failed to load git commits:', err)
    }
  }

  const handleVersionSwitch = async () => {
    if (!selectedCommit) return

    setIsLoading(true)
    try {
      const response = await api.post(`/projects/${projectId}/git/checkout`, {
        commit_hash: selectedCommit
      })
      
      if (response.data.code === 200) {
        alert('版本切换成功！')
        onVersionChanged?.(selectedCommit)
        // 重新加载Git提交记录，确保显示正确的当前版本
        loadGitCommits()
      } else {
        alert('切换失败: ' + (response.data.message || '未知错误'))
      }
    } catch (err: any) {
      console.error('Failed to checkout git commit:', err)
      alert('切换失败: ' + (err.response?.data?.detail || err.message))
    } finally {
      setIsLoading(false)
    }
  }

  if (!isGitRepo) {
    return null
  }

  return (
    <div className="bg-gray-50 rounded-lg border border-gray-200 p-4 mb-4">
      <div className="flex items-center justify-between mb-2">
        <h4 className="text-sm font-medium text-gray-700">Git版本切换</h4>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <select
          value={selectedCommit}
          onChange={(e) => setSelectedCommit(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">选择Git版本</option>
          {commits.map((commit) => (
            <option key={commit.hash} value={commit.hash}>
              {commit.message.substring(0, 50)} ({commit.hash.substring(0, 7)})
            </option>
          ))}
        </select>
        <button
          onClick={handleVersionSwitch}
          disabled={!selectedCommit || isLoading}
          className="px-4 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-lg font-medium hover:from-blue-700 hover:to-indigo-700 transition-all disabled:opacity-50"
        >
          {isLoading ? '切换中...' : '切换版本'}
        </button>
      </div>
    </div>
  )
}
