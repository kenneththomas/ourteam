# File Upload Feature Documentation

## Overview
The gallery feature now supports both URL links and direct file uploads for images and videos. Users can choose between providing a URL or uploading a file directly from their device.

## Features

### Image Uploads
- **URL Upload**: Enter a direct URL to an image (e.g., https://example.com/image.jpg)
- **File Upload**: Upload image files directly from your device
- **Supported Formats**: JPG, JPEG, PNG, GIF, WebP
- **File Size Limit**: 100MB maximum

### Video Uploads
- **URL Upload**: Enter a video URL (YouTube, Vimeo, or direct video link)
- **File Upload**: Upload video files directly from your device
- **Supported Formats**: MP4, AVI, MOV, WMV, FLV, WebM
- **File Size Limit**: 100MB maximum
- **Thumbnail Support**: Optional thumbnail image (URL or file upload)

## How to Use

### Adding Images
1. Navigate to an employee's profile page
2. Click "Add Image" button
3. Choose upload method:
   - **Image URL**: Enter the URL of an image
   - **Upload File**: Select an image file from your device
4. Add an optional caption
5. Click "Add Image"

### Adding Videos
1. Navigate to an employee's profile page
2. Click "Add Video" button
3. Choose upload method:
   - **Video URL**: Enter the URL of a video
   - **Upload File**: Select a video file from your device
4. Add an optional caption
5. Choose thumbnail method (optional):
   - **Thumbnail URL**: Enter the URL of a thumbnail image
   - **Upload Thumbnail**: Select a thumbnail image file
6. Click "Add Video"

## Technical Details

### File Storage
- Uploaded files are stored in `static/uploads/` directory
- Images: `static/uploads/images/`
- Videos: `static/uploads/videos/`
- Thumbnails: `static/uploads/thumbnails/`
- Files are renamed with unique UUIDs to prevent conflicts

### Security Features
- File type validation (only allowed formats accepted)
- File size limits (100MB maximum)
- Secure filename handling
- Unique file naming to prevent overwrites

### Database Storage
- File paths are stored as relative URLs in the database
- URLs are prefixed with `/static/` for proper serving
- Both URL and file upload methods store the same URL format

## File Structure
```
static/
├── uploads/
│   ├── images/          # Uploaded image files
│   ├── videos/          # Uploaded video files
│   └── thumbnails/      # Uploaded thumbnail images
```

## Browser Compatibility
- File uploads work in all modern browsers
- Video playback supports HTML5 video formats
- Fallback messages for unsupported video formats

## Notes
- The existing URL functionality remains unchanged
- Users can switch between URL and file upload methods using radio buttons
- Form validation ensures at least one method is selected
- Success/error messages are displayed to users
