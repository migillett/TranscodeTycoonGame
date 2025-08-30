import logging
from pathlib import Path

from transcode_tycoon.routes import users, jobs, upgrades
from transcode_tycoon.game_logic import game_logic
from transcode_tycoon.models.computer import ComputerInfo
from transcode_tycoon.models.jobs import Priority, Format

import toml
from fastapi import FastAPI
import uvicorn


BASE_DIR = Path(__file__).resolve().parent
VERSION = toml.load('pyproject.toml')['project']['version']
DEBUG = True

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = FastAPI(
    title="Transcode Tycoon Game API",
    version=VERSION,
    docs_url='/'
)
logging.info(f"Starting Transcode Tycoon Game API version {VERSION}")


@app.get("/info", tags=["Root"])
async def render_home_page():
    return {
        'message': 'Welcome to the Transcode Tycoon Game API!',
        'github': 'https://github.com/migillett/TranscodeTycoonGame',
        'version': VERSION,
    }


app.include_router(users.router)
app.include_router(jobs.router)
app.include_router(upgrades.router)


if __name__ == "__main__":
    if DEBUG:
        game_logic.add_user(
            users.UserInfo(
                user_id='user',
                funds=200.0,
                computer=ComputerInfo()
            )
        )
        
        game_logic.add_job(
            jobs.JobInfo(
                job_id='job',
                status=jobs.JobStatus.AVAILABLE,
                priority=Priority.HIGH,
                total_run_time=60,  # 1 minute
                format=Format.SD
            )
        )

    uvicorn.run(app, host='0.0.0.0', port=80)
