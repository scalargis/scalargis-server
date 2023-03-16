from flask import Blueprint

mod = Blueprint('backoffice',  __name__, template_folder='templates', static_folder='static')

from app.modules.backoffice import controllers
