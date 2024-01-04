from flask import Flask, render_template, redirect, url_for, request, session, flash, jsonify
from models import db, Employee, EmployeeImage, Comment, Action, Group, EmployeeXP
from forms import EmployeeForm, AddImageUrlForm
from sqlalchemy import func, or_
from markupsafe import Markup

def nl2br(s):
    #html doesnt do newlines so we need to convert them to <br> tags
    return Markup(s.replace('\n', '<br>\n'))

xp_actions = {
    'send_comment': 10,
    'receive_comment': 5,
    'update_bio' : 10,
}

app = Flask(__name__)
app.jinja_env.filters['nl2br'] = nl2br
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ourteam.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key'
db.init_app(app)

@app.route('/')
def index():
    featured_employees = Employee.query.order_by(func.random()).limit(5).all()
    return render_template('index.html', featured_employees=featured_employees)

@app.route('/employees')
def list_employees():
    page = request.args.get('page', 1, type=int)
    employees = Employee.query.paginate(page=page, per_page=5)
    return render_template('list_employees.html', employees=employees)

@app.route('/employee/<int:id>')
def view_employee(id):
    employee = Employee.query.get_or_404(id)
    images = EmployeeImage.query.filter_by(employee_id=id).all()
    employee_xp = EmployeeXP.query.filter_by(employee_id=id).first()

    if not employee_xp:
        employee_xp = EmployeeXP(employee_id=id, xp=0)
        db.session.add(employee_xp)

    employee_xp.xp += 1
    #print employee name and xp gain
    print(f'employee: {employee.name} xp: {employee_xp.xp} +1 xp')
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
    return render_template('view_employee.html', employee=employee, recent_actions=recent_actions, 
                           subordinates=subordinates, manager_chain=manager_chain, images=images, comments=comments, co_manager=co_manager, employee_xp=employee_xp)

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
    #get original name of manager
    if employee.reports_to:
        original_mgr_name = Employee.query.get(employee.reports_to).name

    if form.validate_on_submit():
        employee.name = form.name.data
        employee.title = form.title.data
        employee.department = form.department.data
        employee.email = form.email.data
        employee.phone = form.phone.data
        employee.picture_url = form.picture_url.data
        employee.reports_to = form.reports_to.data
        employee.bio = form.bio.data
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
            manager = Employee.query.get(form.reports_to.data)
            action = Action(description=f"Manager changed from {original_mgr_name} to {manager.name}", from_id=employee.id)
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
        return redirect(url_for('view_employee', id=employee.id))
    return render_template('add_edit_employee.html', form=form)

@app.route('/search')
def search():
    query = request.args.get('query')
    results = Employee.query.filter(Employee.name.contains(query)).all()
    return render_template('search_results.html', results=results)

@app.route('/employee/<int:id>/add_image', methods=['GET', 'POST'])
def add_image(id):
    form = AddImageUrlForm()
    if form.validate_on_submit():
        image = EmployeeImage(image_url=form.image_url.data, employee_id=id)
        db.session.add(image)
        db.session.commit()
        return redirect(url_for('view_employee', id=id))
    return render_template('add_image.html', form=form)

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
    #print author name and xp
    print(f'author: {author_name} xp: {author_xp.xp}')

    #award xp to recipient
    recipient_xp = EmployeeXP.query.filter_by(employee_id=id).first()
    if recipient_xp is None:
        recipient_xp = EmployeeXP(employee_id=id, xp=0)  # initialize xp to 0
        db.session.add(recipient_xp)
    recipient_xp.xp += xp_actions['receive_comment']  # adjust the amount of XP as needed
    #print recipient name and xp
    print(f'recipient: {recipient_name} xp: {recipient_xp.xp}')

    db.session.add(comment)
    action = Action(description=f"New comment by {author_name} to {recipient_name}: {content}", from_id=author_id, to_id=id)
    db.session.add(action)
    db.session.commit()
    return render_template('comment.html', comment=comment)
    #return redirect(url_for('view_employee', id=id))

@app.route('/department/<department_name>', methods=['GET'])
def list_employees_by_department(department_name):
    employees = Employee.query.filter_by(department=department_name).all()
    return render_template('department_employees.html', employees=employees, department_name=department_name)

@app.route('/recent_actions', methods=['GET'])
def recent_actions():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    actions = Action.query.order_by(Action.timestamp.desc()).paginate(page=page, per_page=per_page, error_out=False)
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
    return render_template('view_group.html', group=group)

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5002)


with app.app_context():
    db.create_all()


