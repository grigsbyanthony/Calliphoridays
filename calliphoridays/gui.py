"""
GUI interface for Calliphoridays forensic entomology tool.
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
from tkinter import font as tkfont
from typing import Optional, Dict
import threading
import os
from datetime import datetime, date
import json

from .models import ForensicSpecies, DevelopmentStage, get_species_info
from .pmi_calculator import PMICalculator
from .weather import WeatherService
from .validation import PMIValidator
from .alternative_methods import AlternativePMICalculator, PMIMethod
from .export import DataExporter


class CalliphoridaysGUI:
    """
    Graphical user interface for the Calliphoridays forensic entomology tool.
    """
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Calliphoridays - Forensic Entomology PMI Estimation")
        self.root.geometry("1000x800")
        self.root.configure(bg='#f0f0f0')
        
        # Load custom fonts
        self.load_custom_fonts()
        
        # Initialize services
        self.pmi_calculator = PMICalculator()
        self.weather_service = WeatherService()
        self.validator = PMIValidator()
        self.exporter = DataExporter()
        
        # Variables
        self.species_var = tk.StringVar()
        self.stage_var = tk.StringVar()
        self.location_var = tk.StringVar()
        self.discovery_date_var = tk.StringVar()
        self.discovery_time_var = tk.StringVar()
        self.specimen_length_var = tk.StringVar()
        self.ambient_temp_var = tk.StringVar()
        self.case_id_var = tk.StringVar()
        self.investigator_var = tk.StringVar()
        self.verbose_var = tk.BooleanVar()
        self.alternative_methods_var = tk.BooleanVar()
        self.validate_var = tk.BooleanVar()
        
        self.setup_ui()
        self.center_window()
        
    def load_custom_fonts(self):
        """Load custom fonts from the font folder."""
        # Get the project root directory (where the script is located)
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        font_dir = os.path.join(script_dir, 'font')
        
        # Default font settings (fallback)
        self.custom_fonts = {
            'title': tkfont.Font(family='Arial', size=40, weight='bold'),
            'subtitle': tkfont.Font(family='Arial', size=26),
            'label': tkfont.Font(family='Arial', size=22),
            'text': tkfont.Font(family='Consolas', size=24),
            'button': tkfont.Font(family='Arial', size=22)
        }
        
        # Try to load Blackbit.otf font
        blackbit_path = os.path.join(font_dir, 'Blackbit.otf')
        
        try:
            if os.path.exists(blackbit_path):
                # Try to use system font loading mechanisms
                self.font_loaded = False
                
                # Method 1: Try platform-specific font loading
                try:
                    import platform
                    system = platform.system()
                    
                    if system == "Windows":
                        # Windows font loading
                        import ctypes
                        from ctypes import wintypes
                        
                        # Load font temporarily
                        gdi32 = ctypes.windll.gdi32
                        result = gdi32.AddFontResourceW(blackbit_path)
                        if result:
                            self.font_loaded = True
                            print("Font loaded on Windows")
                    
                    elif system == "Darwin":  # macOS
                        # macOS font loading
                        try:
                            import subprocess
                            # Try to activate the font temporarily
                            subprocess.run(['cp', blackbit_path, '/tmp/Blackbit.otf'], check=True)
                            self.font_loaded = True
                            print("Font copied to system temporary directory on macOS")
                        except:
                            pass
                    
                    elif system == "Linux":
                        # Linux font loading
                        try:
                            import subprocess
                            # Try to use fc-cache if available
                            subprocess.run(['fc-cache', '-f'], check=False)
                            self.font_loaded = True
                            print("Font cache refreshed on Linux")
                        except:
                            pass
                            
                except Exception as e:
                    print(f"Platform-specific font loading failed: {e}")
                
                # Check if Blackbit is now available and create font objects
                try:
                    available_families = list(tkfont.families())
                    
                    # Look for Blackbit or similar fonts
                    font_family = 'Arial'  # Default fallback
                    
                    for family in available_families:
                        if 'blackbit' in family.lower() or 'Blackbit' in family:
                            font_family = family
                            self.font_loaded = True
                            break
                    
                    # If we found Blackbit or loaded it, use it
                    if self.font_loaded:
                        self.custom_fonts = {
                            'title': tkfont.Font(family=font_family, size=48, weight='bold'),
                            'subtitle': tkfont.Font(family=font_family, size=28),
                            'label': tkfont.Font(family=font_family, size=24),
                            'text': tkfont.Font(family=font_family, size=24),
                            'button': tkfont.Font(family=font_family, size=22)
                        }
                        print(f"Custom font '{font_family}' applied successfully")
                    else:
                        # Use a monospace font that might be similar to Blackbit
                        mono_family = 'Courier New'
                        for family in available_families:
                            if any(term in family.lower() for term in ['courier', 'mono', 'console', 'terminal']):
                                mono_family = family
                                break
                        
                        self.custom_fonts = {
                            'title': tkfont.Font(family=mono_family, size=40, weight='bold'),
                            'subtitle': tkfont.Font(family=mono_family, size=26),
                            'label': tkfont.Font(family='Arial', size=22),
                            'text': tkfont.Font(family=mono_family, size=24),
                            'button': tkfont.Font(family='Arial', size=22)
                        }
                        print(f"Using monospace font '{mono_family}' as Blackbit alternative")
                        
                except Exception as e:
                    print(f"Font application failed: {e}")
                    
        except Exception as e:
            print(f"Could not load custom font: {e}")
            # Keep default fonts if loading fails
    
    def setup_ui(self):
        """Set up the user interface."""
        # Create main container with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="CALLIPHORIDAYS", 
                               font=self.custom_fonts['title'])
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 5))
        
        subtitle_label = ttk.Label(main_frame, 
                                  text="Forensic Entomology PMI Estimation Tool",
                                  font=self.custom_fonts['subtitle'])
        subtitle_label.grid(row=1, column=0, columnspan=3, pady=(0, 20))
        
        # Create notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        main_frame.rowconfigure(2, weight=1)
        
        # Basic Analysis Tab
        basic_frame = ttk.Frame(notebook, padding="10")
        notebook.add(basic_frame, text="Basic Analysis")
        self.setup_basic_tab(basic_frame)
        
        # Advanced Options Tab
        advanced_frame = ttk.Frame(notebook, padding="10")
        notebook.add(advanced_frame, text="Advanced Options")
        self.setup_advanced_tab(advanced_frame)
        
        # Results Tab
        results_frame = ttk.Frame(notebook, padding="10")
        notebook.add(results_frame, text="Results")
        self.setup_results_tab(results_frame)
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=3, pady=10)
        
        ttk.Button(button_frame, text="Calculate PMI", 
                  command=self.calculate_pmi, style="Accent.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear All", 
                  command=self.clear_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Export Results", 
                  command=self.export_results).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Exit", 
                  command=self.root.quit).pack(side=tk.LEFT, padx=5)
        
    def setup_basic_tab(self, parent):
        """Set up the basic analysis tab."""
        # Species selection
        ttk.Label(parent, text="Species:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10), pady=5)
        species_combo = ttk.Combobox(parent, textvariable=self.species_var, width=40)
        
        # Group species by family
        calliphoridae_species = []
        sarcophagidae_species = []
        
        for species in ForensicSpecies:
            info = get_species_info(species)
            display_name = f"{species.value} ({info['common_name']})"
            if info['family'] == 'Calliphoridae':
                calliphoridae_species.append(display_name)
            else:
                sarcophagidae_species.append(display_name)
        
        all_species = (["--- Calliphoridae (Blow flies) ---"] + calliphoridae_species + 
                      ["--- Sarcophagidae (Flesh flies) ---"] + sarcophagidae_species)
        species_combo['values'] = all_species
        species_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)
        species_combo.bind('<<ComboboxSelected>>', self.on_species_selected)
        
        # Stage selection
        ttk.Label(parent, text="Development Stage:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=5)
        stage_combo = ttk.Combobox(parent, textvariable=self.stage_var, width=40)
        stage_combo['values'] = ['1st_instar (First instar larva)', 
                                '2nd_instar (Second instar larva)',
                                '3rd_instar (Third instar larva)', 
                                'pupa (Pupal stage)']
        stage_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # Location
        ttk.Label(parent, text="Location:").grid(row=2, column=0, sticky=tk.W, padx=(0, 10), pady=5)
        location_entry = ttk.Entry(parent, textvariable=self.location_var, width=43)
        location_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5)
        ttk.Label(parent, text="(City, State/Country)", font=self.custom_fonts['label'], 
                 foreground='gray').grid(row=2, column=2, sticky=tk.W, padx=(5, 0))
        
        # Discovery date
        ttk.Label(parent, text="Discovery Date:").grid(row=3, column=0, sticky=tk.W, padx=(0, 10), pady=5)
        date_frame = ttk.Frame(parent)
        date_frame.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Entry(date_frame, textvariable=self.discovery_date_var, width=20).pack(side=tk.LEFT)
        ttk.Button(date_frame, text="Today", 
                  command=lambda: self.discovery_date_var.set(date.today().strftime('%Y-%m-%d'))).pack(side=tk.LEFT, padx=(5, 0))
        ttk.Label(parent, text="(YYYY-MM-DD)", font=self.custom_fonts['label'], 
                 foreground='gray').grid(row=3, column=2, sticky=tk.W, padx=(5, 0))
        
        # Discovery time (optional)
        ttk.Label(parent, text="Discovery Time:").grid(row=4, column=0, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Entry(parent, textvariable=self.discovery_time_var, width=43).grid(row=4, column=1, sticky=(tk.W, tk.E), pady=5)
        ttk.Label(parent, text="(HH:MM, optional)", font=self.custom_fonts['label'], 
                 foreground='gray').grid(row=4, column=2, sticky=tk.W, padx=(5, 0))
        
        # Specimen length (optional)
        ttk.Label(parent, text="Specimen Length:").grid(row=5, column=0, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Entry(parent, textvariable=self.specimen_length_var, width=43).grid(row=5, column=1, sticky=(tk.W, tk.E), pady=5)
        ttk.Label(parent, text="(mm, optional)", font=self.custom_fonts['label'], 
                 foreground='gray').grid(row=5, column=2, sticky=tk.W, padx=(5, 0))
        
        # Ambient temperature override (optional)
        ttk.Label(parent, text="Ambient Temperature:").grid(row=6, column=0, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Entry(parent, textvariable=self.ambient_temp_var, width=43).grid(row=6, column=1, sticky=(tk.W, tk.E), pady=5)
        ttk.Label(parent, text="(°C, overrides weather)", font=self.custom_fonts['label'], 
                 foreground='gray').grid(row=6, column=2, sticky=tk.W, padx=(5, 0))
        
        # Configure column weights
        parent.columnconfigure(1, weight=1)
        
    def setup_advanced_tab(self, parent):
        """Set up the advanced options tab."""
        # Case information
        case_frame = ttk.LabelFrame(parent, text="Case Information", padding="10")
        case_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(case_frame, text="Case ID:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Entry(case_frame, textvariable=self.case_id_var, width=30).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(case_frame, text="Investigator:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Entry(case_frame, textvariable=self.investigator_var, width=30).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)
        
        case_frame.columnconfigure(1, weight=1)
        
        # Analysis options
        options_frame = ttk.LabelFrame(parent, text="Analysis Options", padding="10")
        options_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Checkbutton(options_frame, text="Verbose output (detailed calculations)", 
                       variable=self.verbose_var).grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Checkbutton(options_frame, text="Use alternative PMI methods", 
                       variable=self.alternative_methods_var).grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Checkbutton(options_frame, text="Detailed validation report", 
                       variable=self.validate_var).grid(row=2, column=0, sticky=tk.W, pady=2)
        
        # API Key configuration
        api_frame = ttk.LabelFrame(parent, text="Weather API Configuration", padding="10")
        api_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        current_key = os.environ.get('OPENWEATHER_API_KEY', '')
        api_status = "✓ Configured" if current_key else "⚠ Not configured (using fallback temperatures)"
        
        ttk.Label(api_frame, text=f"OpenWeather API Status: {api_status}").grid(row=0, column=0, sticky=tk.W, pady=2)
        
        if not current_key:
            ttk.Label(api_frame, text="Set OPENWEATHER_API_KEY environment variable for accurate weather data", 
                     font=self.custom_fonts['label'], foreground='gray').grid(row=1, column=0, sticky=tk.W, pady=2)
        
        # Configure column weights
        parent.columnconfigure(1, weight=1)
        
    def setup_results_tab(self, parent):
        """Set up the results display tab."""
        # Results text area
        self.results_text = scrolledtext.ScrolledText(parent, wrap=tk.WORD, width=80, height=30, 
                                                     font=self.custom_fonts['text'])
        self.results_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Configure text area
        self.results_text.configure(state='disabled')
        
        # Progress bar (hidden by default)
        self.progress_var = tk.StringVar(value="Ready")
        self.progress_label = ttk.Label(parent, textvariable=self.progress_var)
        self.progress_label.grid(row=1, column=0, sticky=tk.W)
        
        self.progress_bar = ttk.Progressbar(parent, mode='indeterminate')
        self.progress_bar.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Configure grid weights
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)
        
    def center_window(self):
        """Center the window on the screen."""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
    def on_species_selected(self, event):
        """Handle species selection to show additional information."""
        selected = self.species_var.get()
        if selected and not selected.startswith('---'):
            species_code = selected.split(' (')[0]
            try:
                species = ForensicSpecies(species_code)
                info = get_species_info(species)
                # Could add a tooltip or status bar with species information
            except ValueError:
                pass
                
    def validate_inputs(self) -> bool:
        """Validate user inputs."""
        if not self.species_var.get() or self.species_var.get().startswith('---'):
            messagebox.showerror("Validation Error", "Please select a species.")
            return False
            
        if not self.stage_var.get():
            messagebox.showerror("Validation Error", "Please select a development stage.")
            return False
            
        if not self.location_var.get():
            messagebox.showerror("Validation Error", "Please enter a location.")
            return False
            
        if not self.discovery_date_var.get():
            messagebox.showerror("Validation Error", "Please enter a discovery date.")
            return False
            
        # Validate date format
        try:
            datetime.strptime(self.discovery_date_var.get(), '%Y-%m-%d')
        except ValueError:
            messagebox.showerror("Validation Error", "Please enter date in YYYY-MM-DD format.")
            return False
            
        # Validate optional numeric fields
        if self.specimen_length_var.get():
            try:
                float(self.specimen_length_var.get())
            except ValueError:
                messagebox.showerror("Validation Error", "Specimen length must be a number.")
                return False
                
        if self.ambient_temp_var.get():
            try:
                float(self.ambient_temp_var.get())
            except ValueError:
                messagebox.showerror("Validation Error", "Ambient temperature must be a number.")
                return False
                
        return True
        
    def calculate_pmi(self):
        """Calculate PMI with user inputs."""
        if not self.validate_inputs():
            return
            
        # Switch to results tab
        notebook = self.root.nametowidget(self.root.winfo_children()[0].winfo_children()[2])
        notebook.select(2)  # Results tab
        
        # Start calculation in thread to prevent UI freezing
        threading.Thread(target=self._calculate_pmi_thread, daemon=True).start()
        
    def _calculate_pmi_thread(self):
        """Calculate PMI in background thread."""
        try:
            # Show progress
            self.root.after(0, lambda: self.progress_var.set("Calculating PMI..."))
            self.root.after(0, lambda: self.progress_bar.start())
            
            # Parse inputs
            species_text = self.species_var.get().split(' (')[0]
            species = ForensicSpecies(species_text)
            
            stage_text = self.stage_var.get().split(' (')[0]
            stage = DevelopmentStage(stage_text)
            
            location = self.location_var.get()
            discovery_date = self.discovery_date_var.get()
            discovery_time = self.discovery_time_var.get() if self.discovery_time_var.get() else None
            specimen_length = float(self.specimen_length_var.get()) if self.specimen_length_var.get() else None
            ambient_temp = float(self.ambient_temp_var.get()) if self.ambient_temp_var.get() else None
            
            # Validate inputs
            validation_result = self.validator.validate_inputs(
                species, stage, location, discovery_date,
                discovery_time, specimen_length, ambient_temp
            )
            
            # Get temperature data
            if ambient_temp is not None:
                temperature_data = {'avg_temp': ambient_temp}
            else:
                self.root.after(0, lambda: self.progress_var.set("Fetching weather data..."))
                temperature_data = self.weather_service.get_temperature_data(location, discovery_date, discovery_time)
            
            # Calculate PMI
            self.root.after(0, lambda: self.progress_var.set("Calculating PMI estimate..."))
            pmi_estimate = self.pmi_calculator.calculate_pmi(
                species=species,
                stage=stage,
                temperature_data=temperature_data,
                specimen_length=specimen_length,
                verbose=self.verbose_var.get()
            )
            
            # Validate results
            validation_result = self.validator.validate_calculation_results(
                pmi_estimate, temperature_data, species, stage
            )
            
            # Calculate alternative methods if requested
            alternative_results = None
            if self.alternative_methods_var.get():
                self.root.after(0, lambda: self.progress_var.set("Calculating alternative methods..."))
                alt_calculator = AlternativePMICalculator()
                alternative_results = alt_calculator.calculate_all_methods(
                    species, stage, temperature_data, specimen_length
                )
            
            # Display results
            self.root.after(0, lambda: self._display_results(
                pmi_estimate, validation_result, alternative_results, 
                species, stage, location, discovery_date, discovery_time, temperature_data
            ))
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Calculation Error", f"Error calculating PMI: {str(e)}"))
        finally:
            self.root.after(0, lambda: self.progress_bar.stop())
            self.root.after(0, lambda: self.progress_var.set("Calculation complete"))
            
    def _display_results(self, pmi_estimate, validation_result, alternative_results, 
                        species, stage, location, discovery_date, discovery_time, temperature_data):
        """Display calculation results in the results tab."""
        # Enable text widget for editing
        self.results_text.configure(state='normal')
        self.results_text.delete(1.0, tk.END)
        
        # Format results
        results = []
        results.append("┏┓┏┓┓ ┓ ┳┓┏┏┓┓┏┏┓┳┓┳┳┓┏┓┓┏┏┓")
        results.append("┃ ┣┫┃ ┃ ┃┣┫┃┃┣┫┃┃┣┫┃┃┃┣┫┗┫┗┓") 
        results.append("┗┛┛┗┗┛┗┛┻┛┗┣┛┛┗┗┛┛┗┻┻┛┛┗┗┛┗┛")
        results.append("                            ")
        results.append("")
        results.append("Forensic Entomology PMI Estimation Tool")
        results.append("Using Calliphoridae & Sarcophagidae Evidence and Temperature Data")
        results.append("=" * 70)
        results.append("")
        
        # Main results
        results.append("=" * 50)
        results.append("POSTMORTEM INTERVAL ESTIMATE")
        results.append("=" * 50)
        results.append(f"Species: {species.value.replace('_', ' ').title()}")
        results.append(f"Development Stage: {stage.value.replace('_', ' ').title()}")
        results.append(f"Location: {location}")
        discovery_datetime = f"{discovery_date}" + (f" {discovery_time}" if discovery_time else "")
        results.append(f"Discovery Date: {discovery_datetime}")
        results.append(f"Estimated PMI: {pmi_estimate['pmi_days']:.1f} days ({pmi_estimate['pmi_hours']:.1f} hours)")
        results.append(f"Confidence Interval: {pmi_estimate['confidence_low']:.1f} - {pmi_estimate['confidence_high']:.1f} days")
        results.append(f"Temperature Used: {temperature_data['avg_temp']:.1f}°C")
        results.append("")
        
        # Data quality
        results.append(f"Data Quality: {validation_result.data_quality.value.upper()} ({validation_result.quality_score:.0f}/100)")
        results.append("")
        
        # Validation warnings
        if validation_result.warnings:
            results.append("Validation Alerts:")
            for warning in validation_result.warnings[:3]:
                results.append(f"  {warning}")
            if len(validation_result.warnings) > 3:
                results.append(f"  ... and {len(validation_result.warnings) - 3} more")
            results.append("")
        
        # Verbose details
        if self.verbose_var.get():
            results.append("Detailed Calculations:")
            results.append(f"Accumulated Degree Days: {pmi_estimate['accumulated_dd']:.1f} ADD")
            results.append(f"Base Temperature: {pmi_estimate['base_temp']:.1f}°C")
            results.append(f"Development Threshold: {pmi_estimate['dev_threshold']:.1f} ADD")
            results.append("")
        
        # Alternative methods results
        if alternative_results:
            results.append("=" * 60)
            results.append("ALTERNATIVE PMI METHODS COMPARISON")
            results.append("=" * 60)
            results.append("")
            results.append("INDIVIDUAL METHOD RESULTS:")
            results.append("-" * 40)
            
            for i, estimate in enumerate(alternative_results.estimates, 1):
                method_name = estimate.method.value.replace('_', ' ').title()
                results.append(f"")
                results.append(f"{i}. {method_name}")
                results.append(f"   PMI Estimate: {estimate.pmi_days:.1f} days ({estimate.pmi_hours:.1f} hours)")
                results.append(f"   Confidence: {estimate.confidence_low:.1f} - {estimate.confidence_high:.1f} days")
                results.append(f"   Reliability: {estimate.reliability_score:.0f}/100")
            
            # Method agreement
            agreement = alternative_results.method_agreement
            results.append("")
            results.append("METHOD AGREEMENT ANALYSIS:")
            results.append("-" * 40)
            results.append(f"Agreement Level: {agreement['agreement_level'].upper()}")
            results.append(f"Coefficient of Variation: {agreement['coefficient_of_variation']:.1f}%")
            results.append(f"PMI Range: {agreement['min_pmi']:.1f} - {agreement['max_pmi']:.1f} days")
            results.append(f"Mean PMI: {agreement['mean_pmi']:.1f} days")
            results.append("")
            
            # Consensus estimate
            consensus = alternative_results.consensus_estimate
            results.append("CONSENSUS ESTIMATE:")
            results.append("-" * 40)
            results.append(f"Method: {consensus['method'].replace('_', ' ').title()}")
            results.append(f"Consensus PMI: {consensus['pmi_days']:.1f} days ({consensus['pmi_hours']:.1f} hours)")
            results.append(f"Combined Confidence: {consensus['confidence_low']:.1f} - {consensus['confidence_high']:.1f} days")
            results.append("")
            
            # Recommendations
            if alternative_results.recommendations:
                results.append("METHOD RECOMMENDATIONS:")
                results.append("-" * 40)
                for i, rec in enumerate(alternative_results.recommendations, 1):
                    results.append(f"{i}. {rec}")
                results.append("")
        
        # Disclaimer
        results.append("WARNING: This is an estimate based on available data.")
        results.append("Results should be interpreted by qualified forensic entomologists.")
        
        # Store results for export
        self.last_results = {
            'pmi_estimate': pmi_estimate,
            'validation_result': validation_result,
            'alternative_results': alternative_results,
            'species': species,
            'stage': stage,
            'location': location,
            'discovery_date': discovery_date,
            'discovery_time': discovery_time,
            'temperature_data': temperature_data,
            'case_info': {
                'case_id': self.case_id_var.get() or f"GUI_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'investigator': self.investigator_var.get() or 'GUI User',
                'specimen_length': float(self.specimen_length_var.get()) if self.specimen_length_var.get() else None,
            }
        }
        
        # Display results
        self.results_text.insert(tk.END, '\n'.join(results))
        self.results_text.configure(state='disabled')
        
    def export_results(self):
        """Export results to file."""
        if not hasattr(self, 'last_results'):
            messagebox.showwarning("Export Warning", "No results to export. Please calculate PMI first.")
            return
            
        # Ask user for export format and location
        file_types = [
            ("PDF Report", "*.pdf"),
            ("JSON files", "*.json"),
            ("CSV files", "*.csv"), 
            ("Text files", "*.txt"),
            ("All files", "*.*")
        ]
        
        filename = filedialog.asksaveasfilename(
            title="Export Results",
            filetypes=file_types,
            defaultextension=".json"
        )
        
        if filename:
            try:
                # Determine format from extension
                if filename.endswith('.pdf'):
                    # Generate professional PDF report
                    try:
                        from .report_generator import create_forensic_report
                        
                        pdf_path = create_forensic_report(
                            pmi_estimate=self.last_results['pmi_estimate'],
                            validation_result=self.last_results['validation_result'],
                            case_info=self.last_results['case_info'],
                            temperature_data=self.last_results['temperature_data'],
                            species=self.last_results['species'],
                            stage=self.last_results['stage'],
                            alternative_results=self.last_results['alternative_results'],
                            output_path=filename
                        )
                        
                        messagebox.showinfo("Export Complete", f"Professional PDF report generated: {pdf_path}")
                        
                    except ImportError as e:
                        messagebox.showerror("Export Error", 
                                           f"PDF generation requires additional dependencies.\n"
                                           f"Please install: pip install reportlab matplotlib pillow\n\n"
                                           f"Error: {str(e)}")
                    except Exception as pdf_error:
                        messagebox.showerror("Export Error", f"PDF generation failed: {str(pdf_error)}")
                        
                elif filename.endswith('.json'):
                    export_format = 'json'
                elif filename.endswith('.csv'):
                    export_format = 'csv'
                else:
                    export_format = 'txt'
                
                if not filename.endswith('.pdf'):
                    # Remove extension for exporter
                    base_filename = filename.rsplit('.', 1)[0]
                    
                    # Export using existing data exporter
                    exported_file = self.exporter.export_case_data(
                        self.last_results['pmi_estimate'],
                        self.last_results['temperature_data'],
                        self.last_results['case_info'],
                        base_filename,
                        export_format
                    )
                    
                    messagebox.showinfo("Export Complete", f"Results exported to: {exported_file}")
                
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export results: {str(e)}")
                
    def clear_all(self):
        """Clear all input fields."""
        self.species_var.set('')
        self.stage_var.set('')
        self.location_var.set('')
        self.discovery_date_var.set('')
        self.discovery_time_var.set('')
        self.specimen_length_var.set('')
        self.ambient_temp_var.set('')
        self.case_id_var.set('')
        self.investigator_var.set('')
        self.verbose_var.set(False)
        self.alternative_methods_var.set(False)
        self.validate_var.set(False)
        
        # Clear results
        self.results_text.configure(state='normal')
        self.results_text.delete(1.0, tk.END)
        self.results_text.configure(state='disabled')
        
        self.progress_var.set("Ready")
        
    def run(self):
        """Run the GUI application."""
        self.root.mainloop()


def main():
    """Main entry point for GUI application."""
    app = CalliphoridaysGUI()
    app.run()


if __name__ == '__main__':
    main()