#!/usr/bin/env python3
"""
Test script for video thumbnail generation functionality
"""

import os
import sys
import cv2
import uuid
from werkzeug.utils import secure_filename

def generate_video_thumbnail(video_path, thumbnail_path):
    """Generate a thumbnail from a video file using OpenCV"""
    try:
        # Open the video file
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            print(f"Error: Could not open video file {video_path}")
            return False
        
        # Get video properties
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        if total_frames == 0:
            print(f"Error: Video file {video_path} has no frames")
            cap.release()
            return False
        
        # Seek to 25% of the video (usually a good point for thumbnails)
        frame_position = int(total_frames * 0.25)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_position)
        
        # Read the frame
        ret, frame = cap.read()
        
        if not ret:
            # If we can't read at 25%, try the first frame
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = cap.read()
            
        if not ret:
            print(f"Error: Could not read frame from video {video_path}")
            cap.release()
            return False
        
        # Resize the frame to a reasonable thumbnail size (e.g., 320x240)
        height, width = frame.shape[:2]
        aspect_ratio = width / height
        
        if aspect_ratio > 1:  # Landscape
            new_width = 320
            new_height = int(320 / aspect_ratio)
        else:  # Portrait
            new_height = 240
            new_width = int(240 * aspect_ratio)
        
        frame = cv2.resize(frame, (new_width, new_height))
        
        # Save the thumbnail
        success = cv2.imwrite(thumbnail_path, frame)
        
        # Release the video capture
        cap.release()
        
        if success:
            print(f"Successfully generated thumbnail: {thumbnail_path}")
            return True
        else:
            print(f"Error: Could not save thumbnail to {thumbnail_path}")
            return False
            
    except Exception as e:
        print(f"Error generating thumbnail: {str(e)}")
        return False

def test_thumbnail_generation():
    """Test the thumbnail generation function"""
    print("Testing video thumbnail generation...")
    
    # Check if OpenCV is available
    try:
        import cv2
        print("✓ OpenCV is available")
    except ImportError:
        print("✗ OpenCV is not available. Please install it with: pip install opencv-python")
        return False
    
    # Check if we have a test video file
    test_video_path = "test_video.mp4"
    if not os.path.exists(test_video_path):
        print(f"✗ Test video file '{test_video_path}' not found.")
        print("Please place a test video file named 'test_video.mp4' in the current directory.")
        return False
    
    print(f"✓ Found test video: {test_video_path}")
    
    # Create test thumbnail path
    thumbnail_filename = f"{uuid.uuid4().hex}_test_thumb.jpg"
    thumbnail_path = os.path.join("static", "uploads", "thumbnails", thumbnail_filename)
    
    # Ensure thumbnails directory exists
    os.makedirs(os.path.dirname(thumbnail_path), exist_ok=True)
    
    # Test thumbnail generation
    print("Generating thumbnail...")
    success = generate_video_thumbnail(test_video_path, thumbnail_path)
    
    if success:
        print("✓ Thumbnail generation test passed!")
        print(f"Generated thumbnail: {thumbnail_path}")
        
        # Check if the thumbnail file was actually created
        if os.path.exists(thumbnail_path):
            file_size = os.path.getsize(thumbnail_path)
            print(f"✓ Thumbnail file created successfully (size: {file_size} bytes)")
            return True
        else:
            print("✗ Thumbnail file was not created")
            return False
    else:
        print("✗ Thumbnail generation test failed!")
        return False

if __name__ == "__main__":
    success = test_thumbnail_generation()
    if success:
        print("\n🎉 All tests passed! Video thumbnail generation is working correctly.")
    else:
        print("\n❌ Tests failed. Please check the error messages above.")
        sys.exit(1)
