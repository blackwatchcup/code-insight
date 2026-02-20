import { useState, useEffect } from 'react'
import { useProjectStore } from '../stores/projectStore'
import ProjectCard from '../components/ProjectCard'
import ImportDialog from '../components/ImportDialog'

export default function Projects() {
  const { projects, isLoading, error, fetchProjects, importProject, deleteProject, isImporting } =
    useProjectStore()
  const [isDialogOpen, setIsDialogOpen] = useState(false)

  useEffect(() => {
    fetchProjects()
  }, [fetchProjects])

  const handleImport = async (data: {
    name: string
    url: string
    source_type: 'github' | 'gitlab' | 'gitee' | 'local' | 'zip'
    branch?: string
    token?: string
  }) => {
    await importProject({
      name: data.name,
      url: data.url,
      source_type: data.source_type,
      branch: data.branch,
      token: data.token,
    })
  }

  const handleDeleteProject = async (id: string) => {
    if (window.confirm('确定要删除这个项目吗？')) {
      await deleteProject(id)
    }
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      </div>
    )
  }

  return (
    <div className="p-6">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">项目列表</h2>
          <p className="text-gray-600 mt-1">管理您的代码分析项目</p>
        </div>
        <button
          onClick={() => setIsDialogOpen(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors flex items-center gap-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 4v16m8-8H4"
            />
          </svg>
          导入项目
        </button>
      </div>

      {isLoading ? (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      ) : projects.length === 0 ? (
        <div className="text-center py-16">
          <div className="text-gray-400 mb-4">
            <svg
              className="mx-auto h-16 w-16"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1}
                d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"
              />
            </svg>
          </div>
          <div className="text-gray-500 text-lg font-medium">暂无项目</div>
          <p className="text-gray-400 mt-2">导入项目开始分析代码</p>
          <button
            onClick={() => setIsDialogOpen(true)}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            导入您的第一个项目
          </button>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {projects.map((project) => (
            <ProjectCard
              key={project.id}
              project={project}
              onDelete={() => handleDeleteProject(project.id)}
            />
          ))}
        </div>
      )}

      <ImportDialog
        isOpen={isDialogOpen}
        onClose={() => setIsDialogOpen(false)}
        onImport={handleImport}
        isImporting={isImporting}
      />
    </div>
  )
}
