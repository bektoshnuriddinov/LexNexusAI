import { Button } from '@/components/ui/button'
import { deleteDocument } from '@/lib/api'
import type { Document } from '@/types'
import { useState } from 'react'

interface DocumentListProps {
  documents: Document[]
  loading: boolean
}

function StatusBadge({ status }: { status: Document['status'] }) {
  const styles = {
    pending: 'bg-yellow-100 text-yellow-800',
    processing: 'bg-blue-100 text-blue-800',
    completed: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-800',
  }

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${styles[status]}`}>
      {status}
    </span>
  )
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function getFileIcon(fileType: string): string {
  if (fileType.includes('pdf')) return '📄'
  if (fileType.includes('word') || fileType.includes('docx')) return '📝'
  if (fileType.includes('html')) return '🌐'
  if (fileType.includes('markdown')) return '📋'
  return '📄'
}

export function DocumentList({ documents, loading }: DocumentListProps) {
  const [deletingId, setDeletingId] = useState<string | null>(null)

  const handleDelete = async (doc: Document) => {
    if (!confirm(`Delete "${doc.filename}"? This cannot be undone.`)) return

    setDeletingId(doc.id)
    try {
      await deleteDocument(doc.id)
    } catch (error) {
      console.error('Failed to delete document:', error)
    } finally {
      setDeletingId(null)
    }
  }

  if (loading) {
    return <p className="text-sm text-muted-foreground">Loading documents...</p>
  }

  if (documents.length === 0) {
    return (
      <p className="text-sm text-muted-foreground text-center py-8">
        No documents uploaded yet. Upload a file to get started.
      </p>
    )
  }

  return (
    <div className="space-y-2">
      {documents.map(doc => (
        <div
          key={doc.id}
          className="flex items-center justify-between p-3 rounded-lg border bg-card"
        >
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span className="text-lg" title={doc.file_type}>{getFileIcon(doc.file_type)}</span>
              <p className="text-sm font-medium truncate">{doc.filename}</p>
              <StatusBadge status={doc.status} />
            </div>
            <div className="flex items-center gap-3 mt-1">
              <span className="text-xs text-muted-foreground">
                {formatFileSize(doc.file_size)}
              </span>
              {doc.status === 'completed' && (
                <span className="text-xs text-muted-foreground">
                  {doc.chunk_count} chunks
                </span>
              )}
              {doc.status === 'failed' && doc.error_message && (
                <span className="text-xs text-destructive truncate max-w-[200px]">
                  {doc.error_message}
                </span>
              )}
            </div>

            {/* Metadata badges */}
            {doc.metadata && doc.status === 'completed' && (
              <div className="mt-2 flex flex-wrap gap-1.5 text-xs">
                {doc.metadata.document_type && (
                  <span className="px-2 py-0.5 bg-blue-100 text-blue-800 rounded-full">
                    {doc.metadata.document_type}
                  </span>
                )}
                {doc.metadata.topics?.slice(0, 3).map((topic: string) => (
                  <span key={topic} className="px-2 py-0.5 bg-green-100 text-green-800 rounded-full">
                    {topic}
                  </span>
                ))}
                {doc.metadata.programming_languages?.slice(0, 2).map((lang: string) => (
                  <span key={lang} className="px-2 py-0.5 bg-purple-100 text-purple-800 rounded-full">
                    {lang}
                  </span>
                ))}
                {doc.metadata.frameworks_tools?.slice(0, 2).map((tool: string) => (
                  <span key={tool} className="px-2 py-0.5 bg-orange-100 text-orange-800 rounded-full">
                    {tool}
                  </span>
                ))}
                {doc.metadata.technical_level && doc.metadata.technical_level !== 'intermediate' && (
                  <span className="px-2 py-0.5 bg-gray-100 text-gray-800 rounded-full">
                    {doc.metadata.technical_level}
                  </span>
                )}
              </div>
            )}
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => handleDelete(doc)}
            disabled={deletingId === doc.id}
            className="text-muted-foreground hover:text-destructive"
          >
            {deletingId === doc.id ? '...' : 'Delete'}
          </Button>
        </div>
      ))}
    </div>
  )
}
