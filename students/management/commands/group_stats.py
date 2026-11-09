"""Статистика групи для manage.py."""

from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser

from student_portal.exceptions import StorageError
from student_portal.storage import load_group


class Command(BaseCommand):
    help = "Показати кількість студентів і розподіл оцінок ECTS у JSON-файлі"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("path", type=Path, help="Шлях до JSON-файлу групи")

    def handle(self, *args: Any, **options: Any) -> None:
        try:
            group = load_group(options["path"])
        except StorageError as error:
            raise CommandError(str(error)) from error

        self.stdout.write(f"Група {group.name}: {len(group)} студентів")
        self.stdout.write("Розподіл оцінок за шкалою ECTS:")
        for letter, count in group.ects_distribution().items():
            self.stdout.write(f"  {letter}: {count}")
        self.stdout.write(self.style.SUCCESS("Готово"))
