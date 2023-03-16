import logging
from app.plugins.geonames.api.restx import api as api_geonames


logger = logging.getLogger(__name__)

ns = api_geonames.namespace('geonames', description='API Geonames', path='/v1')

api_module_config = {'APIisOpen': True}

from .geonames import *
