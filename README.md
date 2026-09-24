<div align="center">

# ⏰ alarmclock

**A small, dependency-free alarm clock that lives in your terminal.**

[![tests](https://github.com/prajak002/better/actions/workflows/tests.yml/badge.svg)](https://github.com/prajak002/better/actions/workflows/tests.yml)
![python](https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white)
![deps](https://img.shields.io/badge/dependencies-none-brightgreen)
![platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux-lightgrey)

<img src="demo/demo.gif" alt="alarmclock demo" width="820">

<sub>Set alarms, hit a validation error, watch one ring, snooze it, and see the schedule update. ▶ <a href="demo/demo.mp4">MP4 version</a></sub>

</div>

---

## Quick start

```bash
git clone https://github.com/prajak002/better.git && cd better
pip install -e .

alarm add +1m -l "try me"
alarm run
```

No install? Everything also works with `python3 -m alarmclock <command>`.

## Commands

| Command | What it does |
|---|---|
| `alarm add 07:30` | One-off alarm at the next 07:30 |
| `alarm add 7:30am -r weekdays -l "wake up"` | Repeating alarm with a label |
| `alarm add +25m` | Alarm 25 minutes from now (`+1h30m`, `+30s` work too) |
| `alarm list` | Show all alarms and when each rings next |
| `alarm remove 2` | Delete alarm #2 |
| `alarm run` | Start the clock; rings alarms as they come due |
| `alarm run --snooze 10` | Same, with a 10 minute snooze |

**Time formats:** `07:30` · `7:30am` · `6pm` · `+10m` · `+1h30m` · `+30s`
**Repeat:** `daily` · `weekdays` · `weekends` · `mon,wed,fri`. Without `--repeat` the alarm rings once.

When an alarm goes off it plays a sound (`afplay` on macOS, terminal bell elsewhere) until you press **Enter** to dismiss or **s + Enter** to snooze.

Alarms live in `~/.alarmclock.json`. Point `ALARM_FILE` somewhere else to keep separate sets.

## How it works
<img width="1536" height="1024" alt="ChatGPT Image Sep 24, 2026, 01_10_37 PM" src="https://github.com/user-attachments/assets/ae943284-6784-4e03-9f6f-b0b9007afcc8" />


| Module | Responsibility |
|---|---|
| `alarm.py` | Parsing (times, offsets, days) and scheduling: `next_fire()`, `state()`, `snooze()`, `dismiss()` |
| `store.py` | JSON persistence with atomic writes and merge-by-id updates |
| `ringer.py` | The `run` loop and the sound thread |
| `cli.py` | argparse wiring and output formatting |

## Requirements I settled on

The brief was "build an alarm clock CLI" with no spec and about 30 minutes. I scoped it to what a person actually does with an alarm clock:

1. Set an alarm for a clock time or "in N minutes"
2. Make it repeat on certain days
3. See and delete alarms
4. Have it ring, and snooze or dismiss it

## Design decisions

- **Two processes, one file.** `add/list/remove` are one-shot commands; `run` is a long-running foreground loop. They share a JSON file and `run` reloads it every second, so you can add alarms from another terminal while the clock is running. No database, as the brief asked.
- **One-off and repeating alarms are stored differently.** A one-off stores an absolute datetime, resolved when you add it, so "07:30" added at 08:00 means tomorrow. A repeating alarm stores the time, the weekdays and `last_fired`, and the next ring is computed from those. That keeps `next_fire()` a pure function that is easy to test.
- **Snooze is persisted** (`snoozed_until`), so restarting `run` doesn't lose a snoozed alarm.
- **Missed alarms are skipped, not rung late.** If an alarm is more than 5 minutes overdue when `run` sees it, it is logged and moved on. A 07:00 alarm going off at 11:00 is worse than useless.
- **Safe writes.** Saves go to a temp file followed by `os.replace`, so a crash can't leave half-written JSON. `run` reloads and merges by id instead of writing back a stale list, because the user may take a minute to dismiss an alarm and could add another in the meantime. There is a test for exactly this.
- **One-off alarms are turned off after ringing, not deleted**, so `list` still shows what happened.

## Tests

```bash
python3 -m unittest -v
```

15 tests cover parsing edge cases (`12am`, `13pm`, `25:00`), weekday rollover across weekends, snooze and dismiss transitions, the missed-alarm grace window, and the concurrent-add merge in the store. CI runs them on Python 3.10 to 3.13.

## Recording the demo

The GIF above is a real session, not a mock-up. `demo/record.sh` types the commands and drives the ring with `expect`, recorded with [asciinema](https://asciinema.org) and rendered with [agg](https://github.com/asciinema/agg):

```bash
asciinema rec --headless --window-size 96x27 -i 2 -c demo/record.sh demo/demo.cast
agg --theme monokai --font-size 20 demo/demo.cast demo/demo.gif
```

## Known limits

- Not a background daemon: `run` has to stay open in a terminal.
- Local naive time only; no timezone or DST handling.
- Two `run` processes on the same file would both ring. A lock file would fix that.
- Alarms ring one at a time; if two are due together, the second rings after the first is handled.
