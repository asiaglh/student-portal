"""Меню із підміною input та перехопленням виведення."""

import logging

import pytest

from student_portal import cli
from student_portal.cli import run
from student_portal.decorators import timed


def test_menu_adds_student(group, answers, capsys):
    answers("4", "Марія", "Шевчук", "0")

    run(group)

    assert "Додано: Шевчук Марія (студент)" in capsys.readouterr().out
    assert group.get(4).full_name == "Шевчук Марія"


def test_menu_adds_grade(group, answers, capsys):
    answers("5", "3", "Python", "74", "0")

    run(group)

    assert "Бойко Ірина: 74 (D)" in capsys.readouterr().out
    assert group.get(3).grades[-1].score == 74


@pytest.mark.parametrize(
    "values, message",
    [
        pytest.param(("5", "3", "Python", "сто"), "Помилка введення", id="text-score"),
        pytest.param(("5", "3", "Python", "105"), "Помилка введення", id="score-105"),
        pytest.param(("6", "42"), "Помилка: студента з id=42 немає", id="unknown-id"),
        pytest.param(("99",), "Невідома команда", id="unknown-command"),
    ],
)
def test_menu_continues_after_bad_input(group, answers, capsys, values, message):
    answers(*values, "1", "0")

    run(group)

    output = capsys.readouterr().out
    assert message in output
    assert "Список студентів" in output
    assert len(group) == 3


def test_command_rejects_duplicate_key_without_leaking_registry(monkeypatch):
    monkeypatch.setattr(cli, "COMMANDS", {})

    @cli.command("1", "перша")
    def first(group):
        pass

    with pytest.raises(ValueError, match="пункт меню 1 уже зайнято"):
        cli.command("1", "друга")(first)

    assert {"1": ("перша", first)} == cli.COMMANDS


def test_command_reserves_exit_key(monkeypatch):
    monkeypatch.setattr(cli, "COMMANDS", {})

    with pytest.raises(ValueError, match="пункт меню 0 уже зайнято"):
        cli.command("0", "вихід")(lambda group: None)

    assert cli.COMMANDS == {}


def test_timed_logs_duration_and_keeps_name(caplog):
    @timed
    def add(a: int, b: int) -> int:
        return a + b

    with caplog.at_level(logging.INFO):
        result = add(2, 3)

    assert result == 5
    assert add.__name__ == "add"
    assert "add: " in caplog.text
    assert caplog.text.rstrip().endswith("мс")


def test_timed_logs_even_when_function_raises(caplog):
    @timed
    def fail():
        raise RuntimeError("збій")

    with caplog.at_level(logging.INFO), pytest.raises(RuntimeError, match="збій"):
        fail()

    assert "fail: " in caplog.text
