from flask import Blueprint

mod = Blueprint('map',  __name__, template_folder='templates', static_folder='static')

from app.modules.map import controllers