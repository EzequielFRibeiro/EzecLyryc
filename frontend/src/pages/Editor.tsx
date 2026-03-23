import { useParams } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { apiClient } from '@/lib/api'

export function Editor() {
  const { id } = useParams()
  const [transcription, setTranscription] = useState<any>(null)

  useEffect(() => {
    apiClient.get(`/api/transcriptions/${id}`)
      .then(res => setTranscription(res.data))
      .catch(err => console.error(err))
  }, [id])

  if (!transcription) return <div>Carregando...</div>

  return (
    <div className="editor">
      <h1>{transcription.title || 'Editor de Partitura'}</h1>
      <div className="editor-toolbar">
        <button>Salvar</button>
        <button>Exportar</button>
        <button>Play</button>
      </div>
      <div className="notation-display">
        <p>Visualização de partitura (VexFlow será integrado)</p>
        <p>Instrumento: {transcription.instrument_type}</p>
        <p>Status: {transcription.status}</p>
      </div>
    </div>
  )
}
