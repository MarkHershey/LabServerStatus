from datetime import datetime
from typing import Dict, List, Tuple

from pydantic import BaseModel, validator

from .helpers import mask_sensitive_string

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

#     @validator("users_info", pre=True, always=True)
#     def process_users_info(cls, v):
#         if isinstance(v, dict):
#             for keys in v.keys():
#                 v[keys] = [mask_sensitive_string(user) for user in v[keys]]
#             return v
#         else:
#             return v


class GPUStatus(BaseModel):
    index: int = None
    gpu_name: str = None
    gpu_usage: float = None  # range: [0, 1]
    temperature: float = None  # Celsius
    memory_free: float = None  # MB
    memory_total: float = None  # MB
    memory_usage: float = None  # range: [0, 1]


class GPUComputeProcess(BaseModel):
    pid: int = None
    user: str = None
    gpu_uuid: str = None
    gpu_index: int = None
    gpu_mem_used: float = None  # MB
    gpu_mem_usage: float = None  # range: [0, 1]
    cpu_usage: float = None  # range: [0, 1]
    cpu_mem_usage: float = None  # range: [0, 1]
    proc_uptime: float = None  # seconds
    proc_uptime_str: str = None  # HH:MM:SS
    command: str = None


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
    uptime: float = None  # seconds
    uptime_str: str = None
    # sys usage
    cpu_model: str = None
    cpu_cores: int = None
    cpu_usage: float = None  # range: [0, 1]
    ram_free: float = None  # MB
    ram_total: float = None  # MB
    ram_usage: float = None  # range: [0, 1]
    # gpu usage
    gpu_status: List[GPUStatus] = None
    gpu_compute_processes: List[GPUComputeProcess] = None
    # users info
    users_info: Dict[str, List[str]] = None

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
