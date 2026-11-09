"""Validation order and boundary values for the grade form."""

from datetime import date, timedelta

import pytest

from students.forms import GradeForm

pytestmark = pytest.mark.django_db


def payload(**changes):
    return {"course": " Git ", "score": 74, "graded_on": date.today(), **changes}


def test_valid_data_trims_course():
    form = GradeForm(data=payload())
    assert form.is_valid(), form.errors
    assert form.cleaned_data["course"] == "Git"


@pytest.mark.parametrize("score", [0, 100])
def test_score_boundaries(score):
    assert GradeForm(data=payload(score=score)).is_valid()


@pytest.mark.parametrize("score", [101, -1, "abc"])
def test_invalid_score(score):
    form = GradeForm(data=payload(score=score))
    assert not form.is_valid()
    assert "score" in form.errors


def test_future_date():
    form = GradeForm(data=payload(graded_on=date.today() + timedelta(days=1)))
    assert not form.is_valid()
    assert form.errors["graded_on"] == ["Дата оцінки не може бути в майбутньому"]


@pytest.mark.parametrize("missing", ["course", "score", "graded_on"])
def test_required_fields(missing):
    form = GradeForm(
        data={key: value for key, value in payload().items() if key != missing}
    )
    assert not form.is_valid()
    assert missing in form.errors
