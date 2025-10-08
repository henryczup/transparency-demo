"""
Standalone script to run run-level analysis on existing recording runs
"""
import argparse
import yaml
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.run_analyzer import RunAnalyzer


def load_config(config_path):
    """Load configuration from YAML file"""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def main():
    parser = argparse.ArgumentParser(
        description='Analyze and compare all sessions in a recording run'
    )
    parser.add_argument(
        'run_dir',
        type=str,
        help='Path to run directory (e.g., ./recordings/run_20251007_154637)'
    )
    parser.add_argument(
        '--config',
        type=str,
        default='config.yaml',
        help='Path to configuration file (default: config.yaml)'
    )
    
    args = parser.parse_args()
    
    # Verify run directory exists
    run_dir = Path(args.run_dir)
    if not run_dir.exists():
        print(f"Error: Run directory not found: {run_dir}")
        return
    
    if not run_dir.is_dir():
        print(f"Error: Path is not a directory: {run_dir}")
        return
    
    # Load configuration (optional, can work without it)
    config = None
    if Path(args.config).exists():
        config = load_config(args.config)
    
    # Create analyzer and run
    print(f"\nAnalyzing run: {run_dir}")
    analyzer = RunAnalyzer(run_dir, config)
    analyzer.run_full_analysis()
    
    print(f"\n✓ Analysis complete! Results saved to: {run_dir}")


if __name__ == "__main__":
    main()
