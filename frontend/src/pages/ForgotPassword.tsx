import { useState } from 'react'
import { Link } from 'react-router-dom'
import { apiClient } from '@/lib/api'
import { useUIStore } from '@/stores/uiStore'

export function ForgotPassword() {
  const { addNotification, setLoading } = useUIStore()
  
  const [email, setEmail] = useState('')
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [submitted, setSubmitted] = useState(false)

  const validateForm = () => {
    const newErrors: Record<string, string> = {}
    
    if (!email) {
      newErrors.email = 'Email é obrigatório'
    } else if (!/\S+@\S+\.\S+/.test(email)) {
      newErrors.email = 'Email inválido'
    }
    
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!validateForm()) return
    
    setLoading(true)
    
    try {
      await apiClient.post('/api/auth/request-password-reset', { email })
      
      setSubmitted(true)
      addNotification({
        type: 'success',
        message: 'Email de recuperação enviado! Verifique sua caixa de entrada.'
      })
    } catch (error: any) {
      addNotification({
        type: 'error',
        message: error.response?.data?.detail || 'Erro ao solicitar recuperação'
      })
    } finally {
      setLoading(false)
    }
  }

  if (submitted) {
    return (
      <div className="auth-page">
        <div className="auth-container">
          <h1>Email Enviado</h1>
          <p>Enviamos um link de recuperação para {email}</p>
          <p>Verifique sua caixa de entrada e siga as instruções.</p>
          <Link to="/login" className="btn-primary">Voltar para Login</Link>
        </div>
      </div>
    )
  }

  return (
    <div className="auth-page">
      <div className="auth-container">
        <h1>Recuperar Senha</h1>
        <p>Digite seu email para receber um link de recuperação</p>
        
        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className={errors.email ? 'error' : ''}
            />
            {errors.email && <span className="error-message">{errors.email}</span>}
          </div>
          
          <button type="submit" className="btn-primary">
            Enviar Link de Recuperação
          </button>
        </form>
        
        <div className="auth-links">
          <Link to="/login">Voltar para Login</Link>
        </div>
      </div>
    </div>
  )
}
