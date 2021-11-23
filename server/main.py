import os
import sys
from datetime import datetime
from logging import INFO
from typing import Dict, List, Tuple

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from puts import get_logger
from pydantic import BaseModel, validator

logger = get_logger()
logger.setLevel(INFO)

###############################################################################
# Constants

app = FastAPI()
origins = [
    "http://localhost",
    "http://localhost:8080",
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# print timezone and current time
print()
logger.info(f"Environ 'TZ'    : {os.environ.get('TZ', 'N.A.')}")
logger.info(f"Current Time    : {datetime.now()}")
logger.info(f"Current UTC Time: {datetime.utcnow()}")
logger.info(f"Python Version  : {sys.version}")
print()


# Client whitelist
DATA_CACHE = {
    "Default": {},
    "2080Ti x4 Workstation": {},
    "2080Ti x1 Workstation": {},
    "3090 x3 Workstation": {},
    "Workstation#1 Alan": {},
    "Workstation#2 Maurice": {},
    "Workstation#3 Richard": {},
    "Workstation#4 Marvin": {},
}

###############################################################################
## Helpers


def mask_sensitive_string(value: str) -> str:
    """
    Mask sensitive string
    """
    if value is None:
        return None

    assert isinstance(value, str)

    if len(value) == 0:
        return ""
    elif len(value) == 1:
        return "*"
    elif len(value) == 2:
        return value[0] + "*"
    elif len(value) <= 4:
        return value[0] + "*" * (len(value) - 2) + value[-1]
    else:
        return value[0:2] + "*" * (len(value) - 3) + value[-1]


###############################################################################
## Model


class ServerStatus(BaseModel):
    created_at: datetime = None
    name: str = None
    # ip
    hostname: str = None
    local_ip: str = None
    public_ip: str = None
    ipv4s: list = None
    ipv6s: list = None
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
    gpu_status: List[dict] = None
    # users info
    users_info: dict = None

    @validator("created_at", pre=True, always=True)
    def default_created_at(cls, v):
        return v or datetime.now()

    @validator("users_info", pre=True, always=True)
    def process_users_info(cls, v):
        if isinstance(v, dict):
            for keys in v.keys():
                v[keys] = [mask_sensitive_string(user) for user in v[keys]]
            return v
        else:
            return v


###############################################################################
## ENDPOINTS


@app.get("/")
async def read_root():
    return {"Hello": "World"}


@app.get("/get")
async def get_status():
    return DATA_CACHE


@app.post("/post", status_code=201)
async def post_status(status: ServerStatus):
    global DATA_CACHE

    if status.name in DATA_CACHE:
        DATA_CACHE[status.name] = dict(status.dict())
        return {"msg": "OK"}
    else:
        raise HTTPException(status_code=401)
