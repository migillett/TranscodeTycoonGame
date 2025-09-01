from transcode_tycoon.__main__ import app
from transcode_tycoon.game_logic import game_logic
from transcode_tycoon.models.computer import HardwareType

from fastapi.testclient import TestClient


client = TestClient(app)
game_logic.disable_backups = True


def test_api_functions():
    headers = {
        'Authorization': ''
    }

    ### ROOT ###

    response = client.get('/')
    assert response.status_code == 200
    # register a new user
    register_response = client.post('/register').json()
    headers['Authorization'] = f'Bearer {register_response["token"]}'

    ### USERS ###

    # try to get user info without headers should return error
    no_auth_response = client.get('/users/my_info')
    assert no_auth_response.status_code == 403

    # get basic user information
    user_info_base = client.get('/users/my_info', headers=headers)
    assert user_info_base.status_code == 200

    game_logic.users[user_info_base.json()['user_id']].funds += sum(
        [x['upgrade_price'] for x in user_info_base.json()['computer']['hardware'].values()]
    ) + game_logic.starter_gpu().upgrade_price

    # register another user and make sure the user id and token are different
    new_user_2 = client.post('/register').json()
    assert new_user_2['token'] != register_response['token']
    assert new_user_2['user_info']['user_id'] != register_response['user_info']['user_id']

    # make sure the user can update their information
    update_params = {'username': 'test_username'}
    update_response = client.patch('/users/my_info', headers=headers, json=update_params)
    assert update_response.status_code == 200
    assert update_response.json()['username'] == update_params['username']

    # update params payload should fail if no headers
    update_response = client.patch('/users/my_info', params=update_params)
    assert update_response.status_code == 403

    # don't allow usernames with > 50 characters
    update_response = client.patch('/users/my_info', params={'username': 'asdfgasdfgasdfgasdfgasdfgasdfgasdfgasdfgasdfgasdfgasdfg'})
    assert update_response.status_code == 403

    # leaderboard should return at least 2 users
    leaderboard_response = client.get('/users/leaderboard')
    assert leaderboard_response.status_code == 200
    assert len(leaderboard_response.json()) >= 2

    # make sure the leaderboard reponse has the username included
    successful = False
    for user in leaderboard_response.json()['users']:
        if user['user_id'] == user_info_base.json()['user_id']:
            successful = True
            assert user['username'] == update_params['username']
    assert successful == True

    # searching for a user should return proper response
    user_id = user_info_base.json()["user_id"]
    search_response = client.get(f'/users/search/{user_id}')
    assert user_id == search_response.json()['user_id']

    # searching for a nonsense user should return not found
    search_response = client.get(f'/users/search/asdfasdf')
    assert search_response.status_code == 404

    ### UPGRADES ###

    for upgrade_type in HardwareType:
        # users should have enough starting funds to buy one of each upgrade
        upgrade_response = client.post(
            '/upgrades/purchase',
            params={'upgrade_type': upgrade_type},
            headers=headers
        )
        assert upgrade_response.status_code == 200
    
    # An attempt to upgrade computer hardware without auth should throw an error
    unauth_upgrade_response = client.post(
        '/upgrades/purchase',
        params={'upgrade_type': HardwareType.CPU_CORES}
    )
    assert unauth_upgrade_response.status_code == 403

    # the user should not have enough money now for this next upgrade request
    unauth_upgrade_response = client.post(
        '/upgrades/purchase',
        params={'upgrade_type': HardwareType.CPU_CORES},
        headers=headers
    )
    assert unauth_upgrade_response.status_code == 402, print(f'{unauth_upgrade_response.json()}')

    ### JOBS ###

    # get a list of available jobs
    available_jobs = client.get('/jobs/').json()[-1]

    # attempting to claim a job without header should throw unauth error
    claim_response_no_auth = client.post(
        '/jobs/claim',
        params={'job_id': available_jobs['job_id']}
    )
    assert claim_response_no_auth.status_code == 403

    # claim the job
    claim_response = client.post(
        '/jobs/claim',
        params={'job_id': available_jobs['job_id']},
        headers=headers
    )
    assert claim_response.status_code == 202

    # attempt to claim the same job_id again should not found error
    claim_response = client.post(
        '/jobs/claim',
        params={'job_id': available_jobs['job_id']},
        headers=headers
    )
    assert claim_response.status_code == 404

    # get user info again and queued jobs should == 1
    user_queued_response = client.get(
        '/users/my_info',
        headers=headers
    )
    assert len(user_queued_response.json()['job_queue']) == 1

    # attempt to delete the claimed job without headers should return forbidden
    claim_response = client.delete(
        '/jobs/delete',
        params={'job_id': available_jobs['job_id']}
    )
    assert claim_response.status_code == 403

    # delete the claimed job
    claim_response = client.delete(
        '/jobs/delete',
        params={'job_id': available_jobs['job_id']},
        headers=headers
    )
    assert claim_response.status_code == 202

    # attempt to delete the same claimed job again should yield not found
    claim_response = client.delete(
        '/jobs/delete',
        params={'job_id': available_jobs['job_id']},
        headers=headers
    )
    assert claim_response.status_code == 404

    # get user info again and queued jobs should == 0 after deletion
    user_queued_response = client.get(
        '/users/my_info',
        headers=headers
    )
    assert len(user_queued_response.json()['job_queue']) == 0
    