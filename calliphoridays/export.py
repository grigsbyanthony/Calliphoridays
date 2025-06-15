"""
Data export and reporting functionality for PMI estimates.
"""
import json
import csv
import os
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

from .models import CalliphoridaeSpecies, DevelopmentStage, get_species_info


class DataExporter:
    """
    Handles exporting PMI data to various formats.
    """
    
    def __init__(self):
        self.supported_formats = ['json', 'csv', 'txt']
    
    def export_case_data(self, pmi_result: Dict, temperature_data: Dict, 
                        case_info: Dict, output_path: str, format_type: str = 'json') -> str:
        """
        Export case data to specified format.
        
        Args:
            pmi_result: PMI calculation results
            temperature_data: Temperature data used
            case_info: Case metadata (location, dates, etc.)
            output_path: Output file path
            format_type: Export format ('json', 'csv', 'txt')
            
        Returns:
            Path to exported file
        """
        if format_type not in self.supported_formats:
            raise ValueError(f"Unsupported format: {format_type}. Supported: {self.supported_formats}")
        
        # Prepare comprehensive data package
        export_data = self._prepare_export_data(pmi_result, temperature_data, case_info)
        
        if format_type == 'json':
            return self._export_json(export_data, output_path)
        elif format_type == 'csv':
            return self._export_csv(export_data, output_path)
        elif format_type == 'txt':
            return self._export_txt(export_data, output_path)
    
    def _prepare_export_data(self, pmi_result: Dict, temperature_data: Dict, case_info: Dict) -> Dict:
        """Prepare comprehensive data structure for export."""
        
        # Convert enum objects to strings for serialization
        species = pmi_result['species']
        stage = pmi_result['stage']
        
        export_data = {
            'case_metadata': {
                'export_timestamp': datetime.now().isoformat(),
                'tool_version': '0.1.0',
                'case_id': case_info.get('case_id', f"PMI_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
                'investigator': case_info.get('investigator', 'Unknown'),
                'location': case_info.get('location', 'Unknown'),
                'discovery_date': case_info.get('discovery_date', 'Unknown'),
                'discovery_time': case_info.get('discovery_time', None)
            },
            'specimen_data': {
                'species': species.value if hasattr(species, 'value') else str(species),
                'species_common_name': get_species_info(species)['common_name'] if hasattr(species, 'value') else 'Unknown',
                'development_stage': stage.value if hasattr(stage, 'value') else str(stage),
                'specimen_length_mm': case_info.get('specimen_length'),
                'collection_method': case_info.get('collection_method', 'Not specified'),
                'preservation_method': case_info.get('preservation_method', 'Not specified')
            },
            'temperature_data': {
                'avg_temp_celsius': temperature_data.get('avg_temp'),
                'min_temp_celsius': temperature_data.get('min_temp'),
                'max_temp_celsius': temperature_data.get('max_temp'),
                'source': temperature_data.get('source', 'Unknown'),
                'location_coordinates': temperature_data.get('location'),
                'date_range': temperature_data.get('date_range')
            },
            'pmi_calculations': {
                'estimated_pmi_days': pmi_result.get('pmi_days'),
                'estimated_pmi_hours': pmi_result.get('pmi_hours'),
                'confidence_interval_low_days': pmi_result.get('confidence_low'),
                'confidence_interval_high_days': pmi_result.get('confidence_high'),
                'accumulated_degree_days': pmi_result.get('accumulated_dd'),
                'base_temperature_celsius': pmi_result.get('base_temp'),
                'development_threshold_add': pmi_result.get('dev_threshold'),
                'calculation_method': 'Accumulated Degree Days (ADD)',
                'confidence_percentage': 20.0  # Standard 20% confidence interval
            },
            'scientific_basis': {
                'base_temp_source': 'Published forensic entomology research',
                'development_data_source': 'Peer-reviewed literature',
                'method_reference': 'Accumulated Degree Days method',
                'accuracy_notes': 'Results should be interpreted by qualified forensic entomologists',
                'limitations': [
                    'Based on laboratory-controlled development data',
                    'Actual field conditions may vary',
                    'Temperature estimates may not reflect microclimate',
                    'Species identification must be verified'
                ]
            }
        }
        
        return export_data
    
    def _export_json(self, data: Dict, output_path: str) -> str:
        """Export data as JSON file."""
        if not output_path.endswith('.json'):
            output_path += '.json'
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return output_path
    
    def _export_csv(self, data: Dict, output_path: str) -> str:
        """Export data as CSV file."""
        if not output_path.endswith('.csv'):
            output_path += '.csv'
        
        # Flatten data for CSV format
        csv_rows = []
        
        # Case metadata
        csv_rows.extend([
            ['Section', 'Field', 'Value'],
            ['Case Metadata', 'Export Timestamp', data['case_metadata']['export_timestamp']],
            ['Case Metadata', 'Tool Version', data['case_metadata']['tool_version']],
            ['Case Metadata', 'Case ID', data['case_metadata']['case_id']],
            ['Case Metadata', 'Investigator', data['case_metadata']['investigator']],
            ['Case Metadata', 'Location', data['case_metadata']['location']],
            ['Case Metadata', 'Discovery Date', data['case_metadata']['discovery_date']],
            ['Case Metadata', 'Discovery Time', data['case_metadata']['discovery_time']],
            ['', '', ''],  # Separator
        ])
        
        # Specimen data
        csv_rows.extend([
            ['Specimen Data', 'Species', data['specimen_data']['species']],
            ['Specimen Data', 'Common Name', data['specimen_data']['species_common_name']],
            ['Specimen Data', 'Development Stage', data['specimen_data']['development_stage']],
            ['Specimen Data', 'Specimen Length (mm)', data['specimen_data']['specimen_length_mm']],
            ['Specimen Data', 'Collection Method', data['specimen_data']['collection_method']],
            ['Specimen Data', 'Preservation Method', data['specimen_data']['preservation_method']],
            ['', '', ''],  # Separator
        ])
        
        # Temperature data
        csv_rows.extend([
            ['Temperature Data', 'Average Temperature (°C)', data['temperature_data']['avg_temp_celsius']],
            ['Temperature Data', 'Min Temperature (°C)', data['temperature_data']['min_temp_celsius']],
            ['Temperature Data', 'Max Temperature (°C)', data['temperature_data']['max_temp_celsius']],
            ['Temperature Data', 'Source', data['temperature_data']['source']],
            ['Temperature Data', 'Location Coordinates', data['temperature_data']['location_coordinates']],
            ['Temperature Data', 'Date Range', data['temperature_data']['date_range']],
            ['', '', ''],  # Separator
        ])
        
        # PMI calculations
        csv_rows.extend([
            ['PMI Calculations', 'Estimated PMI (days)', data['pmi_calculations']['estimated_pmi_days']],
            ['PMI Calculations', 'Estimated PMI (hours)', data['pmi_calculations']['estimated_pmi_hours']],
            ['PMI Calculations', 'Confidence Low (days)', data['pmi_calculations']['confidence_interval_low_days']],
            ['PMI Calculations', 'Confidence High (days)', data['pmi_calculations']['confidence_interval_high_days']],
            ['PMI Calculations', 'Accumulated Degree Days', data['pmi_calculations']['accumulated_degree_days']],
            ['PMI Calculations', 'Base Temperature (°C)', data['pmi_calculations']['base_temperature_celsius']],
            ['PMI Calculations', 'Development Threshold (ADD)', data['pmi_calculations']['development_threshold_add']],
            ['PMI Calculations', 'Calculation Method', data['pmi_calculations']['calculation_method']],
            ['PMI Calculations', 'Confidence Percentage', data['pmi_calculations']['confidence_percentage']],
        ])
        
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(csv_rows)
        
        return output_path
    
    def _format_temp(self, temp: Optional[float]) -> str:
        """Format temperature value, handling None."""
        return f"{temp:.1f}" if temp is not None else "N/A"
    
    def _export_txt(self, data: Dict, output_path: str) -> str:
        """Export data as human-readable text report."""
        if not output_path.endswith('.txt'):
            output_path += '.txt'
        
        report_lines = []
        
        # Header
        report_lines.extend([
            "CALLIPHORIDAYS - FORENSIC ENTOMOLOGY PMI REPORT",
            "=" * 60,
            "",
            f"Generated: {data['case_metadata']['export_timestamp']}",
            f"Tool Version: {data['case_metadata']['tool_version']}",
            "",
            "CASE INFORMATION",
            "-" * 30,
            f"Case ID: {data['case_metadata']['case_id']}",
            f"Investigator: {data['case_metadata']['investigator']}",
            f"Location: {data['case_metadata']['location']}",
            f"Discovery Date: {data['case_metadata']['discovery_date']}",
            f"Discovery Time: {data['case_metadata']['discovery_time'] or 'Not specified'}",
            "",
            "SPECIMEN ANALYSIS",
            "-" * 30,
            f"Species: {data['specimen_data']['species']}",
            f"Common Name: {data['specimen_data']['species_common_name']}",
            f"Development Stage: {data['specimen_data']['development_stage']}",
            f"Specimen Length: {data['specimen_data']['specimen_length_mm'] or 'Not measured'} mm",
            f"Collection Method: {data['specimen_data']['collection_method']}",
            f"Preservation Method: {data['specimen_data']['preservation_method']}",
            "",
            "TEMPERATURE DATA",
            "-" * 30,
            f"Average Temperature: {data['temperature_data']['avg_temp_celsius']:.1f}°C",
            f"Temperature Range: {self._format_temp(data['temperature_data']['min_temp_celsius'])}°C - {self._format_temp(data['temperature_data']['max_temp_celsius'])}°C",
            f"Data Source: {data['temperature_data']['source']}",
            f"Location: {data['temperature_data']['location_coordinates'] or 'Not specified'}",
            f"Date Range: {data['temperature_data']['date_range'] or 'Not specified'}",
            "",
            "PMI ESTIMATE",
            "-" * 30,
            f"Estimated PMI: {data['pmi_calculations']['estimated_pmi_days']:.1f} days ({data['pmi_calculations']['estimated_pmi_hours']:.1f} hours)",
            f"Confidence Interval: {data['pmi_calculations']['confidence_interval_low_days']:.1f} - {data['pmi_calculations']['confidence_interval_high_days']:.1f} days",
            f"Confidence Level: ±{data['pmi_calculations']['confidence_percentage']:.0f}%",
            "",
            "CALCULATION DETAILS",
            "-" * 30,
            f"Method: {data['pmi_calculations']['calculation_method']}",
            f"Accumulated Degree Days: {data['pmi_calculations']['accumulated_degree_days']:.1f} ADD",
            f"Base Temperature: {data['pmi_calculations']['base_temperature_celsius']:.1f}°C",
            f"Development Threshold: {data['pmi_calculations']['development_threshold_add']:.1f} ADD",
            "",
            "SCIENTIFIC BASIS & LIMITATIONS",
            "-" * 30,
            f"Method Reference: {data['scientific_basis']['method_reference']}",
            f"Data Source: {data['scientific_basis']['development_data_source']}",
            "",
            "Important Limitations:",
        ])
        
        for limitation in data['scientific_basis']['limitations']:
            report_lines.append(f"• {limitation}")
        
        report_lines.extend([
            "",
            "DISCLAIMER",
            "-" * 30,
            data['scientific_basis']['accuracy_notes'],
            "",
            "This report should be reviewed and interpreted by qualified forensic entomologists.",
            "Results are estimates based on available scientific data and environmental conditions.",
        ])
        
        with open(output_path, 'w') as f:
            f.write('\n'.join(report_lines))
        
        return output_path
    
    def generate_case_id(self, location: str, discovery_date: str) -> str:
        """Generate a unique case ID."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        location_code = ''.join(c.upper() for c in location if c.isalnum())[:6]
        date_code = discovery_date.replace('-', '')
        return f"PMI_{location_code}_{date_code}_{timestamp}"