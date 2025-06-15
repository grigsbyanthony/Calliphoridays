"""
Alternative PMI calculation methods for forensic entomology.
"""
import math
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from .models import ForensicSpecies, CalliphoridaeSpecies, DevelopmentStage, get_development_threshold


class PMIMethod(Enum):
    """Available PMI calculation methods."""
    ADD_STANDARD = "add_standard"  # Standard accumulated degree days
    ADD_OPTIMISTIC = "add_optimistic"  # Minimum development time (fast conditions)
    ADD_CONSERVATIVE = "add_conservative"  # Maximum development time (slow conditions)
    ADH_METHOD = "adh_method"  # Accumulated degree hours
    ISOMEGALEN_METHOD = "isomegalen_method"  # Isomegalen diagram method
    THERMAL_SUMMATION = "thermal_summation"  # Alternative thermal summation
    DEVELOPMENT_RATE = "development_rate"  # Development rate modeling


@dataclass
class PMIEstimate:
    """PMI estimate from a specific method."""
    method: PMIMethod
    pmi_days: float
    pmi_hours: float
    confidence_low: float
    confidence_high: float
    reliability_score: float  # 0-100 score for method reliability
    assumptions: List[str]
    limitations: List[str]
    calculation_details: Dict


@dataclass
class ComparativeResult:
    """Results from multiple PMI methods."""
    estimates: List[PMIEstimate]
    consensus_estimate: Dict
    method_agreement: Dict
    reliability_assessment: Dict
    recommendations: List[str]


class AlternativePMICalculator:
    """
    Calculator implementing multiple PMI estimation methods.
    """
    
    def __init__(self):
        # Method reliability weights (0-1)
        self.method_weights = {
            PMIMethod.ADD_STANDARD: 1.0,
            PMIMethod.ADD_OPTIMISTIC: 0.7,
            PMIMethod.ADD_CONSERVATIVE: 0.7,
            PMIMethod.ADH_METHOD: 0.9,
            PMIMethod.ISOMEGALEN_METHOD: 0.6,
            PMIMethod.THERMAL_SUMMATION: 0.8,
            PMIMethod.DEVELOPMENT_RATE: 0.8
        }
        
        # Temperature adjustment factors for different methods
        self.temp_adjustments = {
            PMIMethod.ADD_OPTIMISTIC: 1.15,  # Assume 15% faster development
            PMIMethod.ADD_CONSERVATIVE: 0.85,  # Assume 15% slower development
        }
    
    def calculate_all_methods(self, species: ForensicSpecies, 
                            stage: DevelopmentStage,
                            temperature_data: Dict,
                            specimen_length: Optional[float] = None,
                            methods: Optional[List[PMIMethod]] = None) -> ComparativeResult:
        """
        Calculate PMI using multiple methods and compare results.
        
        Args:
            species: Calliphoridae species
            stage: Development stage
            temperature_data: Temperature data
            specimen_length: Optional specimen length
            methods: List of methods to use (all if None)
            
        Returns:
            ComparativeResult with all method estimates
        """
        if methods is None:
            methods = list(PMIMethod)
        
        estimates = []
        
        for method in methods:
            try:
                estimate = self._calculate_method(
                    method, species, stage, temperature_data, specimen_length
                )
                estimates.append(estimate)
            except Exception as e:
                # Skip methods that fail
                continue
        
        if not estimates:
            raise ValueError("No PMI methods could be calculated successfully")
        
        # Generate comparative analysis
        consensus = self._generate_consensus(estimates)
        agreement = self._assess_method_agreement(estimates)
        reliability = self._assess_reliability(estimates, species, stage, temperature_data)
        recommendations = self._generate_recommendations(estimates, agreement, reliability)
        
        return ComparativeResult(
            estimates=estimates,
            consensus_estimate=consensus,
            method_agreement=agreement,
            reliability_assessment=reliability,
            recommendations=recommendations
        )
    
    def _calculate_method(self, method: PMIMethod, species: ForensicSpecies,
                         stage: DevelopmentStage, temperature_data: Dict,
                         specimen_length: Optional[float]) -> PMIEstimate:
        """Calculate PMI using a specific method."""
        
        if method == PMIMethod.ADD_STANDARD:
            return self._calculate_add_standard(species, stage, temperature_data, specimen_length)
        elif method == PMIMethod.ADD_OPTIMISTIC:
            return self._calculate_add_optimistic(species, stage, temperature_data, specimen_length)
        elif method == PMIMethod.ADD_CONSERVATIVE:
            return self._calculate_add_conservative(species, stage, temperature_data, specimen_length)
        elif method == PMIMethod.ADH_METHOD:
            return self._calculate_adh_method(species, stage, temperature_data, specimen_length)
        elif method == PMIMethod.ISOMEGALEN_METHOD:
            return self._calculate_isomegalen_method(species, stage, temperature_data, specimen_length)
        elif method == PMIMethod.THERMAL_SUMMATION:
            return self._calculate_thermal_summation(species, stage, temperature_data, specimen_length)
        elif method == PMIMethod.DEVELOPMENT_RATE:
            return self._calculate_development_rate(species, stage, temperature_data, specimen_length)
        else:
            raise ValueError(f"Unknown method: {method}")
    
    def _calculate_add_standard(self, species: ForensicSpecies, stage: DevelopmentStage,
                               temperature_data: Dict, specimen_length: Optional[float]) -> PMIEstimate:
        """Standard ADD method (existing implementation)."""
        threshold = get_development_threshold(species, stage)
        avg_temp = temperature_data['avg_temp']
        effective_temp = avg_temp - threshold.base_temp
        
        if effective_temp <= 0:
            raise ValueError(f"Temperature too low for development")
        
        # Estimate ADD based on stage and specimen length
        estimated_add = self._estimate_add_for_stage(threshold, specimen_length)
        pmi_days = estimated_add / effective_temp
        pmi_hours = pmi_days * 24
        
        # Standard confidence interval (±20%)
        confidence_range = pmi_days * 0.2
        
        return PMIEstimate(
            method=PMIMethod.ADD_STANDARD,
            pmi_days=pmi_days,
            pmi_hours=pmi_hours,
            confidence_low=max(0, pmi_days - confidence_range),
            confidence_high=pmi_days + confidence_range,
            reliability_score=85.0,
            assumptions=[
                "Constant temperature during development",
                "Linear relationship between temperature and development rate",
                "Laboratory-derived development data applies to field conditions"
            ],
            limitations=[
                "Does not account for temperature fluctuations",
                "Assumes optimal development conditions",
                "Species-specific data may be limited"
            ],
            calculation_details={
                'method': 'Accumulated Degree Days',
                'add_required': estimated_add,
                'effective_temperature': effective_temp,
                'base_temperature': threshold.base_temp
            }
        )
    
    def _calculate_add_optimistic(self, species: ForensicSpecies, stage: DevelopmentStage,
                                 temperature_data: Dict, specimen_length: Optional[float]) -> PMIEstimate:
        """Optimistic ADD method (minimum PMI estimate)."""
        threshold = get_development_threshold(species, stage)
        avg_temp = temperature_data['avg_temp']
        
        # Apply optimistic temperature adjustment
        adjusted_temp = avg_temp * self.temp_adjustments[PMIMethod.ADD_OPTIMISTIC]
        effective_temp = adjusted_temp - threshold.base_temp
        
        if effective_temp <= 0:
            raise ValueError(f"Temperature too low for development")
        
        # Use minimum ADD for stage
        min_add = threshold.min_add
        pmi_days = min_add / effective_temp
        pmi_hours = pmi_days * 24
        
        # Tighter confidence interval for minimum estimate
        confidence_range = pmi_days * 0.15
        
        return PMIEstimate(
            method=PMIMethod.ADD_OPTIMISTIC,
            pmi_days=pmi_days,
            pmi_hours=pmi_hours,
            confidence_low=max(0, pmi_days - confidence_range),
            confidence_high=pmi_days + confidence_range,
            reliability_score=70.0,
            assumptions=[
                "Optimal development conditions",
                "Fastest possible development rate",
                "No environmental delays"
            ],
            limitations=[
                "Represents absolute minimum PMI",
                "Rarely achieved in field conditions",
                "Does not account for realistic delays"
            ],
            calculation_details={
                'method': 'Optimistic ADD (Minimum PMI)',
                'add_required': min_add,
                'effective_temperature': effective_temp,
                'temperature_adjustment': self.temp_adjustments[PMIMethod.ADD_OPTIMISTIC]
            }
        )
    
    def _calculate_add_conservative(self, species: ForensicSpecies, stage: DevelopmentStage,
                                   temperature_data: Dict, specimen_length: Optional[float]) -> PMIEstimate:
        """Conservative ADD method (maximum PMI estimate)."""
        threshold = get_development_threshold(species, stage)
        avg_temp = temperature_data['avg_temp']
        
        # Apply conservative temperature adjustment
        adjusted_temp = avg_temp * self.temp_adjustments[PMIMethod.ADD_CONSERVATIVE]
        effective_temp = adjusted_temp - threshold.base_temp
        
        if effective_temp <= 0:
            raise ValueError(f"Temperature too low for development")
        
        # Use maximum ADD for stage
        max_add = threshold.max_add
        pmi_days = max_add / effective_temp
        pmi_hours = pmi_days * 24
        
        # Wider confidence interval for maximum estimate
        confidence_range = pmi_days * 0.25
        
        return PMIEstimate(
            method=PMIMethod.ADD_CONSERVATIVE,
            pmi_days=pmi_days,
            pmi_hours=pmi_hours,
            confidence_low=max(0, pmi_days - confidence_range),
            confidence_high=pmi_days + confidence_range,
            reliability_score=75.0,
            assumptions=[
                "Suboptimal development conditions",
                "Environmental factors slow development",
                "Conservative temperature estimates"
            ],
            limitations=[
                "May overestimate PMI",
                "Accounts for worst-case scenarios",
                "Less precise than standard methods"
            ],
            calculation_details={
                'method': 'Conservative ADD (Maximum PMI)',
                'add_required': max_add,
                'effective_temperature': effective_temp,
                'temperature_adjustment': self.temp_adjustments[PMIMethod.ADD_CONSERVATIVE]
            }
        )
    
    def _calculate_adh_method(self, species: ForensicSpecies, stage: DevelopmentStage,
                             temperature_data: Dict, specimen_length: Optional[float]) -> PMIEstimate:
        """Accumulated Degree Hours method."""
        threshold = get_development_threshold(species, stage)
        avg_temp = temperature_data['avg_temp']
        effective_temp = avg_temp - threshold.base_temp
        
        if effective_temp <= 0:
            raise ValueError(f"Temperature too low for development")
        
        # Convert ADD to ADH (more precise for short time periods)
        estimated_add = self._estimate_add_for_stage(threshold, specimen_length)
        required_adh = estimated_add * 24  # Convert days to hours
        
        pmi_hours = required_adh / effective_temp
        pmi_days = pmi_hours / 24
        
        # More precise confidence interval
        confidence_range = pmi_days * 0.18
        
        return PMIEstimate(
            method=PMIMethod.ADH_METHOD,
            pmi_days=pmi_days,
            pmi_hours=pmi_hours,
            confidence_low=max(0, pmi_days - confidence_range),
            confidence_high=pmi_days + confidence_range,
            reliability_score=90.0,
            assumptions=[
                "Hourly temperature precision is meaningful",
                "Linear development rate within temperature range",
                "Short-term temperature fluctuations matter"
            ],
            limitations=[
                "Requires more precise temperature data",
                "May be over-precise for long PMI periods",
                "Computation complexity vs. benefit trade-off"
            ],
            calculation_details={
                'method': 'Accumulated Degree Hours',
                'adh_required': required_adh,
                'effective_temperature': effective_temp,
                'hourly_precision': True
            }
        )
    
    def _calculate_isomegalen_method(self, species: ForensicSpecies, stage: DevelopmentStage,
                                    temperature_data: Dict, specimen_length: Optional[float]) -> PMIEstimate:
        """Isomegalen diagram method (length-based development)."""
        if specimen_length is None:
            raise ValueError("Specimen length required for Isomegalen method")
        
        threshold = get_development_threshold(species, stage)
        avg_temp = temperature_data['avg_temp']
        
        # Use length-based development curves
        # This is a simplified implementation - real isomegalen diagrams are more complex
        typical_length = threshold.typical_length_mm or 15.0
        length_ratio = specimen_length / typical_length
        
        # Adjust development time based on specimen size
        base_add = self._estimate_add_for_stage(threshold, specimen_length)
        
        # Length-based adjustment (larger specimens = more development time)
        if length_ratio > 1.2:
            adjusted_add = base_add * (0.8 + 0.4 * length_ratio)
        elif length_ratio < 0.8:
            adjusted_add = base_add * (0.6 + 0.5 * length_ratio)
        else:
            adjusted_add = base_add
        
        effective_temp = avg_temp - threshold.base_temp
        if effective_temp <= 0:
            raise ValueError(f"Temperature too low for development")
        
        pmi_days = adjusted_add / effective_temp
        pmi_hours = pmi_days * 24
        
        # Confidence interval based on length measurement precision
        confidence_range = pmi_days * 0.22
        
        return PMIEstimate(
            method=PMIMethod.ISOMEGALEN_METHOD,
            pmi_days=pmi_days,
            pmi_hours=pmi_hours,
            confidence_low=max(0, pmi_days - confidence_range),
            confidence_high=pmi_days + confidence_range,
            reliability_score=65.0,
            assumptions=[
                "Specimen length accurately reflects development stage",
                "Length-development relationship is linear",
                "Individual variation is minimal"
            ],
            limitations=[
                "Requires accurate length measurements",
                "High individual variation in length",
                "Limited validation data for all species"
            ],
            calculation_details={
                'method': 'Isomegalen Diagram (Length-based)',
                'specimen_length': specimen_length,
                'typical_length': typical_length,
                'length_ratio': length_ratio,
                'adjusted_add': adjusted_add
            }
        )
    
    def _calculate_thermal_summation(self, species: ForensicSpecies, stage: DevelopmentStage,
                                    temperature_data: Dict, specimen_length: Optional[float]) -> PMIEstimate:
        """Alternative thermal summation method."""
        threshold = get_development_threshold(species, stage)
        avg_temp = temperature_data['avg_temp']
        
        # Use non-linear thermal summation (accounts for temperature stress)
        base_temp = threshold.base_temp
        optimal_temp = base_temp + 15  # Assume optimal is 15°C above base
        max_temp = base_temp + 25      # Assume stress above this
        
        # Calculate effective temperature with non-linear adjustment
        if avg_temp <= base_temp:
            raise ValueError(f"Temperature too low for development")
        elif avg_temp <= optimal_temp:
            # Linear increase up to optimal
            temp_efficiency = (avg_temp - base_temp) / (optimal_temp - base_temp)
            effective_temp = (avg_temp - base_temp) * temp_efficiency
        else:
            # Decreased efficiency above optimal
            temp_stress = min(1.0, (avg_temp - optimal_temp) / (max_temp - optimal_temp))
            stress_factor = 1.0 - (temp_stress * 0.3)  # Up to 30% reduction
            effective_temp = (optimal_temp - base_temp) * stress_factor
        
        estimated_add = self._estimate_add_for_stage(threshold, specimen_length)
        pmi_days = estimated_add / effective_temp if effective_temp > 0 else float('inf')
        pmi_hours = pmi_days * 24
        
        confidence_range = pmi_days * 0.25
        
        return PMIEstimate(
            method=PMIMethod.THERMAL_SUMMATION,
            pmi_days=pmi_days,
            pmi_hours=pmi_hours,
            confidence_low=max(0, pmi_days - confidence_range),
            confidence_high=pmi_days + confidence_range,
            reliability_score=80.0,
            assumptions=[
                "Non-linear temperature-development relationship",
                "Temperature stress affects development rate",
                "Optimal temperature exists for each species"
            ],
            limitations=[
                "Optimal temperature estimates may be imprecise",
                "Stress factors are species-dependent",
                "Limited validation in extreme temperatures"
            ],
            calculation_details={
                'method': 'Non-linear Thermal Summation',
                'optimal_temperature': optimal_temp,
                'temperature_efficiency': effective_temp / (avg_temp - base_temp) if avg_temp > base_temp else 0,
                'stress_adjusted': avg_temp > optimal_temp
            }
        )
    
    def _calculate_development_rate(self, species: ForensicSpecies, stage: DevelopmentStage,
                                   temperature_data: Dict, specimen_length: Optional[float]) -> PMIEstimate:
        """Development rate modeling method."""
        threshold = get_development_threshold(species, stage)
        avg_temp = temperature_data['avg_temp']
        
        # Use Ikemoto-Takai model for development rate
        base_temp = threshold.base_temp
        
        if avg_temp <= base_temp:
            raise ValueError(f"Temperature too low for development")
        
        # Development rate = a * (T - T0) where a is development rate constant
        # Estimate 'a' from known ADD data
        mid_add = (threshold.min_add + threshold.max_add) / 2
        reference_temp = base_temp + 20  # Reference temperature
        development_rate_constant = 1 / (mid_add * (reference_temp - base_temp))
        
        # Calculate development rate at current temperature
        development_rate = development_rate_constant * (avg_temp - base_temp)
        
        # PMI is inverse of development rate
        pmi_days = 1 / development_rate if development_rate > 0 else float('inf')
        pmi_hours = pmi_days * 24
        
        confidence_range = pmi_days * 0.20
        
        return PMIEstimate(
            method=PMIMethod.DEVELOPMENT_RATE,
            pmi_days=pmi_days,
            pmi_hours=pmi_hours,
            confidence_low=max(0, pmi_days - confidence_range),
            confidence_high=pmi_days + confidence_range,
            reliability_score=82.0,
            assumptions=[
                "Linear relationship between temperature and development rate",
                "Development rate constant is species-specific",
                "Reference temperature data is accurate"
            ],
            limitations=[
                "Simplified model may not capture complex biology",
                "Rate constant estimates may be imprecise",
                "Does not account for developmental non-linearities"
            ],
            calculation_details={
                'method': 'Development Rate Modeling',
                'development_rate': development_rate,
                'rate_constant': development_rate_constant,
                'reference_temperature': reference_temp
            }
        )
    
    def _estimate_add_for_stage(self, threshold, specimen_length: Optional[float]) -> float:
        """Estimate ADD needed for stage (shared helper method)."""
        if specimen_length is None or threshold.typical_length_mm is None:
            return (threshold.min_add + threshold.max_add) / 2
        
        # Adjust based on specimen length
        length_ratio = specimen_length / threshold.typical_length_mm
        
        if length_ratio < 0.8:
            return threshold.min_add + (threshold.max_add - threshold.min_add) * 0.3
        elif length_ratio > 1.2:
            return threshold.min_add + (threshold.max_add - threshold.min_add) * 0.8
        else:
            return (threshold.min_add + threshold.max_add) / 2
    
    def _generate_consensus(self, estimates: List[PMIEstimate]) -> Dict:
        """Generate consensus estimate from multiple methods."""
        if len(estimates) == 1:
            est = estimates[0]
            return {
                'method': 'single_method',
                'pmi_days': est.pmi_days,
                'pmi_hours': est.pmi_hours,
                'confidence_low': est.confidence_low,
                'confidence_high': est.confidence_high
            }
        
        # Weight estimates by reliability scores
        total_weight = sum(est.reliability_score for est in estimates)
        
        if total_weight == 0:
            # Fallback to equal weights
            weights = [1.0] * len(estimates)
            total_weight = len(estimates)
        else:
            weights = [est.reliability_score for est in estimates]
        
        # Calculate weighted averages
        weighted_pmi = sum(est.pmi_days * w for est, w in zip(estimates, weights)) / total_weight
        weighted_conf_low = min(est.confidence_low for est in estimates)
        weighted_conf_high = max(est.confidence_high for est in estimates)
        
        return {
            'method': 'multi_method_consensus',
            'pmi_days': weighted_pmi,
            'pmi_hours': weighted_pmi * 24,
            'confidence_low': weighted_conf_low,
            'confidence_high': weighted_conf_high,
            'methods_used': [est.method.value for est in estimates],
            'reliability_weighted': True
        }
    
    def _assess_method_agreement(self, estimates: List[PMIEstimate]) -> Dict:
        """Assess agreement between methods."""
        if len(estimates) < 2:
            pmi_value = estimates[0].pmi_days if estimates else 0.0
            return {
                'agreement_level': 'single_method', 
                'coefficient_of_variation': 0.0,
                'mean_pmi': pmi_value,
                'std_deviation': 0.0,
                'min_pmi': pmi_value,
                'max_pmi': pmi_value,
                'range': 0.0
            }
        
        pmi_values = [est.pmi_days for est in estimates]
        mean_pmi = sum(pmi_values) / len(pmi_values)
        
        # Calculate coefficient of variation
        variance = sum((x - mean_pmi) ** 2 for x in pmi_values) / len(pmi_values)
        std_dev = math.sqrt(variance)
        cv = (std_dev / mean_pmi) * 100 if mean_pmi > 0 else 0
        
        # Determine agreement level
        if cv < 10:
            agreement_level = 'excellent'
        elif cv < 20:
            agreement_level = 'good'
        elif cv < 35:
            agreement_level = 'moderate'
        else:
            agreement_level = 'poor'
        
        return {
            'agreement_level': agreement_level,
            'coefficient_of_variation': cv,
            'mean_pmi': mean_pmi,
            'std_deviation': std_dev,
            'min_pmi': min(pmi_values),
            'max_pmi': max(pmi_values),
            'range': max(pmi_values) - min(pmi_values)
        }
    
    def _assess_reliability(self, estimates: List[PMIEstimate], species: ForensicSpecies,
                           stage: DevelopmentStage, temperature_data: Dict) -> Dict:
        """Assess overall reliability of estimates."""
        # Calculate average reliability score
        avg_reliability = sum(est.reliability_score for est in estimates) / len(estimates)
        
        # Assess conditions
        temp = temperature_data['avg_temp']
        threshold = get_development_threshold(species, stage)
        
        # Temperature suitability
        temp_optimal = threshold.base_temp + 15
        temp_suitability = 100 - abs(temp - temp_optimal) * 2  # Penalty for deviation
        temp_suitability = max(0, min(100, temp_suitability))
        
        # Method diversity bonus
        method_diversity = len(set(est.method for est in estimates))
        diversity_bonus = min(20, method_diversity * 5)
        
        # Overall reliability
        overall_reliability = (avg_reliability + temp_suitability + diversity_bonus) / 3
        
        return {
            'overall_reliability': overall_reliability,
            'average_method_reliability': avg_reliability,
            'temperature_suitability': temp_suitability,
            'method_diversity_score': diversity_bonus,
            'method_count': len(estimates),
            'reliability_factors': [
                f"Average method reliability: {avg_reliability:.1f}/100",
                f"Temperature suitability: {temp_suitability:.1f}/100",
                f"Method diversity: {method_diversity} methods"
            ]
        }
    
    def _generate_recommendations(self, estimates: List[PMIEstimate], 
                                 agreement: Dict, reliability: Dict) -> List[str]:
        """Generate recommendations based on method comparison."""
        recommendations = []
        
        # Agreement-based recommendations
        if agreement['agreement_level'] == 'poor':
            recommendations.append(
                f"Poor method agreement (CV: {agreement['coefficient_of_variation']:.1f}%) - interpret results with caution"
            )
            recommendations.append(
                "Consider environmental factors that may affect different methods differently"
            )
        elif agreement['agreement_level'] == 'excellent':
            recommendations.append(
                f"Excellent method agreement (CV: {agreement['coefficient_of_variation']:.1f}%) - high confidence in results"
            )
        
        # Reliability-based recommendations
        if reliability['overall_reliability'] < 60:
            recommendations.append(
                "Low overall reliability - collect additional data if possible"
            )
        
        if reliability['temperature_suitability'] < 70:
            recommendations.append(
                "Temperature conditions are suboptimal for accurate PMI estimation"
            )
        
        # Method-specific recommendations
        method_reliabilities = {est.method: est.reliability_score for est in estimates}
        best_method = max(method_reliabilities.items(), key=lambda x: x[1])
        worst_method = min(method_reliabilities.items(), key=lambda x: x[1])
        
        if best_method[1] - worst_method[1] > 30:
            recommendations.append(
                f"Prioritize {best_method[0].value} method (reliability: {best_method[1]:.0f}/100)"
            )
        
        # Range-based recommendations
        if 'range' in agreement and agreement['range'] > agreement['mean_pmi'] * 0.5:
            recommendations.append(
                f"Large PMI range ({agreement['range']:.1f} days) indicates significant uncertainty"
            )
        
        return recommendations