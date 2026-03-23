# 🚀 Quick Start - Git + Vercel

## 1️⃣ Git Setup (5 minutos)

```bash
# Inicializar e fazer primeiro commit
git init
git add .
git commit -m "Initial commit: CifraPartit MVP completo"

# Criar repositório no GitHub
# Acesse: https://github.com/new
# Nome: cifrapartit-music-transcription

# Conectar e push
git remote add origin https://github.com/SEU_USUARIO/cifrapartit-music-transcription.git
git branch -M main
git push -u origin main
```

## 2️⃣ Deploy Frontend no Vercel (3 minutos)

### Opção A: Via Dashboard (Recomendado)
1. Acesse https://vercel.com
2. Clique "Add New Project"
3. Importe seu repositório GitHub
4. Configure:
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
5. Adicione variável de ambiente:
   - `VITE_API_BASE_URL` = `https://seu-backend.railway.app`
6. Clique "Deploy"

### Opção B: Via CLI
```bash
cd frontend
npm i -g vercel
vercel login
vercel --prod
```

## 3️⃣ Deploy Backend no Railway (5 minutos)

```bash
# Instalar Railway CLI
npm i -g @railway/cli

# Login
railway login

# Criar projeto
cd backend
railway init

# Adicionar PostgreSQL
railway add --database postgresql

# Adicionar Redis
railway add --database redis

# Deploy
railway up

# Configurar variáveis de ambiente no dashboard
# https://railway.app/dashboard
```

### Variáveis de Ambiente (Railway)
```
SECRET_KEY=seu-secret-key-aqui
S3_BUCKET=seu-bucket
S3_ACCESS_KEY=sua-key
S3_SECRET_KEY=sua-secret
SMTP_HOST=smtp.gmail.com
SMTP_USER=seu-email
SMTP_PASSWORD=sua-senha
```

## 4️⃣ Configurar Celery Worker (Railway)

1. No Railway Dashboard
2. Criar novo serviço do mesmo repositório
3. Configurar:
   - **Start Command**: `celery -A app.celery_app worker --loglevel=info`
   - Mesmas variáveis de ambiente do backend

## 5️⃣ Atualizar Frontend com URL do Backend

No Vercel Dashboard:
1. Settings → Environment Variables
2. Editar `VITE_API_BASE_URL`
3. Valor: URL do Railway (ex: `https://cifrapartit-backend.railway.app`)
4. Redeploy

## ✅ Verificar Deploy

```bash
# Frontend
curl https://seu-app.vercel.app

# Backend
curl https://seu-backend.railway.app/api/health

# Testar no navegador
https://seu-app.vercel.app
```

## 🎉 Pronto!

Seu app está no ar:
- Frontend: https://seu-app.vercel.app
- Backend: https://seu-backend.railway.app

## 📝 Próximos Passos

1. Configurar domínio customizado
2. Configurar monitoramento (Sentry)
3. Configurar analytics
4. Testar todas as funcionalidades
5. Compartilhar com usuários!

## 🆘 Problemas Comuns

**Build falha no Vercel:**
- Verificar se `frontend/` está correto como Root Directory
- Verificar se todas as dependências estão no package.json

**Backend não conecta ao DB:**
- Verificar variáveis de ambiente no Railway
- Verificar se PostgreSQL foi adicionado

**CORS error:**
- Adicionar domínio do Vercel nas configurações de CORS do backend

**Celery não processa:**
- Verificar se Redis está conectado
- Verificar logs do worker no Railway
