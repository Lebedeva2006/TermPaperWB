
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [col['name'] for col in inspector.get_columns('search_cache')]

    if 'created_at' not in columns:
        op.add_column(
            'search_cache',
            sa.Column(
                'created_at',
                sa.DateTime(),
                server_default=sa.text('now()'),
                nullable=False,
            )
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [col['name'] for col in inspector.get_columns('search_cache')]

    if 'created_at' in columns:
        op.drop_column('search_cache', 'created_at')