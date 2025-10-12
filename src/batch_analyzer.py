"""
Batch-level Analysis Module
Averages difference frames across all recordings in a batch
"""
import json
import numpy as np
import cv2
from pathlib import Path
from datetime import datetime


class BatchAnalyzer:
    """Analyzes and averages difference frames across all recordings in a batch"""
    
    def __init__(self, batch_dir, config=None):
        """
        Initialize the batch analyzer
        
        Args:
            batch_dir: Path to batch directory containing multiple recordings
            config: Optional configuration dictionary
        """
        self.batch_dir = Path(batch_dir)
        self.config = config or {}
        self.recording_dirs = []
        self.difference_frames = []
    
    def discover_recordings(self):
        """Find all recording directories in the batch"""
        self.recording_dirs = sorted([
            d for d in self.batch_dir.iterdir() 
            if d.is_dir() and d.name.startswith('recording_')
        ])
        
        print(f"\n=== Discovered {len(self.recording_dirs)} recordings ===")
        for i, recording_dir in enumerate(self.recording_dirs, 1):
            print(f"  Recording {i}: {recording_dir.name}")
        
        return len(self.recording_dirs)
    
    def load_difference_frames(self):
        """Load difference frames from each recording"""
        print("\n=== Loading Difference Frames ===")
        
        for recording_dir in self.recording_dirs:
            diff_path = recording_dir / "difference_frame_raw.npy"
            
            if diff_path.exists():
                diff_frame = np.load(str(diff_path))
                self.difference_frames.append(diff_frame)
                print(f"  ✓ Loaded: {recording_dir.name}")
            else:
                print(f"  ✗ Missing difference frame: {recording_dir.name}")
        
        print(f"\n✓ Loaded {len(self.difference_frames)} difference frames")
        return len(self.difference_frames)
    
    def calculate_averaged_difference(self):
        """Calculate the average of all difference frames"""
        if not self.difference_frames:
            print("No difference frames to average")
            return None
        
        print("\n=== Calculating Averaged Difference Frame ===")
        
        # Stack all difference frames and calculate mean
        stacked = np.stack(self.difference_frames, axis=0)
        averaged_diff = np.mean(stacked, axis=0)
        
        print(f"✓ Averaged {len(self.difference_frames)} difference frames")
        print(f"  Noise reduction factor: ~{np.sqrt(len(self.difference_frames)):.2f}x")
        print(f"  Averaged difference range: [{averaged_diff.min():.1f}, {averaged_diff.max():.1f}]")
        
        # Save raw averaged difference
        raw_path = self.batch_dir / "averaged_difference_raw.npy"
        np.save(str(raw_path), averaged_diff)
        print(f"✓ Saved: {raw_path.name}")
        
        # Save visualizations
        self._save_visualizations(averaged_diff)
        
        # Save statistics
        self._save_statistics(averaged_diff)
        
        return averaged_diff
    
    def _save_visualizations(self, averaged_diff):
        """Save various visualizations of the averaged difference"""
        print("\n=== Creating Visualizations ===")
        
        # 1. Visualized difference (shifted to center at gray)
        diff_vis = np.clip(averaged_diff + 127, 0, 255).astype(np.uint8)
        vis_path = self.batch_dir / "averaged_difference_visualized.png"
        cv2.imwrite(str(vis_path), diff_vis)
        print(f"✓ Saved: {vis_path.name}")
        
        # 2. Absolute difference
        diff_abs = np.abs(averaged_diff).astype(np.uint8)
        abs_path = self.batch_dir / "averaged_difference_absolute.png"
        cv2.imwrite(str(abs_path), diff_abs)
        print(f"✓ Saved: {abs_path.name}")
        
        # 3. Heatmap (using absolute values)
        # Normalize to 0-255 for better visualization
        diff_normalized = cv2.normalize(diff_abs, None, 0, 255, cv2.NORM_MINMAX)
        heatmap = cv2.applyColorMap(diff_normalized, cv2.COLORMAP_JET)
        heatmap_path = self.batch_dir / "averaged_difference_heatmap.png"
        cv2.imwrite(str(heatmap_path), heatmap)
        print(f"✓ Saved: {heatmap_path.name}")
        
        # 4. Per-channel analysis
        self._save_channel_analysis(averaged_diff)
    
    def _save_channel_analysis(self, averaged_diff):
        """Save per-channel difference analysis"""
        print("\n=== Analyzing Channels ===")
        
        # Split into B, G, R channels
        b_diff, g_diff, r_diff = cv2.split(averaged_diff)
        
        channels_dir = self.batch_dir / "channel_analysis"
        channels_dir.mkdir(exist_ok=True)
        
        # Save each channel as grayscale
        for name, channel in [('blue', b_diff), ('green', g_diff), ('red', r_diff)]:
            # Visualize (shift to center at gray)
            channel_vis = np.clip(channel + 127, 0, 255).astype(np.uint8)
            path = channels_dir / f"{name}_channel_difference.png"
            cv2.imwrite(str(path), channel_vis)
            
            # Also save absolute
            channel_abs = np.abs(channel).astype(np.uint8)
            path_abs = channels_dir / f"{name}_channel_absolute.png"
            cv2.imwrite(str(path_abs), channel_abs)
            
            print(f"  ✓ {name.capitalize()} channel: [{channel.min():.1f}, {channel.max():.1f}]")
    
    def _save_statistics(self, averaged_diff):
        """Save detailed statistics about the averaged difference"""
        print("\n=== Calculating Statistics ===")
        
        # Overall statistics
        stats = {
            'batch_directory': str(self.batch_dir),
            'analysis_timestamp': datetime.now().isoformat(),
            'num_recordings': len(self.difference_frames),
            'noise_reduction_factor': float(np.sqrt(len(self.difference_frames))),
            'overall_stats': {
                'min': float(averaged_diff.min()),
                'max': float(averaged_diff.max()),
                'mean': float(averaged_diff.mean()),
                'std': float(averaged_diff.std()),
                'median': float(np.median(averaged_diff))
            }
        }
        
        # Per-channel statistics
        b_diff, g_diff, r_diff = cv2.split(averaged_diff)
        
        stats['channel_stats'] = {
            'blue': {
                'min': float(b_diff.min()),
                'max': float(b_diff.max()),
                'mean': float(b_diff.mean()),
                'std': float(b_diff.std())
            },
            'green': {
                'min': float(g_diff.min()),
                'max': float(g_diff.max()),
                'mean': float(g_diff.mean()),
                'std': float(g_diff.std())
            },
            'red': {
                'min': float(r_diff.min()),
                'max': float(r_diff.max()),
                'mean': float(r_diff.mean()),
                'std': float(r_diff.std())
            }
        }
        
        # Save to JSON
        stats_path = self.batch_dir / "batch_analysis.json"
        with open(stats_path, 'w') as f:
            json.dump(stats, f, indent=2)
        
        print(f"✓ Statistics saved: {stats_path.name}")
        
        # Also create human-readable report
        self._create_text_report(stats)
    
    def _create_text_report(self, stats):
        """Create human-readable text report"""
        report_path = self.batch_dir / "batch_report.txt"
        
        with open(report_path, 'w') as f:
            f.write("=" * 70 + "\n")
            f.write("BATCH ANALYSIS REPORT\n")
            f.write("=" * 70 + "\n\n")
            
            f.write(f"Batch Directory: {self.batch_dir}\n")
            f.write(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Number of Recordings: {stats['num_recordings']}\n")
            f.write(f"Noise Reduction Factor: ~{stats['noise_reduction_factor']:.2f}x\n\n")
            
            f.write("-" * 70 + "\n")
            f.write("OVERALL DIFFERENCE STATISTICS\n")
            f.write("-" * 70 + "\n\n")
            
            overall = stats['overall_stats']
            f.write(f"  Mean: {overall['mean']:.2f}\n")
            f.write(f"  Std Dev: {overall['std']:.2f}\n")
            f.write(f"  Median: {overall['median']:.2f}\n")
            f.write(f"  Range: [{overall['min']:.2f}, {overall['max']:.2f}]\n\n")
            
            f.write("-" * 70 + "\n")
            f.write("PER-CHANNEL STATISTICS\n")
            f.write("-" * 70 + "\n\n")
            
            for channel_name in ['blue', 'green', 'red']:
                channel = stats['channel_stats'][channel_name]
                f.write(f"{channel_name.upper()} Channel:\n")
                f.write(f"  Mean: {channel['mean']:.2f}\n")
                f.write(f"  Std Dev: {channel['std']:.2f}\n")
                f.write(f"  Range: [{channel['min']:.2f}, {channel['max']:.2f}]\n\n")
            
            f.write("=" * 70 + "\n")
            f.write("FILES GENERATED\n")
            f.write("=" * 70 + "\n\n")
            f.write("  - averaged_difference_raw.npy           : Raw averaged difference (float32)\n")
            f.write("  - averaged_difference_visualized.png    : Visualized (centered at gray)\n")
            f.write("  - averaged_difference_absolute.png      : Absolute difference\n")
            f.write("  - averaged_difference_heatmap.png       : Heatmap visualization\n")
            f.write("  - channel_analysis/                     : Per-channel analysis\n")
            f.write("  - batch_analysis.json                   : Detailed statistics\n")
            f.write("  - batch_report.txt                      : This report\n\n")
            
            f.write("=" * 70 + "\n")
        
        print(f"✓ Text report saved: {report_path.name}")
    
    def run_full_analysis(self):
        """Execute complete batch-level analysis"""
        print("\n" + "=" * 70)
        print("BATCH-LEVEL ANALYSIS")
        print("=" * 70)
        
        # Discover and load recordings
        num_recordings = self.discover_recordings()
        
        if num_recordings == 0:
            print("\n✗ No recordings found in batch directory")
            return
        
        # Load difference frames
        num_loaded = self.load_difference_frames()
        
        if num_loaded == 0:
            print("\n✗ No difference frames loaded")
            return
        
        # Calculate averaged difference
        averaged_diff = self.calculate_averaged_difference()
        
        if averaged_diff is None:
            print("\n✗ Failed to calculate averaged difference")
            return
        
        print("\n" + "=" * 70)
        print("BATCH-LEVEL ANALYSIS COMPLETE")
        print("=" * 70)
        print(f"\nResults saved to: {self.batch_dir}")
