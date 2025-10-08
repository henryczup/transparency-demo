"""
Transparency Analysis Module for Polymer Film Color Change Detection

Analyzes video frames to measure color/transparency changes in polymer films
that transition from purple to transparent when exposed to E-field.
"""
import cv2
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import json


class TransparencyAnalyzer:
    """Analyzes color/transparency changes in polymer film from video frames"""
    
    def __init__(self, session_dir, config, metadata=None, run_dir=None):
        """
        Initialize the transparency analyzer
        
        Args:
            session_dir: Path to session directory containing frames
            config: Configuration dictionary
            metadata: Optional metadata dict with timing information
            run_dir: Optional path to run directory (for shared ROI across sessions)
        """
        self.session_dir = Path(session_dir)
        self.config = config
        self.metadata = metadata
        self.run_dir = Path(run_dir) if run_dir else None
        self.roi = None
        self.baseline_metrics = None
        self.analysis_results = []
        
    def select_roi_interactive(self, frame):
        """
        Interactive ROI selection using mouse
        
        Args:
            frame: First frame to display for selection
            
        Returns:
            dict: ROI coordinates {x, y, width, height}
        """
        print("\n=== Interactive ROI Selection ===")
        print("Instructions:")
        print("  1. Click and drag to draw a rectangle")
        print("  2. Press ENTER to confirm")
        print("  3. Press 'r' to reset and redraw")
        print("  4. Press ESC to cancel")
        
        # Resize frame for display if too large
        display_height, display_width = frame.shape[:2]
        max_display_height = 900
        max_display_width = 1600
        
        scale = 1.0
        if display_height > max_display_height or display_width > max_display_width:
            scale = min(max_display_height / display_height, max_display_width / display_width)
            display_width = int(display_width * scale)
            display_height = int(display_height * scale)
            display_frame_resized = cv2.resize(frame, (display_width, display_height))
        else:
            display_frame_resized = frame.copy()
        
        # Create a copy for drawing
        display_frame = display_frame_resized.copy()
        roi_selected = False
        roi_coords = None
        
        def mouse_callback(event, x, y, flags, param):
            nonlocal roi_selected, roi_coords, display_frame
            
            if event == cv2.EVENT_LBUTTONDOWN:
                param['drawing'] = True
                param['start_point'] = (x, y)
                
            elif event == cv2.EVENT_MOUSEMOVE:
                if param['drawing']:
                    temp_frame = display_frame_resized.copy()
                    cv2.rectangle(temp_frame, param['start_point'], (x, y), (0, 255, 0), 2)
                    cv2.imshow('Select ROI', temp_frame)
                    
            elif event == cv2.EVENT_LBUTTONUP:
                param['drawing'] = False
                param['end_point'] = (x, y)
                
                # Calculate ROI in display coordinates
                x1, y1 = param['start_point']
                x2, y2 = param['end_point']
                
                # Convert back to original frame coordinates
                roi_coords = {
                    'x': int(min(x1, x2) / scale),
                    'y': int(min(y1, y2) / scale),
                    'width': int(abs(x2 - x1) / scale),
                    'height': int(abs(y2 - y1) / scale)
                }
                
                # Draw final rectangle on display frame
                display_frame = display_frame_resized.copy()
                cv2.rectangle(display_frame, (min(x1, x2), min(y1, y2)),
                            (max(x1, x2), max(y1, y2)),
                            (0, 255, 0), 2)
                cv2.putText(display_frame, "Press ENTER to confirm, 'r' to reset",
                          (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.imshow('Select ROI', display_frame)
        
        # Setup window and callback
        cv2.namedWindow('Select ROI')
        param = {'drawing': False, 'start_point': None, 'end_point': None}
        cv2.setMouseCallback('Select ROI', mouse_callback, param)
        cv2.imshow('Select ROI', display_frame)
        
        while True:
            key = cv2.waitKey(1) & 0xFF
            
            if key == 13:  # ENTER
                if roi_coords and roi_coords['width'] > 0 and roi_coords['height'] > 0:
                    roi_selected = True
                    break
                    
            elif key == ord('r'):  # Reset
                display_frame = display_frame_resized.copy()
                roi_coords = None
                param = {'drawing': False, 'start_point': None, 'end_point': None}
                cv2.imshow('Select ROI', display_frame)
                
            elif key == 27:  # ESC
                break
        
        cv2.destroyAllWindows()
        
        if roi_selected:
            print(f"✓ ROI selected: x={roi_coords['x']}, y={roi_coords['y']}, "
                  f"width={roi_coords['width']}, height={roi_coords['height']}")
            return roi_coords
        else:
            print("✗ ROI selection cancelled")
            return None
    
    def set_roi_from_config(self):
        """Load ROI from configuration"""
        roi_config = self.config['transparency_analysis']['roi_coordinates']
        self.roi = {
            'x': roi_config['x'],
            'y': roi_config['y'],
            'width': roi_config['width'],
            'height': roi_config['height']
        }
        print(f"✓ ROI loaded from config: {self.roi}")
    
    def load_roi_from_run(self):
        """Load ROI from run directory if available"""
        if not self.run_dir:
            return None
        
        roi_file = self.run_dir / "shared_roi.json"
        if roi_file.exists():
            with open(roi_file, 'r') as f:
                roi_data = json.load(f)
                self.roi = roi_data['roi']
                print(f"✓ ROI loaded from run directory: {self.roi}")
                return True
        return False
    
    def save_roi_to_run(self):
        """Save ROI to run directory for reuse across sessions"""
        if not self.run_dir or not self.roi:
            return
        
        roi_file = self.run_dir / "shared_roi.json"
        roi_data = {
            'roi': self.roi,
            'description': 'Shared ROI for all sessions in this run'
        }
        
        with open(roi_file, 'w') as f:
            json.dump(roi_data, f, indent=2)
        
        print(f"✓ ROI saved to run directory for reuse: {roi_file}")
    
    def extract_roi(self, frame):
        """
        Extract ROI region from frame
        
        Args:
            frame: Input frame
            
        Returns:
            numpy.ndarray: ROI region
        """
        x, y, w, h = self.roi['x'], self.roi['y'], self.roi['width'], self.roi['height']
        return frame[y:y+h, x:x+w]
    
    def calculate_color_metrics(self, roi_region):
        """
        Calculate color and transparency metrics for ROI
        
        Args:
            roi_region: ROI region from frame
            
        Returns:
            dict: Metrics including HSV values, purple index, transparency score
        """
        # Convert to HSV
        hsv = cv2.cvtColor(roi_region, cv2.COLOR_BGR2HSV)
        
        # Calculate mean values
        mean_hue = np.mean(hsv[:, :, 0])
        mean_saturation = np.mean(hsv[:, :, 1])
        mean_value = np.mean(hsv[:, :, 2])
        
        # Calculate standard deviations (uniformity)
        std_hue = np.std(hsv[:, :, 0])
        std_saturation = np.std(hsv[:, :, 1])
        std_value = np.std(hsv[:, :, 2])
        
        # RGB metrics
        mean_r = np.mean(roi_region[:, :, 2])
        mean_g = np.mean(roi_region[:, :, 1])
        mean_b = np.mean(roi_region[:, :, 0])
        
        # Purple color index (hue around 270-290 degrees, scaled to 0-180 in OpenCV)
        # Purple in OpenCV HSV is around 135-145 (270-290 / 2)
        purple_hue_center = 140  # Target purple hue
        hue_deviation = np.abs(mean_hue - purple_hue_center)
        purple_index = mean_saturation * (1 - min(hue_deviation / 30, 1))
        
        # Luminance (perceived brightness)
        luminance = 0.299 * mean_r + 0.587 * mean_g + 0.114 * mean_b
        
        metrics = {
            'mean_hue': float(mean_hue),
            'mean_saturation': float(mean_saturation),
            'mean_value': float(mean_value),
            'std_hue': float(std_hue),
            'std_saturation': float(std_saturation),
            'std_value': float(std_value),
            'mean_r': float(mean_r),
            'mean_g': float(mean_g),
            'mean_b': float(mean_b),
            'purple_index': float(purple_index),
            'luminance': float(luminance)
        }
        
        return metrics
    
    def calculate_transparency_score(self, current_metrics):
        """
        Calculate transparency score relative to baseline
        
        Args:
            current_metrics: Current frame metrics
            
        Returns:
            float: Transparency score (0 = opaque purple, 1 = fully transparent)
        """
        if self.baseline_metrics is None:
            return 0.0
        
        # Transparency increases as:
        # - Saturation decreases (color fades)
        # - Brightness increases (more light passes through)
        
        baseline_sat = self.baseline_metrics['mean_saturation']
        current_sat = current_metrics['mean_saturation']
        
        baseline_val = self.baseline_metrics['mean_value']
        current_val = current_metrics['mean_value']
        
        # Saturation change (0 to 1, where 1 = complete desaturation)
        sat_change = (baseline_sat - current_sat) / max(baseline_sat, 1)
        sat_change = np.clip(sat_change, 0, 1)
        
        # Brightness change (0 to 1, where 1 = maximum brightness increase)
        val_change = (current_val - baseline_val) / max(255 - baseline_val, 1)
        val_change = np.clip(val_change, 0, 1)
        
        # Combined transparency score (weighted average)
        transparency_score = 0.6 * sat_change + 0.4 * val_change
        
        return float(transparency_score)
    
    def analyze_frames(self, frames_dir=None):
        """
        Analyze all frames in the session
        
        Args:
            frames_dir: Optional path to frames directory (defaults to session_dir/frames)
        """
        if frames_dir is None:
            frames_dir = self.session_dir / "frames"
        
        if not frames_dir.exists():
            print(f"✗ Frames directory not found: {frames_dir}")
            print("  Run frame extraction first")
            return
        
        # Get sorted list of frame files
        frame_files = sorted(frames_dir.glob("frame_*.jpg")) + sorted(frames_dir.glob("frame_*.png"))
        
        if not frame_files:
            print(f"✗ No frames found in {frames_dir}")
            return
        
        print(f"\n=== Analyzing {len(frame_files)} frames ===")
        
        # Load first frame for ROI selection if needed
        first_frame = cv2.imread(str(frame_files[0]))
        
        if self.roi is None:
            # Try to load ROI from run directory first (shared across sessions)
            if self.load_roi_from_run():
                pass  # ROI loaded successfully
            else:
                # No shared ROI, select based on mode
                roi_mode = self.config['transparency_analysis']['roi_selection_mode']
                
                if roi_mode == 'interactive':
                    self.roi = self.select_roi_interactive(first_frame)
                    if self.roi is None:
                        print("✗ ROI selection failed")
                        return
                    # Save ROI to run directory for subsequent sessions
                    self.save_roi_to_run()
                else:  # config mode
                    self.set_roi_from_config()
                    # Save ROI to run directory for subsequent sessions
                    self.save_roi_to_run()
        
        # Calculate baseline metrics from first N frames
        baseline_frames_count = self.config['transparency_analysis'].get('baseline_frames', 10)
        baseline_frames_count = min(baseline_frames_count, len(frame_files))
        
        if baseline_frames_count > 0:
            print(f"\nCalculating baseline from first {baseline_frames_count} frames...")
            baseline_metrics_list = []
            
            for frame_file in frame_files[:baseline_frames_count]:
                frame = cv2.imread(str(frame_file))
                roi_region = self.extract_roi(frame)
                metrics = self.calculate_color_metrics(roi_region)
                baseline_metrics_list.append(metrics)
            
            # Average baseline metrics
            self.baseline_metrics = {}
            for key in baseline_metrics_list[0].keys():
                self.baseline_metrics[key] = np.mean([m[key] for m in baseline_metrics_list])
            
            print(f"✓ Baseline established:")
            print(f"  Saturation: {self.baseline_metrics['mean_saturation']:.1f}")
            print(f"  Brightness: {self.baseline_metrics['mean_value']:.1f}")
            print(f"  Purple Index: {self.baseline_metrics['purple_index']:.1f}")
        else:
            # No baseline - use first frame as baseline
            print(f"\nNo baseline frames specified - using first frame as reference...")
            first_frame = cv2.imread(str(frame_files[0]))
            roi_region = self.extract_roi(first_frame)
            self.baseline_metrics = self.calculate_color_metrics(roi_region)
            
            print(f"✓ Baseline established from first frame:")
            print(f"  Saturation: {self.baseline_metrics['mean_saturation']:.1f}")
            print(f"  Brightness: {self.baseline_metrics['mean_value']:.1f}")
            print(f"  Purple Index: {self.baseline_metrics['purple_index']:.1f}")
        
        # Analyze all frames
        print(f"\nAnalyzing all frames...")
        self.analysis_results = []
        
        for i, frame_file in enumerate(frame_files):
            frame = cv2.imread(str(frame_file))
            roi_region = self.extract_roi(frame)
            
            # Calculate metrics
            metrics = self.calculate_color_metrics(roi_region)
            transparency_score = self.calculate_transparency_score(metrics)
            
            # Get timestamp if available
            frame_number = int(frame_file.stem.split('_')[1])
            timestamp = None
            
            if self.metadata and 'frame_timestamps' in self.metadata:
                if frame_number < len(self.metadata['frame_timestamps']):
                    timestamp = self.metadata['frame_timestamps'][frame_number]
            
            result = {
                'frame_number': frame_number,
                'timestamp': timestamp,
                'transparency_score': transparency_score,
                **metrics
            }
            
            self.analysis_results.append(result)
            
            # Progress indicator
            if (i + 1) % 50 == 0 or (i + 1) == len(frame_files):
                print(f"  Processed {i + 1}/{len(frame_files)} frames", end='\r')
        
        print(f"\n✓ Analysis complete")
    
    def save_results(self):
        """Save analysis results to CSV and JSON"""
        if not self.analysis_results:
            print("No analysis results to save")
            return
        
        # Create DataFrame
        df = pd.DataFrame(self.analysis_results)
        
        # Save CSV
        csv_path = self.session_dir / "transparency_analysis.csv"
        df.to_csv(csv_path, index=False)
        print(f"✓ Analysis data saved: {csv_path}")
        
        # Calculate summary statistics
        summary = {
            'roi': self.roi,
            'baseline_metrics': self.baseline_metrics,
            'statistics': {
                'max_transparency_score': float(df['transparency_score'].max()),
                'min_transparency_score': float(df['transparency_score'].min()),
                'mean_transparency_score': float(df['transparency_score'].mean()),
                'final_transparency_score': float(df['transparency_score'].iloc[-1]),
                'saturation_change_percent': float(
                    (self.baseline_metrics['mean_saturation'] - df['mean_saturation'].iloc[-1]) / 
                    self.baseline_metrics['mean_saturation'] * 100
                ),
                'brightness_change_percent': float(
                    (df['mean_value'].iloc[-1] - self.baseline_metrics['mean_value']) / 
                    self.baseline_metrics['mean_value'] * 100
                ),
            }
        }
        
        # Add time-to-threshold metrics if timestamps available
        if df['timestamp'].notna().any():
            # Time to 50% transparency
            half_transparent = df[df['transparency_score'] >= 0.5]
            if not half_transparent.empty:
                summary['statistics']['time_to_50_percent_transparency_sec'] = float(
                    half_transparent.iloc[0]['timestamp']
                )
            
            # Time to 90% transparency
            mostly_transparent = df[df['transparency_score'] >= 0.9]
            if not mostly_transparent.empty:
                summary['statistics']['time_to_90_percent_transparency_sec'] = float(
                    mostly_transparent.iloc[0]['timestamp']
                )
        
        # Save JSON summary
        json_path = self.session_dir / "transparency_summary.json"
        with open(json_path, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"✓ Summary saved: {json_path}")
        
        # Print summary
        print("\n=== Transparency Analysis Summary ===")
        print(f"Max transparency score: {summary['statistics']['max_transparency_score']:.3f}")
        print(f"Final transparency score: {summary['statistics']['final_transparency_score']:.3f}")
        print(f"Saturation change: {summary['statistics']['saturation_change_percent']:.1f}%")
        print(f"Brightness change: {summary['statistics']['brightness_change_percent']:.1f}%")
        
        if 'time_to_50_percent_transparency_sec' in summary['statistics']:
            print(f"Time to 50% transparent: {summary['statistics']['time_to_50_percent_transparency_sec']:.3f}s")
        if 'time_to_90_percent_transparency_sec' in summary['statistics']:
            print(f"Time to 90% transparent: {summary['statistics']['time_to_90_percent_transparency_sec']:.3f}s")
    
    def create_visualizations(self):
        """Create plots and annotated frames"""
        if not self.analysis_results:
            print("No analysis results to visualize")
            return
        
        analysis_config = self.config['transparency_analysis']
        
        if not analysis_config.get('visualization', {}).get('create_plots', True):
            print("Visualization disabled in config")
            return
        
        print("\n=== Creating Visualizations ===")
        
        df = pd.DataFrame(self.analysis_results)
        
        # Determine x-axis (timestamp or frame number)
        if df['timestamp'].notna().any():
            x_data = df['timestamp']
            x_label = 'Time (seconds)'
        else:
            x_data = df['frame_number']
            x_label = 'Frame Number'
        
        # Create multi-panel plot
        fig, axes = plt.subplots(3, 1, figsize=(12, 10))
        fig.suptitle('Polymer Film Transparency Analysis', fontsize=16, fontweight='bold')
        
        # Plot 1: Transparency Score
        axes[0].plot(x_data, df['transparency_score'], 'b-', linewidth=2, label='Transparency Score')
        axes[0].axhline(y=0.5, color='r', linestyle='--', alpha=0.5, label='50% Threshold')
        axes[0].axhline(y=0.9, color='orange', linestyle='--', alpha=0.5, label='90% Threshold')
        axes[0].set_ylabel('Transparency Score', fontsize=12)
        axes[0].set_title('Transparency Score Over Time')
        axes[0].grid(True, alpha=0.3)
        axes[0].legend()
        axes[0].set_ylim(-0.05, 1.05)
        
        # Plot 2: Saturation and Brightness
        ax2_twin = axes[1].twinx()
        line1 = axes[1].plot(x_data, df['mean_saturation'], 'purple', linewidth=2, label='Saturation')
        line2 = ax2_twin.plot(x_data, df['mean_value'], 'gold', linewidth=2, label='Brightness')
        axes[1].set_ylabel('Saturation', fontsize=12, color='purple')
        ax2_twin.set_ylabel('Brightness (Value)', fontsize=12, color='gold')
        axes[1].set_title('Color Metrics: Saturation and Brightness')
        axes[1].grid(True, alpha=0.3)
        axes[1].tick_params(axis='y', labelcolor='purple')
        ax2_twin.tick_params(axis='y', labelcolor='gold')
        
        # Combined legend
        lines = line1 + line2
        labels = [l.get_label() for l in lines]
        axes[1].legend(lines, labels, loc='best')
        
        # Plot 3: Purple Index
        axes[2].plot(x_data, df['purple_index'], 'm-', linewidth=2, label='Purple Index')
        axes[2].set_xlabel(x_label, fontsize=12)
        axes[2].set_ylabel('Purple Index', fontsize=12)
        axes[2].set_title('Purple Color Intensity')
        axes[2].grid(True, alpha=0.3)
        axes[2].legend()
        
        # Add GPIO trigger line if available
        if (analysis_config.get('visualization', {}).get('plot_gpio_trigger_line', True) and 
            self.metadata and df['timestamp'].notna().any()):
            
            sync_info = self.metadata.get('synchronization', {})
            if sync_info.get('gpio_trigger_time') and sync_info.get('camera_start_time'):
                trigger_time = sync_info['gpio_trigger_time'] - sync_info['camera_start_time']
                
                for ax in axes:
                    ax.axvline(x=trigger_time, color='red', linestyle='--', 
                             linewidth=2, alpha=0.7, label='GPIO Trigger')
        
        plt.tight_layout()
        
        # Save plot
        plot_path = self.session_dir / "transparency_plot.png"
        plt.savefig(plot_path, dpi=150, bbox_inches='tight')
        print(f"✓ Plot saved: {plot_path}")
        plt.close()
        
        # Create ROI visualization (first and last frame comparison)
        if analysis_config.get('visualization', {}).get('annotate_frames', True):
            self._create_roi_comparison()
    
    def _create_roi_comparison(self):
        """Create side-by-side comparison of first and last frame with ROI overlay"""
        frames_dir = self.session_dir / "frames"
        frame_files = sorted(frames_dir.glob("frame_*.jpg")) + sorted(frames_dir.glob("frame_*.png"))
        
        if len(frame_files) < 2:
            return
        
        # Load first and last frames
        first_frame = cv2.imread(str(frame_files[0]))
        last_frame = cv2.imread(str(frame_files[-1]))
        
        # Draw ROI rectangles
        x, y, w, h = self.roi['x'], self.roi['y'], self.roi['width'], self.roi['height']
        
        cv2.rectangle(first_frame, (x, y), (x + w, y + h), (0, 255, 0), 3)
        cv2.rectangle(last_frame, (x, y), (x + w, y + h), (0, 255, 0), 3)
        
        # Add labels
        cv2.putText(first_frame, "BEFORE (Baseline)", (10, 40), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
        cv2.putText(last_frame, "AFTER (Final)", (10, 40), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
        
        # Add transparency scores
        if self.analysis_results:
            first_score = self.analysis_results[0]['transparency_score']
            last_score = self.analysis_results[-1]['transparency_score']
            
            cv2.putText(first_frame, f"Transparency: {first_score:.2f}", (10, 90), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
            cv2.putText(last_frame, f"Transparency: {last_score:.2f}", (10, 90), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
        
        # Combine side by side
        comparison = np.hstack([first_frame, last_frame])
        
        # Save
        comparison_path = self.session_dir / "roi_visualization.png"
        cv2.imwrite(str(comparison_path), comparison)
        print(f"✓ ROI comparison saved: {comparison_path}")
    
    def run_full_analysis(self):
        """Run complete transparency analysis pipeline"""
        print("\n" + "=" * 60)
        print("TRANSPARENCY ANALYSIS")
        print("=" * 60)
        
        self.analyze_frames()
        self.save_results()
        self.create_visualizations()
        
        print("\n" + "=" * 60)
        print("TRANSPARENCY ANALYSIS COMPLETE")
        print("=" * 60)
