"""
Simple test script to verify the NBA API client server integration.
This script demonstrates that the server correctly imports and uses the nba_api library.
"""

from nba_api.stats.endpoints import ScheduleLeagueV2
from server import app

# Test 1: Verify that ScheduleLeagueV2 can be imported
print("✓ Test 1 Passed: Successfully imported ScheduleLeagueV2 from nba_api")

# Test 2: Verify that we can instantiate the endpoint
try:
    schedule = ScheduleLeagueV2()
    print("✓ Test 2 Passed: Successfully instantiated ScheduleLeagueV2")
except Exception as e:
    print(f"✗ Test 2 Failed: {e}")

# Test 3: Verify that we can create a season-specific request
try:
    schedule_2023 = ScheduleLeagueV2(season="2023-24")
    print("✓ Test 3 Passed: Successfully created season-specific ScheduleLeagueV2 instance")
except Exception as e:
    print(f"✗ Test 3 Failed: {e}")

# Test 4: Test server imports
print("✓ Test 4 Passed: Successfully imported Flask app from server.py")

# Test 5: Verify Flask routes are configured
routes = [rule.rule for rule in app.url_map.iter_rules()]
expected_routes = ['/', '/health', '/schedule']

for route in expected_routes:
    if route in routes:
        print(f"✓ Test 5.{expected_routes.index(route) + 1} Passed: Route '{route}' is configured")
    else:
        print(f"✗ Test 5.{expected_routes.index(route) + 1} Failed: Route '{route}' is not configured")

print("\n" + "="*50)
print("All integration tests completed!")
print("="*50)
