import tempfile
import unittest
from pathlib import Path

from alarmclock.alarm import Alarm
from alarmclock.store import Store


def make(label=""):
    return Alarm(id=0, time="07:00", created="2026-09-21T12:00:00", at="2026-09-22T07:00:00", label=label)


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.store = Store(Path(self.dir.name) / "alarms.json")

    def tearDown(self):
        self.dir.cleanup()

    def test_empty_when_missing(self):
        self.assertEqual(self.store.load(), [])

    def test_add_assigns_ids_and_round_trips(self):
        self.store.add(make("a"))
        self.store.add(make("b"))
        loaded = self.store.load()
        self.assertEqual([(a.id, a.label) for a in loaded], [(1, "a"), (2, "b")])

    def test_update_keeps_alarms_added_meanwhile(self):
        first = self.store.add(make("first"))
        self.store.add(make("added from another terminal"))
        first.enabled = False
        self.store.update(first)
        loaded = self.store.load()
        self.assertEqual(len(loaded), 2)
        self.assertFalse(loaded[0].enabled)

    def test_remove(self):
        alarm = self.store.add(make())
        self.assertTrue(self.store.remove(alarm.id))
        self.assertFalse(self.store.remove(alarm.id))

    def test_corrupt_file(self):
        self.store.path.write_text("{not json")
        with self.assertRaises(RuntimeError):
            self.store.load()


if __name__ == "__main__":
    unittest.main()
