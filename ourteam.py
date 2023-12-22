from flask import Flask, render_template, redirect, url_for, request, session, flash
from models import db, Employee, EmployeeImage, Comment, Action, Group
from forms import EmployeeForm, AddImageUrlForm
from sqlalchemy import func

app = Flask(__name__)
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
    comments = Comment.query.filter_by(employee_id=id).order_by(Comment.timestamp.desc()).all()
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
    return render_template('view_employee.html', employee=employee, subordinates=subordinates, manager_chain=manager_chain, images=images, comments=comments)

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

    #get original values for actions
    original_title = employee.title
    original_department = employee.department
    original_reports_to = employee.reports_to
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
    comment = Comment(content=content, employee_id=id, author_id=author_id)
    db.session.add(comment)
    action = Action(description=f"New comment by {author_id}: {content}", from_id=author_id, to_id=id)
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


