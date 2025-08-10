from flask import Flask, render_template, redirect, url_for, request, session, flash, jsonify, send_from_directory
from models import (
    db, Employee, EmployeeImage, EmployeeVideo, Comment, Action, Group, EmployeeXP, Status, GroupComment
)
from forms import EmployeeForm, AddImageUrlForm, AddVideoUrlForm
from sqlalchemy import func, or_, desc
from markupsafe import Markup
import squawk
import os
import uuid
from werkzeug.utils import secure_filename
import cv2

def nl2br(s):
    #html doesnt do newlines so we need to convert them to <br> tags
    return Markup(s.replace('\n', '<br>\n'))

xp_actions = {
    'send_comment': 10,
    'receive_comment': 5,
    'update_bio' : 10,
}

# Global configuration for GPT engine selection
DEFAULT_GPT_ENGINE = 'gpt-4.1-mini'
ALLOWED_GPT_ENGINES = ['gpt-4.1-mini', 'gpt-4.1']

def generate_text_from_prompt(prompt):
    """
    Wrapper that checks the current session for the desired GPT engine.m
    By default, uses 'gpt-4.1-mini'. If the user has selected 'gpt-4.1',
    calls squawk.generate_text() with the engine parameter set to 'gpt-4.1'.
    """
    engine = session.get('gpt_engine', DEFAULT_GPT_ENGINE)
    if engine == 'gpt-4.1':
        return squawk.generate_text(prompt, engine='gpt-4.1')
    # Default or fallback uses gpt-4.1-mini
    return squawk.generate_text(prompt)

def save_uploaded_file(file, folder):
    """Save an uploaded file and return the filename"""
    if file and file.filename:
        # Generate a unique filename to prevent conflicts
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        
        # Ensure the upload directory exists
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], folder)
        os.makedirs(upload_path, exist_ok=True)
        
        # Save the file
        file_path = os.path.join(upload_path, unique_filename)
        file.save(file_path)
        
        # Return the relative path for database storage
        return f"uploads/{folder}/{unique_filename}"
    return None

def generate_video_thumbnail(video_path, thumbnail_path):
    """Generate a thumbnail from a video file using OpenCV"""
    print(f"DEBUG: Starting thumbnail generation for {video_path}")
    print(f"DEBUG: Target thumbnail path: {thumbnail_path}")
    
    try:
        # Check if video file exists
        if not os.path.exists(video_path):
            print(f"ERROR: Video file does not exist: {video_path}")
            return False
            
        # Open the video file
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            print(f"ERROR: Could not open video file {video_path}")
            return False
        
        print(f"DEBUG: Successfully opened video file")
        
        # Get video properties
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        print(f"DEBUG: Video properties - Frames: {total_frames}, FPS: {fps}, Size: {width}x{height}")
        
        if total_frames == 0:
            print(f"ERROR: Video file {video_path} has no frames")
            cap.release()
            return False
        
        # Seek to 25% of the video (usually a good point for thumbnails)
        frame_position = int(total_frames * 0.25)
        print(f"DEBUG: Seeking to frame {frame_position} (25% of {total_frames})")
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_position)
        
        # Read the frame
        ret, frame = cap.read()
        
        if not ret:
            print(f"DEBUG: Could not read frame at 25%, trying first frame")
            # If we can't read at 25%, try the first frame
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = cap.read()
            
        if not ret:
            print(f"ERROR: Could not read any frame from video {video_path}")
            cap.release()
            return False
        
        print(f"DEBUG: Successfully read frame, shape: {frame.shape}")
        
        # Resize the frame to a reasonable thumbnail size (e.g., 320x240)
        height, width = frame.shape[:2]
        aspect_ratio = width / height
        
        if aspect_ratio > 1:  # Landscape
            new_width = 320
            new_height = int(320 / aspect_ratio)
        else:  # Portrait
            new_height = 240
            new_width = int(240 * aspect_ratio)
        
        print(f"DEBUG: Resizing frame from {width}x{height} to {new_width}x{new_height}")
        frame = cv2.resize(frame, (new_width, new_height))
        
        # Ensure thumbnail directory exists
        thumbnail_dir = os.path.dirname(thumbnail_path)
        if not os.path.exists(thumbnail_dir):
            print(f"DEBUG: Creating thumbnail directory: {thumbnail_dir}")
            os.makedirs(thumbnail_dir, exist_ok=True)
        
        # Save the thumbnail
        print(f"DEBUG: Saving thumbnail to {thumbnail_path}")
        success = cv2.imwrite(thumbnail_path, frame)
        
        # Release the video capture
        cap.release()
        
        if success:
            print(f"SUCCESS: Generated thumbnail: {thumbnail_path}")
            # Verify file was created
            if os.path.exists(thumbnail_path):
                file_size = os.path.getsize(thumbnail_path)
                print(f"DEBUG: Thumbnail file created successfully, size: {file_size} bytes")
                return True
            else:
                print(f"ERROR: Thumbnail file was not created despite success flag")
                return False
        else:
            print(f"ERROR: Could not save thumbnail to {thumbnail_path}")
            return False
            
    except Exception as e:
        print(f"ERROR generating thumbnail: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

app = Flask(__name__)
app.jinja_env.filters['nl2br'] = nl2br
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ourteam.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size
app.config['UPLOAD_FOLDER'] = 'static/uploads'
db.init_app(app)

@app.route('/')
def index():
    # Get featured employees (most active based on XP)
    featured_employees = db.session.query(Employee, EmployeeXP)\
        .join(EmployeeXP)\
        .order_by(EmployeeXP.xp.desc())\
        .limit(6)\
        .all()
    
    # Get some statistics
    total_employees = Employee.query.count()
    total_departments = db.session.query(Employee.department).distinct().count()
    total_comments = Comment.query.count()
    total_actions = Action.query.count()
    
    # Get recent activities
    recent_actions = Action.query.order_by(Action.timestamp.desc()).limit(5).all()
    
    return render_template('index.html',
                         featured_employees=[emp for emp, _ in featured_employees],
                         total_employees=total_employees,
                         total_departments=total_departments,
                         total_comments=total_comments,
                         total_actions=total_actions,
                         recent_actions=recent_actions)

@app.route('/employees')
def list_employees():
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Increased from 5 to show more employees
    
    # Add sorting options
    sort_by = request.args.get('sort', 'name')  # Default sort by name
    order = request.args.get('order', 'asc')
    
    # Add department filter
    department = request.args.get('department')
    
    # Base query
    query = Employee.query
    
    # Apply department filter if specified
    if department:
        query = query.filter_by(department=department)
    
    # Apply sorting
    if sort_by == 'name':
        query = query.order_by(Employee.name.asc() if order == 'asc' else Employee.name.desc())
    elif sort_by == 'department':
        query = query.order_by(Employee.department.asc() if order == 'asc' else Employee.department.desc())
    elif sort_by == 'title':
        query = query.order_by(Employee.title.asc() if order == 'asc' else Employee.title.desc())
    elif sort_by == 'level':
        query = query.join(EmployeeXP).order_by(
            EmployeeXP.xp.desc() if order == 'desc' else EmployeeXP.xp.asc()
        )
    
    # Get all unique departments for the filter dropdown, sorted alphabetically
    departments = db.session.query(Employee.department)\
        .distinct()\
        .order_by(Employee.department)\
        .all()
    
    employees = query.paginate(page=page, per_page=per_page)
    
    return render_template(
        'list_employees.html',
        employees=employees,
        departments=departments,
        current_department=department,
        current_sort=sort_by,
        current_order=order
    )

@app.route('/employee/<int:id>')
def view_employee(id):
    employee = Employee.query.get_or_404(id)
    images = EmployeeImage.query.filter_by(employee_id=id).all()
    videos = EmployeeVideo.query.filter_by(employee_id=id).all()
    employee_xp = EmployeeXP.query.filter_by(employee_id=id).first()

    if not employee_xp:
        employee_xp = EmployeeXP(employee_id=id, xp=0)
        db.session.add(employee_xp)

    employee_xp.xp += 1
    #print employee name and xp gain
    print(f'employee: {employee.name} xp: {employee_xp.xp} +1 xp')
    level = calculate_level(employee_xp.xp)
    next_level_xp = level * 100
    progress = employee_xp.xp % next_level_xp
    db.session.commit()

    # this is for my own broken implementation, will fix for real use later
    comanager_overrides = {
        '261' : '225'
    }

    co_manager = None
    if str(id) in comanager_overrides:
        co_manager_id = comanager_overrides[str(id)]
        co_manager = Employee.query.filter_by(name=co_manager_id).first()
        print(f'co_manager: {co_manager}')
    
    # Get the page number for the comments
    comments_page = request.args.get('comments_page', 1, type=int)
    
    # Paginate the comments
    comments = Comment.query.filter(or_(Comment.employee_id==id, Comment.author_id==id)).order_by(Comment.timestamp.desc()).paginate(page=comments_page, per_page=8)
    
    department = employee.department
    session['previous_employee_id'] = id
    session['previous_employee_department'] = department
    manager_chain = None
    if employee.reports_to:
        manager_chain = get_management_chain(employee)
        manager_chain = list(reversed(manager_chain))
    subordinates = Employee.query.filter_by(reports_to=id).all()
    form = EmployeeForm(obj=employee)
    form.id.data = id
    recent_actions = Action.query.filter_by(from_id=id).order_by(Action.timestamp.desc()).limit(5).all()

    # Get recent statuses for this employee
    recent_statuses = Status.query.filter_by(employee_id=id).order_by(Status.timestamp.desc()).limit(5).all()

    return render_template('view_employee.html', employee=employee, recent_actions=recent_actions, 
                           subordinates=subordinates, manager_chain=manager_chain, images=images, 
                           videos=videos, comments=comments, co_manager=co_manager, employee_xp=employee_xp, 
                           next_level_xp=next_level_xp, progress=progress, recent_statuses=recent_statuses)

@app.route('/org_tree/<int:id>')
def org_tree(id):
    employee = Employee.query.get_or_404(id)
    
    # Get 2 levels of managers above
    managers = []
    current = employee
    for _ in range(2):
        if current.reports_to:
            manager = Employee.query.get(current.reports_to)
            if manager:
                managers.append(manager)
                current = manager
            else:
                break
        else:
            break
    
    # Get 2 levels of reports below
    def get_reports(emp_id, depth=0, max_depth=2):
        if depth >= max_depth:
            return []
        
        reports = Employee.query.filter_by(reports_to=emp_id).all()
        result = []
        for report in reports:
            result.append({
                'employee': report,
                'reports': get_reports(report.id, depth + 1, max_depth)
            })
        return result
    
    reports = get_reports(id)
    
    # Get department members for context
    department_members = Employee.query.filter_by(department=employee.department).all()
    
    return render_template('org_tree.html',
                         employee=employee,
                         managers=managers,
                         reports=reports,
                         department_members=department_members)

@app.route('/post_status_from_profile', methods=['POST'])
def post_status_from_profile():
    employee_id = request.form.get('employee_id')
    content = request.form.get('content')
    
    if not employee_id or not content:
        flash('Employee ID and content are required.')
        return redirect(url_for('view_employee', id=employee_id))
    
    employee = Employee.query.get(employee_id)
    if not employee:
        flash('Employee not found.')
        return redirect(url_for('view_employee', id=employee_id))
    
    status = Status(employee_id=employee_id, content=content)
    db.session.add(status)
    db.session.commit()
    
    flash('Status posted successfully.')
    return redirect(url_for('view_employee', id=employee_id))

@app.route('/employee/add', methods=['GET', 'POST'])
def add_employee():
    form = EmployeeForm()
    if 'previous_employee_id' in session:
        form.reports_to.data = session['previous_employee_id']
        del session['previous_employee_id']
    if 'previous_employee_department' in session:
        form.department.data = session['previous_employee_department']
        del session['previous_employee_department']
    if form.validate_on_submit():
        new_employee = Employee(
            name=form.name.data,
            title=form.title.data,
            department=form.department.data,
            email=form.email.data,
            phone=form.phone.data,
            picture_url=form.picture_url.data,
            reports_to=form.reports_to.data
        )
        db.session.add(new_employee)
        db.session.commit()

        #action for new employee
        action = Action(description=f"New employee added: {new_employee.name} - {new_employee.department}", from_id=new_employee.id)
        db.session.add(action)
        db.session.commit()

        return redirect(url_for('view_employee', id=new_employee.id))
    return render_template('add_edit_employee.html', form=form)

@app.route('/employee/edit/<int:id>', methods=['GET', 'POST'])
def edit_employee(id):
    employee = Employee.query.get_or_404(id)
    form = EmployeeForm(obj=employee)

    #initialize xp gain
    employee_xp = EmployeeXP.query.filter_by(employee_id=id).first()
    if not employee_xp:
        employee_xp = EmployeeXP(employee_id=id, xp=0)
        db.session.add(employee_xp)

    #get original values for actions
    original_name = employee.name
    original_title = employee.title
    original_department = employee.department
    original_reports_to = employee.reports_to
    original_bio = employee.bio
    original_location = employee.location
    #get original name of manager
    original_mgr_name = None
    if employee.reports_to:
        original_manager = Employee.query.get(employee.reports_to)
        if original_manager:
            original_mgr_name = original_manager.name

    if form.validate_on_submit():
        employee.name = form.name.data
        employee.title = form.title.data
        employee.department = form.department.data
        employee.email = form.email.data
        employee.phone = form.phone.data
        employee.picture_url = form.picture_url.data
        employee.reports_to = form.reports_to.data
        employee.bio = form.bio.data
        employee.location = form.location.data
        db.session.commit()

        #action for title change
        if form.title.data != original_title:
            action = Action(description=f"Title changed from {original_title} to {form.title.data}", from_id=employee.id)
            db.session.add(action)
            db.session.commit()
        #action for department change
        if form.department.data != original_department:
            action = Action(description=f"Department changed from {original_department} to {form.department.data}", from_id=employee.id)
            db.session.add(action)
            db.session.commit()
        #action for reports_to change but get name of manager
        if form.reports_to.data != original_reports_to:
            new_manager = None
            if form.reports_to.data:
                new_manager = Employee.query.get(form.reports_to.data)
            
            if original_mgr_name and new_manager:
                action = Action(description=f"Manager changed from {original_mgr_name} to {new_manager.name}", from_id=employee.id)
            elif original_mgr_name:
                action = Action(description=f"Manager removed (was {original_mgr_name})", from_id=employee.id)
            elif new_manager:
                action = Action(description=f"Manager set to {new_manager.name}", from_id=employee.id)
            
            if action:
                db.session.add(action)
                db.session.commit()
        #action for name change
        if form.name.data != original_name:
            action = Action(description=f"Name changed from {original_name} to {form.name.data}", from_id=employee.id)
            db.session.add(action)
            db.session.commit()
        #action for bio change
        if form.bio.data != original_bio:
            action = Action(description=f"Bio changed from {original_bio} to {form.bio.data}", from_id=employee.id)
            db.session.add(action)
            #gain xp for bio change
            employee_xp.xp += xp_actions['update_bio']
            db.session.commit()

        #action for location change
        if form.location.data != original_location:
            action = Action(description=f"Location changed from {original_location} to {form.location.data}", from_id=employee.id)
            db.session.add(action)
            #gain xp for location change
            employee_xp.xp += xp_actions['update_bio']
            db.session.commit()
        return redirect(url_for('view_employee', id=employee.id))
    return render_template('add_edit_employee.html', form=form)

@app.route('/search')
def search():
    query = request.args.get('query')
    results = Employee.query.filter(Employee.name.contains(query)).all()
    #also allow search by id
    if not results:
        results = Employee.query.filter(Employee.id.contains(query)).all()
    return render_template('search_results.html', results=results)

@app.route('/employee/<int:id>/add_image', methods=['GET', 'POST'])
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
                return render_template('add_image.html', form=form)
        
        image = EmployeeImage(image_url=image_url, employee_id=id, caption=form.caption.data)
        db.session.add(image)
        db.session.commit()
        flash('Image added successfully!')
        return redirect(url_for('view_employee', id=id))
    return render_template('add_image.html', form=form)

@app.route('/employee/<int:id>/add_video', methods=['GET', 'POST'])
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
                video_file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'videos', filename)
                print(f"DEBUG: Video saved to: {video_file_path}")
            else:
                print(f"ERROR: Failed to save video file")
                flash('Error saving uploaded video file.')
                return render_template('add_video.html', form=form)
        
        # Handle thumbnail - either from URL, uploaded file, or auto-generated
        thumbnail_url = form.thumbnail_url.data
        if form.thumbnail_file.data:
            saved_thumbnail_path = save_uploaded_file(form.thumbnail_file.data, 'thumbnails')
            if saved_thumbnail_path:
                thumbnail_url = f"/static/{saved_thumbnail_path}"
            else:
                flash('Error saving uploaded thumbnail file.')
                return render_template('add_video.html', form=form)
        elif not thumbnail_url and video_file_path:
            # Auto-generate thumbnail from video if no thumbnail provided
            print(f"DEBUG: Attempting to auto-generate thumbnail for video: {video_file_path}")
            try:
                # Generate a unique thumbnail filename
                thumbnail_filename = f"{uuid.uuid4().hex}_auto_thumb.jpg"
                thumbnail_path = os.path.join(app.config['UPLOAD_FOLDER'], 'thumbnails', thumbnail_filename)
                
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
        return redirect(url_for('view_employee', id=id))
    return render_template('add_video.html', form=form)

@app.route('/add_comment/<id>', methods=['POST'])
def add_comment(id):
    content = request.form.get('content')
    author_id = request.form.get('author_id', type=int)
    author = Employee.query.get(author_id)
    author_name = author.name
    recipient = Employee.query.get(id)
    recipient_name = recipient.name
    comment = Comment(content=content, employee_id=id, author_id=author_id)

    author_xp = EmployeeXP.query.filter_by(employee_id=author_id).first()
    if author_xp is None:
        author_xp = EmployeeXP(employee_id=author_id, xp=0)  # initialize xp to 0
        db.session.add(author_xp)
    
    # Award XP to the author for leaving a comment
    author_xp.xp += xp_actions['send_comment']  # adjust the amount of XP as needed
    author_xp.level = calculate_level(author_xp.xp)
    #print author name and xp
    print(f'author: {author_name} xp: {author_xp.xp}')

    #award xp to recipient
    recipient_xp = EmployeeXP.query.filter_by(employee_id=id).first()
    if recipient_xp is None:
        recipient_xp = EmployeeXP(employee_id=id, xp=0)  # initialize xp to 0
        db.session.add(recipient_xp)
    recipient_xp.xp += xp_actions['receive_comment']  # adjust the amount of XP as needed
    recipient_xp.level = calculate_level(recipient_xp.xp)
    #print recipient name and xp
    print(f'recipient: {recipient_name} xp: {recipient_xp.xp}')

    db.session.add(comment)
    action = Action(description=f"New comment by {author_name} to {recipient_name}: {content}", from_id=author_id, to_id=id)
    db.session.add(action)
    db.session.commit()
    return render_template('comment.html', comment=comment)
    #return redirect(url_for('view_employee', id=id))

@app.route('/test_comment', methods=['GET', 'POST'])
def comment():
    if request.method == 'POST':
        from_employee = request.form.get('from')
        to_employee = request.form.get('to')
        content = request.form.get('comment')
        comment = Comment(content=content, employee_id=to_employee, author_id=from_employee)
        db.session.add(comment)
        db.session.commit()

        # Award XP to recipient
        recipient_xp = EmployeeXP.query.filter_by(employee_id=to_employee).first()
        if recipient_xp is None:
            recipient_xp = EmployeeXP(employee_id=to_employee, xp=0)
            db.session.add(recipient_xp)
        recipient_xp.xp += xp_actions['receive_comment']
        recipient_xp.level = calculate_level(recipient_xp.xp)
        print(f'recipient: {to_employee} xp: {recipient_xp.xp}')

        # Award XP to author
        author_xp = EmployeeXP.query.filter_by(employee_id=from_employee).first()
        if author_xp is None:
            author_xp = EmployeeXP(employee_id=from_employee, xp=0)
            db.session.add(author_xp)
        author_xp.xp += xp_actions['send_comment']
        author_xp.level = calculate_level(author_xp.xp)
        print(f'author: {from_employee} xp: {author_xp.xp}')

        fromname = Employee.query.get(from_employee).name
        toname = Employee.query.get(to_employee).name

        action = Action(description=f"New comment by {fromname} to {toname}: {content}", from_id=from_employee, to_id=to_employee)

        db.session.add(action)
        db.session.commit()

        flash('Comment submitted successfully')
        return redirect(url_for('comment'))

    comments = db.session.query(Comment).join(Employee, Comment.employee_id == Employee.id).order_by(Comment.id.desc()).limit(5).all()
    for comment in comments:
        comment.from_employee = Employee.query.get(comment.author_id)
        comment.to_employee = Employee.query.get(comment.employee_id)

    statuses = Status.query.order_by(Status.timestamp.desc()).limit(5).all()
    return render_template('test_comment.html', comments=comments)


@app.route('/department/<department_name>', methods=['GET'])
def list_employees_by_department(department_name):
    return redirect(url_for('list_employees', department=department_name))

@app.route('/recent_actions', methods=['GET'])
def recent_actions():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    actions = Action.query.order_by(Action.timestamp.desc()).paginate(page=page, per_page=per_page, error_out=False)
    #remove duplicate actions
    actions.items = list(set(actions.items))
    next_url = url_for('recent_actions', page=actions.next_num) if actions.has_next else None
    prev_url = url_for('recent_actions', page=actions.prev_num) if actions.has_prev else None
    return render_template('recent_actions.html', actions=actions.items, next_url=next_url, prev_url=prev_url)

@app.route('/add_to_group/<int:id>', methods=['POST'])
def add_to_group(id):
    group_name = request.form.get('groupname')
    group = Group.query.filter_by(groupname=group_name).first()
    employee = Employee.query.get(id)

    print(f'debug: group_name: {group_name} group: {group} employee: {employee}')
    
    if group is None:
        flash('Group not found.')
        return redirect(url_for('view_employee', id=id))

    if employee is None:
        flash('Employee not found.')
        return redirect(url_for('view_employee', id=id))

    group.members.append(employee)
    db.session.commit()
    return redirect(url_for('view_employee', id=id))

@app.route('/manage_groups', methods=['GET', 'POST'])
def manage_groups():
    if request.method == 'POST':
        groupname = request.form.get('groupname')
        if groupname:
            group = Group(groupname=groupname)
            db.session.add(group)
            db.session.commit()
            flash('Group created.')
        else:
            flash('Group name is required.')
    groups = Group.query.all()
    return render_template('manage_groups.html', groups=groups)

@app.route('/view_group/<int:id>', methods=['GET'])
def view_group(id):
    group = Group.query.get(id)
    if group is None:
        flash('Group not found.')
        return redirect(url_for('manage_groups'))
    
    members = group.members.all()
    comments = group.comments  # This will get comments in descending order
    return render_template('view_group.html', group=group, members=members, comments=comments)

@app.route('/group/<int:id>/add_comment', methods=['POST'])
def add_group_comment(id):
    content = request.form.get('content')
    author_id = request.form.get('author_id')
    
    if not content or not author_id:
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Validate author exists
    author = Employee.query.get(author_id)
    if not author:
        return jsonify({'error': 'Invalid author ID'}), 400
    
    # Get group first
    group = Group.query.get(id)
    if not group:
        return jsonify({'error': 'Invalid group ID'}), 400
    
    comment = GroupComment(
        content=content,
        group_id=id,
        author_id=author_id
    )
    
    db.session.add(comment)
    
    # Add an action for the group comment
    action = Action(
        description=f"New group comment by {author.name} in {group.groupname}: {content}", 
        from_id=author_id
    )
    db.session.add(action)
    
    db.session.commit()
    
    # Return the HTML for the new comment
    return render_template('_group_comment.html', comment=comment)

leaderboard_size = 50
@app.route('/leaderboard')
def leaderboard():
    employees = EmployeeXP.query.order_by(EmployeeXP.xp.desc()).limit(leaderboard_size).all()

    # Render the leaderboard template
    return render_template('leaderboard.html', employees=employees)

previous_positions = {}

@app.route('/get_leaderboard_data')
def get_leaderboard_data():
    employees = EmployeeXP.query.order_by(EmployeeXP.xp.desc()).limit(leaderboard_size).all()
    employee_data = []
    for i, e in enumerate(employees):
        previous_position = previous_positions.get(e.employee.id)
        employee_data.append({"id": e.employee.id, "name": e.employee.name, "xp": e.xp, "previous_position": previous_position})
        # Update the previous position
        previous_positions[e.employee.id] = i + 1
    return jsonify({"employees": employee_data})

def get_management_chain(employee, levels=3):
    """Recursively fetches up to `levels` of managers for a given employee."""
    chain = []
    current = employee
    while current and levels > 0:
        if current.reports_to:
            manager = Employee.query.get(current.reports_to)
            chain.append(manager)
            current = manager
            levels -= 1
        else:
            break
    return chain

@app.route('/generate_comment', methods=['POST'])
def generate_comment():
    from_employee = request.form.get('from')
    to_employee = request.form.get('to')
    context = request.form.get('context')

    prompt = f"From: {from_employee}\nTo: {to_employee}\nContext: {context}"
    generated_comment = generate_text_from_prompt(prompt)

    return jsonify({'generated_comment': generated_comment})


@app.route('/generate_context', methods=['POST'])
def generate_context():
    from_employee_id = request.form.get('from')
    to_employee_id = request.form.get('to')

    from_employee = Employee.query.get(from_employee_id)
    to_employee = Employee.query.get(to_employee_id)

    if from_employee and to_employee:
        context = (
            f"From Employee: {from_employee.name}, {from_employee.title}, {from_employee.department}, "
            f"{from_employee.bio}, {from_employee.location}\n"
            f"To Employee: {to_employee.name}, {to_employee.title}, {to_employee.department}, "
            f"{to_employee.bio}, {to_employee.location}"
        )
    else:
        context = "Invalid employee IDs provided."

    return jsonify({'context': context})

@app.route('/set_profile_picture', methods=['POST'])
def set_profile_picture():
    employee_id = request.form.get('employee_id')
    image_url = request.form.get('image_url')

    employee = Employee.query.get(employee_id)
    if employee:
        employee.picture_url = image_url
        db.session.commit()
        return jsonify({'success': True}), 200
    else:
        return jsonify({'error': 'Employee not found'}), 404
    
@app.route('/files/<path:filename>')
def serve_static_files(filename):
    return send_from_directory(app.static_folder, filename)

@app.route('/files')
@app.route('/files/<path:subpath>')
def list_files(subpath=''):
    directory = os.path.join(app.static_folder, subpath)
    if not os.path.exists(directory):
        return "Directory not found", 404

    files = []
    directories = []
    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)
        if os.path.isdir(item_path):
            directories.append(item)
        else:
            files.append(item)

    return render_template('file_directory.html', files=files, directories=directories, subpath=subpath)

def calculate_level(xp):
    # Define the XP requirement for each level
    level = 1
    while xp >= level * 100:
        xp -= level * 100
        level += 1
    return level

@app.route('/delete_comment/<int:comment_id>', methods=['POST'])
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    db.session.delete(comment)
    db.session.commit()
    return jsonify({'success': True}), 200

from sqlalchemy.exc import IntegrityError

@app.route('/employee/<int:id>/add_friend', methods=['POST'])
def add_friend(id):
    employee = Employee.query.get_or_404(id)
    friend_id = request.form.get('friend_id', type=int)
    friend = Employee.query.get(friend_id)

    if friend is None:
        return jsonify({'success': False, 'message': 'Friend not found.'})

    if employee.is_friend_with(friend):
        return jsonify({'success': False, 'message': 'Already friends.'})

    try:
        employee.add_friend(friend)
        friend.add_friend(employee)
        db.session.commit()
        return jsonify({'success': True, 'friend_name': friend.name})
    except IntegrityError:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Friendship already exists.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error adding friend: {str(e)}'})
    
@app.route('/post_status', methods=['POST'])
def post_status():
    employee_id = request.form.get('employee_id')
    content = request.form.get('content')
    
    if not employee_id or not content:
        flash('Employee ID and content are required.')
        return redirect(url_for('view_all_statuses'))
    
    employee = Employee.query.get(employee_id)
    if not employee:
        flash('Employee not found.')
        return redirect(url_for('view_all_statuses'))
    
    status = Status(employee_id=employee_id, content=content)
    db.session.add(status)
    db.session.commit()
    
    flash('Status posted successfully.')
    return redirect(url_for('view_all_statuses'))

@app.route('/statuses')
def view_all_statuses():
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Number of statuses per page
    
    statuses = Status.query.order_by(desc(Status.timestamp)).paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('all_statuses.html', statuses=statuses)

@app.route('/employee/delete/<int:id>', methods=['POST'])
def delete_employee(id):
    employee = Employee.query.get_or_404(id)
    
    # Delete associated records first
    Comment.query.filter((Comment.employee_id == id) | (Comment.author_id == id)).delete()
    Action.query.filter((Action.from_id == id) | (Action.to_id == id)).delete()
    EmployeeImage.query.filter_by(employee_id=id).delete()
    EmployeeVideo.query.filter_by(employee_id=id).delete()
    EmployeeXP.query.filter_by(employee_id=id).delete()
    Status.query.filter_by(employee_id=id).delete()
    
    # Remove from groups
    for group in employee.groups:
        group.members.remove(employee)
    
    # Remove friendships - replace clear() with proper relationship removal
    for friend in employee.friends:
        employee.friends.remove(friend)
        friend.friends.remove(employee)
    
    # Delete the employee
    db.session.delete(employee)
    db.session.commit()
    
    flash('Employee deleted successfully')
    return redirect(url_for('list_employees'))

@app.route('/test_message')
def test_message():
    # Get all employees to populate the coworker dropdowns on the conversation simulation page
    employees = Employee.query.all()
    return render_template('test_message.html', employees=employees)

@app.route('/get_im_prompt_preview', methods=['POST'])
def get_im_prompt_preview():
    from_id = request.form.get('from')
    to_id = request.form.get('to')
    context = request.form.get('context')
    conversation_history = request.form.get('conversation', '')
    from_employee = Employee.query.get(from_id)
    to_employee = Employee.query.get(to_id)

    if not from_employee or not to_employee:
        return jsonify({'error': 'Invalid employee IDs'}), 400

    prompt = f"""Simulate an instant messaging conversation between two coworkers with distinct personalities.

Coworker 1:
Name: {from_employee.name}
Title: {from_employee.title}
Department: {from_employee.department}
Bio: {from_employee.bio}
Location: {from_employee.location}

Coworker 2:
Name: {to_employee.name}
Title: {to_employee.title}
Department: {to_employee.department}
Bio: {to_employee.bio}
Location: {to_employee.location}

Situation Context: {context}

Conversation history:
{conversation_history}

Generate the next succinct message from {from_employee.name} replying to {to_employee.name} in an informal, chat-style tone. Do not include extra commentary.
"""
    return jsonify({'prompt': prompt})

@app.route('/generate_im_message', methods=['POST'])
def generate_im_message():
    from_id = request.form.get('from')
    to_id = request.form.get('to')
    context = request.form.get('context')
    conversation_history = request.form.get('conversation', '')
    custom_prompt = request.form.get('custom_prompt', '').strip()

    from_employee = Employee.query.get(from_id)
    to_employee = Employee.query.get(to_id)

    if not from_employee or not to_employee:
        return jsonify({'error': 'Invalid employee IDs'}), 400

    # Build the prompt
    if custom_prompt:
        prompt = custom_prompt
    else:
        prompt = f"""Simulate an instant messaging conversation between two coworkers with distinct personalities.

Coworker 1:
Name: {from_employee.name}
Title: {from_employee.title}
Department: {from_employee.department}
Bio: {from_employee.bio}
Location: {from_employee.location}

Coworker 2:
Name: {to_employee.name}
Title: {to_employee.title}
Department: {to_employee.department}
Bio: {to_employee.bio}
Location: {to_employee.location}

Situation Context: {context}

Conversation history:
{conversation_history}

Generate only the next message content as a reply from {from_employee.name} to {to_employee.name} in an informal, chat-style tone (copy style you see in history if there is any).
Do not include the sender's name,or any signature.
"""
    generated_message = generate_text_from_prompt(prompt)
    return jsonify({'generated_message': generated_message})

@app.route('/autocomplete_employee', methods=['GET'])
def autocomplete_employee():
    term = request.args.get('term', '')
    # Filter employees whose name contains the search term (case-insensitive)
    employees = Employee.query.filter(Employee.name.ilike(f'%{term}%')).limit(10).all()
    suggestions = []
    for emp in employees:
        suggestions.append({
            'label': f"{emp.name} ({emp.title})",
            'value': emp.id,
            'picture': emp.picture_url
        })
    return jsonify(suggestions)

@app.route('/set_gpt_engine', methods=['POST'])
def set_gpt_engine():
    """
    Set the GPT engine to use for generating messages.
    Accepts a POST parameter 'engine' which must be either 'gpt-4.1-mini' or 'gpt-4.1'.
    """
    engine = request.form.get('engine')
    if engine in ALLOWED_GPT_ENGINES:
        session['gpt_engine'] = engine
        return jsonify({'success': True, 'engine': engine}), 200
    else:
        return jsonify({'success': False, 'message': 'Invalid engine value.'}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5002)


with app.app_context():
    db.create_all()


