import unittest
from datetime import datetime, time, timedelta

from alarmclock.alarm import Alarm, describe_days, next_at, parse_clock, parse_days, parse_offset

GRACE = timedelta(minutes=5)


def repeating(clock, days, created="2026-09-21T12:00:00"):
    return Alarm(id=1, time=clock, created=created, days=days)


class ParseTests(unittest.TestCase):
    def test_clock_formats(self):
        self.assertEqual(parse_clock("07:30"), time(7, 30))
        self.assertEqual(parse_clock("7:30pm"), time(19, 30))
        self.assertEqual(parse_clock("6 PM"), time(18, 0))
        self.assertEqual(parse_clock("12am"), time(0, 0))
        self.assertEqual(parse_clock("12pm"), time(12, 0))

    def test_clock_rejects_garbage(self):
        for bad in ["7", "25:00", "07:61", "13pm", "noon", ""]:
            with self.assertRaises(ValueError, msg=bad):
                parse_clock(bad)

    def test_offset(self):
        self.assertEqual(parse_offset("+10m"), timedelta(minutes=10))
        self.assertEqual(parse_offset("+1h30m"), timedelta(hours=1, minutes=30))
        self.assertIsNone(parse_offset("07:30"))
        self.assertIsNone(parse_offset("+"))

    def test_days(self):
        self.assertEqual(parse_days("weekdays"), [0, 1, 2, 3, 4])
        self.assertEqual(parse_days("fri,Mon, wednesday"), [0, 2, 4])
        with self.assertRaises(ValueError):
            parse_days("mon,funday")
        self.assertEqual(describe_days([5, 6]), "weekends")
        self.assertEqual(describe_days([0, 2]), "mon,wed")
        self.assertEqual(describe_days(None), "once")


class ScheduleTests(unittest.TestCase):
    def test_next_at_rolls_to_tomorrow(self):
        now = datetime(2026, 9, 24, 8, 0)
        self.assertEqual(next_at(time(9, 0), now), datetime(2026, 9, 24, 9, 0))
        self.assertEqual(next_at(time(8, 0), now), datetime(2026, 9, 25, 8, 0))

    def test_weekday_alarm_skips_weekend(self):
        alarm = repeating("07:00", [0, 1, 2, 3, 4], created="2026-09-25T08:00:00")
        self.assertEqual(alarm.next_fire(), datetime(2026, 9, 28, 7, 0))

    def test_dismiss_moves_repeating_alarm_forward(self):
        alarm = repeating("07:00", [0, 1, 2, 3, 4, 5, 6])
        self.assertEqual(alarm.next_fire(), datetime(2026, 9, 22, 7, 0))
        alarm.dismiss(datetime(2026, 9, 22, 7, 0, 20))
        self.assertEqual(alarm.next_fire(), datetime(2026, 9, 23, 7, 0))
        self.assertTrue(alarm.enabled)

    def test_one_shot_turns_off_after_dismiss(self):
        alarm = Alarm(id=1, time="07:00", created="2026-09-21T12:00:00", at="2026-09-22T07:00:00")
        alarm.dismiss(datetime(2026, 9, 22, 7, 1))
        self.assertFalse(alarm.enabled)
        self.assertEqual(alarm.state(datetime(2026, 9, 22, 7, 2), GRACE), "off")

    def test_snooze_overrides_schedule(self):
        alarm = repeating("07:00", [0, 1, 2, 3, 4, 5, 6])
        alarm.snooze(datetime(2026, 9, 22, 7, 0), 5)
        self.assertEqual(alarm.state(datetime(2026, 9, 22, 7, 3), GRACE), "waiting")
        self.assertEqual(alarm.state(datetime(2026, 9, 22, 7, 5), GRACE), "due")
        alarm.dismiss(datetime(2026, 9, 22, 7, 5))
        self.assertEqual(alarm.next_fire(), datetime(2026, 9, 23, 7, 0))

    def test_states(self):
        alarm = Alarm(id=1, time="07:00", created="2026-09-21T12:00:00", at="2026-09-22T07:00:00")
        self.assertEqual(alarm.state(datetime(2026, 9, 22, 6, 59), GRACE), "waiting")
        self.assertEqual(alarm.state(datetime(2026, 9, 22, 7, 4), GRACE), "due")
        self.assertEqual(alarm.state(datetime(2026, 9, 22, 7, 6), GRACE), "missed")


if __name__ == "__main__":
    unittest.main()
