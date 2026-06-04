import unittest
from datetime import datetime

from alarmclock.models import Alarm, parse_repeat, parse_time


class TestParsing(unittest.TestCase):
    def test_parse_time_valid(self):
        self.assertEqual(parse_time("7:05"), "07:05")
        self.assertEqual(parse_time(" 23:59 "), "23:59")

    def test_parse_time_invalid(self):
        for bad in ["25:00", "07:60", "abc", "7", "07-30"]:
            with self.assertRaises(ValueError):
                parse_time(bad)

    def test_parse_repeat(self):
        self.assertEqual(parse_repeat(None), [])
        self.assertEqual(parse_repeat(""), [])
        self.assertEqual(parse_repeat("tue,mon,mon"), ["mon", "tue"])
        self.assertEqual(parse_repeat("Monday,FRI"), ["mon", "fri"])

    def test_parse_repeat_invalid(self):
        with self.assertRaises(ValueError):
            parse_repeat("funday")


class TestAlarm(unittest.TestCase):
    def test_round_trip(self):
        a = Alarm(time="08:00", label="Gym", repeat=["mon", "wed"])
        b = Alarm.from_dict(a.to_dict())
        self.assertEqual(a.to_dict(), b.to_dict())

    def test_is_due_one_time(self):
        a = Alarm(time="08:00")
        self.assertTrue(a.is_due(datetime(2026, 6, 4, 8, 0)))
        self.assertFalse(a.is_due(datetime(2026, 6, 4, 8, 1)))

    def test_is_due_recurring(self):
        # 2026-06-04 is a Thursday.
        a = Alarm(time="08:00", repeat=["thu"])
        self.assertTrue(a.is_due(datetime(2026, 6, 4, 8, 0)))
        a2 = Alarm(time="08:00", repeat=["fri"])
        self.assertFalse(a2.is_due(datetime(2026, 6, 4, 8, 0)))

    def test_is_due_disabled(self):
        a = Alarm(time="08:00", enabled=False)
        self.assertFalse(a.is_due(datetime(2026, 6, 4, 8, 0)))

    def test_repeat_label(self):
        self.assertEqual(Alarm(time="08:00").repeat_label(), "once")
        self.assertEqual(
            Alarm(time="08:00", repeat=["mon", "tue", "wed", "thu", "fri"]).repeat_label(),
            "weekdays",
        )


if __name__ == "__main__":
    unittest.main()
