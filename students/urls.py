"""Маршрути сторінок студентів."""

from django.urls import path

from . import views

app_name = "students"

urlpatterns = [
    path("", views.student_list, name="list"),
    path("ranking/", views.RankingView.as_view(), name="ranking"),
    path("pages/", views.StudentListView.as_view(), name="pages"),
    path("debtors/", views.debtors, name="debtors"),
    path("<int:student_id>/", views.student_detail, name="detail"),
    path("<int:student_id>.json", views.student_json, name="detail-json"),
]
