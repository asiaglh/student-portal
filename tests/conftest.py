"""Спільні фікстури з незалежними даними для кожного тесту."""

from collections.abc import Callable

import pytest

from student_portal.grades import Grade
from student_portal.group import Group
from student_portal.people import Student
from student_portal.storage import save_group

type StudentFactory = Callable[..., Student]


@pytest.fixture
def data_file(tmp_path, settings, group):
    """Use a copy of the group instead of editing data/group.json."""
    path = tmp_path / "group.json"
    save_group(group, path)
    settings.STUDENT_PORTAL_DATA = path
    return path


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
