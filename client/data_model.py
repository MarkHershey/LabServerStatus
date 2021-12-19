from datetime import datetime
from typing import Dict, List, Tuple

from pydantic import BaseModel, validator


# class ServerStatus(BaseModel):
#     """v1"""

#     created_at: datetime = None
#     name: str = None
#     # ip
#     hostname: str = None
#     local_ip: str = None
#     public_ip: str = None
#     ipv4s: list = None
#     ipv6s: list = None
#     # sys info
#     architecture: str = None
#     mac_address: str = None
#     platform: str = None
#     platform_release: str = None
#     platform_version: str = None
#     processor: str = None
#     # sys usage
#     cpu_usage: str = None
#     ram_available: str = None
#     ram_installed: str = None
#     ram_usage: str = None
#     # gpu usage
#     gpu_status: List[dict] = None
#     # users info
#     users_info: dict = None

#     @validator("created_at", pre=True, always=True)
#     def default_created_at(cls, v):
#         return v or datetime.now()


class GPUStatus(BaseModel):
    index: int = None
    gpu_name: str = None
    gpu_usage: float = None  # range: [0, 1]
    temperature: float = None  # Celsius
    memory_free: float = None  # MB
    memory_total: float = None  # MB
    memory_usage: float = None  # range: [0, 1]


class MachineStatus(BaseModel):
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
    cpu_usage: float = None  # range: [0, 1]
    ram_free: float = None  # MB
    ram_total: float = None  # MB
    ram_usage: float = None  # range: [0, 1]
    # gpu usage
    gpu_status: List[GPUStatus] = None
    # users info
    users_info: Dict[str, List[str]] = None

    @validator("created_at", pre=True, always=True)
    def default_created_at(cls, v):
        return v or datetime.now()
