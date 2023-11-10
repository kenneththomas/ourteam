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
    return "Welcome to OurTeam!"

@app.route('/employees')
def list_employees():
    employees = Employee.query.all()
    return render_template('list_employees.html', employees=employees)

@app.route('/employee/<int:id>')
def view_employee(id):
    employee = Employee.query.get_or_404(id)
    manager = None
    if employee.reports_to:
        manager = Employee.query.get(employee.reports_to)  # Get the manager details
    subordinates = Employee.query.filter_by(reports_to=id).all()
    form = EmployeeForm(obj=employee)
    form.id.data = id
    return render_template('view_employee.html', employee=employee, subordinates=subordinates, manager=manager)

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
        return redirect(url_for('list_employees'))
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

if __name__ == '__main__':
    app.run(debug=True, port=5002)

'''
with app.app_context():
    db.create_all()
'''

