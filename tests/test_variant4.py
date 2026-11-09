"""Індивідуальні розширення варіанта 4 з ЛР2 та ЛР3."""

import inspect
from datetime import date

import pytest

from student_portal import cli
from student_portal.grades import Grade
from student_portal.group import Group
from student_portal.journal import export_journal, export_rows, import_journal


@pytest.mark.parametrize("score", [0, 100], ids=["zero-tie", "maximum-tie"])
def test_best_student_tie_uses_alphabetical_order(make_student, score):
    group = Group("КН-11")
    group.add(make_student("Яценко", score))
    best = make_student("Бойко", score)
    group.add(best)

    assert group.best_by_course() == {"Python": best}


def test_best_student_compares_course_average_not_last_grade(group):
    group.get(2).grades = [Grade("Python", 100), Grade("Python", 0)]

    best = group.best_by_course()

    assert best["Python"].id == 1


def test_best_student_omits_course_without_grades(group):
    assert "Математика" not in group.best_by_course()


def test_best_student_empty_group_returns_empty_mapping():
    assert Group("Порожня").best_by_course() == {}


def test_menu_eight_prints_best_students(group, monkeypatch, capsys):
    replies = iter(["8", "0"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(replies))

    cli.run(group)

    assert "Python: Коваль Олена — 95.0" in capsys.readouterr().out


@pytest.mark.parametrize(
    "course",
    ["Python", 'Веб; "основи"\nчастина 2'],
    ids=["plain-course", "quoted-multiline-cyrillic"],
)
def test_export_and_reimport_restore_all_grades_and_dates(group, tmp_path, course):
    group.get(3).add_grade(Grade(course, 0, date(2026, 10, 20)))
    before = {s.id: list(s.grades) for s in group}
    path = tmp_path / "journal.csv"

    count = export_journal(group, path)
    for student in group:
        student.grades.clear()
    imported = import_journal(group, path)

    assert count == imported == 4
    assert path.read_bytes().startswith(b"\xef\xbb\xbf")
    assert {s.id: s.grades for s in group} == before


@pytest.mark.parametrize("empty_kind", ["no-students", "no-grades"])
def test_export_empty_group_writes_only_header(group, tmp_path, empty_kind):
    if empty_kind == "no-students":
        group = Group("Порожня")
    else:
        for student in group:
            student.grades.clear()
    path = tmp_path / "empty.csv"

    count = export_journal(group, path)

    assert count == 0
    assert path.read_text(encoding="utf-8-sig").splitlines() == [
        "student_id;course;score;graded_on"
    ]
    assert import_journal(group, path) == 0


def test_export_rows_is_generator(group):
    rows = export_rows(group)

    assert inspect.isgenerator(rows)
    assert next(rows)["student_id"] == "1"
    rows.close()


def test_menu_eleven_exports_to_requested_path(group, tmp_path, monkeypatch, capsys):
    path = tmp_path / "menu-export.csv"
    replies = iter(["11", str(path), "0"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(replies))

    cli.run(group)

    assert "Експортовано оцінок: 3" in capsys.readouterr().out
    assert path.exists()
