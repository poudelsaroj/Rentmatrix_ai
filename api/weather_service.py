"""
Weather Service for RentMatrix AI Triage System.

Integrates with WeatherAPI.com to provide real-time weather context
for maintenance request prioritization.

API Documentation: https://www.weatherapi.com/docs/

Usage:
    from api.weather_service import WeatherService
    
    weather_service = WeatherService()
    weather_data = await weather_service.get_current_weather("New York")
    # OR
    weather_data = await weather_service.get_current_weather_by_coords(40.7128, -74.0060)
"""

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
import httpx
from dotenv import load_dotenv

load_dotenv()

# WeatherAPI.com configuration
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "6faef13041974745b57122146251612")
WEATHER_API_BASE_URL = "https://api.weatherapi.com/v1"


@dataclass
class WeatherCondition:
    """Current weather condition details."""
    text: str
    icon: str
    code: int


@dataclass
class CurrentWeather:
    """Current weather data from WeatherAPI."""
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
    
    # Visibility
    vis_km: float
    vis_miles: float
    
    # UV Index
    uv: float
    
    # Additional comfort indices
    windchill_c: Optional[float] = None
    windchill_f: Optional[float] = None
    heatindex_c: Optional[float] = None
    heatindex_f: Optional[float] = None
    dewpoint_c: Optional[float] = None
    dewpoint_f: Optional[float] = None
    
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
    
    # Visibility & Humidity
    avgvis_km: float
    avgvis_miles: float
    avghumidity: float
    
    # Condition
    condition: WeatherCondition
    
    # Precipitation chances
    daily_will_it_rain: int
    daily_will_it_snow: int
    daily_chance_of_rain: int
    daily_chance_of_snow: int
    
    # UV
    uv: float


@dataclass
class WeatherAlert:
    """Weather alert information."""
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
                forecast_summary = f"High {day.maxtemp_f}°F, Low {day.mintemp_f}°F. {day.condition.text}"
        
        # Extract alert headlines
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
        
        # Severe weather alerts
        if self.alerts:
            severe_alerts = [a for a in self.alerts if a.severity.lower() in ["severe", "extreme"]]
            if severe_alerts:
                modifiers["has_severe_alerts"] = True
                for alert in severe_alerts[:3]:  # Limit to top 3 alerts
                    modifiers["weather_urgency_notes"].append(
                        f"WEATHER ALERT: {alert.headline}"
                    )
        
        return modifiers


class WeatherService:
    """
    Service for fetching weather data from WeatherAPI.com.
    
    Provides methods for:
    - Current weather by location name or coordinates
    - Forecast data (1-3 days)
    - Weather alerts
    - Integration with RentMatrix context bundle format
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the weather service.
        
        Args:
            api_key: WeatherAPI.com API key. Falls back to WEATHER_API_KEY env var.
        """
        self.api_key = api_key or WEATHER_API_KEY
        self.base_url = WEATHER_API_BASE_URL
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
    
    async def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a request to the WeatherAPI.
        
        Args:
            endpoint: API endpoint (e.g., "current.json", "forecast.json")
            params: Query parameters
            
        Returns:
            JSON response data
            
        Raises:
            WeatherAPIError: If the API request fails
        """
        client = await self._get_client()
        params["key"] = self.api_key
        
        try:
            response = await client.get(f"{self.base_url}/{endpoint}", params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            error_data = e.response.json() if e.response.content else {}
            error_msg = error_data.get("error", {}).get("message", str(e))
            raise WeatherAPIError(f"Weather API error: {error_msg}") from e
        except httpx.RequestError as e:
            raise WeatherAPIError(f"Weather API request failed: {str(e)}") from e
    
    def _parse_current_weather(self, data: Dict[str, Any]) -> CurrentWeather:
        """Parse current weather from API response."""
        current = data.get("current", {})
        condition = current.get("condition", {})
        
        return CurrentWeather(
            temp_c=current.get("temp_c", 0),
            temp_f=current.get("temp_f", 0),
            feelslike_c=current.get("feelslike_c", 0),
            feelslike_f=current.get("feelslike_f", 0),
            condition=WeatherCondition(
                text=condition.get("text", "Unknown"),
                icon=condition.get("icon", ""),
                code=condition.get("code", 0)
            ),
            is_day=current.get("is_day", 1),
            wind_mph=current.get("wind_mph", 0),
            wind_kph=current.get("wind_kph", 0),
            wind_degree=current.get("wind_degree", 0),
            wind_dir=current.get("wind_dir", ""),
            gust_mph=current.get("gust_mph", 0),
            gust_kph=current.get("gust_kph", 0),
            pressure_mb=current.get("pressure_mb", 0),
            pressure_in=current.get("pressure_in", 0),
            humidity=current.get("humidity", 0),
            cloud=current.get("cloud", 0),
            precip_mm=current.get("precip_mm", 0),
            precip_in=current.get("precip_in", 0),
            vis_km=current.get("vis_km", 0),
            vis_miles=current.get("vis_miles", 0),
            uv=current.get("uv", 0),
            windchill_c=current.get("windchill_c"),
            windchill_f=current.get("windchill_f"),
            heatindex_c=current.get("heatindex_c"),
            heatindex_f=current.get("heatindex_f"),
            dewpoint_c=current.get("dewpoint_c"),
            dewpoint_f=current.get("dewpoint_f"),
            last_updated=current.get("last_updated", ""),
            last_updated_epoch=current.get("last_updated_epoch", 0)
        )
    
    def _parse_location(self, data: Dict[str, Any]) -> LocationInfo:
        """Parse location from API response."""
        loc = data.get("location", {})
        return LocationInfo(
            name=loc.get("name", ""),
            region=loc.get("region", ""),
            country=loc.get("country", ""),
            lat=loc.get("lat", 0),
            lon=loc.get("lon", 0),
            tz_id=loc.get("tz_id", ""),
            localtime_epoch=loc.get("localtime_epoch", 0),
            localtime=loc.get("localtime", "")
        )
    
    def _parse_forecast_day(self, day_data: Dict[str, Any]) -> ForecastDay:
        """Parse a single forecast day from API response."""
        day = day_data.get("day", {})
        condition = day.get("condition", {})
        
        return ForecastDay(
            date=day_data.get("date", ""),
            date_epoch=day_data.get("date_epoch", 0),
            maxtemp_c=day.get("maxtemp_c", 0),
            maxtemp_f=day.get("maxtemp_f", 0),
            mintemp_c=day.get("mintemp_c", 0),
            mintemp_f=day.get("mintemp_f", 0),
            avgtemp_c=day.get("avgtemp_c", 0),
            avgtemp_f=day.get("avgtemp_f", 0),
            maxwind_mph=day.get("maxwind_mph", 0),
            maxwind_kph=day.get("maxwind_kph", 0),
            totalprecip_mm=day.get("totalprecip_mm", 0),
            totalprecip_in=day.get("totalprecip_in", 0),
            totalsnow_cm=day.get("totalsnow_cm", 0),
            avgvis_km=day.get("avgvis_km", 0),
            avgvis_miles=day.get("avgvis_miles", 0),
            avghumidity=day.get("avghumidity", 0),
            condition=WeatherCondition(
                text=condition.get("text", "Unknown"),
                icon=condition.get("icon", ""),
                code=condition.get("code", 0)
            ),
            daily_will_it_rain=day.get("daily_will_it_rain", 0),
            daily_will_it_snow=day.get("daily_will_it_snow", 0),
            daily_chance_of_rain=day.get("daily_chance_of_rain", 0),
            daily_chance_of_snow=day.get("daily_chance_of_snow", 0),
            uv=day.get("uv", 0)
        )
    
    def _parse_alerts(self, data: Dict[str, Any]) -> List[WeatherAlert]:
        """Parse weather alerts from API response."""
        alerts_data = data.get("alerts", {}).get("alert", [])
        alerts = []
        
        for alert in alerts_data:
            alerts.append(WeatherAlert(
                headline=alert.get("headline", ""),
                msgtype=alert.get("msgtype", ""),
                severity=alert.get("severity", ""),
                urgency=alert.get("urgency", ""),
                areas=alert.get("areas", ""),
                category=alert.get("category", ""),
                certainty=alert.get("certainty", ""),
                event=alert.get("event", ""),
                note=alert.get("note", ""),
                effective=alert.get("effective", ""),
                expires=alert.get("expires", ""),
                desc=alert.get("desc", ""),
                instruction=alert.get("instruction", "")
            ))
        
        return alerts
    
    async def get_current_weather(
        self,
        location: str,
        include_aqi: bool = False
    ) -> WeatherResponse:
        """
        Get current weather for a location.
        
        Args:
            location: Location query (city name, US zipcode, UK postcode, 
                     Canada postal code, IP address, or lat,lon)
            include_aqi: Whether to include air quality data
            
        Returns:
            WeatherResponse with current conditions
        """
        params = {
            "q": location,
            "aqi": "yes" if include_aqi else "no"
        }
        
        data = await self._make_request("current.json", params)
        
        return WeatherResponse(
            location=self._parse_location(data),
            current=self._parse_current_weather(data)
        )
    
    async def get_current_weather_by_coords(
        self,
        latitude: float,
        longitude: float,
        include_aqi: bool = False
    ) -> WeatherResponse:
        """
        Get current weather by coordinates.
        
        Args:
            latitude: Latitude
            longitude: Longitude
            include_aqi: Whether to include air quality data
            
        Returns:
            WeatherResponse with current conditions
        """
        return await self.get_current_weather(
            f"{latitude},{longitude}",
            include_aqi=include_aqi
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
            days: Number of forecast days (1-3 for free tier)
            include_alerts: Whether to include weather alerts
            include_aqi: Whether to include air quality data
            
        Returns:
            WeatherResponse with current conditions, forecast, and alerts
        """
        params = {
            "q": location,
            "days": min(days, 3),  # Free tier limit
            "aqi": "yes" if include_aqi else "no",
            "alerts": "yes" if include_alerts else "no"
        }
        
        data = await self._make_request("forecast.json", params)
        
        # Parse forecast days
        forecast_days = []
        for day_data in data.get("forecast", {}).get("forecastday", []):
            forecast_days.append(self._parse_forecast_day(day_data))
        
        return WeatherResponse(
            location=self._parse_location(data),
            current=self._parse_current_weather(data),
            forecast=forecast_days,
            alerts=self._parse_alerts(data) if include_alerts else []
        )
    
    async def get_forecast_by_coords(
        self,
        latitude: float,
        longitude: float,
        days: int = 1,
        include_alerts: bool = True,
        include_aqi: bool = False
    ) -> WeatherResponse:
        """
        Get weather forecast by coordinates.
        
        Args:
            latitude: Latitude
            longitude: Longitude
            days: Number of forecast days (1-3 for free tier)
            include_alerts: Whether to include weather alerts
            include_aqi: Whether to include air quality data
            
        Returns:
            WeatherResponse with current conditions, forecast, and alerts
        """
        return await self.get_forecast(
            f"{latitude},{longitude}",
            days=days,
            include_alerts=include_alerts,
            include_aqi=include_aqi
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
            weather = await self.get_forecast(location, days=1, include_alerts=True)
        elif latitude is not None and longitude is not None:
            weather = await self.get_forecast_by_coords(
                latitude, longitude, days=1, include_alerts=True
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
            "condition_code": 1000,
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

