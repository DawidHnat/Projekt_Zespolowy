from datetime import datetime
from uuid import UUID

from sqlalchemy import JSON, CheckConstraint, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import Base


class AccountPreference(Base):
    __tablename__ = "account_preferences"
    __table_args__ = (
        CheckConstraint("version >= 1", name="ck_account_preferences_version"),
        CheckConstraint(
            "module IN ('dashboard', 'vehicles')",
            name="ck_account_preferences_module",
        ),
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    module: Mapped[str] = mapped_column(String(40), primary_key=True)
    value: Mapped[dict] = mapped_column(JSON, nullable=False)
    version: Mapped[int] = mapped_column(nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
