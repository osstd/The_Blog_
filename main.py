from datetime import date
from statistics import mean
from flask import Flask, abort, render_template, redirect, url_for, flash, request
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import relationship
from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm, RatingForm
import smtplib
from twilio.rest import Client
import os


def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # If id is not 1 then return abort with 403 error
        if current_user.id != 1:
            return abort(403)
        # Otherwise continue with the route function
        return f(*args, **kwargs)

    return decorated_function


app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('F_KEY')
ckeditor = CKEditor(app)
Bootstrap5(app)

gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DB_URI", "sqlite:///posts.db")
db = SQLAlchemy()
db.init_app(app)


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))
    add_post = db.Column(db.Boolean, default=False)
    request = db.Column(db.Boolean, default=False)
    # This will act like a List of BlogPost objects attached to each User.
    # The "author" refers to the author property in the BlogPost class.
    posts = relationship("BlogPost", back_populates="author")
    comments = relationship("Comment", back_populates="comment_author")
    ratings = relationship("Rating", back_populates="rating_author")


class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)

    # Create Foreign Key, "users.id" the users refers to the tablename of User.
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    # Create reference to the User object, the "posts" refers to the posts property in the User class.
    author = relationship("User", back_populates="posts")

    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    # Add parent relationship
    # "comment_author" refers to the comment_author property in the Comment class.
    comments = relationship("Comment", back_populates="parent_post")
    ratings = relationship("Rating", back_populates="parent_post")


class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("blog_posts.id"))
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    # Add child relationship
    parent_post = relationship("BlogPost", back_populates="comments")
    comment_author = relationship("User", back_populates="comments")
    text = db.Column(db.Text, nullable=False)


class Rating(db.Model):
    __tablename__ = "ratings"
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("blog_posts.id"))
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    parent_post = relationship("BlogPost", back_populates="ratings")
    rating_author = relationship("User", back_populates="ratings")
    value = db.Column(db.Float, nullable=False)


with app.app_context():
    db.create_all()


@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if request.method == "POST":
        email = request.form.get('email')
        result = db.session.execute(db.select(User).where(User.email == email))
        if result.scalar():
            flash('Email already registered, login with email instead!')
            return redirect(url_for('login'))
        else:
            hash_and_salted_password = generate_password_hash(
                request.form.get('password'),
                method='pbkdf2:sha256',
                salt_length=8
            )
            new_user = User(
                email=email,
                name=request.form.get('name'),
                password=hash_and_salted_password,
            )
            db.session.add(new_user)
            db.session.commit()

            login_user(new_user)
            return redirect(url_for('get_all_posts'))
    return render_template("register.html", form=form, logged_in=current_user.is_authenticated)


@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')

        result = db.session.execute(db.select(User).where(User.email == email))
        user = result.scalar()

        if not user:
            flash("Email not found!")
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        else:
            # user is logged in with Flask-Login
            login_user(user)
            return redirect(url_for('get_all_posts'))
    return render_template("login.html", form=form, logged_in=current_user.is_authenticated)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts', logged_in=False))


@app.route('/')
def get_all_posts():
    result = db.session.execute(db.select(BlogPost))
    posts = result.scalars().all()
    return render_template("index.html", all_posts=posts, logged_in=current_user.is_authenticated,
                           current_user=current_user)


# Allow logged-in users to comment on posts
@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def show_post(post_id):
    requested_post = db.get_or_404(BlogPost, post_id)
    comment_form = CommentForm()
    rating_form = RatingForm()
    if not requested_post.ratings:
        mean_ratings = 0
    else:
        mean_ratings = mean([rating.value for rating in requested_post.ratings])
    if request.method == 'POST':
        if rating_form.rating.data and rating_form.validate():
            if not current_user.is_authenticated:
                flash('You need to login or register to rate.')
                return redirect(url_for('login'))
            new_rating = Rating(value=float(rating_form.rating.data),
                                author_id=current_user.id,
                                post_id=requested_post.id
                                )
            db.session.add(new_rating)
            db.session.commit()
            mean_ratings = mean([rating.value for rating in requested_post.ratings])
        elif comment_form.comment.data and comment_form.validate():
            if not current_user.is_authenticated:
                flash('You need to login or register to comment.')
                return redirect(url_for('login'))
            new_comment = Comment(text=comment_form.comment.data,
                                  author_id=current_user.id,
                                  post_id=requested_post.id
                                  )
            db.session.add(new_comment)
            db.session.commit()
    return render_template("post.html", post=requested_post, logged_in=current_user.is_authenticated,
                           current_user=current_user, form=comment_form, form2=rating_form, mean=mean_ratings)


@app.route("/new-post", methods=["GET", "POST"])
@login_required
def add_new_post():
    if current_user.add_post:
        form = CreatePostForm()
        if form.validate_on_submit():
            new_post = BlogPost(
                title=form.title.data,
                subtitle=form.subtitle.data,
                body=form.body.data,
                img_url=form.img_url.data,
                author=current_user,
                date=date.today().strftime("%B %d, %Y")
            )
            db.session.add(new_post)
            db.session.commit()
            return redirect(url_for("get_all_posts"))
        return render_template("make-post.html", form=form, logged_in=current_user.is_authenticated)
    return 'You are not allowed to add posts, request permission on the home page.'


@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@login_required
def edit_post(post_id):
    post = db.get_or_404(BlogPost, post_id)
    if current_user.id == 1 or post.author_id == current_user.id:
        edit_form = CreatePostForm(
            title=post.title,
            subtitle=post.subtitle,
            img_url=post.img_url,
            author=post.author,
            body=post.body
        )
        if edit_form.validate_on_submit():
            post.title = edit_form.title.data
            post.subtitle = edit_form.subtitle.data
            post.img_url = edit_form.img_url.data
            post.author = current_user
            post.body = edit_form.body.data
            db.session.commit()
            return redirect(url_for("show_post", post_id=post.id))
        return render_template("make-post.html", form=edit_form, is_edit=True, logged_in=current_user.is_authenticated)
    else:
        flash('You are not allowed to edit this post!')
        return redirect(url_for('user'))


@app.route("/request-posting")
@login_required
def request_posting():
    user_request = db.get_or_404(User, current_user.id)
    user_request.request = True
    db.session.commit()
    send_email(
        message=f"Subject: New Request to post on The Blog from {current_user.name}\n\nName: {current_user.name}"
                f"\nEmail: {current_user.email}\n",
        user_email=None)
    send_text(message='You have a request to post pending.')
    return redirect(url_for('get_all_posts'))


@app.route("/process-posting/<int:user_id>/<int:user_allow>", methods=['GET', 'POST'])
@admin_only
def process_posting(user_id, user_allow):
    user_to_allow = db.get_or_404(User, user_id)
    if user_allow == 1:
        user_to_allow.add_post = True
        send_email(
            message=f"Subject: Your request to post have been accepted.\n\nHello, {user_to_allow.name},\nYour "
                    f"request to add posts have been accepted.\nYou can start adding posts. \nSincerely,"
                    f"\nThe Blog.", user_email=user_to_allow.email)
    else:
        send_email(
            message=f"Subject: Your request to post have been denied.\n\nHello, {user_to_allow.name},\nPlease "
                    f"note that your request to add posts has been denied at this time.\nSincerely,"
                    f"\nThe Blog.", user_email=user_to_allow.email)
        if user_to_allow.add_post:
            user_to_allow.add_post = False
    user_to_allow.request = False
    db.session.commit()
    return redirect(url_for('permission'))


@app.route("/permission")
@admin_only
def permission():
    records = db.session.execute(db.select(User))
    user_records = records.scalars().all()
    list_users_request = []
    for user in user_records:
        if user.request:
            list_users_request.append(user)
    return render_template('permission.html', users=list_users_request, logged_in=current_user.is_authenticated)


@app.route("/delete/<int:post_id>")
@login_required
def delete_post(post_id):
    post_to_delete = db.get_or_404(BlogPost, post_id)
    if current_user.id == 1 or post_to_delete.author_id == current_user.id:
        db.session.delete(post_to_delete)
        db.session.commit()
    else:
        flash('You are not allowed to delete this post!')
    return redirect(url_for('user'))


@app.route("/deletecom/<int:comment_id>")
@login_required
def delete_comment(comment_id):
    comment_ids = [comment.id for comment in current_user.comments]
    if comment_id in comment_ids:
        comment_to_delete = db.get_or_404(Comment, comment_id)
        db.session.delete(comment_to_delete)
        db.session.commit()
        return redirect(url_for('user'))
    flash('You are not allowed to delete this comment!')
    return redirect(url_for('user'))


@app.route("/deleterat/<int:rating_id>")
@login_required
def delete_rating(rating_id):
    rating_ids = [rating.id for rating in current_user.ratings]
    if rating_id in rating_ids:
        rating_to_delete = db.get_or_404(Rating, rating_id)
        db.session.delete(rating_to_delete)
        db.session.commit()
        return redirect(url_for('user'))
    flash('You are not allowed to delete this rating!')
    return redirect(url_for('user'))


@app.route("/edit-comment/<int:comment_id>", methods=["GET", "POST"])
@login_required
def edit_comment(comment_id):
    comment_ids = [comment.id for comment in current_user.comments]
    comment = db.get_or_404(Comment, comment_id)
    edit_form = CommentForm(
        comment=comment.text,
    )
    if edit_form.validate_on_submit() and comment_id in comment_ids:
        comment.text = edit_form.comment.data
        db.session.commit()
        return redirect(url_for('user'))
    elif edit_form.validate_on_submit() and comment_id not in comment_ids:
        flash('You are not allowed to edit this comment!')
        return redirect(url_for('user'))
    return render_template("edit-comment-rating.html", type='Comment', form=edit_form,
                           logged_in=current_user.is_authenticated)


@app.route("/edit-rating/<int:rating_id>", methods=["GET", "POST"])
@login_required
def edit_rating(rating_id):
    rating_ids = [rating.id for rating in current_user.ratings]
    rating = db.get_or_404(Rating, rating_id)
    edit_form = RatingForm(
        rating=rating.value,
    )
    if edit_form.validate_on_submit() and rating_id in rating_ids:
        rating.value = edit_form.rating.data
        db.session.commit()
        return redirect(url_for('user'))
    elif edit_form.validate_on_submit() and rating_id not in rating_ids:
        flash('You are not allowed to edit this rating!')
        return redirect(url_for('user'))
    return render_template("edit-comment-rating.html", type='Rating', form=edit_form, is_edit=True,
                           logged_in=current_user.is_authenticated)


@app.route('/user')
def user():
    return render_template('user.html', user=current_user, logged_in=current_user.is_authenticated)


@app.route("/about")
def about():
    return render_template("about.html", logged_in=current_user.is_authenticated)


@app.route("/contact", methods=['GET', 'POST'])
@login_required
def contact():
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        email = request.form['email']
        message = request.form['message']
        send_email(
            message=f"Subject: New Question from The Blog from {name}\n\nName: {name}\nEmail: {email}\nPhone: {phone}"
                    f"\nMessage: "
                    f"\n{message}", user_email=None)
        return render_template("contact.html", sent=True, logged_in=current_user.is_authenticated)
    return render_template('contact.html', logged_in=current_user.is_authenticated)


def send_email(message, user_email):
    my_email = os.environ.get("E_ID")
    password = os.environ.get("E_KEY")
    if not user_email:
        user_email = my_email
    with smtplib.SMTP("smtp.gmail.com", port=587) as connection:
        connection.starttls()
        connection.login(user=my_email, password=password)
        connection.sendmail(from_addr=my_email,
                            to_addrs=user_email,
                            msg=message)
        connection.close()


def send_text(message):
    client = Client(os.environ.get('A_ID'), os.environ.get('A_T'))
    message = client.messages.create(
        body=message,
        from_=os.environ.get('S_ID'),
        to=os.environ.get('T_ID')
    )
    print(message.status)


if __name__ == "__main__":
    app.run(debug=False)
