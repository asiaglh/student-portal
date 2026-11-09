"""Translate database records to and from the independent domain model."""

from django.db import transaction
from django.db.models import Prefetch
from django.http import Http404

from student_portal.exceptions import StorageError, StudentNotFoundError
from student_portal.grades import Grade
from student_portal.group import Group
from student_portal.people import Student

from . import models


def get_group() -> Group:
    """Return the first database group as core objects for existing views."""
    students = models.Student.objects.order_by("id").prefetch_related(
        Prefetch("grades", queryset=models.Grade.objects.order_by("graded_on", "id"))
    )
    record = models.Group.objects.prefetch_related(
        Prefetch("students", queryset=students)
    ).first()
    if record is None:
        raise StorageError("у базі даних немає групи: виконайте manage.py load_group")

    group = Group(record.name)
    for student in record.students.all():
        grades = [
            Grade(grade.course, grade.score, grade.graded_on)
            for grade in student.grades.all()
        ]
        group.add(Student(student.id, student.first_name, student.last_name, grades))
    return group


@transaction.atomic
def store_group(group: Group) -> tuple[int, int]:
    """Save core objects to the database without duplicating grades on re-import."""
    record, _ = models.Group.objects.get_or_create(name=group.name)
    grade_count = 0
    for student in group:
        row, _ = models.Student.objects.update_or_create(
            id=student.id,
            defaults={
                "group": record,
                "first_name": student.first_name,
                "last_name": student.last_name,
            },
        )
        row.grades.all().delete()
        models.Grade.objects.bulk_create(
            models.Grade(
                student=row,
                course=grade.course,
                score=grade.score,
                graded_on=grade.graded_on,
            )
            for grade in student.grades
        )
        grade_count += len(student.grades)
    return len(group), grade_count


def get_student_or_404(group: Group, student_id: int) -> Student:
    """Return a student or let Django render a 404 response."""
    try:
        return group.get(student_id)
    except StudentNotFoundError as error:
        raise Http404(str(error)) from error
