
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    senha_hash = Column(String)
    role = Column(String, default="user")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user_companies = relationship("UserCompany", back_populates="user")

class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True)
    cnpj = Column(String, unique=True, index=True)
    logo_url = Column(String, nullable=True)
    cor_primaria = Column(String, nullable=True)
    cor_secundaria = Column(String, nullable=True)
    dados_fiscais = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user_companies = relationship("UserCompany", back_populates="company")
    clients = relationship("Client", back_populates="company")
    budgets = relationship("Budget", back_populates="company")
    projects = relationship("Project", back_populates="company")
    financial_entries = relationship("Financial", back_populates="company")

class UserCompany(Base):
    __tablename__ = "user_companies"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id"), primary_key=True)

    user = relationship("User", back_populates="user_companies")
    company = relationship("Company", back_populates="user_companies")

class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True)
    email = Column(String, nullable=True)
    telefone = Column(String, nullable=True)
    company_id = Column(Integer, ForeignKey("companies.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    company = relationship("Company", back_populates="clients")
    budgets = relationship("Budget", back_populates="client")
    projects = relationship("Project", back_populates="client")

class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"))
    client_id = Column(Integer, ForeignKey("clients.id"))
    versao = Column(Integer, default=1)
    markup_percentual = Column(Float, default=0.0)
    imposto_percentual = Column(Float, default=0.0)
    valor_total = Column(Float, default=0.0)
    status = Column(String, default="rascunho") # rascunho, aprovado, rejeitado
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    company = relationship("Company", back_populates="budgets")
    client = relationship("Client", back_populates="budgets")
    items = relationship("BudgetItem", back_populates="budget")
    project = relationship("Project", back_populates="budget", uselist=False) # Um orçamento pode ter apenas um projeto

class BudgetItem(Base):
    __tablename__ = "budget_items"

    id = Column(Integer, primary_key=True, index=True)
    orcamento_id = Column(Integer, ForeignKey("budgets.id"))
    descricao = Column(String)
    quantidade = Column(Integer)
    custo_unitario = Column(Float)
    valor_unitario_venda = Column(Float)
    valor_total = Column(Float)

    budget = relationship("Budget", back_populates="items")

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String)
    company_id = Column(Integer, ForeignKey("companies.id"))
    client_id = Column(Integer, ForeignKey("clients.id"))
    orcamento_id = Column(Integer, ForeignKey("budgets.id"), unique=True) # Um projeto está vinculado a um único orçamento
    status = Column(String, default="pendente") # pendente, em_andamento, concluido, cancelado
    data_inicio = Column(DateTime(timezone=True), nullable=True)
    data_fim = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    company = relationship("Company", back_populates="projects")
    client = relationship("Client", back_populates="projects")
    budget = relationship("Budget", back_populates="project")
    financial_entries = relationship("Financial", back_populates="project")

class Financial(Base):
    __tablename__ = "financial"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"))
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    tipo = Column(String) # pagar ou receber
    descricao = Column(String)
    valor = Column(Float)
    data_vencimento = Column(DateTime(timezone=True))
    status = Column(String, default="pendente") # pendente, pago, recebido, atrasado
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    company = relationship("Company", back_populates="financial_entries")
    project = relationship("Project", back_populates="financial_entries")
