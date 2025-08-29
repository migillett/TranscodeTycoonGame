import logging
from datetime import datetime, timedelta
from uuid import uuid4
from random import choice, randint

from transcode_tycoon.models.users import UserInfo
from transcode_tycoon.models.jobs import JobInfo, JobInfoQueued, JobStatus, Format, Priority
from transcode_tycoon.models.computer import ComputerInfo, UpgradePayload, UpgradeType


class ItemNotFoundError(Exception):
    pass

class NoJobsInQueueError(Exception):
    pass

class UnsupportedFormatError(Exception):
    pass

class ComputerUpgradeError(Exception):
    pass

class InsufficientResources(Exception):
    pass


logger = logging.getLogger(__name__)


class TranscodeTycoonGameLogic:
    # TODO - replace with an actual database like SQLite
    def __init__(self, job_board_capacity: int = 10):
        self.users: dict[str, UserInfo] = {}
        self.jobs: dict[str, JobInfo] = {}
        self.job_capacity = job_board_capacity

    ### UTILITIES ###
    def __calculate_render_difficulty__(self, job_info: JobInfo) -> float:
        match job_info.format:
            case Format.SD:
                pixels = 720 * 480
            case Format.HD:
                pixels = 1280 * 720
            case Format.FHD:
                pixels = 1920 * 1080
            case Format.UHD:
                pixels = 3840 * 2160
            case _:
                raise UnsupportedFormatError(f"Unsupported format: {job_info.format}")
        # assuming 30 fps
        pps = (pixels * 30) * job_info.total_run_time
        # in millions of pixels
        return round(pps / 1_000_000, 2)

    ### COMPUTERS ###
    def __calculate_completion_timedelta__(self, job_info: JobInfo, computer_info: ComputerInfo) -> float:
        '''
        Takes the job info and user's computer info to calculate the expected completion float in seconds.
        '''
        # example:
        # SD video at 2 minutes = 1,244.16 million pixels
        # 2 CPUs * 2.0 GHz * 10 = 40.0 compute score
        # 1244.16 mill pix / 40.0 compute score = 31.104 seconds processing time
        difficulty = self.__calculate_render_difficulty__(job_info)
        return round(difficulty / computer_info.processing_power, 4)
    
    def upgrade_computer(self, user_id: str, upgrade_payload: UpgradePayload) -> UserInfo:
        user_info = self.users.get(user_id)
        if not user_info:
            raise ItemNotFoundError(f"User with ID {user_id} not found.")
        
        if len(user_info.job_queue) > 0:
            raise ComputerUpgradeError('Unable to upgrade computer while jobs are in queue')
        
        logger.info(f'Upgrading user computer: {upgrade_payload.model_dump()}')
        match upgrade_payload.upgrade_type:
            case UpgradeType.CPU_CORES:
                user_info.computer.cpu_cores += int(upgrade_payload.upgrade_amount)
            case UpgradeType.CLOCK_SPEED:
                user_info.computer.cpu_ghz += upgrade_payload.upgrade_amount
            case UpgradeType.RAM:
                user_info.computer.ram_gb += int(upgrade_payload.upgrade_amount)
        
        return user_info
        
    ### USERS ###
    def get_user(self, user_id: str) -> UserInfo:
        user_info = self.users.get(user_id)
        if not user_info:
            raise ItemNotFoundError(f"User with ID {user_id} not found.")
        self.check_user_jobs(user_info=user_info)
        return user_info
    
    def add_user(self, user_info: UserInfo) -> None:
        self.users[user_info.user_id] = user_info
    
    ### JOBS ###
    def purge_available_jobs(self) -> None:
        self.jobs = {}

    def check_user_jobs(self, user_info: UserInfo) -> None:
        '''
        Iterates through the user's job queue and checks for completed tasks
        '''
        for job in user_info.job_queue:
            if job.estimated_completion_ts < datetime.now():
                job.status = JobStatus.COMPLETED
                user_info.completed_jobs.append(job)
                user_info.funds += job.payout
                logger.info(f'{job.job_id} marked complete. Payout: ${job.payout}')
        # remove completed jobs from queue
        user_info.job_queue = [
            j for j in user_info.job_queue
            if j.status != JobStatus.COMPLETED
        ]

    def generate_random_job(self) -> JobInfo:
        job_id = f'ren{uuid4().hex[:8]}'
        job = JobInfo(
            job_id=job_id,
            status=JobStatus.AVAILABLE,
            total_run_time=randint(600, 7200),  # between 10 minutes and 2 hours
            priority=choice(list(Priority)),
            format=choice(list(Format))
        )
        return job
    
    def create_new_jobs(self) -> None:
        available_capacity = self.job_capacity - len(self.jobs)
        if available_capacity > 0:
            for _ in range(available_capacity):
                new_job = self.generate_random_job()
                self.add_job(new_job)
            logger.info(f'Generated {available_capacity} new jobs.')
        else:
            logger.info(f'No new jobs created. Job board at maximum capacity.')

    def get_job(self, job_id: str) -> JobInfo:
        job = self.jobs.get(job_id)
        if not job:
            raise ItemNotFoundError(f"Job with ID {job_id} not found or has already been claimed.")
        return job
        
    def add_job(self, job_data: JobInfo) -> None:
        self.jobs[job_data.job_id] = job_data
        logger.debug(f"Added job with ID {job_data.job_id}")

    def register_job(self, job_id: str, user_id: str) -> None:
        user = self.get_user(user_id)

        # RAM in GB is the maximum number of jobs allowed in the queue
        if len(user.job_queue) >= user.computer.ram_gb:
            raise InsufficientResources(
                f'Not enough available RAM to queue another render job.')

        try:
            job = self.jobs.pop(job_id)
        except KeyError:
            raise ItemNotFoundError(f'Job ID not found or has already been claimed: {job_id}')

        estimated_render_time = self.__calculate_completion_timedelta__(
            job_info=job,
            computer_info=user.computer)
        if len(user.job_queue) == 0:
            job.status = JobStatus.IN_PROGRESS
            job_completion_ts = datetime.now() + timedelta(seconds=estimated_render_time)
        else:
            job.status = JobStatus.QUEUED
            job_completion_ts = user.job_queue[-1].estimated_completion_ts + timedelta(seconds=estimated_render_time)
        queued_job = JobInfoQueued(
            **job.model_dump(),
            estimated_completion_ts=job_completion_ts)
        user.job_queue.append(queued_job)
        logger.debug(f"User {user_id} registered job {queued_job.job_id}")


game_logic = TranscodeTycoonGameLogic()
