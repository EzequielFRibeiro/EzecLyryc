import { useState } from 'react'
import { apiClient } from '@/lib/api'
import { useUIStore } from '@/stores/uiStore'

interface YouTubeImportProps {
  onImportComplete: (fileId: string) => void
}

export function YouTubeImport({ onImportComplete }: YouTubeImportProps) {
  const { addNotification, setLoading } = useUIStore()
  const [url, setUrl] = useState('')
  const [error, setError] = useState('')

  const validateYouTubeUrl = (url: string) => {
    const pattern = /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/.+$/
    return pattern.test(url)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (!url) {
      setError('URL é obrigatória')
      return
    }

    if (!validateYouTubeUrl(url)) {
      setError('URL do YouTube inválida')
      return
    }

    setLoading(true)
    try {
      const response = await apiClient.post('/api/upload/youtube', { url })
      addNotification({ type: 'success', message: 'Áudio extraído com sucesso!' })
      onImportComplete(response.data.file_id)
      setUrl('')
    } catch (error: any) {
      addNotification({ type: 'error', message: error.response?.data?.detail || 'Erro ao extrair áudio' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="youtube-import">
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="youtube-url">URL do YouTube</label>
          <input
            type="text"
            id="youtube-url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://www.youtube.com/watch?v=..."
            className={error ? 'error' : ''}
          />
          {error && <span className="error-message">{error}</span>}
        </div>
        <button type="submit" className="btn-primary">Extrair Áudio</button>
      </form>
      <p className="note">Apenas os primeiros 15 minutos serão extraídos</p>
    </div>
  )
}
