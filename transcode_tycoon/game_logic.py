import logging
from datetime import datetime, timedelta
from uuid import uuid4
from random import choice
import json
from os import path, makedirs

from transcode_tycoon.models.users import UserInfo, CreateUserResponse, PatchUserInfo
from transcode_tycoon.models.jobs import JobInfo, JobInfoQueued, JobStatus, Format, Priority
from transcode_tycoon.models.computer import ComputerInfo, HardwareType, HardwareStats

import numpy as np
import hashlib

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
    def __init__(
            self,
            job_board_capacity: int = 25,
            initial_funds: float = 40.0,
            disable_backups: bool = False,
        ) -> None:
        
        self.job_capacity = job_board_capacity
        self.initial_funds = initial_funds
        self.disable_backups = disable_backups
        self.purge_old_job_timedelta = timedelta(hours=6)

        self.users: dict[str, UserInfo] = {}
        # TODO: create user-specific job boards to prevent pulling the same job twice
        # maybe cater them towards the user's compute capacity?
        self.jobs: dict[str, JobInfo] = {}

        self.json_backup = path.join(
            path.dirname(path.abspath(__file__)),
            'data', 'tycoon_state.json'
        )

        self.__load_state__()

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
        # in megabits per second
        return round(pps / 1_000_000, 2)
    
    def __dump_state__(self) -> None:
        if not path.exists(path.dirname(self.json_backup)):
            makedirs(path.dirname(self.json_backup))

        if not self.disable_backups:
            with open(self.json_backup, 'w') as json_file:
                user_dump = {
                    k: v.model_dump(mode='json') for k, v in self.users.items()
                }
                json.dump(user_dump, json_file, indent=2)
                logger.info(f'Dumped users to: {self.json_backup}')

    def __load_state__(self) -> None:
        if path.exists(self.json_backup) and not self.disable_backups:
            with open(self.json_backup, 'r') as json_file:
                user_load = json.load(json_file)
                self.users = {
                    k: UserInfo.model_validate(v) for k, v in user_load.items()
                }
                logger.info(f'Successfully loaded JSON backup file: {self.json_backup}')
        else:
            logger.info(f'Unable to load previous user state. File does not exist.')

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
    
    def create_new_computer(self) -> ComputerInfo:
        cpu_cores = HardwareStats(
            value=2.0,
            unit='Cores',
            upgrade_increment=2.0,
        )

        ram = HardwareStats(
            value=2.0,
            unit='GB',
            upgrade_increment=1.0,
        )

        clock_speed = HardwareStats(
            value=2.0,
            unit='GHz',
            upgrade_increment=1.0,
        )

        comp = ComputerInfo(
            hardware={
                HardwareType.CPU_CORES: cpu_cores,
                HardwareType.RAM: ram,
                HardwareType.CLOCK_SPEED:clock_speed
            }
        )
        return comp
    
    def starter_gpu(self) -> HardwareStats:
        return HardwareStats(
            current_level=1,
            value=50.0,
            unit='H.264 Accelerators',
            upgrade_increment=50.0,
            upgrade_price=250.0,
        )

    def purchase_upgrade(self, user_info: UserInfo, upgrade_type: HardwareType) -> UserInfo:
        existing_hardware = True
        if upgrade_type == HardwareType.GPU and HardwareType.GPU not in user_info.computer.hardware:
            # GPUS aren't included in the default computers, so we can't upgrade an existing item
            hardware_stat = self.starter_gpu()
            existing_hardware = False
        else:
            hardware_stat = user_info.computer.hardware[upgrade_type]

        if hardware_stat.upgrade_price > user_info.funds:
            raise InsufficientResources(
                f"You lack enough funds to purchase a {upgrade_type} upgrade. Price: ${hardware_stat.upgrade_price} | Funds: ${user_info.funds}"
            )
        
        user_info.funds -= hardware_stat.upgrade_price
        logger.info(f'User {user_info.user_id} purchased {upgrade_type} upgrade for {hardware_stat.upgrade_price}.')
        if existing_hardware:
            hardware_stat.upgrade()
        else:
            user_info.computer.hardware[upgrade_type] = hardware_stat
        return user_info
        
    ### USERS ###
    def get_user(self, user_id: str) -> UserInfo:
        user_info = self.users.get(user_id)
        if not user_info:
            raise ItemNotFoundError(f"User with ID {user_id} not found.")
        self.check_user_jobs(user_info=user_info)
        return user_info
    
    def hash_token_to_user_id(self, user_token: str) -> str:
        return f'usr{hashlib.sha256(user_token.encode()).hexdigest()[:10]}'

    def create_user(self) -> CreateUserResponse:
        '''
        Creates a new user and a basic computer to get you started.

        Be sure to save your `token` as you'll need this for all future requests.
        '''
        user_token = str(uuid4())

        user_id = self.hash_token_to_user_id(user_token)
        user = UserInfo(
            user_id=user_id,
            funds=self.initial_funds,
            computer=self.create_new_computer()
        )
        self.users[user_id] = user
        logger.info(f'Created new user: {user.user_id}')
        response = CreateUserResponse(
            token=user_token,
            user_info=user
        )
        return response
    
    def update_user(self, user_info: UserInfo, user_update: PatchUserInfo) -> UserInfo:
        update_payload = user_update.model_dump(mode='json', exclude_none=True)
        logger.info(f'Updating user {user_info.user_id} with payload: {update_payload}')
        for k, v in update_payload.items():
            user_info.__setattr__(k, v)
        return self.get_user(user_info.user_id)

    ### JOBS ###
    def prune_available_jobs(self, cutoff_timestamp: datetime | None = None) -> None:
        '''
        deletes all jobs where the creation timestamp is <= cutoff timestamp
        '''
        if cutoff_timestamp is None:
            cutoff_timestamp = datetime.now() - self.purge_old_job_timedelta
        # drop jobs older than 6 hours ago
        pruned_jobs = {}
        for k, v in self.jobs.items():
            if v._creation_ts > cutoff_timestamp:
                pruned_jobs[k] = v
        logger.info(f'Dropping {len(self.jobs) - len(pruned_jobs)} old jobs from the board')
        self.jobs = pruned_jobs

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
        for job_index, job in enumerate(user_info.job_queue):
            if job_index == 0:
                job.status = JobStatus.IN_PROGRESS
            else:
                job.status = JobStatus.QUEUED
        self.__dump_state__()

    def __left_weighted_trt__(self, min_value: int = 30, max_value: int = 7200) -> float:
        alpha, beta = 1, 6
        beta_samples = np.random.beta(alpha, beta, 1)
        scaled_samples = min_value + beta_samples * (max_value - min_value)
        return round(scaled_samples[0], 1)

    def generate_random_job(self) -> JobInfo:
        job_id = f'ren{uuid4().hex[:8]}'
        job = JobInfo(
            job_id=job_id,
            status=JobStatus.AVAILABLE,
            total_run_time=self.__left_weighted_trt__(),
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

    def claim_job(self, job_id: str, user_info: UserInfo) -> None:
        # RAM in GB is the maximum number of jobs allowed in the queue
        if len(user_info.job_queue) >= user_info.computer.hardware[HardwareType.RAM].value:
            raise InsufficientResources(
                f'Not enough available RAM to queue another render job.')
        
        try:
            job = self.jobs.pop(job_id)
        except KeyError:
            raise ItemNotFoundError(f'Job ID not found or has already been claimed: {job_id}')

        estimated_render_time = self.__calculate_completion_timedelta__(
            job_info=job,
            computer_info=user_info.computer)
        if len(user_info.job_queue) == 0:
            job.status = JobStatus.IN_PROGRESS
            job_completion_ts = datetime.now() + timedelta(seconds=estimated_render_time)
        else:
            job.status = JobStatus.QUEUED
            job_completion_ts = user_info.job_queue[-1].estimated_completion_ts + timedelta(seconds=estimated_render_time)
        queued_job = JobInfoQueued(
            **job.model_dump(),
            estimated_completion_ts=job_completion_ts,
            render_time_seconds=estimated_render_time,
        )
        user_info.job_queue.append(queued_job)
        logger.debug(f"User {user_info.user_id} registered job {queued_job.job_id}")


game_logic = TranscodeTycoonGameLogic()
