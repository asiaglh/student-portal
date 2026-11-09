"""Сервер деканату: жодного справжнього мережевого запиту."""

import io
import json
from urllib.error import URLError

import pytest

from student_portal.exceptions import StorageError
from student_portal.remote import fetch_group
from student_portal.storage import group_to_dict

URL = "https://dekanat.example.edu/api/groups/kn-11"


@pytest.fixture
def urlopen(mocker):
    """Підміна імені, яке використовує саме remote."""
    return mocker.patch("student_portal.remote.urlopen", autospec=True)


def respond_with(urlopen, payload: bytes) -> None:
    urlopen.return_value.__enter__.return_value = io.BytesIO(payload)


def test_fetch_group_parses_response(urlopen, group):
    respond_with(urlopen, json.dumps(group_to_dict(group)).encode())

    fetched = fetch_group(URL)

    assert fetched == group
    urlopen.assert_called_once_with(URL, timeout=5.0)


def test_custom_timeout_is_forwarded(urlopen, group):
    respond_with(urlopen, json.dumps(group_to_dict(group)).encode())

    fetch_group(URL, timeout=1.5)

    assert urlopen.call_args.kwargs["timeout"] == 1.5


@pytest.mark.parametrize(
    "error, message",
    [
        pytest.param(
            URLError("Connection refused"), "сервер недоступний", id="network"
        ),
        pytest.param(TimeoutError(), "не відповів за 5.0 с", id="timeout"),
    ],
)
def test_network_errors_become_storage_errors(urlopen, error, message):
    urlopen.side_effect = error

    with pytest.raises(StorageError, match=message):
        fetch_group(URL)


@pytest.mark.parametrize(
    "payload",
    [b"<html>502 Bad Gateway</html>", b'{"name":"KN-11"}'],
    ids=["html", "missing-students"],
)
def test_invalid_response_becomes_storage_error(urlopen, payload):
    respond_with(urlopen, payload)

    with pytest.raises(StorageError, match="неправильному форматі"):
        fetch_group(URL)
