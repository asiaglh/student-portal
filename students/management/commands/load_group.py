"""Import a JSON group into the Django database."""

from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser

from student_portal.exceptions import StorageError
from student_portal.storage import load_group
from students.services import store_group


class Command(BaseCommand):
    help = "Завантажити групу з JSON-файлу до бази даних"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("path", type=Path, help="Шлях до JSON-файлу групи")

    def handle(self, *args: Any, **options: Any) -> None:
        try:
            group = load_group(options["path"])
            students, grades = store_group(group)
        except StorageError as error:
            raise CommandError(str(error)) from error
        self.stdout.write(
            self.style.SUCCESS(
                f"Група {group.name}: студентів - {students}, оцінок - {grades}"
            )
        )
