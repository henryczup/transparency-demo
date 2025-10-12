"""
Post-processing module for recorded data
Calculates difference frames (end - start) for each recording
"""
import cv2
import json
import numpy as np
from pathlib import Path


class DataPostProcessor:
    """Post-processes recorded video to extract difference frames"""
    
    def __init__(self, recording_dir, config):
        self.recording_dir = Path(recording_dir)
        self.config = config
        self.metadata = None
        
        # Load metadata
        metadata_path = self.recording_dir / "metadata.json"
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                self.metadata = json.load(f)
        else:
            print(f"Warning: No metadata found at {metadata_path}")
    
    def calculate_difference_frame(self):
        """
        Calculate difference between end frame and start frame with configurable offsets
        Returns: difference_frame (end - start)
        """
        video_path = self.recording_dir / "recording.mp4"
        if not video_path.exists():
            print(f"Video file not found: {video_path}")
            return None
        
        print(f"\nCalculating difference frame for {self.recording_dir.name}...")
        cap = cv2.VideoCapture(str(video_path))
        
        # Get total frame count
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        if total_frames < 2:
            print(f"Not enough frames ({total_frames}) to calculate difference")
            cap.release()
            return None
        
        # Get frame offsets from config (default to 0 if not specified)
        postproc_config = self.config.get('postprocessing', {})
        start_offset = postproc_config.get('start_frame_offset', 0)
        end_offset = postproc_config.get('end_frame_offset', 0)
        
        # Calculate actual frame indices
        start_frame_idx = start_offset
        end_frame_idx = total_frames - 1 - end_offset
        
        # Validate indices
        if start_frame_idx >= end_frame_idx:
            print(f"Error: Invalid frame offsets. Start offset ({start_offset}) + end offset ({end_offset}) exceed total frames ({total_frames})")
            cap.release()
            return None
        
        if start_frame_idx < 0 or end_frame_idx >= total_frames:
            print(f"Error: Frame indices out of bounds")
            cap.release()
            return None
        
        # Read start frame (with offset)
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame_idx)
        ret, start_frame = cap.read()
        
        if not ret:
            print(f"Could not read start frame at index {start_frame_idx}")
            cap.release()
            return None
        
        # Read end frame (with offset)
        cap.set(cv2.CAP_PROP_POS_FRAMES, end_frame_idx)
        ret, end_frame = cap.read()
        
        if not ret:
            print(f"Could not read end frame at index {end_frame_idx}")
            cap.release()
            return None
        
        cap.release()
        
        # Convert to float for proper subtraction
        start_float = start_frame.astype(np.float32)
        end_float = end_frame.astype(np.float32)
        
        # Calculate difference: end - start
        difference = end_float - start_float
        
        # Save individual frames for reference
        frames_dir = self.recording_dir / "frames"
        frames_dir.mkdir(exist_ok=True)
        
        cv2.imwrite(str(frames_dir / "start_frame.png"), start_frame)
        cv2.imwrite(str(frames_dir / "end_frame.png"), end_frame)
        
        # Save raw difference (can have negative values)
        difference_path = self.recording_dir / "difference_frame_raw.npy"
        np.save(str(difference_path), difference)
        
        # Save visualizable difference (shifted and scaled)
        # Shift by 127 to center at gray, then clip to 0-255
        difference_vis = np.clip(difference + 127, 0, 255).astype(np.uint8)
        cv2.imwrite(str(frames_dir / "difference_frame_visualized.png"), difference_vis)
        
        # Save absolute difference for easier viewing
        difference_abs = np.abs(difference).astype(np.uint8)
        cv2.imwrite(str(frames_dir / "difference_frame_absolute.png"), difference_abs)
        
        print(f"✓ Difference frame calculated")
        print(f"  Total frames in video: {total_frames}")
        print(f"  Start frame: {start_frame_idx} (offset: {start_offset})")
        print(f"  End frame: {end_frame_idx} (offset: {end_offset})")
        print(f"  Frames analyzed: {end_frame_idx - start_frame_idx + 1}")
        print(f"  Difference range: [{difference.min():.1f}, {difference.max():.1f}]")
        
        # Save metadata about the difference calculation
        diff_metadata = {
            'start_frame_index': int(start_frame_idx),
            'end_frame_index': int(end_frame_idx),
            'start_frame_offset': int(start_offset),
            'end_frame_offset': int(end_offset),
            'total_frames': total_frames,
            'frames_analyzed': int(end_frame_idx - start_frame_idx + 1),
            'difference_stats': {
                'min': float(difference.min()),
                'max': float(difference.max()),
                'mean': float(difference.mean()),
                'std': float(difference.std())
            }
        }
        
        metadata_path = self.recording_dir / "difference_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(diff_metadata, f, indent=2)
        
        return difference
    
    def process_all(self):
        """Run all post-processing steps"""
        print("\n" + "=" * 60)
        print("STARTING POST-PROCESSING")
        print("=" * 60)
        
        difference_frame = self.calculate_difference_frame()
        
        if difference_frame is not None:
            print("\n✓ Post-processing complete")
            print(f"  Files saved in: {self.recording_dir}")
            print("  - frames/start_frame.png")
            print("  - frames/end_frame.png")
            print("  - frames/difference_frame_visualized.png")
            print("  - frames/difference_frame_absolute.png")
            print("  - difference_frame_raw.npy")
            print("  - difference_metadata.json")
        else:
            print("\n✗ Post-processing failed")
        
        print("\n" + "=" * 60)
        print("POST-PROCESSING COMPLETE")
        print("=" * 60)
