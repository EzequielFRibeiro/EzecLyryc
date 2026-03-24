@echo off
echo 🚀 Deploy CifraPartit Backend no Railway
echo.

echo 📦 Instalando Railway CLI...
call npm install -g @railway/cli

echo 🔐 Fazendo login no Railway...
call railway login

echo 📁 Entrando na pasta backend...
cd backend

echo 🆕 Criando projeto no Railway...
call railway init

echo 🗄️ Adicionando PostgreSQL...
call railway add --database postgresql

echo 🔴 Adicionando Redis...
call railway add --database redis

echo ⬆️ Fazendo deploy...
call railway up

echo.
echo ✅ Deploy concluído!
echo.
echo 📝 Próximos passos:
echo 1. Acesse: https://railway.app/dashboard
echo 2. Configure as variáveis de ambiente
echo 3. Execute migrations: railway run alembic upgrade head
echo 4. Copie a URL do backend
echo 5. Atualize VITE_API_BASE_URL no Netlify
echo.
echo 🎉 Pronto!
pause
