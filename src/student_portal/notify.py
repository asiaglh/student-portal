"""Асинхронна імітація розсилки результатів студентам."""

import asyncio
from collections.abc import Iterable

from student_portal.people import Student

SEND_DELAY = 0.5
MAX_CONCURRENT = 3


async def send_result(student: Student) -> str:
    """Імітує поштовий сервер; справжніх листів не надсилає."""
    await asyncio.sleep(SEND_DELAY)
    average = student.average()
    if average is None:
        return f"{student.full_name}: оцінок немає"
    return f"{student.full_name}: середній бал {average:.1f}"


async def notify_sequentially(students: Iterable[Student]) -> list[str]:
    """Послідовно надсилає результати у порядку студентів."""
    return [await send_result(student) for student in students]


async def notify_all(
    students: Iterable[Student], limit: int = MAX_CONCURRENT
) -> list[str]:
    """Запускає завдання з обмеженням одночасності, зберігаючи порядок."""
    if limit < 1:
        raise ValueError("ліміт одночасності має бути додатним")
    semaphore = asyncio.Semaphore(limit)

    async def send(student: Student) -> str:
        async with semaphore:
            return await send_result(student)

    async with asyncio.TaskGroup() as tasks:
        pending = [tasks.create_task(send(student)) for student in students]
    return [task.result() for task in pending]
