"""
Run-level Analysis Module for Multi-Session Transparency Experiments

Aggregates and compares transparency analysis results across all sessions in a run.
"""
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime
import cv2


class RunAnalyzer:
    """Analyzes and compares transparency data across all sessions in a run"""
    
    def __init__(self, run_dir, config=None):
        """
        Initialize the run analyzer
        
        Args:
            run_dir: Path to run directory containing multiple sessions
            config: Optional configuration dictionary
        """
        self.run_dir = Path(run_dir)
        self.config = config or {}
        self.session_dirs = []
        self.session_summaries = []
        self.session_data = []
        self.run_metrics = {}
        
    def discover_sessions(self):
        """Find all session directories in the run"""
        self.session_dirs = sorted([
            d for d in self.run_dir.iterdir() 
            if d.is_dir() and d.name.startswith('session_')
        ])
        
        print(f"\n=== Discovered {len(self.session_dirs)} sessions ===")
        for i, session_dir in enumerate(self.session_dirs, 1):
            print(f"  Session {i}: {session_dir.name}")
        
        return len(self.session_dirs)
    
    def load_session_summaries(self):
        """Load transparency_summary.json from each session"""
        print("\n=== Loading Session Summaries ===")
        
        for session_dir in self.session_dirs:
            summary_path = session_dir / "transparency_summary.json"
            
            if summary_path.exists():
                with open(summary_path, 'r') as f:
                    summary = json.load(f)
                    summary['session_dir'] = str(session_dir)
                    summary['session_name'] = session_dir.name
                    self.session_summaries.append(summary)
                    print(f"  ✓ Loaded: {session_dir.name}")
            else:
                print(f"  ✗ Missing summary: {session_dir.name}")
        
        print(f"\n✓ Loaded {len(self.session_summaries)} session summaries")
    
    def load_session_timeseries(self):
        """Load transparency_analysis.csv from each session"""
        print("\n=== Loading Session Time-Series Data ===")
        
        for session_dir in self.session_dirs:
            csv_path = session_dir / "transparency_analysis.csv"
            
            if csv_path.exists():
                df = pd.read_csv(csv_path)
                df['session_name'] = session_dir.name
                self.session_data.append(df)
                print(f"  ✓ Loaded: {session_dir.name} ({len(df)} frames)")
            else:
                print(f"  ✗ Missing data: {session_dir.name}")
        
        print(f"\n✓ Loaded {len(self.session_data)} session datasets")
    
    def calculate_run_metrics(self):
        """Calculate aggregated metrics across all sessions"""
        print("\n=== Calculating Run-Level Metrics ===")
        
        if not self.session_summaries:
            print("No session summaries available")
            return
        
        # Extract key metrics from each session
        session_metrics = []
        
        for i, summary in enumerate(self.session_summaries, 1):
            stats = summary.get('statistics', {})
            
            metrics = {
                'session_number': i,
                'session_name': summary['session_name'],
                'max_transparency': stats.get('max_transparency_score', 0),
                'final_transparency': stats.get('final_transparency_score', 0),
                'mean_transparency': stats.get('mean_transparency_score', 0),
                'saturation_change_pct': stats.get('saturation_change_percent', 0),
                'brightness_change_pct': stats.get('brightness_change_percent', 0),
                'time_to_50_pct': stats.get('time_to_50_percent_transparency_sec', None),
                'time_to_90_pct': stats.get('time_to_90_percent_transparency_sec', None),
            }
            
            session_metrics.append(metrics)
        
        # Convert to DataFrame for easy analysis
        df = pd.DataFrame(session_metrics)
        
        # Calculate aggregated statistics
        self.run_metrics = {
            'total_sessions': len(session_metrics),
            'roi': self.session_summaries[0].get('roi', {}),
            'session_metrics': session_metrics,
            'aggregated_statistics': {
                'max_transparency': {
                    'mean': float(df['max_transparency'].mean()),
                    'std': float(df['max_transparency'].std()),
                    'min': float(df['max_transparency'].min()),
                    'max': float(df['max_transparency'].max()),
                },
                'final_transparency': {
                    'mean': float(df['final_transparency'].mean()),
                    'std': float(df['final_transparency'].std()),
                    'min': float(df['final_transparency'].min()),
                    'max': float(df['final_transparency'].max()),
                },
                'saturation_change': {
                    'mean': float(df['saturation_change_pct'].mean()),
                    'std': float(df['saturation_change_pct'].std()),
                },
                'brightness_change': {
                    'mean': float(df['brightness_change_pct'].mean()),
                    'std': float(df['brightness_change_pct'].std()),
                },
            }
        }
        
        # Calculate trends
        if len(session_metrics) > 1:
            # Linear regression for trend detection
            x = np.arange(len(session_metrics))
            y_max = df['max_transparency'].values
            
            # Simple linear fit
            coeffs = np.polyfit(x, y_max, 1)
            slope = coeffs[0]
            
            self.run_metrics['trends'] = {
                'max_transparency_trend': 'increasing' if slope > 0.01 else 'decreasing' if slope < -0.01 else 'stable',
                'max_transparency_slope': float(slope),
                'degradation_detected': bool(slope < -0.05),
                'improvement_detected': bool(slope > 0.05),
            }
        
        # Calculate consistency score (inverse of coefficient of variation)
        cv = df['max_transparency'].std() / df['max_transparency'].mean() if df['max_transparency'].mean() > 0 else 1
        consistency_score = max(0, 1 - cv)
        self.run_metrics['consistency_score'] = float(consistency_score)
        
        print(f"✓ Run metrics calculated")
        print(f"  Total sessions: {self.run_metrics['total_sessions']}")
        print(f"  Mean max transparency: {self.run_metrics['aggregated_statistics']['max_transparency']['mean']:.3f}")
        print(f"  Consistency score: {self.run_metrics['consistency_score']:.3f}")
        
        if 'trends' in self.run_metrics:
            print(f"  Trend: {self.run_metrics['trends']['max_transparency_trend']}")
    
    def save_run_summary(self):
        """Save run-level summary to JSON"""
        if not self.run_metrics:
            print("No run metrics to save")
            return
        
        # Add metadata
        summary = {
            'run_directory': str(self.run_dir),
            'analysis_timestamp': datetime.now().isoformat(),
            **self.run_metrics
        }
        
        output_path = self.run_dir / "run_summary.json"
        with open(output_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n✓ Run summary saved: {output_path}")
        
        # Also save as CSV for easy viewing
        df = pd.DataFrame(self.run_metrics['session_metrics'])
        csv_path = self.run_dir / "run_analysis.csv"
        df.to_csv(csv_path, index=False)
        print(f"✓ Run analysis CSV saved: {csv_path}")
    
    def create_comparison_plots(self):
        """Create bar charts comparing sessions"""
        if not self.run_metrics or not self.run_metrics.get('session_metrics'):
            print("No metrics available for plotting")
            return
        
        print("\n=== Creating Comparison Plots ===")
        
        df = pd.DataFrame(self.run_metrics['session_metrics'])
        
        # Create figure with subplots
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('Session Comparison Analysis', fontsize=16, fontweight='bold')
        
        # Plot 1: Max Transparency per Session
        axes[0, 0].bar(df['session_number'], df['max_transparency'], color='steelblue', alpha=0.7)
        axes[0, 0].axhline(y=df['max_transparency'].mean(), color='red', linestyle='--', 
                          label=f"Mean: {df['max_transparency'].mean():.3f}", linewidth=2)
        axes[0, 0].set_xlabel('Session Number', fontsize=11)
        axes[0, 0].set_ylabel('Max Transparency Score', fontsize=11)
        axes[0, 0].set_title('Maximum Transparency by Session')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)
        axes[0, 0].set_ylim(0, 1.05)
        
        # Plot 2: Final Transparency per Session
        axes[0, 1].bar(df['session_number'], df['final_transparency'], color='darkgreen', alpha=0.7)
        axes[0, 1].axhline(y=df['final_transparency'].mean(), color='red', linestyle='--',
                          label=f"Mean: {df['final_transparency'].mean():.3f}", linewidth=2)
        axes[0, 1].set_xlabel('Session Number', fontsize=11)
        axes[0, 1].set_ylabel('Final Transparency Score', fontsize=11)
        axes[0, 1].set_title('Final Transparency by Session')
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3)
        axes[0, 1].set_ylim(0, 1.05)
        
        # Plot 3: Saturation Change per Session
        axes[1, 0].bar(df['session_number'], df['saturation_change_pct'], color='purple', alpha=0.7)
        axes[1, 0].axhline(y=df['saturation_change_pct'].mean(), color='red', linestyle='--',
                          label=f"Mean: {df['saturation_change_pct'].mean():.1f}%", linewidth=2)
        axes[1, 0].set_xlabel('Session Number', fontsize=11)
        axes[1, 0].set_ylabel('Saturation Change (%)', fontsize=11)
        axes[1, 0].set_title('Saturation Change by Session')
        axes[1, 0].legend()
        axes[1, 0].grid(True, alpha=0.3)
        
        # Plot 4: Brightness Change per Session
        axes[1, 1].bar(df['session_number'], df['brightness_change_pct'], color='gold', alpha=0.7)
        axes[1, 1].axhline(y=df['brightness_change_pct'].mean(), color='red', linestyle='--',
                          label=f"Mean: {df['brightness_change_pct'].mean():.1f}%", linewidth=2)
        axes[1, 1].set_xlabel('Session Number', fontsize=11)
        axes[1, 1].set_ylabel('Brightness Change (%)', fontsize=11)
        axes[1, 1].set_title('Brightness Change by Session')
        axes[1, 1].legend()
        axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Save plot
        output_path = self.run_dir / "session_comparison.png"
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"✓ Comparison plot saved: {output_path}")
        plt.close()
    
    def create_timeline_plot(self):
        """Create timeline showing all sessions together"""
        if not self.session_data:
            print("No time-series data available for timeline")
            return
        
        print("\n=== Creating Timeline Plot ===")
        
        # Create figure with multiple panels
        fig, axes = plt.subplots(3, 1, figsize=(16, 12))
        fig.suptitle('Multi-Session Timeline Analysis', fontsize=16, fontweight='bold')
        
        colors = plt.cm.tab10(np.linspace(0, 1, len(self.session_data)))
        
        # Plot each session
        for i, (df, color) in enumerate(zip(self.session_data, colors), 1):
            if 'timestamp' in df.columns and df['timestamp'].notna().any():
                x_data = df['timestamp']
                x_label = 'Time (seconds)'
            else:
                x_data = df['frame_number']
                x_label = 'Frame Number'
            
            # Plot 1: Transparency Score
            axes[0].plot(x_data, df['transparency_score'], 
                        color=color, linewidth=2, label=f'Session {i}', alpha=0.8)
            
            # Plot 2: Saturation
            axes[1].plot(x_data, df['mean_saturation'], 
                        color=color, linewidth=2, label=f'Session {i}', alpha=0.8)
            
            # Plot 3: Brightness
            axes[2].plot(x_data, df['mean_value'], 
                        color=color, linewidth=2, label=f'Session {i}', alpha=0.8)
        
        # Configure Plot 1
        axes[0].set_ylabel('Transparency Score', fontsize=12)
        axes[0].set_title('Transparency Score - All Sessions')
        axes[0].grid(True, alpha=0.3)
        axes[0].legend(loc='best', ncol=min(5, len(self.session_data)))
        axes[0].set_ylim(-0.05, 1.05)
        
        # Configure Plot 2
        axes[1].set_ylabel('Saturation', fontsize=12)
        axes[1].set_title('Saturation - All Sessions')
        axes[1].grid(True, alpha=0.3)
        axes[1].legend(loc='best', ncol=min(5, len(self.session_data)))
        
        # Configure Plot 3
        axes[2].set_xlabel(x_label, fontsize=12)
        axes[2].set_ylabel('Brightness (Value)', fontsize=12)
        axes[2].set_title('Brightness - All Sessions')
        axes[2].grid(True, alpha=0.3)
        axes[2].legend(loc='best', ncol=min(5, len(self.session_data)))
        
        plt.tight_layout()
        
        # Save plot
        output_path = self.run_dir / "run_timeline.png"
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"✓ Timeline plot saved: {output_path}")
        plt.close()
    
    def create_statistical_summary_plot(self):
        """Create box plots and statistical visualizations"""
        if not self.session_data:
            print("No data available for statistical plots")
            return
        
        print("\n=== Creating Statistical Summary ===")
        
        # Collect all transparency scores from all sessions
        all_transparency = []
        all_saturation = []
        all_brightness = []
        session_labels = []
        
        for i, df in enumerate(self.session_data, 1):
            all_transparency.extend(df['transparency_score'].tolist())
            all_saturation.extend(df['mean_saturation'].tolist())
            all_brightness.extend(df['mean_value'].tolist())
            session_labels.extend([f'S{i}'] * len(df))
        
        # Create DataFrame for box plots
        plot_df = pd.DataFrame({
            'Session': session_labels,
            'Transparency': all_transparency,
            'Saturation': all_saturation,
            'Brightness': all_brightness
        })
        
        # Create figure
        fig, axes = plt.subplots(1, 3, figsize=(16, 5))
        fig.suptitle('Statistical Distribution Across Sessions', fontsize=16, fontweight='bold')
        
        # Box plot 1: Transparency
        sessions = [f'S{i}' for i in range(1, len(self.session_data) + 1)]
        transparency_data = [self.session_data[i]['transparency_score'].values 
                            for i in range(len(self.session_data))]
        
        bp1 = axes[0].boxplot(transparency_data, labels=sessions, patch_artist=True)
        for patch in bp1['boxes']:
            patch.set_facecolor('steelblue')
            patch.set_alpha(0.6)
        axes[0].set_ylabel('Transparency Score', fontsize=12)
        axes[0].set_xlabel('Session', fontsize=12)
        axes[0].set_title('Transparency Distribution')
        axes[0].grid(True, alpha=0.3, axis='y')
        
        # Box plot 2: Saturation
        saturation_data = [self.session_data[i]['mean_saturation'].values 
                          for i in range(len(self.session_data))]
        
        bp2 = axes[1].boxplot(saturation_data, labels=sessions, patch_artist=True)
        for patch in bp2['boxes']:
            patch.set_facecolor('purple')
            patch.set_alpha(0.6)
        axes[1].set_ylabel('Saturation', fontsize=12)
        axes[1].set_xlabel('Session', fontsize=12)
        axes[1].set_title('Saturation Distribution')
        axes[1].grid(True, alpha=0.3, axis='y')
        
        # Box plot 3: Brightness
        brightness_data = [self.session_data[i]['mean_value'].values 
                          for i in range(len(self.session_data))]
        
        bp3 = axes[2].boxplot(brightness_data, labels=sessions, patch_artist=True)
        for patch in bp3['boxes']:
            patch.set_facecolor('gold')
            patch.set_alpha(0.6)
        axes[2].set_ylabel('Brightness', fontsize=12)
        axes[2].set_xlabel('Session', fontsize=12)
        axes[2].set_title('Brightness Distribution')
        axes[2].grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        
        # Save plot
        output_path = self.run_dir / "run_statistics.png"
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"✓ Statistical summary saved: {output_path}")
        plt.close()
    
    def generate_text_report(self):
        """Generate human-readable text report"""
        if not self.run_metrics:
            print("No metrics available for report")
            return
        
        print("\n=== Generating Text Report ===")
        
        report_path = self.run_dir / "run_report.txt"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write("RUN ANALYSIS REPORT\n")
            f.write("=" * 70 + "\n\n")
            
            f.write(f"Run Directory: {self.run_dir}\n")
            f.write(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Sessions: {self.run_metrics['total_sessions']}\n\n")
            
            # ROI Information
            roi = self.run_metrics.get('roi', {})
            f.write("ROI (Region of Interest):\n")
            f.write(f"  Position: ({roi.get('x', 'N/A')}, {roi.get('y', 'N/A')})\n")
            f.write(f"  Size: {roi.get('width', 'N/A')} x {roi.get('height', 'N/A')} pixels\n\n")
            
            # Aggregated Statistics
            f.write("-" * 70 + "\n")
            f.write("AGGREGATED STATISTICS\n")
            f.write("-" * 70 + "\n\n")
            
            stats = self.run_metrics['aggregated_statistics']
            
            f.write("Maximum Transparency:\n")
            f.write(f"  Mean: {stats['max_transparency']['mean']:.3f}\n")
            f.write(f"  Std Dev: {stats['max_transparency']['std']:.3f}\n")
            f.write(f"  Range: {stats['max_transparency']['min']:.3f} - {stats['max_transparency']['max']:.3f}\n\n")
            
            f.write("Final Transparency:\n")
            f.write(f"  Mean: {stats['final_transparency']['mean']:.3f}\n")
            f.write(f"  Std Dev: {stats['final_transparency']['std']:.3f}\n")
            f.write(f"  Range: {stats['final_transparency']['min']:.3f} - {stats['final_transparency']['max']:.3f}\n\n")
            
            f.write("Saturation Change:\n")
            f.write(f"  Mean: {stats['saturation_change']['mean']:.1f}%\n")
            f.write(f"  Std Dev: {stats['saturation_change']['std']:.1f}%\n\n")
            
            f.write("Brightness Change:\n")
            f.write(f"  Mean: {stats['brightness_change']['mean']:.1f}%\n")
            f.write(f"  Std Dev: {stats['brightness_change']['std']:.1f}%\n\n")
            
            f.write(f"Consistency Score: {self.run_metrics['consistency_score']:.3f}\n")
            f.write("  (1.0 = perfectly consistent, 0.0 = highly variable)\n\n")
            
            # Trends
            if 'trends' in self.run_metrics:
                f.write("-" * 70 + "\n")
                f.write("TREND ANALYSIS\n")
                f.write("-" * 70 + "\n\n")
                
                trends = self.run_metrics['trends']
                f.write(f"Max Transparency Trend: {trends['max_transparency_trend'].upper()}\n")
                f.write(f"Slope: {trends['max_transparency_slope']:.4f} per session\n")
                
                if trends.get('degradation_detected'):
                    f.write("\n[!] DEGRADATION DETECTED: Film response is declining across sessions\n")
                elif trends.get('improvement_detected'):
                    f.write("\n[+] IMPROVEMENT DETECTED: Film response is improving across sessions\n")
                else:
                    f.write("\n[+] STABLE: Film response is consistent across sessions\n")
                f.write("\n")
            
            # Per-Session Summary
            f.write("-" * 70 + "\n")
            f.write("PER-SESSION SUMMARY\n")
            f.write("-" * 70 + "\n\n")
            
            for metrics in self.run_metrics['session_metrics']:
                f.write(f"Session {metrics['session_number']}: {metrics['session_name']}\n")
                f.write(f"  Max Transparency: {metrics['max_transparency']:.3f}\n")
                f.write(f"  Final Transparency: {metrics['final_transparency']:.3f}\n")
                f.write(f"  Saturation Change: {metrics['saturation_change_pct']:.1f}%\n")
                f.write(f"  Brightness Change: {metrics['brightness_change_pct']:.1f}%\n")
                
                if metrics['time_to_50_pct'] is not None:
                    f.write(f"  Time to 50% Transparency: {metrics['time_to_50_pct']:.2f}s\n")
                if metrics['time_to_90_pct'] is not None:
                    f.write(f"  Time to 90% Transparency: {metrics['time_to_90_pct']:.2f}s\n")
                
                f.write("\n")
            
            f.write("=" * 70 + "\n")
        
        print(f"✓ Text report saved: {report_path}")
    
    def create_averaged_image(self):
        """Create averaged image from selected frames of all sessions to reduce noise"""
        print("\n=== Creating Averaged Image ===")
        
        # Get frame offset from config
        frame_offset = 0
        if self.config:
            frame_offset = self.config.get('run_analysis', {}).get('averaged_image', {}).get('frame_offset_from_end', 0)
        
        if frame_offset > 0:
            print(f"Using frame offset: {frame_offset} frames from end")
        else:
            print("Using final frame from each session")
        
        final_frames = []
        frame_info = []
        
        # Load selected frame from each session
        for session_dir in self.session_dirs:
            frames_dir = session_dir / "frames"
            
            if not frames_dir.exists():
                print(f"  ✗ No frames directory in {session_dir.name}")
                continue
            
            # Get all frame files
            frame_files = sorted(frames_dir.glob("frame_*.jpg")) + sorted(frames_dir.glob("frame_*.png"))
            
            if not frame_files:
                print(f"  ✗ No frames found in {session_dir.name}")
                continue
            
            # Calculate which frame to use
            frame_index = len(frame_files) - 1 - frame_offset
            
            # Validate index
            if frame_index < 0:
                print(f"  ✗ Offset {frame_offset} too large for {session_dir.name} (only {len(frame_files)} frames)")
                continue
            
            # Load the selected frame
            selected_frame_path = frame_files[frame_index]
            frame = cv2.imread(str(selected_frame_path))
            
            if frame is not None:
                final_frames.append(frame)
                frame_number = int(selected_frame_path.stem.split('_')[1])
                frame_info.append({
                    'session': session_dir.name,
                    'frame_number': frame_number,
                    'frame_index': frame_index,
                    'total_frames': len(frame_files)
                })
                print(f"  ✓ Loaded frame {frame_number} from {session_dir.name} (index {frame_index}/{len(frame_files)-1})")
            else:
                print(f"  ✗ Could not load frame from {session_dir.name}")
        
        if len(final_frames) == 0:
            print("✗ No frames loaded - cannot create averaged image")
            return
        
        print(f"\n✓ Loaded {len(final_frames)} final frames")
        
        # Convert to float for averaging
        frames_float = [frame.astype(np.float32) for frame in final_frames]
        
        # Calculate mean across all frames
        averaged_frame = np.mean(frames_float, axis=0).astype(np.uint8)
        
        print(f"✓ Averaged image created (reduces noise by ~{np.sqrt(len(final_frames)):.1f}x)")
        
        # Save averaged image
        averaged_path = self.run_dir / "averaged_final_frame.png"
        cv2.imwrite(str(averaged_path), averaged_frame)
        print(f"✓ Averaged image saved: {averaged_path}")
        
        # Create visualization with ROI overlay
        if self.run_metrics.get('roi'):
            roi = self.run_metrics['roi']
            x, y, w, h = roi['x'], roi['y'], roi['width'], roi['height']
            
            # Create annotated version
            annotated = averaged_frame.copy()
            cv2.rectangle(annotated, (x, y), (x + w, y + h), (0, 255, 0), 3)
            cv2.putText(annotated, f"Averaged from {len(final_frames)} sessions", 
                       (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
            cv2.putText(annotated, f"Noise reduction: ~{np.sqrt(len(final_frames)):.1f}x", 
                       (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
            
            if frame_offset > 0:
                cv2.putText(annotated, f"Frame offset: {frame_offset} from end", 
                           (10, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 0), 2)
            
            annotated_path = self.run_dir / "averaged_final_frame_annotated.png"
            cv2.imwrite(str(annotated_path), annotated)
            print(f"✓ Annotated averaged image saved: {annotated_path}")
        
        # Analyze the averaged image and save combined info
        self._analyze_averaged_image(averaged_frame, frame_offset, frame_info, len(final_frames))
        
        return averaged_frame
    
    def _analyze_averaged_image(self, averaged_frame, frame_offset, frame_info, num_frames):
        """Analyze transparency metrics on the averaged image"""
        if not self.run_metrics.get('roi'):
            print("  No ROI available for analysis")
            return
        
        print("\n=== Analyzing Averaged Image ===")
        
        roi = self.run_metrics['roi']
        x, y, w, h = roi['x'], roi['y'], roi['width'], roi['height']
        
        # Extract ROI
        roi_region = averaged_frame[y:y+h, x:x+w]
        
        # Convert to HSV
        hsv = cv2.cvtColor(roi_region, cv2.COLOR_BGR2HSV)
        
        # Calculate metrics
        mean_hue = np.mean(hsv[:, :, 0])
        mean_saturation = np.mean(hsv[:, :, 1])
        mean_value = np.mean(hsv[:, :, 2])
        
        mean_r = np.mean(roi_region[:, :, 2])
        mean_g = np.mean(roi_region[:, :, 1])
        mean_b = np.mean(roi_region[:, :, 0])
        
        # Purple index
        purple_hue_center = 140
        hue_deviation = np.abs(mean_hue - purple_hue_center)
        purple_index = mean_saturation * (1 - min(hue_deviation / 30, 1))
        
        # Luminance
        luminance = 0.299 * mean_r + 0.587 * mean_g + 0.114 * mean_b
        
        # Combine frame info and metrics into one comprehensive file
        combined_data = {
            'averaging_info': {
                'frame_offset_from_end': frame_offset,
                'num_frames_averaged': num_frames,
                'noise_reduction_factor': float(np.sqrt(num_frames)),
                'frames_used': frame_info
            },
            'color_metrics': {
                'mean_hue': float(mean_hue),
                'mean_saturation': float(mean_saturation),
                'mean_value': float(mean_value),
                'mean_r': float(mean_r),
                'mean_g': float(mean_g),
                'mean_b': float(mean_b),
                'purple_index': float(purple_index),
                'luminance': float(luminance)
            }
        }
        
        # Save combined metrics
        metrics_path = self.run_dir / "averaged_image_analysis.json"
        with open(metrics_path, 'w') as f:
            json.dump(combined_data, f, indent=2)
        
        print(f"✓ Averaged image metrics:")
        print(f"  Saturation: {mean_saturation:.1f}")
        print(f"  Brightness: {mean_value:.1f}")
        print(f"  Purple Index: {purple_index:.1f}")
        print(f"  Luminance: {luminance:.1f}")
        print(f"✓ Analysis saved: {metrics_path}")
        
        # Add to run metrics
        self.run_metrics['averaged_image_analysis'] = combined_data
    
    def run_full_analysis(self):
        """Execute complete run-level analysis"""
        print("\n" + "=" * 70)
        print("RUN-LEVEL ANALYSIS")
        print("=" * 70)
        
        # Discover and load sessions
        num_sessions = self.discover_sessions()
        
        if num_sessions == 0:
            print("\n✗ No sessions found in run directory")
            return
        
        self.load_session_summaries()
        self.load_session_timeseries()
        
        # Calculate metrics
        self.calculate_run_metrics()
        
        # Generate outputs
        self.save_run_summary()
        self.create_comparison_plots()
        self.create_timeline_plot()
        self.create_statistical_summary_plot()
        self.generate_text_report()
        self.create_averaged_image()
        
        print("\n" + "=" * 70)
        print("RUN-LEVEL ANALYSIS COMPLETE")
        print("=" * 70)
        print(f"\nResults saved to: {self.run_dir}")
        print("\nGenerated files:")
        print("  - run_summary.json                  : Aggregated metrics and statistics")
        print("  - run_analysis.csv                  : Per-session metrics table")
        print("  - session_comparison.png            : Bar charts comparing sessions")
        print("  - run_timeline.png                  : Multi-session timeline plot")
        print("  - run_statistics.png                : Statistical distributions")
        print("  - run_report.txt                    : Human-readable summary")
        print("  - averaged_final_frame.png          : Noise-reduced averaged image")
        print("  - averaged_final_frame_annotated.png: Averaged image with ROI overlay")
        print("  - averaged_image_analysis.json      : Frame info + color metrics")
