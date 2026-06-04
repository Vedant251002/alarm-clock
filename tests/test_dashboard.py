import unittest
from datetime import datetime

from alarmclock import bigclock
from alarmclock.dashboard import _fmt_countdown, _next_alarm
from alarmclock.models import Alarm


class TestNextFireTime(unittest.TestCase):
    def test_one_time_later_today(self):
        a = Alarm(time="23:30")
        now = datetime(2026, 6, 4, 8, 0, 0)
        self.assertEqual(a.next_fire_time(now), datetime(2026, 6, 4, 23, 30))

    def test_one_time_already_passed_rolls_to_tomorrow(self):
        a = Alarm(time="06:00")
        now = datetime(2026, 6, 4, 8, 0, 0)
        self.assertEqual(a.next_fire_time(now), datetime(2026, 6, 5, 6, 0))

    def test_recurring_picks_nearest_weekday(self):
        # 2026-06-04 is Thursday.
        a = Alarm(time="09:00", repeat=["mon", "fri"])
        now = datetime(2026, 6, 4, 8, 0, 0)
        # Next Friday is 2026-06-05.
        self.assertEqual(a.next_fire_time(now), datetime(2026, 6, 5, 9, 0))

    def test_disabled_returns_none(self):
        a = Alarm(time="09:00", enabled=False)
        self.assertIsNone(a.next_fire_time(datetime(2026, 6, 4, 8, 0)))


class TestHelpers(unittest.TestCase):
    def test_next_alarm_selects_soonest(self):
        now = datetime(2026, 6, 4, 8, 0, 0)
        a1 = Alarm(time="09:00")
        a2 = Alarm(time="08:30")
        nxt, t = _next_alarm([a1, a2], now)
        self.assertEqual(nxt.id, a2.id)
        self.assertEqual(t, datetime(2026, 6, 4, 8, 30))

    def test_next_alarm_empty(self):
        nxt, t = _next_alarm([], datetime(2026, 6, 4, 8, 0))
        self.assertIsNone(nxt)
        self.assertIsNone(t)

    def test_fmt_countdown(self):
        from datetime import timedelta
        self.assertEqual(_fmt_countdown(timedelta(seconds=45)), "45s")
        self.assertEqual(_fmt_countdown(timedelta(minutes=3, seconds=5)), "3m 05s")
        self.assertEqual(_fmt_countdown(timedelta(hours=2, minutes=1, seconds=9)), "2h 01m 09s")

    def test_bigclock_render_shape(self):
        rows = bigclock.render("12:34")
        self.assertEqual(len(rows), bigclock.HEIGHT)
        self.assertTrue(all(len(r) == len(rows[0]) for r in rows))


if __name__ == "__main__":
    unittest.main()
