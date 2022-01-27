import sys
import os

# Proxy configuration to allow web access (change username, password, ip and port
#os.environ["HTTP_PROXY"] = "http://username:password@172.16.13.254:8080/"
#os.environ["NO_PROXY"] = "localhost,127.0.0.1,172.21.83.17"

activate_this = 'C:/WKT/testes/venv/Scripts/activate_this.py'
with open(activate_this) as file_:
    exec(file_.read(), dict(__file__=activate_this))

# Expand Python classes path with your app's path
sys.path = []
sys.path = [
    'c:\\WKT\\apps\\websig_app\\web',
    'c:\\ms4w\\Python\\python37.zip',
    'c:\\ms4w\\Python\\DLLs',
    'c:\\ms4w\\Python\\lib',
    'c:\\ms4w\\Python',
    'c:\\WKT\\apps\\websig_app\\venv',
    'c:\\WKT\\apps\\websig_app\\venv\\lib\\site-packages',
]
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))

from app.proxy import app, init_wsgi

init_wsgi()

# Put logging code (and imports) here ...

# Initialize WSGI app object
application = app