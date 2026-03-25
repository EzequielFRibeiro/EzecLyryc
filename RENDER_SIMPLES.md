# 🚀 Deploy GRÁTIS no Render.com

## ✅ 100% Grátis - Sem Cartão

### Passo 1: Criar Conta
1. https://render.com
2. Sign up com GitHub
3. Autorizar acesso

### Passo 2: Deploy Backend
1. Dashboard → "New +"
2. "Web Service"
3. Connect repository: `EzequielFRibeiro/EzecLyryc`
4. Configurar:
   - **Name**: cifrapartit-backend
   - **Root Directory**: `backend`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free

### Passo 3: Adicionar PostgreSQL (Grátis)
1. Dashboard → "New +"
2. "PostgreSQL"
3. Name: cifrapartit-db
4. Plan: Free
5. Create

### Passo 4: Adicionar Redis (Grátis)
1. Dashboard → "New +"
2. "Redis"
3. Name: cifrapartit-redis
4. Plan: Free
5. Create

### Passo 5: Conectar Database ao Backend
1. Clique no backend service
2. Environment → Add Environment Variable
3. Adicionar:

```
DATABASE_URL=internal-connection-string-do-postgres
REDIS_URL=internal-connection-string-do-redis
SECRET_KEY=gere-com-python-secrets
S3_BUCKET=cifrapartit
S3_ACCESS_KEY=sua-key
S3_SECRET_KEY=sua-secret
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seu-email
SMTP_PASSWORD=senha-app
```

### Passo 6: Obter URLs
- PostgreSQL: Settings → Connections → Internal Database URL
- Redis: Settings → Connections → Internal Redis URL

### Passo 7: Deploy!
Render faz deploy automático.

### Passo 8: Migrations
1. Backend service → Shell
2. Execute:
```bash
alembic upgrade head
```

### Passo 9: Copiar URL Backend
Settings → copie a URL (ex: `https://cifrapartit-backend.onrender.com`)

### Passo 10: Atualizar Netlify
1. Netlify → Site settings → Environment variables
2. `VITE_API_BASE_URL` = URL do Render
3. Trigger deploy

## ✅ Pronto!

**Vantagens Render:**
- ✅ 100% grátis
- ✅ PostgreSQL grátis
- ✅ Redis grátis
- ✅ Sem cartão
- ✅ Deploy automático
- ✅ SSL grátis

**Desvantagem:**
- ⏱️ Cold start (30s na primeira requisição)

## 🎉 Seu App Completo

- Frontend: Netlify (grátis)
- Backend: Render (grátis)
- Database: Render PostgreSQL (grátis)
- Cache: Render Redis (grátis)
