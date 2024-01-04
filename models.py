from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

employee_group = db.Table('employee_group',
    db.Column('employee_id', db.Integer, db.ForeignKey('employee.id'), primary_key=True),
    db.Column('group_id', db.Integer, db.ForeignKey('group.id'), primary_key=True)
)

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
    groups = db.relationship('Group', secondary=employee_group, backref=db.backref('members', lazy='dynamic'))
    bio = db.Column(db.String)
    location = db.Column(db.String)

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

class Action(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    from_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    to_id = db.Column(db.Integer, db.ForeignKey('employee.id'))

    from_employee = db.relationship('Employee', foreign_keys=[from_id])
    to_employee = db.relationship('Employee', foreign_keys=[to_id])

class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    groupname = db.Column(db.String(200), nullable=False)

class EmployeeXP(db.Model):
    __tablename__ = 'employee_xp'

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'))
    xp = db.Column(db.Integer, default=0)

    # Define a relationship to the Employee model
    employee = db.relationship('Employee', backref='xp')