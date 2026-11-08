"""Учасники навчального процесу."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from statistics import fmean

from student_portal.grades import Grade


@dataclass
class Person(ABC):
    """Абстрактна особа зі спільними даними."""

    id: int
    first_name: str
    last_name: str

    def __post_init__(self) -> None:
        if type(self.id) is not int or self.id < 1:
            raise ValueError("ID має бути додатним цілим числом")
        for value in (self.first_name, self.last_name):
            if not isinstance(value, str) or not value.strip():
                raise ValueError("ім’я та прізвище не можуть бути порожніми")

    @property
    def full_name(self) -> str:
        return f"{self.last_name} {self.first_name}"

    @property
    @abstractmethod
    def role(self) -> str:
        """Назва ролі в системі."""

    def __str__(self) -> str:
        return f"{self.full_name} ({self.role})"


@dataclass
class Student(Person):
    """Студент з незалежним списком оцінок."""

    grades: list[Grade] = field(default_factory=list)

    @property
    def role(self) -> str:
        return "студент"

    def add_grade(self, grade: Grade) -> None:
        self.grades.append(grade)

    def grades_for(self, course: str) -> list[Grade]:
        return [grade for grade in self.grades if grade.course == course]

    def average(self) -> float | None:
        return fmean(grade.score for grade in self.grades) if self.grades else None

    def average_for(self, course: str) -> float | None:
        """Середній бал з однієї дисципліни або None."""
        grades = self.grades_for(course)
        return fmean(grade.score for grade in grades) if grades else None


@dataclass
class Teacher(Person):
    """Викладач із переліком дисциплін."""

    courses: list[str] = field(default_factory=list)

    @property
    def role(self) -> str:
        return "викладач"
