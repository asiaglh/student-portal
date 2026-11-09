"""Login, role permissions, and POST-redirect-GET page flows."""

from datetime import date, timedelta
from io import StringIO

import pytest
from django.contrib.auth.models import Group as AuthGroup
from django.contrib.messages import get_messages
from django.core.management import call_command
from django.test import Client
from django.urls import reverse

from students import models

pytestmark = pytest.mark.django_db


def test_anonymous_redirect_and_login_page(anonymous):
    response = anonymous.get(reverse("students:list"))
    assert response.status_code == 302
    assert response.url == "/accounts/login/?next=/students/"
    assert anonymous.get(reverse("login")).status_code == 200


def test_login_and_post_only_logout(django_user_model, anonymous):
    django_user_model.objects.create_user("reader", password="pass-12345")
    response = anonymous.post(
        reverse("login"), {"username": "reader", "password": "pass-12345"}
    )
    assert response.status_code == 302
    assert response.url == reverse("students:list")
    assert anonymous.get(reverse("logout")).status_code == 405
    assert anonymous.post(reverse("logout")).url == reverse("login")


def test_setup_roles_is_idempotent():
    for _ in range(2):
        call_command("setup_roles", stdout=StringIO())
    assert AuthGroup.objects.count() == 2
    assert AuthGroup.objects.get(name="Викладачі").permissions.count() == 3
    assert AuthGroup.objects.get(name="Деканат").permissions.count() == 4


def test_viewer_cannot_open_grade_form(client, db_group):
    assert client.get(reverse("students:add-grade", args=[1])).status_code == 403


def test_teacher_grade_validation_and_redirect(role_user, db_group):
    user = role_user("teacher", "Викладачі")
    browser = Client()
    browser.force_login(user)
    detail = browser.get(reverse("students:detail", args=[1]))
    assert b"grades/new" in detail.content
    assert b"/edit/" not in detail.content
    url = reverse("students:add-grade", args=[1])
    data = {"course": " Git ", "score": 101, "graded_on": date.today().isoformat()}
    before = models.Grade.objects.count()
    response = browser.post(url, data)
    assert response.status_code == 200
    assert "score" in response.context["form"].errors
    assert models.Grade.objects.count() == before
    data["score"] = 74
    data["graded_on"] = (date.today() - timedelta(days=1)).isoformat()
    response = browser.post(url, data)
    assert response.status_code == 302
    assert response.url == reverse("students:detail", args=[1])
    assert "Оцінку 74 з Git збережено" in [
        str(msg) for msg in get_messages(response.wsgi_request)
    ]
    assert models.Grade.objects.count() == before + 1
    browser.get(response.url)
    assert models.Grade.objects.count() == before + 1


def test_dean_creates_and_edits_student(role_user, db_group):
    dean = role_user("dean", "Деканат")
    browser = Client()
    browser.force_login(dean)
    group = models.Group.objects.get()
    created = browser.post(
        reverse("students:create"),
        {"first_name": "Ніна", "last_name": "Петренко", "group": group.pk},
    )
    assert created.status_code == 302
    student = models.Student.objects.get(first_name="Ніна")
    edited = browser.post(
        reverse("students:edit", args=[student.pk]),
        {"first_name": "Ніна", "last_name": "Сидоренко", "group": group.pk},
    )
    assert edited.url == reverse("students:detail", args=[student.pk])
    student.refresh_from_db()
    assert student.last_name == "Сидоренко"


def test_teacher_cannot_edit_student(role_user, db_group):
    teacher = role_user("teacher", "Викладачі")
    browser = Client()
    browser.force_login(teacher)
    assert browser.get(reverse("students:create")).status_code == 403
    assert browser.get(reverse("students:edit", args=[1])).status_code == 403


def test_variant4_delete_confirm_and_permission(role_user, db_group):
    dean = role_user("dean", "Деканат")
    teacher = role_user("teacher", "Викладачі")
    dean_browser = Client()
    dean_browser.force_login(dean)
    teacher_browser = Client()
    teacher_browser.force_login(teacher)
    url = reverse("students:delete", args=[1])
    assert "Видалити студента?" in dean_browser.get(url).content.decode()
    assert models.Student.objects.filter(pk=1).exists()
    assert teacher_browser.get(url).status_code == 403
    assert teacher_browser.post(url).status_code == 403
    deleted = dean_browser.post(url)
    assert deleted.status_code == 302
    assert deleted.url == reverse("students:list")
    assert not models.Student.objects.filter(pk=1).exists()
