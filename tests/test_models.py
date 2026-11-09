"""ORM persistence, import command, admin, and individual variant 4."""

from io import StringIO

import pytest
from django.core.management import CommandError, call_command
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.urls import reverse
from pytest_django.asserts import assertContains, assertNotContains

from student_portal.storage import save_group
from students.models import Grade, Group, Student
from students.services import get_group, store_group

pytestmark = pytest.mark.django_db


def test_store_group_is_idempotent_and_preserves_ranking(group):
    assert store_group(group) == (3, 3)
    assert (Group.objects.count(), Student.objects.count(), Grade.objects.count()) == (
        1,
        3,
        3,
    )
    assert store_group(group) == (3, 3)
    assert Grade.objects.count() == 3
    assert [s.last_name for s in get_group().ranking()] == [
        "Коваль",
        "Мельник",
        "Бойко",
    ]


def test_database_rejects_score_over_100_and_protects_group(group):
    store_group(group)
    with transaction.atomic(), pytest.raises(IntegrityError):
        Grade.objects.create(
            student=Student.objects.get(pk=1),
            course="Python",
            score=101,
            graded_on="2026-11-09",
        )
    with pytest.raises(ProtectedError):
        Group.objects.get().delete()


def test_load_group_command(tmp_path, group):
    path = tmp_path / "group.json"
    save_group(group, path)
    output = StringIO()
    call_command("load_group", str(path), stdout=output)
    call_command("load_group", str(path), stdout=output)
    assert output.getvalue().count("Група КН-11: студентів - 3, оцінок - 3") == 2
    assert (Group.objects.count(), Student.objects.count(), Grade.objects.count()) == (
        1,
        3,
        3,
    )
    with pytest.raises(CommandError, match="не знайдено"):
        call_command("load_group", str(tmp_path / "missing.json"))


def test_admin_student_list_and_inline(admin_client, group):
    store_group(group)
    listing = admin_client.get(reverse("admin:students_student_changelist"))
    assertContains(listing, "Коваль")
    assertContains(listing, "Мельник")
    detail = admin_client.get(reverse("admin:students_student_change", args=[1]))
    assertContains(detail, 'name="grades-0-course"')


def test_variant4_grade_filter_and_search(admin_client, group):
    store_group(group)
    url = reverse("admin:students_grade_changelist")
    filtered = admin_client.get(url, {"ects": "A"})
    assertContains(filtered, "95")
    assertNotContains(filtered, "88")
    assertNotContains(filtered, "61")
    searched = admin_client.get(url, {"q": "Мельник"})
    assertContains(searched, "Мельник")
    assertNotContains(searched, "Коваль")
