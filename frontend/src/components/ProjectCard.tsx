import type { Project } from '../types'

interface ProjectCardProps {
  project: Project
  onDelete: () => void
}

export default function ProjectCard({ project, onDelete }: ProjectCardProps) {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 hover:shadow-md transition-shadow">
      <div className="flex justify-between items-start mb-3">
        <div className="flex-1">
          <h3 className="font-semibold text-gray-900 text-lg">{project.name}</h3>
          <p className="text-sm text-gray-500 mt-1">
            {project.source_type === 'local' ? '本地目录' : project.source_type.toUpperCase()}
          </p>
        </div>
        <button
          onClick={onDelete}
          className="text-red-500 hover:text-red-700 p-1"
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
      
      <div className="space-y-2 text-sm">
        <div className="flex justify-between">
          <span className="text-gray-500">状态</span>
          <span
            className={`px-2 py-0.5 rounded-full text-xs ${
              project.status === 'ready'
                ? 'bg-green-100 text-green-700'
                : project.status === 'error'
                ? 'bg-red-100 text-red-700'
                : 'bg-yellow-100 text-yellow-700'
            }`}
          >
            {project.status === 'ready' ? '就绪' : project.status === 'error' ? '错误' : '索引中'}
          </span>
        </div>
        
        <div className="flex justify-between">
          <span className="text-gray-500">文件数</span>
          <span className="text-gray-900">{project.file_count}</span>
        </div>
        
        <div className="flex justify-between">
          <span className="text-gray-500">代码行数</span>
          <span className="text-gray-900">{project.line_count.toLocaleString()}</span>
        </div>
        
        <div className="flex justify-between">
          <span className="text-gray-500">创建时间</span>
          <span className="text-gray-900">
            {new Date(project.created_at).toLocaleDateString('zh-CN')}
          </span>
        </div>
      </div>
    </div>
  )
}
