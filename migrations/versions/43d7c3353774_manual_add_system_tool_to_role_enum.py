"""manual_add_system_tool_to_role_enum

Revision ID: 43d7c3353774
Revises: abb4e2a4df9b
Create Date: 2025-05-24 22:56:35.255902

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '43d7c3353774'
down_revision = 'abb4e2a4df9b'
branch_labels = None
depends_on = None


def upgrade():
    # PostgreSQL allows adding values to existing enums with ALTER TYPE
    op.execute("ALTER TYPE role_enum ADD VALUE IF NOT EXISTS 'system'")
    op.execute("ALTER TYPE role_enum ADD VALUE IF NOT EXISTS 'tool'")


def downgrade():
    pass
