from typing import Optional

from transcode_tycoon.models.jobs import JobInfoQueued
from transcode_tycoon.models.computer import ComputerInfo

from pydantic import BaseModel


class UserInfo(BaseModel):
    user_id: str
    username: Optional[str] = ''
    completed_jobs: list[JobInfoQueued] = []
    job_queue: list[JobInfoQueued] = []
    funds: float
    computer: ComputerInfo = ComputerInfo()

class PatchUserInfo(BaseModel):
    username: Optional[str] = None

class LeaderboardUser(BaseModel):
    rank: Optional[int] = None
    user_id: str
    username: Optional[str] = ''
    completed_jobs: int
    processing_power: float
    funds: float


class Leaderboard(BaseModel):
    total: int
    start: int = 0
    users: list[LeaderboardUser]

class CreateUserResponse(BaseModel):
    token: str
    user_info: UserInfo
