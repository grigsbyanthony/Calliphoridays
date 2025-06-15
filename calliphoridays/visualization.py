"""
Terminal-based visualization for PMI estimates.
"""
import math
import random
from typing import Dict, Tuple, List
from datetime import datetime, timedelta


class TerminalVisualizer:
    """
    Creates terminal-based visualizations for PMI data.
    """
    
    def __init__(self, width: int = 60):
        self.width = width
        self.bar_char = "█"
        self.error_char = "─"
        self.center_char = "│"
        self.point_char = "●"
        self.temp_chars = ["▁", "▂", "▃", "▄", "▅", "▆", "▇", "█"]
    
    def create_pmi_barplot(self, pmi_result: Dict) -> str:
        """
        Create a horizontal bar plot showing PMI estimate with confidence intervals.
        
        Args:
            pmi_result: PMI calculation result dictionary
            
        Returns:
            String representation of the bar plot
        """
        pmi_days = pmi_result['pmi_days']
        confidence_low = pmi_result['confidence_low']
        confidence_high = pmi_result['confidence_high']
        species = pmi_result['species'].value.replace('_', ' ').title()
        stage = pmi_result['stage'].value.replace('_', ' ').title()
        
        # Calculate the range for the plot
        plot_min = max(0, confidence_low - (confidence_high - confidence_low) * 0.2)
        plot_max = confidence_high + (confidence_high - confidence_low) * 0.2
        plot_range = plot_max - plot_min
        
        if plot_range == 0:
            plot_range = 1
        
        # Create the visualization
        lines = []
        lines.append("PMI ESTIMATE VISUALIZATION")
        lines.append("=" * 50)
        lines.append(f"Species: {species}")
        lines.append(f"Stage: {stage}")
        lines.append("")
        
        # Create scale labels
        scale_line = self._create_scale_line(plot_min, plot_max)
        lines.append("Days: " + scale_line)
        
        # Create the main bar with confidence interval
        bar_line = self._create_bar_line(
            pmi_days, confidence_low, confidence_high, 
            plot_min, plot_max
        )
        lines.append("PMI:  " + bar_line)
        
        # Add detailed information
        lines.append("")
        lines.append(f"● Estimate: {pmi_days:.1f} days ({pmi_days * 24:.1f} hours)")
        lines.append(f"─ Range: {confidence_low:.1f} - {confidence_high:.1f} days")
        lines.append(f"  Confidence: ±{((confidence_high - confidence_low) / 2 / pmi_days * 100):.1f}%")
        
        return "\n".join(lines)
    
    def create_pmi_with_temperature_timeline(self, pmi_result: Dict, temperature_data: Dict) -> str:
        """
        Create PMI barplot with temperature timeline underneath.
        
        Args:
            pmi_result: PMI calculation result dictionary
            temperature_data: Temperature data dictionary
            
        Returns:
            String representation of combined visualization
        """
        # Get the basic PMI barplot
        pmi_plot = self.create_pmi_barplot(pmi_result)
        
        # Add temperature timeline
        temp_timeline = self._create_temperature_timeline(pmi_result, temperature_data)
        
        return pmi_plot + "\n\n" + temp_timeline
    
    def _create_scale_line(self, min_val: float, max_val: float) -> str:
        """Create a scale line showing day values."""
        scale_positions = [0, 0.25, 0.5, 0.75, 1.0]
        scale_line = [" "] * self.width
        
        for pos in scale_positions:
            char_pos = int(pos * (self.width - 1))
            value = min_val + (max_val - min_val) * pos
            value_str = f"{value:.1f}"
            
            # Place the value string centered on the position
            start_pos = max(0, char_pos - len(value_str) // 2)
            end_pos = min(self.width, start_pos + len(value_str))
            
            for i, char in enumerate(value_str):
                if start_pos + i < self.width:
                    scale_line[start_pos + i] = char
        
        return "".join(scale_line)
    
    def _create_bar_line(self, estimate: float, low: float, high: float,
                        plot_min: float, plot_max: float) -> str:
        """Create the main bar line with confidence interval."""
        plot_range = plot_max - plot_min
        bar_line = [" "] * self.width
        
        # Calculate positions
        low_pos = int((low - plot_min) / plot_range * (self.width - 1))
        high_pos = int((high - plot_min) / plot_range * (self.width - 1))
        estimate_pos = int((estimate - plot_min) / plot_range * (self.width - 1))
        
        # Ensure positions are within bounds
        low_pos = max(0, min(self.width - 1, low_pos))
        high_pos = max(0, min(self.width - 1, high_pos))
        estimate_pos = max(0, min(self.width - 1, estimate_pos))
        
        # Draw confidence interval bar
        for i in range(low_pos, high_pos + 1):
            if i < self.width:
                bar_line[i] = self.bar_char
        
        # Draw error bars (tails)
        if low_pos > 0:
            bar_line[max(0, low_pos - 1)] = self.error_char
        if high_pos < self.width - 1:
            bar_line[min(self.width - 1, high_pos + 1)] = self.error_char
        
        # Draw center point
        if estimate_pos < self.width:
            bar_line[estimate_pos] = self.point_char
        
        return "".join(bar_line)
    
    def create_temperature_plot(self, temp_data: Dict) -> str:
        """
        Create a simple temperature visualization.
        
        Args:
            temp_data: Temperature data dictionary
            
        Returns:
            String representation of temperature plot
        """
        avg_temp = temp_data['avg_temp']
        min_temp = temp_data.get('min_temp', avg_temp - 5)
        max_temp = temp_data.get('max_temp', avg_temp + 5)
        
        lines = []
        lines.append("TEMPERATURE DATA")
        lines.append("=" * 30)
        
        # Create a simple temperature bar
        temp_range = max_temp - min_temp
        if temp_range == 0:
            temp_range = 10
        
        # Normalize temperatures to 0-30 scale for visualization
        plot_width = 30
        avg_pos = int((avg_temp - min_temp) / temp_range * plot_width)
        
        temp_bar = [" "] * plot_width
        temp_bar[min(plot_width - 1, max(0, avg_pos))] = "●"
        
        # Add temperature markers
        for i, temp in enumerate([min_temp, avg_temp, max_temp]):
            pos = int((temp - min_temp) / temp_range * plot_width) if temp_range > 0 else plot_width // 2
            pos = min(plot_width - 1, max(0, pos))
            if i == 1:  # Average temperature
                temp_bar[pos] = "●"
            else:
                temp_bar[pos] = "|"
        
        lines.append(f"Range: {''.join(temp_bar)}")
        lines.append(f"       {min_temp:.1f}°C" + " " * (plot_width - 10) + f"{max_temp:.1f}°C")
        lines.append(f"Average: {avg_temp:.1f}°C")
        
        return "\n".join(lines)
    
    def create_species_comparison(self, species_data: Dict) -> str:
        """
        Create a comparison visualization for different species.
        
        Args:
            species_data: Dictionary with species as keys and PMI data as values
            
        Returns:
            String representation of species comparison
        """
        lines = []
        lines.append("SPECIES COMPARISON")
        lines.append("=" * 40)
        
        max_pmi = max(data['pmi_days'] for data in species_data.values())
        
        for species_enum, data in species_data.items():
            species_name = species_enum.value.replace('_', ' ').title()
            pmi = data['pmi_days']
            
            # Create a proportional bar
            bar_length = int((pmi / max_pmi) * 30)
            bar = self.bar_char * bar_length
            
            lines.append(f"{species_name:20} {bar} {pmi:.1f} days")
        
        return "\n".join(lines)
    
    def create_development_timeline(self, species_name: str, stage_data: Dict) -> str:
        """
        Create a timeline showing development stages.
        
        Args:
            species_name: Name of the species
            stage_data: Dictionary with stages and their ADD values
            
        Returns:
            String representation of development timeline
        """
        lines = []
        lines.append(f"DEVELOPMENT TIMELINE: {species_name.upper()}")
        lines.append("=" * 50)
        
        stages = ['1st_instar', '2nd_instar', '3rd_instar', 'pupa']
        stage_names = ['1st Instar', '2nd Instar', '3rd Instar', 'Pupa']
        
        max_add = max(stage_data.values())
        timeline_width = 40
        
        for i, (stage, stage_name) in enumerate(zip(stages, stage_names)):
            if stage in stage_data:
                add_value = stage_data[stage]
                position = int((add_value / max_add) * timeline_width)
                
                timeline = ["-"] * timeline_width
                timeline[min(timeline_width - 1, position)] = "●"
                
                lines.append(f"{stage_name:12} {''.join(timeline)} {add_value:.1f} ADD")
        
        lines.append(f"{'':12} 0" + " " * (timeline_width - 8) + f"{max_add:.1f} ADD")
        
        return "\n".join(lines)
    
    def _create_temperature_timeline(self, pmi_result: Dict, temperature_data: Dict) -> str:
        """
        Create a temperature timeline showing temperature variation across PMI range.
        
        Args:
            pmi_result: PMI calculation result dictionary
            temperature_data: Temperature data dictionary
            
        Returns:
            String representation of temperature timeline
        """
        pmi_days = pmi_result['pmi_days']
        confidence_low = pmi_result['confidence_low']
        confidence_high = pmi_result['confidence_high']
        avg_temp = temperature_data['avg_temp']
        min_temp = temperature_data.get('min_temp', avg_temp - 8)
        max_temp = temperature_data.get('max_temp', avg_temp + 8)
        
        lines = []
        lines.append("TEMPERATURE TIMELINE (Development Period)")
        lines.append("=" * 50)
        
        # Calculate the range for the plot (same as PMI plot)
        plot_min_days = max(0, confidence_low - (confidence_high - confidence_low) * 0.2)
        plot_max_days = confidence_high + (confidence_high - confidence_low) * 0.2
        
        # Generate simulated daily temperatures across the PMI range
        timeline_temps = self._generate_temperature_timeline(
            plot_min_days, plot_max_days, avg_temp, min_temp, max_temp
        )
        
        # Create temperature scale
        temp_range = max_temp - min_temp
        temp_scale_line = self._create_temperature_scale(min_temp, max_temp)
        lines.append("Temp: " + temp_scale_line)
        
        # Create temperature line plot
        temp_line = self._create_temperature_line(timeline_temps, min_temp, max_temp)
        lines.append("°C:   " + temp_line)
        
        # Create day scale (matching PMI plot)
        day_scale_line = self._create_scale_line(plot_min_days, plot_max_days)
        lines.append("Days: " + day_scale_line)
        
        lines.append("")
        lines.append(f"Temperature range: {min_temp:.1f}°C - {max_temp:.1f}°C (avg: {avg_temp:.1f}°C)")
        lines.append(f"Development period: {confidence_low:.1f} - {confidence_high:.1f} days")
        
        return "\n".join(lines)
    
    def _generate_temperature_timeline(self, start_days: float, end_days: float, 
                                     avg_temp: float, min_temp: float, max_temp: float) -> List[float]:
        """
        Generate simulated daily temperatures for the timeline.
        
        Args:  
            start_days: Start of the period in days
            end_days: End of the period in days
            avg_temp: Average temperature
            min_temp: Minimum temperature
            max_temp: Maximum temperature
            
        Returns:
            List of temperatures for each position in the timeline
        """
        num_points = self.width
        temps = []
        
        # Create realistic temperature variation
        for i in range(num_points):
            # Add some daily variation around the average
            daily_variation = math.sin(i * 2 * math.pi / 7) * (max_temp - min_temp) * 0.3  # Weekly cycle
            random_variation = (random.random() - 0.5) * (max_temp - min_temp) * 0.2  # Random variation
            
            temp = avg_temp + daily_variation + random_variation
            temp = max(min_temp, min(max_temp, temp))  # Clamp to range
            temps.append(temp)
        
        return temps
    
    def _create_temperature_scale(self, min_temp: float, max_temp: float) -> str:
        """Create temperature scale line."""
        scale_positions = [0, 0.25, 0.5, 0.75, 1.0]
        scale_line = [" "] * self.width
        
        for pos in scale_positions:
            char_pos = int(pos * (self.width - 1))
            value = min_temp + (max_temp - min_temp) * pos
            value_str = f"{value:.0f}"
            
            # Place the value string centered on the position
            start_pos = max(0, char_pos - len(value_str) // 2)
            
            for i, char in enumerate(value_str):
                if start_pos + i < self.width:
                    scale_line[start_pos + i] = char
        
        return "".join(scale_line)
    
    def _create_temperature_line(self, temps: List[float], min_temp: float, max_temp: float) -> str:
        """
        Create temperature line using block characters.
        
        Args:
            temps: List of temperatures
            min_temp: Minimum temperature for scaling
            max_temp: Maximum temperature for scaling
            
        Returns:
            String representation of temperature line
        """
        temp_range = max_temp - min_temp
        if temp_range == 0:
            temp_range = 1
        
        temp_line = []
        for temp in temps:
            # Normalize temperature to 0-1 range
            normalized = (temp - min_temp) / temp_range
            
            # Map to character index (0-7 for 8 different heights)
            char_index = int(normalized * (len(self.temp_chars) - 1))
            char_index = max(0, min(len(self.temp_chars) - 1, char_index))
            
            temp_line.append(self.temp_chars[char_index])
        
        return "".join(temp_line)