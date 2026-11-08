"""Імпорт оцінок з журналу CSV конвеєром генераторів."""

import csv
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from student_portal.decorators import timed
from student_portal.exceptions import (
    JournalFormatError,
    StorageError,
    StudentNotFoundError,
)
from student_portal.grades import Grade
from student_portal.group import Group

FIELDS = ["student_id", "course", "score", "graded_on"]
type Row = tuple[int, dict[str, str]]


@dataclass(frozen=True, slots=True)
class JournalEntry:
    """Оцінка з журналу і номер її рядка."""

    line: int
    student_id: int
    grade: Grade


def read_rows(path: Path) -> Iterator[Row]:
    """Видає рядки з номерами, не читаючи файл повністю."""
    try:
        with path.open(encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file, delimiter=";", strict=True)
            if reader.fieldnames != FIELDS:
                raise JournalFormatError(f"заголовок має бути: {';'.join(FIELDS)}")
            for row in reader:
                if None in row:
                    raise JournalFormatError(f"рядок {reader.line_num}: зайві поля")
                yield reader.line_num, row
    except FileNotFoundError as error:
        raise StorageError(f"журнал не знайдено: {path}") from error
    except (UnicodeError, csv.Error) as error:
        raise JournalFormatError(f"неправильний формат CSV: {error}") from error
    except OSError as error:
        raise StorageError(f"не вдалося прочитати журнал {path}: {error}") from error


def parse_entries(rows: Iterable[Row]) -> Iterator[JournalEntry]:
    """Перетворює рядки CSV на типізовані оцінки, зберігаючи номер рядка."""
    for line, row in rows:
        try:
            student_id = int(row["student_id"])
            grade = Grade(
                row["course"].strip(),
                int(row["score"]),
                date.fromisoformat(row["graded_on"]),
            )
            entry = JournalEntry(line, student_id, grade)
        except (AttributeError, KeyError, TypeError, ValueError) as error:
            raise JournalFormatError(f"рядок {line}: {error}") from error
        yield entry


@timed
def import_journal(group: Group, path: Path) -> int:
    """Додає всі оцінки або жодної у разі помилки."""
    count = 0
    with group.transaction():
        for entry in parse_entries(read_rows(path)):
            try:
                student = group.get(entry.student_id)
            except StudentNotFoundError as error:
                raise JournalFormatError(f"рядок {entry.line}: {error}") from error
            student.add_grade(entry.grade)
            count += 1
    return count
