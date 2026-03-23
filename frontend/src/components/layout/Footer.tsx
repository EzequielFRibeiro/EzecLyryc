import { Link } from 'react-router-dom'

export function Footer() {
  return (
    <footer className="footer">
      <div className="container">
        <p>© 2024 Ezequiel Ribeiro. Todos os direitos reservados.</p>
        <nav className="footer-nav">
          <Link to="/credits">Créditos</Link>
          <Link to="/privacy">Política de Privacidade</Link>
          <Link to="/terms">Termos de Serviço</Link>
        </nav>
      </div>
    </footer>
  )
}
