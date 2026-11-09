"""Колекція групи, пошук, рейтинг і транзакції."""

import inspect

import pytest

from student_portal.exceptions import (
    DuplicateStudentError,
    InvalidGradeError,
    StudentNotFoundError,
)
from student_portal.grades import Grade
from student_portal.group import Group
from student_portal.people import Student


def test_length_and_iteration_follow_insertion_order(group):
    assert len(group) == 3
    assert [s.id for s in group] == [1, 2, 3]


def test_duplicate_id_is_rejected_without_changes(group):
    before = list(group)

    with pytest.raises(DuplicateStudentError, match="id=1"):
        group.add(Student(1, "Інша", "Особа"))

    assert list(group) == before


@pytest.mark.parametrize("operation", ["get", "remove"], ids=["get", "remove"])
def test_unknown_student_is_rejected(group, operation):
    with pytest.raises(StudentNotFoundError, match="id=42"):
        getattr(group, operation)(42)

    assert len(group) == 3


def test_remove_returns_removed_student(group):
    student = group.get(2)

    removed = group.remove(2)

    assert removed is student
    assert [s.id for s in group] == [1, 3]


@pytest.mark.parametrize(
    "ids, expected",
    [([], 1), ([1, 2, 3], 4), ([1, 7], 8)],
    ids=["empty", "consecutive", "gaps"],
)
def test_next_id_uses_maximum_id(ids, expected):
    group = Group("КН-11")
    for student_id in ids:
        group.add(Student(student_id, "Студент", "Тестовий"))

    assert group.next_id() == expected


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        pytest.param("Коваль", ["Коваль"], id="exact"),
        pytest.param("коваль", ["Коваль"], id="lowercase"),
        pytest.param("  Мельник ", ["Мельник"], id="spaces"),
        pytest.param("ко", ["Коваль", "Бойко"], id="substring"),
        pytest.param("Шевчук", [], id="not-found"),
    ],
)
def test_find_by_last_name(group, query, expected):
    assert [s.last_name for s in group.find(query)] == expected


def test_ranking_puts_best_first_and_ungraded_last(group):
    assert [s.id for s in group.ranking()] == [1, 2, 3]


def test_ranking_breaks_equal_averages_by_last_name(group, make_student):
    group.students.clear()
    group.add(make_student("Яценко", 80))
    group.add(make_student("Бойко", 80))

    assert [s.last_name for s in group.ranking()] == ["Бойко", "Яценко"]


def test_ranking_keeps_zero_score_before_ungraded(group):
    group.get(3).add_grade(Grade("Python", 0))
    group.get(2).grades.clear()

    assert [s.id for s in group.ranking()] == [1, 3, 2]


def test_average_ignores_ungraded_students(group):
    assert group.average() == pytest.approx((91.5 + 61) / 2)


def test_empty_group_has_no_average():
    assert Group("Порожня").average() is None


def test_iter_grades_is_lazy_and_preserves_order(group):
    pairs = group.iter_grades()

    assert inspect.isgenerator(pairs)
    assert [(s.id, g.course, g.score) for s, g in pairs] == [
        (1, "Python", 95),
        (1, "Git", 88),
        (2, "Python", 61),
    ]


def test_courses_are_unique(group):
    assert group.courses() == {"Python", "Git"}


def test_ects_distribution_uses_scale_order(group):
    distribution = group.ects_distribution()

    assert distribution == {"A": 1, "B": 1, "E": 1}
    assert list(distribution) == ["A", "B", "E"]


def test_transaction_commits_changes_on_success(group):
    with group.transaction():
        group.remove(2)
        group.get(3).add_grade(Grade("Python", 70))

    assert [s.id for s in group] == [1, 3]
    assert group.get(3).average() == 70


def test_transaction_restores_group_after_error(group):
    before = [(s.id, s.average()) for s in group]

    with pytest.raises(InvalidGradeError, match="від 0 до 100"), group.transaction():
        group.remove(2)
        group.get(3).add_grade(Grade("Python", 70))
        group.get(1).add_grade(Grade("Python", 105))

    assert [(s.id, s.average()) for s in group] == before
