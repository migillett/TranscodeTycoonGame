from uuid import uuid4

from transcode_tycoon.models.jobs import JobInfoQueued
from transcode_tycoon.models.computer import ComputerInfo

from pydantic import BaseModel, Field


class UserInfo(BaseModel):
    user_id: str = Field(default=f'usr{uuid4().hex[:8]}')
    completed_jobs: list[JobInfoQueued] = []
    job_queue: list[JobInfoQueued] = []
    funds: float = 0.0
    computer: ComputerInfo = ComputerInfo()


class LeaderboardUser(BaseModel):
    rank: int
    user_id: str
    completed_jobs: int
    funds: float


class Leaderboard(BaseModel):
    total: int
    start: int = 0
    users: list[LeaderboardUser]