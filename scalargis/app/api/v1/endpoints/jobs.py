import logging
import os

from flask import request, send_file
from flask_restx import Resource

from app.models.runner import STATUS_DONE
from ..portal.serializers.job import job_status_api_model, job_result_api_model
from ..portal.dao import job as dao_job
from ..endpoints import ns_jobs as ns


logger = logging.getLogger(__name__)


@ns.route('/<id>')
@ns.param('id', 'The job identifier')
class JobStatus(Resource):
    @ns.doc('get_job_status')
    @ns.response(404, 'Job not found')
    @ns.marshal_with(job_status_api_model)
    def get(self, id):
        """Returns the job status"""
        job = dao_job.get_readable_by_id(request, id)
        if job is None:
            ns.abort(404, 'Job not found')
        return job, 200


@ns.route('/<id>/result')
@ns.param('id', 'The job identifier')
class JobResult(Resource):
    @ns.doc('get_job_result')
    @ns.response(404, 'Job not found')
    @ns.response(409, 'Job not done')
    @ns.response(410, 'Result file deleted')
    def get(self, id):
        """Returns the job result: its file, or its JSON result"""
        job = dao_job.get_readable_by_id(request, id)
        if job is None:
            ns.abort(404, 'Job not found')
        if job.status != STATUS_DONE:
            return ns.marshal(job, job_status_api_model), 409
        if job.result_path:
            if not os.path.isfile(job.result_path):
                ns.abort(410, 'Result file deleted')
            return send_file(job.result_path, as_attachment=True,
                             download_name=os.path.basename(job.result_path))
        return ns.marshal(job, job_result_api_model), 200
