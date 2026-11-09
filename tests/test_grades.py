"""Межі шкали ECTS та інваріанти оцінки."""

from dataclasses import FrozenInstanceError
from datetime import date

import pytest

from student_portal.exceptions import InvalidGradeError
from student_portal.grades import Grade, ects_grade


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (100, "A"),
        (90, "A"),
        (89, "B"),
        (82, "B"),
        (81, "C"),
        (75, "C"),
        (74, "D"),
        (67, "D"),
        (66, "E"),
        (60, "E"),
        (59, "Fx"),
        (1, "Fx"),
        (0, "Fx"),
    ],
)
def test_ects_grade_boundaries(score, expected):
    assert ects_grade(score) == expected


@pytest.mark.parametrize("score", [0, 100], ids=["minimum", "maximum"])
def test_grade_accepts_extreme_valid_scores(score):
    grade = Grade("Python", score)

    assert grade.score == score


@pytest.mark.parametrize("score", [-1, 101], ids=["below-min", "above-max"])
def test_grade_rejects_score_out_of_range(score):
    with pytest.raises(InvalidGradeError, match="від 0 до 100"):
        Grade("Python", score)


def test_grade_ects_property():
    assert Grade("Python", 85).ects == "B"


def test_grade_defaults_to_today_even_across_midnight():
    before = date.today()

    grade = Grade("Python", 85)

    assert before <= grade.graded_on <= date.today()


def test_grade_is_immutable():
    grade = Grade("Python", 85)

    with pytest.raises(FrozenInstanceError):
        grade.score = 100
