"""
Professional PDF report generator for forensic entomology analyses.
"""
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import io
import base64

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.colors import HexColor, black, darkblue, darkgreen, red
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
    from reportlab.platypus.flowables import HRFlowable
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    import numpy as np
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

from .models import ForensicSpecies, DevelopmentStage, get_species_info


class ForensicReportGenerator:
    """
    Professional PDF report generator for forensic entomology cases.
    """
    
    def __init__(self):
        if not REPORTLAB_AVAILABLE:
            raise ImportError("ReportLab is required for PDF generation. Install with: pip install reportlab")
        
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
        
    def setup_custom_styles(self):
        """Set up custom styles for the report."""
        # Title style
        self.styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=self.styles['Title'],
            fontSize=18,
            spaceAfter=20,
            textColor=darkblue,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading1'],
            fontSize=14,
            spaceBefore=15,
            spaceAfter=10,
            textColor=darkblue,
            fontName='Helvetica-Bold'
        ))
        
        # Subsection header style
        self.styles.add(ParagraphStyle(
            name='SubsectionHeader',
            parent=self.styles['Heading2'],
            fontSize=12,
            spaceBefore=10,
            spaceAfter=8,
            textColor=darkgreen,
            fontName='Helvetica-Bold'
        ))
        
        # Warning style
        self.styles.add(ParagraphStyle(
            name='Warning',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceBefore=5,
            spaceAfter=5,
            textColor=red,
            fontName='Helvetica-Bold',
            leftIndent=20,
            rightIndent=20
        ))
        
        # Methodology style
        self.styles.add(ParagraphStyle(
            name='Methodology',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceBefore=5,
            spaceAfter=5,
            alignment=TA_JUSTIFY,
            leftIndent=15
        ))
        
        # Footer style
        self.styles.add(ParagraphStyle(
            name='Footer',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_CENTER
        ))
    
    def generate_forensic_report(self, 
                                pmi_estimate: Dict,
                                validation_result: Any,
                                case_info: Dict,
                                temperature_data: Dict,
                                species: ForensicSpecies,
                                stage: DevelopmentStage,
                                alternative_results: Optional[Any] = None,
                                output_path: str = None) -> str:
        """
        Generate a comprehensive forensic entomology report.
        
        Args:
            pmi_estimate: PMI calculation results
            validation_result: Validation analysis results
            case_info: Case information and metadata
            temperature_data: Temperature data used in calculations
            species: Forensic species analyzed
            stage: Development stage of specimen
            alternative_results: Alternative method results (optional)
            output_path: Output file path (optional)
            
        Returns:
            str: Path to generated PDF report
        """
        if not output_path:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            case_id = case_info.get('case_id', 'Unknown')
            output_path = f"forensic_report_{case_id}_{timestamp}.pdf"
        
        # Ensure output path has .pdf extension
        if not output_path.endswith('.pdf'):
            output_path += '.pdf'
        
        # Create PDF document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=1*inch,
            bottomMargin=0.75*inch
        )
        
        # Build report content
        story = []
        
        # Header and title
        story.extend(self._build_header(case_info))
        story.extend(self._build_case_summary(case_info, species, stage, pmi_estimate))
        story.extend(self._build_methodology_section())
        story.extend(self._build_results_section(pmi_estimate, temperature_data, species, stage))
        story.extend(self._build_validation_section(validation_result))
        
        if alternative_results:
            story.extend(self._build_alternative_methods_section(alternative_results))
        
        story.extend(self._build_conclusions_section(pmi_estimate, validation_result))
        story.extend(self._build_limitations_section())
        story.extend(self._build_references_section())
        story.extend(self._build_footer(case_info))
        
        # Build PDF
        doc.build(story)
        
        return output_path
    
    def _build_header(self, case_info: Dict) -> List:
        """Build report header section."""
        story = []
        
        # Report title
        title = "FORENSIC ENTOMOLOGY ANALYSIS REPORT"
        story.append(Paragraph(title, self.styles['ReportTitle']))
        story.append(Spacer(1, 10))
        
        # Case information table
        case_data = [
            ['Case ID:', case_info.get('case_id', 'Not specified')],
            ['Date of Analysis:', datetime.now().strftime('%B %d, %Y')],
            ['Investigator:', case_info.get('investigator', 'Not specified')],
            ['Location:', case_info.get('location', 'Not specified')],
            ['Discovery Date:', case_info.get('discovery_date', 'Not specified')],
            ['Discovery Time:', case_info.get('discovery_time', 'Not specified')],
        ]
        
        case_table = Table(case_data, colWidths=[2*inch, 4*inch])
        case_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        
        story.append(case_table)
        story.append(Spacer(1, 20))
        story.append(HRFlowable(width="100%"))
        story.append(Spacer(1, 15))
        
        return story
    
    def _build_case_summary(self, case_info: Dict, species: ForensicSpecies, 
                           stage: DevelopmentStage, pmi_estimate: Dict) -> List:
        """Build case summary section."""
        story = []
        
        story.append(Paragraph("EXECUTIVE SUMMARY", self.styles['SectionHeader']))
        
        # Get species information
        species_info = get_species_info(species)
        scientific_name = species.value.replace('_', ' ').title()
        
        summary_text = f"""
        This report presents the forensic entomological analysis of specimens collected from the scene. 
        The analysis was conducted using established accumulated degree days (ADD) methodology with 
        temperature-corrected development models.
        
        <b>Key Findings:</b><br/>
        • Species identified: <i>{scientific_name}</i> ({species_info['common_name']})<br/>
        • Development stage: {stage.value.replace('_', ' ').title()}<br/>
        • Estimated PMI: {pmi_estimate['pmi_days']:.1f} days ({pmi_estimate['pmi_hours']:.1f} hours)<br/>
        • Confidence interval: {pmi_estimate['confidence_low']:.1f} - {pmi_estimate['confidence_high']:.1f} days<br/>
        • Analysis date: {datetime.now().strftime('%B %d, %Y')}
        """
        
        story.append(Paragraph(summary_text, self.styles['Normal']))
        story.append(Spacer(1, 15))
        
        return story
    
    def _build_methodology_section(self) -> List:
        """Build methodology section."""
        story = []
        
        story.append(Paragraph("METHODOLOGY", self.styles['SectionHeader']))
        
        methodology_text = """
        This analysis employs the Accumulated Degree Days (ADD) method, which is the standard 
        approach in forensic entomology for estimating postmortem intervals. The methodology 
        is based on the principle that insect development is temperature-dependent and follows 
        predictable patterns under known thermal conditions.
        """
        story.append(Paragraph(methodology_text, self.styles['Methodology']))
        
        story.append(Paragraph("Calculation Formula", self.styles['SubsectionHeader']))
        formula_text = """
        <b>PMI = Required_ADD / (Average_Temperature - Base_Temperature)</b><br/><br/>
        Where:<br/>
        • Required_ADD: Species and stage-specific development threshold<br/>
        • Average_Temperature: Environmental temperature during development<br/>
        • Base_Temperature: Minimum temperature for development
        """
        story.append(Paragraph(formula_text, self.styles['Methodology']))
        
        story.append(Paragraph("Temperature Data", self.styles['SubsectionHeader']))
        temp_text = """
        Temperature data was obtained from meteorological sources and adjusted for time-of-day 
        variations when discovery time was provided. Temperature represents the average 
        environmental conditions during the estimated development period.
        """
        story.append(Paragraph(temp_text, self.styles['Methodology']))
        
        story.append(Spacer(1, 15))
        return story
    
    def _build_results_section(self, pmi_estimate: Dict, temperature_data: Dict, 
                              species: ForensicSpecies, stage: DevelopmentStage) -> List:
        """Build detailed results section."""
        story = []
        
        story.append(Paragraph("DETAILED RESULTS", self.styles['SectionHeader']))
        
        # Species information
        species_info = get_species_info(species)
        scientific_name = species.value.replace('_', ' ').title()
        story.append(Paragraph("Species Analysis", self.styles['SubsectionHeader']))
        
        species_text = f"""
        <b>Scientific Name:</b> <i>{scientific_name}</i><br/>
        <b>Common Name:</b> {species_info['common_name']}<br/>
        <b>Family:</b> {species_info['family']}<br/>
        <b>Colonization:</b> {species_info['colonization']}<br/>
        <b>Development Stage:</b> {stage.value.replace('_', ' ').title()}
        """
        story.append(Paragraph(species_text, self.styles['Normal']))
        story.append(Spacer(1, 10))
        
        # PMI calculations
        story.append(Paragraph("PMI Calculations", self.styles['SubsectionHeader']))
        
        results_data = [
            ['Parameter', 'Value', 'Units'],
            ['Estimated PMI', f"{pmi_estimate['pmi_days']:.1f}", 'days'],
            ['Estimated PMI', f"{pmi_estimate['pmi_hours']:.1f}", 'hours'],
            ['Confidence Interval', f"{pmi_estimate['confidence_low']:.1f} - {pmi_estimate['confidence_high']:.1f}", 'days'],
            ['Base Temperature', f"{pmi_estimate['base_temp']:.1f}", '°C'],
            ['Average Temperature', f"{temperature_data['avg_temp']:.1f}", '°C'],
            ['Required ADD', f"{pmi_estimate['dev_threshold']:.1f}", 'degree days'],
            ['Accumulated ADD', f"{pmi_estimate['accumulated_dd']:.1f}", 'degree days'],
        ]
        
        results_table = Table(results_data, colWidths=[2.5*inch, 1.5*inch, 1*inch])
        results_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(results_table)
        story.append(Spacer(1, 15))
        
        return story
    
    def _build_validation_section(self, validation_result: Any) -> List:
        """Build validation and quality assessment section."""
        story = []
        
        story.append(Paragraph("DATA QUALITY ASSESSMENT", self.styles['SectionHeader']))
        
        # Quality score
        quality_text = f"""
        <b>Overall Data Quality:</b> {validation_result.data_quality.value.upper()}<br/>
        <b>Quality Score:</b> {validation_result.quality_score:.0f}/100<br/>
        <b>Reliability Level:</b> {'High' if validation_result.quality_score >= 80 else 'Moderate' if validation_result.quality_score >= 60 else 'Low'}
        """
        story.append(Paragraph(quality_text, self.styles['Normal']))
        story.append(Spacer(1, 10))
        
        # Validation warnings
        if validation_result.warnings:
            story.append(Paragraph("Validation Alerts", self.styles['SubsectionHeader']))
            
            warnings_text = "The following factors may affect the reliability of this analysis:<br/><br/>"
            for i, warning in enumerate(validation_result.warnings, 1):
                warnings_text += f"{i}. {warning}<br/>"
            
            story.append(Paragraph(warnings_text, self.styles['Warning']))
        
        story.append(Spacer(1, 15))
        return story
    
    def _build_alternative_methods_section(self, alternative_results: Any) -> List:
        """Build alternative methods comparison section."""
        story = []
        
        story.append(Paragraph("ALTERNATIVE METHODS ANALYSIS", self.styles['SectionHeader']))
        
        # Method agreement
        agreement = alternative_results.method_agreement
        agreement_text = f"""
        Multiple PMI calculation methods were employed to validate the primary estimate. 
        The methods showed <b>{agreement['agreement_level'].lower()}</b> agreement with a 
        coefficient of variation of {agreement['coefficient_of_variation']:.1f}%.
        
        <b>Method Range:</b> {agreement['min_pmi']:.1f} - {agreement['max_pmi']:.1f} days<br/>
        <b>Mean PMI:</b> {agreement['mean_pmi']:.1f} days<br/>
        <b>Standard Deviation:</b> {agreement['std_deviation']:.1f} days
        """
        story.append(Paragraph(agreement_text, self.styles['Normal']))
        story.append(Spacer(1, 10))
        
        # Individual method results
        story.append(Paragraph("Individual Method Results", self.styles['SubsectionHeader']))
        
        method_data = [['Method', 'PMI (days)', 'Confidence Interval', 'Reliability']]
        for estimate in alternative_results.estimates:
            method_name = estimate.method.value.replace('_', ' ').title()
            method_data.append([
                method_name,
                f"{estimate.pmi_days:.1f}",
                f"{estimate.confidence_low:.1f} - {estimate.confidence_high:.1f}",
                f"{estimate.reliability_score:.0f}/100"
            ])
        
        method_table = Table(method_data, colWidths=[2*inch, 1*inch, 1.5*inch, 1*inch])
        method_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(method_table)
        story.append(Spacer(1, 15))
        
        return story
    
    def _build_conclusions_section(self, pmi_estimate: Dict, validation_result: Any) -> List:
        """Build conclusions section."""
        story = []
        
        story.append(Paragraph("CONCLUSIONS", self.styles['SectionHeader']))
        
        # Determine confidence level
        quality_score = validation_result.quality_score
        if quality_score >= 80:
            confidence = "high confidence"
        elif quality_score >= 60:
            confidence = "moderate confidence"
        else:
            confidence = "low confidence"
        
        conclusions_text = f"""
        Based on the forensic entomological analysis of the submitted specimens, the estimated 
        postmortem interval is <b>{pmi_estimate['pmi_days']:.1f} days</b> with a confidence 
        interval of {pmi_estimate['confidence_low']:.1f} to {pmi_estimate['confidence_high']:.1f} 
        days. This estimate is made with <b>{confidence}</b> based on the available data and 
        environmental conditions.
        
        The analysis utilized established forensic entomology protocols and temperature-corrected 
        development models. The quality assessment indicates {'excellent' if quality_score >= 90 else 'good' if quality_score >= 70 else 'acceptable'} 
        data reliability for this type of analysis.
        """
        
        story.append(Paragraph(conclusions_text, self.styles['Normal']))
        story.append(Spacer(1, 15))
        
        return story
    
    def _build_limitations_section(self) -> List:
        """Build limitations and disclaimers section."""
        story = []
        
        story.append(Paragraph("LIMITATIONS AND DISCLAIMERS", self.styles['SectionHeader']))
        
        limitations_text = """
        This analysis is subject to the following limitations and considerations:
        
        <b>1. Environmental Factors:</b> Microclimate conditions, burial depth, clothing, 
        and other environmental factors may significantly affect insect development rates 
        and are not fully accounted for in this analysis.
        
        <b>2. Biological Variation:</b> Natural variation in insect development rates, 
        individual specimen characteristics, and population differences may affect accuracy.
        
        <b>3. Temperature Data:</b> The analysis relies on meteorological data which may 
        not precisely reflect conditions at the specific scene location.
        
        <b>4. Expert Interpretation:</b> These results represent scientific estimates that 
        must be interpreted by qualified forensic entomologists within the context of 
        the complete investigation.
        
        <b>5. Legal Considerations:</b> This analysis is provided for investigative purposes 
        and should be presented as expert evidence only by qualified professionals in 
        appropriate legal proceedings.
        """
        
        story.append(Paragraph(limitations_text, self.styles['Warning']))
        story.append(Spacer(1, 15))
        
        return story
    
    def _build_references_section(self) -> List:
        """Build scientific references section."""
        story = []
        
        story.append(Paragraph("SCIENTIFIC REFERENCES", self.styles['SectionHeader']))
        
        references_text = """
        This analysis is based on established forensic entomology research and methodologies:
        
        1. Amendt, J., Campobasso, C. P., Gaudry, E., Reiter, C., LeBlanc, H. N., & Hall, M. J. (2007). 
           Best practice in forensic entomology—standards and guidelines. International Journal of Legal Medicine, 121(2), 90-104.
        
        2. Catts, E. P., & Goff, M. L. (1992). Forensic entomology in criminal investigations. 
           Annual Review of Entomology, 37(1), 253-272.
        
        3. Higley, L. G., & Haskell, N. H. (2010). Insect development and forensic entomology. 
           In Forensic Entomology: The Utility of Arthropods in Legal Investigations (pp. 287-302). CRC Press.
        
        4. Ikemoto, T., & Takai, K. (2000). A new linearized formula for the law of total effective temperature. 
           Environmental Entomology, 29(4), 671-682.
        """
        
        story.append(Paragraph(references_text, self.styles['Normal']))
        story.append(Spacer(1, 15))
        
        return story
    
    def _build_footer(self, case_info: Dict) -> List:
        """Build report footer."""
        story = []
        
        story.append(PageBreak())
        
        footer_text = f"""
        Report generated by Calliphoridays Forensic Entomology Analysis Tool<br/>
        Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}<br/>
        Case ID: {case_info.get('case_id', 'Not specified')}<br/>
        
        This report contains {len([p for p in story if hasattr(p, 'text')])} pages of analysis and supporting documentation.
        """
        
        story.append(Paragraph(footer_text, self.styles['Footer']))
        
        return story


def create_forensic_report(pmi_estimate: Dict,
                          validation_result: Any,
                          case_info: Dict,
                          temperature_data: Dict,
                          species: ForensicSpecies,
                          stage: DevelopmentStage,
                          alternative_results: Optional[Any] = None,
                          output_path: str = None) -> str:
    """
    Convenience function to generate a forensic report.
    
    Returns:
        str: Path to generated PDF report
    """
    if not REPORTLAB_AVAILABLE:
        raise ImportError("ReportLab is required for PDF generation. Please install with: pip install reportlab")
    
    generator = ForensicReportGenerator()
    return generator.generate_forensic_report(
        pmi_estimate, validation_result, case_info, temperature_data,
        species, stage, alternative_results, output_path
    )