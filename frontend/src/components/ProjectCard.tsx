import type { Project } from '../types'

interface ProjectCardProps {
  project: Project
  onDelete: () => void
}

export default function ProjectCard({ project, onDelete }: ProjectCardProps) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ready':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200'
      case 'error':
        return 'bg-red-50 text-red-700 border-red-200'
      default:
        return 'bg-amber-50 text-amber-700 border-amber-200'
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'ready':
        return '就绪'
      case 'error':
        return '错误'
      default:
        return '索引中'
    }
  }

  const getSourceIcon = (type: string) => {
    if (type === 'local') {
      return (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
        </svg>
      )
    }
    return (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
      </svg>
    )
  }

  return (
    <div className="group bg-white/80 backdrop-blur-sm rounded-2xl border border-gray-200/50 p-5 hover:shadow-xl hover:shadow-blue-500/5 hover:border-blue-200/50 transition-all duration-300 cursor-pointer">
      <div className="flex justify-between items-start mb-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="font-semibold text-gray-900 text-lg truncate">{project.name}</h3>
          </div>
          <div className="flex items-center gap-1.5 text-sm text-gray-500">
            {getSourceIcon(project.source_type)}
            <span>{project.source_type === 'local' ? '本地目录' : project.source_type.toUpperCase()}</span>
          </div>
        </div>
        <button
          onClick={(e) => {
            e.stopPropagation()
            onDelete()
          }}
          className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-500 p-2 rounded-lg hover:bg-red-50 transition-all"
          title="删除项目"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
            />
          </svg>
        </button>
      </div>
      
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-500">状态</span>
          <span className={`px-3 py-1 rounded-full text-xs font-medium border ${getStatusColor(project.status)}`}>
            {getStatusText(project.status)}
          </span>
        </div>
        
        <div className="grid grid-cols-2 gap-3 pt-3 border-t border-gray-100">
          <div className="text-center p-2 bg-gray-50/50 rounded-lg">
            <div className="text-lg font-semibold text-gray-900">{project.file_count}</div>
            <div className="text-xs text-gray-500">文件数</div>
          </div>
          <div className="text-center p-2 bg-gray-50/50 rounded-lg">
            <div className="text-lg font-semibold text-gray-900">{project.line_count.toLocaleString()}</div>
            <div className="text-xs text-gray-500">代码行数</div>
          </div>
        </div>
        
        <div className="flex items-center justify-between text-sm pt-2">
          <span className="text-gray-400">创建于</span>
          <span className="text-gray-600">
            {new Date(project.created_at).toLocaleDateString('zh-CN', {
              year: 'numeric',
              month: 'short',
              day: 'numeric'
            })}
          </span>
        </div>
      </div>
    </div>
  )
}
