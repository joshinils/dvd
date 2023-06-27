import subprocess
import sys


def drive_exists(drive_number: int) -> bool:
    sub_process_result = subprocess.run(['setcd', '-i', f"/dev/sr{drive_number}"],
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
    sub_process_std_err = sub_process_result.stderr.decode('utf-8')
    # print("sub_process_std_out", sub_process_std_out)
    # print("sub_process_std_err", sub_process_std_err)
    return 'No such file or directory' not in sub_process_std_err


def drive_full(drive_number: int) -> bool:
    sub_process_result = subprocess.run(['setcd', '-i', f"/dev/sr{drive_number}"],
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
    sub_process_std_out = sub_process_result.stdout.decode('utf-8', errors="ignore")
    return 'Disc found in drive' in sub_process_std_out


def drive_ready(drive_number: int) -> bool:
    try:
        sub_process_result = subprocess.run(['setcd', '-i', f"/dev/sr{drive_number}"],
                                            stdout=subprocess.PIPE,
                                            stderr=subprocess.PIPE)
        sub_process_std_out = sub_process_result.stdout.decode('utf-8', errors="ignore")
        return 'Drive is not ready' not in sub_process_std_out
    except Exception as e:
        print(e)
        return False


def drive_open(drive_number: int) -> bool:
    sub_process_result = subprocess.run(['setcd', '-i', f"/dev/sr{drive_number}"],
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
    sub_process_std_out = sub_process_result.stdout.decode('utf-8')
    return 'tray is open' in sub_process_std_out


def wait_on_closed_drive(drive_number: int):
    waiting = 1
    while drive_open(drive_number):
        waiting += 1
        print(f"\rdrive /dev/sr{drive_number} is open, waiting for you to close it with a disc inserted. ", end="")
        spinner = "←↖↑↗→↘↓↙"
        print(spinner[waiting % len(spinner)], end="\r")
    sys.stdout.write("\033[K")  # Clear to the end of line


def wait_on_ready_drive(drive_number: int):
    waiting = 1
    while not drive_ready(drive_number):
        waiting += 1
        print(f"\rdrive /dev/sr{drive_number} is not ready, waiting for it to be ready. ", end="")
        spinner = "←↖↑↗→↘↓↙"
        print(spinner[waiting % len(spinner)], end="\r")
    sys.stdout.write("\033[K")  # Clear to the end of line


def get_dvd_label(drive_number: int) -> str:
    sub_process_result = subprocess.run(["blkid", "-o", "value", "-s", "LABEL", f"/dev/sr{drive_number}"],
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
    sub_process_std_out = sub_process_result.stdout.decode('utf-8', 'ignore')
    return sub_process_std_out.replace("_", " ").replace("\n", "").lower()
