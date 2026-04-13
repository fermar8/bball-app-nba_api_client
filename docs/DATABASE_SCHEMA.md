# DynamoDB Schema Design - MVP

> Purpose: define the curated DynamoDB data model for the fantasy basketball MVP.
> Scope: tables, keys, indexes, item attributes, access patterns, and known data gaps.
> Out of scope: Lambda implementation, S3 processing pipeline, infrastructure provisioning, and V2 enrichments.

---

## Design Decision

The MVP should use a multi-table design.

Reasons:

- Games, players, injuries, and player stats have different write frequencies and different query patterns.
- The most important read for the MVP is roster by team with current injury status, which is cleaner with a dedicated `nba_players` table plus a team index.
- Per-game stats and season aggregates have different granularities, so they should not share the same item shape.
- A multi-table design keeps the model explicit and easier to evolve during the MVP phase.

---

## Schema Overview

```text
nba_games
  PK: gameId
  GSI: season -> gameDateTimeEst

nba_teams
  PK: teamId

nba_players
  PK: playerId
  GSI: teamId -> lastName

nba_player_game_stats
  PK: playerId
  SK: gameDate#gameId
  GSI: gameId -> pts

nba_player_season_stats
  PK: playerId
  SK: season

nba_injuries
  PK: playerId
  SK: reportDate#fetchedAt
  GSI: teamAbbr -> reportDate
```

---

## Source Coverage

The DynamoDB model is intentionally limited to data currently supported by the source payloads used in this repository.

### Supported sources

- `ScheduleLeagueV2`
- `teams_static`
- `PlayerIndex`
- `PlayerGameLogs`
- normalized `injury_report`

### Explicitly excluded from MVP

- `PlayerNextNGames`
- player photos if not sourced from current raw payloads
- team logos if not sourced from current raw payloads
- birth date
- birth place
- real age

Upcoming opponents will be derived from `nba_games` using the player's current `teamId`.

---

## Access Patterns

These are the core reads the schema must optimize.

1. Full NBA calendar for a season, ordered by date and time.
2. Games for a specific date.
3. Team roster with current injury status.
4. Player profile card.
5. Full game-by-game stat history for one player in one season.
6. Season totals for one player.
7. Injury history for one player.
8. Current injury list for one team.
9. Boxscore leaders for one game.
10. Next opponents for one player, derived by joining player's `teamId` with future `nba_games` rows in application logic.

---

## Table 1: `nba_games`

Purpose: store regular-season NBA-vs-NBA games from schedule_league_v2, with lean attributes for schedule/state/score and change-detection metadata.

### Keys

- PK: `gameId` (String)

### Indexes

- None

Use cases:

- Get a game by id
- Scan table for full dataset when needed (small/controlled workload)

### Attributes

| Field             | Type   | Notes                        |
| ----------------- | ------ | ---------------------------- |
| `gameId`          | String | Stable NBA game identifier   |
| `season`          | String | Example: `2025-26`           |
| `gameDateEst`     | String | Date only                    |
| `gameDateTimeEst` | String | Date-time used for sorting   |
| `gameStatus`      | Number | 1 scheduled, 2 live, 3 final |
| `gameStatusText`  | String | Human-readable state         |
| `homeTeamId`      | Number | Home team id                 |
| `homeTeamName`    | String | Home team name               |
| `homeTeamTricode` | String | Example: `LAL`               |
| `homeTeamWins`    | Number | Nullable if not available    |
| `homeTeamLosses`  | Number | Nullable if not available    |
| `homeTeamScore`   | Number | Nullable before game ends    |
| `awayTeamId`      | Number | Away team id                 |
| `awayTeamName`    | String | Away team name               |
| `awayTeamTricode` | String | Example: `BOS`               |
| `awayTeamWins`    | Number | Nullable if not available    |
| `awayTeamLosses`  | Number | Nullable if not available    |
| `awayTeamScore`   | Number | Nullable before game ends    |
| `arenaName`       | String | Optional                     |
| `arenaCity`       | String | Optional                     |
| `dataHash`        | String | SHA-256 hash of persisted payload, used to skip unchanged writes |

Notes:

- Optional fields are only written when present (sparse item shape).
- No season field is persisted.
- Upsert is conditional: write occurs only for new gameId or when dataHash changes.

### Example item

```json
{
  "gameId": "0022500001",
  "season": "2025-26",
  "gameDateEst": "2025-10-22",
  "gameDateTimeEst": "2025-10-22T19:30:00Z",
  "gameStatus": 3,
  "gameStatusText": "Final",
  "homeTeamId": 1610612747,
  "homeTeamName": "Lakers",
  "homeTeamTricode": "LAL",
  "homeTeamWins": 1,
  "homeTeamLosses": 0,
  "homeTeamScore": 112,
  "awayTeamId": 1610612738,
  "awayTeamName": "Celtics",
  "awayTeamTricode": "BOS",
  "awayTeamWins": 0,
  "awayTeamLosses": 1,
  "awayTeamScore": 108,
  "arenaName": "Crypto.com Arena",
  "arenaCity": "Los Angeles",
  "dataHash": "9e5fd6d8ef9d8eb0b95d7a7d7c4d2aa4f5ce2d4f0d80ec3a0f5a6a8bd3b7c2a1"
}
```

---

## Table 2: `teams_static`

Purpose: minimal team directory for the MVP.

### Keys

- PK: `teamId` (Number)

### Indexes

No GSI is required for the MVP.

### Attributes

| Field              | Type   | Notes                  |
| ------------------ | ------ | ---------------------- |
| `teamId`           | Number | Stable NBA team id     |
| `fullName`         | String | Full name              |
| `abbreviation` | String | Example: `LAL`         |
| `nickname`         | String | Example: `Lakers`      |


### Example item

```json
{
  "teamId": 1610612747,
  "fullName": "Los Angeles Lakers",
  "abbreviation": "LAL",
  "nickname": "Lakers",
}
```

Note: logos are deferred to V2.

---

## Table 3: `nba_players`

Purpose: player directory and current player card state.

### Keys

- PK: `playerId` (Number)

### Indexes

- `GSI1PK = teamId`
- `GSI1SK = lastName`

Use case:

- fetch roster by team ordered by last name

### Attributes

| Field              | Type   | Notes                                |
| ------------------ | ------ | ------------------------------------ |
| `playerId`         | Number | Stable NBA player id                 |
| `firstName`        | String |                                      |
| `lastName`         | String |                                      |
| `displayName`      | String | Convenience field                    |
| `teamId`           | Number | Current team id                      |
| `teamName`         | String |                                      |
| `teamAbbreviation` | String |                                      |
| `jerseyNumber`     | String |                                      |
| `position`         | String | Example: `G-F`                       |
| `height`           | String | Example: `6-8`                       |
| `country`          | String | Nationality/country                  |
| `rosterStatus`     | Number | 1 active roster, 0 inactive          |
| `injuryStatus`     | Map    | Denormalized current injury snapshot |

### `injuryStatus` map

| Field          | Type   | Notes                                                                 |
| -------------- | ------ | --------------------------------------------------------------------- |
| `status`       | String | `out`, `questionable`, `doubtful`, `probable`, `available`, `unknown` |
| `availability` | String | Simplified availability label                                         |
| `reasonType`   | String | Normalized category                                                   |
| `reason`       | String | Free text                                                             |
| `reportDate`   | String | Latest injury report date                                             |

### Example item

```json
{
  "playerId": 2544,
  "firstName": "LeBron",
  "lastName": "James",
  "displayName": "LeBron James",
  "teamId": 1610612747,
  "teamName": "Lakers",
  "teamAbbreviation": "LAL",
  "jerseyNumber": "23",
  "position": "F",
  "height": "6-9",
  "country": "USA",
  "rosterStatus": 1,
  "injuryStatus": {
    "status": "probable",
    "availability": "likely",
    "reasonType": "injury",
    "reason": "Left ankle soreness",
    "reportDate": "2026-04-05"
  }
}
```

Notes:

- `birthDate`, `birthPlace`, `age`, and `photoUrl` are deferred to V2.
- `injuryStatus` should represent the latest known injury snapshot for fast roster reads.

---

## Table 4: `nba_player_game_stats`

Purpose: one row per player per game.

### Keys

- PK: `playerId` (Number)
- SK: `gameDate#gameId` (String)

Example sort key:

```text
2025-10-22#0022500001
```

### Indexes

- `GSI1PK = gameId`
- `GSI1SK = pts`

Use cases:

- fetch all games for one player ordered by date
- fetch all player rows for one game

If game leaders need strict descending order, store a second sortable numeric field pattern later. It is not required to define that optimization for the MVP schema document.

### Attributes

| Field              | Type   | Notes                                               |
| ------------------ | ------ | --------------------------------------------------- |
| `playerId`         | Number |                                                     |
| `gameDate`         | String | Date only                                           |
| `gameId`           | String |                                                     |
| `season`           | String | Example: `2025-26`                                  |
| `teamId`           | Number |                                                     |
| `teamAbbreviation` | String |                                                     |
| `matchup`          | String | Example: `LAL vs. BOS`                              |
| `winLoss`          | String | `W` or `L`                                          |
| `minutes`          | String | Store canonical display value from source           |
| `minutesDecimal`   | Number | Optional numeric projection for sorting/aggregation |
| `pts`              | Number |                                                     |
| `fgm`              | Number | Total field goals made                              |
| `fga`              | Number | Total field goals attempted                         |
| `fg2m`             | Number | Derived: `fgm - fg3m`                               |
| `fg2a`             | Number | Derived: `fga - fg3a`                               |
| `fg3m`             | Number |                                                     |
| `fg3a`             | Number |                                                     |
| `ftm`              | Number |                                                     |
| `fta`              | Number |                                                     |
| `oreb`             | Number |                                                     |
| `dreb`             | Number |                                                     |
| `reb`              | Number |                                                     |
| `ast`              | Number |                                                     |
| `stl`              | Number |                                                     |
| `tov`              | Number |                                                     |
| `blk`              | Number |                                                     |
| `blka`             | Number | Blocks against                                      |
| `pf`               | Number | Fouls committed                                     |
| `pfd`              | Number | Fouls received                                      |

### Example item

```json
{
  "playerId": 2544,
  "gameDate": "2025-10-22",
  "gameId": "0022500001",
  "season": "2025-26",
  "teamId": 1610612747,
  "teamAbbreviation": "LAL",
  "matchup": "LAL vs. BOS",
  "winLoss": "W",
  "minutes": "35:28",
  "minutesDecimal": 35.47,
  "pts": 28,
  "fgm": 10,
  "fga": 20,
  "fg2m": 7,
  "fg2a": 12,
  "fg3m": 3,
  "fg3a": 8,
  "ftm": 5,
  "fta": 6,
  "oreb": 2,
  "dreb": 8,
  "reb": 10,
  "ast": 8,
  "stl": 1,
  "tov": 3,
  "blk": 0,
  "blka": 1,
  "pf": 2,
  "pfd": 5
}
```

---

## Table 5: `nba_player_season_stats`

Purpose: one row per player per season with accumulated stats for fast reads.

This table should exist separately from `nba_player_game_stats` because it has a different query pattern and a different item granularity.

### Keys

- PK: `playerId` (Number)
- SK: `season` (String)

### Indexes

No GSI is required for the MVP.

If leaderboards by season become important, that can be added later with a dedicated ranking strategy.

### Attributes

| Field              | Type   | Notes                    |
| ------------------ | ------ | ------------------------ |
| `playerId`         | Number |                          |
| `season`           | String | Example: `2025-26`       |
| `teamId`           | Number | Latest season team id    |
| `teamAbbreviation` | String |                          |
| `gamesPlayed`      | Number | Count of rows aggregated |
| `minutesTotal`     | Number | Decimal total            |
| `ptsTotal`         | Number |                          |
| `fgmTotal`         | Number |                          |
| `fgaTotal`         | Number |                          |
| `fg2mTotal`        | Number |                          |
| `fg2aTotal`        | Number |                          |
| `fg3mTotal`        | Number |                          |
| `fg3aTotal`        | Number |                          |
| `ftmTotal`         | Number |                          |
| `ftaTotal`         | Number |                          |
| `orebTotal`        | Number |                          |
| `drebTotal`        | Number |                          |
| `rebTotal`         | Number |                          |
| `astTotal`         | Number |                          |
| `stlTotal`         | Number |                          |
| `tovTotal`         | Number |                          |
| `blkTotal`         | Number |                          |
| `blkaTotal`        | Number |                          |
| `pfTotal`          | Number |                          |
| `pfdTotal`         | Number |                          |
| `ptsAvg`           | Number | Optional but recommended |
| `rebAvg`           | Number | Optional but recommended |
| `astAvg`           | Number | Optional but recommended |

### Example item

```json
{
  "playerId": 2544,
  "season": "2025-26",
  "teamId": 1610612747,
  "teamAbbreviation": "LAL",
  "gamesPlayed": 72,
  "minutesTotal": 2486.5,
  "ptsTotal": 1834,
  "fgmTotal": 690,
  "fgaTotal": 1320,
  "fg2mTotal": 472,
  "fg2aTotal": 850,
  "fg3mTotal": 218,
  "fg3aTotal": 470,
  "ftmTotal": 236,
  "ftaTotal": 301,
  "orebTotal": 74,
  "drebTotal": 418,
  "rebTotal": 492,
  "astTotal": 544,
  "stlTotal": 79,
  "tovTotal": 221,
  "blkTotal": 41,
  "blkaTotal": 58,
  "pfTotal": 109,
  "pfdTotal": 280,
  "ptsAvg": 25.47,
  "rebAvg": 6.83,
  "astAvg": 7.56
}
```

---

## Table 6: `nba_injuries`

Purpose: historical injury and availability snapshots.

### Keys

- PK: `playerId` (Number)
- SK: `reportDate#fetchedAt` (String)

Example sort key:

```text
2026-04-05#2026-04-05T16:40:12Z
```

### Indexes

- `GSI1PK = teamAbbr`
- `GSI1SK = reportDate`

Use cases:

- fetch latest injuries for one team
- fetch injury timeline for one player

### Attributes

| Field          | Type   | Notes                                                                 |
| -------------- | ------ | --------------------------------------------------------------------- |
| `playerId`     | Number | Nullable only if source cannot resolve id                             |
| `playerName`   | String | Denormalized for debugging and UI fallbacks                           |
| `teamAbbr`     | String |                                                                       |
| `status`       | String | `out`, `questionable`, `doubtful`, `probable`, `available`, `unknown` |
| `availability` | String | Simplified availability label                                         |
| `reasonType`   | String | Normalized category                                                   |
| `reason`       | String | Free text                                                             |
| `reportDate`   | String | Injury report date                                                    |
| `fetchedAt`    | String | Snapshot timestamp                                                    |

### Example item

```json
{
  "playerId": 2544,
  "playerName": "LeBron James",
  "teamAbbr": "LAL",
  "status": "probable",
  "availability": "likely",
  "reasonType": "injury",
  "reason": "Left ankle soreness",
  "reportDate": "2026-04-05",
  "fetchedAt": "2026-04-05T16:40:12Z"
}
```

---

## Requirement Coverage

| MVP requirement          | Table                         | Fields                                                           |
| ------------------------ | ----------------------------- | ---------------------------------------------------------------- |
| Full NBA calendar        | `nba_games`                   | `season`, `gameDateEst`, `gameDateTimeEst`, teams, scores, state |
| Past game result         | `nba_games`                   | `gameStatus`, `homeTeamScore`, `awayTeamScore`                   |
| Team names               | `nba_teams`                   | `teamName`, `teamAbbreviation`, `nickname`, `city`               |
| Player names             | `nba_players`                 | `firstName`, `lastName`, `displayName`                           |
| Position                 | `nba_players`                 | `position`                                                       |
| Nationality              | `nba_players`                 | `country`                                                        |
| Jersey                   | `nba_players`                 | `jerseyNumber`                                                   |
| Height                   | `nba_players`                 | `height`                                                         |
| Approximate availability | `nba_players`, `nba_injuries` | `injuryStatus`, injury history                                   |
| Upcoming opponents       | `nba_games`                   | derived by `teamId` + future games                               |
| Per-game stats           | `nba_player_game_stats`       | boxscore fields                                                  |
| Season totals            | `nba_player_season_stats`     | totals and optional averages                                     |

---

## Known Gaps for MVP

These attributes are not part of the current MVP schema.

- `birthDate`
- `birthPlace`
- `age`
- `photoUrl`
- `logoUrl`

They should be added only when a dedicated enrichment source is introduced in V2.

---

## Validation Checklist

Before considering this schema closed, validate these points:

1. One team roster query must be solvable through the `nba_players` team GSI with no join.
2. A full player season history must be solvable through `nba_player_game_stats` ordered by date.
3. A player season summary must be readable from exactly one `nba_player_season_stats` item.
4. Future opponents must be derivable from `nba_games` without needing `PlayerNextNGames`.
5. Injury history must be preserved in `nba_injuries` while the latest state is denormalized into `nba_players`.

---

## Related Documentation

- [GAME_ENDPOINTS.md](./GAME_ENDPOINTS.md) - source endpoint inventory
- [RESPONSE_SCHEMAS.md](./RESPONSE_SCHEMAS.md) - raw payload shapes
- [README.md](../README.md) - project overview
