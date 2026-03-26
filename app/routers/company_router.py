
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.models import models
from app.schemas import schemas
from app.auth import auth

router = APIRouter()

@router.post("/", response_model=schemas.Company)
async def create_company(company: schemas.CompanyCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_active_user)):
    # Apenas administradores podem criar empresas diretamente, ou um fluxo de registro mais complexo seria necessário
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    db_company = db.query(models.Company).filter(models.Company.cnpj == company.cnpj).first()
    if db_company:
        raise HTTPException(status_code=400, detail="Company with this CNPJ already registered")
    
    db_company = models.Company(**company.dict())
    db.add(db_company)
    db.commit()
    db.refresh(db_company)

    # Vincula o usuário admin à nova empresa
    db_user_company = models.UserCompany(user_id=current_user.id, company_id=db_company.id)
    db.add(db_user_company)
    db.commit()

    return db_company

@router.get("/", response_model=List[schemas.Company])
async def read_companies(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_active_user)):
    # Usuário só pode acessar empresas às quais está vinculado
    user_companies_ids = [uc.company_id for uc in current_user.user_companies]
    companies = db.query(models.Company).filter(models.Company.id.in_(user_companies_ids)).offset(skip).limit(limit).all()
    return companies

@router.get("/{company_id}", response_model=schemas.Company)
async def read_company(company_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_active_user)):
    # Usuário só pode acessar empresas às quais está vinculado
    user_companies_ids = [uc.company_id for uc in current_user.user_companies]
    if company_id not in user_companies_ids:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions to access this company")

    company = db.query(models.Company).filter(models.Company.id == company_id).first()
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return company
