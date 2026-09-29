"""Worker entry point: loads the app and its extensions, then runs the background runner."""
import os

from app import app
from app import runner

this_files_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(this_files_dir)


if __name__ == '__main__':
    from app.main import init_wsgi

    init_wsgi(start_runner=False)
    runner.run_forever(app)
