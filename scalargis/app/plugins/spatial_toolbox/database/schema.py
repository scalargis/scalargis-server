import os

from sqlalchemy import text
from sqlalchemy import text
from sqlalchemy.sql import exists, select, and_

from app import app
from app.database import db
from app.database.schema import db_schema


def setup_db():
    with app.app_context():
        return load_functions()

def load_functions():
    created = False

    sql = '''
        select 1 
        from information_schema.routines 
        where routine_name='intersects_layers' and routine_schema='{schema}'
        and routine_type ilike 'FUNCTION';
        '''.format(schema=db_schema)

    with db.engine.begin() as con:
        if not db.session.execute(text(sql)).scalar():
            current_dir = os.path.dirname(os.path.abspath(__file__))
            filepath = os.path.join(current_dir, 'spatial_toolbox_functions.sql')

            file = open(filepath, encoding='utf-8')

            sql_text = file.read()
            sql_text = sql_text.replace('{schema}', db_schema)

            db.session.execute(text(sql_text))

            db.session.commit()

            created = True

    return created
