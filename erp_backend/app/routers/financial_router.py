
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.models import models
from app.schemas import schemas
from app.auth import auth

router = APIRouter()

def check_user_company_access(user: models.User, company_id: int):
    user_companies_ids = [uc.company_id for uc in user.user_companies]
    if company_id not in user_companies_ids:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions to access this company")

@router.post("/", response_model=schemas.Financial)
async def create_financial_entry(financial_entry: schemas.FinancialCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_active_user)):
    check_user_company_access(current_user, financial_entry.company_id)

    if financial_entry.project_id:
        project = db.query(models.Project).filter(models.Project.id == financial_entry.project_id, models.Project.company_id == financial_entry.company_id).first()
        if not project:
            raise HTTPException(status_code=400, detail="Project not found or does not belong to this company.")

    db_financial_entry = models.Financial(**financial_entry.dict())
    db.add(db_financial_entry)
    db.commit()
    db.refresh(db_financial_entry)
    return db_financial_entry

@router.get("/", response_model=List[schemas.Financial])
async def read_financial_entries(company_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_active_user)):
    check_user_company_access(current_user, company_id)

    financial_entries = db.query(models.Financial).filter(models.Financial.company_id == company_id).offset(skip).limit(limit).all()
    return financial_entries

@router.get("/{financial_id}", response_model=schemas.Financial)
async def read_financial_entry(financial_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_active_user)):
    financial_entry = db.query(models.Financial).filter(models.Financial.id == financial_id).first()
    if financial_entry is None:
        raise HTTPException(status_code=404, detail="Financial entry not found")
    
    check_user_company_access(current_user, financial_entry.company_id)
    return financial_entry
