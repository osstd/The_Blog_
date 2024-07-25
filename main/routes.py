from flask import Blueprint, current_app, render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from models.models import UserBlog
from models.transactions import DatabaseError, get_by_id, get_by_condition, put
from extensions import limiter
from .forms import RequestForm
from utils import verify_recaptcha, send_email_async, sanitize_input, validate_email, send_text
from admin import admin_required
from email.mime.text import MIMEText
import asyncio


main_bp = Blueprint('main', __name__)


@main_bp.route('/error')
def error():
    return render_template('error.html')


@main_bp.route('/user')
def user():
    return render_template('user.html', user=current_user)


@main_bp.route("/about")
def about():
    return render_template("about.html")


@main_bp.route('/process-posting/<int:user_id>/<int:user_allow>')
@admin_required
def process_posting(user_id, user_allow):
    try:
        user_to_allow = get_by_id(model=UserBlog, id_reference=user_id)

        if not user_to_allow:
            flash('User record can not be retrieved', 'error')
            return redirect(url_for('main.permission'))

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
        put()
    except DatabaseError as e:
        flash(e.message, 'error')
    finally:
        return redirect(url_for('main.permission'))


@main_bp.route('/permission')
@admin_required
def permission():
    try:
        authors = get_by_condition(UserBlog, 'add_post', True)
        users = get_by_condition(UserBlog, 'request', True)
        return render_template('permission.html', users=users, authors=authors)
    except ValueError as e:
        flash(str(e), 'error')
    except DatabaseError as e:
        flash(e.message, 'error')
    return redirect(url_for('main.error'))


@main_bp.route('/request-posting', methods=["GET", "POST"])
@login_required
@limiter.limit("15 per hour")
def request_posting():
    form = RequestForm()

    if form.submit.data and form.validate():
        recaptcha_response = request.form.get('g-recaptcha-response')
        recaptcha_success = asyncio.run(verify_recaptcha(recaptcha_response))

        if not recaptcha_success:
            flash('Recaptcha verification failed.', 'error')
            return redirect(url_for('main.request_posting'))

        reason = sanitize_input(form.reason.data)
        msg = MIMEText(f"Name: {current_user.name}\nEmail: {current_user.email}\nRequest:{reason}", 'plain',
                       'utf-8')
        msg['Subject'] = f"New Request to post on The Blog from {current_user.name}"

        try:
            current_user.request = True
            put()
        except DatabaseError as e:
            flash(e.message, 'error')
            return redirect(url_for('main.request_posting'))

        asyncio.run(send_email_async(message=msg, recepient_email=None))
        asyncio.run(send_text(message='You have a request to post pending.'))

        flash('Your request has been submitted.', 'success')
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

        if not all([name, email, phone, message]):
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
        return redirect(url_for('main.contact'))

    return render_template('contact.html', site_key=current_app.config['RECAPTCHA_SITE_KEY'], form=True)
