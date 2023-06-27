#!/usr/bin/env python3

import argparse
import os
import subprocess
import time

from funs import drive_exists, drive_full, drive_open, wait_on_closed_drive, wait_on_ready_drive  # NOQA


def main():
    parser = argparse.ArgumentParser(
        description='copies a cd to disc with abcde')

    required_named = parser.add_argument_group('required arguments')
    required_named.add_argument('-d', '--driveNo', help='drive number, ie \'/dev/sr0\' means \'-d 0\'', required=True)
    parser.add_argument('-w', default=None, help='multi-CD identifier')

    args = parser.parse_args()

    w = args.w

    drive_number = args.driveNo
    assert drive_number is not None, "why u put no drive number, that dum"

    # only proceed if the drive exists
    assert drive_exists(drive_number), "drive /dev/sr" + str(drive_number) + " doesn't exist!"

    prevdir = os.getcwd()
    out_dir = f"{prevdir}{os.sep}dev_sr{drive_number}"
    os.makedirs(out_dir, exist_ok=True)
    os.chdir(out_dir)

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

    if w is not None:
        w_str = ["-W", w]
    else:
        w_str = ["", ""]

    abcde_instance = subprocess.Popen(["abcde", "-x", "-N", "-V", "-G", "-B", "-d", f"/dev/sr{str(drive_number)}", w_str[0], w_str[1]])
    abcde_instance.wait()
    os.chdir(prevdir)
    subprocess.Popen(['flatpak', 'run', 'org.musicbrainz.Picard', '.'])

    # eject cd after finishing
    subprocess.run(['eject', '/dev/sr' + str(drive_number)])


if __name__ == '__main__':
    while True:
        main()
