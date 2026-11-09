"""Завантаження групи з сервера деканату."""

import json
from urllib.error import URLError
from urllib.request import urlopen

from student_portal.exceptions import StorageError
from student_portal.group import Group
from student_portal.storage import group_from_dict


def fetch_group(url: str, timeout: float = 5.0) -> Group:
    """Завантажує групу у форматі group.json з адреси url."""
    try:
        with urlopen(url, timeout=timeout) as response:
            return group_from_dict(json.load(response))
    except TimeoutError as error:
        raise StorageError(f"сервер не відповів за {timeout} с") from error
    except URLError as error:
        raise StorageError(f"сервер недоступний: {error.reason}") from error
    except (KeyError, TypeError, ValueError) as error:
        raise StorageError(
            f"сервер повернув дані в неправильному форматі: {error!r}"
        ) from error
