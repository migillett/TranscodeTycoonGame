import pytest
from datetime import datetime, timedelta

from transcode_tycoon.game_logic import TranscodeTycoonGameLogic, InsufficientResources
from transcode_tycoon.models.computer import HardwareType


### CORE FUNCTIONS ###
def test_game_logic():
    print('=== TESTING GAME LOGIC ===')

    game_logic_core = TranscodeTycoonGameLogic(disable_backups=True)

    assert len(game_logic_core.jobs) == 0
    assert len(game_logic_core.users) == 0

    game_logic_core.create_user()
    assert len(game_logic_core.users) == 1
    print(f'Successfully created user')

    game_logic_core.create_new_jobs()
    assert len(game_logic_core.jobs) == game_logic_core.job_capacity
    print(f'Successfully created job board with capacity: {game_logic_core.job_capacity}')

    for job_id in game_logic_core.jobs:
        assert game_logic_core.get_job(job_id).job_id == job_id

    game_logic_core.purge_available_jobs()
    assert len(game_logic_core.jobs) == 0
    
    print('=== GAME LOGIC TESTS PASSED ===')


### UPGRADES ###
def test_upgrades():
    print('=== TESTING UPGRADES FUNCTIONS ===')

    game_logic_upgrades = TranscodeTycoonGameLogic(disable_backups=True)

    test_upgrade_user = game_logic_upgrades.create_user().user_info
    for upgrade_type in HardwareType:
        initial_wallet_value = test_upgrade_user.funds
        purchase_price = test_upgrade_user.computer.hardware[upgrade_type].upgrade_price

        # all upgrades at this point should be level 1
        assert test_upgrade_user.computer.hardware[upgrade_type].current_level == 1

        game_logic_upgrades.purchase_upgrade(
            user_info=test_upgrade_user,
            upgrade_type=upgrade_type
        )
        assert test_upgrade_user.computer.hardware[upgrade_type].current_level == 2
        assert test_upgrade_user.funds == (initial_wallet_value - purchase_price)

        print(f'Successfully upgraded: {upgrade_type}')

    # attempt to purchase another upgrade but should throw error
    with pytest.raises(InsufficientResources):
        game_logic_upgrades.purchase_upgrade(
            user_info=test_upgrade_user,
            upgrade_type=HardwareType.CPU_CORES
        )
    print('Game logic raised correct insufficient funds error')

    print('=== UPGRADES TESTS PASSED ===')

### JOBS ###
def test_jobs():
    print('=== TESTING JOB FUNCTIONS ===')

    game_logic_jobs = TranscodeTycoonGameLogic(disable_backups=True)

    test_job_user = game_logic_jobs.create_user().user_info

    game_logic_jobs.purge_available_jobs()
    game_logic_jobs.create_new_jobs()

    max_user_jobs = int(test_job_user.computer.hardware[HardwareType.RAM].value)

    expected_payout = 0.0

    for i in range(max_user_jobs):
        # grab the last job in the list
        job_id = list(game_logic_jobs.jobs.keys())[-1]

        job_details = game_logic_jobs.get_job(job_id)
        expected_payout += job_details.payout

        game_logic_jobs.claim_job(
            job_id=job_id,
            user_info=test_job_user
        )

        # the job board should decrease when a new job is accepted
        assert len(game_logic_jobs.jobs) == game_logic_jobs.job_capacity - (i + 1)
        assert len(test_job_user.job_queue) == (i + 1)

        # setting the completion time to now - 5 minutes to trigger payout values
        test_job_user.job_queue[i].estimated_completion_ts = datetime.now() - timedelta(minutes=5)

    current_wallet = test_job_user.funds
    game_logic_jobs.check_user_jobs(test_job_user)
    assert round(test_job_user.funds, 2) == round(current_wallet + expected_payout, 2)
    assert len(test_job_user.job_queue) == 0
    assert len(test_job_user.completed_jobs) == max_user_jobs

    print('=== JOB TESTS COMPLETE ===')
