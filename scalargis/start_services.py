import os
import sys


if __name__ == "__main__":
    # Run from the same directory as this script
    this_files_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(this_files_dir)

    from app.services import run

    run(sys.argv)
