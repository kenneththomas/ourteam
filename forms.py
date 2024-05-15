from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, SelectField, HiddenField, TextAreaField
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
    bio = TextAreaField('Bio', validators=[Optional()])
    location = StringField('Location', validators=[Optional()])
    submit = SubmitField('Submit')

class AddImageUrlForm(FlaskForm):
    image_url = StringField('Image URL', validators=[DataRequired()])
    caption = StringField('Caption', validators=[Optional()])
    submit = SubmitField('Add Image')