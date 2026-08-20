import os
import uuid
from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, session, url_for
from sqlalchemy import String, cast, desc, func, or_, text
from sqlalchemy.exc import IntegrityError
from models import db, Employee, EmployeeImage, EmployeeVideo, Comment, Action, Group, EmployeeXP, Status, GroupComment
from forms import EmployeeForm, AddImageUrlForm, AddVideoUrlForm
from services import generate_text_from_prompt

from flask import Blueprint
bp=Blueprint('ai',__name__)

@bp.route('/generate_comment', methods=['POST'])
def generate_comment():
    from_employee = db.session.get(Employee, request.form.get('from'))
    to_employee = db.session.get(Employee, request.form.get('to'))
    context = request.form.get('context')

    if not from_employee or not to_employee:
        return jsonify({'error': 'Invalid employee IDs'}), 400

    prompt = (
        f"From: {from_employee.name}, {from_employee.title}, {from_employee.company}, "
        f"{from_employee.department}\nTo: {to_employee.name}, {to_employee.title}, "
        f"{to_employee.company}, {to_employee.department}\nContext: {context}"
    )
    generated_comment = generate_text_from_prompt(prompt)

    return jsonify({'generated_comment': generated_comment})


@bp.route('/generate_context', methods=['POST'])
def generate_context():
    from_employee_id = request.form.get('from')
    to_employee_id = request.form.get('to')

    from_employee = db.session.get(Employee, from_employee_id)
    to_employee = db.session.get(Employee, to_employee_id)

    if from_employee and to_employee:
        context = (
            f"From Employee: {from_employee.name}, {from_employee.title}, {from_employee.company}, {from_employee.department}, "
            f"{from_employee.bio}, {from_employee.location}\n"
            f"To Employee: {to_employee.name}, {to_employee.title}, {to_employee.company}, {to_employee.department}, "
            f"{to_employee.bio}, {to_employee.location}"
        )
    else:
        context = "Invalid employee IDs provided."

    return jsonify({'context': context})

@bp.route('/set_profile_picture', methods=['POST'])
def set_profile_picture():
    employee_id = request.form.get('employee_id')
    image_url = request.form.get('image_url')

    employee = db.session.get(Employee, employee_id)
    if employee:
        employee.picture_url = image_url
        db.session.commit()
        return jsonify({'success': True}), 200
    else:
        return jsonify({'error': 'Employee not found'}), 404
    
@bp.route('/files')
@bp.route('/files/<path:subpath>')
def list_files(subpath=''):
    directory = os.path.abspath(os.path.join(current_app.static_folder, subpath))
    static_root = os.path.abspath(current_app.static_folder)
    if os.path.commonpath([directory, static_root]) != static_root:
        return "Directory not found", 404
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

    return render_template('file_directory_v2.html', files=files, directories=directories, subpath=subpath)

def calculate_level(xp):
    # Define the XP requirement for each level
    level = 1
    while xp >= level * 100:
        xp -= level * 100
        level += 1
    return level

@bp.route('/delete_comment/<int:comment_id>', methods=['POST'])
def delete_comment(comment_id):
    comment = db.get_or_404(Comment, comment_id)
    db.session.delete(comment)
    db.session.commit()
    return jsonify({'success': True}), 200

@bp.route('/delete_image/<int:image_id>', methods=['POST'])
def delete_image(image_id):
    image = db.get_or_404(EmployeeImage, image_id)
    
    # Delete the actual file if it's an uploaded file
    if image.image_url and image.image_url.startswith('/static/uploads/'):
        file_path = uploaded_file_path(image.image_url)
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
                print(f"Deleted image file: {file_path}")
        except Exception as e:
            print(f"Error deleting image file {file_path}: {str(e)}")
    
    db.session.delete(image)
    db.session.commit()
    return jsonify({'success': True}), 200

@bp.route('/delete_video/<int:video_id>', methods=['POST'])
def delete_video(video_id):
    video = db.get_or_404(EmployeeVideo, video_id)
    
    # Delete the actual video file if it's an uploaded file
    if video.video_url and video.video_url.startswith('/static/uploads/'):
        video_file_path = uploaded_file_path(video.video_url)
        try:
            if video_file_path and os.path.exists(video_file_path):
                os.remove(video_file_path)
                print(f"Deleted video file: {video_file_path}")
        except Exception as e:
            print(f"Error deleting video file {video_file_path}: {str(e)}")
    
    # Delete the thumbnail file if it's an uploaded file
    if video.thumbnail_url and video.thumbnail_url.startswith('/static/uploads/'):
        thumbnail_file_path = uploaded_file_path(video.thumbnail_url)
        try:
            if thumbnail_file_path and os.path.exists(thumbnail_file_path):
                os.remove(thumbnail_file_path)
                print(f"Deleted thumbnail file: {thumbnail_file_path}")
        except Exception as e:
            print(f"Error deleting thumbnail file {thumbnail_file_path}: {str(e)}")
    
    db.session.delete(video)
    db.session.commit()
    return jsonify({'success': True}), 200

from sqlalchemy.exc import IntegrityError

@bp.route('/employee/<int:id>/add_friend', methods=['POST'])
def add_friend(id):
    employee = db.get_or_404(Employee, id)
    friend_id = request.form.get('friend_id', type=int)
    friend = db.session.get(Employee, friend_id)

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
    
@bp.route('/post_status', methods=['POST'])
def post_status():
    employee_id = request.form.get('employee_id')
    content = request.form.get('content')
    
    if not employee_id or not content:
        flash('Employee ID and content are required.')
        return redirect(url_for('social.view_all_statuses'))
    
    employee = db.session.get(Employee, employee_id)
    if not employee:
        flash('Employee not found.')
        return redirect(url_for('social.view_all_statuses'))
    
    status = Status(employee_id=employee_id, content=content)
    db.session.add(status)
    db.session.commit()
    
    flash('Status posted successfully.')
    return redirect(url_for('social.view_all_statuses'))

@bp.route('/statuses')
def view_all_statuses():
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Number of statuses per page
    
    statuses = Status.query.order_by(desc(Status.timestamp)).paginate(page=page, per_page=per_page, error_out=False)
    all_employees = Employee.query.order_by(Employee.name).all()
    return render_template('all_statuses_v2.html', statuses=statuses, all_employees=all_employees)

@bp.route('/employee/delete/<int:id>', methods=['POST'])
def delete_employee(id):
    employee = db.get_or_404(Employee, id)

    # Association tables are not delete-orphan relationships, so unlink them
    # explicitly. Dependent employee records are removed by model cascades.
    for group in employee.groups:
        group.members.remove(employee)

    for friend in list(employee.friends):
        employee.friends.remove(friend)
        friend.friends.remove(employee)

    db.session.delete(employee)
    db.session.commit()
    
    flash('Employee deleted successfully')
    return redirect(url_for('employees.list_employees'))

@bp.route('/test_message')
def test_message():
    # Get all employees to populate the coworker dropdowns on the conversation simulation page
    employees = Employee.query.all()
    return render_template('test_message_v2.html', employees=employees)

@bp.route('/get_im_prompt_preview', methods=['POST'])
def get_im_prompt_preview():
    from_id = request.form.get('from')
    to_id = request.form.get('to')
    context = request.form.get('context')
    conversation_history = request.form.get('conversation', '')
    from_employee = db.session.get(Employee, from_id)
    to_employee = db.session.get(Employee, to_id)

    if not from_employee or not to_employee:
        return jsonify({'error': 'Invalid employee IDs'}), 400

    prompt = f"""Simulate an instant messaging conversation between two coworkers with distinct personalities.

Coworker 1:
Name: {from_employee.name}
Title: {from_employee.title}
Company: {from_employee.company}
Department: {from_employee.department}
Bio: {from_employee.bio}
Location: {from_employee.location}

Coworker 2:
Name: {to_employee.name}
Title: {to_employee.title}
Company: {to_employee.company}
Department: {to_employee.department}
Bio: {to_employee.bio}
Location: {to_employee.location}

Situation Context: {context}

Conversation history:
{conversation_history}

Generate the next succinct message from {from_employee.name} replying to {to_employee.name} in an informal, chat-style tone. Do not include extra commentary.
"""
    return jsonify({'prompt': prompt})

@bp.route('/generate_im_message', methods=['POST'])
def generate_im_message():
    from_id = request.form.get('from')
    to_id = request.form.get('to')
    context = request.form.get('context')
    conversation_history = request.form.get('conversation', '')
    custom_prompt = request.form.get('custom_prompt', '').strip()

    from_employee = db.session.get(Employee, from_id)
    to_employee = db.session.get(Employee, to_id)

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
Company: {from_employee.company}
Department: {from_employee.department}
Bio: {from_employee.bio}
Location: {from_employee.location}

Coworker 2:
Name: {to_employee.name}
Title: {to_employee.title}
Company: {to_employee.company}
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

@bp.route('/autocomplete_employee', methods=['GET'])
def autocomplete_employee():
    term = request.args.get('term', '')
    # Filter employees whose name contains the search term (case-insensitive)
    employees = Employee.query.filter(Employee.name.ilike(f'%{term}%')).limit(10).all()
    suggestions = []
    for emp in employees:
        suggestions.append({
            'label': f"{emp.name} ({emp.title}, {emp.company})",
            'value': emp.id,
            'picture': emp.picture_url
        })
    return jsonify(suggestions)

@bp.route('/set_gpt_engine', methods=['POST'])
def set_gpt_engine():
    """Set the allowed OpenRouter model used for generated messages."""
    engine = request.form.get('engine')
    if engine in current_app.config['ALLOWED_GPT_ENGINES']:
        session['gpt_engine'] = engine
        return jsonify({'success': True, 'engine': engine}), 200
    else:
        return jsonify({'success': False, 'message': 'Invalid engine value.'}), 400

