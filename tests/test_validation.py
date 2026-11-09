"""Додаткові межі моделі та помилки файлового сховища."""

import pytest

from student_portal.exceptions import InvalidGradeError, StorageError
from student_portal.grades import Grade
from student_portal.group import Group
from student_portal.people import Student
from student_portal.storage import group_from_dict, load_group, save_group


@pytest.mark.parametrize("score", [85.5, True, "85"], ids=["float", "bool", "string"])
def test_grade_requires_integer_score(score):
    with pytest.raises(InvalidGradeError, match="цілим числом"):
        Grade("Python", score)


@pytest.mark.parametrize("course", ["", " "], ids=["empty", "spaces"])
def test_grade_requires_nonempty_course(course):
    with pytest.raises(ValueError, match="не може бути порожньою"):
        Grade(course, 85)


def test_grade_rejects_nondate():
    with pytest.raises(ValueError, match="об’єктом date"):
        Grade("Python", 85, "2026-10-20")


def test_group_requires_name():
    with pytest.raises(ValueError, match="назва групи"):
        Group("")


@pytest.mark.parametrize(
    "args, message",
    [
        ((0, "A", "B"), "додатним"),
        ((1, "", "B"), "порожніми"),
    ],
)
def test_person_rejects_invalid_identity(args, message):
    with pytest.raises(ValueError, match=message):
        Student(*args)


@pytest.mark.parametrize(
    "data",
    [
        [],
        {"name": "G", "students": {}},
        {"name": "G", "students": [None]},
        {"name": "G", "students": [{"grades": {}}]},
        {"name": "G", "students": [{"grades": [None]}]},
    ],
    ids=["root-list", "students-dict", "null-student", "grades-dict", "null-grade"],
)
def test_storage_rejects_invalid_container_shapes(data):
    with pytest.raises(ValueError, match="очікується|має бути об’єктом"):
        group_from_dict(data)


def test_load_converts_permission_error(tmp_path, mocker):
    mocker.patch("pathlib.Path.open", side_effect=PermissionError("denied"))

    with pytest.raises(StorageError, match="не вдалося прочитати файл"):
        load_group(tmp_path / "group.json")


def test_save_converts_disk_error(group, tmp_path, mocker):
    mocker.patch("student_portal.storage.atomic_write", side_effect=OSError("full"))

    with pytest.raises(StorageError, match="не вдалося зберегти файл"):
        save_group(group, tmp_path / "group.json")
