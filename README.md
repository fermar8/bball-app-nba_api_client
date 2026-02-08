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

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the MIT License.

## Acknowledgments

- [nba_api](https://github.com/swar/nba_api) - The official Python client for NBA statistics