"""Винятки системи управління студентами."""


class PortalError(Exception):
    """Базовий виняток застосунку."""


class InvalidGradeError(PortalError, ValueError):
    """Оцінка має неправильний тип або поза допустимим діапазоном."""


class DuplicateStudentError(PortalError, ValueError):
    """Студент з таким ідентифікатором уже є в групі."""


class StudentNotFoundError(PortalError, LookupError):
    """Студента з таким ідентифікатором немає в групі."""


class StorageError(PortalError):
    """Помилка читання або запису файлу даних."""


class JournalFormatError(PortalError, ValueError):
    """Рядок журналу оцінок має неправильний формат."""
