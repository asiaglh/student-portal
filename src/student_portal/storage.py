"""Збереження групи у JSON з відновленням об’єктів і дат."""

import json
from datetime import date
from pathlib import Path
from typing import Any

from student_portal.exceptions import StorageError
from student_portal.grades import Grade
from student_portal.group import Group
from student_portal.people import Student


def group_to_dict(group: Group) -> dict[str, Any]:
    return {
        "name": group.name,
        "students": [
            {
                "id": s.id,
                "first_name": s.first_name,
                "last_name": s.last_name,
                "grades": [
                    {
                        "course": g.course,
                        "score": g.score,
                        "graded_on": g.graded_on.isoformat(),
                    }
                    for g in s.grades
                ],
            }
            for s in group
        ],
    }


def group_from_dict(data: dict[str, Any]) -> Group:
    if not isinstance(data, dict) or not isinstance(data["students"], list):
        raise ValueError("очікується об’єкт групи зі списком students")
    group = Group(data["name"])
    for item in data["students"]:
        if not isinstance(item, dict) or not isinstance(item.get("grades", []), list):
            raise ValueError("очікується об’єкт студента зі списком grades")
        if any(not isinstance(grade, dict) for grade in item.get("grades", [])):
            raise ValueError("оцінка має бути об’єктом JSON")
        grades = [
            Grade(g["course"], g["score"], date.fromisoformat(g["graded_on"]))
            for g in item.get("grades", [])
        ]
        group.add(Student(item["id"], item["first_name"], item["last_name"], grades))
    return group


def load_group(path: Path) -> Group:
    try:
        with path.open(encoding="utf-8") as file:
            return group_from_dict(json.load(file))
    except FileNotFoundError as error:
        raise StorageError(f"файл даних не знайдено: {path}") from error
    except (KeyError, TypeError, ValueError) as error:
        raise StorageError(f"файл {path} має неправильний формат: {error}") from error
    except OSError as error:
        raise StorageError(f"не вдалося прочитати файл {path}: {error}") from error


def save_group(group: Group, path: Path) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as file:
            json.dump(group_to_dict(group), file, ensure_ascii=False, indent=2)
    except OSError as error:
        raise StorageError(f"не вдалося зберегти файл {path}: {error}") from error
