from __future__ import annotations

import csv
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ..config import settings
from ..database import get_session
from ..models import Marriage, Person


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
    filename = filename or f"{person.name.replace(' ', '_')}.pdf"
    path = settings.report_dir / filename
    pdf = canvas.Canvas(str(path), pagesize=A4)
    width, height = A4
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(50, height - 50, f"Profil {person.name}")
    pdf.setFont("Helvetica", 12)
    y = height - 100
    for line in _person_lines(person):
        pdf.drawString(50, y, line)
        y -= 20
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
