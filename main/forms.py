from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField
from wtforms.validators import DataRequired, URL, NumberRange
from flask_ckeditor import CKEditorField


class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")


class CommentForm(FlaskForm):
    comment = CKEditorField("Comment", validators=[DataRequired()])
    submit = SubmitField("Submit Comment")


class RatingForm(FlaskForm):
    rating = FloatField('Enter a rating between 0 and 10', validators=[DataRequired(), NumberRange(min=0, max=10, message="Rating must be between 0 and 10")])
    submit = SubmitField("Submit Rating")


class RequestForm(FlaskForm):
    reason = StringField("Reason for Request", validators=[DataRequired()])
    submit = SubmitField("Submit Request")
