# Deploy Backend no Railway

## Passo a Passo

### 1. Instalar Railway CLI
```bash
npm install -g @railway/cli
```

### 2. Login
```bash
railway login
```

### 3. Criar Projeto
```bash
railway init
```
- Nome: `cifrapartit-backend`

### 4. Adicionar PostgreSQL
```bash
railway add --database postgresql
```

### 5. Adicionar Redis
```bash
railway add --database redis
```

### 6. Deploy
```bash
railway up
```

### 7. Configurar Variáveis de Ambiente

No Railway Dashboard (https://railway.app/dashboard):

```
DATABASE_URL=(auto-gerado)
REDIS_URL=(auto-gerado)
SECRET_KEY=gere-com-comando-abaixo
S3_BUCKET=seu-bucket
S3_ACCESS_KEY=sua-key
S3_SECRET_KEY=sua-secret
S3_ENDPOINT=https://s3.amazonaws.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seu-email@gmail.com
SMTP_PASSWORD=sua-senha-app
```

### 8. Gerar SECRET_KEY
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 9. Executar Migrations
```bash
railway run alembic upgrade head
```

### 10. Criar Worker (Celery)

No Railway Dashboard:
1. Criar novo serviço do mesmo repo
2. Configurar Start Command: `celery -A app.celery_app worker --loglevel=info`
3. Adicionar mesmas variáveis de ambiente

### 11. Obter URL do Backend
```bash
railway domain
```

### 12. Atualizar Frontend (Netlify)

No Netlify Dashboard:
1. Site settings → Environment variables
2. Adicionar/Editar: `VITE_API_BASE_URL=https://sua-url.railway.app`
3. Trigger redeploy

## Pronto! 🚀

Backend: https://sua-url.railway.app
Frontend: https://seu-site.netlify.app
