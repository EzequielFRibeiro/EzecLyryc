# Setup Git e GitHub

## 📝 Inicializar Git

```bash
# Inicializar repositório
git init

# Adicionar todos os arquivos
git add .

# Primeiro commit
git commit -m "Initial commit: CifraPartit Music Transcription Platform

- Backend completo (FastAPI + PostgreSQL + Redis + Celery)
- Frontend completo (React + TypeScript + Zustand)
- 300+ testes passando
- Sistema de transcrição musical com IA
- Suporte a 8 instrumentos
- Upload de arquivo, gravação e YouTube
- Export em múltiplos formatos
- Sistema de assinatura Pro"
```

## 🌐 Criar Repositório no GitHub

1. Acesse https://github.com/new
2. Nome: `cifrapartit-music-transcription`
3. Descrição: `Plataforma de transcrição musical com IA - Transforme áudio em partituras`
4. Público ou Privado (sua escolha)
5. NÃO inicialize com README (já temos)

## 🔗 Conectar ao GitHub

```bash
# Adicionar remote
git remote add origin https://github.com/SEU_USUARIO/cifrapartit-music-transcription.git

# Verificar remote
git remote -v

# Push inicial
git branch -M main
git push -u origin main
```

## 📦 Branches Recomendadas

```bash
# Criar branch de desenvolvimento
git checkout -b develop

# Criar branch de produção (já está na main)
# main = produção
# develop = desenvolvimento
# feature/* = novas funcionalidades
```

## 🏷️ Tags de Versão

```bash
# Criar tag da versão inicial
git tag -a v1.0.0 -m "Release v1.0.0 - MVP Completo"
git push origin v1.0.0
```

## 📋 Workflow Sugerido

```bash
# Para novas features
git checkout develop
git checkout -b feature/nome-da-feature
# ... fazer alterações ...
git add .
git commit -m "feat: descrição da feature"
git push origin feature/nome-da-feature
# Criar Pull Request no GitHub

# Para hotfixes
git checkout main
git checkout -b hotfix/nome-do-fix
# ... fazer correção ...
git add .
git commit -m "fix: descrição do fix"
git push origin hotfix/nome-do-fix
# Criar Pull Request no GitHub
```

## 🔐 Secrets do GitHub (para CI/CD)

Se configurar GitHub Actions:

1. Settings → Secrets and variables → Actions
2. Adicionar:
   - `DATABASE_URL`
   - `REDIS_URL`
   - `SECRET_KEY`
   - `S3_BUCKET`
   - etc.

## ✅ Checklist

- [ ] Git inicializado
- [ ] .gitignore configurado
- [ ] Primeiro commit feito
- [ ] Repositório criado no GitHub
- [ ] Remote adicionado
- [ ] Push para GitHub realizado
- [ ] README.md visível no GitHub
- [ ] Branches criadas (opcional)
- [ ] Tags criadas (opcional)

## 🚀 Próximos Passos

1. Conectar Vercel ao repositório GitHub
2. Configurar deploy automático
3. Configurar variáveis de ambiente no Vercel
4. Deploy!
