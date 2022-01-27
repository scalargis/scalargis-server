from flask_wtf import FlaskForm as Form
from wtforms import StringField, IntegerField, DecimalField


class TransformForm(Form):
    code = StringField()
    srid = IntegerField('Sistema de coordenadas do ponto')
    x = DecimalField('X')
    z = DecimalField('Y')
    y = DecimalField('Z')
    mapSrid = IntegerField('Sistema de Coordenadas do mapa')


class IntersectPDMForm(Form):
    geomEWKT = StringField()
    srid = IntegerField('Sistema de coordenadas do plano')
    mapId = IntegerField()


class IntersectCFTForm(Form):
    geomEWKT = StringField()
    srid = IntegerField('Sistema de coordenadas da geometria')
    mapId = IntegerField()
    buffer = IntegerField()
    config = StringField()
