from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    title = db.Column(db.String, nullable=False)
    department = db.Column(db.String)
    email = db.Column(db.String)
    phone = db.Column(db.String)
    picture_url = db.Column(db.String)
    reports_to = db.Column(db.Integer, db.ForeignKey('employee.id'))

class Department(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    manager_id = db.Column(db.Integer, db.ForeignKey('employee.id'))