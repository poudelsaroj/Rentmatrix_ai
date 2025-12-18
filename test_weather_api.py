"""
Quick test script to verify WeatherAPI.com integration.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

from api.weather_service import WeatherService, get_weather_for_triage, WEATHER_API_KEY


async def test_weather_api():
    print("=" * 60)
    print("Testing WeatherAPI.com Integration")
    print("=" * 60)
    print(f"\nAPI Key: {WEATHER_API_KEY[:10]}...{WEATHER_API_KEY[-5:]}")
    
    service = WeatherService()
    
    # Test 1: Current weather by city name
    print("\n" + "-" * 40)
    print("Test 1: Get current weather for 'New York'")
    print("-" * 40)
    try:
        weather = await service.get_current_weather("New York")
        print(f"[OK] Location: {weather.location.name}, {weather.location.region}, {weather.location.country}")
        print(f"[OK] Temperature: {weather.current.temp_f}F ({weather.current.temp_c}C)")
        print(f"[OK] Feels like: {weather.current.feelslike_f}F ({weather.current.feelslike_c}C)")
        print(f"[OK] Condition: {weather.current.condition.text}")
        print(f"[OK] Humidity: {weather.current.humidity}%")
        print(f"[OK] Wind: {weather.current.wind_mph} mph {weather.current.wind_dir}")
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False
    
    # Test 2: Forecast with alerts
    print("\n" + "-" * 40)
    print("Test 2: Get forecast for 'Los Angeles'")
    print("-" * 40)
    try:
        forecast = await service.get_forecast("Los Angeles", days=1, include_alerts=True)
        print(f"[OK] Location: {forecast.location.name}")
        print(f"[OK] Current: {forecast.current.temp_f}F, {forecast.current.condition.text}")
        if forecast.forecast:
            day = forecast.forecast[0]
            print(f"[OK] Forecast: High {day.maxtemp_f}F, Low {day.mintemp_f}F")
            print(f"[OK] Condition: {day.condition.text}")
            print(f"[OK] Rain chance: {day.daily_chance_of_rain}%")
        print(f"[OK] Alerts: {len(forecast.alerts)} alert(s)")
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False
    
    # Test 3: Weather by coordinates
    print("\n" + "-" * 40)
    print("Test 3: Get weather by coordinates (40.7128, -74.0060)")
    print("-" * 40)
    try:
        weather = await service.get_current_weather_by_coords(40.7128, -74.0060)
        print(f"[OK] Location: {weather.location.name}")
        print(f"[OK] Temperature: {weather.current.temp_f}F")
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False
    
    # Test 4: Context bundle format
    print("\n" + "-" * 40)
    print("Test 4: Get weather in context bundle format")
    print("-" * 40)
    try:
        context = await get_weather_for_triage(location="Chicago")
        print(f"[OK] Temperature: {context.get('temperature')}F")
        print(f"[OK] Condition: {context.get('condition')}")
        print(f"[OK] Forecast: {context.get('forecast')}")
        print(f"[OK] Alerts: {context.get('alerts')}")
        
        urgency = context.get('urgency_modifiers', {})
        print(f"[OK] Extreme cold: {urgency.get('is_extreme_cold')}")
        print(f"[OK] Extreme heat: {urgency.get('is_extreme_heat')}")
        print(f"[OK] Freeze risk: {urgency.get('freeze_risk')}")
        print(f"[OK] Urgency notes: {urgency.get('weather_urgency_notes')}")
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False
    
    # Test 5: Zipcode lookup
    print("\n" + "-" * 40)
    print("Test 5: Get weather by US zipcode '10001'")
    print("-" * 40)
    try:
        weather = await service.get_current_weather("10001")
        print(f"[OK] Location: {weather.location.name}, {weather.location.region}")
        print(f"[OK] Temperature: {weather.current.temp_f}F")
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False
    
    await service.close()
    
    print("\n" + "=" * 60)
    print("All tests passed! WeatherAPI integration is working correctly.")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = asyncio.run(test_weather_api())
    sys.exit(0 if success else 1)

