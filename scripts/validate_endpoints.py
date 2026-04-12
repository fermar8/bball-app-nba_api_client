"""
Validation Script for NBA API Endpoints
Purpose: Verify filtered data contains ONLY essential fields per GAME_ENDPOINTS.md
Author: DEV-17 - Data Validation

IMPORTANT: This script validates that field filtering is working correctly.
All sample files should contain ONLY essential fields (no extras).
"""

import json
import os

# Expected fields from GAME_ENDPOINTS.md
EXPECTED_FIELDS = {
    "ScheduleLeagueV2": {
        "essential": [
            "gameId", "gameDateEst", "gameDateTimeEst", "gameStatus", "gameStatusText",
            "homeTeam", "awayTeam",
            "arenaName", "arenaCity"
        ],
        "nested_fields": {
            "homeTeam": ["teamId", "teamName", "teamTricode", "wins", "losses", "score"],
            "awayTeam": ["teamId", "teamName", "teamTricode", "wins", "losses", "score"]
        },
        "file": "exploration_output/schedule_sample.json"
    },
    "PlayerIndex": {
        "essential": [
            "PERSON_ID", "PLAYER_FIRST_NAME", "PLAYER_LAST_NAME",
            "TEAM_ID", "TEAM_NAME", "TEAM_ABBREVIATION",
            "JERSEY_NUMBER", "POSITION", "HEIGHT", "WEIGHT",
            "COUNTRY", "COLLEGE", "DRAFT_YEAR", "DRAFT_ROUND", "DRAFT_NUMBER",
            "ROSTER_STATUS", "FROM_YEAR", "TO_YEAR"
        ],
        "file": "exploration_output/players_lakers_sample.json"
    },
    "Teams": {
        "essential": [
            "id", "full_name", "abbreviation", "nickname",
            "city", "state", "year_founded"
        ],
        "file": "exploration_output/teams_all.json"
    },
    "PlayerGameLogs": {
        "essential": [
            "PLAYER_ID", "PLAYER_NAME", "TEAM_ID", "TEAM_ABBREVIATION",
            "GAME_ID", "GAME_DATE", "MATCHUP", "WL", "MIN",
            "FGM", "FGA", "FG_PCT", "FG3M", "FG3A", "FG3_PCT",
            "FTM", "FTA", "FT_PCT", "OREB", "DREB", "REB",
            "AST", "STL", "BLK", "BLKA", "TOV", "PF", "PFD", "PTS"
        ],
        "file": "exploration_output/player_gamelogs_sample.json"
    },
    "PlayerNextNGames": {
        "essential": [
            "GAME_ID", "GAME_DATE", "GAME_TIME",
            "HOME_TEAM_ID", "HOME_TEAM_NAME", "HOME_TEAM_ABBREVIATION", "HOME_WL",
            "VISITOR_TEAM_ID", "VISITOR_TEAM_NAME", "VISITOR_TEAM_ABBREVIATION", "VISITOR_WL"
        ],
        "file": "exploration_output/player_nextgames_sample.json"
    },
    "TeamInfoCommon": {
        "essential": {
            "team_info": [
                "TEAM_ID", "SEASON_YEAR", "TEAM_CITY", "TEAM_NAME", "TEAM_ABBREVIATION",
                "TEAM_CONFERENCE", "TEAM_DIVISION", "W", "L", "PCT", "CONF_RANK", "DIV_RANK"
            ],
            "season_ranks": [
                "PTS_RANK", "PTS_PG", "REB_RANK", "REB_PG",
                "AST_RANK", "AST_PG", "OPP_PTS_RANK", "OPP_PTS_PG"
            ]
        },
        "file": "exploration_output/team_info_sample.json"
    }
}

def validate_endpoint(endpoint_name, expected_fields, file_path, nested_fields=None):
    """Validate that filtered data contains ONLY essential fields (no extras)"""
    print(f"\n{'='*70}")
    print(f"📋 Validating: {endpoint_name}")
    print(f"{'='*70}")
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle different data structures
        if endpoint_name == "TeamInfoCommon":
            # Special case: nested structure
            validation_results = {}
            for dataset_name, fields in expected_fields.items():
                actual_fields = set(data.get(dataset_name, {}).keys())
                expected = set(fields)
                
                missing = expected - actual_fields
                extra = actual_fields - expected
                present = expected & actual_fields
                
                validation_results[dataset_name] = {
                    'missing': missing,
                    'extra': extra,
                    'present': present
                }
                
                print(f"\n🔍 Dataset: {dataset_name}")
                print(f"   ✅ Expected fields present: {len(present)}/{len(expected)}")
                
                if missing:
                    print(f"   ❌ Missing essential fields: {', '.join(sorted(missing))}")
                if extra:
                    print(f"   ❌ EXTRA FIELDS FOUND (should be filtered out): {', '.join(sorted(extra))}")
                    print(f"      Filtering is NOT working correctly!")
                
                if not missing and not extra:
                    print(f"   ✅ Perfectly filtered! Only essential fields present.")
            
            # Must have all essential fields AND no extras
            return all(not v['missing'] and not v['extra'] for v in validation_results.values())
        
        else:
            # Regular list structure
            if not data:
                print("❌ No data found in file")
                return False
            
            # Get fields from first item
            sample_item = data[0] if isinstance(data, list) else data
            actual_fields = set(sample_item.keys())
            expected = set(expected_fields)
            
            # Check nested fields if specified
            nested_missing = []
            nested_extra = []
            if nested_fields:
                for parent_field, child_fields in nested_fields.items():
                    if parent_field in sample_item:
                        nested_obj = sample_item[parent_field]
                        if isinstance(nested_obj, dict):
                            nested_actual = set(nested_obj.keys())
                            nested_expected = set(child_fields)
                            nested_missing.extend([f"{parent_field}.{f}" for f in (nested_expected - nested_actual)])
                            nested_extra.extend([f"{parent_field}.{f}" for f in (nested_actual - nested_expected)])
            
            missing = expected - actual_fields
            extra = actual_fields - expected
            present = expected & actual_fields
            
            print(f"\n📊 Field Analysis:")
            print(f"   Total fields in filtered file: {len(actual_fields)}")
            print(f"   Essential fields expected: {len(expected)}")
            print(f"   ✅ Essential fields present: {len(present)}/{len(expected)}")
            
            if missing or nested_missing:
                print(f"\n   ❌ MISSING ESSENTIAL FIELDS:")
                for field in sorted(missing):
                    print(f"      - {field}")
                for field in sorted(nested_missing):
                    print(f"      - {field}")
            
            if extra or nested_extra:
                print(f"\n   ❌ EXTRA FIELDS FOUND (should be filtered out): {len(extra) + len(nested_extra)}")
                for field in sorted(extra):
                    print(f"      - {field}")
                for field in sorted(nested_extra):
                    print(f"      - {field}")
                print(f"      🔍 Filtering is NOT working correctly for this endpoint!")
            
            if not missing and not extra and not nested_missing and not nested_extra:
                print(f"\n   ✅ Perfectly filtered! Only essential fields present.")
                print(f"      Storage optimized: {len(actual_fields)} fields (no waste)")
            
            # Show sample data
            print(f"\n📝 Sample Data Preview:")
            for field in list(expected)[:5]:
                if field in sample_item:
                    value = sample_item[field]
                    # Handle nested objects
                    if isinstance(value, dict):
                        print(f"   {field}: (nested object)")
                    else:
                        print(f"   {field}: {value}")
            
            # Must have all essential fields AND no extras (strict validation)
            return len(missing) == 0 and len(nested_missing) == 0 and len(extra) == 0 and len(nested_extra) == 0
    
    except Exception as e:
        print(f"❌ Error validating {endpoint_name}: {e}")
        return False

def main():
    print("="*70)
    print("🔍 NBA API ENDPOINT VALIDATION")
    print("="*70)
    print("\nVerifying filtered data contains ONLY essential fields...")
    print("(No missing fields, no extra fields - perfect filtering)\n")
    
    results = {}
    
    # Validate each endpoint
    for endpoint_name, config in EXPECTED_FIELDS.items():
        expected = config["essential"]
        file_path = config["file"]
        nested_fields = config.get("nested_fields", None)
        
        results[endpoint_name] = validate_endpoint(endpoint_name, expected, file_path, nested_fields)
    
    # Summary
    print("\n" + "="*70)
    print("📊 VALIDATION SUMMARY")
    print("="*70)
    
    total = len(results)
    passed = sum(results.values())
    
    for endpoint, passed_validation in results.items():
        status = "✅ PASS" if passed_validation else "❌ FAIL"
        print(f"{status} - {endpoint}")
    
    print(f"\n📈 Overall: {passed}/{total} endpoints validated successfully")
    
    if passed == total:
        print("\n🎉 Perfect! All endpoints properly filtered!")
        print("   ✅ Only essential fields present (no waste)")
        print("   ✅ All required fields included (no missing data)")
        print("   ✅ Field filtering working correctly")
        print("\n   Ready for DynamoDB implementation with optimized storage!")
    else:
        print("\n❌ Validation failed - filtering issues detected:")
        print("   • Check explore_endpoints.py filtering functions")
        print("   • Verify essential field lists match GAME_ENDPOINTS.md")
        print("   • Re-run exploration after fixes")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
