# 🚀 Setup Completo - CifraPartit

## ✅ JÁ FEITO
- [x] Código no GitHub
- [x] Frontend no Netlify (funcionando)

## 📋 FALTA FAZER

### 1️⃣ Deploy Backend (Railway)

```bash
# Instalar Railway CLI
npm install -g @railway/cli

# Login (abre navegador)
railway login

# Ir para backend
cd backend

# Criar projeto
railway init
# Nome sugerido: cifrapartit-backend

# Adicionar PostgreSQL
railway add --database postgresql

# Adicionar Redis
railway add --database redis

# Deploy
railway up
```

### 2️⃣ Configurar Variáveis de Ambiente (Railway Dashboard)

Acesse: https://railway.app/dashboard

Clique no projeto → Variables → Add Variable

**Copie e cole cada linha:**

```
SECRET_KEY=cole-aqui-o-resultado-do-comando-abaixo
S3_BUCKET=cifrapartit-storage
S3_ACCESS_KEY=sua-key-aqui
S3_SECRET_KEY=sua-secret-aqui
S3_ENDPOINT=https://s3.amazonaws.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seu-email@gmail.com
SMTP_PASSWORD=sua-senha-app-gmail
```

**Gerar SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3️⃣ Executar Migrations

```bash
railway run alembic upgrade head
```

### 4️⃣ Obter URL do Backend

```bash
railway domain
```

Ou no Dashboard: Settings → Domains → copie a URL

Exemplo: `https://cifrapartit-backend.up.railway.app`

### 5️⃣ Configurar Frontend (Netlify)

Acesse: https://app.netlify.com

1. Clique no seu site
2. Site settings → Environment variables
3. Add variable:
   - Key: `VITE_API_BASE_URL`
   - Value: `https://sua-url-do-railway.up.railway.app`
4. Save

### 6️⃣ Redeploy Frontend

No Netlify:
1. Deploys → Trigger deploy → Deploy site

Ou via Git:
```bash
git commit --allow-empty -m "Trigger redeploy"
git push
```

### 7️⃣ Criar Worker Celery (Railway)

No Railway Dashboard:
1. New → Empty Service
2. Connect to GitHub repo
3. Settings → Start Command:
   ```
   celery -A app.celery_app worker --loglevel=info
   ```
4. Variables → Copy all from backend service
5. Deploy

## ✅ VERIFICAR

### Backend funcionando:
```
https://sua-url.railway.app/docs
```

### Frontend funcionando:
```
https://seu-site.netlify.app
```

### Testar cadastro:
1. Abra o frontend
2. Clique em "Registrar"
3. Cadastre um email
4. Deve funcionar!

## 🆘 Problemas Comuns

**Backend não sobe:**
- Verificar logs: `railway logs`
- Verificar variáveis de ambiente

**Frontend não conecta:**
- Verificar VITE_API_BASE_URL no Netlify
- Verificar CORS no backend

**Email não envia:**
- Usar senha de app do Gmail (não a senha normal)
- Ativar "Acesso a apps menos seguros"

## 📞 Comandos Úteis

```bash
# Ver logs do backend
railway logs

# Ver variáveis
railway variables

# Abrir dashboard
railway open

# Executar comando no servidor
railway run <comando>
```

## 🎉 Pronto!

Seu app estará 100% funcional:
- Frontend: Netlify
- Backend: Railway
- Database: PostgreSQL (Railway)
- Cache: Redis (Railway)
- Worker: Celery (Railway)
