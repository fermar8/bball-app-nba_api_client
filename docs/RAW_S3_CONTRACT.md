# Raw S3 Contract

This project writes raw nba_api responses to S3 only.

## AWS

- Account: configured via `AWS_ACCOUNT_ID`
- Bucket: configured via `S3_BUCKET_NAME`

## Object Key Convention

- Format: `raw/{endpoint}/YYYY/MM/DD/HH/{timestamp}_{request_hash}.json`
- ScheduleLeagueV2 example:
  - `raw/schedule_league_v2/2026/03/08/14/20260308T140901Z_7f3a2c1d.json`
- ScoreboardV2 example:
  - `raw/scoreboard_v2/2026/03/08/14/20260308T141015Z_1ab923ef.json`

Timestamp format: `YYYYMMDDTHHMMSSZ` (UTC)
Request hash: first 8 chars of SHA-256 over sorted request params JSON

## JSON Envelope

Each object body is JSON with this envelope:

- `source`: `nba_api`
- `endpoint`: endpoint identifier (`schedule_league_v2` or `scoreboard_v2`)
- `fetched_at_utc`: UTC ISO timestamp
- `aws_account_id`: AWS account id configured in runtime
- `schema_version`: schema envelope version (current: `v1`)
- `ingestion_id`: UUID for each ingested object
- `params`: request parameters used in the call
- `payload`: full raw response returned by `nba_api` (`get_dict()`)

## S3 Object Tags

New uploads include these tags (when `ENABLE_S3_OBJECT_TAGGING=true`):

- `stage=raw`
- `source=nba_api`
- `endpoint=<endpoint_name>`
- `processed=false`

After downstream Lambda finishes processing an object, update it to:

- `processed=true`

This allows lifecycle policies by tag (for example, expire only `processed=true` objects quickly).

## Scheduling Controls

Per-job flags are used so jobs can be enabled independently:

- `SCHEDULE_JOB_ENABLED`
- `SCOREBOARD_JOB_ENABLED`
- `TEAMS_JOB_ENABLED`
- `PLAYER_INDEX_JOB_ENABLED`
- `PLAYER_GAME_LOGS_JOB_ENABLED`
- `PLAYER_NEXT_GAMES_JOB_ENABLED`

Optional startup-run flags:

- `SCHEDULE_JOB_RUN_ON_STARTUP`
- `SCOREBOARD_JOB_RUN_ON_STARTUP`

For player participant jobs, ids are discovered from recent games using `ScoreboardV2` + `BoxScoreTraditionalV2`, then the service fans out to `PlayerGameLogs` and `PlayerNextNGames` with timeout/retry/pacing controls.
