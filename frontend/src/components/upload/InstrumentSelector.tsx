interface InstrumentSelectorProps {
  value: string
  onChange: (instrument: string) => void
  preselected?: string
}

const instruments = [
  { value: 'piano', label: 'Piano' },
  { value: 'guitar', label: 'Guitarra' },
  { value: 'bass', label: 'Baixo' },
  { value: 'vocals', label: 'Vocal' },
  { value: 'drums', label: 'Bateria' },
  { value: 'strings', label: 'Cordas' },
  { value: 'woodwinds', label: 'Sopro' },
  { value: 'brass', label: 'Metais' }
]

export function InstrumentSelector({ value, onChange, preselected }: InstrumentSelectorProps) {
  return (
    <div className="instrument-selector">
      <label>Instrumento</label>
      <div className="instrument-grid">
        {instruments.map(inst => (
          <button
            key={inst.value}
            type="button"
            className={`instrument-btn ${value === inst.value ? 'active' : ''}`}
            onClick={() => onChange(inst.value)}
          >
            {inst.label}
          </button>
        ))}
      </div>
    </div>
  )
}
