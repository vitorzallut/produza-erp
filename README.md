# Produza ERP - Backend FastAPI

API Backend para o sistema ERP da Produza Soluções.

## Tecnologias
- FastAPI
- SQLAlchemy (async)
- PostgreSQL (Supabase)
- JWT Authentication
- Alembic (migrations)

## Deploy no Railway

### Passo 1: Criar projeto no Railway
1. Acesse [railway.app](https://railway.app)
2. Clique em "New Project"
3. Selecione "Deploy from GitHub repo"
4. Conecte e selecione o repositório

### Passo 2: Configurar variáveis de ambiente
No Railway, vá em **Variables** e adicione:

```
DATABASE_URL=postgresql://user:password@host:5432/database
JWT_SECRET=sua-chave-secreta-muito-segura-aqui
```

### Passo 3: Deploy automático
O Railway detectará o `Procfile` e fará o deploy automaticamente.

## Executar localmente

```bash
# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis
export DATABASE_URL="postgresql://..."
export JWT_SECRET="secret"

# Executar
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

## Endpoints principais

| Método | Rota | Descrição |
|--------|------|-----------|
| POST | /api/auth/login | Login |
| GET | /api/auth/me | Usuário atual |
| GET | /api/projetos | Listar projetos |
| GET | /api/orcamentos | Listar orçamentos |
| POST | /api/orcamentos/{id}/aprovar | Aprovar e criar projeto |
| GET | /api/clientes | Listar clientes |
| GET | /api/contas | Listar contas |
