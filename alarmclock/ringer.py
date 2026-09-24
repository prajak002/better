import os
import shutil
import subprocess
import sys
import threading
import time
from datetime import datetime, timedelta

SOUND = "/System/Library/Sounds/Glass.aiff"


def beep(stop):
    player = shutil.which("afplay") if os.path.exists(SOUND) else None
    while not stop.is_set():
        if player:
            subprocess.run([player, SOUND], check=False)
        else:
            sys.stdout.write("\a")
            sys.stdout.flush()
        stop.wait(1)


def ring(alarm, snooze_minutes):
    stop = threading.Event()
    threading.Thread(target=beep, args=(stop,), daemon=True).start()
    label = f" - {alarm.label}" if alarm.label else ""
    print(f"\n>>> ALARM #{alarm.id} {alarm.time}{label}")
    try:
        answer = input(f"Enter to dismiss, s + Enter to snooze {snooze_minutes}m: ")
    except EOFError:
        answer = ""
    finally:
        stop.set()
    return answer.strip().lower().startswith("s")


def run(store, snooze_minutes=5, grace_minutes=5):
    grace = timedelta(minutes=grace_minutes)
    print(f"Watching {store.path}. Ctrl+C to stop.")
    while True:
        for alarm in store.load():
            now = datetime.now()
            state = alarm.state(now, grace)
            if state == "missed":
                print(f"Skipped #{alarm.id} {alarm.time}, it was due at {alarm.next_fire():%H:%M}")
                alarm.dismiss(now)
                store.update(alarm)
            elif state == "due":
                snoozed = ring(alarm, snooze_minutes)
                now = datetime.now()
                if snoozed:
                    alarm.snooze(now, snooze_minutes)
                    print(f"Snoozed until {alarm.next_fire():%H:%M}")
                else:
                    alarm.dismiss(now)
                    print("Dismissed")
                store.update(alarm)
        time.sleep(1)
