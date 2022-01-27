import logging

from flask import Blueprint, request, redirect, url_for, render_template, flash
from flask_security import login_required, current_user
from flask_security.utils import encrypt_password
from sqlalchemy.exc import IntegrityError
from app.database import db
from app.utils import constants, records
from app.models.security import User
from app.models.mapas import Mapa
from app.models.securityForms import UserForm


mod = Blueprint('profile',  __name__, template_folder='templates', static_folder='static')


@mod.route('/profile', methods=['GET'])
@login_required
def index():
    logger = logging.getLogger(__name__)
    logger.debug('This message should go to the log file - profile')

    user_id = None

    if current_user and current_user.is_authenticated:
        user_id = current_user.id

    record = db.session.query(User).filter(User.id == user_id).first()
    error = None

    return render_template('profile/index.html', record=record, error=error)


@mod.route('/profile/account', methods=['GET', 'POST'])
@login_required
def account_edit():
    logger = logging.getLogger(__name__)
    logger.debug('This message should go to the log file - profile')

    user_id = None

    if current_user and current_user.is_authenticated:
        user_id = current_user.id

    record = db.session.query(User).filter(User.id == user_id).first()
    error = None

    maps = db.session.query(Mapa).order_by(Mapa.codigo).all()

    form = UserForm()

    if request.method == 'POST':
        if form.validate_on_submit():

            try:
                record.username = form.username.data
                record.email = form.email.data
                record.name = form.name.data if form.name.data else None
                record.first_name = form.first_name.data if form.first_name.data else None
                record.last_name = form.last_name.data if form.last_name.data else None

                if form.password.data:
                    record.password = encrypt_password(form.password.data)

                record.default_map = form.defaultMap.data if form.defaultMap.data else None

                db.session.commit()

                flash(constants.RECORDS_EDIT_SUCCESS)

                return redirect(url_for('profile.account_edit'))
            except IntegrityError as err:
                error = {"Message": "Já existe um utilizador com o username ou email indicado"}
            except:
                error = {"Message": constants.RECORDS_EDIT_ERROR}

            db.session.rollback()
            form.password.data = ""
        else:
            form.password.data = ""
            error = {"Message": constants.RECORDS_EDIT_ERROR}
    else:
        form.username.data = record.username
        form.email.data = record.email
        form.name.data = record.name
        form.first_name.data = record.first_name
        form.last_name.data = record.last_name
        form.password.data = ""
        form.defaultMap.data = record.default_map

    return render_template('profile/account_edit.html', form=form, record=record, maps=maps, error=error)
