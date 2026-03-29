# DEV-17 - NBA Data Design (Minimal)

This README captures the DEV-17 design decision for data we need from nba_api, how to minimize calls, and how to persist in DynamoDB.

## 1) Data Needed For The Game

Based on GAME_ENDPOINTS.md, the required domains are:

- Schedule and results
- Teams and identifiers
- Player directory and roster status
- Per-game player stats (main fantasy scoring source)
- Player upcoming games

Important limitation:

- nba_api does not provide official detailed injury reports.
- Availability inside nba_api is only roster status from PlayerIndex.

## 2) Endpoints And Response Schemas To Use

Tier 1 (ID providers, low dependency):

- ScheduleLeagueV2
- PlayerIndex
- Teams static module

Tier 2 (depends on Tier 1 IDs):

- PlayerGameLogs (requires PERSON_ID)
- PlayerNextNGames (requires PERSON_ID)
- TeamInfoCommon (requires team ID)

Minimal response schema definitions (essential fields only):

- ScheduleLeagueV2 item:
	gameId, gameDateEst, gameDateTimeEst, gameStatus, gameStatusText, homeTeam{teamId, teamName, teamTricode, wins, losses, score}, awayTeam{teamId, teamName, teamTricode, wins, losses, score}, arenaName, arenaCity
- PlayerIndex item:
	PERSON_ID, PLAYER_FIRST_NAME, PLAYER_LAST_NAME, TEAM_ID, TEAM_NAME, TEAM_ABBREVIATION, JERSEY_NUMBER, POSITION, HEIGHT, WEIGHT, COUNTRY, COLLEGE, DRAFT_YEAR, DRAFT_ROUND, DRAFT_NUMBER, ROSTER_STATUS, FROM_YEAR, TO_YEAR
- PlayerGameLogs item:
	PLAYER_ID, PLAYER_NAME, TEAM_ID, TEAM_ABBREVIATION, GAME_ID, GAME_DATE, MATCHUP, WL, MIN, FGM, FGA, FG_PCT, FG3M, FG3A, FG3_PCT, FTM, FTA, FT_PCT, OREB, DREB, REB, AST, STL, BLK, BLKA, TOV, PF, PFD, PTS
- PlayerNextNGames item:
	GAME_ID, GAME_DATE, GAME_TIME, HOME_TEAM_ID, HOME_TEAM_NAME, HOME_TEAM_ABBREVIATION, HOME_WL, VISITOR_TEAM_ID, VISITOR_TEAM_NAME, VISITOR_TEAM_ABBREVIATION, VISITOR_WL

Reference:

- docs/GAME_ENDPOINTS.md

## 3) Strategy For Fewest nba_api Calls

Use dependency-first ingestion with incremental updates.

1. Fetch Tier 1 first (small number of calls).
2. Cache extracted IDs (player IDs, team IDs, game IDs).
3. For Tier 2, call only active/relevant player IDs, not full universe every run.
4. Use date windows for PlayerGameLogs (date_from/date_to) to fetch only new games.
5. Skip Tier 2 runs when schedule indicates no games since last successful ingestion.
6. Store last successful watermark per dataset (for example: last_game_date_ingested).

This avoids full-season re-fetches and keeps API usage low.

## 4) DynamoDB Persistence Proposal

Minimal table design:

1. nba_games
- PK: gameId (S)
- Core fields: gameDateEst, gameStatus, homeTeam, awayTeam, scores

2. nba_players
- PK: playerId (N)
- Core fields: name, team, position, rosterStatus, profile metadata

3. nba_player_game_stats
- PK: playerId (N)
- SK: gameDate#gameId (S)
- Core fields: fantasy scoring stats (pts, reb, ast, stl, blk, tov, fg/ft/3pt, pfd, blka, min)

4. nba_player_next_games
- PK: playerId (N)
- SK: gameDate#gameId (S)
- Core fields: upcoming opponent and kickoff time

Optional GSIs (if query patterns require them):

- GSI by gameId for reverse lookup of all player stats in one game
- GSI by teamAbbreviation + gameDate for team/day views

Expanded schema notes:

- docs/DATABASE_SCHEMA.md

## 5) Implementation Notes

- Keep whitelist field filtering before persistence to reduce storage and write costs.
- Persist only essential fields listed in docs/GAME_ENDPOINTS.md.
- Use idempotent upserts keyed by PK/SK to support retries safely.

## 6) Scope Boundary

DEV-17 covers design and schema definition.

- Included: endpoint selection, response schema references, call-minimization strategy, DynamoDB model.
- Not included: full production ingestion orchestration and AWS trigger automation.