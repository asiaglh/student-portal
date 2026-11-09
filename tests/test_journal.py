"""CSV-конвеєр, номери рядків і правило все або нічого."""

from collections.abc import Callable
from pathlib import Path

import pytest

from student_portal.exceptions import JournalFormatError, StorageError
from student_portal.journal import import_journal, parse_entries, read_rows

HEADER = "student_id;course;score;graded_on"
type JournalWriter = Callable[..., Path]


@pytest.fixture
def write_journal(tmp_path: Path) -> JournalWriter:
    def write(*rows: str, header: str = HEADER, encoding: str = "utf-8") -> Path:
        path = tmp_path / "journal.csv"
        path.write_text("\n".join([header, *rows]) + "\n", encoding=encoding)
        return path

    return write


def test_import_counts_entries_and_trims_course(group, write_journal):
    path = write_journal("1;  Вебтехнології  ;91;2026-10-20", "3;Git;74;2026-10-20")

    count = import_journal(group, path)

    assert count == 2
    assert group.get(1).grades[-1].course == "Вебтехнології"
    assert group.get(3).grades[-1].score == 74


def test_import_accepts_utf8_bom(group, write_journal):
    path = write_journal("1;Python;91;2026-10-20", encoding="utf-8-sig")

    assert import_journal(group, path) == 1


@pytest.mark.parametrize(
    "row, message",
    [
        pytest.param("1;Python;105;2026-10-20", "від 0 до 100", id="score"),
        pytest.param("1;Python;abc;2026-10-20", "invalid literal", id="text"),
        pytest.param("1;Python;80;20.10.2026", "Invalid isoformat", id="date"),
        pytest.param("1;Python;80", ".*", id="missing-column"),
        pytest.param("x;Python;80;2026-10-20", "invalid literal", id="id"),
        pytest.param("42;Python;80;2026-10-20", "id=42", id="unknown-id"),
    ],
)
def test_bad_row_is_reported_with_line_number(group, write_journal, row, message):
    path = write_journal("1;Python;91;2026-10-20", row)
    before = {s.id: list(s.grades) for s in group}

    with pytest.raises(JournalFormatError, match=f"^рядок 3: .*{message}"):
        import_journal(group, path)

    assert {s.id: s.grades for s in group} == before


def test_failed_import_changes_no_grade_counts(group, write_journal):
    path = write_journal("1;Python;91;2026-10-20", "3;Git;105;2026-10-20")
    before = {s.id: len(s.grades) for s in group}

    with pytest.raises(JournalFormatError, match="^рядок 3:"):
        import_journal(group, path)

    assert {s.id: len(s.grades) for s in group} == before


def test_wrong_header_is_rejected(group, write_journal):
    path = write_journal(header="id;course;score;date")

    with pytest.raises(JournalFormatError, match="заголовок має бути"):
        import_journal(group, path)


def test_read_rows_opens_missing_file_only_when_requested(tmp_path):
    rows = read_rows(tmp_path / "missing.csv")

    with pytest.raises(StorageError, match="журнал не знайдено"):
        next(rows)


def test_parse_entries_preserves_line_numbers(write_journal):
    path = write_journal("1;Python;91;2026-10-20", "2;Git;80;2026-10-20")

    entries = list(parse_entries(read_rows(path)))

    assert [e.line for e in entries] == [2, 3]
    assert [e.student_id for e in entries] == [1, 2]
