"""add gameweek_id to ledger_entry

Revision ID: 940cde429309
Revises: 17c46971f820
Create Date: 2026-10-05 21:01:14.118354

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '940cde429309'
down_revision: Union[str, Sequence[str], None] = '17c46971f820'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('ledger_entry', schema=None) as batch_op:
        batch_op.add_column(sa.Column('gameweek_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_ledger_entry_gameweek_id',
            'gameweek',
            ['gameweek_id'],
            ['id']
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('ledger_entry', schema=None) as batch_op:
        batch_op.drop_constraint('fk_ledger_entry_gameweek_id', type_='foreignkey')
        batch_op.drop_column('gameweek_id')
