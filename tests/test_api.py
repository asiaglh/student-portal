"""API permissions, validation, pagination and query count."""

from datetime import date

import pytest
from rest_framework.test import APIClient

from students import models

pytestmark = pytest.mark.django_db


def api_as(user=None):
    api = APIClient()
    if user is not None:
        api.force_authenticate(user=user)
    return api


def test_anonymous_api_is_closed(db_group):
    response = api_as().get("/api/students/")
    assert response.status_code == 403
    assert "detail" in response.data


def test_student_list_and_query_count(role_user, db_group, django_assert_num_queries):
    teacher = role_user("teacher", "Викладачі")
    api = api_as(teacher)
    with django_assert_num_queries(3):
        response = api.get("/api/students/")
    assert response.status_code == 200
    assert response.data["count"] == 3
    first = response.data["results"][0]
    assert first["average"] == 91.5
    assert first["grades"][0]["ects"] == "A"


def test_teacher_creates_grade_and_score_validation(role_user, db_group):
    api = api_as(role_user("teacher", "Викладачі"))
    data = {
        "student": 1,
        "course": "Git",
        "score": 101,
        "graded_on": date.today().isoformat(),
    }
    response = api.post("/api/grades/", data, format="json")
    assert response.status_code == 400
    assert list(response.data) == ["score"]
    data["score"] = 74
    created = api.post("/api/grades/", data, format="json")
    assert created.status_code == 201
    assert created.data["ects"] == "D"
    assert models.Grade.objects.filter(student_id=1, score=74).exists()
    student = api.get("/api/students/1/")
    assert student.data["average"] == (95 + 88 + 74) / 3


def test_viewer_cannot_create_grade_and_teacher_cannot_delete(
    role_user, db_group, django_user_model
):
    viewer = django_user_model.objects.create_user("viewer2", password="pass-12345")
    payload = {
        "student": 1,
        "course": "Git",
        "score": 74,
        "graded_on": date.today().isoformat(),
    }
    assert (
        api_as(viewer).post("/api/grades/", payload, format="json").status_code == 403
    )
    teacher = role_user("teacher", "Викладачі")
    assert api_as(teacher).delete("/api/students/1/").status_code == 403
    assert (
        api_as(teacher)
        .patch("/api/grades/1/", {"score": 80}, format="json")
        .status_code
        == 404
    )


def test_dean_creates_student(role_user, db_group):
    dean = role_user("dean", "Деканат")
    group = models.Group.objects.get()
    response = api_as(dean).post(
        "/api/students/",
        {"first_name": "Ніна", "last_name": "Нова", "group": group.pk},
        format="json",
    )
    assert response.status_code == 201
    assert response.data["average"] is None
    assert response.data["grades"] == []
