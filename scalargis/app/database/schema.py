import logging
import os

from sqlalchemy import inspect, text
from flask_security.utils import hash_password

from app.models.common import *
from app.models.security import *
from app.models.login_attempt import *
from app.models.files import *
from app.models.portal import *
from app.models.runner import *


db_schema = get_db_schema()


SCHEMA_LOCK_KEY = 7286337507


def create_schema():
    """Create and seed the schema in one transaction under an advisory lock. True when it created the schema."""
    try:
        db.session.execute(text('SELECT pg_advisory_xact_lock(:k)'), {'k': SCHEMA_LOCK_KEY})
        found = db.session.execute(text('SELECT 1 FROM pg_namespace WHERE nspname = :s'),
                                   {'s': db_schema}).first()
        if found is not None:
            db.session.commit()
            return False
        db.session.execute(text('CREATE EXTENSION IF NOT EXISTS postgis'))
        db.session.execute(text('CREATE SCHEMA {schema}'.format(schema=db_schema)))
        db.metadata.create_all(bind=db.session.connection())
        load_data()
        config_admin_user()
        load_functions()
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    ensure_print_outputs()
    ensure_unique_rows()
    return True


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


RECORD_HISTORY_LOCK_KEY = 7286337508


def ensure_record_history():
    """Create the record_history table when it is missing. On PostgreSQL one process at a time does it."""
    bind = db.session.get_bind()
    engine = getattr(bind, 'engine', bind)
    with engine.begin() as conn:
        if conn.dialect.name == 'postgresql':
            conn.execute(text('SELECT pg_advisory_xact_lock(:k)'), {'k': RECORD_HISTORY_LOCK_KEY})
        if inspect(conn).has_table(RecordHistory.__tablename__, schema=db_schema):
            return False
        RecordHistory.__table__.create(bind=conn, checkfirst=True)
    logging.getLogger(__name__).info('record_history table created in %s', db_schema)
    return True


SHARED_LAYERS_LOCK_KEY = 7286337509


def ensure_shared_layers():
    """Create the shared_layers table when it is missing. On PostgreSQL one process at a time does it."""
    bind = db.session.get_bind()
    engine = getattr(bind, 'engine', bind)
    with engine.begin() as conn:
        if conn.dialect.name == 'postgresql':
            conn.execute(text('SELECT pg_advisory_xact_lock(:k)'), {'k': SHARED_LAYERS_LOCK_KEY})
        if inspect(conn).has_table(SharedLayer.__tablename__, schema=db_schema):
            return False
        SharedLayer.__table__.create(bind=conn, checkfirst=True)
    logging.getLogger(__name__).info('shared_layers table created in %s', db_schema)
    return True


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


PRINT_NUMBER_LOCK_KEY = 7286337503
PRINT_OUTPUTS_LOCK_KEY = 7286337504

PRINT_NUMBER_FUNCTION_SQL = """CREATE OR REPLACE FUNCTION {schema}.generate_print_output_number()
RETURNS integer
LANGUAGE plpgsql
AS $function$
DECLARE
    new_output_number integer;
    current_year integer := date_part('year', CURRENT_DATE);
BEGIN
    PERFORM pg_advisory_xact_lock({lock_key});

    SELECT INTO new_output_number COALESCE(max(output_number) + 1, 1)
    FROM {schema}.print_output_number
    WHERE output_year = current_year;

    INSERT INTO {schema}.print_output_number (output_number, output_year)
    VALUES (new_output_number, current_year);

    RETURN new_output_number;
END;
$function$"""


def ensure_print_outputs():
    """Add the status column of print_outputs and the locked print number function when they are missing."""
    bind = db.session.get_bind()
    engine = getattr(bind, 'engine', bind)
    changed = False
    with engine.begin() as conn:
        if conn.dialect.name != 'postgresql':
            return False
        conn.execute(text('SELECT pg_advisory_xact_lock(:k)'), {'k': PRINT_OUTPUTS_LOCK_KEY})
        column = conn.execute(text("SELECT 1 FROM information_schema.columns WHERE table_schema = :s "
                                   "AND table_name = 'print_outputs' AND column_name = 'status'"),
                              {'s': db_schema}).first()
        if column is None:
            conn.execute(text('ALTER TABLE {schema}.print_outputs ADD COLUMN status varchar(16)'.format(
                schema=db_schema)))
            changed = True
        source = conn.execute(text("SELECT p.prosrc FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace "
                                   "WHERE n.nspname = :s AND p.proname = 'generate_print_output_number'"),
                              {'s': db_schema}).scalar()
        if source is None or 'pg_advisory_xact_lock' not in source:
            conn.execute(text(PRINT_NUMBER_FUNCTION_SQL.replace('{schema}', db_schema).replace(
                '{lock_key}', str(PRINT_NUMBER_LOCK_KEY))))
            changed = True
    if changed:
        logging.getLogger(__name__).info('print_outputs status and print number lock set in %s', db_schema)
    return changed


UNIQUE_ROWS_LOCK_KEY = 7286337506

UNIQUE_ROWS = (
    ('user_viewer_session', 'user_viewer_session_viewer_user_key',
     'DELETE FROM {schema}.user_viewer_session s USING (SELECT id, row_number() OVER ('
     'PARTITION BY viewer_id, user_id ORDER BY coalesce(updated_at, created_at) DESC NULLS LAST, id DESC) AS n '
     'FROM {schema}.user_viewer_session) d WHERE s.id = d.id AND d.n > 1',
     'CREATE UNIQUE INDEX user_viewer_session_viewer_user_key ON {schema}.user_viewer_session (viewer_id, user_id)'),
    ('user_data_layer', 'user_data_layer_uuid_key',
     'DELETE FROM {schema}.user_data_layer s USING (SELECT id, row_number() OVER ('
     'PARTITION BY lower(uuid) ORDER BY id) AS n FROM {schema}.user_data_layer WHERE uuid IS NOT NULL) d '
     'WHERE s.id = d.id AND d.n > 1',
     'CREATE UNIQUE INDEX user_data_layer_uuid_key ON {schema}.user_data_layer (lower(uuid))'),
)


def ensure_unique_rows():
    """Remove duplicate user session and data layer rows and add their unique indexes when they are missing."""
    bind = db.session.get_bind()
    engine = getattr(bind, 'engine', bind)
    log = logging.getLogger(__name__)
    changed = False
    with engine.begin() as conn:
        if conn.dialect.name != 'postgresql':
            return False
        conn.execute(text('SELECT pg_advisory_xact_lock(:k)'), {'k': UNIQUE_ROWS_LOCK_KEY})
        for table, index, dedupe, create in UNIQUE_ROWS:
            found = conn.execute(text('SELECT 1 FROM pg_indexes WHERE schemaname = :s AND tablename = :t '
                                      'AND indexname = :i'), {'s': db_schema, 't': table, 'i': index}).first()
            if found is not None:
                continue
            removed = conn.execute(text(dedupe.format(schema=db_schema))).rowcount
            conn.execute(text(create.format(schema=db_schema)))
            log.info('%s.%s: %s duplicate rows removed, unique index %s added', db_schema, table, removed, index)
            changed = True
    return changed


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
