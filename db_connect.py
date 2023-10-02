import datetime

import sqlalchemy as sq
import sqlalchemy.orm as orm
from sqlalchemy.orm import Session
import sqlalchemy.ext.declarative as dec
from sqlalchemy import create_engine

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
    type_id = sq.Column(sq.Integer, sq.ForeignKey('types.id'), nullable=False)


class Media(base):
    __tablename__ = 'media'

    id = sq.Column(sq.Integer, primary_key=True, autoincrement=True)
    name = sq.Column(sq.String)
    data = sq.Column(sq.BLOB, unique=True, nullable=False)
    date = sq.Column(sq.DateTime, default=datetime.datetime.now())
    exe_id = sq.Column(sq.Integer, sq.ForeignKey('extensions.id'))


class Categories(base):
    __tablename__ = 'categories'

    id = sq.Column(sq.Integer, primary_key=True, autoincrement=True)
    name = sq.Column(sq.String)


class MediaCetegories(base):
    __tablename__ = 'media_categories'

    id = sq.Column(sq.Integer, primary_key=True, autoincrement=True)
    category_id = sq.Column(sq.Integer, sq.ForeignKey('categories.id'), nullable=False)
    media_id = sq.Column(sq.Integer, sq.ForeignKey('media.id'), nullable=False)


def init_data():
    global __factory

    if __factory:
        return
    eng = create_engine('sqlite:///db/media_saver.db')
    __factory = orm.sessionmaker(bind=eng)
    base.metadata.create_all(eng)

    con = create_session()
    if not con.query(Type).first():
        default_data()


def create_session() -> Session:
    global __factory
    return __factory()


def default_data():
    con = create_session()
    tpe = list(map(con.add, map(lambda x: Type(name=x), ['audio', 'photo', 'video'])))
    con.commit()
    con.close()
