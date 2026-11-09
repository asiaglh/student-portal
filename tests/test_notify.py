"""AsyncMock, порядок результатів і фактичний ліміт одночасності."""

import asyncio

import pytest

from student_portal import notify
from student_portal.notify import notify_all


@pytest.fixture(autouse=True)
def no_delay(monkeypatch):
    monkeypatch.setattr(notify, "SEND_DELAY", 0)


@pytest.mark.parametrize(
    "student_id, expected",
    [(1, "Коваль Олена: середній бал 91.5"), (3, "Бойко Ірина: оцінок немає")],
    ids=["graded", "ungraded"],
)
def test_send_result_formats_message(group, student_id, expected):
    assert asyncio.run(notify.send_result(group.get(student_id))) == expected


def test_sequential_notifications_preserve_order(group):
    messages = asyncio.run(notify.notify_sequentially(group))

    assert [m.split(":")[0] for m in messages] == [s.full_name for s in group]


@pytest.mark.parametrize("limit", [1, 2, 3])
def test_notify_all_respects_limit_and_order(mocker, group, limit):
    active = 0
    peak = 0

    async def fake_send(student):
        nonlocal active, peak
        active += 1
        peak = max(peak, active)
        await asyncio.sleep(0)
        active -= 1
        return student.last_name

    send = mocker.patch("student_portal.notify.send_result", side_effect=fake_send)

    messages = asyncio.run(notify_all(group, limit=limit))

    assert messages == ["Коваль", "Мельник", "Бойко"]
    assert peak == limit
    assert send.await_count == 3


@pytest.mark.parametrize("limit", [0, -1], ids=["zero", "negative"])
def test_notify_rejects_nonpositive_limit(group, limit):
    with pytest.raises(ValueError, match="додатним"):
        asyncio.run(notify_all(group, limit))


def test_notify_empty_iterable_returns_no_messages():
    assert asyncio.run(notify_all([])) == []
