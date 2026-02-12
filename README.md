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

## Project Structure

```
bball-app-nba_api_client/
├── scripts/               # Utility scripts
│   ├── explore_endpoints.py    # API exploration + field filtering
│   └── validate_endpoints.py   # Data validation (strict)
├── tests/                 # Test suite
│   └── test_integration.py    # Integration tests
├── docs/                  # Documentation
│   ├── GAME_ENDPOINTS.md      # API endpoint specifications
│   └── DATABASE_SCHEMA.md     # DynamoDB schema design
├── exploration_output/    # Generated sample data (gitignored)
├── server.py             # Flask API server
├── requirements.txt      # Python dependencies
└── README.md             # This file
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
The complete DynamoDB schema design with field optimization is in [docs/DATABASE_SCHEMA.md](docs/DATABASE_SCHEMA.md).

### Quick Start

**Explore endpoints and see field filtering in action:**
```bash
python scripts/explore_endpoints.py
```

**Validate filtered data (strict mode - no extra fields):**
```bash
python scripts/validate_endpoints.py
```

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
Key optimizations: **incremental updates** (only fetch new games) and **field filtering** (~60% storage reduction).

### DynamoDB Schema

**Full schema documentation:** [docs/DATABASE_SCHEMA.md](docs/DATABASE_SCHEMA.md)

This structure minimizes tables and writes while still satisfying Tier 1 → Tier 2 dependencies.

1. **nba_games** (ScheduleLeagueV2)
  - **PK:** `gameId`
  - **Essential fields:** 9 (72% reduction from 33 original fields)
  - **Use case:** query games by date, get final scores

2. **nba_players** (PlayerIndex)
  - **PK:** `playerId`
  - **Essential fields:** 18 (31% reduction from 26 original fields)
  - **Use case:** player directory and roster lookup

3. **nba_player_game_stats** (PlayerGameLogs)
  - **PK:** `playerId#gameId` (composite)
  - **SK:** `gameDate`
  - **Essential fields:** 29 (58% reduction from 70 original fields)
  - **Use case:** all games and stats for a player, sorted by date

4. **nba_teams** (Teams static + TeamInfoCommon)
  - **PK:** `teamId`
  - **Essential fields:** 20 total (26% reduction from 27 original fields)
  - **Use case:** team metadata and season rankings

**Storage Optimization:** Field filtering reduces storage costs by ~60% across all endpoints.

### Response Schemas (Minimal)

The canonical response schemas (essential fields) are defined in [docs/GAME_ENDPOINTS.md](docs/GAME_ENDPOINTS.md).
To view real examples with filtering, run `scripts/explore_endpoints.py` (writes sample JSON to `exploration_output/`).

### Persistence Mapping (DynamoDB)

See complete mapping in [docs/DATABASE_SCHEMA.md](docs/DATABASE_SCHEMA.md) including:
- Detailed field lists per table
- Update frequencies and fetch cadences
- Data flow diagrams
- Cost optimization calculations

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