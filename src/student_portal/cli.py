"""Консольне меню на основі реєстру команд."""

import asyncio
import logging
import os
from collections.abc import Callable, Iterable
from pathlib import Path

from student_portal.decorators import timed
from student_portal.exceptions import PortalError, StorageError
from student_portal.grades import ECTS_LETTERS, Grade
from student_portal.group import Group
from student_portal.journal import import_journal
from student_portal.notify import notify_all
from student_portal.people import Student
from student_portal.storage import load_group, save_group

DATA_FILE = Path("data/group.json")
type Handler = Callable[[Group], None]
COMMANDS: dict[str, tuple[str, Handler]] = {}


def command(key: str, title: str) -> Callable[[Handler], Handler]:
    """Реєструє функцію, захоплюючи ключ і назву у замиканні."""

    def register(handler: Handler) -> Handler:
        if key in COMMANDS or key == "0":
            raise ValueError(f"пункт меню {key} уже зайнято")
        COMMANDS[key] = (title, handler)
        return handler

    return register


def menu() -> str:
    items = [f"{key:>2} - {title}" for key, (title, _) in COMMANDS.items()]
    return "\n" + "\n".join([*items, " 0 - зберегти і вийти"])


def format_average(value: float | None) -> str:
    return "-" if value is None else f"{value:.1f}"


def print_students(students: Iterable[Student]) -> None:
    found = False
    for student in students:
        found = True
        print(
            f"{student.id:>3}  {student.full_name:<30}"
            f"{format_average(student.average()):>6}"
        )
    if not found:
        print("Студентів не знайдено.")


@command("1", "список студентів")
def list_students(group: Group) -> None:
    print("Список студентів (ID, ПІБ, середній бал):")
    print_students(group)


@command("2", "рейтинг")
def show_ranking(group: Group) -> None:
    print("Рейтинг студентів:")
    print_students(group.ranking())


@command("3", "пошук за прізвищем")
def find_students(group: Group) -> None:
    query = input("Фрагмент прізвища: ").strip()
    print("Результати пошуку:")
    print_students(group.find(query))


@command("4", "додати студента")
def add_student(group: Group) -> None:
    first_name = input("Ім’я: ").strip()
    last_name = input("Прізвище: ").strip()
    student = Student(group.next_id(), first_name, last_name)
    group.add(student)
    print(f"Додано: {student}")


@command("5", "додати оцінку")
def add_grade(group: Group) -> None:
    student = group.get(int(input("ID студента: ")))
    course = input("Дисципліна: ").strip()
    score = int(input("Бали (0–100): "))
    grade = Grade(course, score)
    student.add_grade(grade)
    print(f"{student.full_name}: {grade.score} ({grade.ects})")


@command("6", "видалити студента")
def remove_student(group: Group) -> None:
    student = group.remove(int(input("ID студента: ")))
    print(f"Видалено: {student}")


@command("7", "розподіл оцінок ECTS")
def show_ects(group: Group) -> None:
    print("Розподіл оцінок ECTS:")
    distribution = group.ects_distribution()
    for letter in ECTS_LETTERS:
        count = distribution.get(letter, 0)
        print(f"{letter:<2}  {'█' * count} {count}")


@command("8", "найкращі за дисциплінами (варіант 4 ЛР2)")
def show_best(group: Group) -> None:
    print("Найкращі студенти з кожної дисципліни (варіант 4):")
    best = group.best_by_course()
    if not best:
        print("Оцінок із дисциплін ще немає.")
    for course, student in best.items():
        average = format_average(student.average_for(course))
        print(f"{course}: {student.full_name} — {average}")


@command("9", "імпортувати журнал CSV")
def import_grades(group: Group) -> None:
    path = Path(input("Шлях до журналу CSV: ").strip())
    count = import_journal(group, path)
    print(f"Імпортовано оцінок: {count}")


@command("10", "розіслати результати (імітація)")
@timed
def notify_students(group: Group) -> None:
    for message in asyncio.run(notify_all(group)):
        print(f"Надіслано: {message}")


def run(group: Group) -> None:
    while True:
        print(menu())
        choice = input("> ").strip()
        if choice == "0":
            return
        if choice not in COMMANDS:
            print("Невідома команда")
            continue
        _, handler = COMMANDS[choice]
        try:
            handler(group)
        except ValueError as error:
            print(f"Помилка введення: {error}")
        except PortalError as error:
            print(f"Помилка: {error}")


def main() -> None:
    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "WARNING").upper(),
        format="%(levelname)s %(name)s: %(message)s",
    )
    if DATA_FILE.exists():
        try:
            group = load_group(DATA_FILE)
        except StorageError as error:
            raise SystemExit(f"Не вдалося завантажити дані: {error}") from error
    else:
        group = Group(input("Назва нової групи: ").strip() or "КН-11")
    print(
        f"Група {group.name}: студентів — {len(group)}, "
        f"середній бал — {format_average(group.average())}"
    )
    try:
        run(group)
    except EOFError, KeyboardInterrupt:
        print("\nЗавершення сеансу.")
    try:
        save_group(group, DATA_FILE)
    except StorageError as error:
        raise SystemExit(f"Не вдалося зберегти дані: {error}") from error
    print(f"Дані збережено у {DATA_FILE}")
