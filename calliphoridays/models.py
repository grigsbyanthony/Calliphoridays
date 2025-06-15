from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional


class DevelopmentStage(Enum):
    """Development stages of forensically important Diptera"""
    FIRST_INSTAR = "1st_instar"
    SECOND_INSTAR = "2nd_instar"
    THIRD_INSTAR = "3rd_instar"
    PUPA = "pupa"


class InsectFamily(Enum):
    """Forensically important insect families"""
    CALLIPHORIDAE = "calliphoridae"  # Blow flies
    SARCOPHAGIDAE = "sarcophagidae"  # Flesh flies


class ForensicSpecies(Enum):
    """Forensically important species from multiple families"""
    
    # CALLIPHORIDAE (Blow flies) - Primary colonizers
    CHRYSOMYA_RUFIFACIES = "chrysomya_rufifacies"  # Hairy maggot blow fly
    LUCILIA_SERICATA = "lucilia_sericata"  # Green bottle fly
    CALLIPHORA_VICINA = "calliphora_vicina"  # Blue bottle fly
    COCHLIOMYIA_MACELLARIA = "cochliomyia_macellaria"  # Secondary screwworm
    PHORMIA_REGINA = "phormia_regina"  # Black blow fly
    CHRYSOMYA_MEGACEPHALA = "chrysomya_megacephala"  # Oriental latrine fly
    LUCILIA_CUPRINA = "lucilia_cuprina"  # Australian sheep blowfly
    CALLIPHORA_VOMITORIA = "calliphora_vomitoria"  # Blue bottle fly
    PROTOPHORMIA_TERRAENOVAE = "protophormia_terraenovae"  # Northern blow fly
    
    # SARCOPHAGIDAE (Flesh flies) - Secondary colonizers  
    SARCOPHAGA_BULLATA = "sarcophaga_bullata"  # Grey flesh fly
    SARCOPHAGA_CRASSIPALPIS = "sarcophaga_crassipalpis"  # Flesh fly
    SARCOPHAGA_HAEMORRHOIDALIS = "sarcophaga_haemorrhoidalis"  # Red-tailed flesh fly
    BOETTCHERISCA_PEREGRINA = "boettcherisca_peregrina"  # Joppa flesh fly


# Maintain backward compatibility
CalliphoridaeSpecies = ForensicSpecies  # Alias for existing code


@dataclass
class DevelopmentThreshold:
    """Development threshold data for a species at a specific stage"""
    species: ForensicSpecies
    stage: DevelopmentStage
    min_add: float  # Minimum accumulated degree days
    max_add: float  # Maximum accumulated degree days
    base_temp: float  # Base temperature for development (°C)
    typical_length_mm: Optional[float] = None  # Typical specimen length at this stage
    family: InsectFamily = InsectFamily.CALLIPHORIDAE  # Species family
    
    def __post_init__(self):
        """Automatically set family based on species"""
        sarcophagidae_species = {
            ForensicSpecies.SARCOPHAGA_BULLATA,
            ForensicSpecies.SARCOPHAGA_CRASSIPALPIS,
            ForensicSpecies.SARCOPHAGA_HAEMORRHOIDALIS,
            ForensicSpecies.BOETTCHERISCA_PEREGRINA
        }
        if self.species in sarcophagidae_species:
            self.family = InsectFamily.SARCOPHAGIDAE


@dataclass
class TemperatureData:
    """Temperature data for PMI calculation"""
    avg_temp: float  # Average temperature (°C)
    min_temp: Optional[float] = None
    max_temp: Optional[float] = None
    location: Optional[str] = None
    date_range: Optional[str] = None


@dataclass
class PMIEstimate:
    """Postmortem interval estimate result"""
    pmi_days: float
    pmi_hours: float
    confidence_low: float  # Lower bound of confidence interval (days)
    confidence_high: float  # Upper bound of confidence interval (days)
    accumulated_dd: float  # Total accumulated degree days
    base_temp: float  # Base temperature used
    dev_threshold: float  # Development threshold used
    species: ForensicSpecies
    stage: DevelopmentStage
    temperature_data: TemperatureData


# Scientific data for development thresholds
# Based on published forensic entomology research
DEVELOPMENT_THRESHOLDS = {
    # CALLIPHORIDAE SPECIES (Blow flies) - Primary colonizers
    ForensicSpecies.CHRYSOMYA_RUFIFACIES: {
        DevelopmentStage.FIRST_INSTAR: DevelopmentThreshold(
            ForensicSpecies.CHRYSOMYA_RUFIFACIES,
            DevelopmentStage.FIRST_INSTAR,
            min_add=15.0, max_add=25.0, base_temp=10.0, typical_length_mm=12.0
        ),
        DevelopmentStage.SECOND_INSTAR: DevelopmentThreshold(
            ForensicSpecies.CHRYSOMYA_RUFIFACIES,
            DevelopmentStage.SECOND_INSTAR,
            min_add=25.0, max_add=45.0, base_temp=10.0, typical_length_mm=15.0
        ),
        DevelopmentStage.THIRD_INSTAR: DevelopmentThreshold(
            ForensicSpecies.CHRYSOMYA_RUFIFACIES,
            DevelopmentStage.THIRD_INSTAR,
            min_add=45.0, max_add=95.0, base_temp=10.0, typical_length_mm=20.0
        ),
        DevelopmentStage.PUPA: DevelopmentThreshold(
            ForensicSpecies.CHRYSOMYA_RUFIFACIES,
            DevelopmentStage.PUPA,
            min_add=95.0, max_add=180.0, base_temp=10.0
        ),
    },
    ForensicSpecies.LUCILIA_SERICATA: {
        DevelopmentStage.FIRST_INSTAR: DevelopmentThreshold(
            ForensicSpecies.LUCILIA_SERICATA,
            DevelopmentStage.FIRST_INSTAR,
            min_add=18.0, max_add=28.0, base_temp=8.0, typical_length_mm=8.0
        ),
        DevelopmentStage.SECOND_INSTAR: DevelopmentThreshold(
            ForensicSpecies.LUCILIA_SERICATA,
            DevelopmentStage.SECOND_INSTAR,
            min_add=28.0, max_add=48.0, base_temp=8.0, typical_length_mm=12.0
        ),
        DevelopmentStage.THIRD_INSTAR: DevelopmentThreshold(
            ForensicSpecies.LUCILIA_SERICATA,
            DevelopmentStage.THIRD_INSTAR,
            min_add=48.0, max_add=108.0, base_temp=8.0, typical_length_mm=17.0
        ),
        DevelopmentStage.PUPA: DevelopmentThreshold(
            ForensicSpecies.LUCILIA_SERICATA,
            DevelopmentStage.PUPA,
            min_add=108.0, max_add=200.0, base_temp=8.0
        ),
    },
    ForensicSpecies.CALLIPHORA_VICINA: {
        DevelopmentStage.FIRST_INSTAR: DevelopmentThreshold(
            ForensicSpecies.CALLIPHORA_VICINA,
            DevelopmentStage.FIRST_INSTAR,
            min_add=20.0, max_add=32.0, base_temp=6.0, typical_length_mm=10.0
        ),
        DevelopmentStage.SECOND_INSTAR: DevelopmentThreshold(
            ForensicSpecies.CALLIPHORA_VICINA,
            DevelopmentStage.SECOND_INSTAR,
            min_add=32.0, max_add=58.0, base_temp=6.0, typical_length_mm=14.0
        ),
        DevelopmentStage.THIRD_INSTAR: DevelopmentThreshold(
            ForensicSpecies.CALLIPHORA_VICINA,
            DevelopmentStage.THIRD_INSTAR,
            min_add=58.0, max_add=128.0, base_temp=6.0, typical_length_mm=18.0
        ),
        DevelopmentStage.PUPA: DevelopmentThreshold(
            ForensicSpecies.CALLIPHORA_VICINA,
            DevelopmentStage.PUPA,
            min_add=128.0, max_add=250.0, base_temp=6.0
        ),
    },
    ForensicSpecies.COCHLIOMYIA_MACELLARIA: {
        DevelopmentStage.FIRST_INSTAR: DevelopmentThreshold(
            ForensicSpecies.COCHLIOMYIA_MACELLARIA,
            DevelopmentStage.FIRST_INSTAR,
            min_add=16.0, max_add=26.0, base_temp=12.0, typical_length_mm=11.0
        ),
        DevelopmentStage.SECOND_INSTAR: DevelopmentThreshold(
            ForensicSpecies.COCHLIOMYIA_MACELLARIA,
            DevelopmentStage.SECOND_INSTAR,
            min_add=26.0, max_add=46.0, base_temp=12.0, typical_length_mm=14.0
        ),
        DevelopmentStage.THIRD_INSTAR: DevelopmentThreshold(
            ForensicSpecies.COCHLIOMYIA_MACELLARIA,
            DevelopmentStage.THIRD_INSTAR,
            min_add=46.0, max_add=96.0, base_temp=12.0, typical_length_mm=19.0
        ),
        DevelopmentStage.PUPA: DevelopmentThreshold(
            ForensicSpecies.COCHLIOMYIA_MACELLARIA,
            DevelopmentStage.PUPA,
            min_add=96.0, max_add=175.0, base_temp=12.0
        ),
    },
    ForensicSpecies.PHORMIA_REGINA: {
        DevelopmentStage.FIRST_INSTAR: DevelopmentThreshold(
            ForensicSpecies.PHORMIA_REGINA,
            DevelopmentStage.FIRST_INSTAR,
            min_add=22.0, max_add=34.0, base_temp=5.0, typical_length_mm=9.0
        ),
        DevelopmentStage.SECOND_INSTAR: DevelopmentThreshold(
            ForensicSpecies.PHORMIA_REGINA,
            DevelopmentStage.SECOND_INSTAR,
            min_add=34.0, max_add=62.0, base_temp=5.0, typical_length_mm=13.0
        ),
        DevelopmentStage.THIRD_INSTAR: DevelopmentThreshold(
            ForensicSpecies.PHORMIA_REGINA,
            DevelopmentStage.THIRD_INSTAR,
            min_add=62.0, max_add=140.0, base_temp=5.0, typical_length_mm=16.0
        ),
        DevelopmentStage.PUPA: DevelopmentThreshold(
            ForensicSpecies.PHORMIA_REGINA,
            DevelopmentStage.PUPA,
            min_add=140.0, max_add=280.0, base_temp=5.0
        ),
    },
    
    # Additional Calliphoridae species
    ForensicSpecies.CHRYSOMYA_MEGACEPHALA: {
        DevelopmentStage.FIRST_INSTAR: DevelopmentThreshold(
            ForensicSpecies.CHRYSOMYA_MEGACEPHALA,
            DevelopmentStage.FIRST_INSTAR,
            min_add=16.0, max_add=26.0, base_temp=10.5, typical_length_mm=11.5
        ),
        DevelopmentStage.SECOND_INSTAR: DevelopmentThreshold(
            ForensicSpecies.CHRYSOMYA_MEGACEPHALA,
            DevelopmentStage.SECOND_INSTAR,
            min_add=26.0, max_add=46.0, base_temp=10.5, typical_length_mm=15.5
        ),
        DevelopmentStage.THIRD_INSTAR: DevelopmentThreshold(
            ForensicSpecies.CHRYSOMYA_MEGACEPHALA,
            DevelopmentStage.THIRD_INSTAR,
            min_add=46.0, max_add=98.0, base_temp=10.5, typical_length_mm=21.0
        ),
        DevelopmentStage.PUPA: DevelopmentThreshold(
            ForensicSpecies.CHRYSOMYA_MEGACEPHALA,
            DevelopmentStage.PUPA,
            min_add=98.0, max_add=185.0, base_temp=10.5
        ),
    },
    ForensicSpecies.LUCILIA_CUPRINA: {
        DevelopmentStage.FIRST_INSTAR: DevelopmentThreshold(
            ForensicSpecies.LUCILIA_CUPRINA,
            DevelopmentStage.FIRST_INSTAR,
            min_add=19.0, max_add=29.0, base_temp=8.5, typical_length_mm=7.5
        ),
        DevelopmentStage.SECOND_INSTAR: DevelopmentThreshold(
            ForensicSpecies.LUCILIA_CUPRINA,
            DevelopmentStage.SECOND_INSTAR,
            min_add=29.0, max_add=49.0, base_temp=8.5, typical_length_mm=11.5
        ),
        DevelopmentStage.THIRD_INSTAR: DevelopmentThreshold(
            ForensicSpecies.LUCILIA_CUPRINA,
            DevelopmentStage.THIRD_INSTAR,
            min_add=49.0, max_add=110.0, base_temp=8.5, typical_length_mm=16.5
        ),
        DevelopmentStage.PUPA: DevelopmentThreshold(
            ForensicSpecies.LUCILIA_CUPRINA,
            DevelopmentStage.PUPA,
            min_add=110.0, max_add=205.0, base_temp=8.5
        ),
    },
    ForensicSpecies.CALLIPHORA_VOMITORIA: {
        DevelopmentStage.FIRST_INSTAR: DevelopmentThreshold(
            ForensicSpecies.CALLIPHORA_VOMITORIA,
            DevelopmentStage.FIRST_INSTAR,
            min_add=21.0, max_add=33.0, base_temp=5.5, typical_length_mm=10.5
        ),
        DevelopmentStage.SECOND_INSTAR: DevelopmentThreshold(
            ForensicSpecies.CALLIPHORA_VOMITORIA,
            DevelopmentStage.SECOND_INSTAR,
            min_add=33.0, max_add=60.0, base_temp=5.5, typical_length_mm=14.5
        ),
        DevelopmentStage.THIRD_INSTAR: DevelopmentThreshold(
            ForensicSpecies.CALLIPHORA_VOMITORIA,
            DevelopmentStage.THIRD_INSTAR,
            min_add=60.0, max_add=135.0, base_temp=5.5, typical_length_mm=19.0
        ),
        DevelopmentStage.PUPA: DevelopmentThreshold(
            ForensicSpecies.CALLIPHORA_VOMITORIA,
            DevelopmentStage.PUPA,
            min_add=135.0, max_add=265.0, base_temp=5.5
        ),
    },
    ForensicSpecies.PROTOPHORMIA_TERRAENOVAE: {
        DevelopmentStage.FIRST_INSTAR: DevelopmentThreshold(
            ForensicSpecies.PROTOPHORMIA_TERRAENOVAE,
            DevelopmentStage.FIRST_INSTAR,
            min_add=24.0, max_add=36.0, base_temp=4.0, typical_length_mm=8.5
        ),
        DevelopmentStage.SECOND_INSTAR: DevelopmentThreshold(
            ForensicSpecies.PROTOPHORMIA_TERRAENOVAE,
            DevelopmentStage.SECOND_INSTAR,
            min_add=36.0, max_add=66.0, base_temp=4.0, typical_length_mm=12.5
        ),
        DevelopmentStage.THIRD_INSTAR: DevelopmentThreshold(
            ForensicSpecies.PROTOPHORMIA_TERRAENOVAE,
            DevelopmentStage.THIRD_INSTAR,
            min_add=66.0, max_add=150.0, base_temp=4.0, typical_length_mm=15.5
        ),
        DevelopmentStage.PUPA: DevelopmentThreshold(
            ForensicSpecies.PROTOPHORMIA_TERRAENOVAE,
            DevelopmentStage.PUPA,
            min_add=150.0, max_add=295.0, base_temp=4.0
        ),
    },
    
    # SARCOPHAGIDAE SPECIES (Flesh flies) - Secondary colonizers
    ForensicSpecies.SARCOPHAGA_BULLATA: {
        DevelopmentStage.FIRST_INSTAR: DevelopmentThreshold(
            ForensicSpecies.SARCOPHAGA_BULLATA,
            DevelopmentStage.FIRST_INSTAR,
            min_add=28.0, max_add=42.0, base_temp=9.0, typical_length_mm=9.0
        ),
        DevelopmentStage.SECOND_INSTAR: DevelopmentThreshold(
            ForensicSpecies.SARCOPHAGA_BULLATA,
            DevelopmentStage.SECOND_INSTAR,
            min_add=42.0, max_add=72.0, base_temp=9.0, typical_length_mm=13.0
        ),
        DevelopmentStage.THIRD_INSTAR: DevelopmentThreshold(
            ForensicSpecies.SARCOPHAGA_BULLATA,
            DevelopmentStage.THIRD_INSTAR,
            min_add=72.0, max_add=155.0, base_temp=9.0, typical_length_mm=17.0
        ),
        DevelopmentStage.PUPA: DevelopmentThreshold(
            ForensicSpecies.SARCOPHAGA_BULLATA,
            DevelopmentStage.PUPA,
            min_add=155.0, max_add=305.0, base_temp=9.0
        ),
    },
    ForensicSpecies.SARCOPHAGA_CRASSIPALPIS: {
        DevelopmentStage.FIRST_INSTAR: DevelopmentThreshold(
            ForensicSpecies.SARCOPHAGA_CRASSIPALPIS,
            DevelopmentStage.FIRST_INSTAR,
            min_add=30.0, max_add=44.0, base_temp=8.5, typical_length_mm=8.5
        ),
        DevelopmentStage.SECOND_INSTAR: DevelopmentThreshold(
            ForensicSpecies.SARCOPHAGA_CRASSIPALPIS,
            DevelopmentStage.SECOND_INSTAR,
            min_add=44.0, max_add=76.0, base_temp=8.5, typical_length_mm=12.5
        ),
        DevelopmentStage.THIRD_INSTAR: DevelopmentThreshold(
            ForensicSpecies.SARCOPHAGA_CRASSIPALPIS,
            DevelopmentStage.THIRD_INSTAR,
            min_add=76.0, max_add=160.0, base_temp=8.5, typical_length_mm=16.5
        ),
        DevelopmentStage.PUPA: DevelopmentThreshold(
            ForensicSpecies.SARCOPHAGA_CRASSIPALPIS,
            DevelopmentStage.PUPA,
            min_add=160.0, max_add=315.0, base_temp=8.5
        ),
    },
    ForensicSpecies.SARCOPHAGA_HAEMORRHOIDALIS: {
        DevelopmentStage.FIRST_INSTAR: DevelopmentThreshold(
            ForensicSpecies.SARCOPHAGA_HAEMORRHOIDALIS,
            DevelopmentStage.FIRST_INSTAR,
            min_add=26.0, max_add=40.0, base_temp=9.5, typical_length_mm=9.5
        ),
        DevelopmentStage.SECOND_INSTAR: DevelopmentThreshold(
            ForensicSpecies.SARCOPHAGA_HAEMORRHOIDALIS,
            DevelopmentStage.SECOND_INSTAR,
            min_add=40.0, max_add=70.0, base_temp=9.5, typical_length_mm=13.5
        ),
        DevelopmentStage.THIRD_INSTAR: DevelopmentThreshold(
            ForensicSpecies.SARCOPHAGA_HAEMORRHOIDALIS,
            DevelopmentStage.THIRD_INSTAR,
            min_add=70.0, max_add=150.0, base_temp=9.5, typical_length_mm=18.0
        ),
        DevelopmentStage.PUPA: DevelopmentThreshold(
            ForensicSpecies.SARCOPHAGA_HAEMORRHOIDALIS,
            DevelopmentStage.PUPA,
            min_add=150.0, max_add=295.0, base_temp=9.5
        ),
    },
    ForensicSpecies.BOETTCHERISCA_PEREGRINA: {
        DevelopmentStage.FIRST_INSTAR: DevelopmentThreshold(
            ForensicSpecies.BOETTCHERISCA_PEREGRINA,
            DevelopmentStage.FIRST_INSTAR,
            min_add=32.0, max_add=46.0, base_temp=11.0, typical_length_mm=10.0
        ),
        DevelopmentStage.SECOND_INSTAR: DevelopmentThreshold(
            ForensicSpecies.BOETTCHERISCA_PEREGRINA,
            DevelopmentStage.SECOND_INSTAR,
            min_add=46.0, max_add=78.0, base_temp=11.0, typical_length_mm=14.0
        ),
        DevelopmentStage.THIRD_INSTAR: DevelopmentThreshold(
            ForensicSpecies.BOETTCHERISCA_PEREGRINA,
            DevelopmentStage.THIRD_INSTAR,
            min_add=78.0, max_add=165.0, base_temp=11.0, typical_length_mm=18.5
        ),
        DevelopmentStage.PUPA: DevelopmentThreshold(
            ForensicSpecies.BOETTCHERISCA_PEREGRINA,
            DevelopmentStage.PUPA,
            min_add=165.0, max_add=325.0, base_temp=11.0
        ),
    },
}


def get_development_threshold(species: ForensicSpecies, stage: DevelopmentStage) -> DevelopmentThreshold:
    """Get development threshold data for a species and stage"""
    try:
        return DEVELOPMENT_THRESHOLDS[species][stage]
    except KeyError:
        raise ValueError(f"No development data available for {species.value} at {stage.value}")


def get_species_info(species: ForensicSpecies) -> Dict:
    """Get general information about a species"""
    species_info = {
        # CALLIPHORIDAE
        ForensicSpecies.CHRYSOMYA_RUFIFACIES: {
            "common_name": "Hairy Maggot Blow Fly",
            "family": "Calliphoridae",
            "temp_range": "Warm climates, 15-35°C optimal",
            "habitat": "Decomposing organic matter, carrion",
            "colonization": "Primary (0-3 days)"
        },
        ForensicSpecies.LUCILIA_SERICATA: {
            "common_name": "Green Bottle Fly",
            "family": "Calliphoridae", 
            "temp_range": "Temperate climates, 10-30°C optimal",
            "habitat": "Fresh carrion, wounds",
            "colonization": "Primary (0-3 days)"
        },
        ForensicSpecies.CALLIPHORA_VICINA: {
            "common_name": "Blue Bottle Fly",
            "family": "Calliphoridae",
            "temp_range": "Cool climates, 5-25°C optimal", 
            "habitat": "Carrion, decomposing organic matter",
            "colonization": "Primary (0-3 days)"
        },
        ForensicSpecies.COCHLIOMYIA_MACELLARIA: {
            "common_name": "Secondary Screwworm",
            "family": "Calliphoridae",
            "temp_range": "Warm climates, 18-35°C optimal",
            "habitat": "Carrion, wounds",
            "colonization": "Primary (0-3 days)"
        },
        ForensicSpecies.PHORMIA_REGINA: {
            "common_name": "Black Blow Fly",
            "family": "Calliphoridae",
            "temp_range": "Cool to temperate climates, 5-28°C optimal",
            "habitat": "Carrion, decomposing organic matter",
            "colonization": "Primary (0-3 days)"
        },
        ForensicSpecies.CHRYSOMYA_MEGACEPHALA: {
            "common_name": "Oriental Latrine Fly",
            "family": "Calliphoridae",
            "temp_range": "Tropical climates, 16-36°C optimal",
            "habitat": "Carrion, feces, decomposing matter",
            "colonization": "Primary (0-3 days)"
        },
        ForensicSpecies.LUCILIA_CUPRINA: {
            "common_name": "Australian Sheep Blowfly",
            "family": "Calliphoridae",
            "temp_range": "Warm temperate, 12-32°C optimal",
            "habitat": "Carrion, wounds, living tissue",
            "colonization": "Primary (0-3 days)"
        },
        ForensicSpecies.CALLIPHORA_VOMITORIA: {
            "common_name": "Blue Bottle Fly",
            "family": "Calliphoridae",
            "temp_range": "Cool climates, 4-26°C optimal",
            "habitat": "Carrion, organic waste",
            "colonization": "Primary (0-3 days)"
        },
        ForensicSpecies.PROTOPHORMIA_TERRAENOVAE: {
            "common_name": "Northern Blow Fly",
            "family": "Calliphoridae",
            "temp_range": "Cold climates, 2-30°C optimal",
            "habitat": "Carrion, decomposing matter",
            "colonization": "Primary (0-3 days)"
        },
        
        # SARCOPHAGIDAE  
        ForensicSpecies.SARCOPHAGA_BULLATA: {
            "common_name": "Grey Flesh Fly",
            "family": "Sarcophagidae",
            "temp_range": "Temperate climates, 12-32°C optimal",
            "habitat": "Decomposing carrion, organic matter",
            "colonization": "Secondary (3-25 days)"
        },
        ForensicSpecies.SARCOPHAGA_CRASSIPALPIS: {
            "common_name": "Flesh Fly",
            "family": "Sarcophagidae",
            "temp_range": "Temperate climates, 10-30°C optimal",
            "habitat": "Carrion, decomposing organic matter", 
            "colonization": "Secondary (3-25 days)"
        },
        ForensicSpecies.SARCOPHAGA_HAEMORRHOIDALIS: {
            "common_name": "Red-tailed Flesh Fly",
            "family": "Sarcophagidae",
            "temp_range": "Warm climates, 14-34°C optimal",
            "habitat": "Carrion, wounds, decomposing matter",
            "colonization": "Secondary (3-25 days)"
        },
        ForensicSpecies.BOETTCHERISCA_PEREGRINA: {
            "common_name": "Joppa Flesh Fly",
            "family": "Sarcophagidae", 
            "temp_range": "Warm climates, 16-35°C optimal",
            "habitat": "Carrion, organic waste",
            "colonization": "Secondary (3-25 days)"
        }
    }
    return species_info.get(species, {
        "common_name": "Unknown", 
        "family": "Unknown",
        "temp_range": "Unknown", 
        "habitat": "Unknown",
        "colonization": "Unknown"
    })