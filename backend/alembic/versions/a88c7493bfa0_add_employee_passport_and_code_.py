"""add_employee_passport_and_code_intelligence_models

Revision ID: a88c7493bfa0
Revises: 7d4760ba951b
Create Date: 2026-11-11 02:12:31.989935

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a88c7493bfa0'
down_revision: Union[str, Sequence[str], None] = '7d4760ba951b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('handover_reports', schema=None) as batch_op:
        batch_op.add_column(sa.Column('departing_employee_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('successor_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('lifecycle_status', sa.String(length=50), server_default='ACTIVE', nullable=False))
        batch_op.add_column(sa.Column('acknowledged_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('acknowledgement_notes', sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('handover_reports', schema=None) as batch_op:
        batch_op.drop_column('acknowledgement_notes')
        batch_op.drop_column('acknowledged_at')
        batch_op.drop_column('lifecycle_status')
        batch_op.drop_column('successor_id')
        batch_op.drop_column('departing_employee_id')
