"""REST API for students and append-only grades."""

from statistics import fmean

from rest_framework import mixins, serializers, viewsets

from student_portal.grades import ects_grade

from . import models


class GradeSerializer(serializers.ModelSerializer):
    ects = serializers.SerializerMethodField()

    class Meta:
        model = models.Grade
        fields = ["id", "student", "course", "score", "graded_on", "ects"]

    def get_ects(self, grade: models.Grade) -> str:
        return ects_grade(grade.score)


class StudentSerializer(serializers.ModelSerializer):
    average = serializers.SerializerMethodField()
    grades = GradeSerializer(many=True, read_only=True)

    class Meta:
        model = models.Student
        fields = ["id", "first_name", "last_name", "group", "average", "grades"]

    def get_average(self, student: models.Student) -> float | None:
        scores = [grade.score for grade in student.grades.all()]
        return fmean(scores) if scores else None


class StudentViewSet(viewsets.ModelViewSet):
    serializer_class = StudentSerializer

    def get_queryset(self):
        return models.Student.objects.prefetch_related("grades").order_by("id")


class GradeViewSet(
    mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet
):
    serializer_class = GradeSerializer
    queryset = models.Grade.objects.order_by("id")
