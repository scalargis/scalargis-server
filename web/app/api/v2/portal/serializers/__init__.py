import json
from flask_restx import fields, Model
from app.api.restx import api2 as api



class ConfigJson(fields.Raw):
    def format(self, value):
        if isinstance(value, dict):
            return value
        else:
            if value is not None and value != '':
                return json.loads(value)
            else:
                return None


pagination = api.model('A page of results', {
    'page': fields.Integer(description='Number of this page of results'),
    'pages': fields.Integer(description='Total number of pages of results'),
    'per_page': fields.Integer(description='Number of items per page of results'),
    'total': fields.Integer(description='Total number of results'),
})

#--------------------------------------------------------------------------

role_api_model = api.model('Role Mode', {
    'id': fields.Integer(required=True, description='Id'),
    'name': fields.String(required=True, description='Name'),
    'description': fields.String(required=True, description='Name'),
    'read_only': fields.Boolean(required=False, description='Read Only')
})

page_roles = api.inherit('Pages Roles Table', pagination, {
    'items': fields.List(fields.Nested(role_api_model))
})

user_role_api_model = api.model('User Role Model', {
    'id': fields.Integer,
    'name': fields.String()
})

group_role_api_model = api.model('Group Role Model', {
    'id': fields.Integer,
    'name': fields.String()
})

viewer_role_api_model = api.model('Viewer Role Model', {
    'id': fields.Integer,
    'name': fields.String()
})

#---

user_simple_api_model = api.model('User Model', {
    'id': fields.Integer(required=True, description='Id'),
    'email': fields.String(required=True, description='Email'),
    'username': fields.String(required=True, description='Username'),
    'name': fields.String(required=True, description='Username'),
    'active': fields.Boolean(required=False, description='Active')
})

group_api_model = api.model('Group Mode', {
    'id': fields.Integer(required=True, description='Id'),
    'name': fields.String(required=True, description='Name'),
    'description': fields.String(required=True, description='Name'),
    'read_only': fields.Boolean(required=False, description='Read Only')
})
group_api_model['roles'] = fields.List(fields.Nested(group_role_api_model))
group_api_model['users'] = fields.List(fields.Nested(user_simple_api_model))

page_groups = api.inherit('Pages Groups Table', pagination, {
    'items': fields.List(fields.Nested(group_api_model))
})

user_group_api_model = api.model('User Group Model', {
    'id': fields.Integer,
    'name': fields.String()
})

#---

user_api_model = api.model('User Model', {
    'id': fields.Integer(required=True, description='Id'),
    'email': fields.String(required=True, description='Email'),
    'username': fields.String(required=True, description='Username'),
    'name': fields.String(required=True, description='Name'),
    'first_name':  fields.String(required=False, description='First Name'),
    'last_name':  fields.String(required=False, description='First Name'),
    'active': fields.Boolean(required=False, description='Active'),
    'auth_token':  fields.String(required=False, description='Authentication Token'),
    'auth_token_expire':  fields.DateTime(required=False, description='Authentication Token Expiration Date'),
    'read_only': fields.Boolean(required=False, description='Read Only'),
    'all_roles': fields.List(fields.Nested(user_role_api_model))
})
user_api_model['roles'] = fields.List(fields.Nested(user_role_api_model))
user_api_model['groups'] = fields.List(fields.Nested(user_group_api_model))
'''
user_api_model['roles'] = fields.List(fields.Nested(Model('User Roles', {
    'id': fields.Integer,
    'name': fields.String()
})))
'''

page_users = api.inherit('Pages Users Table', pagination, {
    'items': fields.List(fields.Nested(user_api_model))
})

#---------------------------------------------------------------------------

component_api_model = api.model('Component Model', {
    'id': fields.Integer(readOnly=True, description='Identifier'),
    'name': fields.String(required=True, description='Name'),
    'title': fields.String(required=True, description='Title'),
    'description': fields.String(required=False, description='Description'),
    'type': fields.String(required=False, description='Type'),
    'plugin': fields.String(required=False, description='Plugin'),
    'target': fields.String(required=False, description='Target'),
    'scripts': fields.String(required=False, description='Scripts'),
    'is_active': fields.Boolean(required=False, description='Is active', default=True),
    'config_version': fields.String(required=False, description='Config Version'),
    'config_json': ConfigJson(required=False, description='Config'),
    'action': fields.String(required=False, description='Action'),
    'template': fields.String(required=False, description='Template'),
    'html_content': fields.String(required=False, description='HTML Content'),
    'icon_css_class': fields.String(required=False, description='Icon CSS Class')
})

page_component = api.inherit('Component pages', pagination, {
    'items': fields.List(fields.Nested(component_api_model))
})

viewer_component_api_model = api.clone('Viewer Component Model',component_api_model, {
    'id': fields.Integer(attribute='component_id', description='Component Identifier'),
    'viewer_id': fields.Integer(attribute='viewer_id', description='Viewer Identifier')
})

page_viewer_component = api.inherit('Viewer Component pages', pagination, {
    'items': fields.List(fields.Nested(viewer_component_api_model))
})

viewer_simple_api_model = api.model('Viewer Simple Model', {
    'id': fields.Integer(readOnly=True, description='Identifier'),
    'name': fields.String(required=True, description='Name'),
    'title': fields.String(required=True, description='Title'),
    'description': fields.String(required=False, description='Description'),
    'is_active': fields.Boolean(required=False, description='View is active')
})

viewer_api_model = api.model('Viewer Model', {
    'id': fields.Integer(readOnly=True, description='Identifier'),
    'name': fields.String(required=True, description='Name'),
    'title': fields.String(required=True, description='Title'),
    'description': fields.String(required=False, description='Description'),
    #'keywords': fields.String(required=False, description='Keywords'),
    'keywords': fields.List(fields.String(required=False, description='Keyword')),
    'author': fields.String(required=False, description='Author'),
    'lang': fields.String(required=False, description='Lang'),
    'slug': fields.String(required=False, description='Slug'),
    'bbox': fields.String(required=False, description='Bounding Box'),
    'maxbbox': fields.String(required=False, description='Max Bounding Box'),
    'config_version': fields.String(required=False, description='Config Version'),
    'config_json': ConfigJson(required=False, description='Config'),
    'is_active': fields.Boolean(required=False, description='View is active'),
    'allow_add_layers': fields.Boolean(required=False, description='Allow to add layers to map'),
    'allow_user_session': fields.Boolean(required=False, description='Allow user to save session'),
    'allow_sharing': fields.Boolean(required=False, description='Allow to share map'),
    'default_component': fields.String(required=False, description='Config Version'),
    'show_help': fields.Boolean(required=False, description='Show help'),
    'show_credits': fields.Boolean(required=False, description='Show credits'),
    'show_contact': fields.Boolean(required=False, description='Show contact'),
    'on_homepage': fields.Boolean(required=False, description='Show on homepage'),
    'img_homepage': fields.String(required=False, description='Image to show on homepage'),
    'img_logo': fields.String(required=False, description='Image logo'),
    'img_icon': fields.String(required=False, description='Image icon'),
    'send_email_notifications_admin': fields.Boolean(required=False, description='send email notifications to admin'),
    'email_notifications_admin': fields.String(required=False, description='Emails of admins'),
    'template': fields.String(required=False, description='Tempate'),
    'components': fields.List(fields.Nested(viewer_component_api_model), attribute='component_assoc'),
    'owner_id': fields.Integer(required=False, description='Owner Id'),
    'owner': fields.Nested(user_simple_api_model, skip_none=True),
    'custom_script':  fields.String(required=False, description='Custom script'),
    'custom_style':  fields.String(required=False, description='Custom style'),
    'styles': ConfigJson(readOnly=False, description='Style files'),
    'scripts': ConfigJson(readOnly=False, description='Script files')
})
viewer_api_model['roles'] = fields.List(fields.Nested(viewer_role_api_model))

print_viewer_api_model = api.model('Child Print Model', {
    'id': fields.Integer(readOnly=True, attribute='print.id', description='Identifier'),
    'code': fields.String(required=True, attribute='print.codigo', description='Code'),
    'title': fields.String(required=False, attribute='print.titulo', description='Title'),
    'description': fields.String(required=False, attribute='print.descricao', description='Description'),
    'is_active': fields.Boolean(readOnly=False, attribute='print.activo', description='Active'),
    'order': fields.Integer(required=False, attribute='order', description='Child order'),
})
viewer_api_model['prints'] = fields.List(fields.Nested(print_viewer_api_model), attribute='print_assoc')

print_group_viewer_api_model = api.model('Child Print Group Model', {
    'id': fields.Integer(readOnly=True, attribute='print_group.id', description='Identifier'),
    'code': fields.String(required=True, attribute='print_group.codigo', description='Code'),
    'title': fields.String(required=False, attribute='print_group.titulo', description='Title'),
    'description': fields.String(required=False, attribute='print_group.descricao', description='Description'),
    'is_active': fields.Boolean(readOnly=False, attribute='print_group.activo', description='Active'),
    'order': fields.Integer(required=False, attribute='order', description='Child order'),
})
viewer_api_model['print_groups'] = fields.List(fields.Nested(print_group_viewer_api_model), attribute='print_group_assoc')



viewer_app_api_model = api.model('Viewer Model', {
    'id': fields.Integer(readOnly=True, description='Identifier'),
    'uuid': fields.String(readOnly=True, description='UUID Identifier'),
    'name': fields.String(required=True, description='Name'),
    'title': fields.String(required=True, description='Title'),
    'description': fields.String(required=False, description='Description'),
    'config_version': fields.String(required=False, description='Config Version'),
    'config_json': ConfigJson(required=False, description='Config'),
    'allow_anonymous': fields.Boolean(required=False, default=True, description='Allow anonymous access'),
    'allow_add_layers': fields.Boolean(required=False, default=True, description='Allow to add layers to map'),
    'allow_user_session': fields.Boolean(required=False, default=False, description='Allow user to save session')
})

viewer_app_saved_api_model = api.model('Viewer App Saved Model', {
    'id': fields.Integer(readOnly=False, description='Identifier'),
    'uuid': fields.String(readOnly=False, description='UUID Identifier'),
    'name': fields.String(required=False, description='Name'),
    'success': fields.Boolean(required=False, description='Operation status')
})

page_viewer = api.inherit('Viewer pages', pagination, {
    'items': fields.List(fields.Nested(viewer_api_model))
})


viewer_contact_message_app_api_model = api.model('Viewer Contact Message Model', {
    'name': fields.String(required=True, description='Name'),
    'email': fields.String(required=True, description='Email'),
    'description': fields.String(required=False, description='Description'),
})


'''
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
    'name': fields.String(required=True, attribute='nome', description='Name'),
    'title': fields.String(required=False, attribute='titulo', description='Title'),
    'description': fields.String(required=False, attribute='descricao', description='Description'),
    'is_active': fields.Boolean(readOnly=False, attribute='activo', description='Active'),
    'scale': fields.Integer(readOnly=False, attribute='escala', description='Scale'),
    'format': fields.String(readOnly=False, attribute='formato', description='Format'),
    'orientation': fields.String(readOnly=False, attribute='orientacao', description='Orientation'),
    'identification': fields.Boolean(readOnly=False, attribute='identificacaoRequerente', description='Identification'),
    'identification_fields': ConfigJson(readOnly=False, attribute='identificacaoCampos',
                                        description='Fields Configuration'),
    'form_fields': ConfigJson(readOnly=False, attribute='formFields',
                                        description='Form Fields Configuration'),
    'location_marking': fields.Boolean(readOnly=False, attribute='marcacaoLocal', description='Location Marking'),
    'draw_location': fields.Boolean(readOnly=False, attribute='desenharLocal', description='Draw Location'),
    'free_printing': fields.Boolean(readOnly=False, attribute='emissaoLivre', description='Free Printing'),
    'add_title': fields.Boolean(readOnly=False, attribute='tituloEmissao', description='Add title'),
    'show_author': fields.Boolean(readOnly=False, attribute='autorEmissao', description='Show Author'),
    'payment_reference': fields.String(readOnly=False, attribute='guiaPagamento', description='Payment Reference'),
    'print_purpose': fields.Boolean(readOnly=False, attribute='finalidadeEmissao', description='Print purpose'),
    'restrict_scales': fields.Boolean(readOnly=False, attribute='escalasRestritas', description='Restrict Scales'),
    'restrict_scales_list': fields.String(readOnly=False, attribute='escalasRestritasLista',
                                          description='Restricted Scales List'),
    'multi_geom':  fields.Boolean(readOnly=False, attribute='multiGeom', description='Multi geometries'),
    'config_json': ConfigJson(readOnly=False, attribute='configuracao', description='Configuration'),

    'layouts': fields.List(fields.Nested(print_layout_api_model))
})
'''

domain_child_api_model = api.model('Modelo de Domínio', {
    'id': fields.Integer(required=True, description='Id'),
    'designacao': fields.String(required=True, description='Designação'),
})

#-------------------------------------------------------------------------------------

generic_api_model = api.model('Modelo das Intervencoes', {
    'id': fields.Integer(required=True, description='Id'),
    'name': fields.String(required=True, description='Name'),
    'code': fields.String(required=True, description='Code'),
    'description': fields.String(required=True, description='Description'),
    'config_json': ConfigJson(required=False, description='Config'),
    'parent_id': fields.Integer(required=False, description='Parent Id'),
    'parent': fields.String(required=False, description='Parent', attribute='parent.name'),
    'order': fields.Integer(required=False, description='Order'),
    'active': fields.Boolean(required=False, description='Active'),
    'read_only': fields.Boolean(required=False, description='Read Only'),
    #'childs': fields.List(fields.Nested(domain_child_api_model), attribute='children')
})
generic_api_model['childs'] = fields.List(fields.Nested(generic_api_model), attribute='children')

page_generic = api.inherit('Pages Generic Table', pagination, {
    'items': fields.List(fields.Nested(generic_api_model))
})


settings_api_model = api.model('Settings Model', {
    'id': fields.Integer(required=True, description='Id'),
    'code': fields.String(required=True, description='Code'),
    'name': fields.String(required=True, description='Name'),
    'notes': fields.String(required=False, description='Description'),
    'setting_value':  fields.String(required=True, description='Setting Value'),
    'active': fields.Boolean(required=False, description='Active'),
    'read_only': fields.Boolean(required=False, description='Read Only')
})
page_settings = api.inherit('Pages Settings Table', pagination, {
    'items': fields.List(fields.Nested(settings_api_model))
})
