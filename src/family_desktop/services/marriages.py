from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ..database import get_session
from ..models import ChildLink, Marriage, Person


def _parse_date(value: str | None):
    if not value:
        return None
    if isinstance(value, datetime):
        return value.date()
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def list_marriages() -> list[dict]:
    with get_session() as session:
        marriages = session.scalars(select(Marriage)).all()
        return [marriage.to_dict() for marriage in marriages]


def create_marriage(payload: dict) -> dict:
    with get_session() as session:
        marriage = Marriage(
            husband_id=payload["husband_id"],
            wife_id=payload["wife_id"],
            marriage_date=_parse_date(payload.get("marriage_date")),
            notes=payload.get("notes"),
        )
        session.add(marriage)
        session.flush()
        return marriage.to_dict()


def update_marriage(marriage_id: int, payload: dict) -> dict:
    with get_session() as session:
        marriage = session.get(Marriage, marriage_id)
        if not marriage:
            raise ValueError("Marriage not found")
        for key in ("husband_id", "wife_id", "notes"):
            if key in payload:
                setattr(marriage, key, payload[key])
        if "marriage_date" in payload:
            marriage.marriage_date = _parse_date(payload["marriage_date"])
        session.add(marriage)
        session.flush()
        return marriage.to_dict()


def delete_marriage(marriage_id: int) -> None:
    with get_session() as session:
        marriage = session.get(Marriage, marriage_id)
        if marriage:
            session.query(ChildLink).filter(ChildLink.marriage_id == marriage.id).delete()
            session.delete(marriage)


def add_child(marriage_id: int, child_id: int) -> dict:
    with get_session() as session:
        marriage = session.get(Marriage, marriage_id)
        child = session.get(Person, child_id)
        if not marriage or not child:
            raise ValueError("Marriage or child not found")
        link = ChildLink(marriage_id=marriage.id, child_id=child.id)
        link.child = child
        session.add(link)
        session.flush()
        return link.to_dict()


def remove_child(link_id: int) -> None:
    with get_session() as session:
        link = session.get(ChildLink, link_id)
        if link:
            session.delete(link)


def list_children(marriage_id: int) -> list[dict]:
    with get_session() as session:
        stmt = (
            select(ChildLink)
            .where(ChildLink.marriage_id == marriage_id)
            .options(selectinload(ChildLink.child))
        )
        children = session.scalars(stmt).all()
        return [child.to_dict() for child in children]
