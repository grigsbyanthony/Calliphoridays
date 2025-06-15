"""
Multiple specimen analysis for forensic entomology PMI estimation.
"""
import statistics
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import json

from .models import CalliphoridaeSpecies, DevelopmentStage, get_species_info
from .pmi_calculator import PMICalculator
from .validation import PMIValidator, DataQuality


@dataclass
class SpecimenData:
    """Data structure for a single specimen."""
    specimen_id: str
    species: CalliphoridaeSpecies
    stage: DevelopmentStage
    length_mm: Optional[float] = None
    collection_location: Optional[str] = None  # Specific location on body
    collection_method: Optional[str] = None
    preservation_method: Optional[str] = None
    notes: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            'specimen_id': self.specimen_id,
            'species': self.species.value,
            'stage': self.stage.value,
            'length_mm': self.length_mm,
            'collection_location': self.collection_location,
            'collection_method': self.collection_method,
            'preservation_method': self.preservation_method,
            'notes': self.notes
        }


@dataclass
class SpecimenResult:
    """PMI calculation result for a single specimen."""
    specimen: SpecimenData
    pmi_days: float
    pmi_hours: float
    confidence_low: float
    confidence_high: float
    quality_score: float
    data_quality: DataQuality
    calculation_details: Dict
    validation_warnings: List[str]


@dataclass
class MultiSpecimenResult:
    """Results from multiple specimen analysis."""
    specimen_results: List[SpecimenResult]
    consensus_pmi: Dict
    statistical_summary: Dict
    conflict_analysis: Dict
    recommendations: List[str]
    overall_quality: DataQuality


class ConflictType:
    """Types of conflicts that can occur between specimens."""
    SPECIES_DISAGREEMENT = "species_disagreement"
    STAGE_INCONSISTENCY = "stage_inconsistency"
    PMI_RANGE_CONFLICT = "pmi_range_conflict"
    QUALITY_DISPARITY = "quality_disparity"


class MultiSpecimenAnalyzer:
    """
    Analyzes multiple specimens from the same forensic scene.
    """
    
    def __init__(self):
        self.pmi_calculator = PMICalculator()
        self.validator = PMIValidator()
        
        # Thresholds for conflict detection
        self.pmi_conflict_threshold = 0.5  # Days difference to flag as conflict
        self.quality_disparity_threshold = 30  # Quality score difference
        
    def analyze_specimens(self, specimens: List[SpecimenData], 
                         temperature_data: Dict,
                         case_info: Dict) -> MultiSpecimenResult:
        """
        Analyze multiple specimens and provide consensus PMI estimate.
        
        Args:
            specimens: List of specimen data
            temperature_data: Temperature data for the scene
            case_info: Case metadata
            
        Returns:
            MultiSpecimenResult with comprehensive analysis
        """
        if not specimens:
            raise ValueError("At least one specimen must be provided")
        
        # Calculate PMI for each specimen
        specimen_results = []
        for specimen in specimens:
            result = self._analyze_single_specimen(specimen, temperature_data)
            specimen_results.append(result)
        
        # Perform statistical analysis
        statistical_summary = self._calculate_statistics(specimen_results)
        
        # Detect and analyze conflicts
        conflict_analysis = self._analyze_conflicts(specimen_results)
        
        # Generate consensus PMI estimate
        consensus_pmi = self._generate_consensus(specimen_results, conflict_analysis)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            specimen_results, conflict_analysis, statistical_summary
        )
        
        # Determine overall quality
        overall_quality = self._assess_overall_quality(specimen_results, conflict_analysis)
        
        return MultiSpecimenResult(
            specimen_results=specimen_results,
            consensus_pmi=consensus_pmi,
            statistical_summary=statistical_summary,
            conflict_analysis=conflict_analysis,
            recommendations=recommendations,
            overall_quality=overall_quality
        )
    
    def _analyze_single_specimen(self, specimen: SpecimenData, 
                                temperature_data: Dict) -> SpecimenResult:
        """Analyze a single specimen."""
        # Validate inputs
        validation_result = self.validator.validate_inputs(
            specimen.species, specimen.stage, 
            temperature_data.get('location', 'Unknown'),
            temperature_data.get('date', '2024-01-01'),
            None,  # discovery_time
            specimen.length_mm,
            temperature_data.get('avg_temp')
        )
        
        # Calculate PMI
        pmi_result = self.pmi_calculator.calculate_pmi(
            species=specimen.species,
            stage=specimen.stage,
            temperature_data=temperature_data,
            specimen_length=specimen.length_mm
        )
        
        # Validate calculation results
        validation_result = self.validator.validate_calculation_results(
            pmi_result, temperature_data, specimen.species, specimen.stage
        )
        
        return SpecimenResult(
            specimen=specimen,
            pmi_days=pmi_result['pmi_days'],
            pmi_hours=pmi_result['pmi_hours'],
            confidence_low=pmi_result['confidence_low'],
            confidence_high=pmi_result['confidence_high'],
            quality_score=validation_result.quality_score,
            data_quality=validation_result.data_quality,
            calculation_details=pmi_result,
            validation_warnings=validation_result.warnings
        )
    
    def _calculate_statistics(self, results: List[SpecimenResult]) -> Dict:
        """Calculate statistical summary of all PMI estimates."""
        pmi_values = [r.pmi_days for r in results]
        quality_scores = [r.quality_score for r in results]
        
        stats = {
            'specimen_count': len(results),
            'pmi_mean': statistics.mean(pmi_values),
            'pmi_median': statistics.median(pmi_values),
            'pmi_std_dev': statistics.stdev(pmi_values) if len(pmi_values) > 1 else 0,
            'pmi_min': min(pmi_values),
            'pmi_max': max(pmi_values),
            'pmi_range': max(pmi_values) - min(pmi_values),
            'quality_mean': statistics.mean(quality_scores),
            'quality_min': min(quality_scores),
            'quality_max': max(quality_scores),
            'species_diversity': len(set(r.specimen.species for r in results)),
            'stage_diversity': len(set(r.specimen.stage for r in results))
        }
        
        # Calculate coefficient of variation
        if stats['pmi_mean'] > 0:
            stats['pmi_cv'] = (stats['pmi_std_dev'] / stats['pmi_mean']) * 100
        else:
            stats['pmi_cv'] = 0
        
        return stats
    
    def _analyze_conflicts(self, results: List[SpecimenResult]) -> Dict:
        """Detect and analyze conflicts between specimens."""
        conflicts = {
            'has_conflicts': False,
            'conflict_types': [],
            'conflict_details': [],
            'severity': 'none'  # none, minor, moderate, severe
        }
        
        if len(results) < 2:
            return conflicts
        
        pmi_values = [r.pmi_days for r in results]
        quality_scores = [r.quality_score for r in results]
        
        # PMI range conflicts
        pmi_range = max(pmi_values) - min(pmi_values)
        if pmi_range > self.pmi_conflict_threshold:
            conflicts['has_conflicts'] = True
            conflicts['conflict_types'].append(ConflictType.PMI_RANGE_CONFLICT)
            conflicts['conflict_details'].append({
                'type': ConflictType.PMI_RANGE_CONFLICT,
                'description': f"PMI estimates vary by {pmi_range:.1f} days",
                'severity': self._assess_pmi_conflict_severity(pmi_range, statistics.mean(pmi_values))
            })
        
        # Quality disparities
        quality_range = max(quality_scores) - min(quality_scores)
        if quality_range > self.quality_disparity_threshold:
            conflicts['has_conflicts'] = True
            conflicts['conflict_types'].append(ConflictType.QUALITY_DISPARITY)
            conflicts['conflict_details'].append({
                'type': ConflictType.QUALITY_DISPARITY,
                'description': f"Quality scores vary by {quality_range:.0f} points",
                'severity': 'moderate' if quality_range > 50 else 'minor'
            })
        
        # Species disagreements
        species_set = set(r.specimen.species for r in results)
        if len(species_set) > 1:
            conflicts['has_conflicts'] = True
            conflicts['conflict_types'].append(ConflictType.SPECIES_DISAGREEMENT)
            conflicts['conflict_details'].append({
                'type': ConflictType.SPECIES_DISAGREEMENT,
                'description': f"Multiple species present: {', '.join(s.value for s in species_set)}",
                'severity': 'moderate'
            })
        
        # Stage inconsistencies (for same species)
        for species in species_set:
            species_results = [r for r in results if r.specimen.species == species]
            if len(species_results) > 1:
                stages = set(r.specimen.stage for r in species_results)
                if len(stages) > 1:
                    # Check if stages are developmentally consistent
                    if not self._stages_are_consistent(stages):
                        conflicts['has_conflicts'] = True
                        conflicts['conflict_types'].append(ConflictType.STAGE_INCONSISTENCY)
                        conflicts['conflict_details'].append({
                            'type': ConflictType.STAGE_INCONSISTENCY,
                            'description': f"Inconsistent stages for {species.value}: {', '.join(s.value for s in stages)}",
                            'severity': 'severe'
                        })
        
        # Determine overall severity
        if conflicts['has_conflicts']:
            severities = [detail['severity'] for detail in conflicts['conflict_details']]
            if 'severe' in severities:
                conflicts['severity'] = 'severe'
            elif 'moderate' in severities:
                conflicts['severity'] = 'moderate'
            else:
                conflicts['severity'] = 'minor'
        
        return conflicts
    
    def _assess_pmi_conflict_severity(self, pmi_range: float, mean_pmi: float) -> str:
        """Assess severity of PMI range conflicts."""
        # Calculate relative variation
        relative_variation = (pmi_range / mean_pmi) * 100 if mean_pmi > 0 else 0
        
        if relative_variation > 50:
            return 'severe'
        elif relative_variation > 25:
            return 'moderate'
        else:
            return 'minor'
    
    def _stages_are_consistent(self, stages: set) -> bool:
        """Check if development stages are consistent (sequential development)."""
        # Define stage order
        stage_order = [
            DevelopmentStage.FIRST_INSTAR,
            DevelopmentStage.SECOND_INSTAR,
            DevelopmentStage.THIRD_INSTAR,
            DevelopmentStage.PUPA
        ]
        
        stage_indices = [stage_order.index(stage) for stage in stages if stage in stage_order]
        
        # Stages are consistent if they're consecutive or span a reasonable range
        if len(stage_indices) <= 1:
            return True
        
        stage_range = max(stage_indices) - min(stage_indices)
        return stage_range <= 2  # Allow up to 2 stages apart
    
    def _generate_consensus(self, results: List[SpecimenResult], 
                           conflicts: Dict) -> Dict:
        """Generate consensus PMI estimate from multiple specimens."""
        if len(results) == 1:
            result = results[0]
            return {
                'method': 'single_specimen',
                'pmi_days': result.pmi_days,
                'pmi_hours': result.pmi_hours,
                'confidence_low': result.confidence_low,
                'confidence_high': result.confidence_high,
                'basis': f"Single specimen: {result.specimen.species.value} {result.specimen.stage.value}"
            }
        
        pmi_values = [r.pmi_days for r in results]
        quality_scores = [r.quality_score for r in results]
        
        # Choose consensus method based on conflict severity
        if conflicts['severity'] in ['severe', 'moderate']:
            # Use quality-weighted average for conflicting data
            consensus = self._quality_weighted_consensus(results)
        else:
            # Use simple statistical measures for consistent data
            consensus = self._statistical_consensus(results)
        
        return consensus
    
    def _quality_weighted_consensus(self, results: List[SpecimenResult]) -> Dict:
        """Generate consensus using quality-weighted average."""
        # Calculate weights based on quality scores
        weights = [r.quality_score for r in results]
        total_weight = sum(weights)
        
        if total_weight == 0:
            # Fallback to equal weights
            weights = [1.0] * len(results)
            total_weight = len(results)
        
        # Calculate weighted averages
        weighted_pmi = sum(r.pmi_days * w for r, w in zip(results, weights)) / total_weight
        weighted_conf_low = sum(r.confidence_low * w for r, w in zip(results, weights)) / total_weight
        weighted_conf_high = sum(r.confidence_high * w for r, w in zip(results, weights)) / total_weight
        
        return {
            'method': 'quality_weighted_average',
            'pmi_days': weighted_pmi,
            'pmi_hours': weighted_pmi * 24,
            'confidence_low': weighted_conf_low,
            'confidence_high': weighted_conf_high,
            'basis': f"Quality-weighted average of {len(results)} specimens"
        }
    
    def _statistical_consensus(self, results: List[SpecimenResult]) -> Dict:
        """Generate consensus using statistical measures."""
        pmi_values = [r.pmi_days for r in results]
        conf_lows = [r.confidence_low for r in results]
        conf_highs = [r.confidence_high for r in results]
        
        # Use median for robust central tendency
        median_pmi = statistics.median(pmi_values)
        
        # Expand confidence interval to encompass range
        consensus_low = min(conf_lows)
        consensus_high = max(conf_highs)
        
        return {
            'method': 'statistical_consensus',
            'pmi_days': median_pmi,
            'pmi_hours': median_pmi * 24,
            'confidence_low': consensus_low,
            'confidence_high': consensus_high,
            'basis': f"Statistical consensus of {len(results)} specimens"
        }
    
    def _generate_recommendations(self, results: List[SpecimenResult],
                                conflicts: Dict, stats: Dict) -> List[str]:
        """Generate recommendations based on analysis."""
        recommendations = []
        
        # Recommendations based on conflicts
        if conflicts['has_conflicts']:
            if ConflictType.SPECIES_DISAGREEMENT in conflicts['conflict_types']:
                recommendations.append(
                    "Multiple species present - verify species identifications with morphological keys"
                )
                recommendations.append(
                    "Consider separate PMI estimates for each species"
                )
            
            if ConflictType.STAGE_INCONSISTENCY in conflicts['conflict_types']:
                recommendations.append(
                    "Inconsistent development stages suggest complex taphonomic history"
                )
                recommendations.append(
                    "Investigate environmental factors that may affect development rates"
                )
            
            if ConflictType.PMI_RANGE_CONFLICT in conflicts['conflict_types']:
                recommendations.append(
                    f"Large PMI range ({stats['pmi_range']:.1f} days) - prioritize highest quality specimens"
                )
                recommendations.append(
                    "Consider microenvironmental differences within the scene"
                )
        
        # Recommendations based on statistics
        if stats['specimen_count'] < 3:
            recommendations.append(
                "Limited sample size - collect additional specimens if possible"
            )
        
        if stats['pmi_cv'] > 30:  # High coefficient of variation
            recommendations.append(
                f"High variability in PMI estimates (CV: {stats['pmi_cv']:.1f}%) - exercise caution in interpretation"
            )
        
        # Quality-based recommendations
        low_quality_count = sum(1 for r in results if r.quality_score < 70)
        if low_quality_count > 0:
            recommendations.append(
                f"{low_quality_count} specimen(s) have low quality scores - review validation warnings"
            )
        
        # Species diversity recommendations
        if stats['species_diversity'] > 2:
            recommendations.append(
                "High species diversity may indicate extended PMI or multiple colonization events"
            )
        
        return recommendations
    
    def _assess_overall_quality(self, results: List[SpecimenResult], 
                               conflicts: Dict) -> DataQuality:
        """Assess overall quality of the multi-specimen analysis."""
        # Start with average quality score
        avg_quality = statistics.mean(r.quality_score for r in results)
        
        # Adjust based on conflicts
        if conflicts['severity'] == 'severe':
            avg_quality -= 30
        elif conflicts['severity'] == 'moderate':
            avg_quality -= 15
        elif conflicts['severity'] == 'minor':
            avg_quality -= 5
        
        # Adjust based on sample size
        if len(results) >= 3:
            avg_quality += 10  # Bonus for good sample size
        
        # Convert to quality enum
        if avg_quality >= 90:
            return DataQuality.EXCELLENT
        elif avg_quality >= 70:
            return DataQuality.GOOD
        elif avg_quality >= 50:
            return DataQuality.FAIR
        elif avg_quality >= 30:
            return DataQuality.POOR
        else:
            return DataQuality.UNRELIABLE
    
    def create_specimen_from_dict(self, data: Dict) -> SpecimenData:
        """Create SpecimenData from dictionary."""
        return SpecimenData(
            specimen_id=data['specimen_id'],
            species=CalliphoridaeSpecies(data['species']),
            stage=DevelopmentStage(data['stage']),
            length_mm=data.get('length_mm'),
            collection_location=data.get('collection_location'),
            collection_method=data.get('collection_method'),
            preservation_method=data.get('preservation_method'),
            notes=data.get('notes')
        )
    
    def export_multi_specimen_results(self, results: MultiSpecimenResult, 
                                     output_path: str) -> str:
        """Export multi-specimen results to JSON file."""
        # Convert results to serializable format
        export_data = {
            'analysis_timestamp': datetime.now().isoformat(),
            'specimen_count': len(results.specimen_results),
            'specimens': [
                {
                    'specimen_data': result.specimen.to_dict(),
                    'pmi_days': result.pmi_days,
                    'pmi_hours': result.pmi_hours,
                    'confidence_low': result.confidence_low,
                    'confidence_high': result.confidence_high,
                    'quality_score': result.quality_score,
                    'data_quality': result.data_quality.value,
                    'validation_warnings': result.validation_warnings
                }
                for result in results.specimen_results
            ],
            'consensus_pmi': results.consensus_pmi,
            'statistical_summary': results.statistical_summary,
            'conflict_analysis': results.conflict_analysis,
            'recommendations': results.recommendations,
            'overall_quality': results.overall_quality.value
        }
        
        if not output_path.endswith('.json'):
            output_path += '.json'
        
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        return output_path