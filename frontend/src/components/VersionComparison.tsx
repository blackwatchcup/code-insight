import { useState, useEffect, useMemo } from 'react'
import ReactMarkdown from 'react-markdown'
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

interface GitCommit {
  hash: string
  message: string
  author: string
  date: string
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

interface GitDiff {
  commit_1: {
    hash: string
    message: string
    author: string
    date: string
  }
  commit_2: {
    hash: string
    message: string
    author: string
    date: string
  }
  file_changes: {
    added: number
    modified: number
    deleted: number
  }
  changes: Array<{
    type: string
    file: string
    diff?: string
  }>
}

interface VersionComparisonProps {
  projectId: string
  isGitRepo?: boolean
}

export default function VersionComparison({ projectId, isGitRepo = false }: VersionComparisonProps) {
  const [versions, setVersions] = useState<Version[]>([])
  const [selectedVersion1, setSelectedVersion1] = useState<string>('')
  const [selectedVersion2, setSelectedVersion2] = useState<string>('')
  const [diff, setDiff] = useState<VersionDiff | null>(null)
  const [gitDiff, setGitDiff] = useState<GitDiff | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isCreating, setIsCreating] = useState(false)
  const [llmSummary, setLlmSummary] = useState<string | null>(null)
  const [isGeneratingSummary, setIsGeneratingSummary] = useState(false)
  const [newVersionNumber, setNewVersionNumber] = useState('')
  const [newVersionDescription, setNewVersionDescription] = useState('')
  
  // Git相关状态
  const [gitBranches, setGitBranches] = useState<string[]>([])
  const [gitCommits, setGitCommits] = useState<GitCommit[]>([])
  const [selectedCommit1, setSelectedCommit1] = useState<string>('')
  const [selectedCommit2, setSelectedCommit2] = useState<string>('')
  const [isLoadingGit, setIsLoadingGit] = useState(false)
  const [isCreatingGitVersion, setIsCreatingGitVersion] = useState(false)
  const [newGitVersionNumber, setNewGitVersionNumber] = useState('')
  const [newGitVersionDescription, setNewGitVersionDescription] = useState('')
  const [selectedCommitForVersion, setSelectedCommitForVersion] = useState<string>('')
  const [llmExpanded, setLlmExpanded] = useState(false)
    const [expandedFiles, setExpandedFiles] = useState<Set<number>>(new Set())

  useEffect(() => {
    loadVersions()
    loadGitInfo()
  }, [projectId])

  const loadVersions = async () => {
    try {
      const res = await api.get(`/projects/${projectId}/versions`)
      setVersions(res.data.data || [])
    } catch (err) {
      console.error('Failed to load versions:', err)
    }
  }

  const loadGitInfo = async () => {
    try {
      // 尝试加载Git分支和提交记录
      const [branchesRes, commitsRes] = await Promise.all([
        api.get(`/projects/${projectId}/git/branches`).catch(() => ({ data: { code: 400, data: { branches: [] } } })),
        api.get(`/projects/${projectId}/git/commits`).catch(() => ({ data: { code: 400, data: { commits: [] } } }))
      ])
      
      if (branchesRes.data.code === 200) {
        setGitBranches(branchesRes.data.data.branches || [])
      }
      
      if (commitsRes.data.code === 200) {
        setGitCommits(commitsRes.data.data.commits || [])
      }
    } catch (err) {
      console.error('Failed to load Git info:', err)
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

  const handleCreateVersionFromGit = async () => {
    if (!newGitVersionNumber.trim() || !selectedCommitForVersion) {
      alert('请输入版本号并选择Git提交')
      return
    }

    setIsCreatingGitVersion(true)
    try {
      await api.post(`/projects/${projectId}/versions/from-git`, {
        commit_hash: selectedCommitForVersion,
        version_number: newGitVersionNumber,
        description: newGitVersionDescription || null,
      })
      setNewGitVersionNumber('')
      setNewGitVersionDescription('')
      setSelectedCommitForVersion('')
      loadVersions()
      alert('从Git提交创建版本成功')
    } catch (err: any) {
      console.error('Failed to create version from Git:', err)
      alert('创建版本失败: ' + (err.response?.data?.detail || err.message))
    } finally {
      setIsCreatingGitVersion(false)
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
      setGitDiff(null)
    } catch (err: any) {
      console.error('Failed to compare versions:', err)
      alert('版本比较失败: ' + (err.response?.data?.detail || err.message))
    } finally {
      setIsLoading(false)
    }
  }

  const handleCompareGit = async () => {
    if (!selectedCommit1 || !selectedCommit2) {
      alert('请选择两个Git提交进行比较')
      return
    }

    if (selectedCommit1 === selectedCommit2) {
      alert('请选择不同的Git提交进行比较')
      return
    }

    setIsLoading(true)
    try {
      const res = await api.post(`/projects/${projectId}/versions/compare-git`, {
        commit_hash_1: selectedCommit1,
        commit_hash_2: selectedCommit2,
      })
      setGitDiff(res.data.data)
      setDiff(null)
      
      // 调用LLM生成变化说明
      generateLlmSummary(res.data.data)
    } catch (err: any) {
      console.error('Failed to compare Git versions:', err)
      alert('Git版本比较失败: ' + (err.response?.data?.detail || err.message))
    } finally {
      setIsLoading(false)
    }
  }

  const generateLlmSummary = async (gitDiffData: GitDiff) => {
    setIsGeneratingSummary(true)
    try {
      // 构建详细的代码变更信息
      const detailedChanges = gitDiffData.changes.map(change => {
        let changeInfo = `【${change.type === 'added' ? '新增' : change.type === 'modified' ? '修改' : '删除'}】${change.file}`
        if (change.diff) {
          // 提供更完整的diff信息（前1000字符）
          changeInfo += `\n代码变更：\n${change.diff.substring(0, 1000)}${change.diff.length > 1000 ? '\n... (更多内容已省略)' : ''}`
        }
        return changeInfo
      }).join('\n\n')

      // 构建优化的提示信息
      const prompt = `你是一位资深的代码审查专家。请深入分析以下两个Git提交之间的代码变化，提供详细的技术分析报告。

## 提交信息
**提交1 (基准版本):**
- Hash: ${gitDiffData.commit_1.hash.substring(0, 7)}
- 消息: ${gitDiffData.commit_1.message}
- 作者: ${gitDiffData.commit_1.author}
- 日期: ${gitDiffData.commit_1.date}

**提交2 (对比版本):**
- Hash: ${gitDiffData.commit_2.hash.substring(0, 7)}
- 消息: ${gitDiffData.commit_2.message}
- 作者: ${gitDiffData.commit_2.author}
- 日期: ${gitDiffData.commit_2.date}

## 文件变更统计
- 新增文件: ${gitDiffData.file_changes.added} 个
- 修改文件: ${gitDiffData.file_changes.modified} 个
- 删除文件: ${gitDiffData.file_changes.deleted} 个

## 详细代码变更
${detailedChanges}

## 分析要求
请从以下几个维度进行深入分析：

1. **变更概述**: 简要总结这次变更的主要内容和目的
2. **技术实现**: 分析具体的技术实现方式和关键代码逻辑
3. **架构影响**: 评估变更对项目架构的影响（如模块划分、依赖关系等）
4. **潜在风险**: 指出可能存在的问题或需要注意的地方
5. **改进建议**: 如果有更好的实现方式，请提出建议

请使用Markdown格式输出，确保结构清晰、重点突出。`
      
      // 调用LLM API
      const llmRes = await api.post(`/chat/ask`, {
        question: prompt,
        project_id: projectId,
        chat_mode: 'project'
      })
      
      if (llmRes.data.code === 200) {
        setLlmSummary(llmRes.data.data.answer || '无法生成总结')
      } else {
        setLlmSummary('无法生成总结: ' + (llmRes.data.message || '未知错误'))
      }
    } catch (err: any) {
      console.error('Failed to generate LLM summary:', err)
      setLlmSummary('生成总结失败: ' + (err.response?.data?.detail || err.message))
    } finally {
      setIsGeneratingSummary(false)
    }
  }

  const handleCheckoutGitCommit = async (commitHash: string) => {
    if (!confirm(`确定要切换到提交 ${commitHash.substring(0, 7)} 吗？`)) {
      return
    }

    setIsLoadingGit(true)
    try {
      const res = await api.post(`/projects/${projectId}/git/checkout`, {
        commit_hash: commitHash
      })
      if (res.data.code === 200) {
        alert('切换成功！')
        // 刷新Git信息
        loadGitInfo()
      } else {
        alert('切换失败: ' + (res.data.message || '未知错误'))
      }
    } catch (err: any) {
      console.error('Failed to checkout Git commit:', err)
      alert('切换失败: ' + (err.response?.data?.detail || err.message))
    } finally {
      setIsLoadingGit(false)
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai', hour12: false })
  }

  return (
    <div className="space-y-6">
      {/* Git Commits Section */}
      {gitCommits.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Git提交记录 ({gitCommits.length})</h3>
            {gitBranches.length > 0 && (
              <div className="text-sm text-gray-500">
                分支: {gitBranches.join(', ')}
              </div>
            )}
          </div>
          <div className="space-y-3 max-h-96 overflow-auto">
            {gitCommits.map((commit) => (
              <div
                key={commit.hash}
                className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-1">
                    <span className="text-xs font-mono bg-gray-200 px-2 py-0.5 rounded">
                      {commit.hash.substring(0, 7)}
                    </span>
                    <span className="text-sm font-semibold text-gray-900">{commit.message}</span>
                  </div>
                  <div className="flex items-center gap-4 text-xs text-gray-500">
                    <span>作者: {commit.author}</span>
                    <span>{commit.date}</span>
                  </div>
                </div>
                <button
                  onClick={() => handleCheckoutGitCommit(commit.hash)}
                  disabled={isLoadingGit}
                  className="px-3 py-1 text-xs bg-blue-50 text-blue-600 border border-blue-200 rounded hover:bg-blue-100 transition-colors"
                >
                  切换到此版本
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Compare Versions */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">版本对比</h3>
        
        {/* Regular Version Comparison */}
        {versions.length >= 2 && (
          <div className="mb-6">
            <h4 className="text-md font-medium text-gray-700 mb-3">版本对比</h4>
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
          </div>
        )}
        
        {/* Git Commit Comparison */}
        {gitCommits.length >= 2 && (
          <div className="mb-6">
            <h4 className="text-md font-medium text-gray-700 mb-3">Git提交对比</h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              <select
                value={selectedCommit1}
                onChange={(e) => setSelectedCommit1(e.target.value)}
                className="px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">选择提交 1</option>
                {gitCommits.map((commit) => (
                  <option key={commit.hash} value={commit.hash}>
                    {commit.message.substring(0, 50)} ({commit.hash.substring(0, 7)})
                  </option>
                ))}
              </select>
              <select
                value={selectedCommit2}
                onChange={(e) => setSelectedCommit2(e.target.value)}
                className="px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">选择提交 2</option>
                {gitCommits.map((commit) => (
                  <option key={commit.hash} value={commit.hash}>
                    {commit.message.substring(0, 50)} ({commit.hash.substring(0, 7)})
                  </option>
                ))}
              </select>
              <button
                onClick={handleCompareGit}
                disabled={isLoading}
                className="px-6 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg font-medium hover:from-purple-700 hover:to-pink-700 transition-all disabled:opacity-50"
              >
                {isLoading ? '比较中...' : '比较Git提交'}
              </button>
            </div>
          </div>
        )}

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

        {/* Git Diff Results */}
        {gitDiff && (
          <div className="mt-6 space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 bg-red-50 rounded-lg border border-red-200">
                <h4 className="text-sm font-semibold text-red-900 mb-2">提交 1: {gitDiff.commit_1.hash.substring(0, 7)}</h4>
                <div className="text-xs text-red-700 space-y-1">
                  <div>消息: {gitDiff.commit_1.message}</div>
                  <div>作者: {gitDiff.commit_1.author}</div>
                  <div>日期: {gitDiff.commit_1.date}</div>
                </div>
              </div>
              <div className="p-4 bg-green-50 rounded-lg border border-green-200">
                <h4 className="text-sm font-semibold text-green-900 mb-2">提交 2: {gitDiff.commit_2.hash.substring(0, 7)}</h4>
                <div className="text-xs text-green-700 space-y-1">
                  <div>消息: {gitDiff.commit_2.message}</div>
                  <div>作者: {gitDiff.commit_2.author}</div>
                  <div>日期: {gitDiff.commit_2.date}</div>
                </div>
              </div>
            </div>

            <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
              <h4 className="text-sm font-semibold text-blue-900 mb-3">文件变更摘要</h4>
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div className="flex items-center justify-between">
                  <span className="text-blue-700">新增文件:</span>
                  <span className="font-semibold text-green-600">{gitDiff.file_changes.added}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-blue-700">修改文件:</span>
                  <span className="font-semibold text-yellow-600">{gitDiff.file_changes.modified}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-blue-700">删除文件:</span>
                  <span className="font-semibold text-red-600">{gitDiff.file_changes.deleted}</span>
                </div>
              </div>
            </div>

            {/* LLM 生成的变化说明 */}
            <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
              <div className="flex items-center justify-between cursor-pointer" onClick={() => !isGeneratingSummary && setLlmExpanded(!llmExpanded)}>
                <h4 className="text-sm font-semibold text-purple-900 mb-3">
                  {isGeneratingSummary ? '生成变化说明中...' : 'LLM 变化说明'}
                </h4>
                {!isGeneratingSummary && (
                  <span className="text-purple-700">{llmExpanded ? '▼' : '▶'}</span>
                )}
              </div>
              <div className="text-sm text-purple-700">
                {isGeneratingSummary ? (
                  <div className="animate-pulse">正在分析代码变化，请稍候...</div>
                ) : llmSummary ? (
                  !llmExpanded ? (
                    <div className="prose max-w-none">
                      <p>{llmSummary.substring(0, 300)}...</p>
                      <p className="text-xs text-purple-600">点击标题查看完整报告</p>
                    </div>
                  ) : (
                    <div className="prose max-w-none">
                      <ReactMarkdown>{llmSummary}</ReactMarkdown>
                    </div>
                  )
                ) : (
                  <div className="text-gray-500">点击"比较Git提交"按钮后将生成变化说明</div>
                )}
              </div>
            </div>

            {gitDiff.changes.length > 0 && (
          <div className="space-y-4">
            <h4 className="text-sm font-semibold text-gray-900">详细变更</h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* 左侧：文件树 */}
              <div className="md:col-span-1">
                <div className="border rounded-lg p-4 bg-white h-full flex flex-col">
                  <h5 className="text-xs font-semibold text-gray-700 mb-2">变更文件</h5>
                  <div className="space-y-2 overflow-y-auto flex-grow max-h-96">
                    {gitDiff.changes.map((change, idx) => (
                      <div key={idx} className="flex items-center cursor-pointer hover:bg-gray-50 rounded px-2 py-1" onClick={() => document.getElementById(`diff-${idx}`)?.scrollIntoView({ behavior: 'smooth' })}>
                        <span className={`mr-2 text-xs ${change.type === 'added' ? 'text-green-600' : change.type === 'modified' ? 'text-yellow-600' : 'text-red-600'}`}>
                          {change.type === 'added' ? '+' : change.type === 'modified' ? '~' : '-'}
                        </span>
                        <span className="text-xs text-gray-800 truncate">{change.file}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
              
              {/* 右侧：详细diff */}
              <div className="md:col-span-2">
                <div className="border rounded-lg overflow-hidden h-full">
                  <div className="max-h-96 overflow-auto space-y-4 p-4">
                    {gitDiff.changes.map((change, idx) => (
                      <div key={idx} id={`diff-${idx}`} className="border rounded-lg overflow-hidden">
                        {/* 文件标题 */}
                        <div className={`px-4 py-2 font-medium text-sm ${change.type === 'added' ? 'bg-green-50 text-green-800 border-b border-green-200' : change.type === 'modified' ? 'bg-yellow-50 text-yellow-800 border-b border-yellow-200' : 'bg-red-50 text-red-800 border-b border-red-200'}`}>
                          <button className="mr-2" onClick={(e) => {
                            e.stopPropagation();
                            setExpandedFiles(prev => {
                              const newExpanded = new Set(prev);
                              if (newExpanded.has(idx)) {
                                newExpanded.delete(idx);
                              } else {
                                newExpanded.add(idx);
                              }
                              return newExpanded;
                            });
                          }}>
                            {expandedFiles.has(idx) ? '▼' : '▶'}
                          </button>
                          <span className="mr-2">{change.type === 'added' ? '+' : change.type === 'modified' ? '~' : '-'}</span>
                          <span>{change.file}</span>
                        </div>
                        
                        {/* diff内容 */}
                        {change.diff && expandedFiles.has(idx) && (
                          <div className="p-4 bg-gray-50">
                            <pre className="text-xs font-mono overflow-x-auto">
                              {change.diff.split('\n').map((line, lineIdx) => {
                                let lineClass = 'text-gray-700'
                                if (line.startsWith('+')) {
                                  lineClass = 'text-green-600 bg-green-50'
                                } else if (line.startsWith('-')) {
                                  lineClass = 'text-red-600 bg-red-50'
                                } else if (line.startsWith('@@')) {
                                  lineClass = 'text-blue-600 bg-blue-50'
                                }
                                return (
                                  <div key={lineIdx} className={lineClass}>
                                    {line}
                                  </div>
                                )
                              })}
                            </pre>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
          </div>
        )}
      </div>
    </div>
  )
}
