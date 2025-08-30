import logging

from transcode_tycoon.models.users import UserInfo, Leaderboard, LeaderboardUser
from transcode_tycoon.game_logic import game_logic, ItemNotFoundError

from fastapi import APIRouter, HTTPException


logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/users",
    tags=["Users"],
    responses={404: {"description": "Not found"}},
)


@router.get("/")
async def get_user_info(user_id: str) -> UserInfo:
    '''
    Returns your user information including your user ID, completed jobs, and total funds.
    '''
    try:
        user = game_logic.get_user(user_id)
    except ItemNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    return user


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


@router.post('/register')
async def register_user() -> UserInfo:
    '''
    Registers a new user and returns a unique user ID.
    '''
    user = game_logic.create_user()
    logger.info(f"Registered new user with ID {user.user_id}")
    return user
