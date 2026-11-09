"""Особи навчального процесу."""

import pytest

from student_portal.grades import Grade
from student_portal.people import Person, Student, Teacher


@pytest.mark.parametrize(
    ("person_type", "role"),
    [
        pytest.param(Student, "студент", id="student"),
        pytest.param(Teacher, "викладач", id="teacher"),
    ],
)
def test_full_name_starts_with_last_name_and_str_contains_role(person_type, role):
    person = person_type(1, "Олена", "Коваль")

    assert person.full_name == "Коваль Олена"
    assert str(person) == f"Коваль Олена ({role})"


def test_person_is_abstract():
    with pytest.raises(TypeError, match="abstract"):
        Person(1, "Олена", "Коваль")


def test_student_without_grades_has_no_average(make_student):
    assert make_student().average() is None


def test_average_of_two_grades(make_student):
    student = make_student("Коваль", 95, 88)

    assert student.average() == pytest.approx(91.5)


def test_adding_grade_changes_average(make_student):
    student = make_student("Коваль", 80)

    student.add_grade(Grade("Git", 100))

    assert student.average() == pytest.approx(90)


def test_grades_for_selects_only_requested_course(make_student):
    student = make_student("Коваль", 95, 88)
    student.add_grade(Grade("Git", 61))

    assert [g.score for g in student.grades_for("Python")] == [95, 88]


def test_students_have_independent_grade_lists(make_student):
    first, second = make_student(), make_student()

    first.add_grade(Grade("Python", 100))

    assert second.grades == []
    assert first.id != second.id
