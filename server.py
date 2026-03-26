"""
Produza ERP - Backend API
"""
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import bcrypt
from jose import jwt, JWTError
import os
import uuid
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent / '.env')

from database import get_db
from models import (
    Usuario, Empresa, UsuarioEmpresa, Cliente, Projeto, ColunaKanban, 
    Tarefa, Comentario, Orcamento, ItemOrcamento, Conta, HistoricoCliente,
    UserRole, ProjectStatus, OrcamentoStatus, ContaStatus, ContaTipo, NegociacaoStatus
)

app = FastAPI(title="Produza ERP API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

JWT_SECRET = os.environ.get('JWT_SECRET', 'secret-key')
security = HTTPBearer()

# Pydantic Models
class LoginRequest(BaseModel):
    email: EmailStr
    senha: str

class TokenResponse(BaseModel):
    token: str
    usuario: dict

class UsuarioCreate(BaseModel):
    email: EmailStr
    senha: str
    nome: str
    telefone: Optional[str] = None
    role: Optional[str] = "visualizacao"

class EmpresaCreate(BaseModel):
    cnpj: str
    razao_social: str
    nome_fantasia: Optional[str] = None
    endereco: Optional[str] = None
    telefone: Optional[str] = None
    email: Optional[str] = None

class ClienteCreate(BaseModel):
    empresa_id: str
    tipo: Optional[str] = "PJ"
    cpf_cnpj: Optional[str] = None
    nome: str
    email: Optional[str] = None
    telefone: Optional[str] = None
    endereco: Optional[str] = None
    observacoes: Optional[str] = None

class ProjetoCreate(BaseModel):
    empresa_id: str
    orcamento_id: str  # Obrigatório - projeto sempre vem de orçamento
    cliente_id: Optional[str] = None
    titulo: str
    descricao: Optional[str] = None
    data_inicio: Optional[datetime] = None
    data_fim_prevista: Optional[datetime] = None

class TarefaCreate(BaseModel):
    coluna_id: str
    titulo: str
    descricao: Optional[str] = None
    responsavel_id: Optional[str] = None
    prazo: Optional[datetime] = None

class OrcamentoCreate(BaseModel):
    empresa_id: str
    cliente_id: Optional[str] = None
    titulo: str
    descricao: Optional[str] = None
    validade: Optional[datetime] = None
    condicoes_pagamento: Optional[str] = None

class ItemOrcamentoCreate(BaseModel):
    categoria: Optional[str] = None
    descricao: str
    quantidade: float = 1
    unidade: str = "un"
    custo_unitario: float = 0
    venda_unitario: float = 0

class ContaCreate(BaseModel):
    empresa_id: str
    projeto_id: Optional[str] = None
    tipo: str
    categoria: Optional[str] = None
    descricao: str
    valor: float
    data_vencimento: datetime
    forma_pagamento: Optional[str] = None
    observacoes: Optional[str] = None

# Helper functions
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_token(user_id: str, email: str, role: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(days=7)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Usuario:
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=["HS256"])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Token inválido")
        
        result = await db.execute(
            select(Usuario)
            .options(selectinload(Usuario.empresas).selectinload(UsuarioEmpresa.empresa))
            .where(Usuario.id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user or not user.ativo:
            raise HTTPException(status_code=401, detail="Usuário não encontrado")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")

def check_admin(user: Usuario):
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Acesso negado. Apenas administradores.")

def check_empresa_access(user: Usuario, empresa_id: str):
    """Verifica se o usuário tem acesso à empresa especificada"""
    if user.role == UserRole.ADMIN:
        return True  # Admin tem acesso a todas
    
    empresa_ids = [ue.empresa_id for ue in user.empresas]
    if empresa_id not in empresa_ids:
        raise HTTPException(status_code=403, detail="Acesso negado a esta empresa")
    return True

# Routes

@app.get("/api/")
async def root():
    return {"message": "Produza ERP API", "status": "online"}

@app.get("/api/health")
async def health():
    return {"status": "healthy"}

# Auth
@app.post("/api/auth/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Usuario)
        .options(selectinload(Usuario.empresas).selectinload(UsuarioEmpresa.empresa))
        .where(Usuario.email == data.email)
    )
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(data.senha, user.senha_hash):
        raise HTTPException(status_code=401, detail="Email ou senha inválidos")
    
    if not user.ativo:
        raise HTTPException(status_code=401, detail="Usuário desativado")
    
    token = create_token(user.id, user.email, user.role.value)
    
    empresas = [{"id": ue.empresa.id, "nome": ue.empresa.nome_fantasia or ue.empresa.razao_social, "cnpj": ue.empresa.cnpj} for ue in user.empresas]
    
    return {
        "token": token,
        "usuario": {
            "id": user.id,
            "email": user.email,
            "nome": user.nome,
            "role": user.role.value,
            "empresas": empresas
        }
    }

@app.get("/api/auth/me")
async def me(user: Usuario = Depends(get_current_user)):
    empresas = [{"id": ue.empresa.id, "nome": ue.empresa.nome_fantasia or ue.empresa.razao_social, "cnpj": ue.empresa.cnpj} for ue in user.empresas]
    return {
        "id": user.id,
        "email": user.email,
        "nome": user.nome,
        "role": user.role.value,
        "telefone": user.telefone,
        "empresas": empresas
    }

# Usuários
@app.get("/api/usuarios")
async def list_usuarios(user: Usuario = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    check_admin(user)
    result = await db.execute(
        select(Usuario)
        .options(selectinload(Usuario.empresas).selectinload(UsuarioEmpresa.empresa))
        .order_by(Usuario.nome)
    )
    usuarios = result.scalars().all()
    return [
        {
            "id": u.id,
            "email": u.email,
            "nome": u.nome,
            "role": u.role.value,
            "ativo": u.ativo,
            "empresas": [{"id": ue.empresa.id, "nome": ue.empresa.nome_fantasia or ue.empresa.razao_social} for ue in u.empresas]
        }
        for u in usuarios
    ]

@app.post("/api/usuarios")
async def create_usuario(data: UsuarioCreate, user: Usuario = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    check_admin(user)
    
    # Check if email exists
    result = await db.execute(select(Usuario).where(Usuario.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email já cadastrado")
    
    novo_usuario = Usuario(
        email=data.email,
        senha_hash=hash_password(data.senha),
        nome=data.nome,
        telefone=data.telefone,
        role=UserRole(data.role)
    )
    db.add(novo_usuario)
    await db.commit()
    await db.refresh(novo_usuario)
    
    return {"id": novo_usuario.id, "email": novo_usuario.email, "nome": novo_usuario.nome}

@app.post("/api/usuarios/{usuario_id}/empresas/{empresa_id}")
async def vincular_usuario_empresa(usuario_id: str, empresa_id: str, user: Usuario = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    check_admin(user)
    
    vinculo = UsuarioEmpresa(usuario_id=usuario_id, empresa_id=empresa_id)
    db.add(vinculo)
    await db.commit()
    return {"message": "Usuário vinculado à empresa"}

# Empresas
@app.get("/api/empresas")
async def list_empresas(user: Usuario = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if user.role == UserRole.ADMIN:
        result = await db.execute(select(Empresa).where(Empresa.ativa == True).order_by(Empresa.razao_social))
        empresas = result.scalars().all()
    else:
        empresa_ids = [ue.empresa_id for ue in user.empresas]
        result = await db.execute(select(Empresa).where(Empresa.id.in_(empresa_ids), Empresa.ativa == True))
        empresas = result.scalars().all()
    
    return [
        {
            "id": e.id,
            "cnpj": e.cnpj,
            "razao_social": e.razao_social,
            "nome_fantasia": e.nome_fantasia,
            "telefone": e.telefone,
            "email": e.email
        }
        for e in empresas
    ]

@app.post("/api/empresas")
async def create_empresa(data: EmpresaCreate, user: Usuario = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    check_admin(user)
    
    empresa = Empresa(**data.model_dump())
    db.add(empresa)
    await db.commit()
    await db.refresh(empresa)
    
    # Vincular admin à empresa
    vinculo = UsuarioEmpresa(usuario_id=user.id, empresa_id=empresa.id)
    db.add(vinculo)
    await db.commit()
    
    return {"id": empresa.id, "cnpj": empresa.cnpj, "razao_social": empresa.razao_social}

@app.get("/api/empresas/{empresa_id}")
async def get_empresa(empresa_id: str, user: Usuario = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Empresa).where(Empresa.id == empresa_id))
    empresa = result.scalar_one_or_none()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    return empresa

# Clientes
@app.get("/api/clientes")
async def list_clientes(empresa_id: str, user: Usuario = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    check_empresa_access(user, empresa_id)
    result = await db.execute(
        select(Cliente)
        .where(Cliente.empresa_id == empresa_id)
        .order_by(Cliente.nome)
    )
    clientes = result.scalars().all()
    return [
        {
            "id": c.id,
            "nome": c.nome,
            "tipo": c.tipo,
            "cpf_cnpj": c.cpf_cnpj,
            "email": c.email,
            "telefone": c.telefone,
            "status_negociacao": c.status_negociacao.value
        }
        for c in clientes
    ]

@app.post("/api/clientes")
async def create_cliente(data: ClienteCreate, user: Usuario = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    check_empresa_access(user, data.empresa_id)
    cliente = Cliente(**data.model_dump())
    db.add(cliente)
    await db.commit()
    await db.refresh(cliente)
    return {"id": cliente.id, "nome": cliente.nome}

@app.get("/api/clientes/{cliente_id}")
async def get_cliente(cliente_id: str, user: Usuario = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Cliente)
        .options(selectinload(Cliente.projetos), selectinload(Cliente.historico), selectinload(Cliente.orcamentos))
        .where(Cliente.id == cliente_id)
    )
    cliente = result.scalar_one_or_none()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    check_empresa_access(user, cliente.empresa_id)
    
    return {
        "id": cliente.id,
        "nome": cliente.nome,
        "tipo": cliente.tipo,
        "cpf_cnpj": cliente.cpf_cnpj,
        "email": cliente.email,
        "telefone": cliente.telefone,
        "endereco": cliente.endereco,
        "observacoes": cliente.observacoes,
        "status_negociacao": cliente.status_negociacao.value,
        "projetos": [{"id": p.id, "titulo": p.titulo, "status": p.status.value} for p in cliente.projetos],
        "orcamentos": [{"id": o.id, "numero": o.numero, "titulo": o.titulo, "status": o.status.value, "total_venda": float(o.total_venda)} for o in cliente.orcamentos],
        "historico": [{"id": h.id, "tipo": h.tipo, "descricao": h.descricao, "data": h.data.isoformat()} for h in cliente.historico]
    }

@app.patch("/api/clientes/{cliente_id}/status")
async def update_cliente_status(cliente_id: str, status: str, user: Usuario = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Cliente).where(Cliente.id == cliente_id))
    cliente = result.scalar_one_or_none()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    cliente.status_negociacao = NegociacaoStatus(status)
    await db.commit()
    return {"message": "Status atualizado"}

# Projetos (Kanban)
@app.get("/api/projetos")
async def list_projetos(empresa_id: str, user: Usuario = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    check_empresa_access(user, empresa_id)
    result = await db.execute(
        select(Projeto)
        .options(selectinload(Projeto.cliente), selectinload(Projeto.orcamento))
        .where(Projeto.empresa_id == empresa_id)
        .order_by(Projeto.created_at.desc())
    )
    projetos = result.scalars().all()
    return [
        {
            "id": p.id,
            "titulo": p.titulo,
            "descricao": p.descricao,
            "status": p.status.value,
            "cliente": {"id": p.cliente.id, "nome": p.cliente.nome} if p.cliente else None,
            "orcamento": {"id": p.orcamento.id, "numero": p.orcamento.numero, "total_venda": float(p.orcamento.total_venda)} if p.orcamento else None,
            "valor_total": float(p.valor_total) if p.valor_total else 0,
            "data_inicio": p.data_inicio.isoformat() if p.data_inicio else None,
            "data_fim_prevista": p.data_fim_prevista.isoformat() if p.data_fim_prevista else None
        }
        for p in projetos
    ]

# Criação de projeto desabilitada diretamente - projetos são criados via aprovação de orçamento
# @app.post("/api/projetos") - REMOVIDO - Use POST /api/orcamentos/{id}/aprovar

@app.get("/api/projetos/{projeto_id}")
async def get_projeto(projeto_id: str, user: Usuario = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Projeto)
        .options(
            selectinload(Projeto.cliente),
            selectinload(Projeto.orcamento),
            selectinload(Projeto.colunas).selectinload(ColunaKanban.tarefas).selectinload(Tarefa.responsavel),
            selectinload(Projeto.colunas).selectinload(ColunaKanban.tarefas).selectinload(Tarefa.comentarios)
        )
        .where(Projeto.id == projeto_id)
    )
    projeto = result.scalar_one_or_none()
    if not projeto:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    
    # Validar acesso à empresa
    check_empresa_access(user, projeto.empresa_id)
    
    return {
        "id": projeto.id,
        "titulo": projeto.titulo,
        "descricao": projeto.descricao,
        "status": projeto.status.value,
        "cliente": {"id": projeto.cliente.id, "nome": projeto.cliente.nome} if projeto.cliente else None,
        "orcamento": {"id": projeto.orcamento.id, "numero": projeto.orcamento.numero, "total_venda": float(projeto.orcamento.total_venda)} if projeto.orcamento else None,
        "valor_total": float(projeto.valor_total) if projeto.valor_total else 0,
        "data_inicio": projeto.data_inicio.isoformat() if projeto.data_inicio else None,
        "data_fim_prevista": projeto.data_fim_prevista.isoformat() if projeto.data_fim_prevista else None,
        "colunas": [
            {
                "id": c.id,
                "titulo": c.titulo,
                "ordem": c.ordem,
                "cor": c.cor,
                "tarefas": [
                    {
                        "id": t.id,
                        "titulo": t.titulo,
                        "descricao": t.descricao,
                        "ordem": t.ordem,
                        "prazo": t.prazo.isoformat() if t.prazo else None,
                        "responsavel": {"id": t.responsavel.id, "nome": t.responsavel.nome} if t.responsavel else None,
                        "checklist": t.checklist,
                        "anexos": t.anexos,
                        "comentarios_count": len(t.comentarios)
                    }
                    for t in sorted(c.tarefas, key=lambda x: x.ordem)
                ]
            }
            for c in sorted(projeto.colunas, key=lambda x: x.ordem)
        ]
    }

# Tarefas
@app.post("/api/tarefas")
async def create_tarefa(data: TarefaCreate, user: Usuario = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Get max ordem
    result = await db.execute(
        select(func.max(Tarefa.ordem)).where(Tarefa.coluna_id == data.coluna_id)
    )
    max_ordem = result.scalar() or 0
    
    tarefa = Tarefa(**data.model_dump(), ordem=max_ordem + 1)
    db.add(tarefa)
    await db.commit()
    await db.refresh(tarefa)
    return {"id": tarefa.id, "titulo": tarefa.titulo}

@app.patch("/api/tarefas/{tarefa_id}")
async def update_tarefa(tarefa_id: str, data: dict, user: Usuario = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Tarefa).where(Tarefa.id == tarefa_id))
    tarefa = result.scalar_one_or_none()
    if not tarefa:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    
    for key, value in data.items():
        if hasattr(tarefa, key):
            setattr(tarefa, key, value)
    await db.commit()
    return {"message": "Tarefa atualizada"}

@app.patch("/api/tarefas/{tarefa_id}/mover")
async def mover_tarefa(tarefa_id: str, coluna_id: str, ordem: int, user: Usuario = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Tarefa).where(Tarefa.id == tarefa_id))
    tarefa = result.scalar_one_or_none()
    if not tarefa:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    
    tarefa.coluna_id = coluna_id
    tarefa.ordem = ordem
    await db.commit()
    return {"message": "Tarefa movida"}

@app.delete("/api/tarefas/{tarefa_id}")
async def delete_tarefa(tarefa_id: str, user: Usuario = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Tarefa).where(Tarefa.id == tarefa_id))
    tarefa = result.scalar_one_or_none()
    if not tarefa:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    await db.delete(tarefa)
    await db.commit()
    return {"message": "Tarefa excluída"}

# Orçamentos
@app.get("/api/orcamentos")
async def list_orcamentos(empresa_id: str, user: Usuario = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    check_empresa_access(user, empresa_id)
    result = await db.execute(
        select(Orcamento)
        .options(selectinload(Orcamento.cliente), selectinload(Orcamento.projeto))
        .where(Orcamento.empresa_id == empresa_id)
        .order_by(Orcamento.created_at.desc())
    )
    orcamentos = result.scalars().all()
    return [
        {
            "id": o.id,
            "numero": o.numero,
            "versao": o.versao,
            "titulo": o.titulo,
            "status": o.status.value,
            "cliente": {"id": o.cliente.id, "nome": o.cliente.nome} if o.cliente else None,
            "projeto": {"id": o.projeto.id, "titulo": o.projeto.titulo} if o.projeto else None,
            "total_custo": float(o.total_custo),
            "total_venda": float(o.total_venda),
            "total_lucro": float(o.total_lucro),
            "created_at": o.created_at.isoformat()
        }
        for o in orcamentos
    ]

@app.post("/api/orcamentos")
async def create_orcamento(data: OrcamentoCreate, user: Usuario = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    check_empresa_access(user, data.empresa_id)
    # Gerar número
    result = await db.execute(
        select(func.count(Orcamento.id)).where(Orcamento.empresa_id == data.empresa_id)
    )
    count = result.scalar() or 0
    numero = f"ORC-{count + 1:04d}"
    
    # Gerar link de compartilhamento
    link = str(uuid.uuid4())[:8]
    
    orcamento = Orcamento(**data.model_dump(), numero=numero, link_compartilhamento=link)
    db.add(orcamento)
    await db.commit()
    await db.refresh(orcamento)
    return {"id": orcamento.id, "numero": orcamento.numero, "link": link}

@app.get("/api/orcamentos/{orcamento_id}")
async def get_orcamento(orcamento_id: str, user: Usuario = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Orcamento)
        .options(selectinload(Orcamento.cliente), selectinload(Orcamento.itens), selectinload(Orcamento.empresa), selectinload(Orcamento.projeto))
        .where(Orcamento.id == orcamento_id)
    )
    orcamento = result.scalar_one_or_none()
    if not orcamento:
        raise HTTPException(status_code=404, detail="Orçamento não encontrado")
    
    check_empresa_access(user, orcamento.empresa_id)
    
    return {
        "id": orcamento.id,
        "numero": orcamento.numero,
        "versao": orcamento.versao,
        "titulo": orcamento.titulo,
        "descricao": orcamento.descricao,
        "status": orcamento.status.value,
        "cliente": {"id": orcamento.cliente.id, "nome": orcamento.cliente.nome, "email": orcamento.cliente.email} if orcamento.cliente else None,
        "empresa": {"id": orcamento.empresa.id, "nome": orcamento.empresa.nome_fantasia or orcamento.empresa.razao_social, "logo": orcamento.empresa.logo_url, "cor": orcamento.empresa.cor_primaria},
        "projeto": {"id": orcamento.projeto.id, "titulo": orcamento.projeto.titulo, "status": orcamento.projeto.status.value} if orcamento.projeto else None,
        "validade": orcamento.validade.isoformat() if orcamento.validade else None,
        "condicoes_pagamento": orcamento.condicoes_pagamento,
        "observacoes": orcamento.observacoes,
        "total_custo": float(orcamento.total_custo),
        "total_venda": float(orcamento.total_venda),
        "total_lucro": float(orcamento.total_lucro),
        "link_compartilhamento": orcamento.link_compartilhamento,
        "itens": [
            {
                "id": i.id,
                "categoria": i.categoria,
                "descricao": i.descricao,
                "quantidade": float(i.quantidade),
                "unidade": i.unidade,
                "custo_unitario": float(i.custo_unitario),
                "venda_unitario": float(i.venda_unitario),
                "custo_total": float(i.custo_total),
                "venda_total": float(i.venda_total),
                "lucro": float(i.lucro),
                "ordem": i.ordem
            }
            for i in sorted(orcamento.itens, key=lambda x: x.ordem)
        ]
    }

@app.post("/api/orcamentos/{orcamento_id}/itens")
async def add_item_orcamento(orcamento_id: str, data: ItemOrcamentoCreate, user: Usuario = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Get max ordem
    result = await db.execute(
        select(func.max(ItemOrcamento.ordem)).where(ItemOrcamento.orcamento_id == orcamento_id)
    )
    max_ordem = result.scalar() or 0
    
    # Calcular totais
    custo_total = data.quantidade * data.custo_unitario
    venda_total = data.quantidade * data.venda_unitario
    lucro = venda_total - custo_total
    
    item = ItemOrcamento(
        orcamento_id=orcamento_id,
        **data.model_dump(),
        custo_total=custo_total,
        venda_total=venda_total,
        lucro=lucro,
        ordem=max_ordem + 1
    )
    db.add(item)
    
    # Atualizar totais do orçamento
    result = await db.execute(select(Orcamento).where(Orcamento.id == orcamento_id))
    orcamento = result.scalar_one()
    orcamento.total_custo = float(orcamento.total_custo) + custo_total
    orcamento.total_venda = float(orcamento.total_venda) + venda_total
    orcamento.total_lucro = float(orcamento.total_lucro) + lucro
    
    await db.commit()
    await db.refresh(item)
    return {"id": item.id}

@app.delete("/api/orcamentos/{orcamento_id}/itens/{item_id}")
async def delete_item_orcamento(orcamento_id: str, item_id: str, user: Usuario = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ItemOrcamento).where(ItemOrcamento.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    
    # Atualizar totais do orçamento
    result = await db.execute(select(Orcamento).where(Orcamento.id == orcamento_id))
    orcamento = result.scalar_one()
    orcamento.total_custo = float(orcamento.total_custo) - float(item.custo_total)
    orcamento.total_venda = float(orcamento.total_venda) - float(item.venda_total)
    orcamento.total_lucro = float(orcamento.total_lucro) - float(item.lucro)
    
    await db.delete(item)
    await db.commit()
    return {"message": "Item excluído"}

# Aprovar orçamento e criar projeto automaticamente
@app.post("/api/orcamentos/{orcamento_id}/aprovar")
async def aprovar_orcamento(orcamento_id: str, user: Usuario = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Aprova o orçamento e cria um projeto vinculado automaticamente"""
    result = await db.execute(
        select(Orcamento)
        .options(selectinload(Orcamento.cliente), selectinload(Orcamento.projeto))
        .where(Orcamento.id == orcamento_id)
    )
    orcamento = result.scalar_one_or_none()
    if not orcamento:
        raise HTTPException(status_code=404, detail="Orçamento não encontrado")
    
    # Validar acesso
    check_empresa_access(user, orcamento.empresa_id)
    
    # Verificar se já tem projeto vinculado
    if orcamento.projeto:
        raise HTTPException(status_code=400, detail="Este orçamento já possui um projeto vinculado")
    
    # Verificar se orçamento tem itens
    if float(orcamento.total_venda) == 0:
        raise HTTPException(status_code=400, detail="Não é possível aprovar orçamento sem itens")
    
    # Atualizar status do orçamento
    orcamento.status = OrcamentoStatus.APROVADO
    
    # Criar projeto vinculado
    projeto = Projeto(
        empresa_id=orcamento.empresa_id,
        cliente_id=orcamento.cliente_id,
        orcamento_id=orcamento.id,
        titulo=orcamento.titulo,
        descricao=orcamento.descricao,
        valor_total=orcamento.total_venda,
        status=ProjectStatus.BACKLOG
    )
    db.add(projeto)
    await db.commit()
    await db.refresh(projeto)
    
    # Criar colunas padrão do Kanban
    colunas_padrao = [
        ("A Fazer", 0, "#6b7280"),
        ("Em Andamento", 1, "#f59e0b"),
        ("Revisão", 2, "#8b5cf6"),
        ("Concluído", 3, "#22c55e")
    ]
    for titulo, ordem, cor in colunas_padrao:
        coluna = ColunaKanban(projeto_id=projeto.id, titulo=titulo, ordem=ordem, cor=cor)
        db.add(coluna)
    await db.commit()
    
    return {
        "message": "Orçamento aprovado e projeto criado com sucesso",
        "projeto_id": projeto.id,
        "projeto_titulo": projeto.titulo
    }

# Atualizar status do orçamento
@app.patch("/api/orcamentos/{orcamento_id}/status")
async def update_orcamento_status(orcamento_id: str, status: str, user: Usuario = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Orcamento).where(Orcamento.id == orcamento_id))
    orcamento = result.scalar_one_or_none()
    if not orcamento:
        raise HTTPException(status_code=404, detail="Orçamento não encontrado")
    
    check_empresa_access(user, orcamento.empresa_id)
    
    # Se já tem projeto e está tentando mudar de aprovado, não permite
    if orcamento.status == OrcamentoStatus.APROVADO and status != "aprovado":
        result = await db.execute(select(Projeto).where(Projeto.orcamento_id == orcamento_id))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Não é possível alterar status de orçamento com projeto vinculado")
    
    orcamento.status = OrcamentoStatus(status)
    await db.commit()
    return {"message": "Status atualizado"}

# Orçamento público (via link)
@app.get("/api/orcamento-publico/{link}")
async def get_orcamento_publico(link: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Orcamento)
        .options(selectinload(Orcamento.cliente), selectinload(Orcamento.itens), selectinload(Orcamento.empresa))
        .where(Orcamento.link_compartilhamento == link)
    )
    orcamento = result.scalar_one_or_none()
    if not orcamento:
        raise HTTPException(status_code=404, detail="Orçamento não encontrado")
    
    return {
        "numero": orcamento.numero,
        "titulo": orcamento.titulo,
        "descricao": orcamento.descricao,
        "cliente": {"nome": orcamento.cliente.nome} if orcamento.cliente else None,
        "empresa": {
            "nome": orcamento.empresa.nome_fantasia or orcamento.empresa.razao_social,
            "logo": orcamento.empresa.logo_url,
            "cor": orcamento.empresa.cor_primaria,
            "telefone": orcamento.empresa.telefone,
            "email": orcamento.empresa.email
        },
        "validade": orcamento.validade.isoformat() if orcamento.validade else None,
        "condicoes_pagamento": orcamento.condicoes_pagamento,
        "total_venda": float(orcamento.total_venda),
        "itens": [
            {
                "categoria": i.categoria,
                "descricao": i.descricao,
                "quantidade": float(i.quantidade),
                "unidade": i.unidade,
                "venda_unitario": float(i.venda_unitario),
                "venda_total": float(i.venda_total)
            }
            for i in sorted(orcamento.itens, key=lambda x: x.ordem)
        ]
    }

# Financeiro
@app.get("/api/contas")
async def list_contas(empresa_id: str, tipo: Optional[str] = None, user: Usuario = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    check_empresa_access(user, empresa_id)
    query = select(Conta).options(selectinload(Conta.projeto)).where(Conta.empresa_id == empresa_id)
    if tipo:
        query = query.where(Conta.tipo == ContaTipo(tipo))
    query = query.order_by(Conta.data_vencimento)
    
    result = await db.execute(query)
    contas = result.scalars().all()
    return [
        {
            "id": c.id,
            "tipo": c.tipo.value,
            "categoria": c.categoria,
            "descricao": c.descricao,
            "valor": float(c.valor),
            "data_vencimento": c.data_vencimento.isoformat(),
            "data_pagamento": c.data_pagamento.isoformat() if c.data_pagamento else None,
            "status": c.status.value,
            "projeto": {"id": c.projeto.id, "titulo": c.projeto.titulo} if c.projeto else None
        }
        for c in contas
    ]

@app.post("/api/contas")
async def create_conta(data: ContaCreate, user: Usuario = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    check_empresa_access(user, data.empresa_id)
    conta_data = data.model_dump()
    conta_data["tipo"] = ContaTipo(data.tipo)  # Convert string to enum
    conta = Conta(**conta_data)
    db.add(conta)
    await db.commit()
    await db.refresh(conta)
    return {"id": conta.id}

@app.patch("/api/contas/{conta_id}/pagar")
async def pagar_conta(conta_id: str, user: Usuario = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Conta).where(Conta.id == conta_id))
    conta = result.scalar_one_or_none()
    if not conta:
        raise HTTPException(status_code=404, detail="Conta não encontrada")
    
    check_empresa_access(user, conta.empresa_id)
    
    conta.status = ContaStatus.PAGO
    conta.data_pagamento = datetime.now(timezone.utc)
    await db.commit()
    return {"message": "Conta paga"}

@app.get("/api/financeiro/resumo")
async def resumo_financeiro(empresa_id: str, user: Usuario = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    check_empresa_access(user, empresa_id)
    # Total a receber
    result = await db.execute(
        select(func.sum(Conta.valor))
        .where(Conta.empresa_id == empresa_id, Conta.tipo == ContaTipo.RECEBER, Conta.status == ContaStatus.PENDENTE)
    )
    total_receber = result.scalar() or 0
    
    # Total a pagar
    result = await db.execute(
        select(func.sum(Conta.valor))
        .where(Conta.empresa_id == empresa_id, Conta.tipo == ContaTipo.PAGAR, Conta.status == ContaStatus.PENDENTE)
    )
    total_pagar = result.scalar() or 0
    
    # Recebido no mês
    inicio_mes = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    result = await db.execute(
        select(func.sum(Conta.valor))
        .where(
            Conta.empresa_id == empresa_id,
            Conta.tipo == ContaTipo.RECEBER,
            Conta.status == ContaStatus.PAGO,
            Conta.data_pagamento >= inicio_mes
        )
    )
    recebido_mes = result.scalar() or 0
    
    # Pago no mês
    result = await db.execute(
        select(func.sum(Conta.valor))
        .where(
            Conta.empresa_id == empresa_id,
            Conta.tipo == ContaTipo.PAGAR,
            Conta.status == ContaStatus.PAGO,
            Conta.data_pagamento >= inicio_mes
        )
    )
    pago_mes = result.scalar() or 0
    
    return {
        "total_receber": float(total_receber),
        "total_pagar": float(total_pagar),
        "recebido_mes": float(recebido_mes),
        "pago_mes": float(pago_mes),
        "saldo": float(recebido_mes) - float(pago_mes)
    }

# Dashboard
@app.get("/api/dashboard")
async def dashboard(empresa_id: str, user: Usuario = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Projetos por status
    result = await db.execute(
        select(Projeto.status, func.count(Projeto.id))
        .where(Projeto.empresa_id == empresa_id)
        .group_by(Projeto.status)
    )
    projetos_status = {row[0].value: row[1] for row in result.all()}
    
    # Orçamentos por status
    result = await db.execute(
        select(Orcamento.status, func.count(Orcamento.id))
        .where(Orcamento.empresa_id == empresa_id)
        .group_by(Orcamento.status)
    )
    orcamentos_status = {row[0].value: row[1] for row in result.all()}
    
    # Total clientes
    result = await db.execute(
        select(func.count(Cliente.id)).where(Cliente.empresa_id == empresa_id)
    )
    total_clientes = result.scalar() or 0
    
    # Contas vencendo em 7 dias
    proxima_semana = datetime.now(timezone.utc) + timedelta(days=7)
    result = await db.execute(
        select(func.count(Conta.id))
        .where(
            Conta.empresa_id == empresa_id,
            Conta.status == ContaStatus.PENDENTE,
            Conta.data_vencimento <= proxima_semana
        )
    )
    contas_vencendo = result.scalar() or 0
    
    return {
        "projetos": projetos_status,
        "orcamentos": orcamentos_status,
        "total_clientes": total_clientes,
        "contas_vencendo": contas_vencendo
    }

# Criar usuário admin inicial
@app.post("/api/setup")
async def setup(db: AsyncSession = Depends(get_db)):
    # Verificar se já existe admin
    result = await db.execute(select(Usuario).where(Usuario.role == UserRole.ADMIN))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Setup já realizado")
    
    # Criar admin
    admin = Usuario(
        email="contato@produzafilmes.com",
        senha_hash=hash_password("Vz14071614@"),
        nome="Administrador",
        role=UserRole.ADMIN
    )
    db.add(admin)
    await db.commit()
    await db.refresh(admin)
    
    return {"message": "Admin criado com sucesso", "email": admin.email}
