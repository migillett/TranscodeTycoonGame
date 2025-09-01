from enum import StrEnum
from typing import Optional

from pydantic import BaseModel, Field, computed_field, PrivateAttr


class HardwareStats(BaseModel):
    current_level: int = 1
    value: float
    unit: str # GHz, Cores, GB
    upgrade_increment: float # what the next value will be
    upgrade_price: float

class HardwareType(StrEnum):
    CPU_CORES = "CPU_CORES"
    CLOCK_SPEED = "CLOCK_SPEED"
    RAM = "RAM"
    GPU = "GPU"

class ComputerInfo(BaseModel):
    hardware: dict[HardwareType, HardwareStats] = Field(default_factory=dict)

    @computed_field
    @property
    def processing_power(self) -> float:
        # 1Hz == 1 pixel calculated
        # 1 core cpu * 1Ghz = 1mbps
        # 2 cores * 2Ghz = 4mbps
        power = self.hardware[HardwareType.CPU_CORES].value
        power *= self.hardware[HardwareType.CLOCK_SPEED].value
        if HardwareType.GPU in self.hardware:
            power *= self.hardware[HardwareType.GPU].value
        return power

class UpgradePayload(BaseModel):
    upgrade_type: HardwareType
    upgrade_amount: float = 0.0
