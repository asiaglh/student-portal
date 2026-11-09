"""Представлення рейтингу та боржників групи."""

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from student_portal.storage import load_group


def ranking(request: HttpRequest) -> HttpResponse:
    """Показати рейтинг групи з одного спільного JSON-файлу."""
    group = load_group(settings.STUDENT_PORTAL_DATA)
    return render(request, "students/ranking.html", {"group": group})


def debtors(request: HttpRequest) -> HttpResponse:
    """Варіант 4: показати студентів і дисципліни з оцінкою Fx."""
    group = load_group(settings.STUDENT_PORTAL_DATA)
    rows = []
    for student in group:
        courses = sorted(
            {grade.course for grade in student.grades if grade.ects == "Fx"}
        )
        if courses:
            rows.append({"student": student, "courses": courses})
    return render(request, "students/debtors.html", {"group": group, "debtors": rows})
