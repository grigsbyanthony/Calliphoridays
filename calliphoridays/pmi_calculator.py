import math
from typing import Dict, Optional, Tuple
import numpy as np

from .models import (
    ForensicSpecies,
    CalliphoridaeSpecies, 
    DevelopmentStage, 
    PMIEstimate, 
    TemperatureData,
    get_development_threshold,
    get_species_info
)


class PMICalculator:
    """
    Postmortem Interval Calculator using accumulated degree days method.
    
    This calculator uses the accumulated degree days (ADD) method to estimate
    the postmortem interval based on insect development stages and temperature data.
    """
    
    def __init__(self):
        self.confidence_factor = 0.2  # 20% confidence interval
        
    def calculate_pmi(self, 
                     species: ForensicSpecies,
                     stage: DevelopmentStage,
                     temperature_data: Dict,
                     specimen_length: Optional[float] = None,
                     verbose: bool = False) -> Dict:
        """
        Calculate the postmortem interval estimate.
        
        Args:
            species: The Calliphoridae species
            stage: The development stage observed
            temperature_data: Temperature data dict with 'avg_temp' key
            specimen_length: Optional specimen length in mm for refinement
            verbose: Whether to show detailed calculations
            
        Returns:
            Dictionary with PMI estimate and related data
        """
        # Get development threshold data
        threshold = get_development_threshold(species, stage)
        
        # Calculate accumulated degree days needed for this stage
        avg_temp = temperature_data['avg_temp']
        base_temp = threshold.base_temp
        
        if avg_temp <= base_temp:
            # Instead of erroring, warn and use minimal effective temperature
            print(f"\033[91mWARNING: Temperature ({avg_temp}°C) is below base temperature ({base_temp}°C) for {species.value}\033[0m")
            print(f"\033[91mDevelopment is unlikely at this temperature. Results should be interpreted with extreme caution.\033[0m")
            effective_temp = 0.5  # Use minimal effective temperature to prevent division by zero
        else:
            # Calculate normal effective temperature
            effective_temp = avg_temp - base_temp
        
        if verbose:
            print(f"Base temperature: {base_temp}°C")
            print(f"Average temperature: {avg_temp}°C")
            print(f"Effective temperature: {effective_temp}°C")
        
        # Estimate ADD based on stage and specimen length
        estimated_add = self._estimate_accumulated_dd(threshold, specimen_length, verbose)
        
        # Calculate PMI in days
        pmi_days = estimated_add / effective_temp
        pmi_hours = pmi_days * 24
        
        # Calculate confidence interval
        confidence_range = pmi_days * self.confidence_factor
        confidence_low = max(0, pmi_days - confidence_range)
        confidence_high = pmi_days + confidence_range
        
        if verbose:
            print(f"Estimated ADD: {estimated_add:.1f}")
            print(f"PMI calculation: {estimated_add:.1f} / {effective_temp:.1f} = {pmi_days:.1f} days")
        
        # Create temperature data object
        temp_data = TemperatureData(
            avg_temp=avg_temp,
            min_temp=temperature_data.get('min_temp'),
            max_temp=temperature_data.get('max_temp'),
            location=temperature_data.get('location'),
            date_range=temperature_data.get('date_range')
        )
        
        # Return results as dictionary (matching CLI expectations)
        return {
            'pmi_days': pmi_days,
            'pmi_hours': pmi_hours,
            'confidence_low': confidence_low,
            'confidence_high': confidence_high,
            'accumulated_dd': estimated_add,
            'base_temp': base_temp,
            'dev_threshold': estimated_add,
            'species': species,
            'stage': stage,
            'temperature_data': temp_data
        }
    
    def _estimate_accumulated_dd(self, 
                                threshold, 
                                specimen_length: Optional[float] = None,
                                verbose: bool = False) -> float:
        """
        Estimate the accumulated degree days based on development stage and specimen length.
        
        Args:
            threshold: DevelopmentThreshold object
            specimen_length: Optional specimen length for refinement
            verbose: Whether to show detailed calculations
            
        Returns:
            Estimated accumulated degree days
        """
        min_add = threshold.min_add
        max_add = threshold.max_add
        typical_length = threshold.typical_length_mm
        
        if specimen_length is None or typical_length is None:
            # Use midpoint of range if no length data
            estimated_add = (min_add + max_add) / 2
            if verbose:
                print(f"No specimen length data, using midpoint: {estimated_add:.1f} ADD")
        else:
            # Adjust estimate based on specimen length
            # Larger specimens are typically older (more ADD)
            length_ratio = specimen_length / typical_length
            
            if length_ratio < 0.8:
                # Smaller than typical, use lower end of range
                estimated_add = min_add + (max_add - min_add) * 0.3
            elif length_ratio > 1.2:
                # Larger than typical, use higher end of range
                estimated_add = min_add + (max_add - min_add) * 0.8
            else:
                # Normal size, use midpoint
                estimated_add = (min_add + max_add) / 2
            
            if verbose:
                print(f"Specimen length: {specimen_length}mm (typical: {typical_length}mm)")
                print(f"Length ratio: {length_ratio:.2f}")
                print(f"Adjusted ADD estimate: {estimated_add:.1f}")
        
        return estimated_add
    
    def validate_temperature_data(self, temperature_data: Dict) -> bool:
        """
        Validate that temperature data is reasonable for PMI calculation.
        
        Args:
            temperature_data: Temperature data dictionary
            
        Returns:
            True if valid, raises ValueError if invalid
        """
        avg_temp = temperature_data.get('avg_temp')
        
        if avg_temp is None:
            raise ValueError("Temperature data must include 'avg_temp'")
        
        if avg_temp < -20 or avg_temp > 50:
            raise ValueError(f"Temperature {avg_temp}°C is outside reasonable range (-20°C to 50°C)")
        
        return True
    
    def get_species_recommendations(self, species: CalliphoridaeSpecies) -> Dict:
        """
        Get recommendations and warnings for a specific species.
        
        Args:
            species: The Calliphoridae species
            
        Returns:
            Dictionary with recommendations and warnings
        """
        species_info = get_species_info(species)
        
        recommendations = {
            'species_info': species_info,
            'temperature_considerations': [],
            'accuracy_notes': []
        }
        
        # Add species-specific recommendations
        if species == CalliphoridaeSpecies.CHRYSOMYA_RUFIFACIES:
            recommendations['temperature_considerations'].append(
                "C. rufifacies develops poorly below 15°C"
            )
            recommendations['accuracy_notes'].append(
                "Most accurate in warm climates (20-35°C)"
            )
        elif species == CalliphoridaeSpecies.LUCILIA_SERICATA:
            recommendations['temperature_considerations'].append(
                "L. sericata is cold-tolerant but optimal above 15°C"
            )
            recommendations['accuracy_notes'].append(
                "Well-studied species with reliable data"
            )
        elif species == CalliphoridaeSpecies.CALLIPHORA_VICINA:
            recommendations['temperature_considerations'].append(
                "C. vicina prefers cooler temperatures (5-20°C)"
            )
            recommendations['accuracy_notes'].append(
                "May be inaccurate in very warm climates"
            )
        
        return recommendations
    
    def calculate_temperature_adjustment(self, 
                                       base_temp: float, 
                                       actual_temp: float,
                                       temp_variation: Optional[float] = None) -> float:
        """
        Calculate temperature adjustment factor for PMI calculation.
        
        Args:
            base_temp: Base development temperature
            actual_temp: Actual environmental temperature
            temp_variation: Optional temperature variation (standard deviation)
            
        Returns:
            Temperature adjustment factor
        """
        if temp_variation is not None and temp_variation > 5:
            # High temperature variation reduces accuracy
            adjustment = 1.0 + (temp_variation / 100)  # Small penalty for high variation
        else:
            adjustment = 1.0
        
        # Adjust for extreme temperatures
        if actual_temp > 35:
            adjustment *= 1.1  # Slight penalty for very high temps
        elif actual_temp < base_temp + 5:
            adjustment *= 1.2  # Larger penalty for low temps
        
        return adjustment