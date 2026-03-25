# Endpoint Response Schemas

This document defines the API response envelope used by this service and the expected high-level shape for each endpoint.

All successful responses follow:

```json
{
  "success": true,
  "data": {}
}
```

Validation errors (HTTP 400) and internal errors (HTTP 500) follow:

```json
{
  "success": false,
  "error": "error message"
}
```

## Validation Contract for S3 Ingestion

Scheduled ingestion jobs use these schemas as runtime validation rules:

1. Call `nba_api` endpoint
2. Validate payload structure
3. Upload raw payload to S3 only if validation passes

If validation fails, upload is skipped for that run.

The runtime validator reads JSON Schema files from:

- `docs/schemas/schedule_league_v2.schema.json`
- `docs/schemas/scoreboard_v2.schema.json`
- `docs/schemas/player_index.schema.json`
- `docs/schemas/player_game_logs.schema.json`
- `docs/schemas/player_next_n_games.schema.json`
- `docs/schemas/teams_static.schema.json`

Current validator coverage:

- `schedule_league_v2`: validates top-level `meta` and `leagueSchedule`, plus nested checks for `gameDates[].games[].homeTeam`, `awayTeam`, and `pointsLeaders` fields.
- `scoreboard_v2`: validates `resource`, `parameters`, `resultSets`, and requires at least one `GameHeader` dataset.
- `player_index`: validates `resource`, `parameters`, and presence of `PlayerIndex` dataset.
- `player_game_logs`: validates `resource`, `parameters`, and presence of `PlayerGameLogs` dataset.
- `player_next_n_games`: validates `resource`, `parameters`, and presence of `NextNGames` dataset.
- `teams_static`: validates each team object includes id/name/abbreviation/city/state/year fields.

## GET /

```json
{
  "name": "NBA API Client Server",
  "version": "1.0.0",
  "endpoints": {
    "/schedule": "Get NBA league schedule",
    "/scoreboard": "Get NBA scoreboard data",
    "/teams": "Get NBA teams list with ids",
    "/players/index": "Get player index data",
    "/players/game-logs": "Get player game logs",
    "/players/next-games": "Get next N games for a player",
    "/health": "Health check endpoint"
  }
}
```

## GET /health

```json
{
  "status": "healthy",
  "timestamp": "2026-03-08T13:30:00.000000"
}
```

## GET /schedule

Backed by `ScheduleLeagueV2` from `nba_api`.

```json
{
  "success": true,
  "data": {
    "meta": {
      "version": 1,
      "request": "...",
      "time": "..."
    },
    "leagueSchedule": {
      "seasonYear": "2024-25",
      "leagueId": "00",
      "gameDates": [
        {
          "gameDate": "2024-10-22",
          "games": [
            {
              "gameId": "0022400001",
              "gameCode": "20241022/NYKBOS",
              "gameStatus": 1,
              "gameStatusText": "7:30 pm ET",
              "gameSequence": 1,
              "gameDateEst": "2024-10-22T00:00:00Z",
              "gameTimeEst": "2024-10-22T19:30:00Z",
              "gameDateTimeEst": "2024-10-22T19:30:00Z",
              "gameDateUTC": "2024-10-22",
              "gameTimeUTC": "23:30:00",
              "gameDateTimeUTC": "2024-10-22T23:30:00Z",
              "awayTeamTime": "",
              "homeTeamTime": "",
              "day": "Tue",
              "monthNum": 10,
              "weekNumber": 1,
              "weekName": "Week 1",
              "ifNecessary": false,
              "seriesGameNumber": "",
              "gameLabel": "",
              "gameSubLabel": "",
              "seriesText": "",
              "arenaName": "...",
              "arenaState": "...",
              "arenaCity": "...",
              "postponedStatus": "",
              "branchLink": "",
              "gameSubtype": "",
              "isNeutral": false,
              "broadcasters": {
                "nationalBroadcasters": [],
                "homeTvBroadcasters": [],
                "awayTvBroadcasters": [],
                "homeRadioBroadcasters": [],
                "awayRadioBroadcasters": []
              },
              "homeTeam": {
                "teamId": 1610612743,
                "teamName": "Nuggets",
                "teamCity": "Denver",
                "teamTricode": "DEN",
                "teamSlug": "nuggets",
                "wins": 0,
                "losses": 1,
                "score": 103,
                "seed": 0
              },
              "awayTeam": {
                "teamId": 1610612738,
                "teamName": "Celtics",
                "teamCity": "Boston",
                "teamTricode": "BOS",
                "teamSlug": "celtics",
                "wins": 1,
                "losses": 0,
                "score": 107,
                "seed": 0
              },
              "pointsLeaders": [
                {
                  "personId": 1630202,
                  "firstName": "Payton",
                  "lastName": "Pritchard",
                  "teamId": 1610612738,
                  "teamCity": "Boston",
                  "teamName": "Celtics",
                  "teamTricode": "BOS",
                  "points": 21.0
                }
              ]
            }
          ]
        }
      ],
      "weeks": []
    }
  }
}
```

Notes:

- `season=YYYY` is converted to `YYYY-YY` before calling `nba_api`.
- `ScheduleLeagueV2` returns nested JSON (`meta` + `leagueSchedule`) instead of `resultSets`.
- `homeTeam` and `awayTeam` currently include: `teamId`, `teamName`, `teamCity`, `teamTricode`, `teamSlug`, `wins`, `losses`, `score`, `seed`.
- `pointsLeaders` items currently include: `personId`, `firstName`, `lastName`, `teamId`, `teamCity`, `teamName`, `teamTricode`, `points`.

## GET /scoreboard

Backed by `ScoreboardV2` from `nba_api`.

```json
{
  "success": true,
  "data": {
    "resource": "scoreboardv2",
    "parameters": {},
    "resultSets": [
      {
        "name": "GameHeader",
        "headers": ["GAME_ID"],
        "rowSet": [["0022400001"]]
      }
    ]
  }
}
```

Notes:

- Optional query param `game_date` is accepted in format `MM/DD/YYYY`.
- Invalid `game_date` values return HTTP 400.

## GET /teams

Backed by `nba_api.stats.static.teams.get_teams()`.

```json
{
  "success": true,
  "data": [
    {
      "id": 1610612737,
      "full_name": "Atlanta Hawks",
      "abbreviation": "ATL",
      "nickname": "Hawks",
      "city": "Atlanta",
      "state": "Georgia",
      "year_founded": 1949
    }
  ]
}
```

## GET /players/index

Backed by `PlayerIndex` from `nba_api`.

```json
{
  "success": true,
  "data": {
    "resource": "playerindex",
    "parameters": {},
    "resultSets": [
      {
        "name": "PlayerIndex",
        "headers": [
          "PERSON_ID",
          "PLAYER_LAST_NAME",
          "PLAYER_FIRST_NAME",
          "PLAYER_SLUG",
          "TEAM_ID",
          "TEAM_SLUG",
          "IS_DEFUNCT",
          "TEAM_CITY",
          "TEAM_NAME",
          "TEAM_ABBREVIATION",
          "JERSEY_NUMBER",
          "POSITION",
          "HEIGHT",
          "WEIGHT",
          "COLLEGE",
          "COUNTRY",
          "DRAFT_YEAR",
          "DRAFT_ROUND",
          "DRAFT_NUMBER",
          "ROSTER_STATUS",
          "FROM_YEAR",
          "TO_YEAR",
          "PTS",
          "REB",
          "AST",
          "STATS_TIMEFRAME"
        ],
        "rowSet": [
          [
            1610612737,
            "...",
            "...",
            "...",
            0,
            "...",
            0,
            "...",
            "...",
            "...",
            "...",
            "...",
            "...",
            "...",
            "...",
            "...",
            "...",
            "...",
            "...",
            "...",
            0,
            0,
            0,
            0,
            0,
            "..."
          ]
        ]
      }
    ]
  }
}
```

## GET /players/game-logs

Backed by `PlayerGameLogs` from `nba_api`.

Query params:

- `player_id` (optional, integer)
- `date_from` + `date_to` (optional, `MM/DD/YYYY`)
- `season` (optional)

At least one of the following must be provided:

- `player_id`
- both `date_from` and `date_to`

```json
{
  "success": true,
  "data": {
    "resource": "playergamelogs",
    "parameters": {
      "PlayerID": "2544"
    },
    "resultSets": [
      {
        "name": "PlayerGameLogs",
        "headers": [
          "SEASON_YEAR",
          "PLAYER_ID",
          "PLAYER_NAME",
          "NICKNAME",
          "TEAM_ID",
          "TEAM_ABBREVIATION",
          "TEAM_NAME",
          "GAME_ID",
          "GAME_DATE",
          "MATCHUP",
          "WL",
          "MIN",
          "FGM",
          "FGA",
          "FG_PCT",
          "FG3M",
          "FG3A",
          "FG3_PCT",
          "FTM",
          "FTA",
          "FT_PCT",
          "OREB",
          "DREB",
          "REB",
          "AST",
          "TOV",
          "STL",
          "BLK",
          "BLKA",
          "PF",
          "PFD",
          "PTS",
          "PLUS_MINUS",
          "NBA_FANTASY_PTS",
          "DD2",
          "TD3",
          "WNBA_FANTASY_PTS",
          "GP_RANK",
          "W_RANK",
          "L_RANK",
          "W_PCT_RANK",
          "MIN_RANK",
          "FGM_RANK",
          "FGA_RANK",
          "FG_PCT_RANK",
          "FG3M_RANK",
          "FG3A_RANK",
          "FG3_PCT_RANK",
          "FTM_RANK",
          "FTA_RANK",
          "FT_PCT_RANK",
          "OREB_RANK",
          "DREB_RANK",
          "REB_RANK",
          "AST_RANK",
          "TOV_RANK",
          "STL_RANK",
          "BLK_RANK",
          "BLKA_RANK",
          "PF_RANK",
          "PFD_RANK",
          "PTS_RANK",
          "PLUS_MINUS_RANK",
          "NBA_FANTASY_PTS_RANK",
          "DD2_RANK",
          "TD3_RANK",
          "WNBA_FANTASY_PTS_RANK",
          "AVAILABLE_FLAG",
          "MIN_SEC",
          "TEAM_COUNT"
        ],
        "rowSet": [
          [
            "2024-25",
            2544,
            "...",
            "...",
            1610612747,
            "LAL",
            "Lakers",
            "0022400001",
            "2024-10-22",
            "LAL vs. MIN",
            "W",
            "...",
            "...",
            "...",
            "...",
            "...",
            "...",
            "...",
            "...",
            "...",
            "...",
            "...",
            "...",
            "...",
            "...",
            "...",
            "...",
            "...",
            "...",
            "...",
            "...",
            "...",
            "...",
            "...",
            "...",
            "...",
            "...",
            "...",
            "...",
            "...",
            "...",
            "...",
            "...",
            "...",
            "...",
            "...",
            "...",
            "...",
            "...",
            "...",
            "...",
            "...",
            "...",
            "...",
            "...",
            "...",
            "...",
            "...",
            "...",
            "...",
            "...",
            "...",
            "...",
            "...",
            "...",
            "...",
            "...",
            "...",
            "...",
            "...",
            "...",
            "..."
          ]
        ]
      }
    ]
  }
}
```

Validation error example:

```json
{
  "success": false,
  "error": "Provide player_id or both date_from and date_to query parameters."
}
```

## GET /players/next-games

Backed by `PlayerNextNGames` from `nba_api`.

Query params:

- `player_id` (required, integer)
- `number_of_games` (optional, integer, default: 5)
- `season` (optional)

```json
{
  "success": true,
  "data": {
    "resource": "playernextngames",
    "parameters": {
      "PlayerID": "2544",
      "NumberOfGames": "5"
    },
    "resultSets": [
      {
        "name": "NextNGames",
        "headers": [
          "GAME_ID",
          "GAME_DATE",
          "HOME_TEAM_ID",
          "VISITOR_TEAM_ID",
          "HOME_TEAM_NAME",
          "VISITOR_TEAM_NAME",
          "HOME_TEAM_ABBREVIATION",
          "VISITOR_TEAM_ABBREVIATION",
          "HOME_TEAM_NICKNAME",
          "VISITOR_TEAM_NICKNAME",
          "GAME_TIME",
          "HOME_WL",
          "VISITOR_WL"
        ],
        "rowSet": [
          [
            "0022400001",
            "2024-10-22",
            1610612747,
            1610612750,
            "Los Angeles Lakers",
            "Minnesota Timberwolves",
            "LAL",
            "MIN",
            "Lakers",
            "Timberwolves",
            "7:30 PM ET",
            "0-0",
            "0-0"
          ]
        ]
      }
    ]
  }
}
```

Validation error example:

```json
{
  "success": false,
  "error": "Invalid number_of_games. Must be an integer."
}
```

---

## S3 Saved Object Schema

This service saves raw payloads in S3 under:

- `raw/schedule_league_v2/YYYY/MM/DD/<timestamp>.json`
- `raw/scoreboard_v2/YYYY/MM/DD/<timestamp>.json`

Object body schema:

```json
{
  "source": "nba_api",
  "endpoint": "schedule_league_v2",
  "fetched_at_utc": "2026-03-08T13:30:00.000000+00:00Z",
  "aws_account_id": "<aws_account_id_from_env>",
  "params": {
    "season": "2025-26"
  },
  "payload": {
    "meta": {
      "version": 1,
      "request": "...",
      "time": "..."
    },
    "leagueSchedule": {
      "seasonYear": "2025-26",
      "leagueId": "00",
      "gameDates": [],
      "weeks": []
    }
  }
}
```

See also: `docs/RAW_S3_CONTRACT.md`
