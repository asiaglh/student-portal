"""Validated form for recording a new grade."""

from datetime import date

from django import forms

from . import models


class GradeForm(forms.ModelForm):
    class Meta:
        model = models.Grade
        fields = ["course", "score", "graded_on"]
        widgets = {"graded_on": forms.DateInput(attrs={"type": "date"})}

    def clean_course(self) -> str:
        return self.cleaned_data["course"].strip()

    def clean(self) -> dict[str, object]:
        cleaned_data = super().clean()
        graded_on = cleaned_data.get("graded_on")
        if graded_on and graded_on > date.today():
            self.add_error("graded_on", "Дата оцінки не може бути в майбутньому")
        return cleaned_data
