import logging
import os

from sqlalchemy import text
from sqlalchemy.sql import exists, select
from flask_security.utils import hash_password

from app.models.common import *
from app.models.security import *
from app.models.login_attempt import *
from app.models.files import *
from app.models.portal import *
from app.models.runner import *


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


RUNNER_TABLES_LOCK_KEY = 7286337501


def create_runner_tables():
    """Create the runner tables on a database made before the runner. On PostgreSQL one process at a time does it."""
    bind = db.session.get_bind()
    engine = getattr(bind, 'engine', bind)
    with engine.begin() as conn:
        if conn.dialect.name == 'postgresql':
            conn.execute(text('SELECT pg_advisory_xact_lock(:k)'), {'k': RUNNER_TABLES_LOCK_KEY})
        for table in (Job.__table__, RunnerHeartbeat.__table__):
            table.create(bind=conn, checkfirst=True)


FS_UNIQUIFIER_LOCK_KEY = 7286337502

FS_UNIQUIFIER_SQL = (
    'ALTER TABLE {schema}."user" ADD COLUMN IF NOT EXISTS fs_uniquifier varchar(64)',
    'UPDATE {schema}."user" SET fs_uniquifier = replace(gen_random_uuid()::text, \'-\', \'\') '
    'WHERE fs_uniquifier IS NULL',
    'ALTER TABLE {schema}."user" ALTER COLUMN fs_uniquifier SET DEFAULT replace(gen_random_uuid()::text, \'-\', \'\')',
    'ALTER TABLE {schema}."user" ALTER COLUMN fs_uniquifier SET NOT NULL',
    'CREATE UNIQUE INDEX IF NOT EXISTS user_fs_uniquifier_key ON {schema}."user" (fs_uniquifier)',
)


def ensure_fs_uniquifier():
    """Add and fill fs_uniquifier on the user table when it is missing. On PostgreSQL one process at a time does it."""
    bind = db.session.get_bind()
    engine = getattr(bind, 'engine', bind)
    with engine.begin() as conn:
        if conn.dialect.name != 'postgresql':
            return False
        conn.execute(text('SELECT pg_advisory_xact_lock(:k)'), {'k': FS_UNIQUIFIER_LOCK_KEY})
        row = conn.execute(text("SELECT is_nullable FROM information_schema.columns WHERE table_schema = :s "
                                "AND table_name = 'user' AND column_name = 'fs_uniquifier'"),
                           {'s': db_schema}).first()
        if row is not None and row[0] == 'NO':
            return False
        for statement in FS_UNIQUIFIER_SQL:
            conn.execute(text(statement.format(schema=db_schema)))
    logging.getLogger(__name__).info('fs_uniquifier column added to %s."user"', db_schema)
    return True


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


def load_sample_data():
    from .sample_data import load_data

    load_data()

    db.session.commit()
