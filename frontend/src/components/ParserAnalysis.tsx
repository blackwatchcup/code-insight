import { useState, useEffect } from 'react'
import { useParserStore } from '../stores/parserStore'
import type { ProjectStructure, CallGraph, DependencyGraph } from '../types'

interface ParserAnalysisProps {
  projectId: string
}

export default function ParserAnalysis({ projectId }: ParserAnalysisProps) {
  const [activeTab, setActiveTab] = useState('structure')
  const [structure, setStructure] = useState<ProjectStructure | null>(null)
  const [callGraph, setCallGraph] = useState<CallGraph | null>(null)
  const [dependencies, setDependencies] = useState<DependencyGraph | null>(null)
  const [summary, setSummary] = useState<any>(null)
  const [expandedFiles, setExpandedFiles] = useState<Set<string>>(new Set())
  
  const { getProjectStructure, getCallGraph, getDependencies, getProjectSummary, isLoading, error } = useParserStore()

  useEffect(() => {
    loadTabData(activeTab)
  }, [projectId, activeTab])

  const loadTabData = async (tab: string) => {
    switch (tab) {
      case 'structure':
        if (!structure) {
          try {
            const struct = await getProjectStructure(projectId)
            setStructure(struct)
          } catch (err) {
            console.error('Failed to load structure:', err)
          }
        }
        break
      case 'callgraph':
        if (!callGraph) {
          try {
            const graph = await getCallGraph(projectId)
            setCallGraph(graph)
          } catch (err) {
            console.error('Failed to load call graph:', err)
          }
        }
        break
      case 'dependencies':
        if (!dependencies) {
          try {
            const dep = await getDependencies(projectId)
            setDependencies(dep)
          } catch (err) {
            console.error('Failed to load dependencies:', err)
          }
        }
        break
      case 'summary':
        if (!summary) {
          try {
            const sum = await getProjectSummary(projectId)
            setSummary(sum)
          } catch (err) {
            console.error('Failed to load summary:', err)
          }
        }
        break
    }
  }

  const toggleFile = (filePath: string) => {
    const newExpanded = new Set(expandedFiles)
    if (newExpanded.has(filePath)) {
      newExpanded.delete(filePath)
    } else {
      newExpanded.add(filePath)
    }
    setExpandedFiles(newExpanded)
  }

  const renderFileStructure = (files: any[], level: number = 0) => {
    return files.slice(0, 100).map((file, idx) => {
      const hasChildren = (file.functions && file.functions.length > 0) || (file.classes && file.classes.length > 0)
      const isExpanded = expandedFiles.has(file.file_path)
      
      return (
        <div key={`${file.file_path}-${idx}`} className="py-0.5">
          <div 
            className="flex items-center gap-2 py-1.5 px-2 rounded-lg hover:bg-gray-50 transition-colors cursor-pointer"
            style={{ paddingLeft: `${level * 12 + 8}px` }}
            onClick={() => hasChildren && toggleFile(file.file_path)}
          >
            {hasChildren && (
              <svg className={`w-3 h-3 text-gray-400 flex-shrink-0 transition-transform ${isExpanded ? 'rotate-90' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            )}
            <svg className="w-4 h-4 text-gray-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <span className="text-sm text-gray-900 truncate">{file.file_path}</span>
          </div>
          {isExpanded && (
            <>
               {file.functions && file.functions.length > 0 && (
                <div className="pl-6">
                  {file.functions.slice(0, 10).map((func: any, fIdx: number) => (
                    <div key={fIdx} className="flex items-center gap-2 py-1 px-2 text-xs text-gray-600 hover:bg-gray-50 rounded">
                      <svg className="w-3 h-3 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                      </svg>
                      <span className="truncate" title={func.name}>{func.name}</span>
                    </div>
                  ))}
                  {file.functions.length > 10 && (
                    <div className="py-1 px-2 text-xs text-gray-400 pl-6">
                      ... 还有 {file.functions.length - 10} 个函数
                    </div>
                  )}
                </div>
              )}
              {file.classes && file.classes.length > 0 && (
                <div className="pl-6">
                  {file.classes.slice(0, 5).map((cls: any, cIdx: number) => (
                    <div key={cIdx} className="py-1">
                      <div className="flex items-center gap-2 py-1 px-2 text-xs text-gray-600 hover:bg-gray-50 rounded font-medium">
                        <svg className="w-3 h-3 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                        </svg>
                        <span>{cls.name}</span>
                      </div>
                      {cls.methods && cls.methods.slice(0, 3).map((method: any, mIdx: number) => (
                        <div key={mIdx} className="flex items-center gap-2 py-1 px-2 text-xs text-gray-500 hover:bg-gray-50 rounded pl-6">
                          <svg className="w-3 h-3 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                          </svg>
                          <span className="truncate" title={method.name}>{method.name}</span>
                        </div>
                      ))}
                    </div>
                  ))}
                  {file.classes.length > 5 && (
                    <div className="py-1 px-2 text-xs text-gray-400 pl-6">
                      ... 还有 {file.classes.length - 5} 个类
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      )
    })
  }

  const tabs = [
    { id: 'structure', label: '项目结构', icon: '📁' },
    { id: 'callgraph', label: '调用图', icon: '🔀' },
    { id: 'dependencies', label: '依赖关系', icon: '🔗' },
    { id: 'summary', label: '项目摘要', icon: '📊' },
  ]

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-6 py-4 rounded-xl">
        {error}
      </div>
    )
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
            <div className="w-8 h-8 border-4 border-blue-200 rounded-full animate-spin border-t-blue-600 mx-auto"></div>
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
                <span>文件: {structure.summary.total_files}</span>
                <span>函数: {structure.summary.total_functions}</span>
                <span>类: {structure.summary.total_classes}</span>
              </div>
            </div>
            <div className="bg-gray-50 rounded-xl p-4 overflow-auto max-h-96">
              {structure.files.length > 0 ? renderFileStructure(structure.files) : (
                <div className="text-center py-8 text-gray-500">暂无文件结构数据</div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'callgraph' && callGraph && (
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">函数调用关系</h3>
              <div className="flex gap-4 text-sm text-gray-600">
                <span>节点: {callGraph.nodes.length}</span>
                <span>边: {callGraph.edges.length}</span>
                <span>入口点: {callGraph.entry_points.length}</span>
              </div>
            </div>
            <div className="grid gap-4">
               <div className="bg-gray-50 rounded-xl p-4">
                 <h4 className="text-sm font-semibold text-gray-900 mb-3">入口函数 ({callGraph.entry_points.length})</h4>
                 {callGraph.entry_points.length > 0 ? (
                   <div className="flex flex-wrap gap-2">
                     {callGraph.entry_points.slice(0, 20).map((entry, idx) => (
                       <span key={idx} className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 hover:bg-blue-200 transition-colors" title={entry}>
                         {entry}
                       </span>
                     ))}
                     {callGraph.entry_points.length > 20 && (
                       <div className="text-xs text-gray-500 self-center py-1.5">
                         ... 还有 {callGraph.entry_points.length - 20} 个入口点
                       </div>
                     )}
                   </div>
                 ) : (
                   <div className="text-sm text-gray-500">暂无入口点</div>
                 )}
               </div>
               <div className="bg-gray-50 rounded-xl p-4">
                 <h4 className="text-sm font-semibold text-gray-900 mb-3">函数节点</h4>
                 {callGraph.nodes.length > 0 ? (
                   <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2 max-h-80 overflow-auto">
                     {callGraph.nodes.slice(0, 50).map((node, idx) => {
                       const isEntryPoint = callGraph.entry_points.includes(node.id || node.name)
                       const edgeCount = callGraph.edges.filter(
                         (e: any) => e.source === (node.id || node.name)
                       ).length
                       
                       return (
                         <div 
                           key={idx} 
                           className="flex items-center gap-2 p-2 text-xs bg-white rounded-lg border border-gray-200 hover:border-blue-300 hover:shadow-md transition-all"
                           title={`${node.name} - ${edgeCount} 个调用`}
                         >
                           <span className="flex-1 truncate font-medium text-gray-900">{node.name}</span>
                           <span className="text-gray-400">{node.type}</span>
                           <span className="text-blue-600 font-semibold">{edgeCount}</span>
                           {isEntryPoint && (
                             <span className="text-green-600">🚀</span>
                           )}
                         </div>
                       )
                     })}
                  </div>
                ) : (
                  <div className="text-sm text-gray-500">暂无函数节点</div>
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'dependencies' && dependencies && (
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">依赖关系分析</h3>
              <div className="flex gap-4 text-sm text-gray-600">
                <span>内部模块: {dependencies.internal_modules.length}</span>
                <span>外部依赖: {dependencies.external_modules.length}</span>
              </div>
            </div>
            <div className="grid gap-4">
              <div className="bg-gray-50 rounded-xl p-4">
                <h4 className="text-sm font-semibold text-gray-900 mb-3">内部模块 ({dependencies.internal_modules.length})</h4>
                {dependencies.internal_modules.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {dependencies.internal_modules.slice(0, 20).map((mod, idx) => (
                      <span key={idx} className="inline-flex items-center px-3 py-1.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800 hover:bg-purple-200 transition-colors" title={`模块: ${mod}`}>
                        {mod}
                      </span>
                    ))}
                    {dependencies.internal_modules.length > 20 && (
                      <div className="text-xs text-gray-500 self-center py-1.5">
                        ... 还有 {dependencies.internal_modules.length - 20} 个模块
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-sm text-gray-500">暂无内部模块</div>
                )}
              </div>
              <div className="bg-gray-50 rounded-xl p-4">
                <h4 className="text-sm font-semibold text-gray-900 mb-3">外部依赖 ({dependencies.external_modules.length})</h4>
                {dependencies.external_modules.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {dependencies.external_modules.slice(0, 20).map((dep, idx) => (
                      <span key={idx} className="inline-flex items-center px-3 py-1.5 rounded-full text-xs font-medium bg-green-100 text-green-800 hover:bg-green-200 transition-colors" title={`依赖: ${dep}`}>
                        {dep}
                      </span>
                    ))}
                    {dependencies.external_modules.length > 20 && (
                      <div className="text-xs text-gray-500 self-center py-1.5">
                        ... 还有 {dependencies.external_modules.length - 20} 个依赖
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-sm text-gray-500">暂无外部依赖</div>
                )}
              </div>
              {(dependencies.graph?.circular_dependencies || []).length > 0 && (
                <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
                  <h4 className="text-sm font-semibold text-amber-900 mb-3 flex items-center gap-2">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                    检测到循环依赖 ({(dependencies.graph?.circular_dependencies || []).length})
                  </h4>
                  <div className="space-y-2">
                    {(dependencies.graph?.circular_dependencies || []).slice(0,5).map((cycle: any, idx: number) => (
                      <div key={idx} className="text-xs text-amber-700 font-mono bg-amber-100 rounded p-2 hover:bg-amber-200 transition-colors" title={cycle.join(' → ')}>
                        {cycle.join(' → ')}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
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
                  {Object.entries(summary.structure.by_language).map(([lang, count]: [string, any]) => (
                    <div key={lang} className="flex items-center gap-3">
                      <span className="text-sm text-gray-900 w-24">{lang}</span>
                      <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-gradient-to-r from-blue-500 to-indigo-500 rounded-full"
                          style={{ width: `${(count / summary.structure.total_files) * 100}%` }}
                        ></div>
                      </div>
                      <span className="text-sm text-gray-600 w-12 text-right">{count}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
