from flask import Flask, render_template, redirect, url_for
from models import db, Employee
from forms import EmployeeForm

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ourteam.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key'
db.init_app(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/employees')
def list_employees():
    employees = Employee.query.all()
    return render_template('list_employees.html', employees=employees)

@app.route('/employee/<int:id>')
def view_employee(id):
    employee = Employee.query.get_or_404(id)
    manager_chain = None
    if employee.reports_to:
        manager_chain = get_management_chain(employee)
        manager_chain = list(reversed(manager_chain))
    subordinates = Employee.query.filter_by(reports_to=id).all()
    form = EmployeeForm(obj=employee)
    form.id.data = id
    return render_template('view_employee.html', employee=employee, subordinates=subordinates, manager_chain=manager_chain)

@app.route('/employee/add', methods=['GET', 'POST'])
def add_employee():
    form = EmployeeForm()
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
        return redirect(url_for('view_employee', id=new_employee.id))
    return render_template('add_edit_employee.html', form=form)

@app.route('/employee/edit/<int:id>', methods=['GET', 'POST'])
def edit_employee(id):
    employee = Employee.query.get_or_404(id)
    form = EmployeeForm(obj=employee)
    if form.validate_on_submit():
        employee.name = form.name.data
        employee.title = form.title.data
        employee.department = form.department.data
        employee.email = form.email.data
        employee.phone = form.phone.data
        employee.picture_url = form.picture_url.data
        employee.reports_to = form.reports_to.data
        db.session.commit()
        return redirect(url_for('view_employee', id=employee.id))
    return render_template('add_edit_employee.html', form=form)

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

'''
with app.app_context():
    db.create_all()
'''

