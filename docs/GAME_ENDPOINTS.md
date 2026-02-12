# NBA API Endpoints for Fantasy Basketball Game

This document describes the NBA API endpoints required to build a fantasy basketball game, organized by dependency chain and optimized for cost-effective data storage.

## Table of Contents

- [Overview](#overview)
- [Dependency Chain Workflow](#dependency-chain-workflow)
- [Tier 1: ID Provider Endpoints](#tier-1-id-provider-endpoints)
- [Tier 2: Parameterized Endpoints](#tier-2-parameterized-endpoints)
- [Essential Fields Reference](#essential-fields-reference)
- [S3 Storage Structure](#s3-storage-structure)
- [Limitations & Workarounds](#limitations--workarounds)
- [Future Enhancements](#future-enhancements)
- [Usage Instructions](#usage-instructions)

## Overview

The endpoints are organized into two tiers based on their dependency requirements:

- **Tier 1 (ID Providers)**: Endpoints that require no parameters and provide IDs for other endpoints
- **Tier 2 (Parameterized)**: Endpoints that require IDs from Tier 1 endpoints

This structure allows for efficient data fetching while minimizing API calls and storage costs by filtering out unnecessary fields.

## Dependency Chain Workflow

```
Tier 1: ID Providers
├── ScheduleLeagueV2 ────────> gameId ───> (Future: BoxScore endpoints)
├── PlayerIndex ─────────────> PERSON_ID ─> PlayerGameLogs
│                                         └> PlayerNextNGames
└── Teams (static module) ───> id ───────> TeamInfoCommon
                                         └> (For logo URL construction)

Tier 2: Parameterized Endpoints
├── PlayerGameLogs(player_id, season)
└── PlayerNextNGames(player_id)
```

## Tier 1: ID Provider Endpoints

These endpoints can be fetched immediately without parameters and provide the foundation data for your game.

### 1. ScheduleLeagueV2

**Full NBA season schedule with game results**

- **Module**: `nba_api.stats.endpoints.scheduleleaguev2`
- **Class**: `ScheduleLeagueV2`
- **Type**: Stats endpoint
- **Required Parameters**:
  - `season` (e.g., "2025-26")
- **Optional Parameters**:
  - `league_id` (default: "00" for NBA)

**Essential Fields** (from `SeasonGames` dataset):

- `gameId` - **ID FIELD** → Used for BoxScore endpoints (future)
- `gameDate` - Game date
- `gameDateTimeEst` - Game date and time (EST)
- `gameStatus` - Game status code (1=scheduled, 2=live, 3=final)
- `gameStatusText` - Human-readable status
- `homeTeam_teamId` - Home team ID
- `homeTeam_teamName` - Home team name
- `homeTeam_teamTricode` - Home team abbreviation (e.g., "LAL")
- `homeTeam_wins` - Home team win count
- `homeTeam_losses` - Home team loss count
- `homeTeam_score` - Home team score (if game completed)
- `awayTeam_teamId` - Away team ID
- `awayTeam_teamName` - Away team name
- `awayTeam_teamTricode` - Away team abbreviation
- `awayTeam_wins` - Away team win count
- `awayTeam_losses` - Away team loss count
- `awayTeam_score` - Away team score (if game completed)
- `arenaName` - Arena name
- `arenaCity` - Arena city
- `arenaState` - Arena state

**Fields to Filter Out**:

- All broadcaster fields (unless needed for specific features)
- `pointsLeaders` (redundant with player stats)
- `gameSequence`, `weekNumber`, `weekName`, `gameLabel`, `gameSubLabel`, `seriesText` (unless displaying detailed schedule)

**Data Category**: Dynamic (date-partitioned)

---

### 2. PlayerIndex

**Comprehensive player directory with filtering capabilities**

- **Module**: `nba_api.stats.endpoints.playerindex`
- **Class**: `PlayerIndex`
- **Type**: Stats endpoint
- **Required Parameters**:
  - `season` (e.g., "2025-26")
- **Optional Parameters**:
  - `league_id` (default: "00")
  - `active_nullable` (filter active/inactive players)
  - `country_nullable` (filter by country)
  - `player_position_abbreviation_nullable` (filter by position)

**Essential Fields** (from `PlayerIndex` dataset):

- `PERSON_ID` - **ID FIELD** → Used for PlayerGameLogs, PlayerNextNGames, and photo URLs
- `PLAYER_FIRST_NAME` - Player first name
- `PLAYER_LAST_NAME` - Player last name
- `TEAM_ID` - Current team ID
- `TEAM_NAME` - Current team name
- `TEAM_ABBREVIATION` - Team abbreviation
- `JERSEY_NUMBER` - Jersey number
- `POSITION` - Position (e.g., "G", "F", "C", "G-F")
- `HEIGHT` - Height (e.g., "6-6")
- `WEIGHT` - Weight in pounds
- `COUNTRY` - Nationality/country
- `COLLEGE` - College attended
- `DRAFT_YEAR` - Draft year
- `DRAFT_ROUND` - Draft round
- `DRAFT_NUMBER` - Draft pick number
- `ROSTER_STATUS` - **Availability indicator** (1=active roster, 0=inactive)
- `FROM_YEAR` - First year in NBA
- `TO_YEAR` - Last/current year in NBA

**Fields to Filter Out**:

- `PLAYER_SLUG`, `TEAM_SLUG`, `TEAM_CITY`, `IS_DEFUNCT` (redundant)
- `PTS`, `REB`, `AST`, `STATS_TIMEFRAME` (use PlayerGameLogs for stats)

**Data Category**: Static (overwrite latest)

---

### 3. Teams (Static Module)

**Basic team information from static data**

- **Module**: `nba_api.stats.static.teams`
- **Functions**: `get_teams()`, `find_team_by_abbreviation()`, `find_teams_by_city()`
- **Type**: Static data (no API call)
- **Parameters**: None

**Essential Fields** (from static data):

- `id` - **ID FIELD** → Used for TeamInfoCommon and logo URL construction
- `full_name` - Full team name (e.g., "Los Angeles Lakers")
- `abbreviation` - Team abbreviation (e.g., "LAL")
- `nickname` - Team nickname (e.g., "Lakers")
- `city` - Team city
- `state` - Team state
- `year_founded` - Year team was founded

**Fields to Filter Out**: None (all fields are minimal)

**Data Category**: Static (overwrite latest)

---

## Tier 2: Parameterized Endpoints

These endpoints require IDs obtained from Tier 1 endpoints. Currently requires manual implementation or future chained fetching enhancement.

### 1. PlayerGameLogs

**Complete player game-by-game statistics (PRIMARY STATS SOURCE)**

- **Module**: `nba_api.stats.endpoints.playergamelogs`
- **Class**: `PlayerGameLogs`
- **Type**: Stats endpoint
- **Required Parameters**:
  - `player_id_nullable` - Player ID from PlayerIndex (`PERSON_ID`)
- **Optional Parameters**:
  - `season_nullable` (e.g., "2025-26")
  - `season_type_nullable` ("Regular Season", "Playoffs", "All Star")
  - `date_from_nullable`, `date_to_nullable` (date range filter)

**Essential Fields** (from `PlayerGameLogs` dataset):

- `PLAYER_ID` - Player ID
- `PLAYER_NAME` - Player name
- `TEAM_ID` - Team ID
- `TEAM_ABBREVIATION` - Team abbreviation
- `GAME_ID` - Game ID
- `GAME_DATE` - Game date
- `MATCHUP` - Matchup description (e.g., "LAL vs. BOS")
- `WL` - Win/Loss
- `MIN` - **Minutes played**
- `FGM` - **Field goals made**
- `FGA` - **Field goals attempted**
- `FG_PCT` - Field goal percentage
- `FG3M` - **3-pointers made**
- `FG3A` - **3-pointers attempted**
- `FG3_PCT` - 3-point percentage
- `FTM` - **Free throws made**
- `FTA` - **Free throws attempted**
- `FT_PCT` - Free throw percentage
- `OREB` - **Offensive rebounds**
- `DREB` - **Defensive rebounds**
- `REB` - **Total rebounds**
- `AST` - **Assists**
- `STL` - **Steals**
- `BLK` - **Blocks**
- `BLKA` - **Blocks against** (blocks received)
- `TOV` - **Turnovers**
- `PF` - **Personal fouls committed**
- `PFD` - **Personal fouls drawn**
- `PTS` - **Points**

**Fields to Filter Out** (cost savings):

- All `*_RANK` fields (GP_RANK, W_RANK, L_RANK, W_PCT_RANK, MIN_RANK, FGM_RANK, etc.) - ~30 fields
- `PLUS_MINUS` (unless needed for advanced stats)
- `NBA_FANTASY_PTS` (can be calculated if needed)
- `DD2`, `TD3` (double-double, triple-double flags - can be calculated)

**Note**: 2-point field goals can be calculated as `FGM - FG3M` (made) and `FGA - FG3A` (attempted)

**Data Category**: Dynamic (date-partitioned per player)

---

### 2. PlayerNextNGames

**Upcoming games for a specific player**

- **Module**: `nba_api.stats.endpoints.playernextngames`
- **Class**: `PlayerNextNGames`
- **Type**: Stats endpoint
- **Required Parameters**:
  - `player_id` - Player ID from PlayerIndex (`PERSON_ID`)
- **Optional Parameters**:
  - `number_of_games` (default: 5)
  - `season` (default: current season)
  - `season_type` (default: "Regular Season")

**Essential Fields** (from `NextNGames` dataset):

- `GAME_ID` - Game ID
- `GAME_DATE` - Game date
- `GAME_TIME` - Game time
- `HOME_TEAM_ID` - Home team ID
- `HOME_TEAM_NAME` - Home team name
- `HOME_TEAM_ABBREVIATION` - Home team abbreviation
- `HOME_WL` - Home team win-loss record
- `VISITOR_TEAM_ID` - Visitor team ID
- `VISITOR_TEAM_NAME` - Visitor team name
- `VISITOR_TEAM_ABBREVIATION` - Visitor team abbreviation
- `VISITOR_WL` - Visitor team win-loss record

**Fields to Filter Out**:

- `HOME_TEAM_NICKNAME`, `VISITOR_TEAM_NICKNAME` (redundant with team name)

**Data Category**: Dynamic (date-partitioned per player)

---

### 3. TeamInfoCommon

**Current season team information and rankings**

- **Module**: `nba_api.stats.endpoints.teaminfocommon`
- **Class**: `TeamInfoCommon`
- **Type**: Stats endpoint
- **Required Parameters**:
  - `team_id` - Team ID from Teams static module
- **Optional Parameters**:
  - `season_nullable` (e.g., "2025-26")
  - `season_type_nullable` (default: "Regular Season")

**Essential Fields** (from `TeamInfoCommon` dataset):

- `TEAM_ID` - Team ID
- `SEASON_YEAR` - Season year
- `TEAM_CITY` - Team city
- `TEAM_NAME` - Team name
- `TEAM_ABBREVIATION` - Team abbreviation
- `TEAM_CONFERENCE` - Conference (East/West)
- `TEAM_DIVISION` - Division
- `W` - Wins
- `L` - Losses
- `PCT` - Win percentage
- `CONF_RANK` - Conference rank
- `DIV_RANK` - Division rank

**Essential Fields** (from `TeamSeasonRanks` dataset):

- `PTS_RANK` - Points per game rank
- `PTS_PG` - Points per game
- `REB_RANK` - Rebounds per game rank
- `REB_PG` - Rebounds per game
- `AST_RANK` - Assists per game rank
- `AST_PG` - Assists per game
- `OPP_PTS_RANK` - Opponent points rank
- `OPP_PTS_PG` - Opponent points per game

**Fields to Filter Out**:

- `TEAM_CODE` (redundant)
- `MIN_YEAR`, `MAX_YEAR` (unless showing team history)

**Data Category**: Dynamic (date-partitioned)

---

## Essential Fields Reference

### For Fantasy Game Requirements

Based on your Supermanager ACB data requirements, here's the mapping:

| Required Data         | Endpoint                        | Field Name(s)                                    |
| --------------------- | ------------------------------- | ------------------------------------------------ |
| **Calendar/Schedule** |                                 |                                                  |
| Full schedule         | ScheduleLeagueV2                | `gameDate`, `gameDateTimeEst`                    |
| Teams in game         | ScheduleLeagueV2                | `homeTeam_*`, `awayTeam_*`                       |
| Game results          | ScheduleLeagueV2                | `gameStatus`, `homeTeam_score`, `awayTeam_score` |
| Game times            | ScheduleLeagueV2                | `gameDateTimeEst`, `gameTimeEst`                 |
| **Teams**             |                                 |                                                  |
| Team names            | Teams static / ScheduleLeagueV2 | `full_name`, `abbreviation`                      |
| Team logos            | Teams static                    | `id` → construct URL                             |
| **Players**           |                                 |                                                  |
| Names                 | PlayerIndex                     | `PLAYER_FIRST_NAME`, `PLAYER_LAST_NAME`          |
| Photos                | PlayerIndex                     | `PERSON_ID` → construct URL                      |
| Position              | PlayerIndex                     | `POSITION`                                       |
| Nationality           | PlayerIndex                     | `COUNTRY`                                        |
| Jersey number         | PlayerIndex                     | `JERSEY_NUMBER`                                  |
| Height                | PlayerIndex                     | `HEIGHT`                                         |
| Birthplace            | N/A                             | Not available in API                             |
| Availability          | PlayerIndex                     | `ROSTER_STATUS`                                  |
| Upcoming opponents    | PlayerNextNGames                | `HOME_TEAM_*`, `VISITOR_TEAM_*`                  |
| **Player Statistics** |                                 |                                                  |
| Points                | PlayerGameLogs                  | `PTS`                                            |
| 2-pointers            | PlayerGameLogs                  | Calculate: `FGM - FG3M`, `FGA - FG3A`            |
| 3-pointers            | PlayerGameLogs                  | `FG3M`, `FG3A`                                   |
| Free throws           | PlayerGameLogs                  | `FTM`, `FTA`                                     |
| Rebounds              | PlayerGameLogs                  | `REB` (or `OREB` + `DREB`)                       |
| Assists               | PlayerGameLogs                  | `AST`                                            |
| Steals                | PlayerGameLogs                  | `STL`                                            |
| Turnovers             | PlayerGameLogs                  | `TOV`                                            |
| Blocks                | PlayerGameLogs                  | `BLK`                                            |
| Blocks against        | PlayerGameLogs                  | `BLKA`                                           |
| Fouls committed       | PlayerGameLogs                  | `PF`                                             |
| Fouls drawn           | PlayerGameLogs                  | `PFD`                                            |
| Minutes played        | PlayerGameLogs                  | `MIN`                                            |

---

## S3 Storage Structure

### Recommended Folder Structure

```
nba-data/
├── schedule/
│   └── {season}/
│       └── {YYYY-MM-DD}/
│           └── {HH-MM-SS}.json
├── players/
│   └── latest.json                    # Overwrite (static data)
├── teams/
│   └── latest.json                    # Overwrite (static data)
├── player-stats/
│   └── {player_id}/
│       └── {season}/
│           └── {YYYY-MM-DD}/
│               └── {HH-MM-SS}.json
├── player-info/
│   └── {player_id}/
│       └── latest.json                # Overwrite per player
└── upcoming-games/
    └── {player_id}/
        └── {YYYY-MM-DD}/
            └── {HH-MM-SS}.json
```

### Storage Category Guidelines

**Dynamic Data (Date-Partitioned)**:

- ScheduleLeagueV2 → Updates daily during season
- PlayerGameLogs → New stats after each game
- PlayerNextNGames → Updates as schedule changes
- TeamInfoCommon → Updates as standings change

**Static Data (Overwrite Latest)**:

- PlayerIndex → Infrequent changes (trades, signings)
- Teams static → Rarely changes

**Cost Optimization**: Static data uses single file overwrite to avoid storing duplicate data. Dynamic data uses date partitioning for historical tracking.

---

## Limitations & Workarounds

### Data Not Available in API

1. **Player Photos**
   - **Workaround**: Construct CDN URL using player ID
   - **Pattern**: `https://cdn.nba.com/headshots/nba/latest/1040x760/{PERSON_ID}.png`
   - **Example**: `https://cdn.nba.com/headshots/nba/latest/1040x760/2544.png` (LeBron James)
   - **Fallback**: `https://cdn.nba.com/headshots/nba/latest/1040x760/logoman.png`

2. **Team Logos**
   - **Workaround**: Construct CDN URL using team ID
   - **Pattern**: `https://cdn.nba.com/logos/nba/{team_id}/primary/L/logo.svg`
   - **Example**: `https://cdn.nba.com/logos/nba/1610612747/primary/L/logo.svg` (Lakers)
   - **Alternative**: `https://cdn.nba.com/logos/nba/{team_id}/global/L/logo.svg`

3. **Player Birthplace (City)**
   - **Status**: Not available in API
   - **Available**: `COUNTRY` field in PlayerIndex
   - **Workaround**: Display country only, or use external data source

4. **Detailed Injury Reports**
   - **Status**: No dedicated injury endpoint
   - **Available**: `ROSTER_STATUS` in PlayerIndex (active/inactive indicator)
   - **Workaround**: Use `ROSTER_STATUS` as approximation, or use external injury data sources

---

## Future Enhancements

### 1. Chained Fetching Implementation

Currently, Tier 2 endpoints require manual implementation because they need parameters from Tier 1 results. A future enhancement would automate this process.

**Example Implementation**:

```python
# In scripts/fetch_and_upload.py or new scripts/fetch_game_data.py

def fetch_with_dependencies(config, s3_client, bucket_name):
    """
    Fetch endpoints with automatic dependency resolution.
    """
    # Step 1: Fetch all Tier 1 endpoints (no parameters needed)
    tier1_results = {}

    for endpoint in config.get('tier1_endpoints', []):
        data = fetch_endpoint_data(endpoint)
        tier1_results[endpoint['name']] = data
        upload_to_s3(data, endpoint, s3_client, bucket_name)

    # Step 2: Extract IDs from Tier 1 results
    player_ids = extract_field(tier1_results['PlayerIndex'], 'PERSON_ID')
    game_ids = extract_field(tier1_results['ScheduleLeagueV2'], 'gameId')
    team_ids = [team['id'] for team in tier1_results.get('Teams', [])]

    # Step 3: Fetch Tier 2 endpoints using extracted IDs
    for endpoint in config.get('tier2_endpoints', []):
        if endpoint['id_source'] == 'player':
            for player_id in player_ids:
                data = fetch_endpoint_data(endpoint, player_id=player_id)
                # Filter fields before upload
                filtered_data = filter_essential_fields(data, endpoint['essential_fields'])
                upload_to_s3(filtered_data, endpoint, s3_client, bucket_name)
```

### 2. Data Transformation and Field Filtering

To minimize S3 storage costs, implement field filtering before upload.

**Example Whitelist Transformation**:

```python
def filter_essential_fields(data, essential_fields):
    """
    Filter API response to include only essential fields.

    Args:
        data: Full API response dictionary
        essential_fields: List of field names to keep

    Returns:
        Filtered data with only essential fields
    """
    if 'resultSets' in data:
        # Handle NBA Stats API format
        for result_set in data['resultSets']:
            if 'rowSet' in result_set:
                headers = result_set['headers']
                # Find indices of essential fields
                essential_indices = [
                    i for i, header in enumerate(headers)
                    if header in essential_fields
                ]
                # Filter headers
                result_set['headers'] = [headers[i] for i in essential_indices]
                # Filter rows
                result_set['rowSet'] = [
                    [row[i] for i in essential_indices]
                    for row in result_set['rowSet']
                ]

    return data


# Usage in endpoints_config.json:
{
  "name": "player_game_logs",
  "module": "nba_api.stats.endpoints.playergamelogs",
  "class": "PlayerGameLogs",
  "essential_fields": [
    "PLAYER_ID", "PLAYER_NAME", "GAME_ID", "GAME_DATE",
    "MIN", "PTS", "FGM", "FGA", "FG3M", "FG3A",
    "FTM", "FTA", "REB", "AST", "STL", "BLK",
    "BLKA", "TOV", "PF", "PFD"
  ]
}
```

**Storage Impact Example** (PlayerGameLogs):

- Full response: ~70 fields per game
- Essential fields: ~20 fields per game
- **Storage reduction: ~70%**

For a player with 82 games:

- Full data: ~82 games × 70 fields = 5,740 data points
- Filtered data: ~82 games × 20 fields = 1,640 data points
- **Cost savings: 71% reduction**

### 3. Batch Processing for Multiple Players

```python
def fetch_player_stats_batch(player_ids, season, essential_fields):
    """
    Fetch stats for multiple players in batch.
    """
    all_stats = []

    for player_id in player_ids:
        try:
            stats = PlayerGameLogs(
                player_id_nullable=player_id,
                season_nullable=season
            )
            filtered = filter_essential_fields(
                stats.get_dict(),
                essential_fields
            )
            all_stats.append({
                'player_id': player_id,
                'data': filtered
            })
        except Exception as e:
            logger.error(f"Failed to fetch stats for player {player_id}: {e}")
            continue

    return all_stats
```

### 4. Incremental Updates

Only fetch new games instead of full season:

```python
# Fetch only games after last update
last_update_date = get_last_update_date(s3_client, bucket_name)

stats = PlayerGameLogs(
    player_id_nullable=player_id,
    season_nullable="2025-26",
    date_from_nullable=last_update_date  # Only new games
)
```

---

## Usage Instructions

### Current Implementation (Tier 1 Only)

The current `scripts/fetch_and_upload.py` script supports Tier 1 endpoints without parameters.

**Prerequisites**:

1. Set environment variable: `AWS_S3_BUCKET_NAME`
2. Configure AWS credentials (via environment or ~/.aws/credentials)
3. Install dependencies: `pip install nba-api boto3`

**Configuration**:

Edit `scripts/endpoints_config.json` to enable/disable endpoints:

```json
{
  "endpoints": [
    {
      "name": "schedule",
      "type": "stats",
      "module": "nba_api.stats.endpoints.scheduleleaguev2",
      "class": "ScheduleLeagueV2",
      "enabled": true,
      "description": "Full season schedule",
      "essential_fields": [
        "gameId",
        "gameDate",
        "gameDateTimeEst",
        "gameStatus",
        "homeTeam_teamId",
        "homeTeam_teamName",
        "homeTeam_teamTricode",
        "homeTeam_score",
        "awayTeam_teamId",
        "awayTeam_teamName",
        "awayTeam_teamTricode",
        "awayTeam_score"
      ]
    }
  ]
}
```

**Run the script**:

```bash
# Windows PowerShell
$env:AWS_S3_BUCKET_NAME="your-bucket-name"
python scripts/fetch_and_upload.py

# Linux/Mac
export AWS_S3_BUCKET_NAME="your-bucket-name"
python scripts/fetch_and_upload.py
```

### Response Schema Reference

See `scripts/response_schemas.md` for detailed documentation of all response formats, including:

- Example responses for each endpoint
- ID field locations for dependency chaining
- Fantasy-relevant stat field descriptions
- Storage impact analysis per endpoint

### Response Schema Files

Example response structures are available in `scripts/`:

- `response_schema_scheduleleaguev2.json` - Full season schedule
- `response_schema_playerindex.json` - Player directory
- `response_schema_playergamelogs.json` - Game-by-game stats
- `response_schema_playernextngames.json` - Upcoming games

---

## Summary

### Minimum Viable Product (MVP) Endpoints

For the fantasy game MVP, you need these endpoints:

**Tier 1** (Can fetch now):

1. ✅ **ScheduleLeagueV2** - Full schedule with results
2. ✅ **PlayerIndex** - Player directory with all details
3. ✅ **Teams (static)** - Team information

**Tier 2** (Requires chained fetching implementation):

4. ⏳ **PlayerGameLogs** - Complete stats including BLKA, PFD (PRIMARY STATS)
5. ⏳ **PlayerNextNGames** - Upcoming opponents per player

### Cost Optimization

- **Filter fields**: Keep only 20-25 essential fields instead of 70+ per endpoint
- **Storage savings**: ~70% reduction in S3 storage costs
- **Use whitelist approach**: Explicitly select needed fields (more efficient than blacklist)
- **Static data**: Overwrite instead of versioning (PlayerIndex, Teams)
- **Dynamic data**: Date-partition only time-sensitive data (schedule, game logs)

### Next Steps

1. ✅ Review essential fields and adjust if needed
2. ⏳ Implement field filtering in fetch_and_upload.py
3. ⏳ Implement chained fetching for Tier 2 endpoints
4. ⏳ Test with small data set before full season fetch
5. ⏳ Monitor S3 costs and adjust filtering as needed
