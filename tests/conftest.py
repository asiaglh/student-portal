"""Спільні фікстури з незалежними даними для кожного тесту."""

from collections.abc import Callable

import pytest

from student_portal.grades import Grade
from student_portal.group import Group
from student_portal.people import Student

type StudentFactory = Callable[..., Student]


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
