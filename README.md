# alarmclock

A small alarm clock for the terminal. Python 3.10+, standard library only.

## Usage

```
pip install -e .                      # gives you the `alarm` command
# or run without installing: python3 -m alarmclock ...

alarm add 07:30 --repeat weekdays --label "wake up"
alarm add 6pm -l tea
alarm add +25m -l "pomodoro"
alarm list
alarm remove 2
alarm run                             # keeps running, rings alarms when due
alarm run --snooze 10
```

Time formats: `07:30`, `7:30am`, `6pm`, or an offset from now like `+10m`, `+1h30m`.
Repeat: `daily`, `weekdays`, `weekends`, or a list like `mon,wed,fri`. Without `--repeat` the alarm rings once.

When an alarm goes off it plays a sound (afplay on macOS, terminal bell elsewhere) until you press Enter to dismiss or `s` + Enter to snooze.

Alarms are stored in `~/.alarmclock.json`. Set `ALARM_FILE` to use a different file.

## Tests

```
python3 -m unittest -v
```

## Requirements I settled on

The brief was "build an alarm clock CLI", no spec, about 30 minutes. I scoped it to what a person actually does with an alarm clock:

1. Set an alarm for a clock time or "in N minutes"
2. Make it repeat on certain days
3. See and delete alarms
4. Have it ring, and snooze or dismiss it

## Design decisions

- **Two processes, one file.** `add/list/remove` are one-shot commands; `run` is a long-running foreground loop. They share a JSON file, and `run` reloads it every second, so you can add alarms from another terminal while the clock is running. No database, as the brief asked.
- **One-off vs repeating alarms are stored differently.** A one-off stores an absolute datetime (`at`), resolved when you add it, so "07:30" added at 08:00 means tomorrow. A repeating alarm stores the time, the weekdays and `last_fired`, and the next ring is computed from those. This keeps `next_fire()` a pure function that is easy to test.
- **Snooze is persisted** (`snoozed_until`), so restarting `run` doesn't lose a snoozed alarm.
- **Missed alarms are skipped, not rung late.** If `run` wasn't running and an alarm is more than 5 minutes overdue, it is logged and moved on. A 07:00 alarm going off at 11:00 when you start the clock is worse than useless.
- **Safe writes.** Saves go to a temp file and `os.replace`, so a crash can't leave half-written JSON. Updates from `run` reload and merge by id rather than writing back a stale list, because the user may take a minute to dismiss an alarm and could add another one in the meantime. There is a test for this case.
- **One-off alarms are turned off after they ring, not deleted**, so `list` shows what already happened.

## Out of scope / known limits

- Not a background daemon: `run` has to stay open in a terminal.
- Local naive time only; no timezone or DST handling.
- Two `run` processes on the same file would both ring. A lock file would fix that.
- Only one alarm rings at a time; if two are due together, the second rings after the first is handled.
