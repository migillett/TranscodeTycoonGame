from enum import StrEnum

from pydantic import BaseModel, Field, computed_field


class HardwareStats(BaseModel):
    current_level: int = 1
    value: float
    unit: str # GHz, Cores, GB
    upgrade_increment: float # what the next value will be
    upgrade_price: float = 50.0

    def upgrade(self) -> None:
        self.current_level += 1
        self.value += self.upgrade_increment
        self.upgrade_price = round(
            50.0 * ((self.upgrade_increment * 1.1) ** self.current_level), 2)

class HardwareType(StrEnum):
    CPU_CORES = "CPU_CORES"
    CLOCK_SPEED = "CLOCK_SPEED"
    RAM = "RAM"
    # GPU = "GPU" # TODO - how to handle upgrades where level == 0?

class ComputerInfo(BaseModel):
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
