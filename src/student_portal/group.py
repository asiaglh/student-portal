"""Академічна група."""

from collections import Counter
from collections.abc import Iterator
from dataclasses import dataclass, field
from statistics import fmean

from student_portal.exceptions import DuplicateStudentError, StudentNotFoundError
from student_portal.grades import ECTS_LETTERS
from student_portal.people import Student


@dataclass
class Group:
    """Група студентів, доступних за ідентифікатором."""

    name: str
    students: dict[int, Student] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("назва групи не може бути порожньою")

    def __len__(self) -> int:
        return len(self.students)

    def __iter__(self) -> Iterator[Student]:
        return iter(self.students.values())

    def add(self, student: Student) -> None:
        if student.id in self.students:
            raise DuplicateStudentError(f"студент з id={student.id} уже є в групі")
        self.students[student.id] = student

    def get(self, student_id: int) -> Student:
        try:
            return self.students[student_id]
        except KeyError:
            raise StudentNotFoundError(f"студента з id={student_id} немає") from None

    def remove(self, student_id: int) -> Student:
        student = self.get(student_id)
        del self.students[student_id]
        return student

    def next_id(self) -> int:
        return max(self.students, default=0) + 1

    def find(self, query: str) -> list[Student]:
        return [s for s in self if query.casefold() in s.last_name.casefold()]

    def ranking(self) -> list[Student]:
        return sorted(
            self,
            key=lambda s: (
                not s.grades,
                -(s.average() or 0),
                s.last_name.casefold(),
                s.first_name.casefold(),
                s.id,
            ),
        )

    def average(self) -> float | None:
        averages = [average for s in self if (average := s.average()) is not None]
        return fmean(averages) if averages else None

    def courses(self) -> set[str]:
        return {grade.course for student in self for grade in student.grades}

    def ects_distribution(self) -> dict[str, int]:
        counts = Counter(grade.ects for student in self for grade in student.grades)
        return {letter: counts[letter] for letter in ECTS_LETTERS if counts[letter]}

    def best_by_course(self) -> dict[str, Student]:
        """Варіант 4: найкращий за середнім балом з кожної дисципліни.

        За рівності балів перемагає перший за прізвищем, ім’ям та ID.
        Студенти без оцінок з дисципліни не беруть участі у порівнянні.
        """
        result: dict[str, Student] = {}
        for course in sorted(self.courses()):
            candidates = sorted(
                (student for student in self if student.grades_for(course)),
                key=lambda s: (s.last_name.casefold(), s.first_name.casefold(), s.id),
            )
            result[course] = max(candidates, key=lambda s: s.average_for(course) or 0)
        return result
