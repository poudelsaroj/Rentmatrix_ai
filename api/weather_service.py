"""
Weather Service for RentMatrix AI Triage System.

Integrates with Open-Meteo API to provide real-time weather context
for maintenance request prioritization.

API Documentation: https://open-meteo.com/en/docs

Usage:
    from api.weather_service import WeatherService

    weather_service = WeatherService()
    weather_data = await weather_service.get_current_weather("New York")
    # OR
    weather_data = await weather_service.get_current_weather_by_coords(40.7128, -74.0060)
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import httpx

# Open-Meteo API configuration (no API key required for non-commercial use)
WEATHER_API_BASE_URL = "https://api.open-meteo.com/v1/forecast"
GEOCODING_API_BASE_URL = "https://geocoding-api.open-meteo.com/v1/search"

# WMO Weather interpretation codes
# https://open-meteo.com/en/docs
WMO_WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


@dataclass
class WeatherCondition:
    """Current weather condition details."""
    text: str
    code: int
    icon: str = ""  # Open-Meteo doesn't provide icons, kept for compatibility


@dataclass
class CurrentWeather:
    """Current weather data from Open-Meteo."""
    # Temperature
    temp_c: float
    temp_f: float
    feelslike_c: float
    feelslike_f: float

    # Conditions
    condition: WeatherCondition
    is_day: int

    # Wind
    wind_mph: float
    wind_kph: float
    wind_degree: int
    wind_dir: str
    gust_mph: float
    gust_kph: float

    # Atmospheric
    pressure_mb: float
    pressure_in: float
    humidity: int
    cloud: int

    # Precipitation
    precip_mm: float
    precip_in: float

    # Visibility (not available in Open-Meteo, using defaults)
    vis_km: float = 10.0
    vis_miles: float = 6.2

    # UV Index (available in daily data only)
    uv: float = 0.0

    # Timestamps
    last_updated: str = ""
    last_updated_epoch: int = 0


@dataclass
class ForecastDay:
    """Daily forecast data."""
    date: str
    date_epoch: int

    # Temperature extremes
    maxtemp_c: float
    maxtemp_f: float
    mintemp_c: float
    mintemp_f: float
    avgtemp_c: float
    avgtemp_f: float

    # Wind
    maxwind_mph: float
    maxwind_kph: float

    # Precipitation
    totalprecip_mm: float
    totalprecip_in: float
    totalsnow_cm: float

    # Visibility & Humidity (defaults for Open-Meteo)
    avgvis_km: float = 10.0
    avgvis_miles: float = 6.2
    avghumidity: float = 50.0

    # Condition
    condition: WeatherCondition = None

    # Precipitation chances
    daily_will_it_rain: int = 0
    daily_will_it_snow: int = 0
    daily_chance_of_rain: int = 0
    daily_chance_of_snow: int = 0

    # UV
    uv: float = 0.0


@dataclass
class WeatherAlert:
    """Weather alert information (not available in Open-Meteo)."""
    headline: str = ""
    msgtype: str = ""
    severity: str = ""
    urgency: str = ""
    areas: str = ""
    category: str = ""
    certainty: str = ""
    event: str = ""
    note: str = ""
    effective: str = ""
    expires: str = ""
    desc: str = ""
    instruction: str = ""


@dataclass
class LocationInfo:
    """Location information from weather API."""
    name: str
    region: str
    country: str
    lat: float
    lon: float
    tz_id: str
    localtime_epoch: int
    localtime: str


@dataclass
class WeatherResponse:
    """Complete weather response with all data."""
    location: LocationInfo
    current: CurrentWeather
    forecast: List[ForecastDay] = field(default_factory=list)
    alerts: List[WeatherAlert] = field(default_factory=list)

    def to_context_bundle(self) -> Dict[str, Any]:
        """
        Convert to RentMatrix context bundle format.

        This format matches the ContextBundle.weather schema in the system architecture:
        {
            "temperature": float (Fahrenheit),
            "condition": str,
            "forecast": str (Next 24 hours description),
            "alerts": List[str]
        }
        """
        # Generate forecast summary for next 24 hours
        forecast_summary = "Clear skies expected"
        if self.forecast:
            day = self.forecast[0]
            conditions = []
            if day.daily_chance_of_rain > 50:
                conditions.append(f"{day.daily_chance_of_rain}% chance of rain")
            if day.daily_chance_of_snow > 50:
                conditions.append(f"{day.daily_chance_of_snow}% chance of snow")
            if day.maxwind_kph > 40:
                conditions.append("strong winds")

            if conditions:
                forecast_summary = f"High {day.maxtemp_f}°F, Low {day.mintemp_f}°F. {', '.join(conditions).capitalize()}"
            else:
                forecast_summary = f"High {day.maxtemp_f}°F, Low {day.mintemp_f}°F. {day.condition.text if day.condition else 'Clear'}"

        # Extract alert headlines (Open-Meteo doesn't provide alerts)
        alert_texts = [alert.headline for alert in self.alerts if alert.headline]

        return {
            "temperature": self.current.temp_f,
            "temperature_c": self.current.temp_c,
            "feelslike_f": self.current.feelslike_f,
            "feelslike_c": self.current.feelslike_c,
            "condition": self.current.condition.text,
            "condition_code": self.current.condition.code,
            "humidity": self.current.humidity,
            "wind_mph": self.current.wind_mph,
            "wind_dir": self.current.wind_dir,
            "uv": self.current.uv,
            "is_day": bool(self.current.is_day),
            "forecast": forecast_summary,
            "alerts": alert_texts,
            "location": {
                "name": self.location.name,
                "region": self.location.region,
                "country": self.location.country,
                "lat": self.location.lat,
                "lon": self.location.lon,
                "localtime": self.location.localtime,
            }
        }

    def get_weather_urgency_modifiers(self) -> Dict[str, Any]:
        """
        Analyze weather conditions and return urgency modifiers for priority calculation.

        This helps the priority calculator agent adjust scores based on weather:
        - Extreme cold (freeze risk for pipes)
        - Extreme heat (AC urgency)
        - Severe weather alerts
        - High precipitation (roof/water leak urgency)
        """
        modifiers = {
            "is_extreme_cold": False,
            "is_extreme_heat": False,
            "freeze_risk": False,
            "has_severe_alerts": False,
            "high_precipitation": False,
            "weather_urgency_notes": []
        }

        temp_f = self.current.temp_f

        # Extreme cold checks
        if temp_f <= 32:
            modifiers["freeze_risk"] = True
            modifiers["is_extreme_cold"] = True
            modifiers["weather_urgency_notes"].append(
                f"Freezing conditions ({temp_f}°F) - Pipe freeze risk, heating issues critical"
            )
        elif temp_f <= 40:
            modifiers["is_extreme_cold"] = True
            modifiers["weather_urgency_notes"].append(
                f"Cold conditions ({temp_f}°F) - Heating issues have elevated priority"
            )

        # Extreme heat checks
        if temp_f >= 100:
            modifiers["is_extreme_heat"] = True
            modifiers["weather_urgency_notes"].append(
                f"Extreme heat ({temp_f}°F) - AC issues critical, especially for vulnerable tenants"
            )
        elif temp_f >= 95:
            modifiers["is_extreme_heat"] = True
            modifiers["weather_urgency_notes"].append(
                f"High heat ({temp_f}°F) - AC issues have elevated priority"
            )

        # Precipitation checks
        if self.forecast:
            day = self.forecast[0]
            if day.daily_chance_of_rain >= 70 or day.totalprecip_mm >= 10:
                modifiers["high_precipitation"] = True
                modifiers["weather_urgency_notes"].append(
                    f"High precipitation expected ({day.daily_chance_of_rain}% rain chance) - "
                    "Roof leaks and water issues more urgent"
                )
            if day.daily_chance_of_snow >= 50 or day.totalsnow_cm >= 5:
                modifiers["weather_urgency_notes"].append(
                    f"Snow expected ({day.totalsnow_cm}cm) - Heating and access issues more critical"
                )

        # Severe weather alerts (Open-Meteo doesn't provide alerts)
        if self.alerts:
            severe_alerts = [a for a in self.alerts if a.severity.lower() in ["severe", "extreme"]]
            if severe_alerts:
                modifiers["has_severe_alerts"] = True
                for alert in severe_alerts[:3]:
                    modifiers["weather_urgency_notes"].append(
                        f"WEATHER ALERT: {alert.headline}"
                    )

        return modifiers


def _celsius_to_fahrenheit(celsius: float) -> float:
    """Convert Celsius to Fahrenheit."""
    return (celsius * 9/5) + 32


def _kph_to_mph(kph: float) -> float:
    """Convert km/h to mph."""
    return kph * 0.621371


def _mm_to_inches(mm: float) -> float:
    """Convert millimeters to inches."""
    return mm * 0.0393701


def _mb_to_inhg(mb: float) -> float:
    """Convert millibars to inches of mercury."""
    return mb * 0.02953


def _degree_to_direction(degree: int) -> str:
    """Convert wind degree to compass direction."""
    directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                  "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    index = round(degree / 22.5) % 16
    return directions[index]


def _get_weather_text(code: int) -> str:
    """Get weather description from WMO code."""
    return WMO_WEATHER_CODES.get(code, "Unknown")


class WeatherService:
    """
    Service for fetching weather data from Open-Meteo API.

    Provides methods for:
    - Current weather by location name or coordinates
    - Forecast data (1-16 days)
    - Integration with RentMatrix context bundle format

    Note: Open-Meteo does not provide weather alerts.
    """

    def __init__(self):
        """Initialize the weather service."""
        self.base_url = WEATHER_API_BASE_URL
        self.geocoding_url = GEOCODING_API_BASE_URL
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=10.0)
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def _geocode_location(self, location: str) -> Optional[Dict[str, Any]]:
        """
        Convert a location name to coordinates using Open-Meteo Geocoding API.

        Args:
            location: Location query (city name, postal code, etc.)

        Returns:
            Dict with lat, lon, name, country, timezone or None if not found
        """
        client = await self._get_client()

        try:
            response = await client.get(
                self.geocoding_url,
                params={"name": location, "count": 1, "language": "en"}
            )
            response.raise_for_status()
            data = response.json()

            results = data.get("results", [])
            if not results:
                return None

            result = results[0]
            return {
                "lat": result.get("latitude"),
                "lon": result.get("longitude"),
                "name": result.get("name", ""),
                "region": result.get("admin1", ""),
                "country": result.get("country", ""),
                "timezone": result.get("timezone", "UTC"),
            }
        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            raise WeatherAPIError(f"Geocoding failed: {str(e)}") from e

    async def _make_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a request to the Open-Meteo Weather API.

        Args:
            params: Query parameters

        Returns:
            JSON response data

        Raises:
            WeatherAPIError: If the API request fails
        """
        client = await self._get_client()

        try:
            response = await client.get(self.base_url, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            error_msg = str(e)
            try:
                if e.response.content:
                    error_data = e.response.json()
                    error_msg = error_data.get("reason", str(e))
            except (ValueError, TypeError):
                pass
            raise WeatherAPIError(f"Weather API error: {error_msg}") from e
        except httpx.RequestError as e:
            raise WeatherAPIError(f"Weather API request failed: {str(e)}") from e

    def _parse_current_weather(self, data: Dict[str, Any]) -> CurrentWeather:
        """Parse current weather from Open-Meteo API response."""
        current = data.get("current", {})

        # Get temperature (API returns in Celsius by default)
        temp_c = current.get("temperature_2m", 0)
        temp_f = _celsius_to_fahrenheit(temp_c)

        feelslike_c = current.get("apparent_temperature", temp_c)
        feelslike_f = _celsius_to_fahrenheit(feelslike_c)

        # Get wind (API returns in km/h by default)
        wind_kph = current.get("wind_speed_10m", 0)
        wind_mph = _kph_to_mph(wind_kph)
        wind_degree = int(current.get("wind_direction_10m", 0))
        gust_kph = current.get("wind_gusts_10m", 0)
        gust_mph = _kph_to_mph(gust_kph)

        # Get precipitation
        precip_mm = current.get("precipitation", 0) + current.get("rain", 0) + current.get("showers", 0)
        precip_in = _mm_to_inches(precip_mm)

        # Get pressure
        pressure_mb = current.get("pressure_msl", current.get("surface_pressure", 1013))
        pressure_in = _mb_to_inhg(pressure_mb)

        # Get weather code
        weather_code = current.get("weather_code", 0)

        return CurrentWeather(
            temp_c=temp_c,
            temp_f=temp_f,
            feelslike_c=feelslike_c,
            feelslike_f=feelslike_f,
            condition=WeatherCondition(
                text=_get_weather_text(weather_code),
                code=weather_code,
                icon=""
            ),
            is_day=1 if current.get("is_day", 1) else 0,
            wind_mph=wind_mph,
            wind_kph=wind_kph,
            wind_degree=wind_degree,
            wind_dir=_degree_to_direction(wind_degree),
            gust_mph=gust_mph,
            gust_kph=gust_kph,
            pressure_mb=pressure_mb,
            pressure_in=pressure_in,
            humidity=int(current.get("relative_humidity_2m", 50)),
            cloud=int(current.get("cloud_cover", 0)),
            precip_mm=precip_mm,
            precip_in=precip_in,
            last_updated=current.get("time", ""),
            last_updated_epoch=0
        )

    def _parse_forecast_days(self, data: Dict[str, Any]) -> List[ForecastDay]:
        """Parse forecast days from Open-Meteo API response."""
        daily = data.get("daily", {})
        if not daily:
            return []

        forecast_days = []
        times = daily.get("time", [])

        for i, date in enumerate(times):
            # Temperature
            max_c = daily.get("temperature_2m_max", [0])[i] if i < len(daily.get("temperature_2m_max", [])) else 0
            min_c = daily.get("temperature_2m_min", [0])[i] if i < len(daily.get("temperature_2m_min", [])) else 0
            avg_c = (max_c + min_c) / 2

            # Precipitation
            precip_mm = daily.get("precipitation_sum", [0])[i] if i < len(daily.get("precipitation_sum", [])) else 0
            snow_cm = daily.get("snowfall_sum", [0])[i] if i < len(daily.get("snowfall_sum", [])) else 0
            rain_chance = daily.get("precipitation_probability_max", [0])[i] if i < len(daily.get("precipitation_probability_max", [])) else 0

            # Wind
            wind_kph = daily.get("wind_speed_10m_max", [0])[i] if i < len(daily.get("wind_speed_10m_max", [])) else 0

            # UV
            uv = daily.get("uv_index_max", [0])[i] if i < len(daily.get("uv_index_max", [])) else 0

            # Weather code
            weather_code = daily.get("weather_code", [0])[i] if i < len(daily.get("weather_code", [])) else 0

            forecast_days.append(ForecastDay(
                date=date,
                date_epoch=0,
                maxtemp_c=max_c,
                maxtemp_f=_celsius_to_fahrenheit(max_c),
                mintemp_c=min_c,
                mintemp_f=_celsius_to_fahrenheit(min_c),
                avgtemp_c=avg_c,
                avgtemp_f=_celsius_to_fahrenheit(avg_c),
                maxwind_mph=_kph_to_mph(wind_kph),
                maxwind_kph=wind_kph,
                totalprecip_mm=precip_mm,
                totalprecip_in=_mm_to_inches(precip_mm),
                totalsnow_cm=snow_cm,
                condition=WeatherCondition(
                    text=_get_weather_text(weather_code),
                    code=weather_code,
                    icon=""
                ),
                daily_will_it_rain=1 if rain_chance > 50 else 0,
                daily_will_it_snow=1 if snow_cm > 0 else 0,
                daily_chance_of_rain=int(rain_chance),
                daily_chance_of_snow=int(min(rain_chance, 100) if snow_cm > 0 else 0),
                uv=uv
            ))

        return forecast_days

    async def get_current_weather(
        self,
        location: str,
        include_aqi: bool = False
    ) -> WeatherResponse:
        """
        Get current weather for a location.

        Args:
            location: Location query (city name, US zipcode, etc.)
            include_aqi: Not supported by Open-Meteo, ignored

        Returns:
            WeatherResponse with current conditions
        """
        # First geocode the location
        geo = await self._geocode_location(location)
        if not geo:
            raise WeatherAPIError(f"Location not found: {location}")

        return await self.get_current_weather_by_coords(
            latitude=geo["lat"],
            longitude=geo["lon"],
            location_info=geo
        )

    async def get_current_weather_by_coords(
        self,
        latitude: float,
        longitude: float,
        include_aqi: bool = False,
        location_info: Optional[Dict[str, Any]] = None
    ) -> WeatherResponse:
        """
        Get current weather by coordinates.

        Args:
            latitude: Latitude
            longitude: Longitude
            include_aqi: Not supported by Open-Meteo, ignored
            location_info: Optional pre-fetched location info

        Returns:
            WeatherResponse with current conditions
        """
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,is_day,precipitation,rain,showers,snowfall,weather_code,cloud_cover,pressure_msl,surface_pressure,wind_speed_10m,wind_direction_10m,wind_gusts_10m",
            "timezone": "auto"
        }

        data = await self._make_request(params)

        # Build location info
        if location_info:
            loc_info = LocationInfo(
                name=location_info.get("name", ""),
                region=location_info.get("region", ""),
                country=location_info.get("country", ""),
                lat=latitude,
                lon=longitude,
                tz_id=data.get("timezone", "UTC"),
                localtime_epoch=0,
                localtime=data.get("current", {}).get("time", "")
            )
        else:
            loc_info = LocationInfo(
                name=f"{latitude}, {longitude}",
                region="",
                country="",
                lat=latitude,
                lon=longitude,
                tz_id=data.get("timezone", "UTC"),
                localtime_epoch=0,
                localtime=data.get("current", {}).get("time", "")
            )

        return WeatherResponse(
            location=loc_info,
            current=self._parse_current_weather(data)
        )

    async def get_forecast(
        self,
        location: str,
        days: int = 1,
        include_alerts: bool = True,
        include_aqi: bool = False
    ) -> WeatherResponse:
        """
        Get weather forecast for a location.

        Args:
            location: Location query
            days: Number of forecast days (1-16)
            include_alerts: Not supported by Open-Meteo, ignored
            include_aqi: Not supported by Open-Meteo, ignored

        Returns:
            WeatherResponse with current conditions and forecast
        """
        # First geocode the location
        geo = await self._geocode_location(location)
        if not geo:
            raise WeatherAPIError(f"Location not found: {location}")

        return await self.get_forecast_by_coords(
            latitude=geo["lat"],
            longitude=geo["lon"],
            days=days,
            location_info=geo
        )

    async def get_forecast_by_coords(
        self,
        latitude: float,
        longitude: float,
        days: int = 1,
        include_alerts: bool = True,
        include_aqi: bool = False,
        location_info: Optional[Dict[str, Any]] = None
    ) -> WeatherResponse:
        """
        Get weather forecast by coordinates.

        Args:
            latitude: Latitude
            longitude: Longitude
            days: Number of forecast days (1-16)
            include_alerts: Not supported by Open-Meteo, ignored
            include_aqi: Not supported by Open-Meteo, ignored
            location_info: Optional pre-fetched location info

        Returns:
            WeatherResponse with current conditions and forecast
        """
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,is_day,precipitation,rain,showers,snowfall,weather_code,cloud_cover,pressure_msl,surface_pressure,wind_speed_10m,wind_direction_10m,wind_gusts_10m",
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,weather_code,wind_speed_10m_max,uv_index_max,snowfall_sum",
            "timezone": "auto",
            "forecast_days": min(days, 16)
        }

        data = await self._make_request(params)

        # Build location info
        if location_info:
            loc_info = LocationInfo(
                name=location_info.get("name", ""),
                region=location_info.get("region", ""),
                country=location_info.get("country", ""),
                lat=latitude,
                lon=longitude,
                tz_id=data.get("timezone", "UTC"),
                localtime_epoch=0,
                localtime=data.get("current", {}).get("time", "")
            )
        else:
            loc_info = LocationInfo(
                name=f"{latitude}, {longitude}",
                region="",
                country="",
                lat=latitude,
                lon=longitude,
                tz_id=data.get("timezone", "UTC"),
                localtime_epoch=0,
                localtime=data.get("current", {}).get("time", "")
            )

        return WeatherResponse(
            location=loc_info,
            current=self._parse_current_weather(data),
            forecast=self._parse_forecast_days(data),
            alerts=[]  # Open-Meteo doesn't provide alerts
        )

    async def get_context_bundle_weather(
        self,
        location: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Get weather data formatted for the RentMatrix context bundle.

        This is the primary method for integrating with the triage pipeline.

        Args:
            location: Location query (city, zipcode, etc.) OR
            latitude/longitude: Coordinate pair

        Returns:
            Weather data in context bundle format:
            {
                "temperature": float,
                "condition": str,
                "forecast": str,
                "alerts": List[str],
                ...
            }
        """
        if location:
            weather = await self.get_forecast(location, days=1)
        elif latitude is not None and longitude is not None:
            weather = await self.get_forecast_by_coords(
                latitude, longitude, days=1
            )
        else:
            raise ValueError("Either location or latitude/longitude must be provided")

        context = weather.to_context_bundle()
        context["urgency_modifiers"] = weather.get_weather_urgency_modifiers()

        return context


class WeatherAPIError(Exception):
    """Exception raised for Weather API errors."""
    pass


# Singleton instance for easy import
_weather_service: Optional[WeatherService] = None


def get_weather_service() -> WeatherService:
    """Get the singleton weather service instance."""
    global _weather_service
    if _weather_service is None:
        _weather_service = WeatherService()
    return _weather_service


async def get_weather_for_triage(
    location: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None
) -> Dict[str, Any]:
    """
    Convenience function to get weather data for triage.

    Falls back to default weather if no location provided.

    Args:
        location: Location name/query
        latitude: Latitude coordinate
        longitude: Longitude coordinate

    Returns:
        Weather context bundle or default values
    """
    if not location and latitude is None:
        # Return default weather context
        return {
            "temperature": 70,
            "temperature_c": 21,
            "feelslike_f": 70,
            "feelslike_c": 21,
            "condition": "clear",
            "condition_code": 0,
            "humidity": 50,
            "wind_mph": 5,
            "wind_dir": "N",
            "uv": 3,
            "is_day": True,
            "forecast": "Clear skies",
            "alerts": [],
            "location": None,
            "urgency_modifiers": {
                "is_extreme_cold": False,
                "is_extreme_heat": False,
                "freeze_risk": False,
                "has_severe_alerts": False,
                "high_precipitation": False,
                "weather_urgency_notes": []
            }
        }

    service = get_weather_service()
    try:
        return await service.get_context_bundle_weather(
            location=location,
            latitude=latitude,
            longitude=longitude
        )
    except WeatherAPIError:
        # Return default on error
        return {
            "temperature": 70,
            "temperature_c": 21,
            "feelslike_f": 70,
            "feelslike_c": 21,
            "condition": "unknown",
            "condition_code": 0,
            "humidity": 50,
            "wind_mph": 0,
            "wind_dir": "",
            "uv": 0,
            "is_day": True,
            "forecast": "Weather data unavailable",
            "alerts": [],
            "location": None,
            "urgency_modifiers": {
                "is_extreme_cold": False,
                "is_extreme_heat": False,
                "freeze_risk": False,
                "has_severe_alerts": False,
                "high_precipitation": False,
                "weather_urgency_notes": []
            }
        }
