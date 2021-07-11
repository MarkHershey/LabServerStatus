import argparse
import csv
import platform
import re
import shlex
import socket
import subprocess
import uuid
from datetime import datetime
from logging import INFO
from pathlib import Path
from time import sleep
from typing import Dict, List, Tuple

import psutil
import requests
from puts.logger import logger
from pydantic import BaseModel

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
args = parser.parse_args()

###############################################################################
## Constants

SERVER = "server-stat.markhh.com"
POST_URL = "https://" + SERVER + "/post"
HEADERS = {"Content-type": "application/json", "Accept": "application/json"}

# get value from parser
INTERVAL = int(args.interval)
MACHINE_NAME = str(args.name)

PUBLIC_IP: str = ""

###############################################################################
## Model


class ServerStatus(BaseModel):
    name: str = MACHINE_NAME
    # ip
    hostname: str = None
    local_ip: str = None
    public_ip: str = None
    ipv4s: List[Tuple[str, str]] = None
    ipv6s: List[Tuple[str, str]] = None
    # sys info
    architecture: str = None
    mac_address: str = None
    platform: str = None
    platform_release: str = None
    platform_version: str = None
    processor: str = None
    # sys usage
    cpu_usage: str = None
    ram_available: str = None
    ram_installed: str = None
    ram_usage: str = None
    # gpu usage
    gpu_status: dict = None


###############################################################################
## Helpers


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


def get_sys_info() -> Dict[str, str]:
    info = {}
    try:
        info["platform"] = platform.system()
        info["platform_release"] = platform.release()
        info["platform_version"] = platform.version()
        info["architecture"] = platform.machine()
        info["mac_address"] = ":".join(re.findall("..", "%012x" % uuid.getnode()))
        info["processor"] = platform.processor()
        info["ram_installed"] = (
            str(round(psutil.virtual_memory().total / (1024.0 ** 3))) + " GB"
        )
    except Exception as e:
        logger.error(e)
        info["error"] = str(e)
    return info


def get_sys_usage() -> Dict[str, str]:
    info = {}
    try:
        mem = psutil.virtual_memory()
        info["ram_installed"] = str(round(mem.total / (1024.0 ** 3))) + " GB"
        info["ram_available"] = str(round(mem.available / (1024.0 ** 3))) + " GB"
        info["ram_usage"] = str(round(mem.percent)) + "%"
        info["cpu_usage"] = str(round(psutil.cpu_percent())) + "%"
    except Exception as e:
        logger.error(e)
        info["error"] = str(e)
    return info


def get_gpu_status() -> List[Dict[str, str]]:
    tmp_file = Path("tmp_nvidia-smi_output.txt")
    cmd = "nvidia-smi --query-gpu=index,gpu_name,utilization.gpu,temperature.gpu,memory.total,memory.used,memory.free --format=csv"
    with tmp_file.open(mode="w") as tmp_out:
        subprocess.run(
            shlex.split(cmd),
            stdout=tmp_out,
        )
        tmp_out.close()

    sleep(0.2)
    gpu_info = []

    with open(str(tmp_file), newline="") as csvfile:
        reader = csv.DictReader(csvfile, delimiter=",")
        for row in reader:
            single_gpu_info = {}
            for key, value in row.items():
                if "index" in key:
                    single_gpu_info["index"] = value.strip()
                elif "name" in key:
                    single_gpu_info["gpu_name"] = value.strip()
                elif "utilization.gpu" in key:
                    single_gpu_info["gpu_usage"] = value.strip("% ") + "%"
                elif "temperature.gpu" in key:
                    single_gpu_info["temperature"] = value.strip() + "°C"
                elif "memory.total" in key:
                    gpu_mem_total = float(value.strip(" MiB"))
                    gpu_mem_total_str = str(round(gpu_mem_total / 1024, 1)) + " GiB"
                    single_gpu_info["memory_total"] = gpu_mem_total_str
                elif "memory.used" in key:
                    gpu_mem_used = float(value.strip(" MiB"))
                elif "memory.free" in key:
                    gpu_mem_free = float(value.strip(" MiB"))
                    gpu_mem_free_str = str(round(gpu_mem_free / 1024, 1)) + " GiB"
                    single_gpu_info["memory_free"] = gpu_mem_free_str

            # compute used memory percentage
            # value returned by utilization.memory is not accurate
            used_percent = round((gpu_mem_used / gpu_mem_total) * 100)
            single_gpu_info["memory_usage"] = str(used_percent) + "%"

            gpu_info.append(single_gpu_info)

        # close file
        csvfile.close()

    return gpu_info


def get_status() -> ServerStatus:

    ip = get_ip()
    sys_info = get_sys_info()
    sys_usage = get_sys_usage()
    gpu_status = get_gpu_status()
    timestamp = datetime.now()
    logger.debug(f"Now: {timestamp}")

    server_status_info: ServerStatus = ServerStatus()

    server_status_info.hostname = ip.get("hostname", "")
    server_status_info.local_ip = ip.get("local_ip", "")
    server_status_info.public_ip = ip.get("public_ip", "")
    server_status_info.ipv4s = ip.get("ipv4s", [])
    server_status_info.ipv6s = ip.get("ipv6s", [])
    server_status_info.architecture = sys_info.get("architecture", "")
    server_status_info.mac_address = sys_info.get("mac_address", "")
    server_status_info.platform = sys_info.get("platform", "")
    server_status_info.platform_release = sys_info.get("platform_release", "")
    server_status_info.platform_version = sys_info.get("platform_version", "")
    server_status_info.processor = sys_info.get("processor", "")
    server_status_info.cpu_usage = sys_usage.get("cpu_usage", "")
    server_status_info.ram_available = sys_usage.get("ram_available", "")
    server_status_info.ram_installed = sys_usage.get("ram_installed", "")
    server_status_info.ram_usage = sys_usage.get("ram_usage", "")
    server_status_info.gpu_status = gpu_status

    return server_status_info


###############################################################################
## Main


def main():

    while True:
        sleep(INTERVAL)
        try:
            if not is_connected():
                logger.warning("Not Connected to Internet.")
                continue

            status: ServerStatus = get_status()
            status = dict(status.dict())

            r = requests.post(POST_URL, json=status, headers=HEADERS)
            if r.status_code != 201:
                logger.error(f"status_code: {r.status_code}")
                print(r.text)
                print(r)
            else:
                print("201 OK")
        except Exception as e:
            logger.exception(e)


if __name__ == "__main__":
    main()
