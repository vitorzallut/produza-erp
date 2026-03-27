"""add_fornecedores_and_item_fornecedor

Revision ID: ed22eefd0fb2
Revises: 3807ce654538
Create Date: 2026-03-27 01:27:48.533721

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'ed22eefd0fb2'
down_revision: Union[str, Sequence[str], None] = '3807ce654538'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Criar tabela de fornecedores
    op.create_table('fornecedores',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('empresa_id', sa.String(length=36), nullable=True),
    sa.Column('tipo', sa.String(length=2), nullable=True),
    sa.Column('cpf_cnpj', sa.String(length=18), nullable=True),
    sa.Column('nome', sa.String(length=255), nullable=False),
    sa.Column('nome_fantasia', sa.String(length=255), nullable=True),
    sa.Column('email', sa.String(length=255), nullable=True),
    sa.Column('telefone', sa.String(length=20), nullable=True),
    sa.Column('endereco', sa.Text(), nullable=True),
    sa.Column('observacoes', sa.Text(), nullable=True),
    sa.Column('ativo', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['empresa_id'], ['empresas.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_fornecedores_cpf_cnpj'), 'fornecedores', ['cpf_cnpj'], unique=False)
    op.create_index(op.f('ix_fornecedores_empresa_id'), 'fornecedores', ['empresa_id'], unique=False)
    
    # Criar tabela de itens_fornecedor
    op.create_table('itens_fornecedor',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('item_orcamento_id', sa.String(length=36), nullable=True),
    sa.Column('fornecedor_id', sa.String(length=36), nullable=True),
    sa.Column('projeto_id', sa.String(length=36), nullable=True),
    sa.Column('descricao', sa.Text(), nullable=True),
    sa.Column('quantidade', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('unidade', sa.String(length=20), nullable=True),
    sa.Column('custo_unitario', sa.Numeric(precision=12, scale=2), nullable=True),
    sa.Column('custo_total', sa.Numeric(precision=12, scale=2), nullable=True),
    sa.Column('prazo', sa.DateTime(timezone=True), nullable=True),
    sa.Column('observacoes', sa.Text(), nullable=True),
    sa.Column('status', sa.Enum('PENDENTE', 'CONTRATADO', 'EM_EXECUCAO', 'CONCLUIDO', 'CANCELADO', name='itemfornecedorstatus'), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['fornecedor_id'], ['fornecedores.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['item_orcamento_id'], ['itens_orcamento.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['projeto_id'], ['projetos.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_itens_fornecedor_fornecedor_id'), 'itens_fornecedor', ['fornecedor_id'], unique=False)
    op.create_index(op.f('ix_itens_fornecedor_item_orcamento_id'), 'itens_fornecedor', ['item_orcamento_id'], unique=False)
    op.create_index(op.f('ix_itens_fornecedor_projeto_id'), 'itens_fornecedor', ['projeto_id'], unique=False)
    
    # Adicionar colunas na tabela contas
    op.add_column('contas', sa.Column('orcamento_id', sa.String(length=36), nullable=True))
    op.add_column('contas', sa.Column('item_fornecedor_id', sa.String(length=36), nullable=True))
    op.create_index(op.f('ix_contas_item_fornecedor_id'), 'contas', ['item_fornecedor_id'], unique=False)
    op.create_index(op.f('ix_contas_orcamento_id'), 'contas', ['orcamento_id'], unique=False)
    op.create_foreign_key('fk_contas_orcamento', 'contas', 'orcamentos', ['orcamento_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_contas_item_fornecedor', 'contas', 'itens_fornecedor', ['item_fornecedor_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('fk_contas_item_fornecedor', 'contas', type_='foreignkey')
    op.drop_constraint('fk_contas_orcamento', 'contas', type_='foreignkey')
    op.drop_index(op.f('ix_contas_orcamento_id'), table_name='contas')
    op.drop_index(op.f('ix_contas_item_fornecedor_id'), table_name='contas')
    op.drop_column('contas', 'item_fornecedor_id')
    op.drop_column('contas', 'orcamento_id')
    
    op.drop_index(op.f('ix_itens_fornecedor_projeto_id'), table_name='itens_fornecedor')
    op.drop_index(op.f('ix_itens_fornecedor_item_orcamento_id'), table_name='itens_fornecedor')
    op.drop_index(op.f('ix_itens_fornecedor_fornecedor_id'), table_name='itens_fornecedor')
    op.drop_table('itens_fornecedor')
    op.drop_index(op.f('ix_fornecedores_empresa_id'), table_name='fornecedores')
    op.drop_index(op.f('ix_fornecedores_cpf_cnpj'), table_name='fornecedores')
    op.drop_table('fornecedores')
