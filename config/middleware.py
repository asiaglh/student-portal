"""Request timing and friendly storage-failure responses."""

import logging
from time import perf_counter

from django.conf import settings
from django.db import DatabaseError
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils.deprecation import MiddlewareMixin

from student_portal.exceptions import StorageError

logger = logging.getLogger(__name__)


class TimingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        started = perf_counter()
        response = self.get_response(request)
        elapsed_ms = (perf_counter() - started) * 1000
        response["Server-Timing"] = f"app;dur={elapsed_ms:.1f}"
        if elapsed_ms > settings.SLOW_REQUEST_MS:
            logger.warning("Повільний запит %s: %.1f мс", request.path, elapsed_ms)
        return response


class StorageErrorMiddleware(MiddlewareMixin):
    def process_exception(
        self, request: HttpRequest, exception: Exception
    ) -> HttpResponse | None:
        if isinstance(exception, StorageError | DatabaseError):
            logger.error("Сховище недоступне: %s", exception)
            return render(request, "503.html", status=503)
        return None
