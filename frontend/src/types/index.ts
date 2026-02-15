export interface Thread {
  id: string
  user_id: string
  title: string
  created_at: string
  updated_at: string
}

export interface Message {
  id: string
  thread_id: string
  user_id: string
  role: 'user' | 'assistant'
  content: string
  created_at: string
}

export interface Document {
  id: string
  user_id: string
  filename: string
  file_type: string
  file_size: number
  storage_path: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  error_message: string | null
  chunk_count: number
  content_hash?: string | null
  metadata?: {
    document_type?: string
    topics?: string[]
    programming_languages?: string[]
    frameworks_tools?: string[]
    date_references?: string | null
    key_entities?: string[]
    summary?: string
    technical_level?: string
  } | null
  created_at: string
  updated_at: string
}
