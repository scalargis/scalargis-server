from flask_restx import fields

from app.api.restx import api


class HasFile(fields.Raw):
    def output(self, key, obj, *args, **kwargs):
        return bool(obj.result_path)


job_status_api_model = api.model('Job status', {
    'id': fields.String(description='Job identifier'),
    'type': fields.String(description='Job type'),
    'status': fields.String(description='queued, running, done or failed'),
    'error': fields.String(description='Error of a failed job'),
    'has_file': HasFile(description='The result is a file'),
    'created_at': fields.DateTime(dt_format='iso8601'),
    'started_at': fields.DateTime(dt_format='iso8601'),
    'finished_at': fields.DateTime(dt_format='iso8601'),
})

job_result_api_model = api.model('Job result', {
    'id': fields.String(description='Job identifier'),
    'result': fields.Raw(description='JSON result of the job'),
})
