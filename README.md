# bball-app-nba_api_client

A Flask-based API server that consumes the [nba_api](https://github.com/swar/nba_api) repository to provide NBA basketball data endpoints.

## Features

- RESTful API server built with Flask
- Integration with nba_api library
- ScheduleLeagueV2 endpoint implementation
- Health check endpoint
- Easy to extend with additional NBA API endpoints

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/fermar8/bball-app-nba_api_client.git
cd bball-app-nba_api_client
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Running the Server

Start the Flask server:
```bash
python server.py
```

The server will start on `http://localhost:5000`

**Development Mode**: To enable debug mode during development:
```bash
FLASK_DEBUG=1 python server.py
```

> **Note**: Debug mode should NEVER be enabled in production as it poses security risks.

### Available Endpoints

#### 1. Root Endpoint
- **URL**: `/`
- **Method**: GET
- **Description**: Returns API information and available endpoints
- **Example**:
```bash
curl http://localhost:5000/
```

#### 2. Health Check
- **URL**: `/health`
- **Method**: GET
- **Description**: Returns server health status
- **Example**:
```bash
curl http://localhost:5000/health
```

#### 3. NBA Schedule
- **URL**: `/schedule`
- **Method**: GET
- **Description**: Returns NBA league schedule data using the ScheduleLeagueV2 endpoint
- **Query Parameters**:
  - `season` (optional): Season year in YYYY format (e.g., 2023 for 2023-24 season)
- **Examples**:
```bash
# Get current season schedule
curl http://localhost:5000/schedule

# Get specific season schedule
curl http://localhost:5000/schedule?season=2023
```

## Dependencies

- **nba_api**: Official Python client for NBA statistics
- **Flask**: Web framework for building the REST API server

## Development

### Project Structure

```
bball-app-nba_api_client/
├── server.py              # Main Flask application
├── requirements.txt       # Python dependencies
├── test_integration.py    # Integration tests
├── README.md             # This file
└── .gitignore            # Git ignore rules
```

## Data Extraction (DEV-17)

This repository uses the nba_api endpoints documented in [docs/GAME_ENDPOINTS.md](docs/GAME_ENDPOINTS.md).
Endpoints are organized into Tier 1 (ID providers) and Tier 2 (parameterized, requires Tier 1 IDs).

### Data Collection Strategy

- **Tier 1 (ID Providers)**
  - ScheduleLeagueV2 → provides `gameId` for future use (fetch daily during season)
  - PlayerIndex → provides `PERSON_ID` for player-specific endpoints (fetch weekly or on roster changes)
  - Teams (static) → provides `TEAM_ID` for team info (fetch once per season; static module)
- **Tier 2 (Parameterized)**
  - PlayerGameLogs → uses `PERSON_ID` (fetch incrementally using date_from/date_to)
  - PlayerNextNGames → uses `PERSON_ID` (fetch on slower cadence, e.g., daily/weekly)
  - TeamInfoCommon → uses `TEAM_ID` (fetch daily for standings)

Static data is overwritten (low frequency updates). Dynamic data is date-partitioned (high frequency updates).
Key optimizations: **incremental updates** (only fetch new games) and **field filtering** (store essential fields only).

### DynamoDB Schema

This structure minimizes tables and writes while still satisfying Tier 1 → Tier 2 dependencies.

1. **Games** (ScheduleLeagueV2)
  - **PK:** `GAME_DATE`
  - **SK:** `GAME_ID`
  - **Use case:** query all games on a date, or one game by ID

2. **Players** (PlayerIndex)
  - **PK:** `PERSON_ID`
  - **GSI:** `TEAM_ID` (list players by team)
  - **Use case:** player directory and roster lookup

3. **PlayerGameStats** (PlayerGameLogs)
  - **PK:** `PERSON_ID`
  - **SK:** `GAME_DATE` (or `GAME_ID`)
  - **Use case:** all games and stats for a player, sorted by date

4. **Teams** (Teams static + TeamInfoCommon)
  - **PK:** `TEAM_ID`
  - **SK:** `SEASON`
  - **Use case:** team metadata and season rankings

Field filtering is recommended (see docs/GAME_ENDPOINTS.md) to reduce storage costs.

### Response Schemas (Minimal)

The canonical response schemas (essential fields) are defined in [docs/GAME_ENDPOINTS.md](docs/GAME_ENDPOINTS.md).
To view real examples, run `explore_endpoints.py` (it writes sample JSON under `exploration_output/`, which is ignored by git).

### Persistence Mapping (DynamoDB)

- **ScheduleLeagueV2 → Games table**
  - PK: `GAME_DATE`, SK: `GAME_ID`
  - Store: essential schedule fields only

- **PlayerIndex → Players table**
  - PK: `PERSON_ID` (GSI on `TEAM_ID`)
  - Store: essential player metadata only

- **PlayerGameLogs → PlayerGameStats table**
  - PK: `PERSON_ID`, SK: `GAME_DATE`
  - Store: essential per-game stats only

- **PlayerNextNGames → Players table (embedded list)**
  - Store: upcoming games as a small list per player (overwrite)

- **Teams static + TeamInfoCommon → Teams table**
  - PK: `TEAM_ID`, SK: `SEASON`
  - Store: static team info + season rankings


## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the MIT License.

## Acknowledgments

- [nba_api](https://github.com/swar/nba_api) - The official Python client for NBA statistics