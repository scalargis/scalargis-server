import os
from waitress import serve

from app import app
from app.services import init_wsgi

# Run from the same directory as this script
this_files_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(this_files_dir)

port = int(os.environ.get('PORT')) if os.environ.get('PORT') else 5000
url_prefix = os.environ.get('URL_PREFIX') or ''
threads = int(os.environ.get('THREADS')) if os.environ.get('THREADS') else 6
trusted_proxy = os.environ.get('TRUSTED_PROXY') or None
url_scheme = os.environ.get('URL_SCHEME') or 'http'

if __name__ == "__main__":
    init_wsgi()

    serve(app, host='0.0.0.0', port=port, threads=threads, url_prefix=url_prefix, trusted_proxy=trusted_proxy,
          url_scheme=url_scheme)

