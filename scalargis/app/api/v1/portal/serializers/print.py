from flask_restx import fields
from app.api.restx import api as api

from ..serializers import pagination, ConfigJson, viewer_simple_api_model, user_simple_api_model


print_layout_api_model = api.model('Print Layout Model', {
    'id': fields.Integer(readOnly=True, description='Identifier'),
    'orientation': fields.String(required=True, description='Name'),
    'format': fields.String(required=True, description='Name'),
    'config': fields.String(required=False, description='Layout Configuration')
})

print_group_simple_api_model = api.model('Print Group Simple Model', {
    'id': fields.Integer(readOnly=True, description='Identifier'),
    'code': fields.String(required=True, description='Code'),
    'name': fields.String(required=True, description='Name'),
    'title': fields.String(required=False, description='Title'),
    'description': fields.String(required=False, description='Description'),
    'is_active': fields.Boolean(readOnly=False, description='Active'),
})

print_simple_api_model = api.model('Print Simple Model', {
    'id': fields.Integer(readOnly=True, description='Identifier'),
    'code': fields.String(required=True, description='Code'),
    'name': fields.String(required=True, description='Name'),
    'title': fields.String(required=False, description='Title'),
    'description': fields.String(required=False, description='Description'),
    'is_active': fields.Boolean(readOnly=False, description='Active')
})

print_api_model = api.model('Print Model', {
    'id': fields.Integer(readOnly=True, description='Identifier'),
    'code': fields.String(required=True, description='Code'),
    'name': fields.String(required=True, description='Name'),
    'title': fields.String(required=False, description='Title'),
    'description': fields.String(required=False, description='Description'),
    'is_active': fields.Boolean(readOnly=False, description='Active'),
    'scale': fields.Integer(readOnly=False, description='Scale'),
    'srid': fields.Integer(readOnly=False, description='SRID'),
    'format': fields.String(readOnly=False, description='Format'),
    'orientation': fields.String(readOnly=False, description='Orientation'),
    'identification': fields.Boolean(readOnly=False, description='Identification'),
    'identification_fields': ConfigJson(readOnly=False, description='Fields Configuration'),
    'form_fields': ConfigJson(readOnly=False, description='Form Fields Configuration'),
    'allow_drawing': fields.Boolean(readOnly=False, description='Allow Drawing'),
    'location_marking': fields.Boolean(readOnly=False, description='Location Marking'),
    'draw_location': fields.Boolean(readOnly=False, description='Draw Location'),
    'free_printing': fields.Boolean(readOnly=False, description='Free Printing'),
    'add_title': fields.Boolean(readOnly=False, description='Add title'),
    'show_author': fields.Boolean(readOnly=False, description='Show Author'),
    'payment_reference': fields.Boolean(readOnly=False, description='Payment Reference'),
    'print_purpose': fields.Boolean(readOnly=False, description='Print purpose'),
    'restrict_scales': fields.Boolean(readOnly=False, description='Restrict Scales'),
    'restrict_scales_list': fields.String(readOnly=False, description='Restricted Scales List'),
    'free_scale': fields.Boolean(readOnly=False, description='Use Free Scale'),
    'map_scale': fields.Boolean(readOnly=False, description='Use Map Scale'),
    'multi_geom':  fields.Boolean(readOnly=False, description='Multi geometries'),
    'config_json': ConfigJson(readOnly=False, description='Configuration'),
    'owner_id': fields.Integer(required=False, description='Owner Id'),
    'owner': fields.Nested(user_simple_api_model, skip_none=True),
    'geom_filter': fields.String(required=False, attribute='geometry_wkt', description='WKT da geometria'),
    'geom_filter_srid': fields.Integer(required=False, attribute='geometry_srid', description='SRID da geometria'),
    'tolerance_filter': fields.Integer(required=False, description='Spatial filter tolerance'),
    'layouts': fields.List(fields.Nested(print_layout_api_model)),
    'groups': fields.List(fields.Nested(print_group_simple_api_model), attribute='print_groups', description='Print Groups'),
    'viewers': fields.List(fields.Nested(viewer_simple_api_model), attribute='viewers', description='Viewers')
})

page_print = api.inherit('Print pages', pagination, {
    'items': fields.List(fields.Nested(print_api_model))
})

print_group_api_model = api.model('Print Model', {
    'id': fields.Integer(readOnly=True, description='Identifier'),
    'code': fields.String(required=True, description='Code'),
    'title': fields.String(required=False, description='Title'),
    'description': fields.String(required=False, description='Description'),
    'is_active': fields.Boolean(readOnly=False, description='Active'),
    'scale': fields.Integer(readOnly=False, description='Scale'),
    'identification': fields.Boolean(readOnly=False, description='Identification'),
    'identification_fields': ConfigJson(readOnly=False, description='Fields Configuration'),
    'form_fields': ConfigJson(readOnly=False, description='Form Fields Configuration'),
    'allow_drawing': fields.Boolean(readOnly=False, description='Allow Drawing'),
    'location_marking': fields.Boolean(readOnly=False, description='Location Marking'),
    'draw_location': fields.Boolean(readOnly=False, description='Draw Location'),
    'show_author': fields.Boolean(readOnly=False, description='Show Author'),
    'payment_reference': fields.Boolean(readOnly=False, description='Payment Reference'),
    'print_purpose': fields.Boolean(readOnly=False, description='Print purpose'),
    'restrict_scales': fields.Boolean(readOnly=False, description='Restrict Scales'),
    'restrict_scales_list': fields.String(readOnly=False, description='Restricted Scales List'),
    'free_scale': fields.Boolean(readOnly=False, description='Use Free Scale'),
    'map_scale': fields.Boolean(readOnly=False, description='Use Map Scale'),
    'multi_geom':  fields.Boolean(readOnly=False, description='Multi geometries'),

    #group options
    'select_prints': fields.Boolean(readOnly=False, description='Select prints'),
    'group_prints': fields.Boolean(readOnly=False, description='Group prints'),
    'show_all_prints': fields.Boolean(readOnly=False, description='Show all prints'),
    'geom_filter': fields.String(required=False, attribute='geometry_wkt', description='WKT da geometria'),
    'geom_filter_srid': fields.Integer(required=False, attribute='geometry_srid', description='SRID da geometria'),
    'tolerance_filter': fields.Integer(required=False, description='Spatial filter tolerance'),

    'layouts': fields.List(fields.Nested(print_layout_api_model)),

    #'prints': fields.List(fields.Nested(print_api_model), attribute='print_assoc', description='Child Prints'),

    'viewers': fields.List(fields.Nested(viewer_simple_api_model), attribute='viewers', description='Viewers')
})

print_group_child_api_model = api.model('Child Print Group Model', {
    'id': fields.Integer(readOnly=True, attribute='print_group_child.id', description='Identifier'),
    'code': fields.String(required=True, attribute='print_group_child.code', description='Code'),
    'title': fields.String(required=False, attribute='print_group_child.title', description='Title'),
    'description': fields.String(required=False, attribute='print_group_child.description', description='Description'),
    'is_active': fields.Boolean(readOnly=False, attribute='print_group_child.is_active', description='Active'),
    'order': fields.Integer(required=False, attribute='order', description='Child order'),
})
print_group_api_model['groups'] = fields.List(fields.Nested(print_group_child_api_model), attribute='print_group_child_assoc')

print_child_api_model = api.model('Child Print Model', {
    'id': fields.Integer(readOnly=True, attribute='print.id', description='Identifier'),
    'code': fields.String(required=True, attribute='print.code', description='Code'),
    'title': fields.String(required=False, attribute='print.title', description='Title'),
    'description': fields.String(required=False, attribute='print.description', description='Description'),
    'is_active': fields.Boolean(readOnly=False, attribute='is_active', description='Active'),
    'order': fields.Integer(required=False, attribute='order', description='Child order'),
})
print_group_api_model['prints'] = fields.List(fields.Nested(print_child_api_model), attribute='print_assoc')



page_print_group = api.inherit('Print group pages', pagination, {
    'items': fields.List(fields.Nested(print_group_api_model))
})


print_element_api_model = api.model('Print Model', {
    'id': fields.Integer(readOnly=True, description='Identifier'),
    'code': fields.String(required=True, description='Code'),
    'name': fields.String(required=True, description='Name'),
    'config': fields.String(required=False, description='Configuration')
})

page_print_element = api.inherit('Print element pages', pagination, {
    'items': fields.List(fields.Nested(print_element_api_model))
})
