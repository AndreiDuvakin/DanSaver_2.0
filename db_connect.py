import datetime

import sqlalchemy as sq
import sqlalchemy.orm as orm
from sqlalchemy.orm import Session
import sqlalchemy.ext.declarative as dec

__factory = None
base = dec.declarative_base()


class Type(base):
    __tablename__ = 'types'

    id = sq.Column(sq.Integer, primary_key=True, autoincrement=True)
    name = sq.Column(sq.String)


class Extensions(base):
    __tablename__ = 'extensions'

    id = sq.Column(sq.Integer, primary_key=True, autoincrement=True)
    name = sq.Column(sq.String)
    type_id = sq.Column(sq.Integer, sq.ForeignKey('type.id'), nullable=False)


class Media(base):
    __tablename__ = 'media'

    id = sq.Column(sq.Integer, primary_key=True, autoincrement=True)
    name = sq.Column(sq.String)
    data = sq.Column(sq.BLOB, unique=True, nullable=False)
    date = sq.Column(sq.DateTime, default=datetime.datetime.now())
    expansion_id = sq.Column(sq.Integer, sq.ForeignKey('extensions.id'), nullable=False)


def init_db():
    global __factory

    if __factory:
        return __factory

    eng = sq.create_engine('sqlite:///db/dan_sever.db')
    __factory = orm.sessionmaker(eng)
    base.meta.create_all(eng)


def connect() -> Session:
    global __factory
    return __factory
