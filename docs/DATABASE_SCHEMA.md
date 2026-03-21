# DynamoDB Schema Design - DEV-17

> **Purpose**: Optimized schema for NBA game and player statistics with field filtering  
> **Storage Optimization**: ~60% reduction through essential-fields-only approach  
> **Design Date**: February 2026  
> **Last Updated**: March 2026

---

## 📊 Schema Overview

```
┌─────────────────┐
│   nba_games     │  ← High-volume writes (1300+/season)
│   (PK: gameId)  │
└────────┬────────┘
         │
         │ Referenced by
         │
         ↓
┌─────────────────┐
│ nba_player_     │  ← Highest volume (50K+/season)
│ game_stats      │     Individual player performance
│ (PK: composite) │
└────────┬────────┘
         │
         │ References
         ↓
┌─────────────────┐       ┌─────────────────┐
│  nba_players    │       │   nba_teams     │
│ (PK: playerId)  │       │  (PK: teamId)   │
└─────────────────┘       └─────────────────┘
  ↑ Low update frequency    ↑ Rarely updates
```

---

## 🗂️ Table 1: `nba_games`

**Purpose**: Game schedules and final scores  
**Write Frequency**: ~1,300 games/season  
**Primary Key**: `gameId` (String)

### Essential Fields (9 fields, 72% reduction)

| Field | Type | Example | Source |
|-------|------|---------|--------|
| `gameId` | String | "0012500008" | ScheduleLeagueV2 |
| `gameDateEst` | String | "2025-10-02" | ScheduleLeagueV2 |
| `gameDateTimeEst` | String | "2025-10-02T12:00:00Z" | ScheduleLeagueV2 |
| `gameStatus` | Number | 3 | ScheduleLeagueV2 |
| `gameStatusText` | String | "Final" | ScheduleLeagueV2 |
| `homeTeam` | Map | `{teamId, teamName, score, wins, losses}` | ScheduleLeagueV2 |
| `awayTeam` | Map | `{teamId, teamName, score, wins, losses}` | ScheduleLeagueV2 |
| `arenaName` | String | "Crypto.com Arena" | ScheduleLeagueV2 |
| `arenaCity` | String | "Los Angeles" | ScheduleLeagueV2 |

**Removed Fields**: 24 non-essential fields (gameCode, gameSequence, gameTimeUTC, etc.)

### Data Example
```json
{
  "gameId": "0012500008",
  "gameDateEst": "2025-10-02",
  "gameDateTimeEst": "2025-10-02T12:00:00Z",
  "gameStatus": 3,
  "gameStatusText": "Final",
  "homeTeam": {
    "teamId": 1610612752,
    "teamName": "Knicks",
    "teamTricode": "NYK",
    "wins": 1,
    "losses": 0,
    "score": 99
  },
  "awayTeam": {
    "teamId": 1610612755,
    "teamName": "76ers",
    "teamTricode": "PHI",
    "wins": 0,
    "losses": 1,
    "score": 84
  },
  "arenaName": "Etihad Arena",
  "arenaCity": "Abu Dhabi"
}
```

---

## 👥 Table 2: `nba_players`

**Purpose**: Player directory and profile information  
**Write Frequency**: ~50 updates/season (roster changes)  
**Primary Key**: `playerId` (Number)

### Essential Fields (18 fields, 31% reduction)

| Field | Type | Example | Source |
|-------|------|---------|--------|
| `playerId` | Number | 2544 | PlayerIndex |
| `firstName` | String | "LeBron" | PlayerIndex |
| `lastName` | String | "James" | PlayerIndex |
| `teamId` | Number | 1610612747 | PlayerIndex |
| `teamName` | String | "Lakers" | PlayerIndex |
| `teamAbbreviation` | String | "LAL" | PlayerIndex |
| `jerseyNumber` | String | "23" | PlayerIndex |
| `position` | String | "F" | PlayerIndex |
| `height` | String | "6-9" | PlayerIndex |
| `weight` | String | "250" | PlayerIndex |
| `country` | String | "USA" | PlayerIndex |
| `college` | String | "St. Vincent-St. Mary HS" | PlayerIndex |
| `draftYear` | Number | 2003 | PlayerIndex |
| `draftRound` | Number | 1 | PlayerIndex |
| `draftNumber` | Number | 1 | PlayerIndex |
| `rosterStatus` | Number | 1 (active) | PlayerIndex |
| `fromYear` | Number | 2003 | PlayerIndex |
| `toYear` | Number | 2025 | PlayerIndex |

`rosterStatus` is the **only availability indicator** provided by nba_api (1 = active roster, 0 = inactive). The library does not expose injury reason, suspension reason, or detailed availability status (confirmed via exhaustive scan of all 139 stats + 4 live endpoints).

**Removed Fields**: 8 non-essential fields (PLAYER_SLUG, TEAM_SLUG, IS_DEFUNCT, etc.)

---

## 📈 Table 3: `nba_player_game_stats`

**Purpose**: Individual player performance per game  
**Write Frequency**: ~50,000 records/season (highest volume)  
**Primary Key**: `playerId#gameId` (Composite String)  
**Sort Key**: `gameDate` (String)

### Essential Fields (29 fields, 58% reduction)

| Category | Fields | Example Values |
|----------|--------|----------------|
| **Identity** | `playerId`, `playerName`, `teamId`, `teamAbbreviation` | 2544, "LeBron James", 1610612747, "LAL" |
| **Game Info** | `gameId`, `gameDate`, `matchup`, `wl`, `min` | "0012500001", "2025-10-03", "LAL vs. PHX", "L", 35.5 |
| **Shooting** | `fgm`, `fga`, `fg_pct`, `fg3m`, `fg3a`, `fg3_pct` | 10, 20, 0.500, 3, 8, 0.375 |
| **Free Throws** | `ftm`, `fta`, `ft_pct` | 5, 6, 0.833 |
| **Rebounds** | `oreb`, `dreb`, `reb` | 2, 8, 10 |
| **Other Stats** | `ast`, `stl`, `blk`, `blka`, `tov`, `pf`, `pfd`, `pts` | 8, 1, 0, 1, 3, 2, 5, 28 |

**Removed Fields**: 41 non-essential fields (all *_RANK fields, PLUS_MINUS, NBA_FANTASY_PTS, DD2, TD3, etc.)

### Composite Key Design
```
PK: "2544#0012500001"  (playerId#gameId)
SK: "2025-10-03"       (gameDate for sorting)
```

---

## 🏀 Table 4: `nba_teams`

**Purpose**: Team information and season rankings  
**Write Frequency**: ~900 updates/season (30 teams × ~30 updates)  
**Primary Key**: `teamId` (Number)

### Essential Fields

#### Team Info (12 fields, 25% reduction)
| Field | Type | Example | Source |
|-------|------|---------|--------|
| `teamId` | Number | 1610612747 | TeamInfoCommon |
| `seasonYear` | String | "2025-26" | TeamInfoCommon |
| `teamCity` | String | "Los Angeles" | TeamInfoCommon |
| `teamName` | String | "Lakers" | TeamInfoCommon |
| `teamAbbreviation` | String | "LAL" | TeamInfoCommon |
| `conference` | String | "West" | TeamInfoCommon |
| `division` | String | "Pacific" | TeamInfoCommon |
| `wins` | Number | 32 | TeamInfoCommon |
| `losses` | Number | 21 | TeamInfoCommon |
| `winPct` | Number | 0.604 | TeamInfoCommon |
| `confRank` | Number | 6 | TeamInfoCommon |
| `divRank` | Number | 1 | TeamInfoCommon |

#### Season Rankings (8 fields, 27% reduction)
| Field | Type | Example | Source |
|-------|------|---------|--------|
| `ptsRank` | Number | 14 | TeamInfoCommon |
| `ptsPg` | Number | 115.9 | TeamInfoCommon |
| `rebRank` | Number | 28 | TeamInfoCommon |
| `rebPg` | Number | 41.1 | TeamInfoCommon |
| `astRank` | Number | 22 | TeamInfoCommon |
| `astPg` | Number | 25.1 | TeamInfoCommon |
| `oppPtsRank` | Number | 18 | TeamInfoCommon |
| `oppPtsPg` | Number | 116.3 | TeamInfoCommon |

**Static Data** (from `nba_api.static.teams`): id, full_name, abbreviation, nickname, city, state, year_founded

---

## 🔄 Data Flow & Update Strategy

### Fetch Cadences

| Table | Update Frequency | Trigger | API Endpoint |
|-------|------------------|---------|--------------|
| `nba_games` | **Daily** | 3 AM ET | ScheduleLeagueV2 |
| `nba_players` | **Weekly** | Sundays 2 AM ET | PlayerIndex |
| `nba_player_game_stats` | **Daily** | Post-game (1 AM ET) | PlayerGameLogs |
| `nba_teams` | **Daily** | 3 AM ET | TeamInfoCommon |

### Update Logic
```python
# Pseudocode for daily updates
if new_game_completed():
    update_games_table(gameId)           # Update final score
    update_team_standings(teamId)        # Update W/L records
    for player in game_roster:
        update_player_stats(playerId, gameId)  # Bulk write stats
```

**Future optimization**: The current exploration script uses a single-player, full-season call (simple demo). In production (DEV-X) this will switch to dynamic `datetime`-based windows, e.g. compute `date_from`/`date_to` daily and pass them to `PlayerGameLogs(date_from_nullable=..., date_to_nullable=...)`, to avoid full-season re-fetches. Example: at 02:00 UTC set `date_from = today - 2 days`, `date_to = today` to capture late games and backfills; skip the call entirely when no games were played the previous day.

---

### Fantasy Game Requirements Coverage

The schema is designed to satisfy all data needs for the fantasy basketball application. The table below maps each game requirement to its corresponding source.

| Category | Requirement | Table | Field(s) |
|----------|-------------|-------|----------|
| **Scoring** | Points | nba_player_game_stats | `pts` |
| | 2PT Field Goals (made/attempted) | nba_player_game_stats | `fgm - fg3m` / `fga - fg3a` (derived) |
| | 3PT Field Goals (made/attempted) | nba_player_game_stats | `fg3m`, `fg3a` |
| | Free Throws (made/attempted) | nba_player_game_stats | `ftm`, `fta` |
| **Box Score** | Rebounds | nba_player_game_stats | `reb` (`oreb` + `dreb`) |
| | Assists | nba_player_game_stats | `ast` |
| | Steals | nba_player_game_stats | `stl` |
| | Turnovers | nba_player_game_stats | `tov` |
| | Blocks | nba_player_game_stats | `blk` |
| | Blocks Against | nba_player_game_stats | `blka` |
| | Personal Fouls | nba_player_game_stats | `pf` |
| | Fouls Drawn | nba_player_game_stats | `pfd` |
| | Minutes Played | nba_player_game_stats | `min` |
| **Player Profile** | Name, Position, Jersey # | nba_players | `firstName`, `lastName`, `position`, `jerseyNumber` |
| | Nationality, Height | nba_players | `country`, `height` |
| | Availability | nba_players | `rosterStatus` (only indicator available) |
| | Headshot Photo | nba_players | `playerId` → CDN: `cdn.nba.com/headshots/nba/latest/1040x760/{playerId}.png` |
| **Schedule** | Upcoming Opponents | PlayerNextNGames API | via `/players/next-games` endpoint |
| | Game Calendar & Results | nba_games | `gameDateEst`, `homeTeam`, `awayTeam`, `gameStatus` |
| | Teams & Logos | nba_teams | `teamName`, `teamAbbreviation` + CDN URL pattern |

> **Data not available via nba_api**: Birthplace (city), age/birth date, detailed injury reports. Country is available; birthdate/age would require an external source.

---

## 💾 Storage Optimization Summary

| Endpoint | Original Fields | Essential Fields | Reduction | Annual Records |
|----------|----------------|------------------|-----------|----------------|
| ScheduleLeagueV2 | 33 | 9 | **72%** | ~1,300 |
| PlayerIndex | 26 | 18 | **31%** | ~550 |
| PlayerGameLogs | 70 | 29 | **58%** | ~50,000 |
| PlayerNextNGames | 13 | 11 | **15%** | N/A (future) |
| TeamInfoCommon | 27 total | 20 total | **26%** | ~900 |

**Estimated Annual Savings**: ~60% storage reduction across all endpoints

---

## 🔍 Validation Status

✅ All 6 endpoints validated with **strict filtering**:
- ✅ Only essential fields present (no extras)
- ✅ All required fields included (no missing data)
- ✅ Validation passing: 6/6 endpoints

**Validation Command**: `python scripts/validate_endpoints.py`

---

## 📋 Next Steps

1. Implement DynamoDB table creation with Terraform/CDK
2. Create data persistence layer using filtered field lists
3. Implement batch write operations for `nba_player_game_stats`
4. Set up daily Lambda triggers for data updates
5. Add TTL for `PlayerNextNGames` (7-day expiration)

> **Note**: The Flask API with S3 raw persistence, scheduled ingestion jobs, and JSON Schema validation were implemented in DEV-16. This schema design feeds into the next phase where raw S3 payloads are transformed and written to DynamoDB.

---

## 📚 Related Documentation

- [GAME_ENDPOINTS.md](./GAME_ENDPOINTS.md) - API endpoint specifications
- [README.md](../README.md) - Project overview and setup
- Exploration script: `scripts/explore_endpoints.py`
- Validation script: `scripts/validate_endpoints.py`
