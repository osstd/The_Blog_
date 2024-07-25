from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from models.models import BlogPost, Comment, Rating
from models.transactions import get_all, get_by_id, get_by_author_id, add, put, delete, DatabaseError, IntegrityError
from extensions import limiter
from .forms import CreatePostForm, CommentForm, RatingForm
from utils import sanitize_input
from datetime import date
from statistics import mean

post_bp = Blueprint('post', __name__)


@post_bp.route('/')
def get_all_posts():
    try:
        posts = get_all(BlogPost)
        return render_template('index.html', all_posts=posts, current_user=current_user)
    except DatabaseError as e:
        flash(e.message, 'error')
        return redirect(url_for('main.error'))


@post_bp.route('/post/<int:post_id>', methods=['GET', 'POST'])
def show_post(post_id):
    try:
        post = get_by_id(model=BlogPost, id_reference=post_id)

        if not post:
            flash('Post record not found', 'error')
            return redirect(url_for('main.error'))

        comment_form = CommentForm()
        rating_form = RatingForm()

        if request.method == 'POST':

            if not current_user.is_authenticated:
                flash('You need to log in to comment or rate', 'error')
                return redirect(url_for('auth.login'))

            if comment_form.validate_on_submit():
                existing_comment = get_by_author_id(Comment, author_id=current_user.id, post_id=post_id)

                if existing_comment:
                    flash('You have already commented on this post.', 'error')
                    return redirect(url_for('main.user'))

                new_comment = Comment(
                    text=comment_form.comment.data,
                    author_id=current_user.id,
                    post_id=post.id
                )
                add(new_comment)
                flash('Comment submitted successfully.', 'success')

                return redirect(url_for('post.show_post', post_id=post_id))

            elif rating_form.validate_on_submit():
                existing_rating = get_by_author_id(Rating, author_id=current_user.id, post_id=post_id)

                if existing_rating:
                    flash('You have already rated this post.', 'error')
                    return redirect(url_for('main.user'))

                new_rating = Rating(
                    value=float(rating_form.rating.data),
                    author_id=current_user.id,
                    post_id=post.id
                )
                add(new_rating)
                flash('Rating submitted successfully.', 'success')

                return redirect(url_for('post.show_post', post_id=post_id))

        mean_ratings = mean([rating.value for rating in post.ratings]) if post.ratings else 0
        return render_template('post.html', post=post, current_user=current_user, form=comment_form, form2=rating_form,
                               mean=mean_ratings)
    except IntegrityError:
        flash('A database constraint was violated', 'error')
    except DatabaseError as e:
        flash(e.message, 'error')

    return redirect(url_for('post.show_post', post_id=post_id))


@post_bp.route('/new-post', methods=["GET", "POST"])
@login_required
@limiter.limit("5 per hour")
def add_new_post():
    if current_user.add_post:
        form = CreatePostForm()

        if form.validate_on_submit():
            new_post = BlogPost(
                title=sanitize_input(form.title.data),
                subtitle=sanitize_input(form.subtitle.data),
                body=form.body.data,
                img_url=sanitize_input(form.img_url.data),
                author=current_user,
                date=date.today().strftime("%B %d, %Y")
            )

            try:
                add(new_post)
                return redirect(url_for('post.get_all_posts'))

            except IntegrityError as e:
                if 'unique constraint' in str(e).lower():
                    flash('This title already exists.', 'error')
                else:
                    flash('A database constraint was violated.', 'error')
            except DatabaseError as e:
                flash(e.message, 'error')

            return redirect(url_for('post.add_new_post'))

        return render_template("make-post.html", form=form)

    flash('You are not allowed to add posts, request permission on the home page.', 'error')
    return redirect(url_for('main.error'))


@post_bp.route('/edit-post/<int:post_id>', methods=["GET", "POST"])
@login_required
@limiter.limit("5 per hour")
def edit_post(post_id):
    try:
        post = get_by_id(model=BlogPost, id_reference=post_id)

        if not post:
            flash('Post record not found', 'error')
            return redirect(url_for('main.user'))

        if not current_user.id == 1 and not post.author_id == current_user.id:
            flash('You are not allowed to edit this post!', 'error')
            return redirect(url_for('main.user'))

        form = CreatePostForm(
            title=post.title,
            subtitle=post.subtitle,
            img_url=post.img_url,
            body=post.body
        )

        if form.validate_on_submit():
            post.title = sanitize_input(form.title.data)
            post.subtitle = sanitize_input(form.subtitle.data)
            post.body = form.body.data
            post.img_url = sanitize_input(form.img_url.data)
            put()
            return redirect(url_for("post.show_post", post_id=post.id))

        return render_template("make-post.html", form=form, is_edit=True)

    except IntegrityError as e:
        if 'unique constraint' in str(e).lower():
            flash('This title already exists.', 'error')
        else:
            flash('A database constraint was violated.', 'error')
    except DatabaseError as e:
        flash(e.message, 'error')

    return redirect(url_for('post.edit_post', post_id=post_id))


@post_bp.route('/delete/<int:post_id>')
@login_required
@limiter.limit("3 per hour")
def delete_post(post_id):
    try:
        post = get_by_id(model=BlogPost, id_reference=post_id)

        if not post:
            flash('Post record not found', 'error')
            return redirect(url_for('main.user'))

        if not current_user.id == 1 and not post.author_id == current_user.id:
            flash('You are not allowed to delete this post!', 'error')
            return redirect(url_for('main.user'))

        delete(post)
        flash('The selected post has been deleted', 'success')

    except DatabaseError as e:
        flash(e.message, 'error')
    finally:
        return redirect(url_for("main.user"))
