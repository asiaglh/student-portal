"""Django-сторінки, команда, конфігурація та варіант 4."""

import os

import pytest
from django.conf import settings as django_settings
from django.core.management import CommandError, call_command
from django.urls import reverse
from pytest_django.asserts import assertContains, assertTemplateUsed

from config import settings as project_settings
from student_portal.grades import Grade
from student_portal.group import Group
from student_portal.storage import save_group


def test_ranking_page_lists_best_student_first(client, data_file):
    response = client.get(reverse("students:ranking"))

    assert response.status_code == 200
    assertTemplateUsed(response, "students/ranking.html")
    assert response.context["group"].name == "КН-11"
    assertContains(response, "<li>Коваль Олена: 91,5</li>", html=True)
    assertContains(response, "<li>Бойко Ірина: немає оцінок</li>", html=True)
    assert response.text.index("Коваль Олена") < response.text.index("Бойко Ірина")


def test_ranking_page_for_empty_group(client, data_file):
    save_group(Group("Порожня"), data_file)

    response = client.get(reverse("students:ranking"))

    assert response.status_code == 200
    assert "Рейтинг групи Порожня" in response.text
    assert "У групі немає студентів" in response.text


def test_unknown_url_returns_404(client):
    assert client.get("/невідома-адреса/").status_code == 404


def test_group_stats_prints_distribution(data_file, capsys):
    call_command("group_stats", str(data_file))

    output = capsys.readouterr().out
    assert "Група КН-11: 3 студентів" in output
    assert "Розподіл оцінок за шкалою ECTS:" in output
    assert "  A: 1" in output
    assert "  B: 1" in output
    assert "  E: 1" in output
    assert output.rstrip().endswith("Готово")


def test_group_stats_missing_file_raises_command_error(tmp_path):
    with pytest.raises(CommandError, match="не знайдено"):
        call_command("group_stats", str(tmp_path / "missing.json"))


def test_group_stats_bad_file_raises_command_error(tmp_path):
    path = tmp_path / "broken.json"
    path.write_text("не JSON")

    with pytest.raises(CommandError, match="неправильний формат"):
        call_command("group_stats", str(path))


def test_settings_are_configured(settings):
    assert settings.LANGUAGE_CODE == "uk"
    assert settings.TIME_ZONE == "Europe/Kyiv"
    assert "students" in settings.INSTALLED_APPS
    assert settings.STUDENT_PORTAL_DATA == settings.BASE_DIR / "data" / "group.json"
    assert os.environ["DJANGO_SECRET_KEY"] == settings.SECRET_KEY
    assert not settings.SECRET_KEY.startswith("django-insecure-")
    assert (os.environ.get("DJANGO_DEBUG", "0") == "1") == project_settings.DEBUG
    assert (
        os.environ.get("DJANGO_ALLOWED_HOSTS", "").split()
        == project_settings.ALLOWED_HOSTS
    )
    assert django_settings.ROOT_URLCONF == "config.urls"


def test_debtors_page_lists_fx_courses(client, data_file, group):
    student = group.get(2)
    student.add_grade(Grade("Python", 45))
    student.add_grade(Grade("Python", 50))
    student.add_grade(Grade("Алгебра", 58))
    save_group(group, data_file)

    response = client.get(reverse("students:debtors"))

    assert response.status_code == 200
    assertTemplateUsed(response, "students/debtors.html")
    assert response.context["group"].name == "КН-11"
    assert len(response.context["debtors"]) == 1
    assert response.context["debtors"][0]["courses"] == ["Python", "Алгебра"]
    assert "<li>Мельник Андрій: Python, Алгебра</li>" in response.text


def test_debtors_page_without_fx(client, data_file):
    response = client.get(reverse("students:debtors"))

    assert response.status_code == 200
    assert response.context["debtors"] == []
    assert "Боржників немає" in response.text
