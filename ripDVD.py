#!/usr/bin/env python3

import subprocess
import argparse
import time
import sys


def drive_exists(drive_number: int) -> bool:
    sub_process_result = subprocess.run(['setcd', '-i', '/dev/sr'+str(drive_number)],
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
    sub_process_std_out = sub_process_result.stdout.decode('utf-8')
    sub_process_std_err = sub_process_result.stderr.decode('utf-8')
    # print("sub_process_std_out", sub_process_std_out)
    # print("sub_process_std_err", sub_process_std_err)
    return 'No such file or directory' not in sub_process_std_err


def drive_full(drive_number: int) -> bool:
    sub_process_result = subprocess.run(['setcd', '-i', '/dev/sr'+str(drive_number)],
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
    sub_process_std_out = sub_process_result.stdout.decode('utf-8')
    return 'Disc found in drive' in sub_process_std_out


def drive_ready(drive_number: int) -> bool:
    sub_process_result = subprocess.run(['setcd', '-i', '/dev/sr'+str(drive_number)],
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
    sub_process_std_out = sub_process_result.stdout.decode('utf-8')
    return 'Drive is not ready' not in sub_process_std_out


def drive_open(drive_number: int) -> bool:
    sub_process_result = subprocess.run(['setcd', '-i', '/dev/sr'+str(drive_number)],
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
    sub_process_std_out = sub_process_result.stdout.decode('utf-8')
    return 'tray is open' in sub_process_std_out


def wait_on_closed_drive(drive_number: int):
    waiting = 1
    while drive_open(drive_number):
        waiting += 1
        print("\rdrive /dev/sr" + str(drive_number) + " is open, waiting for you to close it with a disc inserted. ", end="")
        spinner = "←↖↑↗→↘↓↙"
        print(spinner[waiting % len(spinner)], end="\r")
    sys.stdout.write("\033[K")  # Clear to the end of line


def wait_on_ready_drive(drive_number: int):
    waiting = 1
    while not drive_ready(drive_number):
        waiting += 1
        print("\rdrive /dev/sr" + str(drive_number) + " is not ready, waiting for it to be ready. ", end="")
        spinner = "←↖↑↗→↘↓↙"
        print(spinner[waiting % len(spinner)], end="\r")
    sys.stdout.write("\033[K")  # Clear to the end of line


def main():
    parser = argparse.ArgumentParser(
        description='copies a dvd to disc, no processing. The output will be named by the current date and time.')

    required_named = parser.add_argument_group('required arguments')
    required_named.add_argument('-d', '--driveNo', help='drive number, ie \'/dev/sr0\' means \'-d 0\'', required=True)
    parser.add_argument('-f', type=str, default="DVD", help='filename to prepend the standard name, default="DVD"')

    args = parser.parse_args()

    drive_number = args.driveNo
    assert drive_number is not None, "why u put no drive number, that dum"

    # only proceed if the drive exists
    assert drive_exists(drive_number), "drive /dev/sr" + str(drive_number) + " doesn't exist!"

    file_name = args.f

    # print("driveOpen", driveOpen(drive_number))
    # print("driveReady", driveReady(drive_number))
    # print("driveFull", driveFull(drive_number))

    wait_on_ready_drive(drive_number)
    while not drive_full(drive_number):
        if not drive_open(drive_number):
            print("drive /dev/sr" + str(drive_number) + " does not contain a disc, opening it for you now. ")
            subprocess.run(['eject', '/dev/sr'+str(drive_number)])
        wait_on_closed_drive(drive_number)
        time.sleep(1)
        wait_on_ready_drive(drive_number)
        print("", end="")

    # at this point the drive should be ready and there should be a disc in it

    sub_process_result = subprocess.run(['date', '+"%Y-%m-%dT%H%M%S"'],
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
    now_string = sub_process_result.stdout.decode('utf-8')[1:-2]
    print(now_string)

    subprocess.run(['mplayer', '/dev/sr' + str(drive_number), '-v',
                    '-dumpstream', '-dumpfile', file_name + '_' + now_string + '.avi'])

    # eject dvd after finishing
    subprocess.run(['eject', '/dev/sr' + str(drive_number)])


if __name__ == '__main__':
    main()
