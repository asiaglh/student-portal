"""Спільні фікстури з незалежними даними для кожного тесту."""

from collections.abc import Callable
from io import StringIO

import pytest
from django.contrib.auth.models import Group as AuthGroup
from django.core.management import call_command
from django.test import Client

from student_portal.grades import Grade
from student_portal.group import Group
from student_portal.people import Student
from student_portal.storage import save_group
from students.services import store_group

type StudentFactory = Callable[..., Student]


@pytest.fixture
def client(client, django_user_model):
    """Client signed in as a viewer without editing permissions."""
    user = django_user_model.objects.create_user("viewer", password="pass-12345")
    client.force_login(user)
    return client


@pytest.fixture
def anonymous():
    """Client without a session for login middleware checks."""
    return Client()


@pytest.fixture
def role_user(django_user_model):
    """Create a user assigned to one of the idempotently configured roles."""
    call_command("setup_roles", stdout=StringIO())

    def create(username: str, role: str):
        user = django_user_model.objects.create_user(username, password="pass-12345")
        user.groups.add(AuthGroup.objects.get(name=role))
        return user

    return create


@pytest.fixture
def data_file(tmp_path, settings, group):
    """Use a copy of the group instead of editing data/group.json."""
    path = tmp_path / "group.json"
    save_group(group, path)
    settings.STUDENT_PORTAL_DATA = path
    return path


@pytest.fixture
def db_group(db, group):
    """Store the three-student fixture in the isolated Django test database."""
    store_group(group)
    return group


@pytest.fixture
def group() -> Group:
    """Відмінниця, студент з E та студентка без оцінок."""
    group = Group("КН-11")
    group.add(Student(1, "Олена", "Коваль", [Grade("Python", 95), Grade("Git", 88)]))
    group.add(Student(2, "Андрій", "Мельник", [Grade("Python", 61)]))
    group.add(Student(3, "Ірина", "Бойко"))
    return group


@pytest.fixture
def make_student() -> StudentFactory:
    """Фабрика студентів з незалежними оцінками та унікальними ID."""
    next_id = 100

    def make(last_name: str = "Тестовий", *scores: int) -> Student:
        nonlocal next_id
        next_id += 1
        grades = [Grade("Python", score) for score in scores]
        return Student(next_id, "Студент", last_name, grades)

    return make


@pytest.fixture
def answers(monkeypatch):
    def set_answers(*values: str) -> None:
        replies = iter(values)
        monkeypatch.setattr("builtins.input", lambda prompt="": next(replies))

    return set_answers
