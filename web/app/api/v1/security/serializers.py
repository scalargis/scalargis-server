from flask_restx import fields
from app.api.restx import api


model = api.model('Model', {
    'authenticated': fields.Boolean,
    'token': fields.String,
    'username': fields.String,
    'userroles': fields.List(fields.String)
})