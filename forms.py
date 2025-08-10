from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, SubmitField, IntegerField, SelectField, HiddenField, TextAreaField
from wtforms.validators import DataRequired, Email, Optional, ValidationError

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
    image_url = StringField('Image URL', validators=[Optional()])
    image_file = FileField('Upload Image File', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], 'Only image files are allowed!')
    ])
    caption = StringField('Caption', validators=[Optional()])
    submit = SubmitField('Add Image')
    
    def validate(self, *args, **kwargs):
        if not super().validate(*args, **kwargs):
            return False
        if not self.image_url.data and not self.image_file.data:
            raise ValidationError('Please provide either an image URL or upload an image file.')
        return True

class AddVideoUrlForm(FlaskForm):
    video_url = StringField('Video URL', validators=[Optional()])
    video_file = FileField('Upload Video File', validators=[
        Optional(),
        FileAllowed(['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm'], 'Only video files are allowed!')
    ])
    caption = StringField('Caption', validators=[Optional()])
    thumbnail_url = StringField('Thumbnail URL (Optional)', validators=[Optional()])
    thumbnail_file = FileField('Upload Thumbnail Image', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], 'Only image files are allowed!')
    ])
    submit = SubmitField('Add Video')
    
    def validate(self, *args, **kwargs):
        if not super().validate(*args, **kwargs):
            return False
        if not self.video_url.data and not self.video_file.data:
            raise ValidationError('Please provide either a video URL or upload a video file.')
        return True