import os

from sqlalchemy import text
from flask_security.utils import hash_password

from app.models.common import *
from app.models.security import *
from app.models.logging import *
from app.models.files import *
from app.models.portal import *


def create_schema():
    db.session.execute(text('CREATE EXTENSION IF NOT EXISTS postgis'))
    db.session.execute(text('CREATE SCHEMA IF NOT EXISTS portal'))

    db.session.commit()

    db.drop_all()
    db.create_all()

    load_data()

    config_admin_user()

    load_functions()

    db.session.commit()


def load_data():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(current_dir, 'scalargis_data.sql')

    file = open(filepath, encoding='utf-8')

    db.session.execute(text(file.read()))


def load_functions():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(current_dir, 'scalargis_functions.sql')

    file = open(filepath, encoding='utf-8')

    db.session.execute(text(file.read()))


def config_admin_user():
    user = User.query.filter_by(username='admin').first()
    if user:
        user.password = hash_password('admin')

        role = Role.query.filter_by(name='Admin').first()
        if role:
            user.roles.append(role)

        db.session.add(user)


def load_sample_data():
    from .sample_data import load_data

    load_data()

    db.session.commit()
