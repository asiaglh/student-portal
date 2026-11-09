"""Load the domain model and translate missing student IDs into HTTP 404."""

from django.conf import settings
from django.http import Http404

from student_portal.exceptions import StudentNotFoundError
from student_portal.group import Group
from student_portal.people import Student
from student_portal.storage import load_group


def get_group() -> Group:
    """Read the configured JSON group for each request."""
    return load_group(settings.STUDENT_PORTAL_DATA)


def get_student_or_404(group: Group, student_id: int) -> Student:
    """Return a student or let Django render a 404 response."""
    try:
        return group.get(student_id)
    except StudentNotFoundError as error:
        raise Http404(str(error)) from error
