"""
Enhanced validation and data quality assessment for PMI estimates.
"""
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum

from .models import ForensicSpecies, CalliphoridaeSpecies, DevelopmentStage, get_species_info


class ValidationLevel(Enum):
    """Validation severity levels."""
    INFO = "info"
    WARNING = "warning" 
    ERROR = "error"
    CRITICAL = "critical"


class DataQuality(Enum):
    """Data quality ratings."""
    EXCELLENT = "excellent"  # 90-100% confidence
    GOOD = "good"           # 70-89% confidence
    FAIR = "fair"           # 50-69% confidence
    POOR = "poor"           # 30-49% confidence
    UNRELIABLE = "unreliable"  # <30% confidence


class ValidationResult:
    """Container for validation results."""
    
    def __init__(self):
        self.issues: List[Dict] = []
        self.quality_score: float = 100.0
        self.data_quality: DataQuality = DataQuality.EXCELLENT
        self.accuracy_indicators: Dict = {}
        self.warnings: List[str] = []
        self.recommendations: List[str] = []
    
    def add_issue(self, level: ValidationLevel, category: str, message: str, 
                  score_impact: float = 0.0, recommendation: str = None):
        """Add a validation issue."""
        issue = {
            'level': level.value,
            'category': category,
            'message': message,
            'score_impact': score_impact
        }
        self.issues.append(issue)
        
        # Reduce quality score
        self.quality_score = max(0.0, self.quality_score - score_impact)
        
        # Add to warnings if warning level or higher
        if level in [ValidationLevel.WARNING, ValidationLevel.ERROR, ValidationLevel.CRITICAL]:
            self.warnings.append(f"{level.value.upper()}: {message}")
        
        # Add recommendation if provided
        if recommendation:
            self.recommendations.append(recommendation)
        
        # Update data quality rating
        self._update_data_quality()
    
    def _update_data_quality(self):
        """Update data quality based on score."""
        if self.quality_score >= 90:
            self.data_quality = DataQuality.EXCELLENT
        elif self.quality_score >= 70:
            self.data_quality = DataQuality.GOOD
        elif self.quality_score >= 50:
            self.data_quality = DataQuality.FAIR
        elif self.quality_score >= 30:
            self.data_quality = DataQuality.POOR
        else:
            self.data_quality = DataQuality.UNRELIABLE


class PMIValidator:
    """
    Comprehensive validation system for PMI calculations.
    """
    
    def __init__(self):
        self.result = ValidationResult()
        
        # Temperature thresholds for different species
        self.temp_ranges = {
            ForensicSpecies.CHRYSOMYA_RUFIFACIES: (15, 40),
            ForensicSpecies.LUCILIA_SERICATA: (8, 35),
            ForensicSpecies.CALLIPHORA_VICINA: (5, 30),
            ForensicSpecies.COCHLIOMYIA_MACELLARIA: (12, 38),
            ForensicSpecies.PHORMIA_REGINA: (5, 32),
            ForensicSpecies.SARCOPHAGA_BULLATA: (9, 35),
            ForensicSpecies.SARCOPHAGA_CRASSIPALPIS: (8, 33),
            ForensicSpecies.SARCOPHAGA_HAEMORRHOIDALIS: (9, 36),
            ForensicSpecies.BOETTCHERISCA_PEREGRINA: (11, 38)
        }
        
        # Realistic PMI ranges (in days) for different stages
        self.pmi_ranges = {
            DevelopmentStage.FIRST_INSTAR: (0.5, 5),
            DevelopmentStage.SECOND_INSTAR: (1, 8),
            DevelopmentStage.THIRD_INSTAR: (2, 25),
            DevelopmentStage.PUPA: (5, 120)
        }
        
        # Typical specimen lengths (mm) by stage
        self.specimen_lengths = {
            DevelopmentStage.FIRST_INSTAR: (3, 12),
            DevelopmentStage.SECOND_INSTAR: (8, 18),
            DevelopmentStage.THIRD_INSTAR: (12, 22),
            DevelopmentStage.PUPA: (8, 15)  # Puparium length
        }
    
    def validate_inputs(self, species: ForensicSpecies, stage: DevelopmentStage,
                       location: str, discovery_date: str, discovery_time: Optional[str] = None,
                       specimen_length: Optional[float] = None, 
                       ambient_temp: Optional[float] = None) -> ValidationResult:
        """
        Validate all input parameters.
        
        Args:
            species: Calliphoridae species
            stage: Development stage
            location: Discovery location
            discovery_date: Discovery date string
            discovery_time: Optional discovery time
            specimen_length: Optional specimen length in mm
            ambient_temp: Optional ambient temperature
            
        Returns:
            ValidationResult object
        """
        self.result = ValidationResult()
        
        # Validate species and stage combination
        self._validate_species_stage(species, stage)
        
        # Validate location
        self._validate_location(location)
        
        # Validate date and time
        self._validate_datetime(discovery_date, discovery_time)
        
        # Validate specimen length
        if specimen_length is not None:
            self._validate_specimen_length(specimen_length, stage)
        
        # Validate temperature
        if ambient_temp is not None:
            self._validate_temperature(ambient_temp, species)
        
        return self.result
    
    def validate_calculation_results(self, pmi_result: Dict, temperature_data: Dict,
                                   species: ForensicSpecies, 
                                   stage: DevelopmentStage) -> ValidationResult:
        """
        Validate PMI calculation results for reasonableness.
        
        Args:
            pmi_result: PMI calculation results
            temperature_data: Temperature data used
            species: Species used in calculation
            stage: Development stage
            
        Returns:
            Updated ValidationResult object
        """
        # Validate PMI estimate reasonableness
        self._validate_pmi_estimate(pmi_result['pmi_days'], stage)
        
        # Validate temperature consistency
        self._validate_temperature_consistency(temperature_data, species)
        
        # Check calculation consistency
        self._validate_calculation_consistency(pmi_result)
        
        # Assess method accuracy for conditions
        self._assess_method_accuracy(pmi_result, temperature_data, species, stage)
        
        return self.result
    
    def _validate_species_stage(self, species: ForensicSpecies, stage: DevelopmentStage):
        """Validate species and development stage combination."""
        species_info = get_species_info(species)
        
        # Check if this is a common forensic species
        if species not in self.temp_ranges:
            self.result.add_issue(
                ValidationLevel.WARNING,
                "species",
                f"Limited data available for {species.value}",
                10.0,
                "Verify species identification with morphological keys"
            )
        
        # Stage-specific validations
        if stage == DevelopmentStage.PUPA:
            self.result.add_issue(
                ValidationLevel.INFO,
                "stage", 
                "Pupal stage PMI estimates have higher uncertainty",
                5.0,
                "Consider using pre-pupal stage specimens if available"
            )
    
    def _validate_location(self, location: str):
        """Validate location string."""
        if not location or len(location.strip()) < 3:
            self.result.add_issue(
                ValidationLevel.ERROR,
                "location",
                "Location must be specified with at least 3 characters",
                20.0,
                "Provide city, state/province, and country for accurate weather data"
            )
        
        # Check for common location patterns
        if not re.search(r'[A-Za-z]', location):
            self.result.add_issue(
                ValidationLevel.WARNING,
                "location",
                "Location should contain alphabetic characters",
                5.0
            )
    
    def _validate_datetime(self, discovery_date: str, discovery_time: Optional[str]):
        """Validate discovery date and time."""
        try:
            # Parse and validate date
            date_obj = datetime.strptime(discovery_date, '%Y-%m-%d')
            
            # Check if date is in the future
            if date_obj > datetime.now():
                self.result.add_issue(
                    ValidationLevel.ERROR,
                    "date",
                    "Discovery date cannot be in the future",
                    25.0,
                    "Verify discovery date is correct"
                )
            
            # Check if date is too far in the past (>2 years)
            if date_obj < datetime.now() - timedelta(days=730):
                self.result.add_issue(
                    ValidationLevel.WARNING,
                    "date",
                    "Discovery date is more than 2 years ago",
                    5.0,
                    "Ensure historical weather data is available for this date"
                )
            
            # Validate time if provided
            if discovery_time:
                try:
                    time_obj = datetime.strptime(discovery_time, '%H:%M')
                    
                    # Note optimal collection times
                    hour = time_obj.hour
                    if 22 <= hour or hour <= 6:
                        self.result.add_issue(
                            ValidationLevel.INFO,
                            "time",
                            "Discovery during nighttime hours noted",
                            0.0,
                            "Consider temperature variation during overnight period"
                        )
                        
                except ValueError:
                    self.result.add_issue(
                        ValidationLevel.WARNING,
                        "time",
                        "Invalid time format (should be HH:MM)",
                        5.0,
                        "Use 24-hour format (e.g., 14:30 for 2:30 PM)"
                    )
        
        except ValueError:
            self.result.add_issue(
                ValidationLevel.ERROR,
                "date",
                "Invalid date format (should be YYYY-MM-DD)",
                20.0,
                "Use standard date format (e.g., 2024-06-15)"
            )
    
    def _validate_specimen_length(self, length: float, stage: DevelopmentStage):
        """Validate specimen length against expected ranges."""
        if length <= 0:
            self.result.add_issue(
                ValidationLevel.ERROR,
                "specimen",
                "Specimen length must be positive",
                15.0
            )
            return
        
        if length > 50:
            self.result.add_issue(
                ValidationLevel.WARNING,
                "specimen",
                f"Specimen length ({length}mm) seems unusually large",
                10.0,
                "Verify measurement is in millimeters, not centimeters"
            )
            return
        
        # Check against expected ranges for stage
        expected_range = self.specimen_lengths.get(stage)
        if expected_range:
            min_len, max_len = expected_range
            
            if length < min_len * 0.5:
                self.result.add_issue(
                    ValidationLevel.WARNING,
                    "specimen",
                    f"Specimen length ({length}mm) is smaller than typical for {stage.value}",
                    8.0,
                    "Verify development stage identification"
                )
            elif length > max_len * 1.5:
                self.result.add_issue(
                    ValidationLevel.WARNING,
                    "specimen",
                    f"Specimen length ({length}mm) is larger than typical for {stage.value}",
                    8.0,
                    "Verify development stage identification"
                )
            else:
                # Length is reasonable, improve quality score
                self.result.quality_score = min(100.0, self.result.quality_score + 5.0)
    
    def _validate_temperature(self, temp: float, species: ForensicSpecies):
        """Validate temperature against species requirements."""
        # Check extreme temperatures
        if temp < -30 or temp > 60:
            self.result.add_issue(
                ValidationLevel.ERROR,
                "temperature",
                f"Temperature ({temp}°C) is outside realistic range",
                25.0,
                "Verify temperature measurement and units"
            )
            return
        
        # Check species-specific ranges
        temp_range = self.temp_ranges.get(species)
        if temp_range:
            min_temp, max_temp = temp_range
            
            if temp < min_temp:
                self.result.add_issue(
                    ValidationLevel.WARNING,
                    "temperature",
                    f"Temperature ({temp}°C) is below optimal range for {species.value}",
                    10.0,
                    "Development may be significantly slower than calculated"
                )
            elif temp > max_temp:
                self.result.add_issue(
                    ValidationLevel.WARNING,
                    "temperature",
                    f"Temperature ({temp}°C) is above optimal range for {species.value}",
                    10.0,
                    "High temperatures may affect development accuracy"
                )
        
        # Check if temperature is below base temperature for any species
        # Base temperatures are typically: Lucilia sericata (8°C), Calliphora vicina (6°C), etc.
        typical_base_temps = {
            ForensicSpecies.LUCILIA_SERICATA: 8.0,
            ForensicSpecies.CALLIPHORA_VICINA: 6.0,
            ForensicSpecies.CHRYSOMYA_RUFIFACIES: 10.0,
            ForensicSpecies.COCHLIOMYIA_MACELLARIA: 12.0,
            ForensicSpecies.PHORMIA_REGINA: 5.0,
            ForensicSpecies.SARCOPHAGA_BULLATA: 9.0,
            ForensicSpecies.SARCOPHAGA_CRASSIPALPIS: 8.5,
            ForensicSpecies.SARCOPHAGA_HAEMORRHOIDALIS: 9.5,
            ForensicSpecies.BOETTCHERISCA_PEREGRINA: 11.0
        }
        
        base_temp = typical_base_temps.get(species, 8.0)  # Default to 8°C
        if temp <= base_temp:
            self.result.add_issue(
                ValidationLevel.CRITICAL,
                "temperature",
                f"Temperature ({temp}°C) is at or below base temperature ({base_temp}°C) for {species.value}",
                40.0,
                "Development is unlikely at this temperature. Results are highly unreliable."
            )
    
    def _validate_pmi_estimate(self, pmi_days: float, stage: DevelopmentStage):
        """Validate PMI estimate for reasonableness."""
        if pmi_days <= 0:
            self.result.add_issue(
                ValidationLevel.ERROR,
                "calculation",
                "PMI estimate must be positive",
                30.0
            )
            return
        
        # Check against expected ranges
        expected_range = self.pmi_ranges.get(stage)
        if expected_range:
            min_pmi, max_pmi = expected_range
            
            if pmi_days < min_pmi * 0.1:
                self.result.add_issue(
                    ValidationLevel.WARNING,
                    "calculation",
                    f"PMI estimate ({pmi_days:.1f} days) seems unusually short for {stage.value}",
                    15.0,
                    "Verify temperature data and stage identification"
                )
            elif pmi_days > max_pmi * 2:
                self.result.add_issue(
                    ValidationLevel.WARNING,
                    "calculation",
                    f"PMI estimate ({pmi_days:.1f} days) seems unusually long for {stage.value}",
                    15.0,
                    "Check for environmental factors that may slow development"
                )
    
    def _validate_temperature_consistency(self, temp_data: Dict, species: ForensicSpecies):
        """Validate temperature data consistency."""
        avg_temp = temp_data.get('avg_temp')
        min_temp = temp_data.get('min_temp')
        max_temp = temp_data.get('max_temp')
        
        if min_temp and max_temp and avg_temp:
            # Check temperature range reasonableness
            temp_range = max_temp - min_temp
            
            if temp_range > 25:
                self.result.add_issue(
                    ValidationLevel.WARNING,
                    "temperature",
                    f"Large temperature range ({temp_range:.1f}°C) may affect accuracy",
                    8.0,
                    "Consider using more specific time-of-day temperature data"
                )
            
            if avg_temp < min_temp or avg_temp > max_temp:
                self.result.add_issue(
                    ValidationLevel.ERROR,
                    "temperature",
                    "Average temperature outside of min/max range",
                    20.0
                )
    
    def _validate_calculation_consistency(self, pmi_result: Dict):
        """Validate internal calculation consistency."""
        pmi_days = pmi_result.get('pmi_days', 0)
        pmi_hours = pmi_result.get('pmi_hours', 0)
        confidence_low = pmi_result.get('confidence_low', 0)
        confidence_high = pmi_result.get('confidence_high', 0)
        
        # Check days/hours consistency
        if abs(pmi_days * 24 - pmi_hours) > 0.1:
            self.result.add_issue(
                ValidationLevel.ERROR,
                "calculation",
                "Inconsistency between days and hours calculation",
                25.0
            )
        
        # Check confidence interval consistency
        if confidence_low >= pmi_days or confidence_high <= pmi_days:
            self.result.add_issue(
                ValidationLevel.ERROR,
                "calculation",
                "Invalid confidence interval",
                20.0
            )
        
        if confidence_high < confidence_low:
            self.result.add_issue(
                ValidationLevel.ERROR,
                "calculation",
                "Confidence interval bounds are reversed",
                25.0
            )
    
    def _assess_method_accuracy(self, pmi_result: Dict, temp_data: Dict, 
                               species: ForensicSpecies, stage: DevelopmentStage):
        """Assess accuracy of the ADD method for given conditions."""
        accuracy_factors = []
        
        # Temperature stability factor
        avg_temp = temp_data.get('avg_temp', 20)
        temp_range = 0
        if temp_data.get('min_temp') and temp_data.get('max_temp'):
            temp_range = temp_data['max_temp'] - temp_data['min_temp']
        
        if temp_range <= 10:
            accuracy_factors.append("Stable temperature conditions")
        elif temp_range <= 20:
            accuracy_factors.append("Moderate temperature variation")
        else:
            accuracy_factors.append("High temperature variation")
            self.result.quality_score = max(0.0, self.result.quality_score - 5)
        
        # Species data reliability
        if species in [ForensicSpecies.LUCILIA_SERICATA, ForensicSpecies.CALLIPHORA_VICINA]:
            accuracy_factors.append("Well-studied species with reliable data")
            self.result.quality_score = min(100.0, self.result.quality_score + 5)
        else:
            accuracy_factors.append("Limited research data for this species")
            self.result.quality_score = max(0.0, self.result.quality_score - 3)
        
        # Stage reliability
        if stage in [DevelopmentStage.SECOND_INSTAR, DevelopmentStage.THIRD_INSTAR]:
            accuracy_factors.append("Optimal development stage for PMI estimation")
        elif stage == DevelopmentStage.FIRST_INSTAR:
            accuracy_factors.append("Early stage - shorter PMI with higher relative uncertainty")
            self.result.quality_score = max(0.0, self.result.quality_score - 5)
        else:  # PUPA
            accuracy_factors.append("Pupal stage - longer development with variable duration")
            self.result.quality_score = max(0.0, self.result.quality_score - 8)
        
        # Store accuracy indicators
        self.result.accuracy_indicators = {
            'method': 'Accumulated Degree Days (ADD)',
            'reliability_factors': accuracy_factors,
            'temperature_stability': 'High' if temp_range <= 10 else 'Medium' if temp_range <= 20 else 'Low',
            'species_data_quality': 'High' if species in [ForensicSpecies.LUCILIA_SERICATA, ForensicSpecies.CALLIPHORA_VICINA] else 'Medium',
            'stage_suitability': 'Optimal' if stage in [DevelopmentStage.SECOND_INSTAR, DevelopmentStage.THIRD_INSTAR] else 'Suboptimal'
        }
        
        # Final quality score adjustment
        self.result._update_data_quality()
    
    def generate_validation_report(self) -> str:
        """Generate a human-readable validation report."""
        lines = []
        lines.append("VALIDATION REPORT")
        lines.append("=" * 40)
        lines.append(f"Data Quality: {self.result.data_quality.value.upper()}")
        lines.append(f"Quality Score: {self.result.quality_score:.1f}/100")
        lines.append("")
        
        if self.result.issues:
            lines.append("VALIDATION ISSUES:")
            lines.append("-" * 20)
            for issue in self.result.issues:
                level_indicator = {
                    'info': 'ℹ️',
                    'warning': '⚠️', 
                    'error': '❌',
                    'critical': '🚨'
                }.get(issue['level'], '•')
                
                lines.append(f"{level_indicator} {issue['level'].upper()}: {issue['message']}")
            lines.append("")
        
        if self.result.recommendations:
            lines.append("RECOMMENDATIONS:")
            lines.append("-" * 20)
            for rec in self.result.recommendations:
                lines.append(f"• {rec}")
            lines.append("")
        
        if self.result.accuracy_indicators:
            lines.append("ACCURACY ASSESSMENT:")
            lines.append("-" * 20)
            acc = self.result.accuracy_indicators
            lines.append(f"Method: {acc.get('method', 'Unknown')}")
            lines.append(f"Temperature Stability: {acc.get('temperature_stability', 'Unknown')}")
            lines.append(f"Species Data Quality: {acc.get('species_data_quality', 'Unknown')}")
            lines.append(f"Stage Suitability: {acc.get('stage_suitability', 'Unknown')}")
            
            if acc.get('reliability_factors'):
                lines.append("\nReliability Factors:")
                for factor in acc['reliability_factors']:
                    lines.append(f"• {factor}")
        
        return "\n".join(lines)