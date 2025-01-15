#!/usr/bin/env -S uv run --quiet
# /// script
# requires-python = ">=3.12"
# ///
import subprocess
import re
import sys
from datetime import datetime, timedelta, UTC

CARD_RE = r"""((\s+)card-[a-z-]+:: [^\n]+.)+"""


def fixup_key(entry: str, key: str, value: str) -> str:
    return re.sub(f"{key}:: [^\n]+", f"{key}:: {value}", entry)


LAST_REVIEWED_THRESHOLD = datetime(2024, 1, 1, tzinfo=UTC)

LAST_INTERVAL = "card-last-interval"
NEXT_SCHEDULE = "card-next-schedule"
LAST_REVIEWED = "card-last-reviewed"
REQUIRED_KEYS = {LAST_INTERVAL, NEXT_SCHEDULE, LAST_REVIEWED}


# TODO: attributes in between card- attributes break this code,
# specifically the collapse attribute
def fixup_card(match):
    entry_raw = match.group(0)
    lines = [line.strip() for line in entry_raw.strip().split("\n")]
    d = {s[0]: s[1] for line in lines if (s := line.split(":: "))}

    if not REQUIRED_KEYS.issubset(d.keys()):
        return entry_raw
    if (li := d.get(LAST_INTERVAL)) and li == "-1":
        return entry_raw
    last_reviewed = datetime.fromisoformat(d[LAST_REVIEWED])
    if last_reviewed < LAST_REVIEWED_THRESHOLD:
        return entry_raw

    reps = int(d["card-repeats"])
    new_interval = 2.5**reps

    new_next_schedule = last_reviewed + timedelta(days=new_interval)
    new_next_schedule = new_next_schedule.replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    new_next_schedule_f = new_next_schedule.isoformat(timespec="milliseconds")
    new_next_schedule_f = new_next_schedule_f.replace("+00:00", "Z")

    entry_adj = entry_raw
    entry_adj = fixup_key(entry_adj, LAST_INTERVAL, f"{new_interval:.2f}")
    entry_adj = fixup_key(entry_adj, NEXT_SCHEDULE, new_next_schedule_f)

    return entry_adj


def fixup_cards(fp: str) -> None:
    with open(fp) as f:
        content = f.read()

    processed_content = re.sub(CARD_RE, fixup_card, content, flags=re.DOTALL)
    with open(fp, "w") as f:
        f.write(processed_content)


def run_shell_command(command: str):
    try:
        result = subprocess.run(
            command, shell=True, text=True, capture_output=True, check=True
        )
        return result.stdout.splitlines()
    except subprocess.CalledProcessError as e:
        print(e)
        print(e.stderr)
        sys.exit(2)


def main():
    # cns = card next schedule
    for fp in run_shell_command("ls -1 pages/*"):
        fixup_cards(fp)


if __name__ == "__main__":
    main()
