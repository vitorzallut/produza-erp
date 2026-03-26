# ERP Backend - FastAPI

Este é o backend do sistema ERP, desenvolvido com FastAPI e configurado para utilizar o Supabase (PostgreSQL) como banco de dados.

## Estrutura do Projeto

O projeto está organizado da seguinte forma:

*   `app/`: Contém o código-fonte da aplicação.
    *   `main.py`: Ponto de entrada da aplicação, configuração do CORS e inicialização do banco de dados (seed).
    *   `db/database.py`: Configuração da conexão com o banco de dados via SQLAlchemy.
    *   `models/models.py`: Definição dos modelos de dados (tabelas do banco).
    *   `schemas/schemas.py`: Definição dos schemas Pydantic para validação de dados de entrada e saída.
    *   `auth/auth.py`: Lógica de autenticação JWT e hash de senhas.
    *   `routers/`: Contém as rotas da API separadas por módulo (auth, companies, clients, budgets, projects, financial).
*   `requirements.txt`: Lista de dependências do projeto.
*   `Procfile`: Arquivo de configuração para o deploy no Railway.
*   `.env.example`: Exemplo das variáveis de ambiente necessárias.

## Como Rodar Localmente

1.  **Crie um ambiente virtual (opcional, mas recomendado):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # No Windows: venv\Scripts\activate
    ```

2.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure as variáveis de ambiente:**
    *   Copie o arquivo `.env.example` para `.env`.
    *   Preencha as variáveis com os seus dados (URL do Supabase, chave secreta, etc.).

4.  **Execute a aplicação:**
    ```bash
    uvicorn app.main:app --reload
    ```

A API estará disponível em `http://localhost:8000`. Você pode acessar a documentação interativa (Swagger UI) em `http://localhost:8000/docs`.

## Como Fazer o Deploy no Railway

Siga estes passos para publicar o backend no Railway:

1.  **Prepare o Repositório:**
    *   Inicialize um repositório Git na pasta do projeto e faça o commit de todos os arquivos.
    *   Faça o push do código para o GitHub, GitLab ou Bitbucket.

2.  **Crie um Novo Projeto no Railway:**
    *   Acesse [Railway.app](https://railway.app/) e faça login.
    *   Clique em **"New Project"** e selecione **"Deploy from GitHub repo"** (ou a plataforma que você usou).
    *   Selecione o repositório do seu backend.

3.  **Configure as Variáveis de Ambiente no Railway:**
    *   No painel do seu projeto no Railway, vá até a aba **"Variables"**.
    *   Adicione as seguintes variáveis (conforme o seu `.env.example`):
        *   `DATABASE_URL`: A string de conexão do seu banco de dados Supabase (PostgreSQL).
        *   `SECRET_KEY`: Uma string longa e aleatória para assinar os tokens JWT (você pode gerar uma usando `openssl rand -hex 32`).
        *   `ACCESS_TOKEN_EXPIRE_MINUTES`: O tempo de expiração do token (ex: `30`).
        *   `FRONTEND_URL`: A URL do seu frontend no Netlify (ex: `https://seu-app.netlify.app`). Isso é crucial para o CORS funcionar corretamente.
        *   `ADMIN_EMAIL`: O email do usuário administrador inicial (seed).
        *   `ADMIN_PASSWORD`: A senha do usuário administrador inicial (seed).

4.  **Configuração do Comando de Start (Opcional, mas recomendado):**
    *   O Railway geralmente detecta o `Procfile` automaticamente.
    *   Se precisar configurar manualmente, vá na aba **"Settings"** do seu serviço, encontre a seção **"Deploy"** e defina o **"Start Command"** como:
        ```bash
        uvicorn app.main:app --host 0.0.0.0 --port $PORT
        ```

5.  **Gere o Domínio Público:**
    *   Ainda na aba **"Settings"**, vá até a seção **"Networking"** ou **"Domains"**.
    *   Clique em **"Generate Domain"** para obter a URL pública da sua API (ex: `https://seu-backend-production.up.railway.app`).

6.  **Atualize o Frontend:**
    *   Copie a URL gerada no passo anterior.
    *   Vá até as configurações do seu projeto no Netlify.
    *   Atualize a variável de ambiente `REACT_APP_BACKEND_URL` com a nova URL do Railway.
    *   Faça um novo deploy do frontend no Netlify para aplicar a mudança.

## Seed Inicial

Ao iniciar a aplicação pela primeira vez (seja localmente ou no Railway), o código no `main.py` verificará se o usuário administrador (definido nas variáveis `ADMIN_EMAIL` e `ADMIN_PASSWORD`) existe. Se não existir, ele criará:

1.  O usuário administrador.
2.  Uma empresa de teste.
3.  O vínculo entre o administrador e a empresa de teste.

Isso garante que você possa fazer login imediatamente após o deploy.
