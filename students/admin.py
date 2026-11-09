# Register your models here.
"""Administrative editing for students and grades, including ECTS filtering."""

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from .models import Grade, Group, Student


class GradeInline(admin.TabularInline):
    model = Grade
    extra = 0


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ["last_name", "first_name", "group"]
    list_filter = ["group"]
    search_fields = ["last_name", "first_name"]
    ordering = ["last_name", "first_name"]
    inlines = [GradeInline]


class EctsFilter(admin.SimpleListFilter):
    title = "ECTS"
    parameter_name = "ects"

    def lookups(self, request: HttpRequest, model_admin: admin.ModelAdmin):
        return [(letter, letter) for letter in ("A", "B", "C", "D", "E", "Fx")]

    def queryset(self, request: HttpRequest, queryset: QuerySet[Grade]):
        bounds = {
            "A": (90, 100),
            "B": (82, 89),
            "C": (75, 81),
            "D": (67, 74),
            "E": (60, 66),
            "Fx": (0, 59),
        }
        if (span := bounds.get(self.value())) is None:
            return queryset
        return queryset.filter(score__gte=span[0], score__lte=span[1])


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ["student", "course", "score", "graded_on"]
    search_fields = ["student__last_name"]
    list_filter = [EctsFilter]


admin.site.register(Group)
