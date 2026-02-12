"""
NBA API Endpoints Exploration Script
Purpose: Test endpoints and see real data to understand their structure
Author: DEV-17 - Data Exploration

IMPORTANT: This script demonstrates field filtering as part of the data schema design.
All filtered outputs follow the essential fields defined in docs/GAME_ENDPOINTS.md
"""

import json
from datetime import datetime
from nba_api.stats.endpoints import ScheduleLeagueV2, PlayerIndex
from nba_api.stats.endpoints import playergamelogs, playernextngames
from nba_api.stats.static import teams

# Create folder to save responses
import os
output_dir = "exploration_output"
os.makedirs(output_dir, exist_ok=True)

# ============================================================================
# FIELD FILTERING - Essential fields per endpoint (from GAME_ENDPOINTS.md)
# ============================================================================

# Schedule essential fields (nested structure)
SCHEDULE_ESSENTIAL = [
    'gameId', 'gameDateEst', 'gameDateTimeEst', 'gameStatus', 'gameStatusText',
    'homeTeam', 'awayTeam', 'arenaName', 'arenaCity'
]

SCHEDULE_TEAM_ESSENTIAL = ['teamId', 'teamName', 'teamTricode', 'wins', 'losses', 'score']

# PlayerIndex essential fields
PLAYER_ESSENTIAL = [
    'PERSON_ID', 'PLAYER_FIRST_NAME', 'PLAYER_LAST_NAME',
    'TEAM_ID', 'TEAM_NAME', 'TEAM_ABBREVIATION',
    'JERSEY_NUMBER', 'POSITION', 'HEIGHT', 'WEIGHT',
    'COUNTRY', 'COLLEGE', 'DRAFT_YEAR', 'DRAFT_ROUND', 'DRAFT_NUMBER',
    'ROSTER_STATUS', 'FROM_YEAR', 'TO_YEAR'
]

# PlayerGameLogs essential fields
GAME_LOGS_ESSENTIAL = [
    'PLAYER_ID', 'PLAYER_NAME', 'TEAM_ID', 'TEAM_ABBREVIATION',
    'GAME_ID', 'GAME_DATE', 'MATCHUP', 'WL', 'MIN',
    'FGM', 'FGA', 'FG_PCT', 'FG3M', 'FG3A', 'FG3_PCT',
    'FTM', 'FTA', 'FT_PCT', 'OREB', 'DREB', 'REB',
    'AST', 'STL', 'BLK', 'BLKA', 'TOV', 'PF', 'PFD', 'PTS'
]

# PlayerNextNGames essential fields
NEXT_GAMES_ESSENTIAL = [
    'GAME_ID', 'GAME_DATE', 'GAME_TIME',
    'HOME_TEAM_ID', 'HOME_TEAM_NAME', 'HOME_TEAM_ABBREVIATION', 'HOME_WL',
    'VISITOR_TEAM_ID', 'VISITOR_TEAM_NAME', 'VISITOR_TEAM_ABBREVIATION', 'VISITOR_WL'
]

# TeamInfoCommon essential fields
TEAM_INFO_ESSENTIAL = [
    'TEAM_ID', 'SEASON_YEAR', 'TEAM_CITY', 'TEAM_NAME', 'TEAM_ABBREVIATION',
    'TEAM_CONFERENCE', 'TEAM_DIVISION', 'W', 'L', 'PCT', 'CONF_RANK', 'DIV_RANK'
]

TEAM_RANKS_ESSENTIAL = [
    'PTS_RANK', 'PTS_PG', 'REB_RANK', 'REB_PG',
    'AST_RANK', 'AST_PG', 'OPP_PTS_RANK', 'OPP_PTS_PG'
]

def filter_schedule_game(game):
    """Filter schedule game to essential fields only"""
    filtered = {k: game[k] for k in SCHEDULE_ESSENTIAL if k in game}
    
    # Filter nested team objects
    if 'homeTeam' in filtered and isinstance(filtered['homeTeam'], dict):
        filtered['homeTeam'] = {k: filtered['homeTeam'][k] for k in SCHEDULE_TEAM_ESSENTIAL if k in filtered['homeTeam']}
    if 'awayTeam' in filtered and isinstance(filtered['awayTeam'], dict):
        filtered['awayTeam'] = {k: filtered['awayTeam'][k] for k in SCHEDULE_TEAM_ESSENTIAL if k in filtered['awayTeam']}
    
    return filtered

def filter_player(player_dict):
    """Filter player data to essential fields only"""
    return {k: player_dict[k] for k in PLAYER_ESSENTIAL if k in player_dict}

def filter_game_log_row(headers, row):
    """Filter game log row to essential fields only"""
    full_dict = dict(zip(headers, row))
    return {k: full_dict[k] for k in GAME_LOGS_ESSENTIAL if k in full_dict}

def filter_next_game_row(headers, row):
    """Filter next game row to essential fields only"""
    full_dict = dict(zip(headers, row))
    return {k: full_dict[k] for k in NEXT_GAMES_ESSENTIAL if k in full_dict}

def filter_team_info(headers, row):
    """Filter team info to essential fields only"""
    full_dict = dict(zip(headers, row))
    return {k: full_dict[k] for k in TEAM_INFO_ESSENTIAL if k in full_dict}

def filter_team_ranks(headers, row):
    """Filter team ranks to essential fields only"""
    full_dict = dict(zip(headers, row))
    return {k: full_dict[k] for k in TEAM_RANKS_ESSENTIAL if k in full_dict}

print("="*70)
print("🏀 NBA API ENDPOINTS EXPLORATION")
print("="*70)
print()

# ============================================================================
# TIER 1: ID PROVIDERS
# ============================================================================

print("📊 TIER 1: ID PROVIDER ENDPOINTS\n")

# ----------------------------------------------------------------------------
# 1. ScheduleLeagueV2 - Season schedule
# ----------------------------------------------------------------------------
print("1️⃣  ScheduleLeagueV2 - Game schedule")
print("-" * 70)

try:
    # Get current season schedule (2025-26) - use default (no season param)
    schedule = ScheduleLeagueV2()
    schedule_data = schedule.get_dict()
    
    # Save full response
    with open(f"{output_dir}/schedule_full_response.json", "w", encoding="utf-8") as f:
        json.dump(schedule_data, f, indent=2, ensure_ascii=False)
    
    # Analyze data - new API format uses leagueSchedule
    league_schedule = schedule_data.get('leagueSchedule', {})
    game_dates = league_schedule.get('gameDates', [])
    
    # Flatten all games from all dates
    all_games = []
    for date_obj in game_dates:
        all_games.extend(date_obj.get('games', []))
    
    if all_games:
        # Get field names from first game
        sample_game = all_games[0]
        field_names = list(sample_game.keys())
        
        print(f"✅ Total games in season: {len(all_games)}")
        print(f"✅ Available fields (unfiltered): {len(field_names)}")
        print(f"\n📋 Sample available fields:")
        for i, field in enumerate(field_names[:15]):
            print(f"   {i+1}. {field}")
        
        # Apply field filtering
        filtered_games = [filter_schedule_game(game) for game in all_games]
        filtered_fields = len(SCHEDULE_ESSENTIAL)
        
        print(f"\n🔍 After filtering:")
        print(f"   Essential fields kept: {filtered_fields}")
        print(f"   Fields removed: {len(field_names) - filtered_fields}")
        print(f"   Storage reduction: ~{int((1 - filtered_fields/len(field_names)) * 100)}%")
        
        # Show 3 sample games
        print(f"\n🎮 Sample of 3 games (filtered):")
        for i, game in enumerate(filtered_games[:3]):
            print(f"\n   Game {i+1}:")
            print(f"   - Game ID: {game.get('gameId', 'N/A')}")
            print(f"   - Date: {game.get('gameDateTimeEst', game.get('gameDate', 'N/A'))}")
            print(f"   - Home: {game.get('homeTeam', {}).get('teamName', 'N/A')} ({game.get('homeTeam', {}).get('score', 'N/A')} pts)")
            print(f"   - Away: {game.get('awayTeam', {}).get('teamName', 'N/A')} ({game.get('awayTeam', {}).get('score', 'N/A')} pts)")
            print(f"   - Status: {game.get('gameStatusText', 'N/A')}")
        
        # Save FILTERED version (essential fields only)
        simplified_games = filtered_games[:10]
        
        with open(f"{output_dir}/schedule_sample.json", "w", encoding="utf-8") as f:
            json.dump(simplified_games, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Data saved in '{output_dir}/schedule_*.json'")
        print(f"   (Saved 10 filtered games with essential fields only)")
        
except Exception as e:
    print(f"❌ Error getting schedule: {e}")

print("\n")

# ----------------------------------------------------------------------------
# 2. PlayerIndex - Player directory
# ----------------------------------------------------------------------------
print("2️⃣  PlayerIndex - Player directory")
print("-" * 70)

try:
    # Get all players for current season
    players = PlayerIndex(season="2025-26")
    players_data = players.get_dict()
    
    # Save full response
    with open(f"{output_dir}/players_full_response.json", "w", encoding="utf-8") as f:
        json.dump(players_data, f, indent=2, ensure_ascii=False)
    
    # Analyze data
    result_sets = players_data.get('resultSets', [])
    if result_sets:
        player_data = result_sets[0]
        headers = player_data.get('headers', [])
        rows = player_data.get('rowSet', [])
        
        print(f"✅ Total players: {len(rows)}")
        print(f"✅ Available fields (unfiltered): {len(headers)}")
        print(f"\n📋 Available fields:")
        for i, header in enumerate(headers):
            print(f"   {i+1}. {header}")
        
        print(f"\n🔍 After filtering:")
        print(f"   Essential fields kept: {len(PLAYER_ESSENTIAL)}")
        print(f"   Fields removed: {len(headers) - len(PLAYER_ESSENTIAL)}")
        print(f"   Storage reduction: ~{int((1 - len(PLAYER_ESSENTIAL)/len(headers)) * 100)}%")
        
        # Search for famous players to show as examples
        print(f"\n🌟 Famous player examples (filtered):")
        famous_names = ["LeBron", "Curry", "Durant", "Jokic", "Giannis"]
        examples_found = 0
        
        for player_row in rows:
            player_dict = dict(zip(headers, player_row))
            player_name = f"{player_dict.get('PLAYER_FIRST_NAME', '')} {player_dict.get('PLAYER_LAST_NAME', '')}"
            
            # Search for famous players
            for famous in famous_names:
                if famous.lower() in player_name.lower() and examples_found < 5:
                    filtered_player = filter_player(player_dict)
                    print(f"\n   {player_name}:")
                    print(f"   - PERSON_ID: {filtered_player.get('PERSON_ID', 'N/A')}")
                    print(f"   - Team: {filtered_player.get('TEAM_NAME', 'N/A')} ({filtered_player.get('TEAM_ABBREVIATION', 'N/A')})")
                    print(f"   - Position: {filtered_player.get('POSITION', 'N/A')}")
                    print(f"   - Jersey: {filtered_player.get('JERSEY_NUMBER', 'N/A')}")
                    print(f"   - Height: {filtered_player.get('HEIGHT', 'N/A')}")
                    print(f"   - Status: {'Active' if filtered_player.get('ROSTER_STATUS') == 1 else 'Inactive'}")
                    examples_found += 1
                    break
        
        # Save active Lakers players as example (FILTERED)
        lakers_players = []
        for player_row in rows:
            player_dict = dict(zip(headers, player_row))
            if player_dict.get('TEAM_ABBREVIATION') == 'LAL' and player_dict.get('ROSTER_STATUS') == 1:
                lakers_players.append(filter_player(player_dict))
        
        with open(f"{output_dir}/players_lakers_sample.json", "w", encoding="utf-8") as f:
            json.dump(lakers_players, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Data saved in '{output_dir}/players_*.json'")
        print(f"   (Saved {len(lakers_players)} active Lakers players with essential fields only)")
        
except Exception as e:
    print(f"❌ Error getting players: {e}")

print("\n")

# ----------------------------------------------------------------------------
# 3. Teams - Teams list (static module)
# ----------------------------------------------------------------------------
print("3️⃣  Teams - Team list (static data)")
print("-" * 70)

try:
    # Get all teams
    all_teams = teams.get_teams()
    
    print(f"✅ Total teams: {len(all_teams)}")
    print(f"✅ Available fields: {list(all_teams[0].keys()) if all_teams else []}")
    
    # Show some teams
    print(f"\n🏆 Team examples:")
    for i, team in enumerate(all_teams[:5]):
        print(f"\n   {i+1}. {team['full_name']}:")
        print(f"      - ID: {team['id']}")
        print(f"      - Abbreviation: {team['abbreviation']}")
        print(f"      - City: {team['city']}")
        print(f"      - Year founded: {team['year_founded']}")
    
    # Save all teams
    with open(f"{output_dir}/teams_all.json", "w", encoding="utf-8") as f:
        json.dump(all_teams, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Data saved in '{output_dir}/teams_all.json'")
    
except Exception as e:
    print(f"❌ Error getting teams: {e}")

print("\n")
print("="*70)
print("📊 TIER 2: PARAMETERIZED ENDPOINTS (Need IDs from Tier 1)")
print("="*70)
print()

# ============================================================================
# TIER 2: PARAMETERIZED ENDPOINTS (Need IDs from Tier 1)
# ============================================================================

# We need a PERSON_ID to test these endpoints
# Let's use a known player - search in the data we already obtained

test_player_id = None
test_player_name = None

# Try to find an active player
if 'players_data' in locals():
    result_sets = players_data.get('resultSets', [])
    if result_sets:
        headers = result_sets[0].get('headers', [])
        rows = result_sets[0].get('rowSet', [])
        
        # Search for an active player for testing
        for player_row in rows:
            player_dict = dict(zip(headers, player_row))
            if player_dict.get('ROSTER_STATUS') == 1 and player_dict.get('TEAM_ABBREVIATION') == 'LAL':
                test_player_id = player_dict.get('PERSON_ID')
                test_player_name = f"{player_dict.get('PLAYER_FIRST_NAME')} {player_dict.get('PLAYER_LAST_NAME')}"
                break

if test_player_id:
    print(f"🎯 Using test player: {test_player_name} (ID: {test_player_id})\n")
    
    # ------------------------------------------------------------------------
    # 4. PlayerGameLogs - Game-by-game player statistics
    # ------------------------------------------------------------------------
    print("4️⃣  PlayerGameLogs - Player game-by-game statistics")
    print("-" * 70)
    
    try:
        from nba_api.stats.endpoints import playergamelogs
        
        # Get player statistics
        game_logs = playergamelogs.PlayerGameLogs(
            player_id_nullable=test_player_id,
            season_nullable="2025-26"
        )
        game_logs_data = game_logs.get_dict()
        
        # Save full response
        with open(f"{output_dir}/player_gamelogs_full_response.json", "w", encoding="utf-8") as f:
            json.dump(game_logs_data, f, indent=2, ensure_ascii=False)
        
        # Analyze data
        result_sets = game_logs_data.get('resultSets', [])
        if result_sets:
            logs_data = result_sets[0]
            headers = logs_data.get('headers', [])
            rows = logs_data.get('rowSet', [])
            
            print(f"✅ Total games played: {len(rows)}")
            print(f"✅ Available fields (unfiltered): {len(headers)}")
            print(f"\n📋 Sample stat fields:")
            stat_fields = ['MIN', 'PTS', 'REB', 'AST', 'STL', 'BLK', 'TOV', 'FGM', 'FGA', 'FG3M', 'FG3A']
            for field in stat_fields:
                if field in headers:
                    print(f"   - {field}")
            
            print(f"\n🔍 After filtering:")
            print(f"   Essential fields kept: {len(GAME_LOGS_ESSENTIAL)}")
            print(f"   Fields removed: {len(headers) - len(GAME_LOGS_ESSENTIAL)}")
            print(f"   Storage reduction: ~{int((1 - len(GAME_LOGS_ESSENTIAL)/len(headers)) * 100)}%")
            print(f"   Removed: All *_RANK fields, PLUS_MINUS, NBA_FANTASY_PTS, DD2, TD3")
            
            # Show last 3 games (filtered)
            print(f"\n🎮 Last 3 games for {test_player_name} (filtered):")
            for i, game in enumerate(rows[:3]):
                game_dict = filter_game_log_row(headers, game)
                print(f"\n   Game {i+1}:")
                print(f"   - Date: {game_dict.get('GAME_DATE', 'N/A')}")
                print(f"   - Matchup: {game_dict.get('MATCHUP', 'N/A')}")
                print(f"   - Minutes: {game_dict.get('MIN', 'N/A')}")
                print(f"   - Points: {game_dict.get('PTS', 'N/A')}")
                print(f"   - Rebounds: {game_dict.get('REB', 'N/A')}")
                print(f"   - Assists: {game_dict.get('AST', 'N/A')}")
                print(f"   - 3-pointers: {game_dict.get('FG3M', 'N/A')}/{game_dict.get('FG3A', 'N/A')}")
            
            # Save sample (FILTERED)
            sample_games = [filter_game_log_row(headers, game) for game in rows[:5]]
            with open(f"{output_dir}/player_gamelogs_sample.json", "w", encoding="utf-8") as f:
                json.dump(sample_games, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 Data saved in '{output_dir}/player_gamelogs_*.json'")
            print(f"   (Saved 5 filtered games with essential fields only)")
            
    except Exception as e:
        print(f"❌ Error getting game logs: {e}")
    
    print("\n")
    
    # ------------------------------------------------------------------------
    # 5. PlayerNextNGames - Player upcoming games
    # ------------------------------------------------------------------------
    print("5️⃣  PlayerNextNGames - Player upcoming games")
    print("-" * 70)
    
    try:
        from nba_api.stats.endpoints import playernextngames
        
        # Get upcoming games
        next_games = playernextngames.PlayerNextNGames(
            player_id=test_player_id,
            number_of_games=5
        )
        next_games_data = next_games.get_dict()
        
        # Save full response
        with open(f"{output_dir}/player_nextgames_full_response.json", "w", encoding="utf-8") as f:
            json.dump(next_games_data, f, indent=2, ensure_ascii=False)
        
        # Analyze data
        result_sets = next_games_data.get('resultSets', [])
        if result_sets:
            games_data = result_sets[0]
            headers = games_data.get('headers', [])
            rows = games_data.get('rowSet', [])
            
            print(f"✅ Upcoming games found: {len(rows)}")
            print(f"✅ Available fields (unfiltered): {len(headers)}")
            print(f"\n🔍 After filtering:")
            print(f"   Essential fields kept: {len(NEXT_GAMES_ESSENTIAL)}")
            print(f"   Fields removed: {len(headers) - len(NEXT_GAMES_ESSENTIAL)}")
            print(f"   Storage reduction: ~{int((1 - len(NEXT_GAMES_ESSENTIAL)/len(headers)) * 100)}%")
            
            # Show upcoming games (filtered)
            print(f"\n📅 Upcoming games for {test_player_name} (filtered):")
            for i, game in enumerate(rows):
                game_dict = filter_next_game_row(headers, game)
                print(f"\n   {i+1}. {game_dict.get('GAME_DATE', 'N/A')}:")
                print(f"      Home: {game_dict.get('HOME_TEAM_NAME', 'N/A')}")
                print(f"      Away: {game_dict.get('VISITOR_TEAM_NAME', 'N/A')}")
                print(f"      Time: {game_dict.get('GAME_TIME', 'N/A')}")
            
            # Save sample (FILTERED)
            sample_next = [filter_next_game_row(headers, game) for game in rows]
            with open(f"{output_dir}/player_nextgames_sample.json", "w", encoding="utf-8") as f:
                json.dump(sample_next, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 Data saved in '{output_dir}/player_nextgames_*.json'")
            print(f"   (Saved {len(sample_next)} filtered games with essential fields only)")
            
    except Exception as e:
        print(f"❌ Error getting upcoming games: {e}")
    
    print("\n")
    
    # ------------------------------------------------------------------------
    # 6. TeamInfoCommon - Current season team information
    # ------------------------------------------------------------------------
    print("6️⃣  TeamInfoCommon - Current season team information")
    print("-" * 70)
    
    try:
        from nba_api.stats.endpoints import teaminfocommon
        
        # Get Lakers team info as example (ID: 1610612747)
        test_team_id = 1610612747  # Lakers
        test_team_name = "Los Angeles Lakers"
        
        team_info = teaminfocommon.TeamInfoCommon(
            team_id=test_team_id,
            season_nullable="2025-26"
        )
        team_info_data = team_info.get_dict()
        
        # Save full response
        with open(f"{output_dir}/team_info_full_response.json", "w", encoding="utf-8") as f:
            json.dump(team_info_data, f, indent=2, ensure_ascii=False)
        
        # Analyze data
        result_sets = team_info_data.get('resultSets', [])
        if result_sets and len(result_sets) >= 2:
            # TeamInfoCommon dataset
            team_data = result_sets[0]
            team_headers = team_data.get('headers', [])
            team_rows = team_data.get('rowSet', [])
            
            # TeamSeasonRanks dataset
            ranks_data = result_sets[1]
            ranks_headers = ranks_data.get('headers', [])
            ranks_rows = ranks_data.get('rowSet', [])
            
            print(f"✅ Team: {test_team_name}")
            print(f"✅ Available datasets: {len(result_sets)}")
            print(f"✅ Team info fields (unfiltered): {len(team_headers)}")
            print(f"✅ Season ranks fields (unfiltered): {len(ranks_headers)}")
            
            print(f"\n🔍 After filtering:")
            print(f"   Team info - Essential fields: {len(TEAM_INFO_ESSENTIAL)}")
            print(f"   Team info - Fields removed: {len(team_headers) - len(TEAM_INFO_ESSENTIAL)}")
            print(f"   Team info - Storage reduction: ~{int((1 - len(TEAM_INFO_ESSENTIAL)/len(team_headers)) * 100)}%")
            print(f"   Season ranks - Essential fields: {len(TEAM_RANKS_ESSENTIAL)}")
            print(f"   Season ranks - Fields removed: {len(ranks_headers) - len(TEAM_RANKS_ESSENTIAL)}")
            print(f"   Season ranks - Storage reduction: ~{int((1 - len(TEAM_RANKS_ESSENTIAL)/len(ranks_headers)) * 100)}%")
            
            if team_rows:
                team_dict = filter_team_info(team_headers, team_rows[0])
                print(f"\n📊 Team Information (filtered):")
                print(f"   - Season: {team_dict.get('SEASON_YEAR', 'N/A')}")
                print(f"   - Conference: {team_dict.get('TEAM_CONFERENCE', 'N/A')}")
                print(f"   - Division: {team_dict.get('TEAM_DIVISION', 'N/A')}")
                print(f"   - Wins: {team_dict.get('W', 'N/A')}")
                print(f"   - Losses: {team_dict.get('L', 'N/A')}")
                print(f"   - Win %: {team_dict.get('PCT', 'N/A')}")
                print(f"   - Conference Rank: {team_dict.get('CONF_RANK', 'N/A')}")
                print(f"   - Division Rank: {team_dict.get('DIV_RANK', 'N/A')}")
            
            if ranks_rows:
                ranks_dict = filter_team_ranks(ranks_headers, ranks_rows[0])
                print(f"\n📈 Team Season Rankings (filtered):")
                print(f"   - Points per game: {ranks_dict.get('PTS_PG', 'N/A')} (Rank: {ranks_dict.get('PTS_RANK', 'N/A')})")
                print(f"   - Rebounds per game: {ranks_dict.get('REB_PG', 'N/A')} (Rank: {ranks_dict.get('REB_RANK', 'N/A')})")
                print(f"   - Assists per game: {ranks_dict.get('AST_PG', 'N/A')} (Rank: {ranks_dict.get('AST_RANK', 'N/A')})")
                print(f"   - Opponent points: {ranks_dict.get('OPP_PTS_PG', 'N/A')} (Rank: {ranks_dict.get('OPP_PTS_RANK', 'N/A')})")
            
            # Save sample (FILTERED)
            team_sample = {
                'team_info': filter_team_info(team_headers, team_rows[0]) if team_rows else {},
                'season_ranks': filter_team_ranks(ranks_headers, ranks_rows[0]) if ranks_rows else {}
            }
            with open(f"{output_dir}/team_info_sample.json", "w", encoding="utf-8") as f:
                json.dump(team_sample, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 Data saved in '{output_dir}/team_info_*.json'")
            print(f"   (Saved filtered data with essential fields only)")
            
    except Exception as e:
        print(f"❌ Error getting team info: {e}")

else:
    print("⚠️  Could not find a test player for Tier 2 endpoints")

print("\n")
print("="*70)
print("✅ EXPLORATION COMPLETED")
print("="*70)
print(f"\n📁 All files saved in folder: '{output_dir}/'")
print("\n💡 Next steps:")
print("   1. Review the generated JSON files")
print("   2. Compare with GAME_ENDPOINTS.md")
print("   3. Design DynamoDB schema based on this data")
print()
