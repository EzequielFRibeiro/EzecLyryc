#!/bin/bash

echo "🚀 Deploy CifraPartit Backend no Railway"
echo ""

# Verificar se Railway CLI está instalado
if ! command -v railway &> /dev/null
then
    echo "📦 Instalando Railway CLI..."
    npm install -g @railway/cli
fi

echo "🔐 Fazendo login no Railway..."
railway login

echo "📁 Entrando na pasta backend..."
cd backend

echo "🆕 Criando projeto no Railway..."
railway init

echo "🗄️ Adicionando PostgreSQL..."
railway add --database postgresql

echo "🔴 Adicionando Redis..."
railway add --database redis

echo "⬆️ Fazendo deploy..."
railway up

echo ""
echo "✅ Deploy concluído!"
echo ""
echo "📝 Próximos passos:"
echo "1. Acesse: https://railway.app/dashboard"
echo "2. Configure as variáveis de ambiente:"
echo "   - SECRET_KEY (gere com: python -c 'import secrets; print(secrets.token_urlsafe(32))')"
echo "   - S3_BUCKET, S3_ACCESS_KEY, S3_SECRET_KEY"
echo "   - SMTP_HOST, SMTP_USER, SMTP_PASSWORD"
echo "3. Execute migrations: railway run alembic upgrade head"
echo "4. Copie a URL do backend"
echo "5. Atualize VITE_API_BASE_URL no Netlify"
echo ""
echo "🎉 Pronto!"
