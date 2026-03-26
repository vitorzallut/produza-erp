
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

@router.post("/", response_model=schemas.Project)
async def create_project(project: schemas.ProjectCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_active_user)):
    check_user_company_access(current_user, project.company_id)

    # Regra obrigatória: todo projeto deve estar vinculado a um orçamento
    budget = db.query(models.Budget).filter(models.Budget.id == project.orcamento_id, models.Budget.company_id == project.company_id).first()
    if not budget:
        raise HTTPException(status_code=400, detail="Budget not found or does not belong to this company. A project must be linked to an existing budget.")
    
    # Verifica se o orçamento já possui um projeto vinculado
    existing_project_for_budget = db.query(models.Project).filter(models.Project.orcamento_id == project.orcamento_id).first()
    if existing_project_for_budget:
        raise HTTPException(status_code=400, detail="A project already exists for this budget.")

    db_project = models.Project(**project.dict())
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

@router.get("/", response_model=List[schemas.Project])
async def read_projects(company_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_active_user)):
    check_user_company_access(current_user, company_id)

    projects = db.query(models.Project).filter(models.Project.company_id == company_id).offset(skip).limit(limit).all()
    return projects

@router.get("/{project_id}", response_model=schemas.Project)
async def read_project(project_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_active_user)):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    
    check_user_company_access(current_user, project.company_id)
    return project
