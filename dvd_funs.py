import datetime
import os
import pathlib
import re
import shutil
import subprocess
import time
import traceback
from collections import defaultdict
from typing import DefaultDict, Optional, Tuple, Union

import dateutil.relativedelta
import tqdm
from playsound import playsound

from funs import drive_is_full, drive_is_open, get_dvd_label, wait_on_closed_drive, wait_on_ready_drive  # NOQA


def apply_current_to_bar(bar: tqdm.tqdm, current_val: int, max_v: int) -> None:
    bar.n = current_val
    try:
        if current_val > 0:
            total_left = max_v - current_val
            elapsed_total = datetime.timedelta(seconds=bar.format_dict['elapsed'])
            time_total_left = elapsed_total * total_left / current_val
            total_eta = datetime.datetime.now() + time_total_left

            if time_total_left.days == 1:
                bar.unit = f" <1 tag {datetime.datetime.min + time_total_left:%M:%S} @{total_eta:%a %H:%M:%S}"
            if time_total_left.days > 1:
                bar.unit = f" <{time_total_left.days} tage {datetime.datetime.min + time_total_left:%M:%S} @{total_eta:%a %H:%M:%S}"
            elif time_total_left.total_seconds() < 60 * 60:
                bar.unit = f" <{datetime.datetime.min + time_total_left:%M:%S} @{total_eta:%H:%M:%S}"
            else:
                bar.unit = f" <{datetime.datetime.min + time_total_left:%H:%M:%S} @{total_eta:%H:%M:%S}"
    except Exception as e:
        bar.write(f"{datetime.datetime.now()}: {type(e)}; {e}; {elapsed_total=} {time_total_left=} {total_eta=}")
        bar.write(f"{datetime.datetime.now()}: {traceback.print_exc()}")

    bar.refresh()


def play_sound(drive_no: Union[int, str]):
    if isinstance(drive_no, str) and drive_no.isdigit():
        drive_no = int(drive_no)
    if 0 <= drive_no <= 3:
        file = pathlib.Path(os.path.dirname(os.path.realpath(__file__)))
        fn = file / "klingel" / f"{drive_no}-glocke.mp3"
        playsound(fn)


def rip_single_DVD(drive_number: int, minlength: int, fudge_months: int, fudge_days: int, disc_number: Optional[int] = None) -> Tuple[int, str]:
    wait_on_ready_drive(drive_number)
    while not drive_is_full(drive_number):
        if not drive_is_open(drive_number):
            print(f"drive /dev/sr{drive_number} does not contain a disc, opening it for you now. ")
            subprocess.run(['eject', '/dev/sr' + str(drive_number)])
        wait_on_closed_drive(drive_number)
        time.sleep(1)
        wait_on_ready_drive(drive_number)
        print("", end="")

    # at this point the drive should be ready and there should be a disc in it
    name = get_dvd_label(drive_number)
    out_name = f"dev_sr{drive_number}_{name.title()}".replace(" ", "_")
    complete_name = f"completed__{out_name}"

    print(f"{out_name=}")

    ret_val = 1
    if os.path.exists(complete_name) is False:
        pathlib.Path(out_name).mkdir(exist_ok=True)
    else:
        print(f""""{complete_name}" exists, exiting""")
        subprocess.run(['eject', '/dev/sr' + str(drive_number)])
        time.sleep(5)
        return (-1, complete_name)

    date_fudge = datetime.datetime.now() - dateutil.relativedelta.relativedelta(months=fudge_months, days=fudge_days)
    makemkv_command = f"""datefudge {date_fudge.isoformat()} makemkvcon -r --progress=-stdout --decrypt --minlength {minlength} --noscan mkv dev:/dev/sr{drive_number} all {out_name}"""

    if disc_number is not None:
        makemkv_command = f"""datefudge {date_fudge.isoformat()} makemkvcon -r --progress=-stdout --decrypt --noscan backup disc:{disc_number} {out_name}"""

    # subprocess.run(["sudo", "timedatectl", "set-ntp", "off"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # subprocess.run(["sudo", "date", "--set", "2024-04-30T13:42"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    print(makemkv_command)
    makemkvcon_process = subprocess.Popen(makemkv_command.split(" "), stdout=subprocess.PIPE)

    # subprocess.run(["sudo", "timedatectl", "set-ntp", "on"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    regex_progress = re.compile(r"""PRGV:(\d+),(\d+),(\d+)""")
    regex_progress_title_current = re.compile(r"""PRGC:(\d+),(\d+),\"(.+)\"""")
    regex_progress_title_total = re.compile(r"""PRGT:(\d+),(\d+),\"(.+)\"""")

    bar_format = "{desc}{percentage:7.3f}%{bar}[{n_fmt:>5}/{total_fmt}|{elapsed:^5}<{remaining:^5}]{unit:>17}"
    colour_total_done = "#666666"  # 40L
    colour_current_done = "#808080"  # 50L
    colour_total = "#b3b3b3"  # 70L
    colour_current = "#e6e6e6"  # 90L
    bar_total = tqdm.tqdm(dynamic_ncols=True, position=1, desc="  total", leave=False, bar_format=bar_format, total=65536, colour=colour_total)
    bar_current = tqdm.tqdm(dynamic_ncols=True, position=0, desc="current", leave=False, bar_format=bar_format, total=65536, colour=colour_current)

    last_progress_change = datetime.datetime.now()

    bar_messages_dict: DefaultDict[str, int] = defaultdict(int)
    for line_coded in iter(makemkvcon_process.stdout.readline, ""):
        line = line_coded.decode()

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
            last_progress_change = datetime.datetime.now()
        elif matches_progress_title_current is not None and len(matches_progress_title_current) >= 3:
            bar_current.colour = colour_current_done
            bar_current = tqdm.tqdm(dynamic_ncols=True, position=0, desc=matches_progress_title_current[2].rjust(30), leave=True, bar_format=bar_format, total=65536, colour=colour_current)
        elif matches_progress_title_total is not None and len(matches_progress_title_total) >= 3:
            bar_total.colour = colour_total_done
            bar_total = tqdm.tqdm(dynamic_ncols=True, position=1, desc=matches_progress_title_total[2].rjust(30), leave=True, bar_format=bar_format, total=65536, colour=colour_total)
        else:
            if line == "":
                # empty string after termination,
                # "\n" while still running?
                break

            line = line.strip()

            if line == "":
                continue

            bar_message = f"{line}"
            if line.startswith("MSG:"):
                bar_message = f"""{line.split('"')[1]}"""

            bar_messages_dict[bar_message] += 1
            addendum = ""
            message_count = bar_messages_dict[bar_message]
            if message_count > 1:
                addendum = f" ×{message_count:>4d} {'.' * (message_count % 10)}*{'.' * (9 - message_count % 10)}"

            t_size = shutil.get_terminal_size((80, 20))
            writable = f"{datetime.datetime.now()}: {bar_message}{addendum}"
            terminal_width = t_size.columns
            leftover = terminal_width - len(writable)
            time_since_last_prg_change = datetime.datetime.now() - last_progress_change
            if leftover > 0:
                writable += (" " * terminal_width + f" {last_progress_change} {time_since_last_prg_change}")[-leftover:]
            bar_current.write(writable)

            if bar_message.startswith("Failed to save title"):
                failed_file = bar_message.split("to file")[-1].strip()
                pathlib.Path(f"{failed_file}.failed").touch(exist_ok=True)

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
        return -1, name

    play_sound(drive_number)

    # eject dvd after finishing
    subprocess.run(['eject', '/dev/sr' + str(drive_number)])
    return ret_val, name
