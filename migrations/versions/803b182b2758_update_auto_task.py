"""update auto task

Revision ID: 803b182b2758
Revises: 4dcd819f29fe
Create Date: 2025-06-09 23:04:37.281491

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '803b182b2758'
down_revision = '4dcd819f29fe'
branch_labels = None
depends_on = None


def upgrade():
    # 반드시 USING ...::jsonb 옵션으로 변환!
    op.execute("""
        ALTER TABLE auto_task
            ALTER COLUMN tool TYPE JSONB USING tool::jsonb,
            ALTER COLUMN linked_service TYPE JSONB USING linked_service::jsonb,
            ALTER COLUMN current_step TYPE JSONB USING current_step::jsonb
    """)

def downgrade():
    op.execute("""
        ALTER TABLE auto_task
            ALTER COLUMN current_step TYPE TEXT USING current_step::text,
            ALTER COLUMN linked_service TYPE TEXT USING linked_service::text,
            ALTER COLUMN tool TYPE TEXT USING tool::text
    """)
