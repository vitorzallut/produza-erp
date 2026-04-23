from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware

from app.db.database import engine, Base, get_db
from app.models import models
from app.schemas import schemas
from app.auth import auth

from app.routers import auth_router, company_router, client_router, budget_router, project_router, financial_router

import os
from dotenv import load_dotenv

load_dotenv()

# Cria as tabelas no banco de dados
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ERP Backend",
    description="Backend para o sistema ERP com FastAPI e Supabase",
    version="0.1.0",
)

# Configuração do CORS
origins = [
    "https://produzafilmes.netlify.app",
    "https://produzafilmes.com",
    "https://www.produzafilmes.com",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusão dos routers
app.include_router(auth_router.router, prefix="/auth", tags=["Auth"])
app.include_router(company_router.router, prefix="/companies", tags=["Companies"])
app.include_router(client_router.router, prefix="/clients", tags=["Clients"])
app.include_router(budget_router.router, prefix="/budgets", tags=["Budgets"])
app.include_router(project_router.router, prefix="/projects", tags=["Projects"])
app.include_router(financial_router.router, prefix="/financial", tags=["Financial"])

@app.get("/")
async def root():
    return {"message": "ERP Backend is running!"}

# Seed inicial de dados
@app.on_event("startup")
def create_initial_data():
    db = next(get_db())
    admin_user = db.query(models.User).filter(models.User.email == os.getenv("ADMIN_EMAIL")).first()
    if not admin_user:
        print("Criando usuário admin inicial...")
        hashed_password = auth.get_password_hash(os.getenv("ADMIN_PASSWORD"))
        admin_user = models.User(
            nome="Admin User",
            email=os.getenv("ADMIN_EMAIL"),
            senha_hash=hashed_password,
            role="admin"
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        print(f"Usuário admin {admin_user.email} criado.")

        test_company = db.query(models.Company).filter(models.Company.cnpj == "00.000.000/0001-00").first()
        if not test_company:
            print("Criando empresa de teste inicial...")
            test_company = models.Company(
                nome="Empresa de Teste",
                cnpj="00.000.000/0001-00",
                logo_url="https://example.com/logo.png",
                cor_primaria="#000000",
                cor_secundaria="#FFFFFF",
                dados_fiscais="Dados Fiscais de Teste"
            )
            db.add(test_company)
            db.commit()
            db.refresh(test_company)
            print(f"Empresa de teste {test_company.nome} criada.")

            user_company = models.UserCompany(
                user_id=admin_user.id,
                company_id=test_company.id
            )
            db.add(user_company)
            db.commit()
            print(f"Usuário admin vinculado à empresa {test_company.nome}.")
    else:
        print("Usuário admin já existe.")

    db.close()
