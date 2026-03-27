"""
Database Models for Produza ERP
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Numeric, Integer, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from database import Base
import enum

def generate_uuid():
    return str(uuid.uuid4())

def utc_now():
    return datetime.now(timezone.utc)

# Enums
class UserRole(str, enum.Enum):
    ADMIN = "admin"
    FINANCEIRO = "financeiro"
    PRODUCAO = "producao"
    VISUALIZACAO = "visualizacao"

class ProjectStatus(str, enum.Enum):
    BACKLOG = "backlog"
    EM_ANDAMENTO = "em_andamento"
    REVISAO = "revisao"
    CONCLUIDO = "concluido"
    CANCELADO = "cancelado"

class OrcamentoStatus(str, enum.Enum):
    RASCUNHO = "rascunho"
    ENVIADO = "enviado"
    APROVADO = "aprovado"
    REJEITADO = "rejeitado"

class ContaStatus(str, enum.Enum):
    PENDENTE = "pendente"
    PAGO = "pago"
    ATRASADO = "atrasado"
    CANCELADO = "cancelado"

class ContaTipo(str, enum.Enum):
    PAGAR = "pagar"
    RECEBER = "receber"

class NegociacaoStatus(str, enum.Enum):
    LEAD = "lead"
    CONTATO = "contato"
    PROPOSTA = "proposta"
    NEGOCIACAO = "negociacao"
    FECHADO = "fechado"
    PERDIDO = "perdido"

# Models

class Empresa(Base):
    __tablename__ = 'empresas'
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    cnpj = Column(String(18), unique=True, nullable=False, index=True)
    razao_social = Column(String(255), nullable=False)
    nome_fantasia = Column(String(255))
    endereco = Column(Text)
    telefone = Column(String(20))
    email = Column(String(255))
    logo_url = Column(Text)
    cor_primaria = Column(String(7), default="#f59e0b")
    cor_secundaria = Column(String(7), default="#000000")
    dados_bancarios = Column(JSON)
    ativa = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    
    usuarios = relationship("UsuarioEmpresa", back_populates="empresa")
    projetos = relationship("Projeto", back_populates="empresa")
    orcamentos = relationship("Orcamento", back_populates="empresa")
    contas = relationship("Conta", back_populates="empresa")
    clientes = relationship("Cliente", back_populates="empresa")
    fornecedores = relationship("Fornecedor", back_populates="empresa")

class Usuario(Base):
    __tablename__ = 'usuarios'
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    senha_hash = Column(String(255), nullable=False)
    nome = Column(String(255), nullable=False)
    telefone = Column(String(20))
    avatar_url = Column(Text)
    role = Column(SQLEnum(UserRole), default=UserRole.VISUALIZACAO)
    ativo = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    
    empresas = relationship("UsuarioEmpresa", back_populates="usuario")
    tarefas_responsavel = relationship("Tarefa", foreign_keys="Tarefa.responsavel_id", back_populates="responsavel")
    comentarios = relationship("Comentario", back_populates="autor")

class UsuarioEmpresa(Base):
    __tablename__ = 'usuario_empresa'
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    usuario_id = Column(String(36), ForeignKey('usuarios.id', ondelete='CASCADE'), index=True)
    empresa_id = Column(String(36), ForeignKey('empresas.id', ondelete='CASCADE'), index=True)
    permissoes = Column(JSON, default=dict)  # {"projetos": true, "financeiro": false, etc}
    created_at = Column(DateTime(timezone=True), default=utc_now)
    
    usuario = relationship("Usuario", back_populates="empresas")
    empresa = relationship("Empresa", back_populates="usuarios")

class Cliente(Base):
    __tablename__ = 'clientes'
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    empresa_id = Column(String(36), ForeignKey('empresas.id', ondelete='CASCADE'), index=True)
    tipo = Column(String(2), default="PJ")  # PF ou PJ
    cpf_cnpj = Column(String(18), index=True)
    nome = Column(String(255), nullable=False)
    email = Column(String(255))
    telefone = Column(String(20))
    endereco = Column(Text)
    observacoes = Column(Text)
    status_negociacao = Column(SQLEnum(NegociacaoStatus), default=NegociacaoStatus.LEAD)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    
    empresa = relationship("Empresa", back_populates="clientes")
    projetos = relationship("Projeto", back_populates="cliente")
    orcamentos = relationship("Orcamento", back_populates="cliente")
    historico = relationship("HistoricoCliente", back_populates="cliente")

class HistoricoCliente(Base):
    __tablename__ = 'historico_clientes'
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    cliente_id = Column(String(36), ForeignKey('clientes.id', ondelete='CASCADE'), index=True)
    tipo = Column(String(50))  # contato, reuniao, proposta, etc
    descricao = Column(Text)
    data = Column(DateTime(timezone=True), default=utc_now)
    created_by = Column(String(36), ForeignKey('usuarios.id'))
    
    cliente = relationship("Cliente", back_populates="historico")

class Projeto(Base):
    __tablename__ = 'projetos'
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    empresa_id = Column(String(36), ForeignKey('empresas.id', ondelete='CASCADE'), index=True)
    cliente_id = Column(String(36), ForeignKey('clientes.id', ondelete='SET NULL'), index=True)
    orcamento_id = Column(String(36), ForeignKey('orcamentos.id', ondelete='SET NULL'))
    titulo = Column(String(255), nullable=False)
    descricao = Column(Text)
    status = Column(SQLEnum(ProjectStatus), default=ProjectStatus.BACKLOG, index=True)
    data_inicio = Column(DateTime(timezone=True))
    data_fim_prevista = Column(DateTime(timezone=True))
    data_fim_real = Column(DateTime(timezone=True))
    valor_total = Column(Numeric(12, 2), default=0)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    
    empresa = relationship("Empresa", back_populates="projetos")
    cliente = relationship("Cliente", back_populates="projetos")
    orcamento = relationship("Orcamento", back_populates="projeto")
    colunas = relationship("ColunaKanban", back_populates="projeto", cascade="all, delete-orphan")
    contas = relationship("Conta", back_populates="projeto")
    itens_fornecedor = relationship("ItemFornecedor", back_populates="projeto")

class ColunaKanban(Base):
    __tablename__ = 'colunas_kanban'
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    projeto_id = Column(String(36), ForeignKey('projetos.id', ondelete='CASCADE'), index=True)
    titulo = Column(String(100), nullable=False)
    ordem = Column(Integer, default=0)
    cor = Column(String(7), default="#6b7280")
    
    projeto = relationship("Projeto", back_populates="colunas")
    tarefas = relationship("Tarefa", back_populates="coluna", cascade="all, delete-orphan")

class Tarefa(Base):
    __tablename__ = 'tarefas'
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    coluna_id = Column(String(36), ForeignKey('colunas_kanban.id', ondelete='CASCADE'), index=True)
    responsavel_id = Column(String(36), ForeignKey('usuarios.id', ondelete='SET NULL'), index=True)
    titulo = Column(String(255), nullable=False)
    descricao = Column(Text)
    ordem = Column(Integer, default=0)
    prazo = Column(DateTime(timezone=True))
    checklist = Column(JSON, default=list)  # [{"texto": "...", "concluido": false}]
    anexos = Column(JSON, default=list)  # [{"nome": "...", "url": "..."}]
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    
    coluna = relationship("ColunaKanban", back_populates="tarefas")
    responsavel = relationship("Usuario", foreign_keys=[responsavel_id], back_populates="tarefas_responsavel")
    comentarios = relationship("Comentario", back_populates="tarefa", cascade="all, delete-orphan")

class Comentario(Base):
    __tablename__ = 'comentarios'
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    tarefa_id = Column(String(36), ForeignKey('tarefas.id', ondelete='CASCADE'), index=True)
    autor_id = Column(String(36), ForeignKey('usuarios.id', ondelete='SET NULL'), index=True)
    texto = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    
    tarefa = relationship("Tarefa", back_populates="comentarios")
    autor = relationship("Usuario", back_populates="comentarios")

class Orcamento(Base):
    __tablename__ = 'orcamentos'
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    empresa_id = Column(String(36), ForeignKey('empresas.id', ondelete='CASCADE'), index=True)
    cliente_id = Column(String(36), ForeignKey('clientes.id', ondelete='SET NULL'), index=True)
    numero = Column(String(20), index=True)
    versao = Column(Integer, default=1)
    titulo = Column(String(255), nullable=False)
    descricao = Column(Text)
    status = Column(SQLEnum(OrcamentoStatus), default=OrcamentoStatus.RASCUNHO, index=True)
    validade = Column(DateTime(timezone=True))
    condicoes_pagamento = Column(Text)
    observacoes = Column(Text)
    
    # Campos de cálculo antigos (mantidos para compatibilidade)
    total_custo = Column(Numeric(12, 2), default=0)
    total_venda = Column(Numeric(12, 2), default=0)
    total_lucro = Column(Numeric(12, 2), default=0)
    
    # Novos campos de cálculo - Sistema Jobbs
    taxa_produtora_percent = Column(Numeric(5, 2), default=0)  # Porcentagem da produtora
    imposto_percent = Column(Numeric(5, 2), default=0)  # Porcentagem de imposto
    bv_percent = Column(Numeric(5, 2), default=0)  # BV opcional
    comissao_percent = Column(Numeric(5, 2), default=0)  # Comissão opcional
    desconto_valor = Column(Numeric(12, 2), default=0)  # Desconto em valor
    acrescimo_valor = Column(Numeric(12, 2), default=0)  # Acréscimo em valor
    
    # Modos de exibição (visivel, embutido, distribuido)
    # visivel = aparece separado, embutido = soma no total, distribuido = divide nos itens
    modo_imposto = Column(String(20), default='visivel')  # visivel, embutido, distribuido
    modo_produtora = Column(String(20), default='visivel')  # visivel, embutido, distribuido
    
    # Totais calculados
    subtotal_1 = Column(Numeric(12, 2), default=0)  # Soma dos itens
    valor_produtora = Column(Numeric(12, 2), default=0)  # Valor da taxa produtora
    subtotal_2 = Column(Numeric(12, 2), default=0)  # Subtotal 1 + Taxa Produtora
    valor_imposto = Column(Numeric(12, 2), default=0)  # Valor do imposto
    valor_bv = Column(Numeric(12, 2), default=0)  # Valor do BV
    valor_comissao = Column(Numeric(12, 2), default=0)  # Valor da comissão
    total_geral = Column(Numeric(12, 2), default=0)  # Total final
    
    link_compartilhamento = Column(String(100), unique=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    
    empresa = relationship("Empresa", back_populates="orcamentos")
    cliente = relationship("Cliente", back_populates="orcamentos")
    projeto = relationship("Projeto", back_populates="orcamento", uselist=False)
    itens = relationship("ItemOrcamento", back_populates="orcamento", cascade="all, delete-orphan")
    contas = relationship("Conta", back_populates="orcamento")

class ItemOrcamento(Base):
    __tablename__ = 'itens_orcamento'
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    orcamento_id = Column(String(36), ForeignKey('orcamentos.id', ondelete='CASCADE'), index=True)
    categoria = Column(String(100))
    descricao = Column(Text, nullable=False)
    quantidade = Column(Numeric(10, 2), default=1)
    unidade = Column(String(20), default="un")
    custo_unitario = Column(Numeric(12, 2), default=0)
    venda_unitario = Column(Numeric(12, 2), default=0)  # Valor base de venda
    custo_total = Column(Numeric(12, 2), default=0)
    venda_total = Column(Numeric(12, 2), default=0)
    lucro = Column(Numeric(12, 2), default=0)
    ordem = Column(Integer, default=0)
    
    # Valores finais (quando produtora/imposto distribuídos)
    venda_unitario_final = Column(Numeric(12, 2), default=0)  # Valor unitário com taxas embutidas
    venda_total_final = Column(Numeric(12, 2), default=0)  # Valor total com taxas embutidas
    
    orcamento = relationship("Orcamento", back_populates="itens")
    fornecedores = relationship("ItemFornecedor", back_populates="item_orcamento", cascade="all, delete-orphan")

class ItemFornecedorStatus(str, enum.Enum):
    PENDENTE = "pendente"
    CONTRATADO = "contratado"
    EM_EXECUCAO = "em_execucao"
    CONCLUIDO = "concluido"
    CANCELADO = "cancelado"

class Fornecedor(Base):
    """Cadastro de fornecedores"""
    __tablename__ = 'fornecedores'
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    empresa_id = Column(String(36), ForeignKey('empresas.id', ondelete='CASCADE'), index=True)
    tipo = Column(String(2), default="PJ")  # PF ou PJ
    cpf_cnpj = Column(String(18), index=True)
    nome = Column(String(255), nullable=False)
    nome_fantasia = Column(String(255))
    email = Column(String(255))
    telefone = Column(String(20))
    endereco = Column(Text)
    observacoes = Column(Text)
    ativo = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    
    empresa = relationship("Empresa", back_populates="fornecedores")
    itens_fornecedor = relationship("ItemFornecedor", back_populates="fornecedor")

class ItemFornecedor(Base):
    """Vínculo entre item do orçamento e fornecedor"""
    __tablename__ = 'itens_fornecedor'
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    item_orcamento_id = Column(String(36), ForeignKey('itens_orcamento.id', ondelete='CASCADE'), index=True)
    fornecedor_id = Column(String(36), ForeignKey('fornecedores.id', ondelete='CASCADE'), index=True)
    projeto_id = Column(String(36), ForeignKey('projetos.id', ondelete='SET NULL'), index=True)
    
    descricao = Column(Text)
    quantidade = Column(Numeric(10, 2), default=1)
    unidade = Column(String(20), default="un")
    custo_unitario = Column(Numeric(12, 2), default=0)
    custo_total = Column(Numeric(12, 2), default=0)
    prazo = Column(DateTime(timezone=True))
    observacoes = Column(Text)
    status = Column(SQLEnum(ItemFornecedorStatus), default=ItemFornecedorStatus.PENDENTE)
    
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    
    item_orcamento = relationship("ItemOrcamento", back_populates="fornecedores")
    fornecedor = relationship("Fornecedor", back_populates="itens_fornecedor")
    projeto = relationship("Projeto", back_populates="itens_fornecedor")
    contas = relationship("Conta", back_populates="item_fornecedor")

class Conta(Base):
    __tablename__ = 'contas'
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    empresa_id = Column(String(36), ForeignKey('empresas.id', ondelete='CASCADE'), index=True)
    projeto_id = Column(String(36), ForeignKey('projetos.id', ondelete='SET NULL'), index=True)
    orcamento_id = Column(String(36), ForeignKey('orcamentos.id', ondelete='SET NULL'), index=True)
    item_fornecedor_id = Column(String(36), ForeignKey('itens_fornecedor.id', ondelete='SET NULL'), index=True)
    tipo = Column(SQLEnum(ContaTipo), nullable=False, index=True)
    categoria = Column(String(100))
    descricao = Column(Text, nullable=False)
    valor = Column(Numeric(12, 2), nullable=False)
    data_vencimento = Column(DateTime(timezone=True), index=True)
    data_pagamento = Column(DateTime(timezone=True))
    status = Column(SQLEnum(ContaStatus), default=ContaStatus.PENDENTE, index=True)
    forma_pagamento = Column(String(50))
    comprovante_url = Column(Text)
    observacoes = Column(Text)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    
    empresa = relationship("Empresa", back_populates="contas")
    projeto = relationship("Projeto", back_populates="contas")
    orcamento = relationship("Orcamento", back_populates="contas")
    item_fornecedor = relationship("ItemFornecedor", back_populates="contas")
