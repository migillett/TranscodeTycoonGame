from transcode_tycoon.game_logic import game_logic
from transcode_tycoon.models.users import UserInfo

from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserInfo:
    """Dependency to validate API token"""
    token = credentials.credentials
    user_id = game_logic.hash_token_to_user_id(token)
    if user_id not in game_logic.users.keys():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return game_logic.users[user_id]
