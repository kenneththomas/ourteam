import os
import uuid
from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, session, url_for
from sqlalchemy import String, cast, desc, func, or_, text
from sqlalchemy.exc import IntegrityError
from models import db, Employee, EmployeeImage, EmployeeVideo, Comment, Action, Group, EmployeeXP, Status, GroupComment
from forms import EmployeeForm, AddImageUrlForm, AddVideoUrlForm
from services import save_uploaded_file, uploaded_file_path, generate_video_thumbnail

from flask import Blueprint
bp=Blueprint('media',__name__)

@bp.route('/employee/<int:id>/add_image', methods=['GET', 'POST'])
def add_image(id):
    form = AddImageUrlForm()
    if form.validate_on_submit():
        # Determine the image URL - either from uploaded file or URL field
        image_url = form.image_url.data
        if form.image_file.data:
            saved_path = save_uploaded_file(form.image_file.data, 'images')
            if saved_path:
                image_url = f"/static/{saved_path}"
            else:
                flash('Error saving uploaded file.')
                return render_template('add_image_v2.html', form=form)
        
        image = EmployeeImage(image_url=image_url, employee_id=id, caption=form.caption.data)
        db.session.add(image)
        db.session.commit()
        flash('Image added successfully!')
        return redirect(url_for('employees.view_employee', id=id))
    return render_template('add_image_v2.html', form=form)

@bp.route('/employee/<int:id>/add_video', methods=['GET', 'POST'])
def add_video(id):
    form = AddVideoUrlForm()
    if form.validate_on_submit():
        # Determine the video URL - either from uploaded file or URL field
        video_url = form.video_url.data
        video_file_path = None  # Store the actual file path for thumbnail generation
        
        if form.video_file.data:
            print(f"DEBUG: Video file uploaded: {form.video_file.data.filename}")
            saved_path = save_uploaded_file(form.video_file.data, 'videos')
            if saved_path:
                video_url = f"/static/{saved_path}"
                # Store the full path for thumbnail generation
                # saved_path is "uploads/videos/filename", so we need to construct the full path correctly
                # Extract just the filename from the saved_path
                filename = os.path.basename(saved_path)
                video_file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'videos', filename)
                print(f"DEBUG: Video saved to: {video_file_path}")
            else:
                print(f"ERROR: Failed to save video file")
                flash('Error saving uploaded video file.')
                return render_template('add_video_v2.html', form=form)
        
        # Handle thumbnail - either from URL, uploaded file, or auto-generated
        thumbnail_url = form.thumbnail_url.data
        if form.thumbnail_file.data:
            saved_thumbnail_path = save_uploaded_file(form.thumbnail_file.data, 'thumbnails')
            if saved_thumbnail_path:
                thumbnail_url = f"/static/{saved_thumbnail_path}"
            else:
                flash('Error saving uploaded thumbnail file.')
                return render_template('add_video_v2.html', form=form)
        elif not thumbnail_url and video_file_path:
            # Auto-generate thumbnail from video if no thumbnail provided
            print(f"DEBUG: Attempting to auto-generate thumbnail for video: {video_file_path}")
            try:
                # Generate a unique thumbnail filename
                thumbnail_filename = f"{uuid.uuid4().hex}_auto_thumb.jpg"
                thumbnail_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'thumbnails', thumbnail_filename)
                
                print(f"DEBUG: Generated thumbnail path: {thumbnail_path}")
                
                # Ensure thumbnails directory exists
                os.makedirs(os.path.dirname(thumbnail_path), exist_ok=True)
                print(f"DEBUG: Ensured thumbnail directory exists")
                
                # Generate the thumbnail
                print(f"DEBUG: Calling generate_video_thumbnail...")
                if generate_video_thumbnail(video_file_path, thumbnail_path):
                    thumbnail_url = f"/static/uploads/thumbnails/{thumbnail_filename}"
                    print(f"DEBUG: Thumbnail generation successful, URL: {thumbnail_url}")
                    flash('Video thumbnail generated automatically!')
                else:
                    print(f"DEBUG: Thumbnail generation failed")
                    flash('Warning: Could not generate automatic thumbnail. Video will be displayed without a thumbnail.')
            except Exception as e:
                print(f"ERROR generating automatic thumbnail: {str(e)}")
                import traceback
                traceback.print_exc()
                flash('Warning: Could not generate automatic thumbnail. Video will be displayed without a thumbnail.')
        
        video = EmployeeVideo(
            video_url=video_url, 
            employee_id=id, 
            caption=form.caption.data,
            thumbnail_url=thumbnail_url
        )
        db.session.add(video)
        db.session.commit()
        flash('Video added successfully!')
        return redirect(url_for('employees.view_employee', id=id))
    return render_template('add_video_v2.html', form=form)


