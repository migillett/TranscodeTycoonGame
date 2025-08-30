import logging
from pathlib import Path

from transcode_tycoon.routes import users, jobs, upgrades
from transcode_tycoon.game_logic import game_logic
from transcode_tycoon.models.users import CreateUserResponse

import toml
from fastapi import FastAPI
import uvicorn


BASE_DIR = Path(__file__).resolve().parent
VERSION = toml.load('pyproject.toml')['project']['version']
DEBUG = True
DESCRIPTION = '''A simple API-based idle game. Render video, get paid fake money.
    
The more jobs you do, the more money you make.

Use the money you make to upgrade your computer's CPU cores and Clock Speed to make your renders go faster. Upgrade your system's RAM to increase the size of your job queue.

Send a `POST` request to `/register` to get started. Documentation available at `/docs`.
'''


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__file__)

app = FastAPI(
    title="Transcode Tycoon Game API",
    version=VERSION,
    docs_url='/docs',
    description=DESCRIPTION)
logger.info(f"Starting Transcode Tycoon Game API version {VERSION}")


@app.get("/", tags=["Root"])
async def render_home_page():
    return {
        'message': 'Welcome to the Transcode Tycoon Game API!',
        'github': 'https://github.com/migillett/TranscodeTycoonGame',
        'version': VERSION,
        'description': DESCRIPTION,
    }


@app.post('/register', tags=["Root"])
async def register_user() -> CreateUserResponse:
    '''
    Registers a new user and returns a unique user ID.
    '''
    return game_logic.create_user()


app.include_router(users.router)
app.include_router(jobs.router)
app.include_router(upgrades.router)


if __name__ == "__main__":
    uvicorn.run(app, host='0.0.0.0', port=8000)
