from __future__ import annotations

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from ..app import db

__all__ = ("Sessions", "Messages", "Escalations")


class Sessions(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime, nullable=False, default=func.now())
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    escalated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class Messages(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("sessions.id"), nullable=False)
    sender: Mapped[str] = mapped_column(Enum("user", "bot", "moderator"), nullable=False)
    text: Mapped[str] = mapped_column(String(1000), nullable=False)
    moderator_id: Mapped[int] = mapped_column(Integer, ForeignKey("moderators.id"), nullable=True)
    timestamp: Mapped[DateTime] = mapped_column(DateTime, nullable=False, default=func.now())


class Escalations(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("sessions.id"), nullable=False)
    reason: Mapped[str] = mapped_column(String(1000), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime, nullable=False, default=func.now())
    resolved_at: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    resolved_by: Mapped[int] = mapped_column(Integer, ForeignKey("moderators.id"), nullable=True)
