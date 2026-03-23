import { Link } from 'react-router-dom'

export function Home() {
  return (
    <div className="home">
      <section className="hero">
        <h1>Transforme Áudio em Partituras com IA</h1>
        <p>Transcrição musical profissional para todos os instrumentos</p>
        <Link to="/register" className="cta-button">Começar Gratuitamente</Link>
      </section>
      
      <section className="features">
        <h2>Recursos Principais</h2>
        <div className="feature-grid">
          <div className="feature">
            <h3>Transcrição por IA</h3>
            <p>Motor de IA especializado detecta notas, ritmo e harmonia</p>
          </div>
          <div className="feature">
            <h3>Múltiplos Instrumentos</h3>
            <p>Piano, guitarra, baixo, vocal, bateria, cordas e sopro</p>
          </div>
          <div className="feature">
            <h3>Editor Online</h3>
            <p>Edite partituras diretamente no navegador</p>
          </div>
          <div className="feature">
            <h3>Exportação Profissional</h3>
            <p>PDF, MusicXML, MIDI, Guitar Pro</p>
          </div>
        </div>
      </section>
    </div>
  )
}
