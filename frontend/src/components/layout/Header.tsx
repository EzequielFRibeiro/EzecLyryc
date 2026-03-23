import { Link } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'

export function Header() {
  const { user, logout } = useAuthStore()

  return (
    <header className="header">
      <div className="container">
        <Link to="/" className="logo">
          <h1>CifraPartit</h1>
        </Link>
        
        <nav className="nav">
          <Link to="/piano">Piano</Link>
          <Link to="/guitarra">Guitarra</Link>
          <Link to="/vocal">Vocal</Link>
          <Link to="/bateria">Bateria</Link>
          <Link to="/cordas">Cordas</Link>
          <Link to="/sopro">Sopro</Link>
          
          {user ? (
            <>
              <Link to="/dashboard">Dashboard</Link>
              <button onClick={logout}>Sair</button>
            </>
          ) : (
            <>
              <Link to="/login">Entrar</Link>
              <Link to="/register">Registrar</Link>
            </>
          )}
        </nav>
      </div>
    </header>
  )
}
