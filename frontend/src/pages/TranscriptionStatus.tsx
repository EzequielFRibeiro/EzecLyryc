import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { apiClient } from '@/lib/api'
import { useUIStore } from '@/stores/uiStore'

export function TranscriptionStatus() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { addNotification } = useUIStore()
  const [status, setStatus] = useState<any>(null)
  const [progress, setProgress] = useState(0)

  useEffect(() => {
    let ws: WebSocket
    
    const connectWebSocket = () => {
      ws = new WebSocket(`ws://localhost:8000/ws/transcription/${id}`)
      
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data)
        setProgress(data.progress || 0)
        
        if (data.status === 'completed') {
          addNotification({ type: 'success', message: 'Transcrição concluída!' })
          navigate(`/editor/${id}`)
        } else if (data.status === 'failed') {
          addNotification({ type: 'error', message: data.error || 'Erro na transcrição' })
        }
      }
      
      ws.onerror = () => {
        addNotification({ type: 'error', message: 'Erro na conexão WebSocket' })
      }
    }

    const fetchStatus = async () => {
      try {
        const response = await apiClient.get(`/api/transcriptions/${id}`)
        setStatus(response.data)
        
        if (response.data.status === 'completed') {
          navigate(`/editor/${id}`)
        } else if (response.data.status === 'processing' || response.data.status === 'queued') {
          connectWebSocket()
        }
      } catch (error: any) {
        addNotification({ type: 'error', message: 'Erro ao buscar status' })
      }
    }

    fetchStatus()
    
    return () => {
      if (ws) ws.close()
    }
  }, [id])

  return (
    <div className="transcription-status">
      <h1>Processando Transcrição</h1>
      
      <div className="status-card">
        <div className="status-icon">
          {status?.status === 'queued' && '⏳'}
          {status?.status === 'processing' && '🎵'}
        </div>
        
        <p className="status-text">
          {status?.status === 'queued' && 'Na fila...'}
          {status?.status === 'processing' && 'Processando...'}
        </p>
        
        <div className="progress-bar">
          <div className="progress-fill" style={{ width: `${progress}%` }} />
        </div>
        <span className="progress-text">{progress}%</span>
      </div>
    </div>
  )
}
