import os
import logging
import datetime
import sqlalchemy
from sqlalchemy import Date, cast, or_, desc
from sqlalchemy.exc import IntegrityError

from app.database import db
from app.database import user_datastore
from app.utils import constants, records
from flask import Blueprint, request, redirect, url_for, render_template, jsonify, flash, current_app
from flask_security import login_required, roles_required, current_user
from flask_security.utils import encrypt_password
from flask_sqlalchemy import BaseQuery

from app.models.mapas import ConfigMapa, Mapa, Modulo, Planta, TipoPlanta, TipoPlantaChild, PlantaTipoPlanta, PlantaLayout, SubPlanta, \
    MapaTipoPlanta, MapaPlanta, CatalogoMetadados, SiteSettings, \
    Widget, MapaWidget, ContactoMensagem, SistemaCoordenadas
from app.models.security import User, Role
from app.models.mapasForms import ConfigMapaForm, ConfigMapaSearhForm, MapaSearhForm, MapaForm, TemplatePlantaSearchForm, \
    TipoPlantaSearchForm, TipoPlantaForm, PlantaSearhForm, PlantaForm, PlantaLayoutForm, SubPlantaSearhForm, SubPlantaForm,\
    CatalogoMetadadosSearchForm, CatalogoMetadadosForm, SettingsSiteSearhForm, SettingsSiteForm, \
    AuditLogSearchForm, ContactoMensagemSearchForm
from app.models.securityForms import UserForm, UserSearchForm, RoleSearchForm, RoleForm
from app.models.auditoria import AuditLog, AuditOperacao
from app.utils import auditoria
from instance import settings

#mod = Blueprint('backoffice',  __name__, template_folder='templates', static_folder='static')
from .. import mod

def get_messages():
    return db.session.query(ContactoMensagem).\
        filter(or_(ContactoMensagem.checked == False, ContactoMensagem.checked == None)).\
        filter(or_(ContactoMensagem.closed == False, ContactoMensagem.closed == None)). \
        order_by(desc(ContactoMensagem.data_mensagem)).limit(5).all()



@mod.route('/backoffice')
@login_required
@roles_required('Admin')
def index():
    logger = logging.getLogger(__name__)
    logger.debug('This message should go to the log file - backoffice')

    visualizacoes = db.session.query(AuditLog).\
        filter(cast(AuditLog.data_ref, Date) == datetime.date.today()). \
        outerjoin(AuditLog.operacao).filter(AuditOperacao.codigo.ilike(auditoria.EnumOperacaoAuditoria.VisualizarMapa.value)).count()

    plantas = db.session.query(AuditLog).\
        filter(cast(AuditLog.data_ref, Date) == datetime.date.today()). \
        outerjoin(AuditLog.operacao).filter(AuditOperacao.codigo.ilike(auditoria.EnumOperacaoAuditoria.EmissaoPlanta.value)).count()

    analises = db.session.query(AuditLog).\
        filter(cast(AuditLog.data_ref, Date) == datetime.date.today()). \
        outerjoin(AuditLog.operacao).filter(AuditOperacao.codigo.ilike(auditoria.EnumOperacaoAuditoria.AnalisePlano.value)).count()

    total = db.session.query(AuditLog).\
        filter(cast(AuditLog.data_ref, Date) == datetime.date.today()).count()

    estatisticas = { 'visualizacoes': visualizacoes, 'plantas': plantas, 'analises': analises, 'total': total }

    mensagens = get_messages()

    #sql = text("select logdate::text,sum(count)::integer from portal.return_logs(10) group by logdate order by logdate")
    sql = 'select logdate::text,count,vm,ap,ep from portal.return_logs_types(99) order by logdate'
    result = db.engine.execute(sql)
    data_graph = []
    for row in result:
       data_graph.append({"date":row[0],"count":row[1],"vm":row[2],"ap":row[3],"ep":row[4]})


    return render_template('backoffice/index.html', estatisticas = estatisticas, tipos_stats = auditoria.EnumOperacaoAuditoria,
                           data_graph=data_graph, show_mensagens = True, mensagens = mensagens, version=settings.APP_VERSION)


@mod.route('/backoffice/mapas/config', methods=['GET', 'POST'])
@login_required
def mapas_config():
    logger = logging.getLogger(__name__)
    logger.debug('This message should go to the log file - backoffice')

    form = ConfigMapaSearhForm()

    #Set Ordering default values
    if request.method == 'GET':
        form.page.data = 1
        form.orderField.data = 'id'
        form.sortOrder.data = 'asc'
    elif request.method == 'POST':
        if 'pesquisar' in request.form:
            form.page.data = 1

    order = getattr(getattr(ConfigMapa, form.orderField.data), form.sortOrder.data)()

    query = ConfigMapa.query
    if (form.id.data):
        query = query.filter(cast(ConfigMapa.id, sqlalchemy.String).like('%' + form.id.data + '%'))
    if (form.titulo.data):
        query = query.filter(ConfigMapa.titulo.like(form.titulo.data))
    if (form.mapa.data):
        query = query.outerjoin(ConfigMapa.mapas).filter(Mapa.codigo == form.mapa.data)

    count = query.count()
    list = query.order_by(order). \
        paginate(form.page.data, settings.RECORDS_PER_PAGE, False).items

    if len(list) > 0:
        pagination = records.Pagination(form.page.data, settings.RECORDS_PER_PAGE, count)
    else:
        pagination = records.Pagination(1, settings.RECORDS_PER_PAGE, count)

    return render_template('backoffice/mapas_config.html', form=form, records=list, pagination=pagination)


@mod.route('/backoffice/mapas/config/create', methods=['GET', 'POST'])
@login_required
def mapas_config_create():
    logger = logging.getLogger(__name__)
    logger.debug('This message should go to the log file - backoffice')

    record = None
    error = None

    form = ConfigMapaForm()

    if request.method == 'POST':
        if form.validate_on_submit():
            record = ConfigMapa()

            record.titulo = form.titulo.data
            record.descricao = form.descricao.data
            record.jsonConfig = form.configuracao.data

            record.idUserIns = current_user.id
            record.dataIns = datetime.datetime.now()
            db.session.add(record)

            db.session.commit()

            flash(constants.RECORDS_INSERT_SUCCESS)
            return redirect(url_for('backoffice.mapas_config_edit', id=record.id))
        else:
            error = {"Message": constants.RECORDS_INSERT_ERROR}

    return render_template('backoffice/mapas_config_edit.html', form=form, record=record, error=error)


@mod.route('/backoffice/mapas/config/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def mapas_config_edit(id):
    logger = logging.getLogger(__name__)
    logger.debug('This message should go to the log file - backoffice')

    record = db.session.query(ConfigMapa).filter(ConfigMapa.id == id).first()
    error = None

    form = ConfigMapaForm()

    if request.method == 'POST':
        if form.validate_on_submit():
            record.titulo = form.titulo.data
            record.descricao = request.form['descricao']
            record.jsonConfig = request.form['configuracao']

            db.session.commit()

            flash(constants.RECORDS_EDIT_SUCCESS)
            return redirect(url_for('backoffice.mapas_config_edit', id=record.id))
        else:
            error = {"Message": constants.RECORDS_EDIT_ERROR}
    else:
        form.titulo.data = record.titulo
        form.descricao.data = record.descricao
        form.configuracao.data = record.jsonConfig

    return render_template('backoffice/mapas_config_edit.html', form=form, record=record, error = error)


@mod.route('/backoffice/mapas/config/delete/<int:id>', methods=['POST'])
@login_required
def mapas_config_delete(id):
    logger = logging.getLogger(__name__)
    logger.debug('This message should go to the log file - backoffice')

    record = db.session.query(ConfigMapa).filter(ConfigMapa.id == id).first()

    if record:
        if len(record.mapas) > 0:
            maps_list = ' '.join(['<span class="badge" title="' + (x.titulo or '') + '">' + x.codigo + '</span>' for x in record.mapas])
            return jsonify(Success=False, Id=id, Message='A configuração está a ser utilizada no(s) mapa(s) ' + maps_list)
    else:
        return jsonify(Success=False, Id=id, Message=constants.RECORDS_RECORD_NOT_EXISTS)

    db.session.delete(record)
    db.session.commit()

    return jsonify(Success=True, Id=id,  Message=constants.RECORDS_DELETE_SUCCESS)

@mod.route('/backoffice/mapas/config/get/<int:id>', methods=['GET'])
@login_required
def mapas_config_get(id):
    logger = logging.getLogger(__name__)
    logger.debug('This message should go to the log file - backoffice')

    record = db.session.query(ConfigMapa).filter(ConfigMapa.id == id).first()

    if not record:
        return jsonify(Success=False, Id=id, Message=constants.RECORDS_RECORD_NOT_EXISTS)

    return jsonify(Success=True, Id=id,  Message=record.jsonConfig)


@mod.route('/backoffice/mapas/mapa', methods=['GET', 'POST'])
@login_required
def mapas_mapa():
    logger = logging.getLogger(__name__)
    logger.debug('This message should go to the log file - backoffice')

    form = MapaSearhForm()

    #Set Ordering default values
    if request.method == 'GET':
        form.page.data = 1
        form.orderField.data = 'id'
        form.sortOrder.data = 'asc'
    elif request.method == 'POST':
        if 'pesquisar' in request.form:
            form.page.data = 1

    order = getattr(getattr(Mapa, form.orderField.data), form.sortOrder.data)()

    query = Mapa.query
    if (form.id.data):
        query = query.filter(cast(Mapa.id, sqlalchemy.String).like('%' + form.id.data + '%'))
    if (form.codigo.data):
        query = query.filter(Mapa.codigo.like(form.codigo.data))
    if (form.titulo.data):
        query = query.filter(Mapa.titulo.like(form.titulo.data))
    #if (form.modulo.data):
    #   query = query.outerjoin(Mapa.mapas).filter(Mapa.codigo == form.mapa.data)

    count = query.count()
    list = query.order_by(order).\
        paginate(form.page.data, settings.RECORDS_PER_PAGE, False).items

    if len(list) > 0:
        pagination = records.Pagination(form.page.data, settings.RECORDS_PER_PAGE, count)
    else:
        pagination = records.Pagination(1, settings.RECORDS_PER_PAGE, count)

    return render_template('backoffice/mapas_mapa.html', form=form, records=list, pagination=pagination)


@mod.route('/backoffice/mapas/mapa/create', methods=['GET', 'POST'])
@login_required
def mapas_mapa_create():
    logger = logging.getLogger(__name__)
    logger.debug('This message should go to the log file - backoffice')

    record = None
    error = None

    configuracoes = db.session.query(ConfigMapa).all()
    modulos = db.session.query(Modulo).all()
    catalogos = db.session.query(CatalogoMetadados).all()
    plantas = db.session.query(Planta).all()
    tipos_plantas = db.session.query(TipoPlanta).all()
    roles = db.session.query(Role).all()
    widgets = db.session.query(Widget).all()
    templates = settings.MAP_TEMPLATES

    form = MapaForm()

    if request.method == 'POST':
        if form.validate_on_submit():
            if not Mapa.query.filter(Mapa.codigo.ilike(form.codigo.data)).first():
                record = Mapa()
                record.codigo = form.codigo.data
                record.titulo = form.titulo.data
                record.descricao = form.descricao.data
                record.configuracao_id = form.configuracao.data
                if "portal" in request.form:
                    # Only one Map Portal
                    Mapa.query.update({Mapa.portal: False})
                    record.portal = True
                else:
                    record.portal = False
                if "activo" in request.form:
                    record.activo = True
                else:
                    record.activo = False

                # Template
                template="full"
                record.template = form.template.data or template

                # Default Widget
                record.show_widget = form.showWidget.data

                # Módulos
                for modulo in reversed(record.modulos):
                    record.modulos.remove(modulo)
                modulo_list = form.ModulosList.data
                for vals in modulo_list:
                    index = vals.split('|')[0]
                    for modulo in modulos:
                        if str(modulo.id) == index:
                            record.modulos.append(modulo)
                            break

                #Catalogos
                for catalogo in reversed(record.catalogos):
                    record.catalogos.remove(catalogo)
                catalogo_list = form.CatalogosList.data
                for vals in catalogo_list:
                    index = vals.split('|')[0]
                    for catalogo in catalogos:
                        if str(catalogo.id) == index:
                            record.catalogos.append(catalogo)
                            break

                # Roles
                for role in reversed(record.roles):
                    record.roles.remove(role)
                role_list = form.RolesList.data
                for vals in role_list:
                    index = vals.split('|')[0]
                    for role in roles:
                        if str(role.id) == index:
                            record.roles.append(role)
                            break

                # Header
                record.header_html = form.headerHtml.data

                # Help, Credits and Contact
                if "showHelp" in request.form:
                    record.show_help = True
                else:
                    record.show_help = False
                record.help_html = form.helpHtml.data
                if "showCredits" in request.form:
                    record.show_credits = True
                else:
                    record.show_credits = False
                record.credits_html = form.creditsHtml.data
                if "showContact" in request.form:
                    record.show_contact = True
                else:
                    record.show_contact = False

                # Scripts
                record.post_script = form.postScript.data

                # Tipos Plantas
                for tipo in reversed(record.tipos_plantas):
                    record.tipos_plantas.remove(tipo)
                tipo_planta_list = form.TiposPlantasList.data
                ordem = 1
                for index in tipo_planta_list:
                    for tipo in tipos_plantas:
                        if str(tipo.id) == index:
                            rec = MapaTipoPlanta(ordem=ordem, tipo_planta=tipo, mapa=record)
                            db.session.add(rec)
                            break
                    ordem += 1

                # Plantas
                for planta in reversed(record.plantas):
                    record.plantas.remove(planta)
                planta_list = form.PlantasList.data
                ordem = 1
                for index in planta_list:
                    for planta in plantas:
                        if str(planta.id) == index:
                            rec = MapaPlanta(ordem=ordem, planta=planta, mapa=record)
                            db.session.add(rec)
                            break
                    ordem += 1

                # Widgets
                for widget in reversed(record.widgets):
                    record.widgets.remove(widget)
                widget_list = form.WidgetsList.data
                ordem = 1
                for index in widget_list:
                    for widget in widgets:
                        if str(widget.id) == index:
                            rec = MapaWidget(ordem=ordem, widget=widget, mapa=record)
                            db.session.add(rec)
                            break
                    ordem += 1

                record.idUserIns = current_user.id
                record.dataIns = datetime.datetime.now()
                db.session.add(record)

                db.session.commit()

                flash(constants.RECORDS_INSERT_SUCCESS)
                return redirect(url_for('backoffice.mapas_mapa_edit', id=record.id))
            else:
                error = {"Message": "Já existe um mapa com o código indicado"}
        else:
            error = {"Message": constants.RECORDS_INSERT_ERROR}

    return render_template('backoffice/mapas_mapa_edit.html', form=form, record=record, configuracoes=configuracoes,
                           modulos=modulos, catalogos=catalogos, plantas=plantas, tipos_plantas=tipos_plantas,
                           tiposPlantas=tipos_plantas, roles=roles, widgets=widgets, templates=templates, error=error)


@mod.route('/backoffice/mapas/mapa/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def mapas_mapa_edit(id):
    logger = logging.getLogger(__name__)
    logger.debug('This message should go to the log file - backoffice')

    record = db.session.query(Mapa).filter(Mapa.id == id).first()
    error = None

    configuracoes = db.session.query(ConfigMapa).all()
    modulos = db.session.query(Modulo).all()
    plantas = db.session.query(Planta).all()
    tipos_plantas = db.session.query(TipoPlanta).all()
    catalogos = db.session.query(CatalogoMetadados).all()
    roles = db.session.query(Role).all()
    widgets = db.session.query(Widget).all()
    templates = settings.MAP_TEMPLATES

    '''
    There is an error when we trying to get map widgets information with ORM. We use direct sql to turnaround this error 
    '''
    sql = "select * from portal.mapas_widgets where mapa_id = {0}".format(id)
    result_widgets_old = db.session.execute(sql).fetchall()
    widgets_old = {}
    for w in result_widgets_old:
        widgets_old[str(w['widget_id'])] = {
            'config': w['config'],
            'html_content': w['html_content'],
            'target': w['target'],
            'roles': w['roles']}

    form = MapaForm()

    if request.method == 'POST':
        if form.validate_on_submit():
            try:
                record.codigo = form.codigo.data
                record.titulo = form.titulo.data
                record.descricao = form.descricao.data
                record.configuracao_id = form.configuracao.data
                if "portal" in request.form:
                    # Only one Map Portal
                    Mapa.query.update({Mapa.portal: False})

                    record.portal = True
                else:
                    record.portal = False
                if "activo" in request.form:
                    record.activo = True
                else:
                    record.activo = False

                # Template
                template="full"
                record.template = form.template.data or template

                # Default Widget
                record.show_widget = form.showWidget.data

                # Módulos
                for modulo in reversed(record.modulos):
                    record.modulos.remove(modulo)
                modulo_list = form.ModulosList.data
                for vals in modulo_list:
                    index = vals.split('|')[0]
                    for modulo in modulos:
                        if str(modulo.id) == index:
                            record.modulos.append(modulo)
                            break

                # Tipos Plantas
                for tipo in reversed(record.tipos_plantas):
                    record.tipos_plantas.remove(tipo)
                tipo_planta_list = form.TiposPlantasList.data
                ordem = 1
                for index in tipo_planta_list:
                    for tipo in tipos_plantas:
                        if str(tipo.id) == index:
                            rec = MapaTipoPlanta(ordem=ordem, tipo_planta=tipo, mapa=record)
                            db.session.add(rec)
                            break
                    ordem += 1

                # Plantas
                for planta in reversed(record.plantas):
                    record.plantas.remove(planta)
                planta_list = form.PlantasList.data
                ordem = 1
                for index in planta_list:
                    for planta in plantas:
                        if str(planta.id) == index:
                            rec = MapaPlanta(ordem=ordem, planta=planta, mapa=record)
                            db.session.add(rec)
                            break
                    ordem += 1


                #Catalogos
                for catalogo in reversed(record.catalogos):
                    record.catalogos.remove(catalogo)
                catalogo_list = form.CatalogosList.data
                for vals in catalogo_list:
                    index = vals.split('|')[0]
                    for catalogo in catalogos:
                        if str(catalogo.id) == index:
                            record.catalogos.append(catalogo)
                            break

                # Roles
                for role in reversed(record.roles):
                    record.roles.remove(role)
                role_list = form.RolesList.data
                for vals in role_list:
                    index = vals.split('|')[0]
                    for role in roles:
                        if str(role.id) == index:
                            record.roles.append(role)
                            break

                # Header
                record.header_html = form.headerHtml.data

                # Help, Credits and Contact
                if "showHelp" in request.form:
                    record.show_help = True
                else:
                    record.show_help = False
                record.help_html = form.helpHtml.data
                if "showCredits" in request.form:
                    record.show_credits = True
                else:
                    record.show_credits = False
                record.credits_html = form.creditsHtml.data
                if "showContact" in request.form:
                    record.show_contact = True
                else:
                    record.show_contact = False

                # Scripts
                record.post_script = form.postScript.data

                for widget in reversed(record.widgets):
                    record.widgets.remove(widget)
                widget_list = form.WidgetsList.data
                ordem = 1
                for index in widget_list:
                    for widget in widgets:
                        if str(widget.id) == index:
                            #target = None
                            #if widgets_old.get(str(index), None):
                            #    target = widgets_old.get(str(index)).get('target', None)
                            rec = MapaWidget(ordem=ordem, widget=widget, mapa=record)
                            if widgets_old.get(str(index), None):
                                rec.config = widgets_old.get(str(index)).get('config', None)
                                rec.html_content = widgets_old.get(str(index)).get('html_content', None)
                                rec.target = widgets_old.get(str(index)).get('target', None)
                                rec.roles = widgets_old.get(str(index)).get('roles', None)
                            db.session.add(rec)
                            break
                    ordem += 1

                # Plantas
                for p in sorted(record.planta_assoc, key=lambda x: x.ordem):
                    form.PlantasList.append_entry(str(p.planta_id))

                # Tipo de Plantas
                for t in sorted(record.tipo_planta_assoc, key=lambda x: x.ordem):
                    form.TiposPlantasList.append_entry(str(t.tipo_planta_id))

                # Widgets
                for w in sorted(record.widget_assoc, key=lambda x: x.ordem):
                    form.WidgetsList.append_entry(str(w.widget_id))

                db.session.commit()

                flash(constants.RECORDS_EDIT_SUCCESS)
                return redirect(url_for('backoffice.mapas_mapa_edit', id=record.id))
            except IntegrityError as err:
                error = {"Message": "Já existe um mapa com o código indicado"}
            except Exception as e:
                error = {"Message": constants.RECORDS_EDIT_ERROR}

            db.session.rollback()
        else:
            error = {"Message": constants.RECORDS_EDIT_ERROR}
    else:
        form.codigo.data = record.codigo
        form.titulo.data = record.titulo
        form.descricao.data = record.descricao
        form.configuracao.data = record.configuracao_id
        form.portal.data = record.portal
        form.activo.data = record.activo
        form.showHelp.data = record.show_help
        form.showCredits.data = record.show_credits
        form.showContact.data = record.show_contact
        form.helpHtml.data = record.help_html
        form.creditsHtml.data = record.credits_html
        form.template.data = record.template
        form.headerHtml.data = record.header_html
        form.postScript.data = record.post_script
        form.showWidget.data = record.show_widget

        for m in record.modulos:
            form.ModulosList.append_entry(str(m.id) + '|' + m.titulo)

        for c in record.catalogos:
            form.CatalogosList.append_entry(str(c.id) + '|' + c.titulo)

        for r in record.roles:
            form.RolesList.append_entry(str(r.id) + '|' + r.name)

        for p in sorted(record.planta_assoc, key=lambda x: x.ordem):
            form.PlantasList.append_entry(str(p.planta_id))

        for t in sorted(record.tipo_planta_assoc, key=lambda x: x.ordem):
            form.TiposPlantasList.append_entry(str(t.tipo_planta_id))

        for w in sorted(record.widget_assoc, key=lambda x: x.ordem):
            form.WidgetsList.append_entry(str(w.widget_id))

    return render_template('backoffice/mapas_mapa_edit.html', form=form, record=record, configuracoes=configuracoes,
                           modulos=modulos, plantas=plantas, tipos_plantas=tipos_plantas, catalogos=catalogos,
                           roles=roles, widgets=widgets, templates=templates, error=error)


@mod.route('/backoffice/mapas/mapa/delete/<int:id>', methods=['POST'])
@login_required
def mapas_mapa_delete(id):
    logger = logging.getLogger(__name__)
    logger.debug('This message should go to the log file - backoffice')

    record = db.session.query(Mapa).filter(Mapa.id == id).first()

    if record:
        record.modulos = []
        record.roles = []
        record.widgets = []
        record.tipos_plantas = []
        record.plantas = []
        record.catalogos = []
    else:
        return jsonify(Success=False, Id=id, Message=constants.RECORDS_RECORD_NOT_EXISTS)

    db.session.delete(record)
    db.session.commit()

    return jsonify(Success=True, Id=id,  Message=constants.RECORDS_DELETE_SUCCESS)


@mod.route('/backoffice/security/user', methods=['GET', 'POST'])
@login_required
def security_user():
    logger = logging.getLogger(__name__)
    logger.debug('This message should go to the log file - backoffice')

    form = UserSearchForm()
    query = Role.query

    if request.method == 'GET':
        #Set Ordering default values
        form.page.data = 1
        form.orderField.data = 'id'
        form.sortOrder.data = 'asc'
    elif request.method == 'POST':
        if 'pesquisar' in request.form:
            form.page.data = 1

    order = getattr(getattr(User, form.orderField.data), form.sortOrder.data)()

    query = User.query
    if (form.id.data):
        query = query.filter(cast(User.id, sqlalchemy.String).like('%' + form.id.data + '%'))
    if (form.username.data):
        query = query.filter(User.username.ilike(form.username.data))
    if (form.email.data):
        query = query.filter(User.email.ilike(form.email.data))
    if (form.name.data):
        query = query.filter(User.name.ilike(form.name.data))
    if (form.role.data):
        query = query.outerjoin(User.roles).filter(Role.name == form.role.data)

    count = query.count()
    list = query.order_by(order).\
        paginate(form.page.data, settings.RECORDS_PER_PAGE, False).items

    if len(list) > 0:
        pagination = records.Pagination(form.page.data, settings.RECORDS_PER_PAGE, count)
    else:
        pagination = records.Pagination(1, settings.RECORDS_PER_PAGE, count)

    return render_template('backoffice/security_user.html', form=form, records=list, pagination=pagination)


@mod.route('/backoffice/security/user/create', methods=['GET', 'POST'])
@login_required
def security_user_create():
    logger = logging.getLogger(__name__)
    logger.debug('This message should go to the log file - backoffice')

    record = None
    error = None

    maps = db.session.query(Mapa).order_by(Mapa.codigo).all()

    roles = db.session.query(Role).all()

    form = UserForm()

    if request.method == 'POST':
        if form.validate_on_submit():

            if not User.query.filter(or_(User.email.ilike(form.email.data), User.email.ilike(form.username.data))).first():
                record = user_datastore.create_user(
                    username=form.username.data,
                    email=form.email.data,
                    name=form.name.data if form.name.data else None,
                    first_name=form.first_name.data if form.first_name.data else None,
                    last_name=form.last_name.data if form.last_name.data else None,
                    password=encrypt_password(form.password.data),
                    active= True if "active" in request.form else False,
                    default_map=form.defaultMap.data if form.defaultMap.data else None
                )

                role_list = form.RolesList.data
                for index in role_list:
                    for role in roles:
                        if str(role.id) == index:
                            record.roles.append(role)
                            break

                db.session.commit()

                flash(constants.RECORDS_INSERT_SUCCESS)
                return redirect(url_for('backoffice.security_user_edit', id=record.id))
            else:
                form.password.data = ""
                error = {"Message": "Já existe um utilizador com o username ou email indicado"}
        else:
            form.password.data = ""
            error = {"Message": constants.RECORDS_INSERT_ERROR}

    return render_template('backoffice/security_user_edit.html', form=form, record=record, roles=roles, maps=maps, error=error)


@mod.route('/backoffice/security/user/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def security_user_edit(id):
    logger = logging.getLogger(__name__)
    logger.debug('This message should go to the log file - backoffice')

    record = db.session.query(User).filter(User.id == id).first()
    error = None

    maps = db.session.query(Mapa).order_by(Mapa.codigo).all()

    roles = db.session.query(Role).all()

    form = UserForm()

    if request.method == 'POST':
        if form.validate_on_submit():

            try:
                record.username = form.username.data
                record.email = form.email.data
                record.name = form.name.data if form.name.data else None
                record.first_name = form.first_name.data if form.first_name.data else None
                record.last_name = form.last_name.data if form.last_name.data else None
                if "active" in request.form:
                    record.active = True
                else:
                    record.active = False

                if form.password.data:
                    record.password = encrypt_password(form.password.data)

                record.default_map = form.defaultMap.data if form.defaultMap.data else None

                # Roles
                for role in reversed(record.roles):
                    record.roles.remove(role)
                role_list = form.RolesList.data
                for index in role_list:
                    for role in roles:
                        if str(role.id) == index:
                            record.roles.append(role)
                            break

                db.session.commit()

                flash(constants.RECORDS_EDIT_SUCCESS)

                return redirect(url_for('backoffice.security_user_edit', id=record.id))
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
        form.active.data = record.active
        form.password.data = ""
        form.defaultMap.data = record.default_map
        for r in record.roles:
            form.RolesList.append_entry(str(r.id))

    return render_template('backoffice/security_user_edit.html', form=form, record=record, maps=maps, roles=roles, error=error)


@mod.route('/backoffice/security/user/delete/<int:id>', methods=['POST'])
@login_required
def security_user_delete(id):
    logger = logging.getLogger(__name__)
    logger.debug('This message should go to the log file - backoffice')

    record = db.session.query(User).filter(User.id == id).first()

    if record:
        #if len(record.modulos) > 0:
        #    return jsonify(Success=False, Id=id, Message='A configuração está a ser utilizada em mapas')
        s = ""
    else:
        return jsonify(Success=False, Id=id, Message=constants.RECORDS_RECORD_NOT_EXISTS)

    db.session.delete(record)
    db.session.commit()

    return jsonify(Success=True, Id=id,  Message=constants.RECORDS_DELETE_SUCCESS)


@mod.route('/backoffice/security/role', methods=['GET', 'POST'])
@login_required
def security_role():
    logger = logging.getLogger(__name__)
    logger.debug('This message should go to the log file - backoffice')

    form = RoleSearchForm()
    query = Role.query

    if request.method == 'GET':
        #Set Ordering default values
        form.page.data = 1
        form.orderField.data = 'id'
        form.sortOrder.data = 'asc'
    elif request.method == 'POST':
        if 'pesquisar' in request.form:
            form.page.data = 1

        if (form.id.data):
            query = query.filter(cast(Role.id, sqlalchemy.String).like('%' + form.id.data + '%'))
        if (form.name.data):
            query = query.filter(Role.name.ilike(form.name.data))

    order = getattr(getattr(Role, form.orderField.data), form.sortOrder.data)()
    count = query.count()
    list = query.order_by(order).\
        paginate(form.page.data, settings.RECORDS_PER_PAGE, False).items

    if len(list) > 0:
        pagination = records.Pagination(form.page.data, settings.RECORDS_PER_PAGE, count)
    else:
        pagination = records.Pagination(1, settings.RECORDS_PER_PAGE, count)

    return render_template('backoffice/security_role.html', form=form, records=list, pagination=pagination)


@mod.route('/backoffice/security/role/create', methods=['GET', 'POST'])
@login_required
def security_role_create():
    logger = logging.getLogger(__name__)
    logger.debug('This message should go to the log file - backoffice')

    record = None
    error = None

    users = db.session.query(User).all()

    form = RoleForm()

    if request.method == 'POST':
        if form.validate_on_submit():

            if not Role.query.filter(Role.name.ilike(form.name.data)).first():
                record = Role()

                record.name = form.name.data

                user_list = form.UsersList.data
                for index in user_list:
                    for user in users:
                        if str(user.id) == index:
                            record.users.append(user)
                            break

                db.session.add(record)
                db.session.commit()

                flash(constants.RECORDS_INSERT_SUCCESS)
                return redirect(url_for('backoffice.security_role_edit', id=record.id))
            else:
                error = {"Message": "Já existe um grupo com o nome indicado"}
        else:
            error = {"Message": constants.RECORDS_INSERT_ERROR}

    return render_template('backoffice/security_role_edit.html', form=form, record=record, users=users, error=error)

@mod.route('/backoffice/security/role/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def security_role_edit(id):
    logger = logging.getLogger(__name__)
    logger.debug('This message should go to the log file - backoffice')

    record = db.session.query(Role).filter(Role.id == id).first()
    error = None

    users = db.session.query(User).all()

    form = RoleForm()

    if request.method == 'POST':
        if form.validate_on_submit():

            try:
                record.name = form.name.data

                # Users
                for user in reversed(record.users.all()):
                    record.users.remove(user)
                user_list = form.UsersList.data
                for index in user_list:
                    for user in users:
                        if str(user.id) == index:
                            record.users.append(user)
                            break

                db.session.commit()

                flash(constants.RECORDS_EDIT_SUCCESS)

                return redirect(url_for('backoffice.security_role_edit', id=record.id))
            except IntegrityError as err:
                error = {"Message": "Já existe um grupo com o nome indicado"}
            except:
                error = {"Message": constants.RECORDS_EDIT_ERROR}

        db.session.rollback()
    else:
        form.name.data = record.name
        for u in record.users:
            form.UsersList.append_entry(str(u.id))

    return render_template('backoffice/security_role_edit.html', form=form, record=record, users=users, error=error)


@mod.route('/backoffice/security/role/delete/<int:id>', methods=['POST'])
@login_required
def security_role_delete(id):
    logger = logging.getLogger(__name__)
    logger.debug('This message should go to the log file - backoffice')

    record = db.session.query(Role).filter(Role.id == id).first()

    if record:
        #if len(record.modulos) > 0:
        #    return jsonify(Success=False, Id=id, Message='A configuração está a ser utilizada em mapas')
        s = ""
    else:
        return jsonify(Success=False, Id=id, Message=constants.RECORDS_RECORD_NOT_EXISTS)

    db.session.delete(record)
    db.session.commit()

    return jsonify(Success=True, Id=id,  Message=constants.RECORDS_DELETE_SUCCESS)


@mod.route('/backoffice/plantas/template', methods=['GET', 'POST'])
@login_required
def plantas_template():
    logger = logging.getLogger(__name__)
    logger.debug('This message should go to the log file - backoffice')

    form = TemplatePlantaSearchForm()

    #Set Ordering default values
    if request.method == 'GET':
        form.page.data = 1
        form.orderField.data = 'filename'
        form.sortOrder.data = 'asc'

    # Joining the base and the pdf dir path
    path = os.path.join(settings.APP_RESOURCES, 'pdf')

    # Return 404 if path doesn't exist
    if not os.path.exists(path):
        return 'A directoria definida para os templates não existe: %s' % path

    # Show directory contents
    list_dir = os.listdir(path)

    files = []
    for f in os.scandir(path):
        name = f.name
        if name.lower().endswith('.pdf'):
            st = datetime.datetime.fromtimestamp(f.stat().st_ctime).strftime('%Y-%m-%d %H:%M:%S')
            size = round(f.stat().st_size/1024)
            files.append({"filename": name, "date": st, "size": size})

    if form.sortOrder.data == 'desc':
        files.sort(key=lambda pair: pair.get(form.orderField.data or 'filename'), reverse = True)
    else:
        files.sort(key=lambda pair: pair.get(form.orderField.data or 'filename'))

    return render_template('backoffice/plantas_template_planta.html', form=form, path=path, files=files)


@mod.route('/backoffice/plantas/template/delete/<string:file>', methods=['POST'])
@login_required
def plantas_template_delete(file):
    logger = logging.getLogger(__name__)
    logger.debug('This message should go to the log file - backoffice')

    try:
        os.remove(os.path.join(settings.APP_RESOURCES, 'pdf', file))
        return jsonify(Success=True, Filename=file, Message=constants.RECORDS_DELETE_SUCCESS)
    except OSError:
        pass
        return jsonify(Success=False, Filename=file, Message=constants.RECORDS_DELETE_ERROR)


@mod.route('/backoffice/plantas/grupo', methods=['GET', 'POST'])
@login_required
def plantas_tipo():
    logger = logging.getLogger(__name__)
    logger.debug('This message should go to the log file - backoffice')

    form = TipoPlantaSearchForm()

    mapas = db.session.query(Mapa).all()
    plantas = db.session.query(Planta).all()

    #Set Ordering default values
    if request.method == 'GET':
        form.page.data = 1
        form.orderField.data = 'id'
        form.sortOrder.data = 'asc'
    elif request.method == 'POST':
        if 'pesquisar' in request.form:
            form.page.data = 1

    order = getattr(getattr(TipoPlanta, form.orderField.data), form.sortOrder.data)()

    query = TipoPlanta.query
    if (form.id.data):
        query = query.filter(cast(TipoPlanta.id, sqlalchemy.String).like('%' + form.id.data + '%'))
    if (form.codigo.data):
        query = query.filter(TipoPlanta.codigo.ilike(form.codigo.data))
    if (form.titulo.data):
        query = query.filter(TipoPlanta.titulo.ilike(form.titulo.data))
    if (form.planta.data):
        planta_list = request.form.getlist('planta')
        form.planta.data = ','.join(planta_list)
        query = query.outerjoin(TipoPlanta.plantas).filter(TipoPlanta.codigo.in_(planta_list))
    if (form.mapa.data):
        mapa_list = request.form.getlist('mapa')
        form.mapa.data = ','.join(mapa_list)
        query = query.outerjoin(TipoPlanta.mapas).filter(TipoPlanta.codigo.in_(mapa_list))

    count = query.count()
    list = query.order_by(order).\
        paginate(form.page.data, settings.RECORDS_PER_PAGE, False).items

    if len(list) > 0:
        pagination = records.Pagination(form.page.data, settings.RECORDS_PER_PAGE, count)
    else:
        pagination = records.Pagination(1, settings.RECORDS_PER_PAGE, count)

    return render_template('backoffice/plantas_tipo_planta.html', form=form, records=list, mapas=mapas, plantas=plantas, pagination=pagination)


@mod.route('/backoffice/plantas/grupo/create', methods=['GET', 'POST'])
@login_required
def plantas_tipo_create():
    logger = logging.getLogger(__name__)
    logger.debug('This message should go to the log file - backoffice')

    record = None
    error = None

    tipos_plantas = db.session.query(TipoPlanta).all()

    plantas = db.session.query(Planta).all()

    form = TipoPlantaForm()

    if request.method == 'POST':
        if form.validate_on_submit():
            if not User.query.filter(TipoPlanta.codigo.ilike(form.codigo.data)).first():
                record = TipoPlanta()

                record.codigo = form.codigo.data
                record.titulo = form.titulo.data
                record.descricao = form.descricao.data
                if "identificacaoRequerente" in request.form:
                    record.identificacaoRequerente = True
                else:
                    record.identificacaoRequerente = False
                if "marcacaoLocal" in request.form:
                    record.marcacaoLocal = True
                else:
                    record.marcacaoLocal = False
                if "multiGeom" in request.form:
                    record.multiGeom = True
                else:
                    record.multiGeom = False

                if "autorEmissao" in request.form:
                    record.autorEmissao = True
                else:
                    record.autorEmissao = False
                if "guiaPagamento" in request.form:
                    record.guiaPagamento = True
                else:
                    record.guiaPagamento = False
                if "finalidadeEmissao" in request.form:
                    record.finalidadeEmissao = True
                else:
                    record.finalidadeEmissao = False

                if "activo" in request.form:
                    record.activo = True
                else:
                    record.activo = False
                record.tolerancia = form.tolerancia.data
                if "showAll" in request.form:
                    record.showAll = True
                else:
                    record.showAll = False

                if "seleccaoPlantas" in request.form:
                    record.seleccaoPlantas = True
                else:
                    record.seleccaoPlantas = False
                if "agruparPlantas" in request.form:
                    record.agruparPlantas = True
                else:
                    record.agruparPlantas = False

                record.idUserIns = current_user.id
                record.dataIns = datetime.datetime.now()
                db.session.add(record)

                db.session.commit()

                # Tipos Plantas
                record.tipo_planta_child_assoc.clear()
                tipo_planta_list = form.TiposPlantasList.data
                ordem = 1
                for index in tipo_planta_list:
                    for tipo in tipos_plantas:
                        if str(tipo.id) == index:
                            rec = TipoPlantaChild(ordem=ordem, tipo_planta_id=record.id, tipo_planta_child_id=tipo.id)
                            db.session.add(rec)
                            break
                    ordem += 1

                # Plantas
                for planta in reversed(record.plantas):
                    record.plantas.remove(planta)
                planta_list = form.PlantasList.data
                ordem = 1
                for index in planta_list:
                    for planta in plantas:
                        if str(planta.id) == index:
                            rec = PlantaTipoPlanta(ordem=ordem, planta=planta, tipo_planta=record)
                            #record.plantas.append(planta)
                            db.session.add(rec)
                            break
                    ordem += 1

                db.session.commit()

                flash(constants.RECORDS_INSERT_SUCCESS)
                return redirect(url_for('backoffice.plantas_tipo_edit', id=record.id))
            else:
                error = {"Message": "Já existe um tipo de planta com o código indicado"}
        else:
            error = {"Message": constants.RECORDS_INSERT_ERROR}

    return render_template('backoffice/plantas_tipo_planta_edit.html', form=form, record=record, tipos_plantas=tipos_plantas, plantas=plantas, error=error)

@mod.route('/backoffice/plantas/grupo/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def plantas_tipo_edit(id):
    logger = logging.getLogger(__name__)
    logger.debug('This message should go to the log file - backoffice')

    record = db.session.query(TipoPlanta).filter(TipoPlanta.id == id).first()
    error = None

    plantas = db.session.query(Planta).all()

    tipos_plantas = db.session.query(TipoPlanta).filter(TipoPlanta.id != id).all()

    form = TipoPlantaForm()

    if request.method == 'POST':
        if form.validate_on_submit():
            try:
                record.codigo = form.codigo.data
                record.titulo = form.titulo.data
                record.descricao = form.descricao.data
                if "identificacaoRequerente" in request.form:
                    record.identificacaoRequerente = True
                else:
                    record.identificacaoRequerente = False
                if "marcacaoLocal" in request.form:
                    record.marcacaoLocal = True
                else:
                    record.marcacaoLocal = False
                if "multiGeom" in request.form:
                    record.multiGeom = True
                else:
                    record.multiGeom = False

                if "autorEmissao" in request.form:
                    record.autorEmissao = True
                else:
                    record.autorEmissao = False
                if "guiaPagamento" in request.form:
                    record.guiaPagamento = True
                else:
                    record.guiaPagamento = False
                if "finalidadeEmissao" in request.form:
                    record.finalidadeEmissao = True
                else:
                    record.finalidadeEmissao = False

                if "activo" in request.form:
                    record.activo = True
                else:
                    record.activo = False
                record.tolerancia = form.tolerancia.data
                if "showAll" in request.form:
                    record.showAll = True
                else:
                    record.showAll = False

                if "seleccaoPlantas" in request.form:
                    record.seleccaoPlantas = True
                else:
                    record.seleccaoPlantas = False
                if "agruparPlantas" in request.form:
                    record.agruparPlantas = True
                else:
                    record.agruparPlantas = False

                # Tipos Plantas
                record.tipo_planta_child_assoc.clear()
                tipo_planta_list = form.TiposPlantasList.data
                ordem = 1
                for index in tipo_planta_list:
                    for tipo in tipos_plantas:
                        if str(tipo.id) == index:
                            rec = TipoPlantaChild(ordem=ordem, tipo_planta_id=record.id, tipo_planta_child_id=tipo.id)
                            db.session.add(rec)
                            break
                    ordem += 1

                # Plantas
                for planta in reversed(record.plantas):
                    record.plantas.remove(planta)
                planta_list = form.PlantasList.data
                ordem = 1
                for index in planta_list:
                    for planta in plantas:
                        if str(planta.id) == index:
                            rec = PlantaTipoPlanta(ordem=ordem, planta=planta, tipo_planta=record)
                            #record.plantas.append(planta)
                            db.session.add(rec)
                            break
                    ordem += 1

                db.session.commit()

                flash(constants.RECORDS_EDIT_SUCCESS)
                return redirect(url_for('backoffice.plantas_tipo_edit', id=record.id))
            except IntegrityError as err:
                error = {"Message": "Já existe um tipo de planta com o código indicado"}
            #except:
            #    error = {"Message": constants.RECORDS_EDIT_ERROR}

            db.session.rollback()
        else:
            error = {"Message": constants.RECORDS_EDIT_ERROR}
    else:
        form.codigo.data = record.codigo
        form.titulo.data = record.titulo
        form.descricao.data = record.descricao
        form.identificacaoRequerente.data = record.identificacaoRequerente
        form.marcacaoLocal.data = record.marcacaoLocal
        form.multiGeom.data = record.multiGeom
        form.autorEmissao.data = record.autorEmissao
        form.guiaPagamento.data = record.guiaPagamento
        form.finalidadeEmissao.data = record.finalidadeEmissao
        form.tolerancia.data = record.tolerancia
        form.showAll.data = record.showAll
        form.activo.data = record.activo
        form.seleccaoPlantas.data = record.seleccaoPlantas
        form.agruparPlantas.data = record.agruparPlantas

        for t in sorted(record.tipo_planta_child_assoc, key=lambda x: x.ordem):
            form.TiposPlantasList.append_entry(str(t.tipo_planta_child_id))

        for p in sorted(record.planta_assoc, key=lambda x: x.ordem):
            form.PlantasList.append_entry(str(p.planta_id))

    return render_template('backoffice/plantas_tipo_planta_edit.html', form=form, record=record, tipos_plantas=tipos_plantas, plantas=plantas, error=error)


@mod.route('/backoffice/plantas/grupo/delete/<int:id>', methods=['POST'])
@login_required
def plantas_tipo_delete(id):
    logger = logging.getLogger(__name__)
    logger.debug('This message should go to the log file - backoffice')

    record = db.session.query(TipoPlanta).filter(TipoPlanta.id == id).first()

    if record:
        for planta in reversed(record.plantas):
            record.plantas.remove(planta)

        for planta in reversed(record.planta_assoc):
            record.planta_assoc.remove(planta)
    else:
        return jsonify(Success=False, Id=id, Message=constants.RECORDS_RECORD_NOT_EXISTS)

    db.session.delete(record)
    db.session.commit()

    return jsonify(Success=True, Id=id,  Message=constants.RECORDS_DELETE_SUCCESS)


@mod.route('/backoffice/plantas', methods=['GET', 'POST'])
@login_required
def plantas():
    logger = logging.getLogger(__name__)
    logger.debug('This message should go to the log file - backoffice')

    form = PlantaSearhForm()

    mapas = db.session.query(Mapa).all()

    #Set Ordering default values
    if request.method == 'GET':
        form.page.data = 1
        form.orderField.data = 'id'
        form.sortOrder.data = 'asc'
    elif request.method == 'POST':
        if 'pesquisar' in request.form:
            form.page.data = 1

    order = getattr(getattr(Planta, form.orderField.data), form.sortOrder.data)()

    query = Planta.query
    if (form.id.data):
        query = query.filter(cast(Planta.id, sqlalchemy.String).like('%' + form.id.data + '%'))
    if (form.codigo.data):
        query = query.filter(Planta.codigo.ilike(form.codigo.data))
    if (form.nome.data):
        query = query.filter(Planta.nome.ilike(form.nome.data))
    if (form.titulo.data):
        query = query.filter(Planta.titulo.ilike(form.titulo.data))
    if (form.escala.data):
        query = query.filter(cast(Planta.escala, sqlalchemy.String).like('%' + form.escala.data + '%'))
    if (form.formato.data):
        query = query.filter(Planta.formato.ilike(form.formato.data))
    if (form.orientacao.data):
        query = query.filter(Planta.orientacao.ilike(form.orientacao.data))
    if (form.mapa.data):
        mapa_list = request.form.getlist('mapa')
        form.mapa.data = ','.join(mapa_list)
        query = query.outerjoin(Planta.mapas).filter(Mapa.codigo.in_(mapa_list))

    count = query.count()
    list = query.order_by(order).\
        paginate(form.page.data, settings.RECORDS_PER_PAGE, False).items

    if len(list) > 0:
        pagination = records.Pagination(form.page.data, settings.RECORDS_PER_PAGE, count)
    else:
        pagination = records.Pagination(1, settings.RECORDS_PER_PAGE, count)

    return render_template('backoffice/plantas_planta.html', form=form, records=list, mapas=mapas, pagination=pagination)


@mod.route('/backoffice/plantas/create', methods=['GET', 'POST'])
@login_required
def plantas_create():
    logger = logging.getLogger(__name__)
    logger.debug('This message should go to the log file - backoffice')

    record = None
    error = None

    tipos_plantas = db.session.query(TipoPlanta).all()
    roles = db.session.query(Role).all()
    coord_sys = db.session.query(SistemaCoordenadas).all()

    form = PlantaForm()

    if request.method == 'POST':
        if form.validate_on_submit():
            if not Planta.query.filter(Planta.codigo.ilike(form.codigo.data)).first():
                record = Planta()

                record.codigo = form.codigo.data
                record.nome = form.nome.data
                record.titulo = form.titulo.data
                record.descricao = form.descricao.data
                record.configuracao = form.configuracao.data
                record.escala = form.escala.data
                record.formato = form.formato.data
                record.orientacao = form.orientacao.data
                record.srid = form.srid.data
                record.template = form.template.data
                if "identificacao" in request.form:
                    record.identificacao = True
                else:
                    record.identificacao = False
                if "marcacaoLocal" in request.form:
                    record.marcacaoLocal = True
                else:
                    record.marcacaoLocal = False
                if "desenharLocal" in request.form:
                    record.desenharLocal = True
                else:
                    record.desenharLocal = False
                if "multiGeom" in request.form:
                    record.multiGeom = True
                else:
                    record.multiGeom = False
                if "emissaoLivre" in request.form:
                    record.emissaoLivre  = True
                else:
                    record.emissaoLivre  = False
                if "tituloEmissao" in request.form:
                    record.tituloEmissao  = True
                else:
                    record.tituloEmissao  = False

                if "autorEmissao" in request.form:
                    record.autorEmissao = True
                else:
                    record.autorEmissao = False
                if "guiaPagamento" in request.form:
                    record.guiaPagamento = True
                else:
                    record.guiaPagamento = False
                if "finalidadeEmissao" in request.form:
                    record.finalidadeEmissao = True
                else:
                    record.finalidadeEmissao = False

                if "activo" in request.form:
                    record.activo  = True
                else:
                    record.activo  = False

                record.idUserIns = current_user.id
                record.dataIns = datetime.datetime.now()
                db.session.add(record)

                db.session.commit()

                flash(constants.RECORDS_INSERT_SUCCESS)
                return redirect(url_for('backoffice.plantas_edit', id=record.id))
            else:
                error = {"Message": "Já existe uma planta com o código indicado"}
        else:
            error = {"Message": constants.RECORDS_INSERT_ERROR}

    return render_template('backoffice/plantas_planta_edit.html', form=form, record=record, roles=roles, coord_sys=coord_sys, error=error)


@mod.route('/backoffice/plantas/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def plantas_edit(id):
    logger = logging.getLogger(__name__)
    logger.debug('This message should go to the log file - backoffice')

    record = db.session.query(Planta).filter(Planta.id == id).first()
    error = None

    roles = db.session.query(Role).all()
    coord_sys = db.session.query(SistemaCoordenadas).all()

    form = PlantaForm()

    if request.method == 'POST':
        if form.validate_on_submit():
            try:
                record.codigo = form.codigo.data
                record.nome = form.nome.data
                record.titulo = form.titulo.data
                record.descricao = form.descricao.data
                record.configuracao = form.configuracao.data
                record.escala = form.escala.data
                record.formato = form.formato.data
                record.orientacao = form.orientacao.data
                record.srid = form.srid.data
                if "identificacao" in request.form:
                    record.identificacao = True
                else:
                    record.identificacao = False
                if "marcacaoLocal" in request.form:
                    record.marcacaoLocal = True
                else:
                    record.marcacaoLocal = False
                if "desenharLocal" in request.form:
                    record.desenharLocal = True
                else:
                    record.desenharLocal = False
                if "multiGeom" in request.form:
                    record.multiGeom = True
                else:
                    record.multiGeom = False
                if "emissaoLivre" in request.form:
                    record.emissaoLivre  = True
                else:
                    record.emissaoLivre  = False
                if "tituloEmissao" in request.form:
                    record.tituloEmissao  = True
                else:
                    record.tituloEmissao  = False
                if "autorEmissao" in request.form:
                    record.autorEmissao = True
                else:
                    record.autorEmissao = False
                if "guiaPagamento" in request.form:
                    record.guiaPagamento = True
                else:
                    record.guiaPagamento = False
                if "finalidadeEmissao" in request.form:
                    record.finalidadeEmissao = True
                else:
                    record.finalidadeEmissao = False

                if "activo" in request.form:
                    record.activo  = True
                else:
                    record.activo  = False

                # Roles
                for role in reversed(record.roles):
                    record.roles.remove(role)
                role_list = form.RolesList.data
                for vals in role_list:
                    index = vals.split('|')[0]
                    for role in roles:
                        if str(role.id) == index:
                            record.roles.append(role)
                            break

                db.session.commit()

                flash(constants.RECORDS_EDIT_SUCCESS)
                return redirect(url_for('backoffice.plantas_edit', id=record.id))
            except IntegrityError as err:
                error = {"Message": "Já existe uma planta com o código indicado"}
            except:
                error = {"Message": constants.RECORDS_EDIT_ERROR}

            db.session.rollback()
        else:
            error = {"Message": constants.RECORDS_EDIT_ERROR}
    else:
        form.codigo.data = record.codigo
        form.nome.data = record.nome
        form.titulo.data = record.titulo
        form.descricao.data = record.descricao
        form.escala.data = record.escala
        form.formato.data = record.formato
        form.orientacao.data = record.orientacao
        form.srid.data = record.srid
        form.configuracao.data = record.configuracao
        form.identificacao.data = record.identificacao
        form.marcacaoLocal.data = record.marcacaoLocal
        form.desenharLocal.data = record.desenharLocal
        form.multiGeom.data = record.multiGeom
        form.emissaoLivre.data = record.emissaoLivre
        form.tituloEmissao.data = record.tituloEmissao
        form.autorEmissao.data = record.autorEmissao
        form.guiaPagamento.data = record.guiaPagamento
        form.finalidadeEmissao.data = record.finalidadeEmissao
        form.activo.data = record.activo
        for r in record.roles:
            form.RolesList.append_entry(str(r.id) + '|' + r.name)

    return render_template('backoffice/plantas_planta_edit.html', form=form, record=record, roles=roles, coord_sys=coord_sys, error=error)


@mod.route('/backoffice/plantas/delete/<int:id>', methods=['POST'])
@login_required
def plantas_delete(id):
    logger = logging.getLogger(__name__)
    logger.debug('This message should go to the log file - backoffice')

    record = db.session.query(Planta).filter(Planta.id == id).first()

    if record:
        for tipo in reversed(record.tipos_plantas):
            record.tipos_plantas.remove(tipo)
        for tipo in reversed(record.tipo_planta_assoc):
            record.tipo_planta_assoc.remove(tipo)

        for mapa in reversed(record.mapas):
            record.mapas.remove(mapa)
        for tipo in reversed(record.mapa_assoc):
            record.mapa_assoc.remove(mapa)
    else:
        return jsonify(Success=False, Id=id, Message=constants.RECORDS_RECORD_NOT_EXISTS)

    db.session.delete(record)
    db.session.commit()

    return jsonify(Success=True, Id=id,  Message=constants.RECORDS_DELETE_SUCCESS)




@mod.route('/backoffice/plantas/<int:planta_id>/layouts/create', methods=['GET', 'POST'])
@login_required
def plantas_layouts_create(planta_id):
    logger = logging.getLogger(__name__)
    logger.debug('This message should go to the log file - backoffice')

    record = None
    error = None

    planta = db.session.query(Planta).filter(Planta.id == planta_id).first()

    form = PlantaLayoutForm()
    form.planta_id.data = planta_id

    if request.method == 'POST':
        if form.validate_on_submit():
            record = PlantaLayout()

            record.planta_id = form.planta_id.data
            record.formato = form.formato.data
            record.orientacao = form.orientacao.data
            record.configuracao = form.configuracao.data

            db.session.add(record)

            db.session.commit()

            flash(constants.RECORDS_INSERT_SUCCESS)
            return redirect(url_for('backoffice.plantas_edit', id=planta_id))
        else:
            error = {"Message": constants.RECORDS_INSERT_ERROR}

    return render_template('backoffice/plantas_layout_edit.html', form=form, record=record, planta=planta, error=error)


@mod.route('/backoffice/plantas/layouts/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def plantas_layouts_edit(id):
    logger = logging.getLogger(__name__)
    logger.debug('This message should go to the log file - backoffice')

    record = db.session.query(PlantaLayout).filter(PlantaLayout.id == id).first()
    error = None

    form = PlantaLayoutForm()

    if request.method == 'POST':
        if form.validate_on_submit():
            try:
                record.formato = form.formato.data
                record.orientacao = form.orientacao.data
                record.configuracao = form.configuracao.data

                db.session.commit()

                flash(constants.RECORDS_EDIT_SUCCESS)
                return redirect(url_for('backoffice.plantas_layouts_edit', id=record.id))
            except:
                error = {"Message": constants.RECORDS_EDIT_ERROR}

            db.session.rollback()
        else:
            error = {"Message": constants.RECORDS_EDIT_ERROR}
    else:
        form.planta_id.data = record.planta_id
        form.formato.data = record.formato
        form.orientacao.data = record.orientacao
        form.configuracao.data = record.configuracao

    return render_template('backoffice/plantas_layout_edit.html', form=form, record=record, planta=record.planta, error=error)



@mod.route('/backoffice/plantas/layout/delete/<int:id>', methods=['POST'])
@login_required
def plantas_layouts_delete(id):
    logger = logging.getLogger(__name__)
    logger.debug('This message should go to the log file - backoffice')

    record = db.session.query(PlantaLayout).filter(PlantaLayout.id == id).first()

    if record:
        db.session.delete(record)
        db.session.commit()
    else:
        return jsonify(Success=False, Id=id, Message=constants.RECORDS_RECORD_NOT_EXISTS)

    return jsonify(Success=True, Id=id,  Message=constants.RECORDS_DELETE_SUCCESS)















@mod.route('/backoffice/subplantas', methods=['GET', 'POST'])
@login_required
def sub_plantas():
    logger = logging.getLogger(__name__)
    logger.debug('This message should go to the log file - backoffice')

    form = SubPlantaSearhForm()

    #Set Ordering default values
    if request.method == 'GET':
        form.page.data = 1
        form.orderField.data = 'id'
        form.sortOrder.data = 'asc'
    elif request.method == 'POST':
        if 'pesquisar' in request.form:
            form.page.data = 1

    order = getattr(getattr(SubPlanta, form.orderField.data), form.sortOrder.data)()

    query = SubPlanta.query
    if (form.id.data):
        query = query.filter(cast(Planta.id, sqlalchemy.String).like('%' + form.id.data + '%'))
    if (form.codigo.data):
        query = query.filter(Planta.codigo.ilike(form.codigo.data))
    if (form.nome.data):
        query = query.filter(Planta.nome.ilike(form.nome.data))

    count = query.count()
    list = query.order_by(order).\
        paginate(form.page.data, settings.RECORDS_PER_PAGE, False).items

    if len(list) > 0:
        pagination = records.Pagination(form.page.data, settings.RECORDS_PER_PAGE, count)
    else:
        pagination = records.Pagination(1, settings.RECORDS_PER_PAGE, count)

    return render_template('backoffice/plantas_subplanta.html', form=form, records=list, pagination=pagination)


@mod.route('/backoffice/subplantas/create', methods=['GET', 'POST'])
@login_required
def subplantas_create():
    logger = logging.getLogger(__name__)
    logger.debug('This message should go to the log file - backoffice')

    record = None
    error = None

    form = SubPlantaForm()

    if request.method == 'POST':
        if form.validate_on_submit():
            if not User.query.filter(Planta.codigo.ilike(form.codigo.data)).first():
                record = SubPlanta()

                record.codigo = form.codigo.data
                record.nome = form.nome.data
                record.configuracao = form.configuracao.data

                db.session.add(record)

                db.session.commit()

                flash(constants.RECORDS_INSERT_SUCCESS)
                return redirect(url_for('backoffice.subplantas_edit', id=record.id))
            else:
                error = {"Message": "Já existe um elemento com o código indicado"}
        else:
            error = {"Message": constants.RECORDS_INSERT_ERROR}

    return render_template('backoffice/plantas_subplanta_edit.html', form=form, record=record, error=error)



@mod.route('/backoffice/subplantas/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def subplantas_edit(id):
    logger = logging.getLogger(__name__)
    logger.debug('This message should go to the log file - backoffice')

    record = db.session.query(SubPlanta).filter(SubPlanta.id == id).first()
    error = None


    form = SubPlantaForm()

    if request.method == 'POST':
        if form.validate_on_submit():
            try:
                record.codigo = form.codigo.data
                record.nome = form.nome.data
                record.configuracao = form.configuracao.data

                db.session.commit()

                flash(constants.RECORDS_EDIT_SUCCESS)
                return redirect(url_for('backoffice.subplantas_edit', id=record.id))
            except IntegrityError as err:
                error = {"Message": "Já existe um elemento com o código indicado"}
            except:
                error = {"Message": constants.RECORDS_EDIT_ERROR}

            db.session.rollback()
        else:
            error = {"Message": constants.RECORDS_EDIT_ERROR}
    else:
        form.codigo.data = record.codigo
        form.nome.data = record.nome
        form.configuracao.data = record.configuracao


    return render_template('backoffice/plantas_subplanta_edit.html', form=form, record=record, error=error)


@mod.route('/backoffice/subplantas/delete/<int:id>', methods=['POST'])
@login_required
def subplantas_delete(id):
    logger = logging.getLogger(__name__)
    logger.debug('This message should go to the log file - backoffice')

    record = db.session.query(SubPlanta).filter(SubPlanta.id == id).first()

    if record:
        pass
    else:
        return jsonify(Success=False, Id=id, Message=constants.RECORDS_RECORD_NOT_EXISTS)

    db.session.delete(record)
    db.session.commit()

    return jsonify(Success=True, Id=id,  Message=constants.RECORDS_DELETE_SUCCESS)


@mod.route('/backoffice/catalogos', methods=['GET', 'POST'])
@login_required
def catalogos():
    logger = logging.getLogger(__name__)
    logger.debug('This message should go to the log file - backoffice')

    form = CatalogoMetadadosSearchForm()

    mapas = db.session.query(Mapa).all()

    #Set Ordering default values
    if request.method == 'GET':
        form.page.data = 1
        form.orderField.data = 'id'
        form.sortOrder.data = 'asc'
    elif request.method == 'POST':
        if 'pesquisar' in request.form:
            form.page.data = 1

    order = getattr(getattr(CatalogoMetadados, form.orderField.data), form.sortOrder.data)()

    query = CatalogoMetadados.query
    if (form.id.data):
        query = query.filter(cast(CatalogoMetadados.id, sqlalchemy.String).like('%' + form.id.data + '%'))
    if (form.codigo.data):
        query = query.filter(CatalogoMetadados.codigo.ilike(form.codigo.data))
    if (form.titulo.data):
        query = query.filter(CatalogoMetadados.titulo.ilike(form.titulo.data))
    if (form.mapa.data):
        mapa_list = request.form.getlist('mapa')
        form.mapa.data = ','.join(mapa_list)
        query = query.outerjoin(CatalogoMetadados.mapas).filter(Mapa.codigo.in_(mapa_list))

    count = query.count()
    list = query.order_by(order).\
        paginate(form.page.data, settings.RECORDS_PER_PAGE, False).items

    if len(list) > 0:
        pagination = records.Pagination(form.page.data, settings.RECORDS_PER_PAGE, count)
    else:
        pagination = records.Pagination(1, settings.RECORDS_PER_PAGE, count)

    return render_template('backoffice/catalogos_catalogo.html', form=form, records=list, mapas=mapas, pagination=pagination)


@mod.route('/backoffice/catalogos/create', methods=['GET', 'POST'])
@login_required
def catalogos_create():
    logger = logging.getLogger(__name__)
    logger.debug('This message should go to the log file - backoffice')

    record = None
    error = None

    form = CatalogoMetadadosForm()

    if request.method == 'POST':
        if form.validate_on_submit():
            if not User.query.filter(CatalogoMetadados.codigo.ilike(form.codigo.data)).first():
                record = CatalogoMetadados()

                record.codigo = form.codigo.data
                record.titulo = form.titulo.data
                record.descricao = form.descricao.data
                record.tipo = form.tipo.data
                record.url_base = form.url_base.data
                record.url_csw = form.url_csw.data
                if "portal" in request.form:
                    CatalogoMetadados.query.update({CatalogoMetadados.portal: False})
                    record.portal = True
                else:
                    record.portal = False
                if "activo" in request.form:
                    record.activo = True
                else:
                    record.activo = False
                if "autenticacao" in request.form:
                    record.autenticacao = True
                else:
                    record.autenticacao = False
                record.username = form.username.data
                record.password = form.password.data
                if form.xslt_results_file.data:
                    record.xslt_results_file = form.xslt_results_file.data
                elif not form.xslt_results.data:
                    if form.tipo.data.lower() == 'geonetwork':
                        record.xslt_results_file = 'ListCSWResults.xsl'
                    elif form.tipo.data.lower() == 'geoportal':
                        record.xslt_results_file = 'ListGeoportalCSWResults.xsl'
                record.xslt_results = form.xslt_results.data
                if form.xslt_metadata_file.data:
                    record.xslt_metadata_file = form.xslt_metadata_file.data
                elif not form.xslt_metadata.data:
                    record.xslt_metadata_file = 'MetadataDetails.xsl'
                record.xslt_metadata = form.xslt_metadata.data

                record.idUserIns = current_user.id
                record.dataIns = datetime.datetime.now()
                db.session.add(record)

                db.session.commit()

                flash(constants.RECORDS_INSERT_SUCCESS)
                return redirect(url_for('backoffice.catalogos_edit', id=record.id))
            else:
                error = {"Message": "Já existe um catálogo com o código indicado"}
        else:
            error = {"Message": constants.RECORDS_INSERT_ERROR}

    return render_template('backoffice/catalogos_catalogo_edit.html', form=form, record=record, error=error)


@mod.route('/backoffice/catalogos/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def catalogos_edit(id):
    logger = logging.getLogger(__name__)
    logger.debug('This message should go to the log file - backoffice')

    record = db.session.query(CatalogoMetadados).filter(CatalogoMetadados.id == id).first()
    error = None

    form = CatalogoMetadadosForm()

    if request.method == 'POST':
        if form.validate_on_submit():
            try:
                record.codigo = form.codigo.data
                record.titulo = form.titulo.data
                record.descricao = form.descricao.data
                record.tipo = form.tipo.data
                record.url_base = form.url_base.data
                record.url_csw = form.url_csw.data
                if "portal" in request.form:
                    CatalogoMetadados.query.update({CatalogoMetadados.portal: False})
                    record.portal = True
                else:
                    record.portal = False
                if "activo" in request.form:
                    record.activo = True
                else:
                    record.activo = False
                if "autenticacao" in request.form:
                    record.autenticacao = True
                else:
                    record.autenticacao = False
                record.username = form.username.data
                record.password = form.password.data
                record.xslt_results_file = form.xslt_results_file.data
                record.xslt_results = form.xslt_results.data
                record.xslt_metadata_file = form.xslt_metadata_file.data
                record.xslt_metadata = form.xslt_metadata.data

                db.session.commit()

                flash(constants.RECORDS_EDIT_SUCCESS)
                return redirect(url_for('backoffice.catalogos_edit', id=record.id))
            except IntegrityError as err:
                error = {"Message": "Já existe um catálogo com o código indicado"}
            except:
                error = {"Message": constants.RECORDS_EDIT_ERROR}

            db.session.rollback()
        else:
            error = {"Message": constants.RECORDS_EDIT_ERROR}
    else:
        form.codigo.data = record.codigo
        form.titulo.data = record.titulo
        form.descricao.data = record.descricao
        form.tipo.data = record.tipo
        form.portal.data = record.portal
        form.url_base.data = record.url_base
        form.url_csw.data = record.url_csw
        form.autenticacao.data = record.autenticacao
        form.username.data = record.username
        form.password.data = record.password
        form.activo.data = record.activo
        form.xslt_results_file.data = record.xslt_results_file
        form.xslt_results.data = record.xslt_results
        form.xslt_metadata_file.data = record.xslt_metadata_file
        form.xslt_metadata.data = record.xslt_metadata

    return render_template('backoffice/catalogos_catalogo_edit.html', form=form, record=record, error=error)


@mod.route('/backoffice/catalogos/delete/<int:id>', methods=['POST'])
@login_required
def catalogos_delete(id):
    logger = logging.getLogger(__name__)
    logger.debug('This message should go to the log file - backoffice')

    record = db.session.query(CatalogoMetadados).filter(CatalogoMetadados.id == id).first()

    if not record:
        return jsonify(Success=False, Id=id, Message=constants.RECORDS_RECORD_NOT_EXISTS)

    db.session.delete(record)
    db.session.commit()

    return jsonify(Success=True, Id=id,  Message=constants.RECORDS_DELETE_SUCCESS)


@mod.route('/backoffice/settings/site', methods=['GET', 'POST'])
@login_required
def settings_site():
    logger = logging.getLogger(__name__)
    logger.debug('This message should go to the log file - backoffice')

    form = SettingsSiteSearhForm()

    #Set Ordering default values
    if request.method == 'GET':
        form.page.data = 1
        form.orderField.data = 'id'
        form.sortOrder.data = 'asc'
    elif request.method == 'POST':
        if 'pesquisar' in request.form:
            form.page.data = 1

    order = getattr(getattr(SiteSettings, form.orderField.data), form.sortOrder.data)()

    query = SiteSettings.query
    if form.id.data:
        query = query.filter(cast(SiteSettings.id, sqlalchemy.String).like('%' + form.id.data + '%'))
    if form.codigo.data:
        query = query.filter(SiteSettings.code.like(form.codigo.data))
    if form.nome.data:
        query = query.filter(SiteSettings.name.like(form.nome.data))

    count = query.count()
    list = query.order_by(order). \
        paginate(form.page.data, settings.RECORDS_PER_PAGE, False).items

    if len(list) > 0:
        pagination = records.Pagination(form.page.data, settings.RECORDS_PER_PAGE, count)
    else:
        pagination = records.Pagination(1, settings.RECORDS_PER_PAGE, count)

    return render_template('backoffice/settings_site.html', form=form, records=list, pagination=pagination)


@mod.route('/backoffice/settings/site/create', methods=['GET', 'POST'])
@login_required
def settings_site_create():
    logger = logging.getLogger(__name__)
    logger.debug('This message should go to the log file - backoffice')

    record = None
    error = None

    form = SettingsSiteForm()

    if request.method == 'POST':
        if form.validate_on_submit():
            record = SiteSettings()

            record.code = form.code.data
            record.name = form.name.data
            record.notes = form.notes.data
            record.setting_value = form.setting_value.data
            record.read_only = False
            record.active = True

            db.session.add(record)

            db.session.commit()

            flash(constants.RECORDS_INSERT_SUCCESS)
            return redirect(url_for('backoffice.settings_site_edit', id=record.id))
        else:
            error = {"Message": constants.RECORDS_INSERT_ERROR}

    return render_template('backoffice/settings_site_edit.html', form=form, record=record, error=error)


@mod.route('/backoffice/settings/site/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def settings_site_edit(id):
    logger = logging.getLogger(__name__)
    logger.debug('This message should go to the log file - backoffice')

    record = db.session.query(SiteSettings).filter(SiteSettings.id == id).first()
    error = None

    form = SettingsSiteForm()

    if request.method == 'POST':
        if form.validate_on_submit():
            record.code = form.code.data
            record.name = form.name.data
            record.notes = form.notes.data
            record.setting_value = form.setting_value.data # request.form['setting_value']

            db.session.commit()

            flash(constants.RECORDS_EDIT_SUCCESS)
            return redirect(url_for('backoffice.settings_site_edit', id=record.id))
        else:
            error = {"Message": constants.RECORDS_EDIT_ERROR}
    else:
        form.code.data = record.code
        form.name.data = record.name
        form.notes.data = record.notes
        form.setting_value.data = record.setting_value

    return render_template('backoffice/settings_site_edit.html', form=form, record=record, error=error)


@mod.route('/backoffice/settings/site/delete/<int:id>', methods=['POST'])
@login_required
def settings_site_delete(id):
    logger = logging.getLogger(__name__)
    logger.debug('This message should go to the log file - backoffice')

    record = db.session.query(SiteSettings).filter(SiteSettings.id == id).first()

    if not record:
        return jsonify(Success=False, Id=id, Message=constants.RECORDS_RECORD_NOT_EXISTS)

    db.session.delete(record)
    db.session.commit()

    return jsonify(Success=True, Id=id,  Message=constants.RECORDS_DELETE_SUCCESS)


@mod.route('/backoffice/audit/<string:tipo>', methods=['GET', 'POST'])
@login_required
def audit(tipo):
    logger = logging.getLogger(__name__)
    logger.debug('This message should go to the log file - backoffice')

    form = AuditLogSearchForm()

    title = ''

    mapas = db.session.query(Mapa).all()

    #Set Ordering default values
    if request.method == 'GET':
        form.page.data = 1
        form.orderField.data = 'id'
        form.sortOrder.data = 'desc'
    elif request.method == 'POST':
        if 'pesquisar' in request.form or form.page.data is None:
            form.page.data = 1

    order = getattr(getattr(AuditLog, form.orderField.data), form.sortOrder.data)()

    query = AuditLog.query
    #query = db.session.query(AuditLog, AuditOperacao, Mapa).\
    #    outerjoin(AuditOperacao, AuditLog.operacao_id == AuditOperacao.id).\
    #    outerjoin(Mapa, AuditLog.id_mapa == Mapa.id)

    query = query.outerjoin(AuditLog.operacao)
    #query = query.outerjoin(AuditOperacao, AuditLog.operacao_id == AuditOperacao.id)
    if tipo.lower() == 'all':
        title = 'Total'
    else:
        op = db.session.query(AuditOperacao).filter(AuditOperacao.codigo.ilike(tipo)).first()
        if op is not None:
            title = op.nome
        query = query.filter(AuditOperacao.codigo.ilike(tipo))

    if (form.id.data):
        query = query.filter(cast(AuditLog.id, sqlalchemy.String).like('%' + form.id.data + '%'))

    if (form.data_ref_inicio.data and form.data_ref_fim.data):
        query = query.filter(AuditLog.data_ref >= form.data_ref_inicio.data). \
            filter(AuditLog.data_ref <= form.data_ref_fim.data + datetime.timedelta(days=1))
    elif form.data_ref_inicio.data:
        query = query.filter(AuditLog.data_ref >= form.data_ref_inicio.data)
    elif form.data_ref_fim.data:
        query =  query.filter(AuditLog.data_ref <= form.data_ref_fim.data + datetime.timedelta(days=1))

    if (form.mapa.data):
        mapa_list = request.form.getlist('mapa')
        form.mapa.data = ','.join(mapa_list)
        query = query.outerjoin(AuditLog.mapa).filter(Mapa.codigo.in_(mapa_list))
        #query = query.outerjoin(Mapa, AuditLog.id_mapa == Mapa.id).filter(Mapa.codigo.in_(mapa_list))
        #query = query.filter(Mapa.codigo.in_(mapa_list))
    if (form.operacao.data):
        operacao_list = request.form.getlist('operacao')
        form.operacao.data = ','.join(operacao_list)
        #query = query.outerjoin(AuditLog.operacao).filter(AuditOperacao.codigo.in_(operacao_list))
        query = query.filter(AuditOperacao.codigo.in_(operacao_list))

    count = query.count()
    list = query.order_by(order).\
        paginate(form.page.data, settings.RECORDS_PER_PAGE, False).items

    if len(list) > 0:
        pagination = records.Pagination(form.page.data, settings.RECORDS_PER_PAGE, count)
    else:
        pagination = records.Pagination(1, settings.RECORDS_PER_PAGE, count)

    return render_template('backoffice/audit.html', title=title, tipo=tipo.lower(), form=form, records=list, mapas=mapas, operacoes=auditoria.EnumOperacaoAuditoria, pagination=pagination)


@mod.route('/backoffice/mensagens', methods=['GET', 'POST'])
@login_required
def mensagens():
    logger = logging.getLogger(__name__)
    logger.debug('This message should go to the log file - backoffice')

    form = ContactoMensagemSearchForm()

    mapas = db.session.query(Mapa).all()

    #Set Ordering default values
    if request.method == 'GET':
        form.page.data = 1
        form.orderField.data = 'id'
        form.sortOrder.data = 'desc'
    elif request.method == 'POST':
        if 'pesquisar' in request.form:
            form.page.data = 1

    order = getattr(getattr(ContactoMensagem, form.orderField.data), form.sortOrder.data)()

    #query = db.session.query(ContactoMensagem, Mapa).outerjoin(Mapa, ContactoMensagem.mapa_id == Mapa.id)

    query = BaseQuery([ContactoMensagem, Mapa, User], db.session())\
        .outerjoin(Mapa, ContactoMensagem.mapa_id == Mapa.id)\
        .outerjoin(User, ContactoMensagem.user_id == User.id)

    if (form.id.data):
        query = query.filter(cast(ContactoMensagem.id, sqlalchemy.String).like('%' + form.id.data + '%'))

    if (form.data_inicio.data and form.data_fim.data):
        query = query.filter(ContactoMensagem.data_mensagem >= form.data_inicio.data). \
            filter(ContactoMensagem.data_mensagem <= form.data_fim.data + datetime.timedelta(days=1))
    elif form.data_inicio.data:
        query = query.filter(ContactoMensagem.data_mensagem >= form.data_inicio.data)
    elif form.data_fim.data:
        query =  query.filter(ContactoMensagem.data_mensagem <= form.data_fim.data + datetime.timedelta(days=1))

    if (form.mapa.data):
        mapa_list = request.form.getlist('mapa')
        form.mapa.data = ','.join(mapa_list)
        query = query.filter(Mapa.codigo.in_(mapa_list))

    if (form.user.data):
        query = query.filter(or_(ContactoMensagem.nome.ilike(form.user.data), ContactoMensagem.email.ilike(form.user.data),\
                                 User.username.ilike(form.user.data)))

    if form.estado.data == '1':
        query = query.filter(or_(ContactoMensagem.checked is None, ContactoMensagem.checked == False))
        query = query.filter(or_(ContactoMensagem.closed is None, ContactoMensagem.closed == False))
    elif form.estado.data == '2':
        query = query.filter(or_(ContactoMensagem.checked == True))
        query = query.filter(or_(ContactoMensagem.closed is None, ContactoMensagem.closed == False))
    elif form.estado.data == '3':
        query = query.filter(or_(ContactoMensagem.closed == True))

    '''
    query = query.outerjoin(AuditLog.operacao)
    if tipo.lower() == 'all':
        title = 'Total'
    else:
        op = db.session.query(AuditOperacao).filter(AuditOperacao.codigo.ilike(tipo)).first()
        if op is not None:
            title = op.nome
        query = query.filter(AuditOperacao.codigo.ilike(tipo))

    if (form.id.data):
        query = query.filter(cast(AuditLog.id, sqlalchemy.String).like('%' + form.id.data + '%'))

    if (form.data_ref_inicio.data and form.data_ref_fim.data):
        query = query.filter(AuditLog.data_ref >= form.data_ref_inicio.data). \
            filter(AuditLog.data_ref <= form.data_ref_fim.data + datetime.timedelta(days=1))
    elif form.data_ref_inicio.data:
        query = query.filter(AuditLog.data_ref >= form.data_ref_inicio.data)
    elif form.data_ref_fim.data:
        query =  query.filter(AuditLog.data_ref <= form.data_ref_fim.data + datetime.timedelta(days=1))

    if (form.mapa.data):
        mapa_list = request.form.getlist('mapa')
        form.mapa.data = ','.join(mapa_list)
        query = query.outerjoin(AuditLog.mapa).filter(Mapa.codigo.in_(mapa_list))
    if (form.operacao.data):
        operacao_list = request.form.getlist('operacao')
        form.operacao.data = ','.join(operacao_list)
        query = query.outerjoin(AuditLog.operacao).filter(AuditOperacao.codigo.in_(operacao_list))
    '''

    count = query.count()
    list = query.order_by(order).\
        paginate(form.page.data, settings.RECORDS_PER_PAGE, False).items

    if len(list) > 0:
        pagination = records.Pagination(form.page.data, settings.RECORDS_PER_PAGE, count)
    else:
        pagination = records.Pagination(1, settings.RECORDS_PER_PAGE, count)

    return render_template('backoffice/mensagens_mensagem.html', form=form, records=list, mapas=mapas, pagination=pagination)

@mod.route('/backoffice/mensagens/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def mensagens_edit(id):
    logger = logging.getLogger(__name__)
    logger.debug('This message should go to the log file - backoffice')

    record = db.session.query(ContactoMensagem).filter(ContactoMensagem.id == id).first()
    mapa = None
    error = None

    if not record:
        record = ContactoMensagem()
        flash(constants.RECORDS_RECORD_NOT_EXISTS, 'danger')
        return render_template('backoffice/mensagens_mensagem_edit.html', record=record, error=error)

    if record.mapa_id:
        mapa = db.session.query(Mapa).filter(Mapa.id == record.mapa_id).first()

    if request.method == 'POST':
        if 'action' in request.form:
            try:
                msg = ''

                if request.form['action'] == 'check':
                    record.checked = True
                    record.checked_date = datetime.datetime.now()
                    record.observacoes == request.form['observacoes']
                    msg = constants.RECORDS_CONTACT_MSG_CHECKED_SUCCESS
                elif request.form['action'] == 'close':
                    if not record.checked:
                        record.checked = True
                        record.checked_date = datetime.datetime.now()
                    record.closed = True
                    record.closed_date = datetime.datetime.now()
                    record.observacoes == request.form['observacoes']
                    msg = constants.RECORDS_CONTACT_MSG_CLOSED_SUCCESS
                elif request.form['action'] == 'reopen':
                    record.closed = False
                    record.closed_date = None
                    record.observacoes == request.form['observacoes']
                    msg = constants.RECORDS_CONTACT_MSG_REOPENED_SUCCESS
                elif request.form['action'] == 'save':
                    record.observacoes = request.form['observacoes']
                    msg = constants.RECORDS_EDIT_SUCCESS

                db.session.commit()

                flash(msg, 'success')
                return redirect(url_for('backoffice.mensagens_edit', id=record.id))
            except:
                error = {"Message": constants.RECORDS_EDIT_ERROR}

                db.session.rollback()

    return render_template('backoffice/mensagens_mensagem_edit.html', record=record, mapa=mapa, error=error)


@mod.route('/backoffice/settings/view', methods=['GET'])
def settings_view():
    logger = logging.getLogger(__name__)
    logger.debug('This message should go to the log file - backoffice')

    settings_dir = []
    settings_dir.append({'name': 'VERSION', 'value': settings.APP_VERSION})
    settings_dir.append({'name': 'root_path', 'value': current_app.root_path})
    settings_dir.append({'name': 'instance_path', 'value': current_app.instance_path})

    settings_config = []
    for k in current_app.config:
        if k != 'SECRET_KEY' and k != 'SECURITY_PASSWORD_SALT' and k != 'SQLALCHEMY_DATABASE_URI':
            settings_config.append({'name': k, 'value': current_app.config.get(k)})

    settings_app = []
    settings_app.append({'name': 'RECORDS_PER_PAGE', 'value': settings.RECORDS_PER_PAGE})
    settings_app.append({'name': 'LOCAL_PATH', 'value': settings.LOCAL_PATH})
    settings_app.append({'name': 'APP_SITE_ROOT', 'value': settings.APP_SITE_ROOT})
    settings_app.append({'name': 'APP_STATIC', 'value': settings.APP_STATIC})
    settings_app.append({'name': 'APP_RESOURCES', 'value': settings.APP_RESOURCES})
    settings_app.append({'name': 'APP_TMP_DIR', 'value': settings.APP_TMP_DIR})
    settings_app.append({'name': 'ORGANIZATION_NAME', 'value': settings.ORGANIZATION_NAME})
    settings_app.append({'name': 'MAP_TEMPLATES', 'value': settings.MAP_TEMPLATES})
    settings_app.append({'name': 'LAYOUT_MAP_SIZES_FOR_PREVIEW', 'value': settings.LAYOUT_MAP_SIZES_FOR_PREVIEW})

    settings_ldap = None
    if current_app.config.get('LDAP_CONFIG'):
        settings_ldap = current_app.config.get('LDAP_CONFIG')

    return render_template('backoffice/settings_view.html', settings_dir=settings_dir, settings_config=settings_config,
                           settings_app=settings_app, settings_ldap=settings_ldap)


@mod.route('/backoffice/tree_view', methods=['GET'])
def wktapp_objects_tree_view():

    sql = 'select * from portal.get_maps_groups_layouts_json()'
    json_maps_groups_layouts=db.engine.execute(sql).first()[0]
    sql = 'select * from portal.get_groups_layouts_json()'
    json_groups_layouts = db.engine.execute(sql).first()[0]
    sql = 'select * from portal.get_layouts_json()'
    json_layouts = db.engine.execute(sql).first()[0]

    return render_template('backoffice/objects_tree_view.html',object_tree_layouts=json_layouts,
        object_tree_groups_layouts=json_groups_layouts,object_tree_maps_groups_layouts=json_maps_groups_layouts)


@mod.route('/backoffice/version', methods=['GET'])
def wktapp_version():
    return settings.APP_VERSION