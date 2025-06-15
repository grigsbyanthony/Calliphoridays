"""
CLI for multiple specimen analysis.
"""
import click
import json
import sys
from pathlib import Path
from typing import List, Dict

from .multi_specimen import MultiSpecimenAnalyzer, SpecimenData
from .models import CalliphoridaeSpecies, DevelopmentStage
from .visualization import TerminalVisualizer


@click.command()
@click.option('--specimens-file', '-f', required=True, type=click.Path(exists=True),
              help='JSON file containing specimen data')
@click.option('--location', '-l', required=True,
              help='Location where specimens were found')
@click.option('--discovery-date', '-d', required=True,
              help='Date specimens were discovered (YYYY-MM-DD)')
@click.option('--discovery-time', '--time', type=str,
              help='Time specimens were discovered (HH:MM, 24-hour format)')
@click.option('--ambient-temp', '-a', type=float,
              help='Ambient temperature at discovery (°C)')
@click.option('--case-id', type=str,
              help='Case identifier for documentation')
@click.option('--investigator', type=str,
              help='Investigator name')
@click.option('--export', '-e', type=str,
              help='Export results to file (JSON format)')
@click.option('--no-banner', is_flag=True,
              help='Suppress ASCII banner display')
@click.option('--verbose', '-v', is_flag=True,
              help='Show detailed information')
def multi_analyze(specimens_file: str, location: str, discovery_date: str,
                 discovery_time: str, ambient_temp: float, case_id: str,
                 investigator: str, export: str, no_banner: bool, verbose: bool):
    """
    Analyze multiple specimens from the same forensic scene.
    
    Requires a JSON file with specimen data in the following format:
    
    {
      "specimens": [
        {
          "specimen_id": "SPEC001",
          "species": "lucilia_sericata",
          "stage": "3rd_instar",
          "length_mm": 16.5,
          "collection_location": "torso",
          "notes": "Found in largest mass"
        },
        {
          "specimen_id": "SPEC002", 
          "species": "calliphora_vicina",
          "stage": "2nd_instar",
          "length_mm": 12.0,
          "collection_location": "head"
        }
      ]
    }
    """
    try:
        # Display banner unless suppressed
        if not no_banner:
            banner = r"""
              (    (    (       ) (       )    )  (   (   (                ) (     
   (    (     )\ ) )\ ) )\ ) ( /( )\ ) ( /( ( /(  )\ ))\ ))\ )   (      ( /( )\ )  
   )\   )\   (()/((()/((()/( )\()|()/( )\())))\())(()/(()/(()/(   )\     )\()|()/(  
 (((_|(((_)(  /(_))/(_))/(_)|(_)\ /(_)|(_)\((_)\  /(_))(_))(_)|(((_)(  ((_)\ /(_)) 
 )\___)\ _ )\(_)) (_)) (_))  _((_|_))  _((_) ((_)(_))(_))(_))_ )\ _ )\__ ((_|_))   
((/ __(_)_\(_) |  | |  |_ _|| || | _ \| || |/ _ \| _ \_ _||   \(_)_\(_) \ / / __|  
 | (__ / _ \ | |__| |__ | | | __ |  _/| __ | (_) |   /| | | |) |/ _ \  \ V /\__ \  
  \___/_/ \_\|____|____|___||_||_|_|  |_||_|\___/|_|_\___||___//_/ \_\  |_| |___/  
                                                                                   
            """
            click.echo(banner)
            click.echo("Multi-Specimen Forensic Entomology Analysis")
            click.echo("=" * 50)
        
        # Load specimen data
        specimens = load_specimens_from_file(specimens_file)
        
        if verbose:
            click.echo(f"Loaded {len(specimens)} specimens from {specimens_file}")
        
        # Prepare temperature data
        temperature_data = {
            'avg_temp': ambient_temp if ambient_temp is not None else 20.0,
            'location': location,
            'date': discovery_date,
            'time': discovery_time
        }
        
        # Prepare case info
        case_info = {
            'case_id': case_id,
            'investigator': investigator,
            'location': location,
            'discovery_date': discovery_date,
            'discovery_time': discovery_time
        }
        
        # Analyze specimens
        analyzer = MultiSpecimenAnalyzer()
        results = analyzer.analyze_specimens(specimens, temperature_data, case_info)
        
        # Display results
        display_multi_specimen_results(results, verbose)
        
        # Export if requested
        if export:
            exported_file = analyzer.export_multi_specimen_results(results, export)
            click.echo(f"\nResults exported to: {exported_file}")
        
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


def load_specimens_from_file(file_path: str) -> List[SpecimenData]:
    """Load specimens from JSON file."""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        if 'specimens' not in data:
            raise ValueError("JSON file must contain 'specimens' array")
        
        specimens = []
        analyzer = MultiSpecimenAnalyzer()
        
        for i, spec_data in enumerate(data['specimens']):
            # Validate required fields
            required_fields = ['specimen_id', 'species', 'stage']
            for field in required_fields:
                if field not in spec_data:
                    raise ValueError(f"Specimen {i+1} missing required field: {field}")
            
            # Validate species and stage values
            try:
                species = CalliphoridaeSpecies(spec_data['species'])
                stage = DevelopmentStage(spec_data['stage'])
            except ValueError as e:
                raise ValueError(f"Invalid species or stage in specimen {i+1}: {str(e)}")
            
            specimen = analyzer.create_specimen_from_dict(spec_data)
            specimens.append(specimen)
        
        return specimens
    
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {str(e)}")
    except FileNotFoundError:
        raise ValueError(f"Specimens file not found: {file_path}")


def display_multi_specimen_results(results, verbose: bool = False):
    """Display comprehensive multi-specimen analysis results."""
    
    # Summary header
    click.echo(f"\n{'='*60}")
    click.echo(f"MULTI-SPECIMEN PMI ANALYSIS RESULTS")
    click.echo(f"{'='*60}")
    
    # Specimen summary
    click.echo(f"Specimens Analyzed: {len(results.specimen_results)}")
    click.echo(f"Overall Quality: {results.overall_quality.value.upper()}")
    
    # Individual specimen results
    click.echo(f"\nINDIVIDUAL SPECIMEN RESULTS:")
    click.echo("-" * 40)
    
    for i, result in enumerate(results.specimen_results, 1):
        spec = result.specimen
        click.echo(f"\nSpecimen {i}: {spec.specimen_id}")
        click.echo(f"  Species: {spec.species.value.replace('_', ' ').title()}")
        click.echo(f"  Stage: {spec.stage.value.replace('_', ' ').title()}")
        if spec.length_mm:
            click.echo(f"  Length: {spec.length_mm}mm")
        if spec.collection_location:
            click.echo(f"  Location: {spec.collection_location}")
        click.echo(f"  PMI Estimate: {result.pmi_days:.1f} days ({result.pmi_hours:.1f} hours)")
        click.echo(f"  Confidence: {result.confidence_low:.1f} - {result.confidence_high:.1f} days")
        click.echo(f"  Quality: {result.data_quality.value.upper()} ({result.quality_score:.0f}/100)")
        
        if result.validation_warnings and verbose:
            click.echo(f"  Warnings: {'; '.join(result.validation_warnings[:2])}")
    
    # Statistical summary
    stats = results.statistical_summary
    click.echo(f"\nSTATISTICAL SUMMARY:")
    click.echo("-" * 40)
    click.echo(f"PMI Range: {stats['pmi_min']:.1f} - {stats['pmi_max']:.1f} days")
    click.echo(f"PMI Mean: {stats['pmi_mean']:.1f} days")
    click.echo(f"PMI Median: {stats['pmi_median']:.1f} days")
    click.echo(f"Standard Deviation: {stats['pmi_std_dev']:.1f} days")
    click.echo(f"Coefficient of Variation: {stats['pmi_cv']:.1f}%")
    click.echo(f"Species Diversity: {stats['species_diversity']} species")
    click.echo(f"Stage Diversity: {stats['stage_diversity']} stages")
    
    # Consensus PMI
    consensus = results.consensus_pmi
    click.echo(f"\nCONSENSUS PMI ESTIMATE:")
    click.echo("-" * 40)
    click.echo(f"Method: {consensus['method'].replace('_', ' ').title()}")
    click.echo(f"Consensus PMI: {consensus['pmi_days']:.1f} days ({consensus['pmi_hours']:.1f} hours)")
    click.echo(f"Confidence Range: {consensus['confidence_low']:.1f} - {consensus['confidence_high']:.1f} days")
    click.echo(f"Basis: {consensus['basis']}")
    
    # Conflict analysis
    conflicts = results.conflict_analysis
    if conflicts['has_conflicts']:
        click.echo(f"\nCONFLICT ANALYSIS:")
        click.echo("-" * 40)
        click.echo(f"Conflict Severity: {conflicts['severity'].upper()}")
        
        for detail in conflicts['conflict_details']:
            severity_icon = {
                'minor': '⚠️',
                'moderate': '🔶',
                'severe': '🚨'
            }.get(detail['severity'], '•')
            
            click.echo(f"{severity_icon} {detail['description']} ({detail['severity']})")
    else:
        click.echo(f"\nCONFLICT ANALYSIS: No significant conflicts detected ✓")
    
    # Recommendations
    if results.recommendations:
        click.echo(f"\nRECOMMENDATIONS:")
        click.echo("-" * 40)
        for i, rec in enumerate(results.recommendations, 1):
            click.echo(f"{i}. {rec}")
    
    # Create visualization for multiple specimens
    if len(results.specimen_results) > 1:
        click.echo(f"\nPMI COMPARISON VISUALIZATION:")
        click.echo("-" * 40)
        create_multi_specimen_visualization(results.specimen_results)


def create_multi_specimen_visualization(specimen_results):
    """Create a simple visualization comparing PMI estimates."""
    max_pmi = max(r.pmi_days for r in specimen_results)
    
    for i, result in enumerate(specimen_results, 1):
        spec = result.specimen
        pmi = result.pmi_days
        
        # Create proportional bar
        bar_length = int((pmi / max_pmi) * 40) if max_pmi > 0 else 1
        bar = "█" * bar_length
        
        # Quality indicator
        quality_icon = {
            'excellent': '🟢',
            'good': '🟡', 
            'fair': '🟠',
            'poor': '🔴',
            'unreliable': '⚫'
        }.get(result.data_quality.value, '❓')
        
        click.echo(f"{spec.specimen_id:8} {quality_icon} {bar} {pmi:.1f}d")


@click.command()
@click.option('--output', '-o', required=True,
              help='Output file path for specimen template')
def create_template(output: str):
    """Create a template JSON file for specimen data."""
    template = {
        "specimens": [
            {
                "specimen_id": "SPEC001",
                "species": "lucilia_sericata",
                "stage": "3rd_instar", 
                "length_mm": 16.5,
                "collection_location": "torso",
                "collection_method": "manual collection",
                "preservation_method": "70% ethanol",
                "notes": "Found in largest mass on ventral thorax"
            },
            {
                "specimen_id": "SPEC002",
                "species": "calliphora_vicina", 
                "stage": "2nd_instar",
                "length_mm": 12.0,
                "collection_location": "head",
                "collection_method": "manual collection", 
                "preservation_method": "70% ethanol",
                "notes": "Smaller population near natural orifices"
            },
            {
                "specimen_id": "SPEC003",
                "species": "lucilia_sericata",
                "stage": "pupa",
                "length_mm": 10.0,
                "collection_location": "soil_beneath_body",
                "collection_method": "soil sifting",
                "preservation_method": "dry preservation",
                "notes": "Found 5cm beneath body in soil"
            }
        ]
    }
    
    if not output.endswith('.json'):
        output += '.json'
    
    with open(output, 'w') as f:
        json.dump(template, f, indent=2, ensure_ascii=False)
    
    click.echo(f"Specimen template created: {output}")
    click.echo("\nValid species values:")
    for species in CalliphoridaeSpecies:
        click.echo(f"  - {species.value}")
    
    click.echo("\nValid stage values:")
    for stage in DevelopmentStage:
        click.echo(f"  - {stage.value}")


if __name__ == '__main__':
    multi_analyze()