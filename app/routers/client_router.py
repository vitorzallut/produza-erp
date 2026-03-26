
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

@router.post("/", response_model=schemas.Client)
async def create_client(client: schemas.ClientCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_active_user)):
    check_user_company_access(current_user, client.company_id)

    db_client = models.Client(**client.dict())
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client

@router.get("/", response_model=List[schemas.Client])
async def read_clients(company_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_active_user)):
    check_user_company_access(current_user, company_id)

    clients = db.query(models.Client).filter(models.Client.company_id == company_id).offset(skip).limit(limit).all()
    return clients

@router.get("/{client_id}", response_model=schemas.Client)
async def read_client(client_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_active_user)):
    client = db.query(models.Client).filter(models.Client.id == client_id).first()
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    
    check_user_company_access(current_user, client.company_id)
    return client
