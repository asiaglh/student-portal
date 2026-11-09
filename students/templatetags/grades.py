"""Template helpers for ECTS grades and student cards."""

from django import template

from student_portal.grades import ects_grade
from student_portal.people import Student

register = template.Library()


@register.filter
def ects(score: float | None) -> str:
    """Translate an average score to ECTS; no grades have no letter."""
    if score is None:
        return ""
    return ects_grade(int(score))


@register.inclusion_tag("students/_student_card.html")
def student_card(student: Student) -> dict[str, Student]:
    """Render one ranking item with the same escaped student data."""
    return {"student": student}
