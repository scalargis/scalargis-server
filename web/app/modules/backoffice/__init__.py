from flask import Blueprint

mod = Blueprint('backoffice',  __name__, template_folder='templates', static_folder='static')

from app.modules.backoffice.v1 import controllers
from app.modules.backoffice.v2 import controllers
