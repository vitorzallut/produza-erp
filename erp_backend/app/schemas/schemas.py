
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import List, Optional

class UserBase(BaseModel):
    nome: str
    email: EmailStr
    role: Optional[str] = "user"

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class CompanyBase(BaseModel):
    nome: str
    cnpj: str
    logo_url: Optional[str] = None
    cor_primaria: Optional[str] = None
    cor_secundaria: Optional[str] = None
    dados_fiscais: Optional[str] = None

class CompanyCreate(CompanyBase):
    pass

class Company(CompanyBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class UserCompanyBase(BaseModel):
    user_id: int
    company_id: int

class UserCompanyCreate(UserCompanyBase):
    pass

class UserCompany(UserCompanyBase):
    class Config:
        from_attributes = True

class ClientBase(BaseModel):
    nome: str
    email: Optional[EmailStr] = None
    telefone: Optional[str] = None
    company_id: int

class ClientCreate(ClientBase):
    pass

class Client(ClientBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class BudgetItemBase(BaseModel):
    descricao: str
    quantidade: int
    custo_unitario: float

class BudgetItemCreate(BudgetItemBase):
    pass

class BudgetItem(BudgetItemBase):
    id: int
    orcamento_id: int
    valor_unitario_venda: float
    valor_total: float

    class Config:
        from_attributes = True

class BudgetBase(BaseModel):
    company_id: int
    client_id: int
    versao: Optional[int] = 1
    markup_percentual: Optional[float] = 0.0
    imposto_percentual: Optional[float] = 0.0
    status: Optional[str] = "rascunho"
    items: List[BudgetItemCreate]

class BudgetCreate(BudgetBase):
    pass

class Budget(BudgetBase):
    id: int
    valor_total: float
    created_at: datetime
    items: List[BudgetItem]

    class Config:
        from_attributes = True

class ProjectBase(BaseModel):
    nome: str
    company_id: int
    client_id: int
    orcamento_id: int
    status: Optional[str] = "pendente"
    data_inicio: Optional[datetime] = None
    data_fim: Optional[datetime] = None

class ProjectCreate(ProjectBase):
    pass

class Project(ProjectBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class FinancialBase(BaseModel):
    company_id: int
    project_id: Optional[int] = None
    tipo: str # pagar ou receber
    descricao: str
    valor: float
    data_vencimento: datetime
    status: Optional[str] = "pendente"

class FinancialCreate(FinancialBase):
    pass

class Financial(FinancialBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str
