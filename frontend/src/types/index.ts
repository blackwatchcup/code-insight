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
