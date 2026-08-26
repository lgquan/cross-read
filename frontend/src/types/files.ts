export type FileKind =
  | 'directory'
  | 'markdown'
  | 'pdf'
  | 'docx'
  | 'spreadsheet'
  | 'presentation'
  | 'image'
  | 'text'
  | 'audio'
  | 'video'
  | 'unsupported'

export interface ShareSummary {
  id: string
  name: string
}

export interface ShareListResponse {
  items: ShareSummary[]
}

export interface FileEntry {
  name: string
  path: string
  kind: FileKind
  is_directory: boolean
  size: number | null
  modified_at: string
}

export interface DirectoryResponse {
  share: ShareSummary
  path: string
  items: FileEntry[]
}

export interface SearchResponse {
  share: ShareSummary
  path: string
  query: string
  items: FileEntry[]
  truncated: boolean
}
