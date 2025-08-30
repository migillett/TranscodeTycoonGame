
from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, computed_field, Field
from enum import StrEnum


class JobStatus(StrEnum):
    AVAILABLE = "available"
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class Format(StrEnum):
    UHD = "UHD" # 4K
    FHD = "FHD" # 1080p
    HD = "HD"   # 720p
    SD = "SD"   # 480p


class Priority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class JobInfo(BaseModel):
    job_id: str = Field(default=f'rend{uuid4().hex[:8]}')
    status: JobStatus
    priority: Priority = Priority.LOW
    total_run_time: float  # in seconds
    format: Format

    @computed_field
    @property
    def payout(self) -> float:
        # base rate $ per minute of video
        base_rate = {
            Format.UHD: 10.0,
            Format.FHD: 5.0,
            Format.HD: 2.5,
            Format.SD: 1.0
        }[self.format]

        priority_multiplier = {
            Priority.LOW: 1.0,
            Priority.MEDIUM: 1.5,
            Priority.HIGH: 2.0
        }[self.priority]

        return round(base_rate * priority_multiplier * (self.total_run_time / 60), 2)


class JobInfoQueued(JobInfo):
    estimated_completion_ts: datetime
    render_time_seconds: float
