from __future__ import annotations

from collections import defaultdict
from html import escape

from graphviz import Digraph
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ..config import settings
from ..database import get_session
from ..models import ChildLink, Marriage, Person


MALE_COLOR = "#CDE7FF"
FEMALE_COLOR = "#FFE0F0"
UNKNOWN_COLOR = "#E2E8F0"
NODE_BORDER_COLOR = "#4A5568"
EDGE_COLOR = "#4B5563"
LINEAGE_SYMBOL = "★"
LINEAGE_COLOR = "#2563EB"


def _gender_style(gender: str | None) -> tuple[str, str]:
    normalized = (gender or "").lower()
    if normalized.startswith("m"):
        return "♂", MALE_COLOR
    if normalized.startswith("f"):
        return "♀", FEMALE_COLOR
    return "?", UNKNOWN_COLOR


def _person_label(person: Person) -> str:
    symbol, color = _gender_style(person.gender)
    detail_html = escape(person.name)
    return (
        f'<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" COLOR="{NODE_BORDER_COLOR}">'
        f'<TR>'
        f'<TD WIDTH="20" ALIGN="CENTER" BGCOLOR="{color}"><B>{symbol}</B></TD>'
        f'<TD ALIGN="LEFT" BGCOLOR="{color}">{detail_html}</TD>'
        f'</TR>'
        f'</TABLE>>'
    )


def _marriage_row(person: Person | None, port: str, is_lineage: bool) -> str:
    if not person:
        symbol, color = "?", UNKNOWN_COLOR
        name = "Unknown"
    else:
        symbol, color = _gender_style(person.gender)
        indicator = (
            f' <FONT COLOR="{LINEAGE_COLOR}">{LINEAGE_SYMBOL}</FONT>'
            if is_lineage
            else ""
        )
        name = f"{escape(person.name)}{indicator}"
    return (
        f"<TR>"
        f'<TD WIDTH="20" ALIGN="CENTER" BGCOLOR="{color}"><B>{symbol}</B></TD>'
        f'<TD PORT="{port}" ALIGN="LEFT" BGCOLOR="{color}">{name}</TD>'
        f"</TR>"
    )


def _marriage_label(marriage: Marriage, lineage_people: set[int]) -> str:
    husband_lineage = bool(marriage.husband_id and marriage.husband_id in lineage_people)
    wife_lineage = bool(marriage.wife_id and marriage.wife_id in lineage_people)
    return (
        f'<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" COLOR="{NODE_BORDER_COLOR}">'
        f"{_marriage_row(marriage.husband, 'husband', husband_lineage)}"
        f"{_marriage_row(marriage.wife, 'wife', wife_lineage)}"
        f'</TABLE>>'
    )


def build_tree_image(filename: str = "family_tree") -> str:
    output_path = settings.assets_dir / filename
    graph = Digraph("FamilyTree", engine=settings.graphviz_engine, format="png")
    graph.attr(rankdir="TB", nodesep="0.6", ranksep="0.9", splines="curved")
    graph.attr("node", shape="box", style="rounded", fontname="Helvetica", margin="0.12")
    graph.attr("edge", color=EDGE_COLOR, arrowhead="normal", arrowsize="0.8")

    with get_session() as session:
        people = session.scalars(select(Person)).all()
        marriages = session.scalars(
            select(Marriage).options(
                selectinload(Marriage.husband),
                selectinload(Marriage.wife),
                selectinload(Marriage.children).selectinload(ChildLink.child),
            )
        ).all()

    lineage_people = {
        child_link.child_id for marriage in marriages for child_link in marriage.children
    }
    person_marriages: dict[int, list[tuple[str, str]]] = defaultdict(list)

    for marriage in marriages:
        marriage_node = f"marriage_{marriage.id}"
        graph.node(marriage_node, _marriage_label(marriage, lineage_people))
        if marriage.husband_id:
            person_marriages[marriage.husband_id].append((marriage_node, "husband"))
        if marriage.wife_id:
            person_marriages[marriage.wife_id].append((marriage_node, "wife"))

    for person in people:
        if person_marriages.get(person.id):
            continue
        graph.node(f"person_{person.id}", _person_label(person))

    for marriage in marriages:
        marriage_node = f"marriage_{marriage.id}"
        child_rank_nodes: list[str] = []
        for child_link in marriage.children:
            targets = person_marriages.get(child_link.child_id)
            if not targets:
                child_node = f"person_{child_link.child_id}"
                graph.edge(marriage_node, child_node)
                child_rank_nodes.append(child_node)
            else:
                for target_node, port in targets:
                    graph.edge(marriage_node, f"{target_node}:{port}")
                    child_rank_nodes.append(target_node)
        if len(child_rank_nodes) > 1:
            with graph.subgraph() as siblings:
                siblings.attr(rank="same")
                for node_id in set(child_rank_nodes):
                    siblings.node(node_id)

    graph.render(str(output_path), cleanup=True)
    return str(output_path.with_suffix(".png"))
