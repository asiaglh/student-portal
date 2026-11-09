"""HTML and JSON views for students in the JSON-backed group."""

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.generic import ListView, TemplateView

from student_portal.people import Student

from .services import get_group, get_student_or_404


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
