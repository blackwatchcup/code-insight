export interface Project {
  id: string
  name: string
  source_type: string
  source_url?: string
  local_path?: string
  branch?: string
  status: string
  file_count: number
  line_count: number
  is_git_repo?: boolean
  created_at: string
  updated_at: string
}

export interface ImportData {
  name: string
  url: string
  source_type: 'github' | 'gitlab' | 'gitee' | 'local' | 'zip'
  branch?: string
  token?: string
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: string
  sources?: ChatSource[]
  chat_mode?: 'project' | 'freeform'
}

export interface ChatSession {
  id: string
  title: string
  project_id?: string
  chat_mode?: 'project' | 'freeform'
  created_at: string
  updated_at: string
  message_count?: number
  last_message?: string
}

export interface ChatSource {
  file_path: string
  content: string
  score: number
}

export interface FeatureNode {
  id: string
  name: string
  type: string
  file_path: string
  children?: FeatureNode[]
  metadata?: Record<string, any>
}

export interface FeatureTree {
  id: string
  project_id: string
  root: FeatureNode
  summary: {
    total_features: number
    by_type: Record<string, number>
  }
}

export interface APIEndpoint {
  path: string
  method: string
  handler?: string
  file_path: string
  line: number
  description?: string
  auth_required?: boolean
  params?: Array<{
    name: string
    type: string
    required: boolean
  }>
  request_body?: string
  response_model?: string
  tags?: string[]
}

export interface DataModel {
  name: string
  file_path: string
  line_number: number
  fields: Array<{
    name: string
    type: string
    optional: boolean
  }>
}

export interface FeatureInsightStat {
  name: string
  count: number
}

export interface FeaturePageAnalysis {
  name: string
  file_path: string
  highlights: string[]
  route_count?: number
  page_function_count?: number
  api_call_count?: number
  api_count?: number
  model_count?: number
  system_feature_count?: number
  auth_api_count?: number
  top_types?: FeatureInsightStat[]
  top_api_methods?: FeatureInsightStat[]
  top_system_features?: FeatureInsightStat[]
  sample_routes?: string[]
  sample_api_paths?: string[]
}

export interface FeatureInsightsSection {
  overview: string
  metrics: Record<string, number>
  top_files: FeatureInsightStat[]
  highlights: string[]
  page_analyses?: FeaturePageAnalysis[]
  top_types?: FeatureInsightStat[]
  top_api_methods?: FeatureInsightStat[]
  top_api_groups?: FeatureInsightStat[]
  top_system_features?: FeatureInsightStat[]
  sample_routes?: string[]
}

export interface FeatureInsightsData {
  frontend: FeatureInsightsSection
  backend: FeatureInsightsSection
  llm: {
    enabled: boolean
    frontend_summary: string
    backend_summary: string
    model: string
    error: string
  }
}

export interface ProjectStructure {
  project_path: string
  summary: {
    total_files: number
    total_functions: number
    total_classes: number
    total_imports: number
    by_language: Record<string, number>
  }
  files: FileStructure[]
}

export interface FileStructure {
  file_path: string
  language: string
  functions: FunctionInfo[]
  classes: ClassInfo[]
  imports: string[]
}

export interface FunctionInfo {
  name: string
  signature: string
  line_number: number
  docstring?: string
}

export interface ClassInfo {
  name: string
  line_number: number
  methods: FunctionInfo[]
  docstring?: string
}

export interface CallGraphNode {
  id: string
  name: string
  file_path: string
  type: string
}

export interface CallGraphEdge {
  source: string
  target: string
  type: string
}

export interface CallGraph {
  nodes: CallGraphNode[]
  edges: CallGraphEdge[]
  entry_points: string[]
  leaf_functions: string[]
}

export interface DependencyModuleNode {
  name: string
  file_path: string
  is_external: boolean
}

export interface DependencyEdge {
  source: string
  target: string
  imports: string[]
  is_external: boolean
}

export interface DependencyTreeNode {
  id: string
  name: string
  type:
    | 'root'
    | 'group'
    | 'internal_module'
    | 'external_module'
    | 'internal_dependency'
    | 'external_dependency'
    | 'used_by_module'
    | 'truncated'
  children: DependencyTreeNode[]
  meta?: Record<string, number>
}

export interface DependencyGraphData {
  internal_modules: Record<string, DependencyModuleNode>
  external_modules: Record<string, DependencyModuleNode>
  internal_edges: DependencyEdge[]
  external_edges: DependencyEdge[]
  stats: {
    internal_modules: number
    external_modules: number
    internal_edges: number
    external_edges: number
  }
}

export interface DependencyGraph {
  graph: DependencyGraphData
  dependency_tree?: DependencyTreeNode
  circular_dependencies: string[][]
  most_depended_on: Array<{ module: string; count: number }>
  most_dependent: Array<{ module: string; count: number }>
}

// 智能聊天相关类型
export type SmartChatMode = 'smart' | 'full_context' | 'code_only' | 'documentation'

export interface SmartChatResponse {
  answer: string
  mode: SmartChatMode
  context_used: string[]
  data_needs: {
    needs: string[]
    search_keywords: string[]
    reason: string
  }
  sources: ChatSource[]
  confidence: number
  metadata: Record<string, any>
}

export interface ProjectContext {
  project_id: string
  project_name: string
  has_readme: boolean
  has_summary: boolean
  tech_stack: string[]
  file_count: number
  line_count: number
  source_type?: string
  branch?: string
}
