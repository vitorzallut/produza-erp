# Deploy Backend no Railway - Passo a Passo

## Arquivos Configurados

```
/backend/
├── server.py          # FastAPI app (objeto: app)
├── database.py        # Conexão PostgreSQL
├── models.py          # SQLAlchemy models
├── requirements.txt   # Dependências Python
├── runtime.txt        # Python 3.11.9
├── Procfile           # Comando de start
├── railway.json       # Config Railway
└── alembic/           # Migrations
```

---

## Passo a Passo Railway

### 1. Criar Projeto
1. Acesse [railway.app](https://railway.app)
2. Clique em **"New Project"**
3. Selecione **"Deploy from GitHub repo"**
4. Conecte sua conta GitHub
5. Selecione o repositório

### 2. Configurar Root Directory
⚠️ **IMPORTANTE**: Como o backend está em uma subpasta:
1. Vá em **Settings** do serviço
2. Em **Root Directory**, coloque: `backend`

### 3. Configurar Variáveis de Ambiente
Vá em **Variables** e adicione:

| Variável | Valor | Descrição |
|----------|-------|-----------|
| `DATABASE_URL` | `postgresql://user:pass@host:5432/db` | URL do Supabase |
| `JWT_SECRET` | `sua-chave-secreta-aqui` | Chave para tokens (mínimo 32 caracteres) |

**Sua DATABASE_URL do Supabase:**
```
postgresql://postgres.xxxx:SENHA@aws-0-sa-east-1.pooler.supabase.com:6543/postgres
```

### 4. Verificar Build Settings
O Railway deve detectar automaticamente:
- **Builder**: Nixpacks
- **Start Command**: `uvicorn server:app --host 0.0.0.0 --port $PORT`

Se não detectar, configure manualmente em **Settings > Deploy**.

### 5. Deploy
1. Clique em **"Deploy"** ou faça push no GitHub
2. Aguarde o build (2-3 minutos)
3. Quando aparecer ✅, clique em **"View Logs"** para verificar

### 6. Obter URL Pública
1. Vá em **Settings > Networking**
2. Clique em **"Generate Domain"**
3. Copie a URL gerada (ex: `https://produza-erp-production.up.railway.app`)

---

## Testar Deploy

```bash
# Health check
curl https://SEU-APP.up.railway.app/api/health

# Login
curl -X POST https://SEU-APP.up.railway.app/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"contato@produzafilmes.com","senha":"Vz14071614@"}'
```

---

## Configurar Netlify

Após obter a URL do Railway, configure no Netlify:

1. Vá em **Site settings > Environment variables**
2. Adicione:
   ```
   REACT_APP_BACKEND_URL = https://SEU-APP.up.railway.app
   ```
3. Faça um novo deploy (Deploys > Trigger deploy)

---

## Troubleshooting

### Erro de build
- Verifique se `Root Directory` está como `backend`
- Verifique logs de build

### Erro de conexão com banco
- Confirme que `DATABASE_URL` está correta
- Verifique se o IP do Railway está liberado no Supabase

### Erro 500 na API
- Verifique logs em **Deployments > View Logs**
- Confirme que `JWT_SECRET` está configurado

---

## Variáveis de Ambiente - Resumo

### Railway (Backend)
```env
DATABASE_URL=postgresql://postgres.xxxx:SENHA@aws-0-sa-east-1.pooler.supabase.com:6543/postgres
JWT_SECRET=produza-erp-jwt-secret-key-2024-muito-segura
```

### Netlify (Frontend)
```env
REACT_APP_BACKEND_URL=https://SEU-APP.up.railway.app
```

---

## Credenciais de Teste
- **Email**: contato@produzafilmes.com
- **Senha**: Vz14071614@
