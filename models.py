from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy.orm import relationship

db = SQLAlchemy()

employee_group = db.Table('employee_group',
    db.Column('employee_id', db.Integer, db.ForeignKey('employee.id', ondelete='CASCADE'), primary_key=True),
    db.Column('group_id', db.Integer, db.ForeignKey('group.id', ondelete='CASCADE'), primary_key=True)
)

employee_friends = db.Table('employee_friends',
    db.Column('employee_id', db.Integer, db.ForeignKey('employee.id', ondelete='CASCADE'), primary_key=True),
    db.Column('friend_id', db.Integer, db.ForeignKey('employee.id', ondelete='CASCADE'), primary_key=True)
)

class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    title = db.Column(db.String, nullable=False)
    company = db.Column(db.String, nullable=False, default='OurTeam Industries')
    department = db.Column(db.String)
    email = db.Column(db.String, unique=True, index=True)
    phone = db.Column(db.String)
    picture_url = db.Column(db.String)
    reports_to = db.Column(db.Integer, db.ForeignKey('employee.id', ondelete='SET NULL'), index=True)
    manager = db.relationship(
        'Employee', remote_side=[id],
        backref=db.backref('direct_reports')
    )
    images = db.relationship(
        'EmployeeImage', backref='employee', lazy=True,
        cascade='all, delete-orphan'
    )
    videos = db.relationship(
        'EmployeeVideo', backref='employee', lazy=True,
        cascade='all, delete-orphan'
    )
    groups = db.relationship(
        'Group', secondary=employee_group,
        backref=db.backref('members', lazy='dynamic')
    )
    bio = db.Column(db.String)
    location = db.Column(db.String)
    friends = relationship(
        'Employee', 
        secondary=employee_friends,
        primaryjoin=(employee_friends.c.employee_id == id),
        secondaryjoin=(employee_friends.c.friend_id == id),
        backref=db.backref('befriended_by', lazy='dynamic'),
        lazy='dynamic'
    )

    def add_friend(self, friend):
        if friend not in self.friends and self != friend:
            self.friends.append(friend)
            return True
        return False

    def is_friend_with(self, friend):
        return friend in self.friends or self in friend.friends

    def remove_friend(self, friend):
        if friend in self.friends:
            self.friends.remove(friend)
            friend.friends.remove(self)

class Department(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    manager_id = db.Column(db.Integer, db.ForeignKey('employee.id', ondelete='SET NULL'), index=True)
    manager = db.relationship('Employee', backref='managed_departments')

class EmployeeImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_url = db.Column(db.String(500), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id', ondelete='CASCADE'), nullable=False, index=True)
    caption = db.Column(db.String(255), nullable=True)

class EmployeeVideo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    video_url = db.Column(db.String(500), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id', ondelete='CASCADE'), nullable=False, index=True)
    caption = db.Column(db.String(255), nullable=True)
    thumbnail_url = db.Column(db.String(500), nullable=True)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id', ondelete='CASCADE'), nullable=False, index=True)
    author_id = db.Column(db.Integer, db.ForeignKey('employee.id', ondelete='CASCADE'), nullable=False, index=True)

    employee = db.relationship(
        'Employee', foreign_keys=[employee_id],
        backref=db.backref('received_comments', cascade='all, delete-orphan')
    )
    author = db.relationship(
        'Employee', foreign_keys=[author_id],
        backref=db.backref('authored_comments', cascade='all, delete-orphan')
    )

class Action(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    from_id = db.Column(db.Integer, db.ForeignKey('employee.id', ondelete='CASCADE'), nullable=False, index=True)
    to_id = db.Column(db.Integer, db.ForeignKey('employee.id', ondelete='CASCADE'), index=True)

    from_employee = db.relationship(
        'Employee', foreign_keys=[from_id],
        backref=db.backref('sent_actions', cascade='all, delete-orphan')
    )
    to_employee = db.relationship(
        'Employee', foreign_keys=[to_id],
        backref=db.backref('received_actions', cascade='all, delete-orphan')
    )

class GroupComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id', ondelete='CASCADE'), nullable=False, index=True)
    author_id = db.Column(db.Integer, db.ForeignKey('employee.id', ondelete='CASCADE'), nullable=False, index=True)

    group = db.relationship('Group', backref=db.backref(
        'comments', lazy=True, order_by='desc(GroupComment.timestamp)',
        cascade='all, delete-orphan'
    ))
    author = db.relationship('Employee', backref=db.backref(
        'group_comments', lazy=True, cascade='all, delete-orphan'
    ))

class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    groupname = db.Column(db.String(200), nullable=False, unique=True, index=True)

class EmployeeXP(db.Model):
    __tablename__ = 'employee_xp'

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(
        db.Integer, db.ForeignKey('employee.id', ondelete='CASCADE'),
        nullable=False, unique=True, index=True
    )
    xp = db.Column(db.Integer, default=0)
    level = db.Column(db.Integer, default=1)

    # Define a relationship to the Employee model
    employee = db.relationship('Employee', backref=db.backref('xp', cascade='all, delete-orphan'))

class Status(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id', ondelete='CASCADE'), nullable=False, index=True)
    content = db.Column(db.String(280), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    employee = db.relationship(
        'Employee', backref=db.backref('statuses', lazy=True, cascade='all, delete-orphan')
    )
