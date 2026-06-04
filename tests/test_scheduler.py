import unittest
from datetime import datetime

from alarmclock.models import Alarm
from alarmclock.scheduler import Scheduler


class TestScheduler(unittest.TestCase):
    def test_selects_due_alarm(self):
        sched = Scheduler()
        a = Alarm(time="08:00")
        now = datetime(2026, 6, 4, 8, 0, 0)
        self.assertEqual([al.id for al in sched.due_alarms([a], now)], [a.id])

    def test_dedup_within_same_minute(self):
        sched = Scheduler()
        a = Alarm(time="08:00")
        t1 = datetime(2026, 6, 4, 8, 0, 1)
        t2 = datetime(2026, 6, 4, 8, 0, 59)
        self.assertEqual(len(sched.due_alarms([a], t1)), 1)
        self.assertEqual(len(sched.due_alarms([a], t2)), 0)

    def test_fires_again_next_day(self):
        sched = Scheduler()
        a = Alarm(time="08:00", repeat=["thu", "fri"])
        day1 = datetime(2026, 6, 4, 8, 0, 0)   # Thursday
        day2 = datetime(2026, 6, 5, 8, 0, 0)   # Friday
        self.assertEqual(len(sched.due_alarms([a], day1)), 1)
        self.assertEqual(len(sched.due_alarms([a], day2)), 1)

    def test_ignores_not_due(self):
        sched = Scheduler()
        a = Alarm(time="08:00")
        now = datetime(2026, 6, 4, 9, 30, 0)
        self.assertEqual(sched.due_alarms([a], now), [])


if __name__ == "__main__":
    unittest.main()
