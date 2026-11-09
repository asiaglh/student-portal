"""Views, template composition, escaping, and the variant 4 inclusion tag."""

import pytest
from django.template import Context, Template
from django.template.loader import render_to_string
from django.urls import reverse
from pytest_django.asserts import assertContains, assertNotContains, assertTemplateUsed

from student_portal.grades import Grade
from student_portal.people import Student
from students.services import get_student_or_404, store_group
from students.templatetags.grades import ects


def test_list_order_and_templates(client, db_group):
    response = client.get(reverse("students:list"))
    assertTemplateUsed(response, "students/student_list.html")
    assertTemplateUsed(response, "base.html")
    assert [student.last_name for student in response.context["students"]] == [
        "Коваль",
        "Мельник",
        "Бойко",
    ]
    assertContains(response, "Усього: 3")


def test_search_uses_query_string(client, db_group):
    response = client.get(reverse("students:list"), {"q": " кова "})
    assert [student.last_name for student in response.context["students"]] == ["Коваль"]
    assertContains(response, 'value="кова"')


def test_search_without_results(client, db_group):
    response = client.get(reverse("students:list"), {"q": "zzz"})
    assertContains(response, "Нікого не знайдено за запитом «zzz»")
    assertContains(response, "Усього: 0")


def test_student_detail_and_empty_grades(client, db_group):
    first = client.get(reverse("students:detail", args=[1]))
    assertTemplateUsed(first, "students/student_detail.html")
    assertContains(first, "<td>B</td>", html=True)
    assertContains(first, "Середній бал: 91,5 A")
    empty = client.get(reverse("students:detail", args=[3]))
    assertContains(empty, "Оцінок ще немає")
    assertContains(empty, "Середній бал: -")


def test_unknown_student_is_404(client, db_group):
    assert client.get(reverse("students:detail", args=[42])).status_code == 404
    assert client.get(reverse("students:detail-json", args=[42])).status_code == 404
    assert client.get("/students/abc/").status_code == 404


def test_json_uses_unicode_and_null(client, db_group):
    first = client.get(reverse("students:detail-json", args=[1]))
    assert first.json() == {"id": 1, "full_name": "Коваль Олена", "average": 91.5}
    assert "Коваль" in first.content.decode("utf-8")
    assert client.get(reverse("students:detail-json", args=[3])).json() == {
        "id": 3,
        "full_name": "Бойко Ірина",
        "average": None,
    }


def test_ranking_uses_inclusion_and_include(client, db_group):
    response = client.get(reverse("students:ranking"))
    assertTemplateUsed(response, "students/_student_card.html", count=3)
    assertTemplateUsed(response, "students/_student_line.html", count=3)
    assertContains(response, "Бойко Ірина: немає оцінок")


def test_post_to_ranking_is_405(client, db_group):
    assert client.post(reverse("students:ranking")).status_code == 405


@pytest.mark.parametrize(("page", "first_surname"), [("1", "Коваль"), ("2", "Бойко")])
def test_pages(client, db_group, page, first_surname):
    response = client.get(reverse("students:pages"), {"page": page})
    assert response.status_code == 200
    assert response.context["students"][0].last_name == first_surname
    assertContains(response, f"Сторінка {page} з 2")
    assertContains(response, "/static/students/style.css")


@pytest.mark.parametrize("page", ["9", "x"])
def test_invalid_page_is_404(client, db_group, page):
    assert client.get(reverse("students:pages"), {"page": page}).status_code == 404


def test_last_page(client, db_group):
    response = client.get(reverse("students:pages"), {"page": "last"})
    assert response.context["students"][0].last_name == "Бойко"


def test_pages_follow_ranking_order(client, db_group):
    db_group.add(Student(4, "Марія", "Новак", [Grade("Python", 100)]))
    store_group(db_group)
    response = client.get(reverse("students:pages"))
    assert [student.last_name for student in response.context["students"]] == [
        "Новак",
        "Коваль",
    ]


def test_student_row_partial_renders_alone(group):
    html = render_to_string(
        "students/student_list.html#student-row", {"student": group.get(3)}
    )
    assert '<a href="/students/3/">Бойко Ірина</a>' in html
    assert "<td>-</td>" in html


def test_names_are_escaped(client, db_group):
    db_group.add(Student(4, "Марко", "<script>alert(1)</script>"))
    store_group(db_group)
    response = client.get(reverse("students:list"))
    assertContains(response, "&lt;script&gt;alert(1)&lt;/script&gt; Марко")
    assertNotContains(response, "<script>")


@pytest.mark.parametrize(
    ("score", "expected"),
    [(95, "A"), (89.9, "B"), (60, "E"), (59.5, "Fx"), (None, "")],
)
def test_ects_filter(score, expected):
    assert ects(score) == expected


def test_variant4_inclusion_tag_renders_card(group):
    html = Template("{% load grades %}{% student_card student %}").render(
        Context({"student": group.get(1)})
    )
    assert "<li>Коваль Олена: 91,5" in html


def test_variant4_inclusion_tag_escapes_name(group):
    student = Student(4, "Марко", "<script>alert(1)</script>")
    html = Template("{% load grades %}{% student_card student %}").render(
        Context({"student": student})
    )
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html
    assert "<script>" not in html


def test_service_returns_existing_student(group):
    assert get_student_or_404(group, 1) is group.get(1)
