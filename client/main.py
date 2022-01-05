import argparse
import json
import platform
import re
import shlex
import socket
import subprocess
import uuid
from logging import INFO
from pathlib import Path
from time import sleep
from typing import Dict, List, Tuple

import psutil
import requests
from data_model import GPUStatus, MachineStatus
from puts import get_logger, json_serial

logger = get_logger()
logger.setLevel(INFO)

###############################################################################
## Get Argument Parser

parser = argparse.ArgumentParser()
parser.add_argument(
    "-i",
    "--interval",
    dest="interval",
    default=5,
    help="Interval in number of seconds",
)
parser.add_argument(
    "-n",
    "--name",
    dest="name",
    default="Default",
    help="Name of current machine",
)
parser.add_argument(
    "-s",
    "--server",
    dest="server",
    default="http://127.0.0.1:8000",
    help="Server address",
)

args = parser.parse_args()

# get value from parser
INTERVAL = int(args.interval)
MACHINE_NAME = str(args.name)
SERVER = str(args.server)

###############################################################################
## Constants

if SERVER.endswith("/"):
    SERVER = SERVER[:-1]
POST_URL = SERVER + "/post"
HEADERS = {"Content-type": "application/json", "Accept": "application/json"}
PUBLIC_IP: str = ""


###############################################################################
## Networks


def is_connected() -> bool:
    # https://stackoverflow.com/a/40283805
    try:
        # connect to the host -- tells us if the host is actually reachable
        socket.create_connection(("1.1.1.1", 53))
        return True
    except OSError:
        pass
    return False


def get_ip_addresses(family):
    # Ref: https://stackoverflow.com/a/43478599
    for interface, snics in psutil.net_if_addrs().items():
        for snic in snics:
            if snic.family == family:
                yield (interface, snic.address)


def get_ip() -> str:
    info = {}
    try:
        hostname = socket.gethostname()
        info["hostname"] = hostname
        info["local_ip"] = socket.gethostbyname(hostname)
        info["ipv4s"] = list(get_ip_addresses(socket.AF_INET))
        info["ipv6s"] = list(get_ip_addresses(socket.AF_INET6))
        info["public_ip"] = get_public_ip()
    except Exception as e:
        logger.error(e)
        info["error"] = str(e)
    return info


def get_public_ip() -> str:
    global PUBLIC_IP
    if not PUBLIC_IP:
        try:
            # https://www.ipify.org/
            PUBLIC_IP = requests.get("https://api64.ipify.org").content.decode("utf-8")
        except Exception as e:
            logger.error(e)

    return PUBLIC_IP


###############################################################################
## TODO


def get_temp_status():
    # linux only
    # TODO
    try:
        temp = psutil.sensors_temperatures()
        return temp
    except Exception as e:
        logger.error(e)


def get_fans_status():
    # linux only
    # TODO
    try:
        fans = psutil.sensors_fans()
        return fans
    except Exception as e:
        logger.error(e)


###############################################################################
## System


def get_sys_info() -> Dict[str, str]:
    info = {}
    try:
        info["platform"] = platform.system()
        info["platform_release"] = platform.release()
        info["platform_version"] = platform.version()
        info["architecture"] = platform.machine()
        info["mac_address"] = ":".join(re.findall("..", "%012x" % uuid.getnode()))
        info["processor"] = platform.processor()
    except Exception as e:
        logger.error(e)
        info["error"] = str(e)
    return info


###############################################################################
## CPU & RAM


def get_sys_usage() -> Dict[str, float]:
    info = {}
    try:
        info["cpu_usage"] = psutil.cpu_percent() / 100  # 0 ~ 1
        mem = psutil.virtual_memory()
        info["ram_total"] = mem.total / (1024.0 ** 2)  # MiB
        info["ram_free"] = mem.available / (1024.0 ** 2)  # MiB
        info["ram_usage"] = round(mem.percent / 100, 5)  # 0 ~ 1
    except Exception as e:
        logger.error(e)
        info["error"] = str(e)
    return info


###############################################################################
## Users


def _get_online_users() -> List[str]:
    completed_proc = subprocess.run(
        "users",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if completed_proc.returncode != 0:
        return []

    output = completed_proc.stdout.decode("utf-8").strip()
    online_users = list(set(output.split()))
    return online_users


def _get_all_users() -> List[str]:
    passwd_file = Path("/etc/passwd")
    all_users: List[str] = []

    if not passwd_file.exists():
        return []

    with passwd_file.open(mode="r") as f:
        lines = f.readlines()
        f.close()

    for line in lines:
        line = str(line).strip()
        if line:
            """
            Ref: https://askubuntu.com/a/725122

            /etc/passwd contains one line for each user account, with seven fields
            delimited by colons (“:”). These fields are:

            0 - login name
            1 - optional encrypted password
            2 - numerical user ID
            3 - numerical group ID
            4 - user name or comment field
            5 - user home directory
            6 - optional user command interpreter
            """
            user_data = line.split(":")
            username = user_data[0]
            user_id = user_data[2]
            if 1000 <= int(user_id) <= 60000:
                all_users.append(username)

    all_users = list(set(all_users))
    return all_users


def get_users_info() -> Dict[str, List[str]]:
    online_users = _get_online_users()
    all_users = _get_all_users()
    offline_users = all_users[:]
    for u in online_users:
        if u in offline_users:
            offline_users.remove(u)

    users = {
        "all_users": all_users,
        "online_users": online_users,
        "offline_users": offline_users,
    }
    return users


###############################################################################
## GPU


def get_gpu_status() -> List[GPUStatus]:
    """
    Get GPU utilization info via nvidia-smi command call
    """

    cmd = "nvidia-smi --query-gpu=index,gpu_name,utilization.gpu,temperature.gpu,memory.total,memory.used,memory.free --format=csv"
    completed_proc = subprocess.run(
        shlex.split(cmd),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if completed_proc.returncode != 0:
        return []

    output = completed_proc.stdout.decode("utf-8").strip()
    gpu_status_list: List[GPUStatus] = []
    lines = output.split("\n")
    if len(lines) <= 1:
        return []
    for row in lines[1:]:
        gpu_status = GPUStatus()
        row = row.split(",")
        if len(row) != 7:
            continue
        gpu_status.index = row[0].strip()
        gpu_status.gpu_name = row[1].strip()
        gpu_status.gpu_usage = float(row[2].strip("% ")) / 100
        gpu_status.temperature = float(row[3].strip())
        gpu_status.memory_total = float(row[4].strip(" MiB"))
        gpu_mem_used = float(row[5].strip(" MiB"))
        gpu_status.memory_free = float(row[6].strip(" MiB"))
        # compute used memory percentage
        # value returned by utilization.memory is not accurate
        gpu_status.memory_usage = round(gpu_mem_used / gpu_status.memory_total, 5)
        gpu_status_list.append(gpu_status)

    return gpu_status_list


###############################################################################
## get status


def get_status() -> MachineStatus:

    ip = get_ip()
    sys_info = get_sys_info()
    sys_usage = get_sys_usage()

    status: MachineStatus = MachineStatus()
    # Custom Machine Name
    status.name = MACHINE_NAME
    # Networks
    status.hostname = ip.get("hostname", "")
    status.local_ip = ip.get("local_ip", "")
    status.public_ip = ip.get("public_ip", "")
    status.ipv4s = ip.get("ipv4s", [])
    status.ipv6s = ip.get("ipv6s", [])
    # System
    status.architecture = sys_info.get("architecture", "")
    status.mac_address = sys_info.get("mac_address", "")
    status.platform = sys_info.get("platform", "")
    status.platform_release = sys_info.get("platform_release", "")
    status.platform_version = sys_info.get("platform_version", "")
    status.processor = sys_info.get("processor", "")
    # CPU
    status.cpu_usage = sys_usage.get("cpu_usage", "")
    # RAM
    status.ram_free = sys_usage.get("ram_free", "")
    status.ram_total = sys_usage.get("ram_total", "")
    status.ram_usage = sys_usage.get("ram_usage", "")
    # GPU
    status.gpu_status = get_gpu_status()
    # USER
    status.users_info = get_users_info()

    return status


###############################################################################
## Main


def report_to_server(status: MachineStatus) -> bool:
    status: dict = dict(status.dict())
    data: str = json.dumps(status, default=json_serial)
    r = requests.post(POST_URL, data=data, headers=HEADERS)
    if r.status_code != 201:
        logger.error(f"status_code: {r.status_code}")
        return False
    else:
        return True


def main(debug_mode: bool = False) -> None:
    retry = 0

    while True:
        sleep(INTERVAL)
        sleep(retry)

        try:
            if not is_connected():
                logger.warning("Not Connected to Internet.")
                retry += 5
                continue

            status: MachineStatus = get_status()
            if debug_mode:
                logger.info(status)
                continue

            successful = report_to_server(status)
            if successful:
                retry = 0
                print("201 OK")
            else:
                retry += 5

        except Exception as e:
            logger.error(e)
            retry += 5


if __name__ == "__main__":
    main(debug_mode=False)
