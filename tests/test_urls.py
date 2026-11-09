"""ECTS routes, canonical redirects, and conditional detail links."""

import pytest
from django.urls import NoReverseMatch, Resolver404, resolve, reverse
from pytest_django.asserts import assertContains, assertNotContains

from students.views import by_ects


def test_ects_converter_resolves_only_valid_letters():
    match = resolve("/students/ects/Fx/")
    assert match.func is by_ects
    assert match.kwargs == {"letter": "Fx"}
    assert reverse("students:by-ects", args=["E"]) == "/students/ects/E/"
    for path in ("/students/ects/F/", "/students/ects/a/"):
        with pytest.raises(Resolver404):
            resolve(path)
    with pytest.raises(NoReverseMatch):
        reverse("students:by-ects", args=["F"])


def test_ects_page_filters_average(client, db_group):
    response = client.get(reverse("students:by-ects", args=["A"]))
    assertContains(response, "Коваль Олена")
    assertNotContains(response, "Мельник Андрій")
    assertNotContains(response, "Бойко Ірина")
    assertContains(client.get("/students/ects/Fx/"), "Таких студентів немає")


def test_legacy_and_home_redirects(client):
    old = client.get("/students/st/0003/")
    assert old.status_code == 301
    assert old["Location"] == "/students/3/"
    assert client.get("/students/st/3/").status_code == 404
    home = client.get("/")
    assert home.status_code == 302
    assert home["Location"] == "/students/"


def test_detail_link_is_absent_without_grades(client, db_group):
    assertContains(client.get("/students/2/"), "/students/ects/E/")
    assertNotContains(client.get("/students/3/"), "Інші студенти з оцінкою")
