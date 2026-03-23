import { useParams } from 'react-router-dom'

const instrumentInfo: Record<string, { title: string; description: string }> = {
  piano: {
    title: 'Transcrição para Piano',
    description: 'Transcreva músicas de piano com notação em pauta dupla (clave de sol e fá)'
  },
  guitarra: {
    title: 'Transcrição para Guitarra',
    description: 'Gere tablaturas e partituras para guitarra de 6 cordas'
  },
  vocal: {
    title: 'Transcrição Vocal',
    description: 'Extraia melodias vocais e letras de músicas'
  },
  bateria: {
    title: 'Transcrição para Bateria',
    description: 'Notação de percussão para bateria completa'
  },
  cordas: {
    title: 'Transcrição para Cordas',
    description: 'Violino, viola, violoncelo e contrabaixo'
  },
  sopro: {
    title: 'Transcrição para Sopro',
    description: 'Flauta, clarinete, saxofone, trompete e outros'
  }
}

export function InstrumentPage() {
  const { instrument } = useParams<{ instrument: string }>()
  const info = instrument ? instrumentInfo[instrument] : null
  
  if (!info) {
    return <div>Instrumento não encontrado</div>
  }
  
  return (
    <div className="instrument-page">
      <h1>{info.title}</h1>
      <p>{info.description}</p>
      <p>Página de instrumento em construção - Task 28</p>
    </div>
  )
}
