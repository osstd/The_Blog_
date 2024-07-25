from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from extensions import db
from models.models import UserBlog


class DatabaseError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


def get_all(model, page=None, per_page=None):
    try:
        query = db.session.query(model)
        if page and per_page:
            query = query.paginate(page, per_page)
        return query.all()

    except SQLAlchemyError as error:
        raise DatabaseError(f"Error retrieving all records from {model.__tablename__}: {str(error)}")


def get_by_id(model, id_reference):
    try:
        return db.session.get(model, id_reference)
    except SQLAlchemyError as error:
        raise DatabaseError(f"Error retrieving record from {model.__tablename__}: {str(error)}")


def get_user_by_email(email_id):
    try:
        return UserBlog.query.filter_by(email=email_id).first()
    except SQLAlchemyError as error:
        raise DatabaseError(f"Error retrieving user: {str(error)}")


def get_by_author_id(model, author_id, post_id):
    try:
        return db.session.query(model).filter_by(author_id=author_id, post_id=post_id).first()
    except SQLAlchemyError as error:
        raise DatabaseError(
            f"Error retrieving record from {model.__tablename__}: {str(error)}")


def get_by_condition(model, criteria, condition):
    try:
        if criteria == 'add_post':
            return model.query.filter_by(add_post=condition).all()
        if criteria == 'request':
            return model.query.filter_by(request=condition).all()
        raise ValueError(f"Unsupported criteria: {criteria}")
    except SQLAlchemyError as error:
        raise DatabaseError(
            f"Error retrieving record(s) from {model.__tablename__}: {str(error)}")


def add(entry):
    try:
        db.session.add(entry)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise
    except SQLAlchemyError as error:
        db.session.rollback()
        raise DatabaseError(f"Error adding record to {entry.__tablename__}: {str(error)}")


def put():
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise
    except SQLAlchemyError as error:
        db.session.rollback()
        raise DatabaseError(f"Error updating record: {str(error)}")


def delete(record):
    try:
        db.session.delete(record)
        db.session.commit()
    except SQLAlchemyError as error:
        db.session.rollback()
        raise DatabaseError(f"Error deleting record: {str(error)}")
