import json
from flask_restx import fields, Model
from app.api.restx import api2 as api

from ..serializers import pagination, ConfigJson, viewer_simple_api_model, \
    user_simple_api_model
    #print_layout_api_model, print_simple_api_model, print_api_model


print_layout_api_model = api.model('Print Layout Model', {
    'id': fields.Integer(readOnly=True, description='Identifier'),
    'orientation': fields.String(required=True, attribute='orientacao', description='Name'),
    'format': fields.String(required=True, attribute='formato', description='Name'),
    'config': fields.String(required=False, attribute='configuracao', description='Layout Configuration')
})

print_group_simple_api_model = api.model('Print Group Simple Model', {
    'id': fields.Integer(readOnly=True, description='Identifier'),
    'code': fields.String(required=True, attribute='codigo', description='Code'),
    'name': fields.String(required=True, attribute='nome', description='Name'),
    'title': fields.String(required=False, attribute='titulo', description='Title'),
    'description': fields.String(required=False, attribute='descricao', description='Description'),
    'is_active': fields.Boolean(readOnly=False, attribute='activo', description='Active'),
})

print_simple_api_model = api.model('Print Simple Model', {
    'id': fields.Integer(readOnly=True, description='Identifier'),
    'code': fields.String(required=True, attribute='codigo', description='Code'),
    'name': fields.String(required=True, attribute='nome', description='Name'),
    'title': fields.String(required=False, attribute='titulo', description='Title'),
    'description': fields.String(required=False, attribute='descricao', description='Description'),
    'is_active': fields.Boolean(readOnly=False, attribute='activo', description='Active')
})

print_api_model = api.model('Print Model', {
    'id': fields.Integer(readOnly=True, description='Identifier'),
    'code': fields.String(required=True, attribute='codigo', description='Code'),
    'name': fields.String(required=True, attribute='nome', description='Name'),
    'title': fields.String(required=False, attribute='titulo', description='Title'),
    'description': fields.String(required=False, attribute='descricao', description='Description'),
    'is_active': fields.Boolean(readOnly=False, attribute='activo', description='Active'),
    'scale': fields.Integer(readOnly=False, attribute='escala', description='Scale'),
    'srid': fields.Integer(readOnly=False, attribute='srid', description='SRID'),
    'format': fields.String(readOnly=False, attribute='formato', description='Format'),
    'orientation': fields.String(readOnly=False, attribute='orientacao', description='Orientation'),
    'identification': fields.Boolean(readOnly=False, attribute='identificacao', description='Identification'),
    'identification_fields': ConfigJson(readOnly=False, attribute='identificacaoCampos',
                                        description='Fields Configuration'),
    'form_fields': ConfigJson(readOnly=False, attribute='formFields',
                                        description='Form Fields Configuration'),
    'location_marking': fields.Boolean(readOnly=False, attribute='marcacaoLocal', description='Location Marking'),
    'draw_location': fields.Boolean(readOnly=False, attribute='desenharLocal', description='Draw Location'),
    'free_printing': fields.Boolean(readOnly=False, attribute='emissaoLivre', description='Free Printing'),
    'add_title': fields.Boolean(readOnly=False, attribute='tituloEmissao', description='Add title'),
    'show_author': fields.Boolean(readOnly=False, attribute='autorEmissao', description='Show Author'),
    'payment_reference': fields.Boolean(readOnly=False, attribute='guiaPagamento', description='Payment Reference'),
    'print_purpose': fields.Boolean(readOnly=False, attribute='finalidadeEmissao', description='Print purpose'),
    'restrict_scales': fields.Boolean(readOnly=False, attribute='escalasRestritas', description='Restrict Scales'),
    'restrict_scales_list': fields.String(readOnly=False, attribute='escalasRestritasLista',
                                         description='Restricted Scales List'),
    'free_scale': fields.Boolean(readOnly=False, attribute='escalaLivre', description='Use Free Scale'),
    'map_scale': fields.Boolean(readOnly=False, attribute='escalaMapa', description='Use Map Scale'),
    'multi_geom':  fields.Boolean(readOnly=False, attribute='multiGeom', description='Multi geometries'),
    'config_json': ConfigJson(readOnly=False, attribute='configuracao', description='Configuration'),
    'owner_id': fields.Integer(required=False, description='Owner Id'),
    'owner': fields.Nested(user_simple_api_model, skip_none=True),
    'geom_filter': fields.String(required=False, attribute='geometry_wkt', description='WKT da geometria'),
    'geom_filter_srid': fields.Integer(required=False, attribute='geometry_srid', description='SRID da geometria'),
    'tolerance_filter': fields.Integer(required=False, attribute='tolerancia', description='Spatial filter tolerance'),
    'layouts': fields.List(fields.Nested(print_layout_api_model)),
    'groups': fields.List(fields.Nested(print_group_simple_api_model), attribute='tipos_plantas', description='Print Groups'),
    'viewers': fields.List(fields.Nested(viewer_simple_api_model), attribute='viewers', description='Viewers')
})

page_print = api.inherit('Print pages', pagination, {
    'items': fields.List(fields.Nested(print_api_model))
})

print_group_api_model = api.model('Print Model', {
    'id': fields.Integer(readOnly=True, description='Identifier'),
    'code': fields.String(required=True, attribute='codigo', description='Code'),
    'title': fields.String(required=False, attribute='titulo', description='Title'),
    'description': fields.String(required=False, attribute='descricao', description='Description'),
    'is_active': fields.Boolean(readOnly=False, attribute='activo', description='Active'),
    'scale': fields.Integer(readOnly=False, attribute='escala', description='Scale'),
    'identification': fields.Boolean(readOnly=False, attribute='identificacaoRequerente', description='Identification'),
    'identification_fields': ConfigJson(readOnly=False, attribute='identificacaoCampos',
                                        description='Fields Configuration'),
    'form_fields': ConfigJson(readOnly=False, attribute='formFields',
                                        description='Form Fields Configuration'),
    'location_marking': fields.Boolean(readOnly=False, attribute='marcacaoLocal', description='Location Marking'),
    'show_author': fields.Boolean(readOnly=False, attribute='autorEmissao', description='Show Author'),
    'payment_reference': fields.Boolean(readOnly=False, attribute='guiaPagamento', description='Payment Reference'),
    'print_purpose': fields.Boolean(readOnly=False, attribute='finalidadeEmissao', description='Print purpose'),
    'restrict_scales': fields.Boolean(readOnly=False, attribute='escalasRestritas', description='Restrict Scales'),
    'restrict_scales_list': fields.String(readOnly=False, attribute='escalasRestritasLista',
                                          description='Restricted Scales List'),
    'free_scale': fields.Boolean(readOnly=False, attribute='escalaLivre', description='Use Free Scale'),
    'map_scale': fields.Boolean(readOnly=False, attribute='escalaMapa', description='Use Map Scale'),
    'multi_geom':  fields.Boolean(readOnly=False, attribute='multiGeom', description='Multi geometries'),
    'config_json': ConfigJson(readOnly=False, attribute='configuracao', description='Configuration'),

    #group options
    'select_prints': fields.Boolean(readOnly=False, attribute='seleccaoPlantas', description='Select prints'),
    'group_prints': fields.Boolean(readOnly=False, attribute='agruparPlantas', description='Group prints'),
    'show_all_prints': fields.Boolean(readOnly=False, attribute='showAll', description='Show all prints'),
    'geom_filter': fields.String(required=False, attribute='geometry_wkt', description='WKT da geometria'),
    'geom_filter_srid': fields.Integer(required=False, attribute='geometry_srid', description='SRID da geometria'),
    'tolerance_filter': fields.Integer(required=False, attribute='tolerancia', description='Spatial filter tolerance'),

    'layouts': fields.List(fields.Nested(print_layout_api_model)),

    'prints': fields.List(fields.Nested(print_api_model), attribute='plantas', description='Child Prints'),

    'viewers': fields.List(fields.Nested(viewer_simple_api_model), attribute='viewers', description='Viewers')
})
'''
print_group_child_api_model = api.model('Child Print Group Model', {
    'group': fields.Nested(print_group_api_model, attribute='tipo_planta_child'),
    'order': fields.Integer(required=False, attribute='ordem', description='Child order'),
})
print_group_api_model['groups'] = fields.List(fields.Nested(print_group_child_api_model), attribute='tipo_planta_child_assoc')
'''
print_group_child_api_model = api.model('Child Print Group Model', {
    'id': fields.Integer(readOnly=True, attribute='tipo_planta_child.id', description='Identifier'),
    'code': fields.String(required=True, attribute='tipo_planta_child.codigo', description='Code'),
    'title': fields.String(required=False, attribute='tipo_planta_child.titulo', description='Title'),
    'description': fields.String(required=False, attribute='tipo_planta_child.descricao', description='Description'),
    'is_active': fields.Boolean(readOnly=False, attribute='tipo_planta_child.activo', description='Active'),
    'order': fields.Integer(required=False, attribute='ordem', description='Child order'),
})
print_group_api_model['groups'] = fields.List(fields.Nested(print_group_child_api_model), attribute='tipo_planta_child_assoc')


page_print_group = api.inherit('Print group pages', pagination, {
    'items': fields.List(fields.Nested(print_group_api_model))
})


print_element_api_model = api.model('Print Model', {
    'id': fields.Integer(readOnly=True, description='Identifier'),
    'code': fields.String(required=True, attribute='codigo', description='Code'),
    'name': fields.String(required=True, attribute='nome', description='Name'),
    'title': fields.String(required=False, attribute='titulo', description='Title'),
    'config': fields.String(required=False, attribute='configuracao', description='Description')
})

page_print_element = api.inherit('Print element pages', pagination, {
    'items': fields.List(fields.Nested(print_element_api_model))
})
