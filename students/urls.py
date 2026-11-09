"""Маршрути сторінок студентів."""

from django.urls import path, re_path, register_converter

from . import converters, views

register_converter(converters.EctsConverter, "ects")

app_name = "students"

urlpatterns = [
    path("", views.student_list, name="list"),
    path("ranking/", views.RankingView.as_view(), name="ranking"),
    path("pages/", views.StudentListView.as_view(), name="pages"),
    path("debtors/", views.debtors, name="debtors"),
    path("ects/<ects:letter>/", views.by_ects, name="by-ects"),
    path("<int:student_id>/", views.student_detail, name="detail"),
    path("<int:student_id>.json", views.student_json, name="detail-json"),
    re_path(r"^st/(?P<student_id>[0-9]{4})/$", views.legacy_student),
]
