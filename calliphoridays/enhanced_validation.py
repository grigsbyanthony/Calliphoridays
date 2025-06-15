"""
Enhanced validation features for forensic entomology PMI calculations.

This module provides advanced validation capabilities including:
- Uncertainty propagation through calculations
- Monte Carlo simulation for confidence intervals
- Cross-validation with multiple methods
- Known case validation against published studies
"""

import numpy as np
import random
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import math

from .models import ForensicSpecies, DevelopmentStage, get_development_threshold, get_species_info
from .pmi_calculator import PMICalculator
from .alternative_methods import AlternativePMICalculator, PMIMethod


class UncertaintySource(Enum):
    """Sources of uncertainty in PMI calculations."""
    TEMPERATURE_MEASUREMENT = "temperature_measurement"
    TEMPERATURE_VARIATION = "temperature_variation"
    SPECIES_IDENTIFICATION = "species_identification"
    STAGE_IDENTIFICATION = "stage_identification"
    DEVELOPMENT_THRESHOLD = "development_threshold"
    SPECIMEN_LENGTH = "specimen_length"
    MODEL_LIMITATIONS = "model_limitations"


@dataclass
class UncertaintyComponent:
    """Individual uncertainty component."""
    source: UncertaintySource
    value: float  # Standard deviation or relative uncertainty
    description: str
    impact_factor: float = 1.0  # How much this affects final PMI


@dataclass
class MonteCarloResult:
    """Results from Monte Carlo simulation."""
    mean_pmi: float
    std_pmi: float
    confidence_intervals: Dict[int, Tuple[float, float]]  # {95: (low, high), 99: (low, high)}
    distribution: List[float]  # All simulated PMI values
    convergence_achieved: bool
    iterations_used: int


@dataclass
class CrossValidationResult:
    """Results from cross-validation analysis."""
    method_agreement: Dict[str, float]  # Agreement between methods
    consensus_estimate: float
    reliability_scores: Dict[str, float]
    outlier_methods: List[str]
    overall_confidence: float


@dataclass
class KnownCaseResult:
    """Results from known case validation."""
    case_name: str
    published_pmi: float
    calculated_pmi: float
    relative_error: float
    within_confidence: bool
    notes: str


class EnhancedValidator:
    """
    Advanced validation system with uncertainty quantification and validation studies.
    """
    
    def __init__(self):
        self.pmi_calculator = PMICalculator()
        self.alt_calculator = AlternativePMICalculator()
        
        # Known validation cases from published literature
        self.known_cases = self._load_known_cases()
        
        # Default uncertainty parameters
        self.default_uncertainties = {
            UncertaintySource.TEMPERATURE_MEASUREMENT: 1.0,  # ±1°C
            UncertaintySource.TEMPERATURE_VARIATION: 0.15,   # 15% relative
            UncertaintySource.SPECIES_IDENTIFICATION: 0.05,  # 5% relative
            UncertaintySource.STAGE_IDENTIFICATION: 0.1,     # 10% relative
            UncertaintySource.DEVELOPMENT_THRESHOLD: 0.2,    # 20% relative
            UncertaintySource.SPECIMEN_LENGTH: 0.1,          # 10% relative
            UncertaintySource.MODEL_LIMITATIONS: 0.25        # 25% relative
        }
    
    def propagate_uncertainties(self, 
                               species: ForensicSpecies,
                               stage: DevelopmentStage,
                               temperature_data: Dict,
                               specimen_length: Optional[float] = None,
                               custom_uncertainties: Optional[Dict] = None) -> Dict:
        """
        Propagate uncertainties through PMI calculation using analytical methods.
        
        Args:
            species: Forensic species
            stage: Development stage
            temperature_data: Temperature data
            specimen_length: Optional specimen length
            custom_uncertainties: Custom uncertainty values
            
        Returns:
            Dictionary with uncertainty analysis results
        """
        uncertainties = self.default_uncertainties.copy()
        if custom_uncertainties:
            uncertainties.update(custom_uncertainties)
        
        # Get base calculation
        base_pmi = self.pmi_calculator.calculate_pmi(
            species, stage, temperature_data, specimen_length
        )
        
        # Calculate partial derivatives and uncertainty contributions
        uncertainty_components = []
        total_variance = 0.0
        
        # Temperature uncertainty
        temp_uncertainty = self._calculate_temperature_uncertainty(
            base_pmi, temperature_data, uncertainties
        )
        uncertainty_components.append(temp_uncertainty)
        total_variance += temp_uncertainty.value ** 2
        
        # Development threshold uncertainty
        threshold_uncertainty = self._calculate_threshold_uncertainty(
            base_pmi, species, stage, uncertainties
        )
        uncertainty_components.append(threshold_uncertainty)
        total_variance += threshold_uncertainty.value ** 2
        
        # Specimen length uncertainty (if provided)
        if specimen_length:
            length_uncertainty = self._calculate_length_uncertainty(
                base_pmi, specimen_length, uncertainties
            )
            uncertainty_components.append(length_uncertainty)
            total_variance += length_uncertainty.value ** 2
        
        # Model limitations uncertainty
        model_uncertainty = UncertaintyComponent(
            source=UncertaintySource.MODEL_LIMITATIONS,
            value=base_pmi['pmi_days'] * uncertainties[UncertaintySource.MODEL_LIMITATIONS],
            description="Inherent model limitations and approximations",
            impact_factor=1.0
        )
        uncertainty_components.append(model_uncertainty)
        total_variance += model_uncertainty.value ** 2
        
        # Calculate total uncertainty
        total_std = math.sqrt(total_variance)
        relative_uncertainty = total_std / base_pmi['pmi_days']
        
        return {
            'base_pmi': base_pmi['pmi_days'],
            'total_uncertainty': total_std,
            'relative_uncertainty': relative_uncertainty,
            'uncertainty_components': uncertainty_components,
            'propagated_confidence_95': (
                base_pmi['pmi_days'] - 1.96 * total_std,
                base_pmi['pmi_days'] + 1.96 * total_std
            ),
            'propagated_confidence_99': (
                base_pmi['pmi_days'] - 2.58 * total_std,
                base_pmi['pmi_days'] + 2.58 * total_std
            )
        }
    
    def monte_carlo_simulation(self,
                              species: ForensicSpecies,
                              stage: DevelopmentStage,
                              temperature_data: Dict,
                              specimen_length: Optional[float] = None,
                              iterations: int = 10000,
                              confidence_levels: List[int] = [90, 95, 99]) -> MonteCarloResult:
        """
        Perform Monte Carlo simulation to estimate PMI uncertainty.
        
        Args:
            species: Forensic species
            stage: Development stage
            temperature_data: Temperature data
            specimen_length: Optional specimen length
            iterations: Number of Monte Carlo iterations
            confidence_levels: Confidence levels to calculate
            
        Returns:
            MonteCarloResult object
        """
        pmi_samples = []
        convergence_window = 1000  # Check convergence every N iterations
        convergence_threshold = 0.01  # Relative change threshold for convergence
        
        # Get base threshold data for sampling
        threshold = get_development_threshold(species, stage)
        
        for i in range(iterations):
            # Sample uncertain parameters
            sampled_temp = self._sample_temperature(temperature_data)
            sampled_threshold_data = self._sample_development_threshold(threshold)
            sampled_length = self._sample_specimen_length(specimen_length) if specimen_length else None
            
            try:
                # Create modified temperature data
                temp_data_sample = temperature_data.copy()
                temp_data_sample['avg_temp'] = sampled_temp
                
                # Calculate PMI with sampled parameters
                # We need to temporarily modify the threshold data
                original_threshold = threshold
                # Create a modified calculator for this sample
                pmi_result = self._calculate_pmi_with_sampled_params(
                    species, stage, temp_data_sample, sampled_threshold_data, sampled_length
                )
                
                pmi_samples.append(pmi_result)
                
            except Exception:
                # Skip invalid samples
                continue
            
            # Check convergence periodically
            if i > 0 and i % convergence_window == 0:
                if self._check_convergence(pmi_samples, convergence_threshold):
                    break
        
        # Calculate statistics
        pmi_array = np.array(pmi_samples)
        mean_pmi = np.mean(pmi_array)
        std_pmi = np.std(pmi_array)
        
        # Calculate confidence intervals
        confidence_intervals = {}
        for level in confidence_levels:
            alpha = (100 - level) / 2
            lower = np.percentile(pmi_array, alpha)
            upper = np.percentile(pmi_array, 100 - alpha)
            confidence_intervals[level] = (lower, upper)
        
        return MonteCarloResult(
            mean_pmi=mean_pmi,
            std_pmi=std_pmi,
            confidence_intervals=confidence_intervals,
            distribution=pmi_samples,
            convergence_achieved=len(pmi_samples) < iterations,
            iterations_used=len(pmi_samples)
        )
    
    def cross_validate_methods(self,
                              species: ForensicSpecies,
                              stage: DevelopmentStage,
                              temperature_data: Dict,
                              specimen_length: Optional[float] = None) -> CrossValidationResult:
        """
        Perform cross-validation using multiple PMI calculation methods.
        
        Args:
            species: Forensic species
            stage: Development stage
            temperature_data: Temperature data
            specimen_length: Optional specimen length
            
        Returns:
            CrossValidationResult object
        """
        # Get results from all available methods
        alt_results = self.alt_calculator.calculate_all_methods(
            species, stage, temperature_data, specimen_length
        )
        
        # Extract PMI estimates
        method_estimates = {}
        reliability_scores = {}
        
        for estimate in alt_results.estimates:
            method_name = estimate.method.value
            method_estimates[method_name] = estimate.pmi_days
            reliability_scores[method_name] = estimate.reliability_score
        
        # Calculate method agreement
        method_agreement = self._calculate_method_agreement(method_estimates)
        
        # Identify outlier methods
        outlier_methods = self._identify_outlier_methods(method_estimates)
        
        # Calculate consensus estimate (weighted by reliability)
        consensus_estimate = self._calculate_weighted_consensus(
            method_estimates, reliability_scores, outlier_methods
        )
        
        # Calculate overall confidence
        overall_confidence = self._calculate_overall_confidence(
            method_agreement, reliability_scores, outlier_methods
        )
        
        return CrossValidationResult(
            method_agreement=method_agreement,
            consensus_estimate=consensus_estimate,
            reliability_scores=reliability_scores,
            outlier_methods=outlier_methods,
            overall_confidence=overall_confidence
        )
    
    def validate_against_known_cases(self,
                                   species: ForensicSpecies,
                                   stage: DevelopmentStage,
                                   verbose: bool = False) -> List[KnownCaseResult]:
        """
        Validate PMI calculations against known cases from literature.
        
        Args:
            species: Forensic species to validate
            stage: Development stage to validate
            verbose: Whether to show detailed output
            
        Returns:
            List of KnownCaseResult objects
        """
        results = []
        
        # Filter known cases for this species and stage
        relevant_cases = [
            case for case in self.known_cases
            if case['species'] == species and case['stage'] == stage
        ]
        
        if verbose:
            print(f"Found {len(relevant_cases)} known cases for {species.value} {stage.value}")
        
        for case in relevant_cases:
            try:
                # Calculate PMI using our method
                calculated_pmi = self.pmi_calculator.calculate_pmi(
                    species=case['species'],
                    stage=case['stage'],
                    temperature_data=case['temperature_data'],
                    specimen_length=case.get('specimen_length')
                )
                
                # Compare with published result
                published_pmi = case['published_pmi_days']
                calculated_pmi_days = calculated_pmi['pmi_days']
                
                relative_error = abs(calculated_pmi_days - published_pmi) / published_pmi
                
                # Check if within confidence interval
                within_confidence = (
                    calculated_pmi['confidence_low'] <= published_pmi <= 
                    calculated_pmi['confidence_high']
                )
                
                result = KnownCaseResult(
                    case_name=case['name'],
                    published_pmi=published_pmi,
                    calculated_pmi=calculated_pmi_days,
                    relative_error=relative_error,
                    within_confidence=within_confidence,
                    notes=case.get('notes', '')
                )
                
                results.append(result)
                
                if verbose:
                    print(f"Case: {case['name']}")
                    print(f"  Published: {published_pmi:.1f} days")
                    print(f"  Calculated: {calculated_pmi_days:.1f} days")
                    print(f"  Error: {relative_error:.1%}")
                    print(f"  Within CI: {within_confidence}")
                    print()
                
            except Exception as e:
                if verbose:
                    print(f"Error validating case {case['name']}: {e}")
                continue
        
        return results
    
    def comprehensive_validation_report(self,
                                      species: ForensicSpecies,
                                      stage: DevelopmentStage,
                                      temperature_data: Dict,
                                      specimen_length: Optional[float] = None) -> Dict:
        """
        Generate a comprehensive validation report combining all methods.
        
        Args:
            species: Forensic species
            stage: Development stage
            temperature_data: Temperature data
            specimen_length: Optional specimen length
            
        Returns:
            Comprehensive validation results dictionary
        """
        # Perform all validation analyses
        uncertainty_analysis = self.propagate_uncertainties(
            species, stage, temperature_data, specimen_length
        )
        
        monte_carlo_results = self.monte_carlo_simulation(
            species, stage, temperature_data, specimen_length, iterations=5000
        )
        
        cross_validation_results = self.cross_validate_methods(
            species, stage, temperature_data, specimen_length
        )
        
        known_case_results = self.validate_against_known_cases(species, stage)
        
        # Calculate overall validation score
        validation_score = self._calculate_overall_validation_score(
            uncertainty_analysis, monte_carlo_results, 
            cross_validation_results, known_case_results
        )
        
        return {
            'uncertainty_analysis': uncertainty_analysis,
            'monte_carlo_results': monte_carlo_results,
            'cross_validation_results': cross_validation_results,
            'known_case_results': known_case_results,
            'overall_validation_score': validation_score,
            'recommendations': self._generate_validation_recommendations(
                uncertainty_analysis, cross_validation_results, known_case_results
            )
        }
    
    # Helper methods
    
    def _calculate_temperature_uncertainty(self, base_pmi: Dict, temp_data: Dict, 
                                         uncertainties: Dict) -> UncertaintyComponent:
        """Calculate uncertainty contribution from temperature measurement."""
        avg_temp = temp_data['avg_temp']
        temp_std = uncertainties[UncertaintySource.TEMPERATURE_MEASUREMENT]
        
        # Partial derivative: d(PMI)/d(T) = -PMI/(T-T_base)
        base_temp = base_pmi['base_temp']
        if avg_temp > base_temp:
            partial_derivative = -base_pmi['pmi_days'] / (avg_temp - base_temp)
            uncertainty_contribution = abs(partial_derivative * temp_std)
        else:
            uncertainty_contribution = base_pmi['pmi_days'] * 0.5  # Large uncertainty for low temps
        
        return UncertaintyComponent(
            source=UncertaintySource.TEMPERATURE_MEASUREMENT,
            value=uncertainty_contribution,
            description=f"Temperature measurement uncertainty (±{temp_std}°C)",
            impact_factor=1.0
        )
    
    def _calculate_threshold_uncertainty(self, base_pmi: Dict, species: ForensicSpecies,
                                       stage: DevelopmentStage, uncertainties: Dict) -> UncertaintyComponent:
        """Calculate uncertainty from development threshold variation."""
        threshold = get_development_threshold(species, stage)
        relative_uncertainty = uncertainties[UncertaintySource.DEVELOPMENT_THRESHOLD]
        
        # Development threshold uncertainty directly propagates to PMI
        uncertainty_contribution = base_pmi['pmi_days'] * relative_uncertainty
        
        return UncertaintyComponent(
            source=UncertaintySource.DEVELOPMENT_THRESHOLD,
            value=uncertainty_contribution,
            description=f"Development threshold uncertainty ({relative_uncertainty:.1%})",
            impact_factor=1.0
        )
    
    def _calculate_length_uncertainty(self, base_pmi: Dict, specimen_length: float,
                                    uncertainties: Dict) -> UncertaintyComponent:
        """Calculate uncertainty from specimen length measurement."""
        relative_uncertainty = uncertainties[UncertaintySource.SPECIMEN_LENGTH]
        
        # Length uncertainty has moderate impact on PMI estimate
        uncertainty_contribution = base_pmi['pmi_days'] * relative_uncertainty * 0.5
        
        return UncertaintyComponent(
            source=UncertaintySource.SPECIMEN_LENGTH,
            value=uncertainty_contribution,
            description=f"Specimen length measurement uncertainty ({relative_uncertainty:.1%})",
            impact_factor=0.5
        )
    
    def _sample_temperature(self, temp_data: Dict) -> float:
        """Sample temperature from uncertainty distribution."""
        avg_temp = temp_data['avg_temp']
        temp_std = self.default_uncertainties[UncertaintySource.TEMPERATURE_MEASUREMENT]
        return np.random.normal(avg_temp, temp_std)
    
    def _sample_development_threshold(self, threshold) -> Dict:
        """Sample development threshold parameters."""
        relative_uncertainty = self.default_uncertainties[UncertaintySource.DEVELOPMENT_THRESHOLD]
        
        # Sample ADD threshold
        mid_add = (threshold.min_add + threshold.max_add) / 2
        add_std = mid_add * relative_uncertainty
        sampled_add = np.random.normal(mid_add, add_std)
        
        # Sample base temperature
        base_temp_std = threshold.base_temp * 0.1  # 10% uncertainty
        sampled_base_temp = np.random.normal(threshold.base_temp, base_temp_std)
        
        return {
            'sampled_add': max(0.1, sampled_add),  # Ensure positive
            'sampled_base_temp': max(0, sampled_base_temp)  # Ensure non-negative
        }
    
    def _sample_specimen_length(self, length: float) -> float:
        """Sample specimen length from uncertainty distribution."""
        relative_uncertainty = self.default_uncertainties[UncertaintySource.SPECIMEN_LENGTH]
        length_std = length * relative_uncertainty
        return max(0.1, np.random.normal(length, length_std))
    
    def _calculate_pmi_with_sampled_params(self, species: ForensicSpecies, stage: DevelopmentStage,
                                         temp_data: Dict, threshold_data: Dict, 
                                         specimen_length: Optional[float]) -> float:
        """Calculate PMI with sampled parameters."""
        avg_temp = temp_data['avg_temp']
        sampled_add = threshold_data['sampled_add']
        sampled_base_temp = threshold_data['sampled_base_temp']
        
        if avg_temp <= sampled_base_temp:
            effective_temp = 0.5  # Minimal effective temperature
        else:
            effective_temp = avg_temp - sampled_base_temp
        
        # Apply specimen length adjustment if provided
        if specimen_length:
            # Simple length-based adjustment
            threshold = get_development_threshold(species, stage)
            if threshold.typical_length_mm:
                length_ratio = specimen_length / threshold.typical_length_mm
                if length_ratio < 0.8:
                    sampled_add *= 0.7  # Smaller specimens, less development
                elif length_ratio > 1.2:
                    sampled_add *= 1.3  # Larger specimens, more development
        
        return sampled_add / effective_temp
    
    def _check_convergence(self, samples: List[float], threshold: float) -> bool:
        """Check if Monte Carlo simulation has converged."""
        if len(samples) < 2000:  # Need minimum samples
            return False
        
        # Check last 1000 vs previous 1000 samples
        recent_mean = np.mean(samples[-1000:])
        previous_mean = np.mean(samples[-2000:-1000])
        
        if previous_mean == 0:
            return False
        
        relative_change = abs(recent_mean - previous_mean) / previous_mean
        return relative_change < threshold
    
    def _calculate_method_agreement(self, method_estimates: Dict[str, float]) -> Dict[str, float]:
        """Calculate agreement metrics between methods."""
        estimates = list(method_estimates.values())
        mean_estimate = np.mean(estimates)
        std_estimate = np.std(estimates)
        
        # Calculate pairwise correlations and agreements
        agreement_metrics = {
            'coefficient_of_variation': std_estimate / mean_estimate if mean_estimate > 0 else float('inf'),
            'range': max(estimates) - min(estimates),
            'iqr': np.percentile(estimates, 75) - np.percentile(estimates, 25),
            'mean_estimate': mean_estimate,
            'std_estimate': std_estimate
        }
        
        return agreement_metrics
    
    def _identify_outlier_methods(self, method_estimates: Dict[str, float]) -> List[str]:
        """Identify outlier methods using statistical criteria."""
        estimates = np.array(list(method_estimates.values()))
        methods = list(method_estimates.keys())
        
        # Use IQR method to identify outliers
        q1 = np.percentile(estimates, 25)
        q3 = np.percentile(estimates, 75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        outliers = []
        for method, estimate in method_estimates.items():
            if estimate < lower_bound or estimate > upper_bound:
                outliers.append(method)
        
        return outliers
    
    def _calculate_weighted_consensus(self, method_estimates: Dict[str, float],
                                    reliability_scores: Dict[str, float],
                                    outlier_methods: List[str]) -> float:
        """Calculate reliability-weighted consensus estimate."""
        # Exclude outlier methods
        valid_methods = {k: v for k, v in method_estimates.items() if k not in outlier_methods}
        valid_reliabilities = {k: v for k, v in reliability_scores.items() if k not in outlier_methods}
        
        if not valid_methods:
            return np.mean(list(method_estimates.values()))
        
        # Calculate weighted average
        total_weight = 0
        weighted_sum = 0
        
        for method, estimate in valid_methods.items():
            weight = valid_reliabilities.get(method, 50) / 100  # Convert to 0-1 scale
            weighted_sum += estimate * weight
            total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else np.mean(list(valid_methods.values()))
    
    def _calculate_overall_confidence(self, method_agreement: Dict[str, float],
                                    reliability_scores: Dict[str, float],
                                    outlier_methods: List[str]) -> float:
        """Calculate overall confidence in the analysis."""
        # Start with base confidence
        confidence = 100.0
        
        # Reduce confidence based on method disagreement
        cv = method_agreement['coefficient_of_variation']
        if cv > 0.5:  # High disagreement
            confidence -= 30
        elif cv > 0.3:  # Moderate disagreement
            confidence -= 15
        elif cv > 0.1:  # Low disagreement
            confidence -= 5
        
        # Reduce confidence based on outlier methods
        outlier_penalty = len(outlier_methods) * 10
        confidence -= outlier_penalty
        
        # Adjust based on average reliability
        avg_reliability = np.mean(list(reliability_scores.values()))
        if avg_reliability < 60:
            confidence -= 20
        elif avg_reliability < 80:
            confidence -= 10
        
        return max(0, min(100, confidence))
    
    def _calculate_overall_validation_score(self, uncertainty_analysis: Dict,
                                          monte_carlo_results: MonteCarloResult,
                                          cross_validation_results: CrossValidationResult,
                                          known_case_results: List[KnownCaseResult]) -> float:
        """Calculate overall validation score combining all analyses."""
        score = 100.0
        
        # Uncertainty analysis component (30% weight)
        relative_uncertainty = uncertainty_analysis['relative_uncertainty']
        if relative_uncertainty > 0.5:
            score -= 20
        elif relative_uncertainty > 0.3:
            score -= 10
        elif relative_uncertainty > 0.1:
            score -= 5
        
        # Cross-validation component (40% weight)
        cross_val_confidence = cross_validation_results.overall_confidence
        score = score * 0.6 + cross_val_confidence * 0.4
        
        # Known case validation component (30% weight)
        if known_case_results:
            avg_error = np.mean([r.relative_error for r in known_case_results])
            within_ci_rate = np.mean([r.within_confidence for r in known_case_results])
            
            known_case_score = 100 - (avg_error * 100) + (within_ci_rate * 20)
            score = score * 0.7 + max(0, min(100, known_case_score)) * 0.3
        
        return max(0, min(100, score))
    
    def _generate_validation_recommendations(self, uncertainty_analysis: Dict,
                                           cross_validation_results: CrossValidationResult,
                                           known_case_results: List[KnownCaseResult]) -> List[str]:
        """Generate validation-based recommendations."""
        recommendations = []
        
        # Uncertainty-based recommendations
        if uncertainty_analysis['relative_uncertainty'] > 0.3:
            recommendations.append("High uncertainty detected - consider additional temperature measurements")
        
        # Cross-validation recommendations
        if cross_validation_results.overall_confidence < 70:
            recommendations.append("Low method agreement - interpret results with caution")
        
        if cross_validation_results.outlier_methods:
            recommendations.append(f"Outlier methods detected: {', '.join(cross_validation_results.outlier_methods)}")
        
        # Known case recommendations
        if known_case_results:
            high_error_cases = [r for r in known_case_results if r.relative_error > 0.2]
            if high_error_cases:
                recommendations.append("High error in known case validation - method may be less reliable")
        
        return recommendations
    
    def _load_known_cases(self) -> List[Dict]:
        """Load known validation cases from forensic entomology literature."""
        # Known cases from published studies for validation
        return [
            {
                'name': 'Grassberger & Reiter 2001 - L. sericata 20C',
                'species': ForensicSpecies.LUCILIA_SERICATA,
                'stage': DevelopmentStage.THIRD_INSTAR,
                'temperature_data': {'avg_temp': 20.0},
                'published_pmi_days': 6.5,
                'notes': 'Laboratory study, constant temperature'
            },
            {
                'name': 'Grassberger & Reiter 2001 - L. sericata 25C',
                'species': ForensicSpecies.LUCILIA_SERICATA,
                'stage': DevelopmentStage.THIRD_INSTAR,
                'temperature_data': {'avg_temp': 25.0},
                'published_pmi_days': 4.2,
                'notes': 'Laboratory study, constant temperature'
            },
            {
                'name': 'Donovan et al. 2006 - C. vicina 15C',
                'species': ForensicSpecies.CALLIPHORA_VICINA,
                'stage': DevelopmentStage.THIRD_INSTAR,
                'temperature_data': {'avg_temp': 15.0},
                'published_pmi_days': 8.5,
                'notes': 'Laboratory development study'
            },
            {
                'name': 'Anderson 2000 - P. regina 18C',
                'species': ForensicSpecies.PHORMIA_REGINA,
                'stage': DevelopmentStage.THIRD_INSTAR,
                'temperature_data': {'avg_temp': 18.0},
                'published_pmi_days': 7.1,
                'notes': 'Development rate study'
            },
            {
                'name': 'Byrd & Butler 1997 - C. macellaria 28C',
                'species': ForensicSpecies.COCHLIOMYIA_MACELLARIA,
                'stage': DevelopmentStage.THIRD_INSTAR,
                'temperature_data': {'avg_temp': 28.0},
                'published_pmi_days': 3.8,
                'notes': 'Warm climate development study'
            }
        ]


def create_enhanced_validation_report(species: ForensicSpecies,
                                    stage: DevelopmentStage,
                                    temperature_data: Dict,
                                    specimen_length: Optional[float] = None,
                                    include_monte_carlo: bool = True,
                                    verbose: bool = False) -> Dict:
    """
    Convenience function to generate a comprehensive enhanced validation report.
    
    Args:
        species: Forensic species
        stage: Development stage
        temperature_data: Temperature data
        specimen_length: Optional specimen length
        include_monte_carlo: Whether to include Monte Carlo simulation
        verbose: Whether to show detailed output
        
    Returns:
        Enhanced validation results dictionary
    """
    validator = EnhancedValidator()
    
    if include_monte_carlo:
        return validator.comprehensive_validation_report(
            species, stage, temperature_data, specimen_length
        )
    else:
        # Skip Monte Carlo for faster analysis
        uncertainty_analysis = validator.propagate_uncertainties(
            species, stage, temperature_data, specimen_length
        )
        
        cross_validation_results = validator.cross_validate_methods(
            species, stage, temperature_data, specimen_length
        )
        
        known_case_results = validator.validate_against_known_cases(
            species, stage, verbose
        )
        
        return {
            'uncertainty_analysis': uncertainty_analysis,
            'cross_validation_results': cross_validation_results,
            'known_case_results': known_case_results,
            'recommendations': validator._generate_validation_recommendations(
                uncertainty_analysis, cross_validation_results, known_case_results
            )
        }