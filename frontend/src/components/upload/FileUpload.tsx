import { useState, useRef } from 'react'
import { apiClient } from '@/lib/api'
import { useUIStore } from '@/stores/uiStore'

interface FileUploadProps {
  onUploadComplete: (fileId: string) => void
}

export function FileUpload({ onUploadComplete }: FileUploadProps) {
  const { addNotification, setLoading } = useUIStore()
  const [dragActive, setDragActive] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0])
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0])
    }
  }

  const handleFile = async (file: File) => {
    const maxSize = 100 * 1024 * 1024 // 100MB
    const validFormats = ['audio/mpeg', 'audio/wav', 'audio/flac', 'audio/ogg', 'audio/m4a', 'audio/aac', 'video/mp4', 'video/avi', 'video/quicktime', 'video/webm']
    
    if (file.size > maxSize) {
      addNotification({ type: 'error', message: 'Arquivo muito grande. Máximo 100MB' })
      return
    }
    
    if (!validFormats.includes(file.type)) {
      addNotification({ type: 'error', message: 'Formato não suportado' })
      return
    }

    setLoading(true)
    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await apiClient.post('/api/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          const progress = progressEvent.total 
            ? Math.round((progressEvent.loaded * 100) / progressEvent.total)
            : 0
          setUploadProgress(progress)
        }
      })
      
      addNotification({ type: 'success', message: 'Upload concluído!' })
      onUploadComplete(response.data.file_id)
    } catch (error: any) {
      addNotification({ type: 'error', message: error.response?.data?.detail || 'Erro no upload' })
    } finally {
      setLoading(false)
      setUploadProgress(0)
    }
  }

  return (
    <div className="file-upload">
      <div 
        className={`drop-zone ${dragActive ? 'active' : ''}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          onChange={handleChange}
          accept="audio/*,video/*"
          style={{ display: 'none' }}
        />
        <p>Arraste um arquivo ou clique para selecionar</p>
        <p className="formats">MP3, WAV, FLAC, OGG, M4A, AAC, MP4, AVI, MOV, WEBM</p>
      </div>
      
      {uploadProgress > 0 && (
        <div className="progress-bar">
          <div className="progress-fill" style={{ width: `${uploadProgress}%` }} />
          <span>{uploadProgress}%</span>
        </div>
      )}
    </div>
  )
}
