# Transcode Tycoon API Game

A simple API idle game written using Python3 and FastAPI. You have a computer that renders videos for money. You get payouts depending on the videos format and the total run time. The more pixels you push, the more you get paid (in fake money).

Use your money to upgrade your rig's CPU, Clock Speed, and RAM. The more you upgrade, the faster you can render video.

Try to automate the process and climb the learderboard.

## Running Locally

Clone the repository and run:

```bash
docker compose up -d --force-recreate
```

That command will build the container from the source and start the API. If you want to remap the default port `8000` to something else, modify the `docker-compose.yml` file.
