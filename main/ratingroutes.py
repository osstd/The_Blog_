from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import current_user, login_required
from models.models import Rating
from models.transactions import DatabaseError, get_by_id, put, delete
from extensions import limiter
from .forms import RatingForm

rating_bp = Blueprint('rating', __name__)


@rating_bp.route("/edit-rating/<int:rating_id>", methods=["GET", "POST"])
@limiter.limit("15 per hour")
@login_required
def edit_rating(rating_id):
    try:
        rating = get_by_id(model=Rating, id_reference=rating_id)
    except DatabaseError as e:
        flash(e.message, 'error')
        return redirect(url_for('rating.edit_rating', rating_id=rating_id))

    form = RatingForm(rating=rating.value)

    if rating.author_id != current_user.id:
        flash('You are not allowed to edit this rating!', "error")
        return redirect(url_for('main.user'))

    if form.submit.data and form.validate():
        try:
            rating.value = float(form.rating.data)
            put()
            flash('Your new rating has been submitted', "success")
            return redirect(url_for('main.user'))
        except DatabaseError as e:
            flash(e.message, 'error')
            return redirect(url_for('rating.edit_rating', rating_id=rating_id))

    return render_template('edit-comment-rating.html', type='Rating', form=form, is_edit=True)


@rating_bp.route("/delete-rating/<int:rating_id>")
@login_required
def delete_rating(rating_id):
    try:
        rating = get_by_id(model=Rating, id_reference=rating_id)
    except DatabaseError as e:
        flash(e.message, 'error')
        return redirect(url_for('main.user'))

    if rating.author_id != current_user.id:
        flash('You are not allowed to delete this rating!', "error")
        return redirect(url_for('main.user'))

    try:
        delete(rating)
        flash('Your rating has been deleted', "success")
    except DatabaseError as e:
        flash(e.message, 'error')
    finally:
        return redirect(url_for("main.user"))
