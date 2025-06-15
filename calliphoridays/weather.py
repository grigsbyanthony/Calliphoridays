import requests
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from geopy.geocoders import Nominatim
import os


class WeatherService:
    """
    Service for fetching historical weather data for PMI calculations.
    
    This service integrates with weather APIs to get temperature data
    for specific locations and date ranges.
    """
    
    def __init__(self):
        self.geocoder = Nominatim(user_agent="calliphoridays-forensic-entomology")
        self.openweather_api_key = os.getenv('OPENWEATHER_API_KEY')
        
    def get_temperature_data(self, location: str, discovery_date: str, discovery_time: Optional[str] = None) -> Dict:
        """
        Get temperature data for a location and date range.
        
        Args:
            location: Location string (city, state/country)
            discovery_date: Date body was discovered (YYYY-MM-DD)
            discovery_time: Optional time body was discovered (HH:MM)
            
        Returns:
            Dictionary with temperature data
        """
        try:
            # Parse discovery date and time
            if discovery_time:
                try:
                    discovery = datetime.strptime(f"{discovery_date} {discovery_time}", '%Y-%m-%d %H:%M')
                except ValueError:
                    print(f"Warning: Invalid time format '{discovery_time}'. Using date only.")
                    discovery = datetime.strptime(discovery_date, '%Y-%m-%d')
            else:
                discovery = datetime.strptime(discovery_date, '%Y-%m-%d')
            
            # Get coordinates for location
            coords = self._geocode_location(location)
            
            # Estimate PMI range (typically 1-14 days before discovery)
            # We'll get weather for the past 14 days to cover reasonable PMI range
            end_date = discovery
            start_date = discovery - timedelta(days=14)
            
            # Try to get historical weather data
            temp_data = self._fetch_historical_weather(
                coords['latitude'], 
                coords['longitude'], 
                start_date, 
                end_date
            )
            
            if temp_data:
                return temp_data
            else:
                # Fall back to estimated temperature based on location and season
                return self._estimate_temperature(location, discovery_date, discovery_time)
        
        except Exception as e:
            print(f"Warning: Could not fetch weather data ({str(e)})")
            return self._estimate_temperature(location, discovery_date, discovery_time)
    
    def _geocode_location(self, location: str) -> Dict:
        """
        Get coordinates for a location string.
        
        Args:
            location: Location string
            
        Returns:
            Dictionary with latitude and longitude
        """
        try:
            geocoded = self.geocoder.geocode(location)
            if geocoded:
                return {
                    'latitude': geocoded.latitude,
                    'longitude': geocoded.longitude,
                    'address': geocoded.address
                }
            else:
                raise ValueError(f"Could not geocode location: {location}")
        except Exception as e:
            raise ValueError(f"Geocoding failed for {location}: {str(e)}")
    
    def _fetch_historical_weather(self, 
                                lat: float, 
                                lon: float, 
                                start_date: datetime, 
                                end_date: datetime) -> Optional[Dict]:
        """
        Fetch historical weather data using OpenWeather API.
        
        Args:
            lat: Latitude
            lon: Longitude  
            start_date: Start date for weather data
            end_date: End date for weather data
            
        Returns:
            Temperature data dictionary or None if failed
        """
        if not self.openweather_api_key:
            print("Warning: No OpenWeather API key found. Set OPENWEATHER_API_KEY environment variable.")
            return None
        
        try:
            # OpenWeather One Call API (historical data requires subscription)
            # For free tier, we'll use current weather as approximation
            url = "http://api.openweathermap.org/data/2.5/weather"
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.openweather_api_key,
                'units': 'metric'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract temperature data
            current_temp = data['main']['temp']
            min_temp = data['main'].get('temp_min', current_temp - 5)
            max_temp = data['main'].get('temp_max', current_temp + 5)
            
            return {
                'avg_temp': current_temp,
                'min_temp': min_temp,
                'max_temp': max_temp,
                'location': f"{lat:.2f}, {lon:.2f}",
                'date_range': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
                'source': 'OpenWeather (current conditions)'
            }
            
        except Exception as e:
            print(f"Warning: OpenWeather API request failed: {str(e)}")
            return None
    
    def _estimate_temperature(self, location: str, discovery_date: str, discovery_time: Optional[str] = None) -> Dict:
        """
        Estimate temperature based on location and seasonal patterns.
        
        This is a fallback when weather APIs are unavailable.
        
        Args:
            location: Location string
            discovery_date: Discovery date string
            discovery_time: Optional discovery time string (HH:MM)
            
        Returns:
            Estimated temperature data
        """
        try:
            # Parse discovery date and time
            if discovery_time:
                try:
                    discovery = datetime.strptime(f"{discovery_date} {discovery_time}", '%Y-%m-%d %H:%M')
                except ValueError:
                    discovery = datetime.strptime(discovery_date, '%Y-%m-%d')
            else:
                discovery = datetime.strptime(discovery_date, '%Y-%m-%d')
            month = discovery.month
            
            # Basic seasonal temperature estimates by region
            # These are rough estimates and should be replaced with actual data when possible
            location_lower = location.lower()
            
            # Determine climate zone based on location keywords
            if any(keyword in location_lower for keyword in ['florida', 'texas', 'arizona', 'california', 'hawaii']):
                # Hot/warm climate
                seasonal_temps = {
                    1: 15, 2: 18, 3: 22, 4: 26, 5: 30, 6: 33,
                    7: 35, 8: 34, 9: 31, 10: 27, 11: 22, 12: 17
                }
            elif any(keyword in location_lower for keyword in ['alaska', 'montana', 'north dakota', 'minnesota', 'maine']):
                # Cold climate
                seasonal_temps = {
                    1: -10, 2: -8, 3: -2, 4: 6, 5: 14, 6: 20,
                    7: 23, 8: 21, 9: 16, 10: 8, 11: 0, 12: -7
                }
            elif any(keyword in location_lower for keyword in ['canada', 'alaska', 'scandinavia', 'russia', 'siberia']):
                # Very cold climate
                seasonal_temps = {
                    1: -15, 2: -12, 3: -5, 4: 3, 5: 12, 6: 18,
                    7: 21, 8: 19, 9: 13, 10: 5, 11: -3, 12: -12
                }
            elif any(keyword in location_lower for keyword in ['australia', 'south africa', 'brazil', 'argentina']):
                # Southern hemisphere - reverse seasons
                seasonal_temps = {
                    1: 25, 2: 24, 3: 21, 4: 17, 5: 13, 6: 10,
                    7: 9, 8: 11, 9: 15, 10: 19, 11: 22, 12: 24
                }
            else:
                # Temperate climate (default)
                seasonal_temps = {
                    1: 2, 2: 4, 3: 9, 4: 15, 5: 20, 6: 25,
                    7: 27, 8: 26, 9: 22, 10: 16, 11: 9, 12: 4
                }
            
            estimated_temp = seasonal_temps[month]
            
            # Apply time-of-day temperature adjustment if time is provided
            if discovery_time:
                hour = discovery.hour
                time_adjustment = self._get_time_of_day_adjustment(hour)
                estimated_temp += time_adjustment
                source_info = f'Estimated (seasonal + time-of-day at {discovery_time})'
            else:
                source_info = 'Estimated (seasonal average)'
            
            return {
                'avg_temp': estimated_temp,
                'min_temp': estimated_temp - 8,
                'max_temp': estimated_temp + 8,
                'location': location,
                'date_range': f"{discovery_date}" + (f" {discovery_time}" if discovery_time else ""),
                'source': source_info
            }
            
        except Exception as e:
            # Ultimate fallback - use moderate temperature
            print(f"Warning: Temperature estimation failed: {str(e)}")
            return {
                'avg_temp': 20.0,
                'min_temp': 15.0,
                'max_temp': 25.0,
                'location': location,
                'date_range': discovery_date,
                'source': 'Default (20°C)'
            }
    
    def validate_weather_data(self, weather_data: Dict) -> bool:
        """
        Validate weather data for reasonableness.
        
        Args:
            weather_data: Weather data dictionary
            
        Returns:
            True if valid, raises ValueError if invalid
        """
        avg_temp = weather_data.get('avg_temp')
        
        if avg_temp is None:
            raise ValueError("Weather data missing average temperature")
        
        if avg_temp < -50 or avg_temp > 60:
            raise ValueError(f"Temperature {avg_temp}°C is outside reasonable range")
        
        min_temp = weather_data.get('min_temp')
        max_temp = weather_data.get('max_temp')
        
        if min_temp is not None and max_temp is not None:
            if max_temp < min_temp:
                raise ValueError("Maximum temperature is less than minimum temperature")
            
            if (max_temp - min_temp) > 40:
                print("Warning: Large temperature range may affect accuracy")
        
        return True
    
    def get_weather_summary(self, weather_data: Dict) -> str:
        """
        Generate a human-readable summary of weather data.
        
        Args:
            weather_data: Weather data dictionary
            
        Returns:
            Summary string
        """
        avg_temp = weather_data['avg_temp']
        source = weather_data.get('source', 'Unknown')
        location = weather_data.get('location', 'Unknown')
        
        summary = f"Temperature: {avg_temp:.1f}°C (from {source})"
        
        if 'min_temp' in weather_data and 'max_temp' in weather_data:
            min_temp = weather_data['min_temp']
            max_temp = weather_data['max_temp']
            summary += f"\nRange: {min_temp:.1f}°C to {max_temp:.1f}°C"
        
        if location != 'Unknown':
            summary += f"\nLocation: {location}"
        
        return summary
    
    def _get_time_of_day_adjustment(self, hour: int) -> float:
        """
        Get temperature adjustment based on time of day.
        
        Args:
            hour: Hour of day (0-23)
            
        Returns:
            Temperature adjustment in degrees Celsius
        """
        # Typical daily temperature variation pattern
        # Peak temperature around 14:00-16:00, minimum around 04:00-06:00
        
        if 0 <= hour <= 5:      # Early morning (coldest)
            return -6.0
        elif 6 <= hour <= 8:    # Morning
            return -3.0
        elif 9 <= hour <= 11:   # Late morning
            return 0.0
        elif 12 <= hour <= 16:  # Afternoon (warmest)
            return +4.0
        elif 17 <= hour <= 19:  # Evening
            return +1.0
        elif 20 <= hour <= 23:  # Night
            return -2.0
        else:
            return 0.0  # Default