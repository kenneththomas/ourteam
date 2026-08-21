import os
import uuid
from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, session, url_for
from sqlalchemy import String, cast, desc, func, or_, text
from sqlalchemy.exc import IntegrityError
from models import db, Employee, EmployeeImage, EmployeeVideo, Comment, Action, Group, EmployeeXP, Status, GroupComment
from forms import EmployeeForm, AddImageUrlForm, AddVideoUrlForm
from services import calculate_level, get_management_chain, markdown_to_html, xp_actions

from flask import Blueprint
bp=Blueprint('employees',__name__)

@bp.route('/preview/bio', methods=['POST'])
def preview_bio():
    return jsonify({'html': str(markdown_to_html(request.form.get('content', '')))})

@bp.route('/')
def index():
    # Get featured employees (most active based on XP)
    featured_employees = db.session.query(Employee, EmployeeXP)\
        .outerjoin(EmployeeXP)\
        .order_by(EmployeeXP.xp.desc().nullslast())\
        .limit(6)\
        .all()
    
    # Get some statistics
    total_employees = Employee.query.count()
    total_departments = db.session.query(Employee.department).distinct().count()
    total_comments = Comment.query.count()
    total_actions = Action.query.count()
    
    # Get recent activities
    recent_actions = Action.query.order_by(Action.timestamp.desc()).limit(5).all()
    recent_statuses = Status.query.order_by(Status.timestamp.desc()).limit(6).all()
    department_counts = db.session.query(
        Employee.department, func.count(Employee.id)
    ).group_by(Employee.department).order_by(func.count(Employee.id).desc()).all()
    
    return render_template('index_v2.html',
                         featured_employees=[emp for emp, _ in featured_employees],
                         total_employees=total_employees,
                         total_departments=total_departments,
                         total_comments=total_comments,
                         total_actions=total_actions,
                         recent_actions=recent_actions,
                         recent_statuses=recent_statuses,
                         department_counts=department_counts)

@bp.route('/employees')
def list_employees():
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Increased from 5 to show more employees
    
    # Add sorting options
    sort_by = request.args.get('sort', 'name')  # Default sort by name
    order = request.args.get('order', 'asc')
    
    company = request.args.get('company')
    department = request.args.get('department')
    
    # Base query
    query = Employee.query

    if company:
        query = query.filter_by(company=company)
    
    # Apply department filter if specified
    if department:
        query = query.filter_by(department=department)
    
    # Apply sorting
    if sort_by == 'name':
        query = query.order_by(Employee.name.asc() if order == 'asc' else Employee.name.desc())
    elif sort_by == 'department':
        query = query.order_by(Employee.department.asc() if order == 'asc' else Employee.department.desc())
    elif sort_by == 'company':
        query = query.order_by(Employee.company.asc() if order == 'asc' else Employee.company.desc())
    elif sort_by == 'title':
        query = query.order_by(Employee.title.asc() if order == 'asc' else Employee.title.desc())
    elif sort_by == 'level':
        query = query.join(EmployeeXP).order_by(
            EmployeeXP.xp.desc() if order == 'desc' else EmployeeXP.xp.asc()
        )
    
    # Get all unique departments for the filter dropdown, sorted alphabetically
    department_query = db.session.query(Employee.department)
    if company:
        department_query = department_query.filter(Employee.company == company)
    departments = department_query\
        .distinct()\
        .order_by(Employee.department)\
        .all()
    companies = db.session.query(Employee.company).distinct().order_by(Employee.company).all()
    
    employees = query.paginate(page=page, per_page=per_page)
    
    return render_template(
        'list_employees_v2.html',
        employees=employees,
        companies=companies,
        departments=departments,
        current_company=company,
        current_department=department,
        current_sort=sort_by,
        current_order=order
    )

@bp.route('/employee/<int:id>')
def view_employee(id):
    employee = db.get_or_404(Employee, id)
    images = EmployeeImage.query.filter_by(employee_id=id).all()
    videos = EmployeeVideo.query.filter_by(employee_id=id).all()
    employee_xp = EmployeeXP.query.filter_by(employee_id=id).first()

    if not employee_xp:
        employee_xp = EmployeeXP(employee_id=id, xp=0)

    level = calculate_level(employee_xp.xp)
    xp_at_level_start = 50 * level * (level - 1)
    next_level_xp = level * 100
    progress = max(0, employee_xp.xp - xp_at_level_start)

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
    session['previous_employee_company'] = employee.company
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
    all_employees = Employee.query.order_by(Employee.name).all()
    all_groups = Group.query.order_by(Group.groupname).all()

    return render_template('view_employee_v2.html', employee=employee, recent_actions=recent_actions,
                           subordinates=subordinates, manager_chain=manager_chain, images=images, 
                           videos=videos, comments=comments, co_manager=co_manager, employee_xp=employee_xp, 
                           next_level_xp=next_level_xp, progress=progress, recent_statuses=recent_statuses,
                           all_employees=all_employees, all_groups=all_groups, level=level)

@bp.route('/org_tree/<int:id>')
def org_tree(id):
    employee = db.get_or_404(Employee, id)
    
    # Get 2 levels of managers above
    managers = []
    current = employee
    for _ in range(2):
        if current.reports_to:
            manager = db.session.get(Employee, current.reports_to)
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
    department_members = Employee.query.filter_by(
        department=employee.department,
        company=employee.company,
    ).all()
    
    return render_template('org_tree_v2.html',
                         employee=employee,
                         managers=managers,
                         reports=reports,
                         department_members=department_members)

@bp.route('/post_status_from_profile', methods=['POST'])
def post_status_from_profile():
    employee_id = request.form.get('employee_id')
    content = request.form.get('content')
    
    if not employee_id or not content:
        flash('Employee ID and content are required.')
        return redirect(url_for('employees.view_employee', id=employee_id))
    
    employee = db.session.get(Employee, employee_id)
    if not employee:
        flash('Employee not found.')
        return redirect(url_for('employees.view_employee', id=employee_id))
    
    status = Status(employee_id=employee_id, content=content)
    db.session.add(status)
    db.session.commit()
    
    flash('Status posted successfully.')
    return redirect(url_for('employees.view_employee', id=employee_id))

@bp.route('/employee/add', methods=['GET', 'POST'])
def add_employee():
    form = EmployeeForm()
    if 'previous_employee_id' in session:
        form.reports_to.data = session['previous_employee_id']
        del session['previous_employee_id']
    if 'previous_employee_department' in session:
        form.department.data = session['previous_employee_department']
        del session['previous_employee_department']
    if 'previous_employee_company' in session:
        form.company.data = session['previous_employee_company']
        del session['previous_employee_company']
    elif request.method == 'GET':
        form.company.data = current_app.config['DEFAULT_COMPANY']
    if form.validate_on_submit():
        new_employee = Employee(
            name=form.name.data,
            title=form.title.data,
            company=form.company.data,
            department=form.department.data,
            email=form.email.data,
            phone=form.phone.data,
            picture_url=form.picture_url.data,
            reports_to=form.reports_to.data,
            bio=form.bio.data,
            location=form.location.data,
        )
        db.session.add(new_employee)
        db.session.commit()

        #action for new employee
        action = Action(description=f"New employee added: {new_employee.name} - {new_employee.company} / {new_employee.department}", from_id=new_employee.id)
        db.session.add(action)
        db.session.commit()

        return redirect(url_for('employees.view_employee', id=new_employee.id))
    all_employees = Employee.query.order_by(Employee.name).all()
    current_manager = db.session.get(Employee, form.reports_to.data) if form.reports_to.data else None
    return render_template('add_edit_employee_v2.html', form=form, all_employees=all_employees, current_manager=current_manager)

@bp.route('/employee/edit/<int:id>', methods=['GET', 'POST'])
def edit_employee(id):
    employee = db.get_or_404(Employee, id)
    form = EmployeeForm(obj=employee)

    #initialize xp gain
    employee_xp = EmployeeXP.query.filter_by(employee_id=id).first()
    if not employee_xp:
        employee_xp = EmployeeXP(employee_id=id, xp=0)
        db.session.add(employee_xp)

    #get original values for actions
    original_name = employee.name
    original_title = employee.title
    original_company = employee.company
    original_department = employee.department
    original_reports_to = employee.reports_to
    original_bio = employee.bio
    original_location = employee.location
    #get original name of manager
    original_mgr_name = None
    if employee.reports_to:
        original_manager = db.session.get(Employee, employee.reports_to)
        if original_manager:
            original_mgr_name = original_manager.name

    if form.validate_on_submit():
        employee.name = form.name.data
        employee.title = form.title.data
        employee.company = form.company.data
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
        if form.company.data != original_company:
            action = Action(description=f"Company changed from {original_company} to {form.company.data}", from_id=employee.id)
            db.session.add(action)
            db.session.commit()
        #action for reports_to change but get name of manager
        if form.reports_to.data != original_reports_to:
            action = None
            new_manager = None
            if form.reports_to.data:
                new_manager = db.session.get(Employee, form.reports_to.data)
            
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
        return redirect(url_for('employees.view_employee', id=employee.id))
    all_employees = Employee.query.order_by(Employee.name).all()
    current_manager = db.session.get(Employee, form.reports_to.data) if form.reports_to.data else None
    return render_template('add_edit_employee_v2.html', form=form, all_employees=all_employees, current_manager=current_manager)

@bp.route('/search')
def search():
    query = (request.args.get('query') or '').strip()
    if not query:
        return render_template('search_results_v2.html', results=[])
    results = Employee.query.filter(or_(
        Employee.name.ilike(f'%{query}%'),
        cast(Employee.id, String) == query,
    )).all()
    return render_template('search_results_v2.html', results=results)
