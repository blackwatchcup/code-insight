import { useState } from 'react'
import type { ImportData } from '../types'

interface ImportDialogProps {
  isOpen: boolean
  onClose: () => void
  onImport: (data: ImportData) => Promise<void>
  isImporting: boolean
}

type ImportType = 'github' | 'gitlab' | 'gitee' | 'local' | 'zip'

export default function ImportDialog({ isOpen, onClose, onImport, isImporting }: ImportDialogProps) {
  const [type, setType] = useState<ImportType>('github')
  const [name, setName] = useState('')
  const [url, setUrl] = useState('')
  const [branch, setBranch] = useState('main')
  const [token, setToken] = useState('')

  if (!isOpen) return null

  const handleImport = async () => {
    if (!name || (type !== 'local' && !url)) return
    
    await onImport({
      name,
      url,
      source_type: type,
      branch: type === 'local' ? undefined : branch,
      token: type === 'github' ? token : undefined,
    })
    
    if (!isImporting) {
      onClose()
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-lg w-full mx-4">
        <div className="flex justify-between items-center p-6 border-b">
          <h2 className="text-xl font-semibold">导入项目</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>
        
        <div className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">导入类型</label>
            <div className="flex gap-2">
              {(['github', 'gitlab', 'gitee', 'local', 'zip'] as ImportType[]).map((t) => (
                <button
                  key={t}
                  onClick={() => setType(t)}
                  className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                    type === t
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {t === 'local' ? '本地' : t.toUpperCase()}
                </button>
              ))}
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">项目名称</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="输入项目名称"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          
          {type !== 'local' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {type === 'zip' ? 'ZIP文件URL' : '仓库URL'}
              </label>
              <input
                type="text"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder={
                  type === 'zip'
                    ? 'https://example.com/project.zip'
                    : 'https://github.com/user/repo'
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          )}
          
          {type === 'local' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">本地路径</label>
              <input
                type="text"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="/path/to/project"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          )}
          
          {type !== 'zip' && type !== 'local' && (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">分支</label>
                <input
                  type="text"
                  value={branch}
                  onChange={(e) => setBranch(e.target.value)}
                  placeholder="main"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              
              {type === 'github' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Token (可选)</label>
                  <input
                    type="password"
                    value={token}
                    onChange={(e) => setToken(e.target.value)}
                    placeholder="ghp_xxxx"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              )}
            </div>
          )}
        </div>
        
        <div className="flex justify-end gap-3 p-6 border-t">
          <button
            onClick={onClose}
            disabled={isImporting}
            className="px-4 py-2 text-gray-700 hover:text-gray-900 disabled:opacity-50"
          >
            取消
          </button>
          <button
            onClick={handleImport}
            disabled={isImporting || !name || (type !== 'local' && !url)}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isImporting ? '导入中...' : '导入'}
          </button>
        </div>
      </div>
    </div>
  )
}
