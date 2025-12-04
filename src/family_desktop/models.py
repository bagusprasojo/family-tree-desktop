from __future__ import annotations

from datetime import date
from typing import Optional

from sqlalchemy import Date, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Person(Base):
    __tablename__ = "person"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    gender: Mapped[str] = mapped_column(String(10), nullable=False)
    birth_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    death_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    marriages_as_husband: Mapped[list["Marriage"]] = relationship(
        back_populates="husband",
        foreign_keys="Marriage.husband_id",
    )
    marriages_as_wife: Mapped[list["Marriage"]] = relationship(
        back_populates="wife",
        foreign_keys="Marriage.wife_id",
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "gender": self.gender,
            "birth_date": self.birth_date.isoformat() if self.birth_date else None,
            "death_date": self.death_date.isoformat() if self.death_date else None,
            "notes": self.notes or "",
        }


class Marriage(Base):
    __tablename__ = "marriage"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    husband_id: Mapped[int] = mapped_column(ForeignKey("person.id"), nullable=False)
    wife_id: Mapped[int] = mapped_column(ForeignKey("person.id"), nullable=False)
    marriage_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    husband: Mapped[Person] = relationship(
        foreign_keys=[husband_id],
        back_populates="marriages_as_husband",
    )
    wife: Mapped[Person] = relationship(
        foreign_keys=[wife_id],
        back_populates="marriages_as_wife",
    )
    children: Mapped[list["ChildLink"]] = relationship(back_populates="marriage")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "husband": self.husband.to_dict() if self.husband else None,
            "wife": self.wife.to_dict() if self.wife else None,
            "marriage_date": self.marriage_date.isoformat() if self.marriage_date else None,
            "notes": self.notes or "",
        }


class ChildLink(Base):
    __tablename__ = "children"
    __table_args__ = (
        UniqueConstraint("marriage_id", "child_id", name="uq_children_marriage_child"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    marriage_id: Mapped[int] = mapped_column(ForeignKey("marriage.id"), nullable=False)
    child_id: Mapped[int] = mapped_column(ForeignKey("person.id"), nullable=False)

    marriage: Mapped[Marriage] = relationship(back_populates="children")
    child: Mapped[Person] = relationship()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "marriage_id": self.marriage_id,
            "child": self.child.to_dict() if self.child else None,
        }


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(60), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="user")

    def to_dict(self) -> dict:
        return {"id": self.id, "username": self.username, "role": self.role}

