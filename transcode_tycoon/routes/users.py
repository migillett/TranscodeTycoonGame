import logging

from transcode_tycoon.models.users import UserInfo, Leaderboard, LeaderboardUser
from transcode_tycoon.game_logic import game_logic, ItemNotFoundError
from transcode_tycoon.utils.auth import get_current_user

from fastapi import APIRouter, Depends, HTTPException, status


logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/users",
    tags=["Users"],
    responses={404: {"description": "Not found"}},
)


@router.get("/my_info")
async def get_my_user_info(user_info: UserInfo = Depends(get_current_user)) -> UserInfo:
    '''
    Returns your user information including your user ID, completed jobs, and total funds.
    '''
    game_logic.check_user_jobs(user_info)
    return user_info


@router.get('/search/{user_id}')
async def lookup_user_by_id(user_id: str) -> LeaderboardUser:
    try:
        user_info = game_logic.get_user(user_id)
        return LeaderboardUser(
            user_id=user_info.user_id,
            completed_jobs=len(user_info.completed_jobs),
            funds=user_info.funds
        )
    except ItemNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.get('/leaderboard')
async def get_leaderboard(start: int = 0, items: int = 10) -> Leaderboard:
    '''
    Returns a simple leaderboard of top users by total funds.
    '''
    if len(game_logic.users) == 0:
        return Leaderboard(total=0, users=[])
    
    for user in game_logic.users.values():
        game_logic.check_user_jobs(user)

    users_sorted = sorted(
        game_logic.users.values(),
        key=lambda u: u.funds,
        reverse=True
    )
    return Leaderboard(
        total=len(users_sorted),
        start=start,
        users=[
            LeaderboardUser(
                rank=index + 1 + start,
                user_id=user.user_id,
                completed_jobs=len(user.completed_jobs),
                funds=user.funds
            ) for index, user in enumerate(users_sorted[start:start + items])
        ]
    )
