"""add_orcamento_jobbs_fields

Revision ID: 3807ce654538
Revises: 22865fffcd99
Create Date: 2026-03-26 21:24:37.194852

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '3807ce654538'
down_revision: Union[str, Sequence[str], None] = '22865fffcd99'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add Jobbs-style calculation fields to orcamentos."""
    # Adicionar colunas ao itens_orcamento
    op.add_column('itens_orcamento', sa.Column('venda_unitario_final', sa.Numeric(precision=12, scale=2), nullable=True))
    op.add_column('itens_orcamento', sa.Column('venda_total_final', sa.Numeric(precision=12, scale=2), nullable=True))
    
    # Adicionar colunas ao orcamentos
    op.add_column('orcamentos', sa.Column('taxa_produtora_percent', sa.Numeric(precision=5, scale=2), nullable=True))
    op.add_column('orcamentos', sa.Column('imposto_percent', sa.Numeric(precision=5, scale=2), nullable=True))
    op.add_column('orcamentos', sa.Column('bv_percent', sa.Numeric(precision=5, scale=2), nullable=True))
    op.add_column('orcamentos', sa.Column('comissao_percent', sa.Numeric(precision=5, scale=2), nullable=True))
    op.add_column('orcamentos', sa.Column('desconto_valor', sa.Numeric(precision=12, scale=2), nullable=True))
    op.add_column('orcamentos', sa.Column('acrescimo_valor', sa.Numeric(precision=12, scale=2), nullable=True))
    op.add_column('orcamentos', sa.Column('modo_imposto', sa.String(length=20), nullable=True))
    op.add_column('orcamentos', sa.Column('modo_produtora', sa.String(length=20), nullable=True))
    op.add_column('orcamentos', sa.Column('subtotal_1', sa.Numeric(precision=12, scale=2), nullable=True))
    op.add_column('orcamentos', sa.Column('valor_produtora', sa.Numeric(precision=12, scale=2), nullable=True))
    op.add_column('orcamentos', sa.Column('subtotal_2', sa.Numeric(precision=12, scale=2), nullable=True))
    op.add_column('orcamentos', sa.Column('valor_imposto', sa.Numeric(precision=12, scale=2), nullable=True))
    op.add_column('orcamentos', sa.Column('valor_bv', sa.Numeric(precision=12, scale=2), nullable=True))
    op.add_column('orcamentos', sa.Column('valor_comissao', sa.Numeric(precision=12, scale=2), nullable=True))
    op.add_column('orcamentos', sa.Column('total_geral', sa.Numeric(precision=12, scale=2), nullable=True))


def downgrade() -> None:
    """Remove Jobbs-style calculation fields from orcamentos."""
    op.drop_column('orcamentos', 'total_geral')
    op.drop_column('orcamentos', 'valor_comissao')
    op.drop_column('orcamentos', 'valor_bv')
    op.drop_column('orcamentos', 'valor_imposto')
    op.drop_column('orcamentos', 'subtotal_2')
    op.drop_column('orcamentos', 'valor_produtora')
    op.drop_column('orcamentos', 'subtotal_1')
    op.drop_column('orcamentos', 'modo_produtora')
    op.drop_column('orcamentos', 'modo_imposto')
    op.drop_column('orcamentos', 'acrescimo_valor')
    op.drop_column('orcamentos', 'desconto_valor')
    op.drop_column('orcamentos', 'comissao_percent')
    op.drop_column('orcamentos', 'bv_percent')
    op.drop_column('orcamentos', 'imposto_percent')
    op.drop_column('orcamentos', 'taxa_produtora_percent')
    op.drop_column('itens_orcamento', 'venda_total_final')
    op.drop_column('itens_orcamento', 'venda_unitario_final')
