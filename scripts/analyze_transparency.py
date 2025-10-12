"""
Standalone script to run transparency analysis on existing recording sessions
"""
import argparse
import yaml
from pathlib import Path
import json
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.transparency_analyzer import TransparencyAnalyzer


def load_config(config_path):
    """Load configuration from YAML file"""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def load_metadata(session_dir):
    """Load metadata from session directory"""
    metadata_path = Path(session_dir) / "metadata.json"
    if metadata_path.exists():
        with open(metadata_path, 'r') as f:
            return json.load(f)
    return None


def main():
    parser = argparse.ArgumentParser(
        description='Analyze transparency changes in recorded polymer film sessions'
    )
    parser.add_argument(
        'session_dir',
        type=str,
        help='Path to session directory (e.g., ./recordings/run_20251007_152200/session_01_20251007_152205)'
    )
    parser.add_argument(
        '--config',
        type=str,
        default='config.yaml',
        help='Path to configuration file (default: config.yaml)'
    )
    parser.add_argument(
        '--roi-mode',
        type=str,
        choices=['interactive', 'config'],
        help='Override ROI selection mode from config'
    )
    parser.add_argument(
        '--roi',
        type=str,
        help='Specify ROI as "x,y,width,height" (e.g., "500,400,200,200")'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Override ROI mode if specified
    if args.roi_mode:
        config['transparency_analysis']['roi_selection_mode'] = args.roi_mode
    
    # Override ROI coordinates if specified
    if args.roi:
        try:
            x, y, w, h = map(int, args.roi.split(','))
            config['transparency_analysis']['roi_selection_mode'] = 'config'
            config['transparency_analysis']['roi_coordinates'] = {
                'x': x, 'y': y, 'width': w, 'height': h
            }
            print(f"Using ROI from command line: x={x}, y={y}, width={w}, height={h}")
        except ValueError:
            print("Error: ROI must be in format 'x,y,width,height'")
            return
    
    # Verify session directory exists
    session_dir = Path(args.session_dir)
    if not session_dir.exists():
        print(f"Error: Session directory not found: {session_dir}")
        return
    
    # Load metadata
    metadata = load_metadata(session_dir)
    
    # Determine run directory (parent of session directory)
    run_dir = session_dir.parent if session_dir.parent.name.startswith('run_') else None
    
    # Create analyzer with run_dir for shared ROI
    print(f"\nAnalyzing session: {session_dir}")
    analyzer = TransparencyAnalyzer(session_dir, config, metadata, run_dir)
    
    # Run analysis
    analyzer.run_full_analysis()
    
    print(f"\n✓ Analysis complete! Results saved to: {session_dir}")


if __name__ == "__main__":
    main()
