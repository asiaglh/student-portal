"""Консольний інтерфейс: лише введення, виведення й виклики моделі."""

from collections.abc import Iterable
from pathlib import Path

from student_portal.exceptions import PortalError, StorageError
from student_portal.grades import ECTS_LETTERS, Grade
from student_portal.group import Group
from student_portal.people import Student
from student_portal.storage import load_group, save_group

DATA_FILE = Path("data/group.json")
MENU = """
1 - список студентів       5 - додати оцінку
2 - рейтинг                6 - видалити студента
3 - пошук за прізвищем     7 - розподіл оцінок ECTS
4 - додати студента        8 - найкращі за дисциплінами (варіант 4)
0 - зберегти і вийти"""


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


def run(group: Group) -> None:
    while True:
        print(MENU)
        choice = input("> ").strip()
        try:
            match choice:
                case "1":
                    print("Список студентів (ID, ПІБ, середній бал):")
                    print_students(group)
                case "2":
                    print("Рейтинг студентів:")
                    print_students(group.ranking())
                case "3":
                    query = input("Фрагмент прізвища: ").strip()
                    print("Результати пошуку:")
                    print_students(group.find(query))
                case "4":
                    first_name = input("Ім’я: ").strip()
                    last_name = input("Прізвище: ").strip()
                    student = Student(group.next_id(), first_name, last_name)
                    group.add(student)
                    print(f"Додано: {student}")
                case "5":
                    student = group.get(int(input("ID студента: ")))
                    course = input("Дисципліна: ").strip()
                    score = int(input("Бали (0–100): "))
                    grade = Grade(course, score)
                    student.add_grade(grade)
                    print(f"{student.full_name}: {grade.score} ({grade.ects})")
                case "6":
                    student = group.remove(int(input("ID студента: ")))
                    print(f"Видалено: {student}")
                case "7":
                    print("Розподіл оцінок ECTS:")
                    distribution = group.ects_distribution()
                    for letter in ECTS_LETTERS:
                        count = distribution.get(letter, 0)
                        print(f"{letter:<2}  {'█' * count} {count}")
                case "8":
                    print("Найкращі студенти з кожної дисципліни (варіант 4):")
                    best = group.best_by_course()
                    if not best:
                        print("Оцінок із дисциплін ще немає.")
                    for course, student in best.items():
                        average = format_average(student.average_for(course))
                        print(f"{course}: {student.full_name} — {average}")
                case "0":
                    return
                case _:
                    print("Невідома команда")
        except ValueError as error:
            print(f"Помилка введення: {error}")
        except PortalError as error:
            print(f"Помилка: {error}")


def main() -> None:
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
