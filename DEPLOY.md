# Guia de Deploy - CifraPartit

## 🚀 Deploy no Vercel (Frontend)

### 1. Preparar Frontend
```bash
cd frontend
npm run build
```

### 2. Deploy via Vercel CLI
```bash
npm i -g vercel
vercel login
vercel --prod
```

### 3. Ou via GitHub
1. Push para GitHub
2. Conecte repositório no Vercel Dashboard
3. Configure build:
   - Framework: Vite
   - Root Directory: `frontend`
   - Build Command: `npm run build`
   - Output Directory: `dist`

### 4. Variáveis de Ambiente (Vercel)
```
VITE_API_BASE_URL=https://your-backend-url.com
```

## 🐳 Deploy Backend (Railway/Render/Heroku)

### Railway
```bash
# Instalar Railway CLI
npm i -g @railway/cli

# Login
railway login

# Criar projeto
railway init

# Deploy
railway up
```

### Variáveis de Ambiente (Backend)
```
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
SECRET_KEY=...
S3_BUCKET=...
S3_ACCESS_KEY=...
S3_SECRET_KEY=...
SMTP_HOST=...
SMTP_USER=...
SMTP_PASSWORD=...
```

## 📦 Serviços Necessários

### PostgreSQL
- Railway PostgreSQL
- Supabase
- Neon

### Redis
- Upstash Redis
- Railway Redis
- Redis Cloud

### S3 Storage
- AWS S3
- Cloudflare R2
- DigitalOcean Spaces

### Celery Worker
- Deploy separado como worker
- Mesmo código do backend
- Comando: `celery -A app.celery_app worker`

## 🔧 Configuração Pós-Deploy

1. Executar migrations:
```bash
alembic upgrade head
```

2. Testar endpoints:
```bash
curl https://your-api.com/api/health
```

3. Configurar domínio customizado no Vercel

4. Configurar CORS no backend para domínio do Vercel

## 📊 Monitoramento

- Vercel Analytics (frontend)
- Sentry (error tracking)
- Logs do Railway/Render

## 🔒 Segurança

- [ ] HTTPS habilitado
- [ ] Variáveis de ambiente configuradas
- [ ] CORS configurado corretamente
- [ ] Rate limiting ativo
- [ ] Secrets rotacionados

## ✅ Checklist Final

- [ ] Frontend buildando sem erros
- [ ] Backend rodando em produção
- [ ] Database migrations aplicadas
- [ ] Redis conectado
- [ ] S3 configurado
- [ ] Celery worker rodando
- [ ] Variáveis de ambiente configuradas
- [ ] Domínio configurado
- [ ] SSL/HTTPS ativo
- [ ] Testes passando
