#!/usr/bin/env python3

import subprocess
import argparse
import math
import os
import time
import sys


parser = argparse.ArgumentParser(
    description='copies a dvd to disc, no processing. The output will be named by the current date and time.')

requiredNamed = parser.add_argument_group('required arguments')
requiredNamed.add_argument('-d', '--driveNo', help='drive number, ie \'/dev/sr0\' means \'-d 0\'', required=True)
parser.add_argument('-f', type=str, default="DVD", help='filename to prepend the standard name, default="DVD"')

args = parser.parse_args()

driveNumber = args.driveNo
assert driveNumber != None, "why u put no drive number, that dum"

fileName = args.f


def driveExists(driveNumber: int) -> bool:
    subProcessResult = subprocess.run(['setcd', '-i', '/dev/sr'+str(driveNumber)],
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE)
    subProcessStdOut = subProcessResult.stdout.decode('utf-8')
    subProcessStdErr = subProcessResult.stderr.decode('utf-8')
    #print("subProcessStdOut", subProcessStdOut)
    #print("subProcessStdErr", subProcessStdErr)
    return 'No such file or directory' not in subProcessStdErr


# only proceed if the drive exists
assert driveExists(driveNumber), "drive /dev/sr" + str(driveNumber) + " doesn't exist!"


def driveFull(driveNumber: int) -> bool:
    subProcessResult = subprocess.run(['setcd', '-i', '/dev/sr'+str(driveNumber)],
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE)
    subProcessStdOut = subProcessResult.stdout.decode('utf-8')
    subProcessStdErr = subProcessResult.stderr.decode('utf-8')
    return 'Disc found in drive' in subProcessStdOut


def driveReady(driveNumber: int) -> bool:
    subProcessResult = subprocess.run(['setcd', '-i', '/dev/sr'+str(driveNumber)],
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE)
    subProcessStdOut = subProcessResult.stdout.decode('utf-8')
    subProcessStdErr = subProcessResult.stderr.decode('utf-8')
    return 'Drive is not ready' not in subProcessStdOut


def driveOpen(driveNumber: int) -> bool:
    subProcessResult = subprocess.run(['setcd', '-i', '/dev/sr'+str(driveNumber)],
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE)
    subProcessStdOut = subProcessResult.stdout.decode('utf-8')
    subProcessStdErr = subProcessResult.stderr.decode('utf-8')
    return 'tray is open' in subProcessStdOut


#print("driveOpen", driveOpen(driveNumber))
#print("driveReady", driveReady(driveNumber))
#print("driveFull", driveFull(driveNumber))


def waitOnClosedDrive():
    waiting = 1
    while driveOpen(driveNumber):
        waiting += 1
        print("\rdrive /dev/sr" + str(driveNumber) + " is open, waiting for you to close it with a disc inserted. ", end="")
        spinner = "←↖↑↗→↘↓↙"
        print(spinner[waiting % len(spinner)], end="\r")
    sys.stdout.write("\033[K")  # Clear to the end of line


def waitOnReadyDrive():
    waiting = 1
    while not driveReady(driveNumber):
        waiting += 1
        print("\rdrive /dev/sr" + str(driveNumber) + " is not ready, waiting for it to be ready. ", end="")
        spinner = "←↖↑↗→↘↓↙"
        print(spinner[waiting % len(spinner)], end="\r")
    sys.stdout.write("\033[K")  # Clear to the end of line


waitOnReadyDrive()
while not driveFull(driveNumber):
    if not driveOpen(driveNumber):
        print("drive /dev/sr" + str(driveNumber) + " does not contain a disc, opening it for you now. ")
        subprocess.run(['eject', '/dev/sr'+str(driveNumber)])
    waitOnClosedDrive()
    time.sleep(1)
    waitOnReadyDrive()
    print("", end="")

# at this point the drive should be ready and there should be a disc in it

subProcessResult = subprocess.run(['date', '+"%Y-%m-%dT%H%M%S"'],
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)
now_string = subProcessResult.stdout.decode('utf-8')[1:-2]
print(now_string)

subProcessResult = subprocess.run(['mplayer', '/dev/sr' + str(driveNumber), '-v',
                                   '-dumpstream', '-dumpfile', fileName + '_' + now_string + '.avi'])

subprocess.run(['eject', '/dev/sr'+str(driveNumber)])
