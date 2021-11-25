import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

metadata = sa.MetaData()

project = sa.Table(
    "Project",
    metadata,
    sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    sa.Column("name", sa.TEXT),
    sa.Column("created", sa.TIMESTAMP, nullable=False, default=datetime.utcnow),
    sa.Column("updated", sa.TIMESTAMP, nullable=True),
)
