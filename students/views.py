"""HTML and JSON views for students in the database-backed group."""

from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    ListView,
    TemplateView,
    UpdateView,
)

from student_portal.grades import ects_grade
from student_portal.people import Student

from . import models
from .forms import GradeForm
from .services import get_group, get_student_or_404


@permission_required("students.add_grade", raise_exception=True)
def add_grade(request: HttpRequest, student_id: int) -> HttpResponse:
    student = get_object_or_404(models.Student, pk=student_id)
    form = GradeForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        grade = form.save(commit=False)
        grade.student = student
        grade.save()
        messages.success(request, f"Оцінку {grade.score} з {grade.course} збережено")
        return redirect("students:detail", student_id=student_id)
    return render(
        request, "students/grade_form.html", {"student": student, "form": form}
    )


class StudentCreateView(PermissionRequiredMixin, CreateView):
    model = models.Student
    fields = ["first_name", "last_name", "group"]
    permission_required = "students.add_student"
    template_name = "students/student_form.html"
    success_url = reverse_lazy("students:list")


class StudentUpdateView(PermissionRequiredMixin, UpdateView):
    model = models.Student
    fields = ["first_name", "last_name", "group"]
    permission_required = "students.change_student"
    pk_url_kwarg = "student_id"
    template_name = "students/student_form.html"

    def get_success_url(self) -> str:
        return str(reverse_lazy("students:detail", args=[self.object.pk]))


class StudentDeleteView(PermissionRequiredMixin, DeleteView):
    """Variant 4: only the dean's office may confirm a student deletion."""

    model = models.Student
    permission_required = "students.delete_student"
    pk_url_kwarg = "student_id"
    template_name = "students/student_confirm_delete.html"
    success_url = reverse_lazy("students:list")


def student_list(request: HttpRequest) -> HttpResponse:
    """Show students in group order, optionally filtering by surname."""
    group = get_group()
    query = request.GET.get("q", "").strip()
    students = group.find(query) if query else list(group)
    return render(
        request,
        "students/student_list.html",
        {"group": group, "students": students, "query": query},
    )


def student_detail(request: HttpRequest, student_id: int) -> HttpResponse:
    """Display one student's grades or raise a meaningful 404."""
    student = get_student_or_404(get_group(), student_id)
    return render(request, "students/student_detail.html", {"student": student})


def student_json(request: HttpRequest, student_id: int) -> JsonResponse:
    """Provide the same student's summary as readable UTF-8 JSON."""
    student = get_student_or_404(get_group(), student_id)
    return JsonResponse(
        {
            "id": student.id,
            "full_name": student.full_name,
            "average": student.average(),
        },
        json_dumps_params={"ensure_ascii": False},
    )


class RankingView(TemplateView):
    """Display the group ranking with one shared base template."""

    template_name = "students/ranking.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        context = super().get_context_data(**kwargs)
        group = get_group()
        context["group"] = group
        context["ranking"] = group.ranking()
        return context


class StudentListView(ListView):
    """Show students two at a time using Django's built-in paginator."""

    template_name = "students/student_pages.html"
    context_object_name = "students"
    paginate_by = 2

    def get_queryset(self) -> list[Student]:
        return get_group().ranking()


def debtors(request: HttpRequest) -> HttpResponse:
    """Варіант 4: показати студентів і дисципліни з оцінкою Fx."""
    group = get_group()
    rows = []
    for student in group:
        courses = sorted(
            {grade.course for grade in student.grades if grade.ects == "Fx"}
        )
        if courses:
            rows.append({"student": student, "courses": courses})
    return render(request, "students/debtors.html", {"group": group, "debtors": rows})


def by_ects(request: HttpRequest, letter: str) -> HttpResponse:
    """List students whose average corresponds to an ECTS letter."""
    group = get_group()
    students = [
        student
        for student in group
        if (average := student.average()) is not None
        and ects_grade(int(average)) == letter
    ]
    return render(
        request, "students/by_ects.html", {"letter": letter, "students": students}
    )


def legacy_student(request: HttpRequest, student_id: str) -> HttpResponse:
    """Redirect four-digit old IDs to the canonical student detail URL."""
    return redirect("students:detail", student_id=int(student_id), permanent=True)
