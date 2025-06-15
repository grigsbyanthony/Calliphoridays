"""
Main CLI entry point with subcommands for single and multi-specimen analysis.
"""
import click
from .cli import main as single_specimen
from .multi_cli import multi_analyze, create_template


@click.group()
@click.version_option(version='0.1.0')
def cli():
    """
    CALLIPHORIDAYS - Forensic Entomology PMI Estimation Tool
    
    Estimate postmortem intervals using blow fly evidence and temperature data.
    
    Commands:
      single     Analyze a single specimen (default)
      multi      Analyze multiple specimens from the same scene
      template   Create a template file for multi-specimen analysis
      gui        Launch graphical user interface
    """
    pass


# GUI command
@click.command()
def gui_command():
    """Launch the graphical user interface."""
    try:
        from .gui import main as gui_main
        gui_main()
    except ImportError as e:
        click.echo(f"Error: Could not launch GUI: {e}")
        click.echo("GUI requires tkinter, which should be included with Python.")
    except Exception as e:
        click.echo(f"Error launching GUI: {e}")

# Add subcommands
cli.add_command(single_specimen, name='single')
cli.add_command(multi_analyze, name='multi')
cli.add_command(create_template, name='template')
cli.add_command(gui_command, name='gui')


if __name__ == '__main__':
    cli()