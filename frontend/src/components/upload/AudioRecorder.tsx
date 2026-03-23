import { useState, useRef, useEffect } from 'react'
import { apiClient } from '@/lib/api'
import { useUIStore } from '@/stores/uiStore'

interface AudioRecorderProps {
  onRecordingComplete: (fileId: string) => void
}

export function AudioRecorder({ onRecordingComplete }: AudioRecorderProps) {
  const { addNotification, setLoading } = useUIStore()
  const [isRecording, setIsRecording] = useState(false)
  const [duration, setDuration] = useState(0)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const timerRef = useRef<number>()

  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [])

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream)
      mediaRecorderRef.current = mediaRecorder
      chunksRef.current = []

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data)
      }

      mediaRecorder.onstop = handleRecordingStop

      mediaRecorder.start()
      setIsRecording(true)
      setDuration(0)

      timerRef.current = setInterval(() => {
        setDuration(prev => {
          if (prev >= 600) { // 10 min
            stopRecording()
            return prev
          }
          return prev + 1
        })
      }, 1000)
    } catch (error) {
      addNotification({ type: 'error', message: 'Erro ao acessar microfone' })
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop()
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop())
      setIsRecording(false)
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }

  const handleRecordingStop = async () => {
    const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
    const formData = new FormData()
    formData.append('file', blob, 'recording.webm')

    setLoading(true)
    try {
      const response = await apiClient.post('/api/upload/recording', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      addNotification({ type: 'success', message: 'Gravação enviada!' })
      onRecordingComplete(response.data.file_id)
    } catch (error: any) {
      addNotification({ type: 'error', message: error.response?.data?.detail || 'Erro ao enviar gravação' })
    } finally {
      setLoading(false)
    }
  }

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  return (
    <div className="audio-recorder">
      <div className="recorder-display">
        {isRecording && <div className="recording-indicator" />}
        <span className="duration">{formatTime(duration)}</span>
      </div>
      
      <button 
        onClick={isRecording ? stopRecording : startRecording}
        className={isRecording ? 'btn-stop' : 'btn-record'}
      >
        {isRecording ? 'Parar Gravação' : 'Iniciar Gravação'}
      </button>
    </div>
  )
}
