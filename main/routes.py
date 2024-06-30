from flask import Blueprint, current_app, render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from models.models import UserBlog, BlogPost, Comment, Rating
from extensions import db, limiter
from .forms import CreatePostForm, CommentForm, RatingForm, RequestForm
from utils import verify_recaptcha, send_email_async, sanitize_input, validate_email, send_text
from admin import admin_required
from email.mime.text import MIMEText
import asyncio
from datetime import date
from statistics import mean

main_bp = Blueprint('main', __name__)


@main_bp.route('/user')
def user():
    return render_template('user.html', user=current_user)


@main_bp.route("/about")
def about():
    return render_template("about.html")


@main_bp.route('/')
def get_all_posts():
    posts = BlogPost.query.all()
    return render_template("index.html", all_posts=posts, current_user=current_user)


@main_bp.route('/post/<int:post_id>', methods=["GET", "POST"])
def show_post(post_id):
    post = BlogPost.query.get_or_404(post_id)
    comment_form = CommentForm()
    rating_form = RatingForm()

    if request.method == 'POST':
        if comment_form.submit.data and comment_form.validate():

            if not current_user.is_authenticated:
                flash("You need to log in to comment.", "error")
                return redirect(url_for("auth.login"))

            existing_comment = Comment.query.filter_by(author_id=current_user.id, post_id=post_id).first()
            if existing_comment:
                flash("You have already commented on this post.", "error")
                return redirect(url_for("main.user"))

            new_comment = Comment(
                text=comment_form.comment.data,
                author_id=current_user.id,
                post_id=post.id
            )
            db.session.add(new_comment)
            db.session.commit()
            flash("Comment submitted successfully.", "success")
            return redirect(url_for('main.show_post', post_id=post_id))

        elif rating_form.submit.data and rating_form.validate():
            if not current_user.is_authenticated:
                flash("You need to log in to rate.", "error")
                return redirect(url_for("auth.login"))

            existing_rating = Rating.query.filter_by(author_id=current_user.id, post_id=post_id).first()
            if existing_rating:
                flash("You have already rated this post.", "error")
                return redirect(url_for("main.user"))

            new_rating = Rating(
                value=float(rating_form.rating.data),
                author_id=current_user.id,
                post_id=post.id
            )
            db.session.add(new_rating)
            db.session.commit()
            flash("Rating submitted successfully.", "success")
            return redirect(url_for('main.show_post', post_id=post_id))

    mean_ratings = mean([rating.value for rating in post.ratings]) if post.ratings else 0
    return render_template("post.html", post=post, current_user=current_user, form=comment_form, form2=rating_form,
                           mean=mean_ratings)


@main_bp.route('/new-post', methods=["GET", "POST"])
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
            db.session.add(new_post)
            db.session.commit()
            return redirect(url_for("main.get_all_posts"))
        return render_template("make-post.html", form=form)
    return 'You are not allowed to add posts, request permission on the home page.'


@main_bp.route('/edit-post/<int:post_id>', methods=["GET", "POST"])
@login_required
@limiter.limit("5 per hour")
def edit_post(post_id):
    post = BlogPost.query.get_or_404(post_id)
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
        db.session.commit()
        return redirect(url_for("main.show_post", post_id=post.id))
    return render_template("make-post.html", form=form, is_edit=True)


@main_bp.route('/delete/<int:post_id>')
@login_required
@limiter.limit("3 per hour")
def delete_post(post_id):
    post = BlogPost.query.get_or_404(post_id)

    if post is None:
        flash('Post not found!', "error")
        return redirect(url_for('main.user'))

    if not current_user.id == 1 and not post.author_id == current_user.id:
        flash('You are not allowed to delete this post!', "error")
        return redirect(url_for('main.user'))

    db.session.delete(post)
    db.session.commit()

    flash('The selected post has been deleted', "success")
    return redirect(url_for("main.user"))


@main_bp.route("/edit-comment/<int:comment_id>", methods=["GET", "POST"])
@limiter.limit("15 per hour")
@login_required
def edit_comment(comment_id):
    comment = db.get_or_404(Comment, comment_id)
    form = CommentForm(comment=comment.text)

    if comment.author_id != current_user.id:
        flash('You are not allowed to edit this comment!', "error")
        return redirect(url_for('main.user'))

    if form.submit.data and form.validate():
        comment.text = form.comment.data
        db.session.commit()
        flash('Your comment has been modified', "success")
        return redirect(url_for('main.user'))
    return render_template("edit-comment-rating.html", type='Comment', form=form, is_edit=True)


@main_bp.route("/delete-comment/<int:comment_id>")
@login_required
def delete_comment(comment_id):
    comment = db.get_or_404(Comment, comment_id)

    if comment.author_id != current_user.id:
        flash('You are not allowed to delete this comment!', "error")
        return redirect(url_for('main.user'))

    db.session.delete(comment)
    db.session.commit()
    flash('Your comment has been deleted', "success")
    return redirect(url_for('main.user'))


@main_bp.route("/edit-rating/<int:rating_id>", methods=["GET", "POST"])
@limiter.limit("15 per hour")
@login_required
def edit_rating(rating_id):
    rating = db.get_or_404(Rating, rating_id)
    form = RatingForm(rating=rating.value)

    if rating.author_id != current_user.id:
        flash('You are not allowed to edit this rating!', "error")
        return redirect(url_for('main.user'))

    if form.submit.data and form.validate():
        rating.value = float(form.rating.data)
        db.session.commit()
        flash('Your new rating has been submitted', "success")
        return redirect(url_for('main.user'))
    return render_template('edit-comment-rating.html', type='Rating', form=form, is_edit=True)


@main_bp.route("/delete-rating/<int:rating_id>")
@login_required
def delete_rating(rating_id):
    rating = db.get_or_404(Rating, rating_id)

    if rating.author_id != current_user.id:
        flash('You are not allowed to delete this rating!', "error")
        return redirect(url_for('main.user'))

    db.session.delete(rating)
    db.session.commit()
    flash('Your rating has been deleted', "success")
    return redirect(url_for('main.user'))


@main_bp.route('/process-posting/<int:user_id>/<int:user_allow>')
@admin_required
def process_posting(user_id, user_allow):
    user_to_allow = UserBlog.query.get_or_404(user_id)
    if user_allow == 1:

        user_to_allow.add_post = True

        msg = MIMEText(
            f"Hello {user_to_allow.name},\nYour request to add posts has been accepted.\nYou can start adding "
            f"posts. \nSincerely,\nThe Blog.", 'plain', 'utf-8')
        msg['Subject'] = "Your request to post has been accepted."

        email_sent = asyncio.run(send_email_async(
            message=msg, recepient_email=user_to_allow.email))

        if not email_sent:
            flash('Error sending update to recepient', 'error')
        elif email_sent:
            flash('User posting permission granted.', "success")
    else:
        user_to_allow.add_post = False

        msg = MIMEText(
            f"Hello {user_to_allow.name},\nPlease "
            f"note that your request to add posts has been denied at this time. \nSincerely,\nThe Blog.", 'plain',
            'utf-8')
        msg['Subject'] = "Your request to post has been denied."

        email_sent = asyncio.run(send_email_async(message=msg, recepient_email=user_to_allow.email))

        if not email_sent:
            flash('Error sending update to recepient', 'error')
        elif email_sent:
            flash('User has no pending requests.', 'warning')

    user_to_allow.request = False
    db.session.commit()

    return redirect(url_for('main.permission'))


@main_bp.route('/permission')
@admin_required
def permission():
    users = UserBlog.query.filter_by(request=True).all()
    return render_template('permission.html', users=users)


@main_bp.route('/request-posting', methods=["GET", "POST"])
@login_required
@limiter.limit("6 per hour")
def request_posting():
    form = RequestForm()
    if form.submit.data and form.validate():
        recaptcha_response = request.form.get('g-recaptcha-response')
        recaptcha_success = asyncio.run(verify_recaptcha(recaptcha_response))

        if recaptcha_success:
            current_user.request = True
            db.session.commit()
            reason = sanitize_input(form.reason.data)
            msg = MIMEText(f"Name: {current_user.name}\nEmail: {current_user.email}\nRequest:{reason}", 'plain',
                           'utf-8')
            msg['Subject'] = f"New Request to post on The Blog from {current_user.name}"
            asyncio.run(send_email_async(message=msg, recepient_email=None))
            asyncio.run(send_text(message='You have a request to post pending.'))
            flash('Your request has been submitted.', 'success')
        else:
            flash('Recaptcha verification failed.', 'error')
        return redirect(url_for('main.request_posting'))
    return render_template('request.html', form=form, site_key=current_app.config['RECAPTCHA_SITE_KEY'])


@main_bp.route('/contact', methods=["GET", "POST"])
@limiter.limit("5 per hour")
def contact():
    if request.method == 'POST':

        if not current_user.is_authenticated:
            flash("You need to log in to send a message.", "error")
            return redirect(url_for("auth.login"))

        recaptcha_response = request.form['g-recaptcha-response']
        if not asyncio.run(verify_recaptcha(recaptcha_response)):
            flash("reCAPTCHA verification failed. Please try again.", "error")
            return redirect(url_for("main.contact"))

        name = sanitize_input(request.form.get('name'))
        phone = sanitize_input(request.form.get('phone'))
        email = request.form.get('email').lower().strip()
        message = sanitize_input(request.form.get('message'))

        if not name or not email or not phone or not message:
            flash("Please fill all required fields", 'error')
            return redirect(url_for("main.contact"))

        if not validate_email(email):
            flash("Please enter a valid email address", 'error')
            return redirect(url_for("main.contact"))

        subject = f"New Question from The Blog from {name}"
        body = f"Name: {name}\nEmail: {email}\nPhone: {phone}\nMessage:\n{message}"
        msg = MIMEText(body, 'plain', 'utf-8')
        msg['Subject'] = subject

        if not asyncio.run(send_email_async(msg, None)):
            flash('There was an error sending your message.', 'error')
            return redirect(url_for("main.contact"))

        flash('Your message has been sent.', 'success')
        return render_template('contact.html')

    return render_template('contact.html', site_key=current_app.config['RECAPTCHA_SITE_KEY'], form=True)
