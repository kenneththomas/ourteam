from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

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
    images = db.relationship('EmployeeImage', backref='employee', lazy=True)

class Department(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    manager_id = db.Column(db.Integer, db.ForeignKey('employee.id'))

class EmployeeImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_url = db.Column(db.String(500), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)

    employee = db.relationship('Employee', foreign_keys=[employee_id])
    author = db.relationship('Employee', foreign_keys=[author_id])