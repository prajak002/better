import argparse
import sys
from datetime import datetime

from .alarm import Alarm, describe_days, next_at, parse_clock, parse_days, parse_offset
from .ringer import run
from .store import Store


def cmd_add(store, args):
    now = datetime.now().replace(microsecond=0)
    offset = parse_offset(args.time)
    if offset:
        if args.repeat:
            raise ValueError("--repeat needs a clock time like 07:30, not an offset")
        at = now + offset
        clock = at.time().replace(second=0)
    else:
        clock = parse_clock(args.time)
        at = None if args.repeat else next_at(clock, now)

    alarm = Alarm(
        id=0,
        time=clock.strftime("%H:%M"),
        created=now.isoformat(),
        label=args.label or "",
        days=parse_days(args.repeat) if args.repeat else None,
        at=at.isoformat() if at else None,
    )
    store.add(alarm)
    print(f"Added #{alarm.id}, rings {alarm.next_fire():%a %d %b %H:%M}")


def cmd_list(store, args):
    alarms = store.load()
    if not alarms:
        print("No alarms. Add one with: alarm add 07:30")
        return
    print(f"{'ID':<4}{'TIME':<7}{'REPEAT':<16}{'NEXT':<18}LABEL")
    for a in alarms:
        nxt = a.next_fire().strftime("%a %d %b %H:%M") if a.enabled else "done"
        print(f"{a.id:<4}{a.time:<7}{describe_days(a.days):<16}{nxt:<18}{a.label}")


def cmd_remove(store, args):
    if not store.remove(args.id):
        raise ValueError(f"no alarm with id {args.id}")
    print(f"Removed #{args.id}")


def cmd_run(store, args):
    try:
        run(store, snooze_minutes=args.snooze)
    except KeyboardInterrupt:
        print("\nStopped")


def build_parser():
    parser = argparse.ArgumentParser(prog="alarm", description="A small alarm clock for the terminal.")
    sub = parser.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add", help="add an alarm")
    add.add_argument("time", help="07:30, 7:30am, 6pm or an offset like +10m / +1h30m / +30s")
    add.add_argument("-r", "--repeat", help="daily, weekdays, weekends or days like mon,wed,fri")
    add.add_argument("-l", "--label")
    add.set_defaults(func=cmd_add)

    ls = sub.add_parser("list", help="show alarms")
    ls.set_defaults(func=cmd_list)

    rm = sub.add_parser("remove", help="delete an alarm")
    rm.add_argument("id", type=int)
    rm.set_defaults(func=cmd_remove)

    r = sub.add_parser("run", help="start the clock and ring alarms")
    r.add_argument("--snooze", type=int, default=5, help="snooze length in minutes")
    r.set_defaults(func=cmd_run)

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        args.func(Store(), args)
    except (ValueError, RuntimeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0
