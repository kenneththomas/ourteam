import os
import uuid
from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, session, url_for
from sqlalchemy import String, cast, desc, func, or_, text
from sqlalchemy.exc import IntegrityError
from models import db, Employee, EmployeeImage, EmployeeVideo, Comment, Action, Group, EmployeeXP, Status, GroupComment
from forms import EmployeeForm, AddImageUrlForm, AddVideoUrlForm
from services import calculate_level, xp_actions

from flask import Blueprint
bp=Blueprint('social',__name__)

@bp.route('/add_comment/<id>', methods=['POST'])
def add_comment(id):
    content = request.form.get('content')
    author_id = request.form.get('author_id', type=int)
    author = db.session.get(Employee, author_id)
    author_name = author.name
    recipient = db.session.get(Employee, id)
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
    return render_template('comment_v2.html', comment=comment)
    #return redirect(url_for('employees.view_employee', id=id))

@bp.route('/test_comment', methods=['GET', 'POST'])
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

        fromname = db.session.get(Employee, from_employee).name
        toname = db.session.get(Employee, to_employee).name

        action = Action(description=f"New comment by {fromname} to {toname}: {content}", from_id=from_employee, to_id=to_employee)

        db.session.add(action)
        db.session.commit()

        flash('Comment submitted successfully')
        return redirect(url_for('social.comment'))

    comments = db.session.query(Comment).join(Employee, Comment.employee_id == Employee.id).order_by(Comment.id.desc()).limit(5).all()
    for comment in comments:
        comment.from_employee = db.session.get(Employee, comment.author_id)
        comment.to_employee = db.session.get(Employee, comment.employee_id)

    statuses = Status.query.order_by(Status.timestamp.desc()).limit(5).all()
    employees = Employee.query.order_by(Employee.name).all()
    return render_template('test_comment_v2.html', comments=comments, employees=employees)


@bp.route('/department/<department_name>', methods=['GET'])
def list_employees_by_department(department_name):
    return redirect(url_for('employees.list_employees', department=department_name))

@bp.route('/recent_actions', methods=['GET'])
def recent_actions():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    actions = Action.query.order_by(Action.timestamp.desc()).paginate(page=page, per_page=per_page, error_out=False)
    #remove duplicate actions
    actions.items = list(set(actions.items))
    next_url = url_for('recent_actions', page=actions.next_num) if actions.has_next else None
    prev_url = url_for('recent_actions', page=actions.prev_num) if actions.has_prev else None
    return render_template('recent_actions_v2.html', actions=actions.items, next_url=next_url, prev_url=prev_url)


