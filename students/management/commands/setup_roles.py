"""Create reproducible student-portal roles."""

from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand

ROLES = {
    "Викладачі": ["view_student", "view_grade", "add_grade"],
    "Деканат": ["view_student", "add_student", "change_student", "delete_student"],
}


class Command(BaseCommand):
    help = "Створює групи «Викладачі» і «Деканат» з правами застосунку students"

    def handle(self, *args, **options):
        for name, codenames in ROLES.items():
            role, _ = Group.objects.get_or_create(name=name)
            role.permissions.set(
                Permission.objects.filter(
                    content_type__app_label="students", codename__in=codenames
                )
            )
            self.stdout.write(f"{name}: {', '.join(sorted(codenames))}")
        self.stdout.write(self.style.SUCCESS("Ролі налаштовано"))
