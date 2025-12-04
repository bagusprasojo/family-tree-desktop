from __future__ import annotations

from graphviz import Digraph
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ..config import settings
from ..database import get_session
from ..models import ChildLink, Marriage, Person


def _person_label(person: Person) -> str:
    parts = [person.name]
    if person.birth_date:
        parts.append(f"b. {person.birth_date.isoformat()}")
    if person.death_date:
        parts.append(f"d. {person.death_date.isoformat()}")
    return "\\n".join(parts)


def build_tree_image(filename: str = "family_tree") -> str:
    output_path = settings.assets_dir / filename
    graph = Digraph("FamilyTree", engine=settings.graphviz_engine, format="png")
    graph.attr(rankdir="TB", node="shape=box,style=rounded")

    with get_session() as session:
        people = session.scalars(select(Person)).all()
        marriages = session.scalars(
            select(Marriage).options(
                selectinload(Marriage.children).selectinload(ChildLink.child),
            )
        ).all()

    for person in people:
        graph.node(f"person_{person.id}", _person_label(person))

    for marriage in marriages:
        marriage_node = f"marriage_{marriage.id}"
        graph.node(marriage_node, shape="point", label="", width="0.1")
        if marriage.husband_id:
            graph.edge(f"person_{marriage.husband_id}", marriage_node)
        if marriage.wife_id:
            graph.edge(f"person_{marriage.wife_id}", marriage_node)
        for child_link in marriage.children:
            graph.edge(marriage_node, f"person_{child_link.child_id}")

    graph.render(str(output_path), cleanup=True)
    return str(output_path.with_suffix(".png"))
