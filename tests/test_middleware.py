"""Timing, CSP, and storage failure middleware."""

import logging

from django.db import OperationalError
from django.http import HttpResponse
from django.test import RequestFactory, override_settings
from pytest_django.asserts import assertContains

from config.middleware import StorageErrorMiddleware, TimingMiddleware


def test_timing_header_and_slow_warning(caplog):
    request = RequestFactory().get("/probe/")
    middleware = TimingMiddleware(lambda request: HttpResponse("ok"))
    with override_settings(SLOW_REQUEST_MS=-1), caplog.at_level(logging.WARNING):
        response = middleware(request)
    assert response.status_code == 200
    assert response["Server-Timing"].startswith("app;dur=")
    assert "Повільний запит /probe/" in caplog.text


def test_security_headers_on_success(client, db_group):
    response = client.get("/students/")
    assert response["Content-Security-Policy"] == (
        "default-src 'self'; img-src 'self' data:"
    )
    assert response["X-Frame-Options"] == "DENY"
    assert response["X-Content-Type-Options"] == "nosniff"
    assert response["Referrer-Policy"] == "same-origin"
    assert response["Cross-Origin-Opener-Policy"] == "same-origin"
    assert response["Server-Timing"].startswith("app;dur=")


def test_empty_database_shows_503(client, db):
    assertContains(
        client.get("/students/"), "Сервіс тимчасово недоступний", status_code=503
    )


def test_database_error_shows_503(client, monkeypatch):
    def broken():
        raise OperationalError("database is locked")

    monkeypatch.setattr("students.views.get_group", broken)
    assertContains(
        client.get("/students/"), "Сервіс тимчасово недоступний", status_code=503
    )


def test_unrelated_exception_is_not_consumed():
    middleware = StorageErrorMiddleware(lambda request: HttpResponse())
    assert middleware.process_exception(RequestFactory().get("/"), ValueError()) is None
