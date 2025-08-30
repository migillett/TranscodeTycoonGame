import logging

from transcode_tycoon.models.computer import HardwareType, HardwareStats
from transcode_tycoon.models.users import UserInfo
from transcode_tycoon.game_logic import game_logic, ItemNotFoundError, InsufficientResources
from transcode_tycoon.utils.auth import get_current_user

from fastapi import APIRouter, HTTPException, status, Depends

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/upgrades",
    tags=["Upgrades"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Not found"}},
)



@router.post('/purchase')
async def upgrade_computer(upgrade_type: HardwareType, user_info: UserInfo = Depends(get_current_user)) -> UserInfo:
    try:
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
async def get_available_upgrades(user_info: UserInfo = Depends(get_current_user)) -> dict[HardwareType, HardwareStats]:
    try:
        return user_info.computer.hardware
    except ItemNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
