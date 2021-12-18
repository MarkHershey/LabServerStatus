import os
import sys
from datetime import datetime
from logging import INFO
from typing import Dict, List, Optional, Tuple

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from puts import get_logger

from .data_model import MachineStatus

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
## ENDPOINTS


@app.get("/")
async def read_root():
    return {"Hello": "World"}


@app.get("/get")
async def get_status():
    return DATA_CACHE


@app.post("/reset")
async def reset_status():
    global DATA_CACHE

    for key in DATA_CACHE.keys():
        DATA_CACHE[key] = {}

    return {"msg": "OK"}


@app.post("/post", status_code=201)
async def post_status(status: MachineStatus):
    global DATA_CACHE

    if status.name in DATA_CACHE:
        DATA_CACHE[status.name] = dict(status.dict())
        return {"msg": "OK"}
    else:
        raise HTTPException(status_code=401)
