"""Оцінки та шкала ECTS."""

from dataclasses import dataclass, field
from datetime import date

from student_portal.exceptions import InvalidGradeError

MIN_SCORE = 0
MAX_SCORE = 100
ECTS_LETTERS = ("A", "B", "C", "D", "E", "Fx")


def ects_grade(score: int) -> str:
    """Переводить цілу оцінку 0–100 у літеру ECTS; 0 належить до Fx."""
    if type(score) is not int:
        raise InvalidGradeError("оцінка має бути цілим числом")
    if not MIN_SCORE <= score <= MAX_SCORE:
        raise InvalidGradeError(
            f"оцінка має бути від {MIN_SCORE} до {MAX_SCORE}, отримано {score}"
        )
    match score:
        case s if s > 90:
            return "A"
        case s if s >= 82:
            return "B"
        case s if s >= 75:
            return "C"
        case s if s >= 67:
            return "D"
        case s if s >= 60:
            return "E"
        case _:
            return "Fx"


@dataclass(frozen=True, slots=True)
class Grade:
    """Незмінна оцінка з дисципліни за 100-бальною шкалою."""

    course: str
    score: int
    graded_on: date = field(default_factory=date.today)

    def __post_init__(self) -> None:
        ects_grade(self.score)
        if not isinstance(self.course, str) or not self.course.strip():
            raise ValueError("назва дисципліни не може бути порожньою")
        if type(self.graded_on) is not date:
            raise ValueError("дата оцінки має бути об’єктом date")

    @property
    def ects(self) -> str:
        return ects_grade(self.score)
