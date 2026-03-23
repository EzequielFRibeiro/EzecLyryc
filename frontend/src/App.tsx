import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Layout } from './components/layout/Layout'
import { ProtectedRoute } from './components/ProtectedRoute'
import { Home } from './pages/Home'
import { Login } from './pages/Login'
import { Register } from './pages/Register'
import { ForgotPassword } from './pages/ForgotPassword'
import { ResetPassword } from './pages/ResetPassword'
import { Upload } from './pages/Upload'
import { TranscriptionStatus } from './pages/TranscriptionStatus'
import { Dashboard } from './pages/Dashboard'
import { Editor } from './pages/Editor'
import { InstrumentPage } from './pages/InstrumentPage'

const queryClient = new QueryClient()

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Home />} />
            <Route path="login" element={<Login />} />
            <Route path="register" element={<Register />} />
            <Route path="forgot-password" element={<ForgotPassword />} />
            <Route path="reset-password" element={<ResetPassword />} />
            
            <Route path="piano" element={<InstrumentPage />} />
            <Route path="guitarra" element={<InstrumentPage />} />
            <Route path="vocal" element={<InstrumentPage />} />
            <Route path="bateria" element={<InstrumentPage />} />
            <Route path="cordas" element={<InstrumentPage />} />
            <Route path="sopro" element={<InstrumentPage />} />
            
            <Route path="upload" element={<ProtectedRoute><Upload /></ProtectedRoute>} />
            <Route path="transcription/:id" element={<ProtectedRoute><TranscriptionStatus /></ProtectedRoute>} />
            <Route path="dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
            <Route path="editor/:id" element={<ProtectedRoute><Editor /></ProtectedRoute>} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App
