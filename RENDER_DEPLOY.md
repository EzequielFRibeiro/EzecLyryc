# 🚀 Deploy no Render.com (SEM CLI!)

## Passo a Passo Visual

### 1. Criar Conta
1. Acesse: https://render.com
2. Clique "Get Started"
3. Login com GitHub

### 2. Conectar Repositório
1. Dashboard → "New +"
2. Selecione "Blueprint"
3. Conecte seu GitHub
4. Selecione repositório: `EzequielFRibeiro/EzecLyryc`
5. Clique "Connect"

### 3. Configurar (Automático!)
O Render vai ler o `render.yaml` e criar:
- ✅ Backend (Web Service)
- ✅ Worker (Celery)
- ✅ PostgreSQL
- ✅ Redis

### 4. Adicionar Variáveis Faltantes
No Dashboard, clique no serviço "cifrapartit-backend":

**Environment → Add Environment Variable:**

```
S3_BUCKET=cifrapartit-storage
S3_ACCESS_KEY=sua-key
S3_SECRET_KEY=sua-secret
S3_ENDPOINT=https://s3.amazonaws.com
SMTP_USER=seu-email@gmail.com
SMTP_PASSWORD=sua-senha-app
```

### 5. Deploy Automático
Render vai fazer deploy automaticamente!

Aguarde 5-10 minutos.

### 6. Obter URL
No Dashboard:
- Clique em "cifrapartit-backend"
- Copie a URL (ex: `https://cifrapartit-backend.onrender.com`)

### 7. Executar Migrations
No Dashboard:
1. Clique em "cifrapartit-backend"
2. Shell → Connect
3. Execute:
```bash
cd backend
alembic upgrade head
```

### 8. Atualizar Netlify
1. Acesse: https://app.netlify.com
2. Seu site → Site settings → Environment variables
3. Editar `VITE_API_BASE_URL`:
   - Value: `https://cifrapartit-backend.onrender.com`
4. Deploys → Trigger deploy

## ✅ Pronto!

Teste:
- Backend: https://cifrapartit-backend.onrender.com/docs
- Frontend: https://seu-site.netlify.app

## 💡 Vantagens do Render
- ✅ Sem CLI
- ✅ Deploy automático no push
- ✅ Free tier generoso
- ✅ PostgreSQL e Redis inclusos
- ✅ SSL automático

## 🆘 Problemas?

**Deploy falha:**
- Verificar logs no Dashboard
- Verificar variáveis de ambiente

**Backend lento na primeira requisição:**
- Normal no free tier (cold start)
- Aguarde 30 segundos

**Migrations não rodam:**
- Executar manualmente no Shell
