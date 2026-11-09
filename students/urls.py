"""Маршрути сторінок студентів."""

from django.urls import path

from . import views

app_name = "students"

urlpatterns = [
    path("", views.ranking, name="ranking"),
    path("debtors/", views.debtors, name="debtors"),
]
