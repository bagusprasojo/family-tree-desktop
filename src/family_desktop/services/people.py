from __future__ import annotations

from datetime import datetime
from typing import Iterable

from sqlalchemy import Select, select

from ..database import get_session
from ..models import Person


def _parse_date(value: str | None):
    if not value:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            return None
    return value


def _query_people() -> Select[tuple[Person]]:
    return select(Person).order_by(Person.name)


def list_people() -> list[dict]:
    with get_session() as session:
        people = session.scalars(_query_people()).all()
        return [person.to_dict() for person in people]


def search_people(keyword: str) -> list[dict]:
    pattern = f"%{keyword.lower()}%"
    with get_session() as session:
        stmt = select(Person).where(Person.name.ilike(pattern))
        people = session.scalars(stmt).all()
        return [person.to_dict() for person in people]


def create_person(payload: dict) -> dict:
    person = Person(
        name=payload["name"],
        gender=payload.get("gender", "unknown"),
        birth_date=_parse_date(payload.get("birth_date")),
        death_date=_parse_date(payload.get("death_date")),
        notes=payload.get("notes"),
    )
    with get_session() as session:
        session.add(person)
        session.flush()
        return person.to_dict()


def update_person(person_id: int, payload: dict) -> dict:
    with get_session() as session:
        person = session.get(Person, person_id)
        if not person:
            raise ValueError("Person not found")
        for field in ("name", "gender", "notes"):
            if field in payload:
                setattr(person, field, payload[field])
        if "birth_date" in payload:
            person.birth_date = _parse_date(payload["birth_date"])
        if "death_date" in payload:
            person.death_date = _parse_date(payload["death_date"])
        session.add(person)
        session.flush()
        return person.to_dict()


def delete_person(person_id: int) -> None:
    with get_session() as session:
        person = session.get(Person, person_id)
        if person:
            session.delete(person)


def ensure_people(seed_data: Iterable[dict]) -> None:
    """Bootstrap data to make the first run less empty."""
    with get_session() as session:
        if session.scalar(select(Person.id).limit(1)):
            return
        for row in seed_data:
            session.add(
                Person(
                    name=row["name"],
                    gender=row.get("gender", "unknown"),
                    birth_date=_parse_date(row.get("birth_date")),
                    notes=row.get("notes"),
                )
            )

