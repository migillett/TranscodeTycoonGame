import logging
from typing import Optional

from transcode_tycoon.models.jobs import JobInfo, JobStatus
from transcode_tycoon.game_logic import game_logic, ItemNotFoundError, InsufficientResources

from fastapi import APIRouter, HTTPException, status


logger = logging.getLogger(__name__)


job_data: dict[str, JobInfo] = {}


router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Not found"}},
)


@router.get("/")
async def list_available_jobs(job_id: Optional[str] = None, refresh: bool = False) -> list[JobInfo] | JobInfo:
    '''
    Query for a specific job or all available jobs
    '''
    if refresh:
        game_logic.purge_available_jobs()
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
async def claim_job(user_id: str, job_id: str):
    '''
    Claims a job for a user.
    '''
    try:
        game_logic.register_job(job_id, user_id)
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
