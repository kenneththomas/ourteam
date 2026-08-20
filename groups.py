import os
import uuid
from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, session, url_for
from sqlalchemy import String, cast, desc, func, or_, text
from sqlalchemy.exc import IntegrityError
from models import db, Employee, EmployeeImage, EmployeeVideo, Comment, Action, Group, EmployeeXP, Status, GroupComment
from forms import EmployeeForm, AddImageUrlForm, AddVideoUrlForm
leaderboard_size=50
previous_positions={}

from flask import Blueprint
bp=Blueprint('groups',__name__)

@bp.route('/add_to_group/<int:id>', methods=['POST'])
def add_to_group(id):
    group_name = request.form.get('groupname')
    group = Group.query.filter_by(groupname=group_name).first()
    employee = db.session.get(Employee, id)

    print(f'debug: group_name: {group_name} group: {group} employee: {employee}')
    
    if group is None:
        flash('Group not found.')
        return redirect(url_for('employees.view_employee', id=id))

    if employee is None:
        flash('Employee not found.')
        return redirect(url_for('employees.view_employee', id=id))

    group.members.append(employee)
    db.session.commit()
    return redirect(url_for('employees.view_employee', id=id))

@bp.route('/manage_groups', methods=['GET', 'POST'])
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
    return render_template('manage_groups_v2.html', groups=groups)

@bp.route('/view_group/<int:id>', methods=['GET'])
def view_group(id):
    group = db.session.get(Group, id)
    if group is None:
        flash('Group not found.')
        return redirect(url_for('groups.manage_groups'))
    
    members = group.members.all()
    comments = group.comments  # This will get comments in descending order
    all_employees = Employee.query.order_by(Employee.name).all()
    return render_template('view_group_v2.html', group=group, members=members, comments=comments, all_employees=all_employees)

@bp.route('/group/<int:id>/add_comment', methods=['POST'])
def add_group_comment(id):
    content = request.form.get('content')
    author_id = request.form.get('author_id')
    
    if not content or not author_id:
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Validate author exists
    author = db.session.get(Employee, author_id)
    if not author:
        return jsonify({'error': 'Invalid author ID'}), 400
    
    # Get group first
    group = db.session.get(Group, id)
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
    return render_template('group_comment_v2.html', comment=comment)

@bp.route('/leaderboard')
def leaderboard():
    employees = EmployeeXP.query.order_by(EmployeeXP.xp.desc()).limit(leaderboard_size).all()

    # Render the leaderboard template
    return render_template('leaderboard_v2.html', employees=employees)


@bp.route('/get_leaderboard_data')
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
            manager = db.session.get(Employee, current.reports_to)
            chain.append(manager)
            current = manager
            levels -= 1
        else:
            break
    return chain

