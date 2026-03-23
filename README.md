# CifraPartit - Plataforma de Transcrição Musical com IA

Plataforma web profissional que transforma áudio e vídeo em partituras, tablaturas e arquivos MIDI usando IA.

## 🎵 Funcionalidades

- **Transcrição por IA**: Motor especializado detecta notas, ritmo e harmonia
- **8 Instrumentos**: Piano, guitarra, baixo, vocal, bateria, cordas, sopro, metais
- **Upload Flexível**: Arquivo, gravação browser, ou YouTube
- **Editor Online**: Edite partituras diretamente no navegador
- **Export Profissional**: PDF, MusicXML, MIDI, Guitar Pro (GPX/GP5)
- **Assinatura Pro**: Transcrições ilimitadas, fila prioritária, todos os formatos

## 🚀 Tech Stack

**Backend:**
- Python 3.14 + FastAPI
- PostgreSQL + SQLAlchemy
- Redis + Celery (processamento assíncrono)
- librosa (análise de áudio)
- WebSocket (atualizações em tempo real)

**Frontend:**
- React 18 + TypeScript
- Vite
- Zustand (state management)
- TanStack Query
- React Router

## 📦 Instalação

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Celery Worker
```bash
celery -A app.celery_app worker --loglevel=info
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## 🔧 Configuração

### Backend (.env)
```env
DATABASE_URL=postgresql://user:pass@localhost/cifrapartit
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key
S3_BUCKET=your-bucket
```

### Frontend (.env)
```env
VITE_API_BASE_URL=http://localhost:8000
```

## 📊 Tiers

### Free
- 30 segundos de duração
- 3 transcrições por dia
- Export apenas PDF

### Pro
- 15 minutos de duração
- Transcrições ilimitadas
- Todos os formatos de export
- Fila prioritária

## 🧪 Testes

```bash
cd backend
pytest tests/ -v
```

300+ testes passando

## 📝 Licença

© 2024 Ezequiel Ribeiro. Todos os direitos reservados.

## 🤝 Contato

Para suporte ou dúvidas, entre em contato através do formulário no site.
