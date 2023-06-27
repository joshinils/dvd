#!/usr/bin/env python3

import argparse
import signal
import subprocess
import sys
import time
import urllib.parse

from funs import drive_exists, drive_full, drive_open, get_dvd_label, wait_on_closed_drive, wait_on_ready_drive  # NOQA


def firefox_tab(moviepilot_search_term: str) -> None:
    safe_string = urllib.parse.quote_plus(moviepilot_search_term)
    print(moviepilot_search_term, safe_string)

    subprocess.run(['firefox', '-new-tab', "https://www.moviepilot.de/suche?q=" + safe_string + "&type=movie"])
    # https://www.moviepilot.de/suche?q=BRIDGE%20OF%20SPIES&type=movie


def main():
    parser = argparse.ArgumentParser(
        description='copies a dvd to disc, no processing. The output will be named by the current date and time.')

    required_named = parser.add_argument_group('required arguments')
    required_named.add_argument('-d', '--driveNo', help='drive number, ie \'/dev/sr0\' means \'-d 0\'', required=True)

    args: argparse.Namespace = parser.parse_args()

    global drive_number
    drive_number = args.driveNo
    assert drive_number is not None, "why u put no drive number, that dum"

    # only proceed if the drive exists
    assert drive_exists(drive_number), "drive /dev/sr" + str(drive_number) + " doesn't exist!"

    signal.signal(signal.SIGINT, signal_handler)

    # print("driveOpen", driveOpen(drive_number))
    # print("driveReady", driveReady(drive_number))
    # print("driveFull", driveFull(drive_number))

    wait_on_ready_drive(drive_number)
    while not drive_full(drive_number):
        if not drive_open(drive_number):
            print("drive /dev/sr" + str(drive_number) + " does not contain a disc, opening it for you now. ")
            subprocess.run(['eject', '/dev/sr' + str(drive_number)])
        wait_on_closed_drive(drive_number)
        time.sleep(1)
        wait_on_ready_drive(drive_number)
        print("", end="")

    # at this point the drive should be ready and there should be a disc in it

    handbrake_instance = subprocess.Popen(['handbrake', '-d', '/dev/sr' + str(drive_number)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    pv_instance = subprocess.Popen(['pv', '-d', str(handbrake_instance.pid), '-peI'])

    dvd_label = get_dvd_label(drive_number)
    firefox_tab(dvd_label)

    handbrake_instance.wait()
    pv_instance.wait()

    # eject dvd after finishing
    subprocess.run(['eject', '/dev/sr' + str(drive_number)])


def signal_handler(sig, frame):
    global drive_number
    if drive_open(drive_number):
        subprocess.run(['eject', '/dev/sr' + str(drive_number), '-t'])

        while drive_full(drive_number):
            wait_on_ready_drive(drive_number)
            if not drive_open(drive_number):
                print(f"drive /dev/sr{drive_number} contains a disc, opening it for you now. ")
                subprocess.run(['eject', f"/dev/sr{drive_number}"])
            wait_on_closed_drive(drive_number)
            time.sleep(1)

    sys.exit(0)


if __name__ == '__main__':
    while True:
        main()
