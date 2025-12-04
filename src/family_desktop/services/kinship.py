from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Optional

from sqlalchemy import select

from ..database import get_session
from ..models import ChildLink, Marriage, Person


@dataclass(slots=True)
class RelationshipResult:
    path: list[str]
    distance: int
    is_mahram: bool


def _build_graph():
    adjacency: dict[int, set[int]] = {}
    labels: dict[int, str] = {}
    with get_session() as session:
        people = session.scalars(select(Person)).all()
        marriages = session.scalars(select(Marriage)).all()
        children = session.scalars(select(ChildLink)).all()
    marriage_map = {marriage.id: marriage for marriage in marriages}
    for person in people:
        adjacency[person.id] = set()
        labels[person.id] = person.name
    for marriage in marriages:
        if marriage.husband_id and marriage.wife_id:
            adjacency[marriage.husband_id].add(marriage.wife_id)
            adjacency[marriage.wife_id].add(marriage.husband_id)
    for child in children:
        marriage = marriage_map.get(child.marriage_id)
        parents = []
        if marriage:
            parents = [marriage.husband_id, marriage.wife_id]
        for parent_id in parents:
            if parent_id:
                adjacency[parent_id].add(child.child_id)
                adjacency[child.child_id].add(parent_id)
    return adjacency, labels


def find_relationship(source_id: int, target_id: int) -> Optional[RelationshipResult]:
    adjacency, labels = _build_graph()
    if source_id not in adjacency or target_id not in adjacency:
        return None
    visited = {source_id}
    queue = deque([(source_id, [source_id])])
    while queue:
        node, path = queue.popleft()
        if node == target_id:
            relation_labels = [labels[node_id] for node_id in path]
            distance = len(path) - 1
            is_mahram = distance <= 3
            return RelationshipResult(relation_labels, distance, is_mahram)
        for neighbor in adjacency.get(node, []):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))
    return None
