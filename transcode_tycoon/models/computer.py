from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field


class ComputerInfo(BaseModel):
    computer_id: str = Field(default=f'comp{uuid4().hex[:8]}')
    cpu_cores: int = 2
    cpu_ghz: float = 2.0
    # affects how many jobs you can queue up
    # 1 job = 1 GB of memory for the sake of simplicity
    # TODO: consider differentiating quality 
    ram_gb: int = 2

    @property
    def processing_power(self) -> float:
        return self.cpu_cores * self.cpu_ghz * 10

class UpgradeType(StrEnum):
    CPU_CORES = "CPU_CORES"
    CLOCK_SPEED = "CLOCK_SPEED"
    RAM = "RAM"

class UpgradePayload(BaseModel):
    upgrade_type: UpgradeType
    upgrade_amount: float = 0.0
