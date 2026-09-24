import json
import os
from dataclasses import asdict
from pathlib import Path

from .alarm import Alarm


def default_path():
    return Path(os.environ.get("ALARM_FILE", Path.home() / ".alarmclock.json"))


class Store:
    def __init__(self, path=None):
        self.path = Path(path) if path else default_path()

    def load(self):
        if not self.path.exists():
            return []
        try:
            data = json.loads(self.path.read_text())
        except json.JSONDecodeError as e:
            raise RuntimeError(f"{self.path} is not valid JSON: {e}")
        return [Alarm(**item) for item in data]

    def save(self, alarms):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_name(self.path.name + ".tmp")
        tmp.write_text(json.dumps([asdict(a) for a in alarms], indent=2))
        os.replace(tmp, self.path)

    def add(self, alarm):
        alarms = self.load()
        alarm.id = max((a.id for a in alarms), default=0) + 1
        alarms.append(alarm)
        self.save(alarms)
        return alarm

    def remove(self, alarm_id):
        alarms = self.load()
        kept = [a for a in alarms if a.id != alarm_id]
        if len(kept) == len(alarms):
            return False
        self.save(kept)
        return True

    def update(self, alarm):
        alarms = self.load()
        for i, existing in enumerate(alarms):
            if existing.id == alarm.id:
                alarms[i] = alarm
                self.save(alarms)
                return True
        return False
