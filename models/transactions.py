from flask import abort
from sqlalchemy.exc import SQLAlchemyError
from extensions import db


class DatabaseError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


def get_all(model):
    try:
        return db.session.query(model).all()
    except SQLAlchemyError as error:
        raise DatabaseError(f"Error retrieving all records from {model.__tablename__}: {str(error)}")


def get_by_id(model, id_reference):
    try:
        return db.session.get(model, id_reference) or abort(404)
    except SQLAlchemyError as error:
        raise DatabaseError(f"Error retrieving record from {model.__tablename__}: {str(error)}")


def get_by_author_id(model, author_id, post_id):
    try:
        return db.session.query(model).filter_by(author_id=author_id, post_id=post_id).first()
    except SQLAlchemyError as error:
        raise DatabaseError(
            f"Error retrieving record from {model.__tablename__}: {str(error)}")


def get_by_condition(model, condition):
    try:
        return model.query.filter_by(request=condition).all()
    except SQLAlchemyError as error:
        raise DatabaseError(
            f"Error retrieving record(s) from {model.__tablename__}: {str(error)}")


def add(entry):
    try:
        db.session.add(entry)
        db.session.commit()
    except SQLAlchemyError as error:
        db.session.rollback()
        raise DatabaseError(f"Error adding record to {entry.__tablename__}: {str(error)}")


def put():
    try:
        db.session.commit()
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
