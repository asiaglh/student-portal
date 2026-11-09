"""JSON та атомарний запис виключно у tmp_path."""

import json

import pytest

from student_portal.exceptions import StorageError
from student_portal.storage import atomic_write, group_to_dict, load_group, save_group


def test_round_trip_creates_parent_and_restores_equal_group(group, tmp_path):
    path = tmp_path / "nested" / "group.json"

    save_group(group, path)

    assert load_group(path) == group


def test_json_keeps_cyrillic_characters(group, tmp_path):
    path = tmp_path / "group.json"

    save_group(group, path)

    assert "Коваль" in path.read_text(encoding="utf-8")
    assert r"\u041a" not in path.read_text(encoding="utf-8")


def test_missing_file_is_reported(tmp_path):
    with pytest.raises(StorageError, match="не знайдено"):
        load_group(tmp_path / "missing.json")


@pytest.mark.parametrize(
    "defect",
    ["json", "students", "score", "date"],
    ids=["invalid-json", "missing-students", "score-105", "wrong-date"],
)
def test_corrupt_file_is_reported(group, tmp_path, defect):
    path = tmp_path / "group.json"
    data = group_to_dict(group)
    if defect == "students":
        del data["students"]
    elif defect == "score":
        data["students"][0]["grades"][0]["score"] = 105
    elif defect == "date":
        data["students"][0]["grades"][0]["graded_on"] = "01.10.2026"
    path.write_text("{" if defect == "json" else json.dumps(data), encoding="utf-8")

    with pytest.raises(StorageError, match="неправильний формат"):
        load_group(path)


def test_atomic_write_replaces_content(tmp_path):
    path = tmp_path / "file.txt"
    path.write_text("старий", encoding="utf-8")

    with atomic_write(path) as file:
        file.write("новий")

    assert path.read_text(encoding="utf-8") == "новий"
    assert list(tmp_path.iterdir()) == [path]


def test_atomic_write_keeps_old_file_and_removes_temporary_file(tmp_path):
    path = tmp_path / "file.txt"
    path.write_text("старий", encoding="utf-8")

    with pytest.raises(RuntimeError, match="збій"), atomic_write(path) as file:
        file.write("частина")
        raise RuntimeError("збій")

    assert path.read_text(encoding="utf-8") == "старий"
    assert list(tmp_path.iterdir()) == [path]
