from enum import StrEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy import String, ForeignKey
from geoalchemy2 import Geography
from typing import List
from datetime import datetime, time


class Base(AsyncAttrs, DeclarativeBase):
    pass


class UserRole(StrEnum):
    SUPEROWNER = "SUPEROWNER"
    OWNER = "OWNER"
    MANAGER = "MANAGER"
    OPERATOR = "OPERATOR"


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    role: Mapped[UserRole] = mapped_column(nullable=False)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)

    owner: Mapped['User'] = relationship(back_populates="employees", remote_side=id)
    employees: Mapped[List['User']] = relationship(back_populates="owner", cascade="all, delete-orphan")
    offices: Mapped[List['Office']] = relationship(back_populates="owner", cascade="all, delete-orphan")


class Office(Base):
    __tablename__ = 'offices'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    location = mapped_column(Geography(geometry_type='POINT', srid=4326), nullable=False)
    is_open: Mapped[bool] = mapped_column(nullable=False, default=False)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)

    owner: Mapped['User'] = relationship(back_populates="offices")
    working_hours: Mapped[List['WorkingHours']] = relationship(back_populates="office", cascade="all, delete-orphan")


class WorkingHours(Base):
    __tablename__ = 'working_hours'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    office_id: Mapped[int] = mapped_column(ForeignKey("offices.id"), nullable=False)
    day_of_week: Mapped[int] = mapped_column(nullable=False)
    opening_time: Mapped[time] = mapped_column(nullable=False)
    closing_time: Mapped[time] = mapped_column(nullable=False)

    office: Mapped[Office] = relationship(back_populates="working_hours")


class Notification(Base):
    __tablename__ = 'notifications'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    office_id: Mapped[int] = mapped_column(ForeignKey("offices.id"))
