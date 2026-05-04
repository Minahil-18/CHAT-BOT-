from __future__ import annotations

import os
import platform
from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional


def _try_import_psutil():
    try:
        import psutil  # type: ignore

        return psutil
    except Exception:
        return None


@dataclass
class HardwareInfo:
    os: str
    os_version: str
    machine: str
    processor: str
    python_version: str
    cpu_count_logical: int
    cpu_count_physical: Optional[int]
    ram_total_gb: Optional[float]
    disk_total_gb: Optional[float]


def get_hardware_info() -> Dict[str, Any]:
    psutil = _try_import_psutil()
    cpu_count_logical = os.cpu_count() or 0
    cpu_count_physical = None
    ram_total_gb = None
    disk_total_gb = None

    if psutil is not None:
        try:
            cpu_count_physical = psutil.cpu_count(logical=False)
        except Exception:
            cpu_count_physical = None
        try:
            ram_total_gb = round(psutil.virtual_memory().total / (1024**3), 2)
        except Exception:
            ram_total_gb = None
        try:
            disk_total_gb = round(psutil.disk_usage(os.getcwd()).total / (1024**3), 2)
        except Exception:
            disk_total_gb = None

    info = HardwareInfo(
        os=platform.system(),
        os_version=platform.version(),
        machine=platform.machine(),
        processor=platform.processor(),
        python_version=platform.python_version(),
        cpu_count_logical=cpu_count_logical,
        cpu_count_physical=cpu_count_physical,
        ram_total_gb=ram_total_gb,
        disk_total_gb=disk_total_gb,
    )

    return asdict(info)
