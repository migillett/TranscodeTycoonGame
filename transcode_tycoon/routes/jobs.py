import logging
from typing import Optional
from datetime import timedelta

from transcode_tycoon.models.jobs import JobInfo, JobStatus, JobInfoQueued
from transcode_tycoon.models.users import UserInfo
from transcode_tycoon.game_logic import game_logic, ItemNotFoundError, InsufficientResources
from transcode_tycoon.utils.auth import get_current_user

from fastapi import APIRouter, HTTPException, status, Depends


logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Not found"}},
)


@router.get("/")
async def list_available_jobs(job_id: Optional[str] = None) -> list[JobInfo] | JobInfo:
    '''
    Query for a specific job or all available jobs
    '''
    game_logic.create_new_jobs()
    if job_id:
        try:
            return game_logic.get_job(job_id)
        except ItemNotFoundError as e:
            raise HTTPException(
                status_code=404,
                detail=str(e)
            )
    else:
        jobs = sorted(
            (j for j in game_logic.jobs.values() if j.status == JobStatus.AVAILABLE),
            key=lambda j: j.payout,
            reverse=True
        )
        return jobs

@router.post("/claim", status_code=status.HTTP_202_ACCEPTED)
async def claim_job(job_id: str, user_info: UserInfo = Depends(get_current_user)) -> UserInfo:
    '''
    Claims a job for a user.
    '''
    try:
        game_logic.claim_job(job_id, user_info)
        game_logic.check_user_jobs(user_info)
        return user_info
    except ItemNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except InsufficientResources as e:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail=str(e)   
        )

    
@router.delete('/delete', status_code=status.HTTP_202_ACCEPTED)
async def delete_user_job(job_id: str, user_info: UserInfo = Depends(get_current_user)) -> UserInfo:
    '''
    Deletes a job from the user's queue and pushes the completion time of all other jobs up (plus a tiny time penalty).
    '''
    found_job = False
    shortened_queue: list[JobInfoQueued] = []
    offset = timedelta(seconds=0)

    for job in user_info.job_queue:
        if job.job_id == job_id:
            found_job = True
            offset = timedelta(seconds=job.render_time_seconds + 5)
        else:
            job.estimated_completion_ts -= offset
            shortened_queue.append(job)
    
    if not found_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Unable to find a job with ID {job_id} in user job queue.')
    user_info.job_queue = shortened_queue
    game_logic.check_user_jobs(user_info)
    return user_info
