from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, SelectField, HiddenField
from wtforms.validators import DataRequired, Email, Optional

class EmployeeForm(FlaskForm):
    id = HiddenField('ID')
    name = StringField('Name', validators=[DataRequired()])
    title = StringField('Title', validators=[DataRequired()])
    department = StringField('Department')
    email = StringField('Email', validators=[Optional()]) # removed Email()
    phone = StringField('Phone', validators=[Optional()])
    picture_url = StringField('Picture URL', validators=[Optional()])
    reports_to = IntegerField('Reports To', validators=[Optional()])
    submit = SubmitField('Submit')