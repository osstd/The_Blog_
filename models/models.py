
from flask_login import UserMixin
from sqlalchemy.orm import relationship
from extensions import db


class UserBlog(UserMixin, db.Model):
    __tablename__ = "users_blog"
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
    author_id = db.Column(db.Integer, db.ForeignKey("users_blog.id"))
    # Create reference to the User object, the "posts" refers to the posts property in the User class.
    author = relationship("UserBlog", back_populates="posts")

    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)

    comments = relationship("Comment", back_populates="parent_post", cascade="all, delete-orphan")
    ratings = relationship("Rating", back_populates="parent_post", cascade="all, delete-orphan")


class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("blog_posts.id"))
    author_id = db.Column(db.Integer, db.ForeignKey("users_blog.id"))
    parent_post = relationship("BlogPost", back_populates="comments")
    comment_author = relationship("UserBlog", back_populates="comments")
    text = db.Column(db.Text, nullable=False)


class Rating(db.Model):
    __tablename__ = "ratings"
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("blog_posts.id"))
    author_id = db.Column(db.Integer, db.ForeignKey("users_blog.id"))
    parent_post = relationship("BlogPost", back_populates="ratings")
    rating_author = relationship("UserBlog", back_populates="ratings")
    value = db.Column(db.Float, nullable=False)
