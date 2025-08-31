import requests

url = 'http://localhost:8000'

headers = {
    'Authorization': 'Bearer TOKEN_GOES_HERE'
}

# create a user
r = requests.post(f'{url}/register')
headers['Authorization'] = f'Bearer {r.json()["token"]}'

# get that user's information
r = requests.get(f'{url}/users/my_info', headers=headers)
print(r.json())
