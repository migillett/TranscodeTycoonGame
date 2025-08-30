from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field, computed_field


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
    # GPU = "GPU" # TODO - how to handle upgrades where level == 0?

class ComputerInfo(BaseModel):
    computer_id: str = Field(default=f'comp{uuid4().hex[:8]}')
    hardware: dict[HardwareType, HardwareStats] = Field(default_factory=dict)

    @computed_field
    @property
    def processing_power(self) -> float:
        power = 1
        for hardware_type, stat in self.hardware.items():
            if hardware_type != HardwareType.RAM:
                # RAM is only used for job queue capacity, not how fast you can do the jobs
                power *= stat.value
        return power

class UpgradePayload(BaseModel):
    upgrade_type: HardwareType
    upgrade_amount: float = 0.0
