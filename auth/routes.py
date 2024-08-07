from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError
from extensions import limiter
from models.models import UserBlog
from models.transactions import get_user_by_email, add, DatabaseError
from .forms import RegisterForm, LoginForm
from utils import sanitize_input, validate_email

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=["GET", "POST"])
@limiter.limit("5 per hour")
def register():
    form = RegisterForm()
    if form.submit.data and form.validate_on_submit():
        email = form.email.data.lower().strip()
        password = form.password.data
        name = sanitize_input(form.name.data)

        if not validate_email(email):
            flash('Invalid email format.', "error")
            return redirect(url_for('auth.register'))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)
        new_user = UserBlog(email=email, name=name, password=hashed_password)

        try:
            add(new_user)
            login_user(new_user)
            return redirect(url_for('post.get_all_posts'))

        except IntegrityError:
            flash('Email already registered. Please log in.', 'error')
            return redirect(url_for('auth.login'))

        except DatabaseError as e:
            flash(e.message, 'error')
            return redirect(url_for('auth.register'))

    return render_template("register.html", form=form)


@auth_bp.route('/login', methods=["GET", "POST"])
@limiter.limit("15 per hour")
def login():
    form = LoginForm()
    if form.submit.data and form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        try:
            user = get_user_by_email(email)
            if not user:
                flash('Email not found!', 'error')
                return redirect(url_for('auth.login'))

            elif not check_password_hash(user.password, password):
                flash('Password incorrect, please try again.', 'error')
                return redirect(url_for('auth.login'))

            else:
                login_user(user)
                return redirect(url_for('post.get_all_posts'))

        except DatabaseError as e:
            flash(e.message, 'error')
            return redirect(url_for('auth.login'))

    return render_template("login.html", form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('post.get_all_posts'))
