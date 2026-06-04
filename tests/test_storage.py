import os
import tempfile
import unittest
from pathlib import Path

from alarmclock.models import Alarm
from alarmclock import storage


class TestStorage(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["ALARMCLOCK_HOME"] = self.tmp.name

    def tearDown(self):
        os.environ.pop("ALARMCLOCK_HOME", None)
        self.tmp.cleanup()

    def test_load_empty_when_missing(self):
        self.assertEqual(storage.load_alarms(), [])

    def test_save_and_load_round_trip(self):
        alarms = [
            Alarm(time="06:30", label="Run", repeat=["mon", "wed", "fri"]),
            Alarm(time="22:00", label="Sleep"),
        ]
        storage.save_alarms(alarms)
        loaded = storage.load_alarms()
        self.assertEqual(len(loaded), 2)
        by_id = {a.id: a.to_dict() for a in loaded}
        for original in alarms:
            self.assertEqual(by_id[original.id], original.to_dict())

    def test_corrupt_file_starts_empty(self):
        path = storage.store_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text("{ not json", encoding="utf-8")
        self.assertEqual(storage.load_alarms(), [])

    def test_find_alarm(self):
        a = Alarm(time="06:30")
        self.assertIs(storage.find_alarm([a], a.id), a)
        self.assertIsNone(storage.find_alarm([a], "nope"))


if __name__ == "__main__":
    unittest.main()
