import re
from dataclasses import dataclass
from datetime import datetime, time, timedelta

DAY_NAMES = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
PRESETS = {
    "daily": [0, 1, 2, 3, 4, 5, 6],
    "weekdays": [0, 1, 2, 3, 4],
    "weekends": [5, 6],
}


def parse_clock(text):
    text = text.strip().lower().replace(" ", "")
    m = re.fullmatch(r"(\d{1,2})(?::(\d{2}))?(am|pm)?", text)
    if not m or (m.group(2) is None and m.group(3) is None):
        raise ValueError(f"can't read time '{text}', try 07:30 or 7:30am")
    hour, minute, suffix = int(m.group(1)), int(m.group(2) or 0), m.group(3)
    if suffix:
        if not 1 <= hour <= 12:
            raise ValueError(f"bad hour in '{text}'")
        hour = hour % 12 + (12 if suffix == "pm" else 0)
    if hour > 23 or minute > 59:
        raise ValueError(f"'{text}' is not a valid time")
    return time(hour, minute)


def parse_offset(text):
    m = re.fullmatch(r"\+(?:(\d+)h)?(?:(\d+)m)?", text.strip().lower())
    if not m or not any(m.groups()):
        return None
    return timedelta(hours=int(m.group(1) or 0), minutes=int(m.group(2) or 0))


def parse_days(text):
    text = text.strip().lower()
    if text in PRESETS:
        return list(PRESETS[text])
    days = set()
    for part in text.split(","):
        short = part.strip()[:3]
        if short not in DAY_NAMES:
            raise ValueError(f"unknown day '{part.strip()}', use mon..sun, daily, weekdays or weekends")
        days.add(DAY_NAMES.index(short))
    return sorted(days)


def describe_days(days):
    if days is None:
        return "once"
    for name, preset in PRESETS.items():
        if days == preset:
            return name
    return ",".join(DAY_NAMES[d] for d in days)


def next_at(clock, now):
    candidate = datetime.combine(now.date(), clock)
    if candidate <= now:
        candidate += timedelta(days=1)
    return candidate


@dataclass
class Alarm:
    id: int
    time: str
    created: str
    label: str = ""
    days: list | None = None
    at: str | None = None
    last_fired: str | None = None
    snoozed_until: str | None = None
    enabled: bool = True

    def next_fire(self):
        if self.snoozed_until:
            return datetime.fromisoformat(self.snoozed_until)
        if self.days is None:
            return datetime.fromisoformat(self.at)
        after = datetime.fromisoformat(self.last_fired or self.created)
        clock = time.fromisoformat(self.time)
        for i in range(8):
            candidate = datetime.combine(after.date() + timedelta(days=i), clock)
            if candidate > after and candidate.weekday() in self.days:
                return candidate
        raise ValueError(f"alarm {self.id} has no valid days")

    def snooze(self, now, minutes):
        self.snoozed_until = (now + timedelta(minutes=minutes)).isoformat(timespec="seconds")

    def dismiss(self, now):
        self.snoozed_until = None
        if self.days is None:
            self.enabled = False
        else:
            self.last_fired = now.isoformat(timespec="seconds")

    def state(self, now, grace):
        if not self.enabled:
            return "off"
        fire = self.next_fire()
        if fire > now:
            return "waiting"
        if now - fire > grace:
            return "missed"
        return "due"
