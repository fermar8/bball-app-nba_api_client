# bball-app-nba_api_client

Flask server that consumes [nba_api](https://github.com/swar/nba_api) and supports two things:

1. Public API endpoints (health + schedule)
2. In-process scheduled jobs that fetch raw nba_api payloads and upload them to S3

## Current AWS Target

- AWS Account: from `AWS_ACCOUNT_ID`
- Raw data bucket: from `S3_BUCKET_NAME`

## Features

- `/schedule` endpoint backed by `ScheduleLeagueV2`
- `/health` endpoint
- Daily in-server scheduler (env-controlled)
- Raw payload upload to S3 (no DynamoDB writes)
- Mocked unit tests for route + ingestion behavior

## Prerequisites

- Python 3.10+
- AWS credentials available to the runtime (for S3 put operations)

## Installation

```powershell
py -m pip install -r requirements.txt
```

If `py` is not available:

```powershell
python -m pip install -r requirements.txt
```

## Environment Variables

### Core

- `S3_BUCKET_NAME` (required)
- `AWS_ACCOUNT_ID` (required)
- `ENABLE_IN_PROCESS_SCHEDULER` (`true/false`, default: `true`)
- `ENABLE_ENDPOINT_S3_UPLOAD` (`true/false`, default: `true`)
- `ENABLE_S3_OBJECT_TAGGING` (`true/false`, default: `true`)

Set `ENABLE_IN_PROCESS_SCHEDULER=false` to disable all in-process scheduled jobs.

### Schedule job (`ScheduleLeagueV2`)

- `SCHEDULE_JOB_ENABLED` (`true/false`, default: `false`)
- `SCHEDULE_JOB_HOUR_UTC` (default: `3`)
- `SCHEDULE_JOB_MINUTE_UTC` (default: `0`)
- `SCHEDULE_JOB_RUN_ON_STARTUP` (`true/false`, default: `false`)
- `SCHEDULE_DEFAULT_SEASON_YEAR` (optional, e.g. `2023`)

### Scoreboard job (`ScoreboardV2`)

- `SCOREBOARD_JOB_ENABLED` (`true/false`, default: `false`)
- `SCOREBOARD_JOB_HOUR_UTC` (default: `5`)
- `SCOREBOARD_JOB_MINUTE_UTC` (default: `0`)
- `SCOREBOARD_JOB_RUN_ON_STARTUP` (`true/false`, default: `false`)
- `SCOREBOARD_GAME_DATE` (optional, format `MM/DD/YYYY`)

### Teams job (`teams_static`)

- `TEAMS_JOB_ENABLED` (`true/false`, default: `false`)
- `TEAMS_JOB_HOUR_UTC` (default: `4`)
- `TEAMS_JOB_MINUTE_UTC` (default: `0`)

### Player index job (`PlayerIndex`)

- `PLAYER_INDEX_JOB_ENABLED` (`true/false`, default: `false`)
- `PLAYER_INDEX_JOB_HOUR_UTC` (default: `4`)
- `PLAYER_INDEX_JOB_MINUTE_UTC` (default: `30`)

### Player participant jobs (`PlayerGameLogs`, `PlayerNextNGames`)

- `PLAYER_GAME_LOGS_JOB_ENABLED` (`true/false`, default: `false`)
- `PLAYER_GAME_LOGS_JOB_HOUR_UTC` (default: `6`)
- `PLAYER_GAME_LOGS_JOB_MINUTE_UTC` (default: `0`)
- `PLAYER_GAME_LOGS_SEASON` (optional, e.g. `2025-26`)
- `PLAYER_NEXT_GAMES_JOB_ENABLED` (`true/false`, default: `false`)
- `PLAYER_NEXT_GAMES_JOB_HOUR_UTC` (default: `6`)
- `PLAYER_NEXT_GAMES_JOB_MINUTE_UTC` (default: `30`)
- `PLAYER_NEXT_GAMES_NUMBER_OF_GAMES` (default: `5`)
- `PLAYER_NEXT_GAMES_SEASON` (optional, e.g. `2025-26`)

Participant discovery controls:

- `PLAYER_PARTICIPANT_GAME_DATE` (optional override date `MM/DD/YYYY`)
- `PLAYER_PARTICIPANT_LOOKBACK_DAYS` (default: `1`, means yesterday only)
- `PLAYER_JOB_MAX_PLAYERS_PER_RUN` (default: `150`)

nba_api resilience controls:

- `NBA_API_TIMEOUT_SECONDS` (default: `15`)
- `NBA_API_MAX_RETRIES` (default: `2`)
- `NBA_API_REQUEST_DELAY_MS` (default: `300`)
- `NBA_API_BACKOFF_BASE_SECONDS` (default: `1`)
- `NBA_API_MAX_CONSECUTIVE_ERRORS` (default: `5`)

## Running Locally

### PowerShell example (enable daily schedule ingestion)

```powershell
$env:S3_BUCKET_NAME="your-bucket-name"
$env:AWS_ACCOUNT_ID="your-aws-account-id"
$env:SCHEDULE_JOB_ENABLED="true"
$env:SCHEDULE_JOB_RUN_ON_STARTUP="true"
python server.py
```

Server URL: `http://localhost:5000`

## Endpoints

Base URL (local): `http://localhost:5000`

### Root

- `GET /`
- Example: `GET http://localhost:5000/`

### Health

- `GET /health`
- Example: `GET http://localhost:5000/health`

### Schedule

- `GET /schedule`
- Optional query param: `season=YYYY`
- Optional query param: `persist_raw=true` (validate + upload this response to S3)
- Examples:
  - `GET http://localhost:5000/schedule`
  - `GET http://localhost:5000/schedule?season=2023`

### Teams

- `GET /teams`
- Optional query param: `persist_raw=true` (validate + upload this response to S3)
- Example: `GET http://localhost:5000/teams`

### Player Index

- `GET /players/index`
- Optional query param: `persist_raw=true` (validate + upload this response to S3)
- Example: `GET http://localhost:5000/players/index`

### Player Game Logs

- `GET /players/game-logs`
- Required query pattern: either `player_id` OR both `date_from` and `date_to`
- `season` is required when `player_id` is provided (e.g. `2025-26`)
- `season` is also required when using `date_from` + `date_to`
- Optional query params: `date_from`, `date_to` (`MM/DD/YYYY`)
- Optional query param: `persist_raw=true` (validate + upload this response to S3)
- Example: `GET http://localhost:5000/players/game-logs?player_id=2544&season=2025-26`

Date-window example:

- `GET http://localhost:5000/players/game-logs?date_from=03/07/2026&date_to=03/07/2026&season=2025-26`

### Player Next N Games

- `GET /players/next-games`
- Required query param: `player_id` (integer)
- Optional query params:
  - `number_of_games` (integer, default `5`)
  - `season` (e.g. `2025-26`)
  - `persist_raw=true` (validate + upload this response to S3)
- Example: `GET http://localhost:5000/players/next-games?player_id=2544&number_of_games=5&season=2025-26`

## S3 Raw Object Pattern

- Format: `raw/{endpoint}/YYYY/MM/DD/HH/{timestamp}_{request_hash}.json`
- Schedule example:
  - `raw/schedule_league_v2/2026/03/08/14/20260308T140901Z_7f3a2c1d.json`
- Scoreboard example:
  - `raw/scoreboard_v2/2026/03/08/14/20260308T141015Z_1ab923ef.json`

Each JSON includes:

- source
- endpoint
- fetched timestamp
- aws account id
- schema version
- ingestion id
- request params
- full raw payload from nba_api

Retention best practice:

- Use S3 lifecycle expiration on `raw/` (for example 7-14 days) instead of immediate delete-after-process.
- Prefer lifecycle by object tag: write with `processed=false`, then flip to `processed=true` after successful Lambda processing.

Manual helper for backfills/retries:

```powershell
python scripts/set_object_processed_state.py --key "raw/schedule_league_v2/2026/03/08/14/20260308T140901Z_7f3a2c1d.json" --processed true --endpoint schedule_league_v2
```

Mark object as unprocessed (for reprocessing):

```powershell
python scripts/set_object_processed_state.py --key "raw/schedule_league_v2/2026/03/08/14/20260308T140901Z_7f3a2c1d.json" --processed false --endpoint schedule_league_v2
```

### Validation Gate (Before S3 Upload)

For scheduled ingestion jobs, payloads are validated before upload:

1. Fetch from `nba_api`
2. Validate schema for the endpoint
3. Upload to S3 only if valid

If validation fails, the job logs the error and skips upload for that run.

Validation source of truth:

- `docs/schemas/schedule_league_v2.schema.json`
- `docs/schemas/scoreboard_v2.schema.json`
- `docs/schemas/player_index.schema.json`
- `docs/schemas/player_game_logs.schema.json`
- `docs/schemas/player_next_n_games.schema.json`
- `docs/schemas/teams_static.schema.json`

Detailed shape docs:

- Endpoint response schemas: `docs/RESPONSE_SCHEMAS.md`
- S3 object schema and contract: `docs/RAW_S3_CONTRACT.md`

## Running Tests

```powershell
python -m unittest test_integration.py -v
```

## Hosting Note

In-process schedulers depend on the web process staying alive. On very cheap/free hosts that sleep idle apps, scheduled jobs may pause while the app is asleep.
