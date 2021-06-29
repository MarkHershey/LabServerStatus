import os
import sys
from datetime import datetime
from logging import INFO
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from puts.logger import logger
from pydantic import BaseModel, validator

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


DATA_CACHE = {
    "Default": {},
    "2080Ti x4 Workstation": {},
    "2080Ti x1 Workstation": {},
    "3090 x3 Workstation": {},
}

###############################################################################
## Model


class ServerStatus(BaseModel):
    created_at: datetime = None
    name: str = None
    # ip
    hostname: str = None
    local_ip: str = None
    public_ip: str = None
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

    @validator("created_at", pre=True, always=True)
    def default_created_at(cls, v):
        return v or datetime.now()


###############################################################################
## ENDPOINTS


@app.get("/")
async def read_root():
    return {"Hello": "World"}


@app.post("/post", status_code=201)
async def post_status(status: ServerStatus):
    global DATA_CACHE

    if status.name in DATA_CACHE:
        DATA_CACHE[status.name] = dict(status.dict())
        return {"msg": "OK"}
    else:
        raise HTTPException(status_code=401)


@app.post("/get")
async def get_status():
    return DATA_CACHE
