from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
user_datastore = None


def reset_database():
    from app.models.security import User
    #db.drop_all()
    #db.create_all()

#def init_user_datastore(datastore):
#    user_datastore = datastore