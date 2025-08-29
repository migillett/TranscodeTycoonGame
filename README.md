USERS:
POST /create
    creates user token
GET /user
    get your user info (including $$$)
GET /leaderboard
    most $$$

JOBS:
GET /jobs
    list available render jobs (with filters)

RENDER QUEUE:
POST /queue
    add job to queue
GET /queue
    check status of current jobs

COMPUTERS:
GET /computers
    list computers
GET /computers/n
    get specific computer
GET /computers/n/upgrades
    get upgrades
POST /computers/n/upgrades/{id}
    purchase upgrade

UPGRADES:
upgrade computer
list available upgrades