"""main працює лише з тимчасовим файлом, завантаження — з дублером."""

import pytest

from student_portal import cli
from student_portal.exceptions import StorageError
from student_portal.group import Group
from student_portal.storage import load_group, save_group


@pytest.fixture
def data_file(monkeypatch, tmp_path):
    path = tmp_path / "group.json"
    monkeypatch.setattr(cli, "DATA_FILE", path)
    return path


def test_main_loads_summary_and_persists_changes(group, data_file, answers, capsys):
    save_group(group, data_file)
    answers("4", "Марія", "Шевчук", "0")

    cli.main()

    output = capsys.readouterr().out
    assert "Група КН-11: студентів — 3, середній бал — 76.2" in output
    assert load_group(data_file).get(4).full_name == "Шевчук Марія"


@pytest.mark.parametrize(
    "name, expected", [("Нова", "Нова"), ("", "КН-11")], ids=["named", "default-name"]
)
def test_main_creates_missing_group(data_file, answers, name, expected):
    answers(name, "0")

    cli.main()

    assert load_group(data_file) == Group(expected)


def test_main_exits_on_corrupt_file(data_file):
    data_file.write_text("{", encoding="utf-8")

    with pytest.raises(SystemExit, match="Не вдалося завантажити дані"):
        cli.main()


@pytest.mark.parametrize(
    "reply, replaced", [(" т ", True), ("н", False)], ids=["confirm", "decline"]
)
def test_download_uses_environment_url_and_requires_confirmation(
    group, mocker, monkeypatch, answers, reply, replaced
):
    remote = Group("Серверна")
    fetch = mocker.patch(
        "student_portal.cli.fetch_group", autospec=True, return_value=remote
    )
    monkeypatch.setenv("DEKANAT_URL", "https://example.test/group.json")
    answers(reply)

    cli.download_group(group)

    fetch.assert_called_once_with("https://example.test/group.json")
    assert group.name == ("Серверна" if replaced else "КН-11")


def test_download_uses_default_url(group, mocker, monkeypatch, answers):
    monkeypatch.delenv("DEKANAT_URL", raising=False)
    fetch = mocker.patch(
        "student_portal.cli.fetch_group", autospec=True, return_value=Group("R")
    )
    answers("н")

    cli.download_group(group)

    fetch.assert_called_once_with(cli.DEFAULT_DEKANAT_URL)


def test_menu_continues_after_network_error(group, mocker, answers, capsys):
    mocker.patch(
        "student_portal.cli.fetch_group", side_effect=StorageError("сервер недоступний")
    )
    answers("11", "1", "0")

    cli.run(group)

    output = capsys.readouterr().out
    assert "Помилка: сервер недоступний" in output
    assert "Список студентів" in output


@pytest.mark.parametrize(
    "error", [EOFError(), KeyboardInterrupt()], ids=["eof", "interrupt"]
)
def test_main_saves_after_interrupted_input(group, data_file, mocker, capsys, error):
    save_group(group, data_file)
    mocker.patch("student_portal.cli.run", side_effect=error)

    cli.main()

    assert "Завершення сеансу" in capsys.readouterr().out
    assert load_group(data_file) == group


def test_main_reports_save_failure(data_file, answers, mocker):
    answers("Нова", "0")
    mocker.patch("student_portal.cli.save_group", side_effect=StorageError("диск"))

    with pytest.raises(SystemExit, match="Не вдалося зберегти дані"):
        cli.main()


def test_remaining_menu_commands_use_model(
    group, answers, capsys, tmp_path, monkeypatch
):
    monkeypatch.setattr("student_portal.notify.SEND_DELAY", 0)
    path = tmp_path / "journal.csv"
    path.write_text(
        "student_id;course;score;graded_on\n3;Git;70;2026-10-20\n", encoding="utf-8"
    )
    answers("2", "3", "Коваль", "7", "9", str(path), "10", "6", "2", "0")

    cli.run(group)

    output = capsys.readouterr().out
    assert "Рейтинг студентів" in output and "Результати пошуку" in output
    assert "Імпортовано оцінок: 1" in output and "Надіслано:" in output
    assert "Видалено: Мельник Андрій" in output
    assert len(group) == 2


def test_empty_group_menu_messages(answers, capsys):
    answers("1", "8", "0")

    cli.run(Group("Порожня"))

    output = capsys.readouterr().out
    assert (
        "Студентів не знайдено" in output and "Оцінок із дисциплін ще немає" in output
    )
