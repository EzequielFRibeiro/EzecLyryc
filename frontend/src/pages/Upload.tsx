import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { FileUpload } from '@/components/upload/FileUpload'
import { AudioRecorder } from '@/components/upload/AudioRecorder'
import { YouTubeImport } from '@/components/upload/YouTubeImport'
import { InstrumentSelector } from '@/components/upload/InstrumentSelector'
import { apiClient } from '@/lib/api'
import { useUIStore } from '@/stores/uiStore'

export function Upload() {
  const navigate = useNavigate()
  const { addNotification, setLoading } = useUIStore()
  const [uploadMethod, setUploadMethod] = useState<'file' | 'record' | 'youtube'>('file')
  const [fileId, setFileId] = useState<string | null>(null)
  const [instrument, setInstrument] = useState('piano')
  const [melodyOnly, setMelodyOnly] = useState(false)

  const handleStartTranscription = async () => {
    if (!fileId) return

    setLoading(true)
    try {
      const response = await apiClient.post('/api/transcriptions', {
        audio_file_id: fileId,
        instrument_type: instrument,
        melody_only: melodyOnly
      })
      
      addNotification({ type: 'success', message: 'Transcrição iniciada!' })
      navigate(`/transcription/${response.data.id}`)
    } catch (error: any) {
      addNotification({ type: 'error', message: error.response?.data?.detail || 'Erro ao iniciar transcrição' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="upload-page">
      <h1>Nova Transcrição</h1>
      
      <div className="upload-methods">
        <button 
          className={uploadMethod === 'file' ? 'active' : ''}
          onClick={() => setUploadMethod('file')}
        >
          Upload de Arquivo
        </button>
        <button 
          className={uploadMethod === 'record' ? 'active' : ''}
          onClick={() => setUploadMethod('record')}
        >
          Gravar Áudio
        </button>
        <button 
          className={uploadMethod === 'youtube' ? 'active' : ''}
          onClick={() => setUploadMethod('youtube')}
        >
          YouTube
        </button>
      </div>

      <div className="upload-content">
        {uploadMethod === 'file' && <FileUpload onUploadComplete={setFileId} />}
        {uploadMethod === 'record' && <AudioRecorder onRecordingComplete={setFileId} />}
        {uploadMethod === 'youtube' && <YouTubeImport onImportComplete={setFileId} />}
      </div>

      {fileId && (
        <div className="transcription-options">
          <InstrumentSelector value={instrument} onChange={setInstrument} />
          
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={melodyOnly}
              onChange={(e) => setMelodyOnly(e.target.checked)}
            />
            Apenas melodia principal
          </label>

          <button onClick={handleStartTranscription} className="btn-primary">
            Iniciar Transcrição
          </button>
        </div>
      )}
    </div>
  )
}
