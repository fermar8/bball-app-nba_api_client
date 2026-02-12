"""
NBA API Endpoints Exploration Script
Purpose: Test endpoints and see real data to understand their structure
Author: DEV-17 - Data Exploration
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
        print(f"✅ Available fields: {len(field_names)}")
        print(f"\n📋 Sample available fields:")
        for i, field in enumerate(field_names[:15]):
            print(f"   {i+1}. {field}")
        
        # Show 3 sample games
        print(f"\n🎮 Sample of 3 games:")
        for i, game in enumerate(all_games[:3]):
            print(f"\n   Game {i+1}:")
            print(f"   - Game ID: {game.get('gameId', 'N/A')}")
            print(f"   - Date: {game.get('gameDateTimeEst', game.get('gameDate', 'N/A'))}")
            print(f"   - Home: {game.get('homeTeam', {}).get('teamName', 'N/A')} ({game.get('homeTeam', {}).get('score', 'N/A')} pts)")
            print(f"   - Away: {game.get('awayTeam', {}).get('teamName', 'N/A')} ({game.get('awayTeam', {}).get('score', 'N/A')} pts)")
            print(f"   - Status: {game.get('gameStatusText', 'N/A')}")
        
        # Save simplified version
        simplified_games = all_games[:10]
        
        with open(f"{output_dir}/schedule_sample.json", "w", encoding="utf-8") as f:
            json.dump(simplified_games, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Data saved in '{output_dir}/schedule_*.json'")
        
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
        print(f"✅ Available fields: {len(headers)}")
        print(f"\n📋 Available fields:")
        for i, header in enumerate(headers):
            print(f"   {i+1}. {header}")
        
        # Search for famous players to show as examples
        print(f"\n🌟 Famous player examples:")
        famous_names = ["LeBron", "Curry", "Durant", "Jokic", "Giannis"]
        examples_found = 0
        
        for player_row in rows:
            player_dict = dict(zip(headers, player_row))
            player_name = f"{player_dict.get('PLAYER_FIRST_NAME', '')} {player_dict.get('PLAYER_LAST_NAME', '')}"
            
            # Search for famous players
            for famous in famous_names:
                if famous.lower() in player_name.lower() and examples_found < 5:
                    print(f"\n   {player_name}:")
                    print(f"   - PERSON_ID: {player_dict.get('PERSON_ID', 'N/A')}")
                    print(f"   - Team: {player_dict.get('TEAM_NAME', 'N/A')} ({player_dict.get('TEAM_ABBREVIATION', 'N/A')})")
                    print(f"   - Position: {player_dict.get('POSITION', 'N/A')}")
                    print(f"   - Jersey: {player_dict.get('JERSEY_NUMBER', 'N/A')}")
                    print(f"   - Height: {player_dict.get('HEIGHT', 'N/A')}")
                    print(f"   - Status: {'Active' if player_dict.get('ROSTER_STATUS') == 1 else 'Inactive'}")
                    examples_found += 1
                    break
        
        # Save active Lakers players as example
        lakers_players = []
        for player_row in rows:
            player_dict = dict(zip(headers, player_row))
            if player_dict.get('TEAM_ABBREVIATION') == 'LAL' and player_dict.get('ROSTER_STATUS') == 1:
                lakers_players.append(player_dict)
        
        with open(f"{output_dir}/players_lakers_sample.json", "w", encoding="utf-8") as f:
            json.dump(lakers_players, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Data saved in '{output_dir}/players_*.json'")
        print(f"   (Saved {len(lakers_players)} active Lakers players as example)")
        
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
            print(f"✅ Available fields: {len(headers)}")
            print(f"\n📋 Sample stat fields:")
            stat_fields = ['MIN', 'PTS', 'REB', 'AST', 'STL', 'BLK', 'TOV', 'FGM', 'FGA', 'FG3M', 'FG3A']
            for field in stat_fields:
                if field in headers:
                    print(f"   - {field}")
            
            # Show last 3 games
            print(f"\n🎮 Last 3 games for {test_player_name}:")
            for i, game in enumerate(rows[:3]):
                game_dict = dict(zip(headers, game))
                print(f"\n   Game {i+1}:")
                print(f"   - Date: {game_dict.get('GAME_DATE', 'N/A')}")
                print(f"   - Matchup: {game_dict.get('MATCHUP', 'N/A')}")
                print(f"   - Minutes: {game_dict.get('MIN', 'N/A')}")
                print(f"   - Points: {game_dict.get('PTS', 'N/A')}")
                print(f"   - Rebounds: {game_dict.get('REB', 'N/A')}")
                print(f"   - Assists: {game_dict.get('AST', 'N/A')}")
                print(f"   - 3-pointers: {game_dict.get('FG3M', 'N/A')}/{game_dict.get('FG3A', 'N/A')}")
            
            # Save sample
            sample_games = [dict(zip(headers, game)) for game in rows[:5]]
            with open(f"{output_dir}/player_gamelogs_sample.json", "w", encoding="utf-8") as f:
                json.dump(sample_games, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 Data saved in '{output_dir}/player_gamelogs_*.json'")
            
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
            print(f"✅ Available fields: {len(headers)}")
            
            # Show upcoming games
            print(f"\n📅 Upcoming games for {test_player_name}:")
            for i, game in enumerate(rows):
                game_dict = dict(zip(headers, game))
                print(f"\n   {i+1}. {game_dict.get('GAME_DATE', 'N/A')}:")
                print(f"      Home: {game_dict.get('HOME_TEAM_NAME', 'N/A')}")
                print(f"      Away: {game_dict.get('VISITOR_TEAM_NAME', 'N/A')}")
                print(f"      Time: {game_dict.get('GAME_TIME', 'N/A')}")
            
            # Save sample
            sample_next = [dict(zip(headers, game)) for game in rows]
            with open(f"{output_dir}/player_nextgames_sample.json", "w", encoding="utf-8") as f:
                json.dump(sample_next, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 Data saved in '{output_dir}/player_nextgames_*.json'")
            
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
            
            if team_rows:
                team_dict = dict(zip(team_headers, team_rows[0]))
                print(f"\n📊 Team Information:")
                print(f"   - Season: {team_dict.get('SEASON_YEAR', 'N/A')}")
                print(f"   - Conference: {team_dict.get('TEAM_CONFERENCE', 'N/A')}")
                print(f"   - Division: {team_dict.get('TEAM_DIVISION', 'N/A')}")
                print(f"   - Wins: {team_dict.get('W', 'N/A')}")
                print(f"   - Losses: {team_dict.get('L', 'N/A')}")
                print(f"   - Win %: {team_dict.get('PCT', 'N/A')}")
                print(f"   - Conference Rank: {team_dict.get('CONF_RANK', 'N/A')}")
                print(f"   - Division Rank: {team_dict.get('DIV_RANK', 'N/A')}")
            
            if ranks_rows:
                ranks_dict = dict(zip(ranks_headers, ranks_rows[0]))
                print(f"\n📈 Team Season Rankings:")
                print(f"   - Points per game: {ranks_dict.get('PTS_PG', 'N/A')} (Rank: {ranks_dict.get('PTS_RANK', 'N/A')})")
                print(f"   - Rebounds per game: {ranks_dict.get('REB_PG', 'N/A')} (Rank: {ranks_dict.get('REB_RANK', 'N/A')})")
                print(f"   - Assists per game: {ranks_dict.get('AST_PG', 'N/A')} (Rank: {ranks_dict.get('AST_RANK', 'N/A')})")
                print(f"   - Opponent points: {ranks_dict.get('OPP_PTS_PG', 'N/A')} (Rank: {ranks_dict.get('OPP_PTS_RANK', 'N/A')})")
            
            # Save sample
            team_sample = {
                'team_info': dict(zip(team_headers, team_rows[0])) if team_rows else {},
                'season_ranks': dict(zip(ranks_headers, ranks_rows[0])) if ranks_rows else {}
            }
            with open(f"{output_dir}/team_info_sample.json", "w", encoding="utf-8") as f:
                json.dump(team_sample, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 Data saved in '{output_dir}/team_info_*.json'")
            
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
