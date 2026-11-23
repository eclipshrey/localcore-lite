from dataclasses import dataclass
import os

import psutil


@dataclass(frozen=True)
class HardwareProfile:
    total_ram_gb: float
    cpu_threads: int
    model: str
    num_ctx: int


def detect_hardware() -> HardwareProfile:
    """Detect RAM and CPU resources and select a CPU-safe Ollama profile."""
    total_ram_gb = psutil.virtual_memory().total / (1024 ** 3)
    if total_ram_gb < 10.0:
        model = "qwen3:4b"
        num_ctx = 2048
    elif total_ram_gb < 20.0:
        model = "qwen3:8b"
        num_ctx = 4096
    else:
        model = "qwen3:14b"
        num_ctx = 8192

    cpu_threads = max(2, (os.cpu_count() or 2) - 2)
    return HardwareProfile(
        total_ram_gb=round(total_ram_gb, 2),
        cpu_threads=cpu_threads,
        model=model,
        num_ctx=num_ctx,
    )
