from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field, PrivateAttr


class ComputerInfo(BaseModel):
    computer_id: str = Field(default=f'comp{uuid4().hex[:8]}')
    cpu_cores: float = 2.0
    _cores_level: int = PrivateAttr(default=0)
    cpu_ghz: float = 2.0
    _clock_level: int = PrivateAttr(default=0)
    ram_gb: float = 2.0
    _ram_level: int = PrivateAttr(default=0)

    @property
    def processing_power(self) -> float:
        return self.cpu_cores * self.cpu_ghz * 10

class HardwareType(StrEnum):
    CPU_CORES = "CPU_CORES"
    CLOCK_SPEED = "CLOCK_SPEED"
    RAM = "RAM"

class UpgradePayload(BaseModel):
    upgrade_type: HardwareType
    upgrade_amount: float = 0.0

class UpgradePricing(BaseModel):
    upgrade_type: HardwareType
    current: float
    increase_amount: float
    price: float
