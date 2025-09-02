from enum import StrEnum

from pydantic import BaseModel, Field, computed_field


class MaxUpgradesReached(Exception):
    pass


class HardwareStats(BaseModel):
    current_level: int = 1
    value: float
    unit: str # GHz, Cores, GB
    upgrade_increment: float # what the next value will be
    upgrade_price: float = 50.0
    max_level: int

    def upgrade(self) -> None:
        if self.current_level + 1 > self.max_level:
            raise MaxUpgradesReached(' Maximum upgrades reached for this hardware type.')
        self.current_level += 1
        self.value += self.upgrade_increment
        self.upgrade_price = round((50 * self.current_level) + self.upgrade_price, 2)

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
        power = 1
        for value in [HardwareType.CPU_CORES, HardwareType.CLOCK_SPEED]:
            if value in self.hardware.keys():
                power *= self.hardware[value].value
        if HardwareType.GPU in self.hardware:
            power *= self.hardware[HardwareType.GPU].value
        return power

class UpgradePayload(BaseModel):
    upgrade_type: HardwareType
    upgrade_amount: float = 0.0
