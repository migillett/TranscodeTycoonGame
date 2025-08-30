import logging
from typing import Optional

from transcode_tycoon.models.jobs import JobInfo
from transcode_tycoon.models.computer import HardwareType, HardwareStats
from transcode_tycoon.models.users import UserInfo
from transcode_tycoon.game_logic import game_logic, ItemNotFoundError, InsufficientResources

from fastapi import APIRouter, HTTPException, status


logger = logging.getLogger(__name__)


job_data: dict[str, JobInfo] = {}


router = APIRouter(
    prefix="/upgrades",
    tags=["Upgrades"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Not found"}},
)

@router.post('/purchase')
async def upgrade_computer(user_id: str, upgrade_type: HardwareType) -> UserInfo:
    try:
        user_info = game_logic.get_user(user_id)
        return game_logic.purchase_upgrade(
            user_info=user_info,
            upgrade_type=upgrade_type
        )
    except ItemNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except InsufficientResources as e:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=str(e)
        )

@router.get('/list')
async def get_available_upgrades(user_id: str) -> dict[HardwareType, HardwareStats]:
    try:
        return game_logic.get_user(user_id).computer.hardware
    except ItemNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
