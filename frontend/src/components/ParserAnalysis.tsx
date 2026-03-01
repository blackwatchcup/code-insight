import { useEffect, useMemo, useState } from 'react'
import { useParserStore } from '../stores/parserStore'
import type {
  DependencyGraph,
  DependencyTreeNode,
  FileStructure,
  ProjectStructure,
} from '../types'

interface ParserAnalysisProps {
  projectId: string
  project?: {
    name?: string
  }
}

interface ProjectSummary {
  structure?: {
    total_files: number
    total_functions: number
    total_classes: number
    by_language: Record<string, number>
  }
  call_graph?: {
    total_nodes: number
    total_edges: number
    entry_points: number
    leaf_functions: number
  }
  dependencies?: {
    internal_modules: number
    external_modules: number
    internal_edges: number
    external_edges: number
  }
}

interface FileTreeNode {
  name: string
  isFile: boolean
  children: Record<string, FileTreeNode>
  file?: FileStructure
}

const DEFAULT_EXPANDED_DEP_NODES = new Set<string>([
  'dependency-root',
  'group:internal',
  'group:external',
])

export default function ParserAnalysis({ projectId, project }: ParserAnalysisProps) {
  const [activeTab, setActiveTab] = useState('structure')
  const [structure, setStructure] = useState<ProjectStructure | null>(null)
  const [dependencies, setDependencies] = useState<DependencyGraph | null>(null)
  const [summary, setSummary] = useState<ProjectSummary | null>(null)
  const [expandedFiles, setExpandedFiles] = useState<Set<string>>(new Set())
  const [expandedDependencyNodes, setExpandedDependencyNodes] = useState<Set<string>>(
    DEFAULT_EXPANDED_DEP_NODES
  )

  const { getProjectStructure, getDependencies, getProjectSummary, isLoading, error } = useParserStore()

  useEffect(() => {
    setStructure(null)
    setDependencies(null)
    setSummary(null)
    setExpandedFiles(new Set())
    setExpandedDependencyNodes(new Set(DEFAULT_EXPANDED_DEP_NODES))
  }, [projectId])

  useEffect(() => {
    const loadTabData = async () => {
      try {
        if (activeTab === 'structure' && !structure) {
          const struct = await getProjectStructure(projectId)
          setStructure(struct as ProjectStructure)
          return
        }

        if (activeTab === 'dependencies' && !dependencies) {
          const dep = await getDependencies(projectId)
          setDependencies(dep as DependencyGraph)
          return
        }

        if (activeTab === 'summary' && !summary) {
          const sum = await getProjectSummary(projectId)
          setSummary(sum as ProjectSummary)
        }
      } catch (loadErr: unknown) {
        console.error('Failed to load parser tab data:', loadErr)
      }
    }

    void loadTabData()
  }, [
    activeTab,
    projectId,
    structure,
    dependencies,
    summary,
    getProjectStructure,
    getDependencies,
    getProjectSummary,
  ])

  const toggleFile = (key: string) => {
    setExpandedFiles((prev) => {
      const next = new Set(prev)
      if (next.has(key)) {
        next.delete(key)
      } else {
        next.add(key)
      }
      return next
    })
  }

  const toggleDependencyNode = (nodeId: string) => {
    setExpandedDependencyNodes((prev) => {
      const next = new Set(prev)
      if (next.has(nodeId)) {
        next.delete(nodeId)
      } else {
        next.add(nodeId)
      }
      return next
    })
  }

  const buildFileTree = (files: FileStructure[]): Record<string, FileTreeNode> => {
    const root: Record<string, FileTreeNode> = {}

    files.forEach((file) => {
      const displayPath = file.file_path.replace(/^.*data[\\/\\]projects[\\/\\][^\\/\\]+[\\/\\]/, '')
      const parts = displayPath.split(/[\\/]/).filter(Boolean)
      let cursor = root

      parts.forEach((part, index) => {
        if (!cursor[part]) {
          cursor[part] = {
            name: part,
            isFile: index === parts.length - 1,
            children: {},
            file: index === parts.length - 1 ? file : undefined,
          }
        }
        cursor = cursor[part].children
      })
    })

    return root
  }

  const renderFileTree = (node: Record<string, FileTreeNode>, level = 0): JSX.Element[] =>
    Object.entries(node).map(([name, item]) => {
      const key = item.file?.file_path ?? `${level}-${name}`
      const hasChildren = Object.keys(item.children).length > 0
      const isExpanded = expandedFiles.has(key)

      return (
        <div key={key} className="py-0.5">
          <div
            className="flex items-center gap-2 py-1.5 px-2 rounded-lg hover:bg-gray-50 transition-colors cursor-pointer"
            style={{ paddingLeft: `${level * 12 + 8}px` }}
            onClick={() => (hasChildren || item.isFile ? toggleFile(key) : undefined)}
          >
            {hasChildren ? (
              <svg
                className={`w-3 h-3 text-gray-400 flex-shrink-0 transition-transform ${
                  isExpanded ? 'rotate-90' : ''
                }`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            ) : (
              <span className="w-3" />
            )}

            <svg className="w-4 h-4 text-gray-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              {item.isFile ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
              )}
            </svg>

            <span className="text-sm text-gray-900 truncate">
              {project?.name && level === 0 ? `${project.name}\\${name}` : name}
            </span>
          </div>

          {hasChildren && isExpanded && <div className="ml-4">{renderFileTree(item.children, level + 1)}</div>}

          {item.isFile && isExpanded && item.file && (
            <div className="ml-4">
              {item.file.functions.length > 0 && (
                <div className="pl-6">
                  {item.file.functions.slice(0, 10).map((func) => (
                    <div
                      key={`${item.file?.file_path}-func-${func.name}`}
                      className="flex items-center gap-2 py-1 px-2 text-xs text-gray-600 hover:bg-gray-50 rounded"
                    >
                      <svg className="w-3 h-3 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                      </svg>
                      <span className="truncate" title={func.name}>
                        {func.name}
                      </span>
                    </div>
                  ))}
                  {item.file.functions.length > 10 && (
                    <div className="py-1 px-2 text-xs text-gray-400 pl-6">
                      ... 还有 {item.file.functions.length - 10} 个函数
                    </div>
                  )}
                </div>
              )}

              {item.file.classes.length > 0 && (
                <div className="pl-6">
                  {item.file.classes.slice(0, 5).map((cls) => (
                    <div key={`${item.file?.file_path}-class-${cls.name}`} className="py-1">
                      <div className="flex items-center gap-2 py-1 px-2 text-xs text-gray-600 hover:bg-gray-50 rounded font-medium">
                        <svg className="w-3 h-3 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                        </svg>
                        <span>{cls.name}</span>
                      </div>

                      {cls.methods.slice(0, 3).map((method) => (
                        <div
                          key={`${item.file?.file_path}-method-${cls.name}-${method.name}`}
                          className="flex items-center gap-2 py-1 px-2 text-xs text-gray-500 hover:bg-gray-50 rounded pl-6"
                        >
                          <svg className="w-3 h-3 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                          </svg>
                          <span className="truncate" title={method.name}>
                            {method.name}
                          </span>
                        </div>
                      ))}
                    </div>
                  ))}

                  {item.file.classes.length > 5 && (
                    <div className="py-1 px-2 text-xs text-gray-400 pl-6">
                      ... 还有 {item.file.classes.length - 5} 个类
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      )
    })

  const buildFallbackDependencyTree = (data: DependencyGraph): DependencyTreeNode => {
    const internalModules = Object.keys(data.graph.internal_modules)
    const externalModules = Object.keys(data.graph.external_modules)

    const internalDepsMap = new Map<string, Set<string>>()
    const externalDepsMap = new Map<string, Set<string>>()
    const externalUsedByMap = new Map<string, Set<string>>()

    data.graph.internal_edges.forEach((edge) => {
      if (!internalDepsMap.has(edge.source)) {
        internalDepsMap.set(edge.source, new Set())
      }
      internalDepsMap.get(edge.source)?.add(edge.target)
    })

    data.graph.external_edges.forEach((edge) => {
      if (!externalDepsMap.has(edge.source)) {
        externalDepsMap.set(edge.source, new Set())
      }
      externalDepsMap.get(edge.source)?.add(edge.target)

      if (!externalUsedByMap.has(edge.target)) {
        externalUsedByMap.set(edge.target, new Set())
      }
      externalUsedByMap.get(edge.target)?.add(edge.source)
    })

    const internalChildren: DependencyTreeNode[] = internalModules.map((moduleName) => {
      const internalDeps = Array.from(internalDepsMap.get(moduleName) ?? [])
      const externalDeps = Array.from(externalDepsMap.get(moduleName) ?? [])

      const children: DependencyTreeNode[] = []

      if (internalDeps.length > 0) {
        children.push({
          id: `group:internal-imports:${moduleName}`,
          name: '内部依赖',
          type: 'group',
          children: internalDeps.map((depName) => ({
            id: `internal-ref:${moduleName}:${depName}`,
            name: depName,
            type: 'internal_dependency',
            children: [],
          })),
        })
      }

      if (externalDeps.length > 0) {
        children.push({
          id: `group:external-imports:${moduleName}`,
          name: '外部依赖',
          type: 'group',
          children: externalDeps.map((depName) => ({
            id: `external-ref:${moduleName}:${depName}`,
            name: depName,
            type: 'external_dependency',
            children: [],
          })),
        })
      }

      return {
        id: `internal:${moduleName}`,
        name: moduleName,
        type: 'internal_module',
        meta: {
          imports_count: internalDeps.length + externalDeps.length,
          internal_imports: internalDeps.length,
          external_imports: externalDeps.length,
        },
        children,
      }
    })

    const externalChildren: DependencyTreeNode[] = externalModules.map((depName) => ({
      id: `external:${depName}`,
      name: depName,
      type: 'external_module',
      meta: {
        imported_by_count: (externalUsedByMap.get(depName) ?? new Set()).size,
      },
      children: (externalUsedByMap.get(depName) ?? new Set()).size
        ? [
            {
              id: `used-by:${depName}`,
              name: '被内部模块引用',
              type: 'group',
              children: Array.from(externalUsedByMap.get(depName) ?? []).map((source) => ({
                id: `used-by:${depName}:${source}`,
                name: source,
                type: 'used_by_module',
                children: [],
              })),
            },
          ]
        : [],
    }))

    return {
      id: 'dependency-root',
      name: '依赖关系',
      type: 'root',
      meta: {
        internal_modules: internalModules.length,
        external_modules: externalModules.length,
      },
      children: [
        {
          id: 'group:internal',
          name: '内部模块',
          type: 'group',
          meta: { count: internalModules.length },
          children: internalChildren,
        },
        {
          id: 'group:external',
          name: '外部依赖',
          type: 'group',
          meta: { count: externalModules.length },
          children: externalChildren,
        },
      ],
    }
  }

  const dependencyTree = useMemo(() => {
    if (!dependencies) {
      return null
    }
    return buildFallbackDependencyTree(dependencies)
  }, [dependencies])

  const getNodeTheme = (nodeType: DependencyTreeNode['type']): string => {
    if (nodeType === 'root') return 'bg-gradient-to-r from-blue-500 to-indigo-500 text-white border-blue-300'
    if (nodeType === 'group') return 'bg-indigo-50 text-indigo-700 border-indigo-200'
    if (nodeType === 'internal_module') return 'bg-purple-50 text-purple-700 border-purple-200'
    if (nodeType === 'external_module') return 'bg-emerald-50 text-emerald-700 border-emerald-200'
    if (nodeType === 'internal_dependency') return 'bg-purple-100 text-purple-700 border-purple-200'
    if (nodeType === 'external_dependency') return 'bg-green-100 text-green-700 border-green-200'
    if (nodeType === 'used_by_module') return 'bg-cyan-50 text-cyan-700 border-cyan-200'
    return 'bg-gray-100 text-gray-600 border-gray-200'
  }

  const getNodeMetaCount = (node: DependencyTreeNode): number | null => {
    if (typeof node.meta?.count === 'number') return node.meta.count
    if (typeof node.meta?.imports_count === 'number') return node.meta.imports_count
    if (typeof node.meta?.imported_by_count === 'number') return node.meta.imported_by_count
    return null
  }

  const renderDependencyMindmap = (node: DependencyTreeNode): JSX.Element => {
    const hasChildren = node.children.length > 0
    const isExpanded = expandedDependencyNodes.has(node.id)
    const count = getNodeMetaCount(node)

    return (
      <div key={node.id} className="py-1">
        <button
          type="button"
          onClick={() => (hasChildren ? toggleDependencyNode(node.id) : undefined)}
          className={`w-full text-left flex items-center gap-2 px-3 py-2 rounded-lg border transition-colors ${getNodeTheme(
            node.type
          )} ${hasChildren ? 'hover:opacity-90 cursor-pointer' : 'cursor-default'}`}
        >
          {hasChildren ? (
            <svg
              className={`w-3.5 h-3.5 transition-transform ${isExpanded ? 'rotate-90' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          ) : (
            <span className="w-3.5" />
          )}
          <span className="text-sm font-medium truncate">{node.name}</span>
          {count !== null && <span className="ml-auto text-xs opacity-80">{count}</span>}
        </button>

        {hasChildren && isExpanded && (
          <div className="ml-6 mt-1 border-l border-gray-200 pl-4">
            {node.children.map((childNode) => (
              <div key={childNode.id} className="relative">
                <div className="absolute -left-4 top-4 h-px w-4 bg-gray-200" />
                {renderDependencyMindmap(childNode)}
              </div>
            ))}
          </div>
        )}
      </div>
    )
  }

  const tabs = [
    { id: 'structure', label: '项目结构', icon: '📁' },
    { id: 'dependencies', label: '依赖关系', icon: '🔗' },
    { id: 'summary', label: '项目摘要', icon: '📊' },
  ]

  if (error) {
    return <div className="bg-red-50 border border-red-200 text-red-700 px-6 py-4 rounded-xl">{error}</div>
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

      {isLoading && (
        <div className="flex items-center justify-center h-32">
          <div className="text-center">
            <div className="w-8 h-8 border-4 border-blue-200 rounded-full animate-spin border-t-blue-600 mx-auto" />
            <p className="mt-3 text-gray-500 text-sm">加载中...</p>
          </div>
        </div>
      )}

      <div className="bg-white/80 backdrop-blur-sm rounded-2xl border border-gray-200/50 p-6">
        {activeTab === 'structure' && structure && (
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">项目文件结构</h3>
              <div className="flex gap-4 text-sm text-gray-600">
                <span>文件: {structure.summary?.total_files ?? 0}</span>
                <span>函数: {structure.summary?.total_functions ?? 0}</span>
                <span>类: {structure.summary?.total_classes ?? 0}</span>
              </div>
            </div>
            <div className="bg-gray-50 rounded-xl p-4 overflow-auto max-h-96">
              {structure.files.length > 0 ? (
                renderFileTree(buildFileTree(structure.files))
              ) : (
                <div className="text-center py-8 text-gray-500">暂无文件结构数据</div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'dependencies' && dependencies && (
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">依赖关系思维导图</h3>
              <div className="flex gap-4 text-sm text-gray-600">
                <span>内部模块: {dependencies.graph.stats.internal_modules}</span>
                <span>外部依赖: {dependencies.graph.stats.external_modules}</span>
              </div>
            </div>

            <div className="bg-gray-50 rounded-xl p-4">
              {dependencyTree ? (
                <div className="space-y-1">{renderDependencyMindmap(dependencyTree)}</div>
              ) : (
                <div className="text-center py-8 text-gray-500">暂无依赖关系数据</div>
              )}
            </div>

            {dependencies.circular_dependencies.length > 0 && (
              <div className="mt-4 bg-amber-50 border border-amber-200 rounded-xl p-4">
                <h4 className="text-sm font-semibold text-amber-900 mb-3 flex items-center gap-2">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                    />
                  </svg>
                  检测到循环依赖 ({dependencies.circular_dependencies.length})
                </h4>
                <div className="space-y-2">
                  {dependencies.circular_dependencies.slice(0, 5).map((cycle, index) => (
                    <div
                      key={`cycle-${index}`}
                      className="text-xs text-amber-700 font-mono bg-amber-100 rounded p-2 hover:bg-amber-200 transition-colors"
                      title={cycle.join(' → ')}
                    >
                      {cycle.join(' → ')}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'summary' && summary && (
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">项目统计摘要</h3>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {summary.structure && (
                <>
                  <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl p-4">
                    <div className="text-sm text-blue-600 font-medium mb-1">文件总数</div>
                    <div className="text-2xl font-bold text-blue-900">{summary.structure.total_files}</div>
                  </div>
                  <div className="bg-gradient-to-br from-indigo-50 to-indigo-100 rounded-xl p-4">
                    <div className="text-sm text-indigo-600 font-medium mb-1">函数总数</div>
                    <div className="text-2xl font-bold text-indigo-900">{summary.structure.total_functions}</div>
                  </div>
                  <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl p-4">
                    <div className="text-sm text-purple-600 font-medium mb-1">类总数</div>
                    <div className="text-2xl font-bold text-purple-900">{summary.structure.total_classes}</div>
                  </div>
                </>
              )}

              {summary.call_graph && (
                <>
                  <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-xl p-4">
                    <div className="text-sm text-green-600 font-medium mb-1">调用节点</div>
                    <div className="text-2xl font-bold text-green-900">{summary.call_graph.total_nodes}</div>
                  </div>
                  <div className="bg-gradient-to-br from-emerald-50 to-emerald-100 rounded-xl p-4">
                    <div className="text-sm text-emerald-600 font-medium mb-1">调用关系</div>
                    <div className="text-2xl font-bold text-emerald-900">{summary.call_graph.total_edges}</div>
                  </div>
                  <div className="bg-gradient-to-br from-teal-50 to-teal-100 rounded-xl p-4">
                    <div className="text-sm text-teal-600 font-medium mb-1">入口点</div>
                    <div className="text-2xl font-bold text-teal-900">{summary.call_graph.entry_points}</div>
                  </div>
                </>
              )}

              {summary.dependencies && (
                <>
                  <div className="bg-gradient-to-br from-amber-50 to-amber-100 rounded-xl p-4">
                    <div className="text-sm text-amber-600 font-medium mb-1">内部模块</div>
                    <div className="text-2xl font-bold text-amber-900">{summary.dependencies.internal_modules}</div>
                  </div>
                  <div className="bg-gradient-to-br from-orange-50 to-orange-100 rounded-xl p-4">
                    <div className="text-sm text-orange-600 font-medium mb-1">外部依赖</div>
                    <div className="text-2xl font-bold text-orange-900">{summary.dependencies.external_modules}</div>
                  </div>
                </>
              )}
            </div>

            {summary.structure?.by_language && Object.keys(summary.structure.by_language).length > 0 && (
              <div className="mt-4 bg-gray-50 rounded-xl p-4">
                <h4 className="text-sm font-semibold text-gray-900 mb-3">语言分布</h4>
                <div className="space-y-2">
                  {Object.entries(summary.structure.by_language).map(([lang, count]) => {
                    const totalFiles = summary.structure?.total_files ?? 1
                    const percentage = ((count / totalFiles) * 100).toFixed(1)
                    return (
                      <div key={lang} className="flex items-center gap-3">
                        <span className="text-sm text-gray-900 w-24">{lang}</span>
                        <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-gradient-to-r from-blue-500 to-indigo-500 rounded-full"
                            style={{ width: `${(count / totalFiles) * 100}%` }}
                          />
                        </div>
                        <span className="text-sm text-gray-600 w-12 text-right">{count}</span>
                        <span className="text-sm text-gray-500 w-16 text-right">{percentage}%</span>
                      </div>
                    )
                  })}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
