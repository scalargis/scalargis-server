import os

from sqlalchemy import text
from sqlalchemy.sql import exists, select
from flask_security.utils import hash_password

from app.models.common import *
from app.models.security import *
from app.models.logging import *
from app.models.files import *
from app.models.portal import *


db_schema = get_db_schema()


def create_schema():
    created = False

    q = exists(select(text("schema_name")).select_from(text("information_schema.schemata")).
               where(text("schema_name = '{schema}'".format(schema=db_schema))))
    if not db.session.query(q).scalar():
        db.session.execute(text('CREATE EXTENSION IF NOT EXISTS postgis'))
        db.session.execute(text('CREATE SCHEMA IF NOT EXISTS {schema}'.format(schema=db_schema)))

        db.session.commit()

        #db.drop_all()
        db.create_all()

        load_data()

        config_admin_user()

        load_functions()

        db.session.commit()

        created = True

    return created


def load_data():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(current_dir, 'scalargis_data.sql')

    file = open(filepath, encoding='utf-8')

    sql_text = file.read()
    sql_text = sql_text.replace('{schema}', db_schema)

    db.session.execute(text(sql_text))


def load_functions():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(current_dir, 'scalargis_functions.sql')

    file = open(filepath, encoding='utf-8')

    sql_text = file.read()
    sql_text = sql_text.replace('{schema}', db_schema)

    db.session.execute(text(sql_text))


def config_admin_user():
    user = User.query.filter_by(username='admin').first()
    if user:
        user.password = hash_password('admin')

        role = Role.query.filter_by(name='Admin').first()
        if role:
            user.roles.append(role)

        db.session.add(user)


def update_schema():
    """
    Update existing database schema with new columns.
    This function checks if columns exist before adding them to avoid errors.
    """
    updated = False

    try:
        # Check if NIF column exists in user table
        nif_exists_query = text("""
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = :schema
                AND table_name = 'user'
                AND column_name = 'nif'
            )
        """)

        nif_exists = db.session.execute(nif_exists_query, {'schema': db_schema}).scalar()

        if not nif_exists:
            # Add NIF column to user table
            alter_query = text("""
                ALTER TABLE {schema}.user
                ADD COLUMN nif VARCHAR(9) UNIQUE
            """.format(schema=db_schema))

            db.session.execute(alter_query)

            # Create index on NIF column
            index_query = text("""
                CREATE INDEX IF NOT EXISTS ix_{schema}_user_nif
                ON {schema}.user (nif)
            """.format(schema=db_schema))

            db.session.execute(index_query)

            db.session.commit()
            updated = True

    except Exception as e:
        db.session.rollback()
        raise e

    return updated


def load_sample_data():
    from .sample_data import load_data

    load_data()

    db.session.commit()
