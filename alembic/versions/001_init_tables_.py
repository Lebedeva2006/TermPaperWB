
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'products',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('rating', sa.Float(), nullable=True),
        sa.Column('reviews_count', sa.Integer(), nullable=True),
        sa.Column('marketplace', sa.String(), nullable=False),
        sa.Column('url', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_products_id'), 'products', ['id'], unique=False)
    op.create_index(op.f('ix_products_title'), 'products', ['title'], unique=False)

    op.create_table(
        'search_cache',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('query', sa.String(), nullable=False),
        sa.Column('marketplace', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('rating', sa.Float(), nullable=True),
        sa.Column('reviews_count', sa.Integer(), nullable=True),
        sa.Column('url', sa.String(), nullable=True),
        sa.Column('result_rank', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_search_cache_id'), 'search_cache', ['id'], unique=False)
    op.create_index(op.f('ix_search_cache_query'), 'search_cache', ['query'], unique=False)
    op.create_index(op.f('ix_search_cache_marketplace'), 'search_cache', ['marketplace'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_search_cache_marketplace'), table_name='search_cache')
    op.drop_index(op.f('ix_search_cache_query'), table_name='search_cache')
    op.drop_index(op.f('ix_search_cache_id'), table_name='search_cache')
    op.drop_table('search_cache')

    op.drop_index(op.f('ix_products_title'), table_name='products')
    op.drop_index(op.f('ix_products_id'), table_name='products')
    op.drop_table('products')