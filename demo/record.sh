#!/bin/bash
cd "$(dirname "$0")/.."
source .venv/bin/activate
export ALARM_FILE=/tmp/alarm-demo.json
rm -f "$ALARM_FILE"

PROMPT=$'\e[35malarm-demo\e[0m \e[36m❯\e[0m '

type_cmd() {
    printf "%s" "$PROMPT"
    sleep 0.4
    local text="$1"
    for ((i = 0; i < ${#text}; i++)); do
        printf "%s" "${text:i:1}"
        sleep 0.035
    done
    sleep 0.3
    echo
}

show() {
    type_cmd "$1"
    eval "$1"
    sleep "${2:-1.2}"
}

clear
show "alarm add 07:30 --repeat weekdays --label 'wake up'"
show "alarm add 6pm -l tea"
show "alarm add 7:00 -r funday" 1.8
show "alarm add +6s -l 'standup'"
show "alarm list" 2.5

type_cmd "alarm run --snooze 1"
expect -c '
    set timeout 30
    log_user 1
    spawn -noecho alarm run --snooze 1
    expect "snooze 1m: "
    sleep 1.5
    send "s"
    sleep 0.4
    send "\r"
    expect "Snoozed until"
    sleep 2
    send "\003"
    expect eof
'
sleep 1
show "alarm list" 3
