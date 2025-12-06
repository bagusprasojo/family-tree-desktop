from __future__ import annotations

import csv
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from sqlalchemy import or_, select
from sqlalchemy.orm import selectinload

from ..config import settings
from ..database import get_session
from ..models import ChildLink, Marriage, Person


def _person_lines(person: Person) -> list[str]:
    return [
        f"Nama : {person.name}",
        f"Gender : {person.gender}",
        f"Lahir : {person.birth_date or '-'}",
        f"Wafat : {person.death_date or '-'}",
        f"Catatan : {person.notes or '-'}",
    ]


def generate_family_pdf(filename: str = "family-report.pdf") -> str:
    path = settings.report_dir / filename
    with get_session() as session:
        people = session.scalars(select(Person).order_by(Person.name)).all()
        marriages = session.scalars(
            select(Marriage).options(selectinload(Marriage.husband), selectinload(Marriage.wife))
        ).all()

    pdf = canvas.Canvas(str(path), pagesize=A4)
    width, height = A4
    y = height - 50
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(50, y, "Family Tree Report")
    y -= 30
    pdf.setFont("Helvetica", 10)
    for person in people:
        for line in _person_lines(person):
            pdf.drawString(50, y, line)
            y -= 15
            if y < 60:
                pdf.showPage()
                pdf.setFont("Helvetica", 10)
                y = height - 50
        pdf.drawString(50, y, "-" * 60)
        y -= 20
    pdf.showPage()
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, height - 50, "Data Pernikahan")
    y = height - 80
    pdf.setFont("Helvetica", 10)
    for marriage in marriages:
        pdf.drawString(
            50,
            y,
            f"{marriage.husband.name if marriage.husband else '?'} & "
            f"{marriage.wife.name if marriage.wife else '?'} - {marriage.marriage_date or '-'}",
        )
        y -= 20
        if y < 60:
            pdf.showPage()
            pdf.setFont("Helvetica", 10)
            y = height - 50
    pdf.save()
    return str(path)


def generate_person_pdf(person_id: int, filename: str | None = None) -> str:
    with get_session() as session:
        person = session.get(Person, person_id)
        if not person:
            raise ValueError("Person not found")
        parent_links = session.scalars(
            select(ChildLink)
            .where(ChildLink.child_id == person.id)
            .options(
                selectinload(ChildLink.marriage).selectinload(Marriage.husband),
                selectinload(ChildLink.marriage).selectinload(Marriage.wife),
                selectinload(ChildLink.marriage)
                .selectinload(Marriage.children)
                .selectinload(ChildLink.child),
            )
        ).all()
        parents: list[str] = []
        parent_ids: set[int] = set()
        siblings: list[str] = []
        sibling_ids: set[int] = set()
        for link in parent_links:
            marriage = link.marriage
            if not marriage:
                continue
            for relative in (marriage.husband, marriage.wife):
                if relative and relative.id not in parent_ids:
                    parents.append(relative.name)
                    parent_ids.add(relative.id)
            for sibling_link in marriage.children:
                sibling = sibling_link.child
                if sibling and sibling.id != person.id and sibling.id not in sibling_ids:
                    siblings.append(sibling.name)
                    sibling_ids.add(sibling.id)
        spouse_marriages = session.scalars(
            select(Marriage)
            .where(or_(Marriage.husband_id == person.id, Marriage.wife_id == person.id))
            .options(
                selectinload(Marriage.husband),
                selectinload(Marriage.wife),
                selectinload(Marriage.children).selectinload(ChildLink.child),
            )
        ).all()
        spouses: list[str] = []
        spouse_ids: set[int] = set()
        children: list[str] = []
        child_ids: set[int] = set()
        for marriage in spouse_marriages:
            partner = marriage.wife if marriage.husband_id == person.id else marriage.husband
            if partner and partner.id not in spouse_ids:
                spouses.append(partner.name)
                spouse_ids.add(partner.id)
            for child_link in marriage.children:
                child = child_link.child
                if child and child.id != person.id and child.id not in child_ids:
                    children.append(child.name)
                    child_ids.add(child.id)
    filename = filename or f"{person.name.replace(' ', '_')}.pdf"
    path = settings.report_dir / filename
    pdf = canvas.Canvas(str(path), pagesize=A4)
    width, height = A4
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(50, height - 50, f"Profil {person.name}")
    y = height - 100

    def write_lines(lines: list[str], font: str = "Helvetica", size: int = 12, leading: int = 20, indent: int = 50):
        nonlocal y
        if not lines:
            return
        pdf.setFont(font, size)
        for line in lines:
            if y < 60:
                pdf.showPage()
                y = height - 50
                pdf.setFont(font, size)
            pdf.drawString(indent, y, line)
            y -= leading

    def write_section(title: str, rows: list[str]):
        nonlocal y
        write_lines([title], font="Helvetica-Bold", size=12, leading=18)
        content = rows if rows else ["-"]
        write_lines([f"- {value}" for value in content], font="Helvetica", size=11, leading=16, indent=60)
        y -= 4

    write_lines(_person_lines(person))
    write_section("Orang Tua", parents)
    write_section("Saudara Kandung", siblings)
    write_section("Pasangan", spouses)
    write_section("Anak", children)
    pdf.save()
    return str(path)


def export_people_csv(filename: str = "people.csv") -> str:
    path = settings.export_dir / filename
    with get_session() as session:
        people = session.scalars(select(Person).order_by(Person.name)).all()
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["ID", "Name", "Gender", "Birth", "Death", "Notes"])
        for person in people:
            writer.writerow(
                [
                    person.id,
                    person.name,
                    person.gender,
                    person.birth_date or "",
                    person.death_date or "",
                    person.notes or "",
                ]
            )
    return str(path)
