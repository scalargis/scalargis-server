import json
from flask import Blueprint, render_template, Response, request
from sqlalchemy import sql
from wtforms import StringField, Form
from app.database import db
from app.utils import http

mod = Blueprint('search',  __name__, template_folder='templates', static_folder='static')


class SearchForm(Form):
    autocomplete = StringField('autocomplete',id='autocomplete')


class SearchResult(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    nome = db.Column(db.String(255))
    extra_info = db.Column(db.Text())
    tipo = db.Column(db.Text())
    geom_json = db.Column(db.Text())

    def serialize(self):
        return dict(id=self.id,
                    first_name=self.nome)


@mod.route('/autocomplete', methods=['GET'])
@http.crossdomain(origin='*')
def autocomplete():
    search = request.args.get('term')

    #qsql = sql.text("select * from  portal.get_fullsearch(:filter)")
    #data = wktapp.db.engine.execute(qsql, filter='sd').fetchall()

    #result = [d._row for d in data]
    #return jsonify(result=result)

    data = db.session.query(SearchResult).from_statement(
        sql.text("select * from  portal.get_gazetteer_fullsearch(:filter,20,0.19)")). \
        params(filter=search).all()

    #result = [d.serialize() for d in data]
    # return jsonify(result=result)

    result = [{"id": d.id, "nome": d.nome, "extra_info": d.extra_info, "tipo": d.tipo, "geom_json": d.geom_json} for d in data]
    return Response(json.dumps(result), mimetype='application/json')


@mod.route('/search', methods=['GET','POST'])
def search():
    form = SearchForm(request.form)
    return render_template("search/search.html",form=form)
