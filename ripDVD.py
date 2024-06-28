#!/usr/bin/env python3

import argparse
import os
import pathlib
import subprocess
from typing import List

from dvd_funs import extract_single_input
from funs import drive_exists


def main():
    parser = argparse.ArgumentParser(description='copies a dvd to disc.')

    parser.add_argument(
        '-d',
        '--driveNo',
        required=False,
        type=int,
        action="append",
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
        type=int,
        default=None,
        action="append",
        help='disc number, cause somehow for backup the disc number is not the same as the drives device number',
    )

    parser.add_argument(
        '-extract',
        required=False,
        type=str,
        default=None,
        help='Folder name of a backup, extracts all titles in contained therein',
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
    minlength: int = args.minlength
    extract: str = args.extract

    drive_number_raw: List[int] = args.driveNo
    if drive_number_raw is None and extract is None:
        raise ValueError("why u put no drive number or extract, that dum")
    drive_number = None
    if type(drive_number_raw) is list:
        if len(drive_number_raw) != 1:
            raise ValueError(f"drive_number given multiple times! {drive_number_raw=} {type(drive_number_raw)=}")
        drive_number = drive_number_raw[0]
    if type(drive_number) is int and not drive_exists(drive_number):
        raise ValueError(f"drive /dev/sr{drive_number} doesn't exist!")

    disc_number_raw: List[int] = args.disc
    disc_number = None
    if type(disc_number_raw) is list:
        if len(disc_number_raw) != 1:
            raise ValueError(f"disc given multiple times! {disc_number_raw=} {type(disc_number_raw)=}")
        disc_number = disc_number_raw[0]

    if type(extract) is str:
        extract_input = pathlib.Path(extract)
        if not extract_input.exists():
            raise ValueError(f"extract input '{extract}' does not exist!")

    if extract is not None:
        # only a single folder will be given to extract, makes no sense to keep going
        rc, name = extract_single_input(minlength, fudge_months, fudge_days, extract_input)
        print(rc, name)
    else:
        while True:
            from dvd_funs import rip_single_DVD
            rc, name = rip_single_DVD(drive_number, minlength, fudge_months, fudge_days, disc_number)

            print(rc, name)
            # telegram message
            subprocess.run(
                [os.path.expanduser("/home/jola/Documents/erinner_bot/t_msg"), f"done for drive /dev/sr{drive_number} {name}", "server-mail.id"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )


if __name__ == '__main__':
    main()
