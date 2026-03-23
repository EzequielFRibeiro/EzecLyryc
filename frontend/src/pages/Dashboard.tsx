import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { apiClient } from '@/lib/api'
import { useTranscriptionStore } from '@/stores/transcriptionStore'

export function Dashboard() {
  const { transcriptions, setTranscriptions } = useTranscriptionStore()
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState('')

  useEffect(() => {
    apiClient.get('/api/transcriptions', {
      params: { search, instrument_type: filter }
    })
      .then(res => setTranscriptions(res.data.items))
      .catch(err => console.error(err))
  }, [search, filter])

  return (
    <div className="dashboard">
      <h1>Minhas Transcrições</h1>
      
      <div className="dashboard-controls">
        <input 
          type="text" 
          placeholder="Buscar..." 
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select value={filter} onChange={(e) => setFilter(e.target.value)}>
          <option value="">Todos</option>
          <option value="piano">Piano</option>
          <option value="guitar">Guitarra</option>
          <option value="vocals">Vocal</option>
        </select>
        <Link to="/upload" className="btn-primary">Nova Transcrição</Link>
      </div>

      <div className="transcription-list">
        {transcriptions.map(t => (
          <div key={t.id} className="transcription-card">
            <h3>{t.title}</h3>
            <p>{t.instrument_type} - {t.duration}s</p>
            <Link to={`/editor/${t.id}`}>Editar</Link>
          </div>
        ))}
      </div>
    </div>
  )
}
