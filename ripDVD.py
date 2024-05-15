#!/usr/bin/env python3

import argparse
import os
import subprocess

from funs import drive_exists


def main():
    parser = argparse.ArgumentParser(description='copies a dvd to disc.')

    parser.add_argument(
        '-d',
        '--driveNo',
        action="append",
        required=False,
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
        '-disc',
        required=False,
        default=None,
        action="append",
        help='disc number, cause somehow for backup the disc number is not the same as the drives device number',
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
    assert type(drive_number) is list and len(drive_number) == 1, f"drive_number given multiple times! {drive_number=} {type(drive_number)=}"
    drive_number = drive_number[0]

    # only proceed if the drive exists
    assert drive_exists(drive_number), f"drive /dev/sr{drive_number} doesn't exist!"

    minlength: int = args.minlength
    disc_number: int = args.disc
    assert type(disc_number) is list and len(disc_number) == 1, f"disc given multiple times! {disc_number=} {type(disc_number)=}"
    disc_number = disc_number[0]

    while True:
        from dvd_funs import rip_single_DVD
        rc, name = rip_single_DVD(drive_number, minlength, fudge_months, fudge_days, disc_number)

        print(rc, name)
        subprocess.run(
            [os.path.expanduser("/home/niels/Documents/erinner_bot/t_msg"), f"done for drive /dev/sr{drive_number} {name}", "server-mail.id"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )


if __name__ == '__main__':
    main()
