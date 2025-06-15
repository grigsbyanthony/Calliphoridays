"""
Basic tests for calliphoridays functionality.
"""
import pytest
import sys
import os

# Add the parent directory to the path to import calliphoridays
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from calliphoridays.models import CalliphoridaeSpecies, DevelopmentStage, get_development_threshold
from calliphoridays.pmi_calculator import PMICalculator
from calliphoridays.weather import WeatherService


class TestModels:
    """Test the data models"""
    
    def test_species_enum(self):
        """Test that species enum works correctly"""
        species = CalliphoridaeSpecies.LUCILIA_SERICATA
        assert species.value == "lucilia_sericata"
    
    def test_stage_enum(self):
        """Test that development stage enum works correctly"""
        stage = DevelopmentStage.THIRD_INSTAR
        assert stage.value == "3rd_instar"
    
    def test_development_threshold_lookup(self):
        """Test looking up development thresholds"""
        threshold = get_development_threshold(
            CalliphoridaeSpecies.LUCILIA_SERICATA,
            DevelopmentStage.THIRD_INSTAR
        )
        assert threshold.min_add == 48.0
        assert threshold.max_add == 108.0
        assert threshold.base_temp == 8.0


class TestPMICalculator:
    """Test the PMI calculation engine"""
    
    def test_basic_pmi_calculation(self):
        """Test basic PMI calculation"""
        calculator = PMICalculator()
        
        temperature_data = {'avg_temp': 25.0}
        
        result = calculator.calculate_pmi(
            species=CalliphoridaeSpecies.LUCILIA_SERICATA,
            stage=DevelopmentStage.THIRD_INSTAR,
            temperature_data=temperature_data
        )
        
        assert 'pmi_days' in result
        assert 'pmi_hours' in result
        assert 'confidence_low' in result
        assert 'confidence_high' in result
        assert result['pmi_days'] > 0
        assert result['pmi_hours'] > 0
    
    def test_temperature_validation(self):
        """Test temperature validation"""
        calculator = PMICalculator()
        
        # Test valid temperature
        valid_temp = {'avg_temp': 20.0}
        assert calculator.validate_temperature_data(valid_temp)
        
        # Test invalid temperature (too cold)
        with pytest.raises(ValueError):
            invalid_temp = {'avg_temp': -30.0}
            calculator.validate_temperature_data(invalid_temp)
        
        # Test missing temperature
        with pytest.raises(ValueError):
            missing_temp = {}
            calculator.validate_temperature_data(missing_temp)


class TestWeatherService:
    """Test the weather service"""
    
    def test_temperature_estimation(self):
        """Test temperature estimation fallback"""
        weather_service = WeatherService()
        
        temp_data = weather_service._estimate_temperature("New York, NY", "2024-06-15")
        
        assert 'avg_temp' in temp_data
        assert 'min_temp' in temp_data
        assert 'max_temp' in temp_data
        assert isinstance(temp_data['avg_temp'], (int, float))
    
    def test_weather_validation(self):
        """Test weather data validation"""
        weather_service = WeatherService()
        
        # Valid weather data
        valid_data = {
            'avg_temp': 20.0,
            'min_temp': 15.0,
            'max_temp': 25.0
        }
        assert weather_service.validate_weather_data(valid_data)
        
        # Invalid weather data (missing avg_temp)
        with pytest.raises(ValueError):
            invalid_data = {'min_temp': 15.0, 'max_temp': 25.0}
            weather_service.validate_weather_data(invalid_data)


def test_integration():
    """Test integration between components"""
    calculator = PMICalculator()
    weather_service = WeatherService()
    
    # Get temperature data
    temp_data = weather_service._estimate_temperature("Miami, FL", "2024-07-01")
    
    # Calculate PMI
    result = calculator.calculate_pmi(
        species=CalliphoridaeSpecies.CHRYSOMYA_RUFIFACIES,
        stage=DevelopmentStage.SECOND_INSTAR,
        temperature_data=temp_data
    )
    
    # Verify reasonable results
    assert result['pmi_days'] > 0
    assert result['pmi_days'] < 30  # Should be reasonable PMI
    assert result['confidence_low'] < result['pmi_days'] < result['confidence_high']


if __name__ == "__main__":
    # Run basic tests
    print("Running basic functionality tests...")
    
    # Test models
    print("Testing models...")
    test_models = TestModels()
    test_models.test_species_enum()
    test_models.test_stage_enum()
    test_models.test_development_threshold_lookup()
    print("✓ Models tests passed")
    
    # Test PMI calculator
    print("Testing PMI calculator...")
    test_calc = TestPMICalculator()
    test_calc.test_basic_pmi_calculation()
    test_calc.test_temperature_validation()
    print("✓ PMI calculator tests passed")
    
    # Test weather service
    print("Testing weather service...")
    test_weather = TestWeatherService()
    test_weather.test_temperature_estimation()
    test_weather.test_weather_validation()
    print("✓ Weather service tests passed")
    
    # Test integration
    print("Testing integration...")
    test_integration()
    print("✓ Integration tests passed")
    
    print("\nAll tests passed! ✓")