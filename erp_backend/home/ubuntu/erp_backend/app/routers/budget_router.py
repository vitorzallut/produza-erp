
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
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

@router.post("/", response_model=schemas.Budget)
async def create_budget(budget: schemas.BudgetCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_active_user)):
    check_user_company_access(current_user, budget.company_id)

    db_client = db.query(models.Client).filter(models.Client.id == budget.client_id, models.Client.company_id == budget.company_id).first()
    if not db_client:
        raise HTTPException(status_code=404, detail="Client not found in this company")

    db_budget = models.Budget(
        company_id=budget.company_id,
        client_id=budget.client_id,
        versao=budget.versao,
        markup_percentual=budget.markup_percentual,
        imposto_percentual=budget.imposto_percentual,
        status=budget.status
    )
    db.add(db_budget)
    db.commit()
    db.refresh(db_budget)

    total_budget_value = 0.0
    for item_data in budget.items:
        valor_unitario_venda = item_data.custo_unitario * (1 + db_budget.markup_percentual)
        valor_total_item = (valor_unitario_venda * item_data.quantidade) * (1 + db_budget.imposto_percentual)
        
        db_item = models.BudgetItem(
            orcamento_id=db_budget.id,
            descricao=item_data.descricao,
            quantidade=item_data.quantidade,
            custo_unitario=item_data.custo_unitario,
            valor_unitario_venda=valor_unitario_venda,
            valor_total=valor_total_item
        )
        db.add(db_item)
        total_budget_value += valor_total_item
    
    db_budget.valor_total = total_budget_value
    db.commit()
    db.refresh(db_budget)
    
    return db_budget

@router.get("/", response_model=List[schemas.Budget])
async def read_budgets(company_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_active_user)):
    check_user_company_access(current_user, company_id)

    budgets = db.query(models.Budget).options(joinedload(models.Budget.items)).filter(models.Budget.company_id == company_id).offset(skip).limit(limit).all()
    return budgets

@router.get("/{budget_id}", response_model=schemas.Budget)
async def read_budget(budget_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_active_user)):
    budget = db.query(models.Budget).options(joinedload(models.Budget.items)).filter(models.Budget.id == budget_id).first()
    if budget is None:
        raise HTTPException(status_code=404, detail="Budget not found")
    
    check_user_company_access(current_user, budget.company_id)
    return budget

@router.post("/{budget_id}/aprovar-e-gerar-projeto", response_model=schemas.Project)
async def approve_budget_and_generate_project(budget_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_active_user)):
    budget = db.query(models.Budget).filter(models.Budget.id == budget_id).first()
    if budget is None:
        raise HTTPException(status_code=404, detail="Budget not found")
    
    check_user_company_access(current_user, budget.company_id)

    if budget.status == "aprovado":
        raise HTTPException(status_code=400, detail="Budget already approved")

    # Verifica se já existe um projeto para este orçamento
    existing_project = db.query(models.Project).filter(models.Project.orcamento_id == budget_id).first()
    if existing_project:
        raise HTTPException(status_code=400, detail="A project already exists for this budget")

    budget.status = "aprovado"
    db.add(budget)
    db.commit()
    db.refresh(budget)

    project_name = f"Projeto do Orçamento {budget.id} - Cliente {budget.client_id}"
    db_project = models.Project(
        nome=project_name,
        company_id=budget.company_id,
        client_id=budget.client_id,
        orcamento_id=budget.id,
        status="pendente" # Status inicial do projeto
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)

    return db_project
