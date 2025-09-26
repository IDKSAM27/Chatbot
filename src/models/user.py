from __future__ import annotations

from flask_login import UserMixin
from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from ..app import db

__all__ = ("Users", "Moderators")


class Users(db.Model, UserMixin):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(200), nullable=False)

    created_at: Mapped[DateTime] = mapped_column(DateTime, nullable=False, default=func.now())

    def get_id(self):
        return str(self.id)

    def check_password(self, password: str) -> bool:
        return str(self.password) == str(password)


class Moderators(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime, nullable=False, default=func.now())
