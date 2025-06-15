import click
import sys
from typing import Optional, Dict

from .models import DevelopmentStage, ForensicSpecies, CalliphoridaeSpecies
from .pmi_calculator import PMICalculator
from .weather import WeatherService
from .visualization import TerminalVisualizer
from .export import DataExporter
from .validation import PMIValidator
from .alternative_methods import AlternativePMICalculator, PMIMethod


@click.command()
@click.option('--species', '-s', required=True, 
              type=click.Choice([
                  # Calliphoridae (Blow flies)
                  'chrysomya_rufifacies', 'lucilia_sericata', 'calliphora_vicina', 
                  'cochliomyia_macellaria', 'phormia_regina', 'chrysomya_megacephala',
                  'lucilia_cuprina', 'calliphora_vomitoria', 'protophormia_terraenovae',
                  # Sarcophagidae (Flesh flies)
                  'sarcophaga_bullata', 'sarcophaga_crassipalpis', 
                  'sarcophaga_haemorrhoidalis', 'boettcherisca_peregrina'
              ]),
              help='Forensically important species found on the cadaver (9 Calliphoridae + 4 Sarcophagidae)')
@click.option('--stage', '-t', required=True,
              type=click.Choice(['1st_instar', '2nd_instar', '3rd_instar', 'pupa']),
              help='Development stage of the specimen')
@click.option('--location', '-l', required=True,
              help='Location where body was found (city, state/country)')
@click.option('--discovery-date', '-d', required=True,
              help='Date body was discovered (YYYY-MM-DD)')
@click.option('--discovery-time', '--time', type=str,
              help='Time body was discovered (HH:MM, 24-hour format, optional)')
@click.option('--specimen-length', '-m', type=float,
              help='Length of specimen in mm (optional, improves accuracy)')
@click.option('--ambient-temp', '-a', type=float,
              help='Ambient temperature at discovery (°C) - overrides weather data')
@click.option('--verbose', '-v', is_flag=True,
              help='Show detailed calculation information')
@click.option('--plot', '-p', is_flag=True,
              help='Show visualization plot of PMI estimate')
@click.option('--no-banner', is_flag=True,
              help='Suppress ASCII banner display')
@click.option('--export', type=click.Choice(['json', 'csv', 'txt', 'pdf']),
              help='Export results to specified format (pdf generates professional court report)')
@click.option('--output', '-o', type=str,
              help='Output file path for export (without extension)')
@click.option('--case-id', type=str,
              help='Case identifier for documentation')
@click.option('--investigator', type=str,
              help='Investigator name for case documentation')
@click.option('--validate', is_flag=True,
              help='Show detailed validation report and data quality assessment')
@click.option('--enhanced-validation', is_flag=True,
              help='Perform enhanced validation with uncertainty analysis and cross-validation')
@click.option('--monte-carlo', is_flag=True,
              help='Include Monte Carlo simulation for confidence intervals (slower)')
@click.option('--known-cases', is_flag=True,
              help='Validate against known cases from literature')
@click.option('--methods', is_flag=True,
              help='Calculate PMI using multiple methods and show comparison')
@click.option('--method-list', type=str,
              help='Comma-separated list of specific methods to use (e.g., add_standard,adh_method)')
def main(species: str, stage: str, location: str, discovery_date: str,
         discovery_time: Optional[str], specimen_length: Optional[float], 
         ambient_temp: Optional[float], verbose: bool, plot: bool, no_banner: bool,
         export: Optional[str], output: Optional[str], case_id: Optional[str], 
         investigator: Optional[str], validate: bool, enhanced_validation: bool,
         monte_carlo: bool, known_cases: bool, methods: bool, method_list: Optional[str]):
    """
    Estimate postmortem interval using blow fly evidence.
    
    This tool uses entomological evidence from Calliphoridae (blow flies)
    to estimate the postmortem interval of a cadaver.
    """
    try:
        # Display banner unless suppressed
        if not no_banner:
            banner = r"""
┏┓┏┓┓ ┓ ┳┓┏┏┓┓┏┏┓┳┓┳┳┓┏┓┓┏┏┓
┃ ┣┫┃ ┃ ┃┣┫┃┃┣┫┃┃┣┫┃┃┃┣┫┗┫┗┓
┗┛┛┗┗┛┗┛┻┛┗┣┛┛┗┗┛┛┗┻┻┛┛┗┗┛┗┛
                            
            """
            click.echo(banner)
            click.echo("Forensic Entomology PMI Estimation Tool")
            click.echo("Using Calliphoridae & Sarcophagidae Evidence and Temperature Data")
            click.echo("=" * 70)
        
        # Parse inputs
        forensic_species = ForensicSpecies(species)
        development_stage = DevelopmentStage(stage)
        
        # Initialize validator and validate inputs
        validator = PMIValidator()
        validation_result = validator.validate_inputs(
            forensic_species, development_stage, location, discovery_date,
            discovery_time, specimen_length, ambient_temp
        )
        
        # Initialize services
        weather_service = WeatherService()
        pmi_calculator = PMICalculator()
        visualizer = TerminalVisualizer()
        exporter = DataExporter()
        
        # Get temperature data
        if ambient_temp is not None:
            temperature_data = {'avg_temp': ambient_temp}
            if verbose:
                click.echo(f"Using provided ambient temperature: {ambient_temp}°C")
        else:
            if verbose:
                time_info = f" at {discovery_time}" if discovery_time else ""
                click.echo(f"Fetching weather data for {location}{time_info}...")
            temperature_data = weather_service.get_temperature_data(location, discovery_date, discovery_time)
        
        # Calculate PMI
        if verbose:
            click.echo("Calculating postmortem interval...")
            
        pmi_estimate = pmi_calculator.calculate_pmi(
            species=forensic_species,
            stage=development_stage,
            temperature_data=temperature_data,
            specimen_length=specimen_length,
            verbose=verbose
        )
        
        # Validate calculation results
        validation_result = validator.validate_calculation_results(
            pmi_estimate, temperature_data, forensic_species, development_stage
        )
        
        # Calculate alternative methods if requested
        alternative_results = None
        if methods or method_list:
            try:
                alt_calculator = AlternativePMICalculator()
                
                # Parse method list if provided
                selected_methods = None
                if method_list:
                    method_names = [name.strip() for name in method_list.split(',')]
                    selected_methods = []
                    for name in method_names:
                        try:
                            method = PMIMethod(name)
                            selected_methods.append(method)
                        except ValueError:
                            click.echo(f"Warning: Unknown method '{name}' ignored", err=True)
                    
                    if not selected_methods:
                        click.echo("Error: No valid methods specified", err=True)
                        selected_methods = None
                
                if verbose:
                    click.echo("Calculating alternative PMI methods...")
                
                alternative_results = alt_calculator.calculate_all_methods(
                    forensic_species, development_stage, temperature_data,
                    specimen_length, selected_methods
                )
                
            except Exception as e:
                click.echo(f"Warning: Alternative methods calculation failed: {str(e)}", err=True)
        
        # Output results
        click.echo(f"\n{'='*50}")
        click.echo(f"POSTMORTEM INTERVAL ESTIMATE")
        click.echo(f"{'='*50}")
        click.echo(f"Species: {species.replace('_', ' ').title()}")
        click.echo(f"Development Stage: {stage.replace('_', ' ').title()}")
        click.echo(f"Location: {location}")
        discovery_datetime = f"{discovery_date}" + (f" {discovery_time}" if discovery_time else "")
        click.echo(f"Discovery Date: {discovery_datetime}")
        click.echo(f"Estimated PMI: {pmi_estimate['pmi_days']:.1f} days ({pmi_estimate['pmi_hours']:.1f} hours)")
        click.echo(f"Confidence Interval: {pmi_estimate['confidence_low']:.1f} - {pmi_estimate['confidence_high']:.1f} days")
        click.echo(f"Temperature Used: {temperature_data['avg_temp']:.1f}°C")
        
        # Show data quality assessment
        click.echo(f"\nData Quality: {validation_result.data_quality.value.upper()} ({validation_result.quality_score:.0f}/100)")
        
        # Show validation warnings if any
        if validation_result.warnings:
            click.echo(f"\nValidation Alerts:")
            for warning in validation_result.warnings[:3]:  # Show max 3 warnings
                click.echo(f"  {warning}")
            if len(validation_result.warnings) > 3:
                click.echo(f"  ... and {len(validation_result.warnings) - 3} more (use --validate for full report)")
        
        if verbose:
            click.echo(f"\nDetailed Calculations:")
            click.echo(f"Accumulated Degree Days: {pmi_estimate['accumulated_dd']:.1f} ADD")
            click.echo(f"Base Temperature: {pmi_estimate['base_temp']:.1f}°C")
            click.echo(f"Development Threshold: {pmi_estimate['dev_threshold']:.1f} ADD")
        
        # Show visualization if requested
        if plot:
            click.echo("\n" + visualizer.create_pmi_with_temperature_timeline(pmi_estimate, temperature_data))
        
        # Show full validation report if requested
        if validate:
            click.echo("\n" + validator.generate_validation_report())
        
        # Perform enhanced validation if requested
        enhanced_results = None
        if enhanced_validation or monte_carlo or known_cases:
            try:
                from .enhanced_validation import create_enhanced_validation_report
                
                click.echo("\nPerforming enhanced validation analysis...")
                
                enhanced_results = create_enhanced_validation_report(
                    species=forensic_species,
                    stage=development_stage,
                    temperature_data=temperature_data,
                    specimen_length=specimen_length,
                    include_monte_carlo=monte_carlo,
                    verbose=verbose
                )
                
                display_enhanced_validation_results(enhanced_results, monte_carlo, known_cases)
                
            except ImportError as e:
                click.echo(f"Enhanced validation requires additional dependencies: {str(e)}", err=True)
                click.echo("Install with: pip install numpy", err=True)
            except Exception as e:
                click.echo(f"Enhanced validation failed: {str(e)}", err=True)
        
        # Show alternative methods results if calculated
        if alternative_results:
            display_alternative_methods_results(alternative_results, verbose)
        
        click.echo(f"\nWARNING: This is an estimate based on available data.")
        click.echo(f"Results should be interpreted by qualified forensic entomologists.")
        
        # Export data if requested
        if export:
            try:
                # Prepare case information
                case_info = {
                    'case_id': case_id or exporter.generate_case_id(location, discovery_date),
                    'investigator': investigator or 'Unknown',
                    'location': location,
                    'discovery_date': discovery_date,
                    'discovery_time': discovery_time,
                    'specimen_length': specimen_length,
                    'collection_method': 'Not specified',
                    'preservation_method': 'Not specified'
                }
                
                # Generate output path if not provided
                if not output:
                    output = f"PMI_case_{case_info['case_id']}"
                
                if export == 'pdf':
                    # Generate professional PDF report
                    try:
                        from .report_generator import create_forensic_report
                        
                        pdf_path = create_forensic_report(
                            pmi_estimate=pmi_estimate,
                            validation_result=validation_result,
                            case_info=case_info,
                            temperature_data=temperature_data,
                            species=forensic_species,
                            stage=development_stage,
                            alternative_results=alternative_results,
                            output_path=output + '.pdf'
                        )
                        
                        click.echo(f"\nProfessional PDF report generated: {pdf_path}")
                        
                    except ImportError as e:
                        click.echo(f"PDF generation requires additional dependencies: {str(e)}", err=True)
                        click.echo("Install with: pip install reportlab matplotlib pillow", err=True)
                    except Exception as pdf_error:
                        click.echo(f"PDF generation failed: {str(pdf_error)}", err=True)
                else:
                    # Export using existing data exporter
                    exported_file = exporter.export_case_data(
                        pmi_estimate, temperature_data, case_info, output, export
                    )
                    
                    click.echo(f"\nData exported to: {exported_file}")
                
            except Exception as export_error:
                click.echo(f"Export failed: {str(export_error)}", err=True)
        
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


def display_alternative_methods_results(results, verbose: bool = False):
    """Display results from alternative PMI methods."""
    click.echo(f"\n{'='*60}")
    click.echo(f"ALTERNATIVE PMI METHODS COMPARISON")
    click.echo(f"{'='*60}")
    
    # Individual method results
    click.echo(f"\nINDIVIDUAL METHOD RESULTS:")
    click.echo("-" * 40)
    
    for i, estimate in enumerate(results.estimates, 1):
        method_name = estimate.method.value.replace('_', ' ').title()
        click.echo(f"\n{i}. {method_name}")
        click.echo(f"   PMI Estimate: {estimate.pmi_days:.1f} days ({estimate.pmi_hours:.1f} hours)")
        click.echo(f"   Confidence: {estimate.confidence_low:.1f} - {estimate.confidence_high:.1f} days")
        click.echo(f"   Reliability: {estimate.reliability_score:.0f}/100")
        
        if verbose:
            click.echo(f"   Key Assumptions:")
            for assumption in estimate.assumptions[:2]:  # Show first 2 assumptions
                click.echo(f"     • {assumption}")
            if len(estimate.assumptions) > 2:
                click.echo(f"     ... and {len(estimate.assumptions) - 2} more")
    
    # Method agreement analysis
    agreement = results.method_agreement
    click.echo(f"\nMETHOD AGREEMENT ANALYSIS:")
    click.echo("-" * 40)
    click.echo(f"Agreement Level: {agreement['agreement_level'].upper()}")
    click.echo(f"Coefficient of Variation: {agreement['coefficient_of_variation']:.1f}%")
    click.echo(f"PMI Range: {agreement['min_pmi']:.1f} - {agreement['max_pmi']:.1f} days")
    click.echo(f"Mean PMI: {agreement['mean_pmi']:.1f} days")
    click.echo(f"Standard Deviation: {agreement['std_deviation']:.1f} days")
    
    # Consensus estimate
    consensus = results.consensus_estimate
    click.echo(f"\nCONSENSUS ESTIMATE:")
    click.echo("-" * 40)
    click.echo(f"Method: {consensus['method'].replace('_', ' ').title()}")
    click.echo(f"Consensus PMI: {consensus['pmi_days']:.1f} days ({consensus['pmi_hours']:.1f} hours)")
    click.echo(f"Combined Confidence: {consensus['confidence_low']:.1f} - {consensus['confidence_high']:.1f} days")
    
    if 'methods_used' in consensus:
        methods_list = [m.replace('_', ' ').title() for m in consensus['methods_used']]
        click.echo(f"Based on: {', '.join(methods_list)}")
    
    # Reliability assessment
    reliability = results.reliability_assessment
    click.echo(f"\nRELIABILITY ASSESSMENT:")
    click.echo("-" * 40)
    click.echo(f"Overall Reliability: {reliability['overall_reliability']:.0f}/100")
    click.echo(f"Method Count: {reliability['method_count']} methods")
    
    if verbose:
        for factor in reliability['reliability_factors']:
            click.echo(f"  • {factor}")
    
    # Visual comparison
    click.echo(f"\nMETHOD COMPARISON CHART:")
    click.echo("-" * 40)
    create_methods_comparison_chart(results.estimates)
    
    # Recommendations
    if results.recommendations:
        click.echo(f"\nMETHOD RECOMMENDATIONS:")
        click.echo("-" * 40)
        for i, rec in enumerate(results.recommendations, 1):
            click.echo(f"{i}. {rec}")


def create_methods_comparison_chart(estimates):
    """Create a visual comparison chart for different methods."""
    if not estimates:
        return
    
    max_pmi = max(est.pmi_days for est in estimates)
    
    for estimate in estimates:
        method_name = estimate.method.value.replace('_', ' ').title()
        pmi = estimate.pmi_days
        reliability = estimate.reliability_score
        
        # Create proportional bar
        bar_length = int((pmi / max_pmi) * 30) if max_pmi > 0 else 1
        bar = "█" * bar_length
        
        # Reliability indicator
        if reliability >= 85:
            rel_icon = "🟢"
        elif reliability >= 70:
            rel_icon = "🟡"
        elif reliability >= 55:
            rel_icon = "🟠"
        else:
            rel_icon = "🔴"
        
        # Truncate method name for display
        display_name = method_name[:15].ljust(15)
        
        click.echo(f"{display_name} {rel_icon} {bar} {pmi:.1f}d")


def display_enhanced_validation_results(results: Dict, include_monte_carlo: bool, include_known_cases: bool):
    """Display results from enhanced validation analysis."""
    click.echo(f"\n{'='*70}")
    click.echo(f"ENHANCED VALIDATION ANALYSIS")
    click.echo(f"{'='*70}")
    
    # Uncertainty Analysis
    if 'uncertainty_analysis' in results:
        ua = results['uncertainty_analysis']
        click.echo(f"\nUNCERTAINTY PROPAGATION ANALYSIS:")
        click.echo("-" * 40)
        click.echo(f"Base PMI Estimate: {ua['base_pmi']:.1f} days")
        click.echo(f"Total Uncertainty: ±{ua['total_uncertainty']:.1f} days")
        click.echo(f"Relative Uncertainty: {ua['relative_uncertainty']:.1%}")
        click.echo(f"95% Confidence (Propagated): {ua['propagated_confidence_95'][0]:.1f} - {ua['propagated_confidence_95'][1]:.1f} days")
        
        click.echo(f"\nUncertainty Components:")
        for component in ua['uncertainty_components']:
            click.echo(f"  • {component.description}: ±{component.value:.1f} days")
    
    # Monte Carlo Results
    if include_monte_carlo and 'monte_carlo_results' in results:
        mc = results['monte_carlo_results']
        click.echo(f"\nMONTE CARLO SIMULATION RESULTS:")
        click.echo("-" * 40)
        click.echo(f"Simulated Mean PMI: {mc.mean_pmi:.1f} days")
        click.echo(f"Standard Deviation: {mc.std_pmi:.1f} days")
        click.echo(f"Iterations Used: {mc.iterations_used:,}")
        click.echo(f"Convergence Achieved: {'Yes' if mc.convergence_achieved else 'No'}")
        
        click.echo(f"\nSimulated Confidence Intervals:")
        for level, (low, high) in mc.confidence_intervals.items():
            click.echo(f"  {level}%: {low:.1f} - {high:.1f} days")
    
    # Cross-Validation Results
    if 'cross_validation_results' in results:
        cv = results['cross_validation_results']
        click.echo(f"\nCROSS-VALIDATION ANALYSIS:")
        click.echo("-" * 40)
        click.echo(f"Consensus Estimate: {cv.consensus_estimate:.1f} days")
        click.echo(f"Overall Confidence: {cv.overall_confidence:.0f}/100")
        
        if cv.outlier_methods:
            click.echo(f"Outlier Methods: {', '.join(cv.outlier_methods)}")
        
        click.echo(f"\nMethod Agreement Metrics:")
        for metric, value in cv.method_agreement.items():
            if isinstance(value, float):
                if 'coefficient' in metric:
                    click.echo(f"  {metric.replace('_', ' ').title()}: {value:.1%}")
                else:
                    click.echo(f"  {metric.replace('_', ' ').title()}: {value:.1f}")
    
    # Known Case Validation
    if include_known_cases and 'known_case_results' in results:
        kc = results['known_case_results']
        if kc:
            click.echo(f"\nKNOWN CASE VALIDATION:")
            click.echo("-" * 40)
            click.echo(f"Cases Evaluated: {len(kc)}")
            
            for case in kc[:3]:  # Show first 3 cases
                status = "✓" if case.within_confidence else "✗"
                click.echo(f"  {status} {case.case_name}")
                click.echo(f"    Published: {case.published_pmi:.1f}d, Calculated: {case.calculated_pmi:.1f}d")
                click.echo(f"    Error: {case.relative_error:.1%}")
            
            if len(kc) > 3:
                click.echo(f"    ... and {len(kc) - 3} more cases")
            
            avg_error = sum(case.relative_error for case in kc) / len(kc)
            within_ci_rate = sum(case.within_confidence for case in kc) / len(kc)
            click.echo(f"\nValidation Summary:")
            click.echo(f"  Average Error: {avg_error:.1%}")
            click.echo(f"  Within Confidence Interval: {within_ci_rate:.1%}")
        else:
            click.echo(f"\nKNOWN CASE VALIDATION:")
            click.echo("-" * 40)
            click.echo("No relevant known cases found for this species/stage combination")
    
    # Overall Validation Score
    if 'overall_validation_score' in results:
        score = results['overall_validation_score']
        click.echo(f"\nOVERALL VALIDATION SCORE: {score:.0f}/100")
        
        if score >= 90:
            rating = "EXCELLENT"
        elif score >= 80:
            rating = "VERY GOOD"
        elif score >= 70:
            rating = "GOOD"
        elif score >= 60:
            rating = "FAIR"
        else:
            rating = "POOR"
        
        click.echo(f"Validation Rating: {rating}")
    
    # Recommendations
    if 'recommendations' in results and results['recommendations']:
        click.echo(f"\nVALIDATION RECOMMENDATIONS:")
        click.echo("-" * 40)
        for i, rec in enumerate(results['recommendations'], 1):
            click.echo(f"{i}. {rec}")


if __name__ == '__main__':
    main()