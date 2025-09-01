from typing import Optional

from transcode_tycoon.models.jobs import JobInfoQueued
from transcode_tycoon.models.computer import ComputerInfo

from pydantic import BaseModel, Field, computed_field


class UserInfo(BaseModel):
    user_id: str
    username: Optional[str] = Field(max_length=50, default='')
    completed_jobs: list[JobInfoQueued] = []
    job_queue: list[JobInfoQueued] = []
    funds: float = 0.0
    computer: ComputerInfo = ComputerInfo()

    @computed_field
    @property
    def total_revenue(self) -> float:
        return round(sum(j.payout for j in self.completed_jobs), 2)

class PatchUserInfo(BaseModel):
    username: Optional[str] = Field(max_length=50, default='')

class LeaderboardUser(BaseModel):
    rank: Optional[int] = None
    user_id: str
    username: Optional[str] = ''
    completed_jobs: int
    processing_power: float
    funds: float
    total_revenue: float


class Leaderboard(BaseModel):
    total: int
    start: int = 0
    users: list[LeaderboardUser]

class CreateUserResponse(BaseModel):
    token: str
    user_info: UserInfo
