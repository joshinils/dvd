#!/usr/bin/env python3

import argparse
import datetime
import os
import pathlib
import re
import shutil
import subprocess
import time

import dateutil.relativedelta
import tqdm

from funs import drive_exists, drive_full, drive_open, get_dvd_label, wait_on_closed_drive, wait_on_ready_drive  # NOQA


def apply_current_to_bar(bar: tqdm.tqdm, current_val: int, max_v: int) -> None:
    bar.n = current_val
    if current_val > 0:
        total_left = max_v - current_val
        elapsed_total = datetime.timedelta(seconds=bar.format_dict['elapsed'])
        time_total_left = elapsed_total * total_left / current_val
        total_eta = datetime.datetime.now() + time_total_left
        bar.set_postfix_str(f"{datetime.datetime.min + elapsed_total:%H:%M:%S}<{datetime.datetime.min + time_total_left:%H:%M:%S} @{total_eta:%H:%M:%S}")
    bar.refresh()


def rip_single_DVD(drive_number: int, minlength: int, fudge_months: int, fudge_days: int) -> int:
    wait_on_ready_drive(drive_number)
    while not drive_full(drive_number):
        if not drive_open(drive_number):
            print(f"drive /dev/sr{drive_number} does not contain a disc, opening it for you now. ")
            subprocess.run(['eject', '/dev/sr' + str(drive_number)])
        wait_on_closed_drive(drive_number)
        time.sleep(1)
        wait_on_ready_drive(drive_number)
        print("", end="")

    # at this point the drive should be ready and there should be a disc in it

    out_name = f"dev_sr{drive_number}_{get_dvd_label(drive_number).title()}".replace(" ", "_")
    complete_name = f"completed__{out_name}"

    print(f"{out_name=}")

    ret_val = 1
    if os.path.exists(complete_name) is False:
        pathlib.Path(out_name).mkdir(exist_ok=True)

    date_fudge = datetime.datetime.now() - dateutil.relativedelta.relativedelta(months=fudge_months, days=fudge_days)
    makemkv_command = f"""datefudge {date_fudge.isoformat()} makemkvcon -r mkv --progress=-stdout --decrypt --minlength {minlength} --noscan dev:/dev/sr{drive_number} all {out_name}"""
    print(makemkv_command)
    makemkvcon_process = subprocess.Popen(makemkv_command.split(" "), stdout=subprocess.PIPE)

    regex_progress = re.compile(r"""PRGV:(\d+),(\d+),(\d+)""")
    regex_progress_title_current = re.compile(r"""PRGC:(\d+),(\d+),\"(.+)\"""")
    regex_progress_title_total = re.compile(r"""PRGT:(\d+),(\d+),\"(.+)\"""")

    bar_format = "{desc}{percentage:6.2f}%{bar}[{elapsed}<{remaining}][{postfix}]"
    bar_total = tqdm.tqdm(dynamic_ncols=True, position=0, desc="  total", leave=False, bar_format=bar_format, total=65536)
    bar_current = tqdm.tqdm(dynamic_ncols=True, position=1, desc="current", leave=False, bar_format=bar_format, total=65536)

    for line in iter(makemkvcon_process.stdout.readline, ""):
        line = line.decode()

        matches_progress = regex_progress.match(line)
        matches_progress_title_current = regex_progress_title_current.match(line)
        matches_progress_title_total = regex_progress_title_total.match(line)

        if matches_progress is not None:
            matches_progress = matches_progress.groups()
        if matches_progress_title_current is not None:
            matches_progress_title_current = matches_progress_title_current.groups()
        if matches_progress_title_total is not None:
            matches_progress_title_total = matches_progress_title_total.groups()

        if matches_progress is not None and len(matches_progress) >= 3:
            current, total, max_v, *_ = matches_progress
            apply_current_to_bar(bar_current, int(current), int(max_v))
            apply_current_to_bar(bar_total, int(total), int(max_v))
        elif matches_progress_title_current is not None and len(matches_progress_title_current) >= 3:
            bar_current = tqdm.tqdm(dynamic_ncols=True, position=1, desc=matches_progress_title_current[2].rjust(30), leave=True, bar_format=bar_format, total=65536)
        elif matches_progress_title_total is not None and len(matches_progress_title_total) >= 3:
            bar_total = tqdm.tqdm(dynamic_ncols=True, position=0, desc=matches_progress_title_total[2].rjust(30), leave=True, bar_format=bar_format, total=65536)
        else:
            if line == "":
                # empty string after termination,
                # "\n" while still running?
                break
            if line.strip() == "":
                continue
            if line.strip().startswith("MSG:"):
                quote = "\""
                bar_current.write(f"{datetime.datetime.now()}: {line.strip().split(quote)[1]}")
            else:
                bar_current.write(f"{datetime.datetime.now()}: {line.strip()}")

        bar_current.update(0)
        bar_total.update(0)

        if makemkvcon_process.poll() is not None:
            break
    bar_current.close()
    bar_total.close()

    return_code = makemkvcon_process.wait()

    if return_code == 0:
        print(f"{out_name=} {complete_name=}")
        try:
            shutil.move(out_name, complete_name)
        except Exception as e:
            print(type(e), e)

        ret_val = 0
    else:
        return -1

    # eject dvd after finishing
    subprocess.run(['eject', '/dev/sr' + str(drive_number)])
    return ret_val


def main():
    parser = argparse.ArgumentParser(description='copies a dvd to disc.')

    parser.add_argument(
        '-d',
        '--driveNo',
        required=True,
        help='drive number, ie \'/dev/sr0\' means \'-d 0\'',
    )

    parser.add_argument(
        '-m',
        '--minlength',
        required=False,
        type=int,
        default=300,
        help='minimum title length in seconds, default=300',
    )

    parser.add_argument(
        '-M',
        '--fudge_months',
        required=False,
        type=int,
        default=0,
        help='fudgedate months, default: 0',
    )

    parser.add_argument(
        '-D',
        '--fudge_days',
        required=False,
        type=int,
        default=0,
        help='fudgedate days, default: 0',
    )

    args = parser.parse_args()

    fudge_months: int = args.fudge_months
    fudge_days: int = args.fudge_days

    drive_number: int = args.driveNo
    assert drive_number is not None, "why u put no drive number, that dum"

    # only proceed if the drive exists
    assert drive_exists(drive_number), f"drive /dev/sr{drive_number} doesn't exist!"

    minlength: int = args.minlength

    while True:
        rip_single_DVD(drive_number, minlength, fudge_months, fudge_days)


if __name__ == '__main__':
    main()
