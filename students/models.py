# Create your models here.
"""Database records for groups, students, and their grades."""

from django.core.validators import MaxValueValidator
from django.db import models


class Group(models.Model):
    name = models.CharField("назва", max_length=20, unique=True)

    class Meta:
        verbose_name = "група"
        verbose_name_plural = "групи"

    def __str__(self) -> str:
        return self.name


class Student(models.Model):
    group = models.ForeignKey(
        Group, on_delete=models.PROTECT, related_name="students", verbose_name="група"
    )
    first_name = models.CharField("ім’я", max_length=50)
    last_name = models.CharField("прізвище", max_length=50)

    class Meta:
        verbose_name = "студент"
        verbose_name_plural = "студенти"

    def __str__(self) -> str:
        return f"{self.last_name} {self.first_name}"


class Grade(models.Model):
    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name="grades", verbose_name="студент"
    )
    course = models.CharField("дисципліна", max_length=100)
    score = models.PositiveSmallIntegerField(
        "бали", validators=[MaxValueValidator(100)]
    )
    graded_on = models.DateField("дата")

    class Meta:
        verbose_name = "оцінка"
        verbose_name_plural = "оцінки"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(score__lte=100), name="grade_score_at_most_100"
            )
        ]

    def __str__(self) -> str:
        return f"{self.student}: {self.course} {self.score}"
