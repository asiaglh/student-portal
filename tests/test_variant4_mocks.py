"""Варіант 4: атомарний експорт і всі гілки модуля journal."""

import csv

import pytest

from student_portal.exceptions import JournalFormatError, StorageError
from student_portal.journal import export_journal, import_journal, read_rows
from student_portal.storage import atomic_write


def test_export_uses_atomic_writer_with_excel_encoding(group, tmp_path, mocker):
    path = tmp_path / "export.csv"
    writer = mocker.patch("student_portal.journal.atomic_write", wraps=atomic_write)

    count = export_journal(group, path)

    writer.assert_called_once_with(path, encoding="utf-8-sig")
    assert count == 3
    assert path.read_bytes().startswith(b"\xef\xbb\xbf")
    with path.open(encoding="utf-8-sig", newline="") as file:
        assert [row["score"] for row in csv.DictReader(file, delimiter=";")] == [
            "95",
            "88",
            "61",
        ]


def test_export_converts_disk_failure_to_storage_error(group, tmp_path, mocker):
    mocker.patch(
        "student_portal.journal.atomic_write", side_effect=PermissionError("read-only")
    )

    with pytest.raises(StorageError, match="не вдалося записати журнал"):
        export_journal(group, tmp_path / "export.csv")


def test_import_rejects_extra_column(group, tmp_path):
    path = tmp_path / "extra.csv"
    path.write_text("student_id;course;score;graded_on\n1;Python;85;2026-10-20;extra\n")

    with pytest.raises(JournalFormatError, match="рядок 2: зайві поля"):
        import_journal(group, path)


@pytest.mark.parametrize(
    "error, exception, message",
    [
        pytest.param(
            UnicodeError("encoding"),
            JournalFormatError,
            "неправильний формат CSV",
            id="unicode",
        ),
        pytest.param(
            csv.Error("quotes"), JournalFormatError, "неправильний формат CSV", id="csv"
        ),
        pytest.param(
            PermissionError("denied"),
            StorageError,
            "не вдалося прочитати журнал",
            id="permission",
        ),
    ],
)
def test_reader_reports_unreadable_or_malformed_file(
    tmp_path, mocker, error, exception, message
):
    mocker.patch("pathlib.Path.open", side_effect=error)

    with pytest.raises(exception, match=message):
        list(read_rows(tmp_path / "journal.csv"))
