from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import current_user, login_required
from models.models import Comment
from models.transactions import DatabaseError, get_by_id, put, delete
from extensions import limiter
from .forms import CommentForm


comment_bp = Blueprint('comment', __name__)


@comment_bp.route("/edit-comment/<int:comment_id>", methods=["GET", "POST"])
@limiter.limit("15 per hour")
@login_required
def edit_comment(comment_id):
    try:
        comment = get_by_id(model=Comment, id_reference=comment_id)
    except DatabaseError as e:
        flash(e.message, 'error')
        return redirect(url_for('comment.edit_comment', comment_id=comment_id))

    form = CommentForm(comment=comment.text)

    if comment.author_id != current_user.id:
        flash('You are not allowed to edit this comment!', "error")
        return redirect(url_for('main.user'))

    if form.submit.data and form.validate():
        try:
            comment.text = form.comment.data
            put()
            flash('Your comment has been modified', "success")
            return redirect(url_for('main.user'))
        except DatabaseError as e:
            flash(e.message, 'error')
            return redirect(url_for('comment.edit_comment', comment_id=comment_id))

    return render_template("edit-comment-rating.html", type='Comment', form=form, is_edit=True)


@comment_bp.route("/delete-comment/<int:comment_id>")
@login_required
def delete_comment(comment_id):
    try:
        comment = get_by_id(model=Comment, id_reference=comment_id)
    except DatabaseError as e:
        flash(e.message, 'error')
        return redirect(url_for('main.user'))

    if comment.author_id != current_user.id:
        flash('You are not allowed to delete this comment!', "error")
        return redirect(url_for('main.user'))

    try:
        delete(comment)
        flash('Your comment has been deleted', "success")
    except DatabaseError as e:
        flash(e.message, 'error')
    finally:
        return redirect(url_for("main.user"))
